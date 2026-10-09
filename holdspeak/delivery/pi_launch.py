"""pi as the third coding-agent harness: the launch adapter (pi spike #1020).

pi (``@earendil-works/pi-coding-agent``) runs on the model the hub assigns to
coding work: the engine of the ``agent.code`` capability, through the same
route resolution every other model run uses (capability, then group, then the
default). That engine must be an OpenAI-compatible endpoint; with no engine
the launch refuses ``no_assignment``, with another kind of engine
``no_compatible_assignment`` (the route words the Hand already shows).

Each launch gets its own pi folder (``PI_CODING_AGENT_DIR``), mode 0700, its
files 0600, beside the launch's Claude ``--mcp-config`` file:

- ``models.json``: one provider ``lan`` with the engine's endpoint, its model
  and a key REFERENCE (``${HOLDSPEAK_PI_MODEL_KEY}``). The key itself reaches
  pi only in its environment, from the spawn's one-shot 0600 file
  (``coder_factory.spawn``): never in argv, a file the hub keeps, or a log.
- ``mcp.json``: the HoldSpeak MCP at the hub URL as plain text (pi does not
  expand ``${VAR}`` in ``url``) with the ``Authorization: Bearer
  ${HOLDSPEAK_AGENT_CREDENTIAL}`` header (pi expands it from the launch's
  credential). The core tools are ``direct``; the rest are found through
  pi's ``tool_search`` (``deferred``).
- ``holdspeak.json``: the gate and rider commands the extension
  ``holdspeak/agent_context/pi_extension/holdspeak-pi.ts`` runs.
- ``sessions/``: pi's transcripts (``--session-dir``).

The folder goes with the launch's MCP config (``agent_mcp.remove_mcp_config``):
on a failed launch, when the session ends, and at K4 cleanup.
"""
from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

#: The pi command (``KNOWN_EXECUTABLES``).
EXECUTABLE = "pi"

#: The provider name in ``models.json``; the launch flag is ``--model lan/<model>``.
PROVIDER = "lan"

#: The capability whose engine pi runs on: the hub's engine for coding work.
CAPABILITY_ID = "agent.code"

#: The variable that carries the engine's key into pi's process (never argv):
#: the second line of the spawn's one-shot file (``coder_factory.BOOTSTRAP``).
from ..coder_factory import MODEL_KEY_ENV  # noqa: E402

#: ``models.json`` needs a key; an endpoint that takes none gets this word
#: (pi's own docs use a dummy key for a keyless server).
NO_KEY = "none"

#: The context window when the engine does not name one.
DEFAULT_CONTEXT_WINDOW = 32_768

#: The HoldSpeak MCP tools pi's model sees at once; the rest are deferred
#: (found with ``tool_search``). Patterns: ``*`` matches any characters.
DIRECT_TOOLS = (
    "project.*",
    "desk.needs_you",
    "follow_through.*",
    "decision_record.*",
    "meeting.get",
    "note.*",
    "zone.file",
    "zone.unfile",
)

#: pi's own network calls stay off in a launch (catalog refresh, version
#: check, telemetry).
PI_ENV = {"PI_OFFLINE": "1", "PI_SKIP_VERSION_CHECK": "1", "PI_TELEMETRY": "0"}

#: The maintained extension every pi launch loads (``-e``).
EXTENSION_PATH = Path(__file__).resolve().parents[1] / "agent_context" / "pi_extension" / "holdspeak-pi.ts"


@dataclass(frozen=True)
class PiEngine:
    """The engine one pi launch runs on (no key value: only its slot)."""

    endpoint: str
    model: str
    context_window: int
    key_slot: str
    host: str
    boundary: str

    def to_wire(self) -> dict[str, Any]:
        """Path-free and key-free: what the Hand shows (the egress host)."""
        return {"host": self.host, "model": self.model, "boundary": self.boundary}


def coding_engine(db: Any) -> PiEngine:
    """The hub's engine for coding work, or a refusal by the route's own word.

    ``no_assignment``: no engine is assigned (or the owner turned coding
    off). ``no_compatible_assignment``: the assigned engines include no
    OpenAI-compatible endpoint, or the assignment cannot run."""
    from ..services.errors import ServiceError
    from ..services.inference_route_plan_service import (
        ROUTE_PLANNING_AUTHORITY,
        InferenceRoutePlanService,
    )
    from .factory_launch import LaunchRefused

    try:
        revisions = InferenceRoutePlanService(db).resolve_deployments(
            ROUTE_PLANNING_AUTHORITY, capability_id=CAPABILITY_ID
        )
    except ServiceError as exc:
        code = "no_assignment" if exc.code == "no_assignment" else "no_compatible_assignment"
        raise LaunchRefused(code, f"pi has no engine for coding work ({exc.code})") from exc
    for revision, executable in revisions:
        if not executable or str(revision.engine) != "openai_compatible":
            continue
        endpoint = str(revision.endpoint or "").strip().rstrip("/")
        parsed = urlparse(endpoint)
        model = str(revision.model or "").strip()
        if parsed.scheme not in ("http", "https") or not parsed.netloc or not model:
            continue
        return PiEngine(
            endpoint=endpoint,
            model=model,
            context_window=int(revision.context_ceiling or 0) or DEFAULT_CONTEXT_WINDOW,
            key_slot=str(revision.secret_slot or ""),
            host=str(parsed.netloc),
            boundary=str(revision.boundary or ""),
        )
    raise LaunchRefused(
        "no_compatible_assignment", "the engine for coding work is not an OpenAI-compatible endpoint"
    )


