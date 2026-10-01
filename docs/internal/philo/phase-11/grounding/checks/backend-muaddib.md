# Check — Muad'Dib (Claude Opus 5.5, session https://claude.ai/code/session_01L3k9v1STCS3ur6wJYy5AgF), 2026-09-29

Artifact: `docs/internal/philo/phase-11/grounding/backend.md` @ `8e82b0800` (draft PR #704, Astra's lane, session `01a0efc1-5f67-7820-9ee7-45b05d7bdf2d`).

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. The grounding is sound on the contract as built. §1 anchors (update-bound `channel.preview`/`prepare` descriptors, `render_update`, file naming, `update_id` history filter, update-only delivery projection) match the tree. The lifecycle-preservation list (§1, the last paragraph) is right and binds the charter.
2. Five recommendations were written before the owner's rulings R1–R9 (`faces.md` §7, same day) and are superseded by them:
   - Q1 brief: "omit personal triage state" → R1: the whole brief, including the person sections. "Stop being so paranoid."
   - Q1 decision: "the governing Decision Record only" → R2 "All": the desk record, the meeting decision and the decision receipt each get a renderer.
   - Q2 meeting summary: "summary + selected decisions/actions" → R3 "All": the summary with topics, the digest and the follow-up. Astra's "no transcript" holds; no form sends the transcript.
   - Q3 Slack: "bot token first" → R6: incoming webhook. The receipt says what `200 ok` proves (POSTED, no link), per F5. It never fabricates a link.
   - §1 provenance ("source snapshot digest, renderer version, source revision…") → R9: "if it changes, we re-send." The Phase 10 byte contract stays: a prepared send keeps its frozen bytes, and an inline Send rechecks the preview digest. Add only `kind`, `source_id`, the frozen title/slug and a display label. No snapshot-digest or renderer-version machinery, and no stale-version tracking on the face (Tenet 1).
3. Q5 (C4) agrees with R7: rewrite aftercare Slack onto the channel, with no migration. The owner re-adds one Slack destination. Q7 agrees with R8: Mark delivered stays update-only. Q6 (the thread prepares) default YES stands.
4. Verification: the one failure that also fails serially (`tests/integration/test_phase200_recipe_catalog.py:648`, `co_consts` timing ints) is a Python 3.14 artifact of the lane's venv; the house interpreter is 3.13 (CLAUDE.md law 16: `uv sync --python 3.13`). The full suite at `90fa3888c` under 3.13 did not show it. Classified (a) environment; no home needed beyond using 3.13.

CONDITIONS: the charter adopts R1–R9 over §5's recommendations, as above. No edit to the grounding itself is owed; it stands as the record of what was known before the rulings.

MISSED: Q4 (long Slack documents) is the one fork still open for the owner. It goes into the charter as a question with Astra's default: refuse above 4,000 characters with a named refusal.

TUESDAY: yes. With the rulings applied he opens a brief, a decision or a summary, sees the words, picks a destination and presses Send.

UNKNOWN: I did not rerun the probes; I read §§1–5 against the anchors I spot-checked.
