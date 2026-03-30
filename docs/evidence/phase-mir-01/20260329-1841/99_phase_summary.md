# MIR-01 Incremental Summary

Date: 2026-03-29T18:41:29-06:00
Commit: b434e2cdd945ab9ccc8cd4ca1ffb62b580001bcf

Completed in this increment:
- Added holdspeak/plugins/signals.py (deterministic lexical multi-intent scorer).
- Added holdspeak/intent_timeline.py (rolling window builder + transition detector).
- Extended router with preview_route_from_transcript(...) using shared signals.
- Integrated runtime route preview to use shared signal extraction.
- Added unit tests: intent signals, timeline windows/transitions, transcript-based route preview.

Verification run in this bundle:
- tests/unit/test_intent_signals.py
- tests/unit/test_intent_router.py
- tests/unit/test_intent_timeline.py

Remaining high-priority MIR work:
- Plugin host + idempotency + timeout isolation
- Intent timeline persistence + plugin-run persistence
- Synthesis and lineage
- Timeline and plugin-run web APIs
