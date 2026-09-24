# PHILO-5-03 headless chart — Muad'Dib, 2026-09-24

Claude session: `8c9fa4ed-443d-423e-aa80-8ee77a30f17e`. Command: `claude -p --model claude-fable-5-1 --permission-mode bypassPermissions`.

Read of the in-progress chart and working tree; not counsel on built. Response retained verbatim below.

VERDICT
RATIFY-WITH-CONDITIONS. The chart is a lawful execution of the ratified lane brief: transport, headless posture, separate proofs and the no-claim stance all match the Proof position. Four things it does not say would let a green op verdict be hollow, so I would not ratify a pass until they are paid. No scope amendment is needed.

FINDINGS

1. Transport choice is right. `/api/mcp` inside the owning hub admits a loopback OWNER with remote off (`holdspeak/web/routes/mcp_http.py:96-110`), refuses a token in the query (`:113-118`), and accepts `Authorization: Bearer` (`holdspeak/web_auth.py:100`). The hub transport dispatches the registry bound at composition; no second writer. The canonical-to-tool map in the chart matches every `exposure` tuple in `holdspeak/operations.py:189-563` (`meeting.read`→`meeting.get`, `brief.shelf.write`→`monday_brief.shelf`, `thought.save`→`thought.update_working`, three Thought reads as resources). It is a hand copy, though. Tenet 1 is honoured only if the map is fenced against the descriptors, not merely written twice.

2. Two envelopes, one decoder. A tool answers `{content:[{text}], isError}` (`holdspeak/mcp/server.py:85-88`); a resource answers `{contents:[{uri, mimeType, text}]}` (`holdspeak/mcp/resources.py:430`). A resource refusal is a JSON-RPC `error.data.code` (`server.py:294-299`), a tool refusal is a 200 `isError` body with `code` (`server.py:314-320`). The chart says "decoded result or named refusal" and never names the second envelope. The uncommitted adapter in the worktree (`scripts/graph_walk.py`, `_decode_mcp_envelope`, working tree) reads only `content`, so `thought.read`, `thought.workbench.read` and `thought.list` decode to nothing and `j11` fails as "path absent" instead of a named block. Tenet 3: a proof that cannot read the Thought does not help.

3. An un-coded refusal cannot pair by code. The a1 invalid-status refusal is declared "ValueError: invalid decision status" (`operations.py:214`). Over MCP a ValueError becomes `{error: str}` with no `code` (`server.py:322-323`, `:424-425`); over HTTP it is a status plus body. The chart's "named refusal" and the in-flight `op_refusal` predicate compare `code` first. The pair must compare on `error_contains` for this refusal, or the story must state the refusal is un-coded on MCP. Contrast `route_unavailable`, a ConflictError with a code (`holdspeak/services/meeting_route_projection.py:181`) that pairs cleanly against the HTTP 409 case in `atlas.json` (`case.j6.route_intelligence_run.no_assignment`).

4. Silent restart retention. At base, `restart_hub` skips before/after capture when there is no page (`scripts/graph_walk.py:2739`, `:2742`) and the retention flags are simply absent; the case's protocol predicate can still pass. The chart says retention "must work with no page" but not that a restart record without `summary_retained`, `receipt_retained` and `meeting_identity_retained` is a FAIL. The in-flight `restart_required` flag is opt-in on `op_field`. Article IX: an absent proof is not a passed proof.

5. Headless engine setup is unnamed. Every summary case in `atlas-phase3.json` reaches the LAN engine through the Concierge face (`concierge-add-engine`, fill `http://192.168.1.43:8080`, check, submit; s3 setup). There is no engine operation in the pilot inventory, and the `api` cases that would do it carry a literal `"<engine>"` (`docs/internal/philo/graph/atlas.json:560`, `:1157`) that the rig never resolves (`unresolved` only knows `{name}`, `graph_walk.py:2690`). The `.op` siblings for s2, s3, s5 and the summary refusals have no stated way to assign the engine. Routes exist: `POST /api/concierge/probe`, `/apply`, `/summary-selection` (`holdspeak/web/routes/concierge.py:4-8`).

