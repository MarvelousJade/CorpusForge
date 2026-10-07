"""Reproducible local synthetic measurements; never extrapolate to web corpora."""
import json
from pathlib import Path
import platform
import random
import statistics
import threading
import time
import psutil
import ray
from .core import Config
from .pipeline import run
from .persistence import atomic, encode


def generate(directory, size, seed=42):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    base = [' '.join(f'w{rng.randrange(100000)}' for _ in range(40)) for _ in range(max(1,size//2))]
    docs = []
    for i in range(size):
        text = base[(i//4) % len(base)]
        kind = i % 4
        if kind == 1:
            text = ' '+text.upper()+'  '
        elif kind == 2:
            text += ' controlled edit'
        elif kind == 3:
            text = f'repeat{i//20} ' * (10+i%7)
        docs.append({'id': f'd{i:06}', 'text': text, 'metadata': {'kind': kind}})
    for partition in range(4):
        atomic(directory/f'{partition}.jsonl', b''.join(encode(d)+b'\n' for d in docs[partition::4]))


class Monitor:
    """Sample process-tree RSS and raylet object-store stats at 100ms.

    The pinned Ray private telemetry API is confined to benchmarks.
    """
    def __init__(self):
        self.stop = threading.Event()
        self.process_rss = 0
        self.tree_rss = 0
        self.object_used = 0
        self.object_samples = 0
        self.telemetry_errors = []
        self.state = None
        self.thread = threading.Thread(target=self.sample, daemon=True)

    def sample(self):
        proc = psutil.Process()
        while not self.stop.is_set():
            try:
                rss = proc.memory_info().rss
                tree = rss
                for child in proc.children(recursive=True):
                    try:
                        tree += child.memory_info().rss
                    except psutil.Error:
                        pass
                self.process_rss = max(self.process_rss, rss)
                self.tree_rss = max(self.tree_rss, tree)
                if ray.is_initialized():
                    from ray._private.internal_api import get_state_from_address, get_memory_info_reply
                    try:
                        if self.state is None:
                            self.state = get_state_from_address()
                        stats = get_memory_info_reply(self.state).store_stats
                        self.object_used = max(self.object_used, stats.object_store_bytes_used)
                        self.object_samples += 1
                    except Exception as exc:
                        if len(self.telemetry_errors) < 5:
                            self.telemetry_errors.append(str(exc))
            except (psutil.Error, RuntimeError):
                pass
            self.stop.wait(.1)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.stop.set()
        self.thread.join()


def benchmark(output, sizes, repeats, settings, seed=42):
    output = Path(output)
    if output.exists():
        raise ValueError('benchmark output must not exist')
    output.mkdir(parents=True)
    rows = []
    hardware = dict(platform=platform.platform(), processor=platform.processor(), logical_cpus=psutil.cpu_count(),
                    physical_cpus=psutil.cpu_count(logical=False), ram_bytes=psutil.virtual_memory().total,
                    python=platform.python_version(), ray=ray.__version__)
    for size in sizes:
        source = output/'data'/str(size)
        generate(source, size, seed)
        for batch, workers, bands, band_rows in settings:
            cfg = Config(seed=seed, batch_size=batch, workers=workers, bands=bands, rows=band_rows)
            # Runtime reused only within one setting, so cold/warm labels are explicit.
            ray.shutdown()
            baseline = None
            # Keep sequential memory independent of live Ray children. Then
            # preserve one runtime for a cold run followed by warm repeats.
            for backend in ('sequential', 'ray'):
                for repeat in range(repeats):
                    target = output/'runs'/f'{size}-{batch}-{workers}-{bands}-{band_rows}-{repeat}-{backend}'
                    begin = time.perf_counter()
                    with Monitor() as monitor:
                        report = run(source, target, cfg, backend)
                        # End-to-end run includes finalized files, but excludes
                        # profiler thread/RPC teardown latency.
                        elapsed = time.perf_counter()-begin
                    ids = [json.loads(line)['id'] for line in (target/'kept.jsonl').read_text(encoding='utf-8').splitlines()]
                    if baseline is None:
                        baseline = ids
                    if ids != baseline:
                        raise AssertionError('retained-ID parity failed')
                    rows.append(dict(size=size, backend=backend, repeat=repeat, mode='cold' if backend=='ray' and repeat==0 else 'warm' if backend=='ray' else 'sequential',
                                     batch=batch, workers=workers, bands=bands, rows=band_rows,
                                     seconds=elapsed, throughput=size/elapsed, stage_seconds=report['stage_seconds'],
                                     startup_seconds=report['startup_seconds'], process_peak_rss=monitor.process_rss,
                                     tree_peak_rss=monitor.tree_rss, object_store_sampled_peak_bytes=monitor.object_used if monitor.object_samples else None,
                                     object_store_samples=monitor.object_samples, telemetry_errors=monitor.telemetry_errors, candidates=report['candidates'], quality=report['quality'],
                                     retained=ids, parity=True))
                    atomic(output/'results.json', encode(dict(hardware=hardware, seed=seed, repeats=repeats, measurements=rows)))
            ray.shutdown()
    lines = ['# Local synthetic benchmark', '', 'Generated by `python -m corpusforge benchmark`. No real-corpus claims.', '',
             '| N | backend | batch/workers | bands×rows | mode | seconds | docs/s | candidates | parity |',
             '|---|---|---|---|---|---:|---:|---:|---|']
    for r in rows:
        lines.append(f"| {r['size']} | {r['backend']} | {r['batch']}/{r['workers']} | {r['bands']}×{r['rows']} | {r['mode']} | {r['seconds']:.3f} | {r['throughput']:.1f} | {r['candidates']} | yes |")
    lines += ['', 'Hardware, individual timings, seeds, versions, memory samples and retained IDs: `results.json`.',
              'RSS process-tree sums can double-count shared pages. Object-store measurements use raylet store stats via a pinned-version private API; 100ms sampling plus RPC latency can miss peaks. Missing telemetry is null, not zero. All sequential repeats precede Ray initialization for each setting. Cold Ray includes startup; warm Ray reuses the initialized runtime but reruns all stages and reads/writes. Measurements include profiling overhead but exclude profiler teardown. Sequential driver imports/caches and OS file cache are not cold-cache controlled.', '', 'Warm runtime variation (mean ± sample standard deviation, seconds):']
    for size in sizes:
        for setting in settings:
            for backend in ('sequential','ray'):
                values = [r['seconds'] for r in rows if r['size']==size and (r['batch'],r['workers'],r['bands'],r['rows'])==tuple(setting) and r['backend']==backend and (backend!='ray' or r['mode']=='warm')]
                if values:
                    lines.append(f'- N={size}, {setting}, {backend}: {statistics.mean(values):.3f} ± {statistics.stdev(values) if len(values)>1 else 0:.3f} (n={len(values)})')
    atomic(output/'SUMMARY.md', '\n'.join(lines).encode())
    return rows
