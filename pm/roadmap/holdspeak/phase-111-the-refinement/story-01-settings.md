# HS-111-01 - Settings

- **Project:** holdspeak
- **Phase:** 111
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-111-10
- **Owner:** unassigned

## The thesis (the bar)

The owner named this program first: "The Settings screen needs to be
completely rethought." Not token-tweaked — rethought. Today it is a
SaaS preferences page (sidebar nav, rounded toggles, Inter body,
airy grouped cards) living inside a Signal Workbench window. The bar:
**Settings reads as the OS's own Prefs program — the structural
grammar of Workbench 2.0 Prefs, rendered dark, dense, and 2004-techy.**
Every pane: Appearance, Hotkey, Transcription, Voice Typing, Wake
Word, Presence, Meetings, Cadence, Devices, Delivery, Models,
Integrations.

## Method (phase canon)

1. **Audit.** An agent walks every pane of the current Settings
   interior — every component, layout decision, and control — and
   files what speaks SaaS versus what speaks Workbench.
2. **Rethink.** The agent proposes the native interior: layout,
   density, control style, typography. The measuring question:
   *"If this OS shipped on a CD-ROM in 2004 with this dark techy
   aesthetic, what would its Prefs program look like?"* Bevels are
   the depth grammar; JetBrains Mono is the chrome voice; 2px is the
   only radius.
3. **Implement.** In `web/src` (source only — the bundle is
   gitignored).
4. **Prove.** Live Playwright screenshots of every pane against the
   real hub, 1440 and 393 viewports.

## Test plan

- Open Settings on the real desk: no rounded toggle switches, no
  frosted or floating cards, no Inter section labels.
- Every pane renders in the Signal Workbench control language
  (beveled gadgets, etched groups, full-width hover bands).
- Navigation between panes reads as a program, not a website sidebar.
- Screenshot walk at 1440 and 393 shows no overflow or clipped
  controls on any pane.
