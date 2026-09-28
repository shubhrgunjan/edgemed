# Development roadmap

EdgeMed currently supports **synthetic-data demonstrations only**. These tasks are proposed next steps, not claims of production or clinical readiness. Complete security and data-governance gates before testing with real patient information.

## P0 — trust and deployment foundations

- [ ] Commission an independent threat model, penetration test, dependency review, and privacy assessment. Fix findings and repeat the review after material changes.
- [ ] Define permitted data, retention, deletion, audit, consent, and incident-response policies with a clinical organization. Keep real patient data out until formal approval.
- [ ] Replace demo account provisioning with a hospital identity provider, least-privilege roles, stronger session controls, account recovery, and an emergency-access process with audited review.
- [ ] Design portable, recoverable encryption keys with rotation, device replacement, cold restore, and tested disaster recovery; address whole-volume rollback detection.
- [ ] Create a supported hospital-local server deployment with OS hardening, hospital-managed TLS, network segmentation, monitored backups, logging without sensitive content, and documented update/rollback procedures.
- [ ] Decide availability targets and design a redundant server/failover path. Test power, disk, LAN, and server failure rather than assuming a single Mac is sufficient.
- [ ] Publish a data-flow diagram and test that no private note, embedding, credential, or search query leaves the intended trust boundary.

## P1 — usable multi-device product

- [ ] Build an **Android app** after deciding its offline requirement: a secure browser client for hospital-LAN access, or an actual on-device encrypted backend that continues working when the LAN fails. Treat those as different products and test the Snapdragon 720G/8 GB target.
- [ ] Add a verified physical-phone browser rehearsal: install and validate the demo CA or hospital certificate, check responsive workflows, then remove demo trust material.
- [ ] Package the server and frontend with reproducible, signed releases and a guided install/update process for operators.
- [ ] Extend staff workflow: explicit patient/subject linkage rules, review queues, error correction, scoped deletion and retention, and clear offline/sync status.
- [ ] Define a safe data migration and sync protocol for any Android offline backend, including conflict handling, revocation, replay defense, and lost-device response.

## P2 — evidence and scale

- [ ] Validate retrieval quality on a diverse, held-out, ethically sourced dataset with clinician review; measure harmful misses, false positives, subgroup behavior, and explainability.
- [ ] Improve the 10,000-record query path and rerun latency/resource tests on the intended hospital server and low-power target.
- [ ] Run long soak, backup/restore, outage, update, and browser compatibility tests across supported systems.
- [ ] Reconcile architectural design documents, OpenAPI, schemas, and implementation as features graduate from research concepts to supported behavior.

See [current implementation status](docs/PROJECT_STATUS.md) and [measured limitations](docs/next-phase-results.md) before selecting a milestone.
