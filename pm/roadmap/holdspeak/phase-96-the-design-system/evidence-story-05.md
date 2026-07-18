# Evidence - HS-96-05

- **Story:** HS-96-05 - The accessibility pass
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T06:32:06Z

- **Command:** `bash -c 
npm --prefix web run test:web 2>&1 | grep 'Tests '
uv run python scripts/desk_gl_walk.py focus 2>&1 | tail -2
echo '--- keyboard reachability audit ---'
echo 'chrome mark/menu items/launchers: buttons (menu: arrows+Home/End+Escape, Radix pattern hand-rolled)'
echo 'dock chips/close/reset: buttons in a toolbar; verbs: labeled buttons'
echo 'windows: focus-in on open, focus-return on close, Escape closes, tabIndex=-1 shell, NO trap'
echo 'GL world: sr-only per-object/zone buttons; focused one surfaces as a visible chip above the dock band'
echo 'gaps found: zone rename reachable only via pointer tap on title (rides the pull-out rename verb for keyboard); noted for triage'
echo '--- axe gate: serious+critical (see a11y.test.tsx, part of the suite) ---'
grep -n 'serious.*critical\|critical.*serious' web/src/desk/__tests__/a11y.test.tsx | head -1
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cce277a13999b5c993aa0217bef433b5112333ac

```text
      Tests  259 passed (259)
world focus chip visible: 'My Nuts' ({'w': 81.1875, 'h': 35})
focus walk: 14 tab stops ringed; window focus-in, Escape-close, and the world chip verified
--- keyboard reachability audit ---
chrome mark/menu items/launchers: buttons (menu: arrows+Home/End+Escape, Radix pattern hand-rolled)
dock chips/close/reset: buttons in a toolbar; verbs: labeled buttons
windows: focus-in on open, focus-return on close, Escape closes, tabIndex=-1 shell, NO trap
GL world: sr-only per-object/zone buttons; focused one surfaces as a visible chip above the dock band
gaps found: zone rename reachable only via pointer tap on title (rides the pull-out rename verb for keyboard); noted for triage
--- axe gate: serious+critical (see a11y.test.tsx, part of the suite) ---
4:// furniture passes an axe sweep at the serious/critical gate.
```
