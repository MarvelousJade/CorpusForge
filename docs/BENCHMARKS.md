# Local synthetic benchmark evidence

## Reproduce

Python 3.12 on the measured Windows machine; dependency snapshot: `../requirements-local.txt`.

```sh
python -m corpusforge benchmark --output runs/benchmark-isolated --sizes 40 120 --repeats 3 --settings 16,1,16,4 64,1,16,4 16,2,16,4 16,1,32,2
```

Settings mean **batch size, compute workers, bands, rows**. Baseline plus isolated batch/worker/LSH changes avoids attributing joint-setting differences to one variable. Sequential runs precede Ray initialization per setting; Ray has one cold runtime startup and two warm repeats. Warm runs redo ingestion, computation and persistence (no stage resume). Runtime allocation is workers+1 CPUs for control headroom. Use a fresh output directory. Commands regenerate datasets and reports, not identical wall-clock numbers.

Generator seed 42: four files, 40-word random bases, normalized exact variants, appended controlled edits and repetitive text. The small corpora support exhaustive Jaccard oracles. They are intentionally much smaller/easier than web or training corpora. No speedup or production recall is inferred.

## Measurement definitions
- End-to-end wall time covers `run`, finalized artifacts and profiler startup; excludes profiler teardown. Instrumentation overhead is not removed.
- Stage timings measure stage function computation/Ray execution; checkpoint finalization, fingerprints, oracle and other coordinator overhead also appear in end-to-end time. CLI report seconds are captured before final output/report persistence; benchmark wall time is authoritative for the complete operation.
- Process RSS and summed child-process RSS are sampled every 100ms (plus RPC/inspection latency). Summed RSS can double-count shared pages; short peaks may be missed.
- Object-store usage is actual raylet used-byte stats via a pinned-version private API, not resource capacity. Missing telemetry is null with recorded errors. Sequential should have no initialized Ray runtime/samples.
- Cold means **Ray runtime cold**, not fresh interpreter, OS cache or machine. Driver imports/caches remain; background load is not controlled. One cold observation per setting is not a cold-start variance estimate. Two warm repetitions provide only a small variance sample.
- Retained IDs are asserted equal within each configuration; candidate precision/recall is measured against exhaustive exact-survivor Jaccard truth for <=500 representatives.

## Pilot — preserved, not used for fair memory comparison

`benchmarks/pre-isolation-results.json` contains the actual first 24-run matrix (N=40/120, settings 16/1/16/4 and 64/2/32/2, three repeats). Every parity check passed. Candidate counts were 30/90 respectively; both easy high-overlap settings had measured oracle precision/recall 1.0 and zero misses. That is fixture-specific evidence, not perfect LSH recall.

The pilot interleaved backends, leaving an idle Ray runtime during 8 sequential measurements. These memory rows are **contaminated**; pilot wall time also includes profiler teardown. Do not use them as standalone sequential memory estimates or compare their timings directly with corrected measurements. Full investigation/regression: [journal J04](engineering-journal.md).

## Corrected results

The corrected 48-measurement matrix completed successfully. [Raw results](benchmarks/results.json) and [all individual timings/throughputs](benchmarks/SUMMARY.md) are published separately from the pilot. Execution code: `119fed4` (working baseline `db828f4`). Hardware: Windows 11 (10.0.26200), AMD64 Family 23 Model 113, 6 physical/12 logical CPUs, 17,101,787,136 bytes RAM; Python 3.12.10, Ray 2.55.1, NumPy 2.5.3. Other versions are pinned in `requirements-local.txt`.

| N | Batch/workers | Bands×rows | Sequential mean ± SD (n=3), s | Ray cold (n=1), s | Ray warm mean ± SD (n=2), s |
|---|---|---|---:|---:|---:|
| 40 | 16/1 | 16×4 | 0.184 ± 0.061 | 37.525 | 20.321 ± 0.189 |
| 40 | 64/1 | 16×4 | 0.215 ± 0.015 | 35.739 | 24.509 ± 3.403 |
| 40 | 16/2 | 16×4 | 0.235 ± 0.007 | 36.191 | 17.010 ± 0.204 |
| 40 | 16/1 | 32×2 | 0.465 ± 0.143 | 38.428 | 20.931 ± 0.311 |
| 120 | 16/1 | 16×4 | 0.334 ± 0.080 | 49.262 | 25.172 ± 3.478 |
| 120 | 64/1 | 16×4 | 0.261 ± 0.013 | 53.065 | 35.529 ± 2.299 |
| 120 | 16/2 | 16×4 | 0.306 ± 0.016 | 49.022 | 33.203 ± 1.394 |
| 120 | 16/1 | 32×2 | 0.380 ± 0.057 | 53.104 | 35.130 ± 5.424 |

**Ray is much slower at this scale**, even warm. Two workers improved the 40-record warm observation but not the 120-record one. Larger batches did not help here. These tiny samples and uncontrolled background/cache effects cannot support universal tuning conclusions. Sequential ignores worker/batch settings for computation; variation there must not be interpreted as parallel speed effects.

Candidate counts are 30 at N=40 and 90 at N=120. All observed configurations have oracle precision/recall 1.0 and zero misses, and retain 12/36 IDs respectively. The high-overlap families explain why both LSH settings retrieve the same candidates; more bands still expand more records/shuffle work. Boundary and forced-miss fixtures separately verify that missed candidates are reported, not recovered by Jaccard. Do not extrapolate perfect recall to other data.

All 48 parity flags were validated, and retained IDs also match across the batch/worker/LSH settings for these fixtures. All 24 sequential rows have zero Ray telemetry samples; all 24 Ray rows have positive samples and no recorded RPC errors. The isolation fix eliminated the pilot's idle-runtime measurement contamination.

Ranges of per-run sampled peaks across settings/repeats (MiB, rounded):

| N/backend | Driver RSS | Process-tree RSS | Ray object-store usage |
|---|---:|---:|---:|
| 40/sequential | 68.5–160.9 | 68.5–160.9 | not applicable |
| 40/Ray | 133.8–168.8 | 1215.1–1782.1 | 0.605–1.123 |
| 120/sequential | 129.4–137.5 | 129.4–137.5 | not applicable |
| 120/Ray | 137.6–143.7 | 1273.3–1816.4 | 1.570–2.917 |

The driver retains imported modules/caches across settings, explaining why sequential RSS is not a fresh-process baseline. Tree RSS is a summed-process metric, not physical unique memory. These sampled peaks are lower bounds on instantaneous peaks, not allocator guarantees.

Cold runtime startup ranged from **7.821 to 12.109 seconds**. Baseline warm Ray stage means at N=40: preparation 0.331s, exact grouping 8.344s, candidate grouping 11.444s; at N=120: 0.425s, 9.737s, 14.750s. Verification and decisions each took under 1ms in these small fixtures. Global transformations dominate, not MinHash arithmetic. Runtime logs showed the default 200 shuffle partitions; tuning those partitions is a future experiment, not a measured improvement claimed here.
