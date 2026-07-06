# HANDOVER — 2026-07-06 — the remote-pairing saga (builds 3–6) + what's next

**Read this first if you're picking up the mobile connect / mesh-sync work.**
Full autopsy lives in `phase-15-the-mesh/story-10-the-connect-surface.md`; this is the
operational handover: what's live, what's owed, and the traps that cost us two days.

## The one-paragraph story

The owner (phone in NYC, hub in Denver, Tailscale the only door) could not pair the
TestFlight app while Safari on the same phone reached the identical hub. **Five stacked
defects, one identical symptom** ("Offline · queued" / silence): (1) the build-≤2 manual
sheet never dialed; (2) the hub DB was missing `model_manifests` (additive DDL, no
schema bump); (3) the sync wire was undecodable by the Swift contract (`run_output`
enum value + naive microsecond timestamps); (4) a leftover `tailscale serve`
TLS-over-TCP interceptor on the hub port ate the app's cleartext while Safari's silent
HTTPS auto-upgrade "proved" the network healthy; (5) **the root: ATS** —
`NSAllowsLocalNetworking` alongside `NSAllowsArbitraryLoads` makes iOS silently ignore
ArbitraryLoads, and Tailscale CGNAT (100.64/10) counts as *public*, so every cleartext
dial died inside the phone (`URLError -1022`, zero packets, all builds since 1).
**Resolved:** the hub logged `POST /api/sync/push · auth=yes · ua=HoldSpeakMobile/5`
from NYC. The phone pairs and syncs.

## Live state (as of this handover)

- **TestFlight:** builds 5 and 6 uploaded, VALID, attached to "Owner (internal)".
  Build 6 = the ATS fix (plain `http://100.93.120.0:8765` works). Build 5 works via
  the TLS front only. **The connect card prints its own build number** in the header —
  trust the card, not TestFlight's version UI.
- **Working doors:** `http://100.93.120.0:8765` (build 6+) and
  `https://karol-co-mac.tailad9943.ts.net` port `443` (any build — a `tailscale serve`
  web front → 127.0.0.1:8765). Token `beef7b5e` in
  `~/.config/holdspeak/config.json → meeting.web_auth_token`.
- **The hub on the Denver Mac is still running behind the DEBUG logging proxy:**
  `/tmp/hublog.py` listens on 8765 → real hub on 8799
  (`HOLDSPEAK_WEB_HOST=0.0.0.0 HOLDSPEAK_WEB_PORT=8799 uv run holdspeak web --no-open`).
  Log at `/tmp/hub-requests.log`. **Cleanup owed:** kill both, restart the hub plain on
  8765, retire hublog. Note hublog logs only the FIRST request per TCP connection
  (keep-alive hides follow-ups) and binary TLS hellos print as garbage — both fooled us
  once.
- **Leftover `tailscale serve` web fronts** on :443 (keep — it's the TLS door), :8443
  and :34999 (stale — safe to remove). The **TCP interceptor on :8765 is OFF** — never
  re-add a serve rule on the hub port.
- **Branch/PR:** `holdspeak-mobile/build3-visible-connect`, PR **#271** (saga + both
  scaffolds), CI was pending at handover — **gate the merge on check CONCLUSIONS**
  (never chain watch→merge).

## Repo debt (owed, ordered)

1. ~~**Schema v9 bump**~~ **PAID 2026-07-06** (mesh-repo-debt PR): `SCHEMA_VERSION = 9`
   routes v8 DBs through backup-then-apply; pinned by
   `test_v8_db_gains_model_manifests_via_the_bump`. The owner's hand-fixed live DB reads
   as v8-with-the-table and upgrades cleanly (the DDL is `IF NOT EXISTS`).
2. ~~**`ArtifactType` tolerance**~~ **PAID 2026-07-06**: `case runOutput = "run_output"`
   added (enum + wire schema), and `ChangeSet.init(from:)` is per-record tolerant — a
   novel type drops that record into a visible `undecodedRecords` count, never the set
   (`ChangeSetToleranceTests`).
