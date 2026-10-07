# Bugs — symptoms and reproduction

These issues were introduced on a separate learning branch after validating a working baseline (`db828f4`). They were not defects discovered on main. Fixes restore behavior already present there. Historical bug snapshots remain available; only the corrected, fully checked branch state is eligible for integration.

Use a separate worktree and the main repository's virtualenv by absolute path. A `CorpusForge-learning` worktree already exists. For another:

```sh
git worktree add --detach ../CorpusForge-debug bug/partition
```

Select snapshots with `git switch --detach bug/partition`, `bug/survivor`, or `bug/resume`. Fixed snapshots use `fix/partition`, `fix/survivor`, and `fix/resume` once verified. Checkpoint trees remain unchanged. Commit subjects were reworded at the user's explicit request; current IDs and the old/new mapping are recorded in `docs/commit-reference-map.json`.

## Bug 1: duplicates survive partition boundaries
Expected: equivalent normalized content across two shards retains one ID. Actual: two IDs survive. At `bug/partition`, run:
```sh
python -m pytest -o testpaths=. -k cross_partition -q
```
Compare same-shard and cross-shard inputs; record what changes.

## Bug 2: survivor changes with concurrency
Expected: minimum-ID survivor regardless of completion order. Actual: a controlled two-worker replay chooses a different survivor from one worker. At `bug/survivor`, run:
```sh
python -m pytest -o testpaths=. -k survivor_concurrency -q
```
The harness controls timing; this is not a claim about a particular Ray scheduler order.

## Bug 3: resumed output differs from clean
Expected: completed exact checkpoint survives resume. Actual: interrupted/resumed exact-only execution retains extra IDs. At `bug/resume`, run:
```sh
python -m pytest -o testpaths=. -k resume_matches_clean -q
```

Write problem → hypothesis → evidence → decision → fix → verification before opening `HINTS.md` or `SOLUTIONS.md`. Current fix evidence is on main; from a frozen snapshot, use `git show main:docs/learning/SOLUTIONS.md`. Preserve the bug snapshots when making your own fix branch.
