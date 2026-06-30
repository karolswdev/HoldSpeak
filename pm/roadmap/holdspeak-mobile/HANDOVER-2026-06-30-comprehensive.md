# HANDOVER — 2026-06-30 — Comprehensive (read me first)

An honest map for the next agent: what exists, where the product actually is, what shipped recently,
and the traps that will bite you. No spin.

---

## 1. The product, honestly

HoldSpeak is **two products in one repo**:

- **Desktop (Python, the real shipped product).** `holdspeak` is **LIVE on PyPI, v0.3.1** (launched at
  v0.3.0, Phase 65). It is a web-flagship runtime: a FastAPI server (`holdspeak/`) that serves an
  Astro-built UI (`web/` → `holdspeak/static/_built/`) for dictation + meeting intelligence, plus a
  CLI (`holdspeak web|meeting|dictation|doctor|import|backup|restore`). This is mature, tested
  (~3040 pytest), and people can `pip install` it. **When in doubt, this is the product.**

- **Apple mobile (`apple/`, NOT released).** A SwiftUI iPhone/iPad app (`apple/App/`) — the "Desk"
  (a 2.5D diorama, `DeskDioramaStage.swift`) where every concept is a draggable `DeskPrimitive`
  (meetings, notes, KBs, agents, chains, workflows, connectors, models, games, coders). It does real
  on-device Whisper (WhisperKit) + on-device LLM (llama.cpp via LLM.swift) **and** OpenAI-compatible
  endpoints. It is **far along but pre-GA**: it builds, runs on a real iPhone 17 Pro Max + iPad Air
  M4, and many flows work — but the gate is *craft on the real device*, not features. Most "done" this
  cycle is **Simulator-verified**; the owner walks the physical device and finds the real gaps.

- **Web flagship (served by the desktop hub).** The same Astro app also serves `/desk`, `/profiles`,
  `/dictation`, `/history`, `/settings`, etc. "Web is king" — a first-class authoring port.

**The honest gap:** the desktop is shipped and solid. The mobile app is a strong, beautiful
work-in-progress whose *daily-driver usability* is still being hammered out one owner device-walk at a
time. Do not represent mobile as released.

---

## 2. What shipped this session (2026-06-28 → 06-30)

### Phase 24 — Runtime profiles (CLOSED, PRs #182–#190)
A pre-GA architecture change: split the single inference config into named **RuntimeProfiles**
(on-device GGUF *or* an OpenAI-compatible endpoint) with **per-agent assignment** + an inline "Runs
on" picker at every model-touch point. Landed on **all surfaces**: Apple (contract + Keychain +
basic/advanced UI), the desktop hub (schema v4 + CRUD + agent-run resolution), and web (`/profiles`).
**The one hard rule, enforced + tested: the API key NEVER syncs** — the profile *shape* syncs; the key
lives in each surface's custodian (iPad Keychain / hub env `HOLDSPEAK_PROFILE_<id>_KEY`) and is joined
at request time. 24-06 added a cross-surface never-sync proof + entry-point docs. Detail:
[`phase-24-runtime-profiles/`](./phase-24-runtime-profiles/).

### The mobile desk-craft sweep (owner device walks, PRs #191–#200)
All on `DeskDioramaStage.swift` unless noted. Each was driven by the owner walking the real phone and
(rightly) calling out what was broken:

- **#191** — overlap dock + Record/New orb size parity + honest empty-zone inline hint.
- **#192** — recording UI no longer overlaps the list (hide `laneColumn` while capturing/weaving).
- **#193** — Qlippy (`DioCompanion`) removed from the phone lane (it floated over rows).
- **#194** — Record/New orbs anchored to the bottom edge (were at a `0.9·h` fraction).
- **#195** — iPhone **filing**: long-press a row → "File into…" a zone (the lane had NO drag, so this
  was impossible before). Shared `fileAny(id:into:)`.
