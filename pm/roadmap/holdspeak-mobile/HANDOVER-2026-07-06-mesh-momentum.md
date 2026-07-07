# HANDOVER — 2026-07-06 (evening) — mesh momentum: what shipped, what you build next

**Read this first if you're picking up the HoldSpeak mobile track.** It supersedes
[HANDOVER-2026-07-06-connect-saga.md](./HANDOVER-2026-07-06-connect-saga.md) as the
entry point (that one stays canon for the saga's autopsy and traps — read it second).
You are inheriting a machine that works: the phone pairs and syncs from another city,
agents run on the desktop's models, and the owner is actively dogfooding TestFlight
builds and sending feedback the same day. Your job is to keep that loop tight.

## The bar you're being held to

This project ships **craft, not plumbing** — a feature isn't done until it's shown,
designed, and usable (termination-level standard; see the working-agreement memories
and `docs/internal/POSITIONING.md`). Concretely:

- **Never ship a surface you haven't seen.** Screenshot rigs exist for everything;
  use them before any upload. `strings`-based binary checks LIE (twice — see the
  saga handover). Eyes on rendered pixels or it didn't happen.
- **Prove LLM features on real metal.** Control-vs-treatment against the real
  llama.cpp on `192.168.1.43:8080` (or the live hub on this Mac). A no-LLM pass
  hides broken features. Today's 15-11 proof found a 401 nobody knew about —
  that's what real-metal buys.
- **No prose in the UI.** Labels state WHAT in the fewest words. Egress is ONE badge
  (`EgressScope`: local / mixed / cloud), never a reassurance sentence.
- **Honest states or nothing.** The whole two-day saga happened because four distinct
  failures wore one mask ("Offline · queued"). Every error you surface must name its
  actual cause and, where possible, offer the one-tap next step.
- **PMO hygiene is mechanical.** Every commit needs a fresh `.tmp/CONTRACT.md`
  (template in `pm/roadmap/PMO-CONTRACT.md`), honest checkboxes, tests actually run
  and read. Every shipping commit updates the story header, the phase status row +
  "Where we are", and the project README's "Last updated" line.
- **Merge discipline:** push a branch, open a PR, **gate the merge on check
  CONCLUSIONS** (read the JSON — never chain watch→merge), merge with a merge commit.
  One PR per story or atomic chunk.

## What shipped today (2026-07-06, five PRs — all merged)

| PR | What | The receipt |
|---|---|---|
| #271 | The connect saga close + 15-11/15-12 scaffolds (was red on API-surface drift — `/api/mesh/info` gained its iOS consumer; regenerated) | phone syncs from NYC |
| #272 | The saga's repo debt 1–3: **schema v9** (v8 DBs take backup-then-apply, `model_manifests` lands), **tolerant ChangeSet wire** (`ArtifactType.runOutput` + per-record decode with a visible `undecodedRecords` count), **honest sync-pill states** (`DeskSyncDriver.Outcome.failure`: unauthorized / hubError(code) / contractMismatch / unreachable) | hub 3199 · Swift 484 · sim build green |
| #273 | **HSM-15-11 — agents on your desktop's models.** Hub: `/api/ask` manifest-bounded `model` override (allow-list = the hub's engine + its profiles' models; unknown → 400 naming the runnable set). Swift: `RuntimeProfile.Kind.desktop` + the **`callLLMTurn` seam** — the ONE dispatch recipes/chat/chains/live-lenses funnel through — with the hub-REPORTED per-run egress on the printed card; RunsOnPicker "Your desktop" section; one-tap "Run on this device" fallback | real-metal .43 control-vs-treatment · sim→hub→llama.cpp printed card (`phase-15-the-mesh/screenshots/15-11-desktoprun-live-proof.png`) · hub 3202 |
| #274 | TestFlight **build 7** bump (b7 = merged main at #273) | uploaded, VALID, attached to "Owner (internal)" |
| #275 | **Keyboard dismissal everywhere** (owner feedback on b7, fixed same-day): `KeyboardDismiss.swift` wired once at the app root — accessory-bar hide button + `.scrollDismissesKeyboard(.interactively)` + a window-level swipe-down (covers sheets) | iPhone-sim screenshot with the software keyboard up; **build 8** uploaded, VALID, attached |

**Two real defects found by proof rigs today** (this is why the rigs matter):
1. The desk's `desktopClient` **never sent the pairing token** — every desk hub-run
   since 15-02 would 401 on a token-requiring hub. Fixed via
   `DesktopPeer(host:port:token:scheme:)` through `PeerAddress` (the ONE host rule).
2. The sim pairing injection recipe was wrong (see Rigs below).

## Live state

- **TestFlight:** build **8** is current (keyboard dismissal + everything in b7).
  App record `6787764253`, internal group "Owner (internal)"
  `a3b39930-8c18-4261-8c82-6ab0096dc63b`. The connect card prints its own build
  number — trust the card, not TestFlight's version UI.
- **The hub (this Mac = the Denver Mac):** runs **PLAIN on :8765**
  (`HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_WEB_PORT=8765 uv run holdspeak web
  --no-open`), hublog proxy RETIRED, live DB stamped **v9** (pre-upgrade backup
  `~/.local/share/holdspeak/holdspeak.db.20260706-160553.bak`). Token `beef7b5e`
  in `~/.config/holdspeak/config.json → meeting.web_auth_token`. Doors:
  `http://100.93.120.0:8765` (tailnet, b6+) and the `tailscale serve` TLS front
  `https://karol-co-mac.tailad9943.ts.net:443`. The hub's engine is "cloud" →
  the LAN llama.cpp at `192.168.1.43:8080/v1` serving `Qwen3.5-9B-UD-Q6_K_XL.gguf`.
- **Owner walks pending** (owner-gated, not yours to close): the 15-11
  cross-country agent run on the real phone, the Phase-17 agent-sync fidelity
  rider, the 15-10 on-device green run, the Equilibrium couch session.

## Your unit of work (ordered)

1. **HSM-15-12 — the context envelope** (`phase-15-the-mesh/story-12`): the primary
   build. "Ground this ask": a picker on the chat composer/run sheet (meetings expand
   to transcript / intel / each bound artifact, gauge-priced live), ONE
   provenance-headed assembler shared by every run target, hub-side hydration
   (`/api/ask` gains `grounding` refs — ship ids not bodies over DERP), the
   KB-honesty rider (the hint string dies). Build plan and acceptance rows are in
   the story; step 1 is extracting the pure assembler from `recipeRoleAndContext`
   (`DeskDioramaStage.swift:~5000`) into a host-testable function. The 15-11
   `/api/ask` touch you'd extend is `holdspeak/web/routes/primitives/ask.py`.
2. **Owner-feedback fixes as they arrive.** The owner is dogfooding b8 and said "so
   many bugs" — expect a list. Each becomes a fix row → PR → next build. Today's
   keyboard fix is the template: reproduce, fix app-wide (not per-call-site),
   screenshot-verify, ship the build same-day.
3. **Repo debt row 4** (from the saga handover): retire or port the classic-home
   connect path (`PairMacSheet` in `CompanionMesh.swift`) — the desk card has
   better diagnostics now.
4. **Ops still owed:** remove the stale `tailscale serve` fronts on :8443/:34999
   (keep :443 — it's the TLS door; NEVER re-add a rule on :8765). The tailscaled
   socket wasn't reachable via the homebrew CLI this session — the GUI app owns it.
5. **Phase-15 remainder:** 15-02's open rows (connector sinks from a run / mesh
   source / workflow-level policy), 15-07 docs, then the 15-06 proof narrative.

## The rigs (use these; they end arguments)

- **Sim pairing injection (CORRECTED — the old user-domain recipe silently no-ops):**
  ```sh
  C=$(xcrun simctl get_app_container <SIM> dev.holdspeak.mobile data)
  xcrun simctl spawn <SIM> defaults write "$C/Library/Preferences/dev.holdspeak.mobile" hs.peer.host -string "127.0.0.1"
  xcrun simctl spawn <SIM> defaults write "$C/Library/Preferences/dev.holdspeak.mobile" hs.peer.port -string "8765"
  xcrun simctl spawn <SIM> defaults write "$C/Library/Preferences/dev.holdspeak.mobile" hs.peer.token -string "beef7b5e"
  ```
  Always `-string` — a bare port writes an integer that `@AppStorage` String
  readers silently drop (cost us a false "unreachable" today).
- **The desktop-run proof:** `SIMCTL_CHILD_HS_DESK_RECIPES=desktoprun`
  (+ `SIMCTL_CHILD_HS_DESK_MODEL=<hub model>`) fires a REAL recipe through the
  desktop profile against the live paired hub; the printed card must wear the
  hub-reported egress. Found the missing-token 401 in one pass.
- **Keyboard/screenshot rigs:** `HS_DESK_CONNECT=1` opens the connect card;
  `HS_DESK_KEYFOCUS=1` focuses its host field (software keyboard on:
  `defaults write com.apple.iphonesimulator ConnectHardwareKeyboard -bool false`
  + sim reboot). Full seed list: grep `HS_DESK_` in `DeskDioramaStage.swift`.
- **Sim build loop:** `ruby scripts/gen-meeting-capture.rb` (**COPIES sources —
  re-run after EVERY App/*.swift edit**) → `scripts/patch-llm-macro.sh <dd> <proj>
  HoldSpeakMobile` once per fresh derived-data → `xcodebuild … 
  -disableAutomaticPackageResolution build`. SourceKit single-file diagnostics on
  App files are NOISE (cross-file types); the target build is the truth.
- **TestFlight pipeline (headless, ~15 min):** bump `CURRENT_PROJECT_VERSION` in
  `gen-meeting-capture.rb` → gen → patch-llm-macro → `xcodebuild archive
  -configuration Release` with `DEVELOPER_DIR=/Applications/Xcode.app/...`
  (**release Xcode mandatory** — ASC rejects beta SDKs) + the three ASC auth flags
  (key `PUZZLQB758`, issuer `c1d852da-…`, `.p8` in `~/.appstoreconnect/private_keys`)
  → `xcodebuild -exportArchive -exportOptionsPlist build/export-options.plist` →
  poll `/v1/builds` for VALID, POST the group relationship (pattern:
  `asc_attach_b*.py`; needs `uv run --with pyjwt --with cryptography` — pyjwt alone
  lacks ES256). The archive's own CFBundleVersion reads "1"; the export renumbers.
  Internal group = no beta review; testable in ~2 minutes.
- **Hub tests:** `uv run pytest -q` (full), `-k ask` for the ask route; contract
  validator `uv run --with jsonschema python
  pm/roadmap/holdspeak-mobile/contracts/validate.py`; Swift `cd apple && swift test`
  (the App target is NOT covered — sim build + screenshot is its proof).

## Traps (the saga handover has the full list — these are new or re-confirmed today)

- **The api-surface manifest** (`docs/api-surface.json`) must be regenerated
  (`uv run python scripts/gen_api_surface.py`) whenever a route or a client call
  site changes — it's what broke #271's CI.
- **`ChangeSet` decode is now per-record tolerant.** Do NOT write tests expecting a
  bad record to throw; the contract is skip-and-count (`undecodedRecords`) — one
  SyncEngine test was re-pinned to this today.
- **Profiles sync.** A `desktop`-kind profile created on the phone lands on the hub;
  hub-side it resolves to the hub's own configured engine
  (`build_meeting_intel_for_profile` falls through) — correct by construction, keep
  it that way.
- **Chains mix targets per step** (profileId is per-recipe). The chain's final badge
  currently says `mixed("your desktop")` if ANY step ran there; per-step naming in
  the relay UI is an open question in story-11 — don't silently "fix" it.
- **Xcode-beta is the default toolchain** and cannot build swift-syntax —
  patch-llm-macro severs it. Only exports/archives need release Xcode.

## Memory pointers (auto-memory, `~/.claude/.../memory/`)

`project_phase15_the_mesh` (this track's state), `project_hsm_connect_surfaces`
(hub recipe + saga), `project_hsm_ipad_device_deploy` (TestFlight/ASC recipe),
`feedback_deliver_mobile_craft_not_plumbing`, `feedback_prefer_real_metal_proof`,
`feedback_no_prose_in_ui`, `feedback_gate_merges_on_conclusion` — keep them current
as you go; the index is `MEMORY.md`.

The loop you're stepping into is the best it has ever been: owner asks in the
morning, feature live-proven by evening, on the phone the same day. Match it.
