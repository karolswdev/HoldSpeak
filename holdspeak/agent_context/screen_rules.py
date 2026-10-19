"""Betterment AG7: screen rules, the herdr port (agents/DESIGN.md, "Seeing
every agent").

The desk reads an agent's state from its screen when no hook speaks. The
rules are herdr's own rule files (``rules/*.toml``, Apache-2.0, vendored
unchanged, see ``NOTICE``); this module is a fresh engine for them, written
after herdr's ``src/detect/manifest.rs``:

- a rule has an ``id``, a ``state`` (``working`` / ``blocked`` / ``idle`` /
  ``unknown``), a ``priority`` and a ``region`` of the screen it reads
  (``bottom_non_empty_lines(12)``, ``last_non_empty_above_prompt_box``,
  ``osc_title`` (the pane title), and the rest of herdr's regions);
- its gate: every ``contains`` needle (case-insensitive), every ``regex``,
  every ``line_regex`` (some line matches it), every ``all`` gate, at least
  one ``any`` gate, and no ``not`` gate;
- the matching rule with the highest priority wins (the first on a tie);
  no match is herdr's ``default_known_agent_idle_fallback``.

A file in ``~/.config/holdspeak/agent-rules/<agent>.toml`` replaces the
bundled one for that agent (herdr's local override). Nothing is fetched from
the network. Pure: callers pass the screen text and the title.

``prompt_reading`` gives what a blocked screen asks: the command an approval
prompt wants to run and the numbered choices (it replaces AG2's parse on the
face); ``last_message`` gives the agent's last words above its prompt.
"""
from __future__ import annotations

import re
import threading
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

RULES_DIR = Path(__file__).resolve().parent / "rules"

#: The agents with a bundled rule file (herdr's names).
BUNDLED_AGENTS = ("claude", "codex", "pi", "gemini", "opencode")

#: herdr's fallback label for a known agent no rule matched.
IDLE_FALLBACK = "default_known_agent_idle_fallback"

STATES = frozenset({"working", "blocked", "idle", "unknown"})

#: The evidence a verdict keeps: at most this many lines of the region.
EVIDENCE_LINES = 12
EVIDENCE_CHARS = 240


def override_dir() -> Path:
    """The local override folder (read at call time: an isolated HOME)."""
    return Path.home() / ".config" / "holdspeak" / "agent-rules"


# ── Rust regex syntax, read as Python's ────────────────────────────────


