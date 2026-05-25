# HS-17-06 — Meeting Title in Device Status

- **Project:** holdspeak
- **Phase:** 17
- **Status:** backlog
- **Depends on:** HS-17-05 (Recording-tick emitter — this story extends its payload)
- **Unblocks:** —
- **Owner:** unassigned

## Problem

When a user starts a meeting with a title (via web UI or `POST /api/meeting/start {"title": "Standup"}`), the AIPI-Lite device has no way to show which meeting it's attached to. The activity slot just shows `Recording M:SS` (or will, once HS-17-05 lands) — no context about *which* meeting.

User feedback 2026-05-10: "Shouldn't the meeting title or something be displayed every now and then?"

## Scope

### In

- If a meeting has a non-empty `title`, the periodic Recording-tick payload from HS-17-05 includes it.
- **Display strategy: alternating.** Every other tick swaps between:
  - `Recording M:SS` (5s)
  - `<title>` (5s)
  - …repeating.
  - Net result: title visible every 10s for 5s at a time, recording timer visible every 10s for 5s at a time.
- Title truncation: > 24 chars → first 23 chars + ellipsis `…`.
- If `title` is null/empty: fall back to `Recording M:SS` only (HS-17-05's plain default; no alternation).
- Update `docs/DEVICE_PROTOCOL.md` with the alternation note.

### Out

- Title editing from the device. Read-only display.
- Localization. English title displayed verbatim.
- Other meeting metadata (participants, project, tags). Could be follow-ups (one alternation slot per metadata field).
- Multi-line LCD layout (the activity slot is a single line).

## Acceptance Criteria

- [ ] HS-17-05's Recording-tick emitter checks `meeting.title`; if non-empty, alternates the periodic payload between `Recording M:SS` and `<title>` (truncated).
- [ ] Title truncation at 23 chars + `…` verified by unit test.
- [ ] Integration test: meeting with title `"Standup w/ Jane and Bob"` produces status frames where every other tick contains the title (or a truncated version).
- [ ] Meeting without title: same flow as HS-17-05 alone (every tick is `Recording M:SS`).
- [ ] `docs/DEVICE_PROTOCOL.md` updated.
- [ ] Live verification: meeting with title shows on LCD alternating with the timer.

## Test Plan

- **Unit:** payload generator with title set vs. unset; truncation edge cases (exactly 24 chars, 25 chars, much longer).
- **Integration:** `tests/integration/test_device_title_status.py` — fake WS receives titled status frames; verify alternation; verify fallback when title null.
- **Manual:** AIPI-Lite hardware, meeting with title.

## Notes

- "Alternating" picked over "combined" (`Recording M:SS · <title>` on one line) because typical titles plus the timer easily exceed the LCD width.
- The bridge does not need any changes — it paints whatever HoldSpeak sends. Pure HoldSpeak-side feature.
- Future enhancement: cycle through more metadata fields (participant count, current speaker, etc.) using the same alternation slot.
