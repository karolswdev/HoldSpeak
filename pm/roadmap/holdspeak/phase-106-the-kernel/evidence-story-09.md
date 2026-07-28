# Evidence - HS-106-09

- **Story:** HS-106-09 - Docs: the kernel at the entry points
- **Status:** done
- **Date:** 2026-07-27

## Truth audit

Every present-tense claim added by this story was checked against the merged
HS-106-08 tree. The implementation source, not the story recipe, is the
truth source in this table.

| Entry point | Claim audited | Shipped truth source | Result |
|---|---|---|---|
| Backend architecture | The caller plane is exactly `read`, `submit`, `decide`, and `events`. | `holdspeak/kernel/runtime.py:80-94`; `holdspeak/kernel/broker.py:35-68,137-195` | Exact. Four caller calls remain. |
| Backend architecture | `read` projects operation, canonical, process, and receipt views within read scope. | `holdspeak/kernel/broker.py:35-65` | Exact. |
| Backend architecture | `submit` admits registered typed operations and refuses an unregistered name/version. | `holdspeak/kernel/broker.py:67-75`; `holdspeak/kernel/model.py:51-59` | Exact. |
| Backend architecture | `decide` is owner-only, revision-checked, and cannot replace the admitted payload or target. | `holdspeak/kernel/broker.py:137-185`; `holdspeak/principals.py:37-49` | Exact. The decision changes state and stores authority against the existing envelope hash, target, and placement. |
| Backend architecture | `events` replays journal facts after a cursor. | `holdspeak/kernel/broker.py:188-195`; `holdspeak/kernel/journal.py:114-131` | Exact. |
| Backend architecture | Operation types are registered at trusted startup under `submit`; six are registered now. | `holdspeak/kernel/runtime.py:28-49`; codec names at `tool_call.py:27-28`, `process_input.py:34-35`, `process_spawn.py:34-35`, `actuator.py:42-43`, `inference.py:56-57,183-184` | Exact: `tool.call@1`, `process.input@1`, `process.spawn@1`, `actuator.egress@1`, `inference.run@1`, `inference.cancel@1`. |
| Backend architecture | The executor plane is `claim`, `receipt`, and `reconcile`; only a node can use it. | `holdspeak/kernel/executor.py:9-83`; `holdspeak/kernel/runtime.py:96-105` | Exact. |
| Backend architecture | A claim validates the approved one-use authority before work is returned. | `holdspeak/kernel/executor.py:13-40`; `holdspeak/kernel/broker.py:167-185` | Exact. |
| Backend architecture | A terminal receipt is immutable and includes failed, refused, and indeterminate outcomes. | `holdspeak/kernel/executor.py:42-68`; `holdspeak/kernel/journal.py:271-291` | Exact. |
| Backend architecture | The journal stores bounded metadata on a per-stream SHA-256 chain and supports cursor replay. | `holdspeak/kernel/journal.py:13-27,43-131` | Exact. |
| Backend architecture | Native records remain the content authority and project through `read`, rather than being copied into the journal. | `holdspeak/kernel/broker.py:52-63`; `holdspeak/kernel/actuator.py:172-202`; `holdspeak/kernel/process_input.py:27-31` | Exact. |
| Backend architecture | The bus is a projection of journal facts, not a command path or second truth. | `holdspeak/kernel/runtime.py:92-94`; `holdspeak/kernel/journal.py:114-131`; `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:246-274` | Exact as the kernel transport rule. Commands enter through the typed operation path; replay comes from the journal cursor. |
| Security | The kernel is an audit and consent boundary for cooperating code, not a sandbox against arbitrary in-process Python. | `holdspeak/connector_runtime.py:7-22`; `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:52-65,225-244` | Narrowed early and exact. |
| Security | Raw process, socket, tmux, typing, and desktop effects remain ambient imports in the current process. | `holdspeak/connector_runtime.py:27-30,109-143`; `holdspeak/kernel/effect_ledger.json:137-217,301-390`; RFC `§5b` at `PLAN_KERNEL_OPERATION_BROKER.md:225-244` | Exact. This prevents a sandbox claim. |
| Security | The stronger boundary requires raw effects in a privileged executor process and untrusted code holding warrants instead of ambient imports before untrusted or agent-authored code executes. | `docs/internal/PLAN_KERNEL_OPERATION_BROKER.md:225-244` | Exact named threshold; not claimed as shipped. |
| Security | The live debt register has 40 sites: 4 covered and 36 not covered. | `holdspeak/kernel/effect_ledger.json:14-25`; all 40 entries at lines 26-390; `tests/unit/test_kernel_effect_fence.py:381-404` | Exact live count. |
| Security | The register and Article XI clause 6 expire together when the register is empty. | `docs/internal/CONSTITUTION.md:144-148,156-158` | Exact. |
| Security | Owner, agent, and node identities are derived from credentials at the edge; routing denies by default. | `holdspeak/principals.py:17-69,115-127,165-211` | Exact. Unknown API routes require owner rights rather than falling open. |
| Security | Agents can never call `decide`. | `holdspeak/principals.py:37-49,187-192`; `holdspeak/kernel/broker.py:141-143` | Exact. Agent rights omit `DECIDE`; broker decision also requires owner kind and right. |
| User guide | A direct owner click is not confirmed twice. | `docs/internal/CONSTITUTION.md:135-139`; `holdspeak/delivery/factory_launch.py:823-863`; `holdspeak/web/routes/delivery_prs.py:266-289` | Exact for Send agent and Draft review owner gestures. |
| User guide | Diff reads the local checkout and offers fetch separately when commits are absent. | `holdspeak/delivery/pr_receipts.py:369-398` | Exact. |
| User guide | Send agent uses the exact matched worktree, bounded instruction, and bounded PR diff. | `holdspeak/delivery/pr_receipts.py:295-329`; `holdspeak/web/routes/delivery_prs.py:131-174` | Exact. |
| User guide | Draft review runs the selected inference target and persists the result as an Artifact. | `holdspeak/web/routes/delivery_prs.py:225-338` | Exact. |
| User guide | With the gate armed, a matched risky call waits for Approve or Deny and does not run while held. | `holdspeak/coder_gate.py:11-20,285-376`; `holdspeak/web/routes/system/gate_routes.py:80-198` | Exact. |
| User guide | A PR comment proposal shows the complete preview and waits for Approve or Deny. | `holdspeak/web/routes/delivery_prs.py:347-405`; `web/src/desk/components/PrReceiptsSection.tsx:127-143` | Exact. |
| User guide | Approval posts exactly the stored comment; denial leaves GitHub untouched. | `holdspeak/plugins/builtin/github_pr_actuator.py:1-45`; `holdspeak/web/routes/delivery_prs.py:407-437`; `pm/roadmap/holdspeak/phase-106-the-kernel/evidence-story-08.md:235-250` | Exact. Real GitHub proof found one approved comment and no denied comment. |
| User guide | PR action results render inline below the row, and spawned sessions retain session receipts. | `web/src/desk/components/PrReceiptsSection.tsx:137-143`; `docs/USER_GUIDE.md:706-720`; `holdspeak/delivery/factory_launch.py:906-912` | Exact. |
| User guide | Merge, close, and force-push are not offered. | `holdspeak/delivery/pr_receipts.py:324-329`; `holdspeak/plugins/builtin/github_pr_actuator.py:1-5,17-29` | Exact. The offered write verbs are comment and commit status only. |
| README | The Desk can send a Coder session to a matched worktree, draft a review Artifact, and prepare an approval-held GitHub comment. | `holdspeak/web/routes/delivery_prs.py:131-174,225-405` | Exact. |
| README | The PR row renders the result as a Receipt. | `web/src/desk/components/PrReceiptsSection.tsx:137-143` | Exact. |
| README | Merge, close, and force-push remain unavailable. | `holdspeak/delivery/pr_receipts.py:324-329`; `holdspeak/plugins/builtin/github_pr_actuator.py:1-5` | Exact. |
| Constitution cross-reference | Article XI and its clause 6 sunset anchor still resolve; no constitutional edit is needed. | `docs/internal/CONSTITUTION.md:118-148,150-161`; links from `docs/SECURITY.md` and `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md` | Exact. The link guard is green. |

