# HS-33-05 — Visual assets (pixellab MCP)

- **Status:** done (2026-06-03). Evidence: [evidence-story-05.md](./evidence-story-05.md).

## Goal

Refresh and complete HoldSpeak's visual identity for open-source prime time — a
coherent pixel-art / jRPG-flavored spot-art set that harmonizes with the Phase-30
**"Signal"** web identity (dark-first, signature orange, Space Grotesk / Inter /
JetBrains Mono). The existing `docs/assets/pixellab/` set (5 PNGs + the
`operator-working-loop.gif`) is the **style anchor**; this story audits it and
adds the pieces a great OSS repo needs.

> **Tooling:** generated with the **pixellab MCP** (the same server that made the
> existing set — see `docs/assets/pixellab/README.md`, which records each asset's
> object ID + prompt). The MCP is connected when this story runs; no code gate.
> **Always record each new asset's pixellab object/animation ID + prompt in that
> README** (provenance + regeneration).

## Scope

### Audit (existing set)
- Review `hold-to-talk-microphone.png`, `meeting-intelligence-notebook.png`,
  `project-aware-typing.png`, `aipi-lite-companion.png`,
  `operator-working-loop.gif`. Confirm style/palette coherence with "Signal"
  (orange accent on dark); flag any to regenerate for consistency.

### New assets (prime-time set)
1. **Logo / app mark** — a distinctive HoldSpeak pixel-art mark usable at favicon
   size and as the README header. Motif: a held key + soundwave (the "hold,
   speak, release" gesture). Signal orange on transparent.
2. **GitHub social-preview / OG image** — 1280×640, the repo's share card:
   wordmark "HoldSpeak" + tagline ("Local-first voice input & meeting
   intelligence") + the operator/mic motif, dark Signal background. *(This is the
   single highest-impact OSS asset — it's the first impression on every share.)*
3. **README hero banner** (optional) — a wide pixel-art scene tying the three
   pillars (voice typing · meeting intelligence · project-aware dictation)
   together; or reuse the operator gif as the hero.
4. **Refreshed workflow trio** (only if the audit flags drift) — re-generate the
   three workflow icons in one locked style/palette.

### Wire-in
- Place under `docs/assets/pixellab/` (and `web/public/` for favicon/social if the
  site uses them); reference from the README (header mark + workflow map) and set
  the GitHub repo's social preview (note it in the story — the image is committed;
  setting it in repo settings is a manual GitHub step to record).

## Draft pixellab prompts (refine at generation time)

- **Logo/mark:** "Clean pixel art app icon: a glowing keyboard key being held down
  with three rising soundwave arcs, signature orange (#…Signal orange) on
  transparent background, modern local-first voice app brand mark, crisp at small
  sizes."
- **Social/OG card (1280×640):** "Wide pixel-art banner on a dark slate
  background, bold 'HoldSpeak' wordmark, a charming operator with a headset at a
  glowing terminal on the right, a held-key + soundwave motif on the left,
  signature orange accents, tagline space along the bottom, modern open-source
  project social preview."
- *(Match the existing set's "clean pixel art … transparent background … modern
  product documentation asset" phrasing + the Signal palette.)*

## Test plan

- No automated test (visual). Manual: assets render in the README on GitHub;
  the social card looks right at GitHub's crop; provenance recorded in
  `docs/assets/pixellab/README.md`.

## Done when

- [x] A coherent prime-time asset set exists (logo/mark + social/OG card at
      minimum), harmonized with "Signal."
- [x] Wired into the README/docs; favicon/social placed where the site/repo use
      them.
- [x] Every new asset's pixellab object/animation ID + prompt recorded in
      `docs/assets/pixellab/README.md`.
