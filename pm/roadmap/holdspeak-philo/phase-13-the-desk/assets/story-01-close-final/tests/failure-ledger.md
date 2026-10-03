# B0 close — full-suite failure ledger

OPEN follow-up debt, 2026-10-03. B0's 18 core cases pass; this ledger does
not claim the whole product or the full phase is green. Open tracking
home: [BACKLOG B0-L6](../../../../BACKLOG.md). Astra owns the runtime,
contract, census and fixture work; Muad’Dib owns the face work. The exact
home on each row remains open after this story closes.

Full Python on `95ee5fe31` (product code identical to main `050ce14d`):
**104 failed, 13,907 passed, 117 skipped, four xfailed, four setup errors**
in 2,345.41 s. [Complete output](full-python.txt), [JUnit](full-python.xml),
[derived names/messages/full traces](full-failures.json). All runs used
isolated HOME; the full run used `-n auto --dist loadfile` and excluded
Metal. Vitest also ran during part of this run. Resource contention is
not used as a blanket explanation for the failures.

There are **108 red nodes**. Fifty-five names recur from the
[previous ledger](../../pr757-astra/failure-ledger.md); a matching name
alone does not establish the current cause. Every one of the 29 unit
failures was [collected](baseline-unit-collect.txt) and
[rerun](baseline-unit-run.txt) on exact main
`050ce14d6fc3c2f029d3dff75d37686147044e03` in a separate worktree with the
same pinned environment and an explicit baseline `holdspeak.__file__`.
**28 reproduce with the same causes:** 25 exact messages, two changes in
unordered-set printing, one generated project ID. The primitive-envelope
node passes once. [Comparison data](baseline-unit-results.json).
The remaining **80** causes are unclassified against exact main: 32
names recur from the prior record, 48 are new to it. No generic timeout is
called a product regression or a flake without more proof.

Classification duty: (a) old-posture fences must be checked against the
current real producer before changing an oracle; (b) product defects must
be fixed in their face/runtime home, never hidden by test edits; (c) the
six initial web assertion failures are intermittent by two serial-green
runs below. The 28 same-cause main reproductions are inherited by this
closure, not declarations that those failures are acceptable product
behavior. Remaining a/b/c decisions are open at the named homes.

## Readings that matter to the owner

- **HS202 first use, both widths:** Keep as Note is pressed, but the First
  dictation note is not observed (`test_hs202_first_use_smoke.py:259-261`).
  This is a post-action handoff failure, not merely an unopened test page.
  Home: FirstWords / Desk staged-note handoff; exact subcause unverified.
- **People, four new names:** the plain test database omits `meetings.parked`
  (`tests/unit/test_hs172_people_sources.py:70-72`); the real query requires
  it (`holdspeak/services/people_service.py:581-590`). The wrapper at
  `:608-609` reports `people_plaintext_unavailable`. All four reproduce on
  exact main. Home: HS172/B4 database fixture/schema contract; choose the
  repair against the real producer, not by hiding the missing field.
- **PHILO-8:** 12 new List/Rename/Zone names fail opening a face, palette
  or field; 21 Delete/Workbench names also include post-action waits.
  The resize case records no DELETE after widening
  (`tests/e2e/test_philo8_one_delete_glass.py:1019-1029`). Keep face/rig
  setup and delete/rename lifecycle as separate follow-up homes. These
  are not all setup-only failures.
- **B2 at 393:** the new failure stops before the draft assertion, after
  Decide is pressed but before Decision title appears
  (`tests/e2e/test_philo13_07_remembers_glass.py:324-328`). Its immediate
  home is B2 glass touch/setup investigation; it is not B0-F2 (Dossier and
  Terminal), and this trace does not prove a persistence regression.
- **J10:** three actual atlas smoke cases stop at a missing Chair or
  Generate again door. They do not reach the idempotency or empty-brief
  predicate (`tests/e2e/test_graph_walk_smoke.py:59-76,102`). Home: J10
  arrival/route setup and graph rig.
- **Room:** both new failures occur reopening the Room after first Copy;
  no second delivery row is proved. Home: PHILO-9 staged-open/return path.
- **Primitive envelope:** full-run deployment data has v2 fields while
  the envelope expects v1 `model_path`; the exact-main selected run
  passes once. Home: primitive contract and fixture isolation; no flake
  or product-regression classification yet.
