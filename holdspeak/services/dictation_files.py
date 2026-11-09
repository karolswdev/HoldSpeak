"""The dictation files and the teach seam, moved out of the web routes (2026-11-09).

Project-context resolution, the ``.hs`` project files, the blocks document, the
starter templates and the teach seam (the one server-side diff and refusal
vocabulary, HS-176-02). ``DictationService`` reads and writes through these;
``web/routes/dictation/_helpers.py`` re-exports them for the hand-written
speech routes (dry-run, remote, replay) that still call them.
"""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Optional


def _resolve_project_context(project_root: Optional[str] = None) -> dict[str, Any]:
    """Return detected/manual project context for dictation project APIs."""
    from ..plugins.dictation.project_root import detect_project_for_cwd

    if project_root is None or not str(project_root).strip():
        project = detect_project_for_cwd()
        if project is None:
            raise ValueError("no project detected for current working directory")
        return dict(project)

    root = Path(str(project_root)).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"project_root must be an existing directory: {root}")

    project = detect_project_for_cwd(root)
    if project is not None:
        return dict(project)
    return {"name": root.name, "root": str(root), "anchor": "manual"}


def _resolve_blocks_target(
    scope: str,
    project_root: Optional[str] = None,
) -> tuple[Path, Optional[dict[str, Any]]]:
    """Return `(path, project_ctx)` for the requested scope.

    Raises `ValueError` with a user-facing message on bad input.
    """
    from ..plugins.dictation.assembly import DEFAULT_GLOBAL_BLOCKS_PATH

    if scope == "global":
        return DEFAULT_GLOBAL_BLOCKS_PATH, None
    if scope == "project":
        project = _resolve_project_context(project_root)
        return Path(project["root"]) / ".holdspeak" / "blocks.yaml", dict(project)
    raise ValueError(f"scope must be 'global' or 'project', got {scope!r}")


# ── .hs project-context payload helpers ──────────────────────────────────


def _project_hs_payload(project: dict[str, Any]) -> dict[str, Any]:
    from ..agent_context import (
        DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
        HS_CONTEXT_FILES,
        load_hs_project_context,
    )

    root = Path(project["root"])
    hs_dir = root / ".hs"
    loaded = load_hs_project_context(
        root,
        max_bytes=DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES * 8,
        per_file_max_bytes=DEFAULT_CONTEXT_HARD_FILE_MAX_BYTES,
    )
    loaded_files = loaded.get("files") if isinstance(loaded.get("files"), dict) else {}
    files: dict[str, dict[str, Any]] = {}
    for name in (*HS_CONTEXT_FILES, "ignore"):
        path = hs_dir / name
        loaded_entry = loaded_files.get(name) if isinstance(loaded_files, dict) else None
        entry = loaded_entry if isinstance(loaded_entry, dict) else {}
        files[name] = {
            "path": str(path),
            "exists": path.is_file(),
            "actual_path": str(entry.get("path") or path),
            "content": str(entry.get("content") or ""),
            "source": str(entry.get("source") or "directory"),
            "read_only": bool(entry.get("read_only")),
            "truncated": bool(entry.get("truncated")),
        }
    return {
        "detected": dict(project),
        "context_dir": str(hs_dir),
        "exists": bool(loaded.get("exists")),
        "context_dir_exists": hs_dir.is_dir(),
        "files": files,
        "flat_files": loaded.get("flat_files") if isinstance(loaded.get("flat_files"), dict) else {},
        "skipped": loaded.get("skipped") if isinstance(loaded.get("skipped"), list) else [],
        "warnings": loaded.get("warnings") if isinstance(loaded.get("warnings"), list) else [],
        "write_policy": loaded.get("write_policy") if isinstance(loaded.get("write_policy"), dict) else {},
    }


def _write_project_hs_files(root: Path, files: dict[str, Any]) -> None:
    from ..agent_context import HS_CONTEXT_FILES

    allowed = set(HS_CONTEXT_FILES) | {"ignore"}
    unknown = sorted(set(files) - allowed)
    if unknown:
        raise ValueError(f"unknown .hs file(s): {unknown}; allowed: {sorted(allowed)}")
    hs_dir = root / ".hs"
    hs_dir.mkdir(parents=True, exist_ok=True)
    for name, raw_content in files.items():
        if not isinstance(raw_content, str):
            raise ValueError(f".hs/{name} content must be a string")
        if len(raw_content.encode("utf-8")) > 128_000:
            raise ValueError(f".hs/{name} is too large; max is 128KB")
        path = hs_dir / name
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(raw_content, encoding="utf-8")
        os.replace(tmp, path)


# ── blocks-document IO + starter templates ───────────────────────────────


