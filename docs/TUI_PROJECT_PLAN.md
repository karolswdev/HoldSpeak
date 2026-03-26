# HoldSpeak TUI Project Plan (Source of Truth)

This plan is the guiding execution document for development teams implementing and maintaining the HoldSpeak TUI architecture described in `docs/TUI_ARCHITECTURE_SPEC.md`.
For current-state inventory, see `docs/TUI_INVENTORY.md`.

## Objectives

- Eliminate “brittle UI” failure modes (screen-stack crashes, hidden coupling, racey async renders).
- Make TUI development safe for multiple contributors (clear ownership, contracts, and tests).
- Establish a sustainable architecture: UI emits intents; App orchestrates; services persist.

## Non‑Goals (Explicitly Out of Scope)

- Perfect UX polish in every corner before stabilization completes.
- Rewriting the audio/meeting pipeline (controller + meeting session internals) unless needed for correctness.
- Replacing Textual or migrating away from Python.

## Guiding Docs (Must Read)

- Architecture: `docs/TUI_ARCHITECTURE_SPEC.md`
- Inventory / known brittleness: `docs/TUI_INVENTORY.md`
- UX roadmap context: `docs/TUI_ROADMAP.md`

## Current Status (Baseline)

Already implemented (as of latest commits):
- `MainScreen` owns the main widget tree + keybindings; app routes updates safely.
- Meetings Hub uses intent messages for open/edit/export/delete (no direct navigation/persistence in the pane).
- Saved meeting metadata saves are correctly routed to SQLite (not the active-meeting controller path).

Remaining work focuses on **completing the architecture across all screens/components**, extracting service APIs, and adding integration tests to prevent regressions.

## Workstreams & Epics

### Epic A — Architecture Compliance (UI purity)

**Goal:** Ensure all TUI screens/components follow “UI emits intents; app/services do side effects”.

**Deliverables**
- All DB reads/writes removed from:
  - `holdspeak/tui/screens/meeting_detail.py`
  - `holdspeak/tui/screens/speaker_profile.py`
  - any other TUI modules importing `holdspeak.db`
- All cross-screen navigation initiated via intent messages handled by the App.

**Acceptance Criteria**
- `rg "from \\.\\.\\.db import|get_database\\(" holdspeak/tui` returns no UI-layer hits (only service layer allowed).
- Screens/components do not call `push_screen()` except for strictly local modals (if any), otherwise they post intents.

**Tasks**
- A1. Replace action item status updates with intents (UI → App → service).
- A2. Replace speaker rename/avatar persistence with intents.
- A3. Replace MeetingDetail export logic with an export intent (UI → App → service).

---

### Epic B — Service Layer Extraction (stabilize APIs)

**Goal:** Move persistence and “use-case” logic into small, testable modules.

**Proposed modules**
- `holdspeak/tui/services/meetings.py`
  - `get_meeting(meeting_id)`
  - `list_meetings(filters...)`
  - `update_meeting_metadata(meeting_id, title, tags)`
  - `delete_meeting(meeting_id)`
- `holdspeak/tui/services/action_items.py`
  - `update_action_item_status(action_id, status)`
- `holdspeak/tui/services/speakers.py`
  - `update_speaker_name(speaker_id, name)`
  - `update_speaker_avatar(speaker_id, avatar)`
- `holdspeak/tui/services/export.py`
  - `export_meeting_markdown(meeting_id, destination_dir=...)`

**Acceptance Criteria**
- App intent handlers call only services (not `get_database()` directly).
- Services are covered by unit tests where feasible.

**Tasks**
- B1. Create service modules + move DB calls out of `holdspeak/tui/app.py`.
- B2. Add small unit tests for service functions (no Textual required).

---

### Epic C — State Contract & UI Updates (reduce glue)

**Goal:** Reduce imperative “poke widgets” code and ensure state is authoritative.

**Phased approach**
- C1 (now): keep current “imperative but consistent” approach (state + screen methods).
- C2 (later): migrate high-churn UI to reactive patterns where it reduces complexity (e.g., meeting bar + status).

**Acceptance Criteria**
- No “UI-only” mutation: any user-visible change corresponds to `ui_state` updates or service results.

---

### Epic D — Integration Tests & Regression Gates

**Goal:** Prevent reintroducing brittleness.

**Deliverables**
- Fix/update stale integration test suite (`tests/integration/test_tui.py`) to match current architecture.
- Add new integration tests for:
  - D1. Screen stack safety: start meeting → cockpit on stack → background updates do not crash.
  - D2. Meetings Hub: open detail → compose succeeds, close works.
  - D3. Saved meeting metadata: edit → save updates DB and refreshes hub list.

**Acceptance Criteria**
- Integration tests run in CI (or at least locally with a clear command) and pass.
- A crash like “generator mounted as widget” or “missing #status” is caught by tests.

---

### Epic E — UX Hardening (post-stabilization)

**Goal:** Improve UX without destabilizing the architecture.

**Examples**
- Confirmations for destructive actions (delete).
- Better empty states and diagnostics (system audio routing hints).
- Keyboard/mouse parity improvements (consistent activation patterns).

## Milestones (Suggested)

### Milestone 1 — “Architecture Complete” (1–2 weeks)
- Finish Epic A across remaining screens.
- Confirm no UI-layer DB access.
- Confirm intent routing covers all navigation/persistence.

### Milestone 2 — “Service Layer + Tests” (1–2 weeks)
- Finish Epic B service extraction.
- Finish Epic D integration tests.
- Document dev workflows (how to add a new intent/service/screen safely).

### Milestone 3 — “UX Confidence” (ongoing)
- Execute Epic E improvements with guardrails (tests + architecture checks).

## Development Workflow (Team Guidance)

### Definition of Done (DoD)

- New UI interaction:
  - UI emits an intent message.
  - App handles intent and calls a service in a worker.
  - UI updates happen on the UI thread.
- No new `get_database()` usage inside `holdspeak/tui/screens` or `holdspeak/tui/components`.
- At least one test added/updated if behavior is non-trivial.

### Code Review Checklist (Architecture)

- Does any new code call `push_screen()` from a component? If yes, should it be an intent?
- Does any UI file import `holdspeak.db`? (should be no)
- Are worker threads using `call_from_thread` for UI operations?
- Does the change break screen-stack assumptions (e.g. querying IDs that aren’t on that screen)?

### Suggested Commands

- Unit tests: `./.venv/bin/pytest -q tests/unit`
- (After Epic D) Integration tests: `./.venv/bin/pytest -q tests/integration -m integration`

## Risks & Mitigations

- **Risk:** Teams bypass intents “for speed” and reintroduce coupling.
  - **Mitigation:** enforce architecture checklist in PR review + add CI grep guard.
- **Risk:** Threading bugs from workers updating UI directly.
  - **Mitigation:** standard helper patterns and a few integration tests that keep modals open during background updates.
- **Risk:** Service layer becomes a dumping ground.
  - **Mitigation:** keep services small and use-case shaped; avoid generic “utils”.

