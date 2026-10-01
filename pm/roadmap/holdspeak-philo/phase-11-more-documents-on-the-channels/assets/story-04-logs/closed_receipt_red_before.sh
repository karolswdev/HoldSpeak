#!/bin/bash
# Round four red-before (Astra built-check r3, condition 1): the UNKNOWN and no-answer closed-row
# fences, run UNCHANGED against the implementation at f4127c441 (before ClosedReceipt), exported
# into scratch modules beside the real ones; removed on exit.
set -u
ROOT="$(git rev-parse --show-toplevel)"; cd "$ROOT"
BASE=f4127c441
S="$ROOT/web/src/desk/surface/send_rb"; C="$ROOT/web/src/features/channels_rb"
trap 'rm -rf "$S" "$C"' EXIT
rm -rf "$S" "$C"; mkdir -p "$S/__tests__" "$C/__tests__"
for f in SendWell.tsx send-well.css index.ts; do git show "$BASE:web/src/desk/surface/send/$f" > "$S/$f"; done
for f in SendWell.tsx channels.ts channels.css; do git show "$BASE:web/src/features/channels/$f" > "$C/$f"; done
sed -i '' 's#features/channels/channels#features/channels_rb/channels#g' "$S/SendWell.tsx"
sed -i '' 's#desk/surface/send"#desk/surface/send_rb"#g' "$C/SendWell.tsx"
cp web/src/desk/surface/send/__tests__/closedReceipt.test.tsx "$S/__tests__/"
sed 's#desk/surface/send"#desk/surface/send_rb"#g' web/src/features/channels/__tests__/closedReceipt.test.tsx > "$C/__tests__/closedReceipt.test.tsx"
echo "IMPLEMENTATION = $BASE ($(git rev-parse --short $BASE)); fences = the head's closedReceipt tests, unchanged but for the module path"
cd web && npx vitest run --reporter=verbose src/desk/surface/send_rb src/features/channels_rb 2>&1 | grep -E "✓|×|Tests |AssertionError"
exit ${PIPESTATUS[0]}
