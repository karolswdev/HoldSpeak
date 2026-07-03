# HSM-18-06 — the real-metal walk (press-play protocol)

The owner's device session, prepared. Everything below was staged headless on
2026-07-03; the walk itself needs the cabled iPad, a live hub, and a working
rewriter endpoint. Budget: ~30 minutes once the endpoint answers.

## 0. Pre-flight — the rewriter endpoint: use `.43` (verified 2026-07-03)

`.43` is the pick. The "forced grammar" is per launch script, not the box:
`~/run-qwythos-intel.sh` pins the `{"line"}` grammar (that script would still
break the classify — keep it off), while `~/run-qwythos-vision.sh` runs
grammar-free and is the one active today (probed: free-form output). The two
real classify blockers were HUB bugs, both fixed and test-locked: the schema hint taught models the nested extras shape the validator
rejected, and an honest no-match (`matched: false, block_id: null`) was refused.
After the fix, a five-utterance live probe against `.43` (Qwythos-9B) ran
**5/5 clean** at ~500-700 ms per dry-run, with real block enrichment.

Point the config at it (Settings, or `dictation.runtime` in the config):
`openai_compatible_base_url = "http://192.168.1.43:8080/v1"`,
`openai_compatible_model = "Qwythos-9B-Claude-Mythos-5-1M-Q6_K.gguf"`.

Fallbacks if `.43` is busy: llama-server on this Mac at :8082
(`brew install llama.cpp`, then
`llama-server -m ~/Models/gguf/Qwen3-4B-Instruct-2507-Q6_K.gguf --port 8082`),
or any OpenAI-compatible server. Do NOT use in-process `llama_cpp` — it
segfaults (exit 139) loading that GGUF on this machine.

**Verify before walking** (a rewrite with no warnings):

```bash
curl -s -X POST http://127.0.0.1:8000/api/dictation/dry-run \
  -H 'Content-Type: application/json' \
  -d '{"utterance": "hey can you umm add a retry to the sync push like three attempts"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['final_text']); print(d.get('warnings'))"
```

## 1. Hub + device

- Hub: `holdspeak web` bound for the LAN, iPad paired the HSM-12 way (host/port +
  the mirrored Bearer token in the pairing sheet).
- Install the current build on the iPad:
  `apple/scripts/meeting-capture-device.sh <UDID>` (list: `xcrun devicectl list devices`;
  the device must be UNLOCKED). For a guaranteed-fresh build, first:
  `rm -rf apple/build/meeting-capture-dd apple/build/meeting-capture-sources apple/build/HoldSpeakMeetingCapture.xcodeproj`.

## 2. The walk — five checks, one per story

Capture a screenshot per check into `screenshots/` (device screenshots, not
Simulator) and fill the trace at the bottom.

**W1 — the teleprompter receipt (18-01).** Dictate screen: the readiness strip
shows the live verdict. Toggle **Preview first ON**. Hold, speak
"hey can you umm add a retry to the sync push like three attempts", release.
EXPECT: the receipt card shows the REWRITTEN text (not your ums). Tap Send.
EXPECT: the focused Mac app receives **exactly the receipt text, byte-identical**
(the raw lane — compare character-for-character).

**W2 — the macro fires as an object (18-02).** On the iPad: Commands → author
`standup` → Type text → `## Standup` → Save. Preview first OFF. Speak "standup".
EXPECT: `## Standup` types on the Mac (the macro FIRED); the read-back shows the
fired chip, not dictated prose. CONTROL: toggle Voice commands off on the board,
speak "standup" again → the word "standup" is dictated. This is the
control-vs-treatment pair.

**W3 — the language took (18-03).** Settings → Spoken language → your non-English
pick. Dictate a native sentence. EXPECT: the transcript is in that language with
correct orthography. CONTROL: back to Auto, same sentence, compare.

**W4 — the symbol renders (18-04).** Settings → Your symbols → add
`tilde` → `~`. Speak-to-fill any field (e.g. a Commands payload): "config tilde
slash test". EXPECT: `config ~/test`-shaped output (your symbol, user-wins).

**W5 — the grounding changes the model (18-05).** Open the Dictate screen with a
nudge showing. CONTROL first: Preview ON, speak "draft a reply to that", capture
the receipt. Then tap **Dictate with this** on the nudge (card flips to Armed),
speak the SAME utterance. EXPECT: the second receipt visibly references the
cited record (title/domain) where the first could not — the Phase-53
control-vs-treatment bar, now over the relay.

## 3. The trace (fill during the walk)

```
Date/build:            <commit>
Endpoint used:         <a | b | c + URL/model>
W1 receipt verbatim:   PASS/FAIL — <note>
W2 macro fired + ctrl: PASS/FAIL — <note>
W3 language + ctrl:    PASS/FAIL — <language, note>
W4 symbol:             PASS/FAIL — <note>
W5 grounded vs ctrl:   PASS/FAIL — <what the grounded receipt referenced>
Bugs found:            <list — file them; the walk is a bug hunt too>
```

PASS on all five closes HSM-18-06 and the phase (entry-point docs already landed
with the runway). Any FAIL: fix, re-walk the failed check, then close.