- **#196** — the **meeting drawer**: a meeting's derivatives (summary/actions/agent-replies) group
  INSIDE its in-world pull-out (grouped by lineage: `provenance.sourceCardId` / `source==title`) and
  leave the loose desk. New `SectionBody.derivatives` + `DioPullout` card renderer.
- **#197** — desk **density**: the lane "All" drops the tools bucket (models/connectors/workflows →
  behind the "Tools" chip; they're not content); + `DioHero.densityScale` + wider `looseHome` spread so
  a full iPad desk shrinks-to-a-floor instead of piling up.
- **#198** — the **full editor** redesign (`MeetingDetailView` in `App/MeetingCaptureApp.swift`): one
  endless scroll → a premium segmented **Intelligence / Transcript / Notes** editor; back-button no
  longer overlaps the title; prose trimmed.
- **#199 / #200** — the **sprite library + per-object icon picker** (`SpriteStore.swift`): stable
  per-object variety (djb2 hash) + a "Choose an icon" gallery (`DioIconPicker`); **17 cassettes / 16
  notes / 16 crystals** generated via PixelLab, style-matched, globbed by `gen`.

Per-feature handovers: [overlap](./HANDOVER-2026-06-28-desk-overlap-emptyzone.md),
[meeting drawer](./HANDOVER-2026-06-29-meeting-drawer.md),
[sprite library](./HANDOVER-2026-06-30-sprite-library.md).

---

## 3. Where the mobile app genuinely stands

**Works / shipped (simulator-proven, on the device):** the desk diorama + lane (one app, every size);
in-world note/KB editing; meeting capture + on-device transcription; the meeting drawer; the full
editor; runtime profiles UI; filing (drag on iPad, long-press on iPhone); the sprite library + picker;
on-device + endpoint inference behind one `ILLMProvider` seam; sync to the desktop hub.

**Rough / not done (be honest about these):**
- **Daily-driver usability** is still being shaken out by owner device walks. The last several PRs were
  all "this is broken on my phone" fixes. Expect more.
- **The broader device-gap punch-list** from [2026-06-27](./HANDOVER-2026-06-27-device-gap.md) (kill any
  remaining dimmed-form modals → edit in-world; a speak-to-fill mic on EVERY text input) was largely
  addressed in PR #143 but the owner's standing rules ([[feedback_no_modals_in_world]],
  [[feedback_voice_mic_every_input]], [[feedback_no_prose_in_ui]]) are app-wide and easy to regress.
