"""Step sizing for small-context engines (PG-LANG §5.4, the 64k rule).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §5.4. By
rule, no model:

    estimate(step) = the composed brief's tokens
                   + Σ owned files' bytes / 4 (a folder counts its files, at most 400)
                   + the harness's fixed cost
    fits(step)     = estimate(step) ≤ WORKING_SHARE × budget

One denominator (§5.4, reconciled with the journeys): every size word names
the working share, never the whole budget: with ``budget 64k`` a step reads
``18k of 32k``, and one that does not fit ``Too big for qwen · 41k of 32k``.

The planner (LANG6) sizes its draft with this; the Program wire gives each
Planned or Ready step its ``estimate``. The dispatcher's refusal and the
split by level are LANG8.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

#: §5.4 and §15.8 (approved 2026-10-31): half the window stays for the
#: agent's own reads, edits and the check's log tail. A constant, not a setting.
WORKING_SHARE = 0.5
#: A folder in ``owns`` counts at most this many of its files.
FOLDER_FILES_MAX = 400
#: The brief around the step's own words (``program_brief.compose``): the
#: frame, the goal and the two every-step lines of Build and review, measured
#: 2026-10-31 on the Programs rig as 1,534 characters.
BRIEF_FRAME_CHARS = 1534
#: The harness's own system prompt and tool list, per agent. Not measured
#: yet (PG-LANG §17; LANG8 measures it once per harness): 0 until then.
HARNESS_TOKENS: dict[str, int] = {"pi-default": 0, "claude-default": 0, "codex-default": 0}
_SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", ".tmp"}


def chars_tokens(chars: int) -> int:
    return int(math.ceil(max(0, chars) / 4))


def _inside(root: Path, path: str) -> Optional[Path]:
    text = str(path or "").strip()
    if not text or text.startswith(("/", "~")) or ".." in Path(text).parts:
        return None
    target = (root / text).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    return target


def path_bytes(root: Optional[str], path: str) -> int:
    """The bytes of one owned path: a file's size, a folder's files (at most
    400); 0 for a new file or a path outside the repository (never read)."""
    if not root:
        return 0
    base = Path(root)
    target = _inside(base, path)
    if target is None or not target.exists():
        return 0
    if target.is_file():
        return target.stat().st_size
    total, seen = 0, 0
    for folder, dirs, files in os.walk(target):
        dirs[:] = sorted(d for d in dirs if d not in _SKIP_DIRS)
        for name in sorted(files):
            if seen >= FOLDER_FILES_MAX:
                return total
            try:
                total += (Path(folder) / name).stat().st_size
            except OSError:
                pass
            seen += 1
    return total


def estimate(root: Optional[str], *, brief: str, owns: Iterable[str], requirements: Iterable[str] = (),
             profile: Optional[str] = None) -> int:
    """The step's estimate in tokens (§5.4)."""
    chars = BRIEF_FRAME_CHARS + len(brief or "") + sum(len(line) + 1 for line in requirements)
    files = sum(path_bytes(root, path) for path in owns or [])
    return chars_tokens(chars) + chars_tokens(files) + HARNESS_TOKENS.get(str(profile or ""), 0)


def k_words(tokens: int) -> str:
    """``18k`` (k = 1024, as the text's ``64k``); at least ``1k``."""
    return f"{max(1, int(round(tokens / 1024)))}k"


def share_of(budget: int) -> int:
    return int(budget * WORKING_SHARE)


def size(tokens: int, budget: Optional[int], engine: str) -> dict[str, Any]:
    """The size of one step: ``{tokens, budget, share, fits, words, engine}``;
    with no budget, ``fits`` is ``None`` and the words are the estimate only."""
    if not budget:
        return {"tokens": tokens, "budget": None, "share": None, "fits": None, "words": k_words(tokens),
                "engine": engine or None, "code": None}
    share = share_of(budget)
    fits = tokens <= share
    words = f"{k_words(tokens)} of {k_words(share)}"
    return {"tokens": tokens, "budget": budget, "share": share, "fits": fits,
            "words": words if fits else f"Too big for {engine or 'its engine'} · {words}",
            "engine": engine or None, "code": None if fits else "step_too_big"}


def engine_window(service: Any, engine_id: Optional[str]) -> tuple[Optional[int], str]:
    """``(context window, short name)`` of a library engine pi runs on."""
    if not engine_id:
        return None, ""
    try:
        found = service.engine(engine_id)
    except Exception:
        found = None
    if found is None:
        return None, str(engine_id)
    window = getattr(getattr(found, "engine", None), "context_window", None)
    return (int(window) if window else None), str(getattr(found, "short_name", "") or getattr(found, "label", "") or engine_id)


def budget_of(service: Any, *, explicit: Optional[int], program_budget: Optional[int], step_budget: Optional[int],
              agent: tuple[str, Optional[str]], default_engine: Optional[str]) -> tuple[Optional[int], str]:
    """``(budget, engine word)`` for one step (§5.4): a budget he gave the
    planner, else the step's, else the Program's, else the window of the
    engine pi runs on. Claude Code and Codex have none unless one is named."""
    profile, engine_id = agent
    from .program_text import AGENT_WORDS

    word = AGENT_WORDS.get(profile, profile)
    if profile == "pi-default":
        window, short = engine_window(service, engine_id or default_engine)
        word = short or "pi"
    else:
        window = None
    chosen = explicit or step_budget or program_budget
    if chosen:
        return int(chosen), word
    if profile == "pi-default":
        from ..delivery.pi_launch import DEFAULT_CONTEXT_WINDOW

        return int(window or DEFAULT_CONTEXT_WINDOW), word
    return None, word


def step_estimate(service: Any, program: Mapping[str, Any], step: Mapping[str, Any], *,
                  profile: Optional[str], engine_id: Optional[str],
                  requirements: Iterable[Mapping[str, Any]] = ()) -> dict[str, Any]:
    """A stored step's size (the wire's ``estimate``, §12)."""
    lines = [str(row.get("text") or "") for row in requirements or [] if row.get("step_id") == step.get("id")]
    tokens = estimate(program.get("repo_root"), brief=str(step.get("brief") or ""), owns=step.get("owns") or [],
                      requirements=lines, profile=profile)
    budget, word = budget_of(service, explicit=None, program_budget=program.get("budget_tokens"),
                             step_budget=step.get("budget_tokens"),
                             agent=(str(profile or "claude-default"), engine_id),
                             default_engine=program.get("default_engine"))
    return size(tokens, budget, word)


__all__ = [
    "BRIEF_FRAME_CHARS", "FOLDER_FILES_MAX", "HARNESS_TOKENS", "WORKING_SHARE", "budget_of", "chars_tokens",
    "engine_window", "estimate", "k_words", "path_bytes", "share_of", "size", "step_estimate",
]
