"""HS-S32 (G32, the first branch): the delivery line's recovery, pure.

What a held delivery line allows (``program_delivery.recovery``), when a
receipt's PR identity is whole (``known_pr``), and what one read of the PR
(``_read``, a recording runner, no subprocess) may conclude. The route,
ledger and rig half is ``tests/integration/test_program_delivery.py``.
"""
from __future__ import annotations

import argparse
import io
import json
from types import SimpleNamespace
from typing import Any

from holdspeak.services import program_delivery as delivery

URL = "https://github.com/acme/app/pull/12"
PR = {"url": URL, "number": 12, "branch": "program/x/delivery", "base": "main", "head": "a" * 40}


def _row(choice: str, receipt: Any = None, *, ident: int = 5, **undo: Any) -> dict[str, Any]:
    return {"id": ident, "kind": "delivery", "choice": choice,
            "undo": {**undo, **({"receipt": receipt} if receipt is not None else {})}}


def _receipt(**over: Any) -> dict[str, Any]:
    return {"v": 1, "stage": "merge", "remote": True, "target": {"ref": "dw:app/1", "words": "dw app/1"},
            "pr": dict(PR), **over}


def test_known_pr_needs_the_whole_identity() -> None:
    assert delivery.known_pr(_receipt()) == PR
    for drop in ("url", "number", "branch", "base", "head"):
        pr = {key: value for key, value in PR.items() if key != drop}
        assert delivery.known_pr(_receipt(pr=pr)) is None, drop
    assert delivery.known_pr(_receipt(pr={**PR, "number": 13})) is None  # the URL names another PR
    assert delivery.known_pr(_receipt(pr={**PR, "url": "github.com/acme/app/pull/12"})) is None
    assert delivery.known_pr({}) is None


def test_each_line_offers_what_its_receipt_proves() -> None:
    state = lambda row, rows=None: (delivery.recovery(row, rows) or {}).get("state")  # noqa: E731
    choices = lambda row, rows=None: (delivery.recovery(row, rows) or {}).get("choices")  # noqa: E731
    # A known PR: open (Merge), requested (Check), not confirmed (Check).
    assert choices(_row("pr_open", _receipt(stage="pr"))) == ["merge", "check", "skip"]
    assert choices(_row("pr_open", _receipt(merge_requested_at="t"))) == ["check", "skip"]
    assert state(_row("failed", _receipt(merge_requested_at="t"))) == "requested"
    assert choices(_row("failed", _receipt(stage="check"))) == ["check", "skip"]
    # C32-02: a stop before any remote write retries.
    local = _receipt(stage="evidence", remote=False, pr={"branch": "b", "base": "main"})
    assert choices(_row("failed", local)) == ["retry", "skip"]
    # ... unless another line shows a remote effect.
    earlier = _row("failed", _receipt(stage="push", pr={}), ident=3)
    assert choices(_row("failed", local), [_row("failed", local), earlier]) == ["skip"]
    # C32-03: push or create attempted, no acknowledged PR: blocked.
    assert choices(_row("failed", _receipt(stage="push", pr={"branch": "b"}))) == ["skip"]
    assert choices(_row("failed", _receipt(stage="pr", pr={"branch": "b", "head": "c"}))) == ["skip"]
    # C32-09: old lines (no receipt) are blocked, a PR number or not.
    assert choices(_row("failed", None, pr_number=7, branch="b")) == ["skip"]
    assert choices(_row("pr_open", None, pr_number=7, branch="b")) == ["skip"]
    assert choices(_row("failed", None, words="Delivery Workbench did not take the evidence")) == ["skip"]
    # Answered lines hold nothing.
    assert delivery.recovery(_row("delivered", _receipt())) is None
    assert delivery.recovery(_row("skipped", _receipt())) is None
    assert delivery.recovery(None) is None


class _Runner:
    def __init__(self, answer: Any) -> None:
        self.answer, self.calls = answer, []

    def _run(self, argv: list[str], cwd: str = "", **kw: Any) -> Any:
        self.calls.append(list(argv))
        if isinstance(self.answer, BaseException):
            raise self.answer
        return self.answer