## Claims narrowed or corrected

1. **No sandbox claim.** The docs do not generalize the broker into a security
   boundary. They state the cooperating-code limit before any stronger kernel
   claim and name the RFC section 5b confinement threshold.
2. **No universal-coverage claim.** Article XI clause 2 is not described as
   universally implemented. The security page names all 40 ledgered sites and
   says plainly that 36 remain outside the kernel as declared debt.
3. **No invented PR authority.** The user docs list only the verbs in the live
   PR row. Merge, close, and force-push are absent by design.
4. **Six operations, not four or five.** HS-106-08 registered
   `process.spawn@1`; the documentation uses the merged runtime's current count
   and keeps the four-call count scoped to the caller plane.

## Live count proof

The merged tree was instantiated through `holdspeak.kernel.runtime._build`, and
the broker registry plus ledger entries were counted rather than inferred from
story prose:

```json
{"caller_calls":["read","submit","decide","events"],"caller_count":4,"registered_count":6,"registered_operations":["actuator.egress@1","inference.cancel@1","inference.run@1","process.input@1","process.spawn@1","tool.call@1"],"ledger_total":40,"ledger_covered":4,"ledger_not_covered":36}
```

## Mermaid proof

The exact fenced diagram from `ARCHITECTURE_BACKEND_RUNTIME.md` was rendered
with `@mermaid-js/mermaid-cli`. The command exited 0 and generated an SVG:

