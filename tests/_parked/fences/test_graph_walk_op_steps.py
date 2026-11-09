# PARKED 2026-11-09 (fences diet, pipe/fences-diet): a hand-kept copy of OP_MCP_PROJECTIONS / OP_HTTP_ONLY, edited on every new declared operation.
# Replaced by test_graph_walk_op_steps.py::test_canonical_map_matches_live_operation_exposure_projection (every entry matches its live descriptor).
"""Parked from tests/unit/test_graph_walk_op_steps.py."""
from scripts import graph_walk as gw


def test_the_canonical_map_has_all_seventeen_operations_and_no_local_service_target():
    # PHILO-5's seventeen, PHILO-7-01's fifteen desk-slice rows, then
    # PHILO-7-02's nine (decision.status is HTTP only: OP_HTTP_ONLY), then
    # PHILO-9-01's twenty-five Room rows (the Door's create is HTTP only),
    # then PHILO-9-02's twenty-one (the Door's count, a watch's update and
    # its baseline are HTTP only), then PHILO-10-01's nine (the Send), then
    # Conductor K2's one (agent.hand), then Conductor R7's (people_access.set),
    # then PHILO-16 16b's six (the desk's windows), then PHILO-17's
    # meeting.transcribe, then Betterment Q9's five (Find the tasks), then
    # the declared meeting operations (2026-11-08). No count fence: the set
    # below and the live-exposure test are the proof.
    assert set(gw.OP_MCP_PROJECTIONS) == {
        # the declared meeting operations (2026-11-08, holdspeak/meeting_operations.py)
        "action_item.list", "action_item.review", "action_item.update", "meeting.artifacts",
        "meeting.bookmark", "meeting.facets", "meeting.intent_timeline", "meeting.prepared",
        "meeting.ready_list", "meeting.ready_read", "meeting.recover_capture", "meeting.rename",
        "meeting.resolve_sync_conflict", "meeting.restore", "meeting.sync_conflicts", "meeting.update",
        "speaker.list",
        # the intelligence and aftercare verbs (2026-11-08, holdspeak/meeting_intel_operations.py)
        "meeting.intel_jobs", "meeting.intel_retry", "meeting.intel_recovery", "meeting.intel_recovery_retry",
        "meeting.intel_recovery_skip", "meeting.aftercare", "meeting.aftercare_proposals", "meeting.aftercare_decide",
        # the Decisions app's verbs (2026-11-08, holdspeak/decision_operations.py)
        "decision.ledger", "follow_through.commit_decision",
        # the phone's declared verbs with an MCP tool (2026-11-08, holdspeak/phone_operations.py)
        "phone.calls", "phone.devices", "phone.get_call", "phone.let_wait", "phone.messages", "phone.push_key",
        "phone.revoke", "phone.test_push", "phone.ring", "phone.again",
        # the declared People verbs (2026-11-08, holdspeak/people_operations.py)
        "people.setup", "people.suggestion.add", "people.suggestion.hide", "people.relationship.archive",
        "people.project.link", "people.project.unlink", "people.one_on_one.list", "people.agenda.transition",
        "people.owed.create", "people.note.list", "people.commitment.send_to_workbench",
        "people.commitment.satisfy", "people.calendar.link", "people.calendar.unlink", "people.owner_alias.link", "people.owner_alias.unlink",
        # the declared Automations verbs (2026-11-08, holdspeak/automation_operations.py)
        "automation.set_when", "automation.set_engine", "automation.make_one", "automation.template.list",
        "automation.template.instantiate", "automation.result.open", "automation.new.list", "automation.lesson.list",
        "automation.lesson.forget",
        # the Calls window's declared verbs with an MCP tool (2026-11-08, holdspeak/calls_operations.py)
        "calls.status", "calls.list", "calls.get", "calls.place", "calls.hangup", "calls.test_line",
        "setup.status", "setup.use",
        "decision.create", "decision.update", "decision.read", "decision.list",
        "meeting.list", "meeting.read", "meeting.import", "meeting.transcribe", "meeting.summary.run",
        "brief.generate", "brief.latest", "brief.shelf.write", "brief.shelf.read",
        "thought.create", "thought.save", "thought.read",
        "thought.workbench.read", "thought.list",
        "note.create", "note.read", "note.update", "note.delete", "note.list",
        "zone.create", "zone.read", "zone.update", "zone.delete", "zone.list",
        "kb.create", "kb.read", "kb.update", "kb.delete", "kb.list",
        "zone.file", "zone.unfile", "zone.members",
        "kb.member.add", "kb.member.remove", "kb.members",
        "decision.delete", "decision.supersede", "kernel.receipt.read",
        "project.list", "project.get", "project.get_room", "project.create", "project.update",
        "project.archive", "project.restore", "project.link", "project.unlink",
        "project.open_review", "project.get_delta", "project.decide_proposal", "project.accept_review",
        "project.list_updates", "project.draft_update", "project.update_draft", "project.publish_update",
        "desk.needs_you", "today.get", "project.item.list", "project.item.create", "project.item.update",
        "project.item.transition", "project.resource.list", "project.resource.add", "project.resource.remove",
        "project.configure_steward", "project.run_steward", "project.stop_steward", "project.get_steward_run",
        "project.steward.trigger", "steward.nudges", "nudge.send", "nudge.dismiss",
        "project.watch.inspect", "project.watch.test", "project.watch.evaluate", "project.watch.set_rules",
        "project.watch.pause", "project.watch.resume", "project.watch.retire",
        "project.suggested_sources", "project.add_suggested_source", "project.dismiss_suggested_source",
        "connection.list", "connection.recheck", "project.mark_update_delivered",
        "channel.destinations", "channel.save_destination", "channel.remove_destination",
        "channel.check_destination", "channel.preview", "channel.prepare", "channel.discard",
        "channel.send", "channel.sends",
        "memory.observations.read", "memory.page.read",
        "agent.hand", "people_access.set",
        "windows.list", "windows.open", "windows.close", "windows.raise", "windows.arrange", "windows.seat",
        # One display protocol (2026-11-08): every window verb, and the display requests.
        "windows.move", "windows.resize", "windows.set_geometry", "windows.send_back", "windows.zoom",
        "windows.stage_shelf",
        "desk.mark", "desk.press", "desk.say", "desk.scroll", "desk.request.read",
        "note.outcomes.read", "note.find_tasks", "note.outcome.edit", "note.outcome.dismiss", "note.outcome.confirm",
        # #2027: the Programs descriptors with an MCP tool.
        "program.add_to_night", "program.amend", "program.checkpoint", "program.create", "program.decide", "program.from_action", "program.get", "program.handoff", "program.list", "program.overturn", "program.park", "program.plan", "program.plan_draft", "program.plan_programs", "program.propose_fix", "program.race", "program.require", "program.resume", "program.round", "program.shape", "program.shape_engine", "program.shape_held_drop", "program.start", "program.start_from", "program.step_done", "program.step_hand_back", "program.step_remove", "program.step_take", "program.step_update", "program.templates", "program.text", "program.text_apply", "program.update",
    }
    assert gw.OP_HTTP_ONLY == {"decision.status", "project.door.create", "project.door.preview",
                               "project.door.count", "project.watch.update", "project.watch.baseline",
                               "channel.save_email_key", "channel.save_slack_webhook",
                               "agent_hooks.install", "agent_hooks.remove", "calendar.open_settings", "connection.signin",
                               "setup.found", "setup.people.add", "setup.lan.scan",
                               "project.repository.register",
                               # Betterment capture C5b: Prepare… / Write again (HTTP only).
                               "meeting.result.prepare",
                               # #2027: the Programs descriptors with no MCP tool.
                               "program.close", "program.proposal_decide", "program.requirement_decide", "program.requirement_edit", "program.requirement_evidence", "program.round_answer", "program.round_decide", "program.round_next", "program.rounds_open",
                               # One display protocol (2026-11-08): the compositor's answer (HTTP only).
                               "desk.request.result",
                               # 2026-11-08: the phone verbs with no MCP tool.
                               "phone.redeem", "phone.pair", "phone.save_push_key", "phone.mark_read",
                               "phone.decide", "phone.accept", "phone.decline", "phone.end",
                               # 2026-11-08: the Agents window's launch verbs (HTTP only).
                               "agent.launch.lane", "agent.launch.explain", "agent.launch.answer", "agent.launch.seen",
                               "agent.launch.done", "agent.launch.remove", "agent.launch.resume",
                               "agent.hand.cancel_queued", "agent.helper.allow",
                               # 2026-11-08: the Calls window's tap answer (no MCP tool).
                               "calls.decide",
                               # 2026-11-08: the Settings window's credentials (HTTP only, no tool).
                               "settings.secret.replace", "settings.secret.rotate", "settings.secret.delete"}
    assert all(value["kind"] in {"tool", "resource"}
               for value in gw.OP_MCP_PROJECTIONS.values())


