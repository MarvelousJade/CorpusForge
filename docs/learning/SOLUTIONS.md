# Practice solutions — spoilers

These are deliberately planted defects, not production incidents or personal investigation claims. Implementation-session construction knows the patches; it does not pretend to be a blind debugging exercise. Baseline regressions currently pass (3 tests); faulty checkpoint verification is pending creation. Final receipts will be published here on `main`; use `git show main:docs/learning/SOLUTIONS.md` from a frozen practice checkpoint.

## Partition boundary
Problem → equivalent content across shards survives.
Hypothesis/check → compare candidate key scope before full equality verification.
Planted cause → include a per-record partition alongside the digest in the exact-group key.
Fix → digest groups must be global; partitioning only schedules work. Confirm normalized content within the global group.
Tradeoff → shuffle/coordination rather than partition-local independence.
Regression → `test_cross_partition`: one minimum-ID survivor despite two logical partitions.
Lesson → local correctness is not global correctness.

## Concurrency-sensitive survivor
Problem → different completion order chooses different IDs.
Hypothesis/check → replay identical group contents in different arrival orders; isolate representative selection.
Planted cause → take `ids[0]` instead of `min(ids)` in exact groups.
Fix → deterministic minimum ID and canonical group edges, independent of scheduling.
Tradeoff → compare IDs rather than exploit “first wins”; sorting output adds some cost but makes audit/reproducibility straightforward.
Regression → `test_survivor_concurrency` uses one/two real thread workers and a controlled delay to replay completion order. This is not a Ray performance experiment.
Lesson → asynchronous completion order is not a stable identity policy.

## Resume/clean divergence
Problem → interrupted exact-only run retains extra documents on resume.
Hypothesis/check → compare loaded exact edges with the completed checkpoint and clean stage result.
Planted cause → return an empty list for a completed exact stage while still trusting its completion entry.
Fix → load the actual validated checkpoint; a completion marker skips computation, not the result's semantics.
Tradeoff → checkpoint decoding/validation costs versus correctness; interrupted stages still recompute entirely.
Regression → `test_resume_matches_clean` interrupts after exact and compares final kept bytes.
Lesson → test transitions through persistence and recovery, not just final uninterrupted results.

## Investigation ownership
The supplied hypotheses/diagnoses are explanations of deliberately constructed scenarios. Shaoyu's own investigation notes have not been supplied; personal interview stories should later use those notes. Main's actual development stories are separately sourced from `docs/engineering-journal.md`.
