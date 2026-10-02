import os
from pathlib import Path
import subprocess
import tempfile

tests = [
    'src/desk/needsYou.test.ts',
    'src/desk/attention.test.ts',
    'src/desk/chair/arrivalOneThing.test.tsx',
    'src/desk/chair/arrivalRefresh.test.tsx',
    'src/desk/chair/arrivalAttention.test.tsx',
    'src/desk/chair/arrivalQuietDesk.test.tsx',
    'src/desk/chair/arrivalCoverage.test.tsx',
]
for command, label in [
    (['npx', 'vitest', 'run', *tests, '--reporter=verbose'], 'vitest'),
    (['npx', 'tsc', '--noEmit', '--pretty', 'false'], 'typecheck'),
]:
    with tempfile.TemporaryDirectory(prefix='philo13-a2-web-') as home:
        env = {**os.environ, 'HOME': home,
               'PATH': '/Users/karol/.nvm/versions/node/v22.21.0/bin:/opt/homebrew/bin:/usr/bin:/bin'}
        print('COMMAND', ' '.join(command), flush=True)
        result = subprocess.run(command, cwd='web', env=env, capture_output=True, text=True)
        output = result.stdout + result.stderr
        Path(f'.tmp/philo-13-astra/a2-final-{label}.txt').write_text(output + f'\nEXIT {result.returncode}\n')
        print(output, flush=True)
        print('EXIT', result.returncode, flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
