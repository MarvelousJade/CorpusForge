# CorpusForge repository instructions

## Development and interview preparation workflow

### Main objective
Build or rework this project primarily as an **interview portfolio project**. Produce a useful, working project that is easy to understand and learn quickly, with concrete examples of problem-solving, technical understanding, and engineering judgment. Prioritize a coherent project Shaoyu can explain confidently. Every major feature must contribute to the purpose or provide a meaningful engineering lesson.

### Project purpose and scope
Before implementing, explain the problem, intended users, value, relevant technical skills, and first-version inclusions/exclusions. Suggest motivation wording to personalize; never invent personal motivation. Choose the smallest architecture supporting one complete useful workflow. Limit features/dependencies so the whole project can be understood before an interview.

For an existing project, inspect code, documentation, tests and Git history. Preserve useful functionality and simplify unnecessary complexity. Rebuild only for a concrete reason.

### Understandable implementation
- Clear module boundaries, descriptive names, straightforward code; familiar patterns over clever abstractions.
- Explain stack concepts where they affect implementation. Add infrastructure only for demonstrated requirements.
- Complete the main end-to-end workflow before supporting features.
- Identify the few files/functions to read to understand the system.
- Explain each major component's purpose, inputs, outputs, dependencies and likely failure cases.

### Incremental development and commits
**Define acceptance → implement one meaningful increment → test → investigate failures → fix → verify → inspect diff → commit.**

Read instructions, inspect Git status, preserve existing user changes, and create a short checklist before work. For rework, use `shaoyu/rework`; inspect it first if it already exists. This repository began as a new implementation on `main`, not a rework; future rework follows that branch rule.

Each increment delivers coherent behavior with relevant tests/docs. Commit incrementally, not only at project completion. Define acceptance before implementation, run appropriate checks and manual smoke tests. Reproduce meaningful bugs and add regression tests before fixing them. Fix uncommitted mistakes before committing; use separate fix commits for previously committed behavior.

Use descriptive messages reflecting actual changes. Never manufacture history, claim unperformed verification, commit secrets/unrelated changes, or push/rewrite history without authorization. Use `Shaoyu <fanshaoyu9@outlook.com>` as the requested commit identity. Commit identity is not evidence of personal investigation. After each increment, report behavior, actual checks and hash.

### Problem-solving journal
Maintain **`docs/engineering-journal.md`** throughout development. Record every encountered bug; keep minor mistakes brief and detail meaningful issues:
- Expected/actual behavior, reproduction, hypotheses and evidence.
- Unsuccessful attempts and why they failed; root cause.
- Fix, alternatives, tradeoffs and remaining limitations.
- Actual tests/measurements, relevant files/tests/commits.
- Lessons and prevention.

For non-bug engineering hurdles record difficulty, constraints/alternatives, evidence guiding decisions, how overcome, verification/tradeoffs/lessons. Favor strong understandable stories over manufactured complexity. Include context and investigation ownership: distinguish implementation-session investigation, Shaoyu's reported personal work, and simulated practice. Do not invent personal learning.

### Debugging exercises
After a verified working baseline, create two or three realistic defects on a separate learning branch. For CorpusForge the original acceptance requires three: cross-partition duplicates, concurrency-sensitive survivors, and resume/clean divergence. Teach important stack concepts with reproducible symptoms and regression tests. Keep explanations/solutions separate; progressive hints should not be presented unsolicited. Label simulated reports, hypothetical consequences and example reasoning as practice. Keep main passing and provenance accurate. Use completed personal investigation notes for personal interview stories; do not wait for learning exercises before finishing authorized implementation.

**Learning integration (newer explicit instruction):** Preserve each faulty checkpoint, reproduce failures, retain regression tests, and fix each defect in a separate commit. Existing explicit baseline-restore commits may serve as exercise fixes if their targeted checks are actually verified. Once the learning branch is corrected and all required checks pass, merge it into main with bug-and-fix history preserved (non-fast-forward merge). Never merge unresolved intentional defects. If main already has equivalent correct behavior, integrate regressions/documentation/useful improvements and explain that the fixes restore that existing behavior. Exercise provenance must remain explicit.

