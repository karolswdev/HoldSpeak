# Evidence - HSEGHS001HS104-143-12

- **Story:** HSEGHS001HS104-143-12 - Model Library and Providers
- **Status:** done
- **Date:** 2026-08-25

## Proof

### Captured run — 2026-08-26T05:07:46Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run --python 3.13.11 pytest -q -n auto --ignore=tests/e2e/test_metal.py 2>&1 | tail -120`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 3ed0165079589a75d1586e8d62f7ef1538c0cd10

```text
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
E           docs/MODELS.md:183: legacy-product-nouns: profile binding, endpoint, local path, credential, or assignment state; those
E           docs/MODELS.md:184: legacy-product-nouns: arrive through the later profile and assignment services.
E           docs/MODELS.md:250: legacy-product-nouns: authority stores sparse, ordered chains of at most four
E           docs/MODELS.md:251: legacy-product-nouns: immutable model-profile revisions. Resolution uses the first whole chain at
E           docs/MODELS.md:256: legacy-product-nouns: and previews the exact effective named chain first. Structural compatibility is
E           docs/MODELS.md:258: legacy-product-nouns: and cannot prevent saving an otherwise compatible chain. Assignments, command
E           docs/MODELS.md:263: legacy-product-nouns: their independent ordered chains, boundaries, retry-policy intersections, and
E           web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:411: promotional-narration: Ready when you are
E       assert not [CopyViolation(rule_id='failure-missing-facts', path='web/src/desk/components/Pullout.tsx', line=124, text='Could not ...file and assignment services.', reason='Primary UI uses Coder session, Runs on, Agent, Sequence, and Knowledge.'), ...]

tests/unit/test_product_copy.py:48: AssertionError
____________ test_primary_ui_has_no_new_unqualified_ambiguous_terms ____________
[gw5] darwin -- Python 3.13.11 /Users/karol/dev/tools/HoldSpeak/.venv/bin/python3

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
E           web/src/desk/pullouts/editors/RecipeEditor.tsx:93: Context
E       assert not ['web/src/desk/pullouts/editors/RecipeEditor.tsx:93: Context']

tests/unit/test_product_language.py:148: AssertionError
_______ test_product_components_do_not_mutate_global_dom_or_inject_html ________
[gw1] darwin -- Python 3.13.11 /Users/karol/dev/tools/HoldSpeak/.venv/bin/python3

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
SKIPPED [1] tests/uat/test_mesh_dispatch.py:85: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7DZogcayih/xdist-gw1/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_grounding_rails_live.py:35: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:54: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_grounding_rails_live.py:71: holdspeak not in the project map on this machine
SKIPPED [1] tests/integration/test_rails_observer_live.py:37: no rail events on this machine to summarize
SKIPPED [1] tests/integration/test_rails_observer_live.py:72: no rail events on this machine
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7DZogcayih/xdist-gw2/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.7DZogcayih/xdist-gw2/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
SKIPPED [1] tests/uat/test_induction_integration_43.py:107: live .43 model proof is opt-in: set HOLDSPEAK_UAT_LIVE_43=1 (it runs a real extraction on the LAN model and takes minutes)
SKIPPED [1] tests/uat/test_induction_integration_43.py:118: the UAT node harness cannot pair a mesh worker: since HS-131-16 `mesh serve` requires an imported node pairing (hub pin + node token) and refuses the owner token, but nodes.py still spawns it with --token-env HOLDSPEAK_HUB_TOKEN and never pairs
SKIPPED [10] tests/e2e/test_meeting_transcription.py: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_mermaid_renders.py:101: mermaid renderer unavailable in this env: core/lib/esm/puppeteer/node/BrowserLauncher.js:55:28)
    at async run (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:862:19)
    at async cli (file:///Users/karol/.npm/_npx/668c188756b835f3/node_modules/@mermaid-js/mermaid-cli/src/index.js:374:3)
FAILED tests/unit/test_ask_grounding_claims.py::test_flags_an_unsupported_claim_and_not_a_supported_one
FAILED tests/unit/test_ask_grounding_claims.py::test_no_grounding_claims_when_no_context_material
FAILED tests/unit/test_ask_runner_migration.py::test_ask_uses_versioned_contract_hash_runner_and_staged_projection
FAILED tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_leaks_roadmap_vocabulary
FAILED tests/uat/test_build_ledger.py::test_committed_ledger_is_up_to_date - ...
FAILED tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_modules_stay_within_line_budget
FAILED tests/unit/test_kernel_effect_fence.py::test_kernel_broker_has_zero_driver_specific_conditionals
FAILED tests/unit/test_inference_setup_capability_truth.py::test_first_and_repeated_reads_do_not_mutate_database_or_config
FAILED tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift
FAILED tests/unit/test_product_language.py::test_primary_ui_has_no_new_unqualified_ambiguous_terms
FAILED tests/unit/test_web_null_read_guard.py::test_product_components_do_not_mutate_global_dom_or_inject_html
12 failed, 6635 passed, 53 skipped in 452.18s (0:07:32)
```

## Orchestrator triage note (2026-08-26)

The captured run exits 1 lawfully: all 12 FAILED names are in the
inherited baseline (`assets/story-08-inherited-failure-baseline.txt`) —
**ZERO branch-new**. Three sweeps ran this story: №1 (6626/21: 12
inherited + 9 branch-new around the surface replacement → all fixed in
commit 4a1b6034, incl. the restored Runs-on owner law), №2 (6633/14: 12
inherited + 2 xdist load flakes, each serial-green ×2), and this
captured №3 (6635/12, the inherited set exactly). Story bar: three opus
audits (server half; UI half + acceptance; plus the Story-10-era matrix
fork), all ZERO product bugs; two cosmetic ledger notes (44px assertion
width coverage, reduced-motion spot check). Real-hub review shots at
1440/393/200% in assets/story-12-shots/ went to the owner per the
shots-before-merge law. The owner-DB generator incident is recorded in
the story Progress log — the integrity guard refused, forensics proved
zero damage. Merge additionally awaits the owner's screenshot verdict.
