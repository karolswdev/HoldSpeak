# The four Tuesday faces — the settled design (Phase 170, story 04)

The owner's mandate: "Fedaykin need to make a huge UX pass of
everything." The canon: docs/internal/UX-CANON.md. The grammar: the
Door and the Room (Phase 169). The recon: HS-170-04 research (anchors
below). Four faces, each ONE screen, each with one display-step fact,
sections that appear only when they have content, empty states as one
line, every verb the library Button, every host named.

## Face 1 — THE ARRIVAL (the desk's home; ChairHome / Chair, chair/lanes/*)

**Today.** A big `Develop a thought` hero; then `PEOPLE NOT SET UP`, an
empty ring `Door clear`, the sentence `No calendar connected.`,
`Generate your brief`, `AGENTS · CREW 0 · BLOCKED 0`, `No sessions`.
Five raw buttons in the hero alone. FinishThoughtsLane (the unfinished
thoughts) is built and NOT wired (laneContract.ts:28-33).

**The design.** The arrival answers the Tuesday question first.
1. **Headline** (display, ONCE): `Nothing needs you` (muted) or `3 need
   you across 2 projects` (accent) — summed from every active Room's
   `needsYou` (the 169 wire; in 170 the sum is read-time over active
   projects — `GET /api/projects` then each Room's `needsYou`, N+1 by
   design; 171 gives it one route). Under it one line when true: `NEXT ·
   Standup · 10:00` (the next scheduled recording or calendar event;
   omitted when none — never `No calendar connected.`; connecting a
   calendar is a Settings row).
2. **NEEDS YOU** (caption + count) — the rows across Rooms (source
   emblem · the thing · WHY · `Open`), the Room's grammar; the row's
   project as a faint token when more than one Room. Empty: the section
   is absent (the headline said it).
3. **THOUGHTS** — the arrival's own section (a SurfaceLedgerRow list fed
   by the unfinished-thoughts read; the Chair LANE vocabulary is RETIRED
   by `test_doc_drift_guard` — no lane is revived, no LANE_ORDER edit;
   the old lane component's row logic may be lifted into the section): unfinished thoughts
   as rows (`Continue` / `Ready for you` / `Needs attention` as the
   state token; primary `Continue` on the first). Empty: absent.
4. **BRIEF** — when a brief exists: `N things waiting` rows with `Ack` /
   `Defer` (the 150 verbs); when none: ONE line `No brief yet` with the
   ghost verb `Generate` on the caption row — never a lone button in a
   void.
5. **MEETINGS** — the last three as stream rows (`SEP 04 · Census
   standup · 30 MIN` · state token `OFF` carrying the verb `Run
   intelligence` (dense primary on the row), `SAVED`, `REC`). Empty:
   absent.
6. **AGENTS** — only when a session exists (blocked first, `Answer`).
   Never `CREW 0 · BLOCKED 0`.
7. **The capture bar** (the foot of the arrival, always): the mic
   TransportKey `Talk` (primary) · `Develop a thought` (ghost, opens the
   thought well in place — the 152 PadGadget + `Start developing`) ·
   `Record meeting` (ghost). The old hero and `More capture options`
   fold into this bar; the sentence `Start rough. Keep developing it.`
   goes.
8. **Whole-desk empty state**: the headline `Nothing needs you`, then
   the capture bar. Nothing else. Three type steps: display, primary
   (row titles), caption/secondary.
9. 393: the same order; the capture bar sticky at the foot.

## Face 2 — SPEAK (DictationCore)

**Today.** A cockpit: `PIPELINE LIVE · → TARGET CLAUDE CODE · MIC CLOSED
· LANDED — · BUDGET 600 MS`, a STATE register strip, `Aim / Rehearse`
labels, a warning rail (`box-shadow: inset 3px 0` — the banned rail by
another name) on `Dictation · No default model`, raw Export button.

**The design.** One screen: talk, see it land, teach once.
1. **The transport** (top): `Talk` (MicButton transport, the ONE
   primary) · `Open` latch · the LEVEL meter (LedMeter) — the meter is
   the only thing that moves while he talks.
2. **The utterance well** (PadGadget) — what he said, as it lands; the
   mic law is met by `Talk` (no second mic).
3. **LANDS IN** — ONE line: `Claude Code · 41 MS` (the target name and
   the last latency; the Aim cycle `FOCUSED APP ▾` sits at its right as
   the picker control; `Rehearse` is a token toggle `DRY RUN`, off).
