# People integration surfaces

The People ledger is an organizational relationship authority, not a direct-report
dashboard. Its first vocabulary is deliberately small and extensible:

- `direct_report`: an explicit reporting relationship.
- `peer`: a regular collaborator at a similar organizational level.
- `extended`: a stakeholder, partner, skip-level, or other farther relationship.

Every kind uses the same continuity loop: encrypted context, notes-only 1:1s,
requests, explicit commitments, and Follow-through. The UI never ranks people or
derives relationship health.

## Shipped seams

- **Desk:** one singleton People surface. `people:<relationship-id>` is the stable
  scope used to open a relationship from another surface.
- **HTTP service:** authenticated People endpoints own relationships, 1:1s, agenda,
  grounding notes, requests, and commitments. Callers do not write the sidecar.
- **MCP:** local-owner `write` capability by default; set
  `HOLDSPEAK_MCP_PEOPLE_ACCESS=read` or `=off` at process start to reduce or
  disable it. It exposes only `shared_intent` material and includes
  `people.grounding.get`, a manual-source bundle with no implicit model call.
- **Follow-through:** open commitments are hydrated in memory and deep-link back to
  People. No People content enters `action_items` or Cadence.
- **Commitment execution:** clicking a commitment opens its inspector. An explicit
  `Send to Workbench` gesture creates a normal Workbench item, whose status, result,
  and artifact reference hydrate back into People. Workbench owns execution; People
  owns whether the relationship promise is satisfied.
- **Projects:** a relationship can link existing Project IDs. Linked projects open
  in Project Memory, appear in shared MCP relationship/grounding projections, and
  contribute project name, description, keywords, context, and resource references
  when a commitment becomes Workbench work.
- **Sprite language:** the PixelLab-generated relationship-ledger sprite registers
  as the People family and as the People dock icon.

## Deliberate association: the calendar series link (FULFILLED)

The calendar series link is the first sanctioned deliberate association between a
People relationship and a HoldSpeak data source. It satisfies rules 1 through 7
below and is the only shipped association path in this delivery.

**The gesture.** On the relationship detail, the owner chooses **Link calendar
event** on the Context lens. A picker lists upcoming events from the rail;
rows whose title contains the person's display name are sorted first and tagged
**SUGGESTED** (case-insensitive, in-memory only, never logged or persisted). The
owner's click is the association gesture. The stored evidence is the event's own
title and UID, selected by the owner.

**The link.** The association is a `calendar_links` entry (`uid`, `source_id`,
`label`) inside the relationship's encrypted payload. The link is series-level:
one link covers every past and future occurrence of the recurring event. Invariant
P1 enforces one person per series; linking a series already held by another
relationship refuses by naming the holder (`series_already_linked`). Re-linking
the same person is idempotent (refreshes label and timestamp). Unlinking is a
two-beat in-world verb on the same surface.

**Resolution.** `resolve_relationship_by_series(uid, source_id)` in
`people_service` queries the encrypted store at read time. It is
readiness-guarded: a locked or absent sidecar returns `{“state”: “unavailable”}`,
never an empty match. The plaintext database never stores a person reference (the
138 law). Resolution projects a `person_label` on linked rail event rows and
extends the meeting origin line when the sidecar is open.

**The brief.** `one_on_one_brief(relationship_id)` computes a transient 1:1
preparation view across the encrypted/plaintext boundary: open commitments
(encrypted), agenda backlog (encrypted), grounding note count (encrypted), the
last linked meetings with their open action items (plaintext, by reference), any
decisions minted from those meetings (plaintext, via the `decision_record_sources`
chain), and the count of unlinked meetings in the window (manual recordings
without `calendar_event_id`). The brief never persists a byte to any store.

**MCP boundary.** The `people.one_on_one.brief` tool gates on `access_mode() !=
“off”` via `_require_access` and filters encrypted items to `shared_intent`
visibility via the `_mcp_readable` path. Leader-private content never crosses to
an MCP client. The response carries a `policy` block naming the disclosure
boundary (`visibility: shared_intent_only`, `inference: client_owned`,
`employment_decisions: prohibited`).

**Compliance with the integration contract:**

1. The picker proposes candidates from owner-selected textual evidence only (the
   event title).
2. The owner's click is the explicit gesture; nothing auto-links.
3. The link itself (`calendar_links`) lives inside the encrypted People payload.
4. The Door rail exposes only an opaque person chip (`person_label`); meeting
   surfaces carry no People reference in the plaintext database.
5. Voice embeddings, speaking time, sentiment, attendance, calendar frequency,
   and message volume are never used as identity or relationship signals.
6. Unlinking is complete and auditable; it removes the link from the encrypted
   payload without deleting either the calendar event or the relationship.
7. The MCP adapter applies `_mcp_readable` visibility before any linked material
   reaches an MCP client.

### Deferred: meeting participants

Meeting-participant association (identifying a meeting participant as an existing
People relationship) remains intentionally unshipped. The seven rules above
constrain it when it is reviewed. Automatic correlation, voice-based identity,
attendance frequency analysis, and speaker-to-person inference are forbidden by
this contract.

## Satisfaction history

Commitment history is append-only inside the People authority: accepted, delegated,
satisfied, dismissed, and reopened events retain their timestamp and source. A
satisfaction gesture snapshots available Workbench item status, completion time, and
artifact reference plus an optional human rationale. A Workbench result never marks
a relationship promise satisfied automatically.

The History lens reports accepted, open, satisfied, and evidence-bearing counts for
the selected relationship. These are personal follow-through facts, not employee or
cross-person performance scores.
