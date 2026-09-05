#!/usr/bin/env python3
"""
ux_canon_scan.py -- Mechanical UX-canon violation scanner for HoldSpeak faces.

Scans web/src (tsx + css; skips __tests__ and *.test.*) for canon violations
per the owner's rulings in docs/internal/UX-CANON.md, the surface contract,
and the design system.

Usage:
    python scripts/ux_canon_scan.py [--root DIR] [--json PATH] [--md PATH]

Outputs:
    violations.md   — per-face section with file:line and rule
    violations.json — machine-readable for guards
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Face classification
# ---------------------------------------------------------------------------

FACE_DIRS = ("features/", "pages/cores/", "desk/")

# Tuesday-use ranking from THE-TUESDAY-ARC.md section 0 and the 169 recon.
# Higher = more Tuesday use.  Surfaces a Senior Architect managing 3 people
# meets weekly come first.
TUESDAY_USE: dict[str, int] = {
    # Tier 1 -- weekly contact surfaces
    "settingsModels": 8,
    "ConnectionsPane": 8,
    "SettingsCore": 7,
    "DoorCore": 7,
    "ProjectRoomCore": 7,
    "HistoryCore": 6,       # Meetings + aftercare
    "MeetingDetail": 6,
    "PeopleCore": 6,
    "ThreadPullout": 6,
    "DeskComposer": 6,      # the Thread / Ask
    "AttentionDrawer": 5,   # the shade / attention
    "SystemShade": 5,
    "SpeakFace": 5,         # Speak
    "DictationCore": 5,
    # Tier 2 -- regular but not weekly
    "SetupCore": 4,
    "SetupRoot": 4,
    "SetupInterview": 4,
    "ActivationReview": 4,
    "ReviewPosture": 4,
    "StewardPosture": 4,
    "UpdatePosture": 4,
    "Chair": 4,
    "ChairHome": 4,
    "WorkbenchWindow": 3,
    "CadenceCore": 3,
    "ActivityCore": 3,
    "ModelLibraryCore": 3,
    "AssignmentEditor": 3,
    "frontDoor": 3,
    "DeskChrome": 3,
    "DeskWindow": 3,
    # Tier 3 -- infrequent
    "CommandsCore": 2,
    "CompanionCore": 2,
    "LiveCore": 2,
    "ProcessCore": 2,
    "CalendarSnapshotReviewCore": 2,
    "RuntimeDocsCore": 1,
    "TopologyMapView": 1,
    "ComponentsCore": 1,
    "ConstitutionalContextCore": 1,
    "CapabilityAssignmentsCore": 1,
    "settingsTts": 1,
    "settingsBespoke": 1,
    "settingsPrefs": 1,
}

# Weights per rule class for debt scoring.
# A1 modal/raw button/sentence = 3;  zero counter/egress/rail = 2;  others = 1
RULE_WEIGHTS: dict[str, int] = {
    "A1": 3,   # Raw <button> (not the library Button)
    "A3-sentence": 3,   # Sentences in JSX text
    "A3-prose": 3,      # Prose helpers
    "A4": 3,   # Modals
    "A8": 2,   # Counters of zero
    "A9": 2,   # Missing egress
    "B": 1,    # Non-library controls
    "DS6": 2,  # Accent left rails
    "C": 1,    # Type-step collapse
    "raw-ids": 1,  # Raw kinds/ids on the face
    "emoji": 1,    # Emoji/dingbats in JSX text
    "mic": 1,      # Missing MicButton on text input
}


def classify_face(rel: str) -> str | None:
    """Return a face name from a relative path, or None if not a face file."""
    # Only tsx files are faces (css files contribute to their parent face)
    if not rel.endswith(".tsx"):
        return None
    stem = Path(rel).stem
    # Files under features/**, pages/cores/**, desk/** that render
    # a window/core/lane
    for d in FACE_DIRS:
        if rel.startswith(d):
            return stem
    return None


def face_for_file(rel: str) -> str | None:
    """For any file (tsx or css), return the face it belongs to."""
    if rel.endswith(".tsx"):
        return classify_face(rel)
    # CSS: the face is the nearest tsx in the same directory, or the directory name
    parent = str(Path(rel).parent)
    stem = Path(rel).stem
    return stem  # best effort: surface.css -> surface


# ---------------------------------------------------------------------------
# Scanning rules
# ---------------------------------------------------------------------------

class Violation:
    __slots__ = ("file", "line", "rule", "text", "confidence")

    def __init__(self, file: str, line: int, rule: str, text: str, confidence: str = "high"):
        self.file = file
        self.line = line
        self.rule = rule
        self.text = text
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "file": self.file,
            "line": self.line,
            "rule": self.rule,
            "text": self.text,
        }
        if self.confidence != "high":
            d["confidence"] = self.confidence
        return d


def scan_file(rel_path: str, content: str, lines: list[str]) -> list[Violation]:
    """Scan a single file for all rule classes."""
    violations: list[Violation] = []
    is_tsx = rel_path.endswith(".tsx")
    is_css = rel_path.endswith(".css")

    # Track per-file state
    has_button_import = False
    has_egress_chip = False
    has_provider_fetch = False
    has_mic_button = False
    has_text_input = False
    font_sizes: set[str] = set()

    if is_tsx:
        # Check imports
        has_button_import = bool(re.search(
            r'import\s+\{[^}]*\bButton\b[^}]*\}\s+from\s+["\'].*signal/Signal["\']',
            content
        ))
        has_egress_chip = "EgressChip" in content
        has_mic_button = "MicButton" in content

    for i, line_text in enumerate(lines, 1):
        stripped = line_text.strip()

        if is_tsx:
            # Rule A1: Raw <button (not the library Button)
            # Case-sensitive: <button is raw HTML; <Button is the library component
            # Exclude Signal.tsx (the library itself) and gadgets.tsx (surface kit)
            is_button_library = any(k in rel_path for k in (
                "Signal.tsx", "gadgets.tsx",
            ))
            if not is_button_library and re.search(r'<button[\s>/]', line_text):
                # Exclude comments
                if not stripped.startswith("//") and not stripped.startswith("*") and not stripped.startswith("/*"):
                    violations.append(Violation(rel_path, i, "A1",
                        f"Raw <button> element (use library Button): {stripped[:100]}"))

            # Rule A3-sentence: text nodes > 60 chars ending in ./!/? or with ", " + verb
            # Look for JSX text content (between > and <, or in template literals)
            jsx_texts = re.findall(r'>([^<>{]+)<', line_text)
            for txt in jsx_texts:
                txt = txt.strip()
                if len(txt) > 60 and re.search(r'[.!?]$', txt):
                    violations.append(Violation(rel_path, i, "A3-sentence",
                        f"Sentence in JSX text (>60 chars): \"{txt[:80]}...\""))
                elif len(txt) > 60 and re.search(r',\s+\w+(s|ed|ing|es)\b', txt):
                    violations.append(Violation(rel_path, i, "A3-sentence",
                        f"Sentence in JSX text (verb + comma): \"{txt[:80]}...\""))

            # Also check string literals used as prop values (title=, label=, etc.)
            prop_texts = re.findall(r'(?:title|label|description|placeholder|children)=\{?"([^"]{60,})"', line_text)
            for txt in prop_texts:
                if re.search(r'[.!?]$', txt):
                    violations.append(Violation(rel_path, i, "A3-sentence",
                        f"Sentence in prop text: \"{txt[:80]}...\""))

            # Rule A3-prose: <p>/<small>/className with hint|help|description, text > 40 chars
            if re.search(r'<(?:p|small)\b[^>]*>', line_text):
                # Check if there's text content
                text_match = re.search(r'<(?:p|small)[^>]*>([^<]+)', line_text)
                if text_match and len(text_match.group(1).strip()) > 40:
                    violations.append(Violation(rel_path, i, "A3-prose",
                        f"Prose in <p>/<small> element: \"{text_match.group(1).strip()[:80]}...\""))
            if re.search(r'className\s*=\s*["{][^"]*(?:hint|help|description)', line_text):
                # Find nearby text
                violations.append(Violation(rel_path, i, "A3-prose",
                    f"Prose helper class (hint/help/description): {stripped[:100]}"))

            # Rule A4: Modals
            if re.search(r'role\s*=\s*["\']dialog["\']', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Modal (role=\"dialog\"): {stripped[:100]}"))
            if re.search(r'aria-modal', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Modal (aria-modal): {stripped[:100]}"))
            if re.search(r'<(?:Modal|Dialog)\b', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Modal/Dialog component: {stripped[:100]}"))
            if re.search(r'position:\s*fixed', line_text):
                # Check for backdrop-like patterns
                if re.search(r'(?:backdrop|overlay|modal|z-index)', content[max(0, content.find(line_text)-200):content.find(line_text)+200], re.IGNORECASE):
                    violations.append(Violation(rel_path, i, "A4",
                        f"Fixed overlay (possible modal): {stripped[:100]}", confidence="medium"))

            # Rule A8: Counters of zero (best effort)
            # .length interpolations without zero guard
            if re.search(r'\{[^}]*\.length\s*\}', line_text):
                # Check for a zero guard (ternary, &&, ?? in the same expression)
                expr_match = re.search(r'\{([^}]*\.length[^}]*)\}', line_text)
                if expr_match:
                    expr = expr_match.group(1)
                    if not re.search(r'[?&|]|===?\s*0|!==?\s*0|>\s*0', expr):
                        violations.append(Violation(rel_path, i, "A8",
                            f"Counter may render zero (.length without guard): {stripped[:100]}",
                            confidence="medium"))
            # {count} Noun pattern
            if re.search(r'\{[^}]*(?:count|Count|total|num|len)\b[^}]*\}\s*\w', line_text):
                if not re.search(r'[?&|]|===?\s*0|!==?\s*0|>\s*0', line_text):
                    violations.append(Violation(rel_path, i, "A8",
                        f"Counter may render zero (count pattern): {stripped[:100]}",
                        confidence="low"))
            # Explicit "0 " or "{0}" patterns (rare but direct)
            if re.search(r'>\s*0\s+\w', line_text):
                violations.append(Violation(rel_path, i, "A8",
                    f"Literal zero counter in text: {stripped[:100]}",
                    confidence="medium"))
            # ?? 0 pattern (explicitly renders 0 as fallback)
            if re.search(r'\?\?\s*0\b', line_text):
                # check if it's rendered as text
                if re.search(r'\{[^}]*\?\?\s*0[^}]*\}', line_text):
                    violations.append(Violation(rel_path, i, "A8",
                        f"Zero fallback rendered (?? 0): {stripped[:100]}",
                        confidence="medium"))

            # Rule A9: Provider fetches without EgressChip
            provider_patterns = [
                r'/api/providers/',
                r'\bdiscover\b.*(?:fetch|api|post|get)',
                r'(?:fetch|api|post|get).*\bdiscover\b',
                r'\brecheck\b.*(?:fetch|api)',
                r'\bevaluate\b.*(?:fetch|api)',
            ]
            for pat in provider_patterns:
                if re.search(pat, line_text, re.IGNORECASE):
                    has_provider_fetch = True
                    break

            # Rule B: Non-library controls (raw <input>/<select>/<textarea>)
            # Exclude files that ARE the library wrappers
            is_library_file = any(k in rel_path for k in (
                "Signal.tsx", "gadgets.tsx", "MicButton", "StringGadget",
                "EditInPlace", "CycleGadget", "CheckGadget", "PadGadget",
                "LedgerFilter", "ChoiceCard", "surface/controls/",
            ))
            if not is_library_file and re.search(r'<(?:input|select|textarea)\b', line_text):
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    violations.append(Violation(rel_path, i, "B",
                        f"Raw control element: {stripped[:100]}"))

            # Rule raw-ids: snake_case strings rendered as visible text;
            # id fields rendered as visible text (not in props, keys, APIs, imports)
            # Only flag snake_case between > and < (JSX text position)
            jsx_snake_texts = re.findall(r'>([^<]*[a-z]+_[a-z_]+[^<]*)<', line_text)
            for txt in jsx_snake_texts:
                snakes = re.findall(r'\b([a-z]+_[a-z_]+)\b', txt)
                for snake in snakes:
                    if snake not in ("aria_label", "data_testid", "class_name",
                                     "aria_hidden", "tab_index"):
                        violations.append(Violation(rel_path, i, "raw-ids",
                            f"Snake_case literal in rendered text: \"{snake}\""))
            # Also check title/label props that show visible text with raw IDs
            title_match = re.search(r'(?:title|label)=\{[`"]([^`"]*(?:\.\s*id\b|_id\b)[^`"]*)[`"]\}', line_text)
            if title_match:
                violations.append(Violation(rel_path, i, "raw-ids",
                    f"ID rendered in visible prop: {title_match.group(0)[:100]}",
                    confidence="medium"))
            # {foo.id} directly as JSX child text (between > and <)
            # Matches patterns like >{thing.id}< or >{thing_id}<
            if re.search(r'>\s*\{[^}]*(?:\.\s*id\s*\}|_id\s*\})', line_text):
                violations.append(Violation(rel_path, i, "raw-ids",
                    f"ID field rendered as text: {stripped[:100]}",
                    confidence="medium"))

            # Rule emoji: Emoji/dingbats in JSX text
            # Unicode ranges for common emoji
            emoji_match = re.search(
                r'[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]',
                line_text
            )
            if emoji_match:
                if not stripped.startswith("//") and not stripped.startswith("*"):
                    # Exclude aria-hidden elements (intentional decorative emoji)
                    if 'aria-hidden' not in line_text:
                        violations.append(Violation(rel_path, i, "emoji",
                            f"Emoji in JSX text: {stripped[:100]}"))

            # Rule mic: Track text inputs
            if re.search(r'<(?:input|StringGadget|TextInput)\b', line_text):
                if re.search(r'type\s*=\s*["\']text["\']', line_text) or not re.search(r'type\s*=', line_text):
                    has_text_input = True

        if is_css:
            # Rule DS6: Accent left rails (border-left with accent/color)
            if re.search(r'border-left\s*:', line_text):
                # Check if it has a color value (not just width)
                if re.search(r'border-left\s*:.*(?:var\(--accent|#[0-9a-fA-F]|rgb|hsl|var\(--\w*accent|var\(--\w*color)', line_text):
                    violations.append(Violation(rel_path, i, "DS6",
                        f"Accent left rail (banned by DESIGN_SYSTEM rule 6): {stripped[:100]}"))
                elif re.search(r'border-left\s*:\s*\d+px\s+solid\s+var\(', line_text):
                    violations.append(Violation(rel_path, i, "DS6",
                        f"Border-left with token (check if accent): {stripped[:100]}",
                        confidence="medium"))

            # Rule C: Collect font-sizes for type-step collapse detection
            fs_match = re.search(r'font-size\s*:\s*([^;]+)', line_text)
            if fs_match:
                font_sizes.add(fs_match.group(1).strip())

        # Also check inline styles in tsx for font-size and border-left
        if is_tsx:
            if re.search(r'fontSize\s*:', line_text):
                fs_match = re.search(r'fontSize\s*:\s*["\']?([^"\'}, ]+)', line_text)
                if fs_match:
                    font_sizes.add(fs_match.group(1).strip())
            if re.search(r'borderLeft\s*:', line_text):
                if re.search(r'borderLeft\s*:.*(?:accent|#[0-9a-fA-F]|rgb)', line_text):
                    violations.append(Violation(rel_path, i, "DS6",
                        f"Inline accent left rail: {stripped[:100]}"))

    # Post-file checks

    # Rule A9: Provider fetch without EgressChip
    if is_tsx and has_provider_fetch and not has_egress_chip:
        violations.append(Violation(rel_path, 1, "A9",
            "Provider fetch found but no EgressChip rendered in this file"))

    # Rule C: Type-step collapse (only for TSX face files)
    if is_tsx and classify_face(rel_path):
        # A face with <= 1 distinct font-size is a defect (from CSS or inline)
        # We can only detect this from CSS + inline; mark as best-effort
        if font_sizes and len(font_sizes) <= 1:
            violations.append(Violation(rel_path, 1, "C",
                f"Type-step collapse: only {len(font_sizes)} distinct font-size ({', '.join(font_sizes)})",
                confidence="medium"))

    # Rule mic: Missing MicButton on text input
    if is_tsx and has_text_input and not has_mic_button:
        face = classify_face(rel_path)
        if face:  # Only flag for face files
            violations.append(Violation(rel_path, 1, "mic",
                "Text input found but no MicButton in this face (the voice law)"))

    return violations


# ---------------------------------------------------------------------------
# Aggregate: pair CSS with nearest TSX face
# ---------------------------------------------------------------------------

def find_face_files(root: Path) -> list[Path]:
    """Find all scannable files under web/src."""
    result = []
    src = root / "web" / "src"
    if not src.is_dir():
        return result
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix not in (".tsx", ".css"):
            continue
        rel = str(p.relative_to(src))
        if "__tests__" in rel or ".test." in rel or "_parked" in rel:
            continue
        # Only scan face directories
        is_face_dir = False
        for d in FACE_DIRS:
            if rel.startswith(d):
                is_face_dir = True
                break
        if is_face_dir:
            result.append(p)
    return result


def file_to_face(rel: str) -> str:
    """Map a relative path to a face name for grouping."""
    stem = Path(rel).stem
    # For CSS files, try to find the face they belong to (same directory tsx)
    return stem


def scan_all(root: Path) -> tuple[dict[str, list[Violation]], list[Violation]]:
    """Scan all face files. Returns (per_face, all_violations)."""
    src = root / "web" / "src"
    files = find_face_files(root)
    per_face: dict[str, list[Violation]] = defaultdict(list)
    all_violations: list[Violation] = []

    # Also scan paired CSS files for each TSX face
    css_companions: dict[str, set[str]] = defaultdict(set)

    for f in files:
        rel = str(f.relative_to(src))
        content = f.read_text(errors="replace")
        file_lines = content.splitlines()
        violations = scan_file(rel, content, file_lines)

        face = file_to_face(rel)
        per_face[face].extend(violations)
        all_violations.extend(violations)

    return dict(per_face), all_violations


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def build_totals(all_violations: list[Violation]) -> dict[str, dict[str, int]]:
    """Build totals tables: per rule and per face."""
    per_rule: dict[str, int] = defaultdict(int)
    per_face: dict[str, int] = defaultdict(int)
    for v in all_violations:
        per_rule[v.rule] += 1
        face = file_to_face(v.file)
        per_face[face] += 1
    return {"per_rule": dict(per_rule), "per_face": dict(per_face)}


def build_ranking(per_face: dict[str, list[Violation]]) -> list[dict[str, Any]]:
    """Rank faces by Tuesday use x canon debt."""
    ranking = []
    for face, violations in per_face.items():
        if not violations:
            continue
        tuesday = TUESDAY_USE.get(face, 1)
        debt = sum(RULE_WEIGHTS.get(v.rule, 1) for v in violations)
        score = tuesday * debt
        # Find loudest break (highest weight violation)
        loudest = max(violations, key=lambda v: RULE_WEIGHTS.get(v.rule, 1))
        # Count per rule
        rule_counts: dict[str, int] = defaultdict(int)
        for v in violations:
            rule_counts[v.rule] += 1
        ranking.append({
            "face": face,
            "tuesday_use": tuesday,
            "debt": debt,
            "score": score,
            "hits": len(violations),
            "loudest_rule": loudest.rule,
            "loudest_text": loudest.text,
            "rule_counts": dict(rule_counts),
        })
    ranking.sort(key=lambda r: r["score"], reverse=True)
    return ranking


def write_violations_md(path: Path, per_face: dict[str, list[Violation]],
                        totals: dict[str, dict[str, int]]) -> None:
    """Write violations.md."""
    lines = ["# UX Canon Violations Census\n\n"]
    lines.append("Generated by `scripts/ux_canon_scan.py`.\n\n")

    # Totals per rule
    lines.append("## Totals per rule\n\n")
    lines.append("| Rule | Count | Weight |\n|---|---|---|\n")
    for rule in sorted(totals["per_rule"], key=lambda r: totals["per_rule"][r], reverse=True):
        lines.append(f"| {rule} | {totals['per_rule'][rule]} | {RULE_WEIGHTS.get(rule, 1)} |\n")
    lines.append("\n")

    # Totals per face
    lines.append("## Totals per face\n\n")
    lines.append("| Face | Hits |\n|---|---|\n")
    for face in sorted(totals["per_face"], key=lambda f: totals["per_face"][f], reverse=True):
        lines.append(f"| {face} | {totals['per_face'][face]} |\n")
    lines.append("\n")

    # Per-face sections
    for face in sorted(per_face):
        violations = per_face[face]
        if not violations:
            continue
        lines.append(f"## {face}\n\n")
        for v in sorted(violations, key=lambda x: (x.rule, x.line)):
            conf = f" [{v.confidence}]" if v.confidence != "high" else ""
            lines.append(f"- **{v.rule}** `{v.file}:{v.line}`{conf} -- {v.text}\n")
        lines.append("\n")

    path.write_text("".join(lines))


def write_violations_json(path: Path, per_face: dict[str, list[Violation]],
                          totals: dict[str, dict[str, int]]) -> None:
    """Write violations.json."""
    data = {
        "totals": totals,
        "faces": {
            face: [v.to_dict() for v in violations]
            for face, violations in sorted(per_face.items())
            if violations
        },
    }
    path.write_text(json.dumps(data, indent=2) + "\n")


def write_ranking_md(path: Path, ranking: list[dict[str, Any]]) -> None:
    """Write ranking.md."""
    lines = ["# Face Ranking by Tuesday Use x Canon Debt\n\n"]
    lines.append("Weights: A1/A3/A4 (raw button, sentence, modal) = 3; ")
    lines.append("A8/A9/DS6 (zero counter, missing egress, accent rail) = 2; ")
    lines.append("all others (B, C, raw-ids, emoji, mic) = 1.\n\n")
    lines.append("Score = tuesday_use x weighted_debt.\n\n")

    lines.append("| Rank | Face | Tuesday | Debt | Score | Hits | Loudest break |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for i, r in enumerate(ranking, 1):
        lines.append(
            f"| {i} | {r['face']} | {r['tuesday_use']} | {r['debt']} "
            f"| {r['score']} | {r['hits']} | {r['loudest_rule']}: {r['loudest_text'][:60]} |\n"
        )
    lines.append("\n")

    path.write_text("".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan HoldSpeak web/src for UX canon violations."
    )
    parser.add_argument("--root", type=Path, default=Path("."),
                        help="Project root (default: cwd)")
    parser.add_argument("--json", type=Path, default=None,
                        help="Output JSON path (default: assets/census/violations.json)")
    parser.add_argument("--md", type=Path, default=None,
                        help="Output MD path (default: assets/census/violations.md)")
    parser.add_argument("--ranking", type=Path, default=None,
                        help="Output ranking MD path")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    if not (root / "web" / "src").is_dir():
        print(f"ERROR: {root / 'web' / 'src'} is not a directory", file=sys.stderr)
        return 1

    per_face, all_violations = scan_all(root)
    totals = build_totals(all_violations)
    ranking = build_ranking(per_face)

    # Default output paths
    census_dir = root / "pm" / "roadmap" / "holdspeak" / "phase-170-the-great-pass" / "assets" / "census"
    md_path = args.md or (census_dir / "violations.md")
    json_path = args.json or (census_dir / "violations.json")
    ranking_path = args.ranking or (census_dir / "ranking.md")

    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    ranking_path.parent.mkdir(parents=True, exist_ok=True)

    write_violations_md(md_path, per_face, totals)
    write_violations_json(json_path, per_face, totals)
    write_ranking_md(ranking_path, ranking)

    print(f"Scanned {len(find_face_files(root))} files, found {len(all_violations)} violations across {len(per_face)} faces.")
    print(f"  violations.md:   {md_path}")
    print(f"  violations.json: {json_path}")
    print(f"  ranking.md:      {ranking_path}")

    # Print summary
    print("\nTotals per rule:")
    for rule in sorted(totals["per_rule"], key=lambda r: totals["per_rule"][r], reverse=True):
        print(f"  {rule}: {totals['per_rule'][rule]}")

    if ranking:
        print(f"\nTop {min(10, len(ranking))} faces:")
        for r in ranking[:10]:
            print(f"  {r['face']:30s}  tuesday={r['tuesday_use']}  debt={r['debt']:3d}  "
                  f"score={r['score']:4d}  loudest={r['loudest_rule']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