- **UX ratchet:** PeopleCore raw IDs rise 12→13 (total 17→18). This
  reproduces on exact main. Home: People face / canon ratchet, Tenet 4;
  no ceiling increase is authorized by this closure.
- **Other new names:** HS152 resolves two composer regions (test locator
  scoping); HS176 1440 does not apply the expected taught correction;
  PHILO-7 reaches different setup/receipt boundaries at the two widths;
  PHILO-3 stops before Search. The exact-node table preserves each home.

## Exact Python nodes

| Node | Current reading | Main comparison | Open follow-up home |
|---|---|---|---|
| `tests/unit/test_philo10_atlas.py::test_the_counts_over_every_atlas_file` | AssertionError: assert {'atlas-h-c5....son': 22, ...} == {'atlas-phase...json': 2, ...} | Same cause on exact main | Graph atlas census maintenance; Astra |
| `tests/unit/test_philo9_atlas.py::test_the_counts_over_every_atlas_file` | AssertionError: assert {'atlas-h-c5....son': 22, ...} == {'atlas-phase...json': 2, ...} | Same cause on exact main | Graph atlas census maintenance; Astra |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:UX-CANON.md:179]` | AssertionError: a documentation claim that used to HOLD is now FALSE: docs/internal/UX-CANON.md:179 | Same cause on exact main | UX canon and PHILO bus coverage / registered documentation claims |
| `tests/unit/test_phase200_doc_claims.py::test_registered_claim_matches_its_state[holds:useDeskChangedRefresh.ts:15]` | AssertionError: a documentation claim that used to HOLD is now FALSE: web/src/desk/useDeskChangedRefresh.ts:15 | Same cause on exact main | UX canon and PHILO bus coverage / registered documentation claims |
| `tests/unit/test_graph_walk_calibration.py::test_the_ui_vocabulary_is_closed_and_blocks_before_anything_fires` | AssertionError: assert frozenset({'c...'press', ...}) == {'click', 'cl... 'press', ...} | Same cause on exact main | Graph rig / action-vocabulary calibration fence |
| `tests/unit/test_hs172_people_sources.py::TestBriefEnrichment::test_watch_summary_prs_waiting` | holdspeak.services.people_service.PeopleServiceError: people_plaintext_unavailable | Same cause on exact main | Astra HS172/B4 plain-database fixture/schema contract (missing parked masked as plaintext error) |
| `tests/unit/test_hs172_people_sources.py::TestBriefEnrichment::test_watch_summary_jira_overdue` | holdspeak.services.people_service.PeopleServiceError: people_plaintext_unavailable | Same cause on exact main | Astra HS172/B4 plain-database fixture/schema contract (missing parked masked as plaintext error) |
| `tests/unit/test_hs172_people_sources.py::TestBriefEnrichment::test_watch_summary_no_writes` | holdspeak.services.people_service.PeopleServiceError: people_plaintext_unavailable | Same cause on exact main | Astra HS172/B4 plain-database fixture/schema contract (missing parked masked as plaintext error) |
| `tests/unit/test_hs172_people_sources.py::TestBriefEnrichment::test_last_meeting_present` | sqlite3.OperationalError: no such column: parked | Same cause on exact main | People / B4 plain-database fixture schema |
| `tests/unit/test_hs172_people_sources.py::TestNoPronounInWire::test_watch_summary_no_pronouns` | holdspeak.services.people_service.PeopleServiceError: people_plaintext_unavailable | Same cause on exact main | Astra HS172/B4 plain-database fixture/schema contract (missing parked masked as plaintext error) |
| `tests/integration/test_phase200_recipe_catalog.py::TestTheScheduledOwnerReallyFires::test_the_sweep_is_driven_by_a_wall_clock_loop` | AssertionError: ('Tick every 60 seconds; on each tick, check if a sweep is due.', None, ('get_database', 'get_observer'), ('Principal', 'PrincipalKind'), ('HeartbeatService',), ('observer',), ...) | Prior name only; current cause unclassified | Cadence / scheduled-loop source contract |
| `tests/unit/test_philo4_01_atlas_contracts.py::test_the_reload_claim_points_at_the_quiet_branch` | AssertionError: ({'claim': 'a brief with nothing untriaged keeps its own section, headline and Generate after a reload (the quiet bran...n className="surface-receipt-line" data-testid="arrival-brief-date"> | Same cause on exact main | PHILO 4 Brief atlas / source-branch claim |
| `tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_source_stats_from_db` | AttributeError: '_FakeEvent' object has no attribute 'attendees' | Same cause on exact main | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestCalendarSourcesRoute::test_matched_this_week` | AttributeError: '_FakeEvent' object has no attribute 'attendees' | Same cause on exact main | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestSourcesPayloadClocks::test_event_count_names_what_it_counts` | AttributeError: '_FakeEvent' object has no attribute 'attendees' | Same cause on exact main | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestSourcesPayloadClocks::test_last_read_is_an_instant_and_a_local_clock` | AttributeError: '_FakeEvent' object has no attribute 'attendees' | Same cause on exact main | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestSourcesPayloadClocks::test_matched_this_week_uses_the_local_week` | AttributeError: '_FakeEvent' object has no attribute 'attendees' | Same cause on exact main | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/unit/test_hs175_calendar_sources.py::TestDstEdgeSources::test_matched_this_week_across_fall_back` | AttributeError: '_FakeEvent' object has no attribute 'attendees' | Same cause on exact main | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-9 Room staged-open/return after first Copy; second row unobserved |
| `tests/e2e/test_philo9_03_room_face_glass.py::TestRoomFaceGlass::test_copy_then_mark_delivered_twice_reads_back_two_rows[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-9 Room staged-open/return after first Copy; second row unobserved |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_stream[393-852]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | Prior name only; current cause unclassified | HS176 Journal / 393 tab access |
| `tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named[393]` | AssertionError: ['21-lost-answer-a-393: {\'sel\': "[data-testid=send-open][data-destination=\'Folder Payments\'] [data-testid=send-retry]", \'ok\': False, \'why\': \'covered\', \'text\': \'Retry\'}'] | Prior name only; current cause unclassified | PHILO 10 Send / compact lost-answer face; Muad’Dib |
| `tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_1440` | AssertionError: Dock badge should be absent at zero | Prior name only; current cause unclassified | HS171 system shade / retained face fences |
| `tests/e2e/test_hs171_shade_glass.py::test_shade_quiet_393` | AssertionError: Dock badge should be absent at zero | Prior name only; current cause unclassified | HS171 system shade / retained face fences |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_row_open[393-852]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | Prior name only; current cause unclassified | HS176 Journal / 393 tab access |
| `tests/unit/test_decisions.py::test_meeting_delete_severs_source_without_deleting_decision` | AssertionError: assert 'linked' == 'source_deleted' | Same cause on exact main | Decision source lifecycle / PHILO A1 Park semantics |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_filtered[393-852]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | Prior name only; current cause unclassified | HS176 Journal / 393 tab access |
| `tests/unit/test_product_copy.py::test_primary_copy_has_no_prohibited_operational_drift` | AssertionError: Primary product-copy drift: | Same cause on exact main | PHILO 10 Send refusal copy; Muad’Dib |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-before_guard]` | AssertionError: ('fail', 'TRIGGER lifecycle failed: ui step click not delivered: its guard {\'visible\': \'.undo-receipt.is-pending\',... at delivery (.undo-receipt.is-pending is not visible; "Undo" not in "… | Prior name only; current cause unclassified | PHILO 8 rig / expired undo-window outcome |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_falls_through_to_the_saved_meeting_when_no_live_session_owns_it` | AttributeError: '_ArchiveSpy' object has no attribute '_connection' | Prior name only; current cause unclassified | Live action-item triage / archive test double |
| `tests/integration/test_live_action_item_triage.py::TestLiveFirstResolutionOrder::test_saved_meetings_still_work_with_no_live_session_bound_at_all` | AttributeError: '_ArchiveSpy' object has no attribute '_connection' | Prior name only; current cause unclassified | Live action-item triage / archive test double |
| `tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer` | AssertionError: assert {'holdspeak/d...acement', ...} == {'holdspeak/d...acement', ...} | Same cause on exact main | Phase 143 routing authority census / stale source classification |
| `tests/e2e/test_hs176_journal_glass.py::test_journal_quiet[393-852]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | Prior name only; current cause unclassified | HS176 Journal / 393 tab access |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[1440-click_wait]` | AssertionError: the delay was never injected (the receipt never showed) | Prior name only; current cause unclassified | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[1440]` | AssertionError: Headline should read 'Nothing needs you' on door error: Coverage incomplete | Prior name only; current cause unclassified | HS144 Door / error headline |
| `tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_a_name_the_owner_chose_is_skipped_not_renamed[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 Zone naming / Floor return + Astra rig setup |
| `tests/e2e/test_hs144_door_glass.py::test_hs144_door_empty_and_error_shots[393]` | AssertionError: Headline should read 'Nothing needs you' on door error: Coverage incomplete | Prior name only; current cause unclassified | HS144 Door / error headline |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-before_guard]` | AssertionError: the delay was never injected (the receipt never showed) | Prior name only; current cause unclassified | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[floor-1440]` | playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/integration/test_web_setup_route.py::test_dashboard_owns_first_value_without_redirecting` | assert 'setup?.arrival_required' in "// The Desk route — the web app's front door (HS-73-02).\n//\n// React + Vite in the one Web tree. Full-bleed: the wo...SnapGhost />}\n      {!arrivalRequired && <Expose … | Prior name only; current cause unclassified | Desk arrival / C5 source-fence maintenance; Astra |
| `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_again.same_day_idempotent]` | AssertionError: case.j10.arrival_generate_again.same_day_idempotent: the clicked Generate again's OWN response is the identity, and the face shows what it returned | New to this ledger; cause unclassified | Astra graph rig + Muad’Dib Chair/Brief doors; J10 arrival and route cases |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_taken_name_shows_the_chip_on_the_floor[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/e2e/test_philo8_03_then_guard.py::test_a_follow_up_after_the_window_is_blocked[393-click_wait]` | AssertionError: the delay was never injected (the receipt never showed) | Prior name only; current cause unclassified | PHILO 8 rig / expired undo-window outcome |
| `tests/e2e/test_philo13_07_remembers_glass.py::TestSliceTwoReturns::test_families_and_drafts_return_and_closed_stay_gone[393]` | playwright._impl._errors.TimeoutError: Locator.fill: Timeout 30000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib B2 glass touch/setup; Decision title absent after Decide; not proven persistence regression |
| `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.arrival_generate_brief.generated_empty]` | AssertionError: case.j10.arrival_generate_brief.generated_empty: the empty brief says so on the face | New to this ledger; cause unclassified | Astra graph rig + Muad’Dib Chair/Brief doors; J10 arrival and route cases |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-list-422]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_leaving_the_face_inside_the_window_commits_the_delete[list-1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_graph_walk_smoke.py::test_the_rig_drives_the_real_atlas[case.j10.route_generate_again.same_day_same_id]` | AssertionError: case.j10.route_generate_again.same_day_same_id: the second POST /api/brief/generate returns the SAME brief id that GET /api/brief/latest held before it | New to this ledger; cause unclassified | Astra graph rig + Muad’Dib Chair/Brief doors; J10 arrival and route cases |
| `tests/unit/test_primitive_contract.py::TestHubEmissionsValidate::test_pull_body_validates_against_changeset_envelope` | AssertionError: pull body violates the ChangeSet envelope: ["deployment_revisions/0/value: Additional properties are not allowed ('architecture', 'artifact_id', 'capability_sha256', 'context_ceiling', 'forma… | One main pass; cause unclassified | Astra ChangeSet envelope / deployment fixture isolation; one main pass does not classify the full-run failure |
| `tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[393]` | AssertionError: assert 19678 > 20000 | Prior name only; current cause unclassified | HS163 Steward glass; Muad’Dib |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-list-network]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[1440-list-to-spatial]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 Zone naming / Floor return + Astra rig setup |
| `tests/e2e/test_hs163_steward_glass.py::test_stop_mid_run[1440]` | playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 15000ms exceeded. | Prior name only; current cause unclassified | HS163 Steward glass; Muad’Dib |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-422]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[1440-floor-chair-floor]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 Zone naming / Floor return + Astra rig setup |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_failed_save_shows_in_the_chip_slot[1440-spatial-network]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_chair_withholds_delete_with_its_reason[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-1440]` | playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[list-393]` | playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_01_zone_name_glass.py::TestZoneNameGlass::test_no_stale_rename_field_after_a_face_change[393-floor-chair-floor]` | playwright._impl._errors.TimeoutError: Locator.click: Timeout 30000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 Zone naming / Floor return + Astra rig setup |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[floor-1440]` | playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_repeated_delete_never_offers_a_false_undo[floor-393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/unit/test_interior_canon_guard.py::test_no_left_border_rails_in_web_css` | AssertionError: the left rail is banned (HS-101 canon rule 6) — remove the border-left and use the aerogel inset (.surface-aerogel / --desk-aerogel-* tokens) instead: | Same cause on exact main | UX canon / CSS rail guard |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner` | AssertionError: a pinned operation-contract site moved or is gone; re-read it and re-anchor: stale=['holdspeak/mcp/resources.py:578\|read_resource\|call', 'holdspeak/mcp/tools.py:653\|_primitive_list\|call', 'ho… | Same cause on exact main | Phase 143 inference capability census / stale anchors and classifications |
| `tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers` | AssertionError: shared Ask/Recipe helper callers changed; classify the public semantic operation rather than assigning the helper one false capability. | Same cause on exact main | Phase 143 inference capability census / stale anchors and classifications |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 5000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_failed_refresh_keeps_the_pending_delete_and_its_undo[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_the_foot_never_covers_the_last_rows[393]` | playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[list-1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 18000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[list-393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 18000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_refused_delete_says_so_with_retry[floor-1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_park_works_again_after_a_refusal[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[1440]` | playwright._impl._errors.TimeoutError: Timeout 15000ms exceeded while waiting for event "response" | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_park_works_again_after_a_refusal[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/unit/test_philo3_summary_detail.py::test_summary_wire_fixture_matches_real_producer_states` | AssertionError: assert [{'detail': {...nal_failure'}] == [{'detail': {...nal_failure'}] | Same cause on exact main | PHILO 3 Meetings / summary wire fixture |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_park_after_a_refusal_offers_restore[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_a_refusal_after_the_field_closed_goes_to_the_write_receipt[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_park_after_a_refusal_offers_restore[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo8_01_list_rename_glass.py::TestListRenameGlass::test_f2_on_a_focused_zone_row_opens_the_field[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 List rename / refusal face + Astra rig setup |
| `tests/unit/test_ux_canon_ratchet.py::test_ratchet` | AssertionError: UX canon ratchet broken — new violations introduced: | Same cause on exact main | Muad’Dib People face / raw-ID ratchet (PeopleCore 12→13); no ceiling increase authorized |
| `tests/unit/test_desk_locks.py::test_the_front_door_is_the_desk_with_the_guard` | AssertionError: the first-value state left the front door | Same cause on exact main | Desk arrival / C5 source-fence maintenance; Astra |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_workbench_success_keeps_another_items_refusal[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_section[1440]` | failed on setup with "AttributeError: '_Evt' object has no attribute 'attendees'" | Prior name only; current cause unclassified | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_section[393]` | failed on setup with "AttributeError: '_Evt' object has no attribute 'attendees'" | Prior name only; current cause unclassified | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_calendar_well_unfold` | failed on setup with "AttributeError: '_Evt' object has no attribute 'attendees'" | Prior name only; current cause unclassified | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_hs175_settings_meetings_glass.py::TestSettingsCalendarSection::test_matched_absent_when_zero` | failed on setup with "AttributeError: '_Evt' object has no attribute 'attendees'" | Prior name only; current cause unclassified | Calendar / #756 attendee fixture maintenance; Astra data, Muad’Dib face fixture |
| `tests/e2e/test_hs152_hands_glass.py::test_allow_always_auto_admit` | playwright._impl._errors.Error: Locator.wait_for: Error: strict mode violation: locator(".thread-composer-input") resolved to 2 elements: | New to this ledger; cause unclassified | Muad’Dib Hands / composer scoping; two matching textboxes |
| `tests/e2e/test_hs202_03_species_glass.py::TestSharedControlsAreSpecies::test_menus_dock_and_wings[1440-900]` | AssertionError: the dock's Tab order left DOM order: ['Intelligence, 2 need you', 'Speak', 'Meetings', 'People', 'Agents', 'Settings', 'Floor', 'Desk memory, 2 need attention', 'Delivery', 'Panes', '◌Hide th… | Prior name only; current cause unclassified | PHILO-13-13 C3-W / Dock species; Muad’Dib |
| `tests/e2e/test_hs202_03_species_glass.py::TestSharedControlsAreSpecies::test_menus_dock_and_wings[393-852]` | AssertionError: the dock: rows overlap after the 44px growth — a taller target that eats its neighbour is not a target: 'Agents' x 'More AppIcons' (48.0x54.0px) | Prior name only; current cause unclassified | PHILO-13-13 C3-W / Dock species; Muad’Dib |
| `tests/e2e/test_philo304_thought_foot_reflow.py::test_the_receipt_yields_to_the_verbs[393-None]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 30000ms exceeded. | Prior name only; current cause unclassified | HS141 Thought Workbench / browser boot and compact face |
| `tests/e2e/test_hs172_arrival_glass.py::TestArrivalProposals::test_arrival_confirm_fires` | AssertionError: Headline unchanged after confirm: 4 need you | Prior name only; current cause unclassified | HS171 system shade / retained face fences |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_an_update_keeps_an_unrelated_delete_failure[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/unit/test_philo9_compat.py::test_the_http_routes_keep_their_envelopes_and_statuses` | AssertionError: ('/api/projects/proj-4d212717b1e4/updates', ['latest_published_update_id', 'updates']) | Same cause on exact main | PHILO 9 project updates envelope fence; Astra |
| `tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again` | AssertionError: ['Run summary', 'Decide'] | Prior name only; current cause unclassified | HS201 Meetings / primary-verb count |
| `tests/e2e/test_hs176_loop_glass.py::test_speak_loop_1440` | AssertionError: Ship the queue for platform on schedule | New to this ledger; cause unclassified | Muad’Dib Speak loop; retain the recorded transcript and correction failure |
| `tests/e2e/test_hs176_loop_glass.py::test_speak_loop_393` | AssertionError: [] | Prior name only; current cause unclassified | HS176 Speak / correction and compact surface |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_delete_keeps_an_unrelated_rename_failure[chromium-393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo11_05b_meeting_faces_glass.py::TestMeetingFacesGlass::test_the_meeting_faces_and_slack_destinations[1440]` | playwright._impl._errors.Error: Locator.get_attribute: Error: strict mode violation: locator(".desk-window [data-seat=meeting] [data-testid=send-well]") resolved to 3 elements: | Prior name only; current cause unclassified | PHILO 10 Send / setup and result face |
| `tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-7 delete receipt + Astra setup/guard maintenance |
| `tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[1440-900]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib FirstWords / Desk staged-note handoff; not just setup |
| `tests/e2e/test_philo7_delete_receipt_glass.py::TestDeleteReceiptGlass::test_the_delete_receipt_is_readable_in_the_viewport[393]` | playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 5000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-7 delete receipt + Astra setup/guard maintenance |
| `tests/integration/test_web_history_archive.py::test_history_keeps_approval_and_export_governance` | AssertionError: assert 'ConfirmVerb' in '// HS-170-04 — the Meetings face, rewritten to the settled design.\n// Board: display headline + Record/Import + stre...      Park\n              </Button>\n         … | Prior name only; current cause unclassified | Meetings governance / old ConfirmVerb assertion; PHILO A1 Park face |
| `tests/e2e/test_hs202_first_use_smoke.py::test_first_use_fence[393-852]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 10000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib FirstWords / Desk staged-note handoff; not just setup |
| `tests/e2e/test_philo11_05b_meeting_faces_glass.py::TestMeetingFacesGlass::test_the_meeting_faces_and_slack_destinations[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 20000ms exceeded. | Prior name only; current cause unclassified | PHILO 11 Meetings / compact Send face; Muad’Dib |
| `tests/unit/test_philo6_01_import_badge.py::test_empty_vtt_import_leaves_import_failed_on_the_wire` | AssertionError: the vitest fixture drifted from the real producer; re-run with PHILO6_WRITE_FIXTURE=1 | Same cause on exact main | PHILO 6 Meetings / empty-import wire fixture |
| `tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[1440]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-3 receipt face + Astra setup; initial receipt not reached |
| `tests/e2e/test_philo8_one_delete_glass.py::TestOneDelete::test_a_resize_that_changes_the_face_commits` | AssertionError: (None, '') | New to this ledger; cause unclassified | Muad’Dib PHILO-8 delete/Park/Undo faces + Astra lifecycle/setup; do not loosen guards on a timeout alone |
| `tests/e2e/test_philo3_01_receipt_hits.py::test_receipt_verbs_own_their_areas[393]` | playwright._impl._errors.TimeoutError: Locator.wait_for: Timeout 15000ms exceeded. | New to this ledger; cause unclassified | Muad’Dib PHILO-3 receipt face + Astra setup; initial receipt not reached |

## Web: assertion results and suite-load failure are separate

The initial full run has 3,257 passed and six failed assertions. The five
affected files then pass **90/90 twice** with `--maxWorkers=1` and
`--no-file-parallelism`. The complete serial rerun has **3,263 executed
tests passed, zero failed assertions**, but Vitest exits **1** because
`web/src/desk/DeskApp.test.tsx` cannot load. Its TrustWindow mock at line
118 omits `useTrustWindow`, which B2's workspace code imports. This
collection failure reproduces on exact main: [baseline JSON](baseline-deskapp.json).
No tests in that suite execute. Both full-run JSON files record the same
load failure. [Commands and all raw result paths](web-run-commands.md).

The baseline checker returns “zero branch-new” because
`scripts/check_web_baseline.py:70-77` counts failed assertions and ignores
failed suites with no assertions. That output is captured honestly but
is not a green-suite verdict. Open homes: Muad’Dib B2 / DeskApp mock
contract, and Astra web-baseline checker / suite-load accounting. Repair
the real dependency contract and add load failures to baseline reporting;
do not suppress the mock error or claim the skipped suite passed.

The six original assertion failures are class c (serial green twice),
with the cause beyond intermittency unproven. Their open maintenance homes:

| Exact node | Home |
|---|---|
| `src/desk/chair/arrivalAttention.test.tsx > Arrival attention (HS-200-15) shows five rows with reason, source and one action; the caption carries the cap; the rest is reachable` | Web test timing/fixture maintenance in this file; raw results retained. |
| `src/desk/__tests__/phoneDoors.test.tsx > the phone menu bar has one door that carries every verb carries the Desk, Object and Window menus, in that order, after Chair` | Web test timing/fixture maintenance in this file; raw results retained. |
| `src/desk/components/DeskListView.test.tsx > HS-93-08 pagination at 1,000 items pages by 100 with an honest count and no focus loss` | Web test timing/fixture maintenance in this file; raw results retained. |
| `src/desk/components/DeskListView.test.tsx > HS-93-08 pagination at 1,000 items settles focus on the count when the last page lands` | Web test timing/fixture maintenance in this file; raw results retained. |
| `src/desk/components/__tests__/workbenchAutomations.test.tsx > Workbench STARTS WHEN automations starts from the six-hour nightly preset but persists per-Workbench policy changes` | Web test timing/fixture maintenance in this file; raw results retained. |
| `src/features/project-room/steward/__tests__/StewardPosture.test.tsx > Scroll hint: data-scroll-hint is set on the posture root sets data-scroll-hint on the steward posture element` | Web test timing/fixture maintenance in this file; raw results retained. |

## Documentation and phase tracking

Nine of the 12 Documentation Navigation commands pass. The architecture
validator finds the old window-persistence test title twice in
`docs/internal/philo/data/desk.json:619,1404`; the real test is now
`round-trips rects + order + max + min through one slot (PHILO-13-07 B2)`
at `web/src/desk/__tests__/windows.test.tsx:192`. The same two errors
reproduce on exact main. The capability-doc and coverage checks also
refuse that invalid metadata. Open home: B2 architecture test-reference
maintenance (Muad’Dib's changed test title; Astra's documentation checks).
No source or descriptor reference was changed in this B0 closure.

`dw doctor` is healthy. `dw check` returns the expected last-story
transition issue: all stories are done, but `final-summary.md` is absent.
The phase's exit criteria remain unchecked in its status file. Open home:
Muad’Dib's Phase 13 closing record and exit-criterion reconciliation.
The roadmap method forbids writing a final summary before those criteria
are settled (`pm/roadmap/roadmap-builder.md:327`); B0's explicit story
close does not manufacture a phase-close verdict to silence this issue.
