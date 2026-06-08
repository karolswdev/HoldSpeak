"""HS-52-03: local action connectors for voice command macros.

A voice macro maps a spoken keyword to a deterministic action (HS-52-02). This builds
the ``connector(proposal) -> dict`` the ``ActuatorExecutor`` injects, REUSING the
Phase-38 gated-connector framework (``build_gated_connector`` + ``WriteConnectorManifest``
+ ``PermissionGate``) rather than reinventing guarded execution.

Three of the four action kinds run a bounded subprocess and route through the gate:

  - ``open_url``    -> ``open <url>`` (macOS) / ``xdg-open <url>`` (Linux)
  - ``launch_app``  -> ``open -a <app>`` (macOS) / ``<app>`` (Linux)
  - ``shell``       -> ``sh -c <command>``

The fourth, ``type_text``, is **not** egress (it types a snippet into the focused app),
so it is a plain local connector that types via an injected writer (the dispatcher passes
the runtime typer in HS-52-04).

Each egress connector carries a **per-macro** ``WriteConnectorManifest`` derived from the
macro's own configured action, so the executor bounds it to exactly that one command. A
mishearing fires the wrong configured macro; it can never synthesize a new command.

The proposal payload contract the dispatcher (HS-52-04) stores and ``_plan`` reads:
``{"kind": <action kind>, "payload": <action payload>}``.
"""
from __future__ import annotations

import sys
from typing import Any, Callable, Optional

from ..config import VoiceMacroAction
from ..logging_config import get_logger
from .actuator_executor import Connector
from .gated_connector import (
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)

log = get_logger("plugins.voice_macro_connector")

# The actuator plugin id voice macros record proposals under (the executor's
# allow-list gate checks `proposal.plugin_id` — see HS-52-04).
VOICE_MACRO_PLUGIN_ID = "voice_macro"
DEFAULT_TIMEOUT_SECONDS = 30.0


def _platform() -> str:
    return sys.platform


def voice_macro_argv(
    action: VoiceMacroAction, *, platform: Optional[str] = None
) -> Optional[tuple[str, ...]]:
    """The bounded argv this action runs, or ``None`` for the local ``type_text`` kind."""
    plat = platform if platform is not None else _platform()
    is_mac = plat == "darwin"
    payload = action.payload
    if action.kind == "open_url":
        return ("open", payload) if is_mac else ("xdg-open", payload)
    if action.kind == "launch_app":
        return ("open", "-a", payload) if is_mac else (payload,)
    if action.kind == "shell":
        return ("sh", "-c", payload)
    return None  # type_text is local, not a subprocess


def voice_macro_manifest(
    action: VoiceMacroAction, *, platform: Optional[str] = None
) -> Optional[WriteConnectorManifest]:
    """The per-macro manifest that admits exactly this action's command (or ``None``
    for ``type_text``)."""
    argv = voice_macro_argv(action, platform=platform)
    if argv is None:
        return None
    return WriteConnectorManifest(
        connector_id=f"{VOICE_MACRO_PLUGIN_ID}_{action.kind}",
        permission="shell:exec",
        label=f"Voice command ({action.kind})",
        description=action.preview(),
        allowed_argv_prefixes=(argv,),
    )


def _plan(proposal: Any, *, platform: Optional[str]) -> GatedOperation:
    """Build the bounded subprocess op from the proposal's stored payload."""
    payload = getattr(proposal, "payload", None) or {}
    action = VoiceMacroAction(
        kind=str(payload.get("kind", "")), payload=str(payload.get("payload", ""))
    )
    argv = voice_macro_argv(action, platform=platform)
    if argv is None:
        raise RuntimeError(f"voice macro action {action.kind!r} has no subprocess to run")
    return GatedOperation.subprocess(
        argv, capture_output=True, text=True, timeout=DEFAULT_TIMEOUT_SECONDS
    )


def _interpret(completed: Any, op: GatedOperation) -> dict[str, Any]:
    """Map the subprocess result into the executor's result dict (or raise -> failed)."""
    returncode = getattr(completed, "returncode", 0)
    stdout = (getattr(completed, "stdout", "") or "").strip()
    stderr = (getattr(completed, "stderr", "") or "").strip()
    if returncode not in (0, None):
        raise RuntimeError(
            f"voice command exited {returncode}: {stderr or stdout or 'no output'}"
        )
    return {
        "argv": list(op.argv),
        "returncode": returncode,
        "stdout": stdout,
        "stderr": stderr,
    }


def _default_type_writer(text: str) -> None:
    from ..typer import TextTyper

    TextTyper().type_text(text)


def build_voice_macro_connector(
    action: VoiceMacroAction,
    *,
    runner: Optional[Any] = None,
    type_writer: Optional[Callable[[str], None]] = None,
    platform: Optional[str] = None,
) -> Connector:
    """Build the ``connector(proposal) -> dict`` for one macro action.

    Egress kinds route through the gated framework with a per-macro manifest; ``runner``
    is the injected subprocess primitive (tests pass a fake; production defaults through
    the ``PermissionGate`` to ``subprocess.run``). ``type_text`` types via ``type_writer``
    (the dispatcher injects the runtime typer; default lazily builds a ``TextTyper``).
    """
    if action.kind == "type_text":
        write = type_writer or _default_type_writer

        def _type_connector(proposal: Any) -> dict[str, Any]:
            payload = getattr(proposal, "payload", None) or {}
            text = str(payload.get("payload") or "")
            write(text)
            log.info("voice macro typed %d char(s)", len(text))
            return {"action": "type_text", "typed": text}

        return _type_connector

    manifest = voice_macro_manifest(action, platform=platform)
    if manifest is None:  # pragma: no cover — only type_text has no manifest
        raise RuntimeError(f"no connector for voice macro action {action.kind!r}")
    return build_gated_connector(
        manifest,
        plan=lambda proposal: _plan(proposal, platform=platform),
        interpret=_interpret,
        runner=runner,
    )


__all__ = [
    "VOICE_MACRO_PLUGIN_ID",
    "build_voice_macro_connector",
    "voice_macro_argv",
    "voice_macro_manifest",
]