```text
Generating single mermaid chart
```

## Focused guards

After syncing the repository's test extra, the final focused command covered
voice, vocabulary, links, and the effect register:

```text
uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_kernel_effect_fence.py
25 passed in 1.01s
```

A direct vocabulary scan also found none of `submit`, `decide`, `warrant`, or
`principal` in `docs/USER_GUIDE.md`.

## Full-suite adjudication

The first captured attempt found collection errors because the fresh worktree's
virtual environment did not yet contain the project's test extra. That is test
environment setup, not a product failure. After `uv sync --extra test`, the
suite ran. Its first complete pass found five failures because the optional
OpenAI-compatible client was also absent. Installing that optional client and
re-running the five failures produced **4 passed and only the pre-adjudicated
voice-notes failure** in 259.31 seconds.

The final required command was then run again from the frozen tree and its whole
output file was read before the story flip:

```text
uv run pytest -q --ignore=tests/e2e/test_metal.py
1 failed, 4279 passed, 41 skipped, 1 warning in 817.38s (0:13:37)
```

The sole failure is
`tests/uat/test_voice_notes.py::test_transcribe_up_but_unreachable_is_honest`.
The product returns the honest existing text `Transcribe failed (HTTP 502).`,
while the test accepts only wording containing `reach` or `not up`. This is the
user's pre-adjudicated wording drift and reproduces without kernel code. No
failure outside the accepted list remained. The warning is the existing
meeting-import teardown race: a background thread reached its temporary SQLite
database after the test removed it.

### Captured run — 2026-07-28T00:55:19Z

- **Command:** `bash -o pipefail -c uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/hs10609-full-suite.txt`
- **Cwd:** .
- **Exit code:** 2
- **Index-tree:** 43bf5d6bc229c2957f75c3afeaca4e0962a7fa61

