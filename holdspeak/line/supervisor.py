"""baresip as the Line's supervised child (LINE design §4, §2, §9).

At each start the Line writes baresip's ``config`` and ``accounts`` into its
own folder (``~/.holdspeak/line/baresip``, mode 0600), with a module folder
that holds ONLY the modules on :data:`MODULES` (the licence rule is a list,
not trust) and our ``aupipe``. SIP binds to one address, never ``0.0.0.0``.
``ctrl_tcp`` listens on ``127.0.0.1``. A baresip that exits is started again
after 1 s, then 2, 4 … up to 30 s; the exit ends a call with ``failed``.
"""
from __future__ import annotations

import asyncio
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from ..logging_config import get_logger
from .audio import RATE

log = get_logger("line.supervisor")

#: The command a rig (or the owner) names whole: it wins over the search.
BARESIP_ENV = "HOLDSPEAK_BARESIP"
#: baresip's modules we load, each BSD-3 (baresip's own). Nothing else is
#: ever linked into the module folder; ``gzrtp`` (GNU ZRTP) and any module
#: that links a GPL library are never built or loaded.
MODULES = ("g711", "l16", "opus", "auresamp", "account", "menu", "ctrl_tcp", "stun", "ice", "turn", "srtp")
#: The modules a line cannot run without.
REQUIRED = ("g711", "auresamp", "account", "menu", "ctrl_tcp")
#: Modules that load as applications (``module_app``).
APP_MODULES = ("account", "menu", "ctrl_tcp")
#: Never loaded, by name.
FORBIDDEN = ("gzrtp",)
#: The codec order (design §6): opus where the build has it, then G.711.
CODECS = ("opus", "PCMU", "PCMA")
#: The restart backoff.
BACKOFF_FIRST, BACKOFF_MAX = 1.0, 30.0

AUPIPE_SOURCE = Path(__file__).resolve().parent / "aupipe"


#: The Line's folder, named whole (a machine that keeps the Line in one place).
HOME_ENV = "HOLDSPEAK_LINE_HOME"


def state_dir() -> Path:
    """The Line's folder: ``HOLDSPEAK_LINE_HOME``, else ``~/.holdspeak/line``."""
    named = os.environ.get(HOME_ENV, "").strip()
    return Path(named).expanduser() if named else Path.home() / ".holdspeak" / "line"


def find_baresip() -> Optional[str]:
    """baresip's binary: ``HOLDSPEAK_BARESIP``, then ``PATH``, then our own
    Linux build (``~/holdspeak-line/opt/bin``)."""
    named = os.environ.get(BARESIP_ENV, "").strip()
    if named:
        return named if Path(named).expanduser().exists() or shutil.which(named) else None
    found = shutil.which("baresip")
    if found:
        return found
    own = Path.home() / "holdspeak-line" / "opt" / "bin" / "baresip"
    return str(own) if own.is_file() else None


def stock_modules(binary: str) -> Optional[Path]:
    """baresip's own module folder, next to its binary
    (``<prefix>/lib/baresip/modules``)."""
    real = Path(shutil.which(binary) or binary).resolve()
    prefix = real.parent.parent
    for candidate in (prefix / "lib" / "baresip" / "modules", prefix / "lib64" / "baresip" / "modules",
                      Path("/opt/homebrew/lib/baresip/modules"), Path("/usr/local/lib/baresip/modules")):
        if (candidate / "ctrl_tcp.so").exists():
            return candidate
    return None


