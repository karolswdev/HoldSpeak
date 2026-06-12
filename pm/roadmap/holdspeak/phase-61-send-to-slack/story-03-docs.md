# HS-61-03 — Docs: Send to Slack

- **Project:** holdspeak
- **Phase:** 61
- **Status:** done
- **Depends on:** HS-61-02
- **Unblocks:** HS-61-04
- **Owner:** unassigned

## Problem
A feature that egresses meeting content must be documented with the
approval truth and the security posture before the phase can close, and
"Send to Slack" needs its canonical name fixed in POSITIONING.

## Scope
- **In:** the Meeting Mode Guide's aftercare section gains Send to
  Slack: how to configure (one incoming-webhook URL), what the message
  contains (the digest or the follow-up draft, exactly as previewed),
  the approval truth (nothing sends without a per-action approval), the
  host gate, and the credential note (Slack treats webhook URLs as
  secrets; HoldSpeak stores it locally and never displays it
  elsewhere). `docs/SECURITY.md` egress table gains the row (what
  leaves, where to, when, the gate). `docs/internal/POSITIONING.md`
  gains the canonical row "Send to Slack". All prose under the live
  voice guard.
- **Out:** README feature marketing (the README's plugin/feature counts
  stay as-is unless a lock forces an update — check the locks).

## Acceptance criteria
- [x] The Meeting Mode Guide section ships with the approval truth, the
      host gate, and the credential note stated plainly (plus a real
      product screenshot and the API-list row).
- [x] The SECURITY egress row ships (and the secrets section gains the
      webhook-URL entry).
- [x] The POSITIONING canonical-name row ships ("Send to Slack").
- [x] The voice guard and the full suite are green (no em/en dashes in
      user-facing prose, no banned vocab, names canon-consistent; the
      guard's banned-names pattern now covers the Slack synonyms, proven
      both ways).
      See `evidence-story-03.md`.

## Test plan
- `uv run pytest -q tests/unit/test_doc_drift_guard.py` then the full
  suite.
