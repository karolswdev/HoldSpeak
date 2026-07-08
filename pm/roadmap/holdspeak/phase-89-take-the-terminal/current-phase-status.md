# Phase 89 — Take the Terminal (first-class agent manipulation)

**Status: CLOSED 4/4 — 2026-07-08 (scaffolded and shipped the same day).**
All three limits down, each proven live; the robustness walk passed 6/6.

**Last updated:** 2026-07-08 (phase CLOSED 4/4).

## Goal

Make steering a FIRST-CLASS terminal capability, not a scoped reply
channel. Phase 87 shipped a consent-gated way to type text into a
REGISTERED agent's pane; this phase turns that into real manipulation:
send any key (interrupt a runaway with `C-c`, drive a TUI with arrows
and `Escape`, not just literal text); attach to and steer ANY tmux
pane on the machine, not only the hook-registered ones; and reach a
session on ANOTHER mesh node over the proven relay. Every new verb
rides the EXISTING Phase-87 consent/audit chokepoint — the safety
(watch free, steer armed, pane `%N` re-verified per keystroke, refuse
AND revoke, everything audited, a human behind every keystroke) does
not regress; it extends. Owner: *"we basically need first-class agent
manipulation IN this framework."*

## Scope

- In: full key control (`send_keys` — named + control keys through the
  ONE chokepoint + audit); attach to ANY pane (tmux session/pane
  discovery + peek/arm/steer/keys against a raw pane target, not the
  registry); cross-machine steering (drive a pane on another mesh node
  over the relay, honest liveness, the far node executes locally); the
  robustness walk + docs + close.
- Out: autonomous manipulation (a human is behind every keystroke or
  it does not send — unchanged); spawning/killing sessions (B3, the
  factory); a full PTY attach / live keystroke stream (peek stays a
  content-hash-gated poll — the reach is control, not a terminal
  emulator); any NEW egress of secrets (the far node resolves its own
  tmux; keys and hashes ride the wire, nothing else).

## Exit criteria (evidence required)

- [x] `C-c` interrupts a real runaway process in an armed pane; control
      keys drive the real line editor — every key through the chokepoint,
      every one audited (HS-89-01, live).
- [x] Any tmux pane on the machine (including one started BY HAND,
      never registered) is discoverable, watchable free, and steerable
      under a grant pinned to its `%N` — the registry is no longer the
      gate (HS-89-02, live).
- [x] A pane on ANOTHER node is steered over the relay; the node goes
      quiet and the steer refuses by name; only the command + the node's
      bearer token cross the wire (HS-89-03, two-process live).
- [x] The walk: interrupt a runaway, edit a line, attach a hand-started
      pane, the recycled-pane crown case for keys, steer a remote node —
      the crown cases live; the audit answers who/what/where for every
      key; suite + guards green; docs shipped (HS-89-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-89-01 | Full key control — the send-keys verb | **done** (2026-07-08, live) | [story-01-key-control](./story-01-key-control.md) | [evidence-01](./evidence-story-01.md) |
| HS-89-02 | Attach to any pane — beyond the registry | **done** (2026-07-08, live) | [story-02-any-pane](./story-02-any-pane.md) | [evidence-02](./evidence-story-02.md) |
| HS-89-03 | Cross-machine steering — over the relay | **done** (2026-07-08, two-process live) | [story-03-cross-machine-steer](./story-03-cross-machine-steer.md) | [evidence-03](./evidence-story-03.md) |
| HS-89-04 | The robustness walk, the docs, the close | **done** (2026-07-08, walk 6/6 live) | [story-04-walk-docs](./story-04-walk-docs.md) | [evidence-04](./evidence-story-04.md) |

## Where we are

Scaffolded 2026-07-08 from the owner's direct ask — "first-class agent
manipulation IN this framework" — after an honest audit of Phase 87
found the steering channel real and safe but scoped: text-only,
registry-gated, local-only. This phase removes those three limits on
the same consent spine.

**HS-89-01 done (2026-07-08, live) — text-only is gone.** The chokepoint
now sends real keys: `tmux_transport.send_keys_to_pane` (named keys as
bare `send-keys` args, a literal run via `-l`) and
`coder_steering.deliver_keys` (the SAME grant → verify `%N` → send →
audit shape as `deliver`, an allow-list refusing any junk key BY NAME).
`POST /api/coders/{key}/keys` is a typed 409 when unarmed / `unknown_key`
/ revoking. Proven on real metal through the real chokepoint: `C-c`
interrupted a runaway (counter frozen, shell responsive), `BSpace`
edited a real line (`echo AB`+BSpace+`C` → `AC`), `C-c` cancelled a
typed junk line — the audit read back every sequence with a readable
head. The census pins `send_keys_to_pane` to the one chokepoint; suite
3480/0.

**HS-89-02 done (2026-07-08, live) — the registry is no longer the gate.**
`coder_steering.list_panes` names every tmux pane on the machine
(`GET /api/coders/steering/panes`); a `pane:%N` key resolves the pane
DIRECTLY (a synthetic session over the raw pane), so the whole spine —
peek free, arm pins `%N`, steer/keys re-verify — works on ANY pane, not
just hook-registered ones. The registry path is untouched (regression
pinned). Proven live: a HAND-started pane (confirmed not an agent
session) was discovered, peeked free, armed, steered, and `C-c`'d — the
text landed. Suite 3488/0.

**HS-89-03 done (2026-07-08, two-process live) — local-only is gone; all
three limits are down.** `coder_steering_relay.relay` forwards a peek/
arm/steer/keys to a configured node's OWN steering routes (percent-
encoded key + bearer token); the node executes against its own tmux. The
security model refined from the scaffold: **the machine that types owns
the consent AND the audit** — the far node checks its own grant and
writes its own row; the hub is a relay, and stamps `node` so the caller
knows where it landed. Honest liveness: an unreachable node refuses
`node_offline` BY NAME, an unconfigured one `unknown_node`. Proven
TWO-PROCESS: the hub (never touching tmux) relayed arm+`C-c`+steer to a
SEPARATE node process — the runaway stopped, `REMOTE_STEER_OK` landed in
the node's pane, the grant lived in the node process; killing the node
refused by name in 0.00s. Suite 3499/0.

