"""The Walk: a guided feedback walk on the desk from one link (2026-11-07).

The orchestrator writes a short JSON script (open, verb, highlight, ask).
The owner opens one link; the desk runs the script and he answers each ask.
A walk is one folder under the feedback folder (``ui_feedback.walks_root``):
``walk.json`` holds the script, the token's hash and the answers; each
answer's window shot is a PNG beside it, written by the feedback writer
with the feedback size limits.

The token authorizes ONLY reading its own walk and posting its answers. It
creates no owner session. An unknown token reads nothing (one 404).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import tempfile
import threading
from pathlib import Path
from typing import Any, Mapping, Optional

from ..timestamps import utc_now_iso
from . import ui_feedback
from .errors import ServiceError

PAGE_PREFIX = "/w/"
WALK_FILE = "walk.json"
_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_REF_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_STEP_KEYS = frozenset({"open", "verb", "highlight", "ask"})
MAX_STEPS = 60
MAX_WORDS = 2000
SKIP = "skip"
# The storage bound of one walk (Codex review of #1808). The token routes are
# reachable over Tailscale, so repeated valid answers must not fill the disk:
# - one PNG per question: a later image of the same ref replaces the earlier
#   one (``<ref>.png``), and the refs are the script's asks, so a walk keeps at
#   most one image per step (MAX_STEPS = 60);
# - an earlier answer keeps its TEXT (choice, words, time) under ``earlier``,
#   at most MAX_EARLIER = 5 per question; older text drops off;
# - all the PNGs of one walk together stay within WALK_BYTES = 64 MiB; past it
#   an image is refused (``walk_shot_budget``) and the text answer still lands.
MAX_EARLIER = 5
WALK_BYTES = 64 * 1024 * 1024


class WalkRefused(ServiceError):
    def __init__(self, code: str, detail: str, *, status: int = 409) -> None:
        super().__init__(code, detail, context={"status": status})


def _gone() -> WalkRefused:
    return WalkRefused("walk_not_found", "This walk is not known.", status=404)


def _text(value: Any, name: str, maximum: int, *, required: bool = True) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str) or (required and not value.strip()) or len(value) > maximum:
        raise WalkRefused("walk_invalid", f"{name} must be text of at most {maximum} characters.", status=422)
    return value.strip()


def _step(raw: Any, index: int, refs: set[str]) -> dict[str, Any]:
    where = f"Step {index + 1}"
    if not isinstance(raw, dict) or not raw or set(raw) - _STEP_KEYS:
        raise WalkRefused("walk_invalid", f"{where} must hold only open, verb, highlight or ask.", status=422)
    step: dict[str, Any] = {}
    if "open" in raw:
        opened = raw["open"]
        if not isinstance(opened, dict):
            raise WalkRefused("walk_invalid", f"{where}: open must be an object.", status=422)
        step["open"] = {"app": _text(opened.get("app"), f"{where} open.app", 120)}
        scope = _text(opened.get("scope"), f"{where} open.scope", 240, required=False)
        if scope:
            step["open"]["scope"] = scope
    if "verb" in raw:
        verb = raw["verb"]
        if not isinstance(verb, dict):
            raise WalkRefused("walk_invalid", f"{where}: verb must be an object.", status=422)
        step["verb"] = {"verb": _text(verb.get("verb"), f"{where} verb.verb", 120)}
        window = _text(verb.get("window"), f"{where} verb.window", 120, required=False)
        if window:
            step["verb"]["window"] = window
    if "highlight" in raw:
        mark = raw["highlight"]
        if not isinstance(mark, dict):
            raise WalkRefused("walk_invalid", f"{where}: highlight must be an object.", status=422)
        step["highlight"] = {"target": _text(mark.get("target"), f"{where} highlight.target", 400),
                             "words": _text(mark.get("words"), f"{where} highlight.words", 240, required=False)}
        window = _text(mark.get("window"), f"{where} highlight.window", 120, required=False)
        if window:
            step["highlight"]["window"] = window
    if "ask" in raw:
        ask = raw["ask"]
        if not isinstance(ask, dict):
            raise WalkRefused("walk_invalid", f"{where}: ask must be an object.", status=422)
        ref = ask.get("ref")
        if not isinstance(ref, str) or not _REF_RE.fullmatch(ref) or ref in refs:
            raise WalkRefused("walk_invalid", f"{where}: ask.ref must be a new short name (letters, digits, - and _).",
                              status=422)
        refs.add(ref)
        choices = ask.get("choices")
        if not isinstance(choices, list) or not 1 <= len(choices) <= 6:
            raise WalkRefused("walk_invalid", f"{where}: ask.choices must be one to six words.", status=422)
        step["ask"] = {"ref": ref, "question": _text(ask.get("question"), f"{where} ask.question", 240),
                       "choices": [_text(choice, f"{where} choice", 40) for choice in choices]}
    return step


def validate_script(script: Any) -> dict[str, Any]:
    """The script, as stored: a title and one to sixty known steps."""
    if not isinstance(script, dict):
        raise WalkRefused("walk_invalid", "The walk must be a JSON object.", status=422)
    steps = script.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= MAX_STEPS:
        raise WalkRefused("walk_invalid", f"The walk must have one to {MAX_STEPS} steps.", status=422)
    refs: set[str] = set()
    return {"title": _text(script.get("title"), "title", 200),
            "steps": [_step(step, index, refs) for index, step in enumerate(steps)]}


def _stored(directory: Path, ref: str) -> int:
    """The bytes of the walk's PNGs, without ``<ref>.png`` (it is replaced)."""
    try:
        return sum(entry.stat().st_size for entry in directory.glob("*.png") if entry.name != f"{ref}.png")
    except OSError:
        return 0


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class WalkService:
    def __init__(self, home: Optional[Path] = None) -> None:
        self._home = home
        self._lock = threading.Lock()

    @property
    def root(self) -> Path:
        return ui_feedback.walks_root(self._home)

    # ── storage ────────────────────────────────────────────────────────

    def _write(self, directory: Path, record: Mapping[str, Any]) -> None:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        data = json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        fd, temporary = tempfile.mkstemp(prefix=".walk.", dir=str(directory))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, directory / WALK_FILE)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _load(self, walk_id: str) -> dict[str, Any]:
        if not isinstance(walk_id, str) or not _ID_RE.fullmatch(walk_id):
            raise _gone()
        try:
            return json.loads((self.root / walk_id / WALK_FILE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise _gone() from None

    def _by_token(self, token: Any) -> dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise _gone()
        digest = _hash(token)
        try:
            folders = [entry for entry in self.root.iterdir() if entry.is_dir() and _ID_RE.fullmatch(entry.name)]
        except OSError:
            raise _gone() from None
        for folder in folders:
            try:
                record = json.loads((folder / WALK_FILE).read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if secrets.compare_digest(str(record.get("token_sha256") or ""), digest):
                return record
        raise _gone()

    # ── the owner ──────────────────────────────────────────────────────

    def create(self, script: Any) -> dict[str, Any]:
        clean = validate_script(script)
        walk_id = secrets.token_hex(16)
        token = secrets.token_urlsafe(32)
        record = {"id": walk_id, "token_sha256": _hash(token), "created_at": utc_now_iso(),
                  **clean, "answers": {}}
        with self._lock:
            self._write(self.root / walk_id, record)
        return {"id": walk_id, "token": token, "url_path": f"{PAGE_PREFIX}{token}"}

    def read(self, walk_id: str) -> dict[str, Any]:
        """Everything, for the orchestrator: the script, the answers and the
        folder that holds the shots."""
        record = self._load(walk_id)
        record.pop("token_sha256", None)
        return {**record, "directory": str((self.root / walk_id).absolute())}

    # ── the token holder ───────────────────────────────────────────────

    def known(self, token: Any) -> bool:
        try:
            self._by_token(token)
            return True
        except WalkRefused:
            return False

    def page(self, token: Any) -> dict[str, Any]:
        record = self._by_token(token)
        return {"title": record["title"], "steps": record["steps"], "answers": record.get("answers") or {}}

    def answer(self, token: Any, ref: Any, choice: Any, *, words: Any = None,
               window_png: Any = None) -> dict[str, Any]:
        with self._lock:
            record = self._by_token(token)
            asks = {step["ask"]["ref"]: step["ask"] for step in record["steps"] if "ask" in step}
            ask = asks.get(ref) if isinstance(ref, str) else None
            if ask is None:
                raise WalkRefused("walk_unknown_ask", "This walk has no such question.", status=422)
            if not isinstance(choice, str) or (choice not in ask["choices"] and choice != SKIP):
                raise WalkRefused("walk_unknown_choice", "That choice is not on this question.", status=422)
            said = _text(words, "words", MAX_WORDS, required=False)
            answer: dict[str, Any] = {"choice": choice, "at": utc_now_iso()}
            if said:
                answer["words"] = said
            refused: Optional[dict[str, str]] = None
            if window_png:
                directory = self.root / record["id"]
                try:
                    answer["shot"] = ui_feedback.save_walk_shot(directory, ref, window_png,
                                                                room=WALK_BYTES - _stored(directory, ref))
                except ui_feedback.WalkShotBudgetError as exc:
                    refused = {"code": "walk_shot_budget", "detail": str(exc)}
                except ui_feedback.UIFeedbackError as exc:
                    raise WalkRefused("walk_shot_invalid", str(exc), status=422) from None
            answers = dict(record.get("answers") or {})
            previous = answers.get(ref)
            if previous:
                # A second answer keeps the first answer's text (the image is replaced).
                earlier = list(previous.pop("earlier", []) or [])
                kept = {key: value for key, value in previous.items() if key != "shot"}
                answer["earlier"] = [*earlier, kept][-MAX_EARLIER:]
            answers[ref] = answer
            record["answers"] = answers
            self._write(self.root / record["id"], record)
        receipt = {"ref": ref, **{key: value for key, value in answer.items() if key != "earlier"}}
        if refused:
            receipt["shot_refused"] = refused
        return receipt


_DEFAULT: Optional[WalkService] = None


def default_walk_service() -> WalkService:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = WalkService()
    return _DEFAULT


__all__ = ["MAX_EARLIER", "PAGE_PREFIX", "WALK_BYTES", "WalkRefused", "WalkService", "default_walk_service", "validate_script"]
