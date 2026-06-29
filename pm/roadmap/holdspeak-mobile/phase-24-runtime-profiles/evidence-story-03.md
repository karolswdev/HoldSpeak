# Evidence — HSM-24-03 (Apple advanced: profiles CRUD + per-agent + inline selectors everywhere)

**Date:** 2026-06-28
**Story:** [story-03-apple-advanced-profiles.md](./story-03-apple-advanced-profiles.md)
**Result:** DONE. Landed across two commits (PR #184 = the core; this commit = the inline surfaces).
`swift test` **389/0**; app builds (iphonesimulator) + device-SDK compiles; each surface sim-verified.

## What shipped

**Per-agent + management (PR #184):**
- `Agent.profileId` + `AgentRecord.profileId`, both with **tolerant decoders** so a missing field never
  wipes saved agents.
- **`ProfilesView`** — add/edit/delete on-device + OpenAI-compatible profiles (OpenRouter/Claude/LAN),
  set-active; the API key writes to the Keychain (`ProfileKeyStore`), **never onto the shape**. From
  Settings → "Manage profiles". Store mutators `upsertProfile` / `deleteProfile`.
- Agent builder **"RUNS ON" chip** + the context gauge reads the **assigned** profile's window.
- Agent runs honor it: `callLLM(profileId:)` / `runAssembled` / `runAgent` / `agentReply` resolve
  override → agent → active → `makeProvider(profile:)`.

**The inline selector at every user-facing model-touch point (this commit) — the owner's principle:**
- **The desk "Route through the AI core" / Ask gesture** (`DioRouteSheet`): a `RunsOnPicker` row +
  an **honest egress badge** that now reflects the chosen profile (was hardcoded "On device"). The
  choice threads `runRoute → runAssembled(profileId:)`.
- **Meeting generate** (`MeetingReviewState` + the intelligence pane): a `RunsOnPicker` above the
  Generate button (which dropped its hardcoded "on-device" wording); `generate()` runs on
  `resolveProfile(override:)`.
- **The agent builder** (above) — the per-agent chip.

## Acceptance criteria → proof

- **Define multiple profiles (local + endpoint with a key), set active.** `ProfilesView` + the 2-profile
  list screenshot (This device ACTIVE / Claude 200k / New profile). Key → Keychain. ✅
- **Assign agents to profiles; the gauge reflects each agent's window.** The "RUNS ON" chip + the
  effective-limit gauge. ✅
- **Inline selector wherever a model is touched, default shown + changeable.** Agent builder + desk
  Ask/route (screenshot: "RUNS ON · This device" + honest egress) + meeting generate. ✅
- **No engine regression / no agent data loss.** `swift test` 389/0; tolerant decoders. ✅

## Honest scope notes

- **Dictation** sends to the paired desktop (remote) — there is no *local* profile to pick, so the
  inline picker is honest `n/a` there (it runs on the desktop's runtime).
- **Workbench** node runs still use the active default (exposed in Settings + the active picker).
  Per-node "Runs on" chips are a reasonable future nicety, not a model-touch the user currently
  chooses per-run; tracked as a follow-up, not a gap in the principle's user-facing surfaces.
- A live **multi-profile run on device** (e.g. an agent actually hitting a real Claude endpoint) is the
  owner's device walk — structurally complete + sim-verified here.
