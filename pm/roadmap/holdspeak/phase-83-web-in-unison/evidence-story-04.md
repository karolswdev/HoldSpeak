# Evidence — HS-83-04: docs + the live walk

**Date:** 2026-07-07. **Verdict: done — and the phase closes with it.**

## What shipped

- **Entry-point docs:** the root `README.md` Desk section gains the three
  features in product tense (Ground this ask / Talk to your personas / Open a
  model); `docs/WEB_DESK.md`'s "Ask from the rail" becomes "Converse from the
  rail" (threads, Save to desk, the models list) plus a new "Ground this ask"
  section. Voice + drift guards: 18/18.
- **The token rides every request** (found live, fixed here): a hub bound
  off-loopback gates every `/api` call, and the web frontend never captured
  or attached the token — the ENTIRE desk 401'd on a guarded hub (dev rigs
  bind loopback, so nothing ever noticed). `AppLayout.astro` now captures
  `?token=…` once (the Jupyter-style door `web_auth.py` documents), keeps it
  for the session, scrubs it from the address bar, and attaches
  `X-HoldSpeak-Token` to every same-origin fetch.
- **The live walk** (`scripts/walk_hs83_live.py`): NO scratch DB, NO faked
  engine — the real hub on 127.0.0.1:8765, its engine the LAN llama.cpp,
  authenticated the way an owner arrives.

## The walk's receipts (all asserted, not eyeballed)

1. **Authenticated arrival:** the desk loads with `?token` once, the address
   bar scrubs, every subsequent call carries the header (the fix's own
   proof). The rail lists the hub's REAL runnable set:
   `Qwen3.5-9B-UD-Q6_K_XL.gguf` (hub) + `anthropic/claude-sonnet-4` (profile).
2. **Ground this ask, control vs treatment, in the browser:** the same
   codename question ungrounded answered `Mesh` (a guess); grounded on the
   imported envelope-proof meeting (transcript toggled) it answered
   `BLUE LANTERN` — the real model reading the real record.
   (`hs-83-04-walk-grounded-compose.png`, `…-grounded-answer.png`.)
3. **A persona conversation:** a walk-created recipe, grounded mid-thread,
   answered `BLUE LANTERN` from the real model; per-turn badge on the reply.
   (`…-walk-persona-thread.png`.)
4. **The model door:** one click on the hub's own model opened a chat titled
   `Qwen3.5-9B-UD-Q6_K_XL.gguf · hub model`; the pinned turn's badge read
   `☁ Qwen3.5-9B-UD-Q6_K_XL.gguf · 192.168.1.43`. (`…-walk-model-chat.png`.)

Cleanup: the walk's note and recipe were deleted; the envelope-proof meeting
predates the walk and stays.

## Suites

Docs guards 18/18; full sweep green post-change (see the commit); vitest
untouched by this story's code (the token wrapper is layout-inline; the walk
is its test).
