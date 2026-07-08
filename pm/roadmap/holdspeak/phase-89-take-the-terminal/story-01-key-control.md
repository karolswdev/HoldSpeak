# HS-89-01 — Full key control: the send-keys verb

- **Project:** holdspeak
- **Phase:** 89
- **Status:** backlog
- **Depends on:** none (extends Phase 87)
- **Unblocks:** HS-89-02, HS-89-03

## Problem

Phase 87 can type literal text into an armed pane, but it cannot send
a CONTROL key — so it cannot interrupt a runaway agent (`C-c`),
dismiss a prompt (`Escape`), or drive a TUI (arrows, `Tab`, `Enter`).
That is the single biggest gap between "reply to an agent" and "take
over the terminal." This story adds real key control through the
EXACT Phase-87 consent/audit chokepoint.

## Scope

- In: `tmux_transport.send_keys_to_pane(pane, keys)` — `keys` a list
  of tmux key names (`C-c`, `Enter`, `Escape`, `Up`/`Down`/`Left`/
  `Right`, `Tab`, `BSpace`) or a literal run; `coder_steering.
  deliver_keys(key, keys, *, current_target, ...)` — grant check →
  verify `%N` → send keys → audit (the SAME shape as `deliver`);
  `POST /api/coders/{key}/keys` on the steering router; the audit's
  text_head is the rendered key sequence; the chokepoint census
  extended to pin `send_keys_to_pane`'s call sites.
- Out: attach-to-any-pane (02 — this story still steers registry
  panes); cross-machine (03); a live keystroke stream (peek unchanged).

## Acceptance criteria

- [ ] `deliver_keys` refuses unarmed, refuses+revokes a recycled pane,
      and on success sends the key list to the VERIFIED `%N` — each
      pinned by a test (mirroring `deliver`).
- [ ] A key sequence renders faithfully to `tmux send-keys` (named
      keys as named args, a literal run via `-l`); a test asserts the
      exact argv for `C-c`, for `Down Down Enter`, and for a literal.
- [ ] Every keys delivery, delivered or refused, writes an audit row
      whose head is the readable sequence (`C-c`, `Down Down Enter`).
- [ ] `POST /keys` is a typed 409 when unarmed (the desk shows ARM);
      delivered when armed; a revoking refusal frames the disarm.
- [ ] Live: `C-c` interrupts a REAL runaway process in an armed pane;
      arrows + `Escape` drive a REAL TUI — captured in evidence.
- [ ] Full suite green (read from the file); the chokepoint census
      covers `send_keys_to_pane`; api-surface regen.

## Test plan

- Unit: `send_keys_to_pane` argv rendering (named vs literal); the
  `deliver_keys` chokepoint (refusals, audit, verified `%N`); the
  route.
- Integration: a live `C-c` against a real `yes`/`sleep` runaway; a
  live arrow-drive of a real TUI (e.g. a `less`/`vi` pane).
- Manual / device: interrupt a real agent mid-run.

## Implementation direction

- **The transport:** `send_keys_to_pane(pane, keys)` where each key is
  either `("named", "C-c")` or `("literal", "text")`. Named keys →
  `tmux send-keys -t <pane> C-c`; a literal run → `-l <text>`. Send as
  ordered `send-keys` calls (one per key/run) so named and literal
  never mix in a single call. Reuse `_run_tmux` (timeout, error).
- **The chokepoint:** `deliver_keys` is `deliver` with the send swapped
  — same `require_grant(key, current_target)`, same verified-`%N`
  target, same audit call. Refactor the shared prologue if it stays
  honest; do not duplicate the grant logic.
- **Key vocabulary:** accept a small allow-list of named keys plus
  literal; an unknown named key refuses by name (never pass an
  arbitrary string to `send-keys` as a key — injection discipline).
- **The audit head:** render the sequence readably (`C-c`,
  `Down Down Enter`) so the trail reads like what a human did.