3. ~~**Honest sync-pill states**~~ **PAID 2026-07-06**: `DeskSyncDriver.Outcome.failure`
   classifies unauthorized / hubError(code) / contractMismatch / unreachable; the desk
   pill wears each ("Token rejected", "Hub error 500", "Hub reply unreadable") — only a
   dead network path says "Offline · queued", and "Synced" admits "· n skipped".
4. **Classic-home cleanup:** build 3's diagnostics went to `PairMacSheet` on the
   unreachable classic home; the desk card now has better ones. Consider retiring the
   classic-home connect path entirely.

## Next work (scaffolded, ready to build)

- **HSM-15-11 — Agents on your desktop's models** (`story-11`): a `desktop`
  RuntimeProfile kind; recipe/chat/chain turns dispatch over `POST /api/ask`; picker
  section fed by the synced model manifests; hub-side manifest-bounded model override.
  Agent-definition sync ALREADY ships (Phase 17) — verify fidelity, don't rebuild.
- **HSM-15-12 — The context envelope** (`story-12`): per-ask "Ground this ask" picker
  (meetings expand to transcript/intel/each artifact, gauge-priced), ONE
  provenance-headed assembler across run targets, hub-side hydration
  (`/api/ask` grounding refs — ship ids, not bodies, over DERP), KB-honesty rider.
- Build order: 15-11's hub `/api/ask` touch first; then 15-12's assembler seam.
  Everything is sim-provable against a live hub before TestFlight.

## The rigs (reuse these, they end arguments)

- **Sim pairing injection:** `xcrun simctl spawn <dev> defaults write
  dev.holdspeak.mobile hs.peer.host|port|token|name` → launch fires a REAL desk sync.
- **Card-on-screen before upload:** launch with `SIMCTL_CHILD_HS_DESK_CONNECT=1` →
  the connect card opens itself → screenshot. **Never ship a surface you haven't seen.**
- **Contract decode harness:** `xcrun swiftc -parse-as-library
  apple/Sources/Contracts/*.swift + a @main` that decodes the live `/api/sync/pull`
  JSON and prints the exact `DecodingError`.
- **TestFlight pipeline (headless):** bump `CURRENT_PROJECT_VERSION` in
  `gen-meeting-capture.rb` → `ruby scripts/gen-meeting-capture.rb` (COPIES sources —
  always re-run after edits) → archive/export with the ASC key flags
  (`DEVELOPER_DIR=/Applications/Xcode.app…`, key `PUZZLQB758`) → the
  poll-VALID-then-attach script (`asc_attach_b*.py` pattern; group
  `a3b39930-8c18-4261-8c82-6ab0096dc63b`). ~15 min end to end; Apple processed in <1 min.

## Traps that burned us (don't repeat)

- **`strings`-based binary verification LIES twice:** short literals (≤15 ASCII bytes)
  are register-packed and invisible; em-dashes split ASCII runs so the grep misses
  longer literals too. Verify with pure-ASCII substrings ≥16 chars AND eyes on the
  rendered surface. Two false accusations against a correct binary came from this.
- **ATS key interaction:** when ANY fine-grained ATS key is present, iOS ignores
  `NSAllowsArbitraryLoads`. The plist comment in `Capture-Info.plist` forbids re-adding
  `NSAllowsLocalNetworking` — honor it.
- **Safari is not a network probe** for app connectivity: it's ATS-exempt and silently
  upgrades to HTTPS. "Safari works, app doesn't" ⇒ check `tailscale serve status` and
  ATS before anything else.
- **iOS Local Network permission is a red herring for Tailscale:** VPN-routed traffic
  is never gated; the prompt/toggle only exist after a genuinely gated op (the desk
  card now browses Bonjour on open, which forces it).
- **Loopback sim proofs are ATS-blind** — 127.0.0.1 is exempt. Prove dials against a
  CGNAT/LAN address at least once.
