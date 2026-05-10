# Evidence — HS-18-05 Product Documentation + Phase Exit

**Date:** 2026-05-10
**Status:** done

## What shipped

- `docs/USER_GUIDE.md` now presents HoldSpeak as a local-first voice workspace with two primary surfaces: meeting intelligence and intelligent typing.
- README points new users to the user guide and documents intelligent typing runtime options, including OpenAI-compatible endpoints.
- `final-summary.md` was created using the roadmap-builder required sections.
- Parent roadmap and phase status were updated for phase close.
- Every completed HS-18 story has an evidence file.

## Verification

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
import re
roots=[Path('README.md'), Path('docs/USER_GUIDE.md'), Path('pm/roadmap/holdspeak/phase-18-intelligent-typing-copilot/current-phase-status.md')]
missing=[]
pat=re.compile(r'\[[^\]]+\]\(([^)]+)\)')
for f in roots:
    text=f.read_text(encoding='utf-8')
    for m in pat.finditer(text):
        target=m.group(1).split('#',1)[0]
        if not target or '://' in target or target.startswith('mailto:'):
            continue
        p=(f.parent/target).resolve()
        if not p.exists():
            missing.append((str(f), target))
if missing:
    for item in missing:
        print('MISSING', item[0], item[1])
    raise SystemExit(1)
print('markdown links ok')
PY
```

Result: `markdown links ok`.

```bash
.venv/bin/pytest -q --ignore=tests/e2e/test_metal.py
```

Result: `1622 passed, 5 skipped in 120.72s`.

```bash
cd web && npm run build
```

Result: 7 static pages built successfully into `holdspeak/static/_built/`.

## Notes

- `tests/e2e/test_metal.py` was ignored for the phase baseline because it is hardware/GPU specific.
- The five skipped tests require optional dependencies or local model files: scipy, llama-cpp-python/GGUF, MLX model stack, and llama grammar import.
