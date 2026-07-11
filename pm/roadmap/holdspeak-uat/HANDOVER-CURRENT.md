# HANDOVER — current state (2026-07-09, mid-sitting)

> The original [`HANDOVER.md`](./HANDOVER.md) was the "build the framework
> overnight" spec — **done**. This doc is the live state: the framework +
> the full protocol are built and merged, the conductor is **hosted right now**,
> the owner is **mid-sitting**, and the first findings are surfacing.

> **Protocol-v2 update:** the mid-sitting statements below preserve the
> 2026-07-09 historical record. That sitting used the superseded
> web/iPad/iPhone surface model and must not be resumed or promoted as native
> acceptance evidence. Current execution uses `web_react`,
> `ios_flagship_swift`, `ios_companion_swift`, and `ios_classic_swift` with
> explicit compatible form factors. React Desk and Swift Desk are separate
> campaign legs; viewport evidence never fills a Swift slot.

## 1. What this is / where

The **holdspeak-uat** rig lives under `uat/`. Start it:

```bash
cd /Users/karol/dev/tools/HoldSpeak
uv run python -m uat.conductor            # localhost:8799
UAT_HOST=0.0.0.0 uv run python -m uat.conductor   # LAN-bound for devices
```

Ad-hoc (no sitting): `uv run python -m uat.stage --list | --recipe R | --seed S`.
Docs: `uat/README.md` (runbook), `uat/AUTHORING.md` (author scenarios/recipes/seeds,
incl. `manual_setup`).

**Canon:** the conductor never imports the `holdspeak` package — it drives the
product only as a subprocess (`holdspeak web`) and over HTTP. Enforced by
`tests/uat/test_no_holdspeak_import.py`. Respect this in any extension.

## 2. What's DONE and on `main`

- **The framework** (Phase 1, 6 stories): conductor (isolated runs, boot/health/
  teardown/restart, LAN), induction engine (decks/seeds/recipes/probes, mesh
  nodes), scenario contract + feature ledger (`uat/features.yaml`, every phase
  mapped), the React+Vite guided site, the debrief + triage, docs. All merged.
