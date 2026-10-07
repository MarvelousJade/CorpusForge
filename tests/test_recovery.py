from dataclasses import replace
import json
import pytest
from corpusforge.core import Config
from corpusforge.pipeline import run, Interrupted
from corpusforge.persistence import Store, output_lock


@pytest.mark.parametrize('stage', ['prepared', 'exact', 'candidates', 'verified', 'decisions'])
def test_resume(tmp_path, stage):
    source = tmp_path/'data.jsonl'
    source.write_text('\n'.join(json.dumps({'id': str(i), 'text': t}) for i,t in enumerate(['a b c d', 'a b c d', 'a b c d e', 'other']))+'\n')
    cfg = Config(bands=32, rows=1, threshold=.5)
    with pytest.raises(Interrupted):
        run(source, tmp_path/'interrupted', cfg, stop_after=stage)
    # Partial/uncommitted data isn't trusted: rerun that stage, not an individual task.
    (tmp_path/'interrupted'/'uncommitted.json.tmp').write_text('partial')
    run(source, tmp_path/'interrupted', cfg, resume=True)
    run(source, tmp_path/'clean', cfg)
    for filename in ('kept.jsonl', 'removed.jsonl'):
        assert (tmp_path/'clean'/filename).read_bytes() == (tmp_path/'interrupted'/filename).read_bytes()


def test_incompatible_and_corrupted(tmp_path):
    source = tmp_path/'data.jsonl'
    source.write_text('{"id":"a","text":"a"}\n')
    cfg = Config()
    run(source, tmp_path/'out', cfg)
    with pytest.raises(ValueError, match='configuration'):
        run(source, tmp_path/'out', replace(cfg, seed=1), resume=True)
    source.write_text('{"id":"b","text":"b"}\n')
    with pytest.raises(ValueError, match='inputs'):
        run(source, tmp_path/'out', cfg, resume=True)
    source.write_text('{"id":"a","text":"a"}\n')
    (tmp_path/'out'/'prepared.json').write_text('[]')
    with pytest.raises(ValueError, match='corrupted'):
        run(source, tmp_path/'out', cfg, resume=True)


def test_interrupted_stage_reruns(tmp_path, monkeypatch):
    source = tmp_path/'data.jsonl'
    source.write_text('{"id":"z","text":"same"}\n{"id":"a","text":"same"}\n')
    original = Store.stage
    def crash(self, name, value, seconds):
        if name == 'exact':
            (self.root/'exact.json').write_text('partial')
            raise Interrupted('mid-stage interruption')
        original(self, name, value, seconds)
    monkeypatch.setattr(Store, 'stage', crash)
    with pytest.raises(Interrupted):
        run(source, tmp_path/'out', Config())
    monkeypatch.setattr(Store, 'stage', original)
    run(source, tmp_path/'out', Config(), resume=True)
    run(source, tmp_path/'clean', Config())
    assert (tmp_path/'out'/'kept.jsonl').read_bytes() == (tmp_path/'clean'/'kept.jsonl').read_bytes()


def test_single_writer(tmp_path):
    with output_lock(tmp_path/'out'):
        with pytest.raises(ValueError, match='locked'):
            with output_lock(tmp_path/'out'):
                pass


def test_missing_artifact_and_empty_input(tmp_path):
    source = tmp_path/'empty.jsonl'
    source.write_text('')
    run(source, tmp_path/'out', Config())
    assert (tmp_path/'out'/'kept.jsonl').read_bytes() == b''
    (tmp_path/'out'/'kept.jsonl').unlink()
    with pytest.raises(ValueError, match='missing'):
        run(source, tmp_path/'out', Config(), resume=True)
