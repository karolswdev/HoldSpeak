# Phase 92/93 UI consistency inventory

**Captured:** 2026-07-15<br>
**Trigger:** direct owner finding — the Phase 92/93 deliverables introduced
inconsistency with the general UI layout and with the specific rules individual
components had already established, on Web and iOS.<br>
**Scope reviewed:** every UI file touched in `d955fab0..HEAD` (the Phase 92/93
window): 92 files under `web/src`, 66 under `apple/`. Four independent review
passes (Web desk island, Web pages/shared surfaces, flagship Swift app, and a
desk UX/interaction pass), each anchored against the pre-92 grammar via
`git show d955fab0:<file>`.<br>
**Owner UX finding (2026-07-15):** floating desk areas are glued in place —
not movable, not resizable — which contradicts the Desk OS window grammar this
phase promised; the experience is not streamlined. The UX findings section
below carries this dimension.<br>
**Disposition:** every finding below is verified against the current tree and
carries a remediation status. This document is the inventory the remediation
commits point at; it updates as findings close.

## The established grammar (what the new work must match)

### Web desk island (`web/src/desk`)

- Tokens live only in `web/src/styles/tokens.css`: 4px spacing grid
  (`--space-1..8`), radii (`--radius-xs/sm/md/lg/pill`, plus `--radius-5:18px`),
  type scale (`--font-size-xs..3xl`), color roles (`--surface-1/2/3`,
  `--border*`, `--text*`, semantic `--ok/--warn/--danger/--info`), elevation
  (`--elev-0..4`), motion. There is no `--surface-0` and no `--ink`.
- Every rule is scoped `.desk-next .desk-<component>-<part>`; the base sheet has
  zero unscoped selectors.
- Panel anatomy (canonical `.desk-pullout`): `top:64px; right:18px;
  bottom:18px`, radius 18px, accent color-mix border + 3px accent left border,
  solid `rgba(13,11,18,0.93)` fill, `blur(10px)`, `0 26px 70px` shadow,
  explicit part classes (`-head/-title/-close/-body/-foot`), close glyph `✕`
  at 15px `--text-muted` with `aria-label="Close"`.
- Z-index band: world-drag 20, panels 28–30, the one modal 34, overlay 60.
- Island buttons are `.desk-chip` / `.desk-chip.quiet`.

### Web pages (`web/src/pages`, shared shell)

- Page header: `PageHero` → `.page-hero` with `.signal-eyebrow`, one `<h1>`,
  one supporting line, optional actions, then `WorkroomBar`.
- Surfaces: `.signal-panel` (+ header eyebrow/h2 + `.signal-panel-body`),
  `.data-row`/`.data-list`, `.metric-grid`, `.code-block`. Buttons are `.btn`
  + `.btn--primary/secondary/ghost/danger`. `.notice`, `.button`, `.secondary`,
  and `.quiet` do not exist in the app shell's stylesheets.
- States: loading `Skeleton`, error/info `InlineMessage`, empty `EmptyState`,
  inline status `StatusPill`, key/value facts `.signal-facts`; warnings use
  `--warn-soft` background with a 35% color-mix border.
- Vocabulary flows through `productLanguage.ts`
  (`controlModeLabel/Description`, `destinationClassLabel`); raw wire values
  never render.

### Flagship Swift app (`apple/App/MeetingCapture`)

- Two palettes by surface: `Sig`/`SigN` (Signal) for list/settings/HUD chrome;
  `DioPal` for everything on the diorama canvas. A file picks one and stays in
  it. Stock `List`/`Form`/`.bordered` chrome appears nowhere on these bespoke
  surfaces.
- Dio modal sheet anatomy (`DioActSheet`/`DioSendCard`/`DioRunTargetSheet`):
  scrim `black.opacity(0.6–0.7)` + tap dismiss; glyph icon in a 34–36pt circle
  + title 16pt heavy rounded + subtitle 11–11.5pt muted + optional
  `EgressBadge`; bottom Cancel capsule (44–46pt, `.white.opacity(0.06)`);
  container `padding(20)`, maxWidth 440–460, radius 26, gradient
  `[0x171320, 0x0C0A12]`, `strokeBorder(.white.opacity(0.08))`, heavy shadow.
- `EgressBadge(scope:)` is the single egress chrome; `RunsOnPicker` renders the
  Runs-on chip; `SignalCard`/`GlyphChip`/`PressableCard` are the shared
  containers; haptics via `tactile()`.
- Vocabulary flows through `ProductLanguage` (posture labels/descriptions,
  destination and lifecycle labels).

## Findings

Severity: **crit** (broken rendering/behavior), **high** (grammar broken in a
way the owner sees immediately), **med** (component-rule violation), **low**
(polish/nit). Status: `fixed` = shipped by the Phase-93 UI remediation change
(the commit this document ships in); `open` rows name their follow-up.

