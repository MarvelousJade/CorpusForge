# Reference provenance

DataTrove reference commit: `1977fbb0f3c163d43cace334b073dda17fa3ef26` (resolved with `git ls-remote … HEAD` during implementation).

Consulted at that commit:
- https://github.com/huggingface/datatrove/blob/1977fbb0f3c163d43cace334b073dda17fa3ef26/README.md
- https://github.com/huggingface/datatrove/blob/1977fbb0f3c163d43cace334b073dda17fa3ef26/examples/minhash_deduplication.py
- https://github.com/huggingface/datatrove/blob/1977fbb0f3c163d43cace334b073dda17fa3ef26/src/datatrove/pipeline/dedup/minhash.py

Inspiration: id/text/metadata document model; backend-independent steps; signature → bucket → cluster → filter organization; seeded NumPy affine hashes. CorpusForge is independently implemented, with SHA-256, a 32-bit prime field (not DataTrove's 61-bit arithmetic), exact Jaccard verification, and whole-stage JSON checkpoints. No DataTrove source was copied or adapted line-for-line, and no dependency on DataTrove is included. DataTrove is Apache-2.0 licensed; its code and copyright notices remain with the upstream project. If copying upstream code in future, preserve its license and applicable notices and mark modifications.

Ray guides consulted (live latest documentation; executable dependency pinned separately):
- https://docs.ray.io/en/latest/data/transforming-data.html — lazy execution, map_batches, flat_map, global groupby/map_groups, ordering
- https://docs.ray.io/en/latest/data/performance-tips.html — batching, concurrency and object-store tradeoffs

Ray documentation can move ahead of the pinned version. Integration tests, not documentation alone, establish compatibility.
