# HoldSpeak Mobile — Agent Handover

**Written:** 2026-06-22 · **For:** a fresh agent picking up the mobile roadmap.
**Top priority (owner):** drive **Phase 8 (iPad Experience)** and **Phase 14 (Mobile
Experience & Craft)** to the finish **as fast as humanly possible**. Everything below exists to
let you start producing on day one without rediscovering it.

---

## 0. Read these first (10 min)

- `CLAUDE.md` (repo root) — working agreements. **The PMO pre-commit gate is real** (see §6).
- `pm/roadmap/holdspeak-mobile/README.md` — the mobile roadmap index + "Last updated".
- `docs/internal/POSITIONING.md` — voice/positioning canon (e.g. no "privacy novels"; one egress
  badge). The voice guard CI will reject banned vocabulary and prose dashes.
- This file.

The mobile project runs **parallel tracks** (the "Council Charter"), so several phases are
legitimately in-progress at once — that is by design, not mess. Your lane is **8 and 14**.

---

## 1. The single most important loop: build → deploy → SHOW

The mobile deliverable is **a usable, beautiful, hand-driven app shown via screenshots / on the
device** — NOT backend plumbing. The owner's bar: "alluring, fluid, entertaining"; flat/default
SwiftUI is a failure. Every change is **built, deployed, and shown** (Simulator screenshot or a
device run). Prove LLM-shaped features on **real metal**, not just a no-LLM plumbing pass.

### The app
The flagship is the **meeting-capture app**, one SwiftUI file `apple/App/MeetingCaptureApp.swift`
(~2.6k lines) that compiles all SPM layers (Contracts/Providers/RuntimeCore/InferenceLlama) +
the App into **one module** (so `internal` works cross-"module"). The project is generated, not
checked in.

### Regenerate + build for the iPad (device)
```bash
cd apple
ruby scripts/gen-meeting-capture.rb                  # ALWAYS re-run after editing App/ or Sources/
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug -destination 'generic/platform=iOS' \
  -allowProvisioningUpdates -skipMacroValidation \
  -clonedSourcePackagesDirPath build/spm-meeting -derivedDataPath build/dd-meeting build
DEV=6B2F424D-707F-51F7-A33E-259427861CB1            # iPad Air M4 "AjPed" (keys/devicectl just work)
APP="$PWD/build/dd-meeting/Build/Products/Debug-iphoneos/HoldSpeakMobile.app"
xcrun devicectl device install app --device "$DEV" "$APP"
xcrun devicectl device process launch --terminate-existing --device "$DEV" dev.holdspeak.mobile
# (launch fails with "could not be unlocked" if the iPad is locked — install still succeeds.)
```

### Build for the Simulator + screenshot (how you SHOW UI without the device)
`idb` is **broken** on this machine (libexpat/pyexpat), and AppleScript can't see the Simulator
window (no Accessibility grant) — so you cannot tap. Instead the app has **simulator-only seeds**
gated by `#if targetEnvironment(simulator)` + env flags, then `simctl io screenshot`:
```bash
SIM=$(xcrun simctl list devices available | grep -iE 'iPad (Air|Pro)' | head -1 | grep -oE '\([0-9A-F-]{36}\)' | tr -d '()')
xcrun simctl boot "$SIM"; open -a Simulator
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile \
  -configuration Debug -destination "platform=iOS Simulator,id=$SIM" \
  -skipMacroValidation -clonedSourcePackagesDirPath build/spm-meeting -derivedDataPath build/dd-sim build
xcrun simctl install "$SIM" "$PWD/build/dd-sim/Build/Products/Debug-iphonesimulator/HoldSpeakMobile.app"
# HS_DEMO=1 opens straight to the live capture canvas; +HS_DEMO_NOTES=1 lands on the Notes pane.
SIMCTL_CHILD_HS_DEMO=1 xcrun simctl launch "$SIM" dev.holdspeak.mobile     # env MUST use the SIMCTL_CHILD_ prefix
sleep 2; xcrun simctl io "$SIM" screenshot /tmp/shot.png
```
Commit screenshots under the phase's `screenshots/` dir as evidence. The seed lives in
`CaptureModel.seedDemo(...)` + `MeetingListView.onAppear` — extend it to stage whatever state you
need to photograph; it never ships to device.

