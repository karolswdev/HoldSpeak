# Coder Gate

The Gate holds a matched Claude Code, Codex, or pi tool call until the owner
decides. An unarmed or unmatched call is inert to the Gate and follows the
agent's own policy.

## Turn the Gate on

The Gate has two user opt-ins. Both are required for ordinary repository
matches:

1. Print the hook block and add it to the agent configuration yourself:

   ```sh
   holdspeak gate install
   ```

   HoldSpeak never edits another application's settings.

2. Turn on the master switch:

   ```sh
   holdspeak gate arm
   ```

3. Choose the repository and tools to hold. Bash is the default:

   ```sh
   holdspeak gate allow --repo /path/to/repo
   holdspeak gate allow --repo /path/to/repo --tool Bash --tool Edit
   ```

Claude Code and Codex use their configured hook file. pi uses its HoldSpeak
extension. A Hand to agent launch can arm its new worktree for the launch
without changing the global master switch.

| Command | Effect |
| --- | --- |
| `holdspeak gate status` | Show the master switch and repository matches |
| `holdspeak gate revoke --repo PATH` | Stop holding that repository |
| `holdspeak gate disarm` | Make every hook arrival inert |

The file is `~/.holdspeak/gate.json` with `gate_schema: 1`. A missing or
malformed file means the Gate is off.

## What happens to a call

When no configured match covers the current agent, repository, and tool, the
hook returns without a proposal, audit row, or hub request.

When a match is armed:

1. The hook uses the agent's tool-use id, or creates an idempotency id.
2. It hashes the redacted arguments and sends a 120-character redacted head.
3. A longer redacted call is marked CUT. The hub keeps its full redacted form
   only while the hold is live and only for the owner's Raw view.
4. The hook waits for **Approve** or **Deny** from the Desk.

The proposal route is `POST /api/gate/proposals`. The Desk decides with
`POST /api/gate/proposals/{proposal_id}/decide`.

The default hold time is 240 seconds. `HOLDSPEAK_GATE_TTL` can change it. The
hook waits at most 300 seconds. Its hub URL is `HOLDSPEAK_HUB_URL`, defaulting
to `http://127.0.0.1:8765`.

## States

The final states are `approved`, `denied`, `expired`, and `invalidated`.
Only `held` is not final.

- The same proposal id and hash returns the existing row.
- A different hash for the same id invalidates the held row.
- The first decision wins through a state-guarded transition.
- Every transition writes a `gate_audit` row.
- Expiry is deny. There is no timeout auto-allow.
- A hub restart invalidates every held proposal.

The hook fails closed after an armed match. Authentication failure, hub
failure, HTTP refusal, decision refusal, and timeout all deny the tool call.

## Preview and credentials

The preview is redacted and truncated. A credential in the visible prefix can
still reach the hub, so treat the preview as sensitive tool content. Provider
keys held by the hub are a different boundary.

The hook obtains an agent credential for one session and stores it with local
file permissions. Session end revokes it. A Gate row is a record of the hold,
not authority by itself. Only the waiting hook can continue after approval.

## Routes

`holdspeak/web/routes/system/gate_routes.py` serves:

| Operation | Route |
| --- | --- |
| Create, read, list proposals | `POST /api/gate/proposals`, `GET /api/gate/proposals/{proposal_id}`, `GET /api/gate/proposals` |
| Decide and record receipt | `POST /api/gate/proposals/{proposal_id}/decide`, `POST /api/gate/proposals/{proposal_id}/receipt` |
| Read full held call | `GET /api/gate/proposals/{proposal_id}/command` (owner only) |
| Usage, audit, config | `POST /api/gate/usage`, `GET /api/sessions/{session_key}/receipt`, `GET /api/gate/audit`, `GET /api/gate/config` |
| Agent principal | `POST /api/principals/agents`, `DELETE /api/principals/agents/{identity}`, `DELETE /api/principals/self` |

## Changing the Gate

A matcher change is a policy change. Review its tool scope, redacted preview
limit, idempotency key, terminal states, restart behavior, and fail-closed
path. A passing unit test does not show that a repository is armed or that a
real call was approved.

See [Agent hook install](AGENT_HOOK_INSTALL.md) for hook setup and
[Coder integration](CODER_INTEGRATION.md) for launch-time Gate behavior.
