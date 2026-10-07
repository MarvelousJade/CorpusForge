"""Atomic, checksummed completed stages. Interrupted stages are rerun in full."""
from dataclasses import asdict
import hashlib
import json
import os
from contextlib import contextmanager
from importlib.metadata import version
from pathlib import Path
from . import __version__


def checksum(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def atomic(path, data):
    temp = path.with_suffix(path.suffix + '.tmp')
    with open(temp, 'wb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def encode(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode('utf-8')


class Store:
    def __init__(self, output, paths, config, backend, resume):
        self.root = Path(output)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'manifest.json'
        contract = dict(version=__version__, software={name: version(name) for name in ('numpy', 'ray', 'pyarrow')},
                        configuration=asdict(config), backend=backend,
                        partition_policy='sorted files round-robin logical assignment; Ray controls physical blocks',
                        inputs=[dict(path=str(p.resolve()), bytes=p.stat().st_size, sha256=checksum(p),
                                     partition=i % config.workers) for i,p in enumerate(paths)])
        if self.path.exists():
            if not resume:
                raise ValueError('output already has a manifest; use --resume or a new directory')
            self.manifest = json.loads(self.path.read_text(encoding='utf-8'))
            if self.manifest['contract'] != contract:
                raise ValueError('resume rejected: inputs/configuration/backend/version changed')
            for stage in self.manifest['stages'].values():
                for artifact in stage['artifacts']:
                    path = self.root / artifact['name']
                    if not path.exists() or checksum(path) != artifact['sha256']:
                        raise ValueError(f'resume rejected: missing/corrupted artifact {path}')
        else:
            if resume:
                raise ValueError('resume requires an existing manifest')
            if any(p.name != '.lock' for p in self.root.iterdir()):
                raise ValueError('output directory must be empty')
            self.manifest = dict(contract=contract, stages={})
            self.save()

    def save(self):
        atomic(self.path, encode(self.manifest))

    def load(self, name):
        if name in self.manifest['stages']:
            if name == 'exact':
                return []
            return json.loads((self.root / f'{name}.json').read_text(encoding='utf-8'))
        return None

    def finish(self, name, artifacts, seconds):
        rows = []
        for filename, data in artifacts.items():
            path = self.root / filename
            atomic(path, data)
            rows.append(dict(name=filename, sha256=checksum(path)))
        self.manifest['stages'][name] = dict(artifacts=rows, seconds=seconds)
        self.save()

    def stage(self, name, value, seconds):
        self.finish(name, {f'{name}.json': encode(value)}, seconds)


@contextmanager
def output_lock(output):
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    with open(root / '.lock', 'a+b') as stream:
        stream.seek(0)
        if os.fstat(stream.fileno()).st_size == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ValueError('output is locked by another run') from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