---

## 2. Hard-won gotchas (do not relearn these)

- **Re-run `gen-meeting-capture.rb`** after any `App/` or `Sources/` edit — the build uses a
  staged copy; stale copies cause baffling "my change didn't take" loops.
- **WhisperKit model caching (live):** `WhisperKitTranscriber` caches the model in a lock-guarded
  static (`nonisolated(unsafe)` — WhisperKit is NOT Sendable, so it must be created+used inside
  the same nonisolated async method, never returned from an actor / that fails Swift 6). Do not
  revert to `WhisperKit(...)` per call — that reloads from disk every tick (the old slowness).
- **Live transcription still re-scans the whole buffer each tick** → O(meeting length). The fix is
  planned as **HSM-14-12** (timestamp-driven sliding window). See that story.
- **`MeetingCapture.inputLevel`** (RMS per buffer) drives the audio-reactive `MicWaveform`;
  `CaptureModel.level` polls it at 20 Hz.
- **MLX is thread-bound** (desktop/Python side) and **`GGML_NO_BACKTRACE`** in
  `holdspeak/__init__.py` must never be removed — but those are the *desktop* package; the iPad app
  uses CoreML (WhisperKit) + llama.cpp via `LlamaProvider`/LLM.swift (`InferenceLlama` is a
  separate SPM product so the domain never links the engine).
- **On-device LLM gotcha:** LLM.swift accumulates KV context across calls → use a **fresh
  `LlamaProvider` per inference** (see `MeetingReviewState.generate()`), it deinits at scope exit.
- **Patch targets after the Phase-63 decomposition live in mixin modules** (desktop only) — not
  relevant to the mobile app, but if you touch the Python side, note it.
- **Increased-memory entitlement** is needed for the 4B model on device (portal cap raised already).

---

## 3. PHASE 8 — iPad Experience  →  3 items to close

`pm/roadmap/holdspeak-mobile/phase-8-ipad-experience/current-phase-status.md`

**Done:** 8-01 (shell+capture), 8-02 (PencilKit notebook), 8-03 (transcript linking),
8-04 (artifact review — **Track I workflow gate ACHIEVED** on a real iPad), 8-06 (ink→intelligence).

**Remaining to CLOSE the phase:**
1. **HSM-8-05 — The air-gapped notetaker gate (backlog, the big one).** Run the WHOLE loop in real
   **airplane mode** on the unlocked iPad with a resident **Mode-A GGUF** model: record → on-device
   Whisper transcript → Mode-A intelligence → notebook + linked moments → artifact review, **with
   radios off**. Bar: rich, not a degraded fallback; honest "on-device · nothing leaves" egress;
   graceful no-model-resident guidance. Evidence: a device walkthrough with the network provably
   off → write `evidence-story-05.md`. (This is **Gate 8**, a program quality gate, Amendment 1.1.)
   Story: `story-05-air-gapped-notetaker.md`.
2. **HSM-8-07 device proof** (chunked extraction over a 1h+ meeting) — host-complete (12 tests,
   wired, device-built); needs the on-device walkthrough.
3. **HSM-8-08 device proof** (OOM-safe budget) — same: host-complete, needs the device run.