```text

==================================== ERRORS ====================================
___________ ERROR collecting tests/integration/test_cadence_agent.py ___________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_cadence_agent.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_cadence_agent.py:8: in <module>
    from fastapi import FastAPI
E   ModuleNotFoundError: No module named 'fastapi'
__________ ERROR collecting tests/integration/test_cadence_routes.py ___________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_cadence_routes.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_cadence_routes.py:7: in <module>
    from fastapi import FastAPI
E   ModuleNotFoundError: No module named 'fastapi'
__________ ERROR collecting tests/integration/test_core_path_smoke.py __________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_core_path_smoke.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_core_path_smoke.py:43: in <module>
    from holdspeak.text_processor import TextProcessor
holdspeak/text_processor.py:6: in <module>
    import pyperclip
E   ModuleNotFoundError: No module named 'pyperclip'
_____ ERROR collecting tests/integration/test_dictation_journal_replay.py ______
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_dictation_journal_replay.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_dictation_journal_replay.py:18: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
_____ ERROR collecting tests/integration/test_dictation_journal_wiring.py ______
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_dictation_journal_wiring.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_dictation_journal_wiring.py:28: in <module>
    from holdspeak.web.routes.dictation._helpers import _run_dictation_dry_run_text
holdspeak/web/routes/__init__.py:13: in <module>
    from .activity import build_activity_router
holdspeak/web/routes/activity/__init__.py:26: in <module>
    from fastapi import APIRouter
E   ModuleNotFoundError: No module named 'fastapi'
_____ ERROR collecting tests/integration/test_dictation_moment_of_truth.py _____
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_dictation_moment_of_truth.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_dictation_moment_of_truth.py:20: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
______ ERROR collecting tests/integration/test_one_place_relationships.py ______
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_one_place_relationships.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_one_place_relationships.py:5: in <module>
    from fastapi import FastAPI
E   ModuleNotFoundError: No module named 'fastapi'
_______ ERROR collecting tests/integration/test_principal_separation.py ________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_principal_separation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_principal_separation.py:9: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
_______ ERROR collecting tests/integration/test_setup_first_dictation.py _______
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_setup_first_dictation.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_setup_first_dictation.py:12: in <module>
    import holdspeak.web_runtime as web_runtime
holdspeak/web_runtime.py:50: in <module>
    from .text_processor import TextProcessor
holdspeak/text_processor.py:6: in <module>
    import pyperclip
E   ModuleNotFoundError: No module named 'pyperclip'
_____ ERROR collecting tests/integration/test_setup_first_value_journey.py _____
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_setup_first_value_journey.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_setup_first_value_journey.py:9: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
_________ ERROR collecting tests/integration/test_web_activity_api.py __________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_activity_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_activity_api.py:11: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
___________ ERROR collecting tests/integration/test_web_auth_gate.py ___________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_auth_gate.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_auth_gate.py:12: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
__________ ERROR collecting tests/integration/test_web_built_mount.py __________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_built_mount.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_built_mount.py:9: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
________ ERROR collecting tests/integration/test_web_commands_board.py _________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_commands_board.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_commands_board.py:15: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
_____ ERROR collecting tests/integration/test_web_dictation_blocks_api.py ______
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_blocks_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_blocks_api.py:15: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
__ ERROR collecting tests/integration/test_web_dictation_correction_ritual.py __
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_correction_ritual.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_correction_ritual.py:15: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
___ ERROR collecting tests/integration/test_web_dictation_corrections_api.py ___
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_corrections_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_corrections_api.py:17: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
_______ ERROR collecting tests/integration/test_web_dictation_journal.py _______
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_journal.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_journal.py:17: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
___ ERROR collecting tests/integration/test_web_dictation_learning_digest.py ___
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_learning_digest.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_learning_digest.py:16: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
____ ERROR collecting tests/integration/test_web_dictation_readiness_api.py ____
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_readiness_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_readiness_api.py:10: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
____ ERROR collecting tests/integration/test_web_dictation_settings_api.py _____
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_settings_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_settings_api.py:15: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
____ ERROR collecting tests/integration/test_web_dictation_trust_signals.py ____
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dictation_trust_signals.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dictation_trust_signals.py:17: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
__________ ERROR collecting tests/integration/test_web_dry_run_api.py __________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_dry_run_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_dry_run_api.py:16: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
________ ERROR collecting tests/integration/test_web_flagship_audit.py _________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_flagship_audit.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_flagship_audit.py:23: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
______ ERROR collecting tests/integration/test_web_presence_onboarding.py ______
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_presence_onboarding.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_web_presence_onboarding.py:7: in <module>
    from fastapi.testclient import TestClient
E   ModuleNotFoundError: No module named 'fastapi'
________ ERROR collecting tests/integration/test_web_project_kb_api.py _________
ImportError while importing test module '/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/integration/test_web_project_kb_api.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/lib/python3.14/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-28T00:56:48Z

- **Command:** `bash -o pipefail -c uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/hs10609-full-suite.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 43bf5d6bc229c2957f75c3afeaca4e0962a7fa61

