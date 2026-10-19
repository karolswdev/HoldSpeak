"""The HoldSpeak agent skill and the two supported install layouts.

The skill is a package resource so ``holdspeak --skill`` and launches use the
same installed text. Agent config directories are supplied by the caller;
this module never reads or writes the owner's real home by itself.
"""

from __future__ import annotations

from pathlib import Path

SKILL_NAME = "holdspeak"
SKILL_FILENAME = "SKILL.md"


def skill_path() -> Path:
    """Return the installed skill resource shipped with HoldSpeak."""

    return Path(__file__).with_name(SKILL_FILENAME)


def skill_text() -> str:
    """Read the exact skill text shipped with this HoldSpeak version."""

    return skill_path().read_text(encoding="utf-8")


def _skill_destination(config_dir: Path, agent: str) -> Path:
    """Return the skill path for one agent config directory.

    Callers supply Claude's ``.claude`` directory or Codex's native
    ``.agents`` directory. Private launch copies use the same file layout;
    launchers bind them through each agent's discovery mechanism.
    """

    if agent in {"claude", "codex"}:
        return config_dir / "skills" / SKILL_NAME / SKILL_FILENAME
    raise ValueError(f"unsupported agent: {agent}")


def install_skill(config_dir: Path, agent: str) -> Path:
    """Install this version of the skill below *config_dir* for *agent*.

    Only the HoldSpeak skill file is replaced. Other files and skills in the
    directory stay untouched. Repeating the operation produces the same
    bytes and path.
    """

    destination = _skill_destination(Path(config_dir), agent)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(skill_text(), encoding="utf-8")
    return destination


def install_launch_skills(settings_dir: Path) -> dict[str, Path]:
    """Place both agent layouts in one launch settings directory."""

    root = Path(settings_dir)
    return {
        "claude": install_skill(root / ".claude", "claude"),
        "codex": install_skill(root, "codex"),
    }


def install_codex_repo_skill(worktree_dir: Path) -> Path:
    """Install the skill where Codex discovers repo skills from its CWD."""

    return install_skill(Path(worktree_dir) / ".agents", "codex")


__all__ = [
    "SKILL_FILENAME",
    "SKILL_NAME",
    "install_codex_repo_skill",
    "install_launch_skills",
    "install_skill",
    "skill_path",
    "skill_text",
]
