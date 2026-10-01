#!/bin/bash
set -euo pipefail
phase_home=$(mktemp -d)
trap 'python3 -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
for script in gen_operations_json.py generate_capability_docs.py philo_openapi_reference.py philo_graph_reference.py; do
  env HOME="$phase_home" uv run --python 3.13 python "scripts/$script" --check
done
.githooks/dw check holdspeak-philo
git diff --check
