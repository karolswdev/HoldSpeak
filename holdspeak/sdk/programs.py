"""``holdspeak.sdk.programs``: the Programs verbs for a Python script and for pi (PG-LANG LANG14).

A thin client over the hub's Programs routes, the same calls as the
``holdspeak program`` commands (``holdspeak/commands/program.py``): no logic
of its own; the hub's one ``ProgramService`` decides everything.

    from holdspeak.sdk.programs import Programs

    programs = Programs()                      # the hub on this machine
    made = programs.create("Overnight", repository="~/dev/app", template="fast-cycle")
    programs.start(made["id"])
    text = programs.text(made["id"])["text"]
    programs.decide(made["id"], step_id, kind="core", choice="go_on")

The hub is ``url``, else ``HOLDSPEAK_URL``, else the hub on this machine.
The credential is ``token``, else ``HOLDSPEAK_AGENT_CREDENTIAL`` (an agent:
the service's agent rules apply), else ``HOLDSPEAK_TOKEN``, else the owner
token of the hub on this machine (only to a loopback address, never across
a redirect). A refusal raises :class:`ProgramsRefused` with the hub's code
and words.
"""
from __future__ import annotations

from typing import Any, Optional


class ProgramsRefused(Exception):
    """The hub refused: ``status``, ``code`` and its words (``detail``)."""

    def __init__(self, status: int, answer: Any) -> None:
        body = answer if isinstance(answer, dict) else {}
        self.status = int(status)
        self.code = str(body.get("code") or body.get("error") or "refused")
        self.detail = str(body.get("detail") or body.get("error") or f"HTTP {status}")
        self.answer = answer
        super().__init__(self.detail)


class Programs:
    """The Programs routes of one hub."""

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None, *, opener: Any = None) -> None:
        self.url, self.token, self._opener = url, token, opener

    def _call(self, method: str, path: str, body: Optional[dict[str, Any]] = None) -> Any:
        from ..commands.program import call

        status, answer = call(method, path, body, url=self.url, token=self.token, opener=self._opener)
        if status >= 400:
            raise ProgramsRefused(status, answer)
        return answer

    def create(self, title: str, *, goal: Optional[str] = None, repository: Optional[str] = None,
               template: Optional[str] = None, control: Optional[str] = None, **fields: Any) -> dict[str, Any]:
        """Make a Program (Drafting). ``fields``: any field the create route takes."""
        body = {"title": title, **{key: value for key, value in (("goal", goal), ("repository", repository),
                                                                  ("template", template), ("control", control))
                                   if value is not None}, **fields}
        return self._call("POST", "/api/programs", body)

    def start(self, program_id: str) -> dict[str, Any]:
        return self._call("POST", f"/api/programs/{program_id}/start", {})

    def get(self, program_id: str) -> dict[str, Any]:
        return self._call("GET", f"/api/programs/{program_id}")

    def decide(self, program_id: str, step_id: str, *, kind: str, choice: str, finding_id: Optional[str] = None,
               lesson_id: Optional[int] = None, reason: Optional[str] = None) -> dict[str, Any]:
        """Answer one of his Your turn rows (the owner only; the hub refuses an agent)."""
        body: dict[str, Any] = {"kind": kind, "choice": choice}
        for key, value in (("finding_id", finding_id), ("lesson_id", lesson_id), ("reason", reason)):
            if value is not None:
                body[key] = value
        return self._call("POST", f"/api/programs/{program_id}/steps/{step_id}/decide", body)

    def text(self, program_id: str, new_text: Optional[str] = None, *, apply: bool = False,
             base: Optional[str] = None, allow_lower: Optional[list[str]] = None) -> dict[str, Any]:
        """Read the Program as its text; with ``new_text``, change it by its
        whole text: a dry run (the change rows) unless ``apply``."""
        if new_text is None:
            return self._call("GET", f"/api/programs/{program_id}/text")
        body: dict[str, Any] = {"text": new_text, "dry_run": not apply}
        if base is not None:
            body["base"] = base
        if allow_lower:
            body["allow_lower"] = list(allow_lower)
        return self._call("POST", f"/api/programs/{program_id}/text", body)


__all__ = ["Programs", "ProgramsRefused"]
