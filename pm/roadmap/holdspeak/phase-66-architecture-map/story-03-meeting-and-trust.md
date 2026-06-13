# HS-66-03 — The meeting pipeline + the trust boundary, diagrammed

- **Project:** holdspeak
- **Phase:** 66
- **Status:** done
- **Depends on:** HS-66-01
- **Unblocks:** HS-66-04
- **Owner:** unassigned

## Problem
The meeting pipeline and, more importantly, exactly what crosses the
machine boundary and the gate on each crossing, are not drawn anywhere.

## Scope
- **In:** Mermaid diagrams for the meeting flow (live capture or import →
  windowed transcribe → MIR routing → plugin host → artifacts → aftercare
  → the actuator propose/approve/execute flow → Send to Slack), and a
  dedicated trust/egress boundary diagram aligned to `docs/SECURITY.md`
  §egress and the Phase-62 egress-badge posture (every crossing + its
  gate: cloud intel, the wake-model download, the Slack webhook, connector
  CLIs, the web bind/auth). Prose names real modules.
- **Out:** the dictation side (HS-66-02).

## Acceptance criteria
- [x] The meeting flow and the trust-boundary diagram are accurate to the
      code and to SECURITY (no egress drawn that does not exist; none
      omitted).
- [x] All blocks render (guard green); voice guard + full suite green.

      See `evidence-story-03.md`.

## Test plan
- The render guard; cross-check against SECURITY's egress table; the suite.
