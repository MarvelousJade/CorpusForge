# Architecture and limits

A document is validated with its file/line on the coordinator. Text and metadata remain unchanged. Both backends prepare a separate normalized text, SHA-256 digest, shingle set and seeded MinHash vector. Exact hash groups compare the full normalized string and select the smallest ID. Only their representatives enter LSH. Every band's index and vector form a global key. Matching bands propose canonical `(smaller ID, larger ID)` pairs. Exact Jaccard rejects false positives. Union-find joins verified edges and exact aliases, rooting every component at the smallest ID. `removed.jsonl` points to that final survivor, including when its immediate exact representative was later removed by a near edge.

## Modules
- `core.py`: configuration, strict records, normalization, exact groups, union-find, decisions
- `near.py`: shingling, seeded signatures, bands, candidates, Jaccard, exhaustive oracle
- `ray_backend.py`: Ray Data read_text, map_batches, global digest groups, flat_map band records, global band groups
- `pipeline.py`: stage orchestration and bounded coordinator verification/clustering
- `persistence.py`: fingerprints, stage checksums, atomic writes and single-writer lock
- `benchmark.py`: synthetic generator and measurement harness

Ray reads original JSONL lines as text and decodes in batch UDFs, avoiding Arrow coercion of heterogeneous metadata. Coordinator validation reads the same files first to retain useful source/line diagnostics and reject duplicate IDs globally. This double read and collecting prepared rows are deliberate local-prototype compromises. Global groupby crosses input files and Ray blocks; no per-partition dedup shortcut. Pair emission is lazy, with per-band and global candidate caps. Verified edges and components remain in one coordinator process. Limits (defaults): 50 MB input, 10,000 documents, 100,000 text characters per document, 200,000 unique candidates; LSH expansion is documents × bands. Large hot buckets can still consume substantial group memory before pair rejection. These are bounds, not a production memory guarantee.

## Persistence
`manifest.json` records input paths, byte sizes and SHA-256 fingerprints, configuration (including seed), package versions, backend and logical round-robin file assignments. Ray physical block scheduling is runtime-managed, not inferred from those assignments. Changing workers/batch size is allowed in a **new** run and must preserve decisions; it invalidates **resume** to keep compatibility strict.

Stages: prepared → exact → candidates → verified → decisions → output. Each JSON checkpoint is finalized by replace before its checksum and completion entry are atomically written. Output completion is marked only after kept/removed/report are finalized. Resume validates **all** completed artifacts, then reuses compatible stages. A stage without completion is rerun, replacing any orphan artifacts. No automatic per-task Ray recovery is promised; Ray worker errors propagate with stage context. Single-writer OS locks release on process exit; the lock file is harmless. This assumes a local filesystem with atomic replace and stable input files, not object storage or power-loss-proof directory syncing.

Use `--stop-after candidates` for reproducible boundary interruption; rerun with identical flags plus `--resume` and without `--stop-after`. Reports retain original completed-stage timings; resumed end-to-end timing measures only that invocation. A fully completed resume returns the existing report unchanged. Outputs/decisions are deterministic; timing fields are not.

No language detection, semantic embeddings, image/video, remote ingestion, spam classification, distributed clustering or arbitrary task-level recovery.