6. Replay identity has no headless home. The replay is installed in the hub process (`_install_engine_replay`, `graph_walk.py:1404`; `_serve` `:1498`), so it is page-free. But the identity is read from a DOM selector (`_read_identity` `:569`, `:827`) and a zero diff without one is "UNRESOLVED" (`:953`). The chart labels replayed runs but does not say what identity a replayed op run retains. The natural answer is the `run_receipt` on `meeting.read`.

7. Transport-status refusals are blocks. The in-flight `Hub.mcp` raises `Blocked` on any HTTP status ≥ 400. That is correct for this story (every named refusal returns 200 with `isError`), but the chart should say it, so a 403 `owner_required` or 404 `streamable_http_not_enabled` is never mistaken for a pair result.

8. Face-triggered cases need re-predication, and the calibration is unnamed. `philo404.all_handled` asserts `readable_text "ALL 2 HANDLED"` on a face selector; `s5_with_breakage` asserts `readable_text` on `[data-testid=arrival-brief-row]`. Their `.op` siblings must read `brief.shelf.read` and `brief.latest` fields instead. The chart promises "Removing op support must block its calibration" but names no calibration cases in the `CAL-*` family (`graph_walk.py:2270-2300`).

9. Chart claims that hold: headless confers no face verdict and writes no screenshot; face predicates hard-block without a page; polling is bounded (`wait_for_fixture_completion`, `:1490-1545`); duration is measured per op; producer-clock and scheduler-wait steps touch no page; `http_fault` correctly needs a page and stays browser-only. Both engine modes are labelled in provenance (`:311-325`).

CONDITIONS

C1. Fence the projection map against `OperationDescriptor.exposure` (`operations.py:99`); a mutation that renames one tool in the map turns the fence red.
C2. Decode both envelopes; pair one resource read and one resource refusal (unknown thought) through the real hub; a mutation swapping `content`/`contents` is red.
C3. State per named refusal whether it pairs by `code` or by `error_contains`; the a1 invalid-status pair uses `error_contains` unless the story pays a code on the MCP path.
C4. A headless `restart_hub` without the three retention flags is a FAIL; the s3 `.op` sibling declares it; deleting the flags is a red mutation.
C5. Name the headless engine-assignment steps (`api` on the concierge routes, `--engine real`) for every summary sibling, and record the engine identity in provenance as the browser path does.
C6. Name the replayed identity source for op runs (`run_receipt` via `meeting.read`) and retain it in the record.
C7. Name the calibration cases: op pass, op named refusal, op unresolved-argument block, headless face-predicate block, headless restart retention.
C8. Record the fixture sha256 for the op import as `fixture` steps do (`graph_walk.py:2692`), and state that a status ≥ 400 on `/api/mcp` is a rig block, not a pair result.

MISSED

- The resource envelope (finding 2). Highest cost: three of the named Thought pairs cannot decode.
- The un-coded ValueError refusal over MCP (finding 3).
- Engine assignment without the Concierge face, and the unresolved `<engine>` placeholder (finding 5).
- A silent restart pass (finding 4).

TUESDAY

Yes, unchanged. This story adds nothing the tired architect touches; the browser path he uses is retained with its selectors at 1440 and 393. The op path is proof infrastructure for story 04, where Codex drives the same `/api/mcp`. The one item that reaches him indirectly is finding 3: an un-coded refusal gives Codex a bare string, and a bare string is what he will read back on Tuesday.

UNKNOWN

- Whether the workers' uncommitted 222 lines in `scripts/graph_walk.py` already pay C2 to C7; I read the working tree once, mid-flight, and nothing is committed.
- Whether any lane fence is red pre-fix through the real hub; no test file for the op step exists yet under `tests/unit/`.
- Whether `/api/concierge/apply` accepts an assignment without a prior probe, and whether the LAN engine at .43 is up for the `--engine real` runs.
- Whether `s5_with_breakage` reproduces its breakage without any face step; its setup is forty-two steps, mostly UI, and I did not trace the breakage source.
