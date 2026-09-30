# Evidence - PHILO-11-01

- **Story:** PHILO-11-01 - The document sources
- **Status:** done
- **Date:** 2026-09-29

## Proof

The lane report and a/b/c classification are in [lane-01-astra.md](lane-01-astra.md). Both full-suite red outputs remain below. The final follow-ups prove all unit fallout corrected (48 collected, 48 passed) and all 26 glass failures serial-green twice (52/52 invocations). Counsel-on-built remains with Muad'Dib.

The attempted baseline rig run at `2026-09-30T02:42:51Z` is **not baseline proof**: the parent imported the archived package, but its hub subprocess still resolved the editable current package. Its eight passes are retained as a rejected verification attempt. The corrected baseline run below exports the archived package path to the subprocess too. The in-process baseline wire failure at `2026-09-30T02:40:19Z` is unaffected.

### Captured run — 2026-09-30T02:37:31Z

- **Command:** `uv run python scripts/verify_philo11_update_glass.py --collect-only`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[1440]
tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_the_first_setup_loop_and_every_file_state[393]
tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[1440]
tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result[393]

4 tests collected in 0.02s
```

### Captured run — 2026-09-30T02:40:19Z

- **Command:** `bash -c PHILO_TEST_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_TEST_HOME"' EXIT; env HOME="$PHILO_TEST_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python -c 'import sys; from pathlib import Path; sys.path.insert(0, str(Path(".tmp/philo11/base-332d9158").resolve())); import holdspeak; print("BASE PRODUCT:", holdspeak.__file__); import pytest; raise SystemExit(pytest.main(["-q", "--basetemp=" + sys.argv[1], "tests/unit/test_philo10_send_contract.py::test_http_and_mcp_reach_the_same_rows"]))' "$PHILO_TEST_HOME/pytest"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
BASE PRODUCT: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/holdspeak/__init__.py
F                                                                        [100%]
=================================== FAILURES ===================================
____________________ test_http_and_mcp_reach_the_same_rows _____________________

hub = <test_philo5_the_loop.Hub object at 0x10ebd0d70>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.OJE8xCLeEz/pytest/test_http_and_mcp_reach_the_sa0')

    def test_http_and_mcp_reach_the_same_rows(hub: Hub, tmp_path: Path) -> None:
        _pid, update = room(hub)
        dest = destination(hub, tmp_path / "out")
        is_error, prepared = hub.mcp("channel.prepare", {"document_ref": f"project_update:{update}", "destination_id": dest})
>       assert is_error is False, prepared
E       AssertionError: {'code': 'validation', 'error': "Invalid arguments for channel.prepare: 'update_id' is a required property", 'operatio...ession', 'actor_kind': 'owner', 'authority_basis': 'refused_at_admission', 'created_at': 1790736021.6582558, ...}, ...}
E       assert True is False

tests/unit/test_philo10_send_contract.py:104: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo10_send_contract.py::test_http_and_mcp_reach_the_same_rows
1 failed in 2.24s
```

### Captured run — 2026-09-30T02:41:30Z

- **Command:** `bash -c PHILO_TEST_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_TEST_HOME"' EXIT; env HOME="$PHILO_TEST_HOME" uv run pytest -q --collect-only --basetemp="$PHILO_TEST_HOME/pytest" tests/integration/test_philo11_document_rig.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[project_update]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[monday_brief]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[desk_decision]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_decision]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[decision_record]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_summary]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_digest]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_followup]

8 tests collected in 0.01s
```

### Captured run — 2026-09-30T02:41:45Z

- **Command:** `bash -c PHILO_TEST_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_TEST_HOME"' EXIT; env HOME="$PHILO_TEST_HOME" uv run pytest -q -s --basetemp="$PHILO_TEST_HOME/pytest" tests/integration/test_philo11_document_rig.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text

