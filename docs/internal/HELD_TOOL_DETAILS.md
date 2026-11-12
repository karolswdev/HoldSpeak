# Held tool call details

`thread.held` declares `GET /api/threads/{thread_id}/held/{call_id}` and the
MCP read. Ask's hold frames use the same service projection. The read returns
`call_id`, the tool key (`tool`), its plain name (`words`), ordered `facts`
with `label` and `value`, and `binding {id, revision}`. It sends no argument
object. The owner and the agent principal that made the call can read it.
Other agents, nodes and token-page principals cannot. Thread reads and all
thread writes keep their existing owner rule.

The tool's own `inputSchema` declares its display:

- `title` names the tool.
- `x-held-arguments` is an ordered list of `{key, label, kind}` rows.
- `key` selects the argument and `label` names the fact.
- `kind: text` permits a scalar value to be read.
- Kinds `secret`, `token`, `credential` and `file bytes` hide the value. The
  fact says `hidden (kind)`. An unknown nonempty kind uses `secret`.

This top-level annotation stays in the tool declaration. The existing model
schema renderer omits it, so presentation metadata adds no prompt bytes.

A structured value, an unmarked argument or an unknown argument says
`not described`. Without a tool title, the plain name is `Tool call`.
Only `door.add_item` currently declares readable arguments: Task, Owner, Due,
Source kind and Source. Other tools do not gain an implicit formatter. A tool
that accepts a project can declare that argument in its own schema; the Door
write currently has no project argument.

Both Deny and Allow require the binding from the last read. Its digest covers
the thread, turn, caller, tool, displayed facts, full saved arguments and
elicitation content. Hidden-value changes also invalidate it. The existing
Room binding checker refuses missing or stale bindings with `answer_stale`
and `Read again`, before a policy or decision changes. The check and decision
share the handle lock. Ask keys the question and late replies by this revision,
and marks each fact value for feedback redaction.

Calls uses this same guarded answer port. `calls.decide` requires the held
question's binding over HTTP and MCP. The voice runner keeps the binding from
before it listens. A stale yes approves nothing, says that the call changed,
and reads the new details before asking again. The question's facts come from
this same projection; no raw-argument speech fallback is used.

Calls reads retain the caller scope for the call's lifetime, including its
spoken transcript after the held tool is answered. This does not change which
calls wait or who can answer them. Agents and Program step approvals still
use the separate coder gate and its saved bindings.