4. **RESULT** (when landed): the final text at primary; `OK` (ghost) ·
   `Wrong` (ghost) → the teach row unfolds in place (Field cycle ·
   Value StringGadget with mic · `Teach` primary). The learning loop is
   the face's second job.
5. **ENGINE** — one row: `DICTATION · Qwen 3.5 0.8B` · EgressChip `THIS
   DEVICE` (or `192.168.1.43 · LAN`) · when unset: StateChip `⚠ NOT
   SET` + ghost `Choose` (opens the Concierge in place). NO rail.
6. **Details** (Disclosure, folded): the pipeline state register, `BUDGET
   600 MS`, `MIC`, the raw trace — engineering under a fold, never on
   the face.
7. Footer: EgressChip `THIS DEVICE` (one egress vocabulary on every
   face — counsel M1; `LOCAL` retired) · receipt `9 TODAY` (journal count via
   countToken) · `Review` (ghost) · `Export` (ghost). Wings Speak ·
   Journal · Blocks stay; Journal becomes a SurfaceStream.
8. Empty (never talked): the transport + the well with the placeholder
   `Talk, or type here` + the ENGINE row. One line, no telemetry.
9. 393: transport row, well, LANDS IN, ENGINE stacked; the capture key
   sticky.

## Face 3 — THE SETTINGS HUB (SettingsCore / settingsPrefs)

**Today.** Eight pixel-art tiles (raw buttons) in a 4×2 grid with no
state; `POSTURE · YOLO · YOLO` (said twice); 70% dead space.

**The design.** A hub is rows that tell the truth before you open them.
1. **Headline** (display, ONCE): the one fact that most needs him:
   `No default model` (warning) / `All set` (muted) — derived: an unset
   Tuesday module wins (Models > Connections > Voice).
2. **Rows** (SurfaceLedgerRow, Tuesday first), each: the module name at
   primary · its STATE token(s) · trailing `Open` (ghost) — `MODELS ·
   3 ENGINES · 7 GROUPS SET` (or `⚠ NO DEFAULT`; engines from the model
   library summary, groups from the assignments summary — two reads
   composed on the client) → the Concierge;
   `CONNECTIONS · 2 CONNECTED`; `VOICE · LIVE · CLAUDE CODE`; `MEETINGS ·
   INTELLIGENCE OFF` (warning); `RHYTHM · NO LOOPS`; `SOUNDS & PRESENCE ·
   ON`; `SYSTEM · THIS DEVICE · MESH OFF`. No sprites, no icons — the
   name and the state are the face.
3. **POSTURE** row: the CycleGadget once (`YOLO ▾`); the duplicate
   fact span goes.
4. Footer: EgressChip `THIS DEVICE` · the PrefStatusBar receipt. The
   Guide wing stays.
5. A module opens IN PLACE below its row? No — it opens as today's
   module face (the row is the entry); the hub is the truth table.
6. 393: rows stack their tokens under the name.

## Face 4 — MEETINGS (HistoryCore)

**Today.** `MEETINGS / 1 RECORDS`, `0 SEG`, `INTELLIGENCE OFF` as a bare
fact with NO verb anywhere to run intelligence on a meeting that never
ran (the loudest wire gap on the desk: the pillar's tagline has no
button).

**The design.**
1. **Headline** (display, ONCE): `1 meeting needs intelligence` (accent)
   / `Nothing needs you` (muted) / `No meetings yet` — derived from the
   list's state tokens.
2. **The verbs** in the head: `Record meeting` (the ONE primary) ·
   `Import` (ghost).
3. **The stream** (SurfaceLedger, newest first): `SEP 04 · Census
   standup · 30 MIN` · `NO TRANSCRIPT` (never `0 SEG`) · the state token
   CARRYING its verb: `OFF` + dense `Run intelligence`; `FAILED` +
   `Retry`; `SAVED` + `Open`; `NEEDS YOU · 3` + `Open`. `1 RECORD` via
   countToken.
4. **The detail** (SurfaceSplit on select): the header (title · date ·
   duration · state) · NEEDS YOU (the outcomes table; when the meeting is OFF and has a
   transcript, `Run intelligence` (primary dense) sits at the trailing
   edge of the NEEDS YOU caption row in place of the count) · the transcript well · AFTERCARE
   (only when a channel is configured; never an absent section's
   ghost) · the settled list.
