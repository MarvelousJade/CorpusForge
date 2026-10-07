# Engineering journal

Only observed problems and actual checks are recorded. “Implementation session” identifies investigation performed here, not a personal investigation attributed to Shaoyu. No personal debugging or learning activity by Shaoyu has been reported yet. Commit IDs identify code/evidence, not proof of a person's involvement.

## J01 — JSON checkpoints changed edge types
- **Context:** Whole-stage persistence/resume for sequential exact/near clustering.
- **Symptom/discovery:** `pytest tests/test_recovery.py tests/test_exact.py tests/test_near.py -q --tb=short` failed at resume after `exact` and `candidates`: `TypeError: '<' not supported between instances of 'tuple' and 'list'`. Result: 2 failed, 15 passed. Reproduce with `test_resume[exact]`.
- **Investigation:** Hypothesis: persisted edge representation differs from in-memory edges. Traceback showed `outputs → survivors → sorted(edges)` mixing cached exact edges with freshly verified near edges. JSON arrays reload as lists; pure functions emitted tuples.
- **Root cause:** A sorting boundary assumed homogeneous Python sequence types, which JSON does not preserve.
- **Alternatives:** Convert only in checkpoint loader; convert at each stage; canonicalize in shared clustering.
- **Decision/tradeoffs:** Canonicalize every edge to a tuple in `survivors`. One small O(E) conversion protects both backends and every resume boundary without custom JSON types.
- **Verification:** Follow-up reached 20 passing tests with one unrelated locking failure. Final targeted validation/generator suite: 22 passed in 10.92s, including all five resume boundaries and an interrupted uncommitted stage. Relevant recovery commit: `55e6bfd`.
- **Limitations:** Not task-granular Ray recovery; checksums detect accidental corruption, not maliciously rewritten manifests.
- **Involvement:** Implementation session investigated, changed and tested the fix. Shaoyu's personal investigation/learning: not reported.

## J02 — Windows lock-byte read bypassed friendly lock diagnostics
- **Context:** Single-writer protection for output manifests.
- **Symptom/discovery:** `test_single_writer` failed with `PermissionError` at `stream.read(1)` while a first writer held the byte-range lock. Targeted run: 1 failed, 20 passed.
- **Investigation:** Initial hypothesis: the failure occurred before the intended nonblocking lock call. Traceback confirmed initialization read, not `msvcrt.locking`, raised the exception. The second stream tried to read a locked byte.
- **Root cause:** Windows enforces byte-range locks on reads as well as lock acquisition; POSIX-style initialization assumptions were wrong.
- **Alternatives:** Catch initialization I/O errors broadly; use a separate lock library; avoid reading the byte.
- **Decision/tradeoffs:** Check `fstat().st_size` and initialize only an empty file; attempt the actual lock inside diagnostic handling. Standard-library platform branches keep dependencies small. The harmless `.lock` file stays in the run directory.
- **Verification:** 22 passed in 10.92s including nested writer rejection and recovery boundaries. Relevant recovery commit: `55e6bfd`.
- **Limitations:** Local filesystem assumptions; Linux locking is implemented but not yet exercised. No claim of network-filesystem semantics.
- **Involvement:** Implementation session investigated, changed and ran checks. Shaoyu's personal investigation/learning: not reported.

## J03 — Ray Data CPU reservation stalled a tiny fixture
- **Context:** First real Ray Data integration parity test, 10 documents across 10 input files with batch/worker variants.
- **Symptom/discovery:** Background test still running at 6m41s with no stdout. Tiny workload made this a suspected startup/execution stall, not performance evidence.
- **Investigation:** One deliberate status inspection confirmed it was running; bounded logs had no output. Ray monitor logs showed a healthy active node with `0.01/1.0 CPU` used and a pending `CPU: 1.0, memory: 558` task. This establishes a scheduling stall after runtime startup, not a firewall/startup failure. Dashboard missing-extra warnings were not taken as proof of the stall's cause. Diagnostic output completed log reads but then timed out during process enumeration; remove that nonessential enumeration.
- **Root cause:** Fractional control-actor CPU reservation left less than one CPU available for a 1-CPU Data read task. Reserving control headroom allowed the same fixtures to complete.
- **Alternatives:** Inspect Ray logs before changing configuration; isolate `ray.init`; use another supported local platform if Windows proves blocked. Not replace Ray with a sequential fallback.
- **Decision/tradeoffs:** Stop the stalled test and reserve one extra logical CPU when initializing the local Ray runtime (`workers + 1`), keeping transformation concurrency at the requested worker cap. Cost: runtime resource allocation includes control headroom and can exceed the requested compute-worker count. No sequential fallback.
- **Verification:** `pytest tests/test_ray.py tests/test_ray_recovery.py -q --tb=short`: 4 passed, 4 upstream warnings in 156.42s. Byte-identical kept/removed/candidates/verified artifacts across backends for batch/worker variants (1/1 and 3/2), real worker-UDF failure, and Ray resume/clean parity. Ray commit pending receipt. Benchmark matrix launched separately.
- **Limitations:** Runtime advertises workers+1 logical CPUs; read/shuffle scheduling remains Ray-managed. An externally initialized runtime with insufficient headroom can still stall unless rejected; no general deadlock-recovery promise.
- **Involvement:** Implementation session observed the stall and started diagnosis. Shaoyu's personal investigation/learning: not reported.

## H00 — Deterministic global groups with heterogeneous metadata
- **Context:** Mapping the document contract to Ray Data batches and global dedup groups.
- **Difficulty:** Metadata objects may have different keys/types across records. Letting Arrow infer one nested metadata schema could coerce values or fail; partition-local groups would violate global deduplication. This is a design constraint, not a claim that a coercion failure was reproduced.
- **Approaches/decision:** Keep document/prepared structures inside JSON payload columns for transport; use explicit digest/band/id columns for global grouping. Share comparison and survivor functions with sequential execution. Validate file/line records centrally before Ray rereads text lines.
- **Tradeoffs:** JSON serialization, double reads and coordinator collections sacrifice performance for an inspectable local prototype. Bounds and worker failures must remain explicit. Fully distributed clustering or typed metadata normalization would add scope.
- **Verification:** Exact/near pure-function fixtures pass; 4 real Ray integration tests passed in 156.42s, including heterogeneous per-document metadata, global duplicate groups, deterministic decisions and recovery. Relevant Ray commit pending receipt.
- **Involvement:** Implementation-session design and implementation. Shaoyu's personal investigation/learning: not reported.

## H01 — Object-store measurement must measure usage, not capacity
- **Context:** Benchmark memory instrumentation.
- **Difficulty/evidence:** Review of Ray's installed `internal_api.py` showed actual `store_stats.object_store_bytes_used`. Cluster logical resource capacity is not allocator usage; subtracting resource availability would not establish object-store memory consumption. No fabricated runtime failure is claimed.
- **Approaches/decision:** Replace the draft resource-capacity estimate with pinned-version raylet store-stat RPCs, confined to benchmark instrumentation. Add `grpcio` for a concrete telemetry need. Null measurements and recorded errors are preferable to inventing zero usage.
- **Tradeoffs:** Version-sensitive private API and RPC overhead; sampling misses short peaks. Process-tree RSS can double-count shared pages. This is local evidence, not a production profiler.
- **Verification:** Dependency installation completed; measured runtime verification and benchmark commit pending.
- **Involvement:** Implementation-session code review/design change. Shaoyu's personal investigation/learning: not reported.
