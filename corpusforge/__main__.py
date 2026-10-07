import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
from .core import Config, ingest, prepare, exact_edges, outputs


def main():
    parser = argparse.ArgumentParser(prog='corpusforge')
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('run')
    run.add_argument('--input', required=True)
    run.add_argument('--output', required=True)
    run.add_argument('--backend', choices=['sequential', 'ray'], default='sequential')
    args = parser.parse_args()
    try:
        if args.backend != 'sequential':
            raise ValueError('Ray backend not implemented yet')
        start = time.perf_counter()
        source = Path(args.input)
        paths = sorted(source.rglob('*.jsonl')) if source.is_dir() else [source]
        if not paths:
            raise ValueError('no JSONL inputs')
        config = Config(near=False)
        records = [prepare(doc, config) for doc in ingest(paths, config)]
        kept, removed = outputs(records, exact_edges(records))
        target = Path(args.output)
        target.mkdir(parents=True, exist_ok=True)
        for name, rows in [('kept', kept), ('removed', removed)]:
            (target / f'{name}.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
        (target / 'report.json').write_text(json.dumps(dict(input=len(records), kept=len(kept), removed=len(removed), configuration=asdict(config), seconds=time.perf_counter()-start), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'corpusforge: {exc}\n')


if __name__ == '__main__':
    main()
