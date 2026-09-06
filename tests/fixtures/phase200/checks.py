"""Deterministic invariant checks over the Phase 200 evaluation corpus.

HS-200-08.  The corpus (``corpus/episodes/*.json``) is versioned material.
This module is the *judge that never guesses*: every check here is a
deterministic function of an episode's material and one normalised output.
No model is consulted, and no check reads the clock or the network.

Two rules shape the design.

**Severity belongs to the check, not to the episode.**  ``CRITICAL_FAILURE_KINDS``
is a frozen set in this module, so a corpus file cannot downgrade a critical
factual failure to a soft one.  Phase 200 ACCEPTANCE: "Any unresolved critical
defect blocks its gate regardless of averages."

**Held-out episodes are not tuning material.**  ``read_for_tuning`` raises
``HeldOutEpisodeError`` when a tuning step reaches for a held-out episode.  The
split is recorded in each episode file and was assigned when the episode was
written, before any prompt change measured against it.

The normalised output a runner hands to :func:`check_episode`::

    {
      "text": str,               # every assistant sentence, concatenated
      "questions": [str],        # questions the run asked back
      "fields": {                # structured values the product path produced
          "<name>": "<value>" | {"unknown": "<reason>"} | None
      },
      "claims": [                # C2 axes, as project_update_service spells them
          {"span_id": str, "text": str, "refs": [str],
           "kind": str, "support": str, "acceptance": str,
           "support_record": {"method": str, ...} | None,
           "unknowns": [{"type": str, "value": str}]}
      ],
      "decisions": [             # extracted or recalled decisions
          {"id": str, "text": str, "state": str, "current": bool}
      ],
      "error": str | None,
      "latency_ms": float,
    }

Every key is optional; a missing key reads as empty.  ``None`` and the string
``"unknown"`` both count as a typed unknown, as does ``{"unknown": reason}`` --
the meeting plugins emit ``None`` with a ``gap`` for an unstated owner or due
date, and the update service emits ``unknowns`` entries.

The literal scanners below deliberately *mirror* the update service's own
regexes instead of importing them: this module judges that service's output,
so it must not inherit its definition of a date or a number.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

# ── Corpus location and versions ──────────────────────────────────────

CORPUS_ROOT = Path(__file__).resolve().parent / "corpus"
EPISODES_DIR = CORPUS_ROOT / "episodes"
MANIFEST_PATH = CORPUS_ROOT / "manifest.json"

#: The schema this module reads and the driver writes.
CORPUS_VERSION = "1"

#: Episode categories, in report order.
CATEGORIES: tuple[str, ...] = ("interview", "meeting", "update")

SPLIT_TRAIN = "train"
SPLIT_HELD_OUT = "held_out"
SPLITS: tuple[str, ...] = (SPLIT_TRAIN, SPLIT_HELD_OUT)

# ── Failure kinds ─────────────────────────────────────────────────────

# A critical factual failure: an invented value, a violated correction, a
# restated stale decision, or an irrelevant citation sold as support.  It
# fails its episode whatever else passed, and it cannot be averaged away.
FAILURE_SUPERSEDED_RESTATED = "superseded_value_restated"
FAILURE_INVENTED_VALUE = "invented_value"
FAILURE_INVENTED_UNCERTAIN = "invented_uncertain_value"
FAILURE_STALE_DECISION = "restated_stale_decision"
FAILURE_CITATION_SUPPORTED = "irrelevant_citation_supported"

# Soft failures: real quality defects that do not invent a fact.
FAILURE_CORRECTION_ABSENT = "correction_absent"
FAILURE_QUESTION_REPEATED = "question_repeated"
FAILURE_MISSING_UNKNOWN = "missing_typed_unknown"
FAILURE_MISSING_SUPERSESSION = "missing_supersession"
FAILURE_CLAIM_MISSING = "claim_missing"
FAILURE_RUN_ERROR = "run_error"

CRITICAL_FAILURE_KINDS: frozenset[str] = frozenset({
    FAILURE_SUPERSEDED_RESTATED,
    FAILURE_INVENTED_VALUE,
    FAILURE_INVENTED_UNCERTAIN,
    FAILURE_STALE_DECISION,
    FAILURE_CITATION_SUPPORTED,
})

#: Support states that are *not* an assertion of checked fact (C2).
UNSUPPORTED_STATES: frozenset[str] = frozenset({"unknown", "source_linked", "disputed"})

#: The only two methods that may raise a claim to `supported` (C2).
SUPPORT_METHODS: frozenset[str] = frozenset({"field_mapping", "reviewer"})

#: Lexical evidence that a run declared a value unknown rather than filling it.
UNKNOWN_PHRASES: tuple[str, ...] = (
    "unknown",
    "not recorded",
    "not stated",
    "not available",
    "not specified",
    "no source",
    "not in the material",
    "cannot say",
    "could not read",
    "unfilled",
    "no date",
    "no owner",
    "no decision",
    "coverage gap",
    "missing",
    "unavailable",
    "revoked",
)

# ── Literal scanners (mirrored, not imported -- see the module docstring) ──

_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_NUMBER_RE = re.compile(r"(?<![\w-])\d+(?:[.,]\d+)?%?(?![\w-])")

_LITERAL_SCANNERS: dict[str, re.Pattern[str]] = {
    "date": _DATE_RE,
    "number": _NUMBER_RE,
}

#: A field whose name says it holds a date gets date scanning for free.
_DATE_FIELD_RE = re.compile(r"(date|deadline|due|when)", re.IGNORECASE)


# ── Results ───────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class InvariantResult:
    """One invariant, judged."""

    kind: str
    field: str
    passed: bool
    failure_kind: str = ""
    detail: str = ""

    @property
    def critical(self) -> bool:
        return self.failure_kind in CRITICAL_FAILURE_KINDS

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "kind": self.kind,
            "field": self.field,
            "passed": self.passed,
        }
        if not self.passed:
            payload["failure_kind"] = self.failure_kind
            payload["critical"] = self.critical
            payload["detail"] = self.detail
        return payload


@dataclass(frozen=True, slots=True)
class EpisodeResult:
    """Every invariant of one episode, plus what the run cost."""

    episode_id: str
    category: str
    split: str
    material_sha256: str
    invariants: list[InvariantResult] = field(default_factory=list)
    latency_ms: float = 0.0
    error: str = ""

    @property
    def failures(self) -> list[InvariantResult]:
        return [row for row in self.invariants if not row.passed]

    @property
    def critical_failures(self) -> list[InvariantResult]:
        return [row for row in self.failures if row.critical]

    @property
    def passed(self) -> bool:
        """An episode passes only with no failure at all and no run error."""
        return not self.failures and not self.error

    @property
    def critical(self) -> bool:
        """A critical factual failure. No average can lift this."""
        return bool(self.critical_failures)

    def failure_kinds(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in self.failures:
            counts[row.failure_kind] = counts.get(row.failure_kind, 0) + 1
        if self.error:
            counts[FAILURE_RUN_ERROR] = counts.get(FAILURE_RUN_ERROR, 0) + 1
        return dict(sorted(counts.items()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "category": self.category,
            "split": self.split,
            "material_sha256": self.material_sha256,
            "passed": self.passed,
            "critical": self.critical,
            "latency_ms": round(self.latency_ms, 3),
            "error": self.error,
            "failure_kinds": self.failure_kinds(),
            "invariants": [row.to_dict() for row in self.invariants],
        }


# ── Corpus loading, hashing and the split rule ────────────────────────


#: Invariants that judge one named field and must declare it.
_FIELD_INVARIANTS: frozenset[str] = frozenset({
    "correction_honoured",
    "absent_source_unknown",
    "typed_unknown_field",
})


class CorpusError(RuntimeError):
    """A corpus file does not satisfy the schema."""


class HeldOutEpisodeError(RuntimeError):
    """A tuning step reached for a held-out acceptance episode."""


def canonical_json(payload: Any) -> str:
    """The one canonical encoding used for every hash in this harness."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def material_digest(episode: Mapping[str, Any]) -> str:
    """The episode's context identity: sha256 over its canonical material."""
    return hashlib.sha256(canonical_json(episode.get("material", {})).encode("utf-8")).hexdigest()


