#!/bin/bash
set -euo pipefail
mkdir -p .tmp/philo-12-01/base-27d8bf1a
git archive 27d8bf1a holdspeak web tests scripts agent uat pyproject.toml uv.lock hatch_build.py docs/trust-destinations.json docs/product-language.json | tar -x -C .tmp/philo-12-01/base-27d8bf1a
env PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH npm ci --prefix .tmp/philo-12-01/base-27d8bf1a/web
