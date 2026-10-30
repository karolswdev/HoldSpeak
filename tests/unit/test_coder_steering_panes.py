"""Pane discovery (HS-89-02) — attach beyond the registry.

`list_panes` names every tmux pane on the machine so a hand-started pane is
first-class. Fake runner: the parse, the typed absences, and the honest
empty list when no server is running.
"""

from __future__ import annotations

from types import SimpleNamespace

from holdspeak.coder_steering import (
    arm,
    clear_grants,
    list_panes,
    require_grant,
    resolve_pane_identity,
)


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


def test_list_panes_keeps_live_path_and_process_identity_metadata() -> None:
    out = (
        "%0\tmain\t0\tbash\t\t1\t501\t/dev/ttys001\t"
        "/work\tsess-main\t@1\t0\tbash\t/tmp/tmux-501/default\t500\n"
    )
    result = list_panes(runner=_runner(out))
    pane = result["panes"][0]
    assert pane["current_path"] == "/work"
    assert pane["pane_pid"] == "501"
    assert pane["server_pid"] == "500"
    assert pane["fingerprint"].startswith("sha256:")


def test_identity_parser_keeps_path_out_of_fingerprint() -> None:
    row = (
        "%0\t501\t/dev/ttys001\t/work\t$s1\t@1\t0\t0\t"
        "bash\ttitle\t1\tbash --norc\t/tmp/tmux/default\t500\t"
        "120\t36\t7\t4\n"
    )
    first = resolve_pane_identity("main:0.0", runner=_runner(row))
    moved = resolve_pane_identity(
        "main:0.0", runner=_runner(row.replace("/work", "/work/other"))
    )
    assert first["current_path"] == "/work"
    assert first["fingerprint"] == moved["fingerprint"]
    assert first["pane_pid"] == "501" and first["server_pid"] == "500"
    assert first["pane"] == {"width": 120, "height": 36, "cursor_x": 7, "cursor_y": 4}


def _identity_row(*, pane_pid: str, server_pid: str = "500") -> str:
    return "\t".join(
        (
            "%0",
            pane_pid,
            "/dev/ttys001",
            "/work",
            "$s1",
            "@1",
            "0",
            "0",
            "bash",
            "title",
            "1",
            "bash --norc",
            "/tmp/tmux/default",
            server_pid,
            "120",
            "36",
            "7",
            "4",
        )
    )


def test_arm_refuses_same_pane_id_after_process_respawn() -> None:
    rows = iter((_identity_row(pane_pid="501"), _identity_row(pane_pid="777")))

    def runner(argv, cwd=None):
        return SimpleNamespace(stdout=next(rows) + "\n", returncode=0, stderr="")

    clear_grants()
    try:
        armed = arm("codex:respawn", "main:0.0", runner=runner, clock=lambda: 0.0)
        assert armed["status"] == "armed"
        refused = require_grant(
            "codex:respawn", "main:0.0", runner=runner, clock=lambda: 0.0
        )
        assert refused == {
            "status": "pane_mismatch",
            "detail": "the pane process identity changed — nothing was typed",
            "revoked": True,
        }
    finally:
        clear_grants()
