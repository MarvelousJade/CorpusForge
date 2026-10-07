"""MinHash → LSH → exact verification; independently written, not copied."""
from collections import defaultdict
from itertools import combinations
import hashlib
import numpy as np

PRIME = np.uint64(4294967291)


def shingles(text, size):
    words = text.split()
    return sorted({' '.join(words[i:i+size]) for i in range(len(words)-size+1)})


def signature(tokens, config):
    if not tokens:
        return []
    rng = np.random.default_rng(config.seed)
    count = config.bands * config.rows
    a = rng.integers(1, int(PRIME), count, dtype=np.uint64)
    b = rng.integers(0, int(PRIME), count, dtype=np.uint64)
    result = np.full(count, PRIME, dtype=np.uint64)
    # 32-bit field keeps a*x+b within uint64; avoid overflow-biased arithmetic.
    for token in tokens:
        value = np.uint64(int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], 'big') % int(PRIME))
        result = np.minimum(result, (a * value + b) % PRIME)
    return result.astype(object).tolist()


def add_signature(record, config):
    tokens = shingles(record['normalized'], config.shingle_size) if config.near else []
    return dict(record, shingles=tokens, signature=signature(tokens, config))


def band_keys(record, config):
    sig = record['signature']
    return [(band, tuple(sig[band*config.rows:(band+1)*config.rows])) for band in range(config.bands)] if sig else []


def candidates(records, config):
    buckets = defaultdict(list)
    for record in records:
        for key in band_keys(record, config):
            buckets[key].append(record['id'])
    result = set()
    for ids in buckets.values():
        for pair in combinations(sorted(set(ids)), 2):
            result.add(pair)
            if len(result) > config.max_candidates:
                raise ValueError('LSH candidates exceed max_candidates')
    return sorted(result)


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if a or b else 0.0


def verify(records, pairs, threshold):
    by_id = {r['id']: r['shingles'] for r in records}
    return [tuple(pair) for pair in pairs if by_id[pair[0]] and by_id[pair[1]] and jaccard(by_id[pair[0]], by_id[pair[1]]) >= threshold]


def oracle(records, pairs, config):
    if len(records) > 500:
        return {'status': 'skipped', 'reason': 'oracle limited to 500 exact survivors'}
    truth = set(verify(records, combinations(sorted(r['id'] for r in records), 2), config.threshold))
    proposed = set(map(tuple, pairs))
    hits = truth & proposed
    return dict(status='measured', oracle_pairs=len(truth), hits=len(hits), misses=len(truth-proposed),
                recall=len(hits)/len(truth) if truth else None,
                precision=len(hits)/len(proposed) if proposed else None)
