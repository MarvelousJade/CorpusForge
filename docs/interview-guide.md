# CorpusForge interview guide

## Purpose and motivation
**One sentence:** CorpusForge curates small text datasets with verified exact/near deduplication, deterministic decisions, and interchangeable sequential/Ray Data execution.

**Who/why:** Developers exploring training-data preparation or text-corpus hygiene need to remove redundant examples without losing original text or provenance. Duplicate-heavy datasets waste processing/storage and can overrepresent repeated content. This prototype makes decisions inspectable before attempting scale.

**Motivation to personalize:** “I wanted to understand how scalable text-deduplication pipelines balance approximate search, correctness and reproducibility, so I built a bounded version I could inspect end to end.” Use only if it reflects your actual motivation.

**Scope:** JSONL ingestion, configurable comparison normalization, exact dedup, verified MinHash/LSH near dedup, sequential/Ray parity, stage recovery and synthetic experiments. Excludes semantic similarity, image/video, language-aware tokenization, spam filtering, cloud ingestion and distributed clustering.

## 60-second introduction
“CorpusForge is a small Python text-curation tool inspired by DataTrove. It preserves original documents while comparing configurable normalized copies. Exact deduplication uses stable hashes plus content verification. Near deduplication uses word shingles, seeded MinHash signatures and LSH to propose pairs, exact Jaccard to verify them, and deterministic connected components to choose survivors. The sequential and Ray Data backends share comparison functions. Ray handles batches and global grouping; a bounded coordinator verifies edges and clusters. Checksummed stage manifests make compatible runs resumable. The strongest verified result is backend-identical decisions under different batch and worker settings, plus resume/clean parity. Benchmarks are local/synthetic evidence, not proof that parallelism always helps.”

The implementation uses NumPy for its affine hash vectors. Do not claim personal debugging or learning you have not performed. Add measured benchmark figures only after reading the published results.

## Three-minute walkthrough
- **0:00–0:40 Contract:** show one record, source/line diagnostics and duplicate-ID rejection. Metadata and original text survive.
- **0:40–1:10 Exact:** normalize a comparison copy, SHA-256 for candidates, full equality to defeat collisions, minimum-ID representative globally across files.
- **1:10–1:50 Near:** whitespace word shingles become a set; seeded signatures are divided into bands. Collisions propose canonical pairs; exact Jaccard verifies. Draw A–B–C to explain transitive components and LSH misses.
- **1:50–2:25 Ray:** show read_text, map_batches, digest groupby, band flat_map/groupby, bounded coordinator. Completion order cannot control minimum-ID selection.
- **2:25–3:00 Recovery/evidence:** show fingerprints, finalized artifacts, completion entries. Interrupted stages rerun. Contrast actual cold/warm timings; explain startup and global-group overhead rather than promising speedups.

## Architecture and traced operation
```text
JSONL files → strict source/line validation
                  ↓
 sequential loops OR Ray Data batches/global groups
                  ↓
 normalize copy → SHA-256 + equality → exact representatives
                  ↓
 shingles → seeded MinHash → global LSH-band pairs
                  ↓
 exact Jaccard → bounded coordinator union-find
                  ↓
 minimum-ID survivors → original kept/removed JSONL + report

Every completed stage → atomic artifact → checksum → manifest
```

Example: `z` is a formatting variant of `a`. Their normalized strings and digest match; content verification joins them and `a` represents that group. If `a` and `b` share a band and pass Jaccard, their components join. Final minimum ID is retained; `z`'s removal says `exact`, points to the final survivor, and includes its unchanged original document. A near representative's removal says `near`. If no candidate band matches, similarity alone cannot remove a document: the oracle can report this miss on small corpora.

