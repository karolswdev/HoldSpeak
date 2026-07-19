"""Versioned primary-client copy inventory and regression census.

The product-language registry declares which production surfaces participate in
the Phase-93 copy contract.  This module extracts user-visible literals from
those surfaces, classifies every extracted string, and reports prohibited copy
without confusing stable wire identifiers with rendered language.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import fnmatch
import re
from pathlib import Path
from typing import Iterable, Iterator, Mapping

from .product_language import PRODUCT_LANGUAGE, ProductCopyContract


COPY_CLASSIFICATIONS = frozenset(
    {
        "label",
        "state",
        "supporting_line",
        "detail",
        "error_recovery",
        "marketing_sdk_exception",
    }
)

_QUOTED = re.compile(r'(?P<quote>["`])(?P<text>(?:\\.|(?!\1).)*?)(?P=quote)')
_JSX_TEXT = re.compile(r">\s*([^<{][^<]*?)\s*<")
_INLINE_CODE = re.compile(r"`([^`]+)`")
_MARKDOWN_LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_HTML_ALT = re.compile(r'\balt=["\']([^"\']+)["\']', re.IGNORECASE)
_VISIBLE_PROP = re.compile(
    r"\b(title|label|placeholder|aria-label|eyebrow|description|detail)"
    r"\s*=\s*(?:\{)?(?P<quote>[\"`])(?P<text>.*?)(?P=quote)"
)
_SWIFT_VISIBLE = re.compile(
    r"\b(Text|Label|Button|TextField|Section|navigationTitle|accessibilityLabel|"
    r"accessibilityHint|alert)\s*\("
)
_FAILURE_WORDS = re.compile(
    r"\b(fail(?:ed|ure)?|unavailable|refus(?:ed|al)|error|retry|recover|"
    r"not saved|not changed|offline|unreachable|denied|expired|conflict)\b",
    re.IGNORECASE,
)
_STATE_WORDS = re.compile(
    r"\b(ready|queued|running|succeeded|failed|cancelled|offline|available|"
    r"configured|synced|recording|accepted|dismissed|approved|rejected|"
    r"revoked|needs review|needs approval|needs attention)\b",
    re.IGNORECASE,
)
# HS-93-03 — forced-failure copy must carry the contract's four failure facts.
# A failure statement asserts that an operation failed; short state chips and
# recovery buttons are not statements and are checked by their own rules.
_FAILURE_ASSERTION = re.compile(
    r"\b(?:fail(?:s|ed|ure)?|unavailable|unreachable|refused|denied|"
    r"could not|couldn['’]t|"
    r"cannot\b(?!\s+be\s+(?:restored|undone|recovered))|"
    r"can['’]t\b(?!\s+(?:undo|be\s+(?:restored|undone|recovered)))|"
    r"not (?:saved|changed|sent|recorded|delivered)|timed out|malformed)\b",
    re.IGNORECASE,
)
_RETAINED_FACT = re.compile(
    r"\b(?:retained|saved|kept|keeps?|stays?|remains?|unchanged|preserved|"
    r"recovered|not (?:changed|sent|typed|lost|deleted|created|written|run)|"
    r"nothing (?:was |were )?(?:sent|typed|changed|created|deleted|"
    r"downloaded|recorded|written|lost|run|imported)|"
    r"no (?:audio|file|text|change|draft|work|data|message|meeting|issue)s? "
    r"(?:was|were|is|are) "
    r"(?:recorded|captured|sent|written|created|changed|lost|deleted|affected)|"
    r"still (?:open|editable|here|available|retained|saved|recorded))\b",
    re.IGNORECASE,
)
_NEXT_ACTION_FACT = re.compile(
    r"\b(?:retry|try again|check|reconnect|re-?pair\b|review|choose|select|"
    r"switch|start|record again|reimport|import again|edit|enter|type|reload|"
    r"refresh|sign in|set ?up|grant|dismiss|search again|send again|run again|"
    r"run it again|stop to retry|auto-?resumes?|resumes?|repair|enable|"
    r"open (?:setup|settings|runtime|readiness)|allow|pick|name|shorten|wait)\b",
    re.IGNORECASE,
)
_DESTINATION_RELEVANT = re.compile(
    r"\b(?:send|sent|sending|deliver(?:y|ed|ing)?|sync(?:ed|ing)?|post(?:ed)?|"
    r"publish(?:ed)?|reach(?:ed)?|unreachable|connect(?:ion|ed|ing)?|"
    r"pair(?:ed|ing)?|upload(?:ed)?|download(?:ed)?|webhook|filed?|filing|"
    r"typed?|typing)\b",
    re.IGNORECASE,
)
_DESTINATION_FACT = re.compile(
    r"\b(?:this (?:device|browser|mac)|paired (?:device|desktop)|"
    r"private endpoint|external service|desktop|browser|slack|github|hub|"
    r"node|peer|endpoint|server|device|hugging face|clipboard|homelab)\b"
    r"|\{value\}?|\bvalue\}",
    re.IGNORECASE,
)
_FAILURE_STOPWORDS = frozenset(
    """
    a an and are be been but by for from had has have here in is it its no not
    nothing of on or something request operation error the that this to was
    were will with your
    """.split()
)
_SOURCE_COPY_SUFFIXES = (".tsx", ".ts", ".swift", ".py")
_HUB_LOG_CALL = re.compile(
    r"\blog(?:ger)?\.(?:debug|info|warning|error|exception|critical)\("
)
_ERROR_CONTEXT = re.compile(
    r"(?:setError|setMessage|routeError|State\s*=|toast\(|"
    r"[a-z](?:Error|Detail|Failure|Reason|Message)\s*[:=])"
)
_CODE_PREFIXES = (
    "const ",
    "let ",
    "var ",
    "return ",
    "case ",
    "if ",
    "else ",
    "for ",
    "while ",
    "func ",
    "private ",
    "public ",
    "struct ",
    "class ",
    "import ",
    "export ",
    "type ",
    "interface ",
)


@dataclass(frozen=True, order=True)
class CopyCandidate:
    client: str
    path: str
    line: int
    text: str
    classification: str
    context: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, order=True)
class CopyViolation:
    rule_id: str
    path: str
    line: int
    text: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _expand_braces(pattern: str) -> list[str]:
    """Expand the small comma-brace grammar used by the registry globs."""

    match = re.search(r"\{([^{}]+)\}", pattern)
    if not match:
        return [pattern]
    expanded: list[str] = []
    for choice in match.group(1).split(","):
        replaced = pattern[: match.start()] + choice + pattern[match.end() :]
        expanded.extend(_expand_braces(replaced))
    return expanded


def iter_surface_paths(
    root: Path,
    contract: ProductCopyContract | None = None,
) -> Iterator[tuple[str, Path]]:
    selected = contract or PRODUCT_LANGUAGE.copy_contract
    seen: set[tuple[str, Path]] = set()
    for client, patterns in selected.primary_surfaces.items():
        for source_pattern in patterns:
            for pattern in _expand_braces(source_pattern):
                for path in sorted(root.glob(pattern)):
                    key = (client, path)
                    if (
                        path.is_file()
                        and ".test." not in path.name
                        and key not in seen
                    ):
                        seen.add(key)
                        yield key


def _normalize_literal(value: str) -> str:
    value = re.sub(r"\\\([^)]*\)", "{value}", value)
    value = re.sub(r"\$\{[^}]*\}", "{value}", value)
    value = re.sub(r"\{[A-Za-z_][^{}]*\}", "{value}", value)
    value = value.replace(r'\"', '"').replace(r"\n", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value.strip("{} ")


def _looks_like_copy(value: str) -> bool:
    if not value or not re.search(r"[A-Za-z]", value):
        return False
    if value.startswith(("/", "http://", "https://", "hs.", "--")):
        return False
    if re.fullmatch(r"[a-z0-9_.:/?=&${}-]+", value):
        return False
    if re.fullmatch(r"[a-z0-9.-]+\.[a-z0-9.-]+", value):
        return False
    if value.count("_") >= 2 and " " not in value:
        return False
    return True


def _classification(text: str, context: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text)
    if context == "exception":
        return "marketing_sdk_exception"
    if _FAILURE_WORDS.search(text):
        return "error_recovery"
    if _STATE_WORDS.fullmatch(text.strip(" .·")) or (
        context == "state" and len(words) <= 8
    ):
        return "state"
    if context in {"label", "action", "heading"} or len(words) <= 4:
        return "label"
    if len(words) <= 24 and text.endswith((".", "?", "!")):
        return "supporting_line"
    return "detail"


def _candidate(
    *, client: str, relative: str, line: int, text: str, context: str
) -> CopyCandidate | None:
    normalized = _normalize_literal(text)
    if not _looks_like_copy(normalized):
        return None
    return CopyCandidate(
        client=client,
        path=relative,
        line=line,
        text=normalized,
        classification=_classification(normalized, context),
        context=context,
    )


def _extract_source(client: str, relative: str, source: str) -> Iterator[CopyCandidate]:
    in_fence = False
    in_block_comment = False
    pending_error_context = 0
    for line_number, raw_line in enumerate(source.splitlines(), 1):
        stripped = raw_line.strip()
        if relative.endswith(".md") and stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "/*" in stripped:
            in_block_comment = True
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith(("//", "<!--")):
            continue
        if client == "hub" and _HUB_LOG_CALL.search(stripped):
            # Hub log lines are server diagnostics, not user-served copy.
            continue

        emitted: set[tuple[str, str]] = set()

        def emit(text: str, context: str) -> Iterator[CopyCandidate]:
            candidate = _candidate(
                client=client,
                relative=relative,
                line=line_number,
                text=text,
                context=context,
            )
            if candidate and (candidate.text, context) not in emitted:
                emitted.add((candidate.text, context))
                yield candidate

        if relative.endswith((".md", ".yaml", ".yml")):
            value = stripped
            if relative.endswith((".yaml", ".yml")) and ":" in value:
                key, value = value.split(":", 1)
                context = "heading" if key.strip() == "title" else "detail"
            else:
                context = "heading" if value.startswith("#") else "detail"
                value = value.lstrip("#-*0123456789. ")
            for match in _HTML_ALT.finditer(value):
                yield from emit(match.group(1), "label")
            prose = _INLINE_CODE.sub(" ", value)
            prose = _MARKDOWN_LINK.sub(r"\1", prose)
            prose = re.sub(r"<[^>]+>", " ", prose)
            yield from emit(prose.strip(' "'), context)
            continue

        for match in _VISIBLE_PROP.finditer(raw_line):
            yield from emit(match.group("text"), "label")
        for match in _JSX_TEXT.finditer(raw_line):
            yield from emit(match.group(1), "action" if "button" in raw_line.lower() else "label")

        swift_visible = bool(_SWIFT_VISIBLE.search(raw_line))
        quoted = list(_QUOTED.finditer(raw_line))
        error_context = bool(_ERROR_CONTEXT.search(raw_line))
        # A ternary or wrapped assignment carries its error context onto the
        # literal's continuation line (HS-93-03 failure-copy coverage).
        if pending_error_context and quoted and stripped[:1] in "?:\"'`":
            error_context = True
        if error_context and not quoted:
            pending_error_context = 2
        else:
            pending_error_context = max(0, pending_error_context - 1)
        ui_assignment = bool(
            re.search(
                r"\b(?:title|label|subtitle|preview|message|detail|error|state)\b",
                raw_line,
                re.IGNORECASE,
            )
        )
        registry_adapter = relative.endswith(
            ("productLanguage.ts", "ProductLanguage.swift", "EgressScope.swift")
        )
        if swift_visible or error_context or ui_assignment or registry_adapter:
            context = (
                "error_recovery"
                if error_context
                else "action"
                if re.search(r"\b(?:Button|Label)\s*\(", raw_line)
                else "label"
            )
            for match in quoted:
                yield from emit(match.group("text"), context)

        if relative.endswith(".tsx") and stripped and not any(emitted):
            if (
                stripped[0].isupper()
                and not stripped.startswith(_CODE_PREFIXES)
                and not re.search(r"[=><{};]|=>|\|\||\bString\(", stripped)
            ):
                yield from emit(stripped, "supporting_line")


def inventory(
    root: Path,
    contract: ProductCopyContract | None = None,
) -> list[CopyCandidate]:
    candidates: set[CopyCandidate] = set()
    for client, path in iter_surface_paths(root, contract):
        relative = path.relative_to(root).as_posix()
        source = path.read_text(encoding="utf-8")
        candidates.update(_extract_source(client, relative, source))
    return sorted(candidates)


def _exception_matches(
    exception: Mapping[str, object], candidate: CopyCandidate
) -> bool:
    path = str(exception.get("path") or "")
    if not fnmatch.fnmatch(candidate.path, path):
        return False
    literals = tuple(str(value) for value in exception.get("literals") or ())
    if candidate.text in literals:
        return True
    # HS-100-10: a registry exception may carry `terms` — whole words
    # whose presence excepts the candidate on the matched path (used to
    # stage vocabulary migrations per client, e.g. the Apple surfaces'
    # Persona -> Agent rename that lands with the HSM follow-up).
    terms = tuple(str(value) for value in exception.get("terms") or ())
    return any(
        re.search(rf"\b{re.escape(term)}\b", candidate.text) for term in terms
    )


def _is_failure_statement(candidate: CopyCandidate) -> bool:
    """A rendered statement that an operation failed, not a chip or button."""

    if not candidate.path.endswith(_SOURCE_COPY_SUFFIXES):
        return False
    if not _FAILURE_ASSERTION.search(candidate.text):
        return False
    words = re.findall(r"[A-Za-z0-9]+", candidate.text)
    if len(words) >= 4:
        return True
    return len(words) == 3 and candidate.text.rstrip().endswith((".", "!", "?"))


def _missing_failure_facts(text: str) -> list[str]:
    """The contract's four failure facts a forced-failure string must carry."""

    missing: list[str] = []
    content = [
        word
        for word in re.findall(r"[A-Za-z]+", _FAILURE_ASSERTION.sub(" ", text))
        if word.lower() not in _FAILURE_STOPWORDS
    ]
    if not content:
        missing.append("failed_operation")
    if not _RETAINED_FACT.search(text):
        missing.append("retained_work")
    if not _NEXT_ACTION_FACT.search(text):
        missing.append("next_action")
    if _DESTINATION_RELEVANT.search(text) and not _DESTINATION_FACT.search(text):
        missing.append("destination_when_relevant")
    return missing


