# Phase 24 — AI PI Companion Productization

**Last updated:** 2026-06-01 (HS-24-06 **done** — public companion docs now explain the portable ESPHome device, meeting capture/status, Claude/Codex waiting notifications, spoken replies, controlled-network remote use, and include PixelLab transparent artwork, an intelligence-pipeline GIF, and hardware links). Phase resumed; 3/6 stories shipped. See "Where we are" below.

## Goal

Make AI PI easy to operate during real multi-agent work: the user should be
able to see what is waiting, know which targets are safe to answer, recover
from stale or unavailable sessions, and trust display updates without watching
logs.

## Scope

### In

- Web companion overview for active Claude/Codex sessions.
- Session lifecycle controls: dismiss, refresh, pin, select, and stale markers.
- Clear physical-display affordances for target confidence and unavailable
  reply paths.
- Push/repaint event design or a stronger polling contract for fast display
  transitions.
- Live dogfood with the web overview and physical AI PI running together.

### Out

- Autonomous agent replies without explicit user action.
- Hosted assistant orchestration.
- Direct Claude/Codex API transport.
- Cross-network device reach.
- New hardware design.

## Exit criteria

- [x] The user can see all waiting agent sessions in a browser companion view.
- [x] The user can select, dismiss, or pin a waiting session without editing
      state files.
- [ ] AI PI makes low-confidence or unavailable targets obvious before capture.
- [ ] Display update cadence is documented and dogfooded without premature
      overwrites.
