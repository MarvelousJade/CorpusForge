from dataclasses import replace
import json
import pytest
import ray
from corpusforge.core import Config
from corpusforge.pipeline import run
from corpusforge.ray_backend import pair_batch, initialize


@pytest.mark.parametrize('batch,workers', [(1,1), (3,2)])
def test_ray_parity(tmp_path, batch, workers):
    source = tmp_path / 'input'
    source.mkdir()
    texts = ['a b c d e f g h', ' A B C D E F G H ', 'a b c d e f g h i',
             'q r s t u', 'x x x x x', 'x x x x', 'hi', 'hi', '', '  ']
    for i, text in enumerate(texts):
        document = {'id': f'{9-i:02}', 'text': text}
        if i % 3:
            document['metadata'] = {'index': i} if i % 2 else {'source': ['café'], 'nested': {'ok': True}}
        (source / f'{i}.jsonl').write_text(json.dumps(document, ensure_ascii=False)+'\n', encoding='utf-8')
    cfg = Config(batch_size=batch, workers=workers, bands=32, rows=1, threshold=.5)
    try:
        run(source, tmp_path/'seq', cfg)
        run(source, tmp_path/'ray', cfg, 'ray')
        for name in ('prepared.json', 'exact.json', 'kept.jsonl', 'removed.jsonl', 'candidates.json', 'verified.json'):
            assert (tmp_path/'seq'/name).read_bytes() == (tmp_path/'ray'/name).read_bytes()
    finally:
        ray.shutdown()


def test_worker_failure_surfaces():
    initialize(Config(workers=1))
    try:
        ds = ray.data.from_items([{'id': str(i), 'band': 'same'} for i in range(4)])
        with pytest.raises(Exception, match='exceeds max_candidates'):
            ds.groupby('band').map_groups(pair_batch, fn_kwargs={'limit': 1}).take_all()
    finally:
        ray.shutdown()
