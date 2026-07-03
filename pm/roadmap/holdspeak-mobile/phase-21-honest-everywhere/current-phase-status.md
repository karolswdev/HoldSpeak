# Phase 21 — Honest everywhere (trust, provenance, names)

**Status:** in-progress (opened 2026-07-03, the same evening Phases 18/19 reached 6/7) —
audit theme 4, the cheapest-to-fix, highest-trust-cost class, non-negotiable per
POSITIONING canon.

**Last updated:** 2026-07-03 (**OPENED, survey-corrected.** The 2026-06-27 draft partially
predates Wave 1 and Phase 19: the web banned-copy scan EXISTS
(`test_doc_drift_guard.py` scans `web/src/**/*.astro`; zero "intelligent typing" left in
product copy), web settings binds ALL THREE connectors and the system package persists
them, and the hub's github propose route has a `companion_github_repo` fallback. What
remains is the iPad half of every story — plus fresh drift the survey caught in
tonight's own Phase-18/19 shell work. Stories re-grounded below.)

## Why this phase exists

The badges and names exist; they are not consistently driven by the real posture:

- **The iPad egress badge is cosmetic.** `DeskPrimitive` has no `egress` property;
  `EgressBadge.Scope` (`DeskDioramaStage.swift:2541`) lacks the canonical `.mixed`;
  `DioPullout` hard-codes `lock.fill / "On device"` for EVERY primitive
  (`DeskDioramaStage.swift:1321-1324`) — including **connector primitives whose whole
  purpose is cloud egress** (the sharpest honesty bug). `CompanionMesh` hand-builds
  "ON-DEVICE · …" text (`CompanionMesh.swift:748-753`). Hub runs are honest only via a
  one-off `@State` (`printedEgress`, `:2895`), not the primitive.
- **Fresh drift, caught opening this phase:** the Companion shell grew a SECOND parallel
  egress grammar tonight — `egressChip("Local + \(host)")` renders a **mixed** posture in
  the local/green treatment (`CompanionShellApp.swift:970`), and `cloudChip` duplicates
  the badge by hand (`:607`). Exactly the drift one contract prevents.
- **No guard covers Swift.** ~6 "on-device · nothing leaves" label sites survive in
  `apple/` (worst: the full reassurance sentence in `DeskHome.swift:318`), and nothing
  stops them reappearing — the guard scans docs + web only.
- **The GitHub tile fakes readiness.** The iPad `propose` never sends a repo
  (`DeskHostLink.propose`, `DeskDioramaStage.swift:2699`); it works solely through the
  host's `companion_github_repo` fallback (`desk_actuators.py:236`), and the tile presents
  ready even when the host has no repo configured → a guaranteed 400 at send time.
- **The ambient trust chip is web-only** (`TrustChip.astro`, HS-42-05, over
  `/api/setup/status`); the iPad has no equivalent posture line.

## The load-bearing design call

**One scope model, per-app chrome, driven from the real posture.** `EgressScope`
(`local / mixed(target) / cloud(target)`) lives in Contracts (pure, UI-free: label +
symbol name + tint key), so every surface renders the SAME grammar — the desk's
`EgressBadge`, the mesh line, and the shell's chips all consume it. `DeskPrimitive` gains
`egress: EgressScope` (default `.local`; connectors override to `.cloud(name)`; hub-run
surfaces to `.mixed("your desktop")`). The guard learns Swift so banned names and
reassurance prose cannot reappear (labels state the posture; the badge IS the privacy
sentence, per canon).

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-21-01 | The one egress contract (`EgressScope` in Contracts + `DeskPrimitive.egress` + every surface consumes it) — **leads** | todo |
| HSM-21-02 | The Swift banned-copy + reassurance-prose guard (+ fix the 6 sites) | todo |
| HSM-21-03 | GitHub-repo honesty: the tile's ready state tells the truth; the host-fallback path ratified | todo (web+backend halves shipped pre-open) |
| HSM-21-04 | The ambient trust chip on the iPad + the web-chip posture audit | todo |
| HSM-21-05 | Docs + the walk rider (honesty checks join the staged couch session) | todo |

## Where we are

Opened 2026-07-03. **21-01 leads** — once `EgressScope` lands, every surface (including
the ones 18/19 just built) inherits the honest badge for free, and 21-02's guard keeps it
that way. Artifact provenance rendering shipped in 19-04; this phase owns the audit that
no surface fakes a posture.
