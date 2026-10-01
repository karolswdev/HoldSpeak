"""Repeat only full-suite failures, sequentially, with a fresh HOME per node."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path.cwd()
log_dir = root / '.tmp/philo-12-01'
nodes = json.loads((log_dir / 'failed-nodes.json').read_text())
round_id = sys.argv[1]
results = []
for index, node in enumerate(nodes, 1):
    print(f'ROUND {round_id} NODE {index}: {node}', flush=True)
    with tempfile.TemporaryDirectory(prefix='philo12-serial-') as home:
        temp = Path(home) / 'tmp'
        temp.mkdir()
        env = {
            **os.environ,
            'HOME': home,
            'TMPDIR': str(temp),
            'PATH': '/Users/karol/.nvm/versions/node/v22.21.0/bin:' + os.environ['PATH'],
            'PLAYWRIGHT_BROWSERS_PATH': '/Users/karol/Library/Caches/ms-playwright',
            'npm_config_cache': '/Users/karol/.npm',
        }
        command = ['uv', 'run', '--python', '3.13', 'pytest', '-q', '--basetemp', str(Path(home) / 'pytest'), node]
        run = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        log = log_dir / f'serial-{round_id}-{index:02d}.log'
        log.write_text(run.stdout)
        print(run.stdout, end='', flush=True)
        results.append({'node': node, 'exit_code': run.returncode, 'log': str(log.relative_to(root))})
(log_dir / f'serial-{round_id}-results.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(int(any(result['exit_code'] != 0 for result in results)))
