# Evidence - HS-100-03

- **Story:** HS-100-03 - The thesis
- **Status:** done
- **Date:** 2026-07-19

## Proof

### Captured run — 2026-07-19T07:55:07Z

- **Command:** `uv run python scripts/mockup_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** e85f0372e265410a378329f3243a6d10d319efa2

```text
mockup census: 5 thesis applications
mockup census: every application mocked at 1440 and 393
```

## Summary of proof

- **docs/internal/APPLICATION_LAYER_THESIS.md**: four applications and
  a desk (Speak / Meetings / Agents / Settings + the desk as the
  operating surface), each with its job cited to GROUNDING.md, its
  opening posture, wings (max two), and the one configuration door;
  the full kill/merge accounting (Studio killed, Workbench demoted,
  three launchers collapsed to dock + ⌘K); the interaction model; the
  design-language law carried from the spike; the story-granular build
  plan B1–B8 with a named mechanical guard per story; open questions
  reserved for the owner's gate.
- **Mockups, LOOKED AT** (assets/hs-100-03-mockups/): five screens ×
  two form factors (1440 + 393), high-fidelity HTML on the spike's
  material values with real product sprites and real trace content
  (the imported "Release sync" meeting, the traced dictation loop).
  Census above proves every thesis application is mocked at both
  sizes. Defects found and fixed during my own screenshot walk:
  flex-shrink row clipping in Settings/Agents, the mobile sheet
  inheriting the desktop centering transform.
