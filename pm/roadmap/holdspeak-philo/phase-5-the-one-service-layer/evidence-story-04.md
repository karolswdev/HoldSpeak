# Evidence - PHILO-5-04

- **Story:** PHILO-5-04 - The owner asks in his own words — OWNER REVIEW PENDING
- **Status:** done — OWNER REVIEW PENDING (2026-09-24)
- **Date:** 2026-09-24

## Proof

Target proof mode: **REHEARSED, OWNER-REVIEWED SHOTS — OWNER REVIEW PENDING**.
The final real-engine rehearsal completed; Muad'Dib ratified the technical
close with record conditions paid. Owner review remains separate. This is not a live sitting.

- [Rehearsal: prompts, sequence, shot IDs, readbacks and durations](../../../../docs/internal/philo/phase-5/his-words/rehearsal.md).
- [Final run](assets/story-04-shots/final/20260925T001407Z-his-words-real/observations.json), 326.090 seconds, 15 Codex MCP calls; actual summary host `192.168.1.43`.
- [Receipt pre-fix red](assets/story-04-shots/receipt-red/brief-read.json) and [same-brief green](assets/story-04-shots/receipt-green/brief-read.json), both widths.
- Rendered pre-fix reds: [000904Z](assets/story-04-shots/verification/receipt-tests/run-20260925T000904Z.out), [001056Z](assets/story-04-shots/verification/receipt-tests/run-20260925T001056Z.out), [001255Z](assets/story-04-shots/verification/receipt-tests/run-20260925T001255Z.out). Each has two missing-receipt failures plus one empty-Generate timing failure. `001336Z` is the post-fix timing failure (1 failed, 17 passed), not a product red; the prior citation was corrected.
- [C3 mutation red](assets/story-04-shots/verification/c3-clear-on-failure-mutation.txt): one failure when a failed read clears the existing receipt; the final unmodified product passes 20 scoped web tests.
- [Recorder mutation reds](assets/story-04-shots/verification/recorder/): actual raw failed test outputs.
- [Stopped attempts and limits](assets/story-04-shots/attempts/README.md); no replay was used for closing proof.
- [Carried six dispositions](story-04-the-owner-asks-in-his-own-words.md#carried-in-from-story-03); the missing-decision pair refuses on both sides but parity remains **FAIL 2:1**.

The Python scope collected 240 tests. After the final product change,
239 passed and the atlas reference test failed. Its ten shifted anchors
were corrected; all 113 affected atlas/schema/reference tests then passed.
These scopes overlap. No 352-test or full-suite claim is made.
The original failed capture remains below. Final web proof is 20 receipt/load/date tests plus 18 surviving
philo401/philo404 assertions tests: 38 total across six distinct files.

The first browser opening also wrote to the isolated hub: zero-based
transcript row **43**, `POST /api/desk/seed`, and row **62**,
`PUT /api/setup/onboarding`, both HTTP 200. These are FirstWords' first-open
handoff (`FirstWords.tsx:213-216`), outside every Codex window. `apply_seed`
(`db/seed.py:106-230`) writes the starter `directories`, `notes`, `recipes`
(including mode presets), `kbs`, `directory_memberships` and
`knowledge_memberships`. Note triggers also maintain `notes_memory_fts`
and its FTS backing tables. The onboarding service repeats the additive
seed and writes `onboarding_state` (`setup_service.py:40-43`). The final DB
has six starter directories, ten starter/guardrail notes, six mode recipes,
one KB and their memberships created at 00:14:47Z, plus disposition
`dismissed`. These were not Codex-created job objects. The source and final
rows identify the affected stores; no per-statement SQL trace or allocation
between the two requests is claimed. See the retained first-open readback.

[First-open rows](assets/story-04-shots/verification/first-open-seed-readback.txt).
[Closing check and condition receipts](checks/story-04-closing-muaddib.md).

The phase is **technically done and open — OWNER REVIEW PENDING**.
`dw check` reports one expected phase-close receipt lint:
`ERROR pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer: all stories are done but final-summary.md is missing`.
`dw_pmo/validate.py:189-194` emits it. A summary file would mark this phase
CLOSED by existence alone (`statefeed.py:111-118`; `api.py:30-34`), so it
must not be created now. The stamped commit gate does not consume this
phase lint and remains unchanged. `.githooks/dw phase close`
(`mutations.py:400-415`) is deferred until the owner's review closes exit 5
and the phase close is verified. [Both brains' receipt disposition](checks/story-04-phase-receipt-muaddib.md).

[Exact lint output](assets/story-04-shots/verification/dw-check-deferred-phase-close.txt).

### Captured run — 2026-09-24T23:28:09Z

- **Command:** `zsh -c set -o pipefail; curl --fail-with-body --connect-timeout 5 --max-time 12 -sS -i http://192.168.1.43:8080/v1/models | tee pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/lan-preflight.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 846ddad725e6c418533b949055e693711f30430b

```text
HTTP/1.1 200 OK
Keep-Alive: timeout=5, max=100
Content-Type: application/json; charset=utf-8
Server: llama.cpp
Content-Length: 611
Access-Control-Allow-Origin: 

{"models":[{"name":"Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf","model":"Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf","modified_at":"","size":"","digest":"","type":"model","description":"","tags":[""],"capabilities":["completion"],"parameters":"","details":{"parent_model":"","format":"gguf","family":"","families":[""],"parameter_size":"","quantization_level":""}}],"object":"list","data":[{"id":"Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf","aliases":[],"tags":[],"object":"model","created":1790292489,"owned_by":"llamacpp","meta":{"vocab_type":2,"n_vocab":248320,"n_ctx_train":262144,"n_embd":2048,"n_params":34660610688,"size":26581518848}}]}
```

### Captured run — 2026-09-24T23:53:13Z

- **Command:** `zsh -c set -o pipefail; env HOME=$(mktemp -d) PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright HOLDSPEAK_EVIDENCE_WRITE=1 uv run pytest -q tests/unit/test_philo5_graph_op.py tests/unit/test_philo5_pairs.py tests/unit/test_graph_walk_calibration.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_philo5_codex_seams.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo_graph_schema.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo5_rehearsal_capture.py tests/unit/test_philo5_his_words.py | tee pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/scoped-tests.txt`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 846ddad725e6c418533b949055e693711f30430b

```text
........................................................................ [ 30%]
........................................................................ [ 60%]
........................................................................ [ 90%]
.......................                                                  [100%]
239 passed in 117.39s (0:01:57)
```

### Captured run — 2026-09-25T00:16:40Z

- **Command:** `zsh .tmp/philo504-final-checks.sh`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 846ddad725e6c418533b949055e693711f30430b

```text
........................................................................ [ 30%]
.......................................F................................ [ 60%]
........................................................................ [ 90%]
........................                                                 [100%]
=================================== FAILURES ===================================
_________ test_every_source_reference_lands_on_its_symbol[atlas.json] __________

every_atlas = {'cases': [{'applicability': 'applicable', 'completion_bound_s': 20, 'edge_ids': ['edge.face.first_words_continue_late...son': 'the gate holds ONE capture state and ONE failure (web/src/desk/components/FirstWords.tsx:50, :51).'}, ...], ...}

    def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
        """A line number is evidence, not identity (brief section 1).
    
        The cited line must still hold the cited symbol, or the reference has
        drifted and the claim behind it is no longer proven.
        """
        problems: list[str] = []
        for state in every_atlas["states"]:
            for ref in state["sources"]:
                target = REPO / ref["path"]
                if not target.is_file():
                    problems.append(f"{state['id']}: missing file {ref['path']}")
                    continue
                lines = target.read_text(errors="replace").splitlines()
                if not 1 <= ref["line"] <= len(lines):
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} is past the end of the file"
                    )
                    continue
                line = lines[ref["line"] - 1]
                if ref["symbol"] not in line:
                    problems.append(
                        f"{state['id']}: {ref['path']}:{ref['line']} no longer holds "
                        f"{ref['symbol']!r} (line reads {line.strip()[:80]!r})"
                    )
>       assert not problems, "\n".join(problems)
E       AssertionError: state.briefs.absent: web/src/desk/chair/ChairHome.tsx:1334 no longer holds '!briefLoading && !brief' (line reads '</div>')
E         state.briefs.loading: web/src/desk/chair/ChairHome.tsx:524 no longer holds 'setBriefLoading' (line reads 'head Generate repeats the same POST. */')
E         state.briefs.generating: web/src/desk/chair/ChairHome.tsx:737 no longer holds 'generating' (line reads 'idiom) or failed (BRIEF DID NOT GENERATE · <cause>). */')
E         state.briefs.generation_failure: web/src/desk/chair/ChairHome.tsx:712 no longer holds 'setGenerateFailed' (line reads '} catch (error) {')
E         state.briefs.populated: web/src/desk/chair/ChairHome.tsx:874 no longer holds 'briefItems' (line reads '});')
E         state.briefs.reload_persisted: web/src/desk/chair/ChairHome.tsx:1389 no longer holds 'arrival-brief' (line reads 'PHILO-4-01 boards 7a, 7b, 8a, 8b, 9. */')
E         state.briefs.item.untouched: web/src/desk/chair/ChairHome.tsx:882 no longer holds 'briefShelf' (line reads ': [];')
E         state.meetings.transcription.present: web/src/desk/chair/ChairHome.tsx:2304 no longer holds 'hasTranscript' (line reads ': serverBadge;')
E         state.desk_presentation.reload_reconnect: web/src/desk/chair/ChairHome.tsx:628 no longer holds 're-reads' (line reads '}')
E         state.desk_presentation.reload_reconnect: web/src/desk/chair/ChairHome.tsx:527 no longer holds 'apiFetch' (line reads 'const readBrief = useCallback(() => {')
E       assert not ["state.briefs.absent: web/src/desk/chair/ChairHome.tsx:1334 no longer holds '!briefLoading && !brief' (line reads '</.../chair/ChairHome.tsx:1389 no longer holds 'arrival-brief' (line reads 'PHILO-4-01 boards 7a, 7b, 8a, 8b, 9. */')", ...]

tests/unit/test_philo_graph_atlas.py:279: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas.json]
1 failed, 239 passed in 117.48s (0:01:57)
```

### Captured run — 2026-09-25T00:24:45Z

- **Command:** `zsh .tmp/philo504-anchor-fixed-checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 846ddad725e6c418533b949055e693711f30430b

