# PHILO-11-01 — Astra's lane record

**Status:** Round-two conditions C1–C4 are paid and counsel r1 is recorded; the new head awaits Muad'Dib's full suite.

LANE: PHILO-11-01. Story 01. Worktree `/Users/karol/dev/tools/wt-philo-11-01`; branch `feat/philo-11-01`; base `332d91586bdbd7fe40e3c2c00851a46adc4650e4`.

Delivery: [PR #707 — PHILO-11-01 — the document sources](https://github.com/karolswdev/HoldSpeak/pull/707), to `main`. First-round implementation commit: `862fbba20ade9122bb74e190525ffa7ed9a89a24`; round two updates this PR. No merge is claimed.

OUTCOME: implementation follows the owner's ratified design, sections 1–4. Eight stored document kinds share the existing preview, prepare and Send lifecycle. The update face uses the generic reference. Story 01 is done; round two pays the counsel conditions, and Muad'Dib owns the full-suite rerun on the new head. Slack and the new document faces stay with their named stories.

PROOF: actual command output is in [evidence-story-01.md](evidence-story-01.md). Python 3.13.14 was synced with `uv sync --python 3.13 --all-extras --all-groups`. All Python tests use isolated HOME and basetemp inside it. No metal test or owner desk is used.

| Claim | Fence and observed result |
|---|---|
| Eight stored sources; whole brief and real People overlay; no transcript | `tests/unit/test_philo11_document_sources.py`: 19 cases. `tests/unit/_philo11_documents.py` uses the real source producers and a file keystore in the isolated HOME. The long aftercare fence retains the last of 400 stored decisions. |
| One wire and lifecycle; frozen bytes and names after source removal; owner-only egress | `tests/unit/test_philo11_channel_contract.py`: 10 cases. HTTP/MCP use the real registry and service. The thread finds `#leads` through `channel.destinations`; Send is outside its palette. |
| Every kind through the real rig and subprocess hub | `tests/integration/test_philo11_document_rig.py`: 8 collected, 8 passed. Each goes through preview, prepare, Send, history and receipt readback. The corrected archived-base run fails all 8. |
| Steward still prepares updates | Two real producer failures before the caller correction; then the combined source/contract/rig/CLI selection collects and passes 83 cases. |
| Lifecycle R1–R6 on update and desk decision, both forms | Existing Phase 10 contract, recovery and restart fences are parameterized over both kinds. Worker collection and run logs are retained under [assets/story-01-logs/wire](assets/story-01-logs/wire); the full run covers them too. |
| Update face: inline and prepared Send | `scripts/verify_philo11_update_glass.py`: 4 collected, 4 passed in 123.37s. Shots are in [assets/story-01-shots](assets/story-01-shots). |
| Actual atlas, not sample calibration | `case.p10.send.sent` and `case.p10.send.prepared` at 1440 and 393; both `.op` siblings at 1440: all 6 PASS, terminal `settled`. Retained raw observations and face shots are in [assets/story-01-walks](assets/story-01-walks). Their original `.tmp/graph-walk/` shot paths map to the identical filenames in each retained run directory. |
| Web suite | 2,970 passed, zero failures. Baseline checker reports zero branch-new; its five HEALED entries are observed, not attributed to this story. |

Astra's final captured checks (`2026-09-30T05:34:58Z`) verify all 246 catalogue rows, the real 16,115-token admission, the operations export, ten architecture outputs, OpenAPI and the graph join. They collect and pass 48 tests in 28.34s, including every final full-run unit failure and the unchanged engine regression pair.

The archived baseline lives inside this worktree under `.tmp/philo11/base-332d9158`; no second working tree was moved. The first attempted rig baseline mistakenly loaded the current editable package in the child. The evidence marks that attempt rejected and retains the corrected run with the archived PYTHONPATH exported into the child. A later empty stdin capture is also explicitly rejected; neither is proof.

The saved receipts were inspected at both widths: `05-saved-folder-{1440,393}.png` and `29-prepared-file-sent-{1440,393}.png`. The actual atlas before/after shots were inspected too. All six observations retain the real source revision `332d9158`, `dirty=True`, the fake-home DB path and the loaded web bundle; no owner sitting is inferred from them. Tuesday: the owner can still preview an update and save it to a folder in the existing well; new document faces are not claimed here.

LEDGER: the first quiet full suite ended with `16 failed, 13520 passed, 99 skipped, 4 xfailed, 17 warnings in 3649.54s (1:00:49)` (captured run `2026-09-30T03:02:16Z`). It is a red run, not a green claim.

| Class | Finding | Disposition |
|---|---|---|
| a | Eight old-contract assertions: schema snapshot, operations export, five Phase 5 channel argument producers, Phase 10 source anchors | Updated with the contract; all eight pass. The root's follow-up selection collects and passes 27 cases including all 19 source cases (`2026-09-30T04:18:15Z`). |
| b | Recipe/chat off-loop pair never reaches the engine after the four channel tools join the palette | Current serial 2 failed, archived base 2 passed. Actual route rows say `context_overflow`: the enlarged catalogue makes the request exceed the unchanged fixture's 16,384-token ceiling. The settled correction shortens shared catalogue descriptions while preserving tool schemas and authority. It adds no model-facing adapter. The tests' ceiling and off-loop assertion stay unchanged. The unchanged pair passes. Astra verified all 246 catalogue entries have identical non-description fields. Actual admission rows now fit 16,384: 16,086 tokens in the worker's recipe/run-then-chat reproduction; 16,023 in Astra's standalone chat reproduction. The provider runs off-loop. Captured final checks: `2026-09-30T04:41:59Z`; worker logs: [assets/story-01-logs/catalogue-fix](assets/story-01-logs/catalogue-fix). |
| c | J1 first value, J9 shade receipt, HS-176 Speak at both widths, Philo-8 foot at 393, HS-151 abort | Each of the six exact failing nodes passes twice serially with fresh HOME per invocation; Astra repeated and captured all 12 runs at `2026-09-30T04:19:13Z`. Exact parallel interference remains unknown. |
| b, fixed before full run | Steward `prepare_send` passed a bare update id into the generic service | Both the child operation arguments and service call now pass `document_ref`. Real producer red-before/green-after is captured. |
| Follow-up: story 06 | Graph census is not clean: 36 new edges, 5 miscited sources and 14 subtype conflict notes; zero removed, changed, stale or unread edges | Keep the historical passes sealed. Generated join checks pass; the census remains explicitly red for atlas reconciliation. |
| Scope: story 02 | The old Slack actuator still has its historical 3,800-character cap | The new digest/follow-up document sources are uncapped Markdown. This lane does not rewrite the old transport or build Slack. |

The second quiet full suite, captured at `2026-09-30T04:43:17Z`, ended with:

```text
38 failed, 13498 passed, 99 skipped, 4 xfailed, 3 warnings in 1700.78s (0:28:20)
```

This run used `-n auto --dist=worksteal`, Python 3.13.14, fresh HOME and TMPDIR, basetemp inside HOME, and trap cleanup. No worker edited the tree during either full run. The red result is retained in full.

| Class | Second full-run failures | Disposition |
|---|---|---|
| a | 10: Phase 133 boundary punctuation; six old job-phrase checks; three source-location census checks | Compact words keep the original jobs and argument paths. The discovery fence reads top-level and nested descriptions from the real hub and binds the kind to the matching clause. Six census locations moved; two were masked behind the first failed assertions. No census classification or runtime behavior changes. |
| b | 2: `zone.unfile` lost its ID producer guidance; `desk.create` lost the directories-to-zones alias needed for “make a zone” | Both facts restored. The corrected real `tools/list` fence first fails only “make a zone” (18 passed, 1 failed), then the final focused selection collects and passes 28. Earlier intermediate 28-pass outputs with a weakened reason-to-kind check are superseded; the final fence retains every original task and argument path. |
| c | 26 glass failures: arrival brief, Shade, Speak, receipt hits, delete/undo and rename faces | Every exact node passed twice serially: 26 collected, 52/52 passing invocations, each with a fresh HOME, TMPDIR and basetemp. Astra ran and captured the verification at `2026-09-30T05:15:02Z`. The exact parallel cause remains unknown. Raw logs and node list: [final-glass](assets/story-01-logs/final-glass). |

The final catalogue has the same non-description fields in all 246 tool rows. The actual standalone chat admission now reserves 16,115 of 16,384 tokens (31 tools; 269 headroom), and reaches the engine off-loop. The unchanged recipe/chat regression pair is green. The final word-fence logs are [catalogue-fix/collect-final4.log](assets/story-01-logs/catalogue-fix/collect-final4.log), [run-final4.log](assets/story-01-logs/catalogue-fix/run-final4.log) and [budget-final4.log](assets/story-01-logs/catalogue-fix/budget-final4.log); the census selection collects and passes 18 in [final-census](assets/story-01-logs/final-census).

The preview descriptor is already exempt computation under Constitution XI.5 (`holdspeak/channel_operations.py`, `CHANNEL_PREVIEW`); `test_reads_and_previews_leave_no_operation` requires no operation. Criterion 6's request for a preview admission and receipt conflicts with that binding lifecycle. No extra admission is introduced. Prepare and inline Send name the document in their actual operation targets and receipts; the preview result names it directly. The story records that Constitution XI.5 governs criterion 6. This wording conflict remains explicit for Muad'Dib; the implementation preserves the higher canon and the unchanged Phase 10 lifecycle.

AMENDMENTS: no behavioral amendment. Criterion 6 is applied under Constitution XI.5: preview returns the reference without an admission or receipt; prepare and inline Send retain both. This precedence is explicit beside the original criterion, for counsel-on-built. The dispatch brief names `feat/philo-11-01`, superseding the proposed branch name in the lane table.

UNKNOWN: the exact parallel-glass interference is not identified. This lane does not claim owner observation, real remote delivery, or counsel-on-built. Muad'Dib checks the built lane; no Claude session has been invoked as a substitute.

## Round two — 2026-09-30

LANE: PHILO-11-01, story 01, PR #707, branch `feat/philo-11-01`, worktree `/Users/karol/dev/tools/wt-philo-11-01`.

OUTCOME: Muad'Dib's counsel r1 is recorded verbatim at [checks/story-01-built-muaddib-r1.md](checks/story-01-built-muaddib-r1.md). C1, C2 and C4 are paid; C3 is in the home backlog. F5 is in design §2; the F6 ruling is in phase decisions. Story 01 remains done.

PROOF: the real `/api/mcp` `tools/list` maps all 13 restored PHILO-7/Phase 10 phrases to their intended tools. Base-form discovery, Send contract, document-source and chat-admission tests collect 82 and pass 82. The two persisted chat-admission rows on the final description text show 15,618 + 512 = 16,130 / 16,384 (254 headroom) for standalone chat and 15,657 + 512 = 16,169 / 16,384 (215 headroom) for recipe run then chat. A separate real admission check shows 15,598 + 512 = 16,110 / 16,384 (274 headroom), with 31 palette tools and the engine off-loop. The 1440/393 update Send glass collects and passes 4; it writes temporary shots only. Evidence is appended to [evidence-story-01.md](evidence-story-01.md).

LEDGER: Muad'Dib's full suite on the previous head `3552be416` was **2 failed, 13,534 passed, 99 skipped, 4 xfailed in 3617.52s**. Both failures pass serially and are class (c); zero failures are branch-new. The full suite on this new head is Muad'Dib's to rerun.

AMENDMENTS: restored all ten PHILO-7 job phrases and the three Phase 10 asks in the real catalogue, the original base-form guard tests (only the argument-name change remains), and the project-update `== body` assertion. When People is unavailable, the real brief renderer emits one `PEOPLE · UNAVAILABLE` line. Palette argument fields and authority are unchanged; `document_ref` help now points to `channel.preview`. The document-source update face did not change.

UNKNOWN: the new-head full-suite result and Muad'Dib's follow-up counsel are pending. The parallel class-(c) failures from the previous head remain unclassified beyond their serial passes.

## Round three — 2026-09-30

LANE: PHILO-11-01, story 01, PR #707, branch `feat/philo-11-01`, worktree `/Users/karol/dev/tools/wt-philo-11-01`, starting head `fd1028f3c`.

OUTCOME: Muad'Dib's D2 budget amendment is applied. The chat palette contains only `channel.destinations` and `channel.prepare`; `channel.preview` and `channel.sends` remain public over MCP and HTTP. Prepare returns the preview in its answer, and the thread still finds `#leads` by name. The story stays done. This round's changes are recorded in [evidence-story-01.md](evidence-story-01.md); the branch tip and PR are reported after the gate.

PROOF: the palette membership fence failed against the old four-tool palette, then passed with the two ruled tools. Its real `channel.destinations` → `channel.prepare` path checks the preview text in the prepared payload and confirms a refused `channel.send` creates no operation. The focused selection collects and passes 97 tests in 14.59s. It includes the five branch-new failures from Muad'Dib's prior check, the PHILO-7 and Phase 10 discovery guards, the chat admission pair, the document-source tests and the `#leads` thread fence. The real admission rows use `utf8-byte-upper-bound@1`: recipe/run then chat uses 15,002 input bytes + 512 reserved output = 15,514 / 16,384, with 870 headroom; chat alias uses 14,963 + 512 = 15,475 / 16,384, with 909 headroom. Both are executable. The unchanged update Send glass passes all four cases at 1440 and 393. `dw check holdspeak-philo` and `git diff --check` pass.

LEDGER: Muad'Dib's full suite on `fd1028f3c` was **33 failed, 13,504 passed, 99 skipped, 4 xfailed in 4217.94s**. All 26 e2e failures pass serially; two unit/integration failures also pass serially, class (c). The five branch-new failures were the three moved AST census pins, the regenerated operations export, and the restored desk kind-boundary sentence; all five pass in the focused selection. Astra did not rerun the full suite; Muad'Dib owns it on the new head.

AMENDMENTS: `design/document-sources.md` §2 records the exact palette ruling; §4 and the phase status D2 record its MCP/HTTP boundary and that prepare carries the preview. The story scope and palette membership fence now state the same rule. The original owner phrases, kind-boundary guidance and guard assertions remain intact. Census anchors follow the real source sites without loosening their checks.

UNKNOWN: the full suite on this round's head and Muad'Dib's new counsel are pending. This round makes no claim of owner observation or remote delivery.
