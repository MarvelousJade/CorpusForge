# Learning branch fixes

These issues were introduced on the learning branch, separately from working main; they are not production incidents. Each fix restores behavior main already had. Regression fixtures were added on main in `80409b2` before the branch changes. No personal investigation by Shaoyu is claimed.

| Fault checkpoint | Separate restoring/fix commit | Behavior restored |
|---|---|---|
| `af15876` / `bug/partition` | `504d033` | Global content groups (partition no longer scopes equality) |
| `7f1e6ba` / `bug/survivor` | `3f43243` | Minimum-ID survivor, independent of arrival order |
| `749df11` / `bug/resume` | This resume-fix commit | Load actual validated exact-stage edges on resume |

The first two fix commits were originally described as restoring the passing baseline before the next scenario. They are real separate code-restoration commits, not rewritten history. Historical fix `504d033`: partition regression passed (0.36s). Historical fix `3f43243`: concurrency regression passed (0.31s). Current corrected learning worktree: all three regressions passed (1.07s). Full corrected branch `01d8e28`: 36 checks passed, 4 upstream Ray warnings, 132.64s. Dependency validation, compilation, diff checks and application-source equality with main passed. Integration is authorized only for this working final state; documentation-only follow-up changes receive focused link checks. Bug snapshots remain available after integration.

The bug-snapshot marker is removed from the corrected branch; study historical versions by tag. Current instructions supersede the older permanent-isolation wording. Bug/fix history will be retained by a non-fast-forward merge; no application-behavior improvement is claimed over the already-correct main code. Main receives only a working final tree; unresolved issues block integration.
