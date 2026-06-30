# HS-69-12 — Web /companion → the Agent Desk

- **Status:** done
- **Priority:** MED
- **Depends on:** HS-69-02
- **Catalog pattern(s):** §6, §9 (the desk surface)
- **Evidence:** [evidence-story-12.md](./evidence-story-12.md)

## Goal

Per the owner-approved direction (Phase-68 §1c), the web `/companion` **becomes
the Agent Desk** — the same desk surface as the iPad (HSM-15-08), not a plainer
control panel.

## Scope

- Replace the static docs-portal hero + capability cards with a **living desk**
  fed by the existing HTTP API (no backend change): the real agents
  (`/api/agents`) as desk cards + the live companion link + the coders awaiting
  you (`/api/companion/status`).
- Keep the pairing + credential facts, folded into a "How it connects" footer.
- Signal-crafted (signal-card cards, zone spines, the egress badge).

## Proof required

`/companion` renders as the Agent Desk with the real agents + the companion
link; the desk aesthetic, not a control panel.

## Done

Shipped and screenshot-proven. `/companion` is now "The Agent Desk": a live link
chip ("N need you" / "Companion linked" / "No companion linked"), a warn-spined
**Needs you** zone for the coders awaiting you, an **Agents** zone of the real
persona cards (avatar, role, tool chips, "Open on desk"), and a "How it connects"
footer carrying the pairing + credential facts. Driven by an Alpine factory
(`companion-desk.js`) over `/api/agents` + `/api/companion/status`. The static
docs portal is gone. Route pre-flight (zero page errors) + density guard = 7
passed. Honest note: the deeper iPad CompanionBoard live-session interactions
(select/pin/inject) remain a follow-up; this delivers the desk surface + the
real agents + the awaiting-link.
