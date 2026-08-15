# HS-113-08 - Decision primitive

- **Project:** holdspeak
- **Phase:** 113
- **Status:** done
- **Depends on:** HS-113-01, HS-113-02
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Architecture Decision Records must be first-class Desk objects, not
buried Confluence pages or lost Slack threads. A Decision captures
what was decided, why, what alternatives were considered and rejected,
and what consequences follow. Decisions can supersede each other in
chains. They file into Knowledge Bases and Projects. When someone
asks "why did we pick this approach?" the answer is a Decision on
the desk with a gavel icon, not a search through old meeting notes.

**Articles served:** I (the Desk is the front door — decisions too),
II (capabilities are primitives), VII (no prose in the UI, labels
state what), IX (proof over claim — alternatives and consequences
are the proof).

## Ground (from the pre-charter survey)

- `web/src/lib/primitives.ts` — `PrimitiveKind` union type. Adding
  `"decision"` extends the Desk grammar with a content primitive
  for institutional memory.
- `web/src/desk/components/Pullout.tsx` — the pullout/card system
  for object display. Decisions open as pullout cards with the same
  DeskWindowFrame mechanics.
- `web/src/desk/components/InlineEditor.tsx` — after HS-113-02,
  the editor will be CodeMirror 6. Decision context, decision body,
  and consequences are markdown fields edited in CM6.
- `web/src/desk/surface/Material.tsx` — markdown renderer for
  decision context/body/consequences display.
- `web/src/desk/store.ts` — `createPrimitive` dispatches by kind.
  A `"decision"` kind needs a creation flow.

## Method

1. **Primitive extension:**
   - Add `"decision"` to `PrimitiveKind`.
   - `Decision` interface: kind, id, title, status
     (proposed/accepted/superseded/deprecated), deciders (string[]),
     decidedAt, context (markdown), decision (markdown),
     alternatives (array of {name, reason}), consequences (markdown),
     supersededBy (id), tags, linkedIds, createdAt.
   - `PrimitiveDescriptor`: label "Decision", plural "Decisions",
     syncClass "content", blurb "Architecture decision record",
     authorable true.

2. **Backend routes (`routes/primitives/decisions.py`):**
   - Standard CRUD: `GET/POST/PUT/DELETE /api/decisions`.
   - `GET /api/decisions/{id}` — full decision with alternatives.
   - `PUT /api/decisions/{id}/status` — status transition
     (proposed→accepted, accepted→superseded, accepted→deprecated).
   - `POST /api/decisions/{id}/supersede` — creates a new decision
     linked to this one, marks this one superseded.

3. **Database model (`db/models.py`):**
   - `DecisionRecord`: id, title, status, deciders_json,
     decided_at, context_markdown, decision_markdown,
     alternatives_json, consequences_markdown, superseded_by,
     tags_json, created_at, updated_at, deleted.

4. **Decision card (`DecisionCard.tsx`):**
   - Opens as a pullout/card in `DeskWindowFrame`.
   - Top: title, status badge, deciders, date.
   - Body (stacked sections):
     - **Context** — why this decision was needed (Material renderer).
     - **Decision** — what was decided (Material renderer).
     - **Consequences** — what follows (Material renderer).
     - **Alternatives considered** — expandable section, each
       alternative as a row: name + rejection reason.
   - Bottom: supersession chain — "Supersedes" / "Superseded by"
     links as grounding chips (click to pull the linked decision).
   - `DeskPropertySheet` for status (cycle gadget), deciders,
     tags.
   - `DeskFilingStrip` for zone/KB/project membership.
   - Edit opens all markdown fields in CM6 (from HS-113-02).

5. **Sprites:**
   - Decision: gavel on a block (64x64). Distinct asymmetric
     silhouette. Rest: warm wood tones. `_sel`: bright rim,
     golden gavel head. `_stale`: desaturated.
   - Badge: status mark bottom-left (filled circle for accepted,
     hollow for proposed, X for deprecated, arrow for superseded).

6. **Verbs:**
   - `Accept` — moves status to accepted, stamps decidedAt.
   - `Supersede` — creates a new linked Decision, marks this
     superseded.
   - `Deprecate` — marks deprecated with a reason.
   - `Edit` — in-world editing of all fields.
   - `Cite in meeting` — copies a reference chip.

7. **Drop matrix:**
   - Decision accepts `note`, `artifact`, `meeting` →
     "Cite as context" (attaches as a linked reference).
   - Drag a Decision onto a `kb` → "Add to Knowledge."
   - Drag a Decision onto a `project` → "File decision."

8. **Voice interaction:**
   - "New decision" → creates a decision, opens the editor.
   - "What decisions did we make about the database?" → Ask
     composer searches decisions by tag and content.
   - "Accept the migration decision" → status transition via
     voice (proposal strip with confirmation).

## Test plan

- Unit: `Decision` primitive registers in `PRIMITIVES` table,
  appears in `DESK_GROUPS` under "Content".
- Unit: `POST /api/decisions` creates a decision with all fields.
- Unit: `PUT /api/decisions/{id}/status` transitions
  proposed→accepted, stamps decidedAt.
- Unit: `POST /api/decisions/{id}/supersede` creates a new
  decision, marks the original superseded.
- Unit: `DecisionCard` renders context, decision, consequences,
  and alternatives.
- Unit: supersession chain renders grounding chips for linked
  decisions.
- Unit: status cycle gadget transitions with receipt.
- Unit: DeskFilingStrip shows KB/project membership.
- Integration: create a decision, fill in all fields, accept it,
  supersede it with a new decision — both cards show the chain.
- Screenshot walk: 1440px — decision card open on the desk,
  alternatives expanded, supersession chain visible.
- Screenshot walk: 393px — decision card responsive.
- Error leg: supersede an already-superseded decision — cycle
  gadget ghosted with "Already superseded."
