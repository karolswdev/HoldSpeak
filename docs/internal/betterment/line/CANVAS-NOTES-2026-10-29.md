# Line canvas notes (2026-10-29)

Canvas: `canvases/line-2026-10-29.html` (one self-contained page; the
sprites are the desk's own PNGs inlined: `call` 20/64 and `cartridge` 20 from
`web/public/desk/sprites/`, the Settings and Engines title chips from
`system/dock-settings.png` and `settings/models.png`). The CSS is the Phone
canvas's copy of the kit (`phone/canvases/phone-2026-10-28.html`) plus the Line
rows. Shots: `canvases/shots/`. Design: `LINE-DESIGN-2026-10-29.md` §10, the
Calls faces as built (`web/src/desk/calls/CallsSettings.tsx`,
`PhoneSettings.tsx`) and the Engines words (`engineState` in
`web/src/features/runson/RunsOnCore.tsx`). The owner's "go with suggestions"
(2026-10-27) pre-approves the recommended direction; he judges it live on his
desk.

| Shot | What it shows |
|---|---|
| `canvas-1440.png` | The whole page at a 1440 viewport |
| `1440-directions.png` | The open question, A · B · C, the table, the recommendation |
| `1440-settings.png` | Settings ▸ Calls ▸ Line, the three moments |
| `1440-settings-first-run.png` | Nothing installed; the pending verb |
| `1440-settings-ready.png` | Ready on karol, the free SIP address, Test call answered |
| `1440-settings-telnyx.png` | A Telnyx number, the password stored, Test call ringing |
| `1440-states.png` | Every place word and every Test call word |
| `1440-calls-bar.png` | The Calls window's status bar in five states, and the host chip it does not show |
| `1440-engines.png` | The Engines window with the Line's two model rows |
| `1440-empty.png` | The empty states |
| `1440-phone.png` | The three phones together |
| `393-line-ready.png`, `393-line-first-run.png`, `393-calls-no-line.png` | The phones at 393 × 852 |

## The recommendation: A, inside Settings ▸ Calls ▸ Line

The open question was where the Line's account lives (the place it runs, the
SIP address or the Telnyx user and password, Test call).

- **A, Settings ▸ Calls ▸ Line (recommended).** A sub-page of Calls between
  Set up calls and Phone: Where it runs, The line, Test call, From Calls (read
  only), Adapter, and one egress sentence.
- **B, Engines, an engine of kind Line.** One more Engines row, its inspector
  holds the account and Test call.
- **C, Accounts, beside GitHub and Jira.** Telnyx is an account; the password
  joins the keystore rows there.

The reason, in his terms: the Line has one user, Calls. He thinks "set up
calls" and opens Settings ▸ Calls, where the passphrase, his numbers and the
switch already are. B puts a thing that no job is assigned to in the list of
assignable engines, and splits setup across two windows. C has no home for
the free SIP address (it is not an account), which is the line he uses first,
and makes three windows for one line. A adds no window and no new kind
(Tenet 3). The keystore is the same in all three; only the page that writes
to it changes.

## No Line row in Engines (in A)

The design gives Engines two catalog rows, not a Line row (§7): Phone speech
in (Parakeet, 0.6 GB) and Phone voice (Pocket, 0.2 GB), through the
concierge's download path, each with its CC-BY-4.0 line. The canvas draws
them. It does not add the row "The Line · karol · Ready · 0.4 core per call
minute", because:

1. An Engines row is a thing a job is assigned to (Used for, What runs
   where). Nothing is assigned to the Line; Calls picks it in Adapter.
2. The Line's state has two homes already: Settings ▸ Calls ▸ Line and the
   Calls status bar. A third is a second teller.
3. A SIP password is not an engine setting.

Direction B draws that row, so he can see it and overrule.

## Measurements (read from the page with Playwright, 1440 viewport)

| Part | Value |
|---|---|
| Toolbar | 36 px |
| Status bar | 24 px |
| Settings rows (Where it runs, The line, Test call, Adapter) | 32 px |
| From Calls rows | 30 px |
| Engines rows | 30 px |
| Scroll overflow in every window body and phone page | 0 px |
| Horizontal overflow in any row | none |
| Text under 12 px in a window | none |
| Page | no horizontal scroll at 1440 (scrollWidth 1440) |
| At 393 | every verb 44 px high (Copy 65 × 44, Test call 86 × 44, Install the Line on karol 188 × 44, Call me 101 × 44, Set up the Line › 143 × 44); folded rows 56–95 px |

## The kit pieces each part is made of

