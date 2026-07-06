# HSM-15-11 — Agents on your desktop's models (pick the Mac's model, run through it)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** built + live-proven in the sim — 2026-07-06 (same day as the scaffold).
  The full run path shipped and was proven against the LIVE hub: hub `/api/ask` gained
  the manifest-bounded `model` override (real-metal control-vs-treatment on the
  192.168.1.43 llama.cpp: allowed model → real completion + honest egress; unknown
  model → 400 naming the runnable set), `RuntimeProfile.Kind.desktop` + the `callLLMTurn`
  dispatch cover recipes/chat/chains/live-lenses through the ONE seam, the Runs-on
  picker gained the "Your desktop" section (hub models BY NAME from the mesh manifests),
  and the `desktoprun` rig ran a real recipe sim→hub→llama.cpp: the printed card reads
  the model's answer wearing the hub-reported `Cloud · 192.168.1.43` badge
  (`screenshots/15-11-desktoprun-live-proof.png`). Remaining: the Phase-17 fidelity
  rider walk + the owner's cross-country proof (rows below). Original owner ask:
  (*"can we also extend the sync to also synchronize agent definitions and so on?
  I'd love to, when synced to the PC, have an option to select its local models too?
  And invoke them thru it?"*). Agent-definition sync itself already ships (Phase 17);
  this story is the run-path delta.
- **Depends on:** the paired peer (15-10, now proven NYC→Denver), `/api/ask`
  (HSM-16-04), model manifests on the wire (HSM-16-08), runtime profiles (Phase 24),
  the Workbench mesh dispatch precedent (HSM-15-02).
- **Owner:** unassigned

## Problem

The phone now pairs and syncs with the hub from anywhere. Your agents (recipes) travel
with you — but when you RUN one, the iPad/iPhone resolves the model through
`InferenceConfigStore.resolveProfile` and the only real choices are **on-device GGUF**
or a **raw endpoint**. The Mac sitting at home with 9B-class models and real fans is a
first-class sync peer and a second-class inference target: the Workbench can pin a
*node* to "Your Mac", but an agent chat, a recipe run, a chain, and an ambient marker
cannot say "think with my desktop's model".

## What already exists (grounded 2026-07-06 — do not rebuild)

- **Agent definitions sync** — `recipes`, `chains`, `workflows`, `profiles`, `kbs`
  ride `/api/sync/push|pull` (`sync.py` PRIM_TABLES; Phase 17, schema v8). The ask's
  first half is SHIPPED; this story only *verifies* it on-device (avatar, manualContext,
  kb link fidelity across the wire) as a rider row.
- **Model manifests both ways** (HSM-16-08) — every node pushes "this node has this
  model" rows; the desk caches the mesh's list in `meshModelsJSON`
  (`DeskDioramaStage.swift:3031`), and the hub's own model is named via
  `_hub_model_name`.
- **The RPC** — `POST /api/ask` (`web/routes/primitives/ask.py`): prompt + context in,
  output + honest per-run egress + the model that ran out; already resolves a hub-side
  **profile** (`prof.kind/base_url/model`). The Workbench's "Your Mac" node dispatch
  (15-02) is the working precedent end-to-end.
- **Per-recipe model choice** — `RecipeRecord.profileId` + the profile picker already
  exist on every recipe surface; profiles SYNC, so an id resolves on every device.

## The design — one new profile kind, not a parallel path

A **desktop-backed runtime profile**: `kind: "desktop"` (Phase 24's enum grows one
case). Selecting it on any recipe/chat/chain means: resolve the paired peer
(`DictatePeerStore` / `DeskHostLink`) and run the turn through `POST /api/ask`,
optionally pinning one of the hub's models. Everything downstream (picker UI,
`RecipeRecord.profileId`, sync of the choice itself) comes for free because profiles
are already the vocabulary.

- **The picker gains a "Your desktop" section** — populated from the synced model
  manifests + the hub's profiles, each row named by its real model (the 16-08 honesty
  bar: never "desktop" as an abstract word when we can NAME the GGUF). Unreachable peer
  = the row wears the mesh's `blocked · peer unreachable` state, never disappears.
