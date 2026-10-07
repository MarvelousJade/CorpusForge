# Progressive hints — spoilers

Open one hint at a time.

## Partition scenario
1. Does the candidate scope include the entire corpus?
2. Compare the key used before equality verification for same-partition and cross-partition records.
3. Partition information belongs in scheduling, not in the final content-equivalence key.

## Survivor scenario
1. Replay the same group in a different order.
2. Is the group's representative a function of its contents or its arrival order?
3. Canonicalize survivor IDs before workers/coordinator exchange decisions.

## Resume scenario
1. Inspect completion entries, artifact contents and values actually returned by the loader.
2. Is a reused checkpoint providing the same data as a newly computed stage?
3. A completed exact stage cannot be replaced by “no edges”; persistence saves computation, not the result's meaning.
