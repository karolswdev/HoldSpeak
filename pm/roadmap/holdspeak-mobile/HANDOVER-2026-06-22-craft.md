# HoldSpeak Mobile — Craft-Session Handover (2026-06-22)

**Read this BEFORE the older `HANDOVER.md`.** That one is the cold-start onboarding (Phase 8 + 14
overview, build loop, gotchas) and is still accurate for the mechanics. **This** doc is the live
pickup after a long craft session: where we are, the owner's bar (learned the hard way), and the
**one thing to build next**.

---

## 0. The 30-second version

You are continuing **Phase 14 — Mobile Experience & Craft** on the iPad flagship app
(`apple/App/MeetingCaptureApp.swift`, one ~4.6k-line SwiftUI module; all SPM layers compile into it).
This session shipped **9 PRs (#121–#129), all merged to `main`, all installed on the owner's iPad
Air M4.** The arc went: live-capture engine/UX → a real **Signal design system** → a **flagship home**
→ a **generation theater** → **App Settings (inference target)** → the **Workbench** (a visual,
user-defined intelligence builder).

**▶ BUILD THIS NEXT: wire the Workbench to actually EXECUTE.** The builder is real and beautiful but
its custom `LLM call` node + the `summarize/rewrite/keepIf` steps + the `note/Slack` outputs **do not
run yet** — running a workflow today just drives the existing extract/lens generation. Making a
workflow truly *execute its steps* (custom prompt → the configured model → routed output) is the
payoff and the explicit next task. Details in §3.

---

## 1. The owner's bar (this is the most important section)

The owner gave sharp, repeated, sometimes furious feedback. Internalize it — shipping anything that
violates these will be rejected:

- **NO PROSE IN THE PRODUCT.** Chatty result sentences ("Reachable — the model replied") are banned.
  Use tight chips / symbols ("3 found" ✓, "no connection" ✗). Same spirit as the
  `feedback_no_privacy_novels` memory. Empty-state helper copy is tolerated; narration is not.
- **USE PIXELLAB HEAVILY.** SF-symbol effects read as amateur. Generate bespoke pixel-art sprites for
  effects. Two are already bundled (`App/theaterorb.png` = the generation-theater plasma core;
  `App/crystal.png` = the Workbench header). The flow is in §5. The owner *wants* this used more.
- **REAL POWER + DELIGHTFUL TOUCH, not preset-only chains.** The owner rejected the first Workbench
  ("not even an alpha") because it was fixed preset blocks with cramped menus. They want custom
  primitives (the `LLM call` node — your prompt, your input) AND a genuinely pleasant building
  experience (tap-to-edit sheets, a real prompt editor — now shipped).
- **NATIVE CONVENTIONS.** e.g. an OpenAI endpoint exposes `GET /v1/models` — so you FETCH + PICK the
  model, never hand-type it. Don't reinvent what the platform/standard already gives.
- **"OOZES AWESOMENESS" / premium / native.** Flat, default-SwiftUI, marginal polish = failure.
  Depth, materials, motion, haptics, cohesion.
- **SHOW IT.** Every change is built for the **Simulator AND the device**, and **installed live on the
  iPad**, with a **committed screenshot**. Backend/plumbing is not a deliverable; the *felt* app is.
  Memory: `feedback_deliver_mobile_craft_not_plumbing` (termination-level).
- **DON'T CHECKPOINT — DELIVER.** The owner got annoyed by "what next?" questions. Keep shipping
  merged PRs; surface decisions only when genuinely blocked.

---

## 2. What shipped this session (PRs #121–#129, all on `main` + iPad)

| PR | What | Key files |
|---|---|---|
| #121 | Constant-time live transcription (committed prefix + bounded window); dockable/minimizable recorder; free-place vs tack | `Sources/RuntimeCore/Capture/MeetingCapture.swift`, `RecorderLayout.swift`, `BubblePlacement.swift` |
| #122 | Resizable workspace cards + one-tap tidy/undo | `Sources/RuntimeCore/Capture/CardLayout.swift` |
| #123 | **Signal design system** (depth/motion) + **flagship home** | `App/MeetingCaptureApp.swift` (`Sig`, `SignalCard`, `GlyphChip`, `PressableCard`, `MeetingListView`) |
| #124 | **Generation theater** (the on-device model, thinking, visualized) | `GenerationTheater`, `MeetingReviewState.gen*` |
| #125 | **App Settings** — choose where intelligence runs (iPad / LAN endpoint) | `InferenceConfigStore`, `SettingsView` |
| #126 | Workbench **engine** (the workflow model + tests) | `Sources/RuntimeCore/Workbench/Workflow.swift`, `Tests/.../WorkflowTests.swift` |
| #127 | Settings fixes: **fetched** model picker, tight states (no prose), **PixelLab** plasma orb | `InferenceConfigStore.fetchModels`, `App/theaterorb.png` |
| #128 | Workbench **canvas** + run-from-meeting | `WorkbenchView`, `WorkflowStore`, `generate(workflowTypes:)`, `App/crystal.png` |
| #129 | Workbench becomes a **real builder**: custom `LLM call` node + tap-to-edit prompt editor | `WorkflowStep.llmCall`, `WorkflowInput`, `WorkbenchEditorSheet` |

`swift test` is **241 passed / 6 skipped / 0 failures** (the RuntimeCore engines are host-tested; the
App UI is gated by `xcodebuild` + a committed screenshot — App changes don't run in `swift test`).

---

## 3. ▶ THE NEXT BUILD — make the Workbench EXECUTE (this is the priority)

### Where things stand
- **Engine (done):** `Sources/RuntimeCore/Workbench/Workflow.swift` — `Workflow` = `source` +
  ordered `[WorkflowStep]` + `output`. Steps: `.lens(MIRProfile)`, `.extract(ArtifactType)`,
  `.summarize`, `.rewrite(tone:)`, `.keepIf(keyword)`, **`.llmCall(name:, prompt:, input:)`**
  (the custom node; `WorkflowInput` = `.meeting` | `.previousStep`). `WorkflowPresets`,
  `Workflow.plan`, `Workflow.producedTypes(default:)`. Host-tested (`WorkflowTests`, 8).
- **Builder UI (done):** `WorkbenchView` (home → "Workbench" tile) + `WorkbenchEditorSheet`
  (tap any block → a real editor; the LLM-call node has a NAME + INPUT selector + multi-line PROMPT
  editor with `{input}` injection). `WorkflowStore` (UserDefaults) persists saved workflows.
- **Run (PARTIAL):** the meeting detail's "Run a workflow" menu calls
  `MeetingReviewState.generate(workflowTypes: w.producedTypes(...))` — which only honors the
  **extract/lens** steps (it generates those artifact types). **`llmCall`, `summarize`, `rewrite`,
  `keepIf`, and the `note`/`Slack` outputs are NOT executed.**

### What to build
A real workflow runner that executes the pipeline step-by-step through the configured provider:

1. **The provider is already wired.** `InferenceConfigStore.shared.makeProvider(localModelPath:context:)`
   returns a fresh `ILLMProvider` (on-device `LlamaProvider` or `OpenAIEndpointProvider` per Settings).
   `ILLMProvider.complete(prompt:) async throws -> String` is the one call. `generate()` in
   `MeetingReviewState` already builds providers this way — copy that pattern (fresh provider per call;
   the local one MUST be fresh each call — see the comment in `generate()`).
2. **A `WorkflowRunner`** (put the pure orchestration in `Sources/RuntimeCore/Workbench/` so it's
   host-testable with a fake `ILLMProvider`): walks `workflow.steps`, threading an intermediate text
   value. Suggested semantics:
   - input resolution: `.meeting` = the transcript text (or tacked-moments text); `.previousStep` =
     the prior step's output string.
   - `.llmCall`: `provider.complete(prompt: step.prompt.replacingOccurrences(of: "{input}", with: input))`.
   - `.summarize` / `.rewrite(tone:)`: a built-in prompt template over the input.
   - `.keepIf(keyword)`: a pure text filter (keep lines/sentences containing the keyword).
   - `.lens` / `.extract`: keep using the existing `ArtifactGenerationEngine` path (these already work).
   - output routing: `.artifacts` → save as `needs_review` artifacts (reuse `noteArtifact(...)` /
     the engine); `.note` → one note artifact; `.slack` → the propose→approve→execute path (there's a
     Slack connector on the desktop side; on mobile, at minimum show the egress badge + a draft —
     **do not silently send**; honor the `isEgress` flag).
3. **Drive the generation theater** while it runs (the theater reads
   `MeetingReviewState.genTypes/genDone/genCurrent/genFlourish`; adapt it to show step-by-step
   progress, or generalize it to "stages"). The owner LOVES the theater — keep that treatment.
4. **Host tests** for the runner with a fake provider (assert the prompt sent for an `llmCall`, the
   `{input}` substitution, the `keepIf` filter, step threading). Then build + device + screenshot a
   real run.

### Honesty rule
The owner explicitly values honesty about what's real. Until execution lands, the Workbench docs say
"runs the extract/lens path." Don't claim custom-prompt execution until it actually runs on the model.

---

## 4. Architecture you'll reuse (the Signal design system)

In `App/MeetingCaptureApp.swift`, near the top (`// MARK: - Signal palette` + `// MARK: - Signal
depth + motion`):
- **`Sig`** tokens: `bg/s1/s2/s3/text/muted/faint/accent(amber 0xFF6B35)/ok/warn/bad/local(cobalt)`;
  gradients `bgGradient`, `accentGradient` (amber→ember), `localGradient`, `topHairline`, `accentSoft`.
- **`SignalCard`** ViewModifier → `.signalCard(fill:radius:elevated:)` — the ONE elevation treatment
  (layered fill + top-lit hairline + soft shadow). Use it everywhere; don't hand-roll shadows.
- **`GlyphChip`** — gradient rounded icon container.
- **`PressableCard`** ButtonStyle — HIG scale-on-press for every tappable card.
- **`pixelAsset(name,size,fallback,tint)`** — renders a bundled PNG (full-color) or an SF fallback.
- Reduce-motion: gate repeating animations on `@Environment(\.accessibilityReduceMotion)`.
- **Generation theater** (`GenerationTheater`, near `MeetingDetailView`): the plasma-orb +
  type-constellation "thinking" visualization. Driven by real progress fields on `MeetingReviewState`.

**Inference** (`InferenceConfigStore`, a `@MainActor` singleton): `mode` (`RuntimeMode` local/homelab),
`endpointURL/endpointModel/endpointKey` (UserDefaults), `endpointConfig`, `makeProvider(...)`,
`fetchModels()` (GET /v1/models). `MeetingReviewState.generate(workflowTypes:)` branches on it.

---

## 5. Build / deploy / show loop + sim seeds + gotchas

**Build for the iPad (device 6B2F424D-707F-51F7-A33E-259427861CB1, "AjPed"):**
```bash
cd apple
ruby scripts/gen-meeting-capture.rb     # ALWAYS re-run after editing App/ or Sources/
xcodebuild -project build/HoldSpeakMeetingCapture.xcodeproj -scheme HoldSpeakMobile -configuration Debug \
  -destination 'generic/platform=iOS' -allowProvisioningUpdates -skipMacroValidation \
  -clonedSourcePackagesDirPath build/spm-meeting -derivedDataPath build/dd-meeting build
DEV=6B2F424D-707F-51F7-A33E-259427861CB1
APP="$PWD/build/dd-meeting/Build/Products/Debug-iphoneos/HoldSpeakMobile.app"
xcrun devicectl device install app --device "$DEV" "$APP"     # "App installed:" = success
xcrun devicectl device process launch --terminate-existing --device "$DEV" dev.holdspeak.mobile
# launch fails with "Locked" / "could not be unlocked" if the iPad is locked — INSTALL still succeeds.
# The "No provider was found" provisioning warning is benign — "App installed:" is the truth.
```

**Simulator screenshot (how you SHOW UI without the device — idb is broken):** build with
`-destination "platform=iOS Simulator,id=$SIM"` to `build/dd-sim`, `xcrun simctl install/launch`,
`xcrun simctl io "$SIM" screenshot`. Env flags MUST use the `SIMCTL_CHILD_` prefix. The app has
**simulator-only demo seeds** gated by `#if targetEnvironment(simulator)` + a body switch in
`MeetingListView.body` AND `onAppear` hooks — **a new gate must be added in BOTH places** (I lost a
build cycle when `HS_DEMO_WORKBENCH_LLM` was only in `onAppear`, not the body switch). Existing seeds:
- `HS_DEMO=1` → live capture canvas; `HS_DEMO_HOME=1` → home with seeded meeting rows
- `HS_DEMO_GEN=1` → the generation theater mid-flight (`GenTheaterDemo`)
- `HS_DEMO_SETTINGS=1` → Settings in endpoint mode (`SettingsDemo`)
- `HS_DEMO_WORKBENCH=1` → the builder (with a custom node); `HS_DEMO_WORKBENCH_LLM=1` → opens the LLM editor
- recorder states: `HS_DEMO_DOCK=top|bottom`, `HS_DEMO_MIN=1`, `HS_DEMO_TACK=1`, `HS_DEMO_TIDY=1`

**Gotchas burned this session:**
- `@State private var a = "", b = ""` is INVALID ("property wrapper can only apply to a single
  variable") — one `@State` per line.
- `cd` in a compound bash command can break the next command's cwd in this harness — prefer absolute
  paths or re-`cd`; `swift test` must run from `apple/`.
- Sheet config of an enum-with-associated-values step: seed local `@State` from the step in `onAppear`,
  write back via a `commit()` reconstructing the case (see `WorkbenchEditorSheet`).
- `.overlay(cond ? AnyShapeStyle(a) : AnyShapeStyle(b), ...)` for mixed Color/Gradient strokes.

**PixelLab MCP flow (use it!):** `create_1_direction_object(description, size: 96)` → ~30-90s →
`get_object(id)` (inspect 4 candidates inline) → `select_object_frames(id, indices:[n])` →
`get_object(promotedId)` → `curl` the `rotations/unknown.png` URL with **`dangerouslyDisableSandbox:
true`** → `apple/App/<name>.png` → add the name to the `%w[...]` list in `gen-meeting-capture.rb` →
use via `pixelAsset("<name>", ...)`. ~1.7k generations on the subscription.

---

## 6. Device-gated proofs still owed to the owner (do these AT the iPad with them)

- **14-12** constant-time transcription: eyeball the live cadence stays immediate late in a ≥10-min meeting.
- **14-13** spatial workspace: hardware feel — drag latency, snap/tack/resize haptics, Pencil vs finger.
- **14-11 / 14-10 / 14-03 / 14-01**: their only open boxes are device/live-mic verification → flip to `done`.
- A **real `.43`/LAN run**: Settings → LAN endpoint → fetch models → run a meeting through it + a Workbench workflow.

---

## 7. Remaining Phase 14 + the other track

- **HSM-14-15 (Workbench):** §3 (execution) is the big one; then the spatial-workspace stretch (14-13
  d5/d6: minimap, windowed panes → candidate 14-14).
- **Capture chrome + intelligence pane:** still on the older flat styling in places — apply the Signal
  primitives (the home + theater are the reference bar).
- **14-04/05/06** (interaction craft / accessibility / polish-QA) are unwritten placeholder stories.
- **Phase 8 (iPad on-device, Track I):** 8-05 air-gapped gate + 8-07/8-08 device proofs — all
  device-gated, owner now drives the iPad. See the older `HANDOVER.md` §3.

## 8. Canon / entry points
- Roadmap index + "Last updated": `pm/roadmap/holdspeak-mobile/README.md`.
- Phase 14 status (rich "Where we are" log + story table):
  `pm/roadmap/holdspeak-mobile/phase-14-mobile-experience-craft/current-phase-status.md`.
- Workbench design + build plan: `.../phase-14-…/story-15-workbench.md`.
- Voice/positioning canon (no prose, egress badge): `docs/internal/POSITIONING.md`.
- The single app file: `apple/App/MeetingCaptureApp.swift`. The engines:
  `apple/Sources/RuntimeCore/{Capture,Workbench}/`. Provider seam:
  `apple/Sources/Providers/Inference/`.
- **Commit ritual** (every commit): branch off `main`; stage only your files; `.tmp/CONTRACT.md`
  (8 boxes) + `.tmp/DESIGN-HANDOFF-OK.md` for UI; footer `Co-Authored-By: Claude Opus 4.8 (1M
  context) …` + `Claude-Session: …` (this IS authorized here — the hook accepts it); push → PR → wait
  CI green → merge (merge commit) → delete branch. Screenshots are the design-handoff mechanism.
</content>
