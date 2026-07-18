# Evidence - HS-95-08

- **Story:** HS-95-08 - Studio, sessions, and the last exits
- **Status:** done
- **Date:** 2026-07-17

## Proof

### Captured run — 2026-07-18T04:12:18Z

- **Command:** `bash -c 
set -e
echo '--- the guard fails on a planted violation ---'
printf 'import { Link } from "react-router-dom";\nexport const X = () => <Link to="/dictation">x</Link>;\n' > web/src/desk/components/__planted_violation.tsx
if uv run pytest -q tests/unit/test_desk_no_exit_guard.py > /tmp/guard_planted.out 2>&1; then echo 'GUARD DID NOT FIRE'; rm web/src/desk/components/__planted_violation.tsx; exit 1; fi
grep -m1 'router import on the desk' /tmp/guard_planted.out || tail -3 /tmp/guard_planted.out
rm web/src/desk/components/__planted_violation.tsx
echo '--- clean: guards + suite + walk ---'
uv run pytest -q tests/unit/test_desk_no_exit_guard.py tests/unit/test_page_cores_guard.py tests/unit/test_desk_locks.py 2>&1 | tail -1
npm --prefix web run test:web 2>&1 | tail -3
uv run python scripts/desk_gl_walk.py lastexits
echo '--- page chunks in the bundle ---'
ls holdspeak/static/_built/assets/ | grep -E 'Page-[A-Za-z0-9_-]+\.js$' || true
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dc2fa9f995e985378629c2890046a02449dac098

```text
--- the guard fails on a planted violation ---
>           assert "react-router" not in text, f"{rel}: router import on the desk"
--- clean: guards + suite + walk ---
10 passed in 0.11s
   Start at  22:12:19
   Duration  9.57s (transform 696ms, setup 1.35s, import 3.25s, tests 2.51s, environment 8.60s)

demotion: all 15 routes land on the desk with the right window
workbench maximized + saved via 'Save Workflow'; companion window open
--- page chunks in the bundle ---
PresencePage-Bo_CPbwr.js
WelcomePage-kr5pIaI6.js
```
