"""HS-201-11: the roadmap read survives a project with no next story.

`dw next --json` answers `{"next_story": null}` when nothing is actionable
(exit 2). `_project` read that key with a `{}` default and then called
`.get("story_id")` on the `None` the key actually held, so every desk load
that touched a quiet project raised `AttributeError` -- a 500 on the wire and
a console error on the page (rehearsal-07-opus.md defect 6: 34 tracebacks
across two hub runs).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from holdspeak.web.routes.roadmaps import _project


def _repo(tmp_path: Path, next_json: str) -> Path:
    """A repo root with one roadmap project and a stub `dw` CLI."""
    root = tmp_path / "repo"
    (root / "pm" / "roadmap" / "tiny").mkdir(parents=True)
    (root / "pm" / "roadmap" / "tiny" / "README.md").write_text("# Tiny\n", encoding="utf-8")
    hooks = root / ".githooks"
    hooks.mkdir()
    dw = hooks / "dw"
    dw.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = "next" ]; then\n'
        f"  printf '%s' '{next_json}'\n"
        "  exit 2\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    dw.chmod(dw.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    os.chmod(dw, 0o755)
    return root


def test_project_read_survives_a_null_next_story(tmp_path: Path) -> None:
    """`{"next_story": null}` is the real answer of `dw next` on a quiet project."""
    project = _project(_repo(tmp_path, '{"next_story": null}'), "tiny")
    assert project is not None
    assert project["nextStoryId"] is None


def test_project_read_survives_a_null_next_story_object(tmp_path: Path) -> None:
    """A `next_story` object still names the story it carries."""
    project = _project(
        _repo(tmp_path, '{"next_story": {"story_id": "HS-201-11"}}'), "tiny"
    )
    assert project is not None
    assert project["nextStoryId"] == "HS-201-11"


def test_project_read_survives_a_non_object_answer(tmp_path: Path) -> None:
    """A bare `null` parses as JSON and is not a mapping: still no traceback."""
    project = _project(_repo(tmp_path, "null"), "tiny")
    assert project is not None
    assert project["nextStoryId"] is None