```text
........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 3.08s

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-5-04/web


 Test Files  4 passed (4)
      Tests  18 passed (18)
   Start at  18:24:50
   Duration  1.30s (transform 489ms, setup 192ms, import 969ms, tests 361ms, environment 688ms)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
```

### Captured run — 2026-09-25T00:30:02Z

- **Command:** `zsh .tmp/philo504-web-final.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 846ddad725e6c418533b949055e693711f30430b

```text
npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-5-04/web


 Test Files  4 passed (4)
      Tests  20 passed (20)
   Start at  18:30:04
   Duration  1.42s (transform 710ms, setup 200ms, import 1.20s, tests 376ms, environment 714ms)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
```

### Captured run — 2026-09-25T00:35:12Z

- **Command:** `zsh .tmp/philo504-artifact-check.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 846ddad725e6c418533b949055e693711f30430b

```text
PHILO-5-04 FINAL REHEARSAL ARTIFACT AUDIT — PASS
RUN: /Users/karol/dev/tools/wt-philo-5-04/pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/final/20260925T001407Z-his-words-real
MODE: read-only retained artifacts; no hub, browser, Codex, or pytest process
PASS  retained file: rehearsal-transcript.jsonl
PASS  retained file: db-proof.sqlite
PASS  retained file: run-status.json
PASS  retained file: codex/import/events.jsonl
PASS  retained file: codex/summary/events.jsonl
PASS  retained file: codex/decision_thought/events.jsonl
PASS  retained file: codex/tomorrow_brief/events.jsonl

Transport and catalog
PASS  tools/list retained: 4 tools/list responses; 228 tool names
PASS  recorded MCP transport: POST /api/mcp tools/call rows are present

Codex turns
PASS  import retained window start: transcript-window=5; mcp-audit=5
PASS  summary retained window start: transcript-window=182; mcp-audit=182
PASS  decision_thought retained window start: transcript-window=312; mcp-audit=312
PASS  tomorrow_brief retained window start: transcript-window=857; mcp-audit=857
PASS  transcript window bounds: ranges={'import': (5, 10), 'summary': (182, 311), 'decision_thought': (312, 624), 'tomorrow_brief': (857, 880)}; rows=1003
PASS  import call reconciliation: 2/2 calls matched occurrence-by-occurrence
PASS  import required producer: required=['meeting.import']
PASS  import non-MCP write fence: 0 unmatched write rows in indexed transcript window
PASS  import shell mutation fence: 3 shell commands; 0 mutation commands
PASS  import process outcome: {"elapsed_s": 34.427, "finished_at": "2026-09-25T00:14:43.935209+00:00", "outcome": "process_completed", "started_at": "2026-09-25T00:14:09.508114+00:00"}
NOTE  import tool sequence: meeting.import -> meeting.get
NOTE  import duration: 34.427s; transcript window=5:10; MCP call rows=2
PASS  summary call reconciliation: 4/4 calls matched occurrence-by-occurrence
PASS  summary required producer: required=['meeting.run_intelligence']
PASS  summary non-MCP write fence: 0 unmatched write rows in indexed transcript window
PASS  summary shell mutation fence: 0 shell commands; 0 mutation commands
PASS  summary process outcome: {"elapsed_s": 38.466, "finished_at": "2026-09-25T00:15:30.767047+00:00", "outcome": "process_completed", "started_at": "2026-09-25T00:14:52.301205+00:00"}
NOTE  summary tool sequence: meeting.get -> meeting.run_intelligence -> meeting.get -> meeting.get
NOTE  summary duration: 38.466s; transcript window=182:311; MCP call rows=4
PASS  decision_thought call reconciliation: 7/7 calls matched occurrence-by-occurrence
PASS  decision_thought required producer: required=['desk.create', 'thought.create', 'thought.update_working']
PASS  decision_thought non-MCP write fence: 0 unmatched write rows in indexed transcript window
PASS  decision_thought shell mutation fence: 25 shell commands; 0 mutation commands
PASS  decision_thought process outcome: {"elapsed_s": 201.398, "finished_at": "2026-09-25T00:18:52.619998+00:00", "outcome": "process_completed", "started_at": "2026-09-25T00:15:31.221362+00:00"}
NOTE  decision_thought tool sequence: thought.create -> thought.update_working -> desk.get -> meeting.proposals -> desk.create -> desk.get -> desk.get
NOTE  decision_thought duration: 201.398s; transcript window=312:624; MCP call rows=7
PASS  tomorrow_brief call reconciliation: 2/2 calls matched occurrence-by-occurrence
PASS  tomorrow_brief required producer: required=['monday_brief.generate']
PASS  tomorrow_brief non-MCP write fence: 0 unmatched write rows in indexed transcript window
PASS  tomorrow_brief shell mutation fence: 0 shell commands; 0 mutation commands
PASS  tomorrow_brief process outcome: {"elapsed_s": 23.333, "finished_at": "2026-09-25T00:19:29.459424+00:00", "outcome": "process_completed", "started_at": "2026-09-25T00:19:06.126078+00:00"}
NOTE  tomorrow_brief tool sequence: monday_brief.generate -> monday_brief.get
NOTE  tomorrow_brief duration: 23.333s; transcript window=857:880; MCP call rows=2
PASS  all completed calls reconciled: 15/15 retained completed holdspeak MCP calls
NOTE  refused/error calls: 0 (retained and included in reconciliation)
PASS  no shell mutation commands: 28 commands inspected

Ordinary-language prompts
PASS  import prompt fence: catalog/tool/technical tokens=[]
PASS  summary prompt fence: catalog/tool/technical tokens=[]
PASS  decision_thought prompt fence: catalog/tool/technical tokens=[]
PASS  tomorrow_brief prompt fence: catalog/tool/technical tokens=[]
PASS  all prompts ordinary: all retained as-sent prompts pass the actual tools/list catalog fence

In-memory rejection cases
EXPECTED REJECTION  prompt operation-name mutation: the retained catalog name 'meeting.import' was detected
EXPECTED REJECTION  MCP result mismatch: no POST /api/mcp occurrence for meeting.import with exact args/result hash 11fb166d1d75c8e0ec1c0c2e5e70b5ecf24f3265d169319a89711e3220997292
EXPECTED REJECTION  method/path bypass: no POST /api/mcp occurrence for meeting.import with exact args/result hash 11fb166d1d75c8e0ec1c0c2e5e70b5ecf24f3265d169319a89711e3220997292
EXPECTED REJECTION  extra non-MCP write: detected POST /api/desk/direct-write

Readbacks and identity
PASS  canonical meeting id: '1a1f7ce7'
PASS  canonical decision id: 'decision_96c04b1b7a13'
PASS  canonical Thought id: 'thought_2b4148a5b1f8'
PASS  canonical brief id: 'brief-de8a52459de14125bc7ed351be8451b9'
PASS  meeting import readback: meeting id and complete transcript readback retained
PASS  summary readback: summary=328 chars; LAN host receipt=True
PASS  decision readback: decision content and identity retained
PASS  Thought saved body: final appended sentence and original body retained
PASS  Thought revision advanced: 1 -> 2
PASS  brief decision source: 'decision:decision_96c04b1b7a13'; 1 matching retained items
PASS  SQLite immutable read-only open: query_only=1
PASS  SQLite integrity: integrity_check=ok
PASS  meeting id in immutable DB backup: 1a1f7ce7
PASS  decision id in immutable DB backup: decision_96c04b1b7a13
PASS  Thought id in immutable DB backup: thought=thought_2b4148a5b1f8; note=note_thought_c6f90ab0fab106d0
PASS  brief id in immutable DB backup: brief=brief-de8a52459de14125bc7ed351be8451b9; items=6
PASS  DB Thought final body/revision: working_revision=2
PASS  DB brief decision source: decision:decision_96c04b1b7a13
PASS  unexpected audited created objects: none in meeting/decision/Thought/brief tables

Browser predicates and retained shots
PASS  summary both widths: pages=2
PASS  summary 1440px visible: summary text present
PASS  summary 1440px host: LAN host receipt visible
PASS  summary 1440px in place: same page, no refresh/navigation
PASS  summary 1440px hit-test: {"hit": true, "in_viewport": true, "viewport": {"height": 900, "width": 1440}, "visible": true}
PASS  summary 393px visible: summary text present
PASS  summary 393px host: LAN host receipt visible
PASS  summary 393px in place: same page, no refresh/navigation
PASS  summary 393px hit-test: {"hit": true, "in_viewport": true, "viewport": {"height": 852, "width": 393}, "visible": true}
PASS  decision both widths: pages=2
PASS  decision 1440px content: expected content visible
PASS  decision 1440px shot: 1440.png
PASS  decision 393px content: expected content visible
PASS  decision 393px shot: 393.png
PASS  thought both widths: pages=2
PASS  thought 1440px content: expected content visible
PASS  thought 1440px shot: 1440.png
PASS  thought 393px content: expected content visible
PASS  thought 393px shot: 393.png
PASS  brief both widths: pages=2
PASS  brief 1440px receipt: Brief ready · 6 items · 6:19 PM
PASS  brief 1440px decision row: ["Review decision: Keep summary retrieval on the local desk.\nAck\nDefer", "Meeting recorded: Architecture review\nAck\nDefer", "Unassigned: Test restart retrieval\nAck\nDefer"]
PASS  brief 1440px shot: 1440.png
PASS  brief 1440px receipt_shot: 1440-receipt.png
PASS  brief 1440px row_shot: 1440-row.png
PASS  brief 393px receipt: Brief ready · 6 items · 6:19 PM
PASS  brief 393px decision row: ["Review decision: Keep summary retrieval on the local desk.\nAck\nDefer", "Meeting recorded: Architecture review\nAck\nDefer", "Unassigned: Test restart retrieval\nAck\nDefer"]
PASS  brief 393px shot: 393.png
PASS  brief 393px receipt_shot: 393-receipt.png
PASS  brief 393px row_shot: 393-row.png

Run proof and limitations
PASS  run completed: {"elapsed_s": 326.09, "error": null, "finished_at": "2026-09-25T00:19:33.786633+00:00", "outcome": "completed", "started_at": "2026-09-25T00:14:07.695632+00:00"}
NOTE  total duration: 326.09s; started=2026-09-25T00:14:07.695632+00:00; finished=2026-09-25T00:19:33.786633+00:00
PASS  Codex hub HOME separation: Codex config points at fresh hub HOME
PASS  MCP config exact: {"args": [], "command": "/Users/karol/dev/tools/wt-philo-5-04/.venv/bin/holdspeak-mcp", "cwd": "/Users/karol/dev/tools/wt-philo-5-04", "env": {"HOME": "/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/philo5-04-hub-fx3inucg"}, "name": "holdspeak", "required": true, "timeout": {"startup_seconds": 60, "tool_seconds": 900}, "transport": "stdio"}
PASS  effective Codex config: codex mcp get succeeded and holdspeak enabled
PASS  owner review label: review remains pending
PASS  real engine preflight: LAN model endpoint returned successfully
NOTE  hub shutdown warning: resource_tracker reported one leaked semaphore; run completed and DB proof is intact
NOTE  tool catalog: 228 names retained from 4 tools/list responses
NOTE  proof boundary: Codex calls and shell/transcript writes are audited; browser/setup reads and rig producer writes are outside Codex timing windows

Counts
Codex stages=4; completed MCP calls=15; refusals/errors=0; shell commands=28
```

