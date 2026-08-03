# HS-113-11 - The refit

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Every existing surface on the Desk must be rebuilt from the shared
kit (story 01). No window interior should be a "website embedded in
glass." Pullout faces must be purpose-built object material, not
generic web documents. The Ask panel must hide its config rack behind
a gear door. SessionPullout and PersonaChat must fold into Agents.
AttentionDrawer must become a proper system shade. Links must never
eject the user from the Desk. Error states must be named refusals,
not implementation strings. When this ships, every window on the Desk
looks and behaves like it was born from the same OS, because it was
built from the same kit.

**Articles served:** I (no feature-owned pages, routes are deep
links to desk state), VII (no prose, labels state what, quiet chrome,
in-world), VIII (native-grade craft, consistent quality).

## Ground (from the audit)

**Surfaces that are "websites in glass":**

1. **DeskToolInspector** — `DeskToolInspector.tsx:237-529`.
   Paragraphs, dl fact grids, headings, sections, lists, CTA chips,
   proposal panels, prose error messages. The clearest example.

2. **Pullout meeting/artifact/workflow faces** —
   `Pullout.tsx:383-447,451-587,722-842`. Generic headings,
   paragraphs, repeated sections. Meeting detail leads with summary
   and action lists rather than outcomes and inline approval.

3. **AttentionDrawer** — `AttentionDrawer.tsx:63-251`. Metric tiles,
   filter form with submit button, paginated list, definition-list
   detail view. Duplicates window chrome with an eyebrow heading
   inside the frame.

4. **Ask panel config rack** — `AskPanel.tsx:459-570`. Lens
   selection, destination picker, context inventory, resource/rail
   pickers, and token instrumentation all visible on the working
   face.

5. **SessionPullout as standalone console** —
   `SessionPullout.tsx:665-747`. Terminal, policy facts, arming
   strip, key palette, composer, factory controls, receipt, and
   classification form as separate footer/control bands.

6. **PersonaChat as separate chatbot window** —
   `DeskApp.tsx:49-76`, `PersonaChat.tsx:215-367`. Mounted as a
   standalone `DeskWindowFrame id="chat"` with a conventional
   transcript and composer.

**Route ejection and prose:**

7. **Attention source links eject** — `SystemShade.tsx:188-189,
   227-228`, `AttentionDrawer.tsx:191-193`. Raw `href` links to
   `/history`, `/cadence` routes.

8. **Error strings leak implementation** — `Pullout.tsx:204-207,
   993-996`, `AttentionDrawer.tsx:117-123,135-189`. `String(error)`
   rendered directly.

9. **Prose in empty/error states** — `SystemShade.tsx:87-100`,
   `AttentionDrawer.tsx:231-246`, `Pullout.tsx:272-274,539-543`.
   "Nothing finished while you were away", "Reload the Desk to
   retry."

10. **Note editing as detached form session** —
    `Pullout.tsx:487-507,1021-1044`. Editing swaps the body for a
    textarea with controls in a separate footer.

11. **Dossier asset links open browser tabs** —
    `DeliveryDossierWindow.tsx:160-185`. `target="_blank"` instead
    of Desk presentation.

## Method

1. **Refit Pullout faces onto the shared kit:**
   - Meeting face: lead with outcomes/decisions, not summary
     paragraphs. Transcript behind `DeskReceiptInset` disclosure.
     Approval verbs inline on material.
   - Artifact face: `DeskPropertySheet` for metadata,
     `Material` for body.
   - Note face: editing becomes in-place via the CM6 editor
     (from story 02) in the SAME geometry — no form swap.
   - All faces use `DeskWindowFooter` for actions, `DeskFilingStrip`
     for membership, `SurfaceState` for empty/error.

2. **Refit DeskToolInspector:**
   - Projects, destinations, integrations as `DeskPropertySheet`
     entries with grounding chips.
   - Actions as registered verbs in context menus.
   - Configuration routed to Settings gear door.
   - Proposals as `DeskReceiptInset` with approve/deny verbs.

3. **Refit AttentionDrawer as system shade:**
   - Remove the eyebrow heading (frame has identity chrome).
   - Replace metric tiles + filter form with `DeskSearchFilter`.
   - Replace paginated list with `DeskSortableTable`.
   - Replace definition-list detail with `DeskPropertySheet`.
   - Use `SurfaceState` for empty state ("Empty", not prose).

4. **Refit Ask panel working posture:**
   - Working face: one generous `DeskComposer` column.
   - Model/lens/context configuration behind a gear door.
   - Grounding as lightweight material attachment, not an
     inventory panel.

5. **Fold SessionPullout into Agents:**
   - Agents opens on the blocked-session/question material.
   - Answer composer (`DeskComposer`) one action away.
   - Terminal/admin/configuration in a wing or gear door.
   - Remove the standalone control-console layout.

6. **Fold PersonaChat into Agents:**
   - Remove standalone `DeskWindowFrame id="chat"` mount from
     `DeskApp.tsx`.
   - Chat becomes a wing within the Agents application window.
   - Same working/reviewing posture as other agent material.

7. **Kill route ejection:**
   - `SystemShade.tsx` and `AttentionDrawer.tsx`: replace raw
     `href` links with Desk state transitions (open the relevant
     window/object on the desk).
   - `DeliveryDossierWindow.tsx`: replace `target="_blank"` with
     Desk presentation or named external handoff with egress badge.

8. **Fix error surfaces:**
   - Replace all `String(error)` rendering with named Desk
     refusals: short stable identity, named rule/fix,
     technical details behind disclosure.
   - Replace all prose empty/error states with `SurfaceState`
     grammar: glyph, terse label, compact retry verb.

9. **Responsive surface viewport:**
   - Ask, Session, and Attention bodies use `.desk-surface-body`
     with the 560px container-query breakpoint.

## Test plan

- Visual: open a meeting pullout — outcomes/decisions lead, not
  summary paragraphs. Transcript behind disclosure.
- Visual: edit a note — text becomes editable in place, no form
  swap. CM6 editor in the same geometry.
- Visual: open DeskToolInspector — property sheets and grounding
  chips, not paragraphs and dl grids.
- Visual: open AttentionDrawer — `DeskSortableTable` rows, not
  a paginated list with a submit button.
- Visual: open Ask — one composer column. Config behind gear door.
- Visual: PersonaChat is gone as a standalone window. Chat is a
  wing in Agents.
- Visual: click an attention source link — stays on the Desk.
  No route ejection.
- Visual: trigger an error — named refusal with fix guidance, no
  `String(error)`.
- Visual: empty attention drawer — "Empty", not "Nothing finished
  while you were away."
- Regression: all existing pullout/ask/session tests pass.
- Screenshot walk: 1440px — meeting pullout, note pullout, Ask
  panel, Agents window, AttentionDrawer. All must look like one
  system built from the same kit.
- Screenshot walk: 393px — all surfaces responsive at the
  container-query breakpoint.
