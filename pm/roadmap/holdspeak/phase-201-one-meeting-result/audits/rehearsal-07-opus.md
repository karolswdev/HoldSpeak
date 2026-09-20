# Rehearsal of the sitting — Opus worker, real LAN engine, fresh HOME, 2026-09-20

Read-only on main 321247d2; shots in assets/story-07-rehearsal/. Chartered stories 09, 10, 11 from its defects.

# REHEARSAL — HS-201-07, main @ `321247d2`, real LAN model, fresh HOME

Hub: `HOME=/tmp/hs201-sitting-KUkzJK`, port **8801**, `uv run holdspeak web --no-open`.
Startup line (both boots):
`HoldSpeak runtime identity: backend_commit=321247d2196f6f9085da90e4dad50eda3dabf918 frontend_build=7be1507203a70402 database_path=/tmp/hs201-sitting-KUkzJK/.local/share/holdspeak/holdspeak.db`

Pre-step: main's built bundle was **stale** (50 `web/src` files newer than `holdspeak/static/_built`); rebuilt in 4.5 s. Without it the sitting shoots Phase-200 pixels. Speech: `mlx-community/whisper-base-mlx`, 144 MB, downloaded **automatically at boot in 20 s** (23:13:46→23:14:06), no prompt, no face mention. Engine: `http://192.168.1.43:8080/v1`, `Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`. Mic never used: Record is hub-side capture (`/api/meeting/start`, `AudioRecorder` in `holdspeak/web_runtime.py:538`), so **Import** was used with `tests/fixtures/core_path_smoke_16k.wav` (2.79 s, "The quick brown fox jumps over the lazy dog.").

## STEPS

| # | Script says | What happened | Shot | s |
|---|---|---|---|---|
| 1 | One row "No engine yet" + "Choose an engine"; nothing else asks | Arrival is the **First Sentence gate**: "VOICE TYPING / Dictate one sentence / Speak. Then edit and keep your text." One extra click ("Continue later") to reach the desk. Then: `1 need you`, `NO CALENDAR Connect calendar`, `SETUP / No engine for summaries / Choose an engine`, `BRIEF / Generate / No brief yet`. **Two** things ask, not one; label is "No engine for summaries", not "No engine yet" | `01-arrival-{1440,393}`, `01b-arrival-after-gate-{1440,393}` | 9 |
| 2 | Models, pick engine, "Use this for summaries" | No such label exists anywhere in `web/src`. Models opens headed "No engine yet" with two Qwen downloads and `Add an engine...`. Typed the LAN URL (the placeholder *is* `http://192.168.1.43:8080/v1`) → **Check → 400 "Provider draft is invalid."**, message rendered ~400 px below the button, off-screen. Dead end. Defined the endpoint through the documented route instead; the face then showed `Qwen3.6 35B A3B ● READY 192.168.1.43 · LAN` on Meetings, but **"Use these" was disabled** because the unrelated *Speech recognition* row was WAITING. Had to set Speech recognition **OFF** to unblock it. Apply then succeeded; `summaryAssignment: assigned / lan-43-qwen / boundary lan / ready`; the SETUP row cleared | `02a…-{1440,393}`, `02b`, `02c`, `02d`, `02g`, `02h`, `02i`, `02-arrival-engine-chosen-{1440,393}` | 20 (+ dead end) |
| 3 | A meeting row with its length; no summary yet; no error | Meetings → Import → file → Title → Import. Row appeared: `JUN 03 · 1 MIN · ● RAN · 4 S · 192.168.1.43 · LAN`. **A summary was already there** — the product ran it on the LAN box by itself | `03a`, `03b`, `03c`, `03-meetings-list-{1440,393}` | 121.5 (first whisper load); 6.1 s on the second import |
| 4 | The host that WILL run it, before you click | **Not reachable.** No "Run summary" verb ever rendered — the row went straight to `RAN`. `planned_route` was ready in the payload; the face never had a pre-run moment to show it | `04-meeting-detail-{1440,393}` | — |
| 5 | The host that DID run it + the summary | Summary and `192.168.1.43 · LAN` badge shown. **`run_receipt` was `null`** for both auto-runs. An explicit run with the correct `expected_selection_hash` was refused `409 "Meeting intelligence is already ready"` | `04-meeting-detail-1440` | — |
| 6 | Restart, find the summary in ≤2 moves | Restart printed the same identity line. **1 move**: `Open` on the arrival's MEETINGS row → summary, transcript, host badge. Gate did not reappear | `06a-arrival-after-restart-{1440,393}`, `06-summary-after-restart-{1440,393}` | 18 boot + 4 |
| 7 | Dictate into another app | **Not rehearsed** (no keystroke injection, per brief). In-face mic ("Talk") toggled idle→active→idle and landed no text; the only failed requests were 8× `404 /desk/sfx/*.ogg`. Speech delivery *is* proven through the product's own transcriber: whisper-base produced "The quick brown fox jumps over the lazy dog." twice | `07a`, `07b`, `07c` | 65 |

## DEFECTS

