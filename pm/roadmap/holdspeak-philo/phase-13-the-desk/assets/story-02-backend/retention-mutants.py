"""Restore each real legacy deletion method, prove row loss, then restore bytes."""
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

CASES = [
    ('holdspeak/db/meetings.py', 'MeetingRepository', 'delete_meeting',
     'tests/unit/test_philo13_meeting_parking.py::test_repository_parks_and_restores_without_deleting_retained_work'),
    ('holdspeak/db/workbenches.py', 'WorkbenchItemRepository', 'delete',
     'tests/unit/test_philo13_workbench_parking.py::test_legacy_repository_delete_parks_and_repeats_are_idempotent'),
]

def method(text, cls, name):
    klass = next(n for n in ast.parse(text).body if isinstance(n, ast.ClassDef) and n.name == cls)
    node = next(n for n in klass.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return node.lineno - 1, node.end_lineno

for filename, cls, name, test in CASES:
    path = Path(filename)
    original = path.read_bytes()
    current = original.decode().splitlines(keepends=True)
    legacy = subprocess.check_output(['git', 'show', f'c7073f9:{filename}'], text=True)
    start, end = method(original.decode(), cls, name)
    oldstart, oldend = method(legacy, cls, name)
    try:
        path.write_text(''.join(current[:start] + legacy.splitlines(keepends=True)[oldstart:oldend] + current[end:]))
        with tempfile.TemporaryDirectory(prefix='philo13-retention-red-') as home:
            result = subprocess.run(['uv', 'run', 'pytest', '-q', test], env={**os.environ, 'HOME': home}, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(f'RED {filename}:{cls}.{name} from c7073f9', flush=True)
        print(result.stdout, flush=True)
        assert result.returncode == 1, result.returncode
        assert 'assert retained_row is not None' in result.stdout, 'Failure must demonstrate lost row'
    finally:
        path.write_bytes(original)
        assert path.read_bytes() == original
        print('RESTORED SHA256', hashlib.sha256(original).hexdigest(), filename, flush=True)

with tempfile.TemporaryDirectory(prefix='philo13-retention-green-') as home:
    result = subprocess.run(['uv', 'run', 'pytest', '-q', *[row[3] for row in CASES]], env={**os.environ, 'HOME': home})
assert result.returncode == 0
