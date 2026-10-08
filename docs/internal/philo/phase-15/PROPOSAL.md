# PHILO Phase 15 — The First Day: the proposal

Written 2026-10-07 by Muad'Dib under the owner's autonomy grant of the same
day ("you make ALL the calls"; "once you have already moved this mountain,
that we move another one, of your choosing, that makes the most sense to
work out, to PERFECT the experience with HoldSpeak"). Read with
`docs/internal/philo/phase-14/PROPOSAL.md` (the Desk is objects, closed),
`docs/internal/CONDUCTOR.md` (what the Conductor does) and
`docs/internal/HANDOVER-MUADDIB-XXXIII.md` §Next (the recommendation this
phase takes up).

## 1. Why this mountain

Three facts pick it.

1. **Tenet 2: not even pre-alpha.** The creator has not used HoldSpeak
   once. Every phase since 2026-09-19 has built toward his first real day;
   none has rehearsed it end to end. The 2026-10-03 "week of use" prep
   inventoried and cleaned the product, then the Conductor and Phase 14
   rebuilt the Desk under it. What a first day feels like today is unknown.
2. **The last handover's own next step.** XXXIII §Next: "Hand the Conductor
   one small real action item from one of the owner's own Projects, on his
   real desk, and watch launch → PR → merge." That walk was never run with
   isolated credentials; the one real walk (R1) found what 14k green tests
   missed (every Bash call held; Codex never got its brief; questions never
   reached Needs you).
3. **His ask is "perfect the experience", not "add a feature".** The
   defects that embarrass a first day are not in any backlog row; they are
   found only by living the day. The 393 "missing icons" and the Codex face
   wearing Claude Code's robot were both found this morning by a shot and a
   walk, not by a test.

So Phase 15 does not build a new face. It rehearses the owner's first real
day on real metal, as him, from install to a sent weekly update, and fixes
every bounce before he hits it.

## 2. What Phase 15 is

**One rehearsal, lived twice, every bounce paid.**

- **The Day One script** (`docs/internal/philo/phase-15/DAY-ONE.md`): the
  owner's first day as a Senior Software Architect with reports, in the
  order he would live it: install and first launch; the Morning (Chair
  screen, Needs you, the brief, The week); one meeting (record or import,
  transcript, summary, aftercare card, decisions and action items); People
  and a Project with its connectors; the Conductor (hooks, Hand to agent
  from a Needs row, the lane, a question answered, a held call denied and
  one approved, the PR, the merge receipt, the weekly update's merged row);
  the weekly update sent; the end of day (Parked, what memory keeps for
  tomorrow morning). Each step names the face, the gesture at 1440 and
  393, and the proof that already covers it.
- **Rehearsal 1, the rig (Muad'Dib):** every step of the script walked on
  a fresh isolated HOME with real engines: the LAN model at
  192.168.1.43:8080 for drafting and summaries, Whisper for transcription,
  a real Claude Code and a real Codex under an ISOLATED `CLAUDE_CONFIG_DIR`
  / `CODEX_HOME` login or API keys (never the owner's keychain or
  `auth.json`; law from XXXIII), a throwaway GitHub repo and a Resend test
  key for egress. Both widths. Every step gets a shot. Every bounce becomes
  a lane (small PR, one Astra round, FAST, merge) the same day.
- **Rehearsal 2, the second morning (Muad'Dib):** the same HOME the next
  day: does the brief carry yesterday; does memory show; do the agent's
  receipts read right; does nothing double.
- **The runbook (owner):** `DAY-ONE.md` rewritten from the rehearsal as
  the page he follows on his real first day, ASD-STE100, one screen per
  step with the shot beside it. Published as a canvas artifact too, so he
  can read it on the phone.

What Phase 15 is NOT: no new face, no new feature, no canvas of a new
object. A bounce that needs a new face gets a canvas and a lane under the
Phase 14 rules; a bounce that needs a backend fix gets a lane; a bounce
that is a test gesture gets re-anchored. "Perfect" means: nothing on the
script stops him, confuses him, lies to him, or looks like Windows 1.0.

## 3. Standing rulings carried in

- Tenets first; UX-CANON on every face; ASD-STE100 on every word.
- The isolated-credentials law (XXXIII): the rehearsal never touches the
  owner's keychain, `auth.json`, or real DB.
- One Astra round per PR (max 2 iterations), bounded briefs (never "run
  every case"); one FAST at a time, by the orchestrator; load law: rerun
  alone before calling a red real.
- Never delete; park. Build what was ratified. Shots in PRs are the
  record. Muad'Dib ratifies canvases under the autonomy grant.

## 4. Lanes

| Lane | What | Owner |
|---|---|---|
| 00 | The Day One inventory: the script as main has it, with the honest state of each step (WORKS / UNVERIFIED / KNOWN BROKEN / NEEDS REAL METAL) and the ranked gaps | worker (read-only), running |
| 01 | `DAY-ONE.md` v1 from the inventory | Muad'Dib |
| 02 | Rehearsal 1 on the rig, both widths, shots per step, bounce log | Muad'Dib |
| 03..0N | One lane per bounce, opened the same day, each a small PR | workers |
| 10 | Rehearsal 2, the second morning | Muad'Dib |
| 11 | `DAY-ONE.md` v2 = the owner's runbook + the canvas page | Muad'Dib + worker |
| 12 | Close: handover, STATUS, the phase memory | Muad'Dib |

Carried-in debt that a first day would hit goes into lanes 03..0N by the
inventory's ranking; debt a first day would not hit stays in STATUS.

## 5. Done means

- The owner can follow `DAY-ONE.md` from install to a sent weekly update
  without a step that stops, confuses or lies, at 1440 and at 393.
- Every step on the script has a shot from the rehearsal and a proof (a
  glass or atlas case, or a disclosed NEEDS REAL METAL with the rehearsal's
  own evidence).
- The Conductor loop launch → PR → merge has been walked once with
  isolated credentials and the receipts read right on the lane, in Needs
  you and in the weekly update.
- The second morning carries the first day.

## Phase 15 amendment to PHILO-13-17 C7 Q3 (the phone Go)

Owner ruling 2026-10-07 (bounce B21, lane 11, PR #986). It supersedes C7 Q3,
`pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-17-canvas/README.md:30`
("Go leads with `Chair ▸ Desk ▸ Object ▸ Window ▸`"), and the story-17
criterion "The Desk, Object and Window menus are reachable at 393"
(`pm/roadmap/holdspeak-philo/phase-13-the-desk/story-17-c7-the-phone-desk.md:35`)
as it applies to Go. The roadmap stays as history; it is not edited.

- At 393 Go is: the four Chair windows (Needs you, Brief, The week, Capture),
  then the Dock's places (Meetings, People, Conductor, Settings), then the
  projects, then `New ▸` with four kinds (Thought, Meeting, Project, Person).
- Desk, Object and Window are reached from the window's own menu (a long
  press on the window's title): `Desk ▸` (New Note, New Decision, Search),
  `Send to ▸`, and the window verbs. Every other verb is in Search.
- No keycap on a phone: no menu and no Search row at 393 shows a ⌘ or ⌃ hint.
- 1440 keeps its four menus and their keycaps.
