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
- `key` selects a dot-separated argument path. A list of keys selects the first present path.
- `label` names the fact.
- `kind: text` permits a scalar value to be read.
- Kinds `secret`, `token`, `credential` and `file bytes` hide the value. The
  fact says `hidden (kind)`. An unknown nonempty kind uses `secret`.

A text row can declare a `read` with `tool`, `arguments` and `value`.
`arguments` maps read inputs to call argument paths. An `=` prefix gives a
literal from code. `value` selects a dot-separated result path. A `|` separates
alternative paths. For a list read, `rows` selects the list and `match` maps
its identity fields to call arguments. `rows` can name more than one list.

The one projector calls only work-class evidence reads, with the calling
principal. It caches each read only within one details response. A failed,
forbidden or unnamed result says `hidden (secret)`. It never shows the id or
the read error. Hidden kinds never trigger a read.

This top-level annotation stays in the tool declaration. The existing model
schema renderer omits it, so presentation metadata adds no prompt bytes.

A structured value, an unmarked argument or an unknown argument says
`not described`. Without a tool title, the plain name is `Tool call`.
Declarations now cover sends, Door tasks, task changes, project item creation,
desk object creation/change/delete, note task outcomes, meeting capture/archive
verbs, and the Program verbs held on Calls. A prepared send reads its frozen
document title, destination name and channel through `channel.sends`. An inline
send uses `channel.preview` and `channel.destinations`. The facts are Document,
To and Through. References that cannot be named remain hidden.

`holdspeak/held_arguments.py` holds the schema vocabulary and the explicit
`NOT_YET_DESCRIBED` set. The declaration census derives held write/build tools
from the registered tools and the gate classification, including Calls exceptions.
It rejects a new omission and an obsolete remaining-work entry. The remaining
set describes unfinished coverage, not a new gate or permission rule. The Door
write has no project argument.

Both Deny and Allow require the binding from the last read. Its digest covers
the thread, turn, caller, tool, displayed facts, full saved arguments and
elicitation content. Hidden-value changes and changed names from a public read also invalidate it. The existing
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