### Evidence and technical decisions
Explain why an approach/technology was selected, simpler/competing alternatives, evidence, gains/sacrifices, and changes needed under different requirements. Use meaningful tests and reproducible measurements. Label local/synthetic evidence. Never invent production usage, customer impact or performance improvements.

### Interview preparation package
Maintain **`docs/interview-guide.md`** as the main quick-study document:
- One sentence, 60-second introduction (problem/solution/stack/strongest result), three-minute workflow walkthrough.
- Users, problem, useful scope, suggested motivation to personalize.
- Small diagram, traced operation, technology rationale, concepts, key files in reading order.
- Three to five sourced stories: **problem → hypothesis → evidence → decision → fix → tradeoff → verification → lesson**. Identify actual issue, design hurdle or practice scenario.
- Concepts taught, what to explain, improvements/reflection, production/scale changes.
- Likely questions with concise answer outlines on scope, architecture, bugs, testing, alternatives and limitations; understanding-testing follow-ups, not jargon memorization.
- Study sequence: purpose/architecture → run demo → read key files → reproduce strongest debugging examples → review decisions/evidence/limits → explain without notes.
- Demonstration script and one-page talking-points summary.

### Completion criteria
Work, pass checks, and use focused commits with reproducible evidence. Documentation must quickly explain purpose/problem, system, stack, bugs/fixes, hurdles, tradeoffs, correctness, personal learning (only where reported), and improvements. Finish authorized implementation without waiting for personal exercise completion. Keep exercises available; report unfinished/unverified work honestly.

### Preserved project-specific contract
Both sequential and **real Ray Data** backends are required. Python/dataclasses/argparse/JSONL/pytest/NumPy; additional dependencies need concrete justification. Preserve original text/metadata; normalize comparisons separately. Unique string IDs, file/line errors, stable hashes and content verification, seeded MinHash, global LSH candidates, exact Jaccard, deterministic components. Explicit local limits, stage manifests/checksums/resume, actual benchmarks and reference/license attribution are completion gates. Text curation only; no image/video scope creep. Original implementation checklist/evidence: `WORKLOG.md`.

### Conflicts and resolutions (explicit)
1. Earlier journal path: `docs/ENGINEERING_JOURNAL.md`; newer request: `docs/engineering-journal.md`. Canonical content is the newer path; the earlier file remains a compatibility link, with no entries discarded.
2. Existing study draft: `docs/INTERVIEW.md`; newer requested package: `docs/interview-guide.md`. Canonical package is the newer path; retain a link at the former path.
3. The earlier wording restriction and newer honest-investigation-ownership requirement must both be respected. Use neutral “implementation session” versus “Shaoyu's reported personal investigation”; never imply commit authorship proves personal work. No personal contribution/learning claims without supplied notes.
4. Original request explicitly asks for separate progressive hints/solutions; newer rule says hints when requested. Store separate spoiler files, but do not present their content unless requested.
5. Original workflow commits new implementation on main; newer `shaoyu/rework` rule applies to future rework, not retroactive rewriting of this new-project history. No further history rewrite/push is authorized by this file.
6. Earlier exercise instructions said never merge the learning branch. The newer explicit learning-integration request supersedes permanent isolation: merge only a corrected, fully checked final state, retaining bug snapshots and bug/fix history. This is not authorization to merge unresolved defects.
7. The newer learning-package presentation request uses neutral “Bug”/“Fix” headings. Keep a brief accurate note that issues originated separately on the learning branch and restore existing main behavior. Do not imply production incidents or unreported personal work. Historical commands, file identifiers and commit messages remain unchanged for reproducibility; neutral tag aliases may be added without rewriting history.
