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

Pending full corrected matrix execution and publication. No corrected performance or memory figures are claimed yet. Published results will include hardware, package versions, cold/warm variation, stage times, throughput, memory telemetry, quality and retained IDs, including slowdowns.
