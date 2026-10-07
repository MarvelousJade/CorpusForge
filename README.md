# CorpusForge

Small, inspectable text-curation prototype inspired by DataTrove. Python 3.11–3.13.

```sh
python -m venv .venv
# Activate .venv using your shell's command
python -m pip install -e '.[test]'
python -m pytest -q
python -m corpusforge run --input data/sample --output runs/demo --backend sequential
```

JSONL records require unique nonempty string IDs and string text; optional metadata is an object. Invalid records include file/line diagnostics. NFC, case folding and whitespace collapsing normalize only a comparison copy. Empty/blank normalized content is one exact group. IDs are lexicographically ordered, not numeric. Hash collisions are verified against full normalized content. Output retains original documents and metadata; removed records wrap the original document, reason and final survivor ID.

## Near duplicates

Normalization → whitespace-token word shingles → seeded NumPy MinHash → LSH band collisions → exact set Jaccard → connected components → smallest ID. Exact survivors alone enter near detection. Short documents with no shingles are exact-only. Repeated shingles are sets, so repetitive text may collapse despite differing lengths. Punctuation remains meaningful. Components can join A and C through B even when A–C is below threshold.

`--exact-only`, `--shingle-size`, `--seed`, `--bands`, `--rows`, and `--threshold` configure this tradeoff. LSH is approximate, not a recall guarantee. For at most 500 exact survivors, `report.json` includes exhaustive-oracle precision, recall and missed-pair counts (null for undefined ratios).

Reference provenance: `REFERENCES.md`. Implementation progress and verification: `WORKLOG.md`.
