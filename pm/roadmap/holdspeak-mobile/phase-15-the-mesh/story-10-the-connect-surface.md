# HSM-15-10 — The Connect surface ("Your Computer" / discovery-first pairing)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** in-progress — opened 2026-06-22 (owner: *"Where do I set up the computer and connect
  to? Have you thought about creating a new place for that? a lot of these have got a lot of
  discovery verbs."*). **2026-07-06: the remote-pairing saga — five stacked defects found and
  fixed across builds 3–4 (see the section below); connect is proven end-to-end in the
  Simulator against the live hub; the owner's on-device green run is the remaining beat.**
- **Depends on:** `HTTPDesktopClient`/`DictatePeerStore` (the paired peer), the desktop `holdspeak web`
  LAN bind + `web_auth` token.
- **Owner:** unassigned

## Problem

The whole mesh hangs off one thing — the iPad being paired to your computer — and there is **no place
to do it**. Today: run `holdspeak web` on the LAN, dig the Mac's IP + auth token out of the CLI, and
hand-type host/port/token into a modal buried in the dictation flow. No discovery, no status, no home.
Grounding (2026-06-22): the desktop advertises **nothing** on the network (no Bonjour/zeroconf); auth
is a manual bearer token (`web_auth.py`) + the device PSK (`holdspeak device-psk`).

## The design — discovery-first, a first-class place

- **Desktop advertises** itself via **Bonjour** (`_holdspeak._tcp`, the server name + port) when it
  binds off-loopback, so the iPad can FIND it by name — no IP typing. (New desktop work; behind the
  LAN-bind mode.)
- **The iPad "Your Computer" surface** (a first-class screen, reachable from the home + wherever a
  feature needs pairing): **browses the LAN** (NWBrowser / Bonjour), lists discovered computers by
  name + reachability, tap-to-connect (host/port come from discovery). The **token** arrives via a
  short **pairing code / QR** the desktop shows (not hand-typed). Live status (reachable / asleep),
  and manage / forget peers. The home of the connection every mesh feature reads.
- **Honest + native:** uses the platform's discovery (Bonjour) and a real pairing exchange rather than
  reinventing — the "native conventions" bar. No prose; tight status chips.

## Acceptance criteria

- [ ] **Desktop Bonjour** — `holdspeak web` advertises `_holdspeak._tcp` (name + port) when bound
      off-loopback; verified discoverable on the LAN. A lightweight unauthenticated `GET /api/mesh/info`
      (name, version, requiresToken) so a discovered server identifies itself.
- [ ] **iPad Connect surface** — a first-class "Your Computer" screen that browses Bonjour, lists
      discovered computers (name + reach), tap-to-connect (discovered host/port), and persists the peer
      via `DictatePeerStore`. Simulator-shot (seeded discovery list).
- [ ] **Pairing** — the token arrives via a pairing code / QR shown by the desktop (a desktop pairing
      affordance + an iPad enter/scan), not hand-typed. (v1 may fall back to a manual token field with
      clear guidance if the code exchange is deferred — but discovery of host/port is the bar.)
- [ ] **Status + manage** — reachable / asleep chip; forget/re-pair. Every mesh feature reads this one
      paired peer.

## Build plan

1. **Desktop:** Bonjour advertising (zeroconf) on LAN bind + `GET /api/mesh/info`. Host-tested where
   possible. (Foundational half — built first, non-colliding.)
2. **iPad:** the "Your Computer" Connect surface — Bonjour browse (`NWBrowser`), discovered list,
   tap-to-connect, status, manage; a home entry. Simulator-proven.
3. **Pairing code / QR** the token exchange (desktop shows a code; iPad enters/scans). Can be a second
   slice if the discovery slice ships first.

## Test plan

- Desktop: unit/integration for the advertising toggle + `/api/mesh/info`; manual LAN discovery check.
- iPad: the discovery→connect flow Simulator-shot with a seeded list; a real LAN discover+pair is the
  owner-at-the-iPad proof.

## The remote-pairing saga (2026-07-05/06) — five stacked defects, builds 3 + 4

The owner, remote (phone in NYC, hub in Denver, Tailscale the only door), could not pair the
TestFlight app: the desk pill sat on "Offline · queued" while the same phone's Safari reached
the identical hub. Every one of these was REAL and each masked the next:

1. **The manual sheet never dialed** (build ≤2): `PairMacSheet` bound fields and dismissed —
   no probe, no feedback. **Build 3** gave it a real Test (handshake + on-screen `WILL DIAL`
   URL + the `URLError` reason). But the sheet is on the CLASSIC home, not the desk front
   door — the surface the owner actually uses is `DioConnectCard`, which stayed bool-only.
2. **The hub DB was missing `model_manifests`** — the table was added to `SCHEMA_SQL` without
   bumping `SCHEMA_VERSION` past 8, so a v8-stamped DB no-ops the DDL; `/api/sync/pull`
   500'd forever. (Rider: bump schema v9 in the repo — every other v8 DB breaks identically.)
