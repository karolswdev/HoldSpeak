"""Run the unchanged 393 Speak test three times on an archived base runtime."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path.cwd()
logs = root / '.tmp/philo-12-01'
base = logs / 'base-27d8bf1a'
node = 'tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393'
results = []
for index in range(1, 4):
    with tempfile.TemporaryDirectory(prefix='philo12-base-speak-') as home:
        temp = Path(home) / 'tmp'
        temp.mkdir()
        env = {**os.environ, 'HOME': home, 'TMPDIR': str(temp),
               'PYTHONPATH': str(base),
               'PATH': '/Users/karol/.nvm/versions/node/v22.21.0/bin:' + os.environ['PATH'],
               'PLAYWRIGHT_BROWSERS_PATH': '/Users/karol/Library/Caches/ms-playwright',
               'npm_config_cache': '/Users/karol/.npm'}
        provenance = subprocess.run([sys.executable, '-c', 'import holdspeak,sys; print(sys.version); print(holdspeak.__file__)'], cwd=base, env=env, capture_output=True, text=True, check=True).stdout
        print(f'BASE 27d8bf1a RUN {index}: {node}\n{provenance}', flush=True)
        run = subprocess.run([sys.executable, '-m', 'pytest', '-q', '--basetemp', str(Path(home) / 'pytest'), node], cwd=base, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        (logs / f'base-speak-{index}.log').write_text(provenance + run.stdout)
        print(run.stdout, end='', flush=True)
        results.append({'run': index, 'node': node, 'exit_code': run.returncode})
(logs / 'base-speak-results.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(int(any(row['exit_code'] for row in results)))