def _read_blocks_document(path: Path) -> tuple[dict[str, Any], bool]:
    """Read `path` as a raw YAML mapping; return empty default if missing."""
    import yaml

    if not path.exists():
        return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, False
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    if data is None:
        return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, True
    if not isinstance(data, dict):
        raise ValueError(
            f"{path}: top-level YAML must be a mapping, got {type(data).__name__}"
        )
    data.setdefault("version", 1)
    data.setdefault("default_match_confidence", 0.6)
    data.setdefault("blocks", [])
    return data, True


_STARTER_BLOCK_TEMPLATES: tuple[dict[str, Any], ...] = (
    {
        # HS-47-03: a starter block that consumes a Project Fact, so a fact set
        # in the KB actually shows up in dictation out of the box (otherwise
        # facts have nothing referencing them). The {project.kb.stack}
        # placeholder is left unresolved -- and the injection skipped -- until
        # the user fills in the `stack` fact, so it is safe by default.
        "id": "project_facts_context",
        "title": "Project facts context",
        "description": "Append your project's stack fact to AI-assistant prompts so the copilot always has it. Set the `stack` fact in Project Facts to see it appear.",
        "sample_utterance": "help me refactor the payments module",
        "requires_project": True,
        "block": {
            "id": "project_facts_context",
            "description": "User is dictating a prompt for an AI assistant and wants the project's facts attached.",
            "match": {
                "examples": [
                    "help me refactor the payments module",
                    "write a test for this endpoint",
                    "explain how this service is wired together",
                ],
                "negative_examples": ["remind me to buy milk"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "append",
                "template": "\n\nProject stack: {project.kb.stack}",
            },
        },
    },
    {
        "id": "ai_prompt_context",
        "title": "AI prompt context",
        "description": "Append the selected project name and clear instruction context to AI-assistant prompts.",
        "sample_utterance": "help me design the settings panel",
        "requires_project": True,
        "block": {
            "id": "ai_prompt_context",
            "description": "User is dictating a prompt for an AI assistant and wants project context attached.",
            "match": {
                "examples": [
                    "Claude help me write a function for this project",
                    "build a prompt for the settings panel",
                    "ask the assistant to debug this module",
                ],
                "negative_examples": ["remind me to buy milk"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "append",
                "template": "\n\nProject: {project.name}\nUse the selected project's constraints and local context when answering.",
            },
        },
    },
    {
        "id": "action_item",
        "title": "Action item",
        "description": "Turn short task dictation into a consistent action-item line.",
        "sample_utterance": "follow up with Sam about the launch checklist",
        "requires_project": False,
        "block": {
            "id": "action_item",
            "description": "User is capturing a task or follow-up item.",
            "match": {
                "examples": [
                    "follow up with Sam about the launch checklist",
                    "remember to review the pull request",
                    "make a task to update the docs",
                ],
                "negative_examples": ["write a paragraph about the architecture"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "replace",
                "template": "Action item: {raw_text}",
            },
        },
    },
    {
        "id": "concise_note",
        "title": "Concise note",
        "description": "Format quick thoughts as a clean note that is easy to scan later.",
        "sample_utterance": "the retry worker should surface its next scheduled run",
        "requires_project": False,
        "block": {
            "id": "concise_note",
            "description": "User is dictating a concise note or implementation observation.",
            "match": {
                "examples": [
                    "note that the retry worker needs a status line",
                    "capture this implementation idea",
                    "write down this design concern",
                ],
                "negative_examples": ["send an email to Alex"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "replace",
                "template": "Note: {raw_text}",
            },
        },
    },
    {
        "id": "code_review_focus",
        "title": "Code review focus",
        "description": "Append a review rubric for correctness, edge cases, and tests.",
        "sample_utterance": "review the queue processing change",
        "requires_project": False,
        "block": {
            "id": "code_review_focus",
            "description": "User is dictating a code-review request.",
            "match": {
                "examples": [
                    "review the queue processing change",
                    "look over this implementation for bugs",
                    "check this diff for edge cases",
                ],
                "negative_examples": ["start a meeting recording"],
                "threshold": 0.7,
            },
            "inject": {
                "mode": "append",
                "template": "\n\nReview focus: correctness, edge cases, regressions, and missing tests.",
            },
        },
    },
)

_STARTER_PROJECT_KB: dict[str, Any] = {
    "stack": None,
    "task_focus": None,
    "constraints": None,
}


def _starter_template(template_id: str) -> Optional[dict[str, Any]]:
    for template in _STARTER_BLOCK_TEMPLATES:
        if template["id"] == template_id:
            return deepcopy(template)
    return None


def _unique_block_id(base_id: str, document: dict[str, Any]) -> str:
    existing = {
        b.get("id")
        for b in document.get("blocks", [])
        if isinstance(b, dict)
    }
    if base_id not in existing:
        return base_id
    index = 2
    while f"{base_id}_{index}" in existing:
        index += 1
    return f"{base_id}_{index}"


def _block_summary(path: Path) -> dict[str, Any]:
    from ..plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "valid": True,
            "count": 0,
            "error": None,
        }
    try:
        loaded = load_blocks_yaml(path)
    except BlockConfigError as exc:
        return {
            "path": str(path),
            "exists": True,
            "valid": False,
            "count": 0,
            "error": str(exc),
        }
    return {
        "path": str(path),
        "exists": True,
        "valid": True,
        "count": len(loaded.blocks),
        "error": None,
    }


# ── HS-176-02: the teach seam (the ONE server-side diff + refusal vocabulary) ──
#
# The `text` correction kind teaches from a pair: what the mic HEARD (the raw
# transcript, now served on the run response beside `final_text`) and what the
# owner SAID (his edit). The word-level diff runs HERE, on the server, so both
# teach routes — `POST /api/dictation/corrections` and
# `POST /api/dictation/journal/{entry_id}/correct` — produce identical rules.
#
# The ruled outcomes (assets/settled-design-speak-loop.md D2(a), rulings R1/N3):
#   * no difference                          -> nothing stored, reason `no_change`
#   * exactly one contiguous differing span,
#     at most half the heard tokens          -> a WORD rule (key = the heard
#                                               span, value = the said span)
#   * more than one span, or a span over
#     half the tokens                        -> a WHOLE-PHRASE rule (key = the
#                                               full heard text, value = the
#                                               full said text)
#
# N3: `Utterance.raw_text` is post-TextProcessor on the capture path, so spoken
# punctuation is already attached to the token (`postgress,`). Every stored span
# is therefore stripped of leading/trailing punctuation before it is stored, and
# the key is stored lowercased (matching is case-insensitive; the store's own
# matcher is case-preserving on the first letter).

#: Named refusal reasons on the teach wire. The face turns these into
#: `REFUSED · SECRET` / `REFUSED · ONE WORD` / `NO CHANGE` (R4, R7, R8).
TEACH_NO_CHANGE = "no_change"
TEACH_EMPTY = "empty"
TEACH_SECRET = "secret"
TEACH_ONE_WORD = "one_word"
TEACH_REFUSED = "refused"

#: Leading/trailing characters stripped from a stored span (N3).
_TEACH_PUNCTUATION = "\"'`.,;:!?()[]{}<>…-–—*_/\\"


def _strip_span(span: str) -> str:
    """One whitespace-collapsed line, stripped of leading/trailing punctuation."""
    return " ".join(str(span or "").split()).strip(_TEACH_PUNCTUATION).strip()


def diff_text_correction(heard: str, said: str) -> dict[str, Any]:
    """The ruled word-level diff of `heard` vs `said`.

    Returns ``{"rule": {"key", "value", "shape"}, "reason": None}`` when
    something should be stored, or ``{"rule": None, "reason": "<token>"}`` when
    nothing should be — `no_change` when the two texts agree, `empty` when a
    side is blank. `shape` is ``"word"`` or ``"phrase"`` (diagnostic only; the
    stored kind is `text` either way).
    """
    from difflib import SequenceMatcher

    heard_norm = " ".join(str(heard or "").split())
    said_norm = " ".join(str(said or "").split())
    if not heard_norm or not said_norm:
        return {"rule": None, "reason": TEACH_EMPTY}
    if heard_norm == said_norm:
        return {"rule": None, "reason": TEACH_NO_CHANGE}

    heard_tokens = heard_norm.split()
    said_tokens = said_norm.split()
    spans = [
        op
        for op in SequenceMatcher(
            a=heard_tokens, b=said_tokens, autojunk=False
        ).get_opcodes()
        if op[0] != "equal"
    ]

    key_raw = ""
    value = ""
    shape = "phrase"
    if len(spans) == 1:
        _tag, i1, i2, j1, j2 = spans[0]
        heard_span = " ".join(heard_tokens[i1:i2])
        said_span = " ".join(said_tokens[j1:j2])
        # A pure insertion has no heard span and a pure deletion no said span —
        # neither can be keyed as a word rule. A span over half the heard tokens
        # is the sentence, not a word.
        if heard_span and said_span and (i2 - i1) * 2 <= len(heard_tokens):
            key_raw = _strip_span(heard_span)
            value = _strip_span(said_span)
            shape = "word"
    if shape != "word" or not key_raw or not value:
        key_raw = _strip_span(heard_norm)
        value = _strip_span(said_norm)
        shape = "phrase"

    if not key_raw or not value:
        return {"rule": None, "reason": TEACH_EMPTY}
    if key_raw == value:
        # Only whitespace or edge punctuation differed: the rule would be a
        # no-op, so nothing is written and the receipt says so.
        return {"rule": None, "reason": TEACH_NO_CHANGE}
    return {"rule": {"key": key_raw.lower(), "value": value, "shape": shape}, "reason": None}


def teach_refusal_reason(kind: str, key: str, value: str) -> str:
    """The named reason `CorrectionStore.record` refused a teach (R4/R7).

    `CorrectionStore.record` names its own refusal (`kind` / `empty` / `secret` /
    `one_word`) and `record_correction` passes that through verbatim — the ONE
    vocabulary. This is the fallback for a store that predates that contract:
    the same guards, mirrored, so the wire can still NAME the refusal instead of
    smoothing it (Article V.3). `refused` when no guard explains the no-op.
    """
    from ..project_doc_suggestions import looks_like_secret

    clean_key = " ".join(str(key or "").split())
    clean_value = str(value or "").strip()
    if not clean_key or not clean_value:
        return TEACH_EMPTY
    try:
        if looks_like_secret(clean_key) or looks_like_secret(clean_value):
            return TEACH_SECRET
    except Exception:  # pragma: no cover - the secret check must never raise here
        pass
    # The one-word refusal binds the ROUTING kinds only: a `text` rule is
    # exact-phrase, so a single token is legal and precise (R7).
    if kind in ("intent", "target") and len(clean_key.split()) < 2:
        return TEACH_ONE_WORD
    return TEACH_REFUSED


def _newest_correction_id(store: Any) -> Optional[int]:
    """The durable id of the newest stored correction, or None."""
    try:
        items = store.list_for_display()
    except Exception:  # pragma: no cover - the id linkage is best-effort
        return None
    if items and items[0].get("id") is not None:
        try:
            return int(items[0]["id"])
        except (TypeError, ValueError):
            return None
    return None


def record_correction(
    store: Any, kind: str, key: str, value: str
) -> tuple[bool, Optional[int], Optional[str]]:
    """Teach one correction; return ``(recorded, stored id, refusal reason)``.

    R4: the id and the refusal's NAME both come from `CorrectionStore.record`,
    which returns a `RecordOutcome` (`stored` / `correction_id` / `refusal`).
    No more guessing the id from `list_for_display()[0]` — on a refusal that was
    somebody else's rule entirely.

    The older return shapes are still honoured so a bare/older store cannot
    500 the route: a plain `bool` reads the id back from the durable list and
    ONLY when the record was accepted (which is itself the R4 fix), and the
    refusal is then re-derived from the store's own guards.
    """
    outcome = store.record(kind, key, value)
    stored = getattr(outcome, "stored", None)
    if stored is not None:  # the HS-176-02 `RecordOutcome`
        if not bool(stored):
            reason = getattr(outcome, "refusal", None)
            return False, None, str(reason) if reason else TEACH_REFUSED
        correction_id = getattr(outcome, "correction_id", None)
        return True, (int(correction_id) if correction_id is not None else None), None
    if not bool(outcome):
        return False, None, teach_refusal_reason(kind, key, value)
    return True, _newest_correction_id(store), None


def _teach(
    store: Any,
    kind: str,
    *,
    key: Optional[str] = None,
    value: Optional[str] = None,
    heard: Optional[str] = None,
    said: Optional[str] = None,
) -> dict[str, Any]:
    """Run the ruled teach for one correction kind. Writes AT MOST one row.

    HS-176-02 (R4). The ONE place both teach routes go through, so the refusal
    vocabulary and the stored-id linkage cannot drift between them. A refusal
    writes nothing and carries a named `reason`; an acceptance carries the
    stored row's `id`, `kind`, `key` and `value`.
    """
    if kind == "text":
        outcome = diff_text_correction(heard or "", said or "")
        rule = outcome["rule"]
        if rule is None:
            # `no_change` (heard == said) and `empty` write NOTHING — no
            # correction row, no `taught_from` flag, no id linkage.
            return {
                "recorded": False,
                "id": None,
                "kind": kind,
                "key": None,
                "value": None,
                "reason": str(outcome["reason"]),
            }
        key = str(rule["key"])
        value = str(rule["value"])

    clean_key = " ".join(str(key or "").split())
    clean_value = str(value or "").strip()
    recorded, correction_id, refusal = record_correction(
        store, kind, clean_key, clean_value
    )
    if not recorded:
        return {
            "recorded": False,
            "id": None,
            "kind": kind,
            "key": None,
            "value": None,
            # The store names its own refusal (`secret` / `one_word` / …); the
            # mirror only covers a store that predates that contract.
            "reason": refusal or teach_refusal_reason(kind, clean_key, clean_value),
        }
    return {
        "recorded": True,
        "id": correction_id,
        "kind": kind,
        "key": clean_key,
        "value": clean_value,
        "reason": None,
    }
