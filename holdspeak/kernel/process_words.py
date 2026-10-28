"""What a process did for the owner, in his words (atlas pass 3, defect 8).

The Processes window named each row by its operation (`Setup lan scan`,
`Decision create`). The kernel's read now gives each process a ``label``:
what it did for him (`Checked the LAN`, `Made a decision`). The map is here,
in one place; an operation that is not in it reads as sentence words made
from its name (`project.watch.pause` -> `Project watch pause`).
"""
from __future__ import annotations

PROCESS_WORDS: dict[str, str] = {
    # Setup and connections
    "setup.lan.scan": "Checked the LAN",
    "setup.use": "Set up what Setup found",
    "setup.people.add": "Added your people",
    "connection.recheck": "Checked a connection",
    "connection.signin": "Started a sign-in",
    "calendar.open_settings": "Opened calendar settings",
    "agent_hooks.install": "Connected a coding agent",
    "agent_hooks.remove": "Disconnected a coding agent",
    "people_access.set": "Changed People access",
    # Decisions
    "decision.create": "Made a decision",
    "decision.update": "Changed a decision",
    "decision.status": "Changed a decision's status",
    "decision.supersede": "Replaced a decision",
    "decision.delete": "Withdrew a decision",
    "decision.promotion-draft": "Drafted a decision",
    # Notes, zones, knowledge
    "note.create": "Wrote a note",
    "note.update": "Changed a note",
    "note.delete": "Deleted a note",
    "note.find_tasks": "Found the tasks in a note",
    "note.outcome.confirm": "Confirmed a found task",
    "note.outcome.edit": "Changed a found task",
    "note.outcome.dismiss": "Dismissed a found task",
    "zone.create": "Made a drawer",
    "zone.update": "Changed a drawer",
    "zone.delete": "Deleted a drawer",
    "zone.file": "Filed an item",
    "zone.unfile": "Took an item out of a drawer",
    "kb.create": "Made a knowledge base",
    "kb.update": "Changed a knowledge base",
    "kb.delete": "Deleted a knowledge base",
    "kb.member.add": "Added to a knowledge base",
    "kb.member.remove": "Removed from a knowledge base",
    # Sends
    "channel.save_destination": "Saved a destination",
    "channel.remove_destination": "Removed a destination",
    "channel.prepare": "Prepared a send",
    "channel.discard": "Discarded a send",
    "channel.send": "Sent",
    "channel.save_email_key": "Saved an email key",
    "channel.save_slack_webhook": "Saved a Slack webhook",
    "nudge.send": "Sent a nudge",
    "nudge.dismiss": "Dismissed a nudge",
    # Projects
    "project.create": "Made a project",
    "project.door.create": "Made a project",
    "project.update": "Changed a project",
    "project.archive": "Archived a project",
    "project.restore": "Restored a project",
    "project.link": "Filed a meeting in a project",
    "project.unlink": "Took a meeting out of a project",
    "project.open_review": "Opened a project review",
    "project.decide_proposal": "Decided a proposal",
    "project.accept_review": "Accepted a project review",
    "project.draft_update": "Drafted an update",
    "project.update_draft": "Changed a draft update",
    "project.publish_update": "Published an update",
    "project.mark_update_delivered": "Marked an update delivered",
    "project.item.create": "Added a milestone or risk",
    "project.item.update": "Changed a milestone or risk",
    "project.item.transition": "Moved a milestone or risk",
    "project.resource.add": "Filed an item in a project",
    "project.resource.remove": "Took an item out of a project",
    "project.repository.register": "Registered a repository",
    "project.configure_steward": "Set the steward",
    "project.run_steward": "Ran the steward",
    "project.stop_steward": "Stopped the steward",
    "project.steward.trigger": "Ran the scheduled steward work",
    "project.watch.test": "Tested a watch",
    "project.watch.evaluate": "Read a watch",
    "project.watch.set_rules": "Set a watch's rules",
    "project.watch.pause": "Paused a watch",
    "project.watch.resume": "Resumed a watch",
    "project.watch.retire": "Retired a watch",
    "project.watch.update": "Changed a watch",
    "project.watch.baseline": "Took a watch's baseline",
    "project.add_suggested_source": "Watched a suggested source",
    "project.dismiss_suggested_source": "Dismissed a suggested source",
    "project.door.count": "Counted a source",
    # Windows
    "windows.open": "Opened a window",
    "windows.close": "Closed a window",
    "windows.raise": "Brought a window to the front",
    "windows.arrange": "Arranged windows",
    "windows.seat": "Moved a window to the Dock",
    # Agents, runs and the engine
    "agent.hand": "Handed an item to an agent",
    "delegation.grant": "Gave an agent access",
    "delegation.revoke": "Took an agent's access away",
    "process.spawn": "Started an agent",
    "process.input": "Sent words to an agent",
    "tool.call": "Ran an agent's tool",
    "tool.turn": "Ran an agent's turn",
    "subprocess.exec": "Ran a command",
    "desktop.type_text": "Typed text",
    "external.egress": "Sent data off this Mac",
    "actuator.egress": "Ran an action",
    "inference.run": "Asked the engine",
    "inference.invoke": "Asked the engine",
    "inference.cancel": "Stopped an engine answer",
    "sequence.run": "Ran a sequence",
    "workflow.run": "Ran a workflow",
    "workbench.run": "Ran a workbench",
    "workbench_mint": "Made a workbench",
    "workbench_triage": "Sorted a workbench",
    "meeting.session": "Recorded a meeting",
    "meeting.deferred-intel-job": "Summarized a meeting",
    "dictation.session": "Took a dictation",
    "wake.session": "Listened for the wake word",
    "voice_reference_resolve": "Found what you named",
    "delivery.pr-review-draft": "Drafted a pull request review",
    "cadence.next-action-draft": "Drafted a next action",
    "rails.observer-batch": "Read agent activity",
}


def process_label(kind: str, operation_name: str = "") -> str:
    """What the process named *kind* did, in sentence words.

    A codec may project its own kind (`tool_call_hold` for `tool.call`): the
    map is read by the kind, then by the operation's name, and only then are
    words made from the kind."""
    name = str(kind or "").strip()
    known = PROCESS_WORDS.get(name) or PROCESS_WORDS.get(str(operation_name or "").strip())
    if known:
        return known
    name = name or str(operation_name or "").strip()
    if not name:
        return ""
    words = " ".join(name.replace(".", " ").replace("_", " ").replace("-", " ").split()).lower()
    return words[:1].upper() + words[1:]
