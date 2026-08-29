# Phase 149 settled design — the 1:1 Loop

The design-beat spec (mandatory: this phase carries the Phase-138
privacy boundary). Ruled by the orchestrator 2026-08-29 from the
census + the reduced Tuesday walk; one Opus counsel ruling BEFORE
builders; the owner may overrule any row. Builders implement, they
do not redesign. **docs/PEOPLE_INTEGRATION.md is the governing
contract**: owner-selected evidence, explicit gesture, NO inferred
identity (never voice/attendance/frequency), People content never
leaves the encrypted store.

## The one sentence

The owner links a recurring calendar series to a person once, by
explicit gesture; from then on the rail knows who the 1:1 is with,
Record this produces a meeting that resolves to that person, and
opening the person before the 1:1 yields a read-time brief — open
commitments, agenda backlog, last linked meetings' action items —
computed across the encrypted/plaintext boundary and never
persisted.

## D1 — the honest keystore + sidecar truth (story 01, the unblock)

- **The L3 seam**: `HOLDSPEAK_PEOPLE_KEYSTORE_FILE=<path>` — when
  set, the People store uses a file-backed key at that path instead
  of the macOS keychain, AND (counsel F4) the sidecar path is
  ISOLATED alongside it — the dev keystore NEVER opens or creates
  the production sidecar at DEFAULT_PEOPLE_DB_PATH; doctor warns if
  both worlds exist. NEVER default; ignored when unset;
  `doctor` reports LOUDLY when active ("People keystore:
  DEV FILE — not for real use"); the production path is untouched.
  Grounded in the two-dialog incident: macOS keychains are
  UID-scoped and Python keyring #623 ignores custom keychain
  targets — headless populated-People walking is IMPOSSIBLE without
  this seam.
- **The L2 repair**: a broken/locked/absent sidecar must never
  render as silently empty — PeopleCore states already gate;
  the DOOR projection and the new brief adopt the same honesty
  (a "PEOPLE STORE LOCKED" quiet line beats absence).

## D2 — the link model (encrypted, series-level)

- `calendar_links: [{uid, source_id, label}]` INSIDE the
  relationship's encrypted payload — the link itself is People
  content; additive, no migration (payloads are encrypted JSON).
- **Series link** (uid + source_id), never per-occurrence: linking
  once covers every past and future occurrence of "1:1 w/ Ewa".
- **One person per series** (invariant P1): linking a series
  already linked to another relationship refuses by name
  (`series_already_linked`, naming the holder); re-linking the same
  person is idempotent. Unlink is a first-class verb.
- Resolution (`resolve_relationship_by_series(uid, source_id)`)
  lives in people_service, readiness-guarded: sidecar
  locked/absent → resolution returns "unavailable", NEVER an
  empty match (D1's honesty).

## D3 — the gesture (the INTEGRATION contract made flesh)

- The picker lives on the RELATIONSHIP detail (PeopleCore): "Link
  calendar event…" lists upcoming events (title + next occurrence
  + source label); rows whose title contains the person's
  display_name are suggested-first (counsel F10: the comparison is
  in-memory, case-insensitive, NEVER logged or persisted — a UI
  hint, not an inference) but NOTHING auto-links; the
  owner's click is the gesture; the stored evidence is the event's
  own title+uid (owner-selected textual evidence per the contract).
- Unlink lives beside it (in-world, two-beat).
- The People empty/unconfigured state adopts the joy pattern while
  we're in the room (the walk's era-mismatch note): lead with the
  act, not the absence.

## D4 — resolution on the flywheel surfaces (read-time only)

- `door_service._calendar_event_item` projects `person_label` (the
  display name) onto LINKED event items — computed at read time by
  querying the people service; sidecar unavailable → no chip, plus
  the D1 honesty line on the People surface (the Door never blocks
  on the sidecar). The rail row wears a quiet mono person chip.
- The fired meeting already carries `calendar_event_id` (147);
  the meeting read model's origin line (147's D7) EXTENDS to show
  the resolved person when the sidecar is open. No new meeting
  columns — resolution is always read-time via uid→person so the
  PLAINTEXT DB never stores a person reference (the 138 law).
- PeopleCore's relationship header shows the next linked
  occurrence ("NEXT 1:1 · THU 10:00").

## D5 — the brief (read-time, never persisted)

- `people_service.one_on_one_brief(relationship_id)` computes, in
  memory: open commitments (encrypted), agenda backlog (encrypted),
  grounding notes count (encrypted), the last N linked meetings
  (plaintext, via the uid chain over meetings.calendar_event_id →
  calendar_events.uid) with their OPEN action items (plaintext,
  BY REFERENCE — never copied), and any decisions minted from those
  meetings (plaintext, decision_records by meeting linkage where it
  exists).
- Renders as the **Prep lens** on the relationship; the rail row of
  a linked event gains an in-world **PREP** affordance opening the
  person's Prep lens (beside Record this — the Tuesday pair: prep
  it, record it).
- MCP: `people.one_on_one.brief` (the grounding-bundle pattern,
  families/people.py). **Counsel MUST-FIX F6, law of this story:**
  the tool gates on `access_mode() != "off"` via `_require_access`
  AND filters to `shared_intent` visibility via the `_mcp_readable`
  path (people.py:188, 276-281, 356-361 are the exact precedent) —
  leader_private content NEVER crosses to an MCP client. F7: the
  response carries the grounding bundle's `policy` block naming its
  disclosure boundary. F11: the brief names the count of UN-linked
  meetings in its window (manual recordings without
  calendar_event_id) so the owner sees what it does not cover.
- NEVER persisted; NEVER enters cadence_*/action_items/caches/
  exports (the 138 law verbatim); the deferred-138 "Cadence overlay
  categorically unsafe" ruling is respected — this is a read-time
  view, not an overlay.

## D6 — the commitment triad stays three (settled)

follow-through `action_items` (plaintext), People `commitment`
(encrypted), `decision_commitments` (plaintext) are NOT unified.
The brief OVERLAYS plaintext items beside encrypted ones in memory
— the proven Door projection pattern (follow_through_service.py:
213-229). Any unification is explicitly out of scope.

## D7 — deliberate non-scope

Monday Brief per-person sections (next-arc candidate — needs this
phase's link first); meeting-participant inference (FORBIDDEN by
the contract); key recovery/rotation/multi-device (138 deferred
list); the 393 People reachability gap (ledgered — Open People is
⌘K-only at narrow; weigh a dock/Go entry in a later beauty pass);
writing ANY person reference into the plaintext DB.
