# HS-106-02 - Principal separation on loopback

- **Project:** holdspeak
- **Phase:** 106
- **Status:** ready
- **Depends on:** none
- **Unblocks:** HS-106-04
- **Owner:** unassigned

## The thesis (the bar)

The kernel's central promise is that *the caller never asserts its
own authority*. That promise is void today, because the runtime
derives authority from a network fact: `holdspeak/web_auth.py:9`
enforces the token **only off-loopback**, and `is_loopback_host`
(`web_auth.py:53`) is the whole gate. Every agent HoldSpeak spawns
runs on the same machine. Loopback therefore means "the owner" and
"an agent the owner is supervising" and "a tool that agent decided
to call" — three principals wearing one face.

This is the textbook confused deputy, and Codex found it with
file-level evidence. Building a kernel on top of it would give the
kernel a principal field it cannot honestly populate. The bar: after
this story, the hub can name WHO is asking on every request, and
"it came from 127.0.0.1" is never an answer.

## Problem

Loopback is treated as owner trust. An agent process on the same
host reaches every API with the owner's rights, including the
Phase-104 gate's decision surface — which means the gate's guarantee
that *agents can never `decide`* rests on the agent not thinking to
call the route.

## Recipe

1. **Three principals, named.** `owner`, `agent`, `node` — the RFC
   §5 set, declared as a real type in the runtime, not a string
   convention. Each carries an identity (which owner session, which
   agent session, which node) and is derived at the edge, never
   passed in by the caller.
2. **Agents authenticate even on loopback.** An agent session gets
   its own credential when it is spawned — issued by the hub, scoped
   to that session, distinct from the owner's web token, revoked
   when the session ends. The existing spawn paths
   (`coder_steering`/`coder_factory` and the Phase-104 gate hook rig)
   are where it is minted, so nothing hand-configures it.
3. **Loopback stops being an authority signal.** `is_loopback_host`
   keeps its job for *bind* safety (`nonloopback_bind_blocked`) and
   loses it for *request* authority. An unauthenticated loopback
   request is an unauthenticated request.
4. **The owner's path stays effortless.** The owner's browser
   session is authenticated by construction on first load — no login
   ceremony appears on the desk, no token pasting, nothing the owner
   has to know. If the owner notices this story at all, it failed.
5. **Refusals are typed and named.** A request with no principal, or
   a principal without the right for that route, is refused by name
   in the Phase-104 gate's idiom — never a silent 200, never a bare
   403 with no reason.
6. **`decide` is closed to agents at the type level.** The rule
   "only the owner decides" (Article XI.4) is enforced where the
   principal is derived, so it cannot be forgotten per-route later.

## Out of scope

- Effect-capability confinement (RFC §5b) — the privileged executor
  process. This story closes the deputy on the API surface; it does
  not sandbox effect capabilities.
- Multi-user or multi-owner identity. One owner, still.
- Any broker code. This is a prerequisite, landing as pure
  hardening.

## Acceptance

- A real spawned agent session, on loopback, is refused on a
  decision route by name — proven on real metal with two processes,
  not a unit fixture.
- The same agent session succeeds on the routes its principal is
  entitled to, so the separation is a boundary and not a wall.
- The owner's browser reaches the desk with no visible auth step;
  a screenshot walk shows an unchanged first-load experience.
- `is_loopback_host` has zero remaining callers that treat its
  result as authority; a census test pins that.
- Killing and respawning an agent session invalidates the old
  credential.
- Every refusal path names the principal and the missing right.

## Test plan

- **Unit:** principal derivation for each edge (browser session,
  agent credential, node credential, nothing); the agent-cannot-
  decide rule.
- **Census:** no authority decision reads a loopback fact.
- **Integration:** credential lifecycle across spawn, use, kill,
  respawn.
- **Live (evidence):** a real `claude -p` session against a real
  spawned hub attempting a decision route and being refused by name;
  the owner's first-load walk at 1440 and 393.

## Chef's notes

- The failure mode to guard against is a "local dev bypass" env var.
  If one exists, it is a hole with a friendly name. Do not add one.
- The Phase-104 gate hook rig (`claude -p --settings <file>` with
  PreToolUse and Stop legs) is the right live harness — it already
  spawns a real agent that talks to a real hub.
- Watch the WebSocket path: `websocket_auth_protocol` and
  `extract_websocket_token` are a second door and must derive the
  same principal as the HTTP door.
