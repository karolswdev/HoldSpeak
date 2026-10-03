import os
from pathlib import Path
import subprocess
import tempfile

tests = [
    'tests/unit/test_philo13_needs_you_fixture.py',
    'tests/unit/test_philo_graph_atlas.py',
    'tests/unit/test_philo13_astra_atlas.py',
    'tests/unit/test_philo13_fixture_rig.py',
    'tests/unit/test_philo13_graph_walk.py',
]
for flags, label in [(['--collect-only', '-q'], 'collection'), (['-q'], 'run')]:
    with tempfile.TemporaryDirectory(prefix='philo13-a2-python-') as home:
        command = ['uv', 'run', 'pytest', *flags, *tests]
        print('COMMAND', ' '.join(command), flush=True)
        result = subprocess.run(command, env={**os.environ, 'HOME': home,
                                'PLAYWRIGHT_BROWSERS_PATH': '/Users/karol/Library/Caches/ms-playwright'},
                                capture_output=True, text=True)
        output = result.stdout + result.stderr
        path = Path(f'.tmp/philo-13-astra/a2-python-{label}.txt')
        path.write_text(output)
        print('FULL OUTPUT', path, flush=True)
        print(output[-3000:] if label == 'collection' else output, flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)
