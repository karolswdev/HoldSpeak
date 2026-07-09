"""The product under test, as a managed subprocess.

``ProductProcess`` boots ``holdspeak web --no-open`` in its own process
group, with ``HOME`` overridden onto the run's isolated home and the port
and bind host pinned via the product's own env contract
(``HOLDSPEAK_WEB_PORT`` / ``HOLDSPEAK_WEB_HOST``). It captures stdout and
stderr to per-run log files, polls the auth-exempt ``/health`` route until
the server answers, and tears down cleanly (SIGTERM the group, then kill)
so a ``uv run`` child never orphans.

Everything here is stdlib — no ``holdspeak`` import, no ``httpx`` — because
this is the class that must survive the product it launches being broken.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


class ProductProcess:
    """A single boot of the product. Reusable verbs: start, wait_healthy, stop."""

    def __init__(
        self,
        *,
        home: Path,
        port: int,
        host: str = "127.0.0.1",
        log_dir: Path,
        extra_env: dict[str, str] | None = None,
    ) -> None:
        self.home = Path(home)
        self.port = int(port)
        self.host = host
        self.log_dir = Path(log_dir)
        self.extra_env = dict(extra_env or {})
        self.proc: subprocess.Popen | None = None
        self._stdout_f = None
        self._stderr_f = None
        self.log_dir.mkdir(parents=True, exist_ok=True)

    @property
    def stdout_path(self) -> Path:
        return self.log_dir / "product.stdout.log"

    @property
    def stderr_path(self) -> Path:
        return self.log_dir / "product.stderr.log"

    @property
    def health_host(self) -> str:
        # A server bound to 0.0.0.0 still answers on loopback; polling the LAN
        # address would need the token, but /health is auth-exempt on loopback.
        return "127.0.0.1" if self.host in ("0.0.0.0", "::") else self.host

    @property
    def health_url(self) -> str:
        return f"http://{self.health_host}:{self.port}/health"

    def _command(self) -> list[str]:
        # `python -m holdspeak.main` runs the product's CLI in the subprocess.
        # This is the ONLY place the product is invoked, and it is a subprocess,
        # never an import into the conductor's own process.
        return [sys.executable, "-m", "holdspeak.main", "web", "--no-open"]

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["HOLDSPEAK_WEB_PORT"] = str(self.port)
        env["HOLDSPEAK_WEB_HOST"] = self.host
        # Keep the sandbox honest: don't let the parent's venv-activation or a
        # stray XDG var pull the product back to the real config.
        env.pop("HOLDSPEAK_CONFIG", None)
        env.update(self.extra_env)
        return env

    def start(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            raise RuntimeError("product already started")
        self._stdout_f = open(self.stdout_path, "ab", buffering=0)
        self._stderr_f = open(self.stderr_path, "ab", buffering=0)
        self.proc = subprocess.Popen(
            self._command(),
            cwd=str(_repo_root()),
            env=self._env(),
            stdout=self._stdout_f,
            stderr=self._stderr_f,
            stdin=subprocess.DEVNULL,
            start_new_session=True,  # own process group → clean group kill
        )

    @property
    def pid(self) -> int | None:
        return self.proc.pid if self.proc else None

    def is_alive(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def probe_health(self, timeout: float = 1.5) -> bool:
        try:
            with urllib.request.urlopen(self.health_url, timeout=timeout) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def wait_healthy(self, timeout: float = 45.0, interval: float = 0.4) -> bool:
        """Poll ``/health`` until it answers or the process dies or time runs out.

        Returns True on a healthy answer. Returns False if the process exits
        before answering (a boot crash) or the timeout elapses — never hangs.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if not self.is_alive():
                return False  # crashed on boot; caller reads the log tail
            if self.probe_health():
                return True
            time.sleep(interval)
        return False

    def stop(self, grace: float = 6.0) -> None:
        """SIGTERM the process group, wait out the grace, then SIGKILL."""
        if self.proc is None:
            self._close_logs()
            return
        if self.proc.poll() is None:
            self._signal_group(signal.SIGTERM)
            try:
                self.proc.wait(timeout=grace)
            except subprocess.TimeoutExpired:
                self._signal_group(signal.SIGKILL)
                try:
                    self.proc.wait(timeout=grace)
                except subprocess.TimeoutExpired:
                    pass
        self._close_logs()

    def _signal_group(self, sig: int) -> None:
        try:
            os.killpg(os.getpgid(self.proc.pid), sig)  # type: ignore[union-attr]
        except (ProcessLookupError, PermissionError, OSError):
            # Fall back to signalling just the leader if the group is gone.
            try:
                self.proc.send_signal(sig)  # type: ignore[union-attr]
            except (ProcessLookupError, OSError):
                pass

    def _close_logs(self) -> None:
        for f in (self._stdout_f, self._stderr_f):
            try:
                if f:
                    f.close()
            except OSError:
                pass
        self._stdout_f = None
        self._stderr_f = None

    def tail(self, n: int = 80) -> dict[str, str]:
        return {
            "stdout": _tail_file(self.stdout_path, n),
            "stderr": _tail_file(self.stderr_path, n),
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _tail_file(path: Path, n: int) -> str:
    if not path.exists():
        return ""
    try:
        lines = path.read_text(errors="replace").splitlines()
    except OSError:
        return ""
    return "\n".join(lines[-n:])
