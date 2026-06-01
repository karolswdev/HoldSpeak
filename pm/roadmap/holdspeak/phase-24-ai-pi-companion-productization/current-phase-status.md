# Phase 24 — AI PI Companion Productization

**Last updated:** 2026-06-01 (HS-24-02 story scaffolded as a handover; phase still `paused` but **ready to resume at HS-24-02**). See "Resume guide (2026-06-01)" below.

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
- [ ] The user can select, dismiss, or pin a waiting session without editing
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
| HS-24-02 | Session lifecycle controls | backlog | [story-02-session-lifecycle-controls.md](./story-02-session-lifecycle-controls.md) | — |
| HS-24-03 | Confidence and unavailable-target display affordances | backlog | — | — |
| HS-24-04 | Push/repaint cadence decision | backlog | — | — |
| HS-24-05 | Productization dogfood and closeout | backlog | — | — |

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

**Paused 2026-05-31** to prioritize Phase 25 (Trust & Hardening). **Both Phase 25
(functionally; HS-25-07 hardware dogfood still open) and Phase 26 (Web Runtime
Decomposition, fully) have since progressed/closed** — see the Resume guide above.
HS-24-01 is the last shipped work; **HS-24-02 is the scaffolded, recommended resume
point.**

Phase 23 closed with a working physical companion
loop: AI PI can show long questions, distinguish waiting sessions, cycle the
selected target, reject unavailable reply paths, deliver tmux replies, and hold
status flashes long enough to be readable.

The next product risk is operability. The JSON status and device display are
now truthful, but the user still needs a richer surface for overview and
recovery when several sessions are waiting or stale.

HS-24-01 is closed. The existing HoldSpeak web portal now has a read-only AI PI
Companion surface at `/companion`, backed by `/api/companion/status`.

Next work is HS-24-02: add lifecycle controls for selecting, dismissing,
pinning, and clearing stale sessions without editing state files.

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

## Decisions carried forward

- Replies remain user-driven.
- tmux remains the primary terminal-agent transport.
- GUI text insertion remains a fallback.
- AI PI is a physical attention/action surface, not a tiny chat console.
- Web companion should handle richer overview and recovery workflows.
