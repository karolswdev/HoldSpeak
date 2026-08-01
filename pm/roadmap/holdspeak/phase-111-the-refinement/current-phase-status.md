# Phase 111 - The Refinement

**Status:** IN PROGRESS (2/10). Chartered 2026-07-31 as the mandatory
fast-follow to Phase 110. The owner's condition: every program on the
desk gets its interior rethought — not token-tweaked, RETHOUGHT — to
feel native to Signal Workbench. "The Settings screen needs to be
completely rethought, and many, many others."

**Last updated:** 2026-08-01 (HS-111-02 Speak SHIPPED — the dictation
deck: instrument strip with TALK/LedMeter/STATE register, the journal
as a machine ledger (SurfaceLedger), the correction ritual as an
in-place gadget sheet, the door on the gadget sheet, every toast dead
into the footer receipt bar; four new kit species for 03-08; full
suites green 4207+387. Earlier the same day: HS-111-01 Settings
SHIPPED — the Prefs rethink + the reusable gadget kit.)

## Why this phase exists

Phase 110 replaced the material model at the chrome level: windows,
bars, tokens. But every program on the desk still has its web-app
interior. A Settings page with Inter body text, rounded toggle
switches, and a sidebar navigation layout that says "SaaS dashboard"
sits inside a window that says "Workbench." The chrome is right; the
programs are not.

This phase sends agents into each program to audit what it looks and
feels like, then rethinks the interior to feel native. The question
for each program: **"If this OS shipped on a CD-ROM in 2004 with this
dark techy aesthetic, what would this program look like?"**

## Method

Each story:
1. An agent audits the program's current interior — every component,
   every layout decision, every control
2. The agent proposes what needs to change to feel native (not just
   "apply tokens" — rethink layout, density, control style, typography)
3. Implementation
4. Screenshot proof on the real desk

## Stories

| # | Story | Program / surface | Status |
|---|-------|-------------------|--------|
| 01 | [Settings](./story-01-settings.md) | The Settings program — every pane (Appearance, Hotkey, Transcription, Voice Typing, Wake Word, Presence, Meetings, Cadence, Devices, Delivery, Models, Integrations) | done |
| 02 | [Speak](./story-02-speak.md) | The Speak/Dictation program — the dictation cockpit, journal, correction memory, pipeline config | done |
| 03 | [Meetings](./story-03-meetings.md) | The Meetings program — history list, meeting detail, transcript view, artifact cards, aftercare panel | backlog |
| 04 | [Agents](./story-04-agents.md) | The Agents/Companion program — agent list, persona detail, session inspector, coder steering pullout | backlog |
| 05 | [Ask and conversation](./story-05-ask-conversation.md) | The Ask composer, grounding picker, conversation thread, kept-card receipts | backlog |
| 06 | [Delivery and process](./story-06-delivery-process.md) | The delivery belt, the process window, the project memory window — the kernel-facing programs | backlog |
| 07 | [System chrome](./story-07-system-chrome.md) | Dropdown menus (Desk/Object/Go), context menus, the search palette (Cmd+K), the shortcut sheet, popovers | backlog |
| 08 | [Interactive elements](./story-08-interactive-elements.md) | Every control type across all programs: toggles, selects, inputs, tabs, pills, buttons, badges — one kit, one language | backlog |
| 09 | [Sprite and icon quality](./story-09-sprites.md) | Regenerate bad dock sprites on the real desk, window type icons, overview/reset glyphs | backlog |
| 10 | [The refinement walk](./story-10-walk.md) | Open every program, screenshot at both viewports, prove every room speaks one language | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-111-01 | Settings | done | [story-01-settings](./story-01-settings.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-111-02 | Speak | done | [story-02-speak](./story-02-speak.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-111-03 | Meetings | backlog | [story-03-meetings](./story-03-meetings.md) | — |
| HS-111-04 | Agents | backlog | [story-04-agents](./story-04-agents.md) | — |
| HS-111-05 | Ask and conversation | backlog | [story-05-ask-conversation](./story-05-ask-conversation.md) | — |
| HS-111-06 | Delivery and process | backlog | [story-06-delivery-process](./story-06-delivery-process.md) | — |
| HS-111-07 | System chrome | backlog | [story-07-system-chrome](./story-07-system-chrome.md) | — |
| HS-111-08 | Interactive elements | backlog | [story-08-interactive-elements](./story-08-interactive-elements.md) | — |
| HS-111-09 | Sprite and icon quality | backlog | [story-09-sprites](./story-09-sprites.md) | — |
| HS-111-10 | The refinement walk | backlog | [story-10-walk](./story-10-walk.md) | — |

## Where we are

1/10. HS-111-01 (Settings, the owner-named first target) shipped
2026-08-01: the audit ruled the program a JSON mirror wearing a SaaS
sidebar; the rethink made it the OS's own Prefs program — an
icon-grid drawer face, an authored module roster (the wire can never
mint a pane again; unmapped keys land in the one System module), a
footer receipt bar (`USING · WRITTEN hh:mm:ss`), and a REUSABLE
gadget kit (CheckGadget/CycleGadget/MxRadio/StringGadget/Stepper/
Prop/GadgetTable/SecretRow) built in the surface kit — stories 02-08
consume it, and the sliding-switch species is dead desk-wide. Proven
live at 1440+393 on the real hub; web check 65 files / 380 tests
green. Held for follow-ups: audio-device-list endpoint (Meetings
pickers), per-section defaults source (DEFAULTS verb ships disabled),
delivery keys under `/api/settings`.

2/10. HS-111-02 (Speak) shipped the same day: the audit ruled the
flagship a web form in a void (textarea + button + 70% empty face,
state narrated by a glowing mic and toast banners); the rethink made
it the OS's dictation deck — a sunken instrument strip (TALK
momentary key with inverted-video held state, a real-RMS LedMeter, a
named STATE register, etched pipeline/target/budget readouts), the
journal as a columnar machine ledger with open-in-place rows, the
correction ritual as a gadget sheet extending the receipt, the gear
door recomposed onto the gadget sheet (the Hooks JSON dump is now a
designed face), and every InlineMessage dead into the footer
receipt/refusal bar. Kit grew four species for 03-08: LedMeter,
LampGadget, TransportKey/TransportRow, GadgetTable verbs slot, plus
SurfaceLedger in the surface kit. Five python guards re-pointed
honestly (trust-signals now asserts the banner species stays dead).
Proven live at 1440+393; full suites green (4207 python + 387 web).
Next: HS-111-03 (Meetings) — transport keys and ledgers are on the
shelf.