DOCUMENT RIG {"db_under_home": true, "document_ref": "project_update:philo11-update", "kind": "project_update", "payload_digest": "2c5aaecd37e07012935b29dfb8404cb4faf1858e89213b7ed13930c54f4dc885", "steps": [{"name": "channel.save_destination", "operation_id": "op_3b65b72d094d4aeeb143473994c8ad93", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_a2ad252145394c668c64d91749dd1bc2", "refusal": null}, {"name": "channel.send", "operation_id": "op_860641cb24044f06bb8a80bcab8792a8", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
DOCUMENT RIG {"db_under_home": true, "document_ref": "monday_brief:brief-61e995fbe8d14feeb09a6a55cddb2934", "kind": "monday_brief", "payload_digest": "277de7582cbaf752f6470bb33013cc75dceee17a6c4eda75403af86af6a7eba0", "steps": [{"name": "channel.save_destination", "operation_id": "op_5260ddf7662349f2b3b6a9ce114c72ef", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_272dbb7c29d443b3ba3ed9fc862477a2", "refusal": null}, {"name": "channel.send", "operation_id": "op_c1c180708a0742b58edffb50d0154716", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
DOCUMENT RIG {"db_under_home": true, "document_ref": "desk_decision:desk-philo11", "kind": "desk_decision", "payload_digest": "515f144c4ba42fff351f995d6cb15a583b9380d054962b7b304d42f956ba10d5", "steps": [{"name": "channel.save_destination", "operation_id": "op_5da6e8845dde412bae6a96a8f81f43f1", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_c5f732b2c776442d85e7e5d46384d0b6", "refusal": null}, {"name": "channel.send", "operation_id": "op_e637572f36f74a479ce7814dc0888107", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
DOCUMENT RIG {"db_under_home": true, "document_ref": "meeting_decision:dec-bc5c1e12975d2f314a38", "kind": "meeting_decision", "payload_digest": "a3f3826f1314c203f3783bc02376cfa0a8faca992c23876aecd0acec31f34d69", "steps": [{"name": "channel.save_destination", "operation_id": "op_cd87517dd333448b9fbed443f59c2a3f", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_8bf71c7634f145d08bd6263992ee39b9", "refusal": null}, {"name": "channel.send", "operation_id": "op_d31ee93b7c8d4c8896f422b5dd6b29bd", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
DOCUMENT RIG {"db_under_home": true, "document_ref": "decision_record:record-c61c9032c1054a8bac69791db5271e14", "kind": "decision_record", "payload_digest": "e4d969c11e08001edf8517beff588e7d093266c3140dfb385743d4ec125f390f", "steps": [{"name": "channel.save_destination", "operation_id": "op_7eaca9988a354e24993d902e9560900b", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_b47338bce1e24d2bb3de77c5df32186c", "refusal": null}, {"name": "channel.send", "operation_id": "op_874ff2b0a48c432c88a2df6b2ddfdaa3", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
DOCUMENT RIG {"db_under_home": true, "document_ref": "meeting_summary:philo11-meeting", "kind": "meeting_summary", "payload_digest": "75e1fb53249d37bc89b7be17797dedfa8722d3f275685058f3b2681731c06171", "steps": [{"name": "channel.save_destination", "operation_id": "op_25f65b39838c487d8521972a5d7e3296", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_10778d6b65c941f1afde3a5015cdf3c1", "refusal": null}, {"name": "channel.send", "operation_id": "op_dcfc7ebdaf734413aeb1202a31ce7d7c", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
DOCUMENT RIG {"db_under_home": true, "document_ref": "meeting_digest:philo11-meeting", "kind": "meeting_digest", "payload_digest": "a6b2e22104a8babfa48f20af781b0c85327c3a050c65adbf80ebd51098c35150", "steps": [{"name": "channel.save_destination", "operation_id": "op_1f6088a520cf444daf2dbd4ee45acdad", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_4fc46f2bf2784b988641ebcec0845ca1", "refusal": null}, {"name": "channel.send", "operation_id": "op_24cbd53a5d03426bb0548dec7c9f02f1", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
DOCUMENT RIG {"db_under_home": true, "document_ref": "meeting_followup:philo11-meeting", "kind": "meeting_followup", "payload_digest": "6493dfa6a8570d99e65625d9be091a5da51b3658ac2298cca21a97f3216d31fc", "steps": [{"name": "channel.save_destination", "operation_id": "op_8e96e531f77140aeba5fc856d4fc59ab", "refusal": null}, {"name": "channel.preview", "operation_id": null, "refusal": null}, {"name": "channel.prepare", "operation_id": "op_668a72e134e74252834641621ca4d12d", "refusal": null}, {"name": "channel.send", "operation_id": "op_ddcaa8672dab4f5a8f34e06014989e33", "refusal": null}, {"name": "channel.sends", "operation_id": null, "refusal": null}, {"name": "kernel.receipt.read", "operation_id": null, "refusal": null}]}
.
8 passed in 2.45s
```

### Captured run — 2026-09-30T02:42:51Z

- **Command:** `bash -c PHILO_TEST_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_TEST_HOME"' EXIT; env HOME="$PHILO_TEST_HOME" uv run python -c 'import sys; from pathlib import Path; base=Path(".tmp/philo11/base-332d9158").resolve(); sys.path.insert(0,str(base)); import holdspeak; sys.path.insert(0,str(base/"scripts")); import graph_walk; print("BASE PRODUCT:", holdspeak.__file__); print("BASE RIG:", graph_walk.__file__); import pytest; raise SystemExit(pytest.main(["-q", "--basetemp="+sys.argv[1], "tests/integration/test_philo11_document_rig.py"]))' "$PHILO_TEST_HOME/pytest"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
BASE PRODUCT: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/holdspeak/__init__.py
BASE RIG: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/scripts/graph_walk.py
........                                                                 [100%]
8 passed in 2.46s
```

### Captured run — 2026-09-30T02:43:40Z

- **Command:** `bash -c PHILO_TEST_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_TEST_HOME"' EXIT; env HOME="$PHILO_TEST_HOME" PYTHONPATH=/Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158 uv run python -c 'import sys; from pathlib import Path; base=Path(".tmp/philo11/base-332d9158").resolve(); sys.path.insert(0,str(base)); import holdspeak; sys.path.insert(0,str(base/"scripts")); import graph_walk; print("BASE PRODUCT:", holdspeak.__file__); print("BASE RIG:", graph_walk.__file__); import pytest; raise SystemExit(pytest.main(["-q", "--basetemp="+sys.argv[1], "tests/integration/test_philo11_document_rig.py"]))' "$PHILO_TEST_HOME/pytest"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
BASE PRODUCT: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/holdspeak/__init__.py
BASE RIG: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/scripts/graph_walk.py
FFFFFFFF                                                                 [100%]
=================================== FAILURES ===================================
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[project_update] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'project_update'

    @pytest.mark.parametrize("kind", KINDS)
    def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
        hub, documents, home = document_hub
        provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
        variables: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
    
        def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
            record = gw.run_step(
                {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
            assert record["refusal"] is None, (name, record)
            result = record["response"]
            assert isinstance(result, dict), result
            observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
            return result
    
        destination = op("channel.save_destination", {
            "channel": "file", "name": f"{kind} folder", "folder": str(home),
        })["destination"]["id"]
        ref = documents[kind]
        args = {"document_ref": ref, "destination_id": destination}
>       preview = op("channel.preview", args)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_philo11_document_rig.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'channel.preview'
args = {'destination_id': 'chd_a928e7df8d2e9f460be5c8b4', 'document_ref': 'project_update:philo11-update'}

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
>       assert record["refusal"] is None, (name, record)
E       AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_a928e7df8d2e9f460be5c8b4', 'document_ref': 'project_update:philo11-update'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E       assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None

tests/integration/test_philo11_document_rig.py:60: AssertionError
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[monday_brief] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'monday_brief'

    @pytest.mark.parametrize("kind", KINDS)
    def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
        hub, documents, home = document_hub
        provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
        variables: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
    
        def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
            record = gw.run_step(
                {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
            assert record["refusal"] is None, (name, record)
            result = record["response"]
            assert isinstance(result, dict), result
            observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
            return result
    
        destination = op("channel.save_destination", {
            "channel": "file", "name": f"{kind} folder", "folder": str(home),
        })["destination"]["id"]
        ref = documents[kind]
        args = {"document_ref": ref, "destination_id": destination}
>       preview = op("channel.preview", args)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_philo11_document_rig.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'channel.preview'
args = {'destination_id': 'chd_2a18164b0bf164eb959cc8b4', 'document_ref': 'monday_brief:brief-01d0b0a80e8f46fdb671625fce1d024d'}

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
>       assert record["refusal"] is None, (name, record)
E       AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_2a18164b0bf164eb959cc8b4', 'document_ref': 'monday_brief:brief-01d0b0a80e8f46fdb671625fce1d024d'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E       assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None

tests/integration/test_philo11_document_rig.py:60: AssertionError
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[desk_decision] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'desk_decision'

    @pytest.mark.parametrize("kind", KINDS)
    def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
        hub, documents, home = document_hub
        provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
        variables: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
    
        def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
            record = gw.run_step(
                {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
            assert record["refusal"] is None, (name, record)
            result = record["response"]
            assert isinstance(result, dict), result
            observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
            return result
    
        destination = op("channel.save_destination", {
            "channel": "file", "name": f"{kind} folder", "folder": str(home),
        })["destination"]["id"]
        ref = documents[kind]
        args = {"document_ref": ref, "destination_id": destination}
>       preview = op("channel.preview", args)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_philo11_document_rig.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'channel.preview'
args = {'destination_id': 'chd_2ee81386b4e517dc696adaa7', 'document_ref': 'desk_decision:desk-philo11'}

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
>       assert record["refusal"] is None, (name, record)
E       AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_2ee81386b4e517dc696adaa7', 'document_ref': 'desk_decision:desk-philo11'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E       assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None

tests/integration/test_philo11_document_rig.py:60: AssertionError
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_decision] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'meeting_decision'

    @pytest.mark.parametrize("kind", KINDS)
    def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
        hub, documents, home = document_hub
        provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
        variables: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
    
        def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
            record = gw.run_step(
                {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
            assert record["refusal"] is None, (name, record)
            result = record["response"]
            assert isinstance(result, dict), result
            observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
            return result
    
        destination = op("channel.save_destination", {
            "channel": "file", "name": f"{kind} folder", "folder": str(home),
        })["destination"]["id"]
        ref = documents[kind]
        args = {"document_ref": ref, "destination_id": destination}
>       preview = op("channel.preview", args)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_philo11_document_rig.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'channel.preview'
args = {'destination_id': 'chd_0085edf26f8b841e25d6c1ee', 'document_ref': 'meeting_decision:dec-bc5c1e12975d2f314a38'}

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
>       assert record["refusal"] is None, (name, record)
E       AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_0085edf26f8b841e25d6c1ee', 'document_ref': 'meeting_decision:dec-bc5c1e12975d2f314a38'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E       assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None

tests/integration/test_philo11_document_rig.py:60: AssertionError
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[decision_record] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'decision_record'

    @pytest.mark.parametrize("kind", KINDS)
    def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
        hub, documents, home = document_hub
        provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
        variables: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
    
        def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
            record = gw.run_step(
                {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
            assert record["refusal"] is None, (name, record)
            result = record["response"]
            assert isinstance(result, dict), result
            observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
            return result
    
        destination = op("channel.save_destination", {
            "channel": "file", "name": f"{kind} folder", "folder": str(home),
        })["destination"]["id"]
        ref = documents[kind]
        args = {"document_ref": ref, "destination_id": destination}
>       preview = op("channel.preview", args)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_philo11_document_rig.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'channel.preview'
args = {'destination_id': 'chd_92fae2b1bb8e6c9d098e2f85', 'document_ref': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'}

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
>       assert record["refusal"] is None, (name, record)
E       AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_92fae2b1bb8e6c9d098e2f85', 'document_ref': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E       assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None

tests/integration/test_philo11_document_rig.py:60: AssertionError
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_summary] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'meeting_summary'

    @pytest.mark.parametrize("kind", KINDS)
    def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
        hub, documents, home = document_hub
        provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
        variables: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
    
        def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
            record = gw.run_step(
                {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
            assert record["refusal"] is None, (name, record)
            result = record["response"]
            assert isinstance(result, dict), result
            observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
            return result
    
        destination = op("channel.save_destination", {
            "channel": "file", "name": f"{kind} folder", "folder": str(home),
        })["destination"]["id"]
        ref = documents[kind]
        args = {"document_ref": ref, "destination_id": destination}
>       preview = op("channel.preview", args)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_philo11_document_rig.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'channel.preview'
args = {'destination_id': 'chd_5f4ecbe3a508bb6d5b4baed3', 'document_ref': 'meeting_summary:philo11-meeting'}

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
>       assert record["refusal"] is None, (name, record)
E       AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_5f4ecbe3a508bb6d5b4baed3', 'document_ref': 'meeting_summary:philo11-meeting'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E       assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None

tests/integration/test_philo11_document_rig.py:60: AssertionError
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_digest] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'meeting_digest'

    @pytest.mark.parametrize("kind", KINDS)
    def test_each_document_previews_prepares_and_lists_through_the_real_rig(document_hub, kind: str) -> None:
        hub, documents, home = document_hub
        provenance = {"fixture_hashes": {}, "restarts": [], "boundary_substitutions": [], "clock": {}}
        variables: dict[str, Any] = {}
        observations: list[dict[str, Any]] = []
    
        def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
            record = gw.run_step(
                {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
                page=None, hub=hub, provenance=provenance, variables=variables,
            )
            assert record["refusal"] is None, (name, record)
            result = record["response"]
            assert isinstance(result, dict), result
            observations.append({"name": name, "operation_id": result.get("operation_id"), "refusal": None})
            return result
    
        destination = op("channel.save_destination", {
            "channel": "file", "name": f"{kind} folder", "folder": str(home),
        })["destination"]["id"]
        ref = documents[kind]
        args = {"document_ref": ref, "destination_id": destination}
>       preview = op("channel.preview", args)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/integration/test_philo11_document_rig.py:71: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

name = 'channel.preview'
args = {'destination_id': 'chd_03444b450fa0290440c42206', 'document_ref': 'meeting_digest:philo11-meeting'}

    def op(name: str, args: dict[str, Any]) -> dict[str, Any]:
        record = gw.run_step(
            {"kind": "op", "name": name, "args": args, "adapter": "mcp-tool"},
            page=None, hub=hub, provenance=provenance, variables=variables,
        )
>       assert record["refusal"] is None, (name, record)
E       AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_03444b450fa0290440c42206', 'document_ref': 'meeting_digest:philo11-meeting'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E       assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None

tests/integration/test_philo11_document_rig.py:60: AssertionError
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_followup] _

document_hub = (<graph_walk.Hub object at 0x10b9eb230>, {'decision_record': 'decision_record:record-54a8249aaceb47e7b3d44a568f8e8fd5'...eting', ...}, PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.4iZLsQ6LuS/pytest/philo11-rig0'))
kind = 'meeting_followup'

    @pytest.mark.parametrize
[PMO_EVIDENCE_OUTPUT_TRUNCATED]
```

### Captured run — 2026-09-30T02:44:32Z

- **Command:** `bash -c PHILO_TEST_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_TEST_HOME"' EXIT; env HOME="$PHILO_TEST_HOME" PYTHONPATH=/Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158 uv run python -c 'import sys; from pathlib import Path; base=Path(".tmp/philo11/base-332d9158").resolve(); sys.path.insert(0,str(base)); import holdspeak; sys.path.insert(0,str(base/"scripts")); import graph_walk; print("BASE PRODUCT:", holdspeak.__file__); print("BASE RIG:", graph_walk.__file__); import pytest; raise SystemExit(pytest.main(["-q", "--tb=short", "--basetemp="+sys.argv[1], "tests/integration/test_philo11_document_rig.py"]))' "$PHILO_TEST_HOME/pytest"`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
BASE PRODUCT: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/holdspeak/__init__.py
BASE RIG: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/scripts/graph_walk.py
FFFFFFFF                                                                 [100%]
=================================== FAILURES ===================================
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[project_update] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_10ba29130143f6a3f92ca77f', 'document_ref': 'project_update:philo11-update'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[monday_brief] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_2135e99265ab3e33cfc31fe6', 'document_ref': 'monday_brief:brief-0eca169594544809889409b96c91de15'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[desk_decision] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_6872b04cd000de8ee8d174a4', 'document_ref': 'desk_decision:desk-philo11'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_decision] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_603b188879a6e6c5c8ac083e', 'document_ref': 'meeting_decision:dec-bc5c1e12975d2f314a38'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[decision_record] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_49cf9e3c871c298464486fd4', 'document_ref': 'decision_record:record-4874d872402b4ac594a76364ad170c72'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_summary] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_0e17dfca532f0fbeca836c52', 'document_ref': 'meeting_summary:philo11-meeting'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_digest] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_5eae3a7b15a9bd1a1cafc50f', 'document_ref': 'meeting_digest:philo11-meeting'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
_ test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_followup] _
tests/integration/test_philo11_document_rig.py:71: in test_each_document_previews_prepares_and_lists_through_the_real_rig
    preview = op("channel.preview", args)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/integration/test_philo11_document_rig.py:60: in op
    assert record["refusal"] is None, (name, record)
E   AssertionError: ('channel.preview', {'adapter': 'mcp-tool', 'args': {'destination_id': 'chd_3fdec2db8aa797b18692a3ff', 'document_ref': 'meeting_followup:philo11-meeting'}, 'domain_response': None, 'elapsed_s': 0.001, ...})
E   assert {'code': 'validation', 'error': "Invalid arguments for channel.preview: 'update_id' is a required property", 'refusal': 'invalid_arguments'} is None
=========================== short test summary info ============================
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[project_update]
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[monday_brief]
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[desk_decision]
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_decision]
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[decision_record]
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_summary]
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_digest]
FAILED tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_followup]
8 failed in 2.48s
```

### Captured run — 2026-09-30T02:52:45Z

- **Command:** `bash -c set -e
PHILO_DOC_HOME=$(mktemp -d)
trap 'rm -rf "$PHILO_DOC_HOME"' EXIT
env HOME="$PHILO_DOC_HOME" uv run python scripts/philo_openapi_reference.py
env HOME="$PHILO_DOC_HOME" uv run python scripts/philo_graph_reference.py
env HOME="$PHILO_DOC_HOME" uv run python scripts/philo_graph_reference.py --check
env HOME="$PHILO_DOC_HOME" uv run python scripts/philo_graph_reference.py --census
env HOME="$PHILO_DOC_HOME" uv run python scripts/generate_capability_docs.py --check`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
OpenAPI: 580 paths
case-revision: live-astra ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: live-astra ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: live-astra ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: live-astra ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: live-astra ran an older revision of case.j10.brief_item_shelf.refused
case-revision: live-astra ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: live-astra ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: live-astra ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: live-astra ran an older revision of case.j4.meetings_import.imported
case-revision: live-astra ran an older revision of case.j4.record_only.no_speech_head
case-revision: live-astra ran an older revision of case.j4.record_start.capture_recording
case-revision: live-astra ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: live-astra ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: live-astra ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: live-astra ran an older revision of case.j6.run_summary.host_named
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_failed
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_queued
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_ready
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_retry
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_running
case-revision: live-astra ran an older revision of case.j6.run_summary.summary_text
case-revision: live-astra ran an older revision of case.j9.route_presentation_restore.restored
case-revision: live-astra ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: live-astra ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: live-muaddib ran an older revision of case.j10.arrival_generate_again.next_day
case-revision: live-muaddib ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: live-muaddib ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: live-muaddib ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: live-muaddib ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: live-muaddib ran an older revision of case.j10.brief_item_shelf.refused
case-revision: live-muaddib ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: live-muaddib ran an older revision of case.j3.speech_missing.row_stays
case-revision: live-muaddib ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: live-muaddib ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: live-muaddib ran an older revision of case.j4.meetings_import.imported
case-revision: live-muaddib ran an older revision of case.j4.record_only.no_speech_head
case-revision: live-muaddib ran an older revision of case.j4.record_start.capture_recording
case-revision: live-muaddib ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: live-muaddib ran an older revision of case.j5.meeting_open.planned_host_disclosed
case-revision: live-muaddib ran an older revision of case.j5.meeting_open.route_disclosed
case-revision: live-muaddib ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: live-muaddib ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: live-muaddib ran an older revision of case.j6.run_summary.host_named
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_failed
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_queued
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_ready
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_retry
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_running
case-revision: live-muaddib ran an older revision of case.j6.run_summary.summary_text
case-revision: live-muaddib ran an older revision of case.j7.arrival_load.reload_persisted
case-revision: live-muaddib ran an older revision of case.j7.hub_restart.intel_retained
case-revision: live-muaddib ran an older revision of case.j9.route_presentation_restore.restored
case-revision: live-muaddib ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: live-muaddib ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: live-muaddib ran an older revision of case.j9.shade_open.door_stale
case-revision: static-astra ran an older revision of case.beyond.first_words_reload.retained_draft
case-revision: static-astra ran an older revision of case.j1.first_words_continue_later.draft_custody
case-revision: static-astra ran an older revision of case.j1.first_words_continue_later.idle
case-revision: static-astra ran an older revision of case.j1.first_words_keep_as_note.kept
case-revision: static-astra ran an older revision of case.j1.first_words_speak.kept
case-revision: static-astra ran an older revision of case.j1.first_words_speak.mic_unsupported
case-revision: static-astra ran an older revision of case.j1.first_words_speak.permission_denied
case-revision: static-astra ran an older revision of case.j1.first_words_speak.unreachable_hub
case-revision: static-astra ran an older revision of case.j1.speech_readiness.ready
case-revision: static-astra ran an older revision of case.j10.arrival_generate_again.next_day
case-revision: static-astra ran an older revision of case.j10.arrival_generate_again.same_day_idempotent
case-revision: static-astra ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: static-astra ran an older revision of case.j10.arrival_generate_brief.populated
case-revision: static-astra ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: static-astra ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: static-astra ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: static-astra ran an older revision of case.j10.brief_item_shelf.refused
case-revision: static-astra ran an older revision of case.j10.brief_latest.absent
case-revision: static-astra ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: static-astra ran an older revision of case.j11.thought_keep.kept
case-revision: static-astra ran an older revision of case.j2.arrival_load.engines_both_missing
case-revision: static-astra ran an older revision of case.j2.arrival_load.read_pending
case-revision: static-astra ran an older revision of case.j2.arrival_load.read_unknown
case-revision: static-astra ran an older revision of case.j2.arrival_load.summary_missing_only
case-revision: static-astra ran an older revision of case.j3.concierge_use_for_summaries.assigned_ready
case-revision: static-astra ran an older revision of case.j3.speech_missing.row_stays
case-revision: static-astra ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: static-astra ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: static-astra ran an older revision of case.j4.meetings_import.imported
case-revision: static-astra ran an older revision of case.j4.record_only.no_speech_head
case-revision: static-astra ran an older revision of case.j4.record_start.capture_recording
case-revision: static-astra ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: static-astra ran an older revision of case.j5.meeting_open.route_disclosed
case-revision: static-astra ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: static-astra ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: static-astra ran an older revision of case.j6.run_summary.host_named
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_failed
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_queued
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_ready
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_retry
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_running
case-revision: static-astra ran an older revision of case.j6.run_summary.summary_text
case-revision: static-astra ran an older revision of case.j7.arrival_load.reload_persisted
case-revision: static-astra ran an older revision of case.j7.hub_restart.intel_retained
case-revision: static-astra ran an older revision of case.j9.route_presentation_restore.restored
case-revision: static-astra ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: static-astra ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: static-astra ran an older revision of case.j9.shade_open.door_present
case-revision: static-astra ran an older revision of case.j9.shade_open.door_stale
case-revision: static-astra ran an older revision of case.j9.shade_receipt_open.rhythm_face
case-revision: static-muaddib ran an older revision of case.beyond.first_words_reload.retained_draft
case-revision: static-muaddib ran an older revision of case.j1.first_words_continue_later.draft_custody
case-revision: static-muaddib ran an older revision of case.j1.first_words_continue_later.idle
case-revision: static-muaddib ran an older revision of case.j1.first_words_keep_as_note.kept
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.kept
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.mic_unsupported
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.permission_denied
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.unreachable_hub
case-revision: static-muaddib ran an older revision of case.j1.speech_readiness.ready
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_again.next_day
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_again.same_day_idempotent
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_brief.populated
case-revision: static-muaddib ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: static-muaddib ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: static-muaddib ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: static-muaddib ran an older revision of case.j10.brief_item_shelf.refused
case-revision: static-muaddib ran an older revision of case.j10.brief_latest.absent
case-revision: static-muaddib ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: static-muaddib ran an older revision of case.j11.thought_keep.kept
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.engines_both_missing
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.read_pending
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.read_unknown
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.summary_missing_only
case-revision: static-muaddib ran an older revision of case.j3.concierge_use_for_summaries.assigned_ready
case-revision: static-muaddib ran an older revision of case.j3.speech_missing.row_stays
case-revision: static-muaddib ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: static-muaddib ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: static-muaddib ran an older revision of case.j4.meetings_import.imported
case-revision: static-muaddib ran an older revision of case.j4.record_only.no_speech_head
case-revision: static-muaddib ran an older revision of case.j4.record_start.capture_recording
case-revision: static-muaddib ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: static-muaddib ran an older revision of case.j5.meeting_open.route_disclosed
case-revision: static-muaddib ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: static-muaddib ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: static-muaddib ran an older revision of case.j6.run_summary.host_named
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_failed
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_queued
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_ready
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_retry
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_running
case-revision: static-muaddib ran an older revision of case.j6.run_summary.summary_text
case-revision: static-muaddib ran an older revision of case.j7.arrival_load.reload_persisted
case-revision: static-muaddib ran an older revision of case.j7.hub_restart.intel_retained
case-revision: static-muaddib ran an older revision of case.j9.route_presentation_restore.restored
case-revision: static-muaddib ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: static-muaddib ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: static-muaddib ran an older revision of case.j9.shade_open.door_present
case-revision: static-muaddib ran an older revision of case.j9.shade_open.door_stale
case-revision: static-muaddib ran an older revision of case.j9.shade_receipt_open.rhythm_face
exposure-disagreement: edge.timer.workbench_conductor: astra=conditional; muaddib=active
exposure-disagreement: edge.verb.desk_arrange: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_brief: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_find_receipt: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_overdue: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_review_decisions: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_agent: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_decision: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_knowledge: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_note: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_project: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_thread: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_workbench: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_workflow: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_zone: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_open_intelligence: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_open_people: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_overview: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_refresh: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_reset_layout: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_reset_to_seed: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_settle: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_toggle_view: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_ask: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_ask_project: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_continue_in_thread: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_delete: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_duplicate: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_edit: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_file: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_info: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_open: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_rename: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.system_search: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.system_sheet: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.thread_compact: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_fork: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_guardrail: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_keep: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_mode: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_new: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_prompt: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_stop: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_todo: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_tools: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.window_close: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_cycle: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_cycle_reverse: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_maximize: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_minimize: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_snap_left: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_snap_right: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.zone_focus: astra=active; muaddib=conditional
subtype-conflict: edge.cli.hub_restart: astra=process.restart; muaddib=cli
subtype-conflict: edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
subtype-conflict: edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
subtype-conflict: edge.route.brief_item_shelf: astra=ui; muaddib=http
subtype-conflict: edge.route.brief_latest: astra=ui; muaddib=http
subtype-conflict: edge.route.heartbeat_run_now: astra=ui; muaddib=http
subtype-conflict: edge.route.inference_assignments_set: astra=ui; muaddib=http
subtype-conflict: edge.route.model_profile_delete: astra=ui; muaddib=http
subtype-conflict: edge.route.model_profile_unbind: astra=ui; muaddib=http
subtype-conflict: edge.route.projection_presentation: astra=ui; muaddib=http
subtype-conflict: edge.route.projections_list: astra=ui; muaddib=http
subtype-conflict: edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
subtype-conflict: iface.face.arrival: astra=face.section; muaddib=face.window
subtype-conflict: iface.face.first_words: astra=face.card; muaddib=face.panel
subtype-normalized: edge.face.arrival_brief_generate: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.arrival_brief_generate_again: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_add_check: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_add_engine: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_apply: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_check: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_download: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_use_for_summaries: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_acknowledge: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_dismiss: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_open: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_receipt_open: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.route.inference_assignments: astra=http.GET; muaddib=http -> http.GET (refinement)
subtype-normalized: edge.route.intel_retry: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_capture_recover: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_intelligence_run: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_start: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_stop: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meetings_import: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.verb.desk_arrange: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_brief: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_find_receipt: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_overdue: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_review_decisions: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_agent: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_decision: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_new_knowledge: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_note: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_new_project: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_thread: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_workbench: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_workflow: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_zone: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_open_intelligence: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_open_people: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_overview: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_refresh: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_reset_layout: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_reset_to_seed: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_settle: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_toggle_view: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_ask: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_ask_project: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_continue_in_thread: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_delete: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.object_duplicate: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_edit: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_file: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_info: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_open: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_rename: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.system_search: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.system_sheet: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.thread_compact: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_fork: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_guardrail: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_keep: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_mode: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_new: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_prompt: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_stop: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_todo: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_tools: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.window_close: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_cycle: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_cycle_reverse: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_maximize: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.window_minimize: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_snap_left: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.window_snap_right: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.zone_focus: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: iface.face.concierge: astra=ui; muaddib=face.window -> face.window (bucket)
subtype-normalized: state.briefs.absent: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.generated_empty: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.generating: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.generation_failure: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.item.acknowledged: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.item.deferred: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.item.untouched: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.next_day_window: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.people.unavailable: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.populated: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.reload_persisted: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.same_day_idempotent: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.desk_presentation.reload_reconnect: astra=atlas.desk_presentation; muaddib=browser.presentation -> browser.presentation (vocabulary)
subtype-normalized: state.desk_presentation.window_open_thought: astra=atlas.desk_presentation; muaddib=browser.presentation -> browser.presentation (vocabulary)
subtype-normalized: state.engines.add_engine_ready: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.add_engine_refused: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.assigned_ready: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.assignment_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.binding_absent: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.both_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.profile_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.read_pending: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.read_unknown: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.speech_assignment_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.speech_ready: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.unreachable: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.first_value.continue_later: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.draft_custody: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.failure.permission_denied: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.failure.unreachable_hub: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.kept: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.listening: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.mic_unsupported: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.retained_draft: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.success: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.meetings.capture.finalized: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.imported: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.recording: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.recoverable: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.recovered: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.available: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.failed: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.queued: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.ready: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.retained_after_restart: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.retry_after_failure: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.running: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.transcription.absent: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.transcription.record_only: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.projections.attention.acknowledged: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.attention.dismissed: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.attention.restored: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.door.absent: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.door.present: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.door.stale: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.receipt.resolved: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.time.next_due_sweep: astra=atlas.time; muaddib=clock -> clock (vocabulary)
subtype-normalized: state.time.sweep_held_remote: astra=atlas.time; muaddib=clock -> clock (vocabulary)
graph join generated: docs/generated/graph.json — 6472 nodes, 808 links, 85 cases, 216 observations, 112 claim reviews, 47 findings, 47 resolutions; 352 note(s)
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
census scope: HTTP routes (the app assembled from source by scripts/gen_api_surface.py, schema-hidden page routes excluded; stale = docs/generated/openapi.json differs from source), desk verbs (web/src/desk/verbRegistry.ts + applications.ts), MCP tools (the real holdspeak.mcp.tools catalogue). Face handlers, keys, timers, frames, CLI and connector edges are not censused. miscited = a pass cited a handler that was not in the file at the revision it examined.
new: http DELETE /api/channels/destinations/{destination_id} has no edge (api_channel_remove_destination)
new: http DELETE /api/settings/remote/delegations/{identity} has no edge (revoke_delegation)
new: http DELETE /api/settings/remote/delegations/{identity}/projects/{project_id} has no edge (revoke_project_delegation)
new: http GET /api/channels/destinations has no edge (api_channel_destinations)
new: http GET /api/channels/sends has no edge (api_channel_sends)
new: http POST /api/channels/destinations has no edge (api_channel_save_destination)
new: http POST /api/channels/destinations/{destination_id}/check has no edge (api_channel_check_destination)
new: http POST /api/channels/preview has no edge (api_channel_preview)
new: http POST /api/channels/send has no edge (api_channel_send)
new: http POST /api/channels/sends has no edge (api_channel_prepare)
new: http POST /api/channels/sends/{send_id}/discard has no edge (api_channel_discard)
new: http POST /api/updates/{update_id}/delivered has no edge (api_mark_update_delivered)
new: http PUT /api/channels/email-keys/{key_ref} has no edge (api_channel_save_email_key)
new: http PUT /api/settings/remote/delegations/{identity} has no edge (grant_delegation)
new: http PUT /api/settings/remote/delegations/{identity}/projects/{project_id} has no edge (grant_project_delegation)
miscited: http GET /api/brief/latest (edge.route.brief_latest): def api_latest was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/brief/items/{item_id}/shelf (edge.route.brief_item_shelf): def api_shelf was not in holdspeak/web/routes/monday_brief.py at c42963bc either
miscited: http POST /api/inference/assignments/set (edge.route.inference_assignments_set): def api_set_assignments was not in holdspeak/web/routes/inference_assignments.py at c42963bc either
miscited: http POST /api/settings/heartbeat/run-now (edge.route.heartbeat_run_now): source registered api_heartbeat_run_now at c42963bc already; the pass cited api_run_heartbeat
miscited: http POST /api/stop (edge.route.meeting_stop): source registered api_stop at c42963bc already; the pass cited api_meeting_stop
new: mcp tool channel.check_destination has no edge
new: mcp tool channel.destinations has no edge
new: mcp tool channel.discard has no edge
new: mcp tool channel.prepare has no edge
new: mcp tool channel.preview has no edge
new: mcp tool channel.remove_destination has no edge
new: mcp tool channel.save_destination has no edge
new: mcp tool channel.send has no edge
new: mcp tool channel.sends has no edge
new: mcp tool kernel.receipt has no edge
new: mcp tool meeting.import has no edge
new: mcp tool monday_brief.shelf has no edge
new: mcp tool monday_brief.shelf_read has no edge
new: mcp tool project.item.create has no edge
new: mcp tool project.item.list has no edge
new: mcp tool project.item.transition has no edge
new: mcp tool project.item.update has no edge
new: mcp tool project.mark_update_delivered has no edge
new: mcp tool project.resource.add has no edge
new: mcp tool project.resource.list has no edge
new: mcp tool project.resource.remove has no edge
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
census: 36 new, 0 removed, 0 changed, 0 stale, 5 miscited, 0 unread, 14 subtype conflict note(s) against docs/generated/graph.json (source_commit f575a582)
```

### Captured run — 2026-09-30T02:55:51Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent --brain astra --viewport 1440 --engine none --out .tmp/graph-walk/philo11-01/sent-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
[glass_infra] web bundle rebuilt in 5.0s
PASS: live
BRAIN: astra
SOURCE: 332d91586bdbd7fe40e3c2c00851a46adc4650e4 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:59815 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ne9krw7q/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-01/sent-1440/20260930T025551Z-case.p10.send.sent-astra-1440/before.png', '.tmp/graph-walk/philo11-01/sent-1440/20260930T025551Z-case.p10.send.sent-astra-1440/after.png']
NOTE: predicate: all_of: protocol_status: POST /api/channels/send answered 200, wanted 200 (body sha256 445b20414e12); response body contains the declared admission facts | readable_text: 'SAVED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 75, 'y': 389, 'w': 714, 'h': 50} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_d977015662b9488c85c55b50371224d5 answered 200 with 1 row(s) {'state': 'sent', 'destination_id': 'chd_eb4f24d88cd36301feb0a367', 'channel': 'file'}; GET /api/projects/proj-72b61eabe81a/updates answered 200 with 1 row(s) {'id': 'pupd_d977015662b9488c85c55b50371224d5', 'deliveries.0.channel': 'file', 'deliveries.0.outcome': 'sent'}
```

### Captured run — 2026-09-30T02:57:19Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent --brain astra --viewport 393 --engine none --out .tmp/graph-walk/philo11-01/sent-393`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
PASS: live
BRAIN: astra
SOURCE: 332d91586bdbd7fe40e3c2c00851a46adc4650e4 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:60427 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-qlf6xt3a/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-01/sent-393/20260930T025719Z-case.p10.send.sent-astra-393/before.png', '.tmp/graph-walk/philo11-01/sent-393/20260930T025719Z-case.p10.send.sent-astra-393/after.png']
NOTE: predicate: all_of: protocol_status: POST /api/channels/send answered 200, wanted 200 (body sha256 3335c18987c2); response body contains the declared admission facts | readable_text: 'SAVED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 51, 'y': 394, 'w': 307, 'h': 74} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_9a3ec81606e549da934b590f1df966c2 answered 200 with 1 row(s) {'state': 'sent', 'destination_id': 'chd_ce8abeefeaabca08f8705844', 'channel': 'file'}; GET /api/projects/proj-b045ece1aa65/updates answered 200 with 1 row(s) {'id': 'pupd_9a3ec81606e549da934b590f1df966c2', 'deliveries.0.channel': 'file', 'deliveries.0.outcome': 'sent'}
```

### Captured run — 2026-09-30T02:58:13Z

- **Command:** `bash -c PHILO_RED_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_RED_HOME"' EXIT; env HOME="$PHILO_RED_HOME" PYTHONPATH=. uv run python .tmp/philo11/check_truncation_baseline.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
BASE RENDERER: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/holdspeak/slack_export.py
PRODUCER: Database.meetings.save_meeting + plugins.record_artifact + compute_meeting_aftercare
digest: length=3800; final_stored_decision_retained=False
followup: length=3800; final_stored_decision_retained=False
Traceback (most recent call last):
  File "/Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/check_truncation_baseline.py", line 33, in <module>
    raise AssertionError("Old renderer cuts real stored documents: " + ", ".join(failures))
AssertionError: Old renderer cuts real stored documents: digest, followup
```

### Captured run — 2026-09-30T02:58:47Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared --brain astra --viewport 1440 --engine none --out .tmp/graph-walk/philo11-01/prepared-1440`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
PASS: live
BRAIN: astra
SOURCE: 332d91586bdbd7fe40e3c2c00851a46adc4650e4 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:60939 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ooi5801s/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-01/prepared-1440/20260930T025847Z-case.p10.send.prepared-astra-1440/before.png', '.tmp/graph-walk/philo11-01/prepared-1440/20260930T025847Z-case.p10.send.prepared-astra-1440/after.png']
NOTE: predicate: all_of: readable_text: 'PREPARED' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 238, 'w': 770, 'h': 26} | readable_text: 'BY YOU' is readable in viewport {'width': 1440, 'height': 900} with rect {'x': 39, 'y': 238, 'w': 770, 'h': 26} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_d0f81e88b73c4e79a903b592f7d3ca89 answered 200 with 1 row(s) {'id': 'chs_19ade498723d3e8bc776b314', 'state': 'prepared', 'prepared_by.kind': 'owner'}
```

### Captured run — 2026-09-30T02:59:53Z

- **Command:** `bash -c PHILO_TEST_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_TEST_HOME"' EXIT; env HOME="$PHILO_TEST_HOME" uv run pytest -q --tb=short --basetemp="$PHILO_TEST_HOME/pytest" tests/unit/test_philo10_cli_channels.py -k steward`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
__ test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused __
tests/unit/test_philo10_cli_channels.py:607: in test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused
    [prepare_op] = _ops(hub, "channel.prepare")
    ^^^^^^^^^^^^
E   ValueError: too many values to unpack (expected 1)
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 1/4 failed: Unknown document kind in 'pupd_7b3494dd65c7436aa8b75a2da567ab23'
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 2/4 failed: Unknown document kind in 'pupd_7b3494dd65c7436aa8b75a2da567ab23'
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 3/4 failed: Unknown document kind in 'pupd_7b3494dd65c7436aa8b75a2da567ab23'
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 4/4 failed: Unknown document kind in 'pupd_7b3494dd65c7436aa8b75a2da567ab23'
__________ test_the_scheduled_steward_prepares_under_its_own_identity __________
tests/unit/test_philo10_cli_channels.py:639: in test_the_scheduled_steward_prepares_under_its_own_identity
    [prepare_op] = _ops(hub, "channel.prepare")
    ^^^^^^^^^^^^
E   ValueError: too many values to unpack (expected 1)
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 1/4 failed: Unknown document kind in 'pupd_211b4f440f8542c7a46d82d577e40d0a'
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 2/4 failed: Unknown document kind in 'pupd_211b4f440f8542c7a46d82d577e40d0a'
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 3/4 failed: Unknown document kind in 'pupd_211b4f440f8542c7a46d82d577e40d0a'
WARNING  holdspeak.project_steward:project_steward_service.py:1270 Effect prepare_send attempt 4/4 failed: Unknown document kind in 'pupd_211b4f440f8542c7a46d82d577e40d0a'
=========================== short test summary info ============================
FAILED tests/unit/test_philo10_cli_channels.py::test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused
FAILED tests/unit/test_philo10_cli_channels.py::test_the_scheduled_steward_prepares_under_its_own_identity
2 failed, 44 deselected in 2.04s
```

### Captured run — 2026-09-30T03:00:37Z

- **Command:** `bash -c set -e
PHILO_TEST_HOME=$(mktemp -d)
trap 'rm -rf "$PHILO_TEST_HOME"' EXIT
env HOME="$PHILO_TEST_HOME" uv run pytest -q --collect-only --basetemp="$PHILO_TEST_HOME/pytest" tests/unit/test_philo11_document_sources.py tests/unit/test_philo11_channel_contract.py tests/integration/test_philo11_document_rig.py tests/unit/test_philo10_cli_channels.py
env HOME="$PHILO_TEST_HOME" uv run pytest -q --tb=short --basetemp="$PHILO_TEST_HOME/pytest" tests/unit/test_philo11_document_sources.py tests/unit/test_philo11_channel_contract.py tests/integration/test_philo11_document_rig.py tests/unit/test_philo10_cli_channels.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
tests/unit/test_philo11_document_sources.py::test_registry_declares_the_eight_kinds
tests/unit/test_philo11_document_sources.py::test_real_producers_render_all_eight_sources
tests/unit/test_philo11_document_sources.py::test_meeting_sources_never_copy_transcript
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[project_update]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[monday_brief]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[desk_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[decision_record]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_summary]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[unknown_kind:source-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[meeting_summary:missing-document_not_found]
tests/unit/test_philo11_document_sources.py::test_missing_meeting_summary_is_named_no_summary
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_project_update_refuses_unpublished_by_generic_name
tests/unit/test_philo11_document_sources.py::test_aftercare_document_markdown_is_not_truncated
tests/unit/test_philo11_channel_contract.py::test_generic_document_ref_is_one_wire_for_http_mcp_and_history_filter
tests/unit/test_philo11_channel_contract.py::test_prepared_send_uses_frozen_bytes_and_name_after_source_is_deleted[project_update]
tests/unit/test_philo11_channel_contract.py::test_prepared_send_uses_frozen_bytes_and_name_after_source_is_deleted[desk_decision]
tests/unit/test_philo11_channel_contract.py::test_legacy_prepared_non_file_row_does_not_reread_deleted_source
tests/unit/test_philo11_channel_contract.py::test_inline_send_refuses_changed_preview_then_sends_new_preview[project_update]
tests/unit/test_philo11_channel_contract.py::test_inline_send_refuses_changed_preview_then_sends_new_preview[desk_decision]
tests/unit/test_philo11_channel_contract.py::test_kernel_target_names_document_ref_and_external_agent_send_is_refused_over_mcp[project_update]
tests/unit/test_philo11_channel_contract.py::test_kernel_target_names_document_ref_and_external_agent_send_is_refused_over_mcp[desk_decision]
tests/unit/test_philo11_channel_contract.py::test_agent_brief_preview_and_prepare_keep_owner_overlay_and_payload
tests/unit/test_philo11_channel_contract.py::test_thread_palette_discovers_destination_then_prepares_without_send_admission
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[project_update]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[monday_brief]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[desk_decision]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_decision]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[decision_record]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_summary]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_digest]
tests/integration/test_philo11_document_rig.py::test_each_document_previews_prepares_and_lists_through_the_real_rig[meeting_followup]
tests/unit/test_philo10_cli_channels.py::test_gate1_the_redactors_worst_case_is_bounded
tests/unit/test_philo10_cli_channels.py::test_gate1_a_document_with_the_clis_error_phrase_keeps_the_named_code
tests/unit/test_philo10_cli_channels.py::test_gate2_the_hub_answers_a_read_during_a_slow_send[http]
tests/unit/test_philo10_cli_channels.py::test_gate2_the_hub_answers_a_read_during_a_slow_send[mcp]
tests/unit/test_philo10_cli_channels.py::test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner[github]
tests/unit/test_philo10_cli_channels.py::test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner[jira]
tests/unit/test_philo10_cli_channels.py::test_each_send_is_one_channel_send_with_its_cli_children_parented_under_the_owner[confluence]
tests/unit/test_philo10_cli_channels.py::test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes[github]
tests/unit/test_philo10_cli_channels.py::test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes[jira]
tests/unit/test_philo10_cli_channels.py::test_the_argv_has_the_manifest_prefix_and_no_body_and_the_file_is_the_previewed_bytes[confluence]
tests/unit/test_philo10_cli_channels.py::test_a_plan_with_a_forbidden_flag_or_a_second_key_cannot_be_built
tests/unit/test_philo10_cli_channels.py::test_an_atlassian_send_runs_inside_the_acli_lock_and_a_second_waits
tests/unit/test_philo10_cli_channels.py::test_a_status_that_names_another_account_never_creates
tests/unit/test_philo10_cli_channels.py::test_a_github_destination_saved_as_a_is_refused_when_gh_is_b
tests/unit/test_philo10_cli_channels.py::test_an_oversize_body_is_refused_by_name_before_any_dispatch[github-65536]
tests/unit/test_philo10_cli_channels.py::test_an_oversize_body_is_refused_by_name_before_any_dispatch[jira-32767]
tests/unit/test_philo10_cli_channels.py::test_the_confluence_title_is_in_the_frozen_digest_and_never_in_argv_or_a_receipt
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[unpinned_exit-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[unpinned_exit-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[unpinned_exit-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_no_proof-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_no_proof-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_no_proof-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_malformed-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_malformed-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[exit0_malformed-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[timeout-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[timeout-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[timeout-confluence]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[pinned-github]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[pinned-jira]
tests/unit/test_philo10_cli_channels.py::test_only_a_pinned_error_is_failed_everything_else_unknown[pinned-confluence]
tests/unit/test_philo10_cli_channels.py::test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create[github]
tests/unit/test_philo10_cli_channels.py::test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create[jira]
tests/unit/test_philo10_cli_channels.py::test_a_failed_settle_after_a_cli_create_is_taken_over_as_unknown_without_a_second_create[confluence]
tests/unit/test_philo10_cli_channels.py::test_f5_the_nudges_gh_child_is_parented_under_the_owner
tests/unit/test_philo10_cli_channels.py::test_f4_a_nudge_whose_gh_times_out_is_unknown_and_never_offered_again
tests/unit/test_philo10_cli_channels.py::test_a_nudge_whose_settle_fails_after_the_comment_never_posts_twice_and_the_reaper_says_unknown
tests/unit/test_philo10_cli_channels.py::test_the_steward_prepares_a_send_as_its_runs_child_and_its_send_is_refused
tests/unit/test_philo10_cli_channels.py::test_the_scheduled_steward_prepares_under_its_own_identity
tests/unit/test_philo10_cli_channels.py::test_a_real_kill_during_a_gh_create_ends_unknown_once_and_the_replay_never_runs_gh_again
tests/unit/test_philo10_cli_channels.py::test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub[mcp-save-destination]
tests/unit/test_philo10_cli_channels.py::test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub[http-save-destination]
tests/unit/test_philo10_cli_channels.py::test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub[mcp-recheck]
tests/unit/test_philo10_cli_channels.py::test_gate2_a_slow_cli_read_in_setup_or_recheck_never_blocks_the_hub[http-recheck]
tests/unit/test_philo10_cli_channels.py::test_the_sends_are_egress_owner_presses_and_blocking_io_in_the_one_table

83 tests collected in 0.57s
........................................................................ [ 86%]
...........                                                              [100%]
83 passed in 61.69s (0:01:01)
```

### Captured run — 2026-09-30T03:02:16Z

- **Command:** `bash -c set -o pipefail
PHILO_FULL_HOME=$(mktemp -d)
trap 'rm -rf "$PHILO_FULL_HOME"' EXIT
env -u HOLDSPEAK_EVIDENCE_WRITE HOME="$PHILO_FULL_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py --basetemp="$PHILO_FULL_HOME/pytest" 2>&1 | tee .tmp/philo11/full-suite.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
........................................................................ [  1%]
........................................................................ [  2%]
........................................................................ [  2%]
.......................................................F................ [  3%]
........................................................................ [  3%]
........................................................................ [  4%]
........................................................................ [  4%]
........................................................................ [  5%]
..ssss.sss.sssssssssssssss.............................................. [  5%]
........................................................................ [  6%]
........................................................................ [  6%]
....................................F................................... [  7%]
........................................................................ [  7%]
........................................................................ [  8%]
........................................................................ [  8%]
........................................................................ [  9%]
........................................................................ [ 10%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 11%]
........................................................................ [ 12%]
...........................................................ss........... [ 12%]
........................................................................ [ 13%]
....................................................................ss.. [ 13%]
........................................................................ [ 14%]
................s....................................................... [ 14%]
........................................................................ [ 15%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 16%]
.....F.................................................................. [ 17%]
........................................................................ [ 17%]
........................................................................ [ 18%]
........................................................................ [ 19%]
........................................................................ [ 19%]
........................................................................ [ 20%]
........................................................................ [ 20%]
........................................................................ [ 21%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 22%]
........................................................................ [ 23%]
.........................s.............................................. [ 23%]
.ss..................................................................... [ 24%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 27%]
..................F..................................................... [ 28%]
...................................................................s.... [ 29%]
........................................................................ [ 29%]
........................................................................ [ 30%]
.....................F.................................................. [ 30%]
........................................................................ [ 31%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 32%]
........................................................................ [ 33%]
........................................................................ [ 33%]
........................................................................ [ 34%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 35%]
........................................................................ [ 36%]
........................................................................ [ 36%]
.............s.......................................................... [ 37%]
........................................................................ [ 38%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 43%]
s..s.................................................................... [ 44%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 45%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 47%]
........................................................................ [ 48%]
........................................................................ [ 48%]
........................................................................ [ 49%]
........................................................................ [ 49%]
........................................................................ [ 50%]
........................................................................ [ 50%]
........................................................................ [ 51%]
...................................F..................................s. [ 51%]
........................................................................ [ 52%]
........................................................................ [ 52%]
........................................................................ [ 53%]
............F........................................................... [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 55%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 57%]
........................................................................ [ 58%]
......F................................................................. [ 58%]
........................................................................ [ 59%]
........................................................................ [ 59%]
........................................................................ [ 60%]
...............................................................F........ [ 60%]
......F.......................F......................................... [ 61%]
..................................F..........F..............ssssss...... [ 61%]
........................................................................ [ 62%]
........................................................................ [ 62%]
........................................................................ [ 63%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 64%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 66%]
........................................................................ [ 67%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 69%]
........................................................................ [ 70%]
........................................x............................... [ 70%]
........................................................................ [ 71%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 72%]
........................................................................ [ 73%]
F....................................................................... [ 73%]
.........s.............................................................. [ 74%]
........................................................................ [ 75%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 76%]
........................................................................ [ 77%]
........................................................................ [ 77%]
.............................s.......................................... [ 78%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 80%]
....x................................................................... [ 81%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 82%]
........s............................................................... [ 83%]
........................................................................ [ 83%]
........................................................................ [ 84%]
s....................................................................... [ 85%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 86%]
...........................................................F............ [ 87%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 88%]
........................................................................ [ 89%]
...x.................................................................... [ 89%]
........................................................................ [ 90%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 91%]
........................................................................ [ 92%]
........................................................................ [ 92%]
..........................................F....................s........ [ 93%]
........................................................................ [ 94%]
........................................................................ [ 94%]
....................................x................................... [ 95%]
........................................................................ [ 95%]
.......................ssssssssssss.............sssssssss............... [ 96%]
......................ssss......ssssss..........ssssssssss.s............ [ 96%]
........................................................................ [ 97%]
........................................................................ [ 97%]
........................................................................ [ 98%]
............................s.....................sss................... [ 98%]
........................................................................ [ 99%]
........................................................................ [ 99%]
........................                                                 [100%]
=================================== FAILURES ===================================
________ TestDatabaseShape.test_fresh_schema_matches_canonical_snapshot ________
[gw11] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.unit.test_db.TestDatabaseShape object at 0x122788190>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw11/test_fresh_schema_matches_cano0')
project_root = PosixPath('/Users/karol/dev/tools/wt-philo-11-01')

    def test_fresh_schema_matches_canonical_snapshot(self, tmp_path, project_root: Path):
        """HS-31-04: the migration ladder was squashed to one canonical schema.
        A fresh build must match the committed snapshot exactly — any intended
        schema change must update tests/fixtures/db_schema_canonical.txt in the
        same commit, keeping the schema honest without a version ladder."""
        import re
        import sqlite3
        from holdspeak.db import Database
    
        Database(tmp_path / "schema_check.db")
        conn = sqlite3.connect(str(tmp_path / "schema_check.db"))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        actual = "\n".join(
            f"{r['type']} {r['name']}: {re.sub(r'\s+', ' ', (r['sql'] or '').strip())}"
            for r in rows
        ) + "\n"
        conn.close()
    
        snapshot = project_root / "tests" / "fixtures" / "db_schema_canonical.txt"
        expected = snapshot.read_text()
>       assert actual == expected, (
            "Fresh DB schema diverged from the canonical snapshot. If this change is "
            f"intended, regenerate {snapshot.relative_to(project_root)}."
        )
E       AssertionError: Fresh DB schema diverged from the canonical snapshot. If this change is intended, regenerate tests/fixtures/db_schema_canonical.txt.
E       assert "index idx_ac...ease'); END\n" == "index idx_ac...ease'); END\n"
E         
E         Skipping 40313 identical leading characters in diff, use -v to show
E         - NOT NULL, prepared_by_kind TEXT NOT NULL DEFAULT '', prepared_by_identity TEXT NOT NULL DEFAULT '', prepare_operation_id TEXT UNIQUE, send_operation_id TEXT UNIQUE, state TEXT NOT NULL, proof_json TEXT, reason TEXT, file_path TEXT, created_at TEXT NOT NULL, dispatch_started_at TEXT, settled_at TEXT, dispatch_seq INTEGER )
E         + NOT NULL, -- PHILO-11-01: frozen source naming provenance. NULL is the legacy -- Phase 10 shape and keeps its naming fallback. document_json TEXT, prepared_by_kind TEXT NOT NULL DEFA...
E         
E         ...Full output truncated (292 lines hidden), use '-vv' to show

tests/unit/test_db.py:1755: AssertionError
_ test_the_rig_drives_the_real_atlas[case.j1.first_words_continue_later.idle] __
[gw0] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

case_id = 'case.j1.first_words_continue_later.idle'
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw0/test_the_rig_drives_the_real_a0')

    @pytest.mark.parametrize("case_id", sorted(ATLAS_FENCE))
    def test_the_rig_drives_the_real_atlas(case_id, tmp_path):
        want_verdict, names, why = ATLAS_FENCE[case_id]
        if case_id in PENDING_IN_ATLAS:
            present = {c["id"] for c in json.loads(REAL_ATLAS.read_text())["cases"]}
            if case_id not in present:
                pytest.skip(f"{case_id} is not in the atlas yet (W2 is adding it); "
                            "reserved slot, flip when it lands")
        record = run_case(REAL_ATLAS, case_id, brain="muaddib", viewport=1440,
                          out=tmp_path, engine="none")
    
>       assert record["verdict"] == want_verdict, (
            f"{case_id}: {why}\n" + json.dumps(record["notes"], indent=2))
E       AssertionError: case.j1.first_words_continue_later.idle: Continue later is the trigger, pressed by nothing in setup; the desk (the arrival headline) is the promised result
E         [
E           "BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'chair-first-value'} at '[data-testid=chair-first-value]' \u2014 BLOCKED: observe_at not present ('[data-testid=chair-first-value]'); no element carries 'data-testid'"
E         ]
E       assert 'blocked' == 'pass'
E         
E         - pass
E         + blocked

tests/e2e/test_graph_walk_smoke.py:102: AssertionError
_____________ test_recipe_run_and_chat_run_the_engine_off_the_loop _____________
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

env = (<holdspeak.db.core.Database object at 0x120ed9310>, <starlette.testclient.TestClient object at 0x133fe6270>)
spy = <tests.unit.test_engine_off_the_loop._LoopSpy object at 0x1338cac10>

    def test_recipe_run_and_chat_run_the_engine_off_the_loop(env, spy) -> None:
        _, client = env
        rid = client.post(
            "/api/recipes",
            json={"name": "Loop", "system_prompt": "Answer.", "user_template": "Q: {input}"},
        ).json()["recipe"]["id"]
    
        assert client.post(f"/api/recipes/{rid}/run", json={"input": "hi"}).status_code == 200
        _assert_off_loop(spy)
    
        spy.on_loop = None
        resp = client.post(f"/api/recipes/{rid}/chat", json={"question": "hi"})
        # The thread alias returns 201 and dispatches the engine on a daemon
        # thread (the request never blocks the loop). Wait briefly for the
        # daemon to fire the spy before asserting.
        assert resp.status_code == 201
        for _ in range(100):
            if spy.on_loop is not None:
                break
            time.sleep(0.02)
>       _assert_off_loop(spy)

tests/unit/test_engine_off_the_loop.py:131: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

spy = <tests.unit.test_engine_off_the_loop._LoopSpy object at 0x1338cac10>

    def _assert_off_loop(spy: _LoopSpy) -> None:
>       assert spy.on_loop is False, (
            "the engine ran ON the event loop — a mesh run would deadlock the "
            "worker's claim polls and die at its deadline as 'never claimed'"
        )
E       AssertionError: the engine ran ON the event loop — a mesh run would deadlock the worker's claim polls and die at its deadline as 'never claimed'
E       assert None is False
E        +  where None = <tests.unit.test_engine_off_the_loop._LoopSpy object at 0x1338cac10>.on_loop

tests/unit/test_engine_off_the_loop.py:99: AssertionError
_____________________________ test_speak_loop_1440 _____________________________
[gw1] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw1/test_speak_loop_14400')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x13b637ed0>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_1440(tmp_path, monkeypatch):
        """The full loop at 1440, one session, no restart."""
>       _run(tmp_path, monkeypatch, 1440, 900)

tests/e2e/test_hs176_loop_glass.py:365: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:354: in _run
    _loop(page, width)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

page = <Page url='http://127.0.0.1:64667/'>, width = 1440

    def _loop(page: Any, width: int) -> None:
        _dry_run_on(page)
    
        # ── 1. land, judge, teach ──────────────────────────────────────
        result = _land(page, HEARD)
        result.get_by_role("button", name="Wrong").click()
        teach = page.locator(".speak-teach")
        teach.wait_for(timeout=8000)
        said = teach.get_by_role("textbox", name="What you said")
        assert said.input_value() == HEARD, said.input_value()
        said.fill(SAID)
        page.get_by_role("button", name="Teach correction").click()
        receipt = page.locator(".speak-receipt")
        receipt.wait_for(timeout=8000)
        assert "TAUGHT" in receipt.inner_text(), receipt.inner_text()
    
        # ── 2. speak it again, in the SAME session: the rule fires ─────
        result = _land(page, AGAIN)
        landed = result.locator(".speak-result-text").inner_text()
>       assert landed == APPLIED_TEXT, landed
E       AssertionError: Ship the queue for platform on schedule
E       assert 'Ship the que...m on schedule' == 'Ship the Q4 ...rm in October'
E         
E         - Ship the Q4 platform in October
E         + Ship the queue for platform on schedule

tests/e2e/test_hs176_loop_glass.py:276: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
_____________________________ test_speak_loop_393 ______________________________
[gw1] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw1/test_speak_loop_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x13ef7a0d0>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_393(tmp_path, monkeypatch):
        """The same loop at 393: the Learned row wraps, nothing overflows."""
>       _run(tmp_path, monkeypatch, 393, 852)

tests/e2e/test_hs176_loop_glass.py:372: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:354: in _run
    _loop(page, width)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

page = <Page url='http://127.0.0.1:64725/'>, width = 393

    def _loop(page: Any, width: int) -> None:
        _dry_run_on(page)
    
        # ── 1. land, judge, teach ──────────────────────────────────────
        result = _land(page, HEARD)
        result.get_by_role("button", name="Wrong").click()
        teach = page.locator(".speak-teach")
        teach.wait_for(timeout=8000)
        said = teach.get_by_role("textbox", name="What you said")
        assert said.input_value() == HEARD, said.input_value()
        said.fill(SAID)
        page.get_by_role("button", name="Teach correction").click()
        receipt = page.locator(".speak-receipt")
        receipt.wait_for(timeout=8000)
        assert "TAUGHT" in receipt.inner_text(), receipt.inner_text()
    
        # ── 2. speak it again, in the SAME session: the rule fires ─────
        result = _land(page, AGAIN)
        landed = result.locator(".speak-result-text").inner_text()
>       assert landed == APPLIED_TEXT, landed
E       AssertionError: Ship the queue for platform on schedule
E       assert 'Ship the que...m on schedule' == 'Ship the Q4 ...rm in October'
E         
E         - Ship the Q4 platform in October
E         + Ship the queue for platform on schedule

tests/e2e/test_hs176_loop_glass.py:276: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
_________ TestOneDelete.test_the_foot_never_covers_the_last_rows[393] __________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x111c666c0>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_foot_never_covers_the_last_rows(self, width: int) -> None:
        """P2: with the receipt and the selection bar in the foot, the end of a
        long list scrolls clear of the foot; the last rows own their centres."""
        from playwright.sync_api import sync_playwright
    
        titles = [f"Last row {n:02d}" for n in range(1, 21)]
        with sync_playwright() as pw:
            browser, page, ids, errors = self._open(pw, width, titles)
            try:
                _to_face(page, "list", width)
                page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
                _select(page, "list", ids[-2], titles[-2])
                _row_menu_delete(page, titles[-1])
>               _readable_receipt(page, "Removed", 5_000)

tests/e2e/test_philo8_one_delete_glass.py:614: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:58: in _readable_receipt
    return _readable_now(page, want, timeout_ms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/e2e/test_philo7_delete_receipt_glass.py:70: in _readable_receipt
    page.wait_for_function(
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x141fcdd50>
cb = <function Channel.send.<locals>.<lambda> at 0x1420c7f60>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_________________ test_operations_export_matches_the_catalogue _________________
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

    def test_operations_export_matches_the_catalogue() -> None:
        gen = _load_script("gen_operations_json")
        committed = (REPO / "docs" / "generated" / "operations.json").read_text(encoding="utf-8")
>       assert committed == gen.render(), "regenerate: uv run python scripts/gen_operations_json.py"
E       AssertionError: regenerate: uv run python scripts/gen_operations_json.py
E       assert '{\n  "source...  }\n  ]\n}\n' == '{\n  "source...  }\n  ]\n}\n'
E         
E         Skipping 183198 identical leading characters in diff, use -v to show
E         - get for a stored document: the readable preview, the size and the digest of the exact bytes. Nothing is sent. Pass the digest to channel.send.",
E         ?            ^^^    ^^^^ --
E         + get for a published update: the readable preview, the size and the digest of the exact bytes. Nothing is sent. Pass the digest to channel.send.",
E         ?           +++++ ^   ++ ^^
E                 "args_schema": {...
E         
E         ...Full output truncated (415 lines hidden), use '-vv' to show

tests/unit/test_philo5_one_decision.py:399: AssertionError
__ test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face] __
[gw0] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

case_id = 'case.j9.shade_receipt_open.rhythm_face'
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw0/test_the_rig_drives_the_real_a6')

    @pytest.mark.parametrize("case_id", sorted(ATLAS_FENCE))
    def test_the_rig_drives_the_real_atlas(case_id, tmp_path):
        want_verdict, names, why = ATLAS_FENCE[case_id]
        if case_id in PENDING_IN_ATLAS:
            present = {c["id"] for c in json.loads(REAL_ATLAS.read_text())["cases"]}
            if case_id not in present:
                pytest.skip(f"{case_id} is not in the atlas yet (W2 is adding it); "
                            "reserved slot, flip when it lands")
        record = run_case(REAL_ATLAS, case_id, brain="muaddib", viewport=1440,
                          out=tmp_path, engine="none")
    
>       assert record["verdict"] == want_verdict, (
            f"{case_id}: {why}\n" + json.dumps(record["notes"], indent=2))
E       AssertionError: case.j9.shade_receipt_open.rhythm_face: the sweep receipt's own Open reaches the Rhythm face (the atlas crosses the first-value gate before the bell since round three)
E         [
E           "BLOCKED: ui step click on \"[title='Desk memory']\" failed: TimeoutError: Locator.click: Timeout 10000ms exceeded.\nCall log:\n  - waiting for locator(\"[title='Desk memory']\").first\n"
E         ]
E       assert 'blocked' == 'pass'
E         
E         - pass
E         + blocked

tests/e2e/test_graph_walk_smoke.py:102: AssertionError
____ test_the_declared_result_shape_is_the_producers_shape[channel.discard] ____
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x1365ba080>>, target=<holdspeak.services.channel_service.ChannelService object at 0x1365ba080>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_9d92274de48e1b9639202451', 'update_id': 'pupd_1d1a90987c334fd6b4c9b32ee1a5dd00'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
>               Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))

holdspeak/operations.py:2201: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Draft202012Validator(schema={'additionalProperties': False, 'properties': {'command_id': {'description': 'Optional ide...ting id>.', 'type': 'string'}}, 'required': ['document_ref', 'destination_id'], 'type': 'object'}, format_checker=None)
args = ({'destination_id': 'chd_9d92274de48e1b9639202451', 'update_id': 'pupd_1d1a90987c334fd6b4c9b32ee1a5dd00'},)
kwargs = {}, error = <ValidationError: "'document_ref' is a required property">

    def validate(self, *args, **kwargs):
        for error in self.iter_errors(*args, **kwargs):
>           raise error
E           jsonschema.exceptions.ValidationError: 'document_ref' is a required property
E           
E           Failed validating 'required' in schema:
E               {'type': 'object',
E                'properties': {'document_ref': {'type': 'string',
E                                                'description': 'The source document: '
E                                                               'project_update:<update '
E                                                               'id>, '
E                                                               'monday_brief:<brief '
E                                                               'id>, '
E                                                               'desk_decision:<decision '
E                                                               'id>, '
E                                                               'meeting_decision:<decision '
E                                                               'id>, '
E                                                               'decision_record:<record '
E                                                               'id>, '
E                                                               'meeting_summary:<meeting '
E                                                               'id>, '
E                                                               'meeting_digest:<meeting '
E                                                               'id>, or '
E                                                               'meeting_followup:<meeting '
E                                                               'id>.'},
E                               'destination_id': {'type': 'string',
E                                                  'description': 'The saved '
E                                                                 'destination: '
E                                                                 'destinations[].id '
E                                                                 'from '
E                                                                 'channel.destinations.'},
E                               'command_id': {'type': ['string', 'null'],
E                                              'description': 'Optional idempotency '
E                                                             'key. The same key with '
E                                                             'the same arguments '
E                                                             'returns the first '
E                                                             'result again; the same '
E                                                             'key with different '
E                                                             'arguments is refused '
E                                                             'with '
E                                                             'idempotency_conflict.'}},
E                'required': ['document_ref', 'destination_id'],
E                'additionalProperties': False}
E           
E           On instance:
E               {'update_id': 'pupd_1d1a90987c334fd6b4c9b32ee1a5dd00',
E                'destination_id': 'chd_9d92274de48e1b9639202451'}

.venv/lib/python3.13/site-packages/jsonschema/validators.py:450: ValidationError

The above exception was the direct cause of the following exception:

name = 'channel.discard'
hub = <tests.unit.test_philo5_the_loop.Hub object at 0x133e18130>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x134d0e040>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw9/test_the_declared_result_shape4')

    @pytest.mark.parametrize("name", sorted(PRODUCERS))
    def test_the_declared_result_shape_is_the_producers_shape(name: str, hub: Hub, monkeypatch, tmp_path) -> None:
        descriptor = operations.DESCRIPTORS[[d.name for d in operations.DESCRIPTORS].index(name)]
        keys = _declared_keys(descriptor.result)
>       result = PRODUCERS[name](hub, monkeypatch, tmp_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo5_the_loop_r2.py:590: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/unit/test_philo5_the_loop_r2.py:519: in _p_channel_discard
    prepared = _p_channel_prepare(hub, monkeypatch, tmp_path)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_philo5_the_loop_r2.py:515: in _p_channel_prepare
    return hub.root.operations.invoke(OWNER, "channel.prepare", {"update_id": uid, "destination_id": dest})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x1365ba080>>, target=<holdspeak.services.channel_service.ChannelService object at 0x1365ba080>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_9d92274de48e1b9639202451', 'update_id': 'pupd_1d1a90987c334fd6b4c9b32ee1a5dd00'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
                Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))
            except JsonSchemaValidationError as exc:
                location = ".".join(str(part) for part in exc.absolute_path)
                detail = f"{location}: {exc.message}" if location else exc.message
>               raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: {detail}") from exc
E               holdspeak.operations.OperationRefused: Invalid arguments for channel.prepare: 'document_ref' is a required property

holdspeak/operations.py:2205: OperationRefused
____ test_the_declared_result_shape_is_the_producers_shape[channel.prepare] ____
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x136ae5770>>, target=<holdspeak.services.channel_service.ChannelService object at 0x136ae5770>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_4e2f603417dd8dfd87c753d5', 'update_id': 'pupd_fc3be5bebfe04f6fa2f44d1fe1a46792'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
>               Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))

holdspeak/operations.py:2201: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Draft202012Validator(schema={'additionalProperties': False, 'properties': {'command_id': {'description': 'Optional ide...ting id>.', 'type': 'string'}}, 'required': ['document_ref', 'destination_id'], 'type': 'object'}, format_checker=None)
args = ({'destination_id': 'chd_4e2f603417dd8dfd87c753d5', 'update_id': 'pupd_fc3be5bebfe04f6fa2f44d1fe1a46792'},)
kwargs = {}, error = <ValidationError: "'document_ref' is a required property">

    def validate(self, *args, **kwargs):
        for error in self.iter_errors(*args, **kwargs):
>           raise error
E           jsonschema.exceptions.ValidationError: 'document_ref' is a required property
E           
E           Failed validating 'required' in schema:
E               {'type': 'object',
E                'properties': {'document_ref': {'type': 'string',
E                                                'description': 'The source document: '
E                                                               'project_update:<update '
E                                                               'id>, '
E                                                               'monday_brief:<brief '
E                                                               'id>, '
E                                                               'desk_decision:<decision '
E                                                               'id>, '
E                                                               'meeting_decision:<decision '
E                                                               'id>, '
E                                                               'decision_record:<record '
E                                                               'id>, '
E                                                               'meeting_summary:<meeting '
E                                                               'id>, '
E                                                               'meeting_digest:<meeting '
E                                                               'id>, or '
E                                                               'meeting_followup:<meeting '
E                                                               'id>.'},
E                               'destination_id': {'type': 'string',
E                                                  'description': 'The saved '
E                                                                 'destination: '
E                                                                 'destinations[].id '
E                                                                 'from '
E                                                                 'channel.destinations.'},
E                               'command_id': {'type': ['string', 'null'],
E                                              'description': 'Optional idempotency '
E                                                             'key. The same key with '
E                                                             'the same arguments '
E                                                             'returns the first '
E                                                             'result again; the same '
E                                                             'key with different '
E                                                             'arguments is refused '
E                                                             'with '
E                                                             'idempotency_conflict.'}},
E                'required': ['document_ref', 'destination_id'],
E                'additionalProperties': False}
E           
E           On instance:
E               {'update_id': 'pupd_fc3be5bebfe04f6fa2f44d1fe1a46792',
E                'destination_id': 'chd_4e2f603417dd8dfd87c753d5'}

.venv/lib/python3.13/site-packages/jsonschema/validators.py:450: ValidationError

The above exception was the direct cause of the following exception:

name = 'channel.prepare'
hub = <tests.unit.test_philo5_the_loop.Hub object at 0x135aee900>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1331ab380>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw9/test_the_declared_result_shape5')

    @pytest.mark.parametrize("name", sorted(PRODUCERS))
    def test_the_declared_result_shape_is_the_producers_shape(name: str, hub: Hub, monkeypatch, tmp_path) -> None:
        descriptor = operations.DESCRIPTORS[[d.name for d in operations.DESCRIPTORS].index(name)]
        keys = _declared_keys(descriptor.result)
>       result = PRODUCERS[name](hub, monkeypatch, tmp_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo5_the_loop_r2.py:590: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/unit/test_philo5_the_loop_r2.py:515: in _p_channel_prepare
    return hub.root.operations.invoke(OWNER, "channel.prepare", {"update_id": uid, "destination_id": dest})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x136ae5770>>, target=<holdspeak.services.channel_service.ChannelService object at 0x136ae5770>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_4e2f603417dd8dfd87c753d5', 'update_id': 'pupd_fc3be5bebfe04f6fa2f44d1fe1a46792'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
                Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))
            except JsonSchemaValidationError as exc:
                location = ".".join(str(part) for part in exc.absolute_path)
                detail = f"{location}: {exc.message}" if location else exc.message
>               raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: {detail}") from exc
E               holdspeak.operations.OperationRefused: Invalid arguments for channel.prepare: 'document_ref' is a required property

holdspeak/operations.py:2205: OperationRefused
____ test_the_declared_result_shape_is_the_producers_shape[channel.preview] ____
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x138c904b0>>, target=<holdspeak.services.channel_service.ChannelService object at 0x138c904b0>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.preview'
args = {'destination_id': 'chd_589feeb64261fbfeff2e2ffb', 'update_id': 'pupd_a7296abc78834c66abe17e699abe111d'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
>               Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))

holdspeak/operations.py:2201: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Draft202012Validator(schema={'additionalProperties': False, 'properties': {'destination_id': {'description': 'The save...ting id>.', 'type': 'string'}}, 'required': ['document_ref', 'destination_id'], 'type': 'object'}, format_checker=None)
args = ({'destination_id': 'chd_589feeb64261fbfeff2e2ffb', 'update_id': 'pupd_a7296abc78834c66abe17e699abe111d'},)
kwargs = {}, error = <ValidationError: "'document_ref' is a required property">

    def validate(self, *args, **kwargs):
        for error in self.iter_errors(*args, **kwargs):
>           raise error
E           jsonschema.exceptions.ValidationError: 'document_ref' is a required property
E           
E           Failed validating 'required' in schema:
E               {'type': 'object',
E                'properties': {'document_ref': {'type': 'string',
E                                                'description': 'The source document: '
E                                                               'project_update:<update '
E                                                               'id>, '
E                                                               'monday_brief:<brief '
E                                                               'id>, '
E                                                               'desk_decision:<decision '
E                                                               'id>, '
E                                                               'meeting_decision:<decision '
E                                                               'id>, '
E                                                               'decision_record:<record '
E                                                               'id>, '
E                                                               'meeting_summary:<meeting '
E                                                               'id>, '
E                                                               'meeting_digest:<meeting '
E                                                               'id>, or '
E                                                               'meeting_followup:<meeting '
E                                                               'id>.'},
E                               'destination_id': {'type': 'string',
E                                                  'description': 'The saved '
E                                                                 'destination: '
E                                                                 'destinations[].id '
E                                                                 'from '
E                                                                 'channel.destinations.'}},
E                'required': ['document_ref', 'destination_id'],
E                'additionalProperties': False}
E           
E           On instance:
E               {'update_id': 'pupd_a7296abc78834c66abe17e699abe111d',
E                'destination_id': 'chd_589feeb64261fbfeff2e2ffb'}

.venv/lib/python3.13/site-packages/jsonschema/validators.py:450: ValidationError

The above exception was the direct cause of the following exception:

name = 'channel.preview'
hub = <tests.unit.test_philo5_the_loop.Hub object at 0x13808baf0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x135aeff50>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw9/test_the_declared_result_shape6')

    @pytest.mark.parametrize("name", sorted(PRODUCERS))
    def test_the_declared_result_shape_is_the_producers_shape(name: str, hub: Hub, monkeypatch, tmp_path) -> None:
        descriptor = operations.DESCRIPTORS[[d.name for d in operations.DESCRIPTORS].index(name)]
        keys = _declared_keys(descriptor.result)
>       result = PRODUCERS[name](hub, monkeypatch, tmp_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo5_the_loop_r2.py:590: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/unit/test_philo5_the_loop_r2.py:510: in _p_channel_preview
    return hub.root.operations.invoke(OWNER, "channel.preview", {"update_id": uid, "destination_id": dest})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x138c904b0>>, target=<holdspeak.services.channel_service.ChannelService object at 0x138c904b0>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.preview'
args = {'destination_id': 'chd_589feeb64261fbfeff2e2ffb', 'update_id': 'pupd_a7296abc78834c66abe17e699abe111d'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
                Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))
            except JsonSchemaValidationError as exc:
                location = ".".join(str(part) for part in exc.absolute_path)
                detail = f"{location}: {exc.message}" if location else exc.message
>               raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: {detail}") from exc
E               holdspeak.operations.OperationRefused: Invalid arguments for channel.preview: 'document_ref' is a required property

holdspeak/operations.py:2205: OperationRefused
_____ test_the_declared_result_shape_is_the_producers_shape[channel.send] ______
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x139d19590>>, target=<holdspeak.services.channel_service.ChannelService object at 0x139d19590>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_5cfff77fc62e34c096e328e2', 'update_id': 'pupd_88ec18678d5c405b91a435dbe23f877c'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
>               Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))

holdspeak/operations.py:2201: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Draft202012Validator(schema={'additionalProperties': False, 'properties': {'command_id': {'description': 'Optional ide...ting id>.', 'type': 'string'}}, 'required': ['document_ref', 'destination_id'], 'type': 'object'}, format_checker=None)
args = ({'destination_id': 'chd_5cfff77fc62e34c096e328e2', 'update_id': 'pupd_88ec18678d5c405b91a435dbe23f877c'},)
kwargs = {}, error = <ValidationError: "'document_ref' is a required property">

    def validate(self, *args, **kwargs):
        for error in self.iter_errors(*args, **kwargs):
>           raise error
E           jsonschema.exceptions.ValidationError: 'document_ref' is a required property
E           
E           Failed validating 'required' in schema:
E               {'type': 'object',
E                'properties': {'document_ref': {'type': 'string',
E                                                'description': 'The source document: '
E                                                               'project_update:<update '
E                                                               'id>, '
E                                                               'monday_brief:<brief '
E                                                               'id>, '
E                                                               'desk_decision:<decision '
E                                                               'id>, '
E                                                               'meeting_decision:<decision '
E                                                               'id>, '
E                                                               'decision_record:<record '
E                                                               'id>, '
E                                                               'meeting_summary:<meeting '
E                                                               'id>, '
E                                                               'meeting_digest:<meeting '
E                                                               'id>, or '
E                                                               'meeting_followup:<meeting '
E                                                               'id>.'},
E                               'destination_id': {'type': 'string',
E                                                  'description': 'The saved '
E                                                                 'destination: '
E                                                                 'destinations[].id '
E                                                                 'from '
E                                                                 'channel.destinations.'},
E                               'command_id': {'type': ['string', 'null'],
E                                              'description': 'Optional idempotency '
E                                                             'key. The same key with '
E                                                             'the same arguments '
E                                                             'returns the first '
E                                                             'result again; the same '
E                                                             'key with different '
E                                                             'arguments is refused '
E                                                             'with '
E                                                             'idempotency_conflict.'}},
E                'required': ['document_ref', 'destination_id'],
E                'additionalProperties': False}
E           
E           On instance:
E               {'update_id': 'pupd_88ec18678d5c405b91a435dbe23f877c',
E                'destination_id': 'chd_5cfff77fc62e34c096e328e2'}

.venv/lib/python3.13/site-packages/jsonschema/validators.py:450: ValidationError

The above exception was the direct cause of the following exception:

name = 'channel.send'
hub = <tests.unit.test_philo5_the_loop.Hub object at 0x137646660>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x135965d30>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw9/test_the_declared_result_shape10')

    @pytest.mark.parametrize("name", sorted(PRODUCERS))
    def test_the_declared_result_shape_is_the_producers_shape(name: str, hub: Hub, monkeypatch, tmp_path) -> None:
        descriptor = operations.DESCRIPTORS[[d.name for d in operations.DESCRIPTORS].index(name)]
        keys = _declared_keys(descriptor.result)
>       result = PRODUCERS[name](hub, monkeypatch, tmp_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo5_the_loop_r2.py:590: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/unit/test_philo5_the_loop_r2.py:524: in _p_channel_send
    prepared = _p_channel_prepare(hub, monkeypatch, tmp_path)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_philo5_the_loop_r2.py:515: in _p_channel_prepare
    return hub.root.operations.invoke(OWNER, "channel.prepare", {"update_id": uid, "destination_id": dest})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x139d19590>>, target=<holdspeak.services.channel_service.ChannelService object at 0x139d19590>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_5cfff77fc62e34c096e328e2', 'update_id': 'pupd_88ec18678d5c405b91a435dbe23f877c'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
                Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))
            except JsonSchemaValidationError as exc:
                location = ".".join(str(part) for part in exc.absolute_path)
                detail = f"{location}: {exc.message}" if location else exc.message
>               raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: {detail}") from exc
E               holdspeak.operations.OperationRefused: Invalid arguments for channel.prepare: 'document_ref' is a required property

holdspeak/operations.py:2205: OperationRefused
_____ test_the_declared_result_shape_is_the_producers_shape[channel.sends] _____
[gw9] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x139baff70>>, target=<holdspeak.services.channel_service.ChannelService object at 0x139baff70>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_8ee6c094af0e47b226318c0f', 'update_id': 'pupd_629d61aa1241482ab109569a3df68f7d'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
>               Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))

holdspeak/operations.py:2201: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = Draft202012Validator(schema={'additionalProperties': False, 'properties': {'command_id': {'description': 'Optional ide...ting id>.', 'type': 'string'}}, 'required': ['document_ref', 'destination_id'], 'type': 'object'}, format_checker=None)
args = ({'destination_id': 'chd_8ee6c094af0e47b226318c0f', 'update_id': 'pupd_629d61aa1241482ab109569a3df68f7d'},)
kwargs = {}, error = <ValidationError: "'document_ref' is a required property">

    def validate(self, *args, **kwargs):
        for error in self.iter_errors(*args, **kwargs):
>           raise error
E           jsonschema.exceptions.ValidationError: 'document_ref' is a required property
E           
E           Failed validating 'required' in schema:
E               {'type': 'object',
E                'properties': {'document_ref': {'type': 'string',
E                                                'description': 'The source document: '
E                                                               'project_update:<update '
E                                                               'id>, '
E                                                               'monday_brief:<brief '
E                                                               'id>, '
E                                                               'desk_decision:<decision '
E                                                               'id>, '
E                                                               'meeting_decision:<decision '
E                                                               'id>, '
E                                                               'decision_record:<record '
E                                                               'id>, '
E                                                               'meeting_summary:<meeting '
E                                                               'id>, '
E                                                               'meeting_digest:<meeting '
E                                                               'id>, or '
E                                                               'meeting_followup:<meeting '
E                                                               'id>.'},
E                               'destination_id': {'type': 'string',
E                                                  'description': 'The saved '
E                                                                 'destination: '
E                                                                 'destinations[].id '
E                                                                 'from '
E                                                                 'channel.destinations.'},
E                               'command_id': {'type': ['string', 'null'],
E                                              'description': 'Optional idempotency '
E                                                             'key. The same key with '
E                                                             'the same arguments '
E                                                             'returns the first '
E                                                             'result again; the same '
E                                                             'key with different '
E                                                             'arguments is refused '
E                                                             'with '
E                                                             'idempotency_conflict.'}},
E                'required': ['document_ref', 'destination_id'],
E                'additionalProperties': False}
E           
E           On instance:
E               {'update_id': 'pupd_629d61aa1241482ab109569a3df68f7d',
E                'destination_id': 'chd_8ee6c094af0e47b226318c0f'}

.venv/lib/python3.13/site-packages/jsonschema/validators.py:450: ValidationError

The above exception was the direct cause of the following exception:

name = 'channel.sends'
hub = <tests.unit.test_philo5_the_loop.Hub object at 0x1357502f0>
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x137646c10>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/pytest/popen-gw9/test_the_declared_result_shape11')

    @pytest.mark.parametrize("name", sorted(PRODUCERS))
    def test_the_declared_result_shape_is_the_producers_shape(name: str, hub: Hub, monkeypatch, tmp_path) -> None:
        descriptor = operations.DESCRIPTORS[[d.name for d in operations.DESCRIPTORS].index(name)]
        keys = _declared_keys(descriptor.result)
>       result = PRODUCERS[name](hub, monkeypatch, tmp_path)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/unit/test_philo5_the_loop_r2.py:590: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/unit/test_philo5_the_loop_r2.py:539: in _p_channel_sends
    _p_channel_send(hub, monkeypatch, tmp_path)
tests/unit/test_philo5_the_loop_r2.py:524: in _p_channel_send
    prepared = _p_channel_prepare(hub, monkeypatch, tmp_path)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/unit/test_philo5_the_loop_r2.py:515: in _p_channel_prepare
    return hub.root.operations.invoke(OWNER, "channel.prepare", {"update_id": uid, "destination_id": dest})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = OperationRegistry(operations={'decision.create': BoundOperation(descriptor=OperationDescriptor(name='decision.create',...nelService object at 0x139baff70>>, target=<holdspeak.services.channel_service.ChannelService object at 0x139baff70>)})
principal = Principal(kind=<PrincipalKind.OWNER: 'owner'>, identity='owner-session', allowed_operations=frozenset(), authority_basis='')
name = 'channel.prepare'
args = {'destination_id': 'chd_8ee6c094af0e47b226318c0f', 'update_id': 'pupd_629d61aa1241482ab109569a3df68f7d'}

    def invoke(
        self,
        principal: Any,
        name: str,
        args: Optional[Mapping[str, Any]] = None,
        *,
        held: Optional[Mapping[str, Any]] = None,
    ) -> Any:
        """Validate *args* against the declaration, call the bound method, return its result.
    
        *held* carries the transport-held inputs the descriptor names in
        ``held`` (PHILO-5-02, gap E) -- exactly those, or the call is a
        transport bug and fails before the service runs.
        """
        _LAST_KERNEL.set(None)
        bound = self._bound(name)
        self.authorize(principal, name)
        given_held = dict(held or {})
        if set(given_held) != set(bound.descriptor.held):
            raise RuntimeError(
                f"{name}: the transport must hold exactly {sorted(bound.descriptor.held)}, "
                f"it passed {sorted(given_held)}"
            )
        payload = {} if args is None else args
        try:
            if not isinstance(payload, Mapping):
                raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: expected an object")
            claimed = sorted(AUTHORITY_FIELDS & set(payload))
            if claimed:
                raise OperationRefused(
                    "authority_in_arguments", name,
                    f"Invalid arguments for {name}: {', '.join(claimed)} cannot be an argument; "
                    "the principal comes from the transport",
                )
            try:
                Draft202012Validator(dict(bound.descriptor.args_schema)).validate(dict(payload))
            except JsonSchemaValidationError as exc:
                location = ".".join(str(part) for part in exc.absolute_path)
                detail = f"{location}: {exc.message}" if location else exc.message
>               raise OperationRefused("invalid_arguments", name, f"Invalid arguments for {name}: {detail}") from exc
E               holdspeak.operations.OperationRefused: Invalid arguments for channel.prepare: 'document_ref' is a required property

holdspeak/operations.py:2205: OperationRefused
_____ test_every_source_reference_lands_on_its_symbol[atlas-phase10.json] ______
[gw4] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

every_atlas = {'atlas_version': 'phase10-send', 'cases': [{'applicability': 'applicable', 'completion_bound_s': 30, 'edge_ids': ['ed... 'source': 'datetime.datetime.now() inside the hub process', 'status': 'available', ...}], 'council_readings': [], ...}

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
E       AssertionError: state.desk_presentation.p10_send_face: holdspeak/services/channel_service.py:400 no longer holds 'def send(self, principal' (line reads '# ── the press ────────────────────────────────────────────────────────')
E         state.desk_presentation.p10_send_face: holdspeak/services/channel_service.py:380 no longer holds 'def discard(self, principal' (line reads 'return self._answer(self._db.channel_sends.get(send_id))')
E       assert not ["state.desk_presentation.p10_send_face: holdspeak/services/channel_service.py:400 no longer holds 'def send(self, pri...no longer holds 'def discard(self, principal' (line reads 'return self._answer(self._db.channel_sends.get(send_id))')"]

tests/unit/test_philo_graph_atlas.py:279: AssertionError
__________________ test_abort_mid_stream_flips_send_stop_send __________________
[gw0] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

hub = {'broker': <holdspeak.kernel.broker.Broker object at 0x13508be90>, 'db': <holdspeak.db.core.Database object at 0x139fc9e50>, 'engine_patched': True, 'server': <holdspeak.web_server.MeetingWebServer object at 0x139fca210>, ...}

    def test_abort_mid_stream_flips_send_stop_send(hub: dict) -> None:
        """Abort mid-stream: Send flips to Stop while streaming, Stop aborts,
        and the button returns to Send. An aborted row remains."""
        from playwright.sync_api import sync_playwright
    
        url = hub["url"]
        broker = hub["broker"]
    
        # Use a slow engine so we have time to abort
        if broker is not None:
            broker.inference_runner._engine_factory = lambda _rev, **_kw: SlowStreamingEngine()
    
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    
            r = _api(page, "POST", "/api/threads", {"title": "Abort Test"})
            assert r["status"] == 201
            tid = r["payload"]["id"]
            _open_thread(page, url, tid)
    
            composer = page.locator(".thread-composer-input")
            composer.wait_for(timeout=10000)
            composer.fill("This will be aborted")
    
            # Verify Send button is visible
            send = page.locator("button.desk-chip", has_text="Send")
            assert send.count() > 0, "Send button not found before send"
    
            send.click()
            page.wait_for_timeout(500)
    
            # After sending, button should flip to Stop (if streaming is wired)
            stop_btn = page.locator("button.desk-chip", has_text="Stop")
            if stop_btn.count() > 0:
                # Streaming is active -- Stop is visible
                stop_btn.click()
                page.wait_for_timeout(1000)
    
                # After abort, button should return to Send
                send_after = page.locator("button.desk-chip", has_text="Send")
                assert send_after.count() > 0, "Send button did not return after abort"
    
                # Check for aborted row
                detail = _api(page, "GET", f"/api/threads/{tid}")
                msgs = detail["payload"].get("messages", [])
                assistant_msgs = [m for m in msgs if m.get("role") == "assistant"]
                if assistant_msgs:
                    aborted = assistant_msgs[-1].get("aborted_at")
                    # aborted_at should be set (or streaming=0)
                    assert not assistant_msgs[-1].get("streaming", 0), (
                        "message still streaming after abort"
                    )
            else:
                # Streaming not wired: the non-streaming path completes
                # synchronously before we can observe the Stop button.
                page.wait_for_timeout(6000)
                send_after = page.locator("button.desk-chip", has_text="Send")
                # Send should be back after the turn completes
>               assert send_after.count() > 0, (
                    "Send button missing after non-streaming turn completion"
                )
E               AssertionError: Send button missing after non-streaming turn completion
E               assert 0 > 0
E                +  where 0 = count()
E                +    where count = <Locator frame=<Frame name= url='http://127.0.0.1:53255/?open=thread%3Ath_d274ba1f7a43'> selector='button.desk-chip >> internal:has-text="Send"i'>.count

tests/e2e/test_hs151_thread_glass.py:335: AssertionError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___________________ test_chat_alias_engine_runs_off_the_loop ___________________
[gw10] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

env = (<holdspeak.db.core.Database object at 0x13c4b4910>, <starlette.testclient.TestClient object at 0x1354d7bd0>)
spy = <tests.unit.test_web_routes_recipe_chat._LoopSpy object at 0x136b19d30>

    def test_chat_alias_engine_runs_off_the_loop(env, spy) -> None:
        """The engine dispatched by the chat alias runs off the event loop.
    
        Regression guard: the broken inline ThreadService construction passed
        broker=None, crashing the daemon thread. The shared factory wires the
        kernel broker, and the engine runs in a daemon thread (off the loop).
        """
        db, client = env
        _seed_persona(db)
        resp = client.post("/api/recipes/recipe_scout/chat", json={"question": "hi"})
        assert resp.status_code == 201
        # The turn runs on a daemon thread; wait for the spy to fire.
        for _ in range(100):
            if spy.on_loop is not None:
                break
            time.sleep(0.02)
>       assert spy.on_loop is False, (
            "the engine ran ON the event loop -- the thread alias must dispatch "
            "the turn to a daemon thread so the request never blocks the loop"
        )
E       AssertionError: the engine ran ON the event loop -- the thread alias must dispatch the turn to a daemon thread so the request never blocks the loop
E       assert None is False
E        +  where None = <tests.unit.test_web_routes_recipe_chat._LoopSpy object at 0x136b19d30>.on_loop

tests/unit/test_web_routes_recipe_chat.py:175: AssertionError
=============================== warnings summary ===============================
tests/e2e/test_hs202_05_first_use_type_floor.py:260
tests/e2e/test_hs202_05_first_use_type_floor.py:260
tests/e2e/test_hs202_05_first_use_type_floor.py:260
tests/e2e/test_hs202_05_first_use_type_floor.py:260
tests/e2e/test_hs202_05_first_use_type_floor.py:260
tests/e2e/test_hs202_05_first_use_type_floor.py:260
tests/e2e/test_hs202_05_first_use_type_floor.py:260
  /Users/karol/dev/tools/wt-philo-11-01/tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/e2e/test_hs202_05_first_use_type_floor.py:439
tests/e2e/test_hs202_05_first_use_type_floor.py:439
tests/e2e/test_hs202_05_first_use_type_floor.py:439
tests/e2e/test_hs202_05_first_use_type_floor.py:439
tests/e2e/test_hs202_05_first_use_type_floor.py:439
tests/e2e/test_hs202_05_first_use_type_floor.py:439
tests/e2e/test_hs202_05_first_use_type_floor.py:439
  /Users/karol/dev/tools/wt-philo-11-01/tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:807: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:18: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:42: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:47: no hub listening at http://localhost:8778
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/xdist-gw4/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/xdist-gw4/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_interview_service.py:237: QUARANTINED #694: it drives project.setup.finalize through the thread's bound dispatch to assert the continuation refusal; finalize is CONFIG (the owner's press), no longer in the section, so the call is refused as unavailable before the continuation check. BACKLOG row 'Interview setup continuation after #694'.
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:59: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:110: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:100: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:182: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:159: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:553: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:619: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:172: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:233: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:282: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:150: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:397: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:462: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:555: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:268: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:519: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:671: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:919: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1088: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:328: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1637: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:319: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:279: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:365: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/wt-philo-11-01/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:118: mermaid renderer unavailable in this env: eer-core/lib/puppeteer/node/PuppeteerNode.js:124:16)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:1090:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:493:3)
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.HN4n1gc7Rx/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
FAILED tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot
FAILED tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j1.first_words_continue_later.idle]
FAILED tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 - AssertionEr...
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - AssertionErr...
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]
FAILED tests/unit/test_philo5_one_decision.py::test_operations_export_matches_the_catalogue
FAILED tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face]
FAILED tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.discard]
FAILED tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.prepare]
FAILED tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.preview]
FAILED tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.send]
FAILED tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.sends]
FAILED tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase10.json]
FAILED tests/e2e/test_hs151_thread_glass.py::test_abort_mid_stream_flips_send_stop_send
FAILED tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop
16 failed, 13520 passed, 99 skipped, 4 xfailed, 17 warnings in 3649.54s (1:00:49)
```

### Captured run — 2026-09-30T04:06:05Z

- **Command:** `bash -c set -e
PHILO_TEST_HOME=$(mktemp -d)
trap 'rm -rf "$PHILO_TEST_HOME"' EXIT
env HOME="$PHILO_TEST_HOME" uv run pytest -q --collect-only --basetemp="$PHILO_TEST_HOME/pytest" tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop
env HOME="$PHILO_TEST_HOME" uv run pytest -q --tb=short --basetemp="$PHILO_TEST_HOME/pytest" tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** unknown

```text
tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop

2 tests collected in 0.72s
FF                                                                       [100%]
=================================== FAILURES ===================================
_____________ test_recipe_run_and_chat_run_the_engine_off_the_loop _____________
tests/unit/test_engine_off_the_loop.py:131: in test_recipe_run_and_chat_run_the_engine_off_the_loop
    _assert_off_loop(spy)
tests/unit/test_engine_off_the_loop.py:99: in _assert_off_loop
    assert spy.on_loop is False, (
E   AssertionError: the engine ran ON the event loop — a mesh run would deadlock the worker's claim polls and die at its deadline as 'never claimed'
E   assert None is False
E    +  where None = <tests.unit.test_engine_off_the_loop._LoopSpy object at 0x11155dfd0>.on_loop
___________________ test_chat_alias_engine_runs_off_the_loop ___________________
tests/unit/test_web_routes_recipe_chat.py:175: in test_chat_alias_engine_runs_off_the_loop
    assert spy.on_loop is False, (
E   AssertionError: the engine ran ON the event loop -- the thread alias must dispatch the turn to a daemon thread so the request never blocks the loop
E   assert None is False
E    +  where None = <tests.unit.test_web_routes_recipe_chat._LoopSpy object at 0x1117b5550>.on_loop
=========================== short test summary info ============================
FAILED tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
FAILED tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop
2 failed in 7.15s
```

### Captured run — 2026-09-30T04:06:48Z

- **Command:** `bash -c PHILO_BASE_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_BASE_HOME"' EXIT; env HOME="$PHILO_BASE_HOME" PYTHONPATH=/Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158 uv run python -c 'import sys; from pathlib import Path; base=Path(".tmp/philo11/base-332d9158").resolve(); sys.path.insert(0,str(base)); import holdspeak; print("BASE PRODUCT:",holdspeak.__file__); import pytest; raise SystemExit(pytest.main(["-q","--tb=short","--basetemp="+sys.argv[1],"tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop","tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop"]))' "$PHILO_BASE_HOME/pytest"`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
BASE PRODUCT: /Users/karol/dev/tools/wt-philo-11-01/.tmp/philo11/base-332d9158/holdspeak/__init__.py
..                                                                       [100%]
2 passed in 1.62s
```

### Captured run — 2026-09-30T04:08:06Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared --brain astra --viewport 393 --engine none --out .tmp/graph-walk/philo11-01/prepared-393`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
PASS: live
BRAIN: astra
SOURCE: 332d91586bdbd7fe40e3c2c00851a46adc4650e4 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:58624 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-ltxefdg3/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: ['.tmp/graph-walk/philo11-01/prepared-393/20260930T040806Z-case.p10.send.prepared-astra-393/before.png', '.tmp/graph-walk/philo11-01/prepared-393/20260930T040806Z-case.p10.send.prepared-astra-393/after.png']
NOTE: predicate: all_of: readable_text: 'PREPARED' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 284, 'w': 363, 'h': 96} | readable_text: 'BY YOU' is readable in viewport {'width': 393, 'height': 852} with rect {'x': 15, 'y': 284, 'w': 363, 'h': 96} | protocol_reads: GET /api/channels/sends?document_ref=project_update:pupd_f188f3a9dea9454286eab860b75b0fc9 answered 200 with 1 row(s) {'id': 'chs_826beddf51393bdaaacbbfeb', 'state': 'prepared', 'prepared_by.kind': 'owner'}
```

### Captured run — 2026-09-30T04:09:17Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.sent.op --brain astra --viewport 1440 --engine none --headless --out .tmp/graph-walk/philo11-01/sent-op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
PASS: live
BRAIN: astra
SOURCE: 332d91586bdbd7fe40e3c2c00851a46adc4650e4 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:58784 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-mlrodyci/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: placeholder(s) ['send_op'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all 12 facts hold: the trigger outcome holds; observe_at updates.0.deliveries holds; observe_at updates.0.deliveries.0.outcome holds; observe_at updates.0.deliveries.0.channel holds; observe_at updates.0.deliveries.0.operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds; op read #0 (kernel.receipt.read) objects.0.receipt.actor_kind holds; op read #1 (channel.sends) sends holds; op read #1 (channel.sends) sends.0.state holds; op read #1 (channel.sends) sends.0.proof.sha256 holds
```

### Captured run — 2026-09-30T04:10:06Z

- **Command:** `bash -c PHILO_WALK_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WALK_HOME"' EXIT; env HOME="$PHILO_WALK_HOME" uv run python scripts/graph_walk.py run --atlas docs/internal/philo/graph/atlas-phase10.json --case case.p10.send.prepared.op --brain astra --viewport 1440 --engine none --headless --out .tmp/graph-walk/philo11-01/prepared-op`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
PASS: live
BRAIN: astra
SOURCE: 332d91586bdbd7fe40e3c2c00851a46adc4650e4 dirty=True
CONTRACT: rig=1.5.2 brief=ba5477fd07db atlas=docs/internal/philo/graph/atlas-phase10.json
RUNTIME: build=['index-Dvjkur0f.js'] hub=http://127.0.0.1:58928 db=/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/graph-walk-home-w_9iyg3n/.local/share/holdspeak/holdspeak.db engine=none
JOB: p10
VERDICT: pass terminal=settled
EVIDENCE: []
NOTE: placeholder(s) ['prepare_op'] are bound by the trigger's own `capture_as`; `expected` is resolved after it fires (fields naming them are not read before the trigger)
NOTE: predicate: all 9 facts hold: observe_at sends holds; observe_at sends.0.state holds; observe_at sends.0.prepared_by.kind holds; observe_at sends.0.prepare_operation_id holds; op read #0 (kernel.receipt.read) objects.0.operation.name holds; op read #0 (kernel.receipt.read) objects.0.receipt.operation_id holds; op read #0 (kernel.receipt.read) objects.0.receipt.state holds; op read #0 (kernel.receipt.read) objects.0.receipt.actor_kind holds; op read #1 (project.list_updates) updates.0.deliveries holds
```

### Captured run — 2026-09-30T04:10:33Z

- **Command:** `bash -c PHILO_WEB_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_WEB_HOME"' EXIT; env HOME="$PHILO_WEB_HOME" npm_config_cache=/Users/karol/.npm uv run python scripts/check_web_baseline.py --run`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
Running vitest...

=== Web baseline report ===

HEALED (5):
  src/desk/__tests__/containerQueryLaw.test.ts > HS-129-06 container-query law > keeps viewport-width media limited to shell exceptions
  src/desk/__tests__/writeReceiptGuard.test.ts > HS-132-06 swallowed-write guard > keeps every desk write out of a bare catch
  src/desk/components/InlineEditor.test.tsx > HS-129-08 editor windows > hosts note editing in its open pullout
  src/desk/components/MicButton.test.tsx > MicButton surfaces named refusals (HS-132-05) > never claims retention the session cannot prove
  src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations > tests without delivering work, then enables and pauses the trigger

Suite totals: 2970 passed, 0 failed, 0 skipped

VERDICT: baseline-subset, zero branch-new
```

### Captured run — 2026-09-30T04:11:32Z

- **Command:** `bash -c env HOLDSPEAK_EVIDENCE_WRITE=1 uv run python scripts/verify_philo11_update_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
....                                                                     [100%]
4 passed in 123.37s (0:02:03)
```

### Captured run — 2026-09-30T04:16:21Z

- **Command:** `bash -c set -e; PHILO_DOC_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_DOC_HOME"' EXIT; export HOME="$PHILO_DOC_HOME"; uv run python scripts/generate_capability_docs.py; uv run python scripts/generate_capability_docs.py --check; uv run python scripts/philo_graph_reference.py; uv run python scripts/philo_graph_reference.py --check; uv run python scripts/gen_operations_json.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
Architecture documentation generated (10 outputs).
Architecture documentation checked (10 outputs).
case-revision: live-astra ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: live-astra ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: live-astra ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: live-astra ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: live-astra ran an older revision of case.j10.brief_item_shelf.refused
case-revision: live-astra ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: live-astra ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: live-astra ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: live-astra ran an older revision of case.j4.meetings_import.imported
case-revision: live-astra ran an older revision of case.j4.record_only.no_speech_head
case-revision: live-astra ran an older revision of case.j4.record_start.capture_recording
case-revision: live-astra ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: live-astra ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: live-astra ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: live-astra ran an older revision of case.j6.run_summary.host_named
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_failed
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_queued
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_ready
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_retry
case-revision: live-astra ran an older revision of case.j6.run_summary.intel_running
case-revision: live-astra ran an older revision of case.j6.run_summary.summary_text
case-revision: live-astra ran an older revision of case.j9.route_presentation_restore.restored
case-revision: live-astra ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: live-astra ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: live-muaddib ran an older revision of case.j10.arrival_generate_again.next_day
case-revision: live-muaddib ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: live-muaddib ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: live-muaddib ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: live-muaddib ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: live-muaddib ran an older revision of case.j10.brief_item_shelf.refused
case-revision: live-muaddib ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: live-muaddib ran an older revision of case.j3.speech_missing.row_stays
case-revision: live-muaddib ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: live-muaddib ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: live-muaddib ran an older revision of case.j4.meetings_import.imported
case-revision: live-muaddib ran an older revision of case.j4.record_only.no_speech_head
case-revision: live-muaddib ran an older revision of case.j4.record_start.capture_recording
case-revision: live-muaddib ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: live-muaddib ran an older revision of case.j5.meeting_open.planned_host_disclosed
case-revision: live-muaddib ran an older revision of case.j5.meeting_open.route_disclosed
case-revision: live-muaddib ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: live-muaddib ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: live-muaddib ran an older revision of case.j6.run_summary.host_named
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_failed
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_queued
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_ready
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_retry
case-revision: live-muaddib ran an older revision of case.j6.run_summary.intel_running
case-revision: live-muaddib ran an older revision of case.j6.run_summary.summary_text
case-revision: live-muaddib ran an older revision of case.j7.arrival_load.reload_persisted
case-revision: live-muaddib ran an older revision of case.j7.hub_restart.intel_retained
case-revision: live-muaddib ran an older revision of case.j9.route_presentation_restore.restored
case-revision: live-muaddib ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: live-muaddib ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: live-muaddib ran an older revision of case.j9.shade_open.door_stale
case-revision: static-astra ran an older revision of case.beyond.first_words_reload.retained_draft
case-revision: static-astra ran an older revision of case.j1.first_words_continue_later.draft_custody
case-revision: static-astra ran an older revision of case.j1.first_words_continue_later.idle
case-revision: static-astra ran an older revision of case.j1.first_words_keep_as_note.kept
case-revision: static-astra ran an older revision of case.j1.first_words_speak.kept
case-revision: static-astra ran an older revision of case.j1.first_words_speak.mic_unsupported
case-revision: static-astra ran an older revision of case.j1.first_words_speak.permission_denied
case-revision: static-astra ran an older revision of case.j1.first_words_speak.unreachable_hub
case-revision: static-astra ran an older revision of case.j1.speech_readiness.ready
case-revision: static-astra ran an older revision of case.j10.arrival_generate_again.next_day
case-revision: static-astra ran an older revision of case.j10.arrival_generate_again.same_day_idempotent
case-revision: static-astra ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: static-astra ran an older revision of case.j10.arrival_generate_brief.populated
case-revision: static-astra ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: static-astra ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: static-astra ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: static-astra ran an older revision of case.j10.brief_item_shelf.refused
case-revision: static-astra ran an older revision of case.j10.brief_latest.absent
case-revision: static-astra ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: static-astra ran an older revision of case.j11.thought_keep.kept
case-revision: static-astra ran an older revision of case.j2.arrival_load.engines_both_missing
case-revision: static-astra ran an older revision of case.j2.arrival_load.read_pending
case-revision: static-astra ran an older revision of case.j2.arrival_load.read_unknown
case-revision: static-astra ran an older revision of case.j2.arrival_load.summary_missing_only
case-revision: static-astra ran an older revision of case.j3.concierge_use_for_summaries.assigned_ready
case-revision: static-astra ran an older revision of case.j3.speech_missing.row_stays
case-revision: static-astra ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: static-astra ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: static-astra ran an older revision of case.j4.meetings_import.imported
case-revision: static-astra ran an older revision of case.j4.record_only.no_speech_head
case-revision: static-astra ran an older revision of case.j4.record_start.capture_recording
case-revision: static-astra ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: static-astra ran an older revision of case.j5.meeting_open.route_disclosed
case-revision: static-astra ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: static-astra ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: static-astra ran an older revision of case.j6.run_summary.host_named
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_failed
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_queued
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_ready
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_retry
case-revision: static-astra ran an older revision of case.j6.run_summary.intel_running
case-revision: static-astra ran an older revision of case.j6.run_summary.summary_text
case-revision: static-astra ran an older revision of case.j7.arrival_load.reload_persisted
case-revision: static-astra ran an older revision of case.j7.hub_restart.intel_retained
case-revision: static-astra ran an older revision of case.j9.route_presentation_restore.restored
case-revision: static-astra ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: static-astra ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: static-astra ran an older revision of case.j9.shade_open.door_present
case-revision: static-astra ran an older revision of case.j9.shade_open.door_stale
case-revision: static-astra ran an older revision of case.j9.shade_receipt_open.rhythm_face
case-revision: static-muaddib ran an older revision of case.beyond.first_words_reload.retained_draft
case-revision: static-muaddib ran an older revision of case.j1.first_words_continue_later.draft_custody
case-revision: static-muaddib ran an older revision of case.j1.first_words_continue_later.idle
case-revision: static-muaddib ran an older revision of case.j1.first_words_keep_as_note.kept
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.kept
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.mic_unsupported
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.permission_denied
case-revision: static-muaddib ran an older revision of case.j1.first_words_speak.unreachable_hub
case-revision: static-muaddib ran an older revision of case.j1.speech_readiness.ready
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_again.next_day
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_again.same_day_idempotent
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_brief.generated_empty
case-revision: static-muaddib ran an older revision of case.j10.arrival_generate_brief.populated
case-revision: static-muaddib ran an older revision of case.j10.arrival_reload.reload_persisted
case-revision: static-muaddib ran an older revision of case.j10.brief_item_shelf.acknowledged
case-revision: static-muaddib ran an older revision of case.j10.brief_item_shelf.deferred
case-revision: static-muaddib ran an older revision of case.j10.brief_item_shelf.refused
case-revision: static-muaddib ran an older revision of case.j10.brief_latest.absent
case-revision: static-muaddib ran an older revision of case.j10.route_brief_generate.load_failure
case-revision: static-muaddib ran an older revision of case.j11.thought_keep.kept
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.engines_both_missing
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.read_pending
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.read_unknown
case-revision: static-muaddib ran an older revision of case.j2.arrival_load.summary_missing_only
case-revision: static-muaddib ran an older revision of case.j3.concierge_use_for_summaries.assigned_ready
case-revision: static-muaddib ran an older revision of case.j3.speech_missing.row_stays
case-revision: static-muaddib ran an older revision of case.j4.meeting_stop.capture_finalized
case-revision: static-muaddib ran an older revision of case.j4.meeting_stop.transcription_absent
case-revision: static-muaddib ran an older revision of case.j4.meetings_import.imported
case-revision: static-muaddib ran an older revision of case.j4.record_only.no_speech_head
case-revision: static-muaddib ran an older revision of case.j4.record_start.capture_recording
case-revision: static-muaddib ran an older revision of case.j5.meeting_open.no_engine_no_verb
case-revision: static-muaddib ran an older revision of case.j5.meeting_open.route_disclosed
case-revision: static-muaddib ran an older revision of case.j6.route_intelligence_run.no_assignment
case-revision: static-muaddib ran an older revision of case.j6.route_intelligence_run.refusal
case-revision: static-muaddib ran an older revision of case.j6.run_summary.host_named
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_failed
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_queued
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_ready
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_retry
case-revision: static-muaddib ran an older revision of case.j6.run_summary.intel_running
case-revision: static-muaddib ran an older revision of case.j6.run_summary.summary_text
case-revision: static-muaddib ran an older revision of case.j7.arrival_load.reload_persisted
case-revision: static-muaddib ran an older revision of case.j7.hub_restart.intel_retained
case-revision: static-muaddib ran an older revision of case.j9.route_presentation_restore.restored
case-revision: static-muaddib ran an older revision of case.j9.shade_acknowledge.acknowledged
case-revision: static-muaddib ran an older revision of case.j9.shade_dismiss.dismissed
case-revision: static-muaddib ran an older revision of case.j9.shade_open.door_present
case-revision: static-muaddib ran an older revision of case.j9.shade_open.door_stale
case-revision: static-muaddib ran an older revision of case.j9.shade_receipt_open.rhythm_face
exposure-disagreement: edge.timer.workbench_conductor: astra=conditional; muaddib=active
exposure-disagreement: edge.verb.desk_arrange: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_brief: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_find_receipt: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_overdue: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_intelligence_review_decisions: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_agent: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_decision: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_knowledge: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_note: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_project: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_thread: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_workbench: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_workflow: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_new_zone: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_open_intelligence: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_open_people: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_overview: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_refresh: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_reset_layout: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_reset_to_seed: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_settle: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.desk_toggle_view: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_ask: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_ask_project: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_continue_in_thread: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_delete: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_duplicate: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_edit: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_file: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_info: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_open: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.object_rename: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.system_search: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.system_sheet: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.thread_compact: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_fork: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_guardrail: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_keep: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_mode: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_new: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_prompt: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_stop: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_todo: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.thread_tools: astra=internal; muaddib=conditional
exposure-disagreement: edge.verb.window_close: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_cycle: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_cycle_reverse: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_maximize: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_minimize: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_snap_left: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.window_snap_right: astra=active; muaddib=conditional
exposure-disagreement: edge.verb.zone_focus: astra=active; muaddib=conditional
subtype-conflict: edge.cli.hub_restart: astra=process.restart; muaddib=cli
subtype-conflict: edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
subtype-conflict: edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
subtype-conflict: edge.route.brief_item_shelf: astra=ui; muaddib=http
subtype-conflict: edge.route.brief_latest: astra=ui; muaddib=http
subtype-conflict: edge.route.heartbeat_run_now: astra=ui; muaddib=http
subtype-conflict: edge.route.inference_assignments_set: astra=ui; muaddib=http
subtype-conflict: edge.route.model_profile_delete: astra=ui; muaddib=http
subtype-conflict: edge.route.model_profile_unbind: astra=ui; muaddib=http
subtype-conflict: edge.route.projection_presentation: astra=ui; muaddib=http
subtype-conflict: edge.route.projections_list: astra=ui; muaddib=http
subtype-conflict: edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
subtype-conflict: iface.face.arrival: astra=face.section; muaddib=face.window
subtype-conflict: iface.face.first_words: astra=face.card; muaddib=face.panel
subtype-normalized: edge.face.arrival_brief_generate: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.arrival_brief_generate_again: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_add_check: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_add_engine: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_apply: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_check: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_download: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.concierge_use_for_summaries: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_acknowledge: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_dismiss: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_open: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.face.shade_receipt_open: astra=ui; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.route.inference_assignments: astra=http.GET; muaddib=http -> http.GET (refinement)
subtype-normalized: edge.route.intel_retry: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_capture_recover: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_intelligence_run: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_start: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meeting_stop: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.route.meetings_import: astra=http.POST; muaddib=http -> http.POST (refinement)
subtype-normalized: edge.verb.desk_arrange: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_brief: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_find_receipt: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_overdue: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_intelligence_review_decisions: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_agent: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_decision: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_new_knowledge: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_note: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_new_project: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_thread: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_workbench: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_workflow: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_new_zone: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_open_intelligence: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_open_people: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_overview: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_refresh: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_reset_layout: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_reset_to_seed: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.desk_settle: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.desk_toggle_view: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_ask: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_ask_project: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_continue_in_thread: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_delete: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.object_duplicate: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_edit: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_file: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_info: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_open: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.object_rename: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.system_search: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.system_sheet: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.thread_compact: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_fork: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_guardrail: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_keep: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_mode: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_new: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_prompt: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_stop: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_todo: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.thread_tools: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.window_close: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_cycle: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_cycle_reverse: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_maximize: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.window_minimize: astra=verb; muaddib=keyboard -> keyboard (bucket)
subtype-normalized: edge.verb.window_snap_left: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.window_snap_right: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: edge.verb.zone_focus: astra=verb; muaddib=pointer.click -> pointer.click (bucket)
subtype-normalized: iface.face.concierge: astra=ui; muaddib=face.window -> face.window (bucket)
subtype-normalized: state.briefs.absent: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.generated_empty: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.generating: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.generation_failure: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.item.acknowledged: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.item.deferred: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.item.untouched: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.next_day_window: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.people.unavailable: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.populated: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.reload_persisted: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.briefs.same_day_idempotent: astra=atlas.briefs; muaddib=projection.brief -> projection.brief (vocabulary)
subtype-normalized: state.desk_presentation.reload_reconnect: astra=atlas.desk_presentation; muaddib=browser.presentation -> browser.presentation (vocabulary)
subtype-normalized: state.desk_presentation.window_open_thought: astra=atlas.desk_presentation; muaddib=browser.presentation -> browser.presentation (vocabulary)
subtype-normalized: state.engines.add_engine_ready: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.add_engine_refused: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.assigned_ready: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.assignment_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.binding_absent: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.both_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.profile_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.read_pending: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.read_unknown: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.speech_assignment_missing: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.speech_ready: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.engines.unreachable: astra=atlas.engines; muaddib=projection.assignment -> projection.assignment (vocabulary)
subtype-normalized: state.first_value.continue_later: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.draft_custody: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.failure.permission_denied: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.failure.unreachable_hub: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.kept: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.listening: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.mic_unsupported: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.retained_draft: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.first_value.success: astra=atlas.first_value; muaddib=lifecycle.first_value -> lifecycle.first_value (vocabulary)
subtype-normalized: state.meetings.capture.finalized: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.imported: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.recording: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.recoverable: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.capture.recovered: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.available: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.failed: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.queued: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.ready: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.retained_after_restart: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.retry_after_failure: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.intel.running: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.transcription.absent: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.meetings.transcription.record_only: astra=atlas.meetings; muaddib=domain.meeting -> domain.meeting (vocabulary)
subtype-normalized: state.projections.attention.acknowledged: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.attention.dismissed: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.attention.restored: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.door.absent: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.door.present: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.door.stale: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.projections.receipt.resolved: astra=atlas.projections; muaddib=projection.desk -> projection.desk (vocabulary)
subtype-normalized: state.time.next_due_sweep: astra=atlas.time; muaddib=clock -> clock (vocabulary)
subtype-normalized: state.time.sweep_held_remote: astra=atlas.time; muaddib=clock -> clock (vocabulary)
graph join generated: docs/generated/graph.json — 6472 nodes, 808 links, 85 cases, 216 observations, 112 claim reviews, 47 findings, 47 resolutions; 352 note(s)
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
OK docs/generated/operations.json
```

### Captured run — 2026-09-30T04:18:15Z

- **Command:** `bash -c set -e; PHILO_SCOPE_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_SCOPE_HOME"' EXIT; export HOME="$PHILO_SCOPE_HOME"; uv run python - "$PHILO_SCOPE_HOME" <<'PY'
import sys
from pathlib import Path
import pytest
nodes=[line for line in Path(".tmp/philo11/fallout/contract-fallout.collect.log").read_text().splitlines() if line.startswith("tests/")]
nodes += ["tests/unit/test_philo11_document_sources.py"]
args=["-q", "--basetemp="+sys.argv[1]+"/pytest", *nodes]
code=pytest.main(["--collect-only", *args])
if code: raise SystemExit(code)
raise SystemExit(pytest.main(args))
PY`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot
tests/unit/test_philo5_one_decision.py::test_operations_export_matches_the_catalogue
tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.discard]
tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.prepare]
tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.preview]
tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.send]
tests/unit/test_philo5_the_loop_r2.py::test_the_declared_result_shape_is_the_producers_shape[channel.sends]
tests/unit/test_philo_graph_atlas.py::test_every_source_reference_lands_on_its_symbol[atlas-phase10.json]
tests/unit/test_philo11_document_sources.py::test_registry_declares_the_eight_kinds
tests/unit/test_philo11_document_sources.py::test_real_producers_render_all_eight_sources
tests/unit/test_philo11_document_sources.py::test_meeting_sources_never_copy_transcript
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[project_update]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[monday_brief]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[desk_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[decision_record]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_summary]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[unknown_kind:source-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[meeting_summary:missing-document_not_found]
tests/unit/test_philo11_document_sources.py::test_missing_meeting_summary_is_named_no_summary
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_project_update_refuses_unpublished_by_generic_name
tests/unit/test_philo11_document_sources.py::test_aftercare_document_markdown_is_not_truncated

27 tests collected in 0.50s
...........................                                              [100%]
27 passed in 6.52s
```

### Captured run — 2026-09-30T04:18:48Z

Rejected verification attempt: standard input did not reach the child; no tests ran. The file-based rerun below is the proof.

- **Command:** `uv run python -`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
(no output)
```

### Captured run — 2026-09-30T04:19:13Z

- **Command:** `uv run python .tmp/philo11/recheck_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
ROUND 1: tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j1.first_words_continue_later.idle]
.                                                                        [100%]
1 passed in 8.27s
ROUND 1: tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face]
.                                                                        [100%]
1 passed in 9.12s
ROUND 1: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
.                                                                        [100%]
1 passed in 9.66s
ROUND 1: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
.                                                                        [100%]
1 passed in 9.33s
ROUND 1: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]
.                                                                        [100%]
1 passed in 10.69s
ROUND 1: tests/e2e/test_hs151_thread_glass.py::test_abort_mid_stream_flips_send_stop_send
.                                                                        [100%]
1 passed in 7.03s
ROUND 2: tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j1.first_words_continue_later.idle]
.                                                                        [100%]
1 passed in 8.56s
ROUND 2: tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j9.shade_receipt_open.rhythm_face]
.                                                                        [100%]
1 passed in 9.68s
ROUND 2: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
.                                                                        [100%]
1 passed in 9.34s
ROUND 2: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
.                                                                        [100%]
1 passed in 9.20s
ROUND 2: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]
.                                                                        [100%]
1 passed in 10.58s
ROUND 2: tests/e2e/test_hs151_thread_glass.py::test_abort_mid_stream_flips_send_stop_send
.                                                                        [100%]
1 passed in 7.21s
All six glass failures passed twice serially with a fresh HOME per test.
```

### Captured run — 2026-09-30T04:41:59Z

- **Command:** `bash -c set -e; PHILO_FINAL_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_FINAL_HOME"' EXIT; env HOME="$PHILO_FINAL_HOME" PYTHONPATH=. uv run python .tmp/philo11/check_thread_budget.py; env HOME="$PHILO_FINAL_HOME" uv run python scripts/gen_operations_json.py; env HOME="$PHILO_FINAL_HOME" uv run python scripts/gen_operations_json.py --check; env HOME="$PHILO_FINAL_HOME" uv run python scripts/generate_capability_docs.py --check; env HOME="$PHILO_FINAL_HOME" uv run python scripts/philo_openapi_reference.py --check; env HOME="$PHILO_FINAL_HOME" uv run python scripts/philo_graph_reference.py --check; env HOME="$PHILO_FINAL_HOME" uv run pytest -q --basetemp="$PHILO_FINAL_HOME/pytest" tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop tests/unit/test_philo10_send_contract.py::test_the_words_map_his_asks_and_never_say_an_agent_sends tests/unit/test_philo5_one_decision.py::test_operations_export_matches_the_catalogue`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
246 catalogue entries: all non-description fields unchanged.
SPY RUN 1 on_loop= False
{"context_ceiling": 16384, "engine_off_loop": true, "headroom": 361, "input_tokens": 15511, "palette_tools": 31, "reserved_output_tokens": 512, "source": "actual inference_adoption_route_evidence and material snapshot rows", "total_tokens": 16023}
WROTE docs/generated/operations.json
OK docs/generated/operations.json
Architecture documentation checked (10 outputs).
OpenAPI: 580 paths
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
....                                                                     [100%]
4 passed in 2.06s
```

### Captured run — 2026-09-30T04:43:17Z

- **Command:** `bash -c set -o pipefail; PHILO_FULL_HOME=$(mktemp -d); trap 'rm -rf "$PHILO_FULL_HOME"' EXIT; env HOME="$PHILO_FULL_HOME" TMPDIR="$PHILO_FULL_HOME" PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -n auto --dist=worksteal --ignore=tests/e2e/test_metal.py --basetemp="$PHILO_FULL_HOME/pytest" 2>&1 | tee .tmp/philo11/full-suite-final.log`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  0%]
........................................................................ [  1%]
........................................................................ [  1%]
........................................................................ [  2%]
........................................................................ [  2%]
........................................................................ [  3%]
........................................................................ [  3%]
........................................................................ [  4%]
........................................................................ [  4%]
........................................................................ [  5%]
............ssssssssssssssssssssss...................................... [  5%]
........................................................................ [  6%]
........................................................................ [  6%]
........................................................................ [  7%]
........................................................................ [  7%]
........................................................................ [  8%]
...........ss........................................................... [  8%]
........................................................................ [  9%]
........................................................................ [ 10%]
........................................................................ [ 10%]
........................................................................ [ 11%]
..............s......................................................... [ 11%]
........................................................................ [ 12%]
........................................................................ [ 12%]
........................................................................ [ 13%]
..............................s......................................... [ 13%]
........................................................................ [ 14%]
........................................................................ [ 14%]
........................................................................ [ 15%]
........................................................................ [ 15%]
........................................................................ [ 16%]
........................................................................ [ 16%]
........................................................................ [ 17%]
........................................................................ [ 17%]
........................................................................ [ 18%]
....ss.................................................................. [ 19%]
........................................................................ [ 19%]
........................................................................ [ 20%]
....................................................ss.................. [ 20%]
........................................................................ [ 21%]
........................................................................ [ 21%]
........................................................................ [ 22%]
........................................................................ [ 22%]
........................................................................ [ 23%]
........................................................................ [ 23%]
........................................................................ [ 24%]
........................................................................ [ 24%]
........................................................................ [ 25%]
........................................................................ [ 25%]
........................................................................ [ 26%]
........................................................................ [ 26%]
........................................................................ [ 27%]
........................................................................ [ 27%]
........................................................................ [ 28%]
........................................................................ [ 29%]
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 30%]
........................................................................ [ 31%]
........................................................................ [ 31%]
........................................................................ [ 32%]
........................................................................ [ 32%]
........................................................................ [ 33%]
........................................................................ [ 33%]
........................................................................ [ 34%]
........................................................................ [ 34%]
........................................................................ [ 35%]
.................s...................................................... [ 35%]
......................s................................................. [ 36%]
........................................................................ [ 36%]
........................................................................ [ 37%]
........................................................................ [ 38%]
........................................................................ [ 38%]
........................................................................ [ 39%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 40%]
........................................................................ [ 41%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 42%]
........................................................................ [ 43%]
........................................................................ [ 43%]
........................................................................ [ 44%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 45%]
........................................................................ [ 46%]
...............................................................s........ [ 47%]
........................................................................ [ 47%]
........................................................................ [ 48%]
............................................................F........... [ 48%]
........................................................................ [ 49%]
........................................................................ [ 49%]
........................................................................ [ 50%]
........................................................................ [ 50%]
........................................................................ [ 51%]
.........................................s.............................. [ 51%]
........................................................................ [ 52%]
........................................................................ [ 52%]
........................................................................ [ 53%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 54%]
........................................................................ [ 55%]
........................................................................ [ 55%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 57%]
........................................................................ [ 58%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 59%]
........................................................................ [ 60%]
...............................................s........................ [ 60%]
........................................................................ [ 61%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 62%]
........................................................................ [ 63%]
.............................................F.......................... [ 63%]
...............................................................FFFF.F... [ 64%]
..F.F.......F........................................................... [ 64%]
........................................................................ [ 65%]
........................................................................ [ 66%]
........................................................................ [ 66%]
........................................................................ [ 67%]
........................................................................ [ 67%]
........................................................................ [ 68%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 69%]
........................................................................ [ 70%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 71%]
........................................................................ [ 72%]
........................................................................ [ 72%]
........................................................................ [ 73%]
........................................................................ [ 73%]
...............ss....................................................... [ 74%]
........................................................................ [ 75%]
........................................................................ [ 75%]
..................F...........................................F......... [ 76%]
........................................................................ [ 76%]
........................................................................ [ 77%]
..........s............................................................. [ 77%]
...............................................F........................ [ 78%]
........................................................................ [ 78%]
...............................................ssssss................... [ 79%]
........................................................................ [ 79%]
........................................................................ [ 80%]
........................................................................ [ 80%]
........................................................................ [ 81%]
........................................................................ [ 81%]
........................................................................ [ 82%]
........................................................................ [ 82%]
........................................................................ [ 83%]
........................................................................ [ 83%]
........................................................................ [ 84%]
........................................................................ [ 85%]
........................................................................ [ 85%]
........................................................................ [ 86%]
........................................................................ [ 86%]
........................................................................ [ 87%]
........................................................................ [ 87%]
........................................................................ [ 88%]
........................................................................ [ 88%]
........................................................................ [ 89%]
........................................................................ [ 89%]
........................................................................ [ 90%]
........................................................................ [ 90%]
....................s.............s..................................... [ 91%]
......................................s..............................x.. [ 91%]
.........sss............................................................ [ 92%]
........................................................................ [ 92%]
........................................................................ [ 93%]
........................................................................ [ 94%]
................................................F....................... [ 94%]
........................................................................ [ 95%]
........................................................................ [ 95%]
........................................x.F............................. [ 96%]
............................................................ssss........ [ 96%]
...............x.ssssss................................................. [ 97%]
....F..................x................................................ [ 97%]
.............F..................F...............F.F...F.......F......... [ 98%]
.ssssssssss...s..........................F........F.sssssssss........... [ 98%]
................................F.........s.sssssssssss.........F.F..... [ 99%]
.................F.....F...........F..F.................FF..........F..F [ 99%]
..F...FF................                                                 [100%]
=================================== FAILURES ===================================
___________ test_desk_crud_descriptions_carry_kind_boundary_sentence ___________
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

    def test_desk_crud_descriptions_carry_kind_boundary_sentence() -> None:
        """All five desk.* CRUD tool descriptions contain the kind-boundary sentence."""
        tool_map = {tool["name"]: tool for tool in mcp_tools.TOOLS}
        for tool_name, expected_substring in _EXPECTED_SENTENCES.items():
            tool = tool_map.get(tool_name)
            assert tool is not None, f"{tool_name} missing from TOOLS catalogue"
            desc = tool["description"]
>           assert expected_substring in desc, (
                f"{tool_name} description does not contain the expected kind-boundary sentence.\n"
                f"  Expected substring: {expected_substring!r}\n"
                f"  Actual description: {desc!r}"
            )
E           AssertionError: desk.update description does not contain the expected kind-boundary sentence.
E               Expected substring: 'Authorable kinds: notes, decisions, kbs, directories, workflows, chains.'
E               Actual description: 'Update supplied desk fields. IDs from desk.list. notes title/body_markdown/tags; directories name/parent_id(null=root); decisions context_markdown/decision_markdown/consequences_markdown replace old text. Authorable kinds: notes, decisions, kbs, directories, workflows, and chains.'
E           assert 'Authorable kinds: notes, decisions, kbs, directories, workflows, chains.' in 'Update supplied desk fields. IDs from desk.list. notes title/body_markdown/tags; directories name/parent_id(null=root...n/consequences_markdown replace old text. Authorable kinds: notes, decisions, kbs, directories, workflows, and chains.'

tests/unit/test_mcp_phase133_surface.py:93: AssertionError
_ test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_brief.generated_empty] _
[gw0] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

case_id = 'case.j10.arrival_generate_brief.generated_empty'
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw0/test_the_rig_drives_the_real_a3')

    @pytest.mark.parametrize("case_id", sorted(ATLAS_FENCE))
    def test_the_rig_drives_the_real_atlas(case_id, tmp_path):
        want_verdict, names, why = ATLAS_FENCE[case_id]
        if case_id in PENDING_IN_ATLAS:
            present = {c["id"] for c in json.loads(REAL_ATLAS.read_text())["cases"]}
            if case_id not in present:
                pytest.skip(f"{case_id} is not in the atlas yet (W2 is adding it); "
                            "reserved slot, flip when it lands")
        record = run_case(REAL_ATLAS, case_id, brain="muaddib", viewport=1440,
                          out=tmp_path, engine="none")
    
>       assert record["verdict"] == want_verdict, (
            f"{case_id}: {why}\n" + json.dumps(record["notes"], indent=2))
E       AssertionError: case.j10.arrival_generate_brief.generated_empty: the empty brief says so on the face
E         [
E           "BLOCKED: precondition not met: {'kind': 'attr_equals', 'attr': 'data-testid', 'value': 'arrival-headline'} at '[data-testid=arrival-headline]' \u2014 BLOCKED: observe_at not present ('[data-testid=arrival-headline]'); no element carries 'data-testid'"
E         ]
E       assert 'blocked' == 'pass'
E         
E         - pass
E         + blocked

tests/e2e/test_graph_walk_smoke.py:102: AssertionError
_ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[file a note into a zone] _
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
phrase = 'file a note into a zone'

    @pytest.mark.parametrize("phrase", sorted(JOBS))
    def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
        tool_name, path = JOBS[phrase]
        naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
>       assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
E       AssertionError: 'file a note into a zone' is named by [], expected ['zone.file']
E       assert [] == ['zone.file']
E         
E         Right contains one more item: 'zone.file'
E         Use -v to get more diff

tests/unit/test_philo7_discovery.py:92: AssertionError
___ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[find a note] ___
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
phrase = 'find a note'

    @pytest.mark.parametrize("phrase", sorted(JOBS))
    def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
        tool_name, path = JOBS[phrase]
        naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
>       assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
E       AssertionError: 'find a note' is named by [], expected ['desk.list']
E       assert [] == ['desk.list']
E         
E         Right contains one more item: 'desk.list'
E         Use -v to get more diff

tests/unit/test_philo7_discovery.py:92: AssertionError
_ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[list the notes in a zone] _
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
phrase = 'list the notes in a zone'

    @pytest.mark.parametrize("phrase", sorted(JOBS))
    def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
        tool_name, path = JOBS[phrase]
        naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
>       assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
E       AssertionError: 'list the notes in a zone' is named by [], expected ['zone.list_members']
E       assert [] == ['zone.list_members']
E         
E         Right contains one more item: 'zone.list_members'
E         Use -v to get more diff

tests/unit/test_philo7_discovery.py:92: AssertionError
___ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a zone] ___
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
phrase = 'make a zone'

    @pytest.mark.parametrize("phrase", sorted(JOBS))
    def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
        tool_name, path = JOBS[phrase]
        naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
>       assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
E       AssertionError: 'make a zone' is named by [], expected ['desk.create']
E       assert [] == ['desk.create']
E         
E         Right contains one more item: 'desk.create'
E         Use -v to get more diff

tests/unit/test_philo7_discovery.py:92: AssertionError
_ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[put a decision on my review list] _
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
phrase = 'put a decision on my review list'

    @pytest.mark.parametrize("phrase", sorted(JOBS))
    def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
        tool_name, path = JOBS[phrase]
        naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
>       assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
E       AssertionError: 'put a decision on my review list' is named by [], expected ['desk.create']
E       assert [] == ['desk.create']
E         
E         Right contains one more item: 'desk.create'
E         Use -v to get more diff

tests/unit/test_philo7_discovery.py:92: AssertionError
___ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[read a note] ___
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
phrase = 'read a note'

    @pytest.mark.parametrize("phrase", sorted(JOBS))
    def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
        tool_name, path = JOBS[phrase]
        naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
>       assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
E       AssertionError: 'read a note' is named by [], expected ['desk.get']
E       assert [] == ['desk.get']
E         
E         Right contains one more item: 'desk.get'
E         Use -v to get more diff

tests/unit/test_philo7_discovery.py:92: AssertionError
_ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision] _
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
phrase = 'the reason for a decision'

    @pytest.mark.parametrize("phrase", sorted(JOBS))
    def test_each_job_phrase_maps_to_one_tool_and_its_argument_path(catalogue, phrase) -> None:
        tool_name, path = JOBS[phrase]
        naming = [t["name"] for t in catalogue if phrase in t.get("description", "").lower()]
>       assert naming == [tool_name], f"{phrase!r} is named by {naming}, expected [{tool_name!r}]"
E       AssertionError: 'the reason for a decision' is named by [], expected ['desk.create']
E       assert [] == ['desk.create']
E         
E         Right contains one more item: 'desk.create'
E         Use -v to get more diff

tests/unit/test_philo7_discovery.py:92: AssertionError
_____ test_every_id_argument_names_where_its_value_comes_from[zone.unfile] _____
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

catalogue = [{'description': 'List desk primitives by kind; notes expose IDs, directories member_ids, kbs list knowledge bases. Th...h.add_item, workbench.run.', 'type': 'string'}}, 'required': ['verb_id'], 'type': 'object'}, 'name': 'desk.verb'}, ...]
tool_name = 'zone.unfile'

    @pytest.mark.parametrize("tool_name", SLICE_TOOLS)
    def test_every_id_argument_names_where_its_value_comes_from(catalogue, tool_name) -> None:
        tools = _by_name(catalogue)
        properties = tools[tool_name]["inputSchema"]["properties"]
        id_arguments = [name for name in properties if _ID_ARGUMENT.search(name)]
        assert id_arguments or tool_name in {"desk.list", "desk.create"}, tool_name
        for argument in id_arguments:
            description = properties[argument].get("description", "")
            sources = _FROM_TOOL.findall(description)
            listed = "one of:" in description.lower()
>           assert sources or listed, f"{tool_name}.{argument} does not say where its value comes from: {description!r}"
E           AssertionError: zone.unfile.primitive_id does not say where its value comes from: 'Filed kind:id.'
E           assert ([] or False)

tests/unit/test_philo7_discovery.py:120: AssertionError
__ test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer ___
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

    def test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer() -> None:
        definitions, references, pointers, profile_ids = _routing_ast_inventory(REPO)
        assert definitions == ROUTING_RESOLVER_DEFINITIONS
>       assert references == ROUTING_RESOLVER_REFERENCES
E       AssertionError: assert {'holdspeak/d...acement', ...} == {'holdspeak/d...acement', ...}
E         
E         Extra items in the left set:
E         'holdspeak/mcp/tools.py:1150:import:resolve_meeting_placement'
E         Extra items in the right set:
E         'holdspeak/mcp/tools.py:1163:import:resolve_meeting_placement'
E         Use -v to get more diff

tests/unit/test_phase143_routing_authority_census.py:366: AssertionError
__________ test_phase143_every_product_runner_entrance_has_one_owner ___________
[gw6] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

    def test_phase143_every_product_runner_entrance_has_one_owner() -> None:
        every = set(_runner_entrances())
        pinned = set(OPERATION_CONTRACT_VARIABLE_SITES)
>       assert pinned <= every, (
            "a pinned operation-contract site moved or is gone; re-read it and "
            f"re-anchor: stale={sorted(pinned - every)}"
        )
E       AssertionError: a pinned operation-contract site moved or is gone; re-read it and re-anchor: stale=['holdspeak/mcp/tools.py:662|_primitive_list|call', 'holdspeak/mcp/tools.py:668|_primitive_get|call']
E       assert {'holdspeak/m...ceipted|call'} <= {'holdspeak/k...ed|call', ...}
E         
E         Extra items in the left set:
E         'holdspeak/mcp/tools.py:668|_primitive_get|call'
E         'holdspeak/mcp/tools.py:662|_primitive_list|call'

tests/unit/test_phase143_inference_capability_census.py:675: AssertionError
______________ test_phase143_shared_helpers_have_semantic_callers ______________
[gw6] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

    def test_phase143_shared_helpers_have_semantic_callers() -> None:
        live = set(_semantic_helper_calls())
>       assert live == set(SEMANTIC_HELPER_CALLERS), (
            "shared Ask/Recipe helper callers changed; classify the public semantic "
            "operation rather than assigning the helper one false capability.\n"
            f"unregistered={sorted(live - set(SEMANTIC_HELPER_CALLERS))}\n"
            f"stale={sorted(set(SEMANTIC_HELPER_CALLERS) - live)}"
        )
E       AssertionError: shared Ask/Recipe helper callers changed; classify the public semantic operation rather than assigning the helper one false capability.
E         unregistered=['holdspeak/mcp/tools.py:1016|dispatch|run']
E         stale=['holdspeak/mcp/tools.py:1029|dispatch|run']
E       assert {'holdspeak/m...dispatch|ask'} == {'holdspeak/m...dispatch|ask'}
E         
E         Extra items in the left set:
E         'holdspeak/mcp/tools.py:1016|dispatch|run'
E         Extra items in the right set:
E         'holdspeak/mcp/tools.py:1029|dispatch|run'
E         Use -v to get more diff

tests/unit/test_phase143_inference_capability_census.py:695: AssertionError
____________________________ test_shade_quiet_1440 _____________________________
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw5/test_shade_quiet_14400')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x135bb3380>

    @pytest.mark.timeout(120)
    def test_shade_quiet_1440(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
>       _run_quiet_rig(tmp_path, monkeypatch, 1440)

tests/e2e/test_hs171_shade_glass.py:410: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw5/test_shade_quiet_14400')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x135bb3380>
width = 1440

    def _run_quiet_rig(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int
    ) -> None:
        """No Room items but a brief exists: PROJECTS absent, BRIEF present, badge absent."""
        _ensure_build()
        server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
        errors: list[str] = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": width, "height": 900})
                page.on("pageerror", lambda e: errors.append(str(e)))
    
                # Init desk -- no project seeding, but seed a brief
                page.goto(f"{url}/?token={TOKEN}", wait_until="load")
                _api(page, "POST", "/api/desk/seed", token=TOKEN)
                _api(page, "PUT", "/api/setup/onboarding",
                     {"disposition": "completed"}, token=TOKEN)
    
                _seed_brief()
    
                page.reload(wait_until="load")
                _normal_chair(page)
                _settle(page)
    
                # Open the shade
                _open_shade(page)
    
                # ── PROJECTS section absent (no Room has items) ──
                projects_section = page.get_by_test_id("shade-projects")
                assert projects_section.count() == 0, \
                    "PROJECTS section should be absent when no Room has items"
    
                # ── BRIEF section present ──
                brief_section = page.get_by_test_id("shade-brief")
>               assert brief_section.count() == 1, \
                    "BRIEF section should be present when a brief exists"
E                   AssertionError: BRIEF section should be present when a brief exists
E                   assert 0 == 1
E                    +  where 0 = count()
E                    +    where count = <Locator frame=<Frame name= url='http://127.0.0.1:63691/'> selector='internal:testid=[data-testid="shade-brief"s]'>.count

tests/e2e/test_hs171_shade_glass.py:329: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__________ TestOneDelete.test_a_resize_that_changes_the_face_commits ___________
[gw3] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x10e084ff0>

    @pytest.mark.e2e
    def test_a_resize_that_changes_the_face_commits(self) -> None:
        """MISSED 2: the face is the one the owner SEES. 393 opens the list;
        widening to 1440 resolves the spatial Floor: the pending delete commits."""
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, 393, ["Resize me"])
            try:
                _to_face(page, "list", 393)
                _row_menu_delete(page, "Resize me")
>               _readable_receipt(page, "Removed Resize me", 5_000)

tests/e2e/test_philo8_one_delete_glass.py:996: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:58: in _readable_receipt
    return _readable_now(page, want, timeout_ms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/e2e/test_philo7_delete_receipt_glass.py:70: in _readable_receipt
    page.wait_for_function(
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x148170550>
cb = <function Channel.send.<locals>.<lambda> at 0x14d3cc9a0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestDeleteReceiptGlass.test_the_delete_receipt_is_readable_in_the_viewport[1440] _
[gw1] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo7_delete_receipt_glass.TestDeleteReceiptGlass object at 0x10e30f890>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_delete_receipt_is_readable_in_the_viewport(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": width, "height": 900})
                errors: list[str] = []
                page.on("pageerror", lambda err: errors.append(str(err)))
                page.goto(f"{self.base}/?token={TOKEN}", wait_until="load")
                created = _api(page, "POST", "/api/decisions",
                               {"title": "Glass withdrawn decision", "status": "accepted"}, token=TOKEN)
                decision_id = created["decision"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
    
                # To the Floor; at 393 the Floor opens as a list, so switch to the spatial view.
                page.locator("[data-testid=chair-floor-toggle]").click()
                if width <= 720:
                    page.locator("[aria-controls=desk-tool-shelf]").click()
                    page.locator("[aria-controls=desk-palette-listbox]").fill("Spatial view")
                    page.locator("[id='desk-palette-option-desk.toggle-view']").click()
                row = page.locator(f"[data-obj-id='decision:{decision_id}']")
                row.wait_for(state="attached", timeout=15_000)
                row.focus()
                page.keyboard.press("Shift+Enter")
                # An in-page clock: when 'Removal committed' first shows and when it goes.
                page.evaluate("""() => {
                  window.__committedFirst = null; window.__committedGone = null;
                  const iv = setInterval(() => {
                    const text = document.querySelector('.undo-receipt')?.innerText || '';
                    const now = performance.now();
                    if (text.includes('Removal committed') && window.__committedFirst === null) window.__committedFirst = now;
                    if (!text && window.__committedFirst !== null) { window.__committedGone = now; clearInterval(iv); }
                  }, 50);
                }""")
                page.keyboard.press("Delete")
    
                pending = _readable_receipt(page, "Removed", 5_000)
                page.screenshot(path=str(SHOTS / f"1-pending-{width}.png"))
>               committed = _readable_receipt(page, "Removal committed", 15_000)
                            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/e2e/test_philo7_delete_receipt_glass.py:139: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

page = <Page url='http://127.0.0.1:65262/'>, want = 'Removal committed'
timeout_ms = 15000

    def _readable_receipt(page: Any, want: str, timeout_ms: int) -> dict[str, Any]:
        """Wait until the receipt reads ``want``; then it must be readable and uncovered."""
        page.wait_for_function(
            "(w) => (document.querySelector('.undo-receipt')?.innerText || '').includes(w)",
            arg=want,
            timeout=timeout_ms,
        )
        probe = page.locator(".undo-receipt").first.evaluate(_PROBE_JS)
        assert want in probe["text"], probe
>       assert probe["visible"] and probe["inViewport"], f"{want!r}: not in the viewport: {probe['rect']}"
E       AssertionError: 'Removal committed': not in the viewport: {'x': 0, 'y': 0, 'w': 0, 'h': 0}
E       assert (False)

tests/e2e/test_philo7_delete_receipt_glass.py:77: AssertionError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_______ test_a_follow_up_after_the_window_is_blocked[1440-before_guard] ________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw2/test_a_follow_up_after_the_win0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x14309d080>
width = 1440, mode = 'before_guard'

    @pytest.mark.e2e
    @pytest.mark.timeout(240)
    @pytest.mark.parametrize("mode", ["before_guard", "click_wait"])
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_follow_up_after_the_window_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                      width: int, mode: str) -> None:
        atlas = json.loads(ATLAS8.read_text())
        case = next(c for c in atlas["cases"] if c["id"] == CASE)
        if os.environ.get("PHILO8_GUARD_RED"):
            for step in case["trigger"]["then"]:
                step.pop("requires", None)
        atlas["cases"] = [case]
        path = tmp_path / "atlas-one.json"
        path.write_text(json.dumps(atlas))
    
        real = gw._ui_step
        state = {"delayed": False, "still": False}
    
        def late(page, step, hub=None):
            if page is not None and not state["still"]:
                # A GPU-less runner (CI's macos-14 VM) draws the Floor's
                # every-frame atmosphere in SwiftShader; at 1440 x dpr 2 a frame
                # takes over a second and the 3 s wait for the pending receipt
                # ends first. The product's still mode (reduced motion,
                # gl/atmosphereRuntime.ts:71) stops that loop; the delete, the
                # window and the guard run the same code.
                state["still"] = True
                page.emulate_media(reduced_motion="reduce")
            if (step.get("selector") == TOGGLE and not state["delayed"]
                    and page is not None and page.locator(".undo-receipt").count()):
                state["delayed"] = True
                if mode == "before_guard":
                    page.wait_for_timeout(PAUSE_MS)
                else:  # the target is not actionable for 8.5 s: the wait is inside delivery
                    page.evaluate(_DISABLE_JS, [TOGGLE, PAUSE_MS])
            return real(page, step, hub)
    
        monkeypatch.setattr(gw, "_ui_step", late)
        record = gw.run_case(path, CASE, brain="muaddib", viewport=width, out=tmp_path / "runs",
                             engine="none")
        notes = " | ".join(record.get("notes", []))
        print(f"{width} {mode}: verdict {record['verdict']}; delayed {state['delayed']}; {notes[:420]}")
>       assert state["delayed"], "the delay was never injected (the receipt never showed)"
E       AssertionError: the delay was never injected (the receipt never showed)
E       assert False

tests/e2e/test_philo8_03_then_guard.py:93: AssertionError
----------------------------- Captured stdout call -----------------------------
1440 before_guard: verdict blocked; delayed False; BLOCKED: ui step wait_for on '.desk-world-a11y' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-world-a11y").first

________ test_a_follow_up_after_the_window_is_blocked[1440-click_wait] _________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw2/test_a_follow_up_after_the_win1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x14455eac0>
width = 1440, mode = 'click_wait'

    @pytest.mark.e2e
    @pytest.mark.timeout(240)
    @pytest.mark.parametrize("mode", ["before_guard", "click_wait"])
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_follow_up_after_the_window_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                      width: int, mode: str) -> None:
        atlas = json.loads(ATLAS8.read_text())
        case = next(c for c in atlas["cases"] if c["id"] == CASE)
        if os.environ.get("PHILO8_GUARD_RED"):
            for step in case["trigger"]["then"]:
                step.pop("requires", None)
        atlas["cases"] = [case]
        path = tmp_path / "atlas-one.json"
        path.write_text(json.dumps(atlas))
    
        real = gw._ui_step
        state = {"delayed": False, "still": False}
    
        def late(page, step, hub=None):
            if page is not None and not state["still"]:
                # A GPU-less runner (CI's macos-14 VM) draws the Floor's
                # every-frame atmosphere in SwiftShader; at 1440 x dpr 2 a frame
                # takes over a second and the 3 s wait for the pending receipt
                # ends first. The product's still mode (reduced motion,
                # gl/atmosphereRuntime.ts:71) stops that loop; the delete, the
                # window and the guard run the same code.
                state["still"] = True
                page.emulate_media(reduced_motion="reduce")
            if (step.get("selector") == TOGGLE and not state["delayed"]
                    and page is not None and page.locator(".undo-receipt").count()):
                state["delayed"] = True
                if mode == "before_guard":
                    page.wait_for_timeout(PAUSE_MS)
                else:  # the target is not actionable for 8.5 s: the wait is inside delivery
                    page.evaluate(_DISABLE_JS, [TOGGLE, PAUSE_MS])
            return real(page, step, hub)
    
        monkeypatch.setattr(gw, "_ui_step", late)
        record = gw.run_case(path, CASE, brain="muaddib", viewport=width, out=tmp_path / "runs",
                             engine="none")
        notes = " | ".join(record.get("notes", []))
        print(f"{width} {mode}: verdict {record['verdict']}; delayed {state['delayed']}; {notes[:420]}")
>       assert state["delayed"], "the delay was never injected (the receipt never showed)"
E       AssertionError: the delay was never injected (the receipt never showed)
E       assert False

tests/e2e/test_philo8_03_then_guard.py:93: AssertionError
----------------------------- Captured stdout call -----------------------------
1440 click_wait: verdict blocked; delayed False; BLOCKED: ui step wait_for on '.desk-world-a11y' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-world-a11y").first

________ test_a_follow_up_after_the_window_is_blocked[393-before_guard] ________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw2/test_a_follow_up_after_the_win2')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x144938f30>
width = 393, mode = 'before_guard'

    @pytest.mark.e2e
    @pytest.mark.timeout(240)
    @pytest.mark.parametrize("mode", ["before_guard", "click_wait"])
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_follow_up_after_the_window_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                      width: int, mode: str) -> None:
        atlas = json.loads(ATLAS8.read_text())
        case = next(c for c in atlas["cases"] if c["id"] == CASE)
        if os.environ.get("PHILO8_GUARD_RED"):
            for step in case["trigger"]["then"]:
                step.pop("requires", None)
        atlas["cases"] = [case]
        path = tmp_path / "atlas-one.json"
        path.write_text(json.dumps(atlas))
    
        real = gw._ui_step
        state = {"delayed": False, "still": False}
    
        def late(page, step, hub=None):
            if page is not None and not state["still"]:
                # A GPU-less runner (CI's macos-14 VM) draws the Floor's
                # every-frame atmosphere in SwiftShader; at 1440 x dpr 2 a frame
                # takes over a second and the 3 s wait for the pending receipt
                # ends first. The product's still mode (reduced motion,
                # gl/atmosphereRuntime.ts:71) stops that loop; the delete, the
                # window and the guard run the same code.
                state["still"] = True
                page.emulate_media(reduced_motion="reduce")
            if (step.get("selector") == TOGGLE and not state["delayed"]
                    and page is not None and page.locator(".undo-receipt").count()):
                state["delayed"] = True
                if mode == "before_guard":
                    page.wait_for_timeout(PAUSE_MS)
                else:  # the target is not actionable for 8.5 s: the wait is inside delivery
                    page.evaluate(_DISABLE_JS, [TOGGLE, PAUSE_MS])
            return real(page, step, hub)
    
        monkeypatch.setattr(gw, "_ui_step", late)
        record = gw.run_case(path, CASE, brain="muaddib", viewport=width, out=tmp_path / "runs",
                             engine="none")
        notes = " | ".join(record.get("notes", []))
        print(f"{width} {mode}: verdict {record['verdict']}; delayed {state['delayed']}; {notes[:420]}")
>       assert state["delayed"], "the delay was never injected (the receipt never showed)"
E       AssertionError: the delay was never injected (the receipt never showed)
E       assert False

tests/e2e/test_philo8_03_then_guard.py:93: AssertionError
----------------------------- Captured stdout call -----------------------------
393 before_guard: verdict blocked; delayed False; BLOCKED: ui step wait_for on '.desk-world-a11y' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-world-a11y").first

_____________________________ test_speak_loop_1440 _____________________________
[gw6] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw6/test_speak_loop_14400')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x14f2a6cf0>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_1440(tmp_path, monkeypatch):
        """The full loop at 1440, one session, no restart."""
>       _run(tmp_path, monkeypatch, 1440, 900)

tests/e2e/test_hs176_loop_glass.py:365: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:354: in _run
    _loop(page, width)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

page = <Page url='http://127.0.0.1:50929/'>, width = 1440

    def _loop(page: Any, width: int) -> None:
        _dry_run_on(page)
    
        # ── 1. land, judge, teach ──────────────────────────────────────
        result = _land(page, HEARD)
        result.get_by_role("button", name="Wrong").click()
        teach = page.locator(".speak-teach")
        teach.wait_for(timeout=8000)
        said = teach.get_by_role("textbox", name="What you said")
        assert said.input_value() == HEARD, said.input_value()
        said.fill(SAID)
        page.get_by_role("button", name="Teach correction").click()
        receipt = page.locator(".speak-receipt")
        receipt.wait_for(timeout=8000)
        assert "TAUGHT" in receipt.inner_text(), receipt.inner_text()
    
        # ── 2. speak it again, in the SAME session: the rule fires ─────
        result = _land(page, AGAIN)
        landed = result.locator(".speak-result-text").inner_text()
>       assert landed == APPLIED_TEXT, landed
E       AssertionError: Ship the queue for platform on schedule
E       assert 'Ship the que...m on schedule' == 'Ship the Q4 ...rm in October'
E         
E         - Ship the Q4 platform in October
E         + Ship the queue for platform on schedule

tests/e2e/test_hs176_loop_glass.py:276: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
_____________________________ test_speak_loop_393 ______________________________
[gw6] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw6/test_speak_loop_3930')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1512d7930>

    @pytest.mark.e2e
    @pytest.mark.requires_meeting
    def test_speak_loop_393(tmp_path, monkeypatch):
        """The same loop at 393: the Learned row wraps, nothing overflows."""
>       _run(tmp_path, monkeypatch, 393, 852)

tests/e2e/test_hs176_loop_glass.py:372: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_hs176_loop_glass.py:354: in _run
    _loop(page, width)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

page = <Page url='http://127.0.0.1:51034/'>, width = 393

    def _loop(page: Any, width: int) -> None:
        _dry_run_on(page)
    
        # ── 1. land, judge, teach ──────────────────────────────────────
        result = _land(page, HEARD)
        result.get_by_role("button", name="Wrong").click()
        teach = page.locator(".speak-teach")
        teach.wait_for(timeout=8000)
        said = teach.get_by_role("textbox", name="What you said")
        assert said.input_value() == HEARD, said.input_value()
        said.fill(SAID)
        page.get_by_role("button", name="Teach correction").click()
        receipt = page.locator(".speak-receipt")
        receipt.wait_for(timeout=8000)
        assert "TAUGHT" in receipt.inner_text(), receipt.inner_text()
    
        # ── 2. speak it again, in the SAME session: the rule fires ─────
        result = _land(page, AGAIN)
        landed = result.locator(".speak-result-text").inner_text()
>       assert landed == APPLIED_TEXT, landed
E       AssertionError: Ship the queue for platform on schedule
E       assert 'Ship the que...m on schedule' == 'Ship the Q4 ...rm in October'
E         
E         - Ship the Q4 platform in October
E         + Ship the queue for platform on schedule

tests/e2e/test_hs176_loop_glass.py:276: AssertionError
------------------------------ Captured log call -------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
WARNING  holdspeak.dictation.stages.intent_router:intent_router.py:179 intent-router classify failed: holdspeak.dictation-intent-classify:failed
_________ test_a_follow_up_after_the_window_is_blocked[393-click_wait] _________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/pytest/popen-gw2/test_a_follow_up_after_the_win3')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x1449394e0>
width = 393, mode = 'click_wait'

    @pytest.mark.e2e
    @pytest.mark.timeout(240)
    @pytest.mark.parametrize("mode", ["before_guard", "click_wait"])
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_follow_up_after_the_window_is_blocked(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                      width: int, mode: str) -> None:
        atlas = json.loads(ATLAS8.read_text())
        case = next(c for c in atlas["cases"] if c["id"] == CASE)
        if os.environ.get("PHILO8_GUARD_RED"):
            for step in case["trigger"]["then"]:
                step.pop("requires", None)
        atlas["cases"] = [case]
        path = tmp_path / "atlas-one.json"
        path.write_text(json.dumps(atlas))
    
        real = gw._ui_step
        state = {"delayed": False, "still": False}
    
        def late(page, step, hub=None):
            if page is not None and not state["still"]:
                # A GPU-less runner (CI's macos-14 VM) draws the Floor's
                # every-frame atmosphere in SwiftShader; at 1440 x dpr 2 a frame
                # takes over a second and the 3 s wait for the pending receipt
                # ends first. The product's still mode (reduced motion,
                # gl/atmosphereRuntime.ts:71) stops that loop; the delete, the
                # window and the guard run the same code.
                state["still"] = True
                page.emulate_media(reduced_motion="reduce")
            if (step.get("selector") == TOGGLE and not state["delayed"]
                    and page is not None and page.locator(".undo-receipt").count()):
                state["delayed"] = True
                if mode == "before_guard":
                    page.wait_for_timeout(PAUSE_MS)
                else:  # the target is not actionable for 8.5 s: the wait is inside delivery
                    page.evaluate(_DISABLE_JS, [TOGGLE, PAUSE_MS])
            return real(page, step, hub)
    
        monkeypatch.setattr(gw, "_ui_step", late)
        record = gw.run_case(path, CASE, brain="muaddib", viewport=width, out=tmp_path / "runs",
                             engine="none")
        notes = " | ".join(record.get("notes", []))
        print(f"{width} {mode}: verdict {record['verdict']}; delayed {state['delayed']}; {notes[:420]}")
>       assert state["delayed"], "the delay was never injected (the receipt never showed)"
E       AssertionError: the delay was never injected (the receipt never showed)
E       assert False

tests/e2e/test_philo8_03_then_guard.py:93: AssertionError
----------------------------- Captured stdout call -----------------------------
393 click_wait: verdict blocked; delayed False; BLOCKED: ui step wait_for on '.desk-world-a11y' failed: TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
Call log:
  - waiting for locator(".desk-world-a11y").first

_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[1440] _____
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x1118f0690>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_list_row_menu_delete_removes_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["List delete decision"])
            try:
                _to_face(page, "list", width)
>               box = _row_menu_delete(page, "List delete decision")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/e2e/test_philo8_one_delete_glass.py:234: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:124: in _row_menu_delete
    item.wait_for(timeout=5_000)
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x12d40d050>
cb = <function Channel.send.<locals>.<lambda> at 0x1484205e0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 5000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-world-menu [role=menuitem]").filter(has_text="Delete").last to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_____ TestOneDelete.test_the_list_row_menu_delete_removes_the_object[393] ______
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x1118f0550>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_list_row_menu_delete_removes_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["List delete decision"])
            try:
                _to_face(page, "list", width)
                box = _row_menu_delete(page, "List delete decision")
                print(f"{width}: the row menu's Delete row {box}")  # FINDING S2, measured
>               _readable_receipt(page, "Removed", 5_000)

tests/e2e/test_philo8_one_delete_glass.py:236: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:58: in _readable_receipt
    return _readable_now(page, want, timeout_ms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/e2e/test_philo7_delete_receipt_glass.py:70: in _readable_receipt
    page.wait_for_function(
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x13cef0d50>
cb = <function Channel.send.<locals>.<lambda> at 0x1498dc2c0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
----------------------------- Captured stdout call -----------------------------
393: the row menu's Delete row {'top': 797, 'bottom': 841, 'vh': 852}
_ TestOneDelete.test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440] _
[gw11] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x111ad4870>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_failed_refresh_keeps_the_pending_delete_and_its_undo(self, width: int) -> None:
        """P1-b: the setup read fails (503) while "Undo" shows. The desk shows
        its failure screen; the pending delete must NOT commit early (no DELETE
        before the 8 s window ends), and after Retry the receipt is back."""
        import time
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Refresh pending"])
            try:
                _to_face(page, "list", width)
                stamps: list[float] = []
                page.on("request", lambda req: stamps.append(time.monotonic()) if req.method == "DELETE" else None)
                _name_button(page, "Refresh pending").scroll_into_view_if_needed()
                t0 = time.monotonic()
                _row_menu_delete(page, "Refresh pending")
                fail = lambda route: route.fulfill(status=503, content_type="application/json", body="{}")
                page.route("**/api/setup/status", fail)
                _palette(page, "Refresh from hub", "desk.refresh")
                page.locator("[role=alert]").wait_for(timeout=10_000)
                shown = time.monotonic() - t0
                status_during = _status(page, decision_id) if shown < 7.0 else None
                page.unroute("**/api/setup/status", fail)
                page.locator("[role=alert]").get_by_role("button", name="Retry").click()
>               page.locator(".desk-listmode").wait_for(timeout=10_000)

tests/e2e/test_philo8_one_delete_glass.py:583: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x12fbd5450>
cb = <function Channel.send.<locals>.<lambda> at 0x144da6520>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-listmode") to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393] _
[gw11] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x111ad4820>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_failed_refresh_keeps_the_pending_delete_and_its_undo(self, width: int) -> None:
        """P1-b: the setup read fails (503) while "Undo" shows. The desk shows
        its failure screen; the pending delete must NOT commit early (no DELETE
        before the 8 s window ends), and after Retry the receipt is back."""
        import time
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Refresh pending"])
            try:
                _to_face(page, "list", width)
                stamps: list[float] = []
                page.on("request", lambda req: stamps.append(time.monotonic()) if req.method == "DELETE" else None)
                _name_button(page, "Refresh pending").scroll_into_view_if_needed()
                t0 = time.monotonic()
                _row_menu_delete(page, "Refresh pending")
                fail = lambda route: route.fulfill(status=503, content_type="application/json", body="{}")
                page.route("**/api/setup/status", fail)
                _palette(page, "Refresh from hub", "desk.refresh")
                page.locator("[role=alert]").wait_for(timeout=10_000)
                shown = time.monotonic() - t0
                status_during = _status(page, decision_id) if shown < 7.0 else None
                page.unroute("**/api/setup/status", fail)
                page.locator("[role=alert]").get_by_role("button", name="Retry").click()
>               page.locator(".desk-listmode").wait_for(timeout=10_000)

tests/e2e/test_philo8_one_delete_glass.py:583: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x12e63fc50>
cb = <function Channel.send.<locals>.<lambda> at 0x130393c40>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-listmode") to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestOneDelete.test_the_list_palette_delete_removes_the_selected_object[393] __
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x1118f8af0>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_list_palette_delete_removes_the_selected_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Palette delete decision"])
            try:
                _to_face(page, "list", width)
                _select(page, "list", decision_id, "Palette delete decision")
                _palette(page, "Delete", "object.delete")
>               _readable_receipt(page, "Removed", 5_000)

tests/e2e/test_philo8_one_delete_glass.py:274: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:58: in _readable_receipt
    return _readable_now(page, want, timeout_ms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/e2e/test_philo7_delete_receipt_glass.py:70: in _readable_receipt
    page.wait_for_function(
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x13b7b5b50>
cb = <function Channel.send.<locals>.<lambda> at 0x14ef66340>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_________ TestOneDelete.test_the_foot_never_covers_the_last_rows[393] __________
[gw11] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x111ad48c0>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_the_foot_never_covers_the_last_rows(self, width: int) -> None:
        """P2: with the receipt and the selection bar in the foot, the end of a
        long list scrolls clear of the foot; the last rows own their centres."""
        from playwright.sync_api import sync_playwright
    
        titles = [f"Last row {n:02d}" for n in range(1, 21)]
        with sync_playwright() as pw:
            browser, page, ids, errors = self._open(pw, width, titles)
            try:
                _to_face(page, "list", width)
                page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
                _select(page, "list", ids[-2], titles[-2])
                _row_menu_delete(page, titles[-1])
>               _readable_receipt(page, "Removed", 5_000)

tests/e2e/test_philo8_one_delete_glass.py:614: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:58: in _readable_receipt
    return _readable_now(page, want, timeout_ms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/e2e/test_philo7_delete_receipt_glass.py:70: in _readable_receipt
    page.wait_for_function(
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x12e63fb50>
cb = <function Channel.send.<locals>.<lambda> at 0x13111b2e0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___________________ test_receipt_verbs_own_their_areas[1440] ___________________
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

hub = <graph_walk_receipt_hits.Hub object at 0x14f140980>, width = 1440

    @pytest.mark.parametrize("width", [1440, 393])
    def test_receipt_verbs_own_their_areas(hub, width: int) -> None:
        failures: list[str] = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(viewport=VIEWPORTS[width])
            page.emulate_media(reduced_motion="reduce")
            page.goto(f"{hub.url}/?token={hub.token}")
            try:
                page.get_by_role("button", name="Continue later").click(timeout=4000)
            except Exception:
                pass
>           page.locator("[aria-controls=desk-tool-shelf]").wait_for(timeout=15000)

tests/e2e/test_philo3_01_receipt_hits.py:232: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x145456350>
cb = <function Channel.send.<locals>.<lambda> at 0x14de39580>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded.
E           Call log:
E             - waiting for locator("[aria-controls=desk-tool-shelf]") to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
__________ TestOneDelete.test_undo_on_the_list_keeps_the_object[393] ___________
[gw2] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x111920d50>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_undo_on_the_list_keeps_the_object(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Undo list decision"])
            try:
                _to_face(page, "list", width)
                _row_menu_delete(page, "Undo list decision")
                _readable_receipt(page, "Removed", 5_000)
>               page.locator(".undo-receipt-btn").click()

tests/e2e/test_philo8_one_delete_glass.py:292: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:15637: in click
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:162: in click
    return await self._frame._click(self._selector, strict=True, **params)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:566: in _click
    await self._channel.send("click", self._timeout, locals_to_params(locals()))
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x14efe3350>
cb = <function Channel.send.<locals>.<lambda> at 0x151a49300>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded.
E           Call log:
E             - waiting for locator(".undo-receipt-btn")
E               - locator resolved to <button type="button" class="desk-chip undo-receipt-btn">Undo</button>
E             - attempting click action
E               - waiting for element to be visible, enabled and stable
E               - element is visible, enabled and stable
E               - scrolling into view if needed
E               - done scrolling
E               - performing click action
E               - <html lang="en">…</html> intercepts pointer events
E             - retrying click action
E               - waiting for element to be visible, enabled and stable
E             - element was detached from the DOM, retrying

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestListRenameGlass.test_a_taken_name_shows_the_chip_on_the_floor[1440] ____
[gw1] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_01_list_rename_glass.TestListRenameGlass object at 0x10e349c70>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_taken_name_shows_the_chip_on_the_floor(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, puts = self._open(pw, width, "spatial")
            try:
>               _new_zone(page)

tests/e2e/test_philo8_01_list_rename_glass.py:205: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_01_list_rename_glass.py:82: in _new_zone
    with page.expect_response(
.venv/lib/python3.13/site-packages/playwright/_impl/_sync_base.py:85: in __exit__
    self._event.value
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._sync_base.EventInfo object at 0x148770c50>

    @property
    def value(self) -> T:
        while not self._future.done():
            self._sync_base._dispatcher_fiber.switch()
        asyncio._set_running_loop(self._sync_base._loop)
        exception = self._future.exception()
        if exception:
>           raise exception
E           playwright._impl._errors.TimeoutError: Timeout 15000ms exceeded while waiting for event "response"

.venv/lib/python3.13/site-packages/playwright/_impl/_sync_base.py:59: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
__ TestOneDelete.test_a_repeated_delete_never_offers_a_false_undo[floor-1440] __
[gw10] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x10e1dc4b0>
face = 'floor', width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    @pytest.mark.parametrize("face", ["list", "floor"])
    def test_a_repeated_delete_never_offers_a_false_undo(self, face: str, width: int) -> None:
        """P1-a: Delete the same object twice, then Undo. Never "Restored" with 404."""
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Repeat me"])
            try:
>               _to_face(page, face, width)

tests/e2e/test_philo8_one_delete_glass.py:484: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:89: in _to_face
    page.locator(".desk-world-a11y").wait_for(state="attached", timeout=15_000)
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x15ddbeb50>
cb = <function Channel.send.<locals>.<lambda> at 0x16a5ae980>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-world-a11y")
E               - locator resolved to visible <div class="desk-world-a11y">…</div>

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
INFO     holdspeak.db.reconcile:reconcile.py:740 Reconcile: created tables ['action_items', 'activity_annotations', 'activity_domain_rules', 'activity_enrichment_connectors', 'activity_import_checkpoints', 'activity_meeting_candidates', 'activity_nudge_dismissals', 'activity_privacy_settings', 'activity_project_rules', 'activity_records', 'actuator_proposal_audit', 'actuator_proposals', 'artifact_sources', 'artifacts', 'artifacts_memory_fts', 'artifacts_memory_fts_config', 'artifacts_memory_fts_content', 'artifacts_memory_fts_data', 'artifacts_memory_fts_docsize', 'artifacts_memory_fts_idx', 'ask_results', 'authority_grant_uses', 'authority_grants', 'bookmarks', 'cadence_evidence_refs', 'cadence_loops', 'cadence_next_actions', 'cadence_nudges', 'cadence_policies', 'calendar_event_link_suppressions', 'calendar_event_projects', 'calendar_events', 'capability_attempts', 'capability_invocations', 'chains', 'channel_destinations', 'channel_sends', 'connector_reactions', 'connector_runs', 'connector_watches', 'constitutional_context', 'constitutional_context_history', 'context_dependents', 'context_promotion_suppressions', 'context_promotions', 'decision_commitments', 'decision_record_revisions', 'decision_record_sources', 'decision_record_work', 'decision_records', 'decisions', 'decisions_memory_fts', 'decisions_memory_fts_config', 'decisions_memory_fts_content', 'decisions_memory_fts_data', 'decisions_memory_fts_docsize', 'decisions_memory_fts_idx', 'delivery_command_receipts', 'deployment_revisions', 'desk_decisions', 'desk_projection_state', 'desktop_type_receipts', 'dictation_corrections', 'dictation_journal', 'directories', 'directory_memberships', 'first_value_attempts', 'first_value_events', 'follow_through_proposals', 'front_door_apply_plans', 'gate_audit', 'gate_proposals', 'inference_adoption_attempt_results', 'inference_adoption_composites', 'inference_adoption_material_snapshots', 'inference_adoption_route_evidence', 'inference_assignment_commands', 'inference_assignment_heads', 'inference_assignment_migrations', 'inference_assignment_revisions', 'inference_assignments', 'inference_deployments', 'inference_model_acquisitions', 'inference_model_artifacts', 'inference_operation_route_attempt_budget_evidence', 'inference_operation_route_request_plan_commands', 'inference_operation_route_request_plan_entries', 'inference_operation_route_request_plans', 'inference_parent_route_bundle_members', 'inference_parent_route_bundles', 'inference_parent_stop_handoff_executions', 'inference_parent_stop_handoff_settlements', 'inference_parent_stop_handoffs', 'inference_route_attempts', 'inference_route_execution_commands', 'inference_route_execution_skips', 'inference_route_execution_transitions', 'inference_route_executions', 'inference_route_plan_authority_evidence', 'inference_route_plan_commands', 'inference_route_plan_entries', 'inference_route_plan_preflight_evidence', 'inference_route_plan_principal_evidence', 'inference_route_plans', 'inference_runtime_leases', 'intel_job_attempts', 'intel_jobs', 'intel_snapshots', 'intent_window_scores', 'intent_windows', 'interview_events', 'interview_sessions', 'kbs', 'kernel_desk_delegations', 'kernel_inference_receipt_attestations', 'kernel_journal', 'kernel_meta', 'kernel_operations', 'kernel_parent_checkpoints', 'kernel_parent_runs', 'kernel_project_delegations', 'kernel_projection_stages', 'kernel_receipts', 'kernel_schedule_delegations', 'kernel_schedule_ticks', 'knowledge_memberships', 'meeting_projects', 'meeting_sync_conflicts', 'meeting_tags', 'meetings', 'mesh_relay_jobs', 'mesh_worker_reservations', 'mesh_workers', 'milestones', 'model_library_provider_commands', 'model_manifests', 'model_profile_binding_heads', 'model_profile_binding_revisions', 'model_profile_readiness_observations', 'model_profile_revisions', 'model_profile_tombstones', 'monday_brief_item_shelf', 'monday_brief_items', 'monday_briefs', 'needs_you_last_known', 'notes', 'notes_memory_fts', 'notes_memory_fts_config', 'notes_memory_fts_content', 'notes_memory_fts_data', 'notes_memory_fts_docsize', 'notes_memory_fts_idx', 'onboarding_state', 'pipeline_events', 'plugin_run_jobs', 'plugin_runs', 'preparation_carries', 'profiles', 'project_ask_tasks', 'project_briefs', 'project_changes', 'project_commands', 'project_detection_log', 'project_evidence_links', 'project_items', 'project_observations', 'project_proposals', 'project_resources', 'project_reviews', 'project_setup_answers', 'project_setup_sessions', 'project_sources', 'project_update_deliveries', 'project_updates', 'projects', 'reaction_event_projections', 'recipe_chat_results', 'recipe_results', 'recipes', 'refinement_aggregate_commands', 'refinement_answer_continue_commands', 'refinement_attachment_leaves', 'refinement_attachment_revisions', 'refinement_attachment_visible', 'refinement_completion_receipts', 'refinement_context_actions', 'refinement_default_context_actions', 'refinement_default_context_applications', 'refinement_default_context_current', 'refinement_default_context_revisions', 'refinement_hosts', 'refinement_invocation_attempts', 'refinement_invocations', 'refinement_lifecycle_revisions', 'refinement_resume_sequence', 'refinement_retry_plans', 'refinement_review_actions', 'refinement_review_results', 'refinement_thought_sync_tombstones', 'refinement_thoughts', 'refinement_working_revisions', 'refinement_workspace_identity', 'remote_dictation_deliveries', 'resourceful_dispatches', 'resourceful_policies', 'scheduled_recordings', 'schema_version', 'segments', 'segments_fts', 'segments_fts_config', 'segments_fts_data', 'segments_fts_docsize', 'segments_fts_idx', 'service_events', 'session_usage', 'skills', 'source_suggestions', 'speakers', 'sqlite_sequence', 'steering_audit', 'steward_commands', 'steward_policies', 'steward_runs', 'steward_steps', 'thread_message_parts', 'thread_messages', 'thread_messages_fts', 'thread_messages_fts_config', 'thread_messages_fts_data', 'thread_messages_fts_docsize', 'thread_messages_fts_idx', 'thread_refs', 'thread_tool_policy', 'threads', 'tool_turn_commands', 'tool_turn_effect_children', 'tool_turn_model_steps', 'tool_turn_tool_call_results', 'tool_turn_tool_calls', 'tool_turn_transitions', 'tool_turns', 'topics', 'turn_capability_leases', 'watch_effects', 'watch_evaluations', 'watch_provider_connections', 'watch_rules', 'watch_setup_proposals', 'work_attempt_events', 'work_attempts', 'workbench_items', 'workbench_runs', 'workbenches', 'workflows']
INFO     holdspeak.db.reconcile:reconcile.py:984 Decision backfill: artifacts=0, decisions=0, inserted=0, updated=0, unchanged=0, skipped=0
INFO     holdspeak.db.reconcile:reconcile.py:989 Memory index rebuild: decisions=0, artifacts=0, notes=0, total=0
INFO     holdspeak.db.reconcile:reconcile.py:793 Schema reconciled to version 79 (changed=True)
INFO     holdspeak.web_server:web_server.py:1321 Seeded 10 built-in skills
INFO     holdspeak.workbench_conductor:workbench_conductor.py:517 Workbench conductor started
INFO     holdspeak.scheduled_recording_conductor:scheduled_recording_conductor.py:130 Scheduled recording conductor started
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
DEBUG    holdspeak.web_server:web_server.py:1400 Meeting web server startup complete
INFO     holdspeak.web_server:web_server.py:456 Meeting web server started: http://127.0.0.1:53701
------------------------------ Captured log call -------------------------------
INFO     holdspeak.web.routes.system:ws.py:67 WebSocket connection attempt
INFO     holdspeak.web.routes.system:ws.py:70 WebSocket connected successfully
DEBUG    holdspeak.web_server:web_server.py:585 Broadcasting desk_changed to WebSocket clients
INFO     holdspeak.web.routes.system:ws.py:67 WebSocket connection attempt
INFO     holdspeak.web.routes.system:ws.py:70 WebSocket connected successfully
INFO     holdspeak.audio_devices:audio_devices.py:191 Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
INFO     holdspeak.audio_devices:audio_devices.py:191 Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
INFO     holdspeak.audio_devices:audio_devices.py:191 Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
---------------------------- Captured log teardown -----------------------------
INFO     holdspeak.web_server:web_server.py:490 Stopping meeting web server
INFO     holdspeak.calendar_ingest_conductor:calendar_ingest_conductor.py:234 Calendar ingest conductor stopped
INFO     holdspeak.workbench_conductor:workbench_conductor.py:523 Workbench conductor stopped
INFO     holdspeak.scheduled_recording_conductor:scheduled_recording_conductor.py:143 Scheduled recording conductor stopped
DEBUG    holdspeak.web_server:web_server.py:1443 Meeting web server shutdown complete
_ TestListRenameGlass.test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422] _
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_01_list_rename_glass.TestListRenameGlass object at 0x10fcba450>
width = 1440, face = 'spatial', failure = '422'

    @pytest.mark.e2e
    @pytest.mark.parametrize("failure", ["422", "network"])
    @pytest.mark.parametrize("face", ["list", "spatial"])
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_failed_save_shows_in_the_chip_slot(self, width: int, face: str, failure: str) -> None:
        # The ratified canvas, answer 2: a failed save in the same slot on BOTH
        # faces (the spatial leg: the Astra-role check on PR #673, C2).
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
>           browser, page, puts = self._open(pw, width, face)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/e2e/test_philo8_01_list_rename_glass.py:229: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_01_list_rename_glass.py:120: in _open
    _ensure_view(page, face)
tests/e2e/test_philo8_01_list_rename_glass.py:77: in _ensure_view
    page.locator(".desk-world").wait_for(timeout=T)
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x149bd3750>
cb = <function Channel.send.<locals>.<lambda> at 0x15126c9a0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-world") to be visible
E               - locator resolved to visible <div class="desk-world">…</div>

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestListRenameGlass.test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network] _
[gw5] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_01_list_rename_glass.TestListRenameGlass object at 0x10fcb34d0>
width = 1440, face = 'spatial', failure = 'network'

    @pytest.mark.e2e
    @pytest.mark.parametrize("failure", ["422", "network"])
    @pytest.mark.parametrize("face", ["list", "spatial"])
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_failed_save_shows_in_the_chip_slot(self, width: int, face: str, failure: str) -> None:
        # The ratified canvas, answer 2: a failed save in the same slot on BOTH
        # faces (the spatial leg: the Astra-role check on PR #673, C2).
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
>           browser, page, puts = self._open(pw, width, face)
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/e2e/test_philo8_01_list_rename_glass.py:229: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_01_list_rename_glass.py:120: in _open
    _ensure_view(page, face)
tests/e2e/test_philo8_01_list_rename_glass.py:77: in _ensure_view
    page.locator(".desk-world").wait_for(timeout=T)
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x145456150>
cb = <function Channel.send.<locals>.<lambda> at 0x151822de0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-world") to be visible
E               - locator resolved to visible <div class="desk-world">…</div>

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestOneDelete.test_a_repeated_delete_never_offers_a_false_undo[list-393] ___
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x10dfe19d0>
face = 'list', width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    @pytest.mark.parametrize("face", ["list", "floor"])
    def test_a_repeated_delete_never_offers_a_false_undo(self, face: str, width: int) -> None:
        """P1-a: Delete the same object twice, then Undo. Never "Restored" with 404."""
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, (decision_id,), errors = self._open(pw, width, ["Repeat me"])
            try:
                _to_face(page, face, width)
                if face == "list":
                    # Scroll once: a later right-click must not spend the window scrolling.
                    _name_button(page, "Repeat me").scroll_into_view_if_needed()
                for turn in range(2):
                    if turn:
                        # A probe only inside the first window: still pending.
                        now = page.evaluate("() => document.querySelector('.undo-receipt')?.innerText || ''")
                        assert "Removed Repeat me" in now, f"the second Delete came after the window: {now!r}"
                    if face == "list" and turn:
                        # The second press in one page call: real DOM events on the
                        # row (contextmenu, then the menu's Delete), no round trips.
                        pressed = page.evaluate(_ROW_MENU_DELETE_JS, "Repeat me")
                        assert pressed == "pressed", pressed
                    elif face == "list":
                        _row_menu_delete(page, "Repeat me")
                    else:
                        if not _askbar_count(page):
                            _select(page, face, decision_id, "Repeat me")
                        page.keyboard.press("Delete")
                    page.wait_for_function(
                        "() => (document.querySelector('.undo-receipt')?.innerText || '').includes('Removed Repeat me')",
                        timeout=5_000,
                    )
                # Undo in one page call (the window is 8 s; each Playwright round
                # trip under load costs about a second).
                clicked = page.evaluate(
                    "() => { const b = document.querySelector('.undo-receipt-btn'); if (b) b.click(); return !!b; }"
                )
                assert clicked, "the window ended before Undo"
>               _readable_receipt(page, "Restored Repeat me", 5_000)

tests/e2e/test_philo8_one_delete_glass.py:514: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:58: in _readable_receipt
    return _readable_now(page, want, timeout_ms)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/e2e/test_philo7_delete_receipt_glass.py:70: in _readable_receipt
    page.wait_for_function(
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:11595: in wait_for_function
    self._sync(
.venv/lib/python3.13/site-packages/playwright/_impl/_page.py:1110: in wait_for_function
    return await self._main_frame.wait_for_function(**locals_to_params(locals()))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:878: in wait_for_function
    await self._channel.send("waitForFunction", self._timeout, params)
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x148485f50>
cb = <function Channel.send.<locals>.<lambda> at 0x155286e80>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded.

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
_ TestListRenameGlass.test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440] _
[gw6] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_01_list_rename_glass.TestListRenameGlass object at 0x1121fe8d0>
width = 1440

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", WIDTHS)
    def test_a_refusal_after_the_field_closed_goes_to_the_write_receipt(self, width: int) -> None:
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
>           browser, page, puts = self._open(pw, width, "spatial")
                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/e2e/test_philo8_01_list_rename_glass.py:259: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_01_list_rename_glass.py:120: in _open
    _ensure_view(page, face)
tests/e2e/test_philo8_01_list_rename_glass.py:77: in _ensure_view
    page.locator(".desk-world").wait_for(timeout=T)
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x14fa74950>
cb = <function Channel.send.<locals>.<lambda> at 0x15501aa20>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-world") to be visible
E               - locator resolved to visible <div class="desk-world">…</div>

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
___ TestOneDelete.test_a_repeated_workbench_remove_never_offers_a_false_undo ___
[gw10] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x10e1dc870>

    @pytest.mark.e2e
    def test_a_repeated_workbench_remove_never_offers_a_false_undo(self) -> None:
        """P1-a, the Workbench window (the same hook)."""
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, 1440, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "WB Probe"}, token=TOKEN)["workbench"]["id"]
                item = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Repeat WB item"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
>               _to_face(page, "list", 1440)

tests/e2e/test_philo8_one_delete_glass.py:535: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/e2e/test_philo8_one_delete_glass.py:87: in _to_face
    page.locator(".desk-listmode").wait_for(timeout=15_000)
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x160a31d50>
cb = <function Channel.send.<locals>.<lambda> at 0x17f977560>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-listmode") to be visible
E               - locator resolved to visible <div class="desk-listmode">…</div>

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
INFO     holdspeak.db.reconcile:reconcile.py:740 Reconcile: created tables ['action_items', 'activity_annotations', 'activity_domain_rules', 'activity_enrichment_connectors', 'activity_import_checkpoints', 'activity_meeting_candidates', 'activity_nudge_dismissals', 'activity_privacy_settings', 'activity_project_rules', 'activity_records', 'actuator_proposal_audit', 'actuator_proposals', 'artifact_sources', 'artifacts', 'artifacts_memory_fts', 'artifacts_memory_fts_config', 'artifacts_memory_fts_content', 'artifacts_memory_fts_data', 'artifacts_memory_fts_docsize', 'artifacts_memory_fts_idx', 'ask_results', 'authority_grant_uses', 'authority_grants', 'bookmarks', 'cadence_evidence_refs', 'cadence_loops', 'cadence_next_actions', 'cadence_nudges', 'cadence_policies', 'calendar_event_link_suppressions', 'calendar_event_projects', 'calendar_events', 'capability_attempts', 'capability_invocations', 'chains', 'channel_destinations', 'channel_sends', 'connector_reactions', 'connector_runs', 'connector_watches', 'constitutional_context', 'constitutional_context_history', 'context_dependents', 'context_promotion_suppressions', 'context_promotions', 'decision_commitments', 'decision_record_revisions', 'decision_record_sources', 'decision_record_work', 'decision_records', 'decisions', 'decisions_memory_fts', 'decisions_memory_fts_config', 'decisions_memory_fts_content', 'decisions_memory_fts_data', 'decisions_memory_fts_docsize', 'decisions_memory_fts_idx', 'delivery_command_receipts', 'deployment_revisions', 'desk_decisions', 'desk_projection_state', 'desktop_type_receipts', 'dictation_corrections', 'dictation_journal', 'directories', 'directory_memberships', 'first_value_attempts', 'first_value_events', 'follow_through_proposals', 'front_door_apply_plans', 'gate_audit', 'gate_proposals', 'inference_adoption_attempt_results', 'inference_adoption_composites', 'inference_adoption_material_snapshots', 'inference_adoption_route_evidence', 'inference_assignment_commands', 'inference_assignment_heads', 'inference_assignment_migrations', 'inference_assignment_revisions', 'inference_assignments', 'inference_deployments', 'inference_model_acquisitions', 'inference_model_artifacts', 'inference_operation_route_attempt_budget_evidence', 'inference_operation_route_request_plan_commands', 'inference_operation_route_request_plan_entries', 'inference_operation_route_request_plans', 'inference_parent_route_bundle_members', 'inference_parent_route_bundles', 'inference_parent_stop_handoff_executions', 'inference_parent_stop_handoff_settlements', 'inference_parent_stop_handoffs', 'inference_route_attempts', 'inference_route_execution_commands', 'inference_route_execution_skips', 'inference_route_execution_transitions', 'inference_route_executions', 'inference_route_plan_authority_evidence', 'inference_route_plan_commands', 'inference_route_plan_entries', 'inference_route_plan_preflight_evidence', 'inference_route_plan_principal_evidence', 'inference_route_plans', 'inference_runtime_leases', 'intel_job_attempts', 'intel_jobs', 'intel_snapshots', 'intent_window_scores', 'intent_windows', 'interview_events', 'interview_sessions', 'kbs', 'kernel_desk_delegations', 'kernel_inference_receipt_attestations', 'kernel_journal', 'kernel_meta', 'kernel_operations', 'kernel_parent_checkpoints', 'kernel_parent_runs', 'kernel_project_delegations', 'kernel_projection_stages', 'kernel_receipts', 'kernel_schedule_delegations', 'kernel_schedule_ticks', 'knowledge_memberships', 'meeting_projects', 'meeting_sync_conflicts', 'meeting_tags', 'meetings', 'mesh_relay_jobs', 'mesh_worker_reservations', 'mesh_workers', 'milestones', 'model_library_provider_commands', 'model_manifests', 'model_profile_binding_heads', 'model_profile_binding_revisions', 'model_profile_readiness_observations', 'model_profile_revisions', 'model_profile_tombstones', 'monday_brief_item_shelf', 'monday_brief_items', 'monday_briefs', 'needs_you_last_known', 'notes', 'notes_memory_fts', 'notes_memory_fts_config', 'notes_memory_fts_content', 'notes_memory_fts_data', 'notes_memory_fts_docsize', 'notes_memory_fts_idx', 'onboarding_state', 'pipeline_events', 'plugin_run_jobs', 'plugin_runs', 'preparation_carries', 'profiles', 'project_ask_tasks', 'project_briefs', 'project_changes', 'project_commands', 'project_detection_log', 'project_evidence_links', 'project_items', 'project_observations', 'project_proposals', 'project_resources', 'project_reviews', 'project_setup_answers', 'project_setup_sessions', 'project_sources', 'project_update_deliveries', 'project_updates', 'projects', 'reaction_event_projections', 'recipe_chat_results', 'recipe_results', 'recipes', 'refinement_aggregate_commands', 'refinement_answer_continue_commands', 'refinement_attachment_leaves', 'refinement_attachment_revisions', 'refinement_attachment_visible', 'refinement_completion_receipts', 'refinement_context_actions', 'refinement_default_context_actions', 'refinement_default_context_applications', 'refinement_default_context_current', 'refinement_default_context_revisions', 'refinement_hosts', 'refinement_invocation_attempts', 'refinement_invocations', 'refinement_lifecycle_revisions', 'refinement_resume_sequence', 'refinement_retry_plans', 'refinement_review_actions', 'refinement_review_results', 'refinement_thought_sync_tombstones', 'refinement_thoughts', 'refinement_working_revisions', 'refinement_workspace_identity', 'remote_dictation_deliveries', 'resourceful_dispatches', 'resourceful_policies', 'scheduled_recordings', 'schema_version', 'segments', 'segments_fts', 'segments_fts_config', 'segments_fts_data', 'segments_fts_docsize', 'segments_fts_idx', 'service_events', 'session_usage', 'skills', 'source_suggestions', 'speakers', 'sqlite_sequence', 'steering_audit', 'steward_commands', 'steward_policies', 'steward_runs', 'steward_steps', 'thread_message_parts', 'thread_messages', 'thread_messages_fts', 'thread_messages_fts_config', 'thread_messages_fts_data', 'thread_messages_fts_docsize', 'thread_messages_fts_idx', 'thread_refs', 'thread_tool_policy', 'threads', 'tool_turn_commands', 'tool_turn_effect_children', 'tool_turn_model_steps', 'tool_turn_tool_call_results', 'tool_turn_tool_calls', 'tool_turn_transitions', 'tool_turns', 'topics', 'turn_capability_leases', 'watch_effects', 'watch_evaluations', 'watch_provider_connections', 'watch_rules', 'watch_setup_proposals', 'work_attempt_events', 'work_attempts', 'workbench_items', 'workbench_runs', 'workbenches', 'workflows']
INFO     holdspeak.db.reconcile:reconcile.py:984 Decision backfill: artifacts=0, decisions=0, inserted=0, updated=0, unchanged=0, skipped=0
INFO     holdspeak.db.reconcile:reconcile.py:989 Memory index rebuild: decisions=0, artifacts=0, notes=0, total=0
INFO     holdspeak.db.reconcile:reconcile.py:793 Schema reconciled to version 79 (changed=True)
INFO     holdspeak.web_server:web_server.py:1321 Seeded 10 built-in skills
INFO     holdspeak.workbench_conductor:workbench_conductor.py:517 Workbench conductor started
INFO     holdspeak.scheduled_recording_conductor:scheduled_recording_conductor.py:130 Scheduled recording conductor started
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
DEBUG    holdspeak.web_server:web_server.py:1400 Meeting web server startup complete
INFO     holdspeak.web_server:web_server.py:456 Meeting web server started: http://127.0.0.1:54012
------------------------------ Captured log call -------------------------------
INFO     holdspeak.web.routes.system:ws.py:67 WebSocket connection attempt
INFO     holdspeak.web.routes.system:ws.py:70 WebSocket connected successfully
INFO     holdspeak.audio_devices:audio_devices.py:191 Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
INFO     holdspeak.audio_devices:audio_devices.py:191 Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
INFO     holdspeak.audio_devices:audio_devices.py:191 Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
DEBUG    holdspeak.web_server:web_server.py:585 Broadcasting desk_changed to WebSocket clients
DEBUG    holdspeak.web_server:web_server.py:585 Broadcasting desk_changed to WebSocket clients
INFO     holdspeak.web.routes.system:ws.py:67 WebSocket connection attempt
INFO     holdspeak.web.routes.system:ws.py:70 WebSocket connected successfully
INFO     holdspeak.audio_devices:audio_devices.py:191 Found BlackHole device: BlackHole 2ch (idx=1, in=2, out=2)
---------------------------- Captured log teardown -----------------------------
INFO     holdspeak.web_server:web_server.py:490 Stopping meeting web server
INFO     holdspeak.calendar_ingest_conductor:calendar_ingest_conductor.py:234 Calendar ingest conductor stopped
INFO     holdspeak.workbench_conductor:workbench_conductor.py:523 Workbench conductor stopped
INFO     holdspeak.scheduled_recording_conductor:scheduled_recording_conductor.py:143 Scheduled recording conductor stopped
DEBUG    holdspeak.web_server:web_server.py:1443 Meeting web server shutdown complete
____ TestOneDelete.test_a_workbench_remove_works_again_after_a_refusal[393] ____
[gw8] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python

self = <tests.e2e.test_philo8_one_delete_glass.TestOneDelete object at 0x10dffca50>
width = 393

    @pytest.mark.e2e
    @pytest.mark.parametrize("width", [1440, 393])
    def test_a_workbench_remove_works_again_after_a_refusal(self, width: int) -> None:
        """Round four item 2: a refused Remove (403) frees the item: the next
        Remove sends a DELETE; the window never says "Removal committed"."""
        from playwright.sync_api import sync_playwright
    
        with sync_playwright() as pw:
            browser, page, _ids, errors = self._open(pw, width, [])
            try:
                wb = _api(page, "POST", "/api/workbenches", {"name": "Refused WB"}, token=TOKEN)["workbench"]["id"]
                item = _api(page, "POST", f"/api/workbenches/{wb}/items", {"title": "Refused item"}, token=TOKEN)["item"]["id"]
                page.reload(wait_until="load")
                _normal_chair(page)
                _to_face(page, "list", width)
                _name_button(page, "Refused WB").click()
                window = page.locator(".desk-workbench-window")
>               window.wait_for(timeout=10_000)

tests/e2e/test_philo8_one_delete_glass.py:709: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
.venv/lib/python3.13/site-packages/playwright/sync_api/_generated.py:18080: in wait_for
    self._sync(self._impl_obj.wait_for(timeout=timeout, state=state))
.venv/lib/python3.13/site-packages/playwright/_impl/_locator.py:710: in wait_for
    await self._frame.wait_for_selector(
.venv/lib/python3.13/site-packages/playwright/_impl/_frame.py:369: in wait_for_selector
    await self._channel.send(
.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:69: in send
    return await self._connection.wrap_api_call(
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <playwright._impl._connection.Connection object at 0x15045c050>
cb = <function Channel.send.<locals>.<lambda> at 0x156a272e0>
is_internal = False, title = None

    async def wrap_api_call(
        self, cb: Callable[[], Any], is_internal: bool = False, title: str = None
    ) -> Any:
        if self._api_zone.get():
            return await cb()
        task = asyncio.current_task(self._loop)
        st: List[inspect.FrameInfo] = getattr(
            task, "__pw_stack__", None
        ) or inspect.stack(0)
    
        parsed_st = _extract_stack_trace_information_from_stack(st, is_internal, title)
        self._api_zone.set(parsed_st)
        try:
            return await cb()
        except Exception as error:
>           raise rewrite_error(error, f"{parsed_st['apiName']}: {error}") from None
E           playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded.
E           Call log:
E             - waiting for locator(".desk-workbench-window") to be visible

.venv/lib/python3.13/site-packages/playwright/_impl/_connection.py:559: TimeoutError
------------------------------ Captured log setup ------------------------------
WARNING  holdspeak.intel_queue_conductor:intel_queue_conductor.py:130 Intel queue drainer is OFF: this process does not own the database.
=============================== warnings summary ===============================
tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:260: SyntaxWarning: invalid escape sequence '\s'
    ? '.' + el.className.trim().split(/\s+/)

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_hs202_05_first_use_type_floor.py:439: SyntaxWarning: invalid escape sequence '\('
    const m = /rgba?\(([^)]+)\)/.exec(s || '');

tests/unit/test_evidence_scratch_guard.py::test_no_test_writes_into_tracked_evidence
  tests/e2e/test_philo9_03_room_face_glass.py:807: SyntaxWarning: invalid escape sequence '\s'
    face = row.evaluate("""r => ({text: r.innerText.replace(/\s+/g, ' ').trim(),

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_hs141_models_setup_glass.py:21: HS-170: Settings -> Models module PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge (web/src/features/concierge/ConciergeCore.tsx, open-concierge window)
SKIPPED [1] tests/e2e/test_hs142_model_acquisition_glass.py:26: HS-170: Model Library front-door PARKED (HS-170-03, settled-design-four-faces.md Face 3); download-verify-add now at the Concierge's preset Download (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_assignments_glass.py:18: HS-170: Settings -> Assignments PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's THE SET section + Adjust well (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs143_model_library_glass.py:19: HS-170: ModelLibraryCore PARKED (HS-170-03, settled-design-four-faces.md Face 3); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:42: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:47: no hub listening at http://localhost:8778
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_project_updates_schema.py:576: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_delta_schema.py:640: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/xdist-gw1/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/xdist-gw1/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/integration/test_update_drafter_live_43.py:110: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (runs a real model call on the LAN endpoint)
SKIPPED [1] tests/unit/test_interview_service.py:237: QUARANTINED #694: it drives project.setup.finalize through the thread's bound dispatch to assert the continuation refusal; finalize is CONFIG (the owner's press), no longer in the section, so the call is refused as unavailable before the continuation check. BACKLOG row 'Interview setup continuation after #694'.
SKIPPED [1] tests/unit/test_hs166_walk_fixes.py:183: No proposals generated
SKIPPED [1] tests/unit/test_watch_graduation_schema.py:493: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/unit/test_project_room_schema.py:390: Owner's real DB not found (CI or isolated HOME)
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:59: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:110: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:100: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/e2e/test_hs145_door_polish_glass.py:182: HS-170: door-board scroll-hint PARKED (HS-170-04); the arrival has no horizontal-scroll viewport -- capability intentionally gone
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Qv5MD3RpFP/xdist-gw10/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/e2e/test_hs147_one_tap_glass.py:159: HS-170: door-rail one-tap arm PARKED (HS-170-04); per-event RECORD THIS gone; Schedule + Cancel at the arrival's capture bar covered by test_hs144_door_glass::test_upcoming_rail_schedule_create_round_trip_and_form_cancel
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [2] tests/e2e/test_hs166_jira_glass.py:328: HS-169-07 retired the interview + Jira wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1637: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
SKIPPED [2] tests/e2e/test_hs168_connections_glass.py:319: gh auth status failed (exit 1): You are not logged into any GitHub hosts. To log in, run: gh auth login
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:279: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs168_sources_glass.py:365: HS-169-02 retired the Sources step (ProgressPlan, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/wt-philo-11-01/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:118: mermaid renderer unavailable in this env: eer-core/lib/puppeteer/node/PuppeteerNode.js:124:16)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:1090:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:493:3)
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:268: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:519: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:671: HS-169-07 retired the interview entry point this leg used for project creation; evaluation/delta review is a live capability noted in the close ledger for re-pointing
SKIPPED [2] tests/e2e/test_hs161_github_glass.py:919: HS-169-07 retired the interview + GitHub wizard (SetupCore, suggestion cards, wizards); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs161_github_glass.py:1088: gh CLI not authenticated or not installed (skip-clean)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:553: HS-170: front-door pack cards PARKED (HS-170-03); capability now at the Concierge's FOUND section (ConciergeCore.tsx)
SKIPPED [1] tests/e2e/test_hs156_front_door_glass.py:619: HS-170: front-door candidate picker PARKED (HS-170-03); capability now at the Concierge's picker ChoiceCards (ConciergeCore.tsx)
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:172: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs158_room_glass.py:233: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs158_room_glass.py:282: HS-169-07 retired the 158 Room (identity band, counters, focus block); see test_hs169_room_glass.py for the replacement rig
SKIPPED [2] tests/e2e/test_hs159_interview_glass.py:150: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:397: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); see test_hs169_door_glass.py for the replacement rig
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:462: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); blank leg ported to test_hs169_door_legs_glass.py
SKIPPED [1] tests/e2e/test_hs159_interview_glass.py:555: HS-169-07 retired the interview (SetupCore, suggestion cards, wizards, Review page); abandon leg ported to test_hs169_door_legs_glass.py
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_review_proposals_stay_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[1440-1200] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
XFAIL tests/e2e/test_hs200_meeting_outcomes_glass.py::test_meeting_partial_chain_retry_stays_live_under_amendment[393-900] - HS-201 ratified analysis-only summary amendment; parked proposal pipeline
FAILED tests/unit/test_mcp_phase133_surface.py::test_desk_crud_descriptions_carry_kind_boundary_sentence
FAILED tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_brief.generated_empty]
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[file a note into a zone]
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[find a note]
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[list the notes in a zone]
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a zone]
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[put a decision on my review list]
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[read a note]
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision]
FAILED tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.unfile]
FAILED tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers
FAILED tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440 - Assertion...
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_resize_that_changes_the_face_commits
FAILED tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[1440]
FAILED tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]
FAILED tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]
FAILED tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440 - AssertionEr...
FAILED tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393 - AssertionErr...
FAILED tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[393]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]
FAILED tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[1440]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]
FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[1440]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[floor-1440]
FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422]
FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]
FAILED tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_workbench_remove_never_offers_a_false_undo
FAILED tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[393]
38 failed, 13498 passed, 99 skipped, 4 xfailed, 3 warnings in 1700.78s (0:28:20)
```

### Captured run — 2026-09-30T05:15:02Z

- **Command:** `uv run python .tmp/philo11/final-glass/recheck.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_brief.generated_empty]
tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_resize_that_changes_the_face_commits
tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[1440]
tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]
tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]
tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]
tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[393]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]
tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[1440]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]
tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[1440]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[floor-1440]
tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422]
tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]
tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_workbench_remove_never_offers_a_false_undo
tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[393]

26 tests collected in 0.06s

ROUND 1 CASE 1: tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_brief.generated_empty]
.                                                                        [100%]
1 passed in 11.19s
ROUND 1 CASE 2: tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440
.                                                                        [100%]
1 passed in 6.00s
ROUND 1 CASE 3: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_resize_that_changes_the_face_commits
.                                                                        [100%]
1 passed in 13.16s
ROUND 1 CASE 4: tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[1440]
.                                                                        [100%]
1 passed in 32.78s
ROUND 1 CASE 5: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]
.                                                                        [100%]
1 passed in 25.48s
ROUND 1 CASE 6: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]
.                                                                        [100%]
1 passed in 17.87s
ROUND 1 CASE 7: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]
.                                                                        [100%]
1 passed in 22.56s
ROUND 1 CASE 8: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
.                                                                        [100%]
1 passed in 9.77s
ROUND 1 CASE 9: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
.                                                                        [100%]
1 passed in 9.18s
ROUND 1 CASE 10: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]
.                                                                        [100%]
1 passed in 13.52s
ROUND 1 CASE 11: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]
.                                                                        [100%]
1 passed in 21.00s
ROUND 1 CASE 12: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[393]
.                                                                        [100%]
1 passed in 16.94s
ROUND 1 CASE 13: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]
.                                                                        [100%]
1 passed in 28.92s
ROUND 1 CASE 14: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393]
.                                                                        [100%]
1 passed in 26.59s
ROUND 1 CASE 15: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]
.                                                                        [100%]
1 passed in 16.64s
ROUND 1 CASE 16: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]
.                                                                        [100%]
1 passed in 11.60s
ROUND 1 CASE 17: tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[1440]
.                                                                        [100%]
1 passed in 12.64s
ROUND 1 CASE 18: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]
.                                                                        [100%]
1 passed in 23.31s
ROUND 1 CASE 19: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[1440]
.                                                                        [100%]
1 passed in 25.96s
ROUND 1 CASE 20: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[floor-1440]
.                                                                        [100%]
1 passed in 24.50s
ROUND 1 CASE 21: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422]
.                                                                        [100%]
1 passed in 50.87s
ROUND 1 CASE 22: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network]
.                                                                        [100%]
1 passed in 30.08s
ROUND 1 CASE 23: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]
.                                                                        [100%]
1 passed in 19.12s
ROUND 1 CASE 24: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]
.                                                                        [100%]
1 passed in 25.47s
ROUND 1 CASE 25: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_workbench_remove_never_offers_a_false_undo
.                                                                        [100%]
1 passed in 24.98s
ROUND 1 CASE 26: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[393]
.                                                                        [100%]
1 passed in 32.53s
ROUND 2 CASE 1: tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_brief.generated_empty]
.                                                                        [100%]
1 passed in 9.63s
ROUND 2 CASE 2: tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440
.                                                                        [100%]
1 passed in 5.94s
ROUND 2 CASE 3: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_resize_that_changes_the_face_commits
.                                                                        [100%]
1 passed in 13.53s
ROUND 2 CASE 4: tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[1440]
.                                                                        [100%]
1 passed in 34.21s
ROUND 2 CASE 5: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]
.                                                                        [100%]
1 passed in 27.04s
ROUND 2 CASE 6: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]
.                                                                        [100%]
1 passed in 17.19s
ROUND 2 CASE 7: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]
.                                                                        [100%]
1 passed in 22.32s
ROUND 2 CASE 8: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440
.                                                                        [100%]
1 passed in 9.63s
ROUND 2 CASE 9: tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393
.                                                                        [100%]
1 passed in 10.13s
ROUND 2 CASE 10: tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]
.                                                                        [100%]
1 passed in 13.67s
ROUND 2 CASE 11: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[1440]
.                                                                        [100%]
1 passed in 21.00s
ROUND 2 CASE 12: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_row_menu_delete_removes_the_object[393]
.                                                                        [100%]
1 passed in 17.22s
ROUND 2 CASE 13: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]
.                                                                        [100%]
1 passed in 30.06s
ROUND 2 CASE 14: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393]
.                                                                        [100%]
1 passed in 27.44s
ROUND 2 CASE 15: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_list_palette_delete_removes_the_selected_object[393]
.                                                                        [100%]
1 passed in 17.86s
ROUND 2 CASE 16: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]
.                                                                        [100%]
1 passed in 11.66s
ROUND 2 CASE 17: tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[1440]
.                                                                        [100%]
1 passed in 13.12s
ROUND 2 CASE 18: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_undo_on_the_list_keeps_the_object[393]
.                                                                        [100%]
1 passed in 23.32s
ROUND 2 CASE 19: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[1440]
.                                                                        [100%]
1 passed in 27.16s
ROUND 2 CASE 20: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[floor-1440]
.                                                                        [100%]
1 passed in 24.63s
ROUND 2 CASE 21: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422]
.                                                                        [100%]
1 passed in 50.90s
ROUND 2 CASE 22: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network]
.                                                                        [100%]
1 passed in 29.61s
ROUND 2 CASE 23: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]
.                                                                        [100%]
1 passed in 19.53s
ROUND 2 CASE 24: tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]
.                                                                        [100%]
1 passed in 24.66s
ROUND 2 CASE 25: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_workbench_remove_never_offers_a_false_undo
.                                                                        [100%]
1 passed in 26.37s
ROUND 2 CASE 26: tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_remove_works_again_after_a_refusal[393]
.                                                                        [100%]
1 passed in 32.65s
SERIAL RESULTS: 52/52 passed
```

### Captured run — 2026-09-30T05:34:58Z

- **Command:** `bash .tmp/philo11/final-check.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 189511c053cdd5e37f871b5aa69efa1222977bbb

```text
246 catalogue entries: all non-description fields unchanged.
SPY RUN 1 on_loop= False
{"context_ceiling": 16384, "engine_off_loop": true, "headroom": 269, "input_tokens": 15603, "palette_tools": 31, "reserved_output_tokens": 512, "source": "actual inference_adoption_route_evidence and material snapshot rows", "total_tokens": 16115}
OK docs/generated/operations.json
Architecture documentation checked (10 outputs).
OpenAPI: 580 paths
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
tests/unit/test_mcp_phase133_surface.py::test_retired_destination_and_profile_resources_are_absent
tests/unit/test_mcp_phase133_surface.py::test_workbench_resource_read_truncates_to_100
tests/unit/test_mcp_phase133_surface.py::test_desk_crud_descriptions_carry_kind_boundary_sentence
tests/unit/test_mcp_phase133_surface.py::test_pipeline_events_dispatches
tests/unit/test_mcp_phase133_surface.py::test_retired_underscore_name_absent_from_catalogue
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[file a note into a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[find a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[list the notes in a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[put a decision on my review list]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[read a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.list]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.get]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.create]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.update]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.delete]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.verb]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.file]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.unfile]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.list_members]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.add_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.remove_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.list_members]
tests/unit/test_phase143_routing_authority_census.py::test_census_inventory_has_one_owner_for_each_mutable_family
tests/unit/test_phase143_routing_authority_census.py::test_census_anchors_current_routing_resolvers_and_legacy_assignment_writers
tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
tests/unit/test_phase143_routing_authority_census.py::test_ast_census_rejects_a_new_public_resolver_or_late_pointer_read
tests/unit/test_phase143_routing_authority_census.py::test_phase143_placement_adopters_have_zero_python_resolution_forks
tests/unit/test_phase143_routing_authority_census.py::test_phase143_placement_adopter_fork_scan_rejects_local_resolver_or_runner
tests/unit/test_phase143_routing_authority_census.py::test_profile_service_owner_gate_is_enforced_before_lookup_or_probe
tests/unit/test_phase143_routing_authority_census.py::test_path_bearing_profile_sync_seam_is_a_named_blocker_not_an_exception
tests/unit/test_phase143_routing_authority_census.py::test_phase_f_meeting_execution_surface_has_no_v1_resolver_or_direct_runner
tests/unit/test_phase143_routing_authority_census.py::test_legacy_assignment_writers_are_delete_work_and_acquisition_is_availability_only
tests/unit/test_phase143_inference_capability_census.py::test_phase143_call_site_fixture_is_complete_and_fail_closed
tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner
tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers
tests/unit/test_phase143_inference_capability_census.py::test_phase143_semantic_census_rejects_new_ask_or_recipe_caller
tests/unit/test_phase143_inference_capability_census.py::test_phase143_swift_physical_leaves_remain_explicit_held_scope
tests/unit/test_phase143_inference_capability_census.py::test_phase143_swift_census_rejects_fallback_or_new_provider_open
tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_censused_site_has_one_capability_and_source_owner
tests/unit/test_phase143_inference_capability_census.py::test_phase143_physical_leaves_have_no_legacy_bypass
tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop
tests/unit/test_people_mcp.py::test_people_mcp_catalogue_is_closed_and_does_not_offer_forbidden_operations
tests/unit/test_people_calendar_link.py::TestMCPTools::test_catalogue_includes_calendar_tools
tests/unit/test_philo10_send_contract.py::test_the_words_map_his_asks_and_never_say_an_agent_sends
tests/unit/test_philo5_one_decision.py::test_operations_export_matches_the_catalogue