def baresip_version(binary: str) -> str:
    """``4.12.0`` from ``baresip -h`` (its first line), or ``""``."""
    try:
        out = subprocess.run([binary, "-h"], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    found = re.search(r"baresip v(\d+\.\d+\.\d+)", (out.stdout or "") + (out.stderr or ""))
    return found.group(1) if found else ""


def build_aupipe(out_dir: Path, *, binary: str = "", force: bool = False) -> Path:
    """Compile ``aupipe.so`` into ``out_dir`` against the installed baresip
    (``make``); rebuilt when the baresip version changes (a ``brew upgrade``)."""
    out_dir = Path(out_dir)
    target = out_dir / "aupipe.so"
    stamp = out_dir / "aupipe.version"
    version = baresip_version(binary) if binary else ""
    if target.exists() and not force and (not version or (stamp.exists() and stamp.read_text().strip() == version)):
        return target
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    own = Path.home() / "holdspeak-line" / "opt"
    if binary and own.exists() and Path(binary).resolve().is_relative_to(own.resolve()):
        env["BARESIP_PREFIX"] = str(own)
    proc = subprocess.run(["make", "-s", "-C", str(AUPIPE_SOURCE), f"OUT={out_dir}"], capture_output=True,
                          text=True, env=env, timeout=120)
    if proc.returncode != 0 or not target.exists():
        raise RuntimeError(f"aupipe did not build: {(proc.stderr or proc.stdout).strip()[-400:]}")
    if version:
        stamp.write_text(version + "\n")
    return target


def link_modules(module_dir: Path, stock: Path, aupipe: Path) -> list[str]:
    """The module folder baresip reads: links to the allowed modules that
    this build has, and aupipe. The names it holds."""
    module_dir = Path(module_dir)
    module_dir.mkdir(parents=True, exist_ok=True)
    for old in module_dir.iterdir():
        if old.is_symlink() or old.suffix == ".so":
            old.unlink()
    have: list[str] = []
    for name in MODULES:
        source = Path(stock) / f"{name}.so"
        if source.exists():
            (module_dir / f"{name}.so").symlink_to(source)
            have.append(name)
    (module_dir / "aupipe.so").symlink_to(Path(aupipe).resolve())
    have.append("aupipe")
    missing = [name for name in REQUIRED if name not in have]
    if missing:
        raise RuntimeError(f"baresip has no {', '.join(missing)} module")
    return have


@dataclass
class Account:
    """``calls.line.account``: a SIP address on the tailnet, or a Telnyx line."""

    kind: str = "sip"  # sip | telnyx
    user: str = "holdspeak"
    domain: str = ""
    outbound: str = ""
    password: str = ""  # from the hub's keystore; written only to the 0600 accounts file
    codecs: tuple[str, ...] = CODECS

    @classmethod
    def of(cls, data: Optional[dict[str, Any]], *, password: str = "") -> "Account":
        data = dict(data or {})
        codecs = data.get("codecs") or CODECS
        if isinstance(codecs, str):
            codecs = [part.strip() for part in codecs.split(",")]
        return cls(kind=str(data.get("kind") or "sip"), user=str(data.get("user") or "holdspeak"),
                   domain=str(data.get("domain") or ""), outbound=str(data.get("outbound") or ""),
                   password=password, codecs=tuple(c for c in codecs if c))


def account_line(account: Account, *, bind: str, sip_port: int, codecs: list[str]) -> str:
    """One line of baresip's ``accounts`` file."""
    order = ",".join(c for c in account.codecs if c in codecs or c in {"PCMU", "PCMA"}) or "PCMU,PCMA"
    if account.kind == "telnyx":
        domain = account.domain or "sip.telnyx.com"
        outbound = account.outbound or f"sip:{domain};transport=tcp"
        secret = f";auth_pass={account.password}" if account.password else ""
        return (f"<sip:{account.user}@{domain};transport=tcp>{secret};outbound=\"{outbound}\";regint=600;"
                f"answermode=manual;audio_codecs={order}")
    return f"<sip:{account.user}@{bind}:{sip_port}>;regint=0;answermode=manual;audio_codecs={order}"


@dataclass
class LineConfig:
    home: Path = field(default_factory=lambda: state_dir() / "baresip")
    bind: str = "127.0.0.1"
    sip_port: int = 5060
    ctrl_port: int = 4444
    say_sock: Optional[Path] = None
    heard_sock: Optional[Path] = None
    account: Account = field(default_factory=Account)
    jitter: str = "fixed"
    jitter_ms: str = "40-80"
    audio_buffer: str = "20-60"

    def __post_init__(self) -> None:
        self.home = Path(self.home)
        if self.bind in {"0.0.0.0", "::", ""}:
            raise ValueError("the Line binds SIP to one address, never to every address")
        # A unix socket path is at most 104 bytes on macOS: keep them short.
        sock_dir = Path(os.environ.get("HOLDSPEAK_LINE_SOCK_DIR") or self.home)
        self.say_sock = Path(self.say_sock or sock_dir / "say.sock")
        self.heard_sock = Path(self.heard_sock or sock_dir / "heard.sock")


def write_config(cfg: LineConfig, *, modules: list[str], module_dir: Path) -> Path:
    """baresip's ``config``, ``accounts`` and ``contacts`` in ``cfg.home`` (0600)."""
    home = cfg.home
    home.mkdir(parents=True, exist_ok=True)
    os.chmod(home, 0o700)
    codec_mods = [m for m in ("opus", "g711", "l16") if m in modules]
    lines = [
        f"sip_listen\t\t{cfg.bind}:{cfg.sip_port}",
        f"net_interface\t\t{cfg.bind}",
        "sip_transports\t\tudp,tcp",
        f"audio_source\t\taupipe,{cfg.say_sock}",
        f"audio_player\t\taupipe,{cfg.heard_sock}",
        f"audio_alert\t\taupipe,{home / 'alert.sock'}",
        f"ausrc_srate\t\t{RATE}",
        f"auplay_srate\t\t{RATE}",
        "ausrc_channels\t\t1",
        "auplay_channels\t\t1",
        f"audio_buffer\t\t{cfg.audio_buffer}",
        f"audio_jitter_buffer_type\t{cfg.jitter}",
        f"audio_jitter_buffer_ms\t{cfg.jitter_ms}",
        "audio_level\t\tno",
        f"ctrl_tcp_listen\t\t127.0.0.1:{cfg.ctrl_port}",
        f"module_path\t\t{module_dir}",
    ]
    lines += [f"module\t\t\t{m}.so" for m in codec_mods]
    lines += ["module\t\t\tauresamp.so", "module\t\t\taupipe.so"]
    if cfg.account.kind == "telnyx":
        lines += [f"module\t\t\t{m}.so" for m in ("stun", "ice", "turn", "srtp") if m in modules]
    lines += [f"module_app\t\t{m}.so" for m in APP_MODULES]
    for name in FORBIDDEN:
        assert all(name not in line for line in lines)
    _write_private(home / "config", "\n".join(lines) + "\n")
    codecs = ["opus"] if "opus" in modules else []
    _write_private(home / "accounts", account_line(cfg.account, bind=cfg.bind, sip_port=cfg.sip_port,
                                                   codecs=codecs + ["PCMU", "PCMA"]) + "\n")
    _write_private(home / "contacts", "")
    return home


def _write_private(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.chmod(path, 0o600)


class Supervisor:
    """Runs baresip, starts it again when it exits (backoff 1 s → 30 s)."""

    def __init__(self, cfg: LineConfig, *, binary: str, argv: Optional[list[str]] = None,
                 on_start: Optional[Callable[[], Awaitable[None]]] = None,
                 on_exit: Optional[Callable[[int], Awaitable[None]]] = None) -> None:
        self.cfg = cfg
        self.binary = binary
        #: The whole command (a test's fake baresip); else ``baresip -f <home>``.
        self._argv = argv
        self._on_start = on_start
        self._on_exit = on_exit
        self.proc: Optional[asyncio.subprocess.Process] = None
        self._task: Optional[asyncio.Task[None]] = None
        self._stopping = False
        self.restarts = 0
        self.modules: list[str] = []
        self.log_path = cfg.home / "baresip.log"

    def prepare(self, *, aupipe: Optional[Path] = None) -> None:
        """Write the config and the module folder (a fake baresip needs no modules)."""
        module_dir = self.cfg.home / "modules"
        if self._argv is None:
            stock = stock_modules(self.binary)
            if stock is None:
                raise RuntimeError("baresip's modules are not found")
            built = aupipe or build_aupipe(state_dir() / "build", binary=self.binary)
            self.modules = link_modules(module_dir, stock, built)
        else:
            self.modules = ["g711", "auresamp", "account", "menu", "ctrl_tcp", "aupipe"]
        write_config(self.cfg, modules=self.modules, module_dir=module_dir)

    def command(self) -> list[str]:
        if self._argv is not None:
            return list(self._argv) + ["-f", str(self.cfg.home)]
        return [self.binary, "-f", str(self.cfg.home), "-a", "HoldSpeak Line", "-T", "-c"]

    async def start(self) -> None:
        self._stopping = False
        self._task = asyncio.ensure_future(self._run())

    async def _spawn(self) -> asyncio.subprocess.Process:
        log_file = open(self.log_path, "ab")
        try:
            return await asyncio.create_subprocess_exec(
                *self.command(), stdin=asyncio.subprocess.DEVNULL, stdout=log_file, stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
            )
        finally:
            log_file.close()

    async def _run(self) -> None:
        backoff = BACKOFF_FIRST
        while not self._stopping:
            loop = asyncio.get_running_loop()
            started = loop.time()
            try:
                self.proc = await self._spawn()
            except OSError as exc:
                log.warning(f"baresip did not start: {exc}")
                self.proc = None
            if self.proc is not None:
                if self._on_start is not None:
                    try:
                        await self._on_start()
                    except Exception as exc:
                        log.warning(f"the Line did not reach baresip: {exc}")
                code = await self.proc.wait()
                if self._stopping:
                    return
                log.warning(f"baresip exited ({code}); starting it again in {backoff:g} s")
                if self._on_exit is not None:
                    try:
                        await self._on_exit(code)
                    except Exception as exc:
                        log.warning(f"exit hook failed: {exc}")
            if loop.time() - started > BACKOFF_MAX:
                backoff = BACKOFF_FIRST  # it ran a good while: a fresh failure
            self.restarts += 1
            await asyncio.sleep(backoff)
            backoff = min(BACKOFF_MAX, backoff * 2)

    def running(self) -> bool:
        return self.proc is not None and self.proc.returncode is None

    async def stop(self) -> None:
        self._stopping = True
        proc = self.proc
        if proc is not None and proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), 5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass


__all__ = [
    "Account", "BARESIP_ENV", "CODECS", "FORBIDDEN", "LineConfig", "MODULES", "Supervisor", "account_line",
    "baresip_version", "build_aupipe", "find_baresip", "link_modules", "state_dir", "stock_modules", "write_config",
]