def rust_regex(pattern: str) -> str:
    r"""herdr's patterns are Rust regex: ``\x{2800}`` is a code point and
    ``\z`` the end of the text. Everything else they use reads the same in
    Python's ``re``."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            nxt = pattern[i + 1]
            if nxt == "x" and i + 2 < len(pattern) and pattern[i + 2] == "{":
                end = pattern.index("}", i + 3)
                out.append("\\U%08x" % int(pattern[i + 3 : end], 16))
                i = end + 1
                continue
            if nxt == "z":
                out.append("\\Z")
                i += 2
                continue
            out.append(pattern[i : i + 2])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


# ── the manifest ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class Gate:
    contains: tuple[str, ...] = ()
    regex: tuple[re.Pattern[str], ...] = ()
    line_regex: tuple[re.Pattern[str], ...] = ()
    all: tuple["Gate", ...] = ()
    any: tuple["Gate", ...] = ()
    not_: tuple["Gate", ...] = ()

    def matches(self, text: str, lower: str) -> bool:
        if not all(needle in lower for needle in self.contains):
            return False
        if not all(rx.search(text) for rx in self.regex):
            return False
        if self.line_regex:
            lines = _lines(text)
            if not all(any(rx.search(line) for line in lines) for rx in self.line_regex):
                return False
        if not all(gate.matches(text, lower) for gate in self.all):
            return False
        if self.any and not any(gate.matches(text, lower) for gate in self.any):
            return False
        if any(gate.matches(text, lower) for gate in self.not_):
            return False
        return True


@dataclass(frozen=True)
class Rule:
    id: str
    state: str
    priority: int
    region: str
    gate: Gate
    skip_state_update: bool = False


@dataclass(frozen=True)
class Manifest:
    agent: str
    version: str
    source: str   # "bundled" | "local override"
    path: str
    rules: tuple[Rule, ...]
    aliases: tuple[str, ...] = ()


def _gate(raw: dict[str, Any], where: str) -> Gate:
    def compiled(key: str) -> tuple[re.Pattern[str], ...]:
        out = []
        for pattern in raw.get(key) or ():
            try:
                out.append(re.compile(rust_regex(str(pattern))))
            except re.error as exc:
                raise ValueError(f"{where}: {key} {pattern!r}: {exc}") from exc
        return tuple(out)

    return Gate(
        contains=tuple(str(n).lower() for n in raw.get("contains") or ()),
        regex=compiled("regex"),
        line_regex=compiled("line_regex"),
        all=tuple(_gate(g, where) for g in raw.get("all") or ()),
        any=tuple(_gate(g, where) for g in raw.get("any") or ()),
        not_=tuple(_gate(g, where) for g in raw.get("not") or ()),
    )


def parse_manifest(text: str, *, source: str = "bundled", path: str = "") -> Manifest:
    """One rule file. Raises ``ValueError`` on a rule that does not compile."""
    try:
        raw = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{path or 'rules'}: {exc}") from exc
    agent = str(raw.get("id") or "")
    rules = []
    for item in raw.get("rules") or ():
        rid = str(item.get("id") or "")
        state = str(item.get("state") or "unknown")
        if state not in STATES:
            raise ValueError(f"{path}: rule {rid}: unknown state {state!r}")
        rules.append(Rule(
            id=rid,
            state=state,
            priority=int(item.get("priority") or 0),
            region=str(item.get("region") or "whole_recent").strip(),
            gate=_gate(item, f"{path}: rule {rid}"),
            skip_state_update=bool(item.get("skip_state_update")),
        ))
    return Manifest(
        agent=agent, version=str(raw.get("version") or ""), source=source, path=path,
        rules=tuple(rules), aliases=tuple(str(a) for a in raw.get("aliases") or ()),
    )


_CACHE: dict[str, tuple[tuple[str, float], Manifest]] = {}
_CACHE_LOCK = threading.Lock()


def load_manifest(agent: str) -> Optional[Manifest]:
    """The agent's rules: the local override when one exists and parses,
    else the bundled file; ``None`` for an agent with neither. Cached on the
    file's path and modification time."""
    name = str(agent or "").strip().lower()
    if not name or "/" in name or name.startswith("."):
        return None
    candidates = [(override_dir() / f"{name}.toml", "local override"), (RULES_DIR / f"{name}.toml", "bundled")]
    for path, source in candidates:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        stamp = (str(path), mtime)
        with _CACHE_LOCK:
            hit = _CACHE.get(name)
            if hit is not None and hit[0] == stamp:
                return hit[1]
        try:
            manifest = parse_manifest(path.read_text(encoding="utf-8"), source=source, path=str(path))
        except (OSError, ValueError):
            continue   # an unreadable override falls back to the bundled file
        with _CACHE_LOCK:
            _CACHE[name] = (stamp, manifest)
        return manifest
    return None


# ── the regions (herdr's, line for line) ──────────────────────────────


def _lines(content: str) -> list[str]:
    """Rust's ``str::lines``: split on ``\\n``, drop one trailing empty line
    and a ``\\r`` at each line end."""
    parts = content.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]


def _start(content: str, lines: list[str], index: int) -> int:
    return min(sum(len(line) + 1 for line in lines[: min(index, len(lines))]), len(content))


def _from(content: str, lines: list[str], index: int) -> str:
    return content[_start(content, lines, index):]


def _is_rule_line(line: str) -> bool:
    trimmed = line.strip()
    if not trimmed:
        return False
    count = len(trimmed) - len(trimmed.lstrip("─"))
    if count == 0:
        return False
    return not trimmed[count:].lstrip() or count >= 3


def _codex_prompt(line: str) -> bool:
    return line == "›" or line.startswith("› ")


def _codex_block(line: str) -> bool:
    return line[:1] in ("•", "■", "✗", "✓")


def _codex_prompt_index(lines: list[str]) -> Optional[int]:
    found = [i for i, line in enumerate(lines) if _codex_prompt(line)]
    if not found:
        return None
    index = found[-1]
    if any(_codex_block(line) for line in lines[index + 1:]):
        return None
    return index


def _prompt_box_top(lines: list[str]) -> Optional[int]:
    seen = 0
    for index in range(len(lines) - 1, -1, -1):
        if _is_rule_line(lines[index]):
            seen += 1
            if seen == 2:
                return index
    return None


