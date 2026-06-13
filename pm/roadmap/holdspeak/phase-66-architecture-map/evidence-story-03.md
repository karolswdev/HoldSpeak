# Evidence — HS-66-03: The meeting pipeline + the trust boundary

**Date:** 2026-06-13
**Verdict:** done. Two diagrams: the meeting flow, and the trust boundary
cross-checked one-to-one against SECURITY's egress table.

## What shipped

1. **The meeting pipeline** (flowchart). Live capture or import
   (`meeting_import.py` / `transcript_parse.py`) → windowed transcribe
   (`meeting_session/transcribe_loop.py`) → intent routing, opt-in
   (`plugins/router.py`) → the plugin host chain (`plugins/host.py`, intel
   to the LLM) → typed artifacts → the aftercare digest
   (`meeting_aftercare.py`) → the two outbound proposals (an accepted
   action to a GitHub issue, the digest/draft to Send to Slack via
   `slack_export.py`), both gated by propose/approve/execute
   (`plugins/actuator_executor.py`), approved-only.
2. **The trust boundary** (flowchart). A "Your machine" box (runtime, local
   Whisper, SQLite, local LLM) with each crossing drawn out and labeled by
   its gate. The seven crossings match SECURITY's egress table exactly:
   web responses (loopback/token), cloud intel (only when provider is
   cloud/auto, transcript text), Send to Slack (approved proposal, to the
   configured host), connector CLIs (opt-in pack, entity IDs), the
   deferred-intel ops webhook (opt-in, queue stats only), the wake-model
   download (one-time inbound fetch), and the paired device (same LAN,
   PSK). Rendered to PNG and reviewed: the box-and-gates reads cleanly.

## Accuracy / cross-check

The seven egress arrows were checked one-to-one against the rows parsed
from `docs/SECURITY.md` §4 (Cloud meeting intel, Deferred-intel failure
webhook, Wake-model download, Send to Slack, Connector CLI enrichment,
Web runtime responses, Device audio link). None invented, none omitted.
The doc says SECURITY is the source of truth if they ever drift.

## Proof

- Render guard green (6 blocks total now); both new diagrams rendered to
  PNG and eyeballed (the trust boundary especially).
- Voice guard green (13). Docs-only.
