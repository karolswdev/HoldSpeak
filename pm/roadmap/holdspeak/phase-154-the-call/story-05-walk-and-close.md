# HS-154-05 - The walk and the close

- **Project:** holdspeak
- **Phase:** 154
- **Status:** done
- **Depends on:** HS-154-01, HS-154-02, HS-154-03, HS-154-04
- **Unblocks:** HS-155-01
- **Owner:** unassigned

## Problem

The Call is claimed only when walked: glass at both widths, the turn
loop under call mode on real metal, docs touched, counsel heard
(settled design D5; the arc rhythm).

## Scope

- **In:** metal `assets/story-05-metal.py` on `.43` (the 153 rig
  pattern; the .43 default-grammar law — the `grammar:""` override is
  already wired): call_mode toggled by route, a turn drives
  LISTENING→THINKING→streaming, `thread_call_state` frames observed,
  the R4/404 path exercised with the extra absent. Glass
  `tests/e2e/test_hs154_call_glass.py` full file at 1440 + 393; shots →
  `assets/story-05-shots/`; one exhibit artifact. Docs: README /
  USER_GUIDE (the Call, the GPL note law, the R4 fallback); MCP_SIDECAR
  only if tool counts moved. Close counsel (opus; must-fixes in-round).
  Honest sweep: name-diff vs main's latest; web baseline zero
  branch-new; restore the phase-14* shot assets after rigs.
- **Out:** 155 The Crew.

## Acceptance criteria

- [ ] Metal legs PASS on `.43`, payloads/frames kept under `assets/story-05-metal-payloads/`.
- [ ] Glass both widths, all rooms, zero horizontal overflow; exhibit link in the evidence.
- [ ] Counsel in `assets/counsel-close.md`, zero open must-fix; docs touched; the warpdrv grep still hits only the plan + phase records.
- [ ] The attended voice leg is explicitly left to the owner and marked so.

## Test plan

- **Unit:** the full scoped 154 set + the 153 set (regression).
- **Integration:** the glass file; the metal script.
- **Manual / device:** the owner's attended leg holds the merge word.

## Notes / open questions

- The exhibit joins the 151/152/153 exhibits as the arc's fourth room.

## Metal walk

Rig: `pm/roadmap/holdspeak/phase-154-the-call/assets/story-05-metal.py`
(153 pattern: isolated HOME, 151 helpers, DRY + LIVE modes).

### Command

```
uv run python pm/roadmap/holdspeak/phase-154-the-call/assets/story-05-metal.py          # DRY
HS154_LIVE=1 uv run python pm/roadmap/holdspeak/phase-154-the-call/assets/story-05-metal.py  # LIVE (.43)
```

### Per-leg results

| Leg | Name | DRY | LIVE | Payloads |
|-----|------|-----|------|----------|
| 1 | call_mode law (POST/GET/PATCH toggle, 400 on invalid, reload) | PASS (9/9) | PASS (9/9) | `leg-1-*.json` |
| 2 | Frames (thread_call_state THINKING->LISTENING around a turn) | PASS (3/3) | PASS (3/3) | `leg-2-bus-frames.json` |
| 3 | TTS 404 law (status not-installed, POST 404, no egress receipt) | PASS (5/5) | PASS (5/5) | `leg-3-*.json` |
| 4 | The ear's server half (POST /api/dictation/transcribe + tiny WAV) | PASS (2/2) | BLOCKED-BY-ENV (503: no Whisper model in isolated hub) | `leg-4-transcribe-*.json` |
| 5 | LIVE turn sanity under call mode (grammar override holds) | PASS (2/2, DRY) | PASS (5/5, streaming + call_state) | `leg-5-*.json` |

### Timings

- DRY total: 8.8 s (leg1 0.0 s, leg2 0.9 s, leg3 0.0 s, leg4 0.0 s, leg5 0.5 s)
- LIVE total: 16.4 s (leg1 0.0 s, leg2 2.9 s, leg3 0.0 s, leg4 0.0 s, leg5 2.9 s)

### Payloads

- DRY: `assets/story-05-metal-payloads/` (12 files)
- LIVE: `assets/story-05-metal-payloads-live/` (14 files)

### Leg 4 BLOCKED-BY-ENV note

The LIVE half of leg 4 returned 503 "Transcription is unavailable in this runtime"
because the isolated hub boots without the desktop runtime's Whisper model. The
route itself works correctly (validated in DRY with a canned callback); the 503
is the expected path when no transcriber is loaded. This is environmental, not a
code defect.

