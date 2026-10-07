"""Ray Data does batches and global groups; coordinator owns bounded clustering."""
import json
from itertools import combinations
import ray
from .core import prepare, exact_group
from .near import add_signature, band_keys


def compute_batch(batch, config):
    rows = [add_signature(prepare(json.loads(payload), config), config) for payload in batch['payload']]
    return {'payload': [json.dumps(row) for row in rows], 'digest': [row['digest'] for row in rows]}


def exact_batch(batch):
    rows = [json.loads(payload) for payload in batch['payload']]
    return {'a': [a for a, _ in exact_group(rows)], 'b': [b for _, b in exact_group(rows)]}


def expand(row, config):
    record = json.loads(row['payload'])
    return [{'band': json.dumps(key), 'id': record['id']} for key in band_keys(record, config)]


def pair_batch(batch, limit):
    ids = sorted(set(batch['id']))
    if len(ids)*(len(ids)-1)//2 > limit:
        raise ValueError('band group exceeds max_candidates')
    pairs = list(combinations(ids, 2))
    return {'a': [a for a,b in pairs], 'b': [b for a,b in pairs]}


def bounded_pairs(dataset, limit):
    pairs = set()
    for row in dataset.iter_rows():
        pairs.add((row['a'], row['b']))
        if len(pairs) > limit:
            raise ValueError('global candidates exceed max_candidates')
    return sorted(pairs)


def initialize(config):
    if not ray.is_initialized():
        # Ray Data control actors reserve fractional CPUs. With exactly one
        # logical CPU, a 1-CPU read task can otherwise wait indefinitely.
        ray.init(num_cpus=config.workers + 1, include_dashboard=False, object_store_memory=128*1024*1024, log_to_driver=False)


def prepare_data(paths, config):
    # A JSON payload isolates heterogeneous user metadata from Arrow schema inference.
    # read_text is intentional: strict source/line validation happens before this step.
    dataset = ray.data.read_text([str(p.resolve()) for p in paths])
    dataset = dataset.map(lambda row: {'payload': row['text']})
    transformed = dataset.map_batches(compute_batch, batch_format='numpy', batch_size=config.batch_size,
                                     fn_kwargs={'config': config}, concurrency=config.workers).materialize()
    return sorted([json.loads(row['payload']) for row in transformed.iter_rows()], key=lambda r: r['id'])


def exact_data(records, config):
    dataset = ray.data.from_items([{'payload': json.dumps(r), 'digest': r['digest']} for r in records])
    return bounded_pairs(dataset.groupby('digest').map_groups(exact_batch, batch_format='numpy'), config.max_candidates)


def candidate_data(records, config):
    if not records or not any(r['signature'] for r in records):
        return []
    dataset = ray.data.from_items([{'payload': json.dumps(r)} for r in records])
    bands = dataset.flat_map(expand, fn_kwargs={'config': config}, concurrency=config.workers)
    grouped = bands.groupby('band').map_groups(pair_batch, batch_format='numpy', fn_kwargs={'limit': config.max_candidates})
    return bounded_pairs(grouped, config.max_candidates)
