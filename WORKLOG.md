# Implementation contract and checklist

New isolated repository; parent directory has no usable Git repository and no AGENTS.md or attached instruction files were found. Existing projects untouched. Follow the user's acceptance → implement → test → investigate → fix → verify → diff → commit workflow.

- [x] Ingestion, normalization, deterministic exact dedup, diagnostics
- [x] Seeded MinHash, LSH candidates, verified edges, clustering, oracle tests
- [ ] Real Ray Data batch/global-group backend and parity tests
- [ ] Atomic stage persistence, fingerprint validation, interruption/resume tests
- [ ] Reproducible synthetic benchmark, actual measurements
- [ ] Architecture, decisions, attribution, interview preparation
- [ ] Separate learning branch/checkpoints; investigate and record evidence
- [ ] Final checks and diff review

## Increment 1 verification

`python -m pytest tests/test_exact.py -q`: 7 passed (0.20s). Sequential sample CLI exited 0. Tests cover cross-file duplicates, order independence, metadata, empty text, malformed records, duplicate IDs and simulated hash collisions. Staged diff reviewed; no existing project changes included.

## Increment 2 verification

Full suite at this increment: 10 passed (1.43s); sequential near-enabled sample CLI exited 0. Oracle fixture establishes candidate coverage for that fixture only; explicit empty candidates report misses. Threshold equality, short/repetitive text, seed determinism and transitive clusters tested. Reference commit and independent implementation differences recorded in REFERENCES.md. Diff reviewed before commit.

Contract: IDs are nonempty strings, ordered lexicographically. Metadata must be an object. Unknown fields rejected. Empty normalized strings deduplicate exactly. Original text and metadata are never rewritten. Local prototype with explicit input/record/candidate caps. No claims of production-scale execution or perfect LSH recall.
