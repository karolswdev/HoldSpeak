# Main baseline — initial full run

Source: `fc12a18d56868fc95a3310eb9cf99c0421a25730`, isolated HOME and Node 22.21.0.

Result: 13,452 passed, 47 failed, 117 skipped, 4 xfailed, 443 errors. Disk exhaustion invalidates 455 failure/error entries as regression evidence. The remaining 35 entries below are comparison candidates only; final classification belongs to the lane ledger.

[Raw full output](main-full-initial.txt) · [JUnit result](main-full-initial.xml)

| Test | Observed failure |
|---|---|
| `tests/integration/test_web_history_archive.py::test_history_keeps_approval_and_export_governance` | AssertionError: assert 'ConfirmVerb' in '// HS-170-04 — the Meetings face, rewritten to the settled design.\n// Board: display headline + Record/Import + stre.. |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_filtered[393-852]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. |
| `tests/unit/test_decisions.py::test_meeting_delete_severs_source_without_deleting_decision` | AssertionError: assert 'linked' == 'source_deleted' |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_quiet[393-852]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_falls_through_to_the_saved_meeting_when_no_live_session_owns_it` | AttributeError: '_ArchiveSpy' object has no attribute '_connection' |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_saved_meetings_still_work_with_no_live_session_bound_at_all` | AttributeError: '_ArchiveSpy' object has no attribute '_connection' |
| `tests/unit/test_hs172_people_sources.py::TestBriefEnrichment::test_last_meeting_present` | sqlite3.OperationalError: no such column: parked |
| `tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440` | AssertionError: Ship the queue for platform on schedule |
| `tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393` | AssertionError: [] |
| `tests/unit/test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires` | AssertionError: assert frozenset({'c...'press', ...}) == {'click', 'cl... 'press', ...} |
| `tests/integration/test_phase200_recipe_catalog.py::TestTheScheduledOwnerReallyFires::test_the_sweep_is_driven_by_a_wall_clock_loop` | AssertionError: ('Tick every 60 seconds; on each tick, check if a sweep is due.', None, ('get_database', 'get_observer'), ('Principal', 'PrincipalKind'), ('Hear |
| `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_brief.generated_empty]` | RuntimeError: hub died on boot: |
| `tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer` | AssertionError: assert {'holdspeak/d...acement', ...} == {'holdspeak/d...acement', ...} |
| `tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css` | AssertionError: the left rail is banned (HS-101 canon rule 6) — remove the border-left and use the aerogel inset (.surface-aerogel / --desk-aerogel-* tokens) in |
| `tests/unit/test_people_brief.py::TestBriefAggregation::test_brief_linked_meetings_via_uid_chain` | sqlite3.OperationalError: no such column: parked |
| `tests/unit/test_people_brief.py::TestBriefAggregation::test_brief_unlinked_meeting_count_f11` | sqlite3.OperationalError: no such column: parked |
| `tests/unit/test_people_brief.py::TestWriteCountSpy::test_brief_writes_zero_rows_to_plain_db` | sqlite3.OperationalError: no such column: parked |
| `tests/unit/test_people_brief.py::TestCommitmentTriadUntouched::test_action_items_unchanged_after_brief` | sqlite3.OperationalError: no such column: parked |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:UX-CANON.md:179]` | AssertionError: a documentation claim that used to HOLD is now FALSE: docs/internal/UX-CANON.md:179 |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:useDeskChangedRefresh.ts:15]` | AssertionError: a documentation claim that used to HOLD is now FALSE: web/src/desk/useDeskChangedRefresh.ts:15 |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner` | AssertionError: a pinned operation-contract site moved or is gone; re-read it and re-anchor: stale=['holdspeak/mcp/resources.py:578\|read_resource\|call', 'hold |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers` | AssertionError: shared Ask/Recipe helper callers changed; classify the public semantic operation rather than assigning the helper one false capability. |
| `tests/unit/test_philo4_01_atlas_contracts.py::test_the_reload_claim_points_at_the_quiet_branch` | AssertionError: ({'claim': 'a brief with nothing untriaged keeps its own section, headline and Generate after a reload (the quiet bran...n className="surface-re |
| `tests/unit/test_philo3_summary_detail.py::test_summary_wire_fixture_matches_real_producer_states` | AssertionError: assert [{'detail': {...nal_failure'}] == [{'detail': {...nal_failure'}] |
| `tests/e2e/test_hs141_thought_workbench_glass.py::test_thought_workbench_real_glass[393]` | AssertionError: {'body': '', 'errors': [], 'console': [], 'requests': []} |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[1440]` | AssertionError: Headline should read 'Nothing needs you' on door error: Coverage incomplete |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[393]` | AssertionError: Headline should read 'Nothing needs you' on door error: Coverage incomplete |
| `tests/unit/test_philo6_01_import_badge.py::test_empty_vtt_import_leaves_import_failed_on_the_wire` | AssertionError: the vitest fixture drifted from the real producer; re-run with PHILO6_WRITE_FIXTURE=1 |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]` | AssertionError: ('fail', 'TRIGGER lifecycle failed: ui step click not delivered: its guard {\'visible\': \'.undo-receipt.is-pending\',... at delivery (.undo-rec |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]` | AssertionError: ('fail', "TRIGGER lifecycle failed: ui step click not delivered: its guard {'visible': '.undo-receipt.is-pending', 'te...ndo', 'seconds_left': { |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]` | AssertionError: ('fail', 'TRIGGER lifecycle failed: ui step click not delivered: its guard {\'visible\': \'.undo-receipt.is-pending\',... at delivery (.undo-rec |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]` | AssertionError: ('fail', "TRIGGER lifecycle failed: ui step click not delivered: its guard {'visible': '.undo-receipt.is-pending', 'te...ndo', 'seconds_left': { |
| `tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[393]` | AssertionError: assert 19297 > 20000 |
| `tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again` | AssertionError: ['Run summary', 'Decide'] |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. |