- **`ArtifactDetailView`** (open a single artifact) was left as-is (#198) — it's decent, not redesigned.
- **The meeting drawer is view-layer grouping**, not a true container (owner's explicit choice). Tools
  variety/picker covers meeting/note/kb only — not artifacts/games/agents (agents have their own
  100-avatar system).
- **Owner-only device proofs still pending:** a live multi-profile run against a real cloud endpoint
  with a real key in `HOLDSPEAK_PROFILE_<id>_KEY`; the air-gapped proofs; etc.
- **The Equilibrium parity program** (cross-surface contract parity, the EQUILIBRIUM.md track) is
  bigger than Phase 24 — many phases remain. The mobile README still points "Current phase" at
  **Phase 18**, which is stale relative to the cross-cutting work actually happening; reconcile if you
  resume formal phase work.

---

## 4. Build / run / verify (do this exactly)

**Desktop / web (Python):**
- Tests: `uv run pytest -q` (exclude the mic-bound file: `--ignore=tests/e2e/test_metal.py`).
- Web UI: edit `web/src`, then `cd web && npm run build` (the bundle `holdspeak/static/_built/` is
  GITIGNORED — commit source only). Run the hub: `holdspeak web` (loopback only; no `--host` flag).
- Web pages are Astro; **runtime-injected DOM needs `<style is:global>`** (scoped CSS won't reach it).

**Mobile (`apple/`):** `gen-meeting-capture.rb` **COPIES** sources into `build/meeting-capture-sources/`
and compiles the COPY — so **re-run gen after EVERY `App/**` edit** (the device/screenshot scripts do
this for you). The scripts:
- Device install: `apple/scripts/meeting-capture-device.sh 590C512D-66E2-5E72-B7FF-458B82B2AEC1`
  (iPhone 17 Pro Max). The phone must be **UNLOCKED** (else `xcodebuild` exits 70 / launch fails).
- Simulator screenshot: build for `-sdk iphonesimulator`, then `simctl install` (NOT just launch — a
  launch-only loop shows the STALE app), `simctl launch`, `simctl io <dev> screenshot <ABSOLUTE path>`.
- `swift test` does NOT build the App target — the only real verification is a full `xcodebuild` +
  Simulator screenshot, and ultimately an owner device walk ([[feedback_verify_on_device_not_seeded]]).

---

## 5. Traps that WILL bite you (hard-won this session)

- **Stale device build.** If a device build fails at the locked-device step it never compiles and the
  phone keeps the OLD binary; a later "successful" run can still serve stale objects from cached
  `build/meeting-capture-dd`. **For a guaranteed-fresh device build:**
  `rm -rf build/meeting-capture-dd build/meeting-capture-sources build/HoldSpeakMeetingCapture.xcodeproj`
  + `xcrun devicectl device uninstall app --device <udid> dev.holdspeak.mobile`, then run the script.
  Fastest fresh-build tell-tale for the owner: the lane "All" no longer lists Slack/Webhook/GitHub.
- **Swift 6 concurrency:** a mutable `static let shared` singleton is rejected; for something struct
  primitives read (e.g. `SpriteStore`), use a nonisolated UserDefaults-backed **enum**, not an
  `@MainActor` ObservableObject (which cascades onto the `DeskPrimitive` protocol).
- **Don't use `String.hashValue` for stable choices** — it's seeded per launch. Use a fixed hash
  (djb2) so per-object picks don't reshuffle every cold start.
- **Astro per-camera UI:** the desk reflows iPad diorama (`level()`) vs iPhone lane (`laneColumn`);
  overlays/empty-states often need to differ by `camera.isLane` (a centred card that's fine on the iPad
  canvas lands on top of lane rows).
- **PMO commit gate:** every commit needs `.tmp/CONTRACT.md` (7 `[x]`), freshly written; ≤1 story
  done-flip per commit (a `- **Status:** done` bullet + `evidence-story-NN.md`). Merge via **PR on
  green CI** (the slow check is "Integration Tests (macOS)").
- **Voice guard:** no prose em-dashes and no `HS-…` story IDs in `docs/*.md` (the guard fails CI).
- **PixelLab pipeline:** `create_1_direction_object` (top-down, 128px) + per-candidate
  `item_descriptions` = 4 distinct objects/call; max **8 in-flight jobs**; the default style matched the
  existing sprites (no base64 style-ref needed — that's token-heavy); `curl` the rotation PNGs with
  `dangerouslyDisableSandbox`; curate from ImageMagick `montage` contact sheets (cheap), then
  `dismiss_review`. Account had ~1740 generations.
- **The `.43` endpoint** forces a `{"line":...}` grammar; for clean endpoint proofs use a Mac
  `llama-server` (192.168.1.13:8081), per [[reference_lan_llm_endpoint]].

---

## 6. What I'd do next (suggestions, not orders)

1. **Owner device walk of this session's work** — the meeting drawer, the full editor, filing, the
   sprite picker, density. Expect 2–3 "this is off" items; fix them the same way (small PRs, screenshot
   + device install).
2. **Finish the in-world / no-prose / mic-on-every-input sweep** app-wide (the standing owner rules).
3. **`ArtifactDetailView`** polish if the owner wants the artifact editor to match the new full editor.
4. **Reconcile the mobile roadmap** ("Current phase" vs the cross-cutting craft + Phase 24) and decide
   whether to resume the Equilibrium parity phases formally.
5. **Owner-gated proofs:** the live multi-profile cloud run; air-gapped demos.

Memory index ([[project_primitive_framework]], [[project_mobile_agent_builder_and_profiles]],
[[project_phase65_the_launch]], the `feedback_*` rules) has the durable context; read it before acting.
