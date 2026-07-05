# HSM-16-06 — the cross-surface walk (press-play protocol)

The owner's device session for Phase 16, prepared. Everything below was proven
headless (sim affordances, live-hub route tests, Playwright on the web desk —
see evidence 04/08/09); this walk verifies the same loops with a finger on real
glass. Budget: ~15 minutes. **Joins the standing couch queue** (17-06 + the
18/19/21/22/23 riders) — same hub, same pairing.

## 0. Pre-flight

- Hub on the Mac: `holdspeak web` bound for the LAN; the web desk open in a
  browser at the hub's `/`.
- iPad paired the HSM-12 way (host/port + Bearer token) with at least one
  language GGUF installed (Settings → models) so C2 has something to push.
- Intel: the hub's configured provider as-is (`.43` works; C2 names whatever
  the hub really runs — after the 16-04 fix it emits its live `desktop:intel`
  row from real config, no seeding).
- Install the current MeetingCapture build (device UNLOCKED). Signing is fully
  headless now — the App Store Connect key at
  `~/.appstoreconnect/private_keys/AuthKey_PUZZLQB758.p8` provisions with no
  Xcode sign-in (recipe proven 2026-07-05; a signed build may already sit at
  `apple/build/dd-device/Build/Products/Debug-iphoneos/HoldSpeakMobile.app`):

```bash
cd apple && ruby scripts/gen-meeting-capture.rb
scripts/patch-llm-macro.sh build/dd-capture-device build/HoldSpeakMeetingCapture.xcodeproj HoldSpeakMobile
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -destination "generic/platform=iOS" -derivedDataPath build/dd-capture-device \
  -disableAutomaticPackageResolution -skipMacroValidation \
  -allowProvisioningUpdates \
  -authenticationKeyPath ~/.appstoreconnect/private_keys/AuthKey_PUZZLQB758.p8 \
  -authenticationKeyID PUZZLQB758 \
  -authenticationKeyIssuerID c1d852da-77ac-485c-aa95-2909cbb1bf0e build
xcrun devicectl device install app --device <UDID> \
  build/dd-capture-device/Build/Products/Debug-iphoneos/HoldSpeakMobile.app
```

Both `-authenticationKey*` id flags are required together; the key file is a
credential — never print or commit it.

(UDID list: `xcrun devicectl list devices`. Remember: `gen-meeting-capture.rb`
COPIES sources — rerun it after any App/*.swift edit.)

## 1. The walk — four checks

Capture a screenshot per check into `screenshots/` and fill the trace.

**C1 — the Ask atom on glass (16-09's device beat).** On the iPad desk, lasso
two or three cards, pull **Ask AI**, pick a lens, SPEAK the instruction
(the mic, not the keyboard), Ask. EXPECT: the composer sits in the atelier
posture (desk visible, no scrim), the card PRINTS from the AI core, the badge
states where the run went (On-device for a local profile — airplane mode is
the honest version of this check), Keep lands it on the desk. CONTROL: Bin a
second ask — nothing appears in artifact review.

**C2 — the mesh knows its models (16-08).** iPad → the "where should it run?"
sheet. EXPECT: the desktop row names the hub's REAL model (e.g.
`Qwen3.5-9B-UD-Q6_K_XL · 192.168.1.43`), not "big model" — this row is now
computed from the hub's live config (the 16-04 latent-bug fix), so a wrong or
empty name here is a real finding, not seed drift. On the hub, verify the
iPad's push landed:

```bash
curl -s http://127.0.0.1:8000/api/sync/pull | python3 -m json.tool | grep -A2 '"kind": "model"' | head
```

EXPECT: one row per installed iPad GGUF + the live `desktop:intel` row. The
values carry no `path`/`url` — availability only.

**C3 — the org loop, three surfaces (the story's original spine).** On the
iPad: create a KB, file two meetings into it. EXPECT: the same KB with the
same members on the web desk (dive in) after a sync pass. On the WEB: file a
third object into it. EXPECT: it shows inside the KB on the iPad. Nothing
left the mesh (the egress badge holds on both surfaces).

**C4 — one Ask, every surface (the 16-04 addition).** The Ask you KEPT in C1:
find it on the web desk (it floats as an artifact; pull it out). EXPECT: the
lineage section lists EVERY lasso'd card + `via <lens>` — the same provenance
the iPad shows, because both surfaces mint/read one wire shape. Reverse: on
the web desk, lasso → Ask (runs on the hub or a profile — the badge names it,
`☁ model · host` for a cloud profile) → Keep. EXPECT: the kept card appears
in the iPad's artifact review with the same lineage.

## 2. The trace (fill during the walk)

```
Date/build:                  <commit>
Hub / intel:                 <host + model>
C1 ask on glass + bin ctrl:  PASS/FAIL — <lens, spoken prompt, badge seen>
C2 manifest names the model: PASS/FAIL — <row text + pull rows counted>
C3 org loop both directions: PASS/FAIL — <KB name, members>
C4 one Ask, every surface:   PASS/FAIL — <lineage rows seen on both>
Bugs found:                  <list — file them; the walk is a bug hunt too>
```

PASS on all four closes HSM-16-06 (and unblocks 16-07's docs of the proof).
Any FAIL: fix under the owning story, re-walk the failed check, then close.
