import pytest
import ray
from corpusforge.core import Config
from corpusforge.pipeline import run, Interrupted


def test_ray_resume(tmp_path):
    source = tmp_path/'data.jsonl'
    source.write_text('{"id":"z","text":"a b c d"}\n{"id":"a","text":"a b c d"}\n{"id":"b","text":"a b c d e"}\n')
    cfg = Config(workers=1, batch_size=1, bands=8, rows=1, threshold=.5)
    try:
        with pytest.raises(Interrupted):
            run(source, tmp_path/'interrupted', cfg, 'ray', stop_after='candidates')
        run(source, tmp_path/'interrupted', cfg, 'ray', resume=True)
        run(source, tmp_path/'clean', cfg, 'ray')
        for name in ('kept.jsonl', 'removed.jsonl'):
            assert (tmp_path/'interrupted'/name).read_bytes() == (tmp_path/'clean'/name).read_bytes()
    finally:
        ray.shutdown()
