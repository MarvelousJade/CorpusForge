from dataclasses import asdict
import json
from pathlib import Path
import platform
import time
import numpy as np
from .core import ingest, prepare, exact_edges, outputs, survivors
from .near import add_signature, candidates, verify, oracle
from .persistence import Store, encode, output_lock, checksum
from . import __version__


class Interrupted(RuntimeError):
    """Deliberate fault injection at an atomic completion boundary."""


def run(input_path, output_path, config, backend='sequential', resume=False, stop_after=None):
    with output_lock(output_path):
        return _run(input_path, output_path, config, backend, resume, stop_after)


def _run(input_path, output_path, config, backend, resume, stop_after):
    start = time.perf_counter()
    source = Path(input_path)
    paths = sorted(source.rglob('*.jsonl')) if source.is_dir() else [source]
    if not paths:
        raise ValueError('no JSONL inputs')
    if sum(p.stat().st_size for p in paths) > config.max_input_bytes:
        raise ValueError('input exceeds max_input_bytes')
    # Driver validates source locations even when Ray rereads the dataset.
    documents = ingest(paths, config)
    store = Store(output_path, paths, config, backend, resume)
    ray_api = None
    startup = 0.0
    if backend == 'ray':
        from . import ray_backend as ray_api
        begin = time.perf_counter()
        ray_api.initialize(config)
        startup = time.perf_counter() - begin
    elif backend != 'sequential':
        raise ValueError(f'unknown backend {backend}')
    reused = []

    def stage(name, fn):
        cached = store.load(name)
        if cached is not None:
            reused.append(name)
            return cached
        begin = time.perf_counter()
        try:
            value = fn()
        except Exception as exc:
            raise RuntimeError(f'{backend} stage {name} failed: {exc}') from exc
        store.stage(name, value, time.perf_counter() - begin)
        if stop_after == name:
            raise Interrupted(f'interrupted after {name}')
        return value

    records = stage('prepared', lambda: ray_api.prepare_data(paths, config) if ray_api and documents else
                    [add_signature(prepare(doc, config), config) for doc in documents])
    for info in store.manifest['contract']['inputs']:
        if checksum(info['path']) != info['sha256']:
            raise ValueError('inputs changed during preparation; discard this run')
    exact = stage('exact', lambda: ray_api.exact_data(records, config) if ray_api and records else exact_edges(records))
    roots = survivors([r['id'] for r in records], exact)
    representatives = [r for r in records if roots[r['id']] == r['id']]
    pairs = stage('candidates', lambda: ray_api.candidate_data(representatives, config) if ray_api else candidates(representatives, config))
    edges = stage('verified', lambda: verify(representatives, pairs, config.threshold))
    result = stage('decisions', lambda: dict(zip(('kept', 'removed'), outputs(records, exact, edges))))
    if 'output' in store.manifest['stages']:
        return json.loads((store.root / 'report.json').read_text(encoding='utf-8'))
    report = dict(version=__version__, python=platform.python_version(), numpy=np.__version__, backend=backend,
                  input=len(records), kept=len(result['kept']), removed=len(result['removed']),
                  exact_removed=len(exact), candidates=len(pairs), verified_edges=len(edges),
                  quality=oracle(representatives, pairs, config) if config.near else {'status': 'disabled'},
                  configuration=asdict(config), startup_seconds=startup, reused_stages=reused,
                  stage_seconds={name: info['seconds'] for name, info in store.manifest['stages'].items()},
                  seconds=time.perf_counter()-start)
    if ray_api:
        report['ray'] = ray_api.ray.__version__
    artifacts = {name+'.jsonl': b''.join(encode(row)+b'\n' for row in result[name]) for name in ('kept', 'removed')}
    artifacts['report.json'] = encode(report)
    store.finish('output', artifacts, time.perf_counter()-start)
    return report