All three are **device-gated** and were deferred only because the owner wasn't at the iPad. **The
owner is now actively driving the iPad** — so these are unblocked. A resident Mode-A model is
required (push a `.gguf` to the app's Documents, or AirDrop via the Models screen — see §5).
Qwen3-4B-Instruct-2507 Q6_K is the proven on-device model (PR #85).

---

## 4. PHASE 14 — Mobile Experience & Craft  →  the craft track

`pm/roadmap/holdspeak-mobile/phase-14-mobile-experience-craft/current-phase-status.md`
Opened 2026-06-21 on a termination-level owner mandate: usability/design/modern hand-driven
practice were absent. Design direction = **Tactile Sheets** (gesture-first, haptic). This is the
phase the owner most wants finished.

**Shipped this week (PRs #115–#118), all on `main` + on the iPad:**
- 14-03: intelligence cards **materialize** (glow + animated insert); MIR profile is a **lens**
  (blurb + emphasized-type chips, named on Generate).
- 14-11: the **live capture canvas** — utterances float up as bubbles; **fling a bubble anywhere
  on a free-form dot-grid desktop to tack it** (tacking marks the moment → MIR weights it);
  **pull a bubble into the note canvas** as a draggable quoted card; **promote a note → a real
  `needs_review` artifact** (`pluginId=holdspeak.mobile.note`). Transcription **root-caused +
  cached** (3s→1.2s); **audio-reactive waveform**; the recording controls collapse into a
  **draggable frosted FloatingRecorder** (no big button), canvas full-bleed.

**Story status (the work left):**
| Story | What | Status / what remains |
|---|---|---|
| 14-01 | Native design system (Signal→SwiftUI) | in-progress — substantially done; verify + close with shots |
| 14-02 | Capture experience, recrafted | in-progress — floating recorder + full-bleed landed; polish + close |
| 14-03 | Meeting + intelligence surface | in-progress — materialize + lens landed; close with device proof |
| 14-04 | Interaction craft (gesture/haptic/motion/Pencil) | backlog |
| 14-05 | Accessibility + adaptivity | backlog |
| 14-06 | Polish & craft QA (states, micro-copy, gallery) | backlog |
| 14-07 | Voice correction (reject by voice → re-route) | in-progress — host-tested + on iPad; close |
| 14-08 | Pencil → Mermaid (sketch language) | in-progress — engine host-tested; live Pencil + VLM-for-ambiguity remains |
| 14-09 | Local vision model (Gemma 4) seam | in-progress — seam host-tested + **endpoint Mode B proven**; **on-device Gemma 4 E4B via MLX-VLM (Mode A) is the real remaining build** |
| 14-10 | Models, front & center (import, AirDrop) | in-progress — device-built; close |
| 14-11 | Live capture canvas | in-progress — shipped a lot; one open: **live-mic device verification** |
| **14-12** | **Constant-time live transcription** | **planned** — designed in `story-12`, ready to build |
| **14-13** | **The spatial workspace (OS-like)** | **planned** — designed in `story-13`, ready to build |

**Recommended close-out order (fastest path to "Phase 14 done"):**
1. **Sweep the near-done in-progress stories** (01, 03, 07, 10, 11): verify on device/sim, capture
   the committed screenshots, write evidence, flip to `done`. Several are basically finished.
2. **14-12 (constant-time transcription)** — contained, host-testable, makes the live loop genuinely
   good. Architecture + acceptance criteria are in `story-12`.
3. **14-13 deliverables 1–2** (dock/minimize recorder, free-place vs tack) — most "OS-like" feel for
   least surface area. `story-13` lists the ordered deliverables (and a possible 14-14 split).
4. **14-08 / 14-09 on-device** — the live Pencil→Mermaid + **on-device Gemma 4 (MLX-VLM, Mode A)**.
   This is the largest remaining *tech* (a new MLX-VLM runtime behind the existing `IVisionProvider`
   seam, a separate SPM product mirroring `InferenceLlama`). Prove on the endpoint first (it already
   works on `.43`), then bring on-device.
5. **14-04 / 14-05 / 14-06** — interaction-craft pass, accessibility, polish QA + a screenshot gallery.

---

## 5. Key code map (mobile app)

All in `apple/App/MeetingCaptureApp.swift` unless noted:
- `CaptureModel` — the live meeting model (recording, `liveBubbles`, `pinned`, `partial`, `level`,
  `notebook`, `ingest`, `pin`/`unpin`/`movePin`, `sendToNotes`, `promoteNoteToArtifact`, `seedDemo`).
- `LiveCaptureCanvas` / `LiveBubbleView` / `LiveCaption` / `PinnedNoteView` / `DesktopGrid` /
  `MicWaveform` / `FloatingRecorder` — the spatial capture surface.
- `NotebookModel` / `NotebookView` / `NoteCardView` / `PencilCanvas` — PencilKit notes + pulled-in
  transcript cards (cards persist in `notecards-<meetingID>.json`).
- `MeetingReviewState` — on-device artifact generation/review (`generate()`, `promoteNote`,
  `correct`); the intelligence pane (`artifactsSection`) + the lens.
- `WhisperKitTranscriber` (cached model), `SQLiteMeetingStore`, `FileNotebookStore`, `ModelsView`.
- `Sketch → Diagram`: `SketchToDiagramView`, `SketchVLM`, `MermaidWebView` (bundled `mermaid.min.js`).
- Engine cores (host-tested, `Sources/RuntimeCore/...`): `MeetingCapture` (capture loop +
  `inputLevel`), `MIRRouter.baseEmphasis` (the lens types), `OnDeviceBudget`, `ChunkedExtraction`,
  `ArtifactGenerationEngine`, `SketchToMermaid`, `ArtifactCorrection`. `IVisionProvider` seam +
  `LlamaProvider` (Mode A) in `Sources/Providers` / `Sources/InferenceLlama`.

Pixel-art assets (bundled offline, SF-Symbol fallbacks via `pixelAsset(...)`): `apple/App/{qlippy,
pushpin,waveorb}.png`.

---

## 6. The commit ritual (every commit)

1. Branch off `main`: `git checkout -b holdspeak-mobile/<hsm-id>-<slug>`.
2. Stage **only your files** (the tree carries unrelated pre-existing dirt — never `git add -A`).
3. Write `.tmp/CONTRACT.md` per `pm/roadmap/PMO-CONTRACT.md` §"Contract template" — flip all
   checkboxes only after honestly verifying each. **8 boxes** (the design-handoff one too); for
   UI-facing work also write `.tmp/DESIGN-HANDOFF-OK.md`. The pre-commit hook validates + deletes
   them; a stale/unchecked contract is rejected.
4. **Tests ran is a real gate.** `cd apple && swift test` (currently **211/0**, 6 skipped) for any
   `Sources/` change. App-target-only UI changes are validated by the device + simulator
   `xcodebuild` (BUILD SUCCEEDED) + the committed screenshot — state that honestly in the contract.
   Python suite (if you touch it): `uv run pytest -q --ignore=tests/e2e/test_metal.py` (that file
   hangs without a mic).
5. Commit footer (exact):
   ```
   Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
   Claude-Session: <your session url>
   ```
6. Push, open a PR, wait for CI **CLEAN** (the "Swift package (build + test + layer guard)" check
   builds `Sources/`), merge with a **merge commit**, delete the branch. Don't leave branches local.
7. **Operating cadence:** every shipping commit updates the story header status, the phase's
   `current-phase-status.md` (story-status row + "Where we are"), and the mobile `README.md`
   "Last updated". Each phase gets a **dedicated docs story** before closeout. Flip a story to
   `done` only with on-disk evidence (a committed screenshot / `swift test` output / an
   `evidence-story-N.md`).

---

## 7. External resources

- **`.43` LAN endpoint** — `ssh karol@192.168.1.43` (keys work). Self-hosted llama.cpp at
  `192.168.1.43:8080`. Currently serves **Qwythos-9B + mmproj (vision)** in a **tmux session
  `qwythos`** (survives ssh, not reboot); relaunch:
  `tmux new-session -d -s qwythos "bash ~/run-qwythos-vision.sh > /tmp/qwythos.log 2>&1"`. Two
  scripts on the box: `~/run-qwythos-intel.sh` (text, `{"line"}` grammar) and
  `~/run-qwythos-vision.sh` (vision, no grammar) — one 16GB GPU can't host both, they swap.
  A clean Mac llama-server is sometimes at `192.168.1.13:8081`. **Sandbox can't reach the LAN** —
  probe with `dangerouslyDisableSandbox: true`.
- **Pixellab MCP** (pixel-art assets; owner WANTS it used): `create_1_direction_object` → `get_object`
  → `select_object_frames` → download the promoted `rotations/frame_0.png` (use the sandbox escape).
  ~1.7k subscription generations left. Bundle PNGs as resources in `gen-meeting-capture.rb`.

---

## 8. Definition of done

- **Phase 8 closes** when 8-05 (air-gapped gate, airplane-mode device walkthrough) is proven and
  8-07/8-08 have their device proofs — then write each `evidence-story-N.md`, flip statuses, and a
  `final-summary.md`.
- **Phase 14 closes** when the in-progress stories are verified+closed with committed evidence, the
  on-device vision (14-09) loop is proven on the iPad, 12/13 land, and the polish/a11y/QA pass
  (04/05/06) is done — then a docs story + `final-summary.md`.

Both phases share the same proof posture: **shown on the device / in committed screenshots, with
LLM-shaped features proven on real metal.** Go make it beautiful, and fast.
