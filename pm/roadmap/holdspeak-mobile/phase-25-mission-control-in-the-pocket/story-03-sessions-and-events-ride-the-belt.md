# HSM-25-03 — Sessions and events ride the belt

- **Status:** backlog
- **Depends on:** HSM-25-01, HSM-25-02.

## Problem

The belt without the live layer is a poster. The correlation document says which agent is on which story and whether it is waiting on a human; the event log narrates the rails with gate refusals carrying rule ids. Rendering both turns the conveyor into mission control.

## The design

The model polls sessions and events on the 4-second cancellable-`Task` cadence the coder-session poll already uses (unreachable keeps last truth; re-assign only on change). `on_story` sessions pin to their story chip, awaiting-response the loudest signal, stale dimmed never dropped; other correlation buckets render honestly. An event ticker shows the last N, gate refusals first-class with rule ids verbatim.

## Test plan

View-model tests: session pinning per correlation outcome, awaiting-response emphasis, the event ticker with a refusal, poll single-flight. `swift test`.
