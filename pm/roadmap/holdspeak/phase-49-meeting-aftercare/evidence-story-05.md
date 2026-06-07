# Evidence — HS-49-05: Docs (meeting aftercare, end to end)

Write-once record of the docs story. The rule that matters: tell aftercare as one
coherent flow that matches the shipped UI, ground every claim in code, and
over-claim nothing (off-by-default actuators, preview-only drafts, real
diffs/provenance).

## What shipped

**`docs/MEETING_MODE_GUIDE.md`** — a new "Meeting Aftercare (close the loop)"
section (added to the table of contents) that tells the flow end to end:
- **What the panel shows** — still open by owner, what was decided, and the real
  since-last-meeting diff (and that it stays quiet with no prior meeting / no
  change; the numbers are real, nothing invented).
- **Show me the moment** — the transcript jump appears only where a real timestamp
  resolves to a real segment (no fake `0:00`), reveals the segment without taking
  keyboard focus.
- **File an accepted action as an issue** — records a proposal only through the
  existing propose -> approve -> execute flow, with the honest safety note:
  off by default (`allow_actuators` + per-project allow-list + host-injected
  connector), per-action human approval, audited, payload-parity. States the
  connector runs the operator's local `gh` and can only `gh issue create`.
- **Draft the follow-up** — assembled locally, preview + copy only, no model call,
  nothing sent; honest at empty.
- Three real screenshots from the shipped UI (`docs/assets/aftercare/`:
  `aftercare-digest.png`, `file-as-issue.png`, `followup-draft.png`).
- The three new endpoints added to the Web API "Archive/data APIs" list:
  `GET .../aftercare`, `GET .../followup-draft`, `POST .../aftercare/file-issue`.

**`README.md`** — a "Then close the loop" paragraph after the meeting-intelligence
+ actuator framing, linking the new guide section; frames aftercare as the
meeting-side follow-through, read-only and local, nothing sent or run without
approval.

**`docs/README.md`** — the Meeting Mode Guide index entry now mentions aftercare
(open/decided/changed, jump to the moment, file an approved issue, draft the
follow-up).

## Grounding (every claim traces to code)

- open-by-owner / decisions / since-last diff -> `holdspeak/meeting_aftercare.py`
  (`compute_meeting_aftercare`).
- transcript jump only on a real timestamp -> `resolve_provenance_segment`.
- file-issue records a proposal only -> `holdspeak/web/routes/meetings.py`
  (`api_aftercare_file_issue`) + `db/actuators.record_proposal`.
- off by default / approval / parity / audit -> `plugins/actuator_executor.py`;
  `gh issue create` only -> `plugins/builtin/github_issue_actuator.py`
  (`GITHUB_ISSUE_MANIFEST`).
- follow-up is local + preview only -> `build_followup_draft` +
  `GET /api/meetings/{id}/followup-draft`.

## Tests (ran, read the output)

- `uv run pytest -q -k "doc_drift or link or doc_guard or doc" --ignore=tests/e2e/test_metal.py`
  → **65 passed, 2 skipped**. This covers the dangling-relative-link guard and the
  embedded-image-ref guard, so the new section's three `assets/aftercare/*.png`
  references and the README anchor link all resolve.

## Voice

No em or en dashes, no rule-of-three padding, no "not X but Y" (the humanizer /
`DOCS_STYLE.md` rule). Plain and direct, mirroring the Phase-48 docs pattern (a
numbered end-to-end flow + real screenshots + an honest posture note).
