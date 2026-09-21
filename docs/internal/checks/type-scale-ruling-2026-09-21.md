# HS-202-05: The type-scale ruling

**Status: RATIFIED AND BUILT.** Astra, 2026-09-21 (proposal); ratified by
Muad'Dib on the owner's behalf the same day (see "Ruling" at the end);
built under [HS-202-05](../../../pm/roadmap/holdspeak/phase-202-the-coherent-face/story-05-the-type-scale-ruling-then-the-tokens.md).
The owner may overrule the look at his sitting.

The rules now live in canon: [UX-CANON C and D](../UX-CANON.md#c-the-type-steps-the-interior-canon)
and [DESIGN_SYSTEM](../DESIGN_SYSTEM.md#the-type-scale-ruling-hs-202-05).
Canon is what a face is measured against; this document is the record of
how the ruling was reached.

Two things the build changed after ratification, both recorded in the
story's counsel rounds:

- §3 says "each dense library Button" and the first canon draft said
  "each library Button". Canon now says each PLATED Button. A chrome
  Button is a strip row and takes its target from the strip's row
  height; a halo there would reach over its neighbours.
- §4 expected the 126 ember observations to stay a ledger. On the
  first-use screens they did not: every text pair on an accent fill is
  gated now, and `--accent-ink` was added so the filled Button and the
  Talk key pass. Off-path ember pairs remain a ledger.

## 1. The conflict

[UX-CANON C](../UX-CANON.md#c-the-type-steps-the-interior-canon) permits 11 px captions.
The census M7 check records every text element below its 12 px floor.
The rulebook says **body text**, but the check also counts captions and glyphs.
[DESIGN_SYSTEM](../DESIGN_SYSTEM.md#the-interior-type-scale) permits display, body, and mono roles.
[M10](../surface-inventory-2026-09-20/00-rulebook.md#b-measured-the-walk-asserts-these-with-numbers) permits two stacks: body and mono.
These conflicts require a ruling before implementation.

## 2. The measured truth

Source: [census.json](../surface-inventory-2026-09-20/census.json), head `93f9524f`, 2026-09-20.
A leg is one face, desk state, and width. Counts include repeated observations.
They are not counts of unique controls or current measurements at `10e22669`.
The tables retain the census face IDs for exact lookup.

Coverage: 100 face IDs, 287 measured legs, 57 unopened legs. M8 excludes 48 image/gradient leaves.

`px×n` gives size and count. Sample uses come from text and DOM paths, not stored semantic roles.
Pairs P01–P13 are defined below. A dash means no recorded failure. Unopened is not a pass.

| Face ID | Measured/unopened legs | M7 sizes: px×n | Sample use by size | M7 targets at 393 | M8 pair×n |
| --- | --- | --- | --- | ---: | --- |
| `state-first-sentence` | 2/0 | 10×2 | 10: caption “Voice typing” | 4 | P11×4 |
| `app-chair` | 4/0 | 9×4, 10×212, 11×144 | 9: control “Talk”; 10: text “OFF”, token “RAN”; 11: glyph “●”, control “Open” | 46 | P05×8 |
| `app-floor` | 4/0 | 10×141, 11×63 | 10: glyph “↑”, control “⌘K”; 11: glyph “[ ]” | 116 | P07×5, P09×63, P10×2 |
| `app-places` | 4/0 | — | — | 4 | — |
| `app-speak` | 4/0 | — | — | 4 | — |
| `app-meetings` | 4/0 | — | — | 4 | — |
| `app-agents` | 4/0 | — | — | 4 | — |
| `app-settings` | 4/0 | — | — | 4 | — |
| `app-rhythm` | 4/0 | — | — | 4 | — |
| `app-context` | 4/0 | — | — | 4 | — |
| `app-workbenches` | 4/0 | — | — | 4 | — |
| `app-activity` | 4/0 | — | — | 4 | — |
| `app-desk-memory` | 4/0 | — | — | 4 | — |
| `app-processes` | 4/0 | — | — | 4 | — |
| `app-commands` | 4/0 | — | — | 4 | — |
| `app-models` | 4/0 | — | — | 4 | — |
| `app-connections` | 4/0 | — | — | 4 | — |
| `app-ask` | 4/0 | 9×8, 10×20, 11×8 | 9: control “ASK”, caption “CTX 0.0K/16.4K”; 10: glyph “▤”, caption “GROUNDING”; 11: control “Cancel”, text “NO TRAFFIC” | 12 | P03×4, P13×4 |
| `app-intelligence` | 4/0 | 11×24 | 11: control “Brief” | 18 | P02×4, P13×8 |
| `app-live` | 4/0 | 10×12, 11×8 | 10: text “READY”, caption “Transcript”; 11: glyph “⚙︎”, control “Start meeting” | 8 | P05×4 |
| `app-new-project` | 4/0 | 10×12, 11×44 | 10: token “SIGN IN”; 11: glyph “○”, control “Cancel” | 16 | P05×12, P13×8 |
| `app-people` | 4/0 | — | — | 4 | — |
| `app-components` | 4/0 | 6×8, 9×36, 10×308, 11×184 | 6: stepper glyphs “▲▼”; 9: glyph “*”, caption “CTX”; 10: glyph “—”, token “SET”; 11: glyph “*”, caption “Size” | 82 | P01×2, P05×18, P06×8, P09×20, P13×56 |
| `app-runtime-docs` | 4/0 | 10×16, 11×8 | 10: control “Guide”, caption “Verify”; 11: control “Check readiness” | 12 | — |
| `app-calendar-snapshot` | 0/4 | — | — | unmeasured | — |
| `settings-settings` | 4/0 | 10×16, 11×8 | 10: control “Guide”, caption “Verify”; 11: control “Check readiness” | 12 | — |
| `settings-guide` | 4/0 | 10×16, 11×8 | 10: control “Guide”, caption “Verify”; 11: control “Check readiness” | 12 | — |
| `settings-module-voice` | 0/4 | — | — | unmeasured | — |
| `settings-module-sounds` | 4/0 | 10×12 | 10: control “Guide” | 10 | — |
| `settings-module-wallpaper` | 4/0 | 10×12 | 10: control “Guide” | 10 | — |
| `settings-module-meetings` | 4/0 | 10×12 | 10: control “Guide” | 10 | — |
| `settings-module-rhythm` | 4/0 | 10×12 | 10: control “Guide” | 10 | — |
| `settings-module-models` | 4/0 | 10×12 | 10: control “Guide” | 10 | — |
| `settings-module-assignments` | 0/4 | — | — | unmeasured | — |
| `settings-module-integrations` | 4/0 | 10×12 | 10: control “Guide” | 10 | — |
| `settings-module-system` | 4/0 | 10×12 | 10: control “Guide” | 10 | — |
| `wing-speak-speak` | 4/0 | 9×12, 10×28, 11×64 | 9: control “Open”, caption “Level”; 10: control “Speak”, token “NOT SET”; 11: glyph “·”, control “Choose” | 24 | P05×4, P13×32 |
| `wing-speak-journal` | 4/0 | 10×20, 11×28 | 10: control “Speak”, token “THIS DEVICE”; 11: glyph “⚙︎”, control “ALL” | 28 | — |
| `wing-speak-blocks` | 4/0 | 10×20, 11×20 | 10: control “Speak”, token “THIS DEVICE”; 11: glyph “↻”, control “Export” | 18 | P13×4 |
| `wing-speak-learned` | 4/0 | 10×20, 11×12 | 10: control “Speak”, token “THIS DEVICE”; 11: glyph “⚙︎”, control “Export” | 18 | — |
| `door-speak` | 4/0 | 10×92, 11×84 | 10: glyph “—”, text “ON”; 11: token “0”, glyph “×” | 42 | — |
| `wing-meetings-outcomes` | 4/0 | 10×190, 11×32 | 10: glyph “·”, token “OFF”; 11: glyph “⚙︎”, control “Open” | 30 | P05×2 |
| `wing-meetings-review` | 4/0 | 10×190, 11×24 | 10: glyph “·”, token “OFF”; 11: glyph “⚙︎”, control “Open” | 24 | P05×2 |
| `wing-meetings-record` | 4/0 | 10×22, 11×12 | 10: control “Record”, text “RECORDS”; 11: glyph “⚙︎”, control “Close” | 20 | P05×4, P13×4 |
| `wing-meetings-artifacts` | 4/0 | 10×190, 11×24 | 10: glyph “·”, token “OFF”; 11: glyph “⚙︎”, control “Open” | 24 | P05×2 |
| `door-meetings` | 4/0 | 10×56, 11×12 | 10: caption “Queues”, control “Record”; 11: glyph “↻” | 21 | — |
| `wing-activity-records` | 4/0 | 10×16, 11×12 | 10: control “Rules”, caption “Records”; 11: glyph “⚙︎”, control “Refresh now” | 16 | — |
| `wing-activity-rules` | 4/0 | 10×16, 11×8 | 10: control “Rules”, text “Watching”; 11: glyph “⚙︎”, control “Refresh now” | 14 | — |
| `door-activity` | 4/0 | 10×40, 11×28 | 10: control “Rules”, text “Watching”; 11: glyph “⚙︎”, control “Dry run” | 24 | — |
| `wing-agents-roster` | 4/0 | 10×18, 11×4 | 10: text “OK”, caption “Crew”; 11: glyph “⚙︎” | 11 | P13×8 |
| `wing-agents-delivery` | 4/0 | 10×8, 11×4 | 10: control “Roster”; 11: glyph “⚙︎” | 10 | — |
| `door-agents` | 4/0 | 10×18, 11×4 | 10: text “OK”, caption “Crew”; 11: glyph “⚙︎” | 11 | P13×8 |
| `intel-brief` | 4/0 | 11×24 | 11: control “Brief” | 18 | P02×4, P13×8 |
| `intel-followthrough` | 4/0 | 11×12 | 11: control “Brief” | 10 | — |
| `intel-decisions` | 4/0 | 10×4, 11×24 | 10: text “ALL DECISIONS”; 11: text “WHY”, control “BACK” | 18 | P13×4 |
| `state-trust` | 4/0 | 10×56 | 10: text “Off”, caption “Slack” | 6 | — |
| `state-room` | 4/0 | 10×4, 11×12 | 10: text “THIS DEVICE”, token “SEARCH THE DESK”; 11: control “All” | 11 | — |
| `state-delivery` | 4/0 | 10×20, 11×20 | 10: token “Hub”, caption “owner/repo”; 11: glyph “↻”, token “UNGATED” | 10 | P08×4 |
| `state-terminal` | 4/0 | 9×4, 11×4 | 9: control “SPAWN”; 11: control “ccgram · zsh” | 6 | P12×4 |
| `state-go-menu` | 4/0 | 10×52 | 10: control “1”, glyph “⇧” | 30 | — |
| `state-palette` | 4/0 | 10×140, 11×32 | 10: control “VERB”, text “VERBS”; 11: control “⌘1” | 63 | P05×12, P13×118 |
| `state-create-menu` | 0/4 | — | — | unmeasured | — |
| `state-desk-menu` | 2/2 | 10×16 | 10: control “F”, glyph “⇧” | 0 | — |
| `state-object-menu` | 2/2 | 10×8 | 10: control “F2”, text “Select an object” | 0 | P04×2 |
| `state-window-menu` | 2/2 | 10×24 | 10: control “M”, glyph “`” | 0 | P04×2 |
| `win-system-shade` | 2/2 | 11×2 | 11: text “Missed” | 1 | P09×2 |
| `win-schedule-create` | 4/0 | 10×4, 11×16 | 10: caption “Recording starts on its own ”; 11: glyph “↻”, control “Cancel” | 12 | P05×4 |
| `win-new-workbench` | 4/0 | 10×20 | 10: control “Manual · 2 skills”, caption “START FROM A TEMPLATE” | 4 | P09×16 |
| `win-list-view` | 0/4 | — | — | unmeasured | — |
| `page-welcome` | 4/0 | 10×4 | 10: caption “Voice typing” | 10 | — |
| `page-presence` | 4/0 | 10×4 | 10: text “Ready” | 2 | — |
| `win-expose` | 0/4 | — | — | unmeasured | — |
| `win-switcher` | 4/0 | 9×4, 10×466, 11×228 | 9: control “Talk”; 10: glyph “·”, token “ON”; 11: glyph “↻”, control “Open” | 134 | P05×10, P10×2 |
| `state-meetings-queued` | 2/0 | — | — | 2 | — |
| `state-thought` | 2/0 | 10×6, 11×6 | 10: text “KEPT”, token “NO ENGINE YET”; 11: control “Change”, caption “ONE QUESTION” | 6 | P05×2, P09×4 |
| `state-interview` | 0/2 | — | — | unmeasured | — |
| `win-workbench` | 2/0 | 10×22, 10.83×2, 11×2 | 10: control “P3”, caption “AGENT”; 10.83: control “· Bind an agent first”; 11: text “No items” | 24 | P05×2, P13×2 |
| `win-repository` | 2/0 | 10×16, 11×10 | 10: glyph “↑”, control “PRs”; 11: glyph “↻”, control “root” | 12 | P02×4, P07×2 |
| `win-roadmap` | 0/2 | — | — | unmeasured | — |
| `win-thought-workspace` | 1/1 | 10×3, 11×3 | 10: text “KEPT”, token “NO ENGINE YET”; 11: control “Change”, caption “ONE QUESTION” | 0 | P05×1, P09×2 |
| `pullout-meeting` | 2/0 | 10×12, 11×2 | 10: caption “Zone”, control “INGEST”; 11: control “Review meeting” | 20 | P13×6 |
| `pullout-note` | 2/0 | 10×6, 11×6 | 10: text “KEPT”, token “NO ENGINE YET”; 11: control “Change”, caption “ONE QUESTION” | 6 | P05×2, P09×4 |
| `pullout-thread` | 2/0 | 11×14 | 11: control “CALL” | 12 | P13×4 |
| `pullout-kb` | 0/2 | — | — | unmeasured | — |
| `pullout-decision` | 0/2 | — | — | unmeasured | — |
| `pullout-recipe` | 0/2 | — | — | unmeasured | — |
| `pullout-workflow` | 2/0 | 10×8, 11×6 | 10: caption “Zone”; 11: control “Edit” | 23 | P05×4, P13×6 |
| `pullout-chain` | 0/2 | — | — | unmeasured | — |
| `pullout-directory` | 0/2 | — | — | unmeasured | — |
| `pullout-artifact` | 2/0 | 10×8 | 10: caption “Zone” | 19 | P13×6 |
| `pullout-people` | 2/0 | — | — | 3 | P05×2 |
| `pullout-intelligence` | 2/0 | 10×2, 11×10 | 10: text “ALL DECISIONS”; 11: text “WHY”, control “Brief” | 8 | P13×2 |
| `pullout-project` | 2/0 | 10×80, 11×156 | 10: control “Room”, token “ON TRACK”; 11: glyph “↻”, control “Choose” | 41 | P05×2, P13×1 |
| `pullout-workbench` | 2/0 | 10×22, 10.83×2, 11×2 | 10: control “P3”, caption “AGENT”; 10.83: control “· Bind an agent first”; 11: text “No items” | 24 | P05×2, P13×2 |
| `pullout-repository` | 2/0 | 10×16, 11×10 | 10: glyph “↑”, control “PRs”; 11: glyph “↻”, control “root” | 12 | P02×4, P07×2 |
| `pullout-roadmap` | 0/2 | — | — | unmeasured | — |
| `pullout-coder` | 0/2 | — | — | unmeasured | — |
| `pullout-story` | 0/2 | — | — | unmeasured | — |
| `pullout-game` | 0/2 | — | — | unmeasured | — |
| `pullout-layout` | 0/2 | — | — | unmeasured | — |

All recorded failing pairs require 4.5:1. Shortfall is `4.5 − recorded ratio`, in ratio points.

| Pair | Foreground | Background | Ratio | Shortfall | Observations |
| --- | --- | --- | ---: | ---: | ---: |
| P01 | `#f2f3f5` | `#bc8058` | 2.97:1 | 1.53 | 2 |
| P02 | `#767e8d` | `#272a32` | 3.50:1 | 1.00 | 16 |
| P03 | `#a86e4a` | `#242833` | 3.50:1 | 1.00 | 4 |
| P04 | `#767e8d` | `#242833` | 3.60:1 | 0.90 | 4 |
| P05 | `#f2f3f5` | `#a86e4a` | 3.79:1 | 0.71 | 99 |
| P06 | `#767e8d` | `#212328` | 3.86:1 | 0.64 | 8 |
| P07 | `#a86e4a` | `#1c1f27` | 3.92:1 | 0.58 | 9 |
| P08 | `#a86e4a` | `#1a1d25` | 4.02:1 | 0.48 | 4 |
| P09 | `#767e8d` | `#1c1f27` | 4.03:1 | 0.47 | 111 |
| P10 | `#ffffff` | `#a86e4a` | 4.20:1 | 0.30 | 4 |
| P11 | `#767e8d` | `#1a1b1f` | 4.21:1 | 0.29 | 4 |
| P12 | `#a86e4a` | `#14161c` | 4.29:1 | 0.21 | 4 |
| P13 | `#767e8d` | `#15171d` | 4.38:1 | 0.12 | 291 |

M10 records stack strings and counts. It does not link each stack to an element.
Display causes below use CSS evidence. They are inferences, not measured role assignments.

| Code | Recorded stack |
| --- | --- |
| M | `"JetBrains Mono", SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", monospace` |
| I | `Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif` |
| D | `"Space Grotesk", Inter, system-ui, -apple-system, "system-ui", "Segoe UI", sans-serif` |
| S | `system-ui, -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif` |
| A | `Arial` |
| m | `"JetBrains Mono", monospace` |
| i | `Inter, system-ui, sans-serif` |

| Face ID | Stack set | Legs | Cause to check |
| --- | --- | ---: | --- |
| `app-chair` | D+M+S | 4 | Display headline (`chair.css:44`) plus system body. |
| `app-floor` | I+M+A | 4 | Arial adds a third stack. Element ownership is not stored. |
| `app-intelligence` | D+M+A | 4 | Display title/count (`intelligence.css:69,195,447`) plus Arial. Check repeated display use. |
| `app-new-project` | M+m+i | 4 | Two mono stack strings plus short Inter. This is not proof of three loaded fonts. |
| `app-components` | I+M+A | 4 | Arial adds a third stack in the component catalog. |
| `wing-speak-speak` | I+M+S+m | 4 | System body and short mono add two stack strings. |
| `wing-meetings-outcomes` | D+I+M | 4 | Display/body/mono. Leading-fact assignment needs a fresh element probe. |
| `intel-brief` | D+M+A | 4 | Same Intelligence selectors. Check repeated display use and Arial. |
| `state-trust` | I+M+A | 4 | Arial adds a third stack. Element ownership is not stored. |
| `page-welcome` | D+I+M+A | 4 | Display plus Arial alongside body/mono. Heading ownership is not stored. |
| `win-switcher` | D+I+M+A+S | 4 | Five stacks in the measured root. Do not assign all stacks to the switcher without an element probe. |
| `state-thought` | D+I+M | 2 | Display/body/mono. Leading-fact assignment needs a fresh element probe. |
| `win-workbench` | I+M+A | 2 | Arial adds a third stack. Element ownership is not stored. |
| `win-thought-workspace` | D+I+M | 1 | Display/body/mono. Leading-fact assignment needs a fresh element probe. |
| `pullout-meeting` | I+M+A | 2 | Arial adds a third stack. Element ownership is not stored. |
| `pullout-note` | D+I+M | 2 | Display/body/mono. Leading-fact assignment needs a fresh element probe. |
| `pullout-thread` | D+I+M | 2 | Display/body/mono. Leading-fact assignment needs a fresh element probe. |
| `pullout-workflow` | I+M+A | 2 | Arial adds a third stack. Element ownership is not stored. |
| `pullout-artifact` | I+M+A | 2 | Arial adds a third stack. Element ownership is not stored. |
| `pullout-project` | D+M+S | 2 | Room headline: `ProjectRoomCore.tsx:260` uses `.surface-display` (`surface.css:654`), plus system body. |
| `pullout-workbench` | I+M+A | 2 | Arial adds a third stack. Element ownership is not stored. |

## 3. The proposed ruling

| Ruling | Tenet |
| --- | --- |
| Set readable text to at least 12 px, including captions, chips, and verbs. Exclude only nontext glyphs with a readable equivalent or an accessible control name. | 1, 3, 7 |
| Keep display/body/mono by role. Permit display once for the leading fact on a Chair, application, or object face. Use body/mono for editors, settings, lists, menus, and chrome. | 5, 6 |
| Raise faint gray to `#8b93a3`. Keep muted gray `#9ba2b0`. Require 4.5:1 for small text on its actual background. | 3, 6, 7 |
| At 393, each dense library Button owns a 44 × 44 px hit area. Use padding or a pseudo-element without enlarging its painted face. | 3, 5, 6 |

Words and numbers are not glyphs. A small status symbol needs a readable equivalent.
Keep disabled controls distinct through their disabled state and flat treatment, not gray differences alone.
Check that treatment after the color change. Keep `--disabled-fg: var(--text-faint)`.

Keep at least three size steps on each window face.
Caption and secondary share 12 px. Weight and spacing distinguish their roles.
Display is a leading fact, not a repeated heading style.

For Button at 393, reserve 44 px targets with `--space-2` gaps (8 px at the standard root).
Allow layout growth. Reject clipped hit areas. No adjacent control may own the same point.
Test the center, edges, and corners with `elementFromPoint` and real pointer activation in an isolated fixture.
Each point must activate the intended Button only. Test clipping and adjacent controls.
A rectangle measurement cannot prove ownership. The text-floor correction is separate from hit-area growth.

## 4. Token changes after ratification

Edit [design-tokens.json](../../../web/design-tokens.json), then run `node web/scripts/generate-tokens.cjs`.
The generator writes [tokens.css](../../../web/src/styles/tokens.css) and `web/src/lib/tokens.gen.ts`.
Do not edit generated files directly.

| JSON entry | Generated CSS | Proposed value or use |
| --- | --- | --- |
| `primitive.color.paper.2.value` | `--p-color-paper-2`, `--text-faint` | `#767e8d` → `#8b93a3` |
| `primitive.color.paper.1.value` | `--p-color-paper-1`, `--text-muted` | Keep `#9ba2b0` |
| `component.groups[name="--desk-surface-label-size"].value` | `--desk-surface-label-size` | `0.6875rem` → `0.75rem` |
| `semantic.groups[name="--font-size-xs"].value` | `--font-size-xs` | Keep `0.75rem`. Use for small readable text and dense Button labels. |
| New `component.groups[name="--desk-button-hit-size"]` | `--desk-button-hit-size` | `44px`. Wire the library Button's transparent hit area in `web/src/styles/global.css:128-153` at the narrow container. Keep its 24/28 px painted heights. Keep `--size-touch: 40px` and `--size-btn: 28px`. |
| New `semantic.groups[name="--font-sans"]` | `--font-sans` | `var(--font-ui)`. Add an explicit project alias. Probe consumers of `font:` shorthand, including `surface.css:2979,3016`: resolution can change size and weight as well as family. |
| `primitive.font.display/ui/mono` and their semantic entries | `--font-display`, `--font-ui`, `--font-mono` | Keep stacks. Replace raw Arial/system and shortened aliases on touched controls. |

Raw 6–11 px declarations do not change when a token changes.
Bind readable consumers to the correct token during the build.
For dense Button, replace the raw 11 px at `global.css:152` with `--font-size-xs`.
At a 16 px root, `0.75rem` is 12 px. Verify computed sizes at both widths.

| Diagnostic | Expected movement after implementation | What remains |
| --- | --- | --- |
| M7: 4,358 small text observations | Falls when caption tokens and raw readable consumers reach 12 px. No exact forecast from this snapshot. | Small glyph artwork remains counted. Existing 12 px mono chips need no size change. |
| M7: 1,350 small rectangles on 140 narrow legs | Padding can reduce the count. | Pseudo-elements can leave rectangles unchanged while hit ownership passes. Raw controls outside this lane remain. |
| M8: 560/8,647 failures | The 434 faint-gray observations would pass at full opacity on their recorded backgrounds, at 4.65:1 or more. | 105 light-on-ember and 21 ember-on-dark observations require separate consumer decisions. They are not fixed by gray. |
| M10: 63 legs over two stacks | Falls when default and shortened stacks are corrected. | Valid display/body/mono remains three stacks. Mono chips retain mono. Stack count alone is not a role verdict. |

The 126 ember failures belong to the HS-202-05 build ledger.
On touched faces, use readable text tokens or a checked Button color pair before closure.
Measure all first-use states. Broad counts remain diagnostics, not gates.

## 5. What stays

Keep the 13/15/26 px steps, mono data, ember palette, window geometry, and glyph artwork.
Do not replace fonts or rebuild unrelated faces to lower a count. This serves Tenet 1.
After ratification, record the rules in UX-CANON and DESIGN_SYSTEM before the build.

Tuesday: the owner must read a label and press its control without a precise tap.
This proposal does not claim that the current face passes that test.

## Verification and limits

| Check or limit | Record |
| --- | --- |
| Data | Astra independently summed the JSON arrays: 4,358 / 1,350 / 560 / 63. Luna supplied the per-face extraction. |
| Color arithmetic | `#8b93a3` on the six recorded gray backgrounds: minimum 4.646:1. This is a calculation, not a fresh render. |
| Historical glass | Read [Chair 1440](../surface-inventory-2026-09-20/assets/01-app-chair-cold-1440.png) and [Chair 393](../surface-inventory-2026-09-20/assets/01-app-chair-cold-393.png). No new shots or hit tests. |
| Skill input | Both requested `.claude/skills/` files are absent here. Muad'Dib read their SKILL.md bodies through his Skill tool and supplied excerpts in the check session. Astra read the token architecture and typography/color excerpts: primitive → semantic → component, 12 px body minimum, semantic colors, 4.5:1 pairs, mono data. Source directories resolve under the main checkout, which Astra did not access. Referenced architecture files and CSVs were not read. |
| Doc checks | `python3 scripts/check_docs.py docs/internal/checks/type-scale-ruling-2026-09-21.md`: 1 file passed. `python3 scripts/check_docs.py`: 70 files passed. Independent JSON-to-table assertions passed. Short sentences and technical terms reviewed under DOCS_STYLE. No claim of certified STE compliance. |
| Inherited ledger | Six `dw check` errors at untouched HEAD: orphan evidence in phase 101 and missing final summaries in phases 152, 153, 154, 156, 200. Existing phase records own these issues. No a/b/c test classification applies: no product tests ran. |
| Build ledger | HS-202-05 retains raw sizes, role ownership, 126 ember failures, first-use AA, and hit testing. No acceptance criterion is waived. |
| Astra ruling on skill guidance | At 393, grow layout for 44 px targets and 8 px gaps. Preserve the current opaque disabled text, semantic attribute, cursor, and flat treatment (`global.css:211-217`). Do not add the generic skill's 0.38–0.5 opacity: it would reduce the measured text contrast. Tenets 1 and 6. Verify disabled states on glass before build closure. |

## Check — Muad'Dib, 2026-09-21

Initial check: **RATIFY-WITH-CONDITIONS**. Session `e6a8f455-1287-4a0d-8e27-7099fdbaf546`.
The table summarizes the check and Astra's response.

| Finding | Response |
| --- | --- |
| Gray totals were wrong. | Corrected to 434 gray, 105 light-on-ember, 21 ember-on-dark, and six gray backgrounds. Direct JSON verification passes. |
| `--size-touch` changes the record glyph, not Button. Tenet 1 risk. | Preserve it. Add `--desk-button-hit-size` and name the Button consumer at `global.css:128-153`. |
| The font alias can change size and weight through shorthand resolution. | Name `surface.css:2979,3016` and require element probes before build closure. |
| At least 56 gray failures occur on library Buttons. Disabled controls may lose distinction from muted text. | Keep the disabled attribute and flat treatment. Require visual state checks. Do not use gray differences alone. Disabled status was not stored by this census. |
| Missing inputs and wider contrast scope. | Skills load in the checker's session. `#8b93a3` on unmeasured `#2d313b` is only 4.21:1. The 4.646:1 result applies to recorded backgrounds only. |
| Conditions before build. | Check disabled states, font alias effects, glyph exclusions, and fresh glass. Preserve the story's AA and hit-test exits. |

### Checker reply

VERDICT: RATIFY. You may publish the PROPOSAL. This is not permission to build, and the owner's ratification is still pending.

FINDINGS:
1. The arithmetic is corrected. §4 now reads 434 gray, 105 light-on-ember, 21 ember-on-dark, 126 remaining and six backgrounds, which matches my recount of the census JSON.
2. The hit-area row is corrected.
   - `--size-touch` stays at 40 and `--size-btn` at 28, and a new `--desk-button-hit-size: 44px` names `global.css:128-153`.
   - The raw 11 px is correctly cited at `global.css:152`.
   - `web/design-tokens.json` has no entry for the new token, which is correct for a proposal.
3. The `--font-sans` alias row names `surface.css:2979,3016` and requires family, size and weight probes.
4. The disabled-state ruling is sufficient for a proposal.
5. `ProjectRoomCore.tsx:260` does carry `.surface-display`, so the `pullout-project` fix is correct.
6. The check record in the document matches what I found.

CONDITIONS: None for the PROPOSAL. The build ledger you recorded stands, plus the two MISSED items below.

MISSED (validate before BUILD):
1. A 44 px hit area around a 24 px painted Button extends 10 px past the face on each side. §3 says "reserve space" but gives no number. The skill asks for a gap of 8 px or more between targets. Dense rows will either grow in layout or have their hit areas clipped. State which one the build accepts.
2. The skill's disabled rule is opacity 0.38–0.5 plus the semantic attribute. "Flat treatment" is not yet measured against that rule.

TUESDAY: Not yet proven. The document says this itself.

UNKNOWN: The items from round one still stand. No product verification was done.

No dissent remains.

## Ruling — Muad'Dib, 2026-09-21

RATIFIED as proposed, on the owner's behalf (his 2026-09-17 ruling: counsel
ratifies the canvas; the owner may overrule at the sitting). The 12 px floor
including captions replaces UX-CANON's 11 px allowance; display/body/mono by
surface kind; `--text-faint` to `#8b93a3`; the dense Button owns 44 × 44 px
at 393 through padding or a pseudo-element, proven by hit testing. The
steps, the ember palette, the fonts and the glyph artwork stay. The 126
ember contrast observations are the build's ledger, decided consumer by
consumer on the touched faces only. UX-CANON and DESIGN_SYSTEM record the
rules before the tokens change.
