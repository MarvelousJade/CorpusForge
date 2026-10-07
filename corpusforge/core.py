"""Pure, backend-independent comparison functions."""
from dataclasses import dataclass
import hashlib
import json
import unicodedata


@dataclass(frozen=True)
class Config:
    casefold: bool = True
    whitespace: bool = True
    unicode_form: str = "NFC"
    near: bool = True
    shingle_size: int = 3
    bands: int = 16
    rows: int = 4
    threshold: float = 0.8
    seed: int = 42
    batch_size: int = 64
    workers: int = 2
    max_documents: int = 10000
    max_candidates: int = 200000
    max_input_bytes: int = 50000000
    max_text_chars: int = 100000

    def __post_init__(self):
        for name in ('shingle_size', 'bands', 'rows', 'batch_size', 'workers',
                     'max_documents', 'max_candidates', 'max_input_bytes', 'max_text_chars'):
            if getattr(self, name) < 1:
                raise ValueError(f'{name} must be positive')
        if not 0 <= self.threshold <= 1 or self.seed < 0:
            raise ValueError('threshold must be in [0,1]; seed must be nonnegative')
        if self.unicode_form not in ('NFC', 'NFKC', 'none'):
            raise ValueError('invalid unicode form')


def stable_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize(text, config):
    if config.unicode_form != 'none':
        text = unicodedata.normalize(config.unicode_form, text)
    if config.casefold:
        text = text.casefold()
    if config.whitespace:
        text = ' '.join(text.split())
    return text


def validate(record, source, line, config):
    prefix = f'{source}:{line}'
    if not isinstance(record, dict) or set(record) - {'id', 'text', 'metadata'}:
        raise ValueError(f'{prefix}: expected object with id, text, optional metadata')
    if not isinstance(record.get('id'), str) or not record['id']:
        raise ValueError(f'{prefix}: id must be a nonempty string')
    if not isinstance(record.get('text'), str):
        raise ValueError(f'{prefix}: text must be a string')
    if 'metadata' in record and not isinstance(record['metadata'], dict):
        raise ValueError(f'{prefix}: metadata must be an object')
    try:
        json.dumps(record, ensure_ascii=False).encode('utf-8')
    except UnicodeError as exc:
        raise ValueError(f'{prefix}: invalid Unicode scalar value') from exc
    if len(record['text']) > config.max_text_chars:
        raise ValueError(f'{prefix}: text exceeds max_text_chars')
    return record


def ingest(paths, config):
    docs, seen = [], {}
    def reject_constant(value):
        raise ValueError(f'non-JSON constant {value}')

    for path in paths:
        with open(path, 'rb') as stream:
            for line, raw in enumerate(stream, 1):
                try:
                    record = json.loads(raw.decode('utf-8'), parse_constant=reject_constant)
                except (ValueError, UnicodeError) as exc:
                    raise ValueError(f'{path}:{line}: malformed JSON: {exc}') from exc
                validate(record, path, line, config)
                if record['id'] in seen:
                    raise ValueError(f'{path}:{line}: duplicate id {record["id"]!r}; first at {seen[record["id"]]}')
                seen[record['id']] = f'{path}:{line}'
                docs.append(record)
                if len(docs) > config.max_documents:
                    raise ValueError('dataset exceeds max_documents')
    return sorted(docs, key=lambda d: d['id'])


def prepare(document, config):
    text = normalize(document['text'], config)
    return dict(document=document, id=document['id'], normalized=text, digest=stable_hash(text))


def exact_group(records):
    # Hashes only select candidates: compare normalized content to defeat collisions.
    groups = {}
    for record in records:
        groups.setdefault(record['normalized'], []).append(record['id'])
    return [(ids[0], other) for ids in groups.values() for other in ids[1:]]


def exact_edges(records):
    groups = {}
    for record in records:
        groups.setdefault(record['digest'], []).append(record)
    return sorted(edge for group in groups.values() for edge in exact_group(group))


def survivors(ids, edges):
    parent = {identifier: identifier for identifier in ids}

    def root(identifier):
        while parent[identifier] != identifier:
            parent[identifier] = parent[parent[identifier]]
            identifier = parent[identifier]
        return identifier

    for a, b in sorted(tuple(edge) for edge in edges):
        a, b = root(a), root(b)
        parent[max(a, b)] = min(a, b)
    return {identifier: root(identifier) for identifier in sorted(parent)}


def outputs(records, exact, near=()):
    exact_roots = survivors([r['id'] for r in records], exact)
    roots = survivors(exact_roots, list(exact) + list(near))
    kept, removed = [], []
    for record in sorted(records, key=lambda r: r['id']):
        identifier = record['id']
        if roots[identifier] == identifier:
            kept.append(record['document'])
        else:
            removed.append(dict(document=record['document'], reason='exact' if exact_roots[identifier] != identifier else 'near', survivor_id=roots[identifier]))
    return kept, removed
