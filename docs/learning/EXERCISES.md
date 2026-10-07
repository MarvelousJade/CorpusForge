# Practice scenarios — symptoms only

These deliberately faulty checkpoints are separate from passing `main`. They are learning material, not production incidents. Branch/checkpoint creation is a completion gate: check WORKLOG for whether checkpoints have actually been created.

Use a separate worktree and the main repository's virtualenv (an editable install should not be used while switching worktrees; run from the worktree so its package is imported). Keep your investigation notes before opening hints or solutions.

```sh
git worktree add ../CorpusForge-practice learning/exercises
# In that worktree, use the absolute path to the main .venv Python:
python -m pytest practice_regressions/test_scenarios.py -q
```

Select one faulty checkpoint at a time with `git switch --detach practice/partition`, `practice/survivor`, or `practice/resume`. The checkpoints each isolate one defect; the learning branch tip is the resume scenario. Never merge them into main.

## Scenario 1: duplicates survive partition boundaries
Expected: a two-shard input containing equivalent normalized content retains one ID. Symptom: two IDs survive. Reproduce: `python -m pytest practice_regressions/test_scenarios.py::test_cross_partition -q` at `practice/partition`. Compare same-partition and cross-partition inputs; record what changes.

## Scenario 2: survivor changes with concurrency
Expected: minimum-ID survivor regardless of completion order. Symptom: a controlled two-worker completion-order replay chooses a different survivor from one worker. Reproduce: `python -m pytest practice_regressions/test_scenarios.py::test_survivor_concurrency -q` at `practice/survivor`. This harness deliberately controls timing; it is not a claim about any particular Ray scheduler order.

## Scenario 3: resumed output differs from clean
Expected: completed exact checkpoint survives resume. Symptom: interrupted/resumed exact-only run retains more IDs than a clean run. Reproduce: `python -m pytest practice_regressions/test_scenarios.py::test_resume_matches_clean -q` at `practice/resume`.

Write: problem → hypothesis → evidence → decision → fix → verification. `HINTS.md`, `SOLUTIONS.md`, and `practice_regressions/` are separate spoiler material. Your personal notes should be distinct from supplied investigation notes.
