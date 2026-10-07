# CorpusForge

Small, inspectable text-curation prototype inspired by DataTrove. Python 3.11–3.13.

```sh
python -m venv .venv
# Activate .venv using your shell's command
python -m pip install -e '.[test]'
python -m pytest -q
python -m corpusforge run --input data/sample --output runs/demo --backend sequential
python -m corpusforge run --input data/sample --output runs/ray --backend ray
python -m corpusforge run --input data/sample --output runs/interrupted --stop-after candidates
# Previous command intentionally exits 2. Resume with identical configuration:
python -m corpusforge run --input data/sample --output runs/interrupted --resume
```

JSONL records require unique nonempty string IDs and string text; optional metadata is an object. Invalid records include file/line diagnostics. NFC, case folding and whitespace collapsing normalize only a comparison copy. Empty/blank normalized content is one exact group. IDs are lexicographically ordered, not numeric. Hash collisions are verified against full normalized content. Output retains original documents and metadata; removed records wrap the original document, reason and final survivor ID.

## Near duplicates

Normalization → whitespace-token word shingles → seeded NumPy MinHash → LSH band collisions → exact set Jaccard → connected components → smallest ID. Exact survivors alone enter near detection. Short documents with no shingles are exact-only. Repeated shingles are sets, so repetitive text may collapse despite differing lengths. Punctuation remains meaningful. Components can join A and C through B even when A–C is below threshold.

`--exact-only`, `--shingle-size`, `--seed`, `--bands`, `--rows`, and `--threshold` configure this tradeoff. LSH is approximate, not a recall guarantee. For at most 500 exact survivors, `report.json` includes exhaustive-oracle precision, recall and missed-pair counts (null for undefined ratios).

## Backends and recovery

Ray Data reads JSONL lines, computes normalization/hashes/signatures in batches, globally groups digest and band keys, and emits canonical pairs. Both backends share exact verification and deterministic survivor selection. This is a **bounded local prototype**, not distributed clustering. Default caps are 10,000 documents, 50 MB input, 100,000 characters/document and 200,000 candidates. Configure `--batch-size`, `--workers`, and `--max-*` flags deliberately; hot groups remain a memory risk.

A new output directory is required. `--resume` validates input fingerprints, configuration, software versions and every completed stage's checksums. Interrupted stages rerun; missing/corrupt completed artifacts fail rather than silently reuse. Single-writer locks protect output. Do not edit inputs during runs. Whole-stage recovery is not individual-Ray-task recovery.

## Benchmarks and learning

```sh
python -m corpusforge benchmark --output runs/bench --sizes 40 120 --repeats 3 --settings 16,1,16,4 64,2,32,2
```

This generates four-file synthetic corpora, sequential/Ray measurements, cold/warm labels, stage timings, sampled RSS/raylet object-store usage, candidate/oracle metrics and retained-ID parity checks. Results are local/synthetic evidence; startup and coordinator overhead may make Ray slower. Use a fresh directory for every experiment.

- [Architecture and limits](docs/ARCHITECTURE.md)
- [Engineering decisions](docs/DECISIONS.md)
- Local dependency snapshot: `requirements-local.txt` (benchmark environment; pin with `pip install -r requirements-local.txt`)
- `psutil` measures process memory; `grpcio` supports benchmark-only raylet memory-stat RPCs.
- [Interview preparation](docs/interview-guide.md)
- [Observed bugs and engineering hurdles](docs/engineering-journal.md)
- Repository workflow and explicitly resolved naming conflicts: `AGENTS.md`
- Reference provenance: `REFERENCES.md`
- Implementation progress and checks actually run: `WORKLOG.md`

Python/Ray on Windows is tested locally when verification results say so; Linux is not implicitly verified. Timing reports are not byte-identical across runs; kept/removed decision artifacts should be.
