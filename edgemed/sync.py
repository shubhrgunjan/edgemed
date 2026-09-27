import json
import ssl
import threading
import time
from uuid import uuid4

import httpx
from qdrant_client import QdrantClient, models

from .fixtures import REFERENCES
from .models import Export, Receipt, PullPage
from .security import sign, verify


def tls_context(config, client=True):
    ctx = ssl.create_default_context(cafile=config["ca"])
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    if client:
        ctx.load_cert_chain(config["cert"], config["key"])
    return ctx


def bounded_post(client, path, data):
    with client.stream("POST", path, json=data) as response:
        chunks, size = [], 0
        for chunk in response.iter_bytes(16384):
            size += len(chunk)
            if size > 262144:
                raise ValueError("Synchronization response exceeds limit")
            chunks.append(chunk)
        return httpx.Response(response.status_code, content=b"".join(chunks), request=response.request)


class Transport:
    def __init__(self, store, config, secret):
        self.store, self.config, self.secret = store, config, secret
        self.lock = threading.Lock()
        self.last_error = None
        self.last_sync = None
        self.connection = "unknown"

    def run(self):
        if not self.store.get_setting("transport", False) or not self.lock.acquire(blocking=False):
            return
        try:
            with httpx.Client(
                base_url=self.config["gateway"],
                verify=tls_context(self.config),
                timeout=5,
                trust_env=False,
                follow_redirects=False,
            ) as client:
                for row in self.store.outbox():
                    if (
                        row["state"] in ("acknowledged", "failed", "cancelled")
                        or row["next_attempt"] > time.time()
                    ):
                        continue
                    payload = Export.model_validate_json(row["payload"]).model_dump(mode="json")
                    # Recheck the strict policy immediately before egress.
                    memory = self.store.get(payload["memory_id"], include_deleted=True)
                    if not memory["fixture"] or memory["privacy"] != "PUBLIC":
                        self.store.delivery(row["id"], "cancelled", error="Policy no longer permits sharing")
                        continue
                    if memory["deleted"] and not payload["deleted"]:
                        # Ancestors must reach central before tombstone; they contain fixture IDs only.
                        pass
                    try:
                        response = bounded_post(
                            client,
                            "/sync/push",
                            {
                                "payload": payload,
                                "signature": sign(payload, self.secret["sign_private"]),
                            },
                        )
                        if response.status_code >= 400:
                            permanent = response.status_code in (400, 401, 403, 422)
                            self.store.delivery(
                                row["id"],
                                "failed" if permanent else "retry_wait",
                                error=f"Gateway returned {response.status_code}",
                            )
                            self.connection = "attention" if permanent else "unavailable"
                            self.last_error = (
                                "A shared operation needs attention"
                                if permanent
                                else "Shared service unavailable"
                            )
                            return
                        receipt = response.json()
                        verify(receipt["payload"], receipt["signature"], self.config["gateway_public"])
                        Receipt.model_validate(receipt["payload"])
                        if receipt["payload"]["operation_id"] != row["id"]:
                            raise ValueError("Receipt identity mismatch")
                        self.store.delivery(row["id"], "acknowledged", receipt=receipt["payload"])
                    except (httpx.HTTPError, ValueError):
                        self.store.delivery(
                            row["id"], "retry_wait", error="Transport or receipt verification failed"
                        )
                        raise
                cursor = self.store.get_setting("cursor", 0)
                request = {"device_id": self.store.device, "cursor": cursor, "nonce": str(uuid4())}
                response = bounded_post(
                    client, "/sync/pull", {**request, "signature": sign(request, self.secret["sign_private"])}
                )
                response.raise_for_status()
                envelope = response.json()
                verify(envelope["payload"], envelope["signature"], self.config["gateway_public"])
                body = PullPage.model_validate(envelope["payload"]).model_dump(mode="json")
                if body["nonce"] != request["nonce"] or body["from_cursor"] != cursor:
                    raise ValueError("Pull response binding mismatch")
                for item in body["changes"]:
                    if item["seq"] != cursor + 1:
                        raise ValueError("Invalid change sequence")
                    self.store.accept(item["payload"])
                    self.store.set_setting("cursor", item["seq"])
                    cursor = item["seq"]
                self.last_error = None
                self.last_sync = time.time()
                self.connection = "connected"
        except httpx.HTTPError:
            self.connection = "unavailable"
            self.last_error = "Shared service unavailable; local work continues."
        except Exception:
            self.connection = "verification_error"
            self.last_error = "Synchronization verification failed; sharing stopped for this attempt."
        finally:
            self.lock.release()

    def status(self):
        rows = self.store.outbox()
        return {
            "enabled": self.store.get_setting("transport", False),
            "connection": (
                "paused"
                if not self.store.get_setting("transport", False)
                else "stale"
                if self.connection == "connected" and time.time() - (self.last_sync or 0) > 15
                else self.connection
            ),
            "counts": {
                state: sum(r["state"] == state for r in rows)
                for state in ("pending", "retry_wait", "failed", "cancelled", "acknowledged")
            },
            "last_sync": self.last_sync,
            "error": self.last_error,
            "cursor": self.store.get_setting("cursor", 0),
            "items": [
                {
                    **{k: r[k] for k in ("id", "state", "attempts", "error", "receipt")},
                    "payload": json.loads(r["payload"]),
                }
                for r in rows
            ],
        }


class CentralProjector:
    def __init__(self, store, model, config, secret):
        self.store, self.model = store, model
        self.client = QdrantClient(
            url=config["qdrant"],
            api_key=secret["qdrant_api_key"],
            verify=config["ca"],
            timeout=10,
            check_compatibility=True,
        )
        self.collection = "lex_synthetic_references"
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                self.collection, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )

    def drain(self):
        for job in self.store.pending_jobs()[:4]:
            if job["memory_deleted"]:
                self.client.delete(
                    self.collection, points_selector=models.PointIdsList(points=[job["id"]]), wait=True
                )
            else:
                # No edge-supplied content/vector is accepted; central reconstructs approved template.
                content = job["content"]
                assert any(content in r["variants"] for r in REFERENCES.values())
                vector = next(self.model.embed([content])).tolist()
                self.client.upsert(
                    self.collection,
                    points=[
                        models.PointStruct(
                            id=job["id"],
                            vector=vector,
                            payload={"memory_id": job["memory_id"], "schema_version": 1},
                        )
                    ],
                    wait=True,
                )
            self.store.mark_indexed(job["id"], job["generation"])

    def close(self):
        self.client.close()
