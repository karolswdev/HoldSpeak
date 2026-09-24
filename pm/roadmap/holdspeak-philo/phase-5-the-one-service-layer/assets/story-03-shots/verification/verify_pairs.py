"""Recompute PHILO-5-03 pairs from explicitly selected, retained actual runs."""
from pathlib import Path
import hashlib
import json
import sys
ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'holdspeak/operations.py').exists())
sys.path.insert(0, str(ROOT))
from scripts.philo5_pairs import build_pairs
ASSETS = Path(__file__).resolve().parents[1]

def main():
    source = json.loads((ASSETS / 'pairs-input.json').read_text())
    assert len(source['pairs']) == 20
    index = build_pairs(source, output=ASSETS / 'pairs.json')
    for row in index['pairs']:
        print(row['pair_id'], row['browser']['run_id'], row['op']['run_id'],
              row['verdict'].upper(), f"{row['op']['duration_s']:.3f}s")
        assert row['verdict'] == 'pass', row
        assert row['browser']['viewport'] == 1440
        op = json.loads((ROOT / row['op']['observation_path']).read_text())
        assert op['complete'] and op['verdict'] == 'pass'
        assert op['before']['headless'] and op['after']['headless'] and not op['shots']
        assert 'graph-walk-home-' in op['provenance']['db_path']
        mode = op['provenance']['engine_mode']
        digest = op['provenance']['engine_replay_sha256']
        assert bool(digest) == (mode == 'replayed')
    faces = json.loads((ASSETS / 'faces.json').read_text())['browser_runs']
    for face in faces:
        obs = json.loads((ROOT / face['observation']).read_text())
        assert obs['complete'] and obs['verdict'] == 'pass'
        assert obs['viewport'] == face['viewport']
        assert 'graph-walk-home-' in obs['provenance']['db_path']
        for shot in face['shots']: assert (ROOT / shot).is_file(), shot
    for run in json.loads((ASSETS / 'runs.json').read_text())['runs']:
        assert hashlib.sha256((ROOT / run['path']).read_bytes()).hexdigest() == run['sha256']
    print('PAIRS', index['counts'])
    print('BROWSER OBSERVATIONS', len(faces), 'FACE CLAIMS REMAIN BROWSER-ONLY')
    for atlas_path in ('docs/internal/philo/graph/atlas.json', 'docs/internal/philo/graph/atlas-phase3.json'):
        cases = json.loads((ROOT / atlas_path).read_text())['cases']
        print('ATLAS', atlas_path, 'cases', len(cases), 'op siblings', sum(c['id'].endswith('.op') for c in cases), 'replays', sum(c['id'].endswith('.replayed') for c in cases))

if __name__ == '__main__': main()
