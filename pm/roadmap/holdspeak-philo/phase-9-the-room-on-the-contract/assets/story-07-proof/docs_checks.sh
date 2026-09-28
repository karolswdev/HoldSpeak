#!/bin/bash
# PHILO-9-07: the generated docs, the Documentation Navigation checks and the residual census.
HERE=$(cd "$(dirname "$0")" && pwd)
WT=$(cd "$HERE/../../../../../.." && pwd)
export HOME=$(mktemp -d)
PY=$WT/.venv/bin/python
cd "$WT"
rc=0
for s in "gen_operations_json.py --check" "gen_mcp_sidecar_doc.py --check" "check_docs.py" "philo_repository_census.py --check" "philo_api_reference.py --check" "philo_boundary_census.py --check" "philo_doctor_reference.py --check" "philo_config_reference.py --check" "philo_graph_reference.py --check" "validate_architecture.py" "generate_capability_docs.py --check" "check_doc_coverage.py --check" "residual_census.py --check"; do
  echo "== $s"; $PY scripts/$s 2>&1 | tail -2; r=${PIPESTATUS[0]}; [ $r -ne 0 ] && { echo "rc=$r"; rc=1; }
done
$PY -m unittest discover -s tests/unit -p test_docs_navigation.py 2>&1 | tail -1; [ ${PIPESTATUS[0]} -ne 0 ] && rc=1
$PY scripts/check_docs.py pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-07-the-project-delegation-grant.md pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md 2>&1 | tail -1
echo "DOCS RC=$rc"
exit $rc
