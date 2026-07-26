# HS-104-02 - The tool-call gate — a held hand, not a watched one

- **Project:** holdspeak
- **Phase:** 104
- **Status:** backlog
- **Depends on:** HS-104-01
- **Unblocks:** HS-104-03, HS-104-06
- **Owner:** unassigned

## The research finding (the bar)

AgentGlass's PreToolUse gate holds a risky tool call for human
Approve/Deny from the dashboard. Its design, however, is **fail-open
with a 60s auto-allow**, and its "survives restart" persistence keeps
the approval *card* alive without re-establishing that the *call*
hasn't already run — the council named this approval theater: a
decidable card over a possibly-done deed. HoldSpeak takes the idea
and inverts the failure posture, exactly as Article V demands:
consent that cannot be real refuses to pretend.

## Problem

The desk can steer a live agent (Phases 87–90) but cannot be asked
by one. When a steered Claude Code session is about to run a
destructive Bash command, the owner's only tools are watching the
pane and `C-c`. There is no propose → approve → execute path for the
agent's *own* actions, though the spine for exactly that shape has
existed since Phase 37.

## Recipe

Cook in this order; each step is provable alone.

1. **The proposal record (persistence before plumbing).** New table
   via the schema-bump ritual (`holdspeak/db`, snapshot regenerated
   per the standing recipe): `gate_proposals` — id (idempotency key,
   supplied by the hook), session identity, tool name, arguments
   sha256 + first 120 chars (the `steering_audit` redaction pattern,
   never the full payload), cwd, the operation-policy snapshot at
   proposal time, created/expires timestamps, state
   (`held | approved | denied | expired | invalidated`), decided-by,
   decided-at. **The record is a proposal, never authority**: nothing
   in the DB can cause execution; only a live hook waiting on a
   decision can proceed.
2. **The hook (the only authoritative interceptor).** A small
   forwarder script shipped under the repo (installed explicitly,
   AgentGlass-style: touching an agent's settings is a decision, so
   `holdspeak gate install` prints the hook block for the user to
   add — it never edits `~/.claude` itself). On PreToolUse it POSTs
   the proposal to the hub (loopback, hub token) and **blocks**,
   polling for the decision until `expires`.
3. **Fail-closed, default-off, doubly opted in.** The gate master
   switch is off; arming requires the switch AND a per-repo matcher
   (which tools to hold — start with Bash only). When the gate is
   armed and the hub is unreachable, the hook **denies** with a
   reason ("gate armed but hub unreachable") — never allows. When
   the gate is not armed, the hook is inert (approve immediately,
   zero added latency). There is no timeout-auto-allow anywhere;
   expiry is a deny, with the reason returned to the agent so it can
   say so in the transcript.
4. **Decision on the shade.** Held proposals surface as "what needs
   you" items through the existing Attention path
   (`AttentionDrawer.tsx` / `SystemShade.tsx`) — a card naming
   session, tool, the argument preview, and age, with Approve and
   Deny verbs and nothing else. No new drawer, no new modal (the
   no-modals rule), no prose (the interface serves; Article VII).
   Deny asks for an optional one-line reason that rides back to the
   agent verbatim.
5. **Restart honesty.** On hub restart, every `held` proposal is
   `invalidated` (the hook waiting on it gets a deny-with-reason; if
   the hook itself died with the agent, the record is already
   terminal). Nothing decided pre-restart is re-served; nothing held
   pre-restart is decidable post-restart without the agent proposing
   again. Revalidate-or-expire, never resume.
6. **Audit like steering.** Every proposal reaches a terminal state
   and every transition writes an audit row (the `steering_audit`
   shape: who/when/session/tool/hash, decision, reason). The
   chokepoint census pins the one decision path; a second code path
   that flips proposal state is a census failure.
7. **The ledger tells the truth first.** Flip
   `claude-code-hooks.tool_hooks` and `.blocking` to `authoritative`
   in the HS-104-01 ledger *in this story's commit*, and route both
   the hook receiver and the decision route through
   `require_capability`.

## Out of scope

- Any iPad/HSM leg (standing direction: web Desk OS to the atom
  first; the decision routes + contract schemas are authored
  spec-grade so a Swift recreation can be built from them later).
- Holding tools for agents on other adapters (tmux has no intercept;
  the ledger's `blocking: unavailable` cell forbids offering it).
- Any auto-decision policy ("always allow `ls`"). One matcher, human
  decisions only, this phase.

## Acceptance

- Armed gate, real Claude Code session, real metal: a matched Bash
  call holds; the card appears on the shade; Approve lands the call;
  Deny (with reason) reaches the agent's transcript verbatim.
- Unarmed gate adds zero interception (hook inert, proven by
  timing).
- Armed + hub down: the call is denied with the named reason.
- Expiry denies; restart invalidates; both visible in the audit
  read-back.
- Census green: one decision chokepoint, both call sites through
  `require_capability`.

## Test plan

- **Unit:** proposal state machine (every legal + illegal
  transition), redaction, expiry math, matcher.
- **Integration:** hook → hub → decision → hook round-trip against a
  scripted fake agent; restart invalidation; fail-closed denial.
- **Live (evidence):** the real-session walk above, screenshotted
  through the real desk UI at 1440 + 393.

## Chef's notes

- The hook blocks the *agent's* loop, not the hub's: the hub route
  returns the held proposal immediately and the hook polls. Never
  hold an open HTTP request across a human decision.
- The idempotency key comes from the hook, not the hub, so a hook
  retry after a network blip re-lands on the same proposal instead
  of minting a twin card. HS-104-03 attacks exactly this seam.
- The deny-reason ride-back is the soul of the feature: a denied
  agent that knows *why* course-corrects; a denied agent that sees a
  bare failure retries. Spend the extra hour on it.
