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
        error_context = bool(
            re.search(r"(?:setError|setMessage|routeError|State\s*=|toast\()", raw_line)
        )
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
            for match in _QUOTED.finditer(raw_line):
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
    literals = tuple(str(value) for value in exception.get("literals") or ())
    return fnmatch.fnmatch(candidate.path, path) and candidate.text in literals


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
