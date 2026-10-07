# Fixes — diagnoses and verification

These issues originated on the learning branch, constructed separately from working main. Main already contained equivalent correct behavior. Commit identity does not establish personal investigation; no personal debugging by Shaoyu has been reported. Current evidence is available with `git show main:docs/learning/SOLUTIONS.md` from an older snapshot.

Passing base: `db828f4` (36 checks passed in 158.49s). Each bug snapshot genuinely failed its targeted regression with exit 1:

| Bug alias | Commit | Observed failure | Separate restoring/fix commit |
|---|---|---|---|
| `bug/partition` | `0adcd10` | Two survivors (`d0`, `d2`) instead of one; 0.42s | `f4542c0` |
| `bug/survivor` | `7b150e6` | One-worker replay chose `z`, two-worker replay chose `a`; 0.45s | `c884149` |
| `bug/resume` | `44f21ff` | Resumed kept bytes differ from clean; 0.90s | `4c8c0c7` |

The first two restoring commits returned to the working baseline before the next issue was introduced. At the user's explicit request, subjects were reworded to functional descriptions; trees, identities, dates and bug/fix topology are unchanged. IDs in this document are current aliases for the identical trees originally verified. The old/new mapping is in `docs/commit-reference-map.json`. The branch must pass all required checks before authorized non-fast-forward integration. This preserves history without leaving a broken final state on main.

## Fix 1: global equality groups
**Problem:** Equivalent content across shards survives.
**Check/evidence:** Compare candidate keys before normalized-content verification; the faulty key includes partition plus digest.
**Root cause:** Partitioning incorrectly scopes equality.
**Fix:** Group globally by digest, then verify normalized content. Partitioning schedules work only.
**Tradeoff:** Global shuffle/coordination rather than shard independence.
**Verification:** `cross_partition` regression; historical restoring commit `f4542c0`: passed in 0.36s.
**Lesson:** Local correctness is not global correctness.

## Fix 2: deterministic survivor
**Problem:** Completion order changes selected IDs.
**Check/evidence:** Replay identical group contents with one/two thread workers; first-arrival selection yields `z` versus `a`.
**Root cause:** `ids[0]` was used instead of minimum ID.
**Fix:** Select `min(ids)` and canonicalize group edges, independent of scheduling.
**Tradeoff:** ID comparisons/output ordering rather than first-arrival shortcuts.
**Verification:** `survivor_concurrency` regression; historical restoring commit `c884149`: passed in 0.31s.
**Lesson:** Completion order is not a stable identity policy.

## Fix 3: preserve completed-stage semantics
**Problem:** Resume retains extra documents.
**Check/evidence:** Compare loaded exact edges, the completed checkpoint and clean output; the loader returned an empty list.
**Root cause:** Completion skipped computation and discarded its result.
**Fix:** Load the actual validated checkpoint. A completion entry skips computation, not meaning.
**Tradeoff:** Decoding/checksum costs; interrupted stages still rerun entirely.
**Verification:** `resume_matches_clean` regression; all three regressions pass in the corrected worktree (1.07s). Corrected branch at `4c8c0c7`: 36 checks passed in 132.64s, dependency/compilation/diff checks passed, and application sources equal main. The final integration remains a non-fast-forward merge with history preserved.
**Lesson:** Verify persistence transitions, not just uninterrupted execution.

## Investigation ownership
These diagnoses follow known learning-branch changes and actual reproduced outcomes; they do not claim a blind investigation or production impact. Use your own completed investigation notes for personal interview stories. Main's development issues are independently recorded in `docs/engineering-journal.md`.
