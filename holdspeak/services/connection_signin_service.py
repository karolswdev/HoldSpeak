"""Native provider sign-in processes for the Accounts face.

The service owns only the short lived tmux process record.  It does not read,
parse, or store a provider credential.  The provider CLI owns the browser
flow and its credential file; HoldSpeak only exposes the existing terminal
target and observes the process exit marker.
"""

from __future__ import annotations

import re
import shlex
import shutil
import subprocess
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from ..principals import Principal, PrincipalKind


_HOST = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.-]{0,252}[A-Za-z0-9]$")
_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_RUN = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_DONE = "HOLDSPEAK_SIGNIN_DONE"


class SignInRefused(ValueError):
    """A named refusal before a native CLI process is started."""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = reason
        super().__init__(detail or reason)


@dataclass
class _Run:
    run_id: str
    provider_id: str
    site: str
    email: str
    session: str
    pane_id: str
    target: dict[str, Any]
    state: str = "running"
    exit_code: int | None = None
    error: str = ""


class ConnectionSigninService:
    """Start a provider-owned browser login in the shared terminal seam."""

    def __init__(
        self,
        *,
        target_provider: Callable[[], Any],
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        tmux_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._target_provider = target_provider
        self._runner = runner or subprocess.run
        self._tmux_runner = tmux_runner or subprocess.run
        self._runs: dict[str, _Run] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _require_owner(principal: Principal) -> None:
        if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
            raise SignInRefused("owner_required", "Sign in requires the owner.")

    @staticmethod
    def _help(binary: str, product: str, runner: Callable[..., subprocess.CompletedProcess[str]]) -> str:
        try:
            result = runner(
                [binary, *( [product] if product else []), "auth", "login", "--help"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SignInRefused("cli_help_failed", f"{binary} help failed: {exc}") from exc
        output = f"{result.stdout or ''}\n{result.stderr or ''}".strip()
        if result.returncode != 0:
            raise SignInRefused("cli_help_failed", output or f"{binary} refused its help")
        return output

    @staticmethod
    def _command(
        provider_id: str,
        site: str,
        email: str,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]],
    ) -> list[str]:
        if provider_id == "github":
            binary = shutil.which("gh")
            if not binary:
                raise SignInRefused("cli_unavailable", "gh is not installed")
            help_text = ConnectionSigninService._help(binary, "", runner)
            if "--web" not in help_text or "--hostname" not in help_text:
                raise SignInRefused("browser_flow_unsupported", "gh browser sign-in is not supported by this CLI")
            return [binary, "auth", "login", "--web", "--hostname", site]

        if provider_id not in {"jira", "confluence"}:
            raise SignInRefused("provider_unsupported", f"Sign in is not supported for {provider_id}")
        binary = shutil.which("acli")
        if not binary:
            raise SignInRefused("cli_unavailable", "acli is not installed")
        help_text = ConnectionSigninService._help(binary, provider_id, runner)
        if "--site" not in help_text or "--email" not in help_text:
            raise SignInRefused("browser_flow_unsupported", f"acli {provider_id} browser sign-in is not supported by this CLI")
        # Current acli browser login is the native `auth login` flow.  Add a
        # browser switch only when the installed help names one; never invent
        # a flag for a version that does not expose it.
        browser_flag = "--web" if "--web" in help_text else "--browser" if "--browser" in help_text else ""
        args = [binary, provider_id, "auth", "login", "--site", site, "--email", email]
        if browser_flag:
            args.append(browser_flag)
        if "--token" in help_text and not browser_flag and "browser" not in help_text.lower():
            raise SignInRefused("browser_flow_unsupported", f"acli {provider_id} browser sign-in is not supported by this CLI")
        return args

    @staticmethod
    def _shell_command(argv: list[str], run_id: str) -> str:
        command = shlex.join(argv)
        marker = f"{_DONE}:{run_id}"
        # Keep the pane alive after the native process exits so the existing
        # terminal target can show its final CLI output and accept Retry.
        return (
            f"{command}; _holdspeak_signin_status=$?; "
            f"printf '\\n{marker}:%s\\n' \"$_holdspeak_signin_status\"; "
            'exec "${SHELL:-/bin/sh}" -l'
        )

    def _cleanup_spawned_session(self, session: str) -> None:
        """End only the private session minted by this sign-in attempt."""
        from .. import coder_factory

        coder_factory.discard_signin_session(session, runner=self._tmux_runner)

    def start_sign_in(
        self,
        principal: Principal,
        provider_id: str,
        site: str,
        email: str | None = None,
    ) -> dict[str, Any]:
        self._require_owner(principal)
        provider = str(provider_id or "").strip().lower()
        host = str(site or "").strip()
        address = str(email or "").strip()
        if provider not in {"github", "jira", "confluence"}:
            raise SignInRefused("provider_unsupported", f"Sign in is not supported for {provider}")
        if not _HOST.fullmatch(host):
            raise SignInRefused("site_invalid", "the account site is invalid")
        if provider in {"jira", "confluence"} and not _EMAIL.fullmatch(address):
            raise SignInRefused("email_invalid", "the account email is invalid")

        argv = self._command(provider, host, address, runner=self._runner)
        targets = self._target_provider()
        if targets is None:
            raise SignInRefused("terminal_unavailable", "the terminal target service is not ready")
        run_id = "signin_" + uuid.uuid4().hex[:16]
        session = f"holdspeak-signin-{run_id[-10:]}"
        from .. import coder_factory

        spawned = coder_factory.spawn(session, command=self._shell_command(argv, run_id))
        if spawned.get("status") != "spawned":
            raise SignInRefused(str(spawned.get("status") or "spawn_failed"), str(spawned.get("detail") or "the sign-in pane could not start"))
        pane_id = str(spawned.get("pane_id") or "")
        if not pane_id:
            self._cleanup_spawned_session(session)
            raise SignInRefused("spawn_failed", "the sign-in pane has no target")
        issued = targets.issue(f"pane:{pane_id}")
        if issued.get("status") != "issued":
            self._cleanup_spawned_session(session)
            raise SignInRefused("terminal_target_failed", str(issued.get("detail") or "the sign-in pane has no target"))
        target = {
            "target_id": issued["target_id"],
            "target_generation": issued["target_generation"],
            "node_id": "local",
            "label": f"{provider.title()} sign in · {host}",
            "session_label": session,
            "worktree_id": None,
            "agent": "signin",
            "presentation": "embedded",
        }
        record = _Run(run_id, provider, host, address, session, pane_id, target)
        with self._lock:
            self._runs[run_id] = record
        return {"status": "started", "run_id": run_id, "target": target}

    def status(self, principal: Principal, run_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        clean = str(run_id or "").strip()
        if not _RUN.fullmatch(clean):
            raise SignInRefused("run_unknown", "the sign-in run is unknown")
        with self._lock:
            record = self._runs.get(clean)
        if record is None:
            raise SignInRefused("run_unknown", "the sign-in run is unknown")
        if record.state == "running":
            try:
                pane = self._tmux_runner(
                    ["tmux", "capture-pane", "-p", "-t", record.pane_id, "-S", "-200"],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=3,
                )
                if pane.returncode != 0:
                    record.state = "failed"
                    record.error = "Sign-in terminal is unavailable."
                else:
                    output = f"{pane.stdout or ''}\n{pane.stderr or ''}"
                    match = re.search(rf"{re.escape(_DONE)}:{re.escape(record.run_id)}:(\d+)", output)
                    if match:
                        record.exit_code = int(match.group(1))
                        record.state = "finished" if record.exit_code == 0 else "failed"
                        record.error = "" if record.exit_code == 0 else f"CLI exited with {record.exit_code}"
            except (OSError, subprocess.TimeoutExpired):
                record.state = "failed"
                record.error = "Sign-in terminal is unavailable."
        return {
            "status": record.state,
            "run_id": record.run_id,
            "provider_id": record.provider_id,
            "site": record.site,
            "target": record.target,
            "exit_code": record.exit_code,
            "error": record.error,
        }


__all__ = ["ConnectionSigninService", "SignInRefused"]
