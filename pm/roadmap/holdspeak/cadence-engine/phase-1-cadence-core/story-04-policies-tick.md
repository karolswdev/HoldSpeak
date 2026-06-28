# CAD-1-04 — Policies + quiet hours + the `CadenceMixin` tick (off by default)

- **Program:** cadence-engine · **Phase:** 1 · **Status:** todo
- **Depends on:** CAD-1-01..03. **Unblocks:** 1-05 (CLI drives the same service), all surfaces.

## Problem

The substrate needs a scheduler that decides *which loops are due now* under quiet hours and a
per-source cadence — and an in-runtime tick that runs it, **off by default and byte-identical when
off**.

## The design

1. **Policies.** `holdspeak/cadence/policies.py` — `CadencePolicy` defaults (design §4.5/§7.2):
   per-source `initial_delay`, `repeat_after`, `escalation_after_count`, `max_nudges_per_day`,
   `quiet_hours`, `surfaces`. Seed defaults into `cadence_policies` on first run; user-editable
   later (Phase 2). `pressure` (gentle/normal/aggressive, chart §3.4) is a **timing multiplier**
   applied here — never changes *what* is nudged or any gate.
2. **Scheduler.** `holdspeak/cadence/scheduler.py` — `due_loops(loops, policies, *, now) ->
   list[DueDecision]`: respects `snoozed_until`, quiet hours (default-on; the only exception is an
   urgent agent-blocker, which Phase 1 has none of yet), `last_nudged_at + repeat_after`, and the
   daily cap. Pure given `now`.
3. **Config gate.** Add `CadenceConfig(enabled=False, pressure="normal", quiet_hours=…,
   max_nudges_per_day=…)` to `holdspeak/config.py` (dataclass, off-by-default, mirroring
   `meeting.allow_actuators=False`).
4. **The tick.** `holdspeak/cadence/service.py` → `CadenceService(db, …).tick(now)` = collect →
   score → persist → compute due decisions (Phase 1 *logs/returns* them; it does **not** render or
   deliver — surfaces come in Phase 2+). `holdspeak/runtime/cadence.py` → `CadenceMixin` owns
   `self.cadence_thread`, a daemon thread started in `WebRuntime.run()` **only when
   `config.cadence.enabled`**, looping `while not self.runtime_stop_event.wait(interval):
   self.cadence.tick(...)`, and joined in cleanup — mirroring `PluginQueueMixin`
   (`web_runtime.py:477–482,564`). Add `CadenceMixin` to the `WebRuntime` base list (`:138`).

## Scope

- **In:** default policies + seeding, the pure scheduler, the config gate, `CadenceService.tick`,
  the `CadenceMixin` daemon thread wired off-by-default.
- **Out:** nudge rendering/delivery (Phase 2+), escalation/EOD policies (Phase 6), Telegram (Phase 4).

## Proof / acceptance

- With `enabled=False` (default) the cadence thread **never starts**; `WebRuntime` start/stop is
  byte-identical to `main` (test asserts no thread + no DB writes from cadence).
- With `enabled=True`, `tick()` returns due decisions for active loops outside quiet hours, honors
  snooze + the daily cap, and never returns a `needs_review`/snoozed loop as a push.
- `pressure="aggressive"` shortens delays vs `gentle`; neither changes the loop set.

## Test plan

`tests/unit/test_cadence_scheduler.py` (quiet hours, snooze, repeat window, daily cap, pressure
multiplier — inject `now`); `tests/integration/test_cadence_runtime_gate.py` (enabled=False ⇒ no
thread/no writes; enabled=True ⇒ tick runs once). `uv run pytest -q tests/unit/test_cadence_scheduler.py tests/integration/test_cadence_runtime_gate.py`.