- [ ] Live dogfood records recovery from at least one stale or unavailable
      session.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-24-01 | AI PI Companion surface: read-only session overview | done | [story-01-ai-pi-companion-surface-overview.md](./story-01-ai-pi-companion-surface-overview.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-24-02 | Session lifecycle controls | done | [story-02-session-lifecycle-controls.md](./story-02-session-lifecycle-controls.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-24-03 | Confidence and unavailable-target display affordances | backlog | [story-story-03-confidence-display-affordances](./story-03-confidence-display-affordances.md) | — |
| HS-24-04 | Push/repaint cadence decision | backlog | [story-story-04-display-update-cadence](./story-04-display-update-cadence.md) | — |
| HS-24-05 | Productization dogfood and closeout | backlog | [story-story-05-productization-dogfood-closeout](./story-05-productization-dogfood-closeout.md) | — |
| HS-24-06 | Companion public docs and PixelLab artwork | done | [story-06-companion-public-docs-and-artwork.md](./story-06-companion-public-docs-and-artwork.md) | [evidence-story-06.md](./evidence-story-06.md) |

## Resume guide (2026-06-01)

**Phase 25 and Phase 26 have since closed**, so the prerequisites that paused this
phase are cleared, and the web runtime is now clean and navigable. A handover for
the next agent:

- **Start at HS-24-02 — Session Lifecycle Controls.** Its story is now fully
  scaffolded with a grounded implementation map:
  [story-02-session-lifecycle-controls.md](./story-02-session-lifecycle-controls.md).
- **HS-24-02 is software-only** (web controls + `agent_context` state functions) —
  it does **not** need the physical AI PI, so it is buildable/testable headless and
  is the right pick while hardware dogfood is out of reach.
- **Hardware split — important for sequencing:** HS-24-03 (physical display
  affordances), HS-24-04 (push/repaint cadence), and HS-24-05 (live dogfood) all
  want the physical AI PI on-site. While the author is remote, those stall the same
  way HS-25-07 does. Do HS-24-02 now; scaffold + tackle 03–05 when hardware is in
  hand. Scaffold those story files at that point (they aren't written yet).
- **Web seam (post-Phase-26):** companion routes live in
  `holdspeak/web/routes/system.py` (`/api/companion/status`) +
  `holdspeak/web/routes/pages.py` (`/companion`). New companion control endpoints
  go in `system.py` and may call `agent_context` functions **directly** (the
  dictation routes already do this for `clear_agent_session_response`) — **no
  `WebContext`/constructor change needed**. Construct test servers via
  `MeetingWebServer(WebRuntimeCallbacks(...))` (constructor collapsed in HS-26-06).
- **Frontend:** `/companion` is Astro-built (`web/` → `static/_built/companion/`);
  adding buttons means editing `web/` and `(cd web && npm run build)`. `_built/` is
  gitignored.
- **Gate:** run the **full** suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`),
  not a narrow `-k` — Phase 26 showed narrow filters miss real bugs.

## Where we are

**Resumed 2026-06-01.** Was paused 2026-05-31 to prioritize Phase 25 (Trust &
Hardening). Phase 25 (functionally; HS-25-07 hardware dogfood still open) and
Phase 26 (Web Runtime Decomposition, fully) have since progressed/closed.
**HS-24-02 is now shipped:** `/companion` moved from read-only to operable
— select / dismiss / pin / clear-stale waiting sessions from the browser, mutating
the same selected-target state the physical device reads. The remaining stories
(HS-24-03/04/05) are **hardware-gated** (physical AI PI on-site) and stall the same
way HS-25-07 does while the author is remote; scaffold + tackle them when hardware
is in hand.

**HS-24-06 also shipped (docs/productization, 3/6):** the public docs now show
transparent PixelLab companion artwork and an intelligence-pipeline GIF, explain AIPI-Lite as a portable
ESPHome-based meeting and coding-agent companion, clarify the agent-waiting /
spoken-reply loop, document controlled-network remote use, and link to official
hardware purchase pages. This story was added after the doc commits landed so
the PMO trail matches the shipped public narrative work.

Phase 23 closed with a working physical companion
loop: AI PI can show long questions, distinguish waiting sessions, cycle the
selected target, reject unavailable reply paths, deliver tmux replies, and hold
status flashes long enough to be readable.

The next product risk is operability. The JSON status and device display are
now truthful, but the user still needs a richer surface for overview and
recovery when several sessions are waiting or stale.

HS-24-01, HS-24-02, and HS-24-06 are closed. The HoldSpeak web portal `/companion` surface
now both shows and **controls** the companion state: it is backed by
`/api/companion/status` (now with per-session `stale`/`pinned`/`age_seconds`
markers) and four control routes — `POST /api/companion/{select,dismiss,pin,clear-stale}`
— calling the new `agent_context` state functions directly.

The public docs now explain that the physical AI PI can notify the user when
Claude/Codex is waiting and can route a spoken reply into the selected coding
session when the bridge is reachable over a user-controlled network path.

Next product work remains HS-24-03 (physical display affordances for confidence / unavailable
targets), which is hardware-gated. Scaffold HS-24-03/04/05 when the physical AI PI
is on hand.

## Product problems to solve

| Problem | Why it matters | First likely move |
|---|---|---|
| Session overview is log/API-heavy | The user should not need `curl`, logs, or state files to understand what is waiting. | Build a compact web companion panel from `/api/companion/status`. |
| Session lifecycle is manual | Stale or wrong sessions make the device feel risky. | Add dismiss/select/pin controls that update the same selected-target state. |
| Low-confidence targets are text-only | The physical display can imply safety even when a target is unavailable. | Define short display language/icons for unavailable and low-confidence targets. |
| Polling still owns display cadence | Fast transitions can race unless every path coordinates explicitly. | Decide push events vs. a stricter repaint/hold contract. |
| Dogfood recovery paths are thin | The happy path works; recovery determines whether this is daily-usable. | Run live multi-session dogfood focused on stale and unavailable-session recovery. |

## Pickup order

1. HS-24-01: build the read-only AI PI Companion surface inside the web portal.
2. HS-24-02: add lifecycle controls for selection, dismissal, pinning, and stale sessions.
3. HS-24-03: tighten physical display language for confidence and unavailable targets.
4. HS-24-04: decide and implement display update cadence improvements.
5. HS-24-05: dogfood the full productized loop and close the phase.
6. HS-24-06: public docs and PixelLab artwork for the companion narrative. **Done 2026-06-01.**

## Decisions carried forward

- Replies remain user-driven.
- tmux remains the primary terminal-agent transport.
- GUI text insertion remains a fallback.
- AI PI is a physical attention/action surface, not a tiny chat console.
- Web companion should handle richer overview and recovery workflows.
