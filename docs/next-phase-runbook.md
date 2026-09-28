# Next-phase operation and verification

## Isolated environment

Always use a distinct runtime directory, Keychain namespace and port offset together. Never reuse the original namespace for tests. Example values below create their own synthetic runtime:

```sh
export EDGEMED_RUNTIME="$HOME/Library/Application Support/EdgeMed Verification"
export EDGEMED_KEYCHAIN_SERVICE=org.lex.edgemed.verification
export EDGEMED_PORT_OFFSET=2000
export EDGEMED_BASE_URL=http://127.0.0.1:10765
export EDGEMED_PROFILE=1
uv run python -m edgemed.cli setup
uv run python -m edgemed.cli start
uv run python -m edgemed.cli preflight
```

`EDGEMED_PROFILE=1` enables numeric timing diagnostics for an authenticated administrator. It does not record notes, queries or credentials. Omit it for ordinary use. The runtime directory contains an encrypted sparsebundle; database, vector, TLS and log files stay inside its mounted volume. Keys remain in the named Keychain service.

## Tests and demo

Before running the full backend suite on a fresh checkout, provision the pinned model once online:

```sh
uv run python scripts/provision_assets.py --model-only
```

This works independently of the macOS launcher and server binary; see [Linux retrieval test setup](local-prototype.md#retrieval-tests-on-linux-mint--ubuntu). Tests do not silently download or skip a missing model.

```sh
uv run pytest -q
uv run ruff check edgemed tests scripts
(cd frontend && npm ci && npm run build && npx playwright install chromium --only-shell && npm test)
uv run python scripts/verify_local.py
uv run python scripts/profile_http.py
```

The live verifier refuses the default Keychain namespace. It stops only the isolated gateway to demonstrate a real outage, creates local synthetic notes, edits approved references on both devices, restarts the gateway, resolves a conflict, verifies private-note exclusion, TLS/signature rejection, central projection and a signed full snapshot. Run it three times for rehearsal. It appends synthetic test history; it does not reset either original or isolated data.

For a manual demonstration, show connected sharing, save a private observation, interrupt only the gateway, save/search offline, edit an approved reference and show its queue item, reconnect, demonstrate its appearance on B, then compare and resolve branches. Pausing sharing is labeled a simulation. Turning off Wi-Fi alone does not break an all-loopback gateway.

## Performance

```sh
uv run python scripts/profile_search.py --cache .cache/models \
  --root "$EDGEMED_RUNTIME/vault" --output /tmp/edgemed-profile.json
```

The harness creates and deletes only its own temporary synthetic dataset. Defaults: 1,000 records, 10% with another revision, 20 warm-ups, 200 distinct query strings from five templates, three runs of 1,000 requests. Raw JSONL contains query IDs and numeric durations, not query text. The bounded lexical corpus is warm; query embeddings/results are not cached. Use `--records 10000 --queries 200 --runs 1` for the larger stress sample, with provisional tail statistics.

`tests/test_relevance.py` supplies 50 separate synthetic paraphrase cases over five fixture categories. This does not establish clinical retrieval quality on diverse real data.

On macOS, a process-level network-denied verification can run with:

```sh
sandbox-exec -p '(version 1)(allow default)(deny network*)' \
  .venv/bin/python -m pytest -q tests/test_real_edge.py tests/test_relevance.py
```

This denies network access for that test process and its children. It does not alter system-wide connectivity or demonstrate a 30-minute physical-device soak.

## Backup and recovery rehearsal

Finish browser/live mutation tests first. Use a new backup destination:

```sh
uv run python -m edgemed.cli backup --output "$EDGEMED_RUNTIME/backup-check"
uv run python -m edgemed.cli start
uv run python scripts/verify_recovery.py --backup "$EDGEMED_RUNTIME/backup-check"
```

Recovery mounts the backup read-only, uses the original protected Keychain keys, and compares records, revisions, queues and audit history with the unchanged isolated runtime. Do not mutate the test runtime between the backup and comparison. SQLite immutable mode is used only for the closed, checkpointed backup, never for the live store. The image is unmounted in a finally block.

If a key is unavailable, stop and recover the original protected key material; setup refuses to replace keys for an existing database. If a derived shard cannot be loaded, stop services and preserve the encrypted container before repairing/rebuilding the projection. Do not delete the canonical SQLCipher database or claim that file encryption detects every silent vector modification.

## Platform and deferred work

The supplied Snapdragon 720G/8 GB device is assumed to be Android. No device connection or compatible native build is available in this workspace. Running its browser against a 64-bit local server would not prove on-device search. An experimental Linux x86-64/ARM64 LUKS2 launcher and pinned platform assets are available, but a physical-host encrypted-volume and restore rehearsal remains pending. Android native builds, Linux packaging, portable key recovery/rotation, independent security review and distributed rollback protection remain follow-up work. The current release deliberately preserves the plan's synthetic-data and narrow-sharing boundaries.
