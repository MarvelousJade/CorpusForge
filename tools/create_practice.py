"""Create isolated, tagged practice defects after main has passed.

Does not modify main. Each checkpoint starts from the same passing base.
"""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
worktree = root.parent/'CorpusForge-learning'


def git(*args, cwd=root):
    return subprocess.check_output(['git', *args], cwd=cwd, text=True).strip()


def replace(path, old, new):
    text = path.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise ValueError(f'nonunique patch at {path}')
    path.write_text(text.replace(old,new), encoding='utf-8')


base = git('rev-parse', 'main')
if git('status', '--porcelain'):
    raise SystemExit('Commit verified main changes before creating practice checkpoints')
git('worktree', 'add', '-b', 'learning/exercises', str(worktree), base)
patches = [
    ('partition', 'test_cross_partition', [
        ('corpusforge/core.py', "return dict(document=document, id=document['id'], normalized=text, digest=stable_hash(text))", "return dict(document=document, id=document['id'], normalized=text, digest=stable_hash(text), partition=int(stable_hash(document['id']),16)%config.workers)"),
        ('corpusforge/core.py', "groups.setdefault(record['digest'], []).append(record)", "groups.setdefault((record['partition'], record['digest']), []).append(record)")]),
    ('survivor', 'test_survivor_concurrency', [
        ('corpusforge/core.py', "return [(min(ids), other) for ids in groups.values() for other in sorted(ids) if other != min(ids)]", "return [(ids[0], other) for ids in groups.values() for other in ids[1:]]")]),
    ('resume', 'test_resume_matches_clean', [
        ('corpusforge/persistence.py', "if name in self.manifest['stages']:\n            return json.loads", "if name in self.manifest['stages']:\n            if name == 'exact':\n                return []\n            return json.loads")])]
receipts = []
for index, (name, test, edits) in enumerate(patches):
    if index:
        # Preserve history and tags while restoring the passing source tree.
        git('restore', '--source', base, '--staged', '--worktree', '.', cwd=worktree)
        git('commit', '-m', 'practice: restore passing baseline before next scenario', cwd=worktree)
    for filename, old, new in edits:
        replace(worktree/filename, old, new)
    (worktree/'PRACTICE_CHECKPOINT.md').write_text(
        f'# Practice checkpoint: {name}\n\nIntentionally defective learning material. '
        f'Passing base: `{base}`. Main is not modified.\n\n'
        f'Reproduce: `python -m pytest practice_regressions/test_scenarios.py::{test} -q`.\n'
        'Symptoms and spoiler boundaries: `docs/learning/EXERCISES.md`.\n', encoding='utf-8')
    git('add', '.', cwd=worktree)
    git('diff', '--cached', '--check', cwd=worktree)
    git('commit', '-m', f'practice: isolated {name} defect (intentionally failing)', cwd=worktree)
    git('tag', f'practice/{name}', cwd=worktree)
    receipt = subprocess.run([sys.executable, '-m', 'pytest', f'practice_regressions/test_scenarios.py::{test}', '-q', '--tb=short'], cwd=worktree, text=True, capture_output=True)
    print(f'\n{name} {git("rev-parse", "HEAD", cwd=worktree)} expected failure, exit={receipt.returncode}\n{receipt.stdout}\n{receipt.stderr}', flush=True)
    if receipt.returncode != 1:
        raise AssertionError('Expected a regression failure, not a collection error or pass')
    receipts.append((name, git('rev-parse','HEAD',cwd=worktree)))
print('Main remains at', base)
print('Checkpoints:', receipts)
