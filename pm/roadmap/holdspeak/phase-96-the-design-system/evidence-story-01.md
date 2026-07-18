# Evidence - HS-96-01

- **Story:** HS-96-01 - The token architecture
- **Status:** done
- **Date:** 2026-07-18

## Proof

### Captured run — 2026-07-18T06:13:35Z

- **Command:** `bash -c 
set -e
cd web
echo '=== generation + determinism + drift check ==='
node scripts/generate-tokens.cjs
node scripts/generate-tokens.cjs --check
echo '=== value fidelity (every pre-existing name, identical computed value) ==='
python3 - << 'PY'
import re
def props(path):
    src = open(path).read()
    root = src.split(':root {', 1)[1].split('\n}\n', 1)[0]
    nocomment = re.sub(r'/\*.*?\*/', '', root, flags=re.S)
    out = {}
    for chunk in nocomment.split(';'):
        m = re.match(r'\s*(--[\w-]+):\s*(.*)$', chunk.strip(), re.S)
        if m:
            out[m.group(1)] = re.sub(r'\s+', ' ', m.group(2).strip())
    return out
import subprocess
before = props('/tmp/tokens_before.css')
after = props('src/styles/tokens.css')
missing = [k for k in before if k not in after]
changed = [k for k in before if k in after and before[k].lower() != after[k].lower()]
print(f'before={len(before)} after={len(after)} missing={missing} changed={changed}')
assert not missing and not changed
print('FIDELITY OK: 117 originals preserved;', len(after) - len(before), 'tokens added (primitives + Desk OS component layer)')
PY
echo '=== npm run check (tokens gate + census + typecheck + suites + build) ==='
npm run check 2>&1 | tail -2
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a514c1d3f9192fdfb3cc99b0539ea1692fa982cd

```text
=== generation + determinism + drift check ===
wrote src/styles/tokens.css (241 lines)
tokens.css matches design-tokens.json
=== value fidelity (every pre-existing name, identical computed value) ===
before=117 after=178 missing=[] changed=[]
FIDELITY OK: 117 originals preserved; 61 tokens added (primitives + Desk OS component layer)
=== npm run check (tokens gate + census + typecheck + suites + build) ===
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 3.08s
```