### Web — desk island (WD)

| ID | Sev | Where | Defect | Status |
|---|---|---|---|---|
| WD-01 | crit | `desk.css` 365, 417, 535, 653, 2646, 2823 | `var(--surface-0)` is undefined; the `color-mix()` is invalid so the `background` declaration drops — Create menu, Tool Shelf, Tool Inspector, and Attention Drawer render with no fill over the diorama | fixed |
| WD-02 | high | `.desk-tool-shelf` 406, `.desk-tool-inspector` 523, `.desk-create-menu` 355, `.desk-attention-drawer` 2635 | Four new floating panels invent their own panel language (radii 22/20/16/24 vs the established 18; offsets 62/64/12 vs 64; shelf/drawer drop the accent left border; `blur(24px)` vs 10; hand-rolled shadows) and diverge from each other | fixed |
| WD-03 | high | `desk.css` 359, 410, 528, 2638, 2612 | Z-index inflation (75/82/83/84/90) far above the established 28–34–60 band; Attention Drawer at `top:12px` overlaps the top chrome | fixed |
| WD-04 | high | `desk.css` 717–753 | `.desk-first-*` rules (plus bare `h1,h2,p`) are unscoped, breaking the universal `.desk-next` scoping; they leak outside the island | fixed |
| WD-05 | med | `DeskToolShelf.tsx` 248, `DeskToolInspector.tsx` 247, `AttentionDrawer.tsx` 53 | Close affordance re-invented per panel: bare `<button>×</button>` at 22px `--text` via element selectors, vs the established `.desk-pullout-close` (`✕`, 15px, `--text-muted`) | fixed |
| WD-06 | med | `desk.css` 428–448, 548–566, 2658–2666 | New panels style bare `h2/h3/p/small/header button` tags instead of explicit `.desk-*` part classes | fixed |
| WD-07 | med | `desk.css` 1436–1438 | `.desk-coder-draft-input` invents `--ink` (undefined) and hardcodes input chrome instead of the `.desk-editor input` token pattern | fixed |
| WD-08 | med | `AttentionDrawer.tsx` 36, 50, 51, 56 | One panel, three names ("Desk memory", "DESK ACTIVITY", "Attention and Receipts"); all-caps hardcoded in JSX instead of CSS `text-transform` | fixed |
| WD-09 | med | `FirstWords.tsx` 174, 250–308 | Mixes Signal shell components (`Button`, `.btn`, `signal-eyebrow`) with island `.desk-first-*` classes in one component | accepted — FirstWords is the shell's dictation module embedded in the empty desk; it stays on the Signal lane deliberately (copy fixed under WD-12) |
| WD-10 | low | `desk.css` 336, 362, 373, 402, 404, 550, 741, 2685 | Off-grid spacing (7/9/11px), radius 5px, `font-weight:750`, raw px where `--space/--radius/--font-size` tokens exist; shadow alpha notation drifts (`/ 58%` vs `/ 0.58`) | fixed |
| WD-11 | low | `desk.css` 746, 1394 | Hardcoded `#130b08` where `--text-on-accent` exists; `#ffb5a7` where the sibling line already uses the danger token | fixed |
| WD-12 | low | `FirstWords.tsx` 216, 247 | "Writing your words…" anthropomorphizes the runtime (use "Transcribing…"); copy-contract drift in the placeholder | fixed |

### Web — pages and shared surfaces (WP)

