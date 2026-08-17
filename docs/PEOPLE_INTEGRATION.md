# People integration surfaces

The People ledger is an organizational relationship authority, not a direct-report
dashboard. Its first vocabulary is deliberately small and extensible:

- `direct_report` — an explicit reporting relationship;
- `peer` — a regular collaborator at a similar organizational level;
- `extended` — a stakeholder, partner, skip-level, or other farther relationship.

Every kind uses the same continuity loop: encrypted context, notes-only 1:1s,
requests, explicit commitments, and Follow-through. The UI never ranks people or
derives relationship health.

## Shipped seams

- **Desk:** one singleton People surface. `people:<relationship-id>` is the stable
  scope used to open a relationship from another surface.
- **HTTP service:** authenticated People endpoints own relationships, 1:1s, agenda,
  grounding notes, requests, and commitments. Callers do not write the sidecar.
- **MCP:** default-off `read`/`write` capability. It exposes only `shared_intent`
  material and includes `people.grounding.get`, a manual-source bundle with no
  implicit model call.
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

## Suggested next integration: meeting participants

Maintainer prompt: **consider allowing the owner to identify a meeting participant
as an existing People relationship.** Treat this as a deliberate association, not
identity inference.

A safe follow-up should:

1. propose candidate links from owner-selected textual evidence only;
2. require an explicit owner gesture before persisting a link;
3. keep the association and aliases inside the encrypted People store;
4. expose only an opaque People scope to the meeting surface;
5. never use voice embeddings, speaking time, sentiment, attendance, calendar
   frequency, or message volume as identity or relationship-health signals;
6. make unlinking complete and auditable without deleting either source record;
7. apply visibility before any linked material reaches MCP or a model.

That contract lets a meeting offer “Open relationship,” attach an accepted agenda
source, or suggest a follow-up without turning speaker recognition into employee
monitoring. Automatic correlation remains intentionally unshipped until this
consent, custody, and unlink model is reviewed.

## Satisfaction history

Commitment history is append-only inside the People authority: accepted, delegated,
satisfied, dismissed, and reopened events retain their timestamp and source. A
satisfaction gesture snapshots available Workbench item status, completion time, and
artifact reference plus an optional human rationale. A Workbench result never marks
a relationship promise satisfied automatically.

The History lens reports accepted, open, satisfied, and evidence-bearing counts for
the selected relationship. These are personal follow-through facts, not employee or
cross-person performance scores.