- **Voice notes** — speak-to-fill on every note field (run's own transcribe route).
- **Ad-hoc staging + full-primitive seeding** — `uat/stage.py`; seed manifests
  create notes/kbs/zones(directories)/recipes/chains/workflows/profiles/meetings.
- **Review loop** — reopen a past sitting → its recorded findings + triage render.
- **Manual-staged protocols** — the contract accepts `manual_setup` (a human
  staging checklist) in place of a recipe, so a must-do we can't harness is
  still a first-class protocol.
- **Harness backlog top-3** (from the re-eval): **live steering** (spawn/arm/
  keys/audit via `/api/coders`), **honest learning-count**, **key-never-syncs
  attack**. All proven live.
- **The protocol: 115/115 must-do capabilities have a scenario** — 105 scenarios
  across 9 packs (smoke, aftercare, steering, dictation, honest-failure, desk,
  mesh-edge, mobile, connectors), 0 contract errors, independently verified. 26
  are `manual_setup`. Every auto-staged recipe proven live (incl. `.43` connectors).

`dw check holdspeak-uat` green. Coverage docs:
`phase-2-the-inventory/{PROTOCOL-REEVALUATION,PROTOCOL-COVERAGE,MUST-TEST-COVERAGE}.md`.

## 3. What's RUNNING right now

- The conductor is **hosted** (background), `UAT_HOST=0.0.0.0` on **:8799**
  (LAN: **http://192.168.1.36:8799**). It may still be up — check
  `curl -s localhost:8799/api/health`; re-launch if not.
- A **live sitting on `pack-a-aftercare`** is staged: a golden-43 run
  (product Web Desk at **http://127.0.0.1:8788/**, loopback) with the Pylon
  meeting imported + **4 open actions** from real intel on `.43` (which is UP).
- The owner is walking it. Verdicts land in the run DB the moment cast
  (`uat/_runs/uat.db`); a refresh loses nothing; the sitting resumes.

## 4. FINDINGS so far (not yet filed to BACKLOG)

1. **`/welcome` wizard loop (product bug).** Finishing the wizard bounces back
   to step 1. Root cause: `web/src/pages/index.astro:27` redirects to `/welcome`
   whenever `setup_status.first_run` is true, and `first_run` clears ONLY on the
   `FIRST_DICTATION_SUCCESS` milestone (`setup_status.py:194`) — set by a
   successful dictation, **not** by finishing the wizard. So anyone who finishes
   onboarding before landing a first dictation (fresh machine, no mic/model, or a
   sandboxed run) is trapped. **Fix:** a distinct `WELCOME_DISMISSED` milestone
   the desk redirect gates on — onboarded ≠ has-dictated. → `holdspeak` BACKLOG.
2. **Harness UX: mute staging spinner.** A staging beat that runs intel (2–4 min
   on `.43`'s 9B model) shows a frozen-looking "booting and applying…" with no
   progress — it looks hung. The staging panel should show the current recipe +
   a "running intel on .43, this takes a few minutes…" live line. → harness fix.
3. **Three-surface gap: the product doesn't travel to devices.** A sitting boots
   the product loopback-only (`SittingManager.create` → `create_run(lan=False)`),
   so devices reach the guided *site* (:8799) but not the Web Desk (:8788).
   Default the sitting's run to LAN-bound so the product travels too. → historical
   harness finding. Protocol v2 additionally showed that reachability alone is
   insufficient: native evidence now requires the exact Swift target/form
   factor and a matching pairing-verified device attestation.

## 5. What's NEXT (queued)

- **Finish the sitting + triage.** The owner walks packs; then open the debrief
  together, set dispositions per `uat/TRIAGE.md`, and paste `fix`es into
  `pm/roadmap/holdspeak/BACKLOG.md` (harness proposes the block, human commits).
- **Phase 4 — The Owner Functional Pass**
  ([`phase-4-the-owner-functional-pass/`](./phase-4-the-owner-functional-pass/))
  is active. The guided site leads with seven ordered campaigns spanning 90
  functional scenarios / 327 target-qualified observations. Campaign 1 is
  `web_react:desktop`; Campaign 5 independently exercises flagship Swift Desk
  and native workflows on physical iPad/iPhone. Campaigns 1–5 are the core pass;
  campaign 6 is connected integrations; campaign 7 is conditional on exact
  companion/classic builds. Use `uat/FUNCTIONAL-PASS.md` as the execution canon.
- **Phase 3 paused at 2/5.** Mesh dispatch and cloud-egress shipped. The owner
  explicitly declined the next drift/schema/network-hardening story; do not
  resume HSU-3-03 without a fresh owner decision.
- **Never revive “three surfaces, one script.”** Parity joins independently
  executed target-specific legs. Responsive React and physical-device browser
  evidence do not substitute for Swift.

## 6. Gotchas

- **PMO gate every commit** (`.githooks/dw contract new` → flip boxes → commit;
  never `--no-verify`). Roadmap-status and code commits both pass the gate.
- **Commit-built dist:** `uat/web/dist` is committed (root `.gitignore` has
  `dist/`, re-included via `uat/.gitignore`); rebuild with
  `npm --prefix uat/web run build` after editing `uat/web/src`.
- **`.43`** = `http://192.168.1.43:8080` (llama.cpp). The sandboxed Bash tool
  can't reach the LAN — use `dangerouslyDisableSandbox: true` for any run that
  must hit `.43` (the intel packs a/c/e/g + mesh).
- **Steering** spawns tmux sessions named `uat-<run>-<name>`, killed on teardown.
  NEVER `tmux kill-server` (it would kill the owner's sessions).
- **Intel-heavy staging is slow** (minutes). For a fast first sitting, start with
  `smoke` or `pack-d-honest-failure` (fully local).
- **One story flips `done` per commit.** Most recent harness work shipped as
  gate-passing commits that flip no story (enhancements) — that's accepted here.

## 7. PRs this session (all merged to `main`)

Framework #318–#323; voice #324; ergonomics/seeding #325; review-loop #326;
protocol authoring #327; Phase-3 scaffold #330; steering #328; dict/trust #329;
must-test coverage (115/115) #331. Branch base is clean `main`.
