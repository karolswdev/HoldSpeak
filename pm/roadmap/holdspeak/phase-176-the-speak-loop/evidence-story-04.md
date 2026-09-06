# Evidence - HS-176-04

- **Story:** HS-176-04 - The voice law (MicButton on every text input across the desk; the census gap closed)
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T14:39:00Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); HOME=$T uv run pytest -q tests/unit/test_ux_canon_scan.py tests/unit/test_ux_canon_ratchet.py -p no:cacheprovider 2>&1 | tail -1; uv run python scripts/ux_canon_scan.py --json $T/v.json --md $T/v.md --ranking $T/r.md 2>&1 | grep -i "scanned"; echo -n "mic violations in scan JSON: "; grep -o "\"rule\": *\"mic\"" $T/v.json | wc -l | tr -d " "; echo -n "ceiling: "; grep -o "\"mic\": *[0-9]*" tests/ux_canon_ceiling.json | head -1; echo -n "parked: "; ls web/src/pages/cores/dictation/_parked/ | tr "\n" " "; echo`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 273274e2934fb51ac291ca7c391ddbed8054aa32

```text
37 passed in 0.93s
Scanned 226 files, found 113 violations across 221 faces.
mic violations in scan JSON: 0
ceiling: "mic": 0
parked: AimRow.tsx InstrumentStrip.tsx ResultPanel.tsx UtteranceWell.tsx 
```