def key_for_slot(slot: str) -> Optional[str]:
    """A key value, read from the hub's key custody at spawn time; ``None``
    for no slot or no key. Never logged; it goes only to the spawn's one-shot
    file (``coder_factory.spawn(model_key=...)``)."""
    if not slot:
        return None
    from ..profile_key_store import ProfileKeyStoreError, resolve_profile_key

    try:
        return resolve_profile_key(slot) or None
    except ProfileKeyStoreError:
        return None


def pi_dir(launch_id: str, directory: Optional[Path] = None) -> Path:
    """The launch's pi folder, beside its ``--mcp-config`` file."""
    from .agent_mcp import mcp_config_dir

    return (directory or mcp_config_dir()) / f"pi-{launch_id}"


def models_document(engine: PiEngine, *, keyed: bool) -> dict[str, Any]:
    return {
        "providers": {
            PROVIDER: {
                "baseUrl": engine.endpoint,
                "api": "openai-completions",
                "apiKey": "${" + MODEL_KEY_ENV + "}" if keyed else NO_KEY,
                "models": [{"id": engine.model, "contextWindow": engine.context_window}],
            }
        }
    }


def mcp_document(hub_url: str) -> dict[str, Any]:
    """pi's ``mcp.json``: the hub URL as text, the credential as a variable."""
    from .agent_mcp import CREDENTIAL_ENV, SERVER_NAME

    return {
        "mcpServers": {
            SERVER_NAME: {
                "url": str(hub_url or "").rstrip("/") + "/api/mcp",
                "headers": {"Authorization": "Bearer ${" + CREDENTIAL_ENV + "}"},
                "description": "HoldSpeak hub: the desk, Projects, decisions, meetings, notes",
                "exposure": "deferred",
                "toolExposure": {name: "direct" for name in DIRECT_TOOLS},
            }
        }
    }


def _write_private(path: Path, document: dict[str, Any]) -> None:
    data = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


def write_pi_dir(
    launch_id: str, engine: PiEngine, *, hub_url: str, hooks: dict[str, Any],
    keyed: bool, directory: Optional[Path] = None,
) -> Path:
    """Write the launch's pi folder (0700; files 0600) and return it."""
    folder = pi_dir(launch_id, directory)
    folder.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(folder.parent, 0o700)
    except OSError:
        pass
    folder.mkdir(mode=0o700, exist_ok=True)
    os.chmod(folder, 0o700)
    sessions = folder / "sessions"
    sessions.mkdir(mode=0o700, exist_ok=True)
    os.chmod(sessions, 0o700)
    from ..agent_context.hooks import PI_HOOKS_FILE

    _write_private(folder / "models.json", models_document(engine, keyed=keyed))
    _write_private(folder / "mcp.json", mcp_document(hub_url))
    _write_private(folder / PI_HOOKS_FILE, hooks)
    return folder


def remove_pi_dir(launch_id: str, directory: Optional[Path] = None) -> bool:
    """Remove the launch's pi folder (idempotent)."""
    clean = str(launch_id or "").strip()
    if not clean:
        return False
    folder = pi_dir(clean, directory)
    if not folder.exists():
        return False
    shutil.rmtree(folder, ignore_errors=True)
    return not folder.exists()


def launch_args(engine: PiEngine, folder: Path) -> list[str]:
    """pi's flags: the model, the transcript folder and the extension."""
    return [
        "--model", f"{PROVIDER}/{engine.model}",
        "--session-dir", str(folder / "sessions"),
        "-e", str(EXTENSION_PATH),
    ]


def launch_env(folder: Path, *, mcp_hold: bool = False) -> dict[str, str]:
    """The environment of a pi launch (no secret: the key rides the spawn's file).

    ``mcp_hold``: the launch's MCP tools are not pre-approved (Secure at
    launch, ``agent_mcp.pre_approved``). The gate hook then holds every
    HoldSpeak MCP tool that is not a read (``coder_gate.MCP_HOLD_ENV``), as
    Claude Code asks in its pane for a tool that is not allowed."""
    from ..coder_gate import MCP_HOLD_ENV

    env = {"PI_CODING_AGENT_DIR": str(folder), **PI_ENV}
    if mcp_hold:
        env[MCP_HOLD_ENV] = "1"
    return env


__all__ = [
    "CAPABILITY_ID",
    "DIRECT_TOOLS",
    "EXECUTABLE",
    "EXTENSION_PATH",
    "MODEL_KEY_ENV",
    "PROVIDER",
    "PiEngine",
    "coding_engine",
    "launch_args",
    "launch_env",
    "key_for_slot",
    "mcp_document",
    "models_document",
    "pi_dir",
    "remove_pi_dir",
    "write_pi_dir",
]
