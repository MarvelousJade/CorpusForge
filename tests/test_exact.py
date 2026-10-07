import json
import pytest
from corpusforge.core import Config, ingest, prepare, exact_edges, outputs


def test_cross_file_deterministic_metadata(tmp_path):
    docs = [{'id': 'z', 'text': ' Hello\nWORLD ', 'metadata': {'a': 1}},
            {'id': 'a', 'text': 'hello world'}, {'id': 'empty', 'text': ''},
            {'id': 'blank', 'text': '  '}]
    paths = []
    for index, doc in enumerate(docs):
        path = tmp_path / f'{index}.jsonl'
        path.write_text(json.dumps(doc) + '\n')
        paths.append(path)
    records = [prepare(d, Config()) for d in ingest(paths[::-1], Config())]
    kept, removed = outputs(records, exact_edges(records))
    assert [d['id'] for d in kept] == ['a', 'blank']
    assert removed[-1]['document'] == docs[0]
    assert outputs(records[::-1], exact_edges(records[::-1])) == (kept, removed)


@pytest.mark.parametrize('raw', ['{', '{}', '{"id":"a","text":4}', '{"id":"a","text":"", "metadata":0}'])
def test_bad_records(tmp_path, raw):
    path = tmp_path / 'bad.jsonl'
    path.write_text(raw)
    with pytest.raises(ValueError, match=r'bad.jsonl:1'):
        ingest([path], Config())


def test_duplicate_ids(tmp_path):
    path = tmp_path / 'bad.jsonl'
    path.write_text('{"id":"a","text":""}\n' * 2)
    with pytest.raises(ValueError, match=r'bad.jsonl:2: duplicate id'):
        ingest([path], Config())


def test_hash_collision_and_normalization():
    records = [prepare({'id': str(i), 'text': t}, Config()) for i, t in enumerate(['a', 'b'])]
    for r in records:
        r['digest'] = 'collision'
    assert exact_edges(records) == []
    assert prepare({'id': 'x', 'text': 'A  B'}, Config(casefold=False, whitespace=False))['normalized'] == 'A  B'
