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
- `label` names the fact. A `key: []` row with a literal `value` states a fixed
  destination or scope, such as the owner's phone or eligible projects.
- `kind: text` permits a scalar value to be read.
- Kinds `secret`, `token`, `credential` and `file bytes` hide the value. The
  fact says `hidden (kind)`. An unknown nonempty kind uses `secret`.

A text row can declare a `read` with `tool`, `arguments` and `value`.
`arguments` maps read inputs to call argument paths. An `=` prefix gives a
literal from code. A `{reference, part}` input uses the filing service's
qualified-reference parser to select `kind` or `id`. `desk_kind` uses the Desk
tool's existing kind vocabulary. The lookup then makes the ordinary scoped
public read. Invalid or unsupported references stay hidden. `value` selects a
dot-separated result path. A `|` separates
alternative paths. An optional `through {tool, arguments}` follows a public
read using fields from its filtered result. Each step takes the same reader
policy path; a withheld first answer cannot feed an owner result into a caller
lookup. The final `value` selects a field from the last answer. For a list read, `rows` selects the list and `match` maps
its identity fields to call arguments. `rows` can name more than one list.

The one projector resolves names through the MCP caller path, including its
palette, project-source checks and response filter. The owner uses owner
authority. The caller uses the current caller credential. A forbidden or
unnamed result says `hidden (secret)`. Hidden fields never trigger a read.
Each reader has a separate read cache within that response.

The owner and caller can receive different `facts` for the same call. For
example, the owner can see `Meeting: Project B plan` while a project-A caller
sees `Meeting: hidden (secret)`. Both receive the same `binding`. Its revision
covers the owner's facts, not the caller's filtered copy. There is one
projection function and one revision for the question.

`format: word_count` shows a body's length, for example `Text: 240 words`.
Bodies are never copied into facts. Every fact value is limited to 160
characters. A hidden parent suppresses every child, regardless of declaration
order. Titles remain facts when their parent is not hidden. Undeclared nested fields
produce one `Other fields: hidden (secret)` notice. They do not disappear
behind a declared sibling.

`x-held-target` names the owning operation and its public resolver method.
Description and execution must use that same resolver. A selector is resolved
before facts or a Calls preview are made. Calls freezes a no-op check too.
The held handle keeps the canonical arguments. An
approval freezes that payload for both executor paths. A later name match or
changed call arguments cannot replace the approved target. Explicit ids need
no name selector. A desk save with a typed id names the existing object before
showing its new title or name. Without an id it creates a new object. A missing Program match is frozen as a no-op refusal, even
when a new matching Program appears before the call finishes.

Program starts use the startable resolver and keep its exact id. A missing id
never falls back to a name. The original name can remain as intent so an
already-running named start retains its existing no-op reply. Program shaping
uses its ordinary shared name resolver and also keeps its id. Stop resolves
the active capture and checks any supplied id against it. The runtime checks
that id again under the stop lock. A bound Stop requires a callback that accepts
`meeting_id`. The public meeting read can name a live capture before it is archived.
Start does not claim a title that the controller ignores. Prepared and inline
sends are distinct forms. A mixed form is refused before facts or execution.

This top-level annotation stays in the tool declaration. The existing model
schema renderer omits it, so presentation metadata adds no prompt bytes.

A structured value, an unmarked argument or an unknown argument says
`not described`. Without a tool title, the plain name is `Tool call`.
Declarations now cover sends, Door tasks, task changes, project item creation,
desk object creation/change/delete, note task outcomes, meeting capture/archive
verbs, and the Program verbs held on Calls. The next round covers every
remaining write in Ask's default palette, phone, nudge, People, decision and
project families. The owner-only project Archive tool has facts too; its
authority and admission do not change. The tree-derived census has 168 tools
left in the explicit remaining set after this round. A prepared send reads its frozen
document title, destination name and channel through `channel.sends`. An inline
send uses `channel.preview` and `channel.destinations`. The facts are Document,
To and Through. References that cannot be named remain hidden.

`holdspeak/held_arguments.py` holds the schema vocabulary and the explicit
`NOT_YET_DESCRIBED` set. The declaration census derives held write/build tools
from the registered tools, strongest effects and gate reachability, including
Calls exceptions. Strongest effects include argument-qualified operation
exposures. `monday_brief.get(generate)` and `concierge.detect(fresh)` declare a
possible write. `connection.recheck` is a declared write despite its historical
read gate class. `project.update.job_apply(force)` is already a write.
`concierge.probe(generate/task)` is already an owner-press egress tool, so it
cannot be held by these callers. The existing admission truth table and
answer rights do not change. A possible write cannot be a name lookup.
It rejects a new omission and an obsolete remaining-work entry. The remaining
set describes unfinished coverage, not a new gate or permission rule. The Door
write has no project argument.

Both Deny and Allow require the binding from the last read. Its digest covers
the thread, turn, caller, tool, owner facts, full saved arguments and
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

## Names without bodies

Project updates, engine jobs, steward runs and saved briefs name their project
by following their public read to `project.get`. A caller receives a name only
when each public read permits it. A meeting decision names its source meeting;
its decision text and rationale are never facts. People notes, requests,
commitments and agenda text show a word count when supplied in the call.

Some references have no safe public name read from the arguments a tool takes:
People agenda and commitment ids, setup proposal ids, window ids, nudge steps,
phone held-item refs, and source refs with no supported public name read. Those facts state their hidden
kind. No raw id, body, path, payload or credential is substituted for a name.
A setup stage is a fact from the public session read, never the interview text.

`project.brief.stop` acts on `attempt_id`. Its route's `project_id` is not used
by the existing stop service, so its declaration does not name that project
as the target. Preparation and route refs stay hidden. None of these
declarations changes which calls wait, their effects or who can answer.

Project source writes have one resolver for their legacy decision refs.
`decision:<id>` can denote either a meeting decision or, when only that store
holds it, a Desk decision. A held call keeps `expected_resource_ref` from
`ProjectService.resolve_resource_target`. Add and Remove use the same resolver
and refuse `source_target_changed` if that legacy token changes stores before
the write. A meeting decision ref never reads a Desk decision's title. This
precondition grants no right and changes no call's admission or answer rights.
