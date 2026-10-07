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

Implementation progress and verification: `WORKLOG.md`.
