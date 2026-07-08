"""Pane discovery (HS-89-02) — attach beyond the registry.

`list_panes` names every tmux pane on the machine so a hand-started pane is
first-class. Fake runner: the parse, the typed absences, and the honest
empty list when no server is running.
"""

from __future__ import annotations

from types import SimpleNamespace

from holdspeak.coder_steering import list_panes


def _runner(stdout: str, returncode: int = 0, stderr: str = ""):
    return lambda argv, cwd=None: SimpleNamespace(
        stdout=stdout, returncode=returncode, stderr=stderr
    )


def test_list_panes_parses_every_field() -> None:
    out = (
        "%0\tmain\t0\tnvim\tedit\t1\n"
        "%3\twork\t1\tbash\t\t0\n"
    )
    result = list_panes(runner=_runner(out))
    assert result["status"] == "ok"
    assert result["panes"] == [
        {"pane_id": "%0", "session": "main", "window": "0", "command": "nvim", "title": "edit", "active": True},
        {"pane_id": "%3", "session": "work", "window": "1", "command": "bash", "title": "", "active": False},
    ]


def test_no_tmux_server_is_an_honest_empty_list() -> None:
    # `tmux list-panes -a` exits non-zero with "no server running" — that's
    # zero panes, not an error the desk should apologize for.
    result = list_panes(runner=_runner("", returncode=1, stderr="no server running"))
    assert result["status"] == "ok"
    assert result["panes"] == []


def test_blank_and_short_rows_are_skipped() -> None:
    out = "%0\tmain\t0\tbash\t\t1\n\n%incomplete\trow\n"
    result = list_panes(runner=_runner(out))
    assert [p["pane_id"] for p in result["panes"]] == ["%0"]
