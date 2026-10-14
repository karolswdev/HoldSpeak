# Model discovery and download repair — 2026-10-13

Branch: `fix/model-discovery-download`. Base: `bcd1178b0` (#1198).
One combined repair for the owner's two reported blockers. Luna workers built
discovery, acquisition, and browser proof; Sol integrated and verified.
The settled direction is [DESIGN-model-discovery-download.md](philo/phase-17/DESIGN-model-discovery-download.md).

## What was wrong

- Existing detection checked loopback and saved endpoints. There was no LAN
  subnet scanner, including in the parked implementation. A new reachable
  server therefore required manual address entry before it became a choice.
- The suggested 4B Qwen's catalog used Hugging Face's Xet identifier as the
  downloaded file's SHA-256. The downloader correctly rejected valid bytes.
  The [pinned publisher file](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/blob/e87f176479d0855a907a41277aca2f8ee7a09523/Qwen3.5-4B-Q4_K_M.gguf)
  explicitly distinguishes the two hashes. Expected size was already correct.

| Field | Correct value |
|---|---|
| Repository/revision | `unsloth/Qwen3.5-4B-GGUF` / `e87f176479d0855a907a41277aca2f8ee7a09523` |
| Filename | `Qwen3.5-4B-Q4_K_M.gguf` |
| Bytes | `2740937888` |
| File SHA-256 | `00fe7986ff5f6b463e62455821146049db6f9313603938a70800d1fb69ef11a4` |
| Manifest SHA-256 | `b82ebc361b075d5b73abc33d07831733941515f66b51f204d3942684b1582d2a` |

## Delivered behavior

**Settings → Engines → Find on LAN → Found → Use it.** The explicit owner
action searches bounded attached private IPv4 networks at the four existing
engine ports. It reads `/v1/models`, returns transient actual model identities,
and reports partial/unavailable results honestly. Work runs off the hub event
loop. No prompts, saved keys, profiles, or assignment changes accompany the
search. Use it invokes the existing endpoint definition. Saved profiles are
deduplicated by normalized endpoint and model; concurrent detection reads do
not discard transient results.

**Download again.** Catalog revision 5 carries the corrected file/manifest
digests and a fresh valid Ed25519 signature. The old public trust root remains;
no private signing key is committed or logged. All four default artifact
locators now point to the corrected manifest. Tiny Qwen and Hammer were
independently checked against their pinned publisher metadata and were already
correct.

A fresh acquisition can reuse one of the newest five matching integrity
quarantines. Repository, revision, filename, format, size, SHA-256, and GGUF
magic must match the corrected plan. Expensive verification and transfer run
in the existing acquisition worker. Request handling performs only metadata
and stat checks. A reused complete file avoids network download and still
passes normal verification/install. Bad/unrelated bytes remain unaccepted.
Old failed records and source plans remain intact. Valid older pending plans
without the new storage bound continue after restart using their signed size.

## Observations and verification

Final integrated quick check is recorded at SHIP. Final composed captures
were refreshed after the footer correction and inspected at both widths.
Evidence is retained under `.tmp/models/` in the implementation worktree.

- Read-only owner observations: `/v1/models` at the named LAN server returned
  `qwen3.8-27b`. The actual production scanner subsequently found that server
  from `ifconfig` with no entered address: 253 hosts, four ports, not partial
  (`observed-lan.log`). No model inference or endpoint/profile write occurred.
- Read-only rejected-file observation: four 2,740,937,888-byte quarantines
  exist. The newest file's full SHA-256 matches the publisher's actual digest.
  Only that newest copy was hashed; this does not assert the other three are
  valid. No owner file, DB, configuration, or assignment was changed.
- Download focused proof: 136 tests collected; **134 passed, 2 existing
  faster-whisper availability skips** (`qwen-integrity-legacy-focused.log`).
  Covers valid quarantine reuse without synchronous hashing, wrong bytes,
  wrong identity, low storage, signature/manifest, and legacy pending restart.
- Discovery focused proof: **11 backend tests and 34 web tests passed**;
  scanner interfaces/probes are injected and tests never scan the owner's LAN.
- Real UI/hub integration: **9 passed** (`models-glass-final.log`), including
  both new LAN cases at 1440/393 and the existing selection, undo, consent,
  lost-update, download, and footer checks.
  The new cases cover actual scanner → route → decoder → Found → Use it → durable profile rows,
  with assignment identities unchanged and the saved server not duplicated.
  Network boundaries map a synthetic private host to a real loopback provider;
  these browser runs do not claim owner LAN access or real inference.
- Graph entry walks: `case.models.lan.entry` in
  [atlas-models.json](philo/graph/atlas-models.json), `lan-entry-1440` and
  `lan-entry-393`. Both pass and expose Find on LAN inside Settings; the cases
  intentionally do not trigger a LAN scan. Observations and before/after shots
  remain in `.tmp/models/walks/`. The rig cleans up its isolated DB afterward.
- Settings footer focused regression: **25 passed** (`settings-footer-final.log`);
  home → Engines → Settings keeps one footer and preserves navigation.
- Initial Send readiness regressions: **20 passed** (`sendbusy.log`) and
  **1 deferred chunk case passed** (`lazychunk.log`); corrected full sweep
  **106 passed, 3 existing xfails** (`send-sweep.log`).
- Canvas: four production-component captures in `canvas-shots/`; synthetic
  direction material only. Runtime browser shots live in
  `.tmp/evidence-shots/docs/internal/philo/phase-16/c-shots/p17-lan-{found,after-use-it}-{1440,393}.png`.

## Limits

The owner must retry Download after the repaired build reaches his hub; this
session does not install a model or change his assignments. Real inference
quality, runtime compatibility, and the owner's browser use remain unobserved.
LAN search covers IPv4 and common ports, with larger interface windows capped
and reported partial. Linux parsers are covered by synthetic tests; no Linux
hardware or actual iPad was exercised. Full main tape and Astra review follow
merge under the October 12 fast cycle.

## Week loading seam found during integration

The first combined run reproduced the previously open Week movement: 188 px
at 393. In-RAF traces then reproduced 188 px at 393 and 166 px at 1440.
At the first frame, the meeting Send well was absent. Its lazy chunk inserted
a 47.8 px panel at 25.9 ms; the destinations read expanded it to 165.8 px at
30.6 ms. Scroll remained zero and fonts were already loaded. These traces
identify the source of the movement; the earlier meeting-detail marker could
not cover work inside the later Send well. Traces remain in
`.tmp/models/quick-r1/desk-sweep-trace-week-{1440,393}.json`. Temporary browser
instrumentation was removed.

The shared lazy fallback now reports its actual pending chunk, and SendWell
reports its existing readiness calculation for destinations, sends, and
selected preview through `aria-busy`. Initial loading remains initial loading;
the surface no longer reports itself settled before those reads end. Final
regression and sweep results are recorded above at SHIP.

## Settings engine footer found during integration

The old engine glass checks assumed a separate wide Runs on window and an
always visible Undo. Engines now lives inside Settings: its initial 640 px
window selects list layout even on a 1440 px desktop, and phone secondary
verbs use More. Checks now use the real host Zoom for board gestures, choose
the exact phone alternative, and use More → Undo with durable assignment proof.

A separate genuine composition fault was reproduced after Zoom: the frame
ended at y=824 above the 76 px Dock, but the engine confirmation was at
y=830–858. Settings' generic footer and Runs on's footer both published to the
same frame slot. The second layout started after the first and overflowed the
slot. The repair gives Engines one composed footer and preserves its Settings
return action. It does not raise the window over the Dock or bypass pointer
checks. Diagnostic bounds remain in `.tmp/models/glassdiag3.log`.

The first integrated retry passed 3,472 web and 1,707 Python checks, then
identified the return Button's flat ghost material in six Settings sweep
cases. The return now uses the library's raised secondary variant. No sweep
thresholds or known-red entries changed.
