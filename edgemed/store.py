import json
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from sqlcipher3 import dbapi2 as sqlite

from .fixtures import REFERENCES, fixture_id, initial_revision
from .models import Export
from .security import audit_mac, digest


class Store:
    """SQLCipher is canonical; vector work and export intent are durable projections."""

    def __init__(self, root: Path, key: str, device="edge-a"):
        root = Path(root)
        if len(key) != 64 or any(c not in "0123456789abcdef" for c in key):
            raise ValueError("A 256-bit database key is required")
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.root, self.key, self.device = root, key, device
        self.lock = threading.RLock()
        self.generation = 0
        self.db = sqlite.connect(str(root / "memory.db"), check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite.Row
        self.db.execute(f'''PRAGMA key = "x'{key}'"''')
        if not self.db.execute("PRAGMA cipher_version").fetchone():
            raise RuntimeError("SQLCipher is required")
        self.db.execute("SELECT count(*) FROM sqlite_master").fetchone()
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS memories(
            id TEXT PRIMARY KEY, owner TEXT NOT NULL, title TEXT NOT NULL, subject TEXT,
            category TEXT NOT NULL, privacy TEXT NOT NULL, importance REAL NOT NULL,
            fixture TEXT, heads TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0,
            created REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS revisions(
            id TEXT PRIMARY KEY, memory_id TEXT NOT NULL REFERENCES memories(id),
            parents TEXT NOT NULL, content TEXT NOT NULL, device TEXT NOT NULL,
            variant INTEGER NOT NULL DEFAULT 0, deleted INTEGER NOT NULL DEFAULT 0,
            created REAL NOT NULL);
          CREATE TABLE IF NOT EXISTS jobs(revision_id TEXT PRIMARY KEY REFERENCES revisions(id),
            state TEXT NOT NULL DEFAULT 'pending', error TEXT);
          CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, payload TEXT NOT NULL,
            hash TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending', attempts INTEGER DEFAULT 0,
            next_attempt REAL DEFAULT 0, error TEXT, receipt TEXT);
          CREATE TABLE IF NOT EXISTS inbox(id TEXT PRIMARY KEY, hash TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS changes(seq INTEGER PRIMARY KEY AUTOINCREMENT,
            operation_id TEXT UNIQUE NOT NULL, payload TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,
            payload TEXT NOT NULL, previous TEXT NOT NULL, mac TEXT NOT NULL);
          CREATE INDEX IF NOT EXISTS revisions_memory ON revisions(memory_id);
        """)
        version = self.get_setting("schema", 1)
        if version not in (1, 2):
            raise RuntimeError("Unsupported database schema")
        with self.transaction():
            columns = {r[1] for r in self.db.execute("PRAGMA table_info(jobs)")}
            if "generation" not in columns:
                self.db.execute("ALTER TABLE jobs ADD COLUMN generation INTEGER NOT NULL DEFAULT 0")
            self.db.execute("CREATE INDEX IF NOT EXISTS memory_scope ON memories(owner,deleted,subject)")
            self.set_setting("schema", 2)
        self.verify_audit()

    @contextmanager
    def transaction(self):
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                yield
                self.db.execute("COMMIT")
                self.generation += 1
            except BaseException:
                self.db.execute("ROLLBACK")
                raise

    def get_setting(self, key, default=None):
        with self.lock:
            row = self.db.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
            return json.loads(row[0]) if row else default

    def set_setting(self, key, value):
        with self.lock:
            self.db.execute(
                "INSERT INTO metadata VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value WHERE value!=excluded.value",
                (key, json.dumps(value)),
            )

    def event(self, action, memory_id=None):
        last = self.db.execute("SELECT mac FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        previous = last[0] if last else "0" * 64
        payload = {"action": action, "memory_id": memory_id, "time": time.time(), "device": self.device}
        mac = audit_mac(self.key, previous, payload)
        self.db.execute(
            "INSERT INTO events(payload,previous,mac) VALUES(?,?,?)", (json.dumps(payload), previous, mac)
        )

    def verify_audit(self):
        with self.lock:
            previous = "0" * 64
            for row in self.db.execute("SELECT * FROM events ORDER BY seq"):
                if row["previous"] != previous or row["mac"] != audit_mac(
                    self.key, previous, json.loads(row["payload"])
                ):
                    raise RuntimeError("Audit chain verification failed")
                previous = row["mac"]
            return previous

    def _append(self, memory, rid, parents, content, device, variant=0, deleted=False, outbound=False):
        existing = self.db.execute("SELECT * FROM revisions WHERE id=?", (rid,)).fetchone()
        if existing:
            if (
                existing["memory_id"],
                json.loads(existing["parents"]),
                existing["content"],
                existing["deleted"],
            ) != (memory["id"], parents, content, int(deleted)):
                raise ValueError("Revision ID reused with different content")
            return
        heads = json.loads(memory["heads"]) if isinstance(memory["heads"], str) else list(memory["heads"])
        for parent in parents:
            if not self.db.execute(
                "SELECT 1 FROM revisions WHERE id=? AND memory_id=?", (parent, memory["id"])
            ).fetchone():
                raise ValueError("Missing parent revision")
        if memory["deleted"] and not deleted:
            raise ValueError("Deleted records cannot be resurrected")
        self.db.execute(
            "INSERT INTO revisions VALUES(?,?,?,?,?,?,?,?)",
            (rid, memory["id"], json.dumps(parents), content, device, variant, int(deleted), time.time()),
        )
        heads = [h for h in heads if h not in parents] + [rid]
        self.db.execute(
            "UPDATE memories SET heads=?,deleted=? WHERE id=?",
            (json.dumps(heads), int(deleted or memory["deleted"]), memory["id"]),
        )
        self.db.execute("INSERT INTO jobs(revision_id) VALUES(?)", (rid,))
        if deleted:
            self.db.execute(
                "UPDATE jobs SET state='pending',generation=generation+1 WHERE revision_id IN (SELECT id FROM revisions WHERE memory_id=?)",
                (memory["id"],),
            )
        self.event("deleted" if deleted else "revision_saved", memory["id"])
        if outbound and memory["fixture"]:
            payload = Export(
                operation_id=uuid4(),
                memory_id=memory["id"],
                revision_id=rid,
                parents=parents,
                device_id=self.device,
                fixture=memory["fixture"],
                variant=variant,
                deleted=deleted,
            ).model_dump(mode="json")
            self.db.execute(
                "INSERT INTO outbox(id,payload,hash) VALUES(?,?,?)",
                (payload["operation_id"], json.dumps(payload), digest(payload)),
            )

    def create(self, data, owner="operator"):
        mid, rid = str(uuid4()), str(uuid4())
        with self.transaction():
            self.db.execute(
                "INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    mid,
                    owner,
                    data.title,
                    data.subject,
                    data.category,
                    data.privacy,
                    data.importance,
                    None,
                    "[]",
                    0,
                    time.time(),
                ),
            )
            row = self.db.execute("SELECT * FROM memories WHERE id=?", (mid,)).fetchone()
            self._append(row, rid, [], data.content, self.device)
        return self.get(mid, owner)

    def seed_reference(self, name, owner="operator"):
        mid = fixture_id(name)
        with self.transaction():
            row = self.db.execute("SELECT * FROM memories WHERE id=?", (mid,)).fetchone()
            if row is None:
                self.db.execute(
                    "INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        mid,
                        owner,
                        REFERENCES[name]["title"],
                        None,
                        "REFERENCE",
                        "PUBLIC",
                        0.7,
                        name,
                        "[]",
                        0,
                        time.time(),
                    ),
                )
                row = self.db.execute("SELECT * FROM memories WHERE id=?", (mid,)).fetchone()
                self._append(
                    row,
                    initial_revision(name),
                    [],
                    REFERENCES[name]["variants"][0],
                    self.device,
                    outbound=True,
                )
        return self.get(mid, owner)

    def get(self, mid, owner="operator", include_deleted=False):
        with self.lock:
            row = self.db.execute("SELECT * FROM memories WHERE id=? AND owner=?", (mid, owner)).fetchone()
            if row is None or (row["deleted"] and not include_deleted):
                raise KeyError("Memory not found")
            obj = dict(row)
            obj["heads"] = json.loads(obj["heads"])
            revs = [
                dict(r)
                for r in self.db.execute(
                    "SELECT r.*,j.state AS index_state FROM revisions r JOIN jobs j ON j.revision_id=r.id WHERE memory_id=? ORDER BY created",
                    (mid,),
                )
            ]
            for rev in revs:
                rev["parents"] = json.loads(rev["parents"])
            obj["revisions"] = revs
            active = [r for r in revs if r["id"] in obj["heads"]]
            obj["content"] = active[-1]["content"] if active else ""
            obj["conflicting"] = len(obj["heads"]) > 1 and not obj["deleted"]
            obj["index_state"] = (
                "indexed" if all(r["index_state"] == "indexed" for r in active) else "pending"
            )
            obj["release"] = "ELIGIBLE" if obj["fixture"] else "LOCAL_ONLY"
            obj["reason"] = (
                "Reviewed synthetic reference template; only fixture ID and variant may leave."
                if obj["fixture"]
                else "Patient observations and derived embeddings stay on this device."
            )
            return obj

    def list(self, owner="operator", limit=100, offset=0):
        with self.lock:
            clause, scopes = self._scope_clause(owner)
            rows = self.db.execute(
                f"SELECT id,owner FROM memories WHERE owner IN {clause} AND deleted=0 "
                "ORDER BY created DESC LIMIT ? OFFSET ?",
                (*scopes, limit, offset),
            )
            return [self.get(row[0], row[1]) for row in rows]

    def revise(self, mid, parents, content=None, variant=None, owner="operator", deleted=False):
        with self.transaction():
            memory = self.get(mid, owner)
            if memory["fixture"]:
                if variant not in (0, 1, 2):
                    raise ValueError("Only reviewed reference variants can be shared")
                content = REFERENCES[memory["fixture"]]["variants"][variant]
            self._append(
                memory,
                str(uuid4()),
                parents,
                content or memory["content"],
                self.device,
                variant or 0,
                deleted,
                outbound=bool(memory["fixture"]),
            )
        return self.get(mid, owner, include_deleted=True)

    def resolve(self, mid, parents, chosen, owner="operator"):
        with self.lock:
            memory = self.get(mid, owner)
            if set(parents) != set(memory["heads"]) or chosen not in parents:
                raise ValueError("Resolution must include every current branch")
            rev = next(r for r in memory["revisions"] if r["id"] == chosen)
            return self.revise(
                mid, parents, rev["content"], rev["variant"] if memory["fixture"] else None, owner
            )

    def accept(self, payload, owner="operator", central=False):
        """Already authenticated at transport boundary; DTO cannot contain arbitrary text/vectors."""
        p = Export.model_validate(payload).model_dump(mode="json")
        if p["memory_id"] != fixture_id(p["fixture"]):
            raise ValueError("Fixture identity mismatch")
        h = digest(p)
        with self.transaction():
            old = self.db.execute("SELECT hash FROM inbox WHERE id=?", (p["operation_id"],)).fetchone()
            if old:
                if old[0] != h:
                    raise ValueError("Operation ID reused")
                return False
            row = self.db.execute("SELECT * FROM memories WHERE id=?", (p["memory_id"],)).fetchone()
            if row is None:
                if (
                    p["parents"]
                    or p["revision_id"] != initial_revision(p["fixture"])
                    or p["variant"] != 0
                    or p["deleted"]
                ):
                    raise ValueError("Missing initial reference revision")
                self.db.execute(
                    "INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        p["memory_id"],
                        owner,
                        REFERENCES[p["fixture"]]["title"],
                        None,
                        "REFERENCE",
                        "PUBLIC",
                        0.7,
                        p["fixture"],
                        "[]",
                        0,
                        time.time(),
                    ),
                )
                row = self.db.execute("SELECT * FROM memories WHERE id=?", (p["memory_id"],)).fetchone()
            # A late pre-deletion update is acknowledged but may never resurrect content.
            if not (row["deleted"] and not p["deleted"]):
                self._append(
                    row,
                    p["revision_id"],
                    p["parents"],
                    REFERENCES[p["fixture"]]["variants"][p["variant"]],
                    p["device_id"],
                    p["variant"],
                    p["deleted"],
                )
            self.db.execute("INSERT INTO inbox VALUES(?,?)", (p["operation_id"], h))
            if central:
                self.db.execute(
                    "INSERT INTO changes(operation_id,payload) VALUES(?,?)",
                    (p["operation_id"], json.dumps(p)),
                )
        return True

    def pending_jobs(self):
        with self.lock:
            return [
                dict(r)
                for r in self.db.execute(
                    "SELECT r.*,j.generation,m.owner,m.subject,m.category,m.privacy,m.deleted AS memory_deleted FROM jobs j JOIN revisions r ON r.id=j.revision_id JOIN memories m ON m.id=r.memory_id WHERE j.state!='indexed' LIMIT 32"
                )
            ]

    def mark_indexed(self, rid, generation=None):
        with self.lock:
            if generation is None:
                generation = self.db.execute(
                    "SELECT generation FROM jobs WHERE revision_id=?", (rid,)
                ).fetchone()[0]
            self.generation += 1
            return (
                self.db.execute(
                    "UPDATE jobs SET state='indexed',error=NULL WHERE revision_id=? AND generation=?",
                    (rid, generation),
                ).rowcount
                == 1
            )

    def job_current(self, job):
        with self.lock:
            row = self.db.execute(
                "SELECT generation,state FROM jobs WHERE revision_id=?", (job["id"],)
            ).fetchone()
            return bool(row and row[0] == job["generation"] and row[1] != "indexed")

    @staticmethod
    def _scope_clause(owner):
        scopes = (owner,) if isinstance(owner, str) else tuple(owner)
        if not scopes or len(scopes) > 2 or any(not isinstance(scope, str) for scope in scopes):
            raise ValueError("Invalid authorized scope")
        return "(" + ",".join("?" for _ in scopes) + ")", scopes

    def current_records(self, owner="operator", subject=None):
        """One SQL read of all authorized current heads; no history or silent corpus cap."""
        with self.lock:
            clause, scopes = self._scope_clause(owner)
            rows = self.db.execute(
                "SELECT m.*,r.id AS rid,r.content,r.created AS revision_created,j.state AS index_state "
                "FROM memories m JOIN json_each(m.heads) h "
                "JOIN revisions r ON r.id=h.value JOIN jobs j ON j.revision_id=r.id "
                f"WHERE m.owner IN {clause} AND m.deleted=0 AND (? IS NULL OR m.subject=?) "
                "ORDER BY m.created DESC,m.id,r.created,r.id",
                (*scopes, subject, subject),
            ).fetchall()
            records = {}
            for row in rows:
                r = dict(row)
                mid = r["id"]
                if mid not in records:
                    r["heads"] = json.loads(r["heads"])
                    r["conflicting"] = len(r["heads"]) > 1
                    r["release"] = "ELIGIBLE" if r["fixture"] else "LOCAL_ONLY"
                    r["active"] = []
                    records[mid] = r
                records[mid]["active"].append(
                    {"id": r["rid"], "content": r["content"], "created": r["revision_created"]}
                )
                records[mid]["content"] = r["content"]
                if r["index_state"] != "indexed":
                    records[mid]["index_state"] = "pending"
            return records

    def summaries(self, owner="operator", limit=100, offset=0, conflicts=False):
        with self.lock:
            clause, scopes = self._scope_clause(owner)
            rows = self.db.execute(
                "SELECT m.*,json_array_length(heads)>1 AS conflicting,"
                "EXISTS(SELECT 1 FROM json_each(m.heads) h JOIN jobs j ON j.revision_id=h.value "
                "WHERE j.state!='indexed') AS pending FROM memories m "
                f"WHERE owner IN {clause} AND deleted=0 AND (?=0 OR json_array_length(heads)>1) "
                "ORDER BY created DESC,id LIMIT ? OFFSET ?",
                (*scopes, int(conflicts), limit, offset),
            ).fetchall()
            return [
                {
                    **dict(r),
                    "heads": json.loads(r["heads"]),
                    "conflicting": bool(r["conflicting"]),
                    "index_state": "pending" if r["pending"] else "indexed",
                    "release": "ELIGIBLE" if r["fixture"] else "LOCAL_ONLY",
                }
                for r in rows
            ]

    def stats(self, owner):
        with self.lock:
            clause, scopes = self._scope_clause(owner)
            row = self.db.execute(
                "SELECT count(*) AS total,coalesce(sum(fixture IS NULL),0) AS local_only,"
                "coalesce(sum(json_array_length(heads)>1),0) AS conflicts,"
                "coalesce(sum(NOT EXISTS(SELECT 1 FROM json_each(m.heads) h JOIN jobs j "
                "ON j.revision_id=h.value WHERE j.state!='indexed')),0) AS indexed "
                f"FROM memories m WHERE owner IN {clause} AND deleted=0",
                scopes,
            ).fetchone()
            return dict(row)

    def eligible_results(self, results, owner, subject=None):
        """Final canonical check; complete deletions cannot be returned from stale projection/cache."""
        with self.lock:
            if not results:
                return []
            clause, scopes = self._scope_clause(owner)
            ids = [r["id"] for r in results]
            rows = self.db.execute(
                f"SELECT id,heads FROM memories WHERE owner IN {clause} AND deleted=0 "
                "AND (? IS NULL OR subject=?) AND id IN (" + ",".join("?" for _ in ids) + ")",
                [*scopes, subject, subject, *ids],
            )
            allowed = {r[0]: json.loads(r[1]) for r in rows}
            return [r for r in results if r["id"] in allowed and r["matched_revision_id"] in allowed[r["id"]]]

    def outbox(self):
        with self.lock:
            return [dict(r) for r in self.db.execute("SELECT * FROM outbox ORDER BY rowid")]

    def delivery(self, oid, state, receipt=None, error=None):
        with self.transaction():
            row = self.db.execute("SELECT attempts FROM outbox WHERE id=?", (oid,)).fetchone()
            attempts = row[0] + 1
            self.db.execute(
                "UPDATE outbox SET state=?,attempts=?,next_attempt=?,error=?,receipt=? WHERE id=?",
                (
                    state,
                    attempts,
                    time.time() + min(60, 2 ** min(attempts, 6)),
                    error,
                    json.dumps(receipt),
                    oid,
                ),
            )
            self.event("sync_" + state)

    def activity(self, owner=None):
        with self.lock:
            scopes = None if owner is None else set(self._scope_clause(owner)[1])
            events = []
            for row in self.db.execute("SELECT payload FROM events ORDER BY seq DESC LIMIT 200"):
                event = json.loads(row[0])
                if scopes is not None:
                    memory_id = event["memory_id"]
                    if not memory_id:
                        continue
                    memory = self.db.execute("SELECT owner FROM memories WHERE id=?", (memory_id,)).fetchone()
                    if not memory or memory[0] not in scopes:
                        continue
                events.append(event)
                if len(events) >= 40:
                    break
            return events

    def graph(self, owner="operator"):
        records = self.list(owner)
        nodes, edges = {}, []
        for r in records:
            nodes[r["id"]] = {"id": r["id"], "label": r["title"], "kind": "memory", "privacy": r["privacy"]}
            entity = r["subject"] or "Shared reference"
            nodes[entity] = {"id": entity, "label": entity, "kind": "subject"}
            edges.append({"source": entity, "target": r["id"], "label": r["category"]})
        return {"nodes": list(nodes.values()), "edges": edges}

    def close(self):
        with self.lock:
            self.db.close()