```text
ssssssssssssssssssssssssssssssss........................................ [  1%]
........................................................................ [  3%]
..s..................................................................... [  5%]
.................................................................ss..... [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
...........................................................F...F.......F [ 20%]
...........F............................................................ [ 21%]
...............F........................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
...........................s............................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 98%]
....................................................................     [100%]
=================================== FAILURES ===================================
________________ test_meeting_recipe_yields_a_real_open_action _________________

real_manager = <uat.conductor.runs.RunManager object at 0x1107899f0>

    def test_meeting_recipe_yields_a_real_open_action(real_manager):
        run = _boot_or_skip(real_manager, "golden-43")
>       result = real_manager.apply_recipe(run.id, "meeting-just-ended-open-actions")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_43.py:52: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x1386d18b0>
name = 'meeting-just-ended-open-actions', run_id = 'run-20260728T010138-5f014e'
host = <uat.conductor.runs.RunManager object at 0x1107899f0>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)
    
        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )
    
        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)
    
        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)
    
        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe
    
        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )
    
        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))
    
        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'meeting-just-ended-open-actions' failed to verify: meeting_with_open_actions: timed out after 180s: meetings present but none with ≥1 open actions: Pylon incident war room (UAT seed)(0,queued)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________ test_intel_endpoint_dead_degrades_honestly __________________

real_manager = <uat.conductor.runs.RunManager object at 0x1113ffb10>

    def test_intel_endpoint_dead_degrades_honestly(real_manager):
        run = _boot_or_skip(real_manager)
>       result = real_manager.apply_recipe(run.id, "intel-endpoint-dead")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_induction_integration_local.py:73: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x11136f290>
name = 'intel-endpoint-dead', run_id = 'run-20260728T010951-2005a3'
host = <uat.conductor.runs.RunManager object at 0x1113ffb10>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)
    
        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )
    
        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)
    
        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)
    
        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe
    
        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )
    
        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))
    
        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'intel-endpoint-dead' failed to verify: runtime_endpoint_unreachable: runtime-test ok=False status='unavailable' in 0.0s: Backend 'openai_compatible' requires the 'openai' package. Install with: uv pip install holdspeak[dictation-openai]

uat/conductor/induction/recipes.py:240: RecipeVerifyError
______________ test_run_dispatched_onto_the_worker_returns_badged ______________

real_manager = <uat.conductor.runs.RunManager object at 0x111831130>

    def test_run_dispatched_onto_the_worker_returns_badged(real_manager):
        run = _boot_or_skip(real_manager, "mesh-node")
    
>       result = real_manager.apply_recipe(run.id, "mesh-run-on-worker")
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/uat/test_mesh_dispatch.py:55: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
uat/conductor/runs.py:387: in apply_recipe
    return self.recipes.apply(name, run_id, self, allow_intel=allow_intel)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <uat.conductor.induction.recipes.RecipeEngine object at 0x13ad0de50>
name = 'mesh-run-on-worker', run_id = 'run-20260728T010956-f9c70f'
host = <uat.conductor.runs.RunManager object at 0x111831130>

    def apply(
        self, name: str, run_id: str, host: "RecipeHost", *, allow_intel: bool = True
    ) -> ApplyResult:
        order = self.registry.resolve_order(name)
        target = self.registry.load(name)
    
        if target.requires_intel and not allow_intel:
            raise RecipeError(
                f"recipe {name!r} requires intel (the .43 LAN endpoint) but "
                "intel is disabled for this apply"
            )
    
        # 1. Ensure the run is booted on the recipe's deck + cache posture.
        restarted = host.ensure_deck(run_id, target.deck, link_caches=target.link_caches)
    
        client = host.product_client(run_id)
        home = host.run_home(run_id)
        evaluator = ProbeEvaluator(client, home=home, run_id=run_id)
    
        # The combined probe is the target's own probe (includes stage the world;
        # the target's probe is the authoritative claim). Included recipes still
        # contribute their seeds/actions below.
        probe_spec = target.probe
    
        # 2. Probe-first idempotency.
        pre = evaluator.evaluate(probe_spec)
        if pre.ok and probe_spec:
            return ApplyResult(
                recipe=name,
                deck=target.deck,
                already_satisfied=True,
                probe=pre.to_dict(),
                restarted=restarted,
            )
    
        # 3. Stage: seeds (deps first), then actions (deps first).
        seed_outcomes: list[dict] = []
        action_log: list[dict] = []
        for rn in order:
            r = self.registry.load(rn)
            for seed_name in r.seeds:
                manifest = self.seed_registry.load(seed_name)
                seed_outcomes.append(Seeder(client).apply(manifest).to_dict())
            for action in r.actions:
                action_log.append(self._run_action(action, run_id, host, client))
    
        # 4. Verify.
        post = evaluator.evaluate(probe_spec)
        result = ApplyResult(
            recipe=name,
            deck=target.deck,
            already_satisfied=False,
            probe=post.to_dict(),
            seeds=seed_outcomes,
            actions=action_log,
            restarted=restarted,
        )
        if probe_spec and not post.ok:
>           raise RecipeVerifyError(
                f"recipe {name!r} failed to verify: {post.summary()}", result
            )
E           uat.conductor.induction.recipes.RecipeVerifyError: recipe 'mesh-run-on-worker' failed to verify: run_returned_badged: dispatch failed HTTP 502: None; run_claimed_by_worker: worker claims 0→1 (moved=True); hub provider='' scope='' (no-local=False); run_output_contains: output MISSING 'PYLON-CANARY-7' (0 chars)

uat/conductor/induction/recipes.py:240: RecipeVerifyError
__________________________ test_pack_d_stages_locally __________________________

real_client = <starlette.testclient.TestClient object at 0x13917fce0>

    def test_pack_d_stages_locally(real_client):
        """Pack D demos without the LAN: its bad-endpoint scenario stages + verifies."""
        created = real_client.post("/api/sittings", json={"pack": "pack-d-honest-failure"}).json()
        if created["run"] is None or created["run"]["status"] != "up":
            pytest.skip("product did not boot")
        sid = created["id"]
        # Stage the dead-endpoint scenario (fully local — port 9 refused).
        staged = real_client.post(f"/api/sittings/{sid}/stage", json={"scenario_id": "d-dead-endpoint-doctor"}).json()
>       assert staged["ok"], staged
E       AssertionError: {'ok': False, 'scenario_id': 'd-dead-endpoint-doctor', 'staging': [{'error': "recipe 'intel-endpoint-dead' failed to v...--no-open`): browser auto-open disabled.
E         Press Ctrl+C to stop.'}, 'ok': False, 'recipe': 'intel-endpoint-dead', ...}]}
E       assert False

