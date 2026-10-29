# Phone canvas notes (2026-10-28)

Canvas: `canvases/phone-2026-10-28.html` (one self-contained page; the
sprites are the desk's own PNGs inlined, the QR is a real code made with
`qrcode-generator` 2.0.4, MIT). Shots: `canvases/shots/` (`canvas-1440.png`
is the whole page at a 1440 viewport; `1440-<section>.png` per section;
`393-phone-wing.png`, `393-settings-phone.png`, `393-needs-you.png` are the
phones at 393 × 852). Design: `PHONE-DESIGN-2026-10-28.md` §9. The owner's
"go with suggestions" (2026-10-27) pre-approves the recommended direction;
he judges it live on his desk.

## The recommendation: A, a wing of the Calls window

The open question was where the thread lives (the messages between the desk
and his phone, the calls the desk made, the paired phone).

- **A, a wing of the Calls window (recommended).** The Calls window takes
  the wings species (`surface/wings.tsx`): Calls · Phone. The Phone wing is
  the thread with a mic composer at its foot and a 300 px rail (From the
  desk: the calls the desk made; Your phone: the paired device).
- **B, its own Phone window.** A new app in Go and on the dock.
- **C, a drawer like Needs you.** Over every window, a second badge in the
  menu bar.

The reason, in his terms: he thinks "the desk called me" and opens Calls.
On the number transport every desk call is a Calls call already
(`phone_calls.calls_turn_id`), so B shows each call in two windows, and C
is a second Needs you for the replies that already are Needs you rows. A
adds no app, no drawer, no badge (Tenet 3).

## Measurements (read from the page with Playwright, 1440 viewport)

| Part | Value |
|---|---|
| Toolbar | 36 px |
| Status bar | 24 px |
| Thread message line | 44 px one line, 61–63 px two lines (time 44 px column · who · words; receipt at the right) |
| Desk call line in the thread | 32 px (sprite 20, words, DotWord, one Button) |
| Settings rows | 32 px (name · state · verb); Reach you cells 30 px |
| Needs you row | 51 px (name + fact two lines, verbs `sm`) |
| Scroll overflow in every window body | 0 px |
| At 393 | every verb 44 px high (Message 112 × 44, Call me 101 × 44, Call again 88 × 44, mic 44 × 44, Send 89 × 44, Remove 76 × 44, Call now 91 × 44, Let it wait 98 × 44, Answer here 119 × 44); Reach you radio cells 56 × 44 |
| Page | no horizontal scroll at 1440 (scrollWidth 1440) |

Type: title bar 13.5/600; a row's name 13/500–600 (14 at 393); body 13;
metadata 12 sans muted in sentence case; mono only for code. The empty
state's line is 15/600.

## The kit pieces each part is made of

| Part | Kit pieces |
|---|---|
| The Calls window | the window frame, `SurfaceWings` (Calls · Phone; the Phone tab carries the ember count only when a message waits for his reply), `Toolbar` (Message primary, Call me secondary), `StatusBar` (dot + word) |
| The thread | the `LiveTranscript` grammar (time · who · words) in a list, `DotWord` for Sent · Delivered · Read · Answered · Missed (through `stateWords`), the reply's elbow rule (the race-row elbow of the Programs board), the ember rule on a message that waits (the AskWell family), a ghost link Button "from <Program>" |
| A desk call line | 20 px `call` sprite, `DotWord`, `Button` Open transcript / Call again |
| The composer | `ComposerWell` with `PadGadget` (its mic) and `Button` Send; "Goes to <phone>" in the context slot |
| The rail | `ObjectList` dense rows (From the desk), a device row (handset object, name, Paired date · seen, `DotWord`) |
| Settings ▸ Calls ▸ Phone | the Accounts grammar: `GadgetGroup material="inset"` per group (Your phone, Reach you, Quiet hours, The number), rows name · state · verb; the QR sheet in place under its row (no modal); Reach you a table of radios (one radio group per kind, Message · Call · Nothing) with "Set by Control: <level>" and "Use the <level> set"; `StringGadget` time fields; `CheckGadget` for Quiet hours and Urgent (disabled until the entitlement, with the words of what happens until then); the egress sentence once |
| Empty | `SurfaceState` empty, the 64 px `call` sprite, "No phone yet", "Pair a phone, or add a number in Calls, and the desk can reach you.", primary Pair a phone |
| Needs you | `NeedsRow` (group Phone, dotState), verbs Call now / Let it wait and Call again / Answer here |
| Today | one row in Since this morning: "Reached you 2 times: 1 answered" (only when not zero), opens Calls on the Phone wing |
| Program window | one Reach line under Decided for you: time · "Reached you: called about <q> · answered · you said yes" · Open transcript |
| 393 | the rail folds away (desk calls are thread lines; the device lives in Settings); plated Buttons own 44 × 44; Needs you verbs go under the words |

## Words used on the faces (for `stateWords` and the copy guard)

Message: Sent, Delivered, Read, Waits for you. Call: Ringing, Answered,
Missed, Declined, Ended, urgent. Device: Pairing, Paired, Removed. Verbs:
Message, Call me, Send, Open transcript, Call again, Call now, Let it wait,
Answer here, Pair a phone, New code, Cancel, Remove, Use the Normal set,
Set up calls ›. Lines: "Asked on your phone · 12 min · no reply",
"Missed call: <reason>", "Reached you 2 times: 1 answered", "A reply is
waiting on you", "No phone paired", "Your phone is paired", "Waiting for
your phone".

## Small choices the canvas made (say if another is wanted)

- The device is removed with **Remove** (the Accounts word), not Revoke.
- The thread is the transcript grammar, not chat bubbles, so it reads like
  the Calls call document beside it.
- "Let it wait" keeps the message and hides the Needs you row until a reply
  or the next reach.
- Urgent through Do Not Disturb is drawn off and disabled, with the line
  "Until Apple allows it, an urgent call rings once more after 1 min".

## What the canvas could not establish

- The app does not exist, so the scan is not proven end to end.
- The desk floor is CSS, not a recorded hub shot. No product guard reads
  `docs/` canvases, so the copy here is proven by reading.