3. **The sync wire was undecodable by the Swift contract** — two independent poisons, proven
   by compiling `Sources/Contracts/*.swift` into a decode harness against the live pull JSON:
   a run-born artifact carried `artifact_type: "run_output"` (Phase-74 hub concept, absent
   from the Swift `ArtifactType` enum → the WHOLE ChangeSet decode fails), and `_iso()` in
   `web/routes/sync.py` emitted naive `datetime.isoformat()` (microseconds, no timezone —
   Foundation `.iso8601` rejects both). Fixed `_iso` (strict seconds+`Z`, this commit),
   retyped the row, normalized ~110 stored rows. (Riders: `runOutput` case + unknown-tolerant
   enum decoding in Swift; the driver folds 500/401/decode-fail/no-network into ONE
   "Offline · queued" state — give it honest error states.)
4. **The killer: a leftover `tailscale serve` TLS-over-TCP interceptor on port 8765** (parked
   in tailscaled state during the build-2 proxy investigation). Every tailnet connection to
   the hub port had to speak TLS: Safari silently auto-upgrades to HTTPS so it handshook and
   *looked like proof the network was fine*, while the app's plain-HTTP died inside
   tailscaled — zero packets at the hub, zero iOS prompts, surviving reinstall + reboot.
   `tailscale serve --tls-terminated-tcp=8765 off`. **Lesson: when one app dials and Safari
   works, read `tailscale serve status` FIRST.**
5. **Build 4** hardens the surface the owner uses: `DioConnectCard` gains the literal
   `WILL DIAL` line + the exact probe reason (HTTP status / `URLError` code — this bug would
   have read "SSL error" on screen in one tap); a new `PeerAddress` helper (DeskSync.swift)
   is THE one host-parsing rule for every dial site (card, sync driver, host link, dictate
   peer, mesh-info) and understands an `https://` host prefix, so a TLS front
   (`tailscale serve` at `https://<mac>.ts.net`, 443) is a first-class door; opening the card
   starts the Bonjour browse, forcing iOS to surface the Local Network prompt.

**THE FINAL ROOT CAUSE (2026-07-06, builds 5–6) — ATS was vetoing every dial client-side.**
The plist carried `NSAllowsArbitraryLoads` AND `NSAllowsLocalNetworking`; when the
finer-grained key is present, modern iOS **silently ignores ArbitraryLoads**, so the
effective policy was "HTTPS except local" — and iOS counts only RFC1918 as local. A
Tailscale CGNAT address (100.64/10) reads as PUBLIC internet → cleartext refused inside
the phone (`URLError -1022`), zero packets, no prompt, every build since 1. Safari is
exempt from app ATS (and auto-upgrades to HTTPS), which made the network look healthy;
the Simulator "proof" dialed 127.0.0.1 (loopback-exempt) and was blind to it. **Fix
(build 6): drop `NSAllowsLocalNetworking` — never re-add it.** Interim door that
confirmed everything (build 5): `tailscale serve` HTTPS front
(`https://karol-co-mac.tailad9943.ts.net`, 443) — the phone connected from NYC and the
hub logged `POST /api/sync/push · auth=yes · HoldSpeakMobile/5`. **The phone pairs and
syncs.** Build 5 also added: the build number ON the connect card (ends
which-binary-is-installed arguments; TestFlight's export rewrites `CFBundleVersion`, so
the static plist "1" is renumbered at upload) and the `HS_DESK_CONNECT=1` sim seed so
the card itself is screenshot-verified BEFORE upload (the build-4 lesson: `strings`
verification lies twice — short literals are register-packed and em-dashes split ASCII
runs; verify with pure-ASCII substrings + eyes on the rendered surface).

**Repo debt paid (2026-07-06, the mesh-repo-debt PR):** the saga's three code riders shipped
together: (1) `SCHEMA_VERSION` → 9, so every v8-stamped DB takes the backup-then-apply path and
gains `model_manifests` (regression pin: `test_v8_db_gains_model_manifests_via_the_bump`);
(2) `ArtifactType` knows `runOutput` AND the `ChangeSet` decode is per-record tolerant — a novel
type drops that one record into a visible `undecodedRecords` count instead of failing the set
(`ChangeSetToleranceTests`; the wire schema's `artifact_type` enum gained `run_output`);
(3) `DeskSyncDriver` classifies failure (`unauthorized` / `hubError(code)` / `contractMismatch` /
`unreachable`) and the desk pill wears each honestly — only a dead network path may say
"Offline · queued", and "Synced" admits "· n skipped" when the tolerant decode dropped rows.
Still owed from the saga: the classic-home connect cleanup (debt row 4) and the hub-side
hublog/serve teardown (ops, not repo).

**Debug rig (reusable):** the logging proxy (`/tmp/hublog.py`, 8765→hub) shows arrivals per
TCP connection (keep-alive hides follow-up requests — a "missing" pull can be an unlogged
same-connection ride); `xcrun simctl spawn <sim> defaults write dev.holdspeak.mobile
hs.peer.host/port/token` injects a pairing so a Simulator launch fires a REAL desk sync
against the live hub; the compiled-contracts decode harness prints the exact `DecodingError`.
Evidence: Simulator "Synced · just now" against the live hub with the full desk pulled
(screenshots in the session log); build 4 uploaded, VALID, attached to the internal group.

## Notes

- This is the connection HOME the mesh was missing — the owner flagged it after the dictation surface
  shipped pairing-aware but with no place to actually pair. Discovery (Bonjour) is the headline "verb".
- Reuses `DictatePeerStore` (the persisted peer) so dictation / Agent Desk / Queue HUD all benefit at
  once. See [[story-01-dictation-into-your-mac]], [[story-08-the-agent-desk]].