1. **"Add an engine…" can never succeed.** `web/src/features/concierge/useConciergeController.ts:542-553` posts `{request_id,label,endpoint,model,requires_key}`; `holdspeak/services/model_library_service.py:277-294` demands the exact set including `profile_id`, `expected_profile_revision`, `provider_family`, and 400s on any mismatch. Verified live: face body → 400, lawful body → 200. **Tenet 3; Article IX.** HS-201-05's exit ("one engine and one assignment from the face") is not deliverable by a stranger.
2. **The summary runs itself, un-disclosed, with no receipt.** `holdspeak/meeting_import.py:362-378` enqueues an intel job with only a transcript hash — no route bundle, no selection hash. Result: contact with `192.168.1.43` before any gesture, `run_receipt: null`. **Article III (honest egress at the point of decision); Article VI.** This is the ledgered "hashless legacy entry point" — it is the *only* path a stranger without a mic can take, so the whole Phase-201 disclosure contract is unreachable in practice.
3. **"OFF" does not turn anything off.** Set Meetings → OFF, clicked "Use these", got no refusal; `/api/concierge/detect` still returned `summaryAssignment: assigned, lan-43-qwen`. The next import ran on the LAN again. **Article VI.** Seam: `apply` in `useConciergeController.ts` / Concierge Apply's assignment write.
4. **Models forgets the owner's choice.** Reopened, *Speech recognition* was back to `Quick local Qwen · WAITING` after being set OFF and applied, re-disabling "Use these" (`canApply`, `useConciergeController.ts:294`). The face shows a proposal, never the applied truth.
5. **One unrelated WAITING group blocks the whole apply.** To get a summary engine the stranger must switch *Speech recognition* off — the thing that transcribes his meeting. **Tenet 3.**
6. **Every desk load 500s.** `holdspeak/web/routes/roadmaps.py:147` — `next_data.get(...)` on `None`. 34 tracebacks across the two hub runs; one console error on every page. **Tenet 6.**
7. **393 Models card is broken:** "LAN Qwen 35B" overlaps "THOUGHTS & NOTES WRITING & DICTATION"; a `⚠ TOOL INCOMPATIBLE` badge with no plain reason (`02a-choose-an-engine-393.png`). **Owner ruling: errors never overlap UI.**
8. **Eight 404s for shipped assets** `/desk/sfx/{key-down,key-up,latch,land,error,file}.ogg`.
9. **The row lies about length:** `1 MIN` for 2.79 s, beside `5 S` (run time) in the same dot-line.
10. **The meeting lands in the past:** `started_at_ms = file.lastModified` (`ImportSection.tsx:38`) dated it **JUN 03**; the desk lists it under June.
11. **`transcription_status` stuck at `active`** after the transcript was final and the summary ready.
12. **No door to Models** once the SETUP row clears — not in the dock, not in Places (themes). Only ⌘K → "Models" (PROGRAMS) works. Same shape as the co-creator's "lost in Models" data point.

## THE SUMMARY (real model, LAN Qwen 35B)

> Meeting 1 — "The recording contains a standard pangram sentence with no substantive meeting content." (topics: `General`)
> Meeting 2, identical audio — "No meeting content detected." (topics: `[]`)

**Verdict as an architect:** honest and correctly traceable — it refused to invent content, named the host, and linked to the transcript; two identical inputs gave two different phrasings, so the wording is not stable. But **this says nothing about usefulness**: the only checked-in WAV is a 2.8-second pangram, so the model was never given a meeting. Usefulness is **unproven** — the owner's own sitting with real speech is the only thing that can settle it.

## RESTART — **1 move**

Ctrl-C → same command → same DB path printed → the arrival already lists `MEETINGS 2`; one click on `Open` shows the summary. Verified at 1440 and 393. Meets the ≤2 criterion.

## LANGUAGE (not plain English / not ASD-STE100)

`THE SET` · `PROBE` / `Test` · `WAITING` · `Use these` · `Adjust` · `RAN` · `Provider draft is invalid.` · `TOOL INCOMPATIBLE` · `HAS OPEN ACTIONS` (on a meeting with zero actions) · `OUTCOMES / REVIEW / RECORD / ARTIFACTS` · `Panes` · `Places` (means themes) · `Floor` · `Desk memory` · `TALK` · `Add an engine...` (a verb rendered as plain text, not a Button — **owner ruling: every verb is the library Button**) · `Nothing needs you` printed twice on one 393 screen · `1 need you` while two rows ask.

## WHAT THE OWNER WILL HIT FIRST (ranked)

1. The **First Sentence gate** demanding he dictate before he can look at his desk (step 1 mismatch).
2. **"Add an engine…" → "Provider draft is invalid."** — his .43 box cannot be connected from the face at all. If he uses cloud gpt-5-mini from his existing config the Models list may carry it; that path was **not tested** (his key is forbidden here).
3. **"Use these" greyed out** with no stated reason, until he switches Speech recognition off.
4. The **summary already ran** when the meeting appeared — steps 4 and 5 of his own script never happen; he never sees the host before the run, and there is no receipt after.
5. His **OFF choice silently ignored**, with fresh LAN egress after it.
6. Once set up, **no way back to Models** except ⌘K.

## UNKNOWN

- Whether the **Record** (microphone) path behaves differently from Import — not exercised by instruction; it is hub-side capture, so its Stop hook (the lane-A fence) was never entered.
- Whether the **cloud gpt-5-mini** row in his config connects from the face (his key never used).
- **Before/after row counts of the three ungated loops** — not measured; no baseline was taken before the first import.
- Dictation **into another app** — not rehearsed. The in-face mic landed no text in this rig; cause unknown (fake-audio capture may not feed the AudioWorklet).
- Why two identical inputs produced different summaries beyond ordinary model nondeterminism.

Scratch HOME `/tmp/hs201-sitting-KUkzJK` — **hub stopped and the directory deleted** after these findings were recorded. No tracked file in the tree was modified (`git status --porcelain` shows only the new untracked folder `pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-07-rehearsal/`; the rebuilt bundle under `holdspeak/static/_built/` is gitignored, `.gitignore:58`).