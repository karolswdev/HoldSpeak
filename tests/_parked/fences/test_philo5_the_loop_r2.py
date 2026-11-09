# PARKED 2026-11-09 (fences diet, pipe/fences-diet): two hand-kept lists edited on every new declared operation (the owner-only names; the producer coverage set).
# Replaced by: every owner_only descriptor refuses a non-owner before its service (test_philo5_the_loop_r2.py); each listed producer still proves its shape.
"""Parked from tests/unit/test_philo5_the_loop_r2.py."""
from holdspeak import operations

PRODUCERS: dict = {}  # the live table is in tests/unit/test_philo5_the_loop_r2.py


def _declared_keys(result: str):  # the live helper is in tests/unit/test_philo5_the_loop_r2.py
    raise NotImplementedError


def test_the_owner_only_names_in_declaration_order() -> None:
    # Both secret saves are owner only and HTTP only, with held inputs.
    assert [d.name for d in operations.DESCRIPTORS if d.owner_only] == [
        'meeting.import',
        'meeting.transcribe',
        'channel.save_email_key',
        'channel.save_slack_webhook',
        'agent_hooks.install',
        'agent_hooks.remove',
        'people_access.set',
        'calendar.open_settings',
        'connection.signin',
        'setup.found',
        'setup.use',
        'setup.people.add',
        'setup.lan.scan',
        'project.repository.register',
        'agent.hand',
        'agent.launch.answer',
        'agent.launch.done',
        'agent.launch.remove',
        'desk.press',
        'phone.devices',
        'phone.revoke',
        'phone.let_wait',
        'phone.calls',
        'phone.ring',
        'phone.again',
        'phone.push_key',
        'phone.save_push_key',
        'phone.test_push',
        'phone.pair',
        'people.setup',
        'people.suggestion.add',
        'people.suggestion.hide',
        'people.relationship.archive',
        'people.project.link',
        'people.project.unlink',
        'people.agenda.transition',
        'people.owed.create',
        'people.commitment.send_to_workbench',
        'people.commitment.satisfy',
        'people.calendar.link',
        'people.calendar.unlink',
        'people.owner_alias.link',
        'people.owner_alias.unlink',
        'calls.place',
        'calls.decide',
        'calls.test_line',
        'settings.secret.replace',
        'settings.secret.rotate',
        'settings.secret.delete',
    ]  # the declared tables in declaration order; writes are the owner's


def test_every_braced_declaration_has_a_producer_here() -> None:
    declared = {d.name for d in operations.DESCRIPTORS if _declared_keys(d.result) is not None}
    assert declared == set(PRODUCERS), "a descriptor declares a shape this fence does not run"


