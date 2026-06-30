# HS-69-01 — Egress badge → the cockpit

- **Status:** done
- **Priority:** HIGH (cheapest, POSITIONING obligation)
- **Depends on:** —
- **Catalog pattern(s):** §6 egress badge
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## Goal

The canonical structured `{scope,label}` egress badge — POSITIONING's one-glance
privacy chip — rides the cockpit cards, not just `/presence`.

## Done

Shipped in the substrate wave and confirmed across the cockpit: the global
`.egress-badge` (`web/src/styles/global.css`) + `egress-badge.js` ride the
dashboard live-intel card, the Qlippy cockpit cards (HS-69-06), the activity
agent runs-on chip, and the companion desk (HS-69-12) — local = `--ok`,
mixed/cloud = `--accent`. See the evidence file.
