# System Configuration Specification

- **Document Version:** 1.0.0
- **Status:** Complete / Configuration Contract
- **Date:** 2026-09-26

---

## 1. Environment Configuration Variables

The system is configured entirely via environment variables (backed by `.env` file support in Pydantic Settings):

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `EDGEMED_DATA_DIR` | `./data` | Base local storage directory on edge disk. |
| `EDGEMED_QDRANT_EDGE_DIR` | `./data/qdrant_edge` | Filesystem path for Qdrant Edge shards. |
| `EDGEMED_SQLITE_PATH` | `./data/edgemed.sqlite` | SQLite database file path. |
| `EDGEMED_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | FastEmbed ONNX model identifier. |
| `EDGEMED_CLOUD_URL` | `http://localhost:6333` | Central Qdrant Server endpoint. |
| `EDGEMED_CLOUD_API_KEY` | `""` | Optional mTLS / API key for server. |
| `EDGEMED_SYNC_BATCH_SIZE` | `10` | Number of points per sync micro-batch. |
| `EDGEMED_DEVICE_ID` | `node_ryzen5_dev` | Physical device identifier string. |
| `EDGEMED_FACILITY_ID` | `field_clinic_alpha` | Operational facility namespace. |
| `EDGEMED_DEFAULT_PRIVACY` | `SENSITIVE` | Default privacy tier for new notes. |