| ID | Sev | Where | Defect | Status |
|---|---|---|---|---|
| WP-01 | crit | `WorkbenchPage.tsx` 311–317 | Status/errors use undefined `.notice` / `.notice error` classes — unstyled error surface; convention is `InlineMessage` | fixed |
| WP-02 | high | `WorkbenchPage.tsx` 434 | "Return to kept Artifact" uses non-existent `button secondary` classes; convention is `btn btn--secondary` | fixed |
| WP-03 | med | `WorkbenchPage.tsx` 441 | Run output in a bare `<pre>` instead of `.code-block` | fixed |
| WP-04 | med | `MeetingIntelRecovery.tsx` 143 | `.quiet` exists only in `desk.css` (not loaded by the app shell) — unstyled text on HistoryPage | fixed |
| WP-05 | high | `SettingsPage.tsx`, `HistoryPage.tsx` 427–433, 463 | The same control-posture concept rendered three unrelated ways with no shared component | fixed |
| WP-06 | med | `ProfilesPage.tsx` 156–164 | Destination class re-derived by hand (lowercase strings + inline RFC1918 regex) instead of `destinationClassLabel()`; casing now differs from LivePage | fixed |
| WP-07 | high | `HistoryPage.tsx` 463–475, 503 | Raw wire values in user copy: `effect_class`/`destination`/`authority_basis` snake_case fallbacks and `String(row.status)` — copy contract forbids bare wire state | fixed |
| WP-08 | med | `HistoryPage.tsx` 321 | Capture warning prints raw `capture_status` although `displayState()` already maps it; trailing reassurance clause ("…not false completion") is contract filler | fixed |
| WP-09 | med | `react-app.css` 256–260 vs 778–783, 835–840 | Two divergent warning tints coexist in the Meeting detail (recovery cards use 45%/7% mixes vs the canonical `--warn-soft`/35%) | fixed |
| WP-10 | med | `react-app.css` 773–873 | `.meeting-conflict*` and `.meeting-intel-recovery*` are near-byte-identical parallel CSS families for one recovery-card concept | fixed |
| WP-11 | med | `SettingsPage.tsx` 410–419 | Policy source/version/precedence internals in permanent Settings chrome; contract wants them behind a detail/disclosure layer | fixed |
| WP-12 | med | `MeetingConflictRecovery.tsx` 150–155 | Anthropomorphic + redundant copy ("HoldSpeak kept both and made no silent choice") | fixed |
| WP-13 | low | `MeetingConflictRecovery.tsx` 35–147, `MeetingIntelRecovery.tsx` 100–117 | Recovery cards re-derive a bespoke facts grammar instead of `.signal-facts` | fixed |
| WP-14 | low | `SettingsPage.tsx` 355 | Posture toast concatenates three clauses; static facts belong in the panel description | fixed |
| WP-15 | low | `StudioPage.tsx` | Read-only tools (Activity) get `configure-*` workroom actions and a uniform "Configure →" CTA | fixed |

### iOS — flagship Swift app (N)

| ID | Sev | Where | Defect | Status |
|---|---|---|---|---|
| N-01 | high | `QueuePresence.swift` 150–192 | Desk-memory detail is a stock grouped `List`/`Section`/`LabeledContent` sheet inside a fully hand-drawn Signal HUD; no peer surface uses system form chrome | fixed |
| N-02 | high | `DeskDioramaStage.swift` 1546–1616 | `DioProjectInspector` bypasses the Dio sheet anatomy on nearly every shared value (radius 24 vs 26, flat fill vs gradient, no shadow, no glyph header, top-right `xmark` vs bottom Cancel capsule, flat CTA) | fixed |
| N-03 | high | `CompanionMesh.swift` 1011–1027 | Recovery card uses native `.buttonStyle(.bordered)` and generic labels; grammar is capsule/`PressableCard` buttons with commitment verbs ("Retry transcription") | fixed |
| N-04 | med | `DeskDioramaStage.swift` 1842, 2356 | Two hand-rolled "This device" badges duplicate `EgressBadge` (one even re-implements the capsule at a different height) | fixed |
| N-05 | med | `AppSettings.swift` 172, `DeskSteer.swift` 127–141, `QueuePresence.swift` 219–228 | Posture chrome rendered three unrelated ways; no shared `PostureBadge` (contrast `EgressBadge`, which unifies egress) | fixed |
| N-06 | med | `DeskDioramaStage.swift` 1466 | Documentation prose baked into the permanent relationship pull-out ("A Zone is where this object lives…") | fixed |
| N-07 | med | `AppSettings.swift` 190–192 | Invariant enumeration in permanent posture-card chrome; contract puts implementation detail behind a diagnostic layer | fixed |
| N-08 | med | `RunsOnPicker.swift` 88–92 | Full sentence at fixed 8.5pt with `lineLimit(1)` — Dynamic-Type-hostile, truncates; body lines are 11–13.5pt | fixed |
| N-09 | med | `QueuePresence.swift` 116 | Hardcoded `.frame(maxHeight: 520)` can exceed a small iPhone's height and ignores Dynamic Type | fixed |
| N-10 | low | `DeskSteer.swift` 216–221 | Authorized-foot line concatenates destination/authority/receipt telemetry with raw lowercase wire fallbacks ("yolo") | fixed |
| N-11 | low | `AppSettings.swift` 49, `ProfilesView.swift` 536–554 | Runs-on/destination naming drifts ("Manage destinations" / "Runs on" / "New Runs on destination") | fixed |
| N-12 | low | `GroundingPicker.swift` 135 | `meetingRow` lacks the `accessibilityLabel` its new sibling `resourceRow` correctly carries | fixed |

### Web — desk UX / interaction model (UX)

The owner's finding verified: every floating desk surface is pinned with
`position: fixed`/`absolute` to one hardcoded corner; none is movable or
resizable. The desk already ships a proven drag + persistence pipeline — but
only pixel-art objects use it (`DeskObject.tsx:67-114` drag via
`@use-gesture/react` with tap-vs-drag threshold and unit-space clamp;
`store.ts:25-41,559-573` position state persisted under `hs.diorama.pos`).
Panels reuse none of it.

