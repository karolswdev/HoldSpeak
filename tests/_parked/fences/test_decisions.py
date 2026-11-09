# PARKED 2026-11-09 (fences diet, pipe/fences-diet): the whole catalogue as a hand-kept name list, and the residual census against its committed set (a baseline re-recorded by hand).
# Replaced by: test_the_catalogue_is_explicit_descriptors (unique names, each descriptor's fields), test_operations_export_matches_the_catalogue; the residual set: nothing (a shape fence).
"""Parked from tests/unit/test_decisions.py."""
import json
from pathlib import Path

from holdspeak import operations

REPO = Path(__file__).resolve().parents[3]


def _load_script(name):  # the live helper is in tests/unit/test_decisions.py
    raise NotImplementedError


def test_the_catalogue_names_in_declaration_order() -> None:
    names = [d.name for d in operations.DESCRIPTORS]
    # PHILO-5-01's four, then PHILO-5-02's loop, then PHILO-7-01's desk slice
    # -- an explicit list, no framework.
    assert names == [
        # The catalogue in declaration order (regenerated from DESCRIPTORS when a table
        # is added; still an explicit list, no framework).
        'decision.create', 'decision.update', 'decision.read', 'decision.list', 'meeting.list', 'meeting.read',
        'meeting.import', 'meeting.transcribe', 'meeting.summary.run', 'meeting.result.prepare', 'brief.generate', 'brief.latest',
        'brief.shelf.write', 'brief.shelf.read', 'thought.create', 'thought.save', 'thought.read', 'thought.workbench.read',
        'thought.list', 'note.create', 'note.read', 'note.update', 'note.delete', 'note.list',
        'zone.create', 'zone.read', 'zone.update', 'zone.delete', 'zone.list', 'kb.create',
        'kb.read', 'kb.update', 'kb.delete', 'kb.list', 'zone.file', 'zone.unfile',
        'zone.members', 'kb.member.add', 'kb.member.remove', 'kb.members', 'decision.delete', 'decision.status',
        'decision.supersede', 'kernel.receipt.read', 'memory.observations.read', 'memory.page.read', 'project.list', 'project.get',
        'project.get_room', 'project.create', 'project.door.preview', 'project.door.create', 'project.update', 'project.archive',
        'project.restore', 'project.link', 'project.unlink', 'project.open_review', 'project.get_delta', 'project.decide_proposal',
        'project.accept_review', 'project.list_updates', 'project.draft_update', 'project.update_draft', 'project.publish_update', 'desk.needs_you',
        'project.item.list', 'project.item.create', 'project.item.update', 'project.item.transition', 'project.resource.list', 'project.resource.add',
        'project.resource.remove', 'project.configure_steward', 'project.run_steward', 'project.stop_steward', 'project.get_steward_run', 'project.steward.trigger',
        'steward.nudges', 'nudge.send', 'nudge.dismiss', 'project.watch.inspect', 'project.watch.test', 'project.watch.evaluate',
        'project.watch.set_rules', 'project.watch.pause', 'project.watch.resume', 'project.watch.retire', 'project.watch.update', 'project.watch.baseline',
        'project.suggested_sources', 'project.add_suggested_source', 'project.dismiss_suggested_source', 'connection.list', 'connection.recheck', 'project.door.count',
        'project.mark_update_delivered', 'channel.destinations', 'channel.save_destination', 'channel.remove_destination', 'channel.check_destination', 'channel.preview',
        'channel.prepare', 'channel.discard', 'channel.send', 'channel.sends', 'channel.save_email_key', 'channel.save_slack_webhook',
        'agent_hooks.install', 'agent_hooks.remove', 'people_access.set', 'calendar.open_settings', 'connection.signin', 'setup.found',
        'setup.status', 'setup.use', 'setup.people.add', 'setup.lan.scan', 'project.repository.register', 'agent.hand',
        'agent.launch.lane', 'agent.launch.explain', 'agent.launch.answer', 'agent.launch.seen', 'agent.launch.done', 'agent.launch.remove',
        'agent.launch.resume', 'agent.hand.cancel_queued', 'agent.helper.allow', 'windows.list', 'windows.arrange', 'windows.stage_shelf',
        'windows.open', 'windows.close', 'windows.move', 'windows.resize', 'windows.set_geometry', 'windows.raise',
        'windows.send_back', 'windows.seat', 'windows.zoom', 'desk.mark', 'desk.press', 'desk.say',
        'desk.scroll', 'desk.request.read', 'desk.request.result', 'note.outcomes.read', 'note.find_tasks', 'note.outcome.edit',
        'note.outcome.dismiss', 'note.outcome.confirm', 'today.get', 'program.list', 'program.templates', 'program.create',
        'program.from_action', 'program.add_to_night', 'program.get', 'program.update', 'program.plan', 'program.start',
        'program.park', 'program.resume', 'program.decide', 'program.race', 'program.handoff', 'program.start_from',
        'program.overturn', 'program.step_update', 'program.step_take', 'program.step_hand_back', 'program.amend', 'program.require',
        'program.requirement_edit', 'program.requirement_decide', 'program.proposal_decide', 'program.requirement_evidence', 'program.text', 'program.text_apply',
        'program.shape_engine', 'program.shape', 'program.shape_held_drop', 'program.plan_draft', 'program.plan_programs', 'program.rounds_open',
        'program.round_next', 'program.round_answer', 'program.round_decide', 'program.close', 'program.propose_fix', 'program.step_remove',
        'program.round', 'program.checkpoint', 'program.step_done', 'meeting.ready_list', 'meeting.ready_read', 'meeting.facets',
        'meeting.rename', 'meeting.restore', 'meeting.recover_capture', 'meeting.sync_conflicts', 'meeting.resolve_sync_conflict', 'meeting.intent_timeline',
        'meeting.artifacts', 'meeting.prepared', 'speaker.list', 'action_item.list', 'action_item.update', 'action_item.review',
        'meeting.bookmark', 'meeting.update', 'phone.devices', 'phone.revoke', 'phone.let_wait', 'phone.calls',
        'phone.ring', 'phone.again', 'phone.push_key', 'phone.save_push_key', 'phone.test_push', 'phone.redeem',
        'phone.pair', 'phone.messages', 'phone.mark_read', 'phone.decide', 'phone.get_call', 'phone.accept',
        'phone.decline', 'phone.end', 'people.setup', 'people.suggestion.add', 'people.suggestion.hide', 'people.relationship.archive',
        'people.project.link', 'people.project.unlink', 'people.one_on_one.list', 'people.agenda.transition', 'people.owed.create', 'people.note.list',
        'people.commitment.send_to_workbench', 'people.commitment.satisfy', 'people.calendar.link', 'people.calendar.unlink', 'people.owner_alias.link', 'people.owner_alias.unlink',
        'meeting.intel_jobs', 'meeting.intel_retry', 'meeting.intel_recovery', 'meeting.intel_recovery_retry', 'meeting.intel_recovery_skip', 'meeting.aftercare',
        'meeting.aftercare_proposals', 'meeting.aftercare_decide', 'automation.set_when', 'automation.set_engine', 'automation.make_one', 'automation.template.list',
        'automation.template.instantiate', 'automation.result.open', 'automation.new.list', 'automation.lesson.list', 'automation.lesson.forget', 'calls.status',
        'calls.list', 'calls.get', 'calls.place', 'calls.hangup', 'calls.decide', 'calls.test_line',
        'settings.secret.replace', 'settings.secret.rotate', 'settings.secret.delete', 'decision.ledger', 'follow_through.commit_decision',
    ]


def test_the_residual_set_equals_the_trees_census() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    assert census.check(REPO, committed) == []
    for entry in committed["entries"]:
        assert entry["reason"], entry


def test_the_residual_fence_names_a_new_identity_and_lets_a_paid_one_stay() -> None:
    census = _load_script("residual_census")
    committed = json.loads(census.SET_PATH.read_text(encoding="utf-8"))
    dropped = dict(committed, entries=committed["entries"][1:])
    problems = census.check(REPO, dropped)
    assert len(problems) == 1 and problems[0].startswith("NEW residual identity")
    stale = dict(committed, entries=committed["entries"] + [
        {"transport": "mcp", "entry_point": "desk.create", "discriminator": "kind=decisions", "reason": "x"}])
    assert census.check(REPO, stale) == []  # a paid entry left behind is not a bypass


