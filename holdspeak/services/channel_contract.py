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
from typing import Any, Iterator, Mapping, Optional, Protocol

from ..home_paths import home_display
from .errors import NotFound, ServiceError, ValidationError

#: Size limits, refused by name before dispatch (section 3): ``payload_too_large:<channel>``.
#: ``(limit, unit)``: GitHub and Jira count characters (the services' published
#: limits; PROVISIONAL until the real-account leg pins them), the rest bytes.
SIZE_LIMITS: dict[str, tuple[int, str]] = {
    "file": (10 * 1024 * 1024, "bytes"),
    "github": (65_536, "characters"),
    "jira": (32_767, "characters"),
    "confluence": (1_000_000, "bytes"),
    # Slack's incoming webhook body is one exact text message.  Refuse before
    # the dispatch boundary; never truncate, split, or upload a second body.
    "slack": (39_000, "characters"),
}
#: An error text that reaches a receipt, a log or the face is cut to this many characters.
ERROR_LIMIT = 240


def payload_size(channel: str, payload: bytes) -> tuple[int, int, str]:
    """``(size, limit, unit)`` of *payload* for *channel* (limit 0: no limit)."""
    limit, unit = SIZE_LIMITS.get(channel, (0, "bytes"))
    if channel == "slack":
        # Slack's limit applies to the text value, while the frozen payload is
        # the complete JSON request body.  Count the real producer's field so
        # receipts and refusal metadata describe the same value the transport
        # will post.
        import json

        try:
            data = json.loads(bytes(payload).decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            data = {}
        size = len(data.get("text", "")) if isinstance(data, dict) else 0
    else:
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
    #: What a channel names a file by (a source-owned safe slug).
    slug: str = "document"
    #: A short source-owned label frozen into a prepared send's provenance.
    label: str = "DOCUMENT"


class DocumentSource(Protocol):
    """One stored document kind in the explicit Phase 11 registry."""

    kind: str

    def render(self, db: Any, source_id: str) -> Document:
        """Read one stored source by id and render its Markdown document."""


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


#: The model drafter's mark on a claim with no evidence (UPD-002).
_UNVERIFIED_MARK = re.compile(r"\*\*\[UNVERIFIED\]\*\*[ \t]*")


def claim_verified(claim: Mapping[str, Any]) -> bool:
    """PHILO-15 B64 ruling: a claim counts as verified only when it has
    evidence refs or the owner reviewed it. Astra r1 (P1-3): the CURRENT
    review wins over every historical flag: an accepted claim is verified even
    when the model once marked it ``verified: false``; a rejected one is not.
    An inference the owner did not review is not verified, whatever it cites."""
    acceptance = str(claim.get("acceptance") or "")
    if acceptance == "accepted":
        return True
    if acceptance in ("rejected", "superseded"):
        return False
    record = claim.get("support_record") or {}
    if (claim.get("support") == "supported" and isinstance(record, Mapping)
            and record.get("method") == "reviewer" and not record.get("invalidated_at")):
        return True
    if claim.get("verified") is False:
        return False
    if str(claim.get("kind") or "") == "inference":
        return False
    return bool(claim.get("refs"))


#: Astra r2: the desk mark in any styling (bold, italic, code, bare).
_ANY_MARK = re.compile(r"\[\s*UNVERIFIED\s*\]", re.IGNORECASE)
_LEAD = re.compile(r"^(?:\s*(?:#{1,6}\s+|>\s*|[-*+]\s+|\d+[.)]\s+))+")
_EMPHASIS = re.compile(r"\*\*|__|~~|`|\*|(?<!\w)_|_(?!\w)")


def _normalized(text: str) -> str:
    """A line's words with every formatting removed (Astra r2): heading,
    quote and list markers, markdown emphasis, the desk mark in any styling,
    and spacing. Formatting never makes a sentence new, and never reviews it."""
    out = _EMPHASIS.sub("", str(text))
    out = _ANY_MARK.sub("", out)
    out = _LEAD.sub("", out)
    out = _EMPHASIS.sub("", out)
    return " ".join(out.split()).strip()


def has_desk_mark(line: str) -> bool:
    """The producer's ``[UNVERIFIED]`` mark, bold or not."""
    return bool(_ANY_MARK.search(_EMPHASIS.sub("", str(line))))


def _sentence(line: str) -> str:
    """A body line as a claim's words, formatting removed (Astra r1 P1-1, r2)."""
    return _normalized(line)


def _claim_lines(claim: Mapping[str, Any]) -> list[str]:
    return [t for t in (_normalized(part) for part in str(claim.get("text") or "").split("\n")) if t]


#: The drafter's own section headings: the only headings sent as structure.
def _section_headings() -> frozenset[str]:
    from .project_update_service import _SECTION_HEADINGS

    return frozenset(f"## {h}" for h in _SECTION_HEADINGS.values())


def stored_claims(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    """A stored update's claims on the three axes (legacy rows mapped)."""
    import json

    from .project_update_service import migrate_claims_json

    raw = migrate_claims_json(
        str(row.get("claims_json") or ""), generator=str(row.get("generator") or "deterministic"),
    )
    try:
        claims = json.loads(raw or "[]")
    except (TypeError, ValueError):
        return []
    return [c for c in claims if isinstance(c, dict)] if isinstance(claims, list) else []


def _outbound(body_md: str, claims: Any = None) -> tuple[list[list[str]], int]:
    """The body's sections (heading line first) with every unchecked claim
    omitted WHOLE, and the count omitted.

    ``claims`` given (a list, even empty): PHILO-15 B64 and Astra r1 P1-1:
    the CLAIMS SET decides. A line is sent only when its words are a verified
    claim's words (any line of a multi-line claim); a line whose words belong
    to no verified claim is omitted whatever its formatting (bullet, plain
    paragraph, desk mark). The drafter's "nothing here" sentences are kept.
    ``claims`` None (a legacy caller with no claim record): the desk mark
    alone decides, as before."""
    from .project_update_service import _HONEST_MINIMAL

    sections: list[list[str]] = [[]]
    dropped_in: list[int] = [0]
    dropped = 0
    skipping = False
    use_claims = claims is not None
    verified: set[str] = set()
    firsts: set[str] = set()
    tails: set[str] = set()
    if use_claims:
        for claim in claims or ():
            if not isinstance(claim, Mapping):
                continue
            lines = _claim_lines(claim)
            if claim_verified(claim):
                verified.update(lines)
            elif lines:
                firsts.add(lines[0])
                tails.update(lines[1:])
    neutral = _EMPTY_WORDS | {str(v).strip() for v in _HONEST_MINIMAL.values()}
    headings = _section_headings()
    for line in str(body_md or "").splitlines():
        stripped = line.strip()
        if use_claims and line.startswith("#") and stripped not in headings:
            # Astra r2: a heading that is not one of the drafter's own section
            # headings is a sentence like any other (below).
            pass
        elif line.startswith("#"):
            skipping = False
            if line.startswith("## "):
                sections.append([line])
                dropped_in.append(0)
            else:
                sections[-1].append(line)
            continue
        if use_claims:
            words = _sentence(line)
            # The desk mark still says "not checked" for words no verified
            # claim carries (the review, never the formatting, clears it).
            held = words in firsts or words in tails or has_desk_mark(line)
            if not words or words in verified or (words in neutral and not held):
                skipping = False
                # A desk mark never leaves the desk (the owner's review won).
                sections[-1].append(_ANY_MARK.sub("", _UNVERIFIED_MARK.sub("", line)))
                continue
            # Omitted. A tail line of the claim omitted just above is not
            # counted again.
            if not (skipping and words in tails and words not in firsts):
                dropped += 1
                dropped_in[-1] += 1
            skipping = True
            continue
        if _UNVERIFIED_MARK.search(line):
            if not skipping or stripped.startswith(("- ", "* ")):
                dropped += 1
                dropped_in[-1] += 1
            skipping = True
        elif skipping and stripped and not stripped.startswith(("- ", "* ")):
            continue  # the rest of the omitted claim
        else:
            skipping = False
            sections[-1].append(line)
    out: list[list[str]] = []
    for lines, cut in zip(sections, dropped_in):
        if cut and not any(ln.strip() for ln in lines[1:]):
            lines = [lines[0], "", "Not checked.", ""] if lines else ["Not checked.", ""]
        out.append(lines)
    return out, dropped


def without_desk_marks(body_md: str, heading: str = "", claims: Any = None) -> str:
    """An update's Markdown as it leaves the desk (Send, Copy), PHILO-15 B53
    and Astra's rulings: a claim the model could not tie to evidence (the
    ``[UNVERIFIED]`` mark) is OMITTED whole, continuation lines included,
    never sent as a fact; a section left empty by that reads "Not checked.";
    the last line counts what stayed on the desk. ``heading`` (the
    document's identity) leads when given."""
    sections, dropped = _outbound(body_md, claims)
    text = "\n".join(line for lines in sections for line in lines).rstrip("\n") + "\n"
    if dropped:
        text += f"\n{dropped} claim{'' if dropped == 1 else 's'} not checked, kept on the desk.\n"
    if heading:
        text = f"# {heading}\n\n" + text
    return text


#: The sentences that say a section has nothing (the drafter's honest
#: minimums, and the omission's own word): not substantive content.
_EMPTY_WORDS = frozenset({"Not checked."})


def nothing_verified(body_md: str, claims: Any = None) -> bool:
    """True when the update must not leave the desk: NOTHING VERIFIED.

    ``claims`` given (PHILO-15 B64, Astra r1 P1-1): decided on the CLAIMS
    SET: no claim record is verified (a draft with no claims at all
    included), or no verified claim's words are in the body. ``claims``
    None (legacy): omitting the marked claims leaves no substantive content.
    Source Coverage is never content."""
    from .project_update_service import _HONEST_MINIMAL

    sections, dropped = _outbound(body_md, claims)
    if claims is not None:
        verified = {
            line for c in claims if isinstance(c, Mapping) and claim_verified(c)
            for line in _claim_lines(c)
        }
        sent = {_sentence(line) for lines in sections for line in lines}
        # Zero verified claims (none at all included), or none left in the body.
        return not (verified & sent)
    if not dropped:
        return False
    empty = _EMPTY_WORDS | {str(v).strip() for v in _HONEST_MINIMAL.values()}
    for lines in sections:
        if lines and lines[0].strip().lower() == "## source coverage":
            continue
        for line in lines[1 if lines and lines[0].startswith("## ") else 0:]:
            text = line.strip()
            if text and not text.startswith("#") and _sentence(text) not in empty:
                return False
    return True


def render_update(db: Any, update_id: str) -> Document:
    """``project_update:<id>`` -> its Document: a PUBLISHED update, its exact Markdown."""
    row = db.project_updates.get_update(str(update_id or ""))
    if row is None:
        raise NotFound("update", str(update_id or ""))
    if str(row.get("lifecycle") or "") != "published":
        raise ChannelRefused("not_published",
                             f"Update {update_id} is {row.get('lifecycle')}; only a published update can be sent",
                             status=400)
    with db._connection() as conn:
        project = conn.execute("SELECT name FROM projects WHERE id=?", (row["project_id"],)).fetchone()
    name = str(project["name"] if project is not None else row["project_id"])
    published = str(row.get("published_at") or "")[:10]
    title = f"{name} — update r{row.get('draft_revision') or 1}" + (f" ({published})" if published else "")
    revision = int(row.get("draft_revision") or 1)
    # PHILO-15 B53: an unchecked claim never leaves the desk as a fact (the
    # face keeps it, with its UNVERIFIED lamp).
    # The document names itself (PHILO-15 B53 ruling): "<Project> · Update · <date>".
    heading = f"{name} · Update" + (f" · {published}" if published else "")
    raw = str(row.get("body_md") or "")
    # PHILO-15 B64: verified means evidence refs or the owner's review; an
    # unreviewed inference stays on the desk like an unverified claim.
    claims = stored_claims(row)
    if nothing_verified(raw, claims):
        # Astra r2 ruling: an update whose every claim stays on the desk is not
        # sent (its stored claims are kept; the owner checks them first).
        raise ChannelRefused("nothing_verified",
                             "NOTHING VERIFIED: every claim in this update is not checked; it stays on the desk",
                             status=400)
    body = without_desk_marks(raw, heading, claims)
    return Document(ref=f"project_update:{row['id']}", title=title, body_md=body,
                    slug=_slug(name), label=f"REV {revision}")


def _document_parts(document_ref: str) -> tuple[str, str]:
    kind, separator, source_id = str(document_ref or "").partition(":")
    if not separator or not kind or not source_id:
        raise ChannelRefused("document_kind_unknown", f"Unknown document kind: {document_ref}", status=400)
    return kind, source_id


def render_document(db: Any, document_ref: str) -> Document:
    """Render one declared document source by its ``<kind>:<id>`` reference.

    The registry is deliberately imported at call time.  The source module
    uses :class:`Document` and the project-update renderer, so a top-level
    import would make the two small contract modules depend on each other's
    initialization order.
    """
    from .document_sources import render_document as resolve_source

    try:
        document = resolve_source(db, document_ref)
    except ChannelRefused:
        raise
    except NotFound:
        raise ChannelRefused("document_not_found", f"Document {document_ref} was not found", status=404) from None
    if not isinstance(document, Document):
        raise TypeError(f"document source returned {type(document).__name__}, expected Document")
    return document


def frozen_document_json(document: Document) -> str:
    """Serialize only the three provenance fields required by the design."""
    import json

    return json.dumps({"title": document.title, "slug": document.slug, "label": document.label},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def document_from_json(document_ref: str, value: Any) -> Document:
    """Rebuild a naming document from a prepared row's frozen provenance."""
    import json

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            value = {}
    if not isinstance(value, Mapping):
        value = {}
    return Document(ref=str(document_ref), title=str(value.get("title") or ""), body_md="",
                    slug=str(value.get("slug") or "document"), label=str(value.get("label") or "DOCUMENT"))


def naming(db: Any, document_ref: str, document_json: Any = None) -> Document:
    """Return frozen file naming data, with a legacy-row fallback.

    New rows pass ``document_json`` captured at prepare or at the inline
    boundary.  A pre-Phase-11 row has no column value, so its historical
    update naming is resolved as a compatibility fallback only.
    """
    if document_json:
        return document_from_json(document_ref, document_json)
    kind, source_id = _document_parts(document_ref)
    # Legacy Phase 10 rows have no provenance column.  Preserve their old
    # naming lookup exactly: it read the update and project name, but did not
    # require the update to remain published and did not read its body.
    if kind == "project_update":
        with db._connection() as conn:
            row = conn.execute("SELECT u.draft_revision, p.name FROM project_updates u LEFT JOIN projects p"
                               " ON p.id=u.project_id WHERE u.id=?", (source_id,)).fetchone()
        if row is None:
            raise ChannelRefused("document_not_found", f"Document {document_ref} was not found", status=404)
        revision = int(row["draft_revision"] or 1)
        return Document(ref=str(document_ref), title="", body_md="", slug=_slug(row["name"] or ""),
                        label=f"r{revision}")
    raise ChannelRefused("document_not_found", f"Document {document_ref} was not found", status=404)


# ── the built-in folder (owner ruling 2026-10-05) ───────────────────────────

#: A folder the user browses: rwxr-xr-x, the same reach as the 0644 files in it.
BUILTIN_FOLDER_MODE = 0o755


def documents_dir(platform: Optional[str] = None) -> str:
    """The user's Documents folder, read now (never frozen).

    Linux: ``XDG_DOCUMENTS_DIR`` from ``$XDG_CONFIG_HOME/user-dirs.dirs`` (what
    ``xdg-user-dir DOCUMENTS`` reads), then the environment variable, then
    ``~/Documents``. A value of ``$HOME`` itself means "no Documents folder"
    in the XDG convention, so it falls back too. Every other platform:
    ``~/Documents``.
    """
    from pathlib import Path

    home = str(Path.home())
    fallback = os.path.join(home, "Documents")
    if not str(platform or PLATFORM).startswith("linux"):
        return fallback

    config = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    found, written = "", False
    try:
        with open(os.path.join(config, "user-dirs.dirs"), encoding="utf-8") as handle:
            for line in handle:
                key, _, value = line.strip().partition("=")
                if key == "XDG_DOCUMENTS_DIR":
                    written, found = True, decode_user_dir(value, home)
    except OSError:
        pass
    if written and not found:
        return fallback  # a value that cannot be decoded: never a wrong literal path
    if not found:
        env = os.environ.get("XDG_DOCUMENTS_DIR", "")  # the shell already expanded it: a literal path
        found = os.path.normpath(env) if os.path.isabs(env) else ""
    if not found or os.path.normpath(found) == os.path.normpath(home):
        return fallback
    return found


def decode_user_dir(raw: str, home: str) -> str:
    """One ``user-dirs.dirs`` value, decoded as ``xdg-user-dirs`` writes it; "" when it cannot be.

    The format is a shell assignment: a double-quoted value, ``$HOME`` only at
    its start (then ``/`` or the end), and the backslash escapes ``\\$``,
    ``\\"``, ``\\\\`` and ``\\``` for those literal characters. Any other
    backslash, an unescaped ``$``, backquote or quote inside, or a value that
    is not absolute is not decoded.
    """
    text = raw.strip()
    if len(text) < 2 or text[0] != '"' or text[-1] != '"':
        return ""
    body, out, i = text[1:-1], [], 0
    if body.startswith("$HOME") and (len(body) == 5 or body[5] == "/"):
        out.append(home)
        i = 5
    while i < len(body):
        ch = body[i]
        if ch == "\\":
            if i + 1 < len(body) and body[i + 1] in '$"\\`':
                out.append(body[i + 1])
                i += 2
                continue
            return ""
        if ch in '$`"':
            return ""
        out.append(ch)
        i += 1
    path = "".join(out)
    return os.path.normpath(path) if os.path.isabs(path) else ""


def builtin_folder(platform: Optional[str] = None) -> str:
    """The built-in destination's folder: Documents + HoldSpeak/Sent, resolved now."""
    return os.path.realpath(os.path.join(documents_dir(platform), "HoldSpeak", "Sent"))


#: The platform the Documents resolver and the iCloud detector read (a seam: a fence sets "darwin" or "linux").
PLATFORM = __import__("sys").platform

#: The xattr macOS puts on a folder that a File Provider (iCloud Drive) manages.
_FILE_PROVIDER_XATTR = "com.apple.file-provider-domain-id"


def _read_xattr(path: str, name: str) -> Optional[bytes]:
    """One extended attribute of *path* (macOS ``getxattr(2)`` through libc), or None.

    The OS-call boundary of the iCloud detector: the fences replace this
    function, never the real ~/Documents.
    """
    import ctypes
    import ctypes.util

    try:
        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
        getxattr = libc.getxattr
        getxattr.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_size_t,
                             ctypes.c_uint32, ctypes.c_int]
        getxattr.restype = ctypes.c_ssize_t
        raw_path, raw_name = os.fsencode(path), name.encode()
        size = getxattr(raw_path, raw_name, None, 0, 0, 0)
        if size <= 0:
            return None
        buf = ctypes.create_string_buffer(size)
        got = getxattr(raw_path, raw_name, buf, size, 0, 0)
        return buf.raw[:got] if got > 0 else None
    except (OSError, AttributeError, TypeError):
        return None


def _finder_pref(key: str) -> bool:
    """A Finder preference (``FXICloudDriveDocuments`` / ``FXICloudDriveDesktop``) read from its plist; False when unknown."""
    import plistlib
    from pathlib import Path

    try:
        with open(Path.home() / "Library" / "Preferences" / "com.apple.finder.plist", "rb") as handle:
            prefs = plistlib.load(handle)
    except (OSError, ValueError, plistlib.InvalidFileException):
        return False
    return bool(prefs.get(key)) if isinstance(prefs, dict) else False


#: A File Provider domain id (the xattr's value, or a ~/Library/CloudStorage
#: folder name) -> the provider the face names. Any other provider: "synced".
_PROVIDERS: tuple[tuple[str, str], ...] = (
    ("com.apple.clouddocs", "icloud"),
    ("com.getdropbox", "dropbox"),
    ("dropbox", "dropbox"),
    ("com.google.drivefs", "googledrive"),
    ("googledrive", "googledrive"),
    ("com.microsoft.onedrive", "onedrive"),
    ("onedrive", "onedrive"),
)


def _provider_of(marker: str) -> str:
    text = marker.lower()
    for prefix, provider in _PROVIDERS:
        if text.startswith(prefix):
            return provider
    return "synced"


def sync_provider(folder: str, platform: Optional[str] = None) -> Optional[str]:
    """Which sync service takes *folder* off this device, or None (macOS only; read now, it can change).

    "Not iCloud" never means "this device": any File Provider counts. Every
    path is resolved first (a symlinked Documents is judged where it really
    is). In order:

    1. Inside the resolved ``~/Library/Mobile Documents``: ``icloud``.
    2. Inside the resolved ``~/Library/CloudStorage/<name>`` (where Dropbox,
       Google Drive and OneDrive keep File Provider folders): the provider
       named by ``<name>``.
    3. The nearest existing folder of the resolved path, or any folder above it
       up to the filesystem root, carries ``com.apple.file-provider-domain-id``:
       the provider its value names.
    4. Finder's "Desktop & Documents Folders" switch for a resolved path under
       the resolved ~/Documents (``FXICloudDriveDocuments``) or ~/Desktop
       (``FXICloudDriveDesktop``): ``icloud``.

    Recognised providers: ``icloud``, ``dropbox``, ``googledrive``,
    ``onedrive``; any other: ``synced``. Linux and every other platform:
    None (THIS DEVICE).
    """
    if not str(platform or PLATFORM).startswith("darwin"):
        return None
    home = os.path.expanduser("~")
    path = os.path.realpath(folder)

    def under(base: str) -> bool:
        return path == base or path.startswith(base.rstrip(os.sep) + os.sep)

    if under(os.path.realpath(os.path.join(home, "Library", "Mobile Documents"))):
        return "icloud"
    storage = os.path.realpath(os.path.join(home, "Library", "CloudStorage"))
    if under(storage):
        rest = path[len(storage):].lstrip(os.sep)
        return _provider_of(rest.split(os.sep, 1)[0]) if rest else "synced"
    probe = path
    while not os.path.exists(probe) and os.path.dirname(probe) != probe:
        probe = os.path.dirname(probe)
    while True:
        value = _read_xattr(probe, _FILE_PROVIDER_XATTR)
        if value is not None:
            return _provider_of(value.decode("utf-8", errors="replace"))
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    for top, key in (("Documents", "FXICloudDriveDocuments"), ("Desktop", "FXICloudDriveDesktop")):
        if under(os.path.realpath(os.path.join(home, top))):
            return "icloud" if _finder_pref(key) else None
    return None


def icloud_synced(folder: str, platform: Optional[str] = None) -> bool:
    """Whether iCloud Drive (and not another provider) syncs *folder*."""
    return sync_provider(folder, platform) == "icloud"


def egress_at_boundary(target: Mapping[str, Any], folder: Optional[str]) -> Optional[str]:
    """The send's egress, judged ONCE at the dispatch boundary and stored on its row.

    The built-in folder: the sync service that takes the file off this device
    (``sync_provider``), or None. Every other destination: None (a saved
    folder carries its own ``synced`` flag).
    """
    if folder and is_builtin_target(target):
        return sync_provider(folder)
    return None


def builtin_egress() -> Optional[str]:
    """The built-in folder's egress, read now: its sync provider, or None (this device)."""
    return sync_provider(builtin_folder())


def is_builtin_target(target: Mapping[str, Any]) -> bool:
    return bool(target.get("builtin"))


def shown_target(target: Mapping[str, Any]) -> dict[str, Any]:
    """A target as the face reads it: the built-in's folder is resolved now;
    every folder carries its short token (`display`), so no face prints the
    full home path of a saved folder."""
    shown = dict(target)
    if is_builtin_target(target):
        folder = builtin_folder()
        shown["folder"] = folder
        shown["display"] = home_display(folder)
        cloud = builtin_egress()
        if cloud:
            shown["cloud"] = cloud
    elif isinstance(target.get("folder"), str) and target.get("folder"):
        shown["display"] = home_display(str(target["folder"]))
    return shown


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
        """The folder resolved again: a different resolved path is ``destination_changed``.

        The built-in folder is resolved HERE, at send time (it may not exist
        yet: dispatch makes it).
        """
        if is_builtin_target(target):
            return builtin_folder()
        frozen = str(target.get("folder") or "")
        real = os.path.realpath(frozen)
        if real != frozen or not os.path.isdir(real):
            raise ChannelRefused("destination_changed", f"The folder no longer resolves to {frozen}")
        return real

    def choose_path(self, folder: str, document: Document, send_id: str) -> str:
        """``<date>-<slug>-<label>-<8 hex of send id>.md``; suffix when taken."""
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        stem = f"{day}-{_slug(document.slug)}-{_slug(document.label)}-{send_id.split('_')[-1][:8]}"
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
        if is_builtin_target(_target_of(row)):
            # The built-in folder only: made on the first send, made again when it
            # was deleted. A SAVED folder is never made (it may be an unmounted drive).
            try:
                os.makedirs(os.path.dirname(path), mode=BUILTIN_FOLDER_MODE, exist_ok=True)
            except OSError:
                return Outcome("failed", "folder_not_created")
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


def _target_of(row: Mapping[str, Any]) -> dict[str, Any]:
    import json

    try:
        value = json.loads(row.get("target_json") or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


#: THE registry: channel name -> its implementation. Story 02 adds the CLI
#: channels (``channel_cli.py``); story 03 adds email.
CHANNELS: dict[str, Any] = {"file": FileChannel()}

# The CLI channels register themselves at the end of their module (either import order works).
from . import channel_cli  # noqa: E402,F401

# The Slack channel is another explicit registry row.  Keep this import at
# the end: channel_slack imports the contract types and registers its one
# implementation after they have been defined.
from . import channel_slack  # noqa: E402,F401


def channel(name: str) -> Any:
    found = CHANNELS.get(str(name or ""))
    if found is None:
        raise ValidationError(f"Unknown channel: {name}", code="channel_unknown")
    return found


def serialize_for(destination: Mapping[str, Any], document: Document) -> bytes:
    """The exact transport bytes of *document* for *destination* (the one byte contract).

    PHILO-10-03: an ``addressed`` channel (email) serializes per destination:
    its bytes name the frozen sender and recipients. Every other channel's
    bytes are the document's alone.
    """
    chan = channel(destination["channel"])
    if getattr(chan, "addressed", False):
        return chan.serialize(document, destination)
    return chan.serialize(document)


def preview_for(channel_name: str, payload: bytes, account_json: Any = None) -> dict[str, Any]:
    """The readable preview, derived from the frozen bytes (an addressed channel reads its account's provider)."""
    import json

    chan = channel(channel_name)
    if getattr(chan, "addressed", False):
        return chan.preview(payload, json.loads(account_json or "{}"))
    return chan.preview(payload)