def _gh(**over: Any) -> SimpleNamespace:
    data = {"url": URL, "number": 12, "state": "OPEN", "headRefOid": "a" * 40, "baseRefName": "main",
            "headRefName": "program/x/delivery", "isCrossRepository": False, **over}
    return SimpleNamespace(returncode=0, stdout=json.dumps(data), stderr="")


def test_one_read_by_url_and_only_a_whole_match_is_a_yes() -> None:
    """C32-05, C32-06, C32-07: one bounded read command; every mismatch,
    error or unreadable answer is never merged or open."""
    runner = _Runner(_gh())
    assert delivery._read(runner, {"repo_root": "/r"}, PR)["result"] == "open"
    assert runner.calls == [["gh", "pr", "view", URL, "--json",
                             "url,number,state,headRefOid,baseRefName,headRefName,isCrossRepository"]]
    assert delivery._read(_Runner(_gh(state="MERGED")), {}, PR)["result"] == "merged"
    assert delivery._read(_Runner(_gh(state="CLOSED")), {}, PR)["result"] == "closed"
    cases = {
        "foreign": _gh(url="https://github.com/other/app/pull/12"),
        "number": _gh(number=13),
        "fork": _gh(isCrossRepository=True),
        "fork_unknown": _gh(isCrossRepository=None),
        "base": _gh(baseRefName="release"),
        "branch": _gh(headRefName="someone/else"),
        "head": _gh(headRefOid="b" * 40, state="MERGED"),
    }
    for name, answer in cases.items():
        assert delivery._read(_Runner(answer), {}, PR)["result"] == "mismatch", name
    for name, answer in {"nonzero": SimpleNamespace(returncode=1, stdout="", stderr="HTTP 401"),
                         "timeout": TimeoutError("timed out"), "garbage": SimpleNamespace(returncode=0, stdout="<html>"),
                         "list": SimpleNamespace(returncode=0, stdout="[]"),
                         "state": _gh(state="QUEUED_SOMEHOW")}.items():
        assert delivery._read(_Runner(answer), {}, PR)["result"] == "unavailable", name
    huge = SimpleNamespace(returncode=0, stdout=json.dumps({**json.loads(_gh().stdout), "pad": "x" * 50000}))
    assert delivery._read(_Runner(huge), {}, PR)["result"] == "unavailable"  # bounded: cut, not parsed whole


def test_the_adapters_carry_the_delivery_line() -> None:
    """C32-10: the MCP schema, the SDK and the CLI send the row's line."""
    from holdspeak.commands.program import build_program_subparsers, run_program_command
    from holdspeak.mcp.families.program import TOOLS
    from holdspeak.sdk.programs import Programs

    [tool] = [row for row in TOOLS if row["name"] == "program.decide"]
    assert "expected_delivery_checkpoint_id" in tool["inputSchema"]["properties"]
    sent: list[Any] = []
    sdk = Programs.__new__(Programs)
    sdk._call = lambda method, path, body=None: sent.append(body) or {}
    sdk.decide("p1", "program", kind="delivery", choice="check", expected_delivery_checkpoint_id=9)
    assert sent == [{"kind": "delivery", "choice": "check", "expected_delivery_checkpoint_id": 9}]

    class _Answer:
        status = 200

        def __init__(self, req: Any) -> None:
            sent.append(json.loads(req.data.decode("utf-8")))

        def read(self) -> bytes:
            return b"{}"

        def __enter__(self) -> "_Answer":
            return self

        def __exit__(self, *exc: Any) -> None:
            return None

    parser = argparse.ArgumentParser(prog="holdspeak")
    build_program_subparsers(parser.add_subparsers(dest="command").add_parser("program"))
    args = parser.parse_args(["program", "--url", "http://127.0.0.1:1", "--token", "t", "decide", "p1", "program",
                              "--kind", "delivery", "--choice", "skip", "--expected-delivery-checkpoint-id", "9"])
    run_program_command(args, out=io.StringIO(), opener=lambda req, timeout=0: _Answer(req))
    assert sent[-1] == {"kind": "delivery", "choice": "skip", "expected_delivery_checkpoint_id": 9}