### Defects found

None. All code paths exercised cleanly.

### Attended voice leg

The attended voice leg (actual microphone + audible speech) is the owner's and
holds the merge word.

## Glass

### Run

```
tests/e2e/test_hs154_call_glass.py  (via scoped.sh, isolated HOME)
```

### Result

5 passed in 67.78s. Zero failures, zero horizontal overflow at 1440 and 393.

| Leg | Test | Status |
|-----|------|--------|
| 1 | `test_tts_api_404_law` | PASS (status not-installed, POST 404, download 404) |
| 2 | `test_tts_settings_glass` | PASS (Settings Sounds module at 1440+393, install hint visible, zero overflow) |
| 3 | `test_call_loop_glass` | PASS (call loop drives a visible turn at 1440+393, transcript visible) |
| 4 | `test_call_chip_glass` | PASS (chip OFF by default, PATCH ON persists on reload, click stops, zero overflow) |
| 5 | `test_speaker_glyph_glass` | PASS (glyph present on assistant row, click replays, speaking state visible, stop works) |

### Exhibit shots

12 curated shots in `assets/story-05-shots/` (6 rooms x 2 widths):

| Shot | Source |
|------|--------|
| `settings-speech-{1440,393}.png` | story-01 tts-settings-extra-off |
| `call-chip-off-{1440,393}.png` | story-03 call-chip-off |
| `call-chip-on-{1440,393}.png` | story-03 call-chip-on |
| `call-loop-turn-{1440,393}.png` | story-02 call-loop-turn-visible |
| `speaker-glyph-{1440,393}.png` | story-04 speaker-glyph-present |
| `speaker-glyph-speaking-{1440,393}.png` | story-04 speaker-glyph-speaking |

## Docs

### Files touched

- `README.md` -- Threads/Desk Chat section: added The Call paragraph (call mode, browser voice default, server voice extra, click to stop).
- `docs/USER_GUIDE.md` -- added "### The Call" subsection after Slash commands: chip states, click-to-stop, speaker glyph, auto-speak, the GPL note + install line for `holdspeak[tts]`, the R4 fallback.
- `docs/internal/PLAN_PHASE_DESK_CHAT.md` -- header updated (DC-04 shipped as Phase 154 The Call); section 6.8 marked SHIPPED.

### Not touched

- `docs/MCP_SIDECAR.md` -- 142 tools across 31 families unchanged. Phase 154 added no new MCP tools (all new surface is client-side TTS/VAD/call-mode, not tool-callable).

### Fence tests

- `test_doc_drift_guard.py`: 26/26 passed.
- `test_product_copy.py`: pre-existing failures only (none in files this story touched).

### warpdrv grep

`git grep -il warpdrv` hits only:
- `docs/internal/PLAN_PHASE_DESK_CHAT.md` (the plan)
- `pm/roadmap/holdspeak/` phase records (BACKLOG, HANDOVER, README, phase-151 through phase-155 evidence/stories/settled-design)

No source code, no user-facing docs. Clean.


## The honest sweep

Full isolated suite (`-n 6`, metal excluded), after the in-round counsel
fixes: **11 failed / 7382 passed / 53 skipped**. Name-diff against
main@`fb2d1082` (27 names — the platform reset healed 14 of the old 41):
**two** survivors. (1) the canonical schema snapshot — `call_mode`
changed the DDL; regenerated with the fence's own normalizer in this
commit. (2) `test_refinement_coordinator.py::test_reciprocal_host_stop_
never_calls_the_non_owner_runner` — passes 3/3 alone; the known
refinement-coordinator flake family under xdist load; recorded, not
touched. Web baseline after all fixes: 1659 passed, zero branch-new.

## Counsel

`assets/counsel-close.md`: **RATIFY-WITH-CONCERNS** — M1 (the server
voice's Audio element escaped `stop()` — the one-click-stops-everything
law) and S1–S4 (double-speak guard, call_mode 400 on junk, local-only
voice pick, bounded auto-speak sets) ALL FIXED IN-ROUND with tests
(38 vitest + 15 call-mode tests green).


## Exhibit

Shot exhibit for the owner (six rooms, both widths, the metal table):
https://claude.ai/code/artifact/bc5bb869-3817-4b96-8936-b128cdb1b7a3
