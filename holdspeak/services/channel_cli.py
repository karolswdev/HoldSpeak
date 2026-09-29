"""PHILO-10-02: the GitHub, Jira and Confluence channels (``design/send-lifecycle.md`` sections 3-6).

Each channel is the Phase 38 write seam as it is: one ``WriteConnectorManifest``
(``shell:exec`` and its argv prefixes), a ``plan`` (the one argv, the body only
as a path to the private 0600 payload file) and an ``interpret`` (the native
answer -> SENT with the channel's proof, FAILED only on the pinned
known-non-delivery list, UNKNOWN for everything else). Every command runs
through ``build_gated_connector`` as a ``subprocess.exec`` CHILD of the send,
under the send's authenticated owner principal, through the send's broker
(design section 6). No framework: three classes and the registry's dict rows.

* **GitHub:** ``gh issue|pr comment <n> --repo <host/owner/repo> --body-file
  <file>``; proof = the comment URL for the frozen target. The destination
  freezes ``{host, login}`` (read at save with ``gh api user --hostname``); the
  send reads it again BEFORE the boundary and refuses ``github_identity_changed``
  or ``github_not_logged_in`` by name (section 5). Residual window, named not
  engineered away (Tenet 1): a ``gh auth switch`` by hand between that read and
  the command.
* **Jira:** ``acli jira workitem comment create --key <ONE canonical key>
  --body-file <file> --json``; never ``--jql``, ``--filter`` or
  ``--edit-last``; a second key is refused ``jira_key_not_single``.
* **Confluence:** ``acli confluence blog create --space-id <id> --from-json
  <file> --json``: the title and the storage-format body in the ONE private
  JSON file, no title in argv (Q3, "Blog post"). UNVERIFIED: the JSON field
  names ``acli`` reads are unknown until the real-account leg (the grounding
  probe answered ``unauthorized`` before reading the file).
* **Atlassian:** switch -> status -> create under the existing cross-process
  ``_ACLI_LOCK`` (``services/jira_provider.py``); create runs only when the
  status read-back names the frozen site and email (the switch-and-verify law).
  The send does not switch his account back (the probe precedent does not).

Tests replace :data:`CLI_RUNNER` (the process edge) with a canned runner.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Mapping, Optional

from ..plugins.gated_connector import (
    ConnectorOperationRefused,
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)
from .channel_contract import ChannelRefused, Document, Outcome, private_payload_file, redact, sha256
from .errors import ValidationError

#: The process edge every CLI channel command goes through (tests can it).
CLI_RUNNER: Any = subprocess.run
#: Seconds a create command may run; past it the answer is UNKNOWN (``timeout``).
CREATE_TIMEOUT = 60.0
_FORBIDDEN_FLAGS = ("--jql", "--filter", "--edit-last")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_HOST = re.compile(r"^[A-Za-z0-9.-]+(:[0-9]+)?$")
_JIRA_KEY = re.compile(r"^[A-Z][A-Z0-9_]+-[1-9][0-9]*$")
_SPACE_ID = re.compile(r"^[0-9]{1,20}$")


@dataclass(frozen=True)
class Seam:
    """The send's authority for its children: the authenticated owner, the send, the broker."""

    principal: Any
    parent_operation_id: str
    broker: Any
    #: The process edge for this send (``None``: :data:`CLI_RUNNER`); the nudge passes its service's runner.
    runner: Any = None


def _run(manifest: WriteConnectorManifest, op: GatedOperation, seam: Seam) -> Any:
    """One command as a ``subprocess.exec`` child of the send (plan -> kernel -> the native answer)."""
    connector = build_gated_connector(
        manifest, plan=lambda _proposal: op, interpret=lambda raw, _op: raw, runner=seam.runner or CLI_RUNNER,
        principal=seam.principal, parent_operation_id=seam.parent_operation_id, broker=seam.broker)
    return connector(None)


