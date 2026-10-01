#!/bin/bash
set -euo pipefail
phase_home=$(mktemp -d)
trap 'uv run --python 3.13 python -c "import shutil,sys; shutil.rmtree(sys.argv[1])" "$phase_home"' EXIT
export HOME="$phase_home"

uv run --python 3.13 pytest --collect-only -q tests/unit/test_philo12_brief_read.py --basetemp "$phase_home/pytest-collect"
uv run --python 3.13 pytest -q tests/unit/test_philo12_brief_read.py --basetemp "$phase_home/pytest-route"
