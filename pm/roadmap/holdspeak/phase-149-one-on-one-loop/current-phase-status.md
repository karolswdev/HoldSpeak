# Phase 149 — The 1:1 Loop

**Status:** chartered (0/6).

**Last updated:** 2026-08-29.

## Owner mandate

The value era's keystone, picked by the owner from the handover
menu after their pivot (verbatim in HANDOVER.md §0: value for "a
Senior Software Architect, who now manages 3 people"). The owner
confirmed the People module exists and asked why it isn't carrying
their week; the audits answered: two eras of machinery, one seam
never sewn. Branch `feat/hs149-one-on-one-loop` from main
`1be8fb00`.

Standing laws with extra weight: **docs/PEOPLE_INTEGRATION.md is
the governing contract** (explicit gesture, owner-selected
evidence, NO inferred identity); the 138 privacy law (People
content never leaves the encrypted store — read-time projection is
the only bridge); the keychain walk law (this arc's two-dialog
incident is the proof and the story-01 charter); joy on any touched
surface; the Tuesday question IS this phase.

## Evidence base

- [`assets/audit-census.md`](./assets/audit-census.md) — every seam
  file:line. Headlines: **the keystone is ONE encrypted series
  link** (147 already threads calendar_event_id onto meetings);
  **three parallel commitment systems, deliberately — never unify**;
  the brief's input table (only the link and the decisions chain
  are missing).
- [`assets/audit-tuesday-walk.md`](./assets/audit-tuesday-walk.md)
  + [`assets/audit-walk-shots/`](./assets/audit-walk-shots/) +
  [`assets/audit-walk-rig.py`](./assets/audit-walk-rig.py) — the
  reduced walk (zero keychain writes by construction) and the
  two-dialog incident record: **the Tuesday probes both DO NOT
  EXIST on glass** (event→person; armed-recording→person); the
  populated-People walk is BLOCKED by 138's L3 (macOS keychains are
  UID-scoped; Python keyring #623 ignores custom keychains) — story
  01 unblocks it forever.
- [`assets/settled-design.md`](./assets/settled-design.md) — D1–D7:
  the dev keystore seam + sidecar truth, the encrypted series link
  with invariant P1, the explicit-gesture picker, read-time
  resolution on the flywheel surfaces, the never-persisted brief,
  the triad staying three.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-149-01 | The honest keystore + sidecar truth (L3+L2) | ready | [story-01](./story-01-honest-keystore.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-149-02 | The link (encrypted series link + resolution) | ready | [story-02](./story-02-the-link.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-149-03 | The gesture (picker + rail person chip) | ready | [story-03](./story-03-the-gesture.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-149-04 | The brief (Prep lens + PREP on the rail) | ready | [story-04](./story-04-the-brief.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-149-05 | The record book | ready | [story-05](./story-05-record-book.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-149-06 | The walk and the close | ready | [story-06](./story-06-walk-and-close.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Chartered 2026-08-29 from the census + the reduced Tuesday walk;
the design counsel ruling is the gate ahead of builders. No story
started.

## Decision log

- **2026-08-29 — owner pick:** The 1:1 Loop chosen from the
  value-era menu (over the delegation lane, decision practice, and
  the chief-of-staff brief).
- **2026-08-29 — the two-dialog incident:** two delegated walk
  attempts threw the macOS "Keychain Not Found" GUI dialog at the
  owner (the 138 dialog, seen again). Root cause established:
  UID-scoped keychains + keyring #623; the owner's keychain search
  list verified untouched both times; the walk was completed
  REDUCED (zero keychain writes) by the orchestrator; L3 graduates
  to story 01. Lesson recorded in memory: module-touching walk
  briefs carry the module's gotchas verbatim.
- **2026-08-29 — orchestrator rulings (the spec):** series-level
  link in the ENCRYPTED payload; invariant P1 (one person per
  series, named refusal); explicit-gesture picker on the
  relationship detail; read-time resolution everywhere (no person
  reference EVER in the plaintext DB); the brief never persisted;
  the commitment triad stays three. The owner may overrule any row.
- **2026-08-29 — counsel design ruling: RATIFY-WITH-CONCERNS —
  "The design earns the owner's Tuesday."** ONE must-fix, absorbed
  as story-04 law before any builder: the brief MCP tool gates on
  access_mode + shared_intent visibility (F6 — the exact people.py
  precedent; skipping it would be a REAL breach). Four should-fixes
  absorbed: F1 (the gate emphasized), F4 (the dev keystore's
  sidecar path is isolated, never the production path), F7 (the
  policy disclosure block rides the brief), F8 (PREP suppressed
  when resolution unavailable). The counsel also VERIFIED the
  privacy boundary concretely: no Door cache, no Door WS
  broadcast, the 138 observer redaction already covers the
  projection path, meeting payloads carry zero person fields —
  "lawful display", no leak path found.

## Ledger (counsel, carried openly)

- F2: if the brief EVER gains a persist path, the
  _FollowThroughObserver redaction pattern must ride it (persist
  is D7-forbidden this phase).
- F5: (uid, source_id) linkage assumes per-source UID namespaces;
  revisit P1 if cross-source dedupe ever lands (146 ruled no
  dedupe — aligned today).
- F10: title-match suggestions are in-memory UI hints, never
  logged/persisted (folded into stories 03/04).
- F11: manual recordings (null calendar_event_id) are excluded
  from the brief's linked history; the brief names their count
  (folded into story 04).
- Source re-subscription dangles links; unlink/relink is the
  honest recovery (auto-migration deliberately not built).

## Risk register

- The encrypted↔plaintext read-time bridge is the phase's whole
  risk surface: every new read path must be readiness-guarded (D1
  honesty) and never write across (the 138 law). The counsel is
  asked to probe exactly this.
- Recurring-series semantics: the link is by (uid, source_id);
  feed re-subscription changes source_id → links dangle; the
  unlink/relink gesture is the honest recovery (ledger the
  auto-migration question).
- The 393 People reachability gap (⌘K-only) — ledgered, not
  chased.
- Walk law: every walk leg touching populated People rides the
  story-01 seam; keychain drills are RETIRED for walks.
