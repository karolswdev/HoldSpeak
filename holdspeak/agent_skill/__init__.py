"""The HoldSpeak agent skill and the two supported install layouts.

The skill is a package resource so ``holdspeak --skill`` and launches use the
same installed text. Agent config directories are supplied by the caller;
this module never reads or writes the owner's real home by itself.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

SKILL_NAME = "holdspeak"
SKILL_FILENAME = "SKILL.md"

# AG13 ownership survives one packaged wording upgrade.  This is the exact
# SHA-256 of the previous HoldSpeak skill shipped before the owner-started
# native-MCP wording.  A different same-name file belongs to the owner and
# must remain foreign.
PREVIOUS_SKILL_SHA256 = "3c1dea2767b6f4aa9e7ffe1377e046e6c7e73a940070be19725b5ad5707a5b04"


class SkillOwnershipError(ValueError):
    """A same-name skill is present but is not a HoldSpeak-owned version."""

    code = "skill_name_taken"

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"The skill at {path} belongs to another setup.")


def skill_path() -> Path:
    """Return the installed skill resource shipped with HoldSpeak."""

    return Path(__file__).with_name(SKILL_FILENAME)


def skill_text() -> str:
    """Read the exact skill text shipped with this HoldSpeak version."""

    return skill_path().read_text(encoding="utf-8")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _owned_digests() -> set[str]:
    return {PREVIOUS_SKILL_SHA256, _digest(skill_text().encode("utf-8"))}


def skill_state(path: Path) -> str:
    """Return ``missing``, ``installed``, ``outdated`` or ``foreign``."""

    try:
        data = Path(path).read_bytes()
    except FileNotFoundError:
        return "missing"
    except OSError:
        return "foreign"
    digest = _digest(data)
    current = _digest(skill_text().encode("utf-8"))
    if digest == current:
        return "installed"
    if digest == PREVIOUS_SKILL_SHA256:
        return "outdated"
    return "foreign"


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
    if destination.exists() and skill_state(destination) == "foreign":
        raise SkillOwnershipError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(skill_text(), encoding="utf-8")
    return destination


def uninstall_skill(config_dir: Path, agent: str) -> bool:
    """Remove only the exact HoldSpeak skill, preserving a foreign file."""

    destination = _skill_destination(Path(config_dir), agent)
    try:
        if skill_state(destination) not in {"installed", "outdated"}:
            return False
        destination.unlink()
    except FileNotFoundError:
        return False
    except OSError:
        return False
    # Empty directories are ours when this skill was the only file.  Removing
    # them is best effort and never reaches into a directory containing a
    # foreign skill.
    for directory in (destination.parent, destination.parent.parent):
        try:
            directory.rmdir()
        except OSError:
            break
    return True


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
    "PREVIOUS_SKILL_SHA256",
    "SkillOwnershipError",
    "install_codex_repo_skill",
    "install_launch_skills",
    "install_skill",
    "uninstall_skill",
    "skill_path",
    "skill_state",
    "skill_text",
]