tests/uat/test_packs.py:180: AssertionError
_________________ test_transcribe_up_but_unreachable_is_honest _________________

client = <starlette.testclient.TestClient object at 0x10fe35370>

    def test_transcribe_up_but_unreachable_is_honest(client):
        # Fake product reports 'up' but nothing actually serves the transcribe route,
        # so the proxy honestly reports it could not reach the product — never fakes.
        sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
        r = client.post(f"/api/sittings/{sid}/transcribe", content=_silence_wav())
        body = r.json()
        assert body["ok"] is False
>       assert "reach" in body["error"].lower() or "not up" in body["error"].lower()
E       AssertionError: assert ('reach' in 'transcribe failed (http 502).' or 'not up' in 'transcribe failed (http 502).')
E        +  where 'transcribe failed (http 502).' = <built-in method lower of str object at 0x10f5dda20>()
E        +    where <built-in method lower of str object at 0x10f5dda20> = 'Transcribe failed (HTTP 502).'.lower
E        +  and   'transcribe failed (http 502).' = <built-in method lower of str object at 0x10f5dda20>()
E        +    where <built-in method lower of str object at 0x10f5dda20> = 'Transcribe failed (HTTP 502).'.lower

tests/uat/test_voice_notes.py:52: AssertionError
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/.venv/lib/python3.14/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-8aa15508
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_hash=state.t
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-07-28T01:19:10Z

