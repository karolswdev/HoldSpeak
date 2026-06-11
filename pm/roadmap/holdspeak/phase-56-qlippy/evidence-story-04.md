# Evidence — HS-56-04: Learning + aftercare cards

**Date:** 2026-06-11
**Branch:** `phase-56-qlippy`

## 1. What shipped

**Backend (three observational seams, nothing on the hot path changed):**
- **`learning_event`** at the journal correct route
  (`holdspeak/web/routes/dictation/pipeline.py`): broadcast **only when the
  correction was actually taught AND has real Jaccard reach**
  (`recorded and similar > 0`) — the honest-reach rule. Payload
  `{kind, gist (120-char truncated), value, similar, enabled}`; the `similar`
  on the wire is the very number the route returns (one matcher,
  `reach_for_gist`, one number — no second heuristic). A refused teach (e.g.
  a secret-shaped transcript) or zero reach stays silent.
- **`aftercare_ready`** from the meeting wrap flow:
  `build_aftercare_ready_event(db, meeting_id)` appended to
  `meeting_aftercare.py` — computed from the same read-only digest /history
  uses, returns `None` when the digest is empty or errors. Wire-safe payload
  `{meeting_id, title, open_total, decided_total, top_items (max 2 of
  task/owner)}`. Fired from `MeetingSession.save()` only when the DB save
  succeeded AND the meeting is finished (`ended_at` set) — an autosave
  mid-meeting stays silent; a broadcast failure never breaks the save.
- **`on_meeting_ready`** observer threaded through the deferred intel queue
  (`process_next_intel_job` / `drain_intel_queue`) and wired in the web drain
  route to broadcast `aftercare_ready` when deferred intelligence lands —
  purely observational; an exploding observer never breaks the audited job
  completion (tested).

**Frontend (`qlippy-events.js`):**
- `learning_event` → the `learned` card (lightbulb glyph): "Learned from
  you", `Applied "gist" → value — matches N past dictations`, with the
  corrections-off honesty suffix when the memory is taught but not yet
  routing; "View digest" opens /dictation; local-only privacy line. Guards
  `!data.similar` client-side too — Qlippy never claims learning that did
  not happen.
- `aftercare_ready` → the `present-note` card: "Your meeting left N open
  item(s)", the title + top items, "Open aftercare" opens /history,
  auto-dismisses (14 s, pause-on-hover holds it); local-only privacy line.

## 2. Live dogfood (real correction, real wrap, real socket)

`dogfood_story04.py` — no mocks in the chain: a real journal row corrected
through the real route fires the real broadcast; a real `MeetingSession`
wrapping a finished meeting emits through the server's own broadcast:

```
PASS  the real correction's real broadcast presented the learned card (matches 2, same number the route returned)
PASS  a refused teach stayed silent — no learned card for no learning
PASS  the real meeting wrap's real broadcast presented the aftercare card (2 open, top items named)
PASS  zero page errors across the whole run
RESULT: PASS
```

Screenshots reviewed: `story04-learned-card.png` (learned Qlippy with the
composited lightbulb, the applied gist → value, "matches 2 past dictations",
the local-only line, View digest) and `story04-aftercare-card.png`
(present-note Qlippy, "Your meeting left 2 open items", "Roadmap sync — Fix
the login bug (Me) · Draft the rollout note (Sam)", Open aftercare).

## 3. Tests + suite

`tests/integration/test_presence_learning_aftercare_broadcasts.py` — 8 tests:
learning_event positive (broadcast reach == response reach), the
nothing-taught negative, gist truncation; aftercare_ready on a wrapped
meeting with open work (top_items capped at 2, wire-safe keys), the
empty-digest negative, the unfinished-meeting negative; the intel queue's
`on_meeting_ready` hand-off and the exploding-observer guarantee.

```
$ uv run pytest -q tests/integration/test_presence_learning_aftercare_broadcasts.py
8 passed in 1.01s
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2590 passed, 17 skipped in 82.24s (0:01:22)
```

(2582 → 2590.) Build clean; correction storage, reach math, and the
aftercare computation untouched per scope.
