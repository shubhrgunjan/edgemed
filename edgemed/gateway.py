import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .models import SignedOperation, PullRequest
from .security import sign, verify
from .retrieval import local_embedder
from .store import Store
from .sync import CentralProjector


def create_gateway(config, secret, cache, projector_factory=CentralProjector):
    store = Store(config["data_path"], secret["db_key"], "central")
    projector = None

    @asynccontextmanager
    async def lifespan(app):
        nonlocal projector
        model = local_embedder(cache)
        projector = projector_factory(store, model, config, secret)

        from .workers import repeat, finish

        stop = asyncio.Event()
        tasks = [
            asyncio.create_task(
                repeat(
                    stop,
                    projector.drain,
                    lambda: store.set_setting("projection_error", "Central index temporarily unavailable"),
                )
            )
        ]
        try:
            yield
        finally:
            await finish(stop, tasks)
            projector.close()
            store.close()

    app = FastAPI(
        title="EdgeMed central gateway", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.store = store
    from .http_boundary import BoundedHTTP

    app.add_middleware(BoundedHTTP)
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse({"detail": "Invalid synchronization request"}, 422)

    def authenticate(device, payload, signature):
        identity = config["devices"].get(device)
        if not identity or identity.get("revoked"):
            raise HTTPException(403, "Device not authorized")
        try:
            verify(payload, signature, identity["public"])
        except ValueError:
            raise HTTPException(403, "Invalid device signature") from None

    def signed(payload):
        return {"payload": payload, "signature": sign(payload, secret["sign_private"])}

    @app.post("/sync/push")
    def push(op: SignedOperation):
        p = op.payload.model_dump(mode="json")
        authenticate(p["device_id"], p, op.signature)
        try:
            inserted = store.accept(p, central=True)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        with store.lock:
            row = store.db.execute(
                "SELECT state FROM jobs WHERE revision_id=?", (p["revision_id"],)
            ).fetchone()
        return signed(
            {
                "operation_id": p["operation_id"],
                "accepted": True,
                "duplicate": not inserted,
                "indexed": bool(row and row[0] == "indexed"),
            }
        )

    @app.post("/sync/pull")
    def pull(req: PullRequest):
        p = req.model_dump(mode="json")
        signature = p.pop("signature")
        authenticate(req.device_id, p, signature)
        import json

        with store.lock:
            changes = [
                {"seq": r[0], "payload": json.loads(r[1])}
                for r in store.db.execute(
                    "SELECT seq,payload FROM changes WHERE seq>? ORDER BY seq LIMIT 100", (req.cursor,)
                )
            ]
        return signed({"from_cursor": req.cursor, "nonce": str(req.nonce), "changes": changes})

    @app.post("/sync/reference-snapshot")
    def snapshot(req: PullRequest):
        from .snapshots import produce

        p = req.model_dump(mode="json")
        signature = p.pop("signature")
        authenticate(req.device_id, p, signature)
        try:
            path, header = produce(store, config, secret, str(req.nonce))
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from None
        return FileResponse(
            path,
            media_type="application/gzip",
            headers={"x-edgemed-manifest": header},
            background=BackgroundTask(path.unlink, missing_ok=True),
        )

    return app
