# Evidence — Cadence Phase 4 (Telegram remote presence)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase4-telegram`.

## What shipped (hermetic; the live bot walk is the owner's button)

| Story | Files | Proof |
|-------|-------|-------|
| CAD-4-01 | `config.py` (`TelegramConfig`, top-level, off by default) | `test_off_by_default` + config round-trip |
| CAD-4-02 | `cadence_telegram.py` (`call_telegram` via urllib) | mocked in every test |
| CAD-4-03 | `cadence_telegram.py` (`TelegramSurface` auth + commands) | unpaired/pairing/brief tests |
| CAD-4-04 | inline-button callbacks (snooze/done + kill-confirm) | decision tests |
| CAD-4-05 | `runtime/cadence.py` (`_push_due_to_telegram`) + `push_due_nudges` | push tests |
| CAD-4-06 | `tests/unit/test_cadence_telegram.py` (12) | all green |

## The surface

`holdspeak/cadence_telegram.py` is a **sibling of the cadence core** (not under `holdspeak/cadence/`)
so the Phase-1 no-side-effects guard stays a strong, simple invariant — the surface does the egress,
the core never does.

- **Security held:**
  - the **bot token is a credential** — `call_telegram` joins it into the URL only at call time; it
    never appears in a rendered message (`test_token_never_appears_in_sent_text`), a log (redacted),
    or a persisted row.
  - **hard pairing** — an unpaired chat gets one "not paired" line and **no loop data**
    (`test_unpaired_chat_gets_no_data`); `/pair <code>` self-pairs on the configured code; an
    unpaired callback is rejected without acting (`test_unpaired_callback_rejected`).
  - **kill is behind a second confirm** (`test_kill_requires_second_confirm` /
    `test_kill_cancel_keeps_loop`); snooze/done are one-tap (reversible).
  - **off by default** — `TelegramConfig.is_active` is False unless `enabled` AND a token is set
    (`test_off_by_default`); push is a no-op without a paired chat (`test_push_is_noop_without_paired_chats`).
- **Push:** the `CadenceMixin` tick calls `push_due_nudges` when the surface is active — each due loop
  is sent to every paired chat with snooze/done/kill buttons, and a `telegram` nudge is recorded
  (`test_push_due_nudges_sends_and_records`).

## Proof

- `uv run pytest -q` over cadence + web-server + config/doctor/schema → **272 passed.**
- The cadence-core `test_cadence_package_has_no_external_side_effects` guard still passes (the
  Telegram surface is a sibling module).
- **Owner's live walk (the gate):** a real bot token + `pairing_code`, `/pair` from a real chat, a
  pushed nudge, an inline-button decision.
