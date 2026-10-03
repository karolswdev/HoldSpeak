"""Scoped H-A1 verification; each pytest process has a fresh HOME."""
import os
import subprocess
import tempfile
from pathlib import Path

TESTS = [
 'tests/unit/test_philo13_meeting_parking.py',
 'tests/unit/test_philo13_workbench_parking.py',
 'tests/unit/test_db_schema_policy.py', 'tests/unit/test_reconcile.py',
 'tests/unit/test_db.py::TestDatabase',
 'tests/unit/test_db.py::TestTranscriptSearch',
 'tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot',
 'tests/unit/test_phase200_meeting_outcomes.py',
 'tests/unit/test_phase143_meeting_route_primitives.py',
 'tests/unit/test_meeting_import.py',
 'tests/unit/test_project_projection_services.py',
 'tests/unit/test_desk_projections.py',
 'tests/unit/test_mcp_tools.py',
 'tests/unit/test_thought_workbench_backend.py',
 'tests/unit/test_workbench_triage.py',
 'tests/unit/test_workbench_triage_kernel.py',
 'tests/unit/test_workbench_runner_migration.py',
 'tests/integration/test_phase143_workbench_route_adoption.py',
 'tests/unit/test_api_surface.py',
 'tests/unit/test_philo_graph_atlas.py',
 'tests/unit/test_philo13_astra_atlas.py',
]
for flags in [['--collect-only', '-q'], ['-q']]:
 with tempfile.TemporaryDirectory(prefix='philo13-a1-focused-') as home:
  cmd=['uv','run','pytest',*flags,*TESTS]
  print('COMMAND', ' '.join(cmd), flush=True)
  result=subprocess.run(cmd, env={**os.environ, 'HOME':home}, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  label='collection' if '--collect-only' in flags else 'run'
  path=Path(f'.tmp/philo-13-astra/a1-final-{label}.txt')
  path.write_text(result.stdout)
  print('FULL OUTPUT', path, flush=True)
  print(result.stdout[-2500:] if label=='collection' else result.stdout, flush=True)
  if result.returncode: raise SystemExit(result.returncode)
