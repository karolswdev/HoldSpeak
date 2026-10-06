# People integration

The People ledger keeps relationships with the people you work with. It is not a dashboard of direct reports. It never ranks people and never derives relationship health.

A relationship has one kind:

- `direct_report`: an explicit reporting relationship.
- `peer`: a regular collaborator at a similar level.
- `extended`: a stakeholder, partner, skip-level, or other farther relationship.

All kinds use the same loop: encrypted context, notes-only 1:1s, requests, explicit commitments, and Follow-through. For the encryption and the access rules, see [People security](PEOPLE_SECURITY.md).

## Where People connects

- **Desk:** one People surface. The scope `people:<relationship-id>` opens a relationship from another surface.
- **HTTP:** the People routes own relationships, 1:1s, agendas, grounding notes, requests, and commitments (`holdspeak/web/routes/people.py`). No other code writes the encrypted store.
- **MCP:** the `people.*` tools (`holdspeak/mcp/families/people.py`). The default access is `write`. Set `HOLDSPEAK_MCP_PEOPLE_ACCESS=read` or `off` before the process starts to reduce it. MCP clients see only `shared_intent` material. `people.grounding.get` returns a bundle of manual sources and makes no model call.
- **Follow-through:** open commitments appear in Follow-through and link back to People. People content never enters `action_items` or Cadence.
- **Commitment execution:** select a commitment to open its inspector. **Send to Workbench** creates a normal Workbench item. The item status, result, and artifact reference show in People. Workbench runs the work. People records whether the promise is kept. A Workbench result never marks a promise as satisfied.
- **Projects:** a relationship can link existing Projects. Linked Projects open in Project Memory. Their name, description, keywords, context, and resource references go into the Workbench item when a commitment becomes work.

## Deliberate associations

An association links a relationship to other HoldSpeak data. Two exist. Both follow these rules:

1. The owner chooses the link. Nothing links automatically.
2. A picker proposes candidates from visible text only: an event title or an owner string.
3. The link lives inside the encrypted People payload. The plaintext database never stores a person reference.
4. Voice embeddings, speaking time, sentiment, attendance, calendar frequency, and message volume are never identity signals.
5. Unlinking removes the link from the encrypted payload. It deletes neither the other record nor the relationship.
6. MCP applies its access mode and `shared_intent` filter before linked material reaches a client.
7. A locked or missing store returns `{"state": "unavailable"}`, never an empty match.

### Calendar series

1. Open the relationship and select the Context lens.
2. Select **Link calendar event**.
3. Choose an upcoming event. Events with the person's display name in the title sort first and show **SUGGESTED**.

The link is a `calendar_links` entry (`uid`, `source_id`, `label`). One link covers every past and future occurrence of the series. One series belongs to one person. A series that another relationship holds fails with `series_already_linked`. Linking the same person again only refreshes the label.

`resolve_relationship_by_series` in `holdspeak/services/people_service.py` reads the link. Linked calendar events show an opaque `person_label`. MCP tools: `people.calendar.link` and `people.calendar.unlink`.

`one_on_one_brief` builds a 1:1 preparation view and stores nothing. It holds open commitments, agenda backlog, the grounding note count, recent linked meetings with their open action items, decisions from those meetings, and the count of unlinked meetings in the window. MCP tool: `people.one_on_one.brief`. Its `policy` block states `visibility: shared_intent_only`, `inference: client_owned`, and `employment_decisions: prohibited`.

### Owner alias

An owner alias maps an owner string from Follow-through to a relationship.

1. Open the relationship and select the Context lens.
2. In **Owner aliases**, type the string and select **Add**.
3. To remove an alias, select **Remove**, then **Remove?**.

The alias is an `owner_aliases` entry in the encrypted payload. One alias belongs to one person. Comparison ignores case. Failures:

| Code | Cause |
| --- | --- |
| `owner_alias_taken` | Another relationship holds the alias. |
| `owner_alias_reserved` | The string is `me`, `remote`, or `you`. |
| `owner_alias_required` | The string is empty. |

`resolve_relationship_by_owner` reads the alias. The `/api/follow-through/board` route adds `person_label` and `person_relationship_id` to mapped cards (`holdspeak/web/routes/follow_through.py`). `FollowThroughService.board()` stays free of person data. If the store is locked, the board shows no person data. MCP tools: `people.owner_alias.link` and `people.owner_alias.unlink`.

`compose_person_overlay` (`holdspeak/services/person_overlay.py`) adds per-person sections to the Monday brief response. It counts what they owe you, what you owe them, the agenda backlog, and the next linked 1:1. The stored brief never holds these sections. When People access is `off`, the `monday_brief.get` tool omits them.

### Not available: meeting participants

HoldSpeak does not link a meeting participant to a relationship. The rules above apply if this changes. Automatic matching, voice identity, and attendance analysis stay forbidden.

## Satisfaction history

Commitment history is append-only. Events for accepted, delegated, satisfied, dismissed, and reopened keep their time and source. A satisfaction gesture records the Workbench item status, completion time, and artifact reference. It can also record your reason.

The History lens shows counts of accepted, open, satisfied, and evidence-backed commitments for one relationship. These are your follow-through facts. They are not performance scores.