def _guard(argv: tuple[str, ...], manifest: WriteConnectorManifest) -> tuple[str, ...]:
    """A plan can only be built with the manifest's prefix and none of the forbidden flags."""
    if not any(argv[:len(prefix)] == prefix for prefix in manifest.allowed_argv_prefixes):
        raise ValueError("argv_not_on_manifest")
    if any(part.split("=", 1)[0] in _FORBIDDEN_FLAGS for part in argv):
        raise ValueError("forbidden_flag")
    return argv


def _native(completed: Any) -> tuple[int, str, str]:
    code = completed.get("returncode") if isinstance(completed, Mapping) else getattr(completed, "returncode", None)
    out = completed.get("stdout") if isinstance(completed, Mapping) else getattr(completed, "stdout", "")
    err = completed.get("stderr") if isinstance(completed, Mapping) else getattr(completed, "stderr", "")
    return (int(code) if code is not None else -1), str(out or ""), str(err or "")


def _first_pinned(text: str, pinned: tuple[tuple[str, str], ...]) -> Optional[str]:
    lowered = text.lower()
    for phrase, code in pinned:
        if phrase in lowered:
            return code
    return None


def _json_id(stdout: str) -> Optional[dict[str, Any]]:
    """The created object's id from an ``acli --json`` answer (shape PROVISIONAL until a real send)."""
    try:
        data = json.loads(stdout)
    except (TypeError, ValueError):
        return None
    if isinstance(data, list) and len(data) == 1:
        data = data[0]
    if not isinstance(data, dict):
        return None
    ident = data.get("id") or data.get("commentId")
    if not isinstance(ident, (str, int)) or not str(ident).strip():
        return None
    proof = {"id": str(ident)}
    links = data.get("_links") if isinstance(data.get("_links"), dict) else {}
    for key in ("self", "webui", "url"):
        value = data.get(key) or links.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://", "/")):
            proof["url"] = value
            break
    return proof


