# Engineering decisions

## 1. Normalize comparisons, preserve documents
**Problem:** superficial formatting inflates exact duplicates, but case, compatibility Unicode and punctuation may convey meaning.
**Alternatives:** raw-byte equality; destructive cleaning; aggressive punctuation/Unicode stripping; separate configurable normalization.
**Evidence:** cross-file tests merge case/whitespace differences while preserving metadata and text. Collision tests ensure a hash alone cannot delete content. Empty strings form one exact group.
**Choice:** NFC + casefold + collapsed whitespace by default, separate comparison copy. Flags preserve case/whitespace or select NFKC/none.
**Tradeoffs:** easy to explain and audit, but casefold can merge meaningful distinctions. Whitespace tokenization retains punctuation and does not suit every language. No universal semantic-cleaning claim. Review domain-specific normalization before use.

## 2. Probabilistic candidates, exact verification
**Problem:** exhaustive Jaccard is quadratic; LSH can miss real similarities and hot buckets explode.
**Alternatives:** all pairs; LSH-only removal; embeddings; LSH followed by set Jaccard.
**Evidence:** oracle, threshold-boundary, repetitive-text and transitive-cluster tests establish the verification rule. Runtime reports measure misses for <=500 exact representatives. Benchmark results supply local candidate counts, not theoretical recall claims.
**Choice:** seeded NumPy affine MinHash over stable SHA-256 shingle hashes, explicit bands/rows, canonical pairs, exact threshold comparison. Approximate candidate probability is `1-(1-s^rows)^bands` under ideal independent MinHash assumptions; affine hashes and finite shingle sets do not perfectly meet those assumptions.
**Tradeoffs:** more bands/fewer rows improve recall at the expense of candidates and shuffle work. Verification eliminates LSH false positives, not misses. Connected components introduce transitive grouping even without all-pair threshold agreement. Repetition uses sets, ignoring frequency. Configurable caps abort rather than silently truncate.

## 3. Ray transformations, bounded coordinator
**Problem:** global duplicate groups must cross partitions while deterministic clustering and recovery remain understandable.
**Alternatives:** partition-local dedup (incorrect globally); fully distributed union-find; Ray tasks alone; Ray Data global transformations plus one coordinator.
**Evidence:** integration tests compare files, candidates and decisions across batch/worker configurations. Failure tests exercise a genuine Ray worker UDF error. Recovery tests reuse stage artifacts and reject changed contracts/corruption. Published local synthetic timing/memory evidence must be consulted before making speed claims.
**Choice:** shared pure functions; Ray Data reads/batches/global groups; coordinator verifies and clusters; atomic whole-stage checkpoints and strict manifests.
**Tradeoffs:** Ray startup, serialization, shuffle and double ingestion dominate small datasets. Global hot groups and collected records limit scale. Stage recovery is simpler but recomputes an interrupted stage. Logical partition assignments are stable contract information, not fixed Ray placement. This is a local prototype; distributed clustering and task-granular recovery are deliberately deferred.
