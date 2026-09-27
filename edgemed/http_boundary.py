"""Bound bodies before parsing and record only numeric request diagnostics."""

import asyncio
import time
from collections import deque

from starlette.responses import JSONResponse


class BoundedHTTP:
    def __init__(self, app, metrics=None, max_bytes=32768):
        self.app, self.max_bytes = app, max_bytes
        self.metrics = metrics if metrics is not None else deque(maxlen=256)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        start = time.perf_counter()
        chunks, size = [], 0
        try:
            async with asyncio.timeout(10):
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    size += len(message.get("body", b""))
                    if size > self.max_bytes:
                        return await JSONResponse(
                            {"detail": "Request too large"}, 413, headers={"Cache-Control": "no-store"}
                        )(scope, receive, send)
                    chunks.append(message.get("body", b""))
                    if not message.get("more_body"):
                        break
        except TimeoutError:
            return await JSONResponse(
                {"detail": "Request timed out"}, 408, headers={"Cache-Control": "no-store"}
            )(scope, receive, send)
        consumed = False
        response_bytes, status = 0, 0

        async def bounded_receive():
            nonlocal consumed
            if not consumed:
                consumed = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        async def observe(message):
            nonlocal response_bytes, status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = list(message.get("headers", []))
                headers.extend([(b"cache-control", b"no-store"), (b"x-content-type-options", b"nosniff")])
                message = {**message, "headers": headers}
            if message["type"] == "http.response.body":
                response_bytes += len(message.get("body", b""))
            await send(message)
            if message["type"] == "http.response.body" and not message.get("more_body"):
                self.metrics.append(
                    {
                        "total_ms": (time.perf_counter() - start) * 1000,
                        "bytes": response_bytes,
                        "status": status,
                    }
                )

        await self.app(scope, bounded_receive, observe)
