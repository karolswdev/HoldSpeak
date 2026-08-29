# Phase 149 audit — the People/flywheel structural census

Read-only opus audit, 2026-08-29, against `feat/hs149-one-on-one-loop`
(= main `1be8fb00`). Condensed with every load-bearing file:line;
companion: [audit-tuesday-walk.md](./audit-tuesday-walk.md).

## The headline

**The keystone is ONE link: relationship ↔ calendar series
(uid + source_id).** Phase 147 already threads
`calendar_event_id` from an armed event onto the fired meeting
(web_server.py:986-988 → meeting_glue.py:294-303 →
meetings.calendar_event_id, schema.py:47). The moment a person
links to a calendar uid, the whole chain — event → armed recording
→ meeting → action items — resolves to that person. Everything
else the brief needs already exists.

## The People module as shipped (Phase 138)

- **Encrypted sidecar**, not the main DB:
  `~/.local/share/holdspeak/people.v1.sqlite3`
  (holdspeak/people/store.py:19); TWO tables — `meta` +
  `records(id, kind, lifecycle, …, nonce, ciphertext)`
  (store.py:414-421). Kinds: relationship, one_on_one, agenda_item,
  request, commitment, grounding_note. Payloads are encrypted JSON
  dicts — **additive fields need NO migration**.
- Service (services/people_service.py): relationship CRUD (:82-108),
  1:1s + agenda with roll-forward (:141-157, :318-341),
  request→commitment (:159-222), notes (:177-191), transition
  done/dismiss/reopen (:370-383), the Door projection
  `list_cards()` with `meeting_id=None` always (:358,
  `source="people_commitment"`, card_id `people:{id}` :352).
- Readiness = a content-free capability state (:497-506), NOT a
  score; sync always "local_only", capture "notes_only".
- Grounding = a manual evidence bundle (mcp/families/people.py:
  334-353) — no model call.
- Routes: /api/people/* (web/routes/people.py:29 — readiness,
  setup, relationships, one-on-ones, agenda, requests, notes,
  commitments/workbench|satisfy).
- MCP family lives at holdspeak/mcp/families/people.py (the
  Phase-133 families layout — NOT tools.py); 11 tools; default
  access "write" per the ledger-not-gate ruling (:156).
- Web: web/src/pages/cores/PeopleCore.tsx (296 lines) — roster +
  five lenses (Now/1:1s/Context/History/Info).

## The missing links (exhaustive-grep verdicts)

(a) person ↔ calendar event/uid: **DOES NOT EXIST** (zero hits any
direction). (b) person ↔ meeting: **DOES NOT EXIST**
(`meeting_id=None` is the only mention in the People lane;
docs/PEOPLE_INTEGRATION.md names it the deferred integration).
(c) **THREE PARALLEL COMMITMENT SYSTEMS** — follow-through
`action_items` (plaintext, meeting_id FK, schema.py:98-110) vs
People `kind='commitment'` (encrypted, own history model) vs
`decision_commitments` (schema.py:221-232); bridged ONLY by the
in-memory Door projection (follow_through_service.py:213-229) with
the 138 privacy law explicit at :214 (People content never enters
action_items/cadence/caches/exports). (d) 1:1 records ↔
meetings/calendar: **DOES NOT EXIST** (one_on_one payload:
relationship_id, agenda, private_prep, visibility, state —
people_service.py:150-156).

## The brief's input table

| Input | Exists? |
|---|---|
| Person↔event link | **NO — the keystone gap** |
| Open commitments per person | YES (`_open_commitments`, people_service.py:453-457) |
| Agenda backlog per person | YES (:141-146) |
| Decisions per person | NO (double gap — decisions↔person and meetings↔person) |
| Grounding/readiness | YES (MCP-only today) |
| Past 1:1 meetings per person | Broken at uid→person only |

## Phase-138 carried items that bite here

- **L2**: a broken sidecar yields SILENT empty People cards —
  a silent empty 1:1 brief would repeat it; 149 must surface
  sidecar state in the brief.
- **L3**: no dev-only keystore seam → populated People state can't
  walk headlessly without the keychain drill (the owner saw the
  GUI dialog a SECOND time this arc; the walk recipe is law).
- Deferred decision "relationship-to-meeting-participant
  association": 149 IS the first deliberate association path (via
  calendar, not participants); **docs/PEOPLE_INTEGRATION.md is the
  governing contract** — owner-selected textual evidence, explicit
  gesture, NO inferred identity (no voice/attendance/frequency).
- Deferred "encrypted Cadence overlay is categorically unsafe":
  the 149 brief must be READ-TIME computed, never persisted.

## Census recommendations (for the settled design)

1. **Series link, not occurrence**: store
   `calendar_links: [{uid, source_id, label}]` INSIDE the
   relationship's encrypted payload (additive; the link itself is
   People content and stays encrypted).
2. **Matching UX**: the explicit picker on the relationship detail
   ("Link calendar event" listing upcoming events, title-based
   suggestion, owner gesture) — satisfies the INTEGRATION contract.
3. **Never unify the commitment triad** — the brief overlays
   plaintext action items of person-resolved meetings alongside
   encrypted People commitments, in memory, the proven Door
   pattern.
4. Brief surface: the People relationship (a Prep/Brief lens)
   and/or the Door when a linked event is upcoming.
5. Seam map: people/store.py payload (no migration),
   people_service (link/unlink/resolve-by-uid/brief),
   door_service._calendar_event_item (person chip),
   monday_brief_service (per-person sections), mcp families/people
   (a brief/upcoming tool), PeopleCore (the lens), follow_through
   read path (action items by person-resolved meeting).
