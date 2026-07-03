# HSM-19-07 — the real-metal walk (press-play protocol)

The owner's device session, prepared. Everything below was staged headless on
2026-07-03; every check was already proven end to end against a live scratch hub
from the simulator (see the per-story evidence), so this walk verifies the same
loops with a finger on real glass. Budget: ~25 minutes. **Designed to share the
couch session with [`HSM-18-06-WALK.md`](../phase-18-ipad-dictation-contracts/HSM-18-06-WALK.md)** —
same hub, same pairing, same `.43` setup (W4 needs it; the other checks don't
touch the rewriter).

## 0. Pre-flight

- Hub: `holdspeak web` bound for the LAN, iPad paired the HSM-12 way (host/port +
  Bearer token). For W4, `dictation.runtime`/intel pointed at `.43` per the 18-06
  pre-flight (`~/run-qwythos-vision.sh`, NOT the `-intel` script).
- A meeting archive with some history (any real day works): at least one meeting
  with **accepted** action items, speakers, and a tag or two. A quick maker if
  the archive is bare: import two transcripts in W3 first, then accept an action
  item on the web review screen.
- Install the current CompanionShell build on the iPad (device must be UNLOCKED):

```bash
cd apple && ruby scripts/gen-companion-shell.rb
xcodebuild -project build/HoldSpeakCompanionShell.xcodeproj -scheme HoldSpeakMobile \
  -destination "platform=iOS,id=<UDID>" -derivedDataPath build/dd-shell-device \
  -allowProvisioningUpdates build
xcrun devicectl device install app --device <UDID> \
  build/dd-shell-device/Build/Products/Debug-iphoneos/HoldSpeakMobile.app
```

(UDID list: `xcrun devicectl list devices`.)

## 1. The walk — six checks, one per story

Capture a device screenshot per check into `screenshots/` and fill the trace.

**W1 — file the issue (19-01).** Meetings → tap a meeting with an accepted open
item. EXPECT: the aftercare digest renders (open by owner, decided, the diff
chips) and the accepted item alone wears **File issue**. Tap it, type a real
`owner/name`, File. EXPECT: the item flips to the **proposed** pill. CONTROL: a
pending (not accepted) item shows no File issue chip.

**W2 — the archive narrows (19-02).** On the Meetings tab, tap a speaker chip.
EXPECT: the list narrows to meetings that speaker spoke in (the chip lights;
the hub does the narrowing). Type a word you know was said, submit. EXPECT: the
transcript hit. Clear (xmark). EXPECT: the full list returns.

**W3 — import from Files (19-03).** Tap **Import file**, pick a `.vtt`/`.srt`/
`.txt` from Files. EXPECT: "Importing on your desktop", the new row appears
(marked importing, then settles), tap it later and the digest is real. BONUS
(real audio): pick a `.wav` recording — same loop through Whisper. CONTROL: an
unsupported file is refused with the format reason.

**W4 — the ring is earned (19-04).** Tap a meeting whose intel ran on `.43`
(or run/import one now). EXPECT: the ARTIFACTS card shows each artifact's
confidence ring banded by value and "Synthesized from …" naming its real
sources; a needs-review artifact wears the amber edge.

**W5 — the queue decides (19-05).** After W1, the PROPOSALS card lists your
filed issue as **proposed** with Approve/Reject. Approve it. EXPECT: the pill
flips to **approved** (github only flips state). Verify the audit on the hub:

```bash
curl -s http://127.0.0.1:8000/api/meetings/<id>/proposals | python3 -m json.tool | grep decided_by
```

EXPECT: `"decided_by": "ipad-companion"`. BONUS (if a Slack webhook is
configured): approve a slack proposal — its Approve wears **Cloud · slack**
and the message lands; the pill reads **executed**.

**W6 — the loop reads back (19-06).** Dictate tab. EXPECT: the LEARNED card
shows your real digest numbers, the correction rows with their reach, and the
journal with "learned from N similar" where the router would actually nudge.
Toggle **All**. EXPECT: the wider window's numbers.

## 2. The trace (fill during the walk)

```
Date/build:              <commit>
Hub / endpoint:          <host + .43 model for W4>
W1 file-issue + ctrl:    PASS/FAIL — <note>
W2 narrow + search:      PASS/FAIL — <speaker/word used>
W3 import (+audio?):     PASS/FAIL — <file(s), settle time>
W4 ring + sources:       PASS/FAIL — <artifact types seen>
W5 decide + audit (+slack?): PASS/FAIL — <decided_by verified?>
W6 learned card:         PASS/FAIL — <totals seen>
Bugs found:              <list — file them; the walk is a bug hunt too>
```

PASS on all six closes HSM-19-07 and the phase (entry-point docs land with this
runway). Any FAIL: fix, re-walk the failed check, then close.
