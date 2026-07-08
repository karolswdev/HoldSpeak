# Phase 89 — Take the Terminal — final summary

**Closed 2026-07-08, 4/4, scaffolded and shipped the same day.**

## What it is

First-class agent manipulation, from the owner's direct ask: *"we basically
need first-class agent manipulation IN this framework."* An honest audit of
Phase 87 found the steering channel real and consent-safe but scoped three
ways — **text-only, registry-gated, local-only.** This phase removed all
three on the EXACT same consent/audit chokepoint. The safety spine did not
regress; it extended: watch free, manipulate armed, pane `%N` re-verified
before every key, a recycled pane refuses AND revokes, every key audited, a
human behind every keystroke.

## The three limits, gone (each proven live)

- **HS-89-01 — text-only → any key.** `tmux_transport.send_keys_to_pane`
  (named keys as bare `send-keys` args, a literal run via `-l`) +
  `coder_steering.deliver_keys` (the same grant → verify `%N` → send → audit
  as `deliver`). An allow-list (`_SPECIAL_KEYS` + a modifier-combo regex)
  refuses any junk key BY NAME — an arbitrary string never reaches `tmux` as
  a key. `POST /api/coders/{key}/keys`. Live: `C-c` froze a real runaway,
  `BSpace` edited a line, `C-c` cancelled a typed line; the audit read back
  every sequence readably.
- **HS-89-02 — registry-gated → any pane.** `coder_steering.list_panes`
  names every tmux pane (`GET /api/coders/steering/panes`); a `pane:%N` key
  resolves the pane directly (a synthetic session over the raw pane), so the
  whole spine works on ANY pane. The registry path is regression-pinned.
  Live: a HAND-started pane, confirmed not an agent session, was discovered,
  watched free, armed, steered, and `C-c`'d.
- **HS-89-03 — local-only → any configured machine.**
  `coder_steering_relay.relay` forwards a peek/arm/steer/keys to a node's own
  steering routes (`HOLDSPEAK_STEER_NODES`, explicit config never discovery);
  the node executes against its own tmux. **The machine that types owns the
  consent AND the audit** — the far node checks its own grant and writes its
  own row; the hub relays and stamps `node`. Honest liveness: an unreachable
  node refuses `node_offline` by name, an unconfigured one `unknown_node`.
  Proven TWO-PROCESS: the hub (never touching tmux) relayed arm+`C-c`+steer to
  a separate node process — the runaway stopped, `REMOTE_STEER_OK` landed, the
  grant lived in the node process; killing the node refused by name in 0.00s.

## HS-89-04 — the walk, the docs, the close

A single walk exercised every beat live against real tmux, a real runaway, and
a two-process remote: interrupt, edit a line with a control key, attach a
hand-started pane, the recycled-pane crown case refusing AND revoking for keys,
a cross-machine steer landing + a killed node refusing by name, and the audit
read back with every key's row. Docs shipped in canon voice — USER_GUIDE "Take
Over A Session", SECURITY.md the widened manipulation model (any key/pane/
machine, same consent), ARCHITECTURE.md the chokepoint-grown paragraph. Full
suite green (3499+); both chokepoints (`send_text_to_pane`,
`send_keys_to_pane`) pinned by the census.

## What the next phase inherits

- **B3 (the factory) — spawn / kill / rename sessions.** Explicitly deferred
  here. It rides this same spine: creating or ending a session is another
  consequential act to gate with a grant + audit, and the relay already
  reaches another machine to do it there. The factory manages the LIFECYCLE
  of the panes this phase learned to manipulate.
- **The on-glass surface for manipulation.** The web/iPad steer composer
  gained the wire (keys, pane picker, node selector) but not yet a first-class
  UI — a key palette, a pane list, a node chip. The client contracts from the
  B4 track (Phase 26) already model the peek/arm/steer shapes; the key + node
  additions extend them.

## Decisions of record

- Every new verb rides the existing `coder_steering` chokepoint + audit; the
  spine is reused, never forked — more reach, never less consent.
- Named keys are held to an allow-list; a literal run uses `-l`. One transport
  craft, two shapes (`send_text_to_pane`, `send_keys_to_pane`).
- Any-pane attach keys the grant by the pane `%N` itself (`pane:%N`).
- Cross-machine: **the machine that types owns the consent and the audit**
  (supersedes the scaffold's "grant stays on the hub"); nodes are explicit
  config, never discovery; the far node executes, the hub relays.

## Deferred riders

- A full PTY live stream (vs the hash-gated poll) — the reach is control, not
  a terminal emulator; revisit only if a TUI outpaces the poll.
- A persistent grant ledger across restarts — no; fail-closed stays the
  feature (Phase 87 decision, unchanged).
- A fleet of steering nodes — one remote is proven; the multi-node console is
  a surface concern, not a wire one.
