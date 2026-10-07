from itertools import combinations
from corpusforge.core import Config, prepare, survivors
from corpusforge.near import add_signature, signature, shingles, candidates, verify, jaccard, oracle


def fixture(texts, config):
    return [add_signature(prepare({'id': str(i), 'text': text}, config), config) for i, text in enumerate(texts)]


def test_boundary_short_repetitive():
    assert jaccard(['a', 'b'], ['b', 'c']) == 1/3
    cfg = Config(shingle_size=1, threshold=1/3)
    records = fixture(['a b', 'b c', ''], cfg)
    assert verify(records, [('0', '1'), ('0', '2')], cfg.threshold) == [('0', '1')]
    assert shingles('x x x x', 3) == ['x x x']
    assert shingles('a b', 3) == []
    assert signature(['x'], cfg) == signature(['x'], cfg)
    assert signature(['x'], cfg) != signature(['x'], Config(seed=43))


def test_oracle_candidates_and_misses():
    cfg = Config(shingle_size=1, bands=64, rows=1, threshold=.5)
    records = fixture(['a b c d', 'a b c e', 'q r s', 'a b c d'], cfg)
    pairs = candidates(records, cfg)
    truth = verify(records, combinations(['0','1','2','3'], 2), cfg.threshold)
    assert set(truth) <= set(pairs)
    assert oracle(records, pairs, cfg)['misses'] == 0
    assert oracle(records, [], cfg)['misses'] == len(truth)


def test_transitive_cluster():
    cfg = Config(shingle_size=1, threshold=.5)
    records = fixture(['a b', 'a b c', 'b c'], cfg)
    edges = verify(records, combinations(['0','1','2'], 2), cfg.threshold)
    assert ('0', '2') not in edges
    assert survivors(['2','1','0'], edges) == {'0':'0', '1':'0', '2':'0'}
