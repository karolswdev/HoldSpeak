"""The MCP tools that may take long: a model call, the network, a subprocess, a download.

``POST /api/mcp`` (``holdspeak/web/routes/mcp_http.py``) runs every other tool
call one at a time, in arrival order, on one worker thread, because the
services are not safe for two writers (two ``desk.update`` calls on one Note
lose a change). A tool named here runs on the thread pool beside that queue, so
a 60-second model call does not hold a ``desk.get`` for 60 seconds. Operations
that declare ``blocking_io`` (``holdspeak/operations.py``) take the same path.

What is given up: a long tool is not ordered against other calls. Each of these
writes only the rows of its own run (a run, a job, an observation, a probe
result), or nothing; the HTTP routes that reach the same services already run
beside MCP calls with no order. Add a tool here when its body waits on a model
or on something outside the process.
"""
from __future__ import annotations

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
    # The network or a CLI subprocess (gh, acli, an engine probe).
    "watch.refresh": "network",
    "watch.preview": "network",
    "reaction.process": "network",
    "project.open_review": "network (source collectors)",
    "project.watch.test": "network",
    "project.watch.evaluate": "network",
    "connection.recheck": "subprocess (gh / acli)",
    "heartbeat.run_now": "network (watch sweep, calendar)",
    "provider.github_connection": "subprocess (gh)",
    "provider.github_discover": "subprocess (gh)",
    "provider.github_validate_repo": "subprocess (gh)",
    "provider.jira_connection": "subprocess (acli)",
    "provider.jira_discover": "subprocess (acli)",
    "provider.jira_search": "subprocess (acli)",
    "provider.jira_validate_scope": "subprocess (acli)",
    "provider.confluence_discover": "subprocess (acli)",
    "provider.confluence_validate_space": "subprocess (acli)",
    "concierge.detect": "network (engine probes)",
    "concierge.probe": "network (engine probe)",
    "concierge.download": "download",
    "model_library.download": "download",
}