5. **The wire gap paid in this story:** `POST /api/meetings/{id}/intelligence/run`
   — one verb that enqueues a fresh intelligence job for a meeting that
   never ran (the existing intel job machinery — check first whether
   `POST /api/intel/process` takes a single meeting id before adding a
   route; the plugin set from the
   meeting settings; a receipt; the egress chip names the model's host
   at the point of decision).
6. Footer: EgressChip `THIS DEVICE` · receipt (`1 RECORD`) · export
   verbs when a detail is open.
7. 393: the stream alone; the detail opens over it as the wing.

## Laws and counsel's hunts (all four)

One display fact per face · empty sections absent, empty faces one
line · every verb a Button · no counters of zero (`countToken`,
`countLabel`) · no sprites/emoji as icons · no rails (border or
box-shadow) · every host named (the ENGINE row, the model on `Run
intelligence`) · the name said once · three type steps · 393 stacks
under `surface`. Hunts: a headline that disagrees with the rows; a
state token with no verb; a sentence that survived as a "helper"; a
hero that is a button in a void; a face that still needs narration.

## Artboards (640 at 1440; 393)

Arrival: needs-you (3 across 2 projects + a thought + a meeting OFF) ·
quiet (`Nothing needs you` + the capture bar) · 393. Speak: idle ·
landed with result · 393. Settings hub: 1440 (`No default model`) ·
393. Meetings: list with one OFF row · detail open · 393. Twelve boards.


## Counsel (2026-09-05)

RATIFY-W-C. M1 `LOCAL` vs `THIS DEVICE` on the Speak footer — paid on
the boards and above. S1 the OFF detail placement — written above.
S2 the Models row's two wire reads — above. S3 the N+1 aggregate — above,
171 pays it. S4 the THOUGHTS section — its own section, not a revived lane (the
doc-drift guard retired the Chair lane vocabulary) — above. N1 the
posture said twice in settingsPrefs.tsx:383 — the build removes the
`gadget-fact` span. N5 `1,204 WORDS` = the transcript word count. N6 the
intelligence run route — check `/api/intel/process` first.


## Addendum (2026-09-05 03:50) — the Door's items join NEEDS YOU

Parking the Chair board (144) left `/api/door` items — the owner's own
action items with owners and due dates (overdue · now · waiting ·
active · unassigned) — with no face. They are needs-you by any reading.
Ruling: the arrival's NEEDS YOU merges them with the Rooms' items —
overdue first (`OVERDUE · Nd`, danger), then now (`NOW`, warning), then
waiting (`WAITING ON <owner>`, muted); unassigned items carry the ghost
verb `Name an owner` in place of `Open`; active items do not appear (the
headline says nothing is needed of them). Source emblem = the item's
origin (`MTG` for a meeting, `TH` for a thought, `DOOR` when unknown);
`Open` opens the origin. The headline counts them (`N need you` when no
project is involved; `across M projects` only when Rooms contribute).
The board's five columns retire; the 144 rig re-points to these rows,
to the NEXT line (the rail), and to Settings → Meetings for the
calendar glass.


## Addendum (2026-09-05 04:10) — the other lost doors (the audit)

Four owner-facing verbs had a face only in the parked Chair; they get
one on the arrival, in its grammar:
1. **Schedule** — the capture bar's fourth verb (ghost, after `Record
   meeting`): opens the existing ScheduleCreate window.
2. **The armed countdown** — while a scheduled recording is arming, one
   row under the NEXT line: `ARMED · <title> · IN MM:SS` (warning token)
   with danger `Cancel`; absent otherwise.
3. **The Door items' verbs** — a Door item's first lawful verb (Complete
   / Close / …, from `lawful_verbs` via the parked lane's `labelFor` +
   `commandForDoorVerb`, lifted into a shared util) is the row's primary
   dense verb; `Open` stays as the ghost beside it.
4. **Connect calendar** — when `calendar_configured` is false the NEXT
   slot reads `NO CALENDAR` (muted token) + ghost `Connect calendar` →
   Settings → Meetings; never the sentence `No calendar connected.`
Not restored, by design: inline thought compose (Speak is the compose
point; `Develop a thought` opens it), the lane pagination (the
Intelligence brief holds the full list), the setup wizard's JQL editor
(post-creation Watch configuration).