48 tests collected in 0.73s
................................................                         [100%]
48 passed in 28.34s
```

### Captured run — 2026-09-30T07:08:23Z

- **Command:** `uv run python .tmp/philo11/round2_verify.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[file a note into a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[find a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[list the notes in a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[put a decision on my review list]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[read a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.list]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.get]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.create]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.update]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.delete]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.verb]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.file]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.unfile]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.list_members]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.add_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.remove_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.list_members]
tests/unit/test_philo10_send_contract.py::test_the_operations_are_declared_once_and_reach_one_service_over_http_and_mcp
tests/unit/test_philo10_send_contract.py::test_http_and_mcp_reach_the_same_rows
tests/unit/test_philo10_send_contract.py::test_each_admitted_row_is_one_operation_with_one_terminal_receipt[http]
tests/unit/test_philo10_send_contract.py::test_each_admitted_row_is_one_operation_with_one_terminal_receipt[mcp]
tests/unit/test_philo10_send_contract.py::test_reads_and_previews_leave_no_operation
tests/unit/test_philo10_send_contract.py::test_each_refusal_class_leaves_its_receipt_and_sends_nothing
tests/unit/test_philo10_send_contract.py::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required[project_update]
tests/unit/test_philo10_send_contract.py::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required[desk_decision]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[project_update-mcp]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[project_update-http]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[desk_decision-mcp]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[desk_decision-http]
tests/unit/test_philo10_send_contract.py::test_the_channel_tools_sit_in_the_agents_project_palette
tests/unit/test_philo10_send_contract.py::test_two_sends_of_one_update_to_one_folder_make_two_files_with_their_proof
tests/unit/test_philo10_send_contract.py::test_the_suffix_and_exclusive_create_never_write_over_an_old_file
tests/unit/test_philo10_send_contract.py::test_a_name_that_leaves_the_folder_is_refused
tests/unit/test_philo10_send_contract.py::test_a_create_refused_by_the_os_is_failed_and_writes_no_history
tests/unit/test_philo10_send_contract.py::test_an_error_off_the_pinned_list_and_bytes_that_do_not_read_back_are_unknown
tests/unit/test_philo10_send_contract.py::test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes[project_update]
tests/unit/test_philo10_send_contract.py::test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes[desk_decision]
tests/unit/test_philo10_send_contract.py::test_a_changed_payload_is_refused_before_any_effect
tests/unit/test_philo10_send_contract.py::test_an_oversize_payload_is_refused_by_name
tests/unit/test_philo10_send_contract.py::test_the_body_never_reaches_a_kernel_row_a_receipt_the_journal_a_log_or_an_error
tests/unit/test_philo10_send_contract.py::test_the_private_payload_file_is_0600_in_0700_and_its_digest_is_checked
tests/unit/test_philo10_send_contract.py::test_an_error_is_redacted_and_cut
tests/unit/test_philo10_send_contract.py::test_an_excerpt_of_the_payload_and_a_secret_are_redacted
tests/unit/test_philo10_send_contract.py::test_edit_parks_the_old_row_and_a_send_prepared_to_it_is_refused_with_the_historical_target
tests/unit/test_philo10_send_contract.py::test_a_destination_whose_target_changed_after_prepare_is_refused
tests/unit/test_philo10_send_contract.py::test_remove_parks_and_keeps_history
tests/unit/test_philo10_send_contract.py::test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched[send_id]
tests/unit/test_philo10_send_contract.py::test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched[inline]
tests/unit/test_philo10_send_contract.py::test_a_remove_after_the_boundary_parks_and_the_send_stands[send_id]
tests/unit/test_philo10_send_contract.py::test_a_remove_after_the_boundary_parks_and_the_send_stands[inline]
tests/unit/test_philo10_send_contract.py::test_a_folder_marked_synced_is_badged_cloud
tests/unit/test_philo10_send_contract.py::test_send_and_discard_pressed_together_settle_once[project_update]
tests/unit/test_philo10_send_contract.py::test_send_and_discard_pressed_together_settle_once[desk_decision]
tests/unit/test_philo10_send_contract.py::test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands[project_update]
tests/unit/test_philo10_send_contract.py::test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands[desk_decision]
tests/unit/test_philo10_send_contract.py::test_manual_rows_read_channel_manual
tests/unit/test_philo10_send_contract.py::test_an_existing_database_gains_the_columns_and_its_rows_read_manual
tests/unit/test_philo10_send_contract.py::test_the_words_map_his_asks_and_never_say_an_agent_sends
tests/unit/test_philo11_document_sources.py::test_registry_declares_the_eight_kinds
tests/unit/test_philo11_document_sources.py::test_real_producers_render_all_eight_sources
tests/unit/test_philo11_document_sources.py::test_monday_brief_names_unavailable_people_once
tests/unit/test_philo11_document_sources.py::test_meeting_sources_never_copy_transcript
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[project_update]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[monday_brief]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[desk_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[decision_record]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_summary]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[unknown_kind:source-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[meeting_summary:missing-document_not_found]
tests/unit/test_philo11_document_sources.py::test_missing_meeting_summary_is_named_no_summary
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_project_update_refuses_unpublished_by_generic_name
tests/unit/test_philo11_document_sources.py::test_aftercare_document_markdown_is_not_truncated
tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop

82 tests collected in 0.70s
bringing up nodes...
bringing up nodes...

........................................................................ [ 87%]
..........                                                               [100%]
82 passed in 9.33s
{"ceiling": 16384, "database": "popen-gw1/test_recipe_run_and_chat_run_t0/holdspeak.db", "headroom": 148, "input_tokens_bytes": 15724, "leaf_entries": 0, "operation_id": "chat_turn_261b80d858dd42109b4db3584396ac89", "reserved_output_tokens": 512, "source": "persisted inference_adoption_route_evidence row from the real test producer", "total_tokens": 16236}
{"ceiling": 16384, "database": "popen-gw4/test_chat_alias_engine_runs_of0/holdspeak.db", "headroom": 187, "input_tokens_bytes": 15685, "leaf_entries": 0, "operation_id": "chat_turn_556597eb823d4744ad9a74b643e65dca", "reserved_output_tokens": 512, "source": "persisted inference_adoption_route_evidence row from the real test producer", "total_tokens": 16197}
```

### Captured run — 2026-09-30T07:10:56Z

- **Command:** `uv run python .tmp/philo11/round2_real_proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
Intel queue drainer is OFF: this process does not own the database.
246 catalogue entries: all non-description fields unchanged.
SPY RUN 1 on_loop= False
{"context_ceiling": 16384, "engine_off_loop": true, "headroom": 207, "input_tokens": 15665, "palette_tools": 31, "reserved_output_tokens": 512, "source": "actual inference_adoption_route_evidence and material snapshot rows", "total_tokens": 16177}
REAL tools/list: 'file a note into a zone' -> zone.file
REAL tools/list: 'find a note' -> desk.list
REAL tools/list: 'read a note' -> desk.get
REAL tools/list: 'make a zone' -> desk.create
REAL tools/list: 'put a decision on my review list' -> desk.create
REAL tools/list: 'list the notes in a zone' -> zone.list_members
REAL tools/list: 'the reason for a decision' -> desk.create
REAL tools/list: 'write a note' -> desk.create
REAL tools/list: 'rename a zone' -> desk.update
REAL tools/list: 'move a zone' -> desk.update
REAL tools/list: 'Where can I send' -> channel.destinations
REAL tools/list: 'send the update to <destination>' -> channel.prepare
REAL tools/list: 'What was sent' -> channel.sends
```

### Captured run — 2026-09-30T07:15:59Z

- **Command:** `uv run python .tmp/philo11/round2_verify.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[file a note into a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[find a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[list the notes in a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[put a decision on my review list]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[read a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.list]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.get]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.create]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.update]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.delete]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.verb]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.file]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.unfile]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.list_members]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.add_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.remove_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.list_members]
tests/unit/test_philo10_send_contract.py::test_the_operations_are_declared_once_and_reach_one_service_over_http_and_mcp
tests/unit/test_philo10_send_contract.py::test_http_and_mcp_reach_the_same_rows
tests/unit/test_philo10_send_contract.py::test_each_admitted_row_is_one_operation_with_one_terminal_receipt[http]
tests/unit/test_philo10_send_contract.py::test_each_admitted_row_is_one_operation_with_one_terminal_receipt[mcp]
tests/unit/test_philo10_send_contract.py::test_reads_and_previews_leave_no_operation
tests/unit/test_philo10_send_contract.py::test_each_refusal_class_leaves_its_receipt_and_sends_nothing
tests/unit/test_philo10_send_contract.py::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required[project_update]
tests/unit/test_philo10_send_contract.py::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required[desk_decision]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[project_update-mcp]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[project_update-http]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[desk_decision-mcp]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[desk_decision-http]
tests/unit/test_philo10_send_contract.py::test_the_channel_tools_sit_in_the_agents_project_palette
tests/unit/test_philo10_send_contract.py::test_two_sends_of_one_update_to_one_folder_make_two_files_with_their_proof
tests/unit/test_philo10_send_contract.py::test_the_suffix_and_exclusive_create_never_write_over_an_old_file
tests/unit/test_philo10_send_contract.py::test_a_name_that_leaves_the_folder_is_refused
tests/unit/test_philo10_send_contract.py::test_a_create_refused_by_the_os_is_failed_and_writes_no_history
tests/unit/test_philo10_send_contract.py::test_an_error_off_the_pinned_list_and_bytes_that_do_not_read_back_are_unknown
tests/unit/test_philo10_send_contract.py::test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes[project_update]
tests/unit/test_philo10_send_contract.py::test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes[desk_decision]
tests/unit/test_philo10_send_contract.py::test_a_changed_payload_is_refused_before_any_effect
tests/unit/test_philo10_send_contract.py::test_an_oversize_payload_is_refused_by_name
tests/unit/test_philo10_send_contract.py::test_the_body_never_reaches_a_kernel_row_a_receipt_the_journal_a_log_or_an_error
tests/unit/test_philo10_send_contract.py::test_the_private_payload_file_is_0600_in_0700_and_its_digest_is_checked
tests/unit/test_philo10_send_contract.py::test_an_error_is_redacted_and_cut
tests/unit/test_philo10_send_contract.py::test_an_excerpt_of_the_payload_and_a_secret_are_redacted
tests/unit/test_philo10_send_contract.py::test_edit_parks_the_old_row_and_a_send_prepared_to_it_is_refused_with_the_historical_target
tests/unit/test_philo10_send_contract.py::test_a_destination_whose_target_changed_after_prepare_is_refused
tests/unit/test_philo10_send_contract.py::test_remove_parks_and_keeps_history
tests/unit/test_philo10_send_contract.py::test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched[send_id]
tests/unit/test_philo10_send_contract.py::test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched[inline]
tests/unit/test_philo10_send_contract.py::test_a_remove_after_the_boundary_parks_and_the_send_stands[send_id]
tests/unit/test_philo10_send_contract.py::test_a_remove_after_the_boundary_parks_and_the_send_stands[inline]
tests/unit/test_philo10_send_contract.py::test_a_folder_marked_synced_is_badged_cloud
tests/unit/test_philo10_send_contract.py::test_send_and_discard_pressed_together_settle_once[project_update]
tests/unit/test_philo10_send_contract.py::test_send_and_discard_pressed_together_settle_once[desk_decision]
tests/unit/test_philo10_send_contract.py::test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands[project_update]
tests/unit/test_philo10_send_contract.py::test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands[desk_decision]
tests/unit/test_philo10_send_contract.py::test_manual_rows_read_channel_manual
tests/unit/test_philo10_send_contract.py::test_an_existing_database_gains_the_columns_and_its_rows_read_manual
tests/unit/test_philo10_send_contract.py::test_the_words_map_his_asks_and_never_say_an_agent_sends
tests/unit/test_philo11_document_sources.py::test_registry_declares_the_eight_kinds
tests/unit/test_philo11_document_sources.py::test_real_producers_render_all_eight_sources
tests/unit/test_philo11_document_sources.py::test_monday_brief_names_unavailable_people_once
tests/unit/test_philo11_document_sources.py::test_meeting_sources_never_copy_transcript
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[project_update]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[monday_brief]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[desk_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[decision_record]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_summary]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[unknown_kind:source-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[meeting_summary:missing-document_not_found]
tests/unit/test_philo11_document_sources.py::test_missing_meeting_summary_is_named_no_summary
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_project_update_refuses_unpublished_by_generic_name
tests/unit/test_philo11_document_sources.py::test_aftercare_document_markdown_is_not_truncated
tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop

82 tests collected in 0.73s
bringing up nodes...
bringing up nodes...

...................F.................................................... [ 87%]
..........                                                               [100%]
=================================== FAILURES ===================================
_ test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision] _
[gw3] darwin -- Python 3.13.14 /Users/karol/dev/tools/wt-philo-11-01/.venv/bin/python
tests/unit/test_philo7_discovery.py:105: in test_each_job_phrase_maps_to_one_tool_and_its_argument_path
    assert f"kind={value}" in sentence, f"{phrase!r}: the sentence does not name kind={value}: {sentence!r}"
