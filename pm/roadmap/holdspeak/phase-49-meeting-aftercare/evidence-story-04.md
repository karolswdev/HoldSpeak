# Evidence — HS-49-04: Draft the follow-up (preview + copy)

Write-once record of the follow-up draft. The rule that matters: it is preview +
copy only — assembled locally from data that already exists, never sent, no
connector opened. Honest when there's little to say (no padding).

## What shipped

**Backend**
- `holdspeak/meeting_aftercare.py` — `build_followup_draft(digest)`: a pure,
  deterministic markdown assembler over the HS-49-01 digest. It re-uses the
  aggregation rather than re-querying. Sections appear only when they have
  content: a `# Follow-up: {title}` header + date, `## What we decided` (decision
  + "Why: rationale" when present), `## Open items` (owner: task with due), and
  `## Since {previous}` (new decisions / new action items / closed since last
  time) only when the diff actually changed. An empty meeting yields one plain
  line ("Nothing was decided and nothing is open for this meeting."), not filler.
  The voice avoids dashes so the draft pastes cleanly into chat.
  - **Local-first / no LLM:** settled on deterministic assembly. There is no model
    call and nothing to fail open from — the draft is always available offline.
- `holdspeak/web/routes/meetings.py` — `GET /api/meetings/{id}/followup-draft`
  returns `{meeting_id, markdown, is_empty}`. Pure read; 404 for an unknown
  meeting. No write, no egress.

**UI** (`web/src/pages/history.astro` + `web/src/scripts/history-app.js`)
- A "Draft follow-up" toggle in the aftercare panel head. `fetchFollowupDraft()`
  pulls the locally-assembled markdown; the panel reveals it in a monospace
  preview with a "Copy draft" button (reuses the existing `copyMarkdown` idiom
  the artifact cards use) and a note: "Assembled locally from this meeting.
  Preview and copy only; nothing is sent." Toggling again hides it.

## Tests (ran, read the output)

- `tests/unit/test_meeting_aftercare.py`:
  - the draft includes decisions with "Why: …", open items as "owner: task (due …)",
    folds a blank owner to "Unassigned", and contains no em dash;
  - an empty meeting is honest, not padded (the plain line, zero `## ` headers);
  - the since-last section renders new decisions / new action items / closed.
- `tests/integration/test_web_meeting_aftercare_api.py` — the endpoint returns the
  assembled markdown (header + decisions + open items) and `is_empty=False`; 404
  for an unknown meeting.
- `uv run pytest -q -k "aftercare or followup or meeting or action_item or artifact" --ignore=tests/e2e/test_metal.py`
  → **479 passed, 12 skipped**.

## Build + screenshot

- `(cd web && npm run build)` clean; `git ls-files holdspeak/static/_built` →
  empty (0 tracked).
- `scripts/screenshot_aftercare_followup.py` →
  `screenshots/story-04-followup-draft.png`: the "Draft follow-up" preview with
  the assembled markdown (Follow-up header, What we decided with rationale, Open
  items by owner with due, Since-last delta), the Copy button, and the
  "nothing is sent" note.

## Honesty / invariants held

- **Preview + copy only.** The only new endpoint is a GET that returns text; the
  UI shows it and copies it. Nothing is sent, no connector is opened.
- **No padding.** Sections render only with real content; an empty meeting gets
  one honest line.
- **Local-first.** Deterministic assembly from existing data; no model call, no
  network. Read-only and behavior-preserving; no duplication of the HS-49-01
  aggregation (the draft consumes it).
