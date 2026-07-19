# Evidence - HS-101-01

- **Story:** HS-101-01 - The interior canon + mockups
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T18:23:50Z

- **Command:** `uv run python scripts/mockup_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5a993374708b12b736aade0d7c81674214949c46

```text
mockup census: 5 thesis applications, 5 interior-canon screens
mockup census: every canon screen mocked at 1440 and 393
```

### Captured run — 2026-07-19T18:23:56Z

- **Command:** `bash -c cd web && npm run tokens:check --silent && npm run tokens:gate --silent`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 5a993374708b12b736aade0d7c81674214949c46

```text
tokens.css and tokens.gen.ts match design-tokens.json
token gate: clean (62 allow-listed exceptions, all in use)
```

## Summary of proof

- **The canon** (docs/internal/DESIGN_SYSTEM.md §"The interior canon
  (HS-101)"): the five-step interior type scale ratified as component
  tokens (`--desk-type-display-*`, `--desk-type-primary-*` NEW in
  web/design-tokens.json, riding the existing body/detail/label
  steps), five composition rules (data as material / purpose-built
  compositions / verbs on the material / direct manipulation through
  the glass / motion as meaning), the kit that carries them
  (SurfaceStream, SurfaceLibrary, SurfaceSwitchboard, EditInPlace,
  SystemShade, the glass-drop contract — designed, wired at the
  build), and the AGENT_BRIEF §6 OS-territory inventory ratified for
  the gate. Marked **proposed — nothing ships before HS-101-02**.
- **Mockups, LOOKED AT** (assets/hs-101-01-mockups/): five screens ×
  two form factors (1440 + 393) on the Phase-100 mockup material —
  the Journal as a dated stream (display count, day headers,
  primary-step spoken text, verbs on the hovered entry, in-place
  edit, the learned moment), Blocks as a library (the injection text
  IS the tile face, spoken-match quotes, ghost create tile), Runs on
  as a switchboard (the DEFAULT bay leads with its model at display
  step, lamps with named offline reasons, boundary badges at the
  point of decision), the system shade (honest counts incl. zero,
  verbs inline, egress badges), and the drag-through-glass moment
  (lifted Project KB, drop-ready composer well, ghost chip).
  Defects found and fixed during my own screenshot walk: hover verbs
  colliding with entry/tile text (re-anchored), the switchboard side
  column auto-placing into column 1 (explicit grid columns), the
  desk object hiding behind the shade, the invisible drag cursor
  (clip-path pointer), phone-size label collisions.
- **Census**: scripts/mockup_census.py now derives the HS-101 roster
  from the canon doc's "The mockup roster (HS-101-01)" list and
  requires both form factors per screen (first capture above).
- **Token gate**: generated CSS/TS match the JSON; no raw values
  (second capture above). Doc guards green: judgment census
  (14 surfaces / 28 components, zero omissions), web vocabulary
  guard 4/4.
