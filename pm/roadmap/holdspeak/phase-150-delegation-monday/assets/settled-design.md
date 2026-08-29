# Phase 150 settled design — Delegation + the Chief-of-Staff Brief

The design-beat spec (mandatory: this phase extends the People
privacy boundary onto a PERSISTED surface). Ruled by the
orchestrator 2026-08-29 (night) from the census + the Monday walk;
one Opus counsel ruling BEFORE builders; the owner may overrule any
row. Builders implement, they do not redesign.
docs/PEOPLE_INTEGRATION.md governs: explicit gesture, NO inferred
identity; the 138 law: People content never persists outside the
encrypted store.

## The one sentence

The owner maps an owner-string to a person once (a second explicit
gesture, encrypted like calendar_links); the Door then answers
"waiting on WHOM" with person chips, filters, and honest
staleness; and the Monday Brief gains a read-time chief-of-staff
overlay — each report's week — that is computed on every read and
never touches the persisted brief tables.

## D1 — the owner gesture (encrypted, explicit, never inferred)

- `owner_mappings: [{owner_string, relationship_id? — NO:
  mappings live ON the relationship}]` — precisely: the
  relationship's encrypted payload gains
  `owner_aliases: [<string>, …]` (the calendar_links pattern; an
  alias is owner-selected evidence — the exact string from a real
  card). `resolve_relationship_by_owner(owner_string)`: the
  readiness-guarded clone of resolve_relationship_by_series
  (case-insensitive compare in memory, never logged).
- **Invariant P2 (one person per alias):** an alias held by
  another relationship refuses `owner_alias_taken` naming the
  holder; self-remap idempotent; unalias first-class.
- The GESTURE lives where the pain is: on a Door card's owner
  fragment ("map to person…" via the card's existing open/verb
  surface → a picker listing relationships, suggestion-first by
  case-insensitive equality, NOTHING auto-maps) AND on the
  relationship detail (an Aliases row beside Calendar series).
  Reserved strings "Me"/"Remote"/"you" are never mappable
  (refused by name).
- `delegated_at` lands on action_items (a bare TIMESTAMP — no
  person reference; lawful under the schema grep pin): set by the
  delegate verb and by commit_decision/edit when the owner string
  CHANGES; staleness renders from delegated_at ?? created_at.

## D2 — the delegation lane (read-time projection on the board)

- The board projection resolves MAPPED owner strings to
  {person_label, person_relationship_id} via a request-scoped memo
  (the door person-index pattern); unmapped strings render exactly
  as today. The Door card's owner fragment becomes a quiet person
  chip for mapped owners (click → filter), plus "waiting Nd" from
  delegated_at.
- Filter UI: person chips in the board header (one per mapped
  person present on the board + "everyone"); clicking drives the
  EXISTING server owner filter (or client filter — builder picks
  the smaller honest diff and states it). Group-by-person is OUT
  of scope this phase (chips+filter first; ledger the grouping).
- The _FollowThroughObserver redaction already covers the board
  result — VERIFY it swallows the new projected fields (a pin).
- People's inverse view: the relationship detail's Prep lens
  ALREADY shows THEY-OWE via linked meetings' action items; the
  board filter is the manager's other direction. No new store
  crossings.

## D3 — the chief-of-staff overlay (READ-TIME ONLY, the hard law)

- The Monday Brief response gains `person_sections` — computed in
  BOTH generate() and _load_brief() for the RESPONSE, NEVER
  inserted into monday_briefs/monday_brief_items/shelf (the
  never-persist pin: a write-count spy on the brief tables during
  generation with People present).
- Each section (per relationship with ANY signal): the next linked
  1:1 (the door person-index read), open THEY-OWE count + stalest
  age (board filtered by the person's aliases), YOU-OWE count
  (encrypted commitments), agenda backlog count — sourced via
  one_on_one_brief + the board; names resolve at read time from
  the encrypted store; sidecar unavailable → the L2 honesty line,
  never silence, never half-truth.
- **Person-item verbs are the manager's** (the walk's D3): "Add to
  1:1 agenda" (the EXISTING 138 people.agenda.add path — a real
  write to the encrypted store through its own authority) and
  "Open person" — never Acknowledge/Defer on a human.
- MCP: monday_brief.get returns person_sections ONLY through the
  People family's gate discipline: reuse the F6 pattern — if
  people access is off, person_sections is absent; contents
  filtered shared_intent-only. (The brief tool precedent from 149
  is the law.)

## D4 — the walk's defects, folded

- D1: BriefLane first-load presence — when NO brief exists, the
  lane renders the lead-with-the-act state ("Generate your brief"
  — the joy pattern), not null.
- D2: persisted brief details become summary-level — the
  SettingsService receipt detail truncates to the event name, raw
  argument paths never enter monday_brief_items (a hygiene pin).

## D5 — the debt rider (non-negotiable this phase)

**The web-inherited baseline**: a
`web/web-inherited-baseline.txt` (the six names, each annotated
with its main-anchored provenance) + a vitest-side or script-side
checker the close sweep can consult, so web failures get the same
baseline-subset vocabulary as pytest. Fixing any of the six
instead is welcome but not required.

## D6 — deliberate non-scope

Group-by-person board partitions (ledger); auto-matching owner
strings EVER (forbidden); persisting any person section (forbidden
— F2 made mechanical); JIRA; the 393 People reachability; new key
bindings; Brief regeneration semantics (frozen-per-day stands).
