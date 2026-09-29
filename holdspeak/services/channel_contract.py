"""PHILO-10-01: the Send contract's parts (``design/send-lifecycle.md``).

* :class:`Document` -- ``{ref, title, body_md}`` from a renderer the document
  kind owns; the project update's renderer is the first (:func:`render_update`).
* The byte contract (section 3; round five): at prepare a channel serializes its
  transport request -- the exact bytes the far side receives -- and those bytes
  are frozen with their sha256. The readable preview is derived FROM them;
  dispatch writes or transmits those same bytes; the digest is checked again
  just before dispatch (``payload_changed``).
* :class:`Outcome` -- sent (proof), failed (a KNOWN non-delivery on the
  channel's pinned list), unknown (HoldSpeak cannot know). A refusal before the
  boundary is a :class:`ChannelRefused` and moves nothing.
* :func:`private_payload_file` -- the 0600 file in a 0700 directory a CLI
  channel reads its body from (argv carries only paths; story 02 is its first
  user), its digest checked just before the command runs.
* :data:`CHANNELS` -- the registry: a dict. The file channel is the one direct
  writer (the write manifest has no file kind, ``plugins/gated_connector.py``);
  the CLI channels (GitHub, Jira, Confluence) join it as a
  ``WriteConnectorManifest`` + ``plan`` + ``interpret`` each
  (``channel_cli.py``, PHILO-10-02). No framework, no discovery.
"""
from __future__ import annotations

import errno
import hashlib
import os
import re
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator, Mapping, Optional

from .errors import NotFound, ServiceError, ValidationError

#: Size limits, refused by name before dispatch (section 3): ``payload_too_large:<channel>``.
#: ``(limit, unit)``: GitHub and Jira count characters (the services' published
#: limits; PROVISIONAL until the real-account leg pins them), the rest bytes.
SIZE_LIMITS: dict[str, tuple[int, str]] = {
    "file": (10 * 1024 * 1024, "bytes"),
    "github": (65_536, "characters"),
    "jira": (32_767, "characters"),
    "confluence": (1_000_000, "bytes"),
}
#: An error text that reaches a receipt, a log or the face is cut to this many characters.
ERROR_LIMIT = 240


def payload_size(channel: str, payload: bytes) -> tuple[int, int, str]:
    """``(size, limit, unit)`` of *payload* for *channel* (limit 0: no limit)."""
    limit, unit = SIZE_LIMITS.get(channel, (0, "bytes"))
    size = len(payload.decode("utf-8", errors="replace")) if unit == "characters" else len(payload)
    return size, limit, unit


class ChannelRefused(ServiceError):
    """A named refusal BEFORE the dispatch boundary: nothing ran; the row does not move."""

    def __init__(self, code: str, detail: str, *, status: int = 409, **context: Any) -> None:
        super().__init__(code, detail, context={"status": status, **context})


@dataclass(frozen=True)
class Document:
    """A rendered document: what a channel serializes. ``ref`` is ``<kind>:<id>``."""

    ref: str
    title: str
    body_md: str
    #: What a channel names a file by (the project update's project and revision).
    slug: str = "document"
    revision: int = 1


@dataclass(frozen=True)
class Outcome:
    """A settled send. ``reason`` is a FIXED, named code (GATE 1): it is chosen
    from the raw native answer by the channel's pinned list and is never passed
    through :func:`redact`, so the diagnosis survives when the text is redacted.
    ``detail`` is the only free text, and it is always redacted."""

    state: str  # sent | failed | unknown
    reason: Optional[str] = None
    proof: Mapping[str, Any] = field(default_factory=dict)
    detail: Optional[str] = None

    def kernel_end(self) -> tuple[str, str]:
        """The kernel's terminal state and receipt outcome: the kernel state follows the row."""
        if self.state == "sent":
            return "succeeded", "succeeded"
        if self.state == "failed":
            return "failed", str(self.reason or "failed")
        return "indeterminate", str(self.reason or "unknown")

    def record(self) -> Optional[dict[str, Any]]:
        """What the row keeps as ``proof_json``: the proof, or the redacted detail of a failure."""
        if self.proof:
            return dict(self.proof)
        return {"error": self.detail} if self.detail else None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


#: A run of this many characters shared with the payload is an excerpt of it.
EXCERPT_MIN = 10
#: GATE 1 (Codex Astra r2 on #692): the most payload the excerpt scan reads.
#: Every CLI channel's own limit is below it (GitHub 65,536 characters, Jira
#: 32,767, Confluence 1 MB), so a CLI payload is always scanned whole. A larger
#: payload (only the file channel, whose errors are fixed OS codes) is not
#: scanned: its error text is withheld whole -- fail closed, never a leak.
REDACT_SCAN_LIMIT = 1024 * 1024
#: Secret shapes a CLI may echo (tokens, keys, bearer headers, key=value pairs).
_SECRET = re.compile(
    r"(?i)(bearer\s+\S+|(?:token|password|passwd|secret|api[_-]?key|authorization)\s*[=:]\s*(?:bearer\s+)?\S+"
    r"|gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}|xox[abprs]-[A-Za-z0-9-]{10,}"
    r"|SG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}|ATATT[A-Za-z0-9_=-]{16,})")
