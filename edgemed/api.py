import asyncio
import hashlib
import hmac
import threading
import time
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from .fixtures import NOTES, REFERENCES
from .models import Login, CreateMemory, Revision, Resolve, Search, FixtureRevision, TransportState
from .retrieval import Retrieval, MODEL
from .security import password_valid, issue_session
from .store import Store
from .sync import Transport
from .governance import evaluate
from .accounts import scopes, record_owner


def create_app(config, secret, cache, frontend=None, retrieval_factory=Retrieval):
    store = Store(Path(config["data_path"]), secret["db_key"], config["device_id"])
    sessions, attempts = {}, {}
    auth_lock = threading.Lock()
    snapshot_lock = threading.Lock()
    retrieval = retrieval_factory(store, Path(cache))
    transport = Transport(store, config, secret) if config.get("gateway") else None

    @asynccontextmanager
    async def lifespan(app):
        from .workers import repeat, finish

        stop = asyncio.Event()

        def index():
            result = retrieval.drain()
            store.set_setting("worker_error", None)
            return result

        tasks = [
            asyncio.create_task(
                repeat(
                    stop,
                    index,
                    lambda: store.set_setting(
                        "worker_error", "Indexing delayed; saved records are preserved."
                    ),
                )
            )
        ]
        if transport:
            tasks.append(asyncio.create_task(repeat(stop, transport.run)))
        try:
            yield
        finally:
            await finish(stop, tasks)
            retrieval.close()
            store.close()

    app = FastAPI(
        title="EdgeMed Local",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    app.state.store, app.state.retrieval, app.state.transport = store, retrieval, transport
    app.state.sessions = sessions
    from collections import deque
    from .http_boundary import BoundedHTTP

    app.state.request_metrics = deque(maxlen=256)
    app.state.search_metrics = deque(maxlen=256)
    app.add_middleware(BoundedHTTP, metrics=app.state.request_metrics)

    def clear_cache():
        if hasattr(retrieval, "clear_cache"):
            retrieval.clear_cache()

    origin = config.get("origin", "http://127.0.0.1:8765")
    host = origin.split("://", 1)[1]

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        if request.headers.get("host") != host:
            return JSONResponse({"detail": "Host not permitted"}, 400)
        if (
            request.headers.get("origin") not in (None, origin)
            or request.headers.get("sec-fetch-site") == "cross-site"
        ):
            return JSONResponse({"detail": "Origin not permitted"}, 403)
        if request.method not in ("GET", "HEAD"):
            body, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 32768:
                    return JSONResponse({"detail": "Request too large"}, 413)
                body.append(chunk)
            request._body = b"".join(body)
        if request.url.path.startswith("/api/") and request.url.path not in ("/api/login", "/api/health"):
            token = request.cookies.get("edgemed_session", "")
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            with auth_lock:
                session = sessions.get(token_hash)
                if (
                    not session
                    or session["expires"] < time.time()
                    or time.monotonic() - session["last_active"] >= config.get("idle_seconds", 300)
                ):
                    sessions.pop(token_hash, None)
                    clear_cache()
                    return JSONResponse({"detail": "Please sign in"}, 401)
                if request.method not in ("GET", "HEAD") and not hmac.compare_digest(
                    request.headers.get("x-csrf-token", ""), session["csrf"]
                ):
                    return JSONResponse({"detail": "CSRF verification failed"}, 403)
                if request.method not in ("GET", "HEAD"):
                    session["last_active"] = time.monotonic()
                request.state.identity = session["identity"]
                request.state.session = session
                request.state.token_hash = token_hash
        try:
            response = await call_next(request)
        except KeyError:
            response = JSONResponse({"detail": "Record not found"}, 404)
        except ValueError as exc:
            response = JSONResponse({"detail": str(exc)}, 409)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse(
            {"detail": [{"loc": e["loc"], "msg": e["msg"], "type": e["type"]} for e in exc.errors()]}, 422
        )

    def owner(request):
        return scopes(request.state.identity)

    def own_scope(request, privacy):
        return record_owner(request.state.identity, privacy)

    def authorized_record(mid, request):
        for scope in owner(request):
            try:
                return store.get(mid, scope), scope
            except KeyError:
                continue
        raise KeyError("Memory not found")

    def admin(request):
        if request.state.identity.get("role") != "admin":
            raise HTTPException(403, "Administrator permission required")

    def system_admin(request):
        admin(request)
        if request.state.identity["username"] != "operator":
            raise HTTPException(403, "Server operator permission required")

    @app.get("/api/health")
    def health():
        return {"status": "ready"}

    @app.post("/api/login")
    def login(data: Login, request: Request):
        remote = request.client.host if request.client else "local"
        with auth_lock:
            recent = [t for t in attempts.get(remote, []) if time.time() - t < 300]
            if len(recent) >= 8:
                raise HTTPException(429, "Too many attempts; retry in five minutes")
            attempts[remote] = recent + [time.time()]
        user = secret["operators"].get(data.username)
        candidate_hash = (
            user["password_hash"] if user else next(iter(secret["operators"].values()))["password_hash"]
        )
        if not password_valid(candidate_hash, data.password) or not user or user.get("disabled"):
            raise HTTPException(401, "Invalid credentials")
        token, csrf, expires = issue_session()
        with auth_lock:
            attempts.pop(remote, None)
            for expired in [k for k, v in sessions.items() if v["expires"] < time.time()]:
                sessions.pop(expired, None)
            if len(sessions) >= 32:
                sessions.pop(next(iter(sessions)))
            sessions[hashlib.sha256(token.encode()).hexdigest()] = {
                "csrf": csrf,
                "expires": expires,
                "last_active": time.monotonic(),
                "identity": {"username": data.username, "owner": user["owner"], "role": user["role"]},
            }
        response = JSONResponse({"csrf": csrf, "username": data.username, "role": user["role"]})
        response.set_cookie(
            "edgemed_session",
            token,
            httponly=True,
            secure=origin.startswith("https:"),
            samesite="strict",
            max_age=1800,
        )
        return response

    @app.get("/api/session")
    def session(request: Request):
        return {
            "csrf": request.state.session["csrf"],
            "username": request.state.identity["username"],
            "role": request.state.identity["role"],
        }

    @app.post("/api/session/activity")
    def user_activity(request: Request):
        return {"ok": True}

    @app.post("/api/logout")
    def logout(request: Request):
        with auth_lock:
            sessions.pop(request.state.token_hash, None)
        clear_cache()
        response = JSONResponse({"ok": True})
        response.delete_cookie("edgemed_session")
        return response

    @app.get("/api/status")
    def status(request: Request):
        return {
            "device": store.device,
            "synthetic_only": True,
            "deployment": "hospital_lan" if config.get("lan_mode") else "local",
            "workspace": request.state.identity["owner"],
            "role": request.state.identity["role"],
            "generation": store.generation,
            **store.stats(owner(request)),
            "model": MODEL,
            "engine": "Qdrant Edge 0.8.0",
            "database": "SQLCipher",
            "vault": config.get("vault_verified", False),
            "worker_error": store.get_setting("worker_error"),
        }

    @app.get("/api/memories")
    def memories(
        request: Request,
        limit: int = Query(100, ge=1, le=100),
        offset: int = Query(0, ge=0),
        conflicts: bool = False,
    ):
        return store.summaries(owner(request), limit, offset, conflicts)

    @app.post("/api/memories", status_code=201)
    def create(data: CreateMemory, request: Request):
        return store.create(data, own_scope(request, data.privacy))

    @app.get("/api/memories/{mid}")
    def get(mid: UUID, request: Request):
        memory = authorized_record(str(mid), request)[0]
        if config.get("lan_mode") and not memory["fixture"]:
            memory["reason"] = (
                "Personal observation visible only to this staff account on the server."
                if memory["privacy"] == "HIGHLY_SENSITIVE"
                else "Workspace observation visible to authorized staff on this server."
            )
        return memory

    @app.get("/api/memories/{mid}/governance")
    def governance(mid: UUID, request: Request):
        return evaluate(authorized_record(str(mid), request)[0])

    @app.post("/api/memories/{mid}/revisions", status_code=201)
    def revise(mid: UUID, data: Revision, request: Request):
        memory, scope = authorized_record(str(mid), request)
        if memory["fixture"]:
            raise HTTPException(403, "Reference changes require administrator permission")
        return store.revise(str(mid), [str(data.parent)], data.content, owner=scope)

    @app.post("/api/memories/{mid}/reference-variant", status_code=201)
    def reference_variant(mid: UUID, data: FixtureRevision, request: Request):
        admin(request)
        memory, scope = authorized_record(str(mid), request)
        if not memory["fixture"]:
            raise HTTPException(409, "Only reviewed references accept variants")
        return store.revise(str(mid), [str(data.parent)], variant=data.variant, owner=scope)

    @app.post("/api/memories/{mid}/resolve")
    def resolve(mid: UUID, data: Resolve, request: Request):
        admin(request)
        _, scope = authorized_record(str(mid), request)
        return store.resolve(str(mid), list(map(str, data.parents)), str(data.chosen), scope)

    @app.delete("/api/memories/{mid}")
    def delete(mid: UUID, request: Request):
        m, scope = authorized_record(str(mid), request)
        if scope != f"personal:{request.state.identity['username']}":
            admin(request)
        return store.revise(
            str(mid), m["heads"], variant=0 if m["fixture"] else None, owner=scope, deleted=True
        )

    @app.post("/api/search")
    def search(data: Search, request: Request):
        start = time.perf_counter()
        timings = {} if config.get("profiling", False) else None
        results = retrieval.search(
            data.query, owner(request), data.limit, data.mode, data.subject, timings=timings
        )
        body = {
            "results": results,
            "elapsed_ms": round((time.perf_counter() - start) * 1000, 1),
            "route": "LOCAL",
            **({"timings_ms": timings} if timings is not None else {}),
            "model": MODEL,
        }
        encode = time.perf_counter()
        response = JSONResponse(body)
        if timings is not None:
            app.state.search_metrics.append(
                {
                    **timings,
                    "serialization": (time.perf_counter() - encode) * 1000,
                    "handler_total": (time.perf_counter() - start) * 1000,
                }
            )
        return response

    @app.get("/api/diagnostics")
    def diagnostics(request: Request):
        admin(request)
        if not config.get("profiling", False):
            raise HTTPException(404, "Diagnostics disabled")
        return {"requests": list(app.state.request_metrics), "searches": list(app.state.search_metrics)}

    @app.get("/api/graph")
    def graph(request: Request):
        return store.graph(owner(request))

    @app.get("/api/activity")
    def activity(request: Request):
        admin(request)
        return store.activity(owner(request))

    @app.get("/api/sync/status")
    def sync_status(request: Request):
        system_admin(request)
        return (
            transport.status()
            if transport
            else {"enabled": False, "items": [], "error": "Central node not configured"}
        )

    @app.post("/api/sync/transport")
    def sync_state(data: TransportState, request: Request):
        system_admin(request)
        store.set_setting("transport", data.enabled)
        return {"enabled": data.enabled}

    @app.post("/api/sync")
    def sync_now(request: Request):
        system_admin(request)
        if transport:
            transport.run()
            return transport.status()
        raise HTTPException(503, "Central node not configured")

    @app.post("/api/sync/reference-snapshot")
    def reference_snapshot(request: Request):
        system_admin(request)
        if not transport:
            raise HTTPException(503, "Central node not configured")
        from .snapshots import fetch

        transport.run()
        with snapshot_lock:
            previous = store.get_setting("reference_snapshot")
            state = fetch(transport)
            try:
                retrieval.reload_reference()
            except Exception:
                store.set_setting("reference_snapshot", previous)
                raise HTTPException(
                    409, "Reference cache activation failed; previous cache preserved"
                ) from None
            if previous and previous["path"] != state["path"]:
                import shutil

                old = Path(previous["path"])
                if (
                    old.parent.resolve() == (store.root / "reference-snapshots").resolve()
                    and not old.is_symlink()
                ):
                    shutil.rmtree(old, ignore_errors=True)
            return state

    @app.post("/api/demo/seed")
    def seed(request: Request):
        admin(request)
        workspace = request.state.identity["owner"]
        if store.get_setting("seeded:" + workspace, False):
            return {"seeded": False}
        for data in NOTES:
            store.create(CreateMemory(**data), workspace)
        if workspace == "operator":
            for name in REFERENCES:
                store.seed_reference(name, workspace)
        store.set_setting("seeded:" + workspace, True)
        return {"seeded": True}

    @app.get("/api/contract")
    def contract(request: Request):
        return app.openapi()

    if frontend and Path(frontend, "index.html").exists():
        app.mount("/assets", StaticFiles(directory=Path(frontend, "assets")), name="assets")

        @app.get("/")
        def index():
            return FileResponse(Path(frontend, "index.html"))

    return app
