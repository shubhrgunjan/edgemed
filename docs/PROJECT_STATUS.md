# EdgeMed implementation status

Updated 28 September 2026. The initial architecture-only phase is complete; this page describes the implemented synthetic-data prototype. The original requirements and architectural decisions remain under `docs/` and `architecture/` as design references, and not every proposed component exists in code.

| Area | Status |
| --- | --- |
| macOS ARM64 encrypted local backend and semantic retrieval | Implemented and tested with synthetic data. |
| macOS Intel and Linux x86-64/ARM64 launcher paths | Native assets pinned and portable checks added; physical encrypted-host rehearsals remain pending. |
| Browser interface, staff workspaces, and private-LAN HTTPS demo | Implemented and locally verified. |
| Reviewed synthetic reference synchronization | Implemented for the demo; staff observations remain local. |
| Public browser sample | Static, synthetic, and intentionally separate from the local backend. |
| Native Android app/backend, production hospital deployment, real patient data | Not implemented or approved. |

See the [installation guide](installation.md), [measured next-phase results](next-phase-results.md), [hospital LAN verification](hospital-lan-results.md), and [roadmap](../TODO.md) for exact scope, commands, and remaining work. In particular, a phone browser connected to a Mac is not an on-phone backend, and benchmark results from synthetic data are not clinical validation.
