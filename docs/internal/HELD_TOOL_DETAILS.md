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
  fact says `hidden (kind)`. An unknown or omitted kind uses `secret`.

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
its identity fields to call arguments. `rows` can name more than one list; `$` selects a root list. A match input
can use `{path, prefix}` for a fixed public row id prefix, such as `profile:`;
this selects a name from the filtered answer and never changes a write target.

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
`format: utf8_bytes` shows a text file's encoded size without its content.
`item_count` shows a path count. `spend_limit` shows US dollars or `No limit`.
`host` and `account` accept only the safe locator parts; a credential-bearing
URL stays hidden. Bodies are never copied into facts. Every fact value is limited to 160
characters. A hidden parent suppresses every child, regardless of declaration
order, including an owner-only parent in the caller copy. Titles remain facts when their parent is not hidden. Undeclared nested fields
produce one `Other fields: hidden (secret)` notice. They do not disappear
behind a declared sibling.

`x-held-target` names the owning operation and its public resolver method.
Description and execution must use that same resolver. A selector is resolved
before facts or a Calls preview are made. Calls freezes a no-op check too.
The held handle keeps the canonical arguments. Later detail reads refresh
shown names but do not reselect the target. An
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
verbs, and the Program verbs held on Calls. Declarations also cover the completed Ask-default, phone, nudge, People,
decision and project families, followed by Desk, window, work-item, Calls,
settings, model-library, recordings, memory, repository, provider and Agent
writes. Only live MCP tools are in this coverage; HTTP-only credential
surfaces do not gain a tool. The owner-only project Archive tool has facts too; its
authority and admission do not change. The tree-derived census enforces the shrinking remaining set in the declaration vocabulary. A prepared send reads its frozen
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

## Effective arguments and defaults

The declaration uses the owning adapter or service's `x-held-normalize`
function for scalar defaults and normalization. MCP dispatch runs that same
function before the effect port. Preparation must be idempotent: a second
pass cannot turn a blank into a different generator or destination. Stateful
derivation stays in `x-held-target`. The held payload carries the resolved
operand; the writer checks its preconditions again. Tests derive optional
arguments from every live declaration and try absent, blank and whitespace.
They compare projected facts with effective arguments at the dispatch port;
domain regressions also inspect real saved results and stale refusals.

A target can declare a composition `factory` when no registry operation owns
that MCP family. It can use `actor: caller` when its direction depends on the
sender. `phone.send_message` resolves the parent and direction through
`PhoneService.resolve_message_target`: an owner's reply to an outgoing message
names the Desk, while an agent's send still names the owner's phone. Its
`expected_direction` and `destination` are checked at the write. Neither field
gives authority. A reviewing owner does not replace the caller as sender.

`PeopleService.resolve_accept_request` selects the actual commitment body.
An omitted, empty or whitespace body falls back to the request. An accepted
request resolves to its saved commitment on replay. The owner sees its word
count and `From: Request`, `Supplied` or `Saved commitment`; no body leaves the
facts wire. The frozen source is checked again before the write. The caller
sees the count and its source as `hidden (secret)` because the body can come from encrypted
server state. `owner_only` rows similarly protect a resolved note owner, a
configured Later time, and a saved call preview's mode. Both copies keep the
same owner-facts binding and the same read/answer principals as before.

Phone Later uses the service's parser once to bind `resolved_at` and
`return_at`. Execution checks the parsed time against that base and current
settings and stores that exact time. A changed default is refused. Program
shaping binds the saved call preview's content before its spoken question;
its later yes/later answer does not change the content revision. Replacement
or loss of that preview is refused. Direct shaping retains its existing
apply policy. Facts distinguish Preview, Apply allowed changes and Call
read-back; they do not claim that the raw optional apply flag controls a
saved call answer.

Project filing reads and removals expand an old `decision:` spelling only
when no meeting decision with that id exists, including retired decisions.
Removal checks inside its write transaction. Add writes one canonical ref;
meeting Link and Unlink use one exact `meeting:` ref. No operation expands an
approved Desk decision into a second real meeting decision.

A generator fact is the requested generator; execution can still fall back
when its engine fails. Update-save provenance that the owner's edit ignores
is hidden, not described as a change to the generator. Follow-through facts
contain only the selected verb's effective payload, including its canonical
due day. Fields ignored by that verb do not appear as effective writes.


Desk aliases reuse the selected existing tool's declaration through
`x-held-delegate`. The same allowlisted handler table selects execution and
the inner declaration. The held call keeps that inner canonical payload;
the one projector reads it with the same reader. A hidden argument parent
suppresses all delegated facts. `workbench.run` uses `automation.run`.
No alias grants an additional verb or changes its admission.

Repository writes bind the registered worktree selected by the existing
workspace resolver, including its primary-worktree default. Commit shows the
message and staged-file count. It also binds the staged index digest and
refuses a changed index before invoking Git. An external Git process can still
change the index concurrently; this is a pre-invocation check, not an external
Git transaction. File contents remain hidden with their byte length.

Calls place/test resolves the configured default number once. The held call
carries that exact private number, so a later settings change cannot redirect
it. The number is hidden in both copies. Manual recording schedules carry the
same parsed defaults used at dispatch. Event-linked schedules discard ignored
manual inputs and name the selected calendar event through the public Door
read. Saved schedules use the public schedule list's title.

Provider account preparation shares the adapters' parsers. Facts show the
normalized host and account, never a token or credential URL; invalid account
fields produce a content-free refusal. Model Library preparation shares its
provider and CLI draft parsers. CLI model/label/host defaults are frozen; a
host from local config is owner-only. The supplied spend amount retains its
input precision for idempotent parsing and is shown at the writer's precision.

An Agent hand freezes the selected Project, including the absence of a
Project, and refuses a later fallback to a new filing. An omitted profile is
not described as a fixed agent: execution may resume the item's existing
agent. Launch and helper facts state the allowed action and its subject;
private ids, keys, prompts and briefs stay hidden or show word counts. An
available profile label is obtained through the public launch/profile reads.
