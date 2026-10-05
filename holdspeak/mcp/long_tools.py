"""The MCP tools that may take long, and the per-key locks every tool call takes.

``POST /api/mcp`` (``holdspeak/web/routes/mcp_http.py``) runs every tool call
not named here one at a time, in arrival order, on one worker thread: the
services are not safe for two writers (two ``desk.update`` calls on one Note
lose a change). A tool named here runs on the thread pool beside that queue, so
a 60-second model call does not hold a ``desk.get``. Operations that declare
``blocking_io`` (``holdspeak/operations.py``) take the same path.

Overlap is made safe by KEY (Astra on #867). Every tool call, queued or long,
first takes a lock for each key in :func:`lock_keys`: the object ids in its
arguments (a project, a watch, a workbench, a thought ...) and, for tools that
drive ``gh`` or ``acli``, the one ``providers`` key (``acli`` switches a global
active account). Calls on the same key run one at a time; calls on different
keys run in parallel. The writes that a key lock cannot cover from HTTP are
atomic on their own: one open review per project, one draft per command_id,
and a watch test saves its result only at the rules revision it read.

The audit, tool by tool (2026-10-05):

* model calls: each writes only its own new run, invocation or result rows,
  or rows of the object its key names (the workbench, the thought with its
  expected revisions, the project's draft with its command claim).
  ``memory.search`` only reads.
* ``watch.preview`` only reads (it persists nothing). ``project.watch.test``
  saves with a revision compare-and-set. ``project.watch.evaluate`` is
  idempotent on (watch, watch revision, source revision).
* the provider reads write only the provider's own connection-status row and
  share the ``providers`` key with every other ``gh``/``acli`` tool.

Not here, because overlap was not provably safe: ``project.open_review`` (the
collector reads only the database: it is not long), ``watch.refresh``,
``reaction.process`` and ``heartbeat.run_now`` (sweeps over many watches, also
run by the background loops), ``concierge.*`` (detection may assign a
default engine) and ``model_library.download``.
"""
from __future__ import annotations

from typing import Any, Mapping

#: tool name -> why it can take long.
LONG_TOOLS: dict[str, str] = {
    # A model call.
    "ask.run": "model",
    "workbench.run": "model",
    "recipe.run": "model",
    "sequence.run": "model",
    "workflow.run": "model",
    "thought.refine": "model",
    "thought.answer_and_continue": "model",
    "project.draft_update": "model (generator llm)",
    "memory.search": "embedding model",
    # The network or a CLI subprocess (gh, acli).
    "watch.preview": "network",
    "project.watch.test": "network",
    "project.watch.evaluate": "network",
    "connection.recheck": "subprocess (gh / acli)",
    "provider.github_connection": "subprocess (gh)",
    "provider.github_discover": "subprocess (gh)",
    "provider.github_validate_repo": "subprocess (gh)",
    "provider.jira_connection": "subprocess (acli)",
    "provider.jira_discover": "subprocess (acli)",
    "provider.jira_search": "subprocess (acli)",
    "provider.jira_validate_scope": "subprocess (acli)",
    "provider.confluence_discover": "subprocess (acli)",
    "provider.confluence_validate_space": "subprocess (acli)",
}

#: Argument names whose value names one object; a call locks each one.
KEY_ARGUMENTS: tuple[str, ...] = (
    "project_id", "watch_id", "workbench_id", "recipe_id", "chain_id",
    "workflow_id", "thought_id", "request_id", "command_id",
)

#: Tools that drive gh or acli (acli switches one global active account).
PROVIDER_TOOLS: frozenset[str] = frozenset({
    "connection.recheck", "watch.preview", "watch.refresh",
    "project.watch.test", "project.watch.evaluate",
}) | frozenset(name for name in LONG_TOOLS if name.startswith("provider."))


def lock_keys(name: str, arguments: Mapping[str, Any]) -> list[str]:
    """The sorted lock keys of one tool call (sorted: no lock-order deadlock)."""
    keys = {
        f"{arg}={value.strip()}"
        for arg in KEY_ARGUMENTS
        if isinstance(value := arguments.get(arg), str) and value.strip()
    }
    if name in PROVIDER_TOOLS or name.startswith("provider."):
        keys.add("providers")
    return sorted(keys)