### Stack rationale
- **Python/dataclasses:** readable configuration and pure functions; no service/ORM required.
- **argparse/JSONL:** standard-library CLI and auditable records; no web application scope.
- **SHA-256:** stable across processes; equality verification, not cryptographic probability alone, authorizes exact deletion.
- **NumPy:** seeded affine MinHash vectors; a 32-bit prime field avoids uint64 overflow. It is approximate, not a semantic embedding.
- **Ray Data:** actual parallel batches and global grouped transformations; costs include startup, serialization/shuffle and hot-key memory.
- **pytest:** small oracles, parity fixtures, fault injection, corruption checks and worker errors.
- **psutil/grpcio:** concrete benchmark telemetry needs: sampled process RSS and raylet object-store stats. RPC instrumentation uses a pinned private API only in the benchmark module.

### Read these files in order
1. `core.py`: `Config`, `ingest`, `normalize`, `exact_group`, `survivors`, `outputs`.
2. `near.py`: `shingles`, `signature`, `band_keys`, `candidates`, `verify`, `oracle`.
3. `pipeline.py`: `run`, `_run`, nested `stage` orchestration.
4. `ray_backend.py`: `compute_batch`, `exact_data`, `candidate_data`, `bounded_pairs`.
5. `persistence.py`: `Store`, `atomic`, `output_lock`.
6. Tests and published benchmark summary; then `benchmark.py` if investigating performance.

Paths above are under `corpusforge/`. Component input/output/dependency/failure reference: [architecture](ARCHITECTURE.md).

## Evidence-based problem-solving stories
These are implementation-session evidence, **not personal stories attributed to Shaoyu**. Full reproductions/commits: [journal](engineering-journal.md). Personal stories should later use your own completed notes.

1. **Actual development issue: checkpoint sequence types.** Problem: resumed clustering failed. Hypothesis: JSON changes Python types. Evidence: cached lists plus new tuples fail in sorting. Decision/fix: canonicalize edges inside shared clustering. Tradeoff: O(E) conversion. Verification: all boundary resumes pass in targeted 22-test run. Lesson: test serialization boundaries, not only pure functions.
2. **Actual development issue: Windows locks.** Problem: second writer raised raw PermissionError. Hypothesis: error precedes lock acquisition. Evidence: traceback at lock-byte read. Decision/fix: use fstat instead of reading the locked byte. Tradeoff: explicit platform branches/local filesystem assumptions. Verification: nested writer rejection and recovery tests pass. Lesson: OS lock semantics differ; test the target platform.
3. **Actual development issue: Ray scheduling headroom.** Problem: tiny fixture stalled. Initial startup hypothesis was rejected by a healthy active node. Evidence: 0.01/1 CPU used and a pending 1-CPU task. Decision/fix: allocate workers+1 runtime CPUs for control headroom. Tradeoff: requested compute concurrency and runtime allocation differ. Verification: 4 real Ray tests passed in 156.42s. Lesson: distinguish schedulability from workload speed; inspect resource demand.
4. **Design hurdle: LSH quality versus workload.** Problem: exhaustive comparisons are quadratic. Hypothesis: probabilistic candidates plus exact verification give a useful bounded workflow. Evidence: exhaustive small-fixture oracle, threshold and transitive tests; runtime misses explicitly counted. Decision/fix: seeded bands and exact Jaccard, abort on caps. Tradeoff: verification fixes false positives, not missed candidates. Lesson: correctness claims must separate retrieval from verification.
5. **Design hurdle: trustworthy telemetry.** Problem: logical resource capacity is not object-store usage. Evidence: installed Ray code exposes raylet used-byte stats. Decision/fix: RPC sampling, errors/nulls rather than fabricated zero. Tradeoff: private-version-sensitive API and sampled peaks. Verification: see actual benchmark report, not a prospective claim. Lesson: define exactly what a metric measures.

Separate planted practice scenarios: [exercises](learning/EXERCISES.md). Their outcomes are learning evidence, not production incidents.