E   AssertionError: 'the reason for a decision': the sentence does not name kind=decisions: 'the reason for a decision in data.context_markdown.'
E   assert 'kind=decisions' in 'the reason for a decision in data.context_markdown.'
=========================== short test summary info ============================
FAILED tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision]
1 failed, 81 passed in 10.82s
```

### Captured run — 2026-09-30T07:16:33Z

- **Command:** `uv run python .tmp/philo11/round2_verify.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[file a note into a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[find a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[list the notes in a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a zone]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[put a decision on my review list]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[read a note]
tests/unit/test_philo7_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[the reason for a decision]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.list]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.get]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.create]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.update]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.delete]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[desk.verb]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.file]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.unfile]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[zone.list_members]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.add_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.remove_member]
tests/unit/test_philo7_discovery.py::test_every_id_argument_names_where_its_value_comes_from[kb.list_members]
tests/unit/test_philo10_send_contract.py::test_the_operations_are_declared_once_and_reach_one_service_over_http_and_mcp
tests/unit/test_philo10_send_contract.py::test_http_and_mcp_reach_the_same_rows
tests/unit/test_philo10_send_contract.py::test_each_admitted_row_is_one_operation_with_one_terminal_receipt[http]
tests/unit/test_philo10_send_contract.py::test_each_admitted_row_is_one_operation_with_one_terminal_receipt[mcp]
tests/unit/test_philo10_send_contract.py::test_reads_and_previews_leave_no_operation
tests/unit/test_philo10_send_contract.py::test_each_refusal_class_leaves_its_receipt_and_sends_nothing
tests/unit/test_philo10_send_contract.py::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required[project_update]
tests/unit/test_philo10_send_contract.py::test_an_agents_send_discard_and_destination_writes_are_refused_owner_principal_required[desk_decision]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[project_update-mcp]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[project_update-http]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[desk_decision-mcp]
tests/unit/test_philo10_send_contract.py::test_an_agents_prepare_completes_under_its_own_identity_and_waits_for_the_owner[desk_decision-http]
tests/unit/test_philo10_send_contract.py::test_the_channel_tools_sit_in_the_agents_project_palette
tests/unit/test_philo10_send_contract.py::test_two_sends_of_one_update_to_one_folder_make_two_files_with_their_proof
tests/unit/test_philo10_send_contract.py::test_the_suffix_and_exclusive_create_never_write_over_an_old_file
tests/unit/test_philo10_send_contract.py::test_a_name_that_leaves_the_folder_is_refused
tests/unit/test_philo10_send_contract.py::test_a_create_refused_by_the_os_is_failed_and_writes_no_history
tests/unit/test_philo10_send_contract.py::test_an_error_off_the_pinned_list_and_bytes_that_do_not_read_back_are_unknown
tests/unit/test_philo10_send_contract.py::test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes[project_update]
tests/unit/test_philo10_send_contract.py::test_the_preview_is_the_frozen_bytes_and_the_file_is_those_bytes[desk_decision]
tests/unit/test_philo10_send_contract.py::test_a_changed_payload_is_refused_before_any_effect
tests/unit/test_philo10_send_contract.py::test_an_oversize_payload_is_refused_by_name
tests/unit/test_philo10_send_contract.py::test_the_body_never_reaches_a_kernel_row_a_receipt_the_journal_a_log_or_an_error
tests/unit/test_philo10_send_contract.py::test_the_private_payload_file_is_0600_in_0700_and_its_digest_is_checked
tests/unit/test_philo10_send_contract.py::test_an_error_is_redacted_and_cut
tests/unit/test_philo10_send_contract.py::test_an_excerpt_of_the_payload_and_a_secret_are_redacted
tests/unit/test_philo10_send_contract.py::test_edit_parks_the_old_row_and_a_send_prepared_to_it_is_refused_with_the_historical_target
tests/unit/test_philo10_send_contract.py::test_a_destination_whose_target_changed_after_prepare_is_refused
tests/unit/test_philo10_send_contract.py::test_remove_parks_and_keeps_history
tests/unit/test_philo10_send_contract.py::test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched[send_id]
tests/unit/test_philo10_send_contract.py::test_a_remove_that_commits_before_the_boundary_wins_and_nothing_is_dispatched[inline]
tests/unit/test_philo10_send_contract.py::test_a_remove_after_the_boundary_parks_and_the_send_stands[send_id]
tests/unit/test_philo10_send_contract.py::test_a_remove_after_the_boundary_parks_and_the_send_stands[inline]
tests/unit/test_philo10_send_contract.py::test_a_folder_marked_synced_is_badged_cloud
tests/unit/test_philo10_send_contract.py::test_send_and_discard_pressed_together_settle_once[project_update]
tests/unit/test_philo10_send_contract.py::test_send_and_discard_pressed_together_settle_once[desk_decision]
tests/unit/test_philo10_send_contract.py::test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands[project_update]
tests/unit/test_philo10_send_contract.py::test_a_discard_pressed_while_the_send_dispatches_is_refused_and_the_send_stands[desk_decision]
tests/unit/test_philo10_send_contract.py::test_manual_rows_read_channel_manual
tests/unit/test_philo10_send_contract.py::test_an_existing_database_gains_the_columns_and_its_rows_read_manual
tests/unit/test_philo10_send_contract.py::test_the_words_map_his_asks_and_never_say_an_agent_sends
tests/unit/test_philo11_document_sources.py::test_registry_declares_the_eight_kinds
tests/unit/test_philo11_document_sources.py::test_real_producers_render_all_eight_sources
tests/unit/test_philo11_document_sources.py::test_monday_brief_names_unavailable_people_once
tests/unit/test_philo11_document_sources.py::test_meeting_sources_never_copy_transcript
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[project_update]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[monday_brief]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[desk_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_decision]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[decision_record]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_summary]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_each_source_names_a_missing_record[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[unknown_kind:source-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[-document_kind_unknown]
tests/unit/test_philo11_document_sources.py::test_named_source_refusals[meeting_summary:missing-document_not_found]
tests/unit/test_philo11_document_sources.py::test_missing_meeting_summary_is_named_no_summary
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_digest]
tests/unit/test_philo11_document_sources.py::test_empty_aftercare_is_named_no_summary[meeting_followup]
tests/unit/test_philo11_document_sources.py::test_project_update_refuses_unpublished_by_generic_name
tests/unit/test_philo11_document_sources.py::test_aftercare_document_markdown_is_not_truncated
tests/unit/test_engine_off_the_loop.py::test_recipe_run_and_chat_run_the_engine_off_the_loop
tests/unit/test_web_routes_recipe_chat.py::test_chat_alias_engine_runs_off_the_loop

82 tests collected in 0.67s
bringing up nodes...
bringing up nodes...

........................................................................ [ 87%]
..........                                                               [100%]
82 passed in 9.88s
{"ceiling": 16384, "database": "popen-gw5/test_chat_alias_engine_runs_of0/holdspeak.db", "headroom": 254, "input_tokens_bytes": 15618, "leaf_entries": 0, "operation_id": "chat_turn_9566940f29514959aab089acbe5ac471", "reserved_output_tokens": 512, "source": "persisted inference_adoption_route_evidence row from the real test producer", "total_tokens": 16130}
{"ceiling": 16384, "database": "popen-gw8/test_recipe_run_and_chat_run_t0/holdspeak.db", "headroom": 215, "input_tokens_bytes": 15657, "leaf_entries": 0, "operation_id": "chat_turn_00bed555d00c4d859b136748f7b1d03b", "reserved_output_tokens": 512, "source": "persisted inference_adoption_route_evidence row from the real test producer", "total_tokens": 16169}
```

### Captured run — 2026-09-30T07:16:51Z

- **Command:** `uv run python .tmp/philo11/round2_real_proof.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
Intel queue drainer is OFF: this process does not own the database.
246 catalogue entries: all non-description fields unchanged.
SPY RUN 1 on_loop= False
{"context_ceiling": 16384, "engine_off_loop": true, "headroom": 274, "input_tokens": 15598, "palette_tools": 31, "reserved_output_tokens": 512, "source": "actual inference_adoption_route_evidence and material snapshot rows", "total_tokens": 16110}
REAL tools/list: 'file a note into a zone' -> zone.file
REAL tools/list: 'find a note' -> desk.list
REAL tools/list: 'read a note' -> desk.get
REAL tools/list: 'make a zone' -> desk.create
REAL tools/list: 'put a decision on my review list' -> desk.create
REAL tools/list: 'list the notes in a zone' -> zone.list_members
REAL tools/list: 'the reason for a decision' -> desk.create
REAL tools/list: 'write a note' -> desk.create
REAL tools/list: 'rename a zone' -> desk.update
REAL tools/list: 'move a zone' -> desk.update
REAL tools/list: 'Where can I send' -> channel.destinations
REAL tools/list: 'send the update to <destination>' -> channel.prepare
REAL tools/list: 'What was sent' -> channel.sends
```

### Captured run — 2026-09-30T07:20:33Z

- **Command:** `uv run python scripts/verify_philo11_update_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b1f71ec6b5210279b668fd978f157aafaeafb4ca

```text
....                                                                     [100%]
4 passed in 195.50s (0:03:15)
```

### Captured run — 2026-09-30T09:39:35Z

- **Command:** `uv run --python 3.13 python .tmp/philo11-round3-admission.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 802e431c299a893ea64f75eec8096885574ef7ac

```text
bringing up nodes...
bringing up nodes...

..                                                                       [100%]
2 passed in 2.82s
{"accounting": "utf8-byte-upper-bound@1", "capability_id": "recipe.run", "context_ceiling": 16384, "eligibility": "executable", "headroom": 15242, "input_bytes_upper_bound": 630, "reason_code": null, "reserved_output_tokens": 512, "route_leg_ordinal": 1, "total": 1142}
{"accounting": "utf8-byte-upper-bound@1", "capability_id": "chat.turn", "context_ceiling": 16384, "eligibility": "executable", "headroom": 870, "input_bytes_upper_bound": 15002, "reason_code": null, "reserved_output_tokens": 512, "route_leg_ordinal": 1, "total": 15514}
{"accounting": "utf8-byte-upper-bound@1", "capability_id": "chat.turn", "context_ceiling": 16384, "eligibility": "executable", "headroom": 909, "input_bytes_upper_bound": 14963, "reason_code": null, "reserved_output_tokens": 512, "route_leg_ordinal": 1, "total": 15475}
Actual route evidence rows: 3
```

### Captured run — 2026-09-30T09:39:55Z

- **Command:** `uv run --python 3.13 python .tmp/philo11-round3-focused.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 802e431c299a893ea64f75eec8096885574ef7ac

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 74%]
.........................                                                [100%]
97 passed in 14.59s
```

### Captured run — 2026-09-30T09:40:22Z

- **Command:** `uv run --python 3.13 python scripts/verify_philo11_update_glass.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 802e431c299a893ea64f75eec8096885574ef7ac

```text
....                                                                     [100%]
4 passed in 121.59s (0:02:01)
```