def validate_episode(episode: Mapping[str, Any], *, source: str = "") -> None:
    where = f" ({source})" if source else ""
    for key in ("id", "corpus_version", "category", "split", "title", "tags", "material", "invariants"):
        if key not in episode:
            raise CorpusError(f"episode missing {key!r}{where}")
    if episode["category"] not in CATEGORIES:
        raise CorpusError(f"unknown category {episode['category']!r}{where}")
    if episode["split"] not in SPLITS:
        raise CorpusError(f"unknown split {episode['split']!r}{where}")
    if not episode["invariants"]:
        raise CorpusError(f"episode {episode['id']} declares no invariant{where}")
    for invariant in episode["invariants"]:
        kind = invariant.get("kind", "")
        if kind not in CHECKS:
            raise CorpusError(f"episode {episode['id']} names unknown invariant {kind!r}{where}")
        if kind in _FIELD_INVARIANTS and "field" not in invariant.get("params", {}):
            raise CorpusError(f"episode {episode['id']} invariant {kind} has no field{where}")


def load_episode(path: Path) -> dict[str, Any]:
    episode = json.loads(Path(path).read_text())
    validate_episode(episode, source=str(path))
    return episode


def load_corpus(root: Path | None = None) -> list[dict[str, Any]]:
    """Every episode, id-sorted. Reads the episode files, not the manifest."""
    directory = Path(root or EPISODES_DIR)
    episodes = [load_episode(path) for path in sorted(directory.glob("*.json"))]
    ids = [episode["id"] for episode in episodes]
    duplicates = {value for value in ids if ids.count(value) > 1}
    if duplicates:
        raise CorpusError(f"duplicate episode ids: {sorted(duplicates)}")
    return sorted(episodes, key=lambda episode: episode["id"])


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    return json.loads(Path(path or MANIFEST_PATH).read_text())


