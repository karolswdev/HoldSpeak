"""Run exactly one B0 atlas case, then stop for Astra to read the observation."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

case_id, width, label = sys.argv[1:]
root = Path(__file__).resolve().parents[2]
out = root / '.tmp/graph-walk/philo-13-02' / label
out.mkdir(parents=True, exist_ok=False)
cmd = [
    '.githooks/dw', 'evidence', 'capture', 'holdspeak-philo', '13', '02', '--',
    'uv', 'run', '--extra', 'dev', 'python', 'scripts/graph_walk.py', 'run',
    '--atlas', 'docs/internal/philo/graph/atlas-phase13-astra.json',
    '--case', case_id, '--brain', 'astra', '--viewport', width,
    '--engine', 'none', '--no-build', '--out', str(out.relative_to(root)),
]
with tempfile.TemporaryDirectory(prefix='philo13-b0-command-') as home:
    env = {**os.environ, 'HOME': home,
           'PATH': '/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/usr/bin:/bin',
           'PLAYWRIGHT_BROWSERS_PATH': '/Users/karol/Library/Caches/ms-playwright'}
    with (out / 'command.log').open('w') as log:
        result = subprocess.run(cmd, cwd=root, env=env, stdout=log,
                                stderr=subprocess.STDOUT, text=True)
print('CAPTURE_EXIT', result.returncode)
records = list(out.glob('*/observation.json'))
for path in records:
    record = json.loads(path.read_text())
    provenance = record.get('provenance', {})
    hub_home = Path(provenance['hub']['home']).resolve()
    db_path = Path(provenance['db_path']).resolve()
    assert db_path.is_relative_to(hub_home), (hub_home, db_path)
    print(json.dumps({
        'observation': str(path.relative_to(root)),
        'verdict': record.get('verdict'), 'complete': record.get('complete'),
        'notes': record.get('notes'), 'shots': record.get('shots'),
        'initial_feedback': (record.get('initial_feedback') or {}).get('reading'),
        'terminal_outcome': record.get('terminal_outcome'),
        'touch': provenance.get('touch_mode'),
        'revision': provenance.get('revision'), 'dirty': provenance.get('dirty'),
        'db_path': str(db_path), 'hub_home': str(hub_home),
    }, indent=2))
if not records:
    print((out / 'command.log').read_text()[-4000:])
sys.exit(result.returncode)