| ID | Sev | Where | Defect | Status |
|---|---|---|---|---|
| UX-01 | crit | `desk.css:933-948`, `AskPanel.tsx:218`, `PersonaChat.tsx:186`, `SessionPullout.tsx:633` | Object Pullout, Ask panel, Persona chat, and Session pullout all render into the same fixed rectangle (`top:64 right:18 bottom:18`); none movable, none resizable | fixed |
| UX-02 | crit | `store.ts:260-555` vs `steering.ts:114,278`, `DeskToolShelf.tsx:85`, `AttentionDrawer.tsx:20` | Open-state split across four uncoordinated stores + component-local state: `useDesk` panels exclude each other, but SessionPullout/ToolShelf/AttentionDrawer are not coordinated — panels genuinely occlude in the same corner, DOM order breaking ties | fixed |
| UX-03 | high | `store.ts:260-267,345-355,517-555` | Opening any `useDesk` panel nulls the other four — one drawer plus the Ask panel cannot coexist, and closing unmounts the component so un-persisted panel state is discarded | fixed |
| UX-04 | high | `desk.css:28,241-243,410,528,2638` | No stacking policy: hand-tuned z ladder (28/75/82/83/84/90) with an in-CSS comment admitting the band-aid; no focus-to-front, no active-window concept | fixed |
| UX-05 | high | `DeskStartActions.tsx:12,18-23`, `RecordOrb.tsx:70,109`, `DeskChrome.tsx:14` | Competing entry points: Record has two doors with different behavior (chip navigates off-desk to /live; orb records in place); Dictate leaves the desk entirely via two doors | fixed |
| UX-06 | med | `SessionPullout.tsx`, `desk.css:2452`, `MissionControlConveyor.tsx:75` | Steering one coder spans three surfaces in three corners (PanePicker bottom-left, SessionPullout top-right, conveyor pins bottom) | open — partially eased: the Session window is now movable/resizable and survives stray clicks; consolidating the pane picker into the Session window is follow-up scope |
| UX-07 | med | `World.tsx:83-86`, `store.ts:514-516` | A stray tap on the empty desk clears the selection and closes the Ask panel — one background click wipes a roped Ask context | fixed |

**Desk-window contract (the remediation for UX-01..04):** one shared
`DeskWindow` shell — `.desk-window` with a `-head` drag handle and a corner
resize grip — whose `{x,y,w,h}` come from a new `panels` record in the desk
store persisted beside object positions (`hs.desk.panels`), applied as inline
geometry the same way `DeskObject.tsx:138-147` applies object position. Drag
and resize reuse the `DeskObject` `useDrag` pattern; a `focusPanel(id)` action
bumps a z counter on pointer-down (the same trivial lift the dragged object
already gets), replacing the hand-tuned ladder. Adopters: Pullout, AskPanel,
PersonaChat, SessionPullout, DeskToolShelf, DeskToolInspector,
AttentionDrawer; the hardcoded corner geometry leaves
`.desk-pullout/.desk-tool-shelf/.desk-tool-inspector/.desk-attention-drawer`.
With per-panel rects the destroy-on-open exclusivity relaxes to
focus-not-destroy.

### Noted, not scheduled here

- `AmbientLayer.tsx` 277–279 copy ("Making meeting intelligence", "The hub is
  working through the transcript") predates Phase 92 but violates the same
  contract; fix alongside WD-12 if cheap.
- `RuntimeDocsPage` `<ol>` styling gap predates Phase 92.
- `RunsOnPicker.swift` 52–70 stale indentation after a removed wrapper —
  cosmetic, fold into N-08's edit.
- `WorkbenchPage.tsx` `apiFetch<any>` usages — type hygiene, not UI; fold into
  WP-01/02/03 edits only if trivial.

## Remediation rules (what the fixes converge on)

1. **One panel chrome per client.** Web desk panels share the `.desk-pullout`
   values (18px radius, 64px top clearance, accent left border, solid fill,
   `blur(10px)`, the established shadow, part classes, one close affordance)
   via a shared base class; Dio sheets share the `DioActSheet` container and
   header/Cancel anatomy.
2. **Tokens or nothing.** No undefined custom properties, no raw hex/px where
   a token exists, no new alpha-notation styles.
3. **One component per concept.** Posture, egress, destination class, recovery
   cards, and facts lists each render through exactly one shared component per
   client, fed by `productLanguage.ts` / `ProductLanguage`.
4. **Copy stays operational.** No raw wire values, no anthropomorphism, no
   implementation enumerations in permanent chrome; details live behind the
   existing disclosure/inspector layers.
5. **Scale and scope.** Desk CSS stays scoped under `.desk-next`; z-indexes
   stay in the documented band; fixed dimensions give way to relative caps.
