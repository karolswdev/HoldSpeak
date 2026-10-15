# Settings audit: bounded Python verification repair

Status: DRAFT — hold for SHIP. No staging or commit by this worker.

Worktree: `/Users/karol/dev/tools/wt-settings-audit-20261014`
Branch: `feat/settings-audit-20261014`
Source baseline: `eef72f987`

The first related-Python quick check reported **1129 passed, 2 failed**
(`.tmp/settings-audit/quick-first-python.log`). Both defects were already
present at the source baseline. This repair changes one test setup and one
recorded hub answer. It changes no product code.

## Exact causes

1. `test_install_follows_codex_home_and_reads_back_ready` supplied a temporary
   `CODEX_HOME` but no agent-state setting. The service used that explicit env
   to choose the hooks file. Its trust step then merged the process env, whose
   `HOLDSPEAK_AGENT_STATE=off` guard removed `CODEX_HOME`
   (`holdspeak/services/onboarding_service.py:544`, `:581`). The on-disk fake
   Codex therefore listed session hooks but could not list the installed rider
   hooks. The trust result was `codex_hooks_untrusted`, with seven missing
   installed hooks. The diagnostic recorded `agent_state: off`,
   `codex_home: null`, and an executable under the test's `fakebin` in
   `.tmp/settings-audit/python-codex-diagnostic.json`.

   `git show eef72f987:tests/unit/test_onboarding_agents.py` and
   `git show eef72f987:holdspeak/services/onboarding_service.py` confirmed the
   same test setup, merge, and guard in the baseline. The audit's product diff
   in this service is confined to calendar source labels.

2. The stored honest-faces board lacked `provenance.source_ref` on its two
   action items. `git show eef72f987:holdspeak/services/follow_through_service.py`
   confirmed that `CardProvenance.source_ref` already existed in the baseline
   (`holdspeak/services/follow_through_service.py:83`). The real hub produced
   that key as `null` for both meeting action items. The existing shape fence
   correctly rejected the stale recording.

## Changes

- `tests/unit/test_onboarding_agents.py:276` explicitly enables reads for the
  service's wholly temporary fake-agent environment and uses `fake.home`.
  The enclosing process remains isolated with agent state off. The test still
  uses authenticated HTTP, the admitted kernel operation, the real hook
  installer, and an on-disk fake app-server process. All prior assertions
  remain. An added assertion proves that the fake trusted a key from the
  installed hooks file at that temporary `CODEX_HOME` (`:290`).
- `web/src/test/wire/follow-through-board.honest-faces.wire.json:24` and `:49`
  now contain the real producer's `source_ref: null`. The capture time and two
  relative creation dates changed with the recording. IDs, labels, rows,
  lanes, statuses, and all other payload values are unchanged.

The diagnostic loaded `.tmp/settings-audit/python_diagnostic.py` to assert
that the Codex executable was the temporary fake, record only relevant guard
facts, and redirect the honest-faces wire output to
`.tmp/settings-audit/wire-regenerated/`. The one named test ran with
`HOLDSPEAK_WIRE_WRITE=1`; no tracked wire was rewritten during that run.
All six generated recordings were diffed against their stored originals.
Only the owned follow-through recording was copied into the tree; the other
five had date/ID churn only and remain in scratch.

## Proof

Every invocation used `.tmp/settings-audit/locked.py`: one machine-wide test
lock, a fresh HOME removed afterward, and the four isolation switches
(`HOLDSPEAK_AGENT_STATE=off`, `HOLDSPEAK_ACTIVE_TARGET=off`,
`HOLDSPEAK_DESKTOP_NOTIFY=0`, `HOLDSPEAK_MACOS_CALENDAR=0`).

Diagnostic, before the repair:

```sh
PYTHONPATH=.tmp/settings-audit HOLDSPEAK_WIRE_WRITE=1 .venv/bin/python .tmp/settings-audit/locked.py python-diagnostic .venv/bin/python -m pytest -q -p python_diagnostic tests/unit/test_onboarding_agents.py::test_install_follows_codex_home_and_reads_back_ready tests/integration/test_face_wire_fences.py::test_honest_faces_and_arrival_reads
```

`.tmp/settings-audit/python-diagnostic.log`: **1 failed, 1 passed in 1.85s**.
The intended Codex failure reproduced. The real hub successfully generated
all honest-faces/arrival answers into scratch.

Green run, without the diagnostic plugin or wire writing:

```sh
.venv/bin/python .tmp/settings-audit/locked.py python-repair-green .venv/bin/python -m pytest -q -rA tests/unit/test_onboarding_agents.py::test_install_follows_codex_home_and_reads_back_ready tests/integration/test_face_wire_fences.py::test_honest_faces_and_arrival_reads
```

`.tmp/settings-audit/python-repair-green.log`: **2 passed in 1.84s**. Its
summary names both exact node IDs. This is one diagnostic execution and one
green execution, within the worker budget.

Collection only, with no tests executed:

```sh
.venv/bin/python .tmp/settings-audit/locked.py python-repair-collect .venv/bin/python -m pytest --collect-only -q tests/unit/test_onboarding_agents.py::test_install_follows_codex_home_and_reads_back_ready tests/integration/test_face_wire_fences.py::test_honest_faces_and_arrival_reads
```

`.tmp/settings-audit/python-repair-collect.log` names both exact nodes and
reports **2 tests collected in 0.33s**.

## Limits and handoff

No owner state, native service, network service, or real Codex process was
used. No assertion or shape fence was weakened. No product defect was found
in this bounded diagnosis. This preserves the audit's useful checks without
adding product machinery (Tenets 1 and 3).

The root orchestrator owns the complete quick-check rerun and the merge.
This worker did not rerun whole files, exercise Settings in a browser, or
make a Tuesday usability claim. The two tracked repair paths and this report
are ready for review and explicit-path staging by the root orchestrator.
