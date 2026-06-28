# Phase 19 — The iPad joins the meeting contracts

**Status:** planned — runs in parallel with Phase 18 (disjoint client surfaces:
`meetings` vs `dictation`). Stories detailed on open.

**Last updated:** 2026-06-27 (**authored** from the parity audit, the meetings half of
theme 2/3.)

## Why this phase exists

The same imbalance as Phase 18, on the meetings side: the hub serves the full meeting
contract; the iPad reads almost none of it. The audit's verified holes:

- **Meeting aftercare** is never fetched or rendered on Apple — no
  `/api/meetings/{id}/aftercare` client, no close-the-loop card, no
  `aftercare/file-issue` call (`meetings.py:999` is unreachable from Swift).
- **The faceted archive** is missing — flat lists only (`MeetingListView`,
  `CompanionShellApp.swift:205`); `listMeetings()` sends zero query params; no
  `/api/meetings/facets` caller.
- **Meeting import** has no iPad surface — the only `.fileImporter`
  (`ModelManager.swift:93`) is GGUF-gated; there is no audio/transcript import.
- **Artifacts render without their provenance** — `ReviewUI.swift:530/611` bind
  type/title/body/status only, though `Models.swift` carries `confidence` and `sources`. The
  deeper question: does the iPad ever read the hub's persisted `/artifacts` /
  `/all-action-items`, or rely solely on changeset sync?
- **Proposals review** is missing — nothing reads `GET /api/meetings/{id}/proposals`; the
  iPad only approves its own sends, and `sendNow` collapses propose→review→approve into one
  tap.
- **The learning loop** has no read client (deliberately parked per `ENTITY-CATALOG.md`); a
  read-first review surface is in scope, on-device journaling is not.

## The load-bearing design call

**Read the hub's source of truth; do not re-derive from sync.** The artifacts/aftercare/
proposals data is persisted on the hub. The iPad should read it (or the phase must *document*
the changeset sync as the single guaranteed source). The artifact confidence/sources gap is
the canary: the data is already carried on the wire and simply not rendered. Reuse the
Phase-18 `HTTPDesktopClient` extension pattern; reuse the existing `DeskHostLink.decide`
approval UI for any new propose→approve flow (split the one-tap send while here).

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-19-01 | Meeting aftercare — client + close-the-loop card + file-issue — **leads** | in-progress (client + close-the-loop card landed, sim-proven; file-issue + metal remain) |
| HSM-19-02 | The faceted archive — search + facets (compact-aware) | todo |
| HSM-19-03 | Meeting import on the iPad (audio + transcript → the hub engine) | todo |
| HSM-19-04 | Artifact provenance — read the hub's artifacts, render confidence + sources | in-progress (client + confidence-ring card landed, sim-proven; metal remains) |
| HSM-19-05 | The proposals review surface + split the one-tap send | todo |
| HSM-19-06 | The learning-loop review client (read-first; on-device journaling deferred) | todo |
| HSM-19-07 | The real-metal proof + docs | todo |

## Where we are

Not started. **19-01 leads** (aftercare is the highest-severity meetings hole and exercises
the full read-client + approval-reuse pattern the rest follow). 19-04 carries the
artifact-provenance render fix that also feeds Phase 20's compact pass and Phase 21's honesty
work. The `TextProcessor` ported in 18-04 is reused for meeting-side symbol application here —
do not re-implement it.