- **`callLLM` / `runAssembled` learn the desktop kind** — one dispatch branch to
  `DeskHostLink.ask(...)` (mirror of the Workbench's HSM-15-02 branch), carrying the
  recipe's assembled blocks verbatim. No second prompt assembler.
- **Egress honesty** — the run's egress badge comes from `/api/ask`'s per-run egress in
  the response (16-04 contract), not inferred client-side: `local+LAN → <peer>` or
  whatever the hub truthfully reports (it may itself be on endpoint mode).
- **Offline = honest, not queued** — agent turns are interactive; an unreachable peer
  fails the turn with the mesh vocabulary and a one-tap fallback to the device profile.
  (Queueing belongs to sync and the Workbench queue, not chat.)
- **Hub-side gap to close** — `/api/ask` runs the hub's *active/selected profile*;
  verify whether a **model override** param exists for "this specific manifest row";
  add one if not (bounded to models the hub actually has — the manifest is the
  allow-list).

## Acceptance criteria

- [ ] **Verify (rider):** an agent authored on the hub arrives on the phone whole —
      name, avatar, role, system prompt, template, manualContext, kb link, profileId —
      and vice versa. Any fidelity gap becomes its own fix row here. *(Owner walk —
      still owed. Note: the sim pulled the owner's real agents whole during the proof.)*
- [x] **The picker:** every recipe/chat/chain profile picker shows a "Your desktop"
      section listing the hub's real models by name (from synced manifests, node
      `desktop` only — another node's model is not runnable there), with an honest
      blocked row when unpaired / nothing synced. (One RunsOnPicker feeds every
      surface; the menu-open screenshot rides the next sim pass.)
- [x] **The run:** a recipe turn with a desktop profile executes on the hub via
      `/api/ask`, renders the answer in the same run surface, and wears the per-run
      egress the hub reported (`Cloud · 192.168.1.43` on the proof card — the hub's
      OWN engine egress, never inferred client-side). Chains/chat/live-lenses inherit
      via the one `callLLMTurn` seam. Live-proven: `15-11-desktoprun-live-proof.png`.
- [x] **Model pinning:** picking a *specific* hub model runs THAT model (hub-side
      override, allow-listed to the hub's model + its profiles' models), and the run
      names it. Real-metal proof: allowed pin → the .43 Qwen3.5-9B answered; unknown
      pin → 400 `{"allowed_models": [...]}`. Pytest ×3 rides `test_web_routes_ask.py`.
- [x] **Offline:** with the peer unreachable, the turn fails in mesh vocabulary
      ("Your desktop isn’t reachable…" / "No desktop paired…") with the one-tap
      **Run on this device** alert action; nothing silently retargets.
      Screenshot-proven (the unreachable pass of the proof rig).
- [ ] **The proof:** owner runs an agent on the phone in another city; the answer is
      generated by the Mac's model (hub log + the run's named model as receipts) —
      the 15-10 NYC→Denver rig repeats as the walk. *(Owner walk — the sim proof above
      is the same wire from the same code; TestFlight build owed.)*

## Build plan

1. **Hub:** `/api/ask` model-override param (manifest-bounded) + test; confirm egress
   payload names the model. (Small; host-tested.)
2. **Swift:** `RuntimeProfile.kind = .desktop` + `InferenceConfigStore.resolveProfile`
   handling + the `callLLM` dispatch branch over `DeskHostLink.ask` (reuse the 15-02
   transport). Sim-provable against a live hub with the 15-10 rig
   (`HS_DESK_CONNECT` seed + injected pairing).
3. **Picker:** the "Your desktop" section fed by `meshModelsJSON` + synced profiles;
   unreachable state; screenshot-verified via the pre-upload card rig.
4. **Fidelity rider:** the Phase-17 agent-sync verification walk on the real phone.
5. **Docs + the cross-country proof run.**

## Test plan

- Hub: pytest for the ask override (allow-listed model, refusal on unknown, egress
  names the model). `uv run pytest -q -k ask`.
- Swift: host tests for profile resolution + dispatch selection; the sim rig run
  against a live hub (real `/api/ask` round-trip) before any device build.
- Device: the owner's cross-country agent run (acceptance row 6).

## Open questions (decide at build time, not silently)

- **Streaming:** `/api/ask` is request/response today; a long hub generation over DERP
  shows nothing until done. Ship v1 without streaming (spinner + the queue-HUD
  vocabulary), or add SSE first? (Lean: v1 without; streaming is its own story.)
- **Size bounds:** recipe context blocks can be large (KB + zone context); confirm
  `/api/ask` body limits and truncation vocabulary match the on-device runner's.
- **Chains that mix targets** (step 1 on-device, step 2 on desktop): allowed by
  construction since profileId is per-recipe — but the chain runner's progress UI
  should name where each step ran.

## Build log (2026-07-06)

- **Two real defects found by the proof rig** (`HS_DESK_RECIPES=desktoprun` — fires a
  REAL recipe run through the desktop profile against the live paired hub):
  1. **The desk's `desktopClient` never carried the pairing token** — every desk
     hub-run (recipes/chains/workflows via the run-target sheet, since 15-02) would
     401 against a token-requiring hub. Fixed: `DesktopPeer(host:port:token:scheme:)`
     built through `PeerAddress` (the ONE host rule), token joined at call time.
  2. **The sim pairing rig's defaults domain trap:** `simctl spawn <dev> defaults
     write dev.holdspeak.mobile …` lands in the sim USER domain; the containerized
     app reads its CONTAINER plist. Inject via
     `defaults write "$(simctl get_app_container <dev> dev.holdspeak.mobile data)/Library/Preferences/dev.holdspeak.mobile" key -string value`
     (and mind `-string` — a bare port writes an integer `@AppStorage` String readers
     silently drop).
- The hub half went in first and was proven independently: live curl on the restarted
  Denver hub (plain :8765, hublog retired, DB stamped v9 with a fresh backup) — the
  override ran the real .43 model and refused an unknown one naming the allowed set.

## Notes

- The sync half of the owner's ask is Phase 17's shipped work; this story is honest
  about only building the missing run path. See [[story-10-the-connect-surface]] for
  the pairing saga that unlocked it, and HSM-15-02's dispatch as the transport
  precedent.
