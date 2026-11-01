"""``holdspeak program``: the Programs verbs for his shell and for pi (PG-LANG LANG14).

Thin commands over the hub's one ``ProgramService`` (its REST routes; no
logic of their own):

    holdspeak program create --title T [--goal G] [--repo PATH] [--template ID] [--control LEVEL]
    holdspeak program start <program id>
    holdspeak program get <program id>
    holdspeak program decide <program id> <step id> --kind KIND --choice CHOICE [--lesson-id N]

``--json`` prints the hub's answer as it came. Without it, one plain line.
The hub: ``--url``, else ``HOLDSPEAK_URL``, else the running hub on this
machine. The credential: ``--token``, else ``HOLDSPEAK_AGENT_CREDENTIAL``
(an agent, such as pi: the service's agent rules apply), else
``HOLDSPEAK_TOKEN``, else the owner token of the hub on this machine (sent
only to a loopback address, never across a redirect).
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional, TextIO
from urllib import error as urlerror
from urllib import request as urlrequest


def build_program_subparsers(parser: Any) -> None:
    parser.add_argument("--url", default=None, help="The hub (default: HOLDSPEAK_URL, then this machine's hub)")
    parser.add_argument("--token", default=None, help="The credential (default: see `holdspeak program --help`)")
    sub = parser.add_subparsers(dest="program_command")
    create = sub.add_parser("create", help="Make a Program (Drafting)")
    create.add_argument("--title", required=True)
    create.add_argument("--goal", default=None)
    create.add_argument("--repo", dest="repository", default=None, help="The repository path")
    create.add_argument("--template", default=None)
    create.add_argument("--control", default=None, help="secure, normal or yolo")
    create.add_argument("--json", action="store_true")
    start = sub.add_parser("start", help="Start a Program")
    start.add_argument("program_id")
    start.add_argument("--json", action="store_true")
    get = sub.add_parser("get", help="Read a Program")
    get.add_argument("program_id")
    get.add_argument("--json", action="store_true")
    decide = sub.add_parser("decide", help="Answer one of his Your turn rows (the owner only)")
    decide.add_argument("program_id")
    decide.add_argument("step_id")
    decide.add_argument("--kind", required=True)
    decide.add_argument("--choice", required=True)
    decide.add_argument("--finding-id", default=None)
    decide.add_argument("--lesson-id", default=None)
    decide.add_argument("--reason", default=None)
    decide.add_argument("--json", action="store_true")


def _hub(url: Optional[str], token: Optional[str]) -> tuple[str, str]:
    from ..doctor import _base_url, _local_owner_token, resolve_hub_url

    base = _base_url(resolve_hub_url(url))
    credential = token or os.environ.get("HOLDSPEAK_AGENT_CREDENTIAL", "") or os.environ.get("HOLDSPEAK_TOKEN", "")
    if not credential and not url and not os.environ.get("HOLDSPEAK_URL", ""):
        from ..loopback_http import is_loopback_url, pin_loopback_url

        if is_loopback_url(base):
            base = pin_loopback_url(base)
            credential = _local_owner_token()
    return base, credential


class _NoRedirect(urlrequest.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None


def call(method: str, path: str, body: Optional[dict[str, Any]] = None, *, url: Optional[str] = None,
         token: Optional[str] = None, opener: Any = None) -> tuple[int, Any]:
    """One request to the hub: ``(status, answer)``."""
    base, credential = _hub(url, token)
    headers = {"Content-Type": "application/json"}
    if credential:
        headers.update({"Authorization": f"Bearer {credential}", "X-HoldSpeak-Token": credential})
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urlrequest.Request(f"{base}{path}", data=data, headers=headers, method=method)
    open_ = opener or urlrequest.build_opener(_NoRedirect).open
    try:
        with open_(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urlerror.HTTPError as exc:
        try:
            return exc.code, json.loads(exc.read().decode("utf-8") or "{}")
        except ValueError:
            return exc.code, {"error": str(exc)}
    except (urlerror.URLError, OSError) as exc:
        return 503, {"error": "hub_unreachable", "detail": f"No hub answers at {base}. Start it with `holdspeak web`."}


def _line(answer: Any) -> str:
    """One plain line from the hub's Program answer."""
    program = answer.get("program") if isinstance(answer, dict) and isinstance(answer.get("program"), dict) else answer
    if not isinstance(program, dict):
        return str(answer)
    title = program.get("title") or program.get("id") or "Program"
    words = program.get("line") or program.get("status_line") or program.get("state_word") or program.get("state") or ""
    return f"{program.get('id', '')} · {title} · {words}".strip(" ·")


def run_program_command(args: Any, *, out: Optional[TextIO] = None, opener: Any = None) -> int:
    stream = out or sys.stdout
    command = getattr(args, "program_command", None)
    if command is None:
        print("Say a verb: create, start, get or decide.", file=sys.stderr)
        return 2
    kw = {"url": args.url, "token": args.token, "opener": opener}
    if command == "create":
        body = {key: getattr(args, key) for key in ("title", "goal", "repository", "template", "control")
                if getattr(args, key) is not None}
        status, answer = call("POST", "/api/programs", body, **kw)
    elif command == "start":
        status, answer = call("POST", f"/api/programs/{args.program_id}/start", {}, **kw)
    elif command == "get":
        status, answer = call("GET", f"/api/programs/{args.program_id}", **kw)
    else:
        body = {"kind": args.kind, "choice": args.choice}
        for key, value in (("finding_id", args.finding_id), ("lesson_id", args.lesson_id), ("reason", args.reason)):
            if value is not None:
                body[key] = int(value) if key == "lesson_id" and str(value).isdigit() else value
        status, answer = call("POST", f"/api/programs/{args.program_id}/steps/{args.step_id}/decide", body, **kw)
    if args.json:
        print(json.dumps(answer, indent=2, ensure_ascii=False), file=stream)
    elif status >= 400:
        detail = answer.get("detail") or answer.get("error") if isinstance(answer, dict) else answer
        print(f"Refused: {detail}" if detail else f"Refused (HTTP {status})", file=stream)
    else:
        print(_line(answer), file=stream)
    return 0 if status < 400 else 1


__all__ = ["build_program_subparsers", "call", "run_program_command"]
