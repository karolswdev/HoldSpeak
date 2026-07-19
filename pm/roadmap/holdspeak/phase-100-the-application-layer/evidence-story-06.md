# Evidence - HS-100-06

- **Story:** HS-100-06 - B2: the honest mic
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T13:56:43Z

- **Command:** `sh -c cd web && npx vitest run src/desk/components/MicButton.test.tsx 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6e231c43f57ece6f985f4c5e249cd899a915b3bf

```text
   Start at  07:56:44
   Duration  647ms (transform 51ms, setup 65ms, import 130ms, tests 62ms, environment 299ms)
```

## Summary of proof

- **speakToFillUnsupportedReason()** (lib/speakToFill.ts): names WHY
  capture is unavailable — the insecure-origin case ("Mic capture
  needs a secure origin. Open this hub via localhost or HTTPS to
  speak.") distinguished from a capture-less browser.
- **MicButton never vanishes**: the unsupported state renders a
  visible, disabled `.desk-mic.is-unsupported` with the reason in
  title + aria-label; the retained-audio recovery path is untouched.
  Vitest pins insecure-origin / no-capture-browser / supported states
  (4 passed, captured above).
- **Proven on the real trap**: the staged LAN instance (plain HTTP,
  192.168.1.36) rebuilt and probed — `unsupported mics visible: 1`,
  `disabled: True`, title carries the reason verbatim. Screenshot:
  assets/hs-100-06-honest-mic-lan-1440.png.
- Rider in this commit: `design/inset-groups-spike` merged onto the
  phase branch (the gate's resolution — material reaches main only
  with the built interiors; this branch IS the interiors' branch).
  Vocabulary guard stays green post-merge.
