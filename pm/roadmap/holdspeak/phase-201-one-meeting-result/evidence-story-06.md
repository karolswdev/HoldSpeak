# Evidence - HS-201-06

- **Story:** HS-201-06 - Plain words on the path
- **Status:** done
- **Date:** 2026-09-19

## Proof

### Captured run — 2026-09-19T22:48:28Z

- **Command:** `sh -c cd web && npx vitest run src/desk/surface/__tests__/count.test.ts src/meetings/MeetingIntelRecovery.test.tsx src/pages/cores/__tests__/ChangePlacesCore.test.tsx 2>&1 | tail -5`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f68e722fbc45e4f4afd68c51c0ca514762508b57

```text
 Test Files  3 passed (3)
      Tests  18 passed (18)
   Start at  16:48:29
   Duration  1.31s (transform 522ms, setup 258ms, import 746ms, tests 554ms, environment 899ms)
```

### Captured run — 2026-09-19T22:48:30Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.zI1mhVmRqW uv run pytest -q tests/unit/test_product_copy.py tests/unit/test_product_language.py tests/unit/test_ux_canon_ratchet.py tests/unit/test_ux_canon_scan.py tests/unit/test_phase200_canon_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f68e722fbc45e4f4afd68c51c0ca514762508b57

```text
........................................................................ [ 41%]
........................................................................ [ 83%]
....F.....F.................                                             [100%]
=================================== FAILURES ===================================
_________ test_docs_do_not_restore_retired_inference_setup_vocabulary __________

    def test_docs_do_not_restore_retired_inference_setup_vocabulary() -> None:
        offenders: list[str] = []
        for path in _all_docs_and_readme():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                match = _RETIRED_INFERENCE_VOCAB.search(line)
                if match:
                    offenders.append(f"{path.relative_to(_REPO)}:{lineno}: {match.group(0)!r}")
    
>       assert not offenders, (
            "Retired inference setup vocabulary returned to docs/ or README. Use "
            "Models for availability and Assignments for job selection instead:\n  "
            + "\n  ".join(offenders)
        )
E       AssertionError: Retired inference setup vocabulary returned to docs/ or README. Use Models for availability and Assignments for job selection instead:
E           docs/internal/inventory-2026-09-19/02-capabilities.md:500: 'inference_target_id'
E           docs/internal/inventory-2026-09-19/02-capabilities.md:531: 'inference_target_id'
E           docs/internal/inventory-2026-09-19/03-roadmap.md:75: 'Download & use'
E       assert not ["docs/internal/inventory-2026-09-19/02-capabilities.md:500: 'inference_target_id'", "docs/internal/inventory-2026-09-...2-capabilities.md:531: 'inference_target_id'", "docs/internal/inventory-2026-09-19/03-roadmap.md:75: 'Download & use'"]

tests/unit/test_doc_drift_guard.py:121: AssertionError
________________ test_no_live_doc_has_a_dangling_relative_link _________________

    def test_no_live_doc_has_a_dangling_relative_link() -> None:
        offenders: list[str] = []
        for path in _maintained_docs():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for target in _MD_LINK.findall(line):
                    target = target.strip()
                    # Skip external, anchor-only, and non-doc targets.
                    if target.startswith(("http://", "https://", "mailto:", "#", "<")):
                        continue
                    # Drop any #fragment / ?query suffix.
                    rel = target.split("#", 1)[0].split("?", 1)[0]
                    if not rel:
                        continue
                    resolved = (path.parent / rel).resolve()
                    if not resolved.exists():
                        offenders.append(
                            f"{path.relative_to(_REPO)}:{lineno}: -> {target}"
                        )
    
>       assert not offenders, (
            "A maintained doc links a path that does not exist (dangling relative link). "
            "Fix the path or the move:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: A maintained doc links a path that does not exist (dangling relative link). Fix the path or the move:
E           docs/internal/checks/constitution-seven-tenets-astra.md:14: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:25
E           docs/internal/checks/constitution-seven-tenets-astra.md:16: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/DOCS_STYLE.md:10
E           docs/internal/checks/constitution-seven-tenets-astra.md:16: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:35
E           docs/internal/checks/constitution-seven-tenets-astra.md:18: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:39
E           docs/internal/checks/constitution-seven-tenets-astra.md:20: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:102
E           docs/internal/checks/constitution-seven-tenets-astra.md:20: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:163
E           docs/internal/checks/constitution-seven-tenets-astra.md:22: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:125
E           docs/internal/checks/constitution-seven-tenets-astra.md:22: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:27
E           docs/internal/checks/constitution-seven-tenets-astra.md:24: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:134
E           docs/internal/checks/constitution-seven-tenets-astra.md:24: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:115
E           docs/internal/checks/constitution-seven-tenets-astra.md:24: -> /Users/karol/dev/tools/HoldSpeak/AGENTS.md:33
E           docs/internal/checks/constitution-seven-tenets-astra.md:26: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:89
E           docs/internal/checks/constitution-seven-tenets-astra.md:26: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:109
E           docs/internal/checks/constitution-seven-tenets-astra.md:26: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/INVENTORY-2026-09-19.md:13
E           docs/internal/checks/constitution-seven-tenets-astra.md:28: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/ORCHESTRATION.md:51
E           docs/internal/checks/constitution-seven-tenets-astra.md:28: -> /Users/karol/dev/tools/HoldSpeak/CLAUDE.md:33
E           docs/internal/checks/constitution-seven-tenets-astra.md:28: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:194
E           docs/internal/checks/constitution-seven-tenets-astra.md:88: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:24
E           docs/internal/checks/constitution-seven-tenets-astra.md:88: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:39
E           docs/internal/checks/constitution-seven-tenets-astra.md:90: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/checks/constitution-seven-tenets-astra.md:51
E           docs/internal/checks/constitution-seven-tenets-astra.md:90: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:23
E           docs/internal/checks/constitution-seven-tenets-astra.md:90: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/ORCHESTRATION.md:234
E           docs/internal/checks/constitution-seven-tenets-astra.md:92: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/checks/constitution-seven-tenets-astra.md:43
E           docs/internal/checks/constitution-seven-tenets-astra.md:92: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/ORCHESTRATION.md:52
E           docs/internal/checks/constitution-seven-tenets-astra.md:92: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:206
E           docs/internal/checks/constitution-seven-tenets-astra.md:94: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/checks/constitution-seven-tenets-astra.md:66
E           docs/internal/inventory-2026-09-19/06-check-astra.md:15: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:220
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_deferred_queue_binding.py:126
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/inference_service_route_policy.py:93
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py:361
E           docs/internal/inventory-2026-09-19/06-check-astra.md:17: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:140
E           docs/internal/inventory-2026-09-19/06-check-astra.md:19: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/meeting_intel_service.py:81
E           docs/internal/inventory-2026-09-19/06-check-astra.md:19: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:614
E           docs/internal/inventory-2026-09-19/06-check-astra.md:19: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:45
E           docs/internal/inventory-2026-09-19/06-check-astra.md:21: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:39
E           docs/internal/inventory-2026-09-19/06-check-astra.md:21: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:67
E           docs/internal/inventory-2026-09-19/06-check-astra.md:21: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:157
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/features/project-room/recall/RecallFace.tsx:84
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/chair/ChairHome.tsx:1296
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/features/project-room/useProjectRoomController.ts:33
E           docs/internal/inventory-2026-09-19/06-check-astra.md:23: -> /Users/karol/dev/tools/HoldSpeak/web/src/pages/cores/PeopleCore.tsx:456
E           docs/internal/inventory-2026-09-19/06-check-astra.md:25: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/watch_service.py:102
E           docs/internal/inventory-2026-09-19/06-check-astra.md:25: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/project_door_service.py:308
E           docs/internal/inventory-2026-09-19/06-check-astra.md:25: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/services/reaction_service.py:219
E           docs/internal/inventory-2026-09-19/06-check-astra.md:27: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:311
E           docs/internal/inventory-2026-09-19/06-check-astra.md:27: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/01-faces.md:410
E           docs/internal/inventory-2026-09-19/06-check-astra.md:29: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts:581
E           docs/internal/inventory-2026-09-19/06-check-astra.md:29: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/verbRegistry.ts:232
E           docs/internal/inventory-2026-09-19/06-check-astra.md:29: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/05-desk-census.md:176
E           docs/internal/inventory-2026-09-19/06-check-astra.md:31: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/threads.ts:1083
E           docs/internal/inventory-2026-09-19/06-check-astra.md:31: -> /Users/karol/dev/tools/HoldSpeak/web/src/desk/pullouts/ThreadPullout.tsx:640
E           docs/internal/inventory-2026-09-19/06-check-astra.md:33: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/03-roadmap.md:140
E           docs/internal/inventory-2026-09-19/06-check-astra.md:33: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:106
E           docs/internal/inventory-2026-09-19/06-check-astra.md:33: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/INVENTORY-2026-09-19.md:361
E           docs/internal/inventory-2026-09-19/06-check-astra.md:89: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:70
E           docs/internal/inventory-2026-09-19/06-check-astra.md:91: -> /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/THE-TUESDAY-ARC.md:54
E           docs/internal/inventory-2026-09-19/06-check-astra.md:91: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/UX-CANON.md:30
E           docs/internal/inventory-2026-09-19/06-check-astra.md:91: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:29
E           docs/internal/inventory-2026-09-19/06-check-astra.md:93: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:54
E           docs/internal/inventory-2026-09-19/06-check-astra.md:93: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:66
E           docs/internal/inventory-2026-09-19/06-check-astra.md:93: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:75
E           docs/internal/inventory-2026-09-19/06-check-astra.md:95: -> /Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py:361
E           docs/internal/inventory-2026-09-19/06-check-astra.md:97: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/inventory-2026-09-19/06-check-astra.md:56
E       assert not ['docs/internal/checks/constitution-seven-tenets-astra.md:14: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTI...cks/constitution-seven-tenets-astra.md:20: -> /Users/karol/dev/tools/HoldSpeak/docs/internal/CONSTITUTION.md:163', ...]

tests/unit/test_doc_drift_guard.py:269: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_doc_drift_guard.py::test_docs_do_not_restore_retired_inference_setup_vocabulary
FAILED tests/unit/test_doc_drift_guard.py::test_no_live_doc_has_a_dangling_relative_link
2 failed, 170 passed in 23.36s
```