## Questions and concise answer outlines
| Question | Answer outline / follow-up |
|---|---|
| Why this project/scope? | One auditable text-curation workflow. Why not embeddings or cloud deployment? They add a different problem before correctness is established. |
| What does MinHash estimate? | Set Jaccard via minimum values under seeded hash permutations. Why are repeated tokens collapsed? Shingles are a set, not counts. |
| Why not Python hash? | Process-randomized; persistent comparisons need stable hashes. Is a stable hash enough to delete? No, compare normalized content. |
| How do bands and rows affect recall? | Ideal candidate probability `1-(1-s^r)^b`; more bands/fewer rows usually increase recall and candidate cost. What assumptions might fail? Independence/ideal permutations. |
| Why exact verification? | Reject candidate false positives. Can it recover misses? No; compare against an oracle to measure retrieval quality. |
| What happens to short/empty text? | No shingles means exact-only; normalized empty strings share an exact group. |
| Why can A/C share a survivor below threshold? | Connected components are transitive. Would all-pairs cluster verification change behavior/cost? Yes, stricter and potentially quadratic. |
| Why global groups? | Partitions schedule work; equality/LSH equivalence spans the corpus. A batch is not a deduplication boundary. |
| Why deterministic IDs? | Sorted/canonical edges and minimum roots; no arrival-order choices. Test changed batch/worker counts. |
| What does resume guarantee? | Compatible checksummed completed stages reused; incomplete stages rerun. What if an artifact is missing? Reject, do not silently trust completion. |
| Why Ray can be slower? | Startup, JSON transport, shuffle, driver collections and persistence dominate small workloads. What experiment would support larger-scale claims? Larger bounded corpora with repeated warm/cold runs and memory measurements. |
| Main bottleneck? | Driver verification/components and hot band groups. How to scale? Distributed edges/components, stronger memory limits, partitioned artifacts; revalidate recovery/determinism. |
| What did you personally learn? | Answer only from your study/investigation notes; the supplied implementation journal is not your personal experience. |

## Learning and reflection
Explain the distinction between data preservation and comparison normalization; stable hashing versus equality; probabilistic retrieval versus verified similarity; global grouping versus local partitioning; deterministic decisions versus deterministic timings; stage versus task recovery. Improvements: language-aware tokenization, fewer JSON copies, cached signature parameters, stronger resource budgeting, explicit external-runtime validation, distributed clustering and genuine-corpus threshold studies. Production adds versioned schemas, remote storage semantics, observability, security/data-governance review and robust scale tests—not simply a larger worker count.

## Quick preparation plan and demonstration
1. Read purpose/diagram and state scope without notes.
2. Run both backends and inspect original versus removed records.
3. Read the six files in order and trace one ID.
4. Reproduce the real regression tests; later investigate practice tags before spoilers.
5. Read decisions, journal, measured benchmarks and limitations.
6. Practice 60-second/three-minute explanations, then answer follow-ups without jargon.

**Demo (fresh output paths):**
```sh
python -m pytest -q
python -m corpusforge run --input data/sample --output runs/interview-seq --backend sequential
python -m corpusforge run --input data/sample --output runs/interview-ray --backend ray
python -m corpusforge run --input data/sample --output runs/interview-resume --stop-after candidates
# Intentional interruption exits 2:
python -m corpusforge run --input data/sample --output runs/interview-resume --resume
python -m pytest practice_regressions -q
```
Show identical kept/removed artifacts (not timing fields), manifest checksums and oracle misses. Show the published benchmark command/results, including slowdowns. No new benchmark numbers should be improvised during the interview.

## One-page talking points
- **Problem:** redundant text; preserve originals/provenance and make decisions inspectable.
- **Workflow:** normalize copy → verified exact groups → shingles/MinHash → LSH → Jaccard → components → minimum ID.
- **Correctness:** global groups, stable seeds/hashes, collision verification, batch/worker parity, resume/clean parity.
- **Recovery:** atomic stage artifacts then completion; fingerprints/config/software checks; interrupted stage reruns.
- **Three real bugs:** JSON tuple/list boundary; Windows lock read; fractional Ray CPU reservation.
- **Tradeoffs:** casefold can erase meaning; LSH misses; transitive groups; Ray overhead; driver/hot-bucket memory limits.
- **Evidence:** actual tests and local synthetic measurements; no production-user/impact claims.
- **Personal contribution/learning:** use only your own completed notes. Separate supplied development evidence and planted exercises.
- **Next:** language-aware comparisons and better memory/coordination only after measuring need. No image/video scope creep.
