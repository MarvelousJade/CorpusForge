import argparse
import json
from .core import Config
from .pipeline import run, Interrupted


def main():
    parser = argparse.ArgumentParser(prog='corpusforge')
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('run')
    command.add_argument('--input', required=True)
    command.add_argument('--output', required=True)
    command.add_argument('--backend', choices=['sequential', 'ray'], default='sequential')
    command.add_argument('--resume', action='store_true')
    command.add_argument('--stop-after', choices=['prepared', 'exact', 'candidates', 'verified', 'decisions'], help='practice interruption after a completed stage')
    command.add_argument('--exact-only', action='store_true')
    command.add_argument('--preserve-case', action='store_true')
    command.add_argument('--preserve-whitespace', action='store_true')
    command.add_argument('--unicode-form', choices=['NFC', 'NFKC', 'none'], default='NFC')
    defaults = Config()
    for name in ('seed', 'bands', 'rows', 'shingle_size', 'batch_size', 'workers', 'max_documents', 'max_candidates', 'max_input_bytes', 'max_text_chars'):
        command.add_argument('--'+name.replace('_','-'), type=int, default=getattr(defaults,name))
    command.add_argument('--threshold', type=float, default=.8)
    bench = sub.add_parser('benchmark')
    bench.add_argument('--output', required=True)
    bench.add_argument('--sizes', type=int, nargs='+', default=[40, 120])
    bench.add_argument('--repeats', type=int, default=3)
    bench.add_argument('--seed', type=int, default=42)
    bench.add_argument('--settings', nargs='+', default=['16,1,16,4', '64,1,16,4', '16,2,16,4', '16,1,32,2'], help='batch,workers,bands,rows tuples')
    args = parser.parse_args()
    try:
        if args.command == 'benchmark':
            from .benchmark import benchmark
            settings = [tuple(map(int, value.split(','))) for value in args.settings]
            if any(len(s)!=4 for s in settings) or args.repeats < 2 or min(args.sizes) < 1:
                raise ValueError('settings need four integers; repeats >=2 and sizes >=1')
            benchmark(args.output, args.sizes, args.repeats, settings, args.seed)
        else:
            config = Config(**{name: getattr(args,name) for name in ('seed','bands','rows','shingle_size','threshold','batch_size','workers','max_documents','max_candidates','max_input_bytes','max_text_chars','unicode_form')},
                            near=not args.exact_only, casefold=not args.preserve_case, whitespace=not args.preserve_whitespace)
            report = run(args.input, args.output, config, args.backend, args.resume, args.stop_after)
            print(json.dumps({'kept':report['kept'], 'removed':report['removed'], 'seconds':report['seconds']}))
    except (ValueError, OSError, RuntimeError) as exc:
        parser.exit(2, f'corpusforge: {exc}\n')


if __name__ == '__main__':
    main()
