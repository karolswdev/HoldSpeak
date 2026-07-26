# Evidence - HS-104-05

- **Story:** HS-104-05 - Session receipts — honest numbers on the card
- **Status:** done
- **Date:** 2026-07-26

## The live walk — the three tiers on real glass

Staged hub (`uat.stage --recipe seeded-desk-steering`, port 8789, a
real armed tmux pane). Screenshots in assets/story-05/, read before
the flip.

1. **Reported tier, real Stop hook.** A real gated `claude -p`
   session (HS-104-02 rig, PreToolUse + Stop hooks): the held Bash
   call approved, the command ran, and on session end the Stop hook
   read the agent's OWN transcript and reported
   `claude:6191f8c8…` totals — model claude-opus-5, in 4, out 109,
   cache read 40,188, cache new 3,531, each figure separate. (The
   first session, run before the Stop hook entry existed in the
   settings, honestly showed NO reported tier — absent, not zero.)
2. **Estimated tier, price-row rule.** A `claude-opus-5` row in the
   staged home's `~/.holdspeak/pricing.json` → `estimated: ≈ $0.01
   (price table, 2026-07-26)`; the file removed → `estimated`
   ABSENT from the wire (never $0.00).
3. **The attempt card, all tiers composed**
   (receipt-attempt-desktop-1440.png, receipt-attempt-phone-393.png):
   a Work attempt attached to the gated session renders ONE line —
   `3s · 1 holds · tokens in 4 · out 109 · cache read 40,188 ·
   cache new 3,531 (reported) · ≈ $0.01 (price table, 2026-07-26) ·
   Bash holds 1, max 2.66s` — every number's tier readable from the
   glass alone.
4. **The steered pull-out, always tier only**
   (receipt-pullout-desktop-1440.png): pane %72 attached through the
   Panes picker, ARMED by hold-to-arm in the real UI, a real steer
   (`echo RECEIPT_STEER_OK`) landed in the real pane through the one
   chokepoint — the pull-out line reads `1 of 1 steers landed`, and
   NO token or cost line renders for a tmux pane (usage_tokens:
   unavailable — the ledger refusal working on glass).
5. **Below the floor.** The real session's `Bash holds 1, max 2.66s`
   is the sub-floor rendering; the 19-vs-20 boundary is unit-pinned.

## Proof

### Captured run — 2026-07-26T19:12:03Z

- **Command:** `uv run pytest -q tests/unit/test_session_receipts.py tests/unit/test_agent_capabilities.py tests/unit/test_coder_gate.py tests/unit/test_gate_chokepoint.py tests/unit/test_db.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 082b6769472f61de371696d865e534c501b193a0

```text
........................................................................ [ 51%]
...................................................................      [100%]
139 passed in 10.87s
```