def region(spec: str, screen: str, title: str = "", progress: str = "") -> str:
    """The text one rule reads (herdr's ``region``)."""
    name = spec.strip()
    if name == "osc_title":
        return title
    if name == "osc_progress":
        return progress
    content = screen
    lines = _lines(content)
    if name == "whole_recent":
        return content
    if name == "after_last_prompt_marker":
        found = [i for i, line in enumerate(lines) if _codex_prompt(line)]
        return _from(content, lines, found[-1] + 1) if found else content
    if name == "before_current_prompt_marker":
        index = _codex_prompt_index(lines)
        return content if index is None else content[: _start(content, lines, index)]
    if name == "whole_recent_without_current_prompt_marker":
        return "" if _codex_prompt_index(lines) is not None else content
    if name in ("current_prompt_block_marker", "after_current_prompt_block_marker"):
        index = _codex_prompt_index(lines)
        if index is None:
            return ""
        blocks = [i for i in range(index) if _codex_block(lines[i])]
        if not blocks:
            return ""
        return lines[blocks[-1]] if name == "current_prompt_block_marker" else _from(content, lines, blocks[-1])
    if name == "prompt_box_body":
        top = _prompt_box_top(lines)
        if top is None:
            return ""
        end = next((top + 1 + i for i, line in enumerate(lines[top + 1:]) if _is_rule_line(line)), len(lines))
        return content[_start(content, lines, top + 1): _start(content, lines, end)]
    if name in ("above_prompt_box", "last_non_empty_above_prompt_box"):
        top = _prompt_box_top(lines)
        above = content if top is None else content[: _start(content, lines, top)]
        if name == "above_prompt_box":
            return above
        return next((line for line in reversed(_lines(above)) if line.strip()), "")
    if name == "after_last_horizontal_rule":
        offset = end = 0
        for line in content.split("\n"):
            nxt = offset + len(line) + 1
            if _is_rule_line(line):
                end = min(nxt, len(content))
            offset = nxt
        return content[end:]
    match = re.fullmatch(r"(bottom_lines|bottom_non_empty_lines|top_non_empty_lines)\((\d+)\)", name)
    if match:
        kind, count = match.group(1), int(match.group(2))
        if kind == "bottom_lines":
            return _from(content, lines, max(0, len(lines) - count))
        filled = [i for i, line in enumerate(lines) if line.strip()]
        if not filled or count <= 0:
            return ""
        if kind == "bottom_non_empty_lines":
            return _from(content, lines, filled[-count:][0])
        last = filled[:count][-1]
        return content[: _start(content, lines, last + 1)]
    return ""


# ── the verdict ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class Verdict:
    agent: str
    state: str
    rule: Optional[str] = None
    priority: int = 0
    region: str = ""
    evidence: tuple[str, ...] = ()
    manifest: str = ""
    version: str = ""
    source: str = ""
    fallback: Optional[str] = None
    skip_state_update: bool = False
    #: Every rule tried and whether it matched (``explain``).
    tried: tuple[tuple[str, int, bool], ...] = field(default=())

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "state": self.state,
            "rule": self.rule,
            "priority": self.priority,
            "region": self.region,
            "evidence": list(self.evidence),
            "manifest": self.manifest,
            "version": self.version,
            "source": self.source,
            "fallback": self.fallback,
            "skip_state_update": self.skip_state_update,
        }


def _evidence(text: str) -> tuple[str, ...]:
    lines = [line.rstrip() for line in _lines(text) if line.strip()]
    return tuple(line[:EVIDENCE_CHARS] for line in lines[-EVIDENCE_LINES:])


def read_screen(agent: str, screen: str, *, title: str = "", progress: str = "",
             manifest: Optional[Manifest] = None) -> Optional[Verdict]:
    """The state the screen shows, by the agent's rules; ``None`` for an
    agent with no rule file."""
    manifest = manifest or load_manifest(agent)
    if manifest is None:
        return None
    best: Optional[Rule] = None
    best_text = ""
    tried: list[tuple[str, int, bool]] = []
    for rule in manifest.rules:
        text = region(rule.region, screen, title, progress)
        hit = rule.gate.matches(text, text.lower())
        tried.append((rule.id, rule.priority, hit))
        if hit and (best is None or rule.priority > best.priority):
            best, best_text = rule, text
    common = {"agent": manifest.agent or agent, "manifest": manifest.path, "version": manifest.version,
              "source": manifest.source, "tried": tuple(tried)}
    if best is None:
        return Verdict(state="idle", fallback=IDLE_FALLBACK, evidence=_evidence(screen)[-3:], **common)
    return Verdict(
        state=best.state, rule=best.id, priority=best.priority, region=best.region,
        evidence=_evidence(best_text), skip_state_update=best.skip_state_update, **common,
    )


