#!/usr/bin/env bash
# Phase 51 dogfood: prove the public-docs hygiene guard works both ways.
# No mic/LLM. Drives the doc-drift guard directly: it passes on the clean tree,
# catches a planted leak, and goes green again after revert. Run from anywhere:
#   bash pm/roadmap/holdspeak/phase-51-public-docs-hygiene/dogfood.sh
set -u
cd "$(git rev-parse --show-toplevel)"
GUARD='tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_leaks_roadmap_vocabulary'
PASS=1

echo "== Phase 51 dogfood: public-docs hygiene =="
echo

echo "-- 1. clean tree: the roadmap-vocabulary guard passes --"
if uv run pytest -q "$GUARD" >/tmp/hs51_a.txt 2>&1; then
  echo "PASS (guard green on clean tree): $(tail -1 /tmp/hs51_a.txt)"
else
  echo "UNEXPECTED FAIL on clean tree"; cat /tmp/hs51_a.txt; PASS=0
fi
echo

echo "-- 2. in-scope leak grep (README + docs/*.md, case-insensitive) is empty --"
HITS=$(grep -rInE '\bHS-[0-9]{2}-?[0-9]*\b|\bphase[ -][0-9]+\b|\bPMO\b|\bcloseout\b|the current roadmap' \
  README.md docs/*.md -i | grep -v 'docs/internal/' || true)
if [ -z "$HITS" ]; then
  echo "PASS (no in-scope roadmap vocabulary)"
else
  echo "UNEXPECTED in-scope hits:"; echo "$HITS"; PASS=0
fi
echo

echo "-- 3. plant a leak in a user-facing doc: the guard must go red --"
printf '\nPlanted dogfood leak: scheduled for phase 99.\n' >> docs/USER_GUIDE.md
if uv run pytest -q "$GUARD" >/tmp/hs51_b.txt 2>&1; then
  echo "UNEXPECTED PASS (guard missed the planted leak)"; PASS=0
else
  echo "PASS (guard caught the planted leak):"
  grep -E 'USER_GUIDE.md:[0-9]+' /tmp/hs51_b.txt | head -1 | sed 's/^E *//'
fi
echo

echo "-- 4. revert: the guard is green again and the tree is clean --"
git checkout -- docs/USER_GUIDE.md
if uv run pytest -q "$GUARD" >/tmp/hs51_c.txt 2>&1; then
  echo "PASS (guard green after revert): $(tail -1 /tmp/hs51_c.txt)"
else
  echo "UNEXPECTED FAIL after revert"; cat /tmp/hs51_c.txt; PASS=0
fi
if [ -z "$(git status --porcelain docs/USER_GUIDE.md)" ]; then
  echo "PASS (USER_GUIDE.md clean, no diff)"
else
  echo "UNEXPECTED dirty USER_GUIDE.md"; PASS=0
fi
echo

if [ "$PASS" -eq 1 ]; then echo "RESULT: PASS"; else echo "RESULT: FAIL"; fi
