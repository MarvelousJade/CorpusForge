from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_local_documentation_links():
    files = list(ROOT.glob('*.md')) + list((ROOT/'docs').rglob('*.md'))
    for path in files:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            target = target.split('#')[0]
            assert (path.parent/target).exists(), f'{path}: broken link {target}'


def test_workflow_documents_present():
    assert '## Development and interview preparation workflow' in (ROOT/'AGENTS.md').read_text(encoding='utf-8')
    for name in ('engineering-journal.md', 'interview-guide.md'):
        assert (ROOT/'docs'/name).stat().st_size > 1000