REDACTED = "[redacted]"


def redact(text: Any, payload: bytes = b"", secrets: Any = ()) -> str:
    """An error for a receipt, a log or the face: no payload text, no secret, at most 240 characters.

    Any run of ``EXCERPT_MIN`` or more characters that also occurs in the
    payload is replaced (an excerpt, not only a whole line); each known
    secret value and each secret-shaped token is replaced too.

    The cost is bounded (GATE 1): the text is cut to ``ERROR_LIMIT`` BEFORE
    the scan (at most 231 windows, each one C-speed ``in`` over at most
    ``REDACT_SCAN_LIMIT`` of payload); a payload over that limit withholds the
    text whole. A named code (``Outcome.reason``, a refusal code) never passes
    through here, so a redaction never erases the diagnosis.
    """
    raw = " ".join(" ".join(str(text or "").split())[:ERROR_LIMIT].split())
    for value in secrets or ():
        if value and len(str(value)) >= 4:
            raw = raw.replace(str(value), REDACTED)
    raw = _SECRET.sub(REDACTED, raw)
    if payload and len(payload) > REDACT_SCAN_LIMIT:
        return REDACTED if raw else ""
    body = " ".join(payload.decode("utf-8", errors="replace").split()) if payload else ""
    if body and len(raw) >= EXCERPT_MIN:
        covered = [False] * len(raw)
        seen: dict[str, bool] = {}
        for i in range(len(raw) - EXCERPT_MIN + 1):
            window = raw[i:i + EXCERPT_MIN]
            found = seen.get(window)
            if found is None:
                found = seen[window] = window in body
            if found:
                for j in range(i, i + EXCERPT_MIN):
                    covered[j] = True
        out: list[str] = []
        for i, ch in enumerate(raw):
            if not covered[i]:
                out.append(ch)
            elif i == 0 or not covered[i - 1]:
                out.append(REDACTED)
        raw = "".join(out)
    return raw[:ERROR_LIMIT]


@contextmanager
def private_payload_file(payload: bytes, digest: str, *, suffix: str = ".txt") -> Iterator[str]:
    """The payload in a 0600 file (exclusive create) inside a 0700 directory the hub makes.

    Its sha256 is compared with *digest* just before the caller runs its
    command (``payload_changed``, nothing runs). Deleted after the command ends.
    """
    directory = tempfile.mkdtemp(prefix="holdspeak-send-")
    os.chmod(directory, 0o700)
    path = os.path.join(directory, "payload" + suffix)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        with open(path, "rb") as handle:
            if sha256(handle.read()) != digest:
                raise ChannelRefused("payload_changed", "The payload file does not match the frozen digest")
        yield path
    finally:
        shutil.rmtree(directory, ignore_errors=True)


# ── the project update's renderer (the first document kind) ───────────────


