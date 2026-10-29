# People integration

People stores relationship context for the people you work with. It is not a
dashboard of direct reports. It does not rank people or derive relationship
health.

A relationship has one kind:

- `direct_report`: an explicit reporting relationship.
- `peer`: a regular collaborator at a similar level.
- `extended`: a stakeholder, partner, skip-level, or other relationship.

All kinds use the same loop: encrypted context, notes-only 1:1s, requests,
explicit commitments, and follow-through. See [People security](PEOPLE_SECURITY.md)
for access rules.

## Where People connects

- **Desk:** one People surface. A `people:<relationship-id>` scope opens one relationship.
- **HTTP:** People routes own relationships, 1:1s, agendas, grounding notes, requests, and commitments. No other service writes the encrypted store.
- **MCP:** `people.*` tools use a separate access setting. Set `HOLDSPEAK_MCP_PEOPLE_ACCESS=read` or `off` before the process starts. Agents can read when access is not off. Agents do not write People records. Only `shared_intent` material crosses MCP.
- **Follow-through:** open commitments can appear in Follow-through and link back to People. People content does not enter `action_items` or Cadence.
- **Projects:** a relationship can link an existing Project. The link does not copy confidential People content into the Project.

On first use, an empty People roster does not require a separate setup wizard.
Select **Add person** to create the local People store and add a relationship.
The relationship pane offers **Direct report**, **Peer**, and **Extended
relationship**.

If the store is not ready, locked, or unavailable, the surface reports that
state. “People is not set up on this Mac.” and “People could not be read.
Nothing changed. Press Try again.” are different states. An unavailable store
does not mean an empty roster.

## Deliberate associations

People associations are explicit. Nothing links automatically.

1. Open a relationship.
2. Select the **Context** lens.
3. Use the named control to add a link or note.
4. Check the relationship before you save.

The picker can propose a calendar event by title or an owner alias from
Follow-through. It does not use voice identity, speaking time, sentiment,
attendance, calendar frequency, or message volume.

Links live inside the encrypted People payload. The plaintext database does
not store a person reference. Unlinking removes the People link. It does not
delete the other record or the relationship.

The **Context** lens can show Notes, linked Projects, Links, calendar series,
and **Names in meeting notes** aliases. **Add note** asks for a visibility of
**Leader private** or **Shared**. These are owner choices. A locked or missing
store returns an unavailable state, not an empty match.

### Calendar series

1. Open the relationship and select **Context**.
2. Select **Link calendar event**.
3. Choose an upcoming event.

Events with the person's display name in the title can show **SUGGESTED**.
One link covers past and future occurrences of one series. A series already
linked to another relationship cannot be linked again.

The link is a `calendar_links` entry with an opaque event source and label.
Linked calendar events show an opaque person label. Use **Unlink** to remove
the association. The link does not infer that the person attended an event.

The 1:1 preparation view reads open commitments, agenda backlog, grounding notes, linked meetings, actions, and decisions.
It also reports unlinked meetings within the selected window. It stores no generated brief. Its policy
states `visibility: shared_intent_only`, `inference: client_owned`, and
`employment_decisions: prohibited`.

### Owner alias

An owner alias maps an owner string from Follow-through to a relationship.

1. Open the relationship and select **Context**.
2. In **Names in meeting notes**, type the string and select **Add**.
3. Select **Remove** when you no longer want the alias.

Comparison ignores case. Reserved values include `me`, `remote`, and `you`.
One alias belongs to one relationship. The service rejects an empty alias or
an alias already held by another relationship.

Follow-through can add a person label and relationship identifier to a mapped
card when the alias resolves. If People is locked, the board shows no person
data. It does not guess the owner.

### Not available: meeting participants

HoldSpeak does not link a meeting participant to a People relationship.
Automatic matching, voice identity, and attendance analysis are not available
for this integration. A meeting name or title does not establish a person link.

## Satisfaction history

Commitment history is append-only. Events for accepted, delegated, satisfied,
dismissed, and reopened keep their time and source.

Open a commitment to inspect it. **Send to automation** can send the selected
commitment to a configured Workbench when that control is available. This
starts an automation path. It does not mark the commitment satisfied.
Select **Mark satisfied** only when you have the evidence that the commitment
is complete.

The History lens shows counts of accepted, open, satisfied, and
evidence-backed commitments for one relationship. These are follow-through
facts. They are not performance scores.
