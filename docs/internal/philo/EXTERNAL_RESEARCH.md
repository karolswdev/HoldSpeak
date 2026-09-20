# Workbench principles and modern requirements

Research date: 2026-09-20 UTC. This is a design rationale, not evidence that
HoldSpeak meets every requirement. The [SRS](SRS.md) owns proposed requirements.
The Constitution and UX Canon govern HoldSpeak-specific decisions.

## Source provenance

Commodore Electronics published the *Amiga User Interface Style Guide* in 1991.
The inspected [online transcription](https://amigaos.exec.pl/amiga_user_interface_style_guide/index.html)
identifies that edition and links its chapters. It is a hosted transcription,
not a scan authenticated against every printed page. The
[AmigaOS documentation wiki](https://wiki.amigaos.net/wiki/User_Interface_Style_Guide)
also carries the guide, with later updates. Do not describe all wiki wording as
an unchanged 1991 quotation. No original artwork is copied into this package.

## Principle crosswalk

The historical column is a short paraphrase. The adaptation column is the
Philo recommendation. Implementation status comes from the Desk source audit.

| Historical principle | Disposition | HoldSpeak adaptation | Source |
| --- | --- | --- | --- |
| Select the object before its action | Already implemented; audit parity | Keep selection separate from command execution | [GUI basics](https://amigaos.exec.pl/amiga_user_interface_style_guide/basics_of_the_gui.html) |
| Metaphors reduce memorization | Adopt | Use drawers and objects where they explain the task; preserve literal names for technical controls | [GUI basics](https://amigaos.exec.pl/amiga_user_interface_style_guide/basics_of_the_gui.html) |
| Focus and feedback show what happened | Modernize | Distinguish DOM focus, selection and active window; announce meaningful outcomes | [GUI basics](https://amigaos.exec.pl/amiga_user_interface_style_guide/basics_of_the_gui.html) |
| Color supplements other cues | Adopt | Couple status color with a label or shape; verify forced-color behavior | [GUI basics](https://amigaos.exec.pl/amiga_user_interface_style_guide/basics_of_the_gui.html) |
| Raised and recessed controls communicate use | Already implemented in tokens | Preserve the common press geometry; no feature-specific imitation | [GUI basics](https://amigaos.exec.pl/amiga_user_interface_style_guide/basics_of_the_gui.html) |
| Ghost unavailable controls | Modernize | Menus can explain unavailable commands; body content need not display dead verbs | [GUI basics](https://amigaos.exec.pl/amiga_user_interface_style_guide/basics_of_the_gui.html) |
| Fonts and translated text affect geometry | Modernize | Test enlarged text and 30–50% expansion; keep protocol IDs untranslated | [GUI basics](https://amigaos.exec.pl/amiga_user_interface_style_guide/basics_of_the_gui.html) |
| Standard gadgets prevent reinvention | Already implemented; audit exceptions | Extend the Surface library before adding recurring custom controls | [AmigaOS basics](https://wiki.amigaos.net/wiki/UI_Style_Guide_Basics) |
| One selection context avoids ambiguity | Adopt | Define which window or world selection receives a command | [AmigaOS basics](https://wiki.amigaos.net/wiki/UI_Style_Guide_Basics) |
| A title bar provides safe activation | Modernize | Bring a window forward without changing its content selection | [Windows](https://wiki.amigaos.net/wiki/UI_Style_Guide_Windows_and_Requesters) |
| Remember window size and location | Already implemented; audit recovery | Retain normal geometry through maximize/restore and clamp to changed viewports | [Windows](https://wiki.amigaos.net/wiki/UI_Style_Guide_Windows_and_Requesters) |
| Zoom restores the previous geometry | Already implemented | Specify round-trip geometry precisely in the shared frame | [Windows](https://wiki.amigaos.net/wiki/UI_Style_Guide_Windows_and_Requesters) |
| AppWindows expose drop regions | Modernize | Use the declared drop matrix and an equivalent menu operation | [Windows](https://wiki.amigaos.net/wiki/UI_Style_Guide_Windows_and_Requesters) |
| Small screens are a compatibility test | Modernize | Use 393 CSS-pixel and narrow-container fixtures, not literal 640×200 layouts | [Windows](https://wiki.amigaos.net/wiki/UI_Style_Guide_Windows_and_Requesters) |
| Requesters can constrain a user | Reject product-modal adaptation | HoldSpeak's stronger no-modal rule selects inline editing or nonmodal Desk windows | [Windows](https://wiki.amigaos.net/wiki/UI_Style_Guide_Windows_and_Requesters) |
| Menus expose commands without permanent clutter | Adopt | Derive menus, palette and shortcut help from the same verb definitions | [Menus](https://wiki.amigaos.net/wiki/UI_Style_Guide_Menus) |
| Release and cancel have distinct meanings | Modernize | Commit over a valid target; Escape cancels; preserve source until the operation succeeds | [Gadgets](https://wiki.amigaos.net/wiki/UI_Style_Guide_Gadgets) |
| Icons have distinct selection images | Already implemented | Use current HoldSpeak sprites and state assets; do not redraw historical trademarks | [Icons](https://amigaos.exec.pl/amiga_user_interface_style_guide/icons.html) |
| Keyboard shortcuts need consistent meaning | Modernize | Specify platform modifiers and browser conflicts; dispatch existing commands | [Keyboard](https://wiki.amigaos.net/wiki/UI_Style_Guide_Keyboard) |
| GUI, Shell and ARexx are complementary | Modernize | Voice, GUI, HTTP and MCP should share domain operations without sharing all rights | [Shell](https://wiki.amigaos.net/wiki/UI_Style_Guide_Shell) |
| Preferences should not become a burden | Adopt | Expose useful choices; keep advanced configuration subordinate to the first task | [Preferences](https://amigaos.exec.pl/amiga_user_interface_style_guide/prefs_in_moderation.html) |

These dispositions concern behavior. They do not prescribe another component
framework or a retro skin. Current contracts remain in
[Desk grammar](../DESK_GRAMMAR.md), [design system](../DESIGN_SYSTEM.md), and
[surface contract](../../../web/src/desk/surface/contract.md).

## Accessibility acceptance sources

WCAG 2.2 is a testable web-content standard with A, AA and AAA levels. The SRS
uses AA as its target; this package does not claim product conformance.
Automation alone cannot establish complete-process conformance.
[W3C recommendation](https://www.w3.org/TR/WCAG22/)

| Requirement | Interpretation for the Desk | Acceptance method |
| --- | --- | --- |
| [2.5.7 Dragging Movements](https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements.html) | Supply a single-pointer operation without dragging, unless an applicable exception is established. Keyboard support alone does not meet this pointer criterion. | Complete filing, grounding, move/resize and ordering jobs with click/tap controls; document genuine exceptions. |
| [2.5.8 Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html) | Use 24×24 CSS pixels or satisfy a specified exception such as spacing. A tiny visual glyph can have a larger hit region. | Measure target rectangles and spacing at supported scales. |
| [2.4.11 Focus Not Obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) | At AA, authored content must not entirely hide the focused component. Full visibility is a stronger product target. | Tab through overlapping windows, menus and sheets; assert visibility and manually inspect. |

The proposed 44-pixel frequent-touch target is a HoldSpeak design choice. Do
not describe it as the default AA minimum. Test zoom/reflow, reading order,
accessible names, status announcements, keyboard alternatives and contrast in
addition to these three criteria. Screen-reader and motor-access walks remain
manual evidence obligations.

## Component taxonomy and library decision

[Atomic Design](https://atomicdesign.bradfrost.com/chapter-2/) describes atoms,
molecules, organisms, templates and pages as related levels. Philo uses these
as catalogue labels. Foundations are an added token category. No folder rewrite
or alternate component API follows from that taxonomy.

[React Aria](https://react-aria.adobe.com/) provides accessible React components
and interaction utilities. It is a candidate for a demonstrated composite-widget
gap, not an automatic dependency. Require a prototype behind the existing
Surface component API, parity tests and an explicit decision before adoption.
No new headless library is introduced by this documentation package.

## Desktop sources

Electron's [process model](https://www.electronjs.org/docs/latest/tutorial/process-model)
separates main, renderer and preload responsibilities. Its
[security guidance](https://www.electronjs.org/docs/latest/tutorial/security)
supports restricted navigation, sandboxing, context isolation and narrow IPC.
These are design constraints for a host experiment, not proof that a proposed
wrapper is secure.

Tauri's [architecture](https://v2.tauri.app/concept/architecture/) uses a native
core and system WebView. Its [capability model](https://v2.tauri.app/security/capabilities/)
scopes accessible commands by window/webview and permission. Multiple grants
must be reviewed together. No renderer should receive a generic shell bridge.

The [desktop ADR](adr/desktop-host.md) records the comparison and evidence
required before choosing a host. Browser operation remains the reference.
