#!/bin/bash
# Item 5 (Astra built-check r1 F5): the kit's no-viewport-media guard now scans desk/surface/ at any
# depth. Mutation: append a viewport query to the NESTED species stylesheet, run the guard (must
# fail naming send/send-well.css), revert (trap), run again (must pass).
set -u
cd "$(git rev-parse --show-toplevel)"
F=web/src/desk/surface/send/send-well.css
cp "$F" "$F.orig"; trap 'mv "$F.orig" "$F"' EXIT
printf '\n@media (max-width: 420px) { [data-send="well"] { color: red; } }\n' >> "$F"
H=$(mktemp -d)
echo "== mutated (expect FAIL)"
HOME=$H uv run pytest -q -p no:cacheprovider tests/unit/test_native_surfaces_guard.py 2>&1 | grep -E "send/send-well.css|passed|failed" | head -4
mv "$F.orig" "$F"; trap - EXIT
echo "== reverted (expect pass)"; git diff --quiet HEAD -- "$F" || git diff --stat -- "$F"
HOME=$H uv run pytest -q -p no:cacheprovider tests/unit/test_native_surfaces_guard.py 2>&1 | tail -1
rc=$?; rm -rf "$H"; exit $rc