| Part | Kit pieces |
|---|---|
| Settings ▸ Calls ▸ Line | the Accounts grammar of `CallsSettings.tsx` / `PhoneSettings.tsx`: `GadgetGroup material="inset"` per group (Where it runs, The line, Test call, From Calls, Adapter); rows name · fact · state · verb; `DotWord` for each state; `Button` dense for Copy, Test call, Change, Cancel, Install the Line on karol (primary); the egress sentence once (`calls-egress` class) |
| Where it runs | a radio per place (`MxRadio`, one group); the 20 px `cartridge` sprite (`spriteUrl("model", …, 20)`, the Engines row's sprite); the place name; a muted fact (the measured core per call minute); `DotWord` with the Engines words; `CommandWell` for the Mac's command with Copy |
| The line | a radio per kind (`MxRadio`); the address in mono (code only) with Copy; `StringGadget` for User, Domain, Number; `StringGadget type="password"` for the password, write only (the `PassphraseField` pattern); "Stored in your keystore" as a `DotWord` with Change; the codecs as one muted line |
| Test call | the 20 px `call` sprite; the target; `DotWord` (Ringing is `live`, the kit breath); `Button` Test call (hover title "From the Line on karol") / Cancel while ringing |
| From Calls | read-only rows (the `calls-may-row` pattern): Daily limit, First words out, Never dialled |
| Adapter | `MxRadio` of two: The Line · ai-phone ("Optional, AGPL, runs as a separate program") with a `DotWord` each |
| Calls window status bar | `StatusBar` items (lamp + text): Ready for calls (ok), Line starting (info, live), No line: set one in Settings ▸ Calls ▸ Line (idle), Line not running (warn), On a call · 2:14 (as built) |
| Engines | `ObjectList` dense rows (as built), two new catalog rows with the `cartridge` sprite |
| Empty, Calls window | `SurfaceState` empty, the 64 px `call` sprite, "No line yet", one line, primary `Button` Set up the Line › (`openSurfaceOr` to Settings ▸ Calls ▸ Line); Call me off |
| Empty, Test call | the row with "No number" and the verb off |
| 393 | the rows fold (name and verb on line one, fact and state under it); verbs 44 px; the page scrolls |

New for LINE-4 (none is a new species): `LineSettings.tsx` beside
`PhoneSettings.tsx`, the Line rows' CSS, and the words below in `stateWords`.
A dedicated `line` sprite (a cartridge with a handset) is a gap if he wants
one; the canvas uses the Engines cartridge.

## Words used on the faces (for `stateWords` and the copy guard)

Place: Ready, Starting, Downloading N %, Not running, Not installed, Not set
up, Offline. Line: Listening, Registered, Needs a place. Test call: Ringing,
Answered · m:ss, No answer, Rejected, Line not running, Busy, No number.
Password: Stored in your keystore. Adapter: In use. Status bar: Ready for
calls, Line starting, No line: set one in Settings ▸ Calls ▸ Line, Line not
running, On a call. Verbs: Copy, Test call, Cancel, Change, Install the Line
on karol, Set up the Line ›.

## Small choices the canvas made (say if another is wanted)

- The status bar keeps "Line not running" (the design's word) for a line that
  is set up but down, and adds "No line: set one in Settings ▸ Calls ▸ Line"
  for a desk with no place. They are different repairs.
- The LINE-1 brief asked for "Line on karol · ready" on the status bar; the design (§10) flagged it, because UX-CANON A.9
  forbids a host chip there, so karol is named only in Settings ▸ Calls ▸ Line
  and as the hover title on Test call. The canvas draws the forbidden form
  struck through, so he can overrule.
- Each place shows its measured cost (about 0.13 core per call minute on the
  Mac, 0.4 on karol, §12) as a muted fact. An architect picks a place on cost.
- The first-run row for karol says what the press does: "Builds baresip 4.12
  in ~/holdspeak-line on karol. No sudo. About 1 min and 3 GB."
- The daily limit, the first words and the emergency rule are read only here;
  they are set in Calls.

## What the canvas could not establish

- Install the Line on karol is a pending verb (an orange dashed mark on the
  canvas only): the enrolment is LINE-3. The canvas assumes karol is already
  a linked node of the hub, so it is listed before the Line is on it.
- The Telnyx shape is from the design's §8 and is not verified; the account
  does not exist. The password custody needs the owner's word (CONFIG, §14).
- The SIP app's address (`sip:karol@karol-iphone`) is drawn, not read from
  his app.
- The desk floor is CSS, not a recorded hub shot. No product guard reads
  `docs/` canvases, so the copy here is proven by reading.
