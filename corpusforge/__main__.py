import argparse
from dataclasses import asdict
import json
from pathlib import Path
import time
from .core import Config, ingest, prepare, exact_edges, outputs, survivors
from .near import add_signature, candidates, verify, oracle


def main():
    parser = argparse.ArgumentParser(prog='corpusforge')
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('run')
    run.add_argument('--input', required=True)
    run.add_argument('--output', required=True)
    run.add_argument('--backend', choices=['sequential', 'ray'], default='sequential')
    run.add_argument('--exact-only', action='store_true')
    run.add_argument('--seed', type=int, default=42)
    run.add_argument('--bands', type=int, default=16)
    run.add_argument('--rows', type=int, default=4)
    run.add_argument('--shingle-size', type=int, default=3)
    run.add_argument('--threshold', type=float, default=.8)
    args = parser.parse_args()
    try:
        if args.backend != 'sequential':
            raise ValueError('Ray backend not implemented yet')
        start = time.perf_counter()
        source = Path(args.input)
        paths = sorted(source.rglob('*.jsonl')) if source.is_dir() else [source]
        if not paths:
            raise ValueError('no JSONL inputs')
        config = Config(near=not args.exact_only, seed=args.seed, bands=args.bands, rows=args.rows,
                        shingle_size=args.shingle_size, threshold=args.threshold)
        records = [add_signature(prepare(doc, config), config) for doc in ingest(paths, config)]
        exact = exact_edges(records)
        roots = survivors([r['id'] for r in records], exact)
        representatives = [r for r in records if roots[r['id']] == r['id']]
        pairs = candidates(representatives, config)
        near = verify(representatives, pairs, config.threshold)
        quality = oracle(representatives, pairs, config) if config.near else {'status': 'disabled'}
        kept, removed = outputs(records, exact, near)
        target = Path(args.output)
        target.mkdir(parents=True, exist_ok=True)
        for name, rows in [('kept', kept), ('removed', removed)]:
            (target / f'{name}.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
        (target / 'report.json').write_text(json.dumps(dict(input=len(records), kept=len(kept), removed=len(removed), configuration=asdict(config), candidates=len(pairs), verified_edges=len(near), quality=quality, seconds=time.perf_counter()-start), indent=2))
    except (ValueError, OSError) as exc:
        parser.exit(2, f'corpusforge: {exc}\n')


if __name__ == '__main__':
    main()
