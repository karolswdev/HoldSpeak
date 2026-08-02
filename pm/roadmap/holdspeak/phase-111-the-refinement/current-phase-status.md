# Phase 111 - The Refinement

**Status:** IN PROGRESS (7/11). Chartered 2026-07-31 as the mandatory
fast-follow to Phase 110. The owner's condition: every program on the
desk gets its interior rethought — not token-tweaked, RETHOUGHT — to
feel native to Signal Workbench. "The Settings screen needs to be
completely rethought, and many, many others."

**Last updated:** 2026-08-02 (HS-111-07 System chrome SHIPPED — the
biggest room: WorkMenu v2 species (the z bug dead — dropdowns draw
OVER windows), the five parallel verb lists collapsed into ONE
registry + keymap (doctrine P2/P11 now law in code), THE FLOOR
RIGHT-CLICK exists (NEW>/LAUNCH>, long-press at 393, nothing
minted), the palette is a command deck (Enter runs the top hit,
ranked), the list view is a SurfaceLedger face, the sheet derives
from the registry, ONE egress species, all four naked-debug sites
behind RAW; suites green 4214+424. Earlier: 06 Delivery/process, 05
Ask, 04 Agents, 03 Meetings, 02 Speak, 01 Settings.)

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
| 03 | [Meetings](./story-03-meetings.md) | The Meetings program — history list, meeting detail, transcript view, artifact cards, aftercare panel | done |
| 04 | [Agents](./story-04-agents.md) | The Agents/Companion program — agent list, persona detail, session inspector, coder steering pullout | done |
| 05 | [Ask and conversation](./story-05-ask-conversation.md) | The Ask composer, grounding picker, conversation thread, kept-card receipts | done |
| 06 | [Delivery and process](./story-06-delivery-process.md) | The delivery belt, the process window, the project memory window — the kernel-facing programs | done |
| 07 | [System chrome](./story-07-system-chrome.md) | Dropdown menus (Desk/Object/Go), context menus, the search palette (Cmd+K), the shortcut sheet, popovers | done |
| 08 | [Interactive elements](./story-08-interactive-elements.md) | Every control type across all programs: toggles, selects, inputs, tabs, pills, buttons, badges — one kit, one language | backlog |
| 09 | [Sprite and icon quality](./story-09-sprites.md) | Regenerate bad dock sprites on the real desk, window type icons, overview/reset glyphs | backlog |
| 10 | [The refinement walk](./story-10-walk.md) | Open every program, screenshot at both viewports, prove every room speaks one language | backlog |
| 11 | [The terminal pane](./story-11-terminal-pane.md) | Owner rider on 04: the pane well becomes a real terminal (xterm.js over a raw peek mode, read-only, consent spine untouched) + utility density | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-111-01 | Settings | done | [story-01-settings](./story-01-settings.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-111-02 | Speak | done | [story-02-speak](./story-02-speak.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-111-03 | Meetings | done | [story-03-meetings](./story-03-meetings.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-111-04 | Agents | done | [story-04-agents](./story-04-agents.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-111-05 | Ask and conversation | done | [story-05-ask-conversation](./story-05-ask-conversation.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-111-06 | Delivery and process | done | [story-06-delivery-process](./story-06-delivery-process.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-111-07 | System chrome | done | [story-07-system-chrome](./story-07-system-chrome.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-111-08 | Interactive elements | backlog | [story-08-interactive-elements](./story-08-interactive-elements.md) | — |
| HS-111-09 | Sprite and icon quality | backlog | [story-09-sprites](./story-09-sprites.md) | — |
| HS-111-10 | The refinement walk | backlog | [story-10-walk](./story-10-walk.md) | — |
| HS-111-11 | The terminal pane | backlog | [story-11-terminal-pane](./story-11-terminal-pane.md) | — |
| HSEGHS001HS104-111-11 | The terminal pane | backlog | [story-11-terminal-pane](./story-11-terminal-pane.md) | - |

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

3/10. HS-111-03 (Meetings) shipped the same day: the audit ruled the
archive a card feed with the record's body buried (the transcript
folded behind a Disclosure while a rounded warn-tinted prose card
owned the pane; plus a real footer/tile overlap bug at 1440); the
rethink made it the tape catalog — History consumes SurfaceLedger
(chronology restored, attention as token tone, states axis-named),
the transcript always visible in the new SurfaceWell species, needs-
you a GadgetTable with APPROVE/REJECT, artifacts stamped as receipts
(ART 03 · DECISION · 21:31), recovery cards dead into a one-row slab
and twin CURRENT/INCOMING slips, exports on the one footer receipt
bar (the overlap retired by construction). LiveCore scope-limited:
SurfaceStream and the one-verb posture byte-untouched. Zero wire
changes; three python locks re-pointed honestly. Proven live at
1440+393; suites green (4207 python + 389 web).

4/10. HS-111-04 (Agents) shipped the same day: the audit ruled the
program three eras stapled together (SaaS empty-state Sessions page,
profile-card directory, messenger-bubble persona chat, glow-ringed
steering chips — including a 2px accent rail smuggled past the
border-left guard as an inset box-shadow); the rethink made it the
crew console — Sessions + Chat collapsed into ONE SurfaceLedger
board (CREW n · SESSIONS n · BLOCKED n, blocked-first, LampGadget
cells, open-in-place ANSWER), persona detail a personnel record over
a SurfaceTraffic transmission log (new kit species: prefixed mono
YOU> / <NAME>> turns, per-reply egress chips), and steering
re-rendered in gadget grammar (ARM a TransportKey with inverted-
video armed state, the TTL countdown a draining LedMeter GRANT,
policy prose as axis-named tokens) with the Phase-87 CONSENT SPINE
BYTE-UNTOUCHED — steering.ts zero diff, steering.test.ts and all
python steering wire tests passed with zero edits. Proven live at
1440+393 (nothing armed or steered during the walk); suites green
(4207 python + 389 web).

5/11. HS-111-05 (Ask) shipped 2026-08-02 (the small hours): the
audit ruled AskPanel a chat app wearing Phase-110 paint and found
the honesty gap — the HS-109-04 grounding receipt parsed off the
wire and rendered NOWHERE — plus a live overflow defect; mid-build
the owner hit the error-tooltip-overlap live and rated the room a
mixed-era joke. The rethink shipped all of it: the thread is
SurfaceTraffic (YOU>/HUB> turns, scanning RX while routing), the
answer turn carries GROUNDED ON N OF M + openable CitationChips
(promoted to the kit, ProjectMemoryCore imports the same species),
every fault is in-flow (receiptbar or error turn — machine-verified
all controls operable in the refusal state at both viewports), zero
naked HTML controls survive, and the rack is one GadgetGroup with
the CTX LedMeter (overflow dead by construction, proven with the
57-char offender). No printed turn was faked — no model was
reachable; the refusal path is the captured proof, and the next
story's walk owes a printed turn once .43 returns.

6/11. HS-111-06 (Delivery and process) shipped 2026-08-02: the audit
found the phase's largest violation (an unbounded ~450 emoji-pin
flood burying the desk at both viewports) and root-caused the
owner's PR-387 duplicate rows LIVE as two wire bugs — the state
sweep ran only as a side effect of one read (liveness-by-gaze:
"starting" persisted for days until someone opened the board) and a
worktree-resolution change defeated the idempotence key, minting a
rider_claim sibling per run. Both fixed on the wire (sweep on the
attempts read path; claims bind/adopt by session) with 7 new tests;
no pre-existing-dirty python touched. The rendering: belt → rails
panel (census tokens, inverted NEEDS YOU as the only individual
layer, zero emoji), process window → zeroed instrument (kernel
consumer files git-diff EMPTY), delivery keypad → TransportRow,
dossier + project memory onto ledgers/tokens/RAW folds, and ONE
PaneWell seam extracted for both terminal surfaces — xterm deferred
to HS-111-11 so story 11 swaps a single interior. Proven live at
1440+393 including the error leg; suites green (4214 python + 398
web).

7/11. HS-111-07 (System chrome) shipped 2026-08-02: the audit found
the chrome half-right in material but fragmented in organs — FIVE
parallel verb lists (why ⌘K couldn't run what the menus could and
Enter dead-ended), no engine miss branch (why the floor had no
right-click), the menubar trapped in a z-30 stacking context under
z-42 windows, the list view naked HTML, two Phase-101 glass relics
(the sheet, the egress pill). Shipped on the audit's ratified cut
line with NOTHING dropped: WorkMenu v2 (one portaled species for
dropdowns + all context menus), registry v2 + desk/keymap.ts as the
only key binder (the five lists grep to zero), the floor
right-click with NEW>/LAUNCH> and honest ghost reasons (the walk
minted a workflow from the floor — the first ever — and binned it),
the command-deck palette (Enter runs the top hit, prefix > recents
> substring, banded ledger rows, in-flow miss leg), the list view a
SurfaceLedger face with window discipline, the sheet opaque AND
derived from registry keys, the egress badge ONE species, the four
naked-debug sites behind RAW wells. Deferred by the honest cut:
palette deep-settings + meeting content search (plug-in points
documented); 08 owns the new faces' roving/arming conformance.
Proven live at 1440+393; suites green (4214 python + 424 web).
Next: HS-111-08 (interactive elements).
