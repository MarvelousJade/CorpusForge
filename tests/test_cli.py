import json
from pathlib import Path
import subprocess
import sys


def invoke(*args):
    return subprocess.run([sys.executable, '-m', 'corpusforge', *map(str,args)], capture_output=True, text=True)


def test_cli_and_resume(tmp_path):
    source = Path(__file__).resolve().parents[1]/'data'/'sample'
    result = invoke('run', '--input', source, '--output', tmp_path/'out', '--stop-after', 'exact')
    assert result.returncode == 2 and 'interrupted after exact' in result.stderr
    result = invoke('run', '--input', source, '--output', tmp_path/'out', '--resume')
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['removed'] >= 1


def test_cli_diagnostics(tmp_path):
    source = tmp_path/'bad.jsonl'
    source.write_text('{}\n')
    result = invoke('run', '--input', source, '--output', tmp_path/'out')
    assert result.returncode == 2
    assert 'bad.jsonl:1' in result.stderr


def test_limits_and_invalid_configuration(tmp_path):
    source = tmp_path/'data.jsonl'
    source.write_text('{"id":"a","text":"a"}\n{"id":"b","text":"b"}\n')
    result = invoke('run', '--input', source, '--output', tmp_path/'out', '--max-documents', 1)
    assert result.returncode == 2 and 'max_documents' in result.stderr
    result = invoke('run', '--input', source, '--output', tmp_path/'out', '--rows', 0)
    assert result.returncode == 2 and 'rows must be positive' in result.stderr
