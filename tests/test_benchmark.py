import json
from corpusforge.benchmark import generate
import corpusforge.benchmark as module


def test_generator_reproducible(tmp_path):
    generate(tmp_path/'a', 24, 42)
    generate(tmp_path/'b', 24, 42)
    for i in range(4):
        assert (tmp_path/'a'/f'{i}.jsonl').read_bytes() == (tmp_path/'b'/f'{i}.jsonl').read_bytes()
    docs = [json.loads(line) for p in (tmp_path/'a').glob('*.jsonl') for line in p.read_text().splitlines()]
    assert len(docs) == 24
    assert len({d['id'] for d in docs}) == 24
    assert {d['metadata']['kind'] for d in docs} == {0,1,2,3}


def test_sequential_measurements_have_no_idle_ray(tmp_path, monkeypatch):
    state = {'ray': False}
    calls = []
    monkeypatch.setattr(module.ray, 'shutdown', lambda: state.update(ray=False))
    def fake_run(source, target, config, backend):
        if backend == 'sequential':
            assert not state['ray'], 'sequential memory includes idle Ray runtime'
        else:
            state['ray'] = True
        calls.append(backend)
        target.mkdir(parents=True)
        (target/'kept.jsonl').write_text('{"id":"a"}\n')
        return {'stage_seconds': {}, 'startup_seconds': 0., 'candidates': 0, 'quality': {'status': 'stub'}}
    class FakeMonitor:
        process_rss = tree_rss = object_used = object_samples = 0
        telemetry_errors = []
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr(module, 'run', fake_run)
    monkeypatch.setattr(module, 'Monitor', FakeMonitor)
    module.benchmark(tmp_path/'bench', [4], 3, [(2,1,4,2)])
    assert calls == ['sequential']*3 + ['ray']*3
