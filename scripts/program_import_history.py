#!/usr/bin/env python3
"""Make a Program from PRs that merged already (PG17).

The Programs engine's first Program is its own history: the refactor
program (#1584 to #1598) is made again from its PRs and shows Done.

    uv run python scripts/program_import_history.py \\
        --title "The hub stops stalling" --goal "..." \\
        --repository /Users/karol/dev/tools/HoldSpeak \\
        --pr 1584-1598 --hub http://127.0.0.1:8765

For each PR it reads the title, the merge commit and the merge time with
``gh pr view --json``, then posts ``POST /api/programs`` (create) and
``POST /api/programs/{id}/plan`` with one history step per merged PR to the
hub. A PR that did not merge is left out (one line on stderr says so). The
script never opens a database. ``--dry-run`` prints the payload and posts
nothing. The token: ``--token``, else ``$HOLDSPEAK_TOKEN``, else (a hub on
127.0.0.1 only) the owner token in the hub's config file.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Callable, Iterable, Mapping, Optional
from urllib.request import ProxyHandler, Request, build_opener

GH_FIELDS = "number,title,url,state,mergedAt,mergeCommit"
TITLE_MAX = 200


def pr_numbers(values: Iterable[str]) -> list[int]:
    """``1584``, ``1584-1598`` or ``1584,1590``: the PR numbers, in order, once."""
    out: list[int] = []
    for value in values:
        for part in str(value).split(","):
            part = part.strip().lstrip("#")
            if not part:
                continue
            if "-" in part:
                low, _, high = part.partition("-")
                first, last = int(low.lstrip("#")), int(high.lstrip("#"))
                if last < first:
                    raise ValueError(f"{part}: the range goes up")
                numbers = range(first, last + 1)
            else:
                numbers = range(int(part), int(part) + 1)
            out.extend(number for number in numbers if number not in out)
    return out


def _title(raw: str) -> str:
    title = " ".join(str(raw or "").split())
    if len(title) <= TITLE_MAX:
        return title
    cut = title[: TITLE_MAX - 1].rsplit(" ", 1)[0]
    return cut + "…"


def history_step(pr: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    """One plan step for a merged PR (``gh pr view --json`` fields), else ``None``."""
    if str(pr.get("state") or "").upper() != "MERGED" or not pr.get("mergedAt"):
        return None
    commit = pr.get("mergeCommit") if isinstance(pr.get("mergeCommit"), Mapping) else {}
    return {
        "title": _title(str(pr.get("title") or f"PR #{pr['number']}")),
        "history": {
            "pr_number": int(pr["number"]),
            "pr_url": pr.get("url") or None,
            "merged_at": str(pr["mergedAt"]),
            "head_commit": (commit or {}).get("oid") or None,
        },
    }


def build_payload(prs: Iterable[Mapping[str, Any]], *, title: str, goal: str, repository: str) -> dict[str, Any]:
    """The create and plan bodies; ``skipped`` lists the PRs that did not merge.
    Steps run in merge order."""
    steps, skipped = [], []
    for pr in prs:
        step = history_step(pr)
        if step is None:
            skipped.append({"number": pr.get("number"), "state": pr.get("state")})
        else:
            steps.append(step)
    steps.sort(key=lambda step: (step["history"]["merged_at"], step["history"]["pr_number"]))
    if not steps:
        raise ValueError("no PR in the list merged")
    return {
        "create": {"title": title, "goal": goal, "repository": repository},
        "plan": {"steps": steps},
        "skipped": skipped,
    }


def gh_pr_view(number: int, *, repo: Optional[str], cwd: Optional[str]) -> dict[str, Any]:
    command = ["gh", "pr", "view", str(number), "--json", GH_FIELDS]
    if repo:
        command += ["--repo", repo]
    done = subprocess.run(command, capture_output=True, text=True, cwd=cwd if cwd and os.path.isdir(cwd) else None)
    if done.returncode != 0:
        raise RuntimeError(f"gh pr view {number} failed: {done.stderr.strip() or done.stdout.strip()}")
    return json.loads(done.stdout)


def _loopback(url: str) -> bool:
    from urllib.parse import urlparse

    return (urlparse(url).hostname or "") in {"127.0.0.1", "localhost", "::1"}


def _token(given: Optional[str], hub: str) -> str:
    token = (given or os.environ.get("HOLDSPEAK_TOKEN") or "").strip()
    if token or not _loopback(hub):
        return token
    try:
        from holdspeak.mcp.server import _owner_token

        return _owner_token()
    except Exception:
        return ""


def post_json(hub: str, path: str, body: Mapping[str, Any], token: str) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-HoldSpeak-Token"] = token
    request = Request(hub.rstrip("/") + path, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    opener = build_opener(ProxyHandler({})) if _loopback(hub) else build_opener()
    with opener.open(request, timeout=30) as response:  # noqa: S310 - the hub he named
        return json.loads(response.read().decode("utf-8") or "{}")


def run(argv: Optional[list[str]] = None, *, view: Callable[..., dict[str, Any]] = gh_pr_view,
        post: Callable[..., dict[str, Any]] = post_json, out: Any = sys.stdout, err: Any = sys.stderr) -> int:
    parser = argparse.ArgumentParser(description="Make a Done Program from PRs that merged already (PG17).")
    parser.add_argument("--title", required=True)
    parser.add_argument("--goal", default="")
    parser.add_argument("--repository", required=True, help="The local git folder the Program is for (on the hub's machine).")
    parser.add_argument("--pr", action="append", required=True, help="A PR number, a range 1584-1598, or a list 1584,1590.")
    parser.add_argument("--gh-repo", default=None, help="owner/name for gh (default: the repository folder's remote).")
    parser.add_argument("--hub", default=os.environ.get("HOLDSPEAK_URL") or "http://127.0.0.1:8765")
    parser.add_argument("--token", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Print the payload; post nothing.")
    args = parser.parse_args(argv)

    numbers = pr_numbers(args.pr)
    prs = [view(number, repo=args.gh_repo, cwd=args.repository) for number in numbers]
    payload = build_payload(prs, title=args.title, goal=args.goal, repository=args.repository)
    for row in payload["skipped"]:
        print(f"PR #{row['number']} did not merge ({str(row['state'] or 'unknown').lower()}); left out", file=err)
    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=out)
        return 0
    token = _token(args.token, args.hub)
    made = post(args.hub, "/api/programs", payload["create"], token)
    program_id = str(made.get("id") or "")
    if not program_id:
        print(f"The hub did not make the program: {made}", file=err)
        return 1
    planned = post(args.hub, f"/api/programs/{program_id}/plan", payload["plan"], token)
    print(f"{planned.get('title')} · {planned.get('state_word')} · "
          f"{(planned.get('history') or {}).get('words') or str(len(payload['plan']['steps'])) + ' steps'} · {program_id}",
          file=out)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