**HS-89-04 done (2026-07-08) — PHASE CLOSED 4/4.** One consolidated walk
passed 6/6 live against real tmux, a real runaway, and a two-process
remote: interrupt, edit a line with a control key, attach a hand-started
pane, the recycled-pane crown case refusing AND revoking for keys, a
cross-machine steer landing + a killed node refusing by name, and the
audit read back with every key's row. Docs shipped in canon voice
(USER_GUIDE "Take Over A Session", SECURITY.md the widened manipulation
model, ARCHITECTURE.md the chokepoint-grown paragraph);
[final-summary.md](./final-summary.md) records the B3 (factory) handoff.
Both chokepoints (`send_text_to_pane`, `send_keys_to_pane`) pinned by the
census. The owner's ask — "first-class agent manipulation IN this
framework" — is answered: any key, any pane, any configured machine, on
the one consent spine.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Full key control + any pane = disrupt any process on the machine | the power this phase grants | the SAME consent spine gates it: watch free, arm per pane (pinned `%N`), keys re-verify the pane, refuse+revoke on mismatch, every key audited, a human behind each | any key delivered whose pane `%N` was not re-verified, or that skipped the chokepoint |
| A control key (`C-c`) hits the wrong pane | the reason `%N` is pinned | keys go to the VERIFIED `%N`, never the target string; the recycled-pane crown case covers keys too | a `C-c` audited against a pane that was not the armed one |
| Cross-machine keystrokes over a lossy relay garble a TUI | medium | keys ride as a discrete list (not a byte stream); the far node executes atomically and returns the result; honest liveness refuses a quiet node | a remote key sequence delivered out of order |
| The peek poll or discovery melts the machine | low | discovery is on-demand (a list call, not a poll); peek stays the Phase-87 hash-gated poll | machine load spikes on an idle attach |

## Decisions made (this phase)

- 2026-07-08 — Every new verb (keys, any-pane, remote) rides the
  EXISTING `coder_steering` chokepoint + audit; the safety spine is
  reused verbatim, never forked — the whole point is that manipulation
  gets MORE reach without LESS consent.
- 2026-07-08 — Keys are a discrete named-key list (`C-c`, `Enter`,
  `Up`, `Escape`, or a literal run), sent via `tmux send-keys`
  (named, not `-l`) — the transport gains a `send_keys_to_pane`
  beside the literal `send_text_to_pane`; one craft, two shapes.
- 2026-07-08 — Any-pane attach keys the grant store by the pane `%N`
  itself (a `pane:%N` pseudo-key), so a hand-started pane needs no
  registry entry; peek by pane is free, steer/keys need the grant.
- 2026-07-08 (HS-89-03) — Cross-machine: **the machine that types owns
  the consent AND the audit.** The far node checks its own grant and
  writes its own audit row; the hub is a relay (a push to the node's own
  steering routes), never the authority over another machine's terminal.
  This SUPERSEDES the scaffold's "grant + audit stay on the hub" — the
  node-owns-consent model is safer and shipped. Nodes are explicit
  config (`HOLDSPEAK_STEER_NODES`), never discovery.

## Decisions deferred

- Spawning / killing / renaming sessions from the framework — B3 (the
  factory) — default: manipulate existing panes only.
- A full PTY live stream (vs the hash-gated poll) — trigger: a TUI the
  poll cannot render fast enough — default: the poll, tightened.
- A persistent grant ledger across restarts — default: no; fail closed
  stays the feature (Phase 87 decision, unchanged).
