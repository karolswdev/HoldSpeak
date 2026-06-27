# Phase 21 — Honest everywhere (trust, provenance, names)

**Status:** planned — opens once the iPad surfaces from 18/19 exist (the badges need
something real to describe). Stories detailed on open.

**Last updated:** 2026-06-27 (**authored** from the parity audit, theme 4 + the web
connector half of theme 3.)

## Why this phase exists

Audit theme 4: *honesty drift in trust and provenance.* The badges and names exist; they are
not consistently driven by the real posture. This is the cheapest-to-fix, highest-trust-cost
class of gap, and it is non-negotiable per POSITIONING canon ([[feedback_no_privacy_novels]]):

- **The iPad egress badge is cosmetic.** `DioPullout` (`DeskDioramaStage.swift:1221-1224`)
  hard-codes a `lock.fill / On device` capsule for *every* primitive; `DeskPrimitive` has no
  `egress` property. `EgressBadge.Scope` lacks the canonical `.mixed` case (the contract names
  local / mixed / cloud); `CompanionMesh` hand-builds "ON-DEVICE · …" text instead.
- **Artifacts render without provenance** (`confidence` / `sources`) on the iPad — carried in
  Phase 19, surfaced here as the honesty line.
- **Banned copy reappears.** Web uses "intelligent typing" (a banned synonym, `POSITIONING.md:105`)
  in five strings; two Swift sites narrate forbidden "nothing leaves" reassurance prose
  (`POSITIONING.md:140-143`). The voice guard does not scan `web/src/**/*.astro` or Swift.
- **Web cannot configure two of three connectors** — `settings.astro` binds only
  `slack_webhook_url`; `system.py` persists only Slack. The iPad GitHub tile presents ready
  but `propose` never sends a repo.

## The load-bearing design call

**Drive every badge and name from the real posture, and make the guard enforce it.** Add
`egress` to the `DeskPrimitive` protocol (default `.local`, overridden on Mac-backed
primitives) and the `.mixed(String)` scope; replace the hard-coded capsule with
`EgressBadge(scope: prim.egress)`. Broaden the voice guard to scan `web/src/**/*.astro` and
Swift so banned names/prose cannot reappear. Honest egress is a contract, not decoration.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-21-01 | The egress contract on the iPad (`DeskPrimitive.egress` + `.mixed`) — **leads** | todo |
| HSM-21-02 | The banned-copy + reassurance-prose guard (web + Swift) | todo |
| HSM-21-03 | Web connector configs (webhook + GitHub) + the iPad GitHub-repo fix | todo |
| HSM-21-04 | The ambient trust chip + setup-status adapter | todo |

## Where we are

Not started. **21-01 leads.** This phase intentionally overlaps the surfaces 18/19 build — do
not let a new iPad screen ship with a hard-coded badge; once `DeskPrimitive.egress` lands,
every new surface inherits the honest badge for free. The artifact provenance render is built
in 19-04; this phase owns the *audit* that no surface fakes a posture.
