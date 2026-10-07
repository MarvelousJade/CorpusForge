"""Practice regression tests, intentionally separate from the regular suite."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
import pytest
from corpusforge.core import Config, stable_hash, prepare, exact_edges, exact_group, outputs
from corpusforge.pipeline import run, Interrupted


def test_cross_partition():
    # IDs land in different deterministic partitions when split into two shards.
    ids = []
    for parity in (0,1):
        ids.append(next(f'd{i}' for i in range(100) if int(stable_hash(f'd{i}'),16)%2 == parity))
    records = [prepare({'id': identifier, 'text': 'same'}, Config(workers=2, near=False)) for identifier in ids]
    kept, removed = outputs(records, exact_edges(records))
    assert len(kept) == 1
    assert kept[0]['id'] == min(ids)


def completion_replay(workers):
    def task(identifier):
        if identifier == 'z':
            time.sleep(.05)
        return prepare({'id': identifier, 'text': 'same'}, Config(near=False))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(task, identifier) for identifier in ('z','a')]
        records = [future.result() for future in as_completed(futures)]
    edges = exact_group(records)
    return {a for a,b in edges}


def test_survivor_concurrency():
    # Controlled completion-order replay, not a Ray scheduling benchmark.
    assert completion_replay(1) == completion_replay(2) == {'a'}


def test_resume_matches_clean(tmp_path):
    source = tmp_path/'source.jsonl'
    source.write_text('{"id":"z","text":"same"}\n{"id":"a","text":"same"}\n')
    cfg = Config(near=False)
    with pytest.raises(Interrupted):
        run(source, tmp_path/'resumed', cfg, stop_after='exact')
    run(source, tmp_path/'resumed', cfg, resume=True)
    run(source, tmp_path/'clean', cfg)
    assert (tmp_path/'resumed'/'kept.jsonl').read_bytes() == (tmp_path/'clean'/'kept.jsonl').read_bytes()