- **Command:** `bash -o pipefail -c uv run pytest -q --ignore=tests/e2e/test_metal.py 2>&1 | tee /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/755cdf1e-8c7b-4e33-923d-a46dc3bb7d49/scratchpad/hs10609-full-suite-final.txt`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 43bf5d6bc229c2957f75c3afeaca4e0962a7fa61

```text
ssssssssssssssssssssssssssssssss........................................ [  1%]
........................................................................ [  3%]
..s..................................................................... [  5%]
.................................................................ss..... [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 21%]
...............F........................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
...........................s............................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 98%]
....................................................................     [100%]
=================================== FAILURES ===================================
_________________ test_transcribe_up_but_unreachable_is_honest _________________

client = <starlette.testclient.TestClient object at 0x111876470>

    def test_transcribe_up_but_unreachable_is_honest(client):
        # Fake product reports 'up' but nothing actually serves the transcribe route,
        # so the proxy honestly reports it could not reach the product — never fakes.
        sid = client.post("/api/sittings", json={"pack": "smoke"}).json()["id"]
        r = client.post(f"/api/sittings/{sid}/transcribe", content=_silence_wav())
        body = r.json()
        assert body["ok"] is False
>       assert "reach" in body["error"].lower() or "not up" in body["error"].lower()
E       AssertionError: assert ('reach' in 'transcribe failed (http 502).' or 'not up' in 'transcribe failed (http 502).')
E        +  where 'transcribe failed (http 502).' = <built-in method lower of str object at 0x13dd54850>()
E        +    where <built-in method lower of str object at 0x13dd54850> = 'Transcribe failed (HTTP 502).'.lower
E        +  and   'transcribe failed (http 502).' = <built-in method lower of str object at 0x13dd54850>()
E        +    where <built-in method lower of str object at 0x13dd54850> = 'Transcribe failed (HTTP 502).'.lower

tests/uat/test_voice_notes.py:52: AssertionError
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/.venv/lib/python3.14/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-354fdf83
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_hash=state.transcript_hash(),
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          reason=state.intel_status_detail,
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/db/core.py", line 1449, in _connection
      conn.commit()
      ~~~~~~~~~~~^^
  sqlite3.OperationalError: disk I/O error
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/threading.py", line 1082, in _bootstrap_inner
      self._context.run(self.run)
      ~~~~~~~~~~~~~~~~~^^^^^^^^^^
    File "/Users/karol/.local/share/uv/python/cpython-3.14.2-macos-aarch64-none/lib/python3.14/threading.py", line 1024, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/web/routes/meeting_import.py", line 136, in _run_import_job
      _set_import_status(
      ~~~~~~~~~~~~~~~~~~^
          db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/web/routes/meeting_import.py", line 72, in _set_import_status
      state = db.meetings.get_meeting(meeting_id)
    File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/holdspeak/db/meetings.py", line 440, in get_meeting
      row = conn.execute(
            ~~~~~~~~~~~~^
          "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      ).fetchone()
      ^
  sqlite3.OperationalError: no such table: meetings
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_live_bus.py:24: needs Playwright + a browser
SKIPPED [1] tests/e2e/test_route_preflight.py:26: pre-flight needs Playwright + a browser
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/unit/test_mesh_discovery.py:21: could not import 'zeroconf': No module named 'zeroconf'
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a630412d34d224c90/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_dictation_grammars.py:91: could not import 'llama_cpp': No module named 'llama_cpp'
FAILED tests/uat/test_voice_notes.py::test_transcribe_up_but_unreachable_is_honest
1 failed, 4279 passed, 41 skipped, 1 warning in 817.38s (0:13:37)
```

### Captured run — 2026-07-28T01:37:25Z

- **Command:** `uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_kernel_effect_fence.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dc196e15205b3b38de0058eebb9a1dab43146c90

```text
.........................                                                [100%]
25 passed in 1.28s
```
