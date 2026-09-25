# Unit Testing Specifications

- **Document Version:** 1.0.0
- **Status:** Complete
- **Date:** 2026-09-26

---

## 1. Scope of Unit Tests

Unit tests target isolated algorithmic components without spawning network daemons or mounting full disk shards:
- `test_governor_scoring`: Tests calculation of $G_{\text{score}}$ across corner-case signal vectors. Verifies that $I \ge 0.85$ hard-blocks eviction.
- `test_privacy_firewall`: Verifies regex pattern scrubbing of synthetic names, phone numbers, and SSNs. Confirms `HIGHLY_SENSITIVE` strings are blocked.
- `test_embedding_dimensions`: Asserts that FastEmbed outputs exactly 384-dimensional unit-normalized FP32 vectors.
- `test_rrf_scoring`: Validates reciprocal rank fusion mathematical monotonicity and rank ordering.
- `test_provenance_hashing`: Verifies SHA-256 deterministic digest generation for observation records.
