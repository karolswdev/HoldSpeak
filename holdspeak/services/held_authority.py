"""The effective authority a held action commits to, checked by its writer.

The declaration uses the owning resolver. Its saved authority is a precondition,
never a request to select Control, a destination, a folder or a principal.
"""
from __future__ import annotations

from typing import Any

from .errors import ServiceError


def check_authority(expected: Any, current: Any) -> None:
    if expected is not None and expected != (digest(current) if isinstance(expected, str) else current):
        raise ServiceError('answer_stale', 'The authority changed. Read again.', context={
            'status': 409, 'code': 'answer_stale', 'verbs': ['Read again']})


def launch_authority(profile: dict[str, Any], mode: Any, folder: str, *, read_only: bool = False,
                     live_mode: Any = None, options: Any = None) -> dict[str, Any]:
    """One material description of the launch driver's native and Desk rights."""
    from ..delivery.agent_mcp import normalized_mode
    native, live = normalized_mode(mode), normalized_mode(live_mode if live_mode is not None else mode)
    executable = str(profile.get('executable') or '')
    # The same allowed slots the launch resolves; they are also in the binding.
    from ..delivery.factory_launch import AgentProfileStore
    store = object.__new__(AgentProfileStore)
    store._profiles = {profile['profile_id']: profile}
    argv = store.resolve_argv(profile['profile_id'], options)
    ro = read_only or (executable == 'codex' and any(v == 'read-only' or v == '--sandbox=read-only' for v in argv))
    network = 'No' if executable == 'codex' and (ro or native != 'yolo') else 'Yes'
    files = 'Read only' if ro else ('Work folder; more files need approval' if native == 'safe' else 'Work folder edits; other access follows the agent and tool gate')
    commands = ('No shell commands' if executable == 'claude' else 'Read-only commands') if ro else {
        'safe': 'Tool commands ask before they run',
        'neutral': 'Read and test commands pass the tool gate; other commands ask',
        'yolo': 'Work commands pass the tool gate; outside or unknown commands ask',
    }[live]
    desk = 'Read only' if read_only else ('Ask before Desk writes' if live == 'safe' else 'Routine Desk work; no settings or authority tools')
    return {'control': {'safe': 'Secure', 'neutral': 'Normal', 'yolo': 'YOLO'}[live],
        'files': files, 'commands': commands, 'desk': desk, 'network': network,
        'folder': str(folder), 'agent': str(profile.get('label') or executable),
        'until': 'Until this agent stops; Desk grants last at most 12 hours',
        'material': {'profile': profile['profile_id'], 'argv': argv, 'native': native, 'live': live,
                     'read_only': read_only, 'native_read_only': ro, 'folder': str(folder)}}


def digest(value: Any) -> str:
    import hashlib
    import json
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def program_authority(program: dict[str, Any]) -> dict[str, Any]:
    """The Program's own effective control and limits, not the Desk's mode."""
    from .program_rules import level_of
    mode = level_of(program.get('control'))
    profiles = list(program.get('allowed_profiles') or [])
    if not profiles:
        profiles = [str(program.get('default_profile') or 'claude-default')]
    profiles += [str(program['reviewer_profile'])] if program.get('reviewer_profile') else []
    profiles += [str(row.get('profile') or '') for row in program.get('default_runs_on') or [] if isinstance(row, dict)]
    return {'control': {'secure': 'Secure', 'normal': 'Normal', 'yolo': 'YOLO'}[mode],
        'files': 'Agent worktrees and their Git data',
        'commands': 'Run work commands under the tool gate' if mode == 'yolo' else 'Ask when work needs approval',
        'desk': 'Ask before Desk writes' if mode == 'secure' else 'Routine Desk work; no settings or authority tools',
        'network': 'No' if mode != 'yolo' and profiles and all(str(p).startswith('codex') for p in profiles) else 'Yes, under each agent and tool gate',
        'folder': str(program.get('repo_root') or 'No agent work folder'),
        'calls': 'Yes, under the call gate' if program.get('may_call') else 'No',
        'handoff': 'Yes, under the parent limits' if program.get('may_handoff') else 'No',
        'spend': str(program['spend_limit_usd']) + ' US dollars' if program.get('spend_limit_usd') is not None else 'No Program spend limit',
        'agent': 'Program agents', 'until': 'Until the Program is parked or ends',
        'material': {key: program.get(key) for key in ('id', 'control', 'repo_root', 'default_profile', 'default_engine',
            'reviewer_profile', 'reviewer_engine', 'default_runs_on', 'allowed_profiles', 'may_call', 'may_handoff',
            'within', 'spend_limit_usd', 'budget_tokens')}}


def permission_facts() -> list[dict[str, Any]]:
    """Rows for one native grant/revoke; used by the same facts projector."""
    from ..held_arguments import text, hidden
    return [{**text('expected_authority.' + key, label, owner_only=True), 'redact': True, **({'format': 'prompt'} if key in ('scope', 'principal') else {})}
            for key, label in (('action', 'Allowed'), ('principal', 'For'), ('scope', 'Scope'), ('until', 'Until'),
                ('control', 'Control'), ('files', 'Files'), ('commands', 'Commands'), ('desk', 'Desk'), ('network', 'Network'))] + [
        {**text('expected_authority.prompt', 'Command', owner_only=True), 'format': 'prompt', 'redact': True},
        hidden('expected_authority.material', 'Authority binding', 'token')]
