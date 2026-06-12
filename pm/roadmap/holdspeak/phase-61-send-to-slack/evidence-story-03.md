# Evidence — HS-61-03: Docs: Send to Slack

**Date:** 2026-06-12
**Verdict:** done. The Meeting Mode Guide, SECURITY, and POSITIONING all
carry the feature honestly; the voice guard now knows its banned synonyms,
proven both ways.

## What shipped

- **Meeting Mode Guide** (`docs/MEETING_MODE_GUIDE.md`): a "Send to Slack"
  subsection in Meeting Aftercare, right after "Draft the follow-up", with
  a real product screenshot (`assets/aftercare/send-to-slack.png`, from the
  HS-61-02 live dogfood). It states the configured-only visibility, the
  three-step truth (button → proposal whose preview IS the message →
  **approving is the moment it posts**, explicitly contrasted with the
  GitHub-issue flow where approval is state-only), the host gate, and the
  two honesty notes (the URL is treated like a password; long digests
  truncate visibly). The archive-API list gains the export route.
- **SECURITY** (`docs/SECURITY.md`): the egress table gains the Send to
  Slack row (what leaves: the digest/draft exactly as previewed, no
  transcript, no audio; the gate: double opt-in, URL = consent for exactly
  its host, per-action approval, credential rule). Section 5 (secrets)
  gains the `slack_webhook_url` entry: stored in config.json because it IS
  the configuration, treated as a credential everywhere else.
- **POSITIONING** (`docs/internal/POSITIONING.md`): the canonical row —
  "Send to Slack", not "Slack integration" / "Slack connector"
  (user-facing) / "Slack export".
- **The voice guard** (`tests/unit/test_doc_drift_guard.py`): `_BANNED_NAMES`
  gains `slack (integration|export)`, and the seeded-violations test proves
  it both ways (flags "the Slack integration" / "use the Slack export";
  spares "Send to Slack creates a proposal" and "the configured Slack
  webhook").

## Proof

- `uv run pytest -q tests/unit/test_doc_drift_guard.py` → 13 passed (zero
  dashes in the new prose, image refs resolve, vocab + names clean, the
  new pattern proven both ways).
- Full suite: **2767 passed, 17 skipped** (docs + one guard pattern; no
  count change).
