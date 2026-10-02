import os
from pathlib import Path
import subprocess
import tempfile

with tempfile.TemporaryDirectory(prefix='philo13-a2-web-baseline-') as home:
    env = {**os.environ, 'HOME': home,
           'PATH': '/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/usr/bin:/bin'}
    command = ['uv', 'run', 'python', 'scripts/check_web_baseline.py', '--run']
    print('COMMAND', ' '.join(command), flush=True)
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    output = result.stdout + result.stderr
    Path('.tmp/philo-13-astra/a2-web-baseline.txt').write_text(output)
    print(output, flush=True)
    raise SystemExit(result.returncode)
