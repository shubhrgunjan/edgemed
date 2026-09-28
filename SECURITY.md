# EdgeMed security scope

EdgeMed is a **synthetic-data research prototype**. Do not enter real patient information, credentials from a clinical system, or other regulated data. It has not had an independent security audit or clinical validation and is not approved for medical use.

## Implemented boundaries

- The macOS launcher requires an encrypted sparsebundle and stores application secrets in the macOS Keychain. On Linux, the experimental launcher refuses to start unless its vault is an exact, private LUKS2 mount backed by the configured mapper; it also requires an unlocked system Secret Service or KWallet keyring. It does not select a plaintext keyring backend.
- The canonical SQLite store uses SQLCipher. The local vector index, TLS materials, configuration, and logs live inside the verified encrypted volume. Runtime search uses verified, pinned local model assets and makes no model download request.
- API authentication, CSRF/origin checks, session expiry, server-side workspace scoping, and personal-record scoping are covered by tests. Only reviewed synthetic reference variants enter the optional sync queue; staff observations do not.
- Private-LAN access is explicit: the operator provisions a certificate for one private IP, and only Edge A can bind there. Other services remain on loopback. A firewall and trusted client certificate store are still operator responsibilities.
- The public browser demo is static and separate. It has no backend, account, or persistent note storage; notes added there vanish on refresh. It is unsuitable for sensitive data.

## Known limits

The Linux path has automated native-asset and fail-closed tests, but still needs a physical encrypted-host rehearsal, outage test, and recovery test. On Linux, the operator must stop services and unmount the LUKS volume with system tooling; the macOS `lock` and cold-backup commands do not apply. The current key management lacks a portable recovery/rotation workflow, and an unlocked host can read its mounted vault. There is no whole-volume rollback protection, high availability, hospital identity-provider integration, emergency access workflow, or verified clinical safety process. See the [roadmap](TODO.md).

## Reporting a vulnerability

Contact the repository maintainers privately with reproduction steps, affected version, and impact. Do not publish exploit details in a public issue before maintainers can investigate. Avoid including real patient data in any report.
