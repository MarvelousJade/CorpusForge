# Implementation contract and checklist

New isolated repository; parent directory has no usable Git repository and no AGENTS.md or attached instruction files were found. Existing projects untouched. Follow the user's acceptance → implement → test → investigate → fix → verify → diff → commit workflow.

- [x] Ingestion, normalization, deterministic exact dedup, diagnostics
- [x] Seeded MinHash, LSH candidates, verified edges, clustering, oracle tests
- [x] Real Ray Data batch/global-group backend and parity tests
- [x] Atomic stage persistence, fingerprint validation, interruption/resume tests (both backends)
- [x] Reproducible synthetic benchmark, actual measurements
- [x] Architecture, decisions, attribution, interview preparation
- [x] Bug snapshots, regressions and separate fixes (full branch verified; integrated with non-fast-forward history)
- [x] Final checks and diff review

## Increment 1 verification

`python -m pytest tests/test_exact.py -q`: 7 passed (0.20s). Sequential sample CLI exited 0. Tests cover cross-file duplicates, order independence, metadata, empty text, malformed records, duplicate IDs and simulated hash collisions. Staged diff reviewed; no existing project changes included.

## Increment 2 verification

Full suite at this increment: 10 passed (1.43s); sequential near-enabled sample CLI exited 0. Oracle fixture establishes candidate coverage for that fixture only; explicit empty candidates report misses. Threshold equality, short/repetitive text, seed determinism and transitive clusters tested. Reference commit and independent implementation differences recorded in REFERENCES.md. Diff reviewed before commit.

## Recovery investigation

Initial recovery check: 2 failures, 15 passes. Cached JSON edges reload as lists; newly computed edges were tuples. Sorting the mixed representations failed. Normalize all edges to tuples inside survivor selection. Follow-up: 1 failure, 20 passes; on Windows, the second writer's lock-byte read raised PermissionError before lock handling. Replace that read with fstat size inspection. Final targeted check: 22 passed (10.92s), including boundary interrupts, a partial uncommitted stage, changed inputs/configuration, missing/corrupt artifacts, locking and reproducible synthetic generation. Ray integration remains a separate completion gate.

## Increment 4 — Ray verification

First one-CPU fixture stalled: monitor showed 0.01 CPU occupied by control work while a 1-CPU task waited. Stopped that run; reserve one extra runtime CPU while batch/flat-map concurrency remains configured. Actual integration rerun: 4 passed, 4 upstream warnings in 156.42s. Tests compare kept/removed/candidates/verified bytes across sequential/Ray for batch/workers 1/1 and 3/2, exercise a real worker UDF exception, and compare Ray resume with clean. CLI regressions separately: 3 passed in 6.61s. Detailed evidence and ownership are in docs/ENGINEERING_JOURNAL.md.

## Complete baseline verification before learning checkpoints

`python -m pytest tests practice_regressions -q --tb=short`: **36 passed**, 4 upstream Ray warnings, 158.49s. Includes expanded prepared/exact artifact parity, heterogeneous Unicode metadata, Unicode-normalization controls, benchmark isolation regression, CLI diagnostics/recovery, documentation links and all three fixed learning-branch regressions. `pip check`: no broken requirements. `compileall` and `git diff --check`: passed.

Pilot benchmark completed 24 measurements with retained-ID parity, but 8 sequential memory rows included an idle Ray runtime. Raw evidence retained and regression reproduced before fixing loop order. Corrected one-factor benchmark matrix will be published separately; measurements are still a completion gate.

## Learning checkpoint receipts

Passing base `db828f4`. Separate branch `learning/exercises`, worktree `../CorpusForge-learning`; main untouched. Actual targeted failures: partition `0adcd10` (2 rather than 1 survivor, 0.42s), survivor `7b150e6` (z versus a under controlled completion replay, 0.45s), resume `44f21ff` (kept-byte divergence, 0.90s). Each exit 1 was checked; aliases `bug/partition`, `bug/survivor`, `bug/resume` refer to preserved bug snapshots. These issues were introduced on the learning branch separately from working main; no production-incident or personal investigation claims follow. Solutions/evidence are separate from symptoms/hints. Individual fixes verified: `f4542c0` partition check passed (0.36s), `c884149` concurrency check passed (0.31s), all three checks after resume fix `4c8c0c7` passed (1.07s).

Benchmark harness: `119fed4`; learning preparation: `db828f4`. Corrected 48-row benchmark matrix completed with baseline and isolated batch/worker/LSH changes; all retained-ID checks passed. All sequential rows have zero Ray telemetry samples; all Ray rows have valid telemetry/no errors. Raw results and timings published in docs/benchmarks; interpretation/limits in docs/BENCHMARKS.md. New integration instruction: retain bug/fix history and merge only after full corrected-branch checks pass; no unresolved issue may enter main.

## Corrected learning branch gate

`4c8c0c7`: 36 checks passed, 4 upstream warnings, 132.64s. `pip check`, compilation, diff checks and application-source comparison against main passed. Separate fixes `f4542c0`, `c884149`, `4c8c0c7` restore already-correct main behavior. Commit subjects were reworded at the user's explicit request; checkpoint trees, identities, dates and topology were preserved. Current IDs resolve to the same trees previously checked. Original history is backed up locally in `runs/before-message-reword.bundle`, verified by Git; mapping is in `docs/commit-reference-map.json`. Documentation-only follow-up passed (2 checks, 0.12s). Non-fast-forward integration completed (`5ebb70e` after subject reword). Final main sign-off passed: 36 checks, 4 upstream warnings, 131.05s; editable extras install, dependency validation, compilation and diff checks passed. Sequential/Ray sample CLIs both kept 2 and removed 2; kept and removed JSONL files are byte-identical (0.070s sequential, 26.741s Ray).

Contract: IDs are nonempty strings, ordered lexicographically. Metadata must be an object. Unknown fields rejected. Empty normalized strings deduplicate exactly. Original text and metadata are never rewritten. Local prototype with explicit input/record/candidate caps. No claims of production-scale execution or perfect LSH recall.