def build_manifest(episodes: Sequence[Mapping[str, Any]], *, split_rule: str) -> dict[str, Any]:
    """The manifest is derived from the episode files; it never leads them."""
    rows = []
    for episode in episodes:
        rows.append({
            "id": episode["id"],
            "category": episode["category"],
            "split": episode["split"],
            "title": episode["title"],
            "tags": list(episode["tags"]),
            "invariants": [invariant["kind"] for invariant in episode["invariants"]],
            "material_sha256": material_digest(episode),
        })
    counts: dict[str, dict[str, int]] = {}
    for category in CATEGORIES:
        rows_in = [row for row in rows if row["category"] == category]
        counts[category] = {
            "total": len(rows_in),
            SPLIT_TRAIN: len([row for row in rows_in if row["split"] == SPLIT_TRAIN]),
            SPLIT_HELD_OUT: len([row for row in rows_in if row["split"] == SPLIT_HELD_OUT]),
        }
    return {
        "corpus_version": CORPUS_VERSION,
        "split_rule": split_rule,
        "episode_count": len(rows),
        "counts": counts,
        "held_out_ids": [row["id"] for row in rows if row["split"] == SPLIT_HELD_OUT],
        "episodes": rows,
    }


def tuning_episodes(episodes: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """The only episodes a prompt or recipe change may read."""
    return [dict(episode) for episode in episodes if episode.get("split") == SPLIT_TRAIN]


def assert_tunable(episode: Mapping[str, Any]) -> None:
    if episode.get("split") == SPLIT_HELD_OUT:
        raise HeldOutEpisodeError(
            f"episode {episode.get('id')} is held out: tuning may not read it. "
            "Held-out episodes are acceptance evidence and were separated before "
            "any prompt change."
        )


def read_for_tuning(episode: Mapping[str, Any]) -> dict[str, Any]:
    """The tuning-side door into an episode's material. Held-out episodes raise."""
    assert_tunable(episode)
    return dict(episode.get("material", {}))


# ── Output readers ────────────────────────────────────────────────────


def _text_of(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return " ".join(_text_of(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return " ".join(_text_of(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def haystack(output: Mapping[str, Any]) -> str:
    """Every sentence a reader would see, normalised for literal matching."""
    parts = [
        _text_of(output.get("text")),
        _text_of(output.get("questions")),
        _text_of([claim.get("text") for claim in output.get("claims") or []]),
        _text_of([decision.get("text") for decision in output.get("decisions") or []]),
        _text_of(output.get("fields")),
    ]
    return _normalize(" ".join(parts))


def material_haystack(episode: Mapping[str, Any]) -> str:
    return _normalize(_text_of(episode.get("material", {})))


def contains(hay: str, literal: str) -> bool:
    """Whole-token containment, case and whitespace insensitive."""
    needle = _normalize(literal)
    if not needle:
        return False
    pattern = re.escape(needle)
    if needle[0].isalnum():
        pattern = r"(?<![\w-])" + pattern
    if needle[-1].isalnum() or needle[-1] == "%":
        pattern = pattern + r"(?![\w-])"
    return re.search(pattern, hay) is not None


def field_value(output: Mapping[str, Any], name: str) -> Any:
    fields = output.get("fields") or {}
    return fields.get(name, _MISSING)


_MISSING = object()


def is_typed_unknown(value: Any) -> bool:
    """A typed unknown: an absent value the run marked absent on purpose."""
    if value is None:
        return True
    if isinstance(value, Mapping):
        return "unknown" in value or value.get("state") == "unknown"
    if isinstance(value, str):
        return _normalize(value) in {"unknown", "typed_unknown", ""}
    return False


def declares_unknown(output: Mapping[str, Any], name: str) -> bool:
    """Structured typed unknown, or a plain sentence saying so."""
    value = field_value(output, name)
    if value is not _MISSING and is_typed_unknown(value):
        return True
    # Plain substring: these are stems and phrases ("no decision" inside "no
    # decisions in this window"), which the whole-token rule would miss.  This
    # half of the check is lexical and advisory -- it can only ever produce the
    # soft `missing_typed_unknown`, never a critical failure.
    hay = haystack(output)
    return any(phrase in hay for phrase in UNKNOWN_PHRASES)


def invented_literals(output: Mapping[str, Any], episode: Mapping[str, Any], literal_type: str) -> list[str]:
    """Literals of a type in the output that the episode material never carried."""
    scanner = _LITERAL_SCANNERS.get(literal_type)
    if scanner is None:
        return []
    hay = haystack(output)
    material = material_haystack(episode)
    if literal_type == "number":
        # A year inside a date is not a free-standing number.
        hay = _DATE_RE.sub(" ", hay)
        material = _DATE_RE.sub(" ", material)
    found = []
    for literal in scanner.findall(hay):
        if not contains(material, literal) and literal not in found:
            found.append(literal)
    return found


# ── The six invariant checks ──────────────────────────────────────────

#: Words that mark a value as the OLD one rather than asserting it.
_SUPERSESSION_MARKERS: tuple[str, ...] = (
    "supersed", "replaced", "no longer", "previous", "previously", "earlier",
    "former", "was ", "not ", "instead of", "corrected", "correction",
    "outdated", "stale", "rather than", "up from", "down from",
    "moved", "changed", "revised", "from ",
)

#: How far before a literal a marker may sit and still be about it.
_MARKER_WINDOW = 60


def _marked_superseded(hay: str, literal: str) -> bool:
    """True when every mention of ``literal`` is marked as the superseded one.

    "The deadline moved from 2026-05-20 to 2026-06-15" is not a restatement of
    the old date; "the deadline is 2026-05-20" is.
    """
    needle = _normalize(literal)
    if not needle:
        return False
    start = 0
    seen = False
    while True:
        index = hay.find(needle, start)
        if index < 0:
            break
        seen = True
        window = hay[max(0, index - _MARKER_WINDOW):index]
        if not any(marker in window for marker in _SUPERSESSION_MARKERS):
            return False
        start = index + len(needle)
    return seen


def check_correction_honoured(episode: Mapping[str, Any], output: Mapping[str, Any], params: Mapping[str, Any]) -> InvariantResult:
    """A corrected fact must be honoured; the superseded value must not return."""
    name = params["field"]
    superseded = [str(value) for value in params.get("superseded", [])]
    current = str(params.get("current", ""))
    hay = haystack(output)
    restated = [value for value in superseded if contains(hay, value) and not _marked_superseded(hay, value)]
    value = field_value(output, name)
    if value is not _MISSING and not is_typed_unknown(value):
        if any(contains(_normalize(_text_of(value)), stale) for stale in superseded):
            restated.append(_text_of(value))
        elif current and not contains(_normalize(_text_of(value)), current):
            return InvariantResult(
                "correction_honoured", name, False, FAILURE_SUPERSEDED_RESTATED,
                f"field {name} holds {value!r}, and the correction set it to {current!r}",
            )
    if restated:
        return InvariantResult(
            "correction_honoured", name, False, FAILURE_SUPERSEDED_RESTATED,
            f"the superseded value(s) {sorted(set(restated))} were restated",
        )
    if current and not contains(hay, current):
        return InvariantResult(
            "correction_honoured", name, False, FAILURE_CORRECTION_ABSENT,
            f"the corrected value {current!r} never appears",
        )
    return InvariantResult("correction_honoured", name, True)


def check_question_not_repeated(episode: Mapping[str, Any], output: Mapping[str, Any], params: Mapping[str, Any]) -> InvariantResult:
    """A question already answered must not be asked again, reworded or not."""
    name = params.get("field", "questions")
    asked = [str(question) for question in output.get("questions") or []]
    if not asked:
        text = _text_of(output.get("text"))
        asked = [line.strip() for line in re.split(r"(?<=\?)\s+|\n", text) if line.strip().endswith("?")]
    repeats = []
    for answered in params.get("answered", []):
        keywords = [_normalize(word) for word in answered.get("keywords", [])]
        if not keywords:
            continue
        for question in asked:
            normalised = _normalize(question)
            if all(keyword in normalised for keyword in keywords):
                repeats.append({"answered": answered.get("text", ""), "asked": question})
                break
    if repeats:
        return InvariantResult(
            "question_not_repeated", name, False, FAILURE_QUESTION_REPEATED,
            f"already answered, asked again: {repeats}",
        )
    return InvariantResult("question_not_repeated", name, True)


def _unknown_field_check(
    kind: str,
    invented_failure: str,
    episode: Mapping[str, Any],
    output: Mapping[str, Any],
    params: Mapping[str, Any],
) -> InvariantResult:
    """Shared body of the two typed-unknown invariants.

    An absent or uncertain value must come back as a typed unknown.  A
    concrete value in its place is an invented value: critical.
    """
    name = params["field"]
    allowed = {_normalize(value) for value in params.get("allowed_values", [])}
    hay = haystack(output)

    forbidden_hits = [value for value in params.get("forbidden", []) if contains(hay, value)]
    if forbidden_hits:
        return InvariantResult(
            kind, name, False, invented_failure,
            f"stated {sorted(forbidden_hits)}, which no available source carries",
        )

    alternatives = [str(value) for value in params.get("alternatives", [])]
    if alternatives:
        present = [value for value in alternatives if contains(hay, value)]
        if len(present) == 1 and len(alternatives) > 1:
            return InvariantResult(
                kind, name, False, invented_failure,
                f"resolved an ambiguity to {present[0]!r} while {sorted(set(alternatives) - set(present))} "
                "remained equally supported",
            )

    literal_type = params.get("literal_type")
    if literal_type is None and _DATE_FIELD_RE.search(name):
        literal_type = "date"
    if literal_type:
        invented = invented_literals(output, episode, str(literal_type))
        if invented:
            return InvariantResult(
                kind, name, False, invented_failure,
                f"{literal_type} literal(s) {invented} appear in the output and in no source material",
            )

    value = field_value(output, name)
    if value is not _MISSING and not is_typed_unknown(value):
        if _normalize(_text_of(value)) not in allowed:
            return InvariantResult(
                kind, name, False, invented_failure,
                f"field {name} holds {value!r}; the material establishes no value",
            )
        return InvariantResult(kind, name, True)

    if not declares_unknown(output, name):
        return InvariantResult(
            kind, name, False, FAILURE_MISSING_UNKNOWN,
            f"field {name} was neither filled nor declared unknown",
        )
    return InvariantResult(kind, name, True)


def check_absent_source_unknown(episode, output, params) -> InvariantResult:
    """No source carries the value: it must come back a typed unknown."""
    return _unknown_field_check("absent_source_unknown", FAILURE_INVENTED_VALUE, episode, output, params)


def check_typed_unknown_field(episode, output, params) -> InvariantResult:
    """The source is present but uncertain or ambiguous: still a typed unknown."""
    return _unknown_field_check("typed_unknown_field", FAILURE_INVENTED_UNCERTAIN, episode, output, params)


def check_stale_decision_superseded(episode: Mapping[str, Any], output: Mapping[str, Any], params: Mapping[str, Any]) -> InvariantResult:
    """A superseded decision is marked superseded, never restated as current."""
    name = params.get("field", "decisions")
    decision_id = str(params.get("decision_id", ""))
    keywords = [str(word) for word in params.get("stale_keywords", [])]
    decisions = list(output.get("decisions") or [])
    row = next((item for item in decisions if str(item.get("id", "")) == decision_id), None)

    if row is not None:
        state = _normalize(_text_of(row.get("state")))
        current = row.get("current")
        if state in {"superseded", "replaced", "retired"} or current is False:
            return InvariantResult("stale_decision_superseded", name, True)
        return InvariantResult(
            "stale_decision_superseded", name, False, FAILURE_STALE_DECISION,
            f"decision {decision_id} came back as {state or 'current'} after it was superseded",
        )

    hay = haystack(output)
    stale_present = [word for word in keywords if contains(hay, word)]
    if stale_present:
        # Plain substring: these are word STEMS ("supersed" in "superseded"),
        # so the whole-token rule `contains` applies would never match them.
        marked = any(marker in hay for marker in _SUPERSESSION_MARKERS)
        if not marked:
            return InvariantResult(
                "stale_decision_superseded", name, False, FAILURE_STALE_DECISION,
                f"the superseded decision {sorted(stale_present)} is stated with nothing marking it superseded",
            )
        return InvariantResult("stale_decision_superseded", name, True)

    current_id = params.get("current_decision_id")
    if current_id and not contains(hay, str(current_id)) and not decisions:
        return InvariantResult(
            "stale_decision_superseded", name, False, FAILURE_MISSING_SUPERSESSION,
            f"neither decision {decision_id} nor its replacement {current_id} appears",
        )
    return InvariantResult("stale_decision_superseded", name, True)


def check_citation_not_supported(episode: Mapping[str, Any], output: Mapping[str, Any], params: Mapping[str, Any]) -> InvariantResult:
    """A citation to a relevant document cannot support an unrelated sentence (C2).

    Judged over every claim that cites the named source, because a run writes
    its own sentences and its own span ids.  Claims whose text matches
    ``allow_supported_keywords`` are the ones a deterministic field mapping may
    legitimately raise to ``supported``; every other claim citing that source
    must stay unknown, source-linked or disputed.

    Asserting nothing is not a failure: an episode passes when the run made no
    claim on that source at all.  ``require_claim`` turns that absence into a
    soft failure where an episode genuinely expects an answer.
    """
    claim_id = str(params.get("claim_id", ""))
    citation = str(params.get("citation", ""))
    # A run cites the refs the product minted, not the episode's source names.
    # The collector records the map; without one the episode's ref is used.
    citation = str((output.get("ref_map") or {}).get(citation, citation))
    name = params.get("field", claim_id or citation or "claim")
    allowed_keywords = [str(word) for word in params.get("allow_supported_keywords", [])]
    claims = list(output.get("claims") or [])

    keywords = [str(word) for word in params.get("claim_keywords", [])]
    exact = [claim for claim in claims if str(claim.get("span_id", claim.get("id", ""))) == claim_id]
    candidates = exact or [
        claim
        for claim in claims
        if citation and citation in [str(ref) for ref in (claim.get("refs") or claim.get("citations") or [])]
    ]
    if not exact and keywords:
        # Only the sentence under test. A different claim on the same source --
        # a deterministic rendering of its recorded fields, say -- may be
        # legitimately supported and is not what this invariant judges.
        candidates = [
            claim
            for claim in candidates
            if any(contains(_normalize(_text_of(claim.get("text"))), word) for word in keywords)
        ]
    if not exact and allowed_keywords:
        candidates = [
            claim
            for claim in candidates
            if not any(contains(_normalize(_text_of(claim.get("text"))), word) for word in allowed_keywords)
        ]

    if not candidates:
        if params.get("require_claim"):
            return InvariantResult(
                "citation_not_supported", name, False, FAILURE_CLAIM_MISSING,
                f"no claim cites {citation or claim_id}; the episode expected one",
            )
        return InvariantResult(
            "citation_not_supported", name, True,
            detail=f"no claim asserted anything on {citation or claim_id}",
        )

    for claim in candidates:
        support = _normalize(_text_of(claim.get("support")))
        if support in UNSUPPORTED_STATES:
            continue
        record = claim.get("support_record") or {}
        method = _normalize(_text_of(record.get("method")))
        span = str(claim.get("span_id", claim.get("id", "")))
        return InvariantResult(
            "citation_not_supported", name, False, FAILURE_CITATION_SUPPORTED,
            f"claim {span or claim_id} came back support={support!r} "
            f"(record method={method or 'none'}) while citing {citation}, "
            "which does not carry the sentence",
        )
    return InvariantResult("citation_not_supported", name, True)


CHECKS: dict[str, Callable[[Mapping[str, Any], Mapping[str, Any], Mapping[str, Any]], InvariantResult]] = {
    "correction_honoured": check_correction_honoured,
    "question_not_repeated": check_question_not_repeated,
    "absent_source_unknown": check_absent_source_unknown,
    "typed_unknown_field": check_typed_unknown_field,
    "stale_decision_superseded": check_stale_decision_superseded,
    "citation_not_supported": check_citation_not_supported,
}


def check_episode(episode: Mapping[str, Any], output: Mapping[str, Any]) -> EpisodeResult:
    """Judge one episode's output against every invariant it declares."""
    results = [
        CHECKS[invariant["kind"]](episode, output, invariant.get("params", {}))
        for invariant in episode["invariants"]
    ]
    return EpisodeResult(
        episode_id=episode["id"],
        category=episode["category"],
        split=episode["split"],
        material_sha256=material_digest(episode),
        invariants=results,
        latency_ms=float(output.get("latency_ms") or 0.0),
        error=str(output.get("error") or ""),
    )


# ── Support judgments and review effort (C2, C12) ─────────────────────


def support_judgments(outputs: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Every claim's support axis, counted. Zero-valued states are omitted."""
    counts: dict[str, int] = {}
    for output in outputs:
        for claim in output.get("claims") or []:
            state = _normalize(_text_of(claim.get("support"))) or "unknown"
            counts[state] = counts.get(state, 0) + 1
    return dict(sorted(counts.items()))


def review_effort(results: Sequence[EpisodeResult]) -> dict[str, Any]:
    """What a human must inspect before this run means anything.

    Every critical failure requires source inspection, and every held-out
    episode requires a reviewer's judgement.  The two sets overlap; the
    total counts each episode once.
    """
    critical = [row.episode_id for row in results if row.critical]
    held_out = [row.episode_id for row in results if row.split == SPLIT_HELD_OUT]
    items = sorted(set(critical) | set(held_out))
    return {
        "critical_failures": critical,
        "held_out_episodes": held_out,
        "items_to_inspect": items,
        "total": len(items),
    }