class CliChannel:
    """What the three CLI channels share: the dispatch of one planned command and the outcome rules."""

    name = ""
    manifest: WriteConnectorManifest
    suffix = ".txt"
    #: Pinned known non-delivery: (a phrase of the raw native error, its FIXED code).
    PINNED: tuple[tuple[str, str], ...] = ()

    @staticmethod
    def badge(synced: bool) -> str:
        return "cloud"

    def serialize(self, document: Document) -> bytes:
        return document.body_md.encode("utf-8")

    def preview(self, payload: bytes) -> dict[str, Any]:
        return {"text": payload.decode("utf-8", errors="replace")}

    def recover(self, row: Mapping[str, Any]) -> Outcome:
        """A ``dispatching`` row found by a take-over: NEVER dispatch again. HoldSpeak cannot know."""
        return Outcome("unknown", "interrupted")

    # -- the effect ---------------------------------------------------------

    def _dispatch_one(self, op_for: Any, row: Mapping[str, Any], seam: Seam, target: Mapping[str, Any]) -> Outcome:
        """The private payload file, the digest re-checked, the one command, its outcome."""
        payload, digest = bytes(row["payload"]), str(row["payload_digest"])
        try:
            with private_payload_file(payload, digest, suffix=self.suffix) as path:
                op = op_for(path)
                return self._outcome(lambda: _run(self.manifest, op, seam), payload, target)
        except ChannelRefused as exc:  # the file's digest did not match: nothing ran
            return Outcome("failed", exc.code)
        except ValueError as exc:  # the plan could not be built: nothing ran
            return Outcome("failed", "plan_refused", detail=redact(str(exc), payload))

    def _outcome(self, call: Any, payload: bytes, target: Mapping[str, Any]) -> Outcome:
        from ..kernel.subprocess_exec import SubprocessOutcomeIndeterminate

        try:
            completed = call()
        except SubprocessOutcomeIndeterminate as exc:
            if isinstance(exc.cause, subprocess.TimeoutExpired):
                return Outcome("unknown", "timeout")
            return Outcome("unknown", f"{self.name}_interrupted", detail=redact(type(exc.cause).__name__))
        except ConnectorOperationRefused as exc:
            # The kernel refused the child: the command never ran (a known non-delivery).
            return Outcome("failed", "subprocess_refused", detail=redact(exc.reason, payload))
        except FileNotFoundError:
            return Outcome("failed", f"{self.name}_cli_missing")
        except OSError as exc:
            return Outcome("failed", f"{self.name}_cli_not_started", detail=redact(type(exc).__name__))
        return self.interpret(completed, payload, target)

    def interpret(self, completed: Any, payload: bytes, target: Mapping[str, Any]) -> Outcome:
        """Exit 0 with a valid proof: SENT. A pinned error: FAILED. Anything else: UNKNOWN."""
        code, out, err = _native(completed)
        detail = redact(err or out, payload) or None
        if code == 0:
            proof = self.proof(out, target)
            if proof is None:
                return Outcome("unknown", f"{self.name}_no_proof", detail=detail)
            return Outcome("sent", None, proof)
        pinned = self.pinned(code, err + "\n" + out)
        if pinned:
            return Outcome("failed", pinned, detail=detail)
        return Outcome("unknown", f"{self.name}_exit_{code}", detail=detail)

    def pinned(self, code: int, text: str) -> Optional[str]:
        return _first_pinned(text, self.PINNED)

    def proof(self, stdout: str, target: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        return _json_id(stdout)


# ── GitHub ──────────────────────────────────────────────────────────────


class GitHubChannel(CliChannel):
    """A comment on an issue or a pull request (Q2); the gist is parked."""

    name = "github"
    suffix = ".md"
    manifest = WriteConnectorManifest(
        connector_id="channel_github", permission="shell:exec", label="GitHub comment (Send)",
        description="gh issue comment / gh pr comment with --body-file only.",
        allowed_argv_prefixes=(("gh", "issue", "comment"), ("gh", "pr", "comment")),
    )
    #: Exit 4 is gh's "authentication required"; these answers come before a comment exists.
    PINNED = (
        ("could not resolve to a repository", "github_repository_not_found"),
        ("could not resolve to an issue", "github_target_not_found"),
        ("could not resolve to a pullrequest", "github_target_not_found"),
        ("http 404", "github_target_not_found"),
        ("resource not accessible", "github_permission_denied"),
        ("http 403", "github_permission_denied"),
        ("permission denied", "github_permission_denied"),
    )

    def pinned(self, code: int, text: str) -> Optional[str]:
        if code == 4:
            return "github_not_authenticated"
        return _first_pinned(text, self.PINNED)

    # -- save and the identity --------------------------------------------

    def target_at_save(self, args: Mapping[str, Any], principal: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        host = str(args.get("host") or "github.com").strip().lower()
        repo = str(args.get("repo") or "").strip()
        kind = str(args.get("kind") or "issue").strip().lower()
        try:
            number = int(args.get("number") or 0)
        except (TypeError, ValueError):
            number = 0
        if not _HOST.fullmatch(host) or not _REPO.fullmatch(repo) or kind not in {"issue", "pr"} or number < 1:
            raise ValidationError("A GitHub destination needs owner/repo, issue or pr, and a number of 1 or more",
                                  code="github_target_invalid")
        login = self.login(host, principal)
        if not login:
            raise ChannelRefused("github_not_logged_in", f"gh is not logged in to {host}")
        return {"host": host, "login": login}, {"host": host, "repo": repo, "kind": kind, "number": number}

    @staticmethod
    def login(host: str, principal: Any) -> str:
        """``gh api user --hostname <host>``: a classified CLI read (not an effect). "" when not logged in."""
        from ..connector_packs import github_cli
        from ..connector_runtime import PermissionGate

        try:
            completed = PermissionGate(github_cli.MANIFEST).run_read_subprocess(
                ["gh", "api", "user", "--hostname", host], principal=principal, runner=CLI_RUNNER,
                stdin=subprocess.DEVNULL, capture_output=True, text=True, errors="replace", timeout=15.0)
        except subprocess.TimeoutExpired as exc:
            raise ChannelRefused("github_identity_unverified", "gh api user did not answer") from exc
        except OSError as exc:
            raise ChannelRefused("github_cli_missing", "gh is not installed") from exc
        code, out, _err = _native(completed)
        if code != 0:
            return ""
        try:
            return str((json.loads(out) or {}).get("login") or "").strip()
        except (TypeError, ValueError, AttributeError):
            return ""

    def check_before_dispatch(self, target: Mapping[str, Any], *, account: Mapping[str, Any],
                              principal: Any, **_: Any) -> None:
        """Before the boundary: the frozen target is valid and gh is still logged in as the frozen login."""
        if not _REPO.fullmatch(str(target.get("repo") or "")) or int(target.get("number") or 0) < 1:
            raise ChannelRefused("destination_changed", "The frozen GitHub target is not valid")
        host = str(account.get("host") or target.get("host") or "github.com")
        login = self.login(host, principal)
        if not login:
            raise ChannelRefused("github_not_logged_in", f"gh is not logged in to {host}")
        if login.lower() != str(account.get("login") or "").lower():
            raise ChannelRefused("github_identity_changed",
                                 f"gh is logged in to {host} as another account than the one saved")

    # -- the plan and the effect --------------------------------------------

    def plan(self, target: Mapping[str, Any], path: str) -> GatedOperation:
        host, repo = str(target.get("host") or "github.com"), str(target.get("repo") or "")
        kind, number = str(target.get("kind") or ""), int(target.get("number") or 0)
        if not _REPO.fullmatch(repo) or kind not in {"issue", "pr"} or number < 1 or not _HOST.fullmatch(host):
            raise ValueError("github_target_invalid")
        where = repo if host == "github.com" else f"{host}/{repo}"
        argv = _guard(("gh", kind, "comment", str(number), "--repo", where, "--body-file", path), self.manifest)
        return GatedOperation.subprocess(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                         errors="replace", timeout=CREATE_TIMEOUT)

    def proof(self, stdout: str, target: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        """The comment URL for THE frozen target, or nothing."""
        host = re.escape(str(target.get("host") or "github.com"))
        repo = re.escape(str(target.get("repo") or ""))
        path = "pull" if target.get("kind") == "pr" else "issues"
        found = re.search(rf"https://{host}/{repo}/{path}/{int(target.get('number') or 0)}#issuecomment-[0-9]+",
                          stdout, re.IGNORECASE)
        return {"url": found.group(0)} if found else None

    def dispatch(self, row: Mapping[str, Any], seam: Optional[Seam] = None) -> Outcome:
        target = json.loads(row["target_json"] or "{}")
        return self._dispatch_one(lambda path: self.plan(target, path), row, _need(seam), target)

    def comment(self, target: Mapping[str, Any], payload: bytes, seam: Seam) -> Outcome:
        """The nudge's path (F4, F5): the same plan, file, child and outcome rules, without a destination."""
        row = {"payload": payload, "payload_digest": sha256(payload)}
        return self._dispatch_one(lambda path: self.plan(target, path), row, seam, target)


# ── Atlassian (Jira and Confluence) ────────────────────────────────────────


class _Atlassian(CliChannel):
    product = ""

    def target_account(self, args: Mapping[str, Any]) -> dict[str, Any]:
        from .jira_provider import _normalize_site

        site = _normalize_site(str(args.get("site") or ""))
        email = str(args.get("email") or "").strip().lower()
        if "@" not in email or any(ch.isspace() for ch in email):
            raise ValidationError("An Atlassian destination needs the account's email", code="atlassian_email_invalid")
        return {"site": site, "email": email}

    def check_before_dispatch(self, target: Mapping[str, Any], **_: Any) -> None:
        self.valid(target)

    def valid(self, target: Mapping[str, Any]) -> None:  # pragma: no cover - each product
        raise NotImplementedError

    def dispatch(self, row: Mapping[str, Any], seam: Optional[Seam] = None) -> Outcome:
        """switch -> status -> create under the acli lock; create only when status names the frozen account."""
        from .jira_provider import _ACLI_LOCK, _is_unauthenticated, _parse_acli_auth_status

        seam = _need(seam)
        account = json.loads(row["account_json"] or "{}")
        target = json.loads(row["target_json"] or "{}")
        site, email = str(account.get("site") or ""), str(account.get("email") or "")
        with _ACLI_LOCK:
            prefix = ("acli", self.product, "auth")
            step =self._step(_guard((*prefix, "switch", "--site", site, "--email", email), self.manifest), seam)
            if isinstance(step, Outcome):
                return step
            code, out, err = step
            if code != 0:
                reason = ("atlassian_not_logged_in" if _is_unauthenticated(out + "\n" + err)
                          else "atlassian_switch_failed")
                return Outcome("failed", reason, detail=redact(err or out))
            step = self._step(_guard((*prefix, "status"), self.manifest), seam)
            if isinstance(step, Outcome):
                return step
            code, out, err = step
            if code != 0 or not _parse_acli_auth_status(out + "\n" + err, site, email).get("match"):
                return Outcome("failed", "atlassian_identity_unverified", detail=redact(err or out))
            return self._dispatch_one(lambda path: self.plan(target, path), row, seam, target)

    def _step(self, argv: tuple[str, ...], seam: Seam) -> Any:
        """A switch or status child BEFORE create: any failure is a known non-delivery (create never ran)."""
        from ..kernel.subprocess_exec import SubprocessOutcomeIndeterminate

        op = GatedOperation.subprocess(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                       errors="replace", timeout=15.0)
        try:
            return _native(_run(self.manifest, op, seam))
        except SubprocessOutcomeIndeterminate:
            return Outcome("failed", "atlassian_switch_failed")
        except ConnectorOperationRefused as exc:
            return Outcome("failed", "subprocess_refused", detail=redact(exc.reason))
        except OSError:
            return Outcome("failed", f"{self.name}_cli_missing")


class JiraChannel(_Atlassian):
    """A comment on ONE Jira work item, in plain text."""

    name = "jira"
    product = "jira"
    manifest = WriteConnectorManifest(
        connector_id="channel_jira", permission="shell:exec", label="Jira comment (Send)",
        description="acli jira auth switch/status and workitem comment create with --body-file only.",
        allowed_argv_prefixes=(("acli", "jira", "auth", "switch"), ("acli", "jira", "auth", "status"),
                               ("acli", "jira", "workitem", "comment", "create")),
    )
    PINNED = (("unauthorized", "atlassian_unauthorized"), ("can't be edited", "jira_cannot_be_edited"),
              ("cannot be edited", "jira_cannot_be_edited"), ("does not exist", "jira_not_found"),
              ("not found", "jira_not_found"))

    @staticmethod
    def key(value: Any) -> str:
        text = str(value or "").strip()
        if "," in text or any(ch.isspace() for ch in text):
            raise ChannelRefused("jira_key_not_single", "A Jira destination names exactly one work item", status=400)
        if not _JIRA_KEY.fullmatch(text):
            raise ValidationError("A Jira destination needs one work item key, like ABC-123", code="jira_key_invalid")
        return text

    def target_at_save(self, args: Mapping[str, Any], principal: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        return self.target_account(args), {"key": self.key(args.get("key"))}

    def valid(self, target: Mapping[str, Any]) -> None:
        try:
            self.key(target.get("key"))
        except ValidationError as exc:
            raise ChannelRefused("destination_changed", "The frozen Jira key is not valid") from exc

    def plan(self, target: Mapping[str, Any], path: str) -> GatedOperation:
        key = self.key(target.get("key"))
        argv = _guard(("acli", "jira", "workitem", "comment", "create", "--key", key, "--body-file", path, "--json"),
                      self.manifest)
        return GatedOperation.subprocess(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                         errors="replace", timeout=CREATE_TIMEOUT)

    def proof(self, stdout: str, target: Mapping[str, Any]) -> Optional[dict[str, Any]]:
        found = _json_id(stdout)
        return {**found, "key": str(target.get("key") or "")} if found else None


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "br", "pre"} and self.parts:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("- ")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def storage_xhtml(markdown: str) -> str:
    """The Markdown body in Confluence storage format: headings, bullet lists, paragraphs, all escaped."""
    out: list[str] = []
    para: list[str] = []
    in_list = False

    def flush() -> None:
        if para:
            out.append("<p>" + html.escape(" ".join(para)) + "</p>")
            para.clear()

    for line in markdown.splitlines():
        stripped = line.strip()
        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        bullet = re.match(r"^[-*+]\s+(.*)$", stripped)
        if bullet:
            flush()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + html.escape(bullet.group(1)) + "</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if not stripped:
            flush()
        elif heading:
            flush()
            level = len(heading.group(1))
            out.append(f"<h{level}>" + html.escape(heading.group(2)) + f"</h{level}>")
        else:
            para.append(stripped)
    flush()
    if in_list:
        out.append("</ul>")
    return "".join(out)


class ConfluenceChannel(_Atlassian):
    """A blog post in the saved space (Q3): the title and the body in the one private JSON file."""

    name = "confluence"
    product = "confluence"
    suffix = ".json"
    manifest = WriteConnectorManifest(
        connector_id="channel_confluence", permission="shell:exec", label="Confluence blog post (Send)",
        description="acli confluence auth switch/status and blog create with --from-json only.",
        allowed_argv_prefixes=(("acli", "confluence", "auth", "switch"), ("acli", "confluence", "auth", "status"),
                               ("acli", "confluence", "blog", "create")),
    )
    PINNED = (("unauthorized", "atlassian_unauthorized"), ("space not found", "confluence_space_not_found"),
              ("permission", "confluence_permission_denied"))

    def serialize(self, document: Document) -> bytes:
        """The transport request: ``{title, body: {representation: storage, value}}`` (field names UNVERIFIED)."""
        request = {"title": document.title, "status": "current",
                   "body": {"representation": "storage", "value": storage_xhtml(document.body_md)}}
        return json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def preview(self, payload: bytes) -> dict[str, Any]:
        """The title and the body as text, derived from the frozen bytes (never raw JSON or XHTML)."""
        try:
            request = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return {"title": "", "text": ""}
        parser = _Text()
        parser.feed(str(((request.get("body") or {}).get("value")) or ""))
        return {"title": str(request.get("title") or ""), "text": "".join(parser.parts).strip()}

    def target_at_save(self, args: Mapping[str, Any], principal: Any) -> tuple[dict[str, Any], dict[str, Any]]:
        space = str(args.get("space_id") or "").strip()
        if not _SPACE_ID.fullmatch(space):
            raise ValidationError("A Confluence destination needs the space id (digits)", code="confluence_space_invalid")
        return self.target_account(args), {"space_id": space}

    def valid(self, target: Mapping[str, Any]) -> None:
        if not _SPACE_ID.fullmatch(str(target.get("space_id") or "")):
            raise ChannelRefused("destination_changed", "The frozen Confluence space is not valid")

    def plan(self, target: Mapping[str, Any], path: str) -> GatedOperation:
        space = str(target.get("space_id") or "")
        if not _SPACE_ID.fullmatch(space):
            raise ValueError("confluence_space_invalid")
        argv = _guard(("acli", "confluence", "blog", "create", "--space-id", space, "--from-json", path, "--json"),
                      self.manifest)
        return GatedOperation.subprocess(argv, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                                         errors="replace", timeout=CREATE_TIMEOUT)


def _need(seam: Optional[Seam]) -> Seam:
    if seam is None:
        raise RuntimeError("a CLI channel dispatches only as a child of an admitted send")
    return seam


CLI_CHANNELS: dict[str, CliChannel] = {
    "github": GitHubChannel(), "jira": JiraChannel(), "confluence": ConfluenceChannel(),
}

from .channel_contract import CHANNELS  # noqa: E402

CHANNELS.update(CLI_CHANNELS)