### Captured run — 2026-09-25T00:43:32Z

- **Command:** `zsh .tmp/philo504-closing-assertions.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f2e4010050cb731a1b890c05d80fea1b3b305bc7

```text
npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-5-04/web


 Test Files  2 passed (2)
      Tests  18 passed (18)
   Start at  18:43:33
   Duration  951ms (transform 635ms, setup 121ms, import 873ms, tests 284ms, environment 356ms)

npm notice
npm notice New minor version of npm available! 11.6.2 -> 11.20.0
npm notice Changelog: https://github.com/npm/cli/releases/tag/v11.20.0
npm notice To update run: npm install -g npm@11.20.0
npm notice
```

### Captured run — 2026-09-25T00:48:15Z

- **Command:** `python3 pm/roadmap/holdspeak-philo/phase-5-the-one-service-layer/assets/story-04-shots/verification/philo504-seed-readback.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f2e4010050cb731a1b890c05d80fea1b3b305bc7

```text
First-open seed/onboarding readback (immutable final DB).
Transcript indices are zero-based, as in the Codex-window audit.
row 43: {"method": "POST", "path": "/api/desk/seed", "status": 200}
row 62: {"method": "PUT", "path": "/api/setup/onboarding", "status": 200}
directories: [{"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-decisions", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-inbox", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-meetings", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-personal", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-reference", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-work", "last_modified": "2026-09-25T00:14:47Z"}]
notes: [{"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-about-me", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-current-priorities", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-guardrail-effect-guard", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-guardrail-egress-guard", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-how-i-like-help", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-meeting-preferences", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-people-vocabulary", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-prompt-one-on-one-prep", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-prompt-weekly-update", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-start-here", "last_modified": "2026-09-25T00:14:47Z", "updated_at": "2026-09-25T00:14:47Z"}]
kbs: [{"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-everyday-context", "last_modified": "2026-09-25T00:14:47Z"}]
recipes: [{"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-mode-chase", "kind": "mode", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-mode-desk", "kind": "mode", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-mode-draft", "kind": "mode", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-mode-interview", "kind": "mode", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-mode-plan", "kind": "mode", "last_modified": "2026-09-25T00:14:47Z"}, {"created_at": "2026-09-25T00:14:47Z", "id": "hs-seed-mode-project", "kind": "mode", "last_modified": "2026-09-25T00:14:47Z"}]
directory_memberships: [{"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "directory_id": "hs-seed-inbox", "last_modified": "2026-09-25T00:14:47Z", "primitive_id": "note:hs-seed-start-here"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "directory_id": "hs-seed-personal", "last_modified": "2026-09-25T00:14:47Z", "primitive_id": "note:hs-seed-about-me"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "directory_id": "hs-seed-personal", "last_modified": "2026-09-25T00:14:47Z", "primitive_id": "note:hs-seed-how-i-like-help"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "directory_id": "hs-seed-work", "last_modified": "2026-09-25T00:14:47Z", "primitive_id": "note:hs-seed-current-priorities"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "directory_id": "hs-seed-meetings", "last_modified": "2026-09-25T00:14:47Z", "primitive_id": "note:hs-seed-meeting-preferences"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "directory_id": "hs-seed-reference", "last_modified": "2026-09-25T00:14:47Z", "primitive_id": "note:hs-seed-people-vocabulary"}, {"created_at": "2026-09-25T00:16:27Z", "deleted": 0, "directory_id": "hs-seed-inbox", "last_modified": "2026-09-25T00:16:27Z", "primitive_id": "note:note_thought_c6f90ab0fab106d0"}]
knowledge_memberships: [{"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "knowledge_id": "hs-seed-everyday-context", "last_modified": "2026-09-25T00:14:47Z", "resource_ref": "note:hs-seed-about-me"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "knowledge_id": "hs-seed-everyday-context", "last_modified": "2026-09-25T00:14:47Z", "resource_ref": "note:hs-seed-current-priorities"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "knowledge_id": "hs-seed-everyday-context", "last_modified": "2026-09-25T00:14:47Z", "resource_ref": "note:hs-seed-how-i-like-help"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "knowledge_id": "hs-seed-everyday-context", "last_modified": "2026-09-25T00:14:47Z", "resource_ref": "note:hs-seed-meeting-preferences"}, {"created_at": "2026-09-25T00:14:47Z", "deleted": 0, "knowledge_id": "hs-seed-everyday-context", "last_modified": "2026-09-25T00:14:47Z", "resource_ref": "note:hs-seed-people-vocabulary"}]
onboarding_state: [{"disposition": "dismissed", "id": 1, "updated_at": "2026-09-24T18:14:47.955875"}]
notes_memory_fts seed rows: 10
Source: FirstWords.tsx:213-216 calls both routes on first-open handoff.
Source: db/seed.py:106-230,269-313 writes manifest directories, notes, recipes, kbs and filing; thread_modes.py:171,344 ensures mode recipes and guardrail notes.
Source: db/primitives.py:384-437 maintains knowledge_memberships; schema.py:1312-1328 maintains notes_memory_fts and its FTS backing tables.
Source: services/setup_service.py:40-43 repeats additive apply_seed then writes onboarding_state.
The final snapshot proves rows exist; it is not a per-statement SQL trace or a before/after allocation between the two calls.
```
