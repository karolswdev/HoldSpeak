# Evidence - HS-96-02

- **Story:** HS-96-02 - The validator gate and the burn-down
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T06:20:49Z

- **Command:** `bash -c 
set -e
cd web
echo '=== the gate fails on a planted raw value ==='
printf '.desk-next .planted { color: #ff0001; }\n' >> src/desk/desk.css
if node scripts/validate-tokens.cjs > /tmp/gate_planted.out 2>&1; then echo 'GATE DID NOT FIRE'; git checkout -- src/desk/desk.css; exit 1; fi
grep -m1 'ff0001' /tmp/gate_planted.out
python3 -c "
s=open('src/desk/desk.css').read()
open('src/desk/desk.css','w').write(s.replace('.desk-next .planted { color: #ff0001; }\n',''))
"
echo '=== clean: gate + drift + census + suite + build ==='
node scripts/validate-tokens.cjs
node scripts/generate-tokens.cjs --check
echo '=== CSS/TS drift lock: the physics constants come from the generated module ==='
grep -n 'DESK_WINDOW.grab' src/desk/components/DeskWindow.tsx | head -1
grep -n 'GLOW_POOL' src/desk/world.ts | head -1
npm run check 2>&1 | tail -2
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4aacf7189b4130cabba33970a7ec814aca6741c5

```text
=== the gate fails on a planted raw value ===
  src/desk/desk.css:3309: hex color `#ff0001` — use a semantic/component color token
=== clean: gate + drift + census + suite + build ===
token gate: clean (70 allow-listed exceptions, all in use)
tokens.css and tokens.gen.ts match design-tokens.json
=== CSS/TS drift lock: the physics constants come from the generated module ===
26:const GRAB = DESK_WINDOW.grab;
5:import { GLOW_POOL } from "../lib/tokens.gen";
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 3.05s
```