def violations(
    candidates: Iterable[CopyCandidate],
    contract: ProductCopyContract | None = None,
) -> list[CopyViolation]:
    selected = contract or PRODUCT_LANGUAGE.copy_contract
    result: set[CopyViolation] = set()
    for candidate in candidates:
        if candidate.classification == "marketing_sdk_exception":
            continue
        excepted = any(
            _exception_matches(exception, candidate)
            for exception in selected.exceptions
        )
        for rule in selected.prohibited_operational_patterns:
            if excepted:
                break
            if re.search(rule.pattern, candidate.text, re.IGNORECASE):
                result.add(
                    CopyViolation(
                        rule_id=rule.id,
                        path=candidate.path,
                        line=candidate.line,
                        text=candidate.text,
                        reason=rule.reason,
                    )
                )
        if (
            candidate.text in selected.generic_consequential_verbs
            and candidate.context == "action"
            and not excepted
        ):
            result.add(
                CopyViolation(
                    rule_id="generic-consequential-verb",
                    path=candidate.path,
                    line=candidate.line,
                    text=candidate.text,
                    reason="Name the immediate consequence and destination.",
                )
            )
        if (
            selected.failure_requirements
            and not excepted
            and _is_failure_statement(candidate)
        ):
            missing = _missing_failure_facts(candidate.text)
            if missing:
                result.add(
                    CopyViolation(
                        rule_id="failure-missing-facts",
                        path=candidate.path,
                        line=candidate.line,
                        text=candidate.text,
                        reason=(
                            "Failure copy names what failed, retained work, "
                            "the next valid action, and the destination when "
                            "relevant (missing: " + ", ".join(missing) + ")."
                        ),
                    )
                )
    return sorted(result)


def census(root: Path) -> dict[str, object]:
    candidates = inventory(root)
    problems = violations(candidates)
    counts: dict[str, int] = {}
    clients: dict[str, int] = {}
    for candidate in candidates:
        counts[candidate.classification] = counts.get(candidate.classification, 0) + 1
        clients[candidate.client] = clients.get(candidate.client, 0) + 1
    return {
        "registry_version": PRODUCT_LANGUAGE.version,
        "copy_contract_version": PRODUCT_LANGUAGE.copy_contract.version,
        "counts_by_classification": dict(sorted(counts.items())),
        "counts_by_client": dict(sorted(clients.items())),
        "candidate_count": len(candidates),
        "violation_count": len(problems),
        "violations": [problem.to_dict() for problem in problems],
        "inventory": [candidate.to_dict() for candidate in candidates],
    }


__all__ = [
    "COPY_CLASSIFICATIONS",
    "CopyCandidate",
    "CopyViolation",
    "census",
    "inventory",
    "iter_surface_paths",
    "violations",
]
