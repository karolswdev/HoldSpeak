# HSM-11-03 — Low battery + thermal stress

- **Project:** holdspeak-mobile
- **Phase:** 11
- **Status:** backlog
- **Depends on:** HSM-5-03, HSM-5-05
- **Owner:** unassigned

## Problem

Local Whisper + LLM inference is the hottest, most power-hungry thing the runtime
does. On a phone in a long meeting, thermal throttling and a draining battery are
inevitable. The charter requires the runtime to degrade gracefully — downgrade the
model, throttle, warn — not crash or corrupt.

## Scope

- **In:** explicit behavior under thermal pressure and low battery: model
  downgrade per the local-model strategy (e.g. drop to a smaller model, or defer
  12B+/heavy work, or fall back to Mode B if configured), throttling, and honest
  user-facing warnings; verified by inducing thermal/battery stress on real
  hardware.
- **Out:** the 4-hour endurance bar (HSM-11-01). Airplane mode (HSM-11-02). The
  per-device default selection itself (Phase 5 / HSM-5-03 — this exercises its
  downgrade paths under stress).

## Acceptance criteria

- [ ] Under sustained thermal pressure, the runtime degrades gracefully (smaller
      model / throttle / defer heavy work) and keeps working — it does not crash or
      corrupt data.
- [ ] Under low battery, heavy/experimental work (12B+, plugged-in-only) is
      refused or deferred per the local-model strategy.
- [ ] Degradation is surfaced to the user honestly (a warning/state), not silent.
- [ ] The behavior is proven by inducing real thermal/battery stress on hardware,
      with the device state recorded.

## Test plan

- Manual / device: induce thermal stress (sustained inference / warm environment)
  and low-battery state on a Tier-1/Tier-2 device; observe downgrade + survival +
  warning.
- Unit: the downgrade-decision logic (thermal/battery state → model/mode choice)
  tested across the matrix.

## Notes / open questions

- Graceful degradation is a charter requirement, not optional (phase stop signal:
  a crash instead of a downgrade). Build the downgrade path, don't just detect the
  state.
- This may surface encryption-at-rest and other deferred decisions as findings —
  file them for the owner rather than scope-creeping the gate.
