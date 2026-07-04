# Phase 21 — Honest everywhere (trust, provenance, names)

**Status:** in-progress (opened 2026-07-03, the same evening Phases 18/19 reached 6/7) —
audit theme 4, the cheapest-to-fix, highest-trust-cost class, non-negotiable per
POSITIONING canon.

**Last updated:** 2026-07-04 (**4/5, gate staged — and one process failure on the record.**
PR #233 (21-03) was merged with RED checks: the HS-72-02 route-surface lock fired on the
new `api/desk/actuators/status` consumer, and the merge was chained after the CI watch
instead of gated on the conclusion — the exact trap the two-track handover names. Healed
same-hour: the regenerated manifest (covering 21-03's and 21-04's consumers,
`test_api_surface` 5/5) rides PR #234; noted on #233. The honesty phase gets an honest
ledger. Earlier: **OPENED, survey-corrected.** The 2026-06-27 draft partially
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
| HSM-21-01 | The one egress contract (`EgressScope` in Contracts + `DeskPrimitive.egress` + every surface consumes it) — **leads** | done — [`evidence-story-01.md`](./evidence-story-01.md) (sim-proven ×3; the hard-coded capsule is dead) |
| HSM-21-02 | The Swift banned-copy + reassurance-prose guard (+ fix the sites) | done — [`evidence-story-02.md`](./evidence-story-02.md) (7 sites; the guard caught the 7th itself) |
| HSM-21-03 | GitHub-repo honesty: the tile's ready state tells the truth; the host-fallback path ratified | done — [`evidence-story-03.md`](./evidence-story-03.md) (control-vs-treatment on one live hub) |
| HSM-21-04 | The ambient trust chip on the iPad + the web-chip posture audit | done — [`evidence-story-04.md`](./evidence-story-04.md) (two surfaces, two postures, one live hub) |
| HSM-21-05 | Docs + the walk rider (honesty checks join the staged couch session) | in-progress — docs done; [`HSM-21-WALK-RIDER.md`](./HSM-21-WALK-RIDER.md) staged (H1–H3); the rider is the owner's |

## Where we are

Opened 2026-07-03; **2/5 the same hour** — 21-01 landed: `EgressScope` is the one grammar,
`DeskPrimitive.egress` drives the pull-out badge (connectors wear Cloud, a live coder
session wears Local + your desktop, everything else stays honestly local), and the desk
capsule / mesh text / shell chips all consume it — including fixing the mixed-as-local
drift from tonight's own 18/19 chips. **21-02 followed**: seven "nothing leaves" labels
adopted the badge grammar (the new guard's FIRST RUN caught the 7th — the classic home
header the survey missed) and the guard now scans Swift string literals for banned names +
reassurance prose, red-proven. **21-03 followed** (3/5): the GitHub tile's ready state
now derives from the live HS-77-03 status route (paired vs configured are separate
truths; the act sheet lists only completable sends), proven control-vs-treatment on one
live hub with the repo flipped mid-run. **21-04 followed** (4/5): the setup-status
client + the shared four-posture mapping (test-locked to the web chip's precedence) +
the shell top-bar chip — proven on one live hub flipped local → writes-need-approval,
with the real web TrustChip audited against the same hub (same words, both surfaces).
**21-05's docs half is done and the rider is STAGED** (H1–H3, ~5 minutes riding the
18/19 couch session). **The phase now sits at 4/5 with the gate staged — the owner's
device session closes Phases 18, 19, AND 21 in one sitting.** Artifact provenance rendering shipped in 19-04; this phase owns the audit
that no surface fakes a posture.
