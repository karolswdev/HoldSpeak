# Evidence - HSEGHS001HS104-143-11

- **Story:** HSEGHS001HS104-143-11 - HTTP MCP Sync and Compatibility
- **Status:** done
- **Date:** 2026-08-26

## Proof

### Captured run — 2026-08-27T00:00:58Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run --python 3.13.11 pytest -q -n auto --ignore=tests/e2e/test_metal.py 2>&1 | tail -120`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 26e354ba84f7b6587f486836e468232d4f06f73f

```text
[gw8] darwin -- Python 3.13.11 /Users/karol/dev/tools/HoldSpeak/.venv/bin/python3

    def test_primary_copy_has_no_prohibited_operational_drift() -> None:
        problems = violations(inventory(REPO))
>       assert not problems, "Primary product-copy drift:\n  " + "\n  ".join(
            f"{item.path}:{item.line}: {item.rule_id}: {item.text}"
            for item in problems
        )
E       AssertionError: Primary product-copy drift:
E           web/src/desk/components/Pullout.tsx:124: failure-missing-facts: Could not check this Note on this hub.
E           web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:218: failure-missing-facts: The answer was added, but its exact place in the Note could not be verified. Reload the workspace.
E           web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:428: failure-missing-facts: Default AI context was not applied. {value} could not be attached; the whole set was skipped.
E           web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:474: failure-missing-facts: Could not open this Thought. The Note is unchanged.
E           web/src/pages/cores/AssignmentEditor.tsx:201: failure-missing-facts: (".assignment-candidates button")?.focus()}>Replace unavailable model
E           web/src/pages/cores/AssignmentEditor.tsx:108: legacy-product-nouns: Choose a model chain.
E           web/src/pages/cores/AssignmentEditor.tsx:207: legacy-product-nouns: No custom chain
E           web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:411: promotional-narration: Ready when you are
E       assert not [CopyViolation(rule_id='failure-missing-facts', path='web/src/desk/components/Pullout.tsx', line=124, text='Could not ..., text='Choose a model chain.', reason='Primary UI uses Coder session, Runs on, Agent, Sequence, and Knowledge.'), ...]

tests/unit/test_product_copy.py:48: AssertionError
____________ test_primary_ui_has_no_new_unqualified_ambiguous_terms ____________
[gw8] darwin -- Python 3.13.11 /Users/karol/dev/tools/HoldSpeak/.venv/bin/python3

    def test_primary_ui_has_no_new_unqualified_ambiguous_terms() -> None:
        """Guard visible literals, not compatibility identifiers or historical comments."""
    
        offenders: list[str] = []
        web_roots = [REPO / "web" / "src" / "desk", REPO / "web" / "src" / "pages"]
        swift_root = REPO / "apple" / "App" / "MeetingCapture"
    
        for root in web_roots:
            for path in sorted(root.rglob("*.tsx")):
                for line_no, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), 1
                ):
                    for match in _TS_VISIBLE.finditer(line):
                        value = next((part for part in match.groups() if part), "").strip()
                        if _EXACT_UNQUALIFIED.fullmatch(value):
                            offenders.append(f"{path.relative_to(REPO)}:{line_no}: {value}")
    
        for path in sorted(swift_root.rglob("*.swift")):
            for line_no, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                for value in _SWIFT_VISIBLE.findall(line):
                    if _EXACT_UNQUALIFIED.fullmatch(value.strip()):
                        offenders.append(
                            f"{path.relative_to(REPO)}:{line_no}: {value.strip()}"
                        )
    
>       assert not offenders, (
            "Unqualified ambiguous product terms reached primary UI copy. Use the "
            "registry term or a qualified phrase:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: Unqualified ambiguous product terms reached primary UI copy. Use the registry term or a qualified phrase:
E           web/src/desk/pullouts/editors/RecipeEditor.tsx:91: Context
E       assert not ['web/src/desk/pullouts/editors/RecipeEditor.tsx:91: Context']

tests/unit/test_product_language.py:148: AssertionError
_______ test_product_components_do_not_mutate_global_dom_or_inject_html ________
[gw2] darwin -- Python 3.13.11 /Users/karol/dev/tools/HoldSpeak/.venv/bin/python3

    def test_product_components_do_not_mutate_global_dom_or_inject_html() -> None:
        offenders = []
        for path in sorted(ROOT.rglob("*")):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            text = path.read_text()
            for pattern in (r"document\.(?:querySelector|querySelectorAll)\s*\(", r"\.innerHTML\s*=", r"insertAdjacentHTML\s*\("):
                if re.search(pattern, text):
                    offenders.append(str(path.relative_to(ROOT)))
>       assert not offenders, f"Selector/HTML-owned product state: {sorted(set(offenders))}"
E       AssertionError: Selector/HTML-owned product state: ['desk/pullouts/NotePullout.test.tsx', 'desk/thought-workspace/ThoughtWorkspaceWindow.test.tsx']
E       assert not ['desk/pullouts/NotePullout.test.tsx', 'desk/thought-workspace/ThoughtWorkspaceWindow.test.tsx']

tests/unit/test_web_null_read_guard.py:17: AssertionError
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_workbench_walk.py:46: no hub listening at http://localhost:8778
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [2] tests/e2e/test_hs14104_refinement_glass.py:58: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105_context_glass.py:109: superseded by the Thought Workbench real-path glass
SKIPPED [2] tests/e2e/test_hs14105a_default_context_glass.py:99: superseded by the Thought Workbench real-path glass
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Cvs7o4mBNA/xdist-gw1/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Cvs7o4mBNA/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Cvs7o4mBNA/xdist-gw2/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:101: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
FAILED tests/unit/test_ask_grounding_claims.py::test_flags_an_unsupported_claim_and_not_a_supported_one
FAILED tests/unit/test_ask_grounding_claims.py::test_no_grounding_claims_when_no_context_material
FAILED tests/unit/test_ask_runner_migration.py::test_ask_uses_versioned_contract_hash_runner_and_staged_projection
FAILED tests/e2e/test_hs143_assignments_glass.py::test_assignments_overview_real_hub[populated-1440]
FAILED tests/e2e/test_hs143_assignments_glass.py::test_assignments_overview_real_hub[populated-393]
FAILED tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date - ...
FAILED tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals
FAILED tests/unit/test_inference_setup_capability_truth.py::test_first_and_repeated_reads_do_not_mutate_database_or_config
FAILED tests/unit/test_refinement_coordinator.py::test_live_bound_owner_survives_other_startup_and_late_success_stays_suppressed
FAILED tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift
FAILED tests/unit/test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms
FAILED tests/unit/test_web_null_read_guard.py::test_product_components_do_not_mutate_global_dom_or_inject_html
14 failed, 6674 passed, 53 skipped in 478.92s (0:07:58)
```

## Orchestrator triage note (2026-08-27)

The captured run exits 1 lawfully: 11 of 14 FAILED names are the
inherited baseline; the other three triage as flakes, with one honest
distinction. `test_refinement_coordinator...late_success_stays_suppressed`
and `test_assignments_overview_real_hub[populated-1440]` are ordinary
xdist/serial-green flakes. `test_assignments_overview_real_hub
[populated-393]` is GENUINELY TIMING-FLAKY — it fails ~1-in-3 even
serially. It is Story-13 shipped code (on main), so it is not a
Story-11 regression, but it is not called a load flake either: it is
NAMED FOR STORY 14's closeout intake as a test-stability fix. Story 11
itself: the pre-capture sweep was 6677 passed / 11 failed with ZERO
branch-new on the FIRST sweep (first story this phase — the in-round
cross-cutting-net discipline). Closing opus audit: clean on all seven
dimensions, zero product bugs, one ledger note (stale MCP_SIDECAR
resource-count prose) fixed in the close commit. Transport-only story:
the shots-before-merge law is satisfied vacuously.