# ── what a blocked screen asks (was AG2's parse on the face) ───────────

_BOX = re.compile(r"[│┃║╭╮╰╯─━═┌┐└┘]")
_MENU = re.compile(r"^(?:[❯>›]\s*)?(\d+)\.\s+(\S.*)$")
_PROCEED = re.compile(r"do you want to (?:proceed|run|make this edit|allow)|allow command\?", re.IGNORECASE)
_HEADER = re.compile(r"^(?:●\s*)?[A-Z][\w ]*?(?:command|tool use|edit|write)\s*$", re.IGNORECASE)


def _clean(line: str) -> str:
    return _BOX.sub(" ", line).strip()


def menu_choices(screen: str) -> list[dict[str, str]]:
    """The agent's numbered menu: the last run of ``N. words`` lines (the
    selected one may wear ``❯``). Fewer than two: no menu."""
    rows = [_clean(line) for line in _lines(screen)]
    end = len(rows) - 1
    while end >= 0 and not _MENU.match(rows[end]):
        end -= 1
    if end < 0:
        return []
    start = end
    while start - 1 >= 0 and _MENU.match(rows[start - 1]):
        start -= 1
    out = []
    for row in rows[start : end + 1]:
        match = _MENU.match(row)
        label = re.sub(r"\s*\((?:esc|enter)\)\s*$", "", match.group(2), flags=re.IGNORECASE).strip()
        out.append({"n": match.group(1), "label": label})
    return out if len(out) >= 2 else []


def wants_to_run(screen: str) -> Optional[str]:
    """The command an approval prompt asks to run: the lines between the
    tool's header (``● Bash command``, ``Bash command``) and "Do you want to
    proceed?". ``None`` when the screen shows no such prompt."""
    rows = [_clean(line) for line in _lines(screen)]
    ask = len(rows) - 1
    while ask >= 0 and not _PROCEED.search(rows[ask]):
        ask -= 1
    if ask < 0:
        return None
    body: list[str] = []
    for i in range(ask - 1, max(-1, ask - 13), -1):
        row = rows[i]
        if _HEADER.match(row) or row.startswith("●") or _is_rule_line(row):
            break
        if not row:
            if body:
                break
            continue
        body.insert(0, row)
    command = "\n".join(body).strip()
    return command or None


def prompt_reading(screen: str) -> dict[str, Any]:
    """What a blocked screen asks: ``wait`` (``approve`` when it names a
    command to run, else ``question``), the ``command`` and the ``choices``."""
    command = wants_to_run(screen)
    return {
        "wait": "approve" if command else "question",
        "command": command,
        "choices": menu_choices(screen),
    }


_MESSAGE_MARK = ("●", "•", "⏺")


def last_message(screen: str) -> str:
    """The agent's last words: the last ``●`` (Claude Code) or ``•`` (Codex)
    block above the prompt, its continuation lines joined."""
    lines = _lines(screen)
    top = _prompt_box_top(lines)
    if top is not None:
        lines = lines[:top]
    start = None
    for index in range(len(lines) - 1, -1, -1):
        if lines[index].lstrip()[:1] in _MESSAGE_MARK:
            start = index
            break
    if start is None:
        return ""
    head = lines[start].lstrip()[1:].strip()
    words = [head]
    for line in lines[start + 1 :]:
        text = line.strip()
        if not text or _is_rule_line(text) or text.startswith(("⎿", ">", "❯", "›")):
            break
        words.append(text)
    return " ".join(w for w in words if w).strip()


__all__ = [
    "BUNDLED_AGENTS", "IDLE_FALLBACK", "Manifest", "Rule", "Verdict", "read_screen", "last_message",
    "load_manifest", "menu_choices", "override_dir", "parse_manifest", "prompt_reading", "region",
    "rust_regex", "wants_to_run",
]
