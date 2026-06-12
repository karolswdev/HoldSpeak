# HS-62-03 — Docs + re-shot screenshots

- **Project:** holdspeak
- **Phase:** 62
- **Status:** done
- **Depends on:** HS-62-02
- **Unblocks:** HS-62-04
- **Owner:** unassigned

## Problem
The docs quote the old privacy paragraphs verbatim (and a lock enforces
that), and user-facing docs embed screenshots showing the old copy.

## Scope
- **In:** `INTELLIGENT_TYPING_GUIDE.md` Qlippy section describes the
  badge contract instead of quoting paragraphs (the verbatim lock in
  `test_doc_drift_guard.py` rewritten to pin the badge); `USER_GUIDE.md`
  + `MEETING_MODE_GUIDE.md` aligned where they quote card/note copy;
  `POSITIONING.md` gains the voice rule: egress is stated by the badge,
  not prose — cards and notifications never narrate privacy.
  Re-shoot from live runs every user-facing-doc screenshot showing old
  copy (the Qlippy card assets, `aftercare/followup-draft.png`,
  `aftercare/send-to-slack.png`, others found by eye).
- **Out:** SECURITY.md (reference docs explain once — allowed); roadmap
  evidence screenshots (history, not user-facing).

## Acceptance criteria
- [x] No user-facing doc quotes a privacy paragraph as card copy; the
      badge contract is documented once.
- [x] The POSITIONING voice rule ships; the voice guard green.
- [x] Every re-shot screenshot reviewed by eye and embedded; no
      user-facing doc image shows the old copy.

      See `evidence-story-03.md`.

## Test plan
- The rewritten doc-drift locks; the doc guard slice; the full suite.
