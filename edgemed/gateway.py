import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .models import SignedOperation, PullRequest
from .security import sign, verify
from .retrieval import TextEmbedding, MODEL
from .store import Store
from .sync import CentralProjector


def create_gateway(config, secret, cache, projector_factory=CentralProjector):
    store = Store(config["data_path"], secret["db_key"], "central")
    projector = None

    @asynccontextmanager
    async def lifespan(app):
        nonlocal projector
        model = TextEmbedding(MODEL, cache_dir=str(cache), local_files_only=True, threads=2)
        projector = projector_factory(store, model, config, secret)

        async def worker():
            while True:
                try:
                    await asyncio.to_thread(projector.drain)
                except Exception:
                    store.set_setting("projection_error", "Central index temporarily unavailable")
                await asyncio.sleep(1)

        task = asyncio.create_task(worker())
        yield
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        projector.close()
        store.close()

    app = FastAPI(
        title="EdgeMed central gateway", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan
    )
    app.state.store = store

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