def _slug(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", str(name or "").lower())
    return "-".join(words)[:60].strip("-") or "project"


def render_update(db: Any, update_id: str) -> Document:
    """``project_update:<id>`` -> its Document: a PUBLISHED update, its exact Markdown."""
    row = db.project_updates.get_update(str(update_id or ""))
    if row is None:
        raise NotFound("update", str(update_id or ""))
    if str(row.get("lifecycle") or "") != "published":
        raise ChannelRefused("update_not_published",
                             f"Update {update_id} is {row.get('lifecycle')}; only a published update can be sent",
                             status=400)
    with db._connection() as conn:
        project = conn.execute("SELECT name FROM projects WHERE id=?", (row["project_id"],)).fetchone()
    name = str(project["name"] if project is not None else row["project_id"])
    published = str(row.get("published_at") or "")[:10]
    title = f"{name} — update r{row.get('draft_revision') or 1}" + (f" ({published})" if published else "")
    return Document(ref=f"project_update:{row['id']}", title=title, body_md=str(row.get("body_md") or ""),
                    slug=_slug(name), revision=int(row.get("draft_revision") or 1))


def naming(db: Any, document_ref: str) -> Document:
    """What a file is named by (slug, revision) for a frozen document; its bytes stay the frozen ones."""
    kind, _, ident = str(document_ref or "").partition(":")
    if kind != "project_update" or not ident:
        raise ValidationError(f"Unknown document: {document_ref}", code="document_unknown")
    with db._connection() as conn:
        row = conn.execute("SELECT u.draft_revision, p.name FROM project_updates u LEFT JOIN projects p"
                           " ON p.id=u.project_id WHERE u.id=?", (ident,)).fetchone()
    if row is None:
        raise NotFound("update", ident)
    return Document(ref=str(document_ref), title="", body_md="", slug=_slug(row["name"] or ""),
                    revision=int(row["draft_revision"] or 1))


# ── the file channel: the one direct writer ────────────────────────────────


class FileChannel:
    """A new file per send in a saved folder (Q4): exclusive create, never over an old file.

    SENT: create, write, fsync, close, and the bytes read back match the
    digest (proof: absolute path + sha256 + size). FAILED only when the OS
    refuses the create before any byte (the pinned list: ``EACCES``,
    ``ENOSPC``, ``EEXIST``). Every other error, a partial file or bytes that
    do not read back: UNKNOWN.
    """

    name = "file"
    #: The pinned known non-delivery list: the create refused before any byte.
    FAILED_ON_CREATE = {errno.EACCES: "permission_denied", errno.ENOSPC: "no_space", errno.EEXIST: "name_taken"}

    # -- save --------------------------------------------------------------

    def target_at_save(self, folder: Any) -> dict[str, Any]:
        text = str(folder or "").strip()
        if not text or not os.path.isabs(os.path.expanduser(text)):
            raise ValidationError("A folder destination needs an absolute folder path", code="folder_not_absolute")
        real = os.path.realpath(os.path.expanduser(text))
        if not os.path.isdir(real):
            raise ValidationError(f"No folder at {real}", code="folder_missing")
        return {"folder": real}

    @staticmethod
    def badge(synced: bool) -> str:
        return "cloud" if synced else "local"

    # -- the bytes ---------------------------------------------------------

    @staticmethod
    def serialize(document: Document) -> bytes:
        """The file bytes: the document's exact Markdown, UTF-8."""
        return document.body_md.encode("utf-8")

    @staticmethod
    def preview(payload: bytes) -> dict[str, Any]:
        """The readable preview, derived from the frozen bytes."""
        return {"text": payload.decode("utf-8", errors="replace")}

    # -- before the boundary -------------------------------------------------

    def check_before_dispatch(self, target: Mapping[str, Any], **_: Any) -> str:
        """The folder resolved again: a different resolved path is ``destination_changed``."""
        frozen = str(target.get("folder") or "")
        real = os.path.realpath(frozen)
        if real != frozen or not os.path.isdir(real):
            raise ChannelRefused("destination_changed", f"The folder no longer resolves to {frozen}")
        return real

    def choose_path(self, folder: str, document: Document, send_id: str) -> str:
        """``<YYYY-MM-DD>-<slug>-r<revision>-<8 hex of the send id>.md``; ``-2``, ``-3`` ... when taken."""
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stem = f"{day}-{document.slug}-r{document.revision}-{send_id.split('_')[-1][:8]}"
        for index in range(1, 100):
            name = stem + ("" if index == 1 else f"-{index}") + ".md"
            path = self.inside(folder, name)
            if not os.path.lexists(path):
                return path
        raise ChannelRefused("name_exhausted", "Every file name for this send is taken")

    @staticmethod
    def inside(folder: str, name: str) -> str:
        """The path of *name* in *folder*; a name that leaves the folder is refused."""
        path = os.path.normpath(os.path.join(folder, name))
        if os.path.dirname(path) != os.path.normpath(folder) or os.path.basename(path) != name:
            raise ChannelRefused("path_outside_folder", "The file name leaves the saved folder")
        return path

    # -- the effect (after the boundary committed) ------------------------------

    def dispatch(self, row: Mapping[str, Any], seam: Any = None) -> Outcome:
        path, payload, digest = str(row["file_path"]), bytes(row["payload"]), str(row["payload_digest"])
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags, 0o644)
        except OSError as exc:
            if exc.errno in self.FAILED_ON_CREATE:
                return Outcome("failed", self.FAILED_ON_CREATE[exc.errno])
            return Outcome("unknown", f"create_{errno.errorcode.get(exc.errno or 0, 'error').lower()}")
        try:
            try:
                view = memoryview(payload)
                while view:
                    written = os.write(fd, view)
                    view = view[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError as exc:
            return Outcome("unknown", f"write_{errno.errorcode.get(exc.errno or 0, 'error').lower()}")
        return self.read_back(path, digest)

    @staticmethod
    def read_back(path: str, digest: str) -> Outcome:
        try:
            with open(path, "rb") as handle:
                data = handle.read()
        except FileNotFoundError:
            return Outcome("unknown", "missing_after_write")
        except OSError:
            return Outcome("unknown", "read_back_failed")
        found = sha256(data)
        if found != digest:
            return Outcome("unknown", "read_back_mismatch")
        return Outcome("sent", None, {"path": os.path.abspath(path), "sha256": found, "size": len(data)})

    def recover(self, row: Mapping[str, Any]) -> Outcome:
        """A ``dispatching`` row found by a take-over: NEVER dispatch again (section 4 table)."""
        path = str(row.get("file_path") or "")
        if not path or not os.path.lexists(path):
            return Outcome("failed", "not_written")
        return self.read_back(path, str(row["payload_digest"]))


#: THE registry: channel name -> its implementation. Story 02 adds the CLI
#: channels (``channel_cli.py``); story 03 adds email.
CHANNELS: dict[str, Any] = {"file": FileChannel()}

# The CLI channels register themselves at the end of their module (either import order works).
from . import channel_cli  # noqa: E402,F401


def channel(name: str) -> Any:
    found = CHANNELS.get(str(name or ""))
    if found is None:
        raise ValidationError(f"Unknown channel: {name}", code="channel_unknown")
    return found
