# Fix verification

These issues were introduced on the learning branch, separately from working main; they are not production incidents. Each fix restores behavior main already had. Regression fixtures were added on main in `db828f4` before the branch changes. No personal investigation by Shaoyu is claimed.

| Fault checkpoint | Separate restoring/fix commit | Behavior restored |
|---|---|---|
| `0adcd10` / `bug/partition` | `f4542c0` | Global content groups (partition no longer scopes equality) |
| `7b150e6` / `bug/survivor` | `c884149` | Minimum-ID survivor, independent of arrival order |
| `44f21ff` / `bug/resume` | `4c8c0c7` | Load actual validated exact-stage edges on resume |

The first two fix commits were originally described as restoring the passing baseline before the next scenario. They are separate code-restoration commits. The user later authorized functional subject rewording; current IDs refer to the identical trees previously checked. Trees, identities, dates and topology were preserved; the old/new mapping is in `docs/commit-reference-map.json`. Historical fix `f4542c0`: partition regression passed (0.36s). Historical fix `c884149`: concurrency regression passed (0.31s). Current corrected learning worktree: all three regressions passed (1.07s). Full corrected branch `4c8c0c7`: 36 checks passed, 4 upstream Ray warnings, 132.64s. Dependency validation, compilation, diff checks and application-source equality with main passed. Integration is authorized only for this working final state; documentation-only follow-up changes receive focused link checks. Bug snapshots remain available after integration.

The bug-snapshot marker is removed from the corrected branch; study historical versions by tag. Current instructions supersede the older permanent-isolation wording. Bug/fix history was retained by the non-fast-forward merge `5ebb70e`; no application-behavior improvement is claimed over the already-correct main code. Main receives only a working final tree; unresolved issues block integration.
