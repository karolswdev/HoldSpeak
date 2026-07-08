"""Structural validation and drift warnings for roadmap projects."""

from __future__ import annotations

import re
from pathlib import Path

from .model import (
    DONE_STATUSES,
    EVIDENCE_PLACEHOLDER,
    OPEN_STATUSES,
    Project,
    normalize_status,
    row_is_retired,
)
from .parse import (
    current_phase_status_path,
    discover_phases,
    header_status,
    hook_snapshot,
    link_target,
    parse_current_phase_target,
    parse_story_rows,
    phase_story_files,
    story_num_from_file,
)
from .paths import read_text, rel
from .evidence import CAPTURE_HEADING_RE

_ASSET_REF_RE = re.compile(r"\]\(((?:\./)?assets/[^)]+)\)")
_HEADER_BULLET_RE = re.compile(r"^- \*\*(Story|Status|Date):\*\*")


def _evidence_body_is_empty(text: str) -> bool:
    """True when nothing but scaffold (headings, header bullets) remains."""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if _HEADER_BULLET_RE.match(stripped):
            continue
        return False
    return True


def evidence_content_issues(evidence_path: Path, phase_path: Path, root: Path) -> list[str]:
    """ERROR-level content lints for a done story's evidence file."""
    issues: list[str] = []
    try:
        text = read_text(evidence_path)
    except OSError:
        return [f"{rel(evidence_path, root)}: evidence file could not be read"]
    if EVIDENCE_PLACEHOLDER in text:
        issues.append(f"{rel(evidence_path, root)}: evidence still contains the generator placeholder")
    elif _evidence_body_is_empty(text):
        issues.append(f"{rel(evidence_path, root)}: evidence body is empty (no proof content)")
    for m in _ASSET_REF_RE.finditer(text):
        target = m.group(1)
        if not (phase_path / target).exists():
            issues.append(f"{rel(evidence_path, root)}: broken asset reference: {target}")
    return issues


def project_warnings(project: Project, root: Path) -> list[str]:
    warnings: list[str] = []
    active = []
    uncaptured: list[str] = []
    file_derived: list[str] = []
    for phase in discover_phases(project):
        rows = parse_story_rows(phase.path / "current-phase-status.md")
        covered = {story_num_from_file(row.story_file) for row in rows}
        uncovered = [num for num in phase_story_files(phase.path) if num not in covered]
        if uncovered:
            file_derived.append(f"{phase.path.name} ({len(uncovered)})")
        if any(normalize_status(row.status) in OPEN_STATUSES for row in rows):
            active.append(phase.path.name)
        for row in rows:
            if normalize_status(row.status) not in DONE_STATUSES:
                continue
            target = link_target(row.evidence)
            if not target or target in {"-", "—"}:
                continue
            path = (phase.path / target).resolve()
            if not path.exists():
                continue
            try:
                text = read_text(path)
            except OSError:
                continue
            if not any(CAPTURE_HEADING_RE.match(line) for line in text.splitlines()):
                uncaptured.append(rel(path, root))
    if len(active) > 1:
        warnings.append(f"multiple open phases detected: {', '.join(active)}")
    if uncaptured:
        shown = ", ".join(uncaptured[:8])
        more = f" (+{len(uncaptured) - 8} more)" if len(uncaptured) > 8 else ""
        warnings.append(f"narrative-only evidence (no captured runs): {shown}{more}")
    if file_derived:
        shown = ", ".join(file_derived[:8])
        more = f" (+{len(file_derived) - 8} more)" if len(file_derived) > 8 else ""
        warnings.append(f"story files not in the story table (read file-derived): {shown}{more}")
    snapshot = hook_snapshot(root)
    if snapshot["appears_older_snapshot"]:
        warnings.append("installed pre-commit hook appears older than current Delivery Workbench seams")
    return warnings


def check_project(project: Project, root: Path) -> list[str]:
    issues: list[str] = []
    current_status = current_phase_status_path(project)
    if current_status and not current_status.exists():
        issues.append(f"{rel(project.path / 'README.md', root)}: current phase pointer is stale: {parse_current_phase_target(project)}")

    for phase in discover_phases(project):
        status_file = phase.path / "current-phase-status.md"
        if not status_file.exists():
            issues.append(f"{rel(phase.path, root)}: missing current-phase-status.md")
            continue
        rows = parse_story_rows(status_file)
        # Receipts first (WLA-16-02): a story exists when its FILE
        # exists, whether or not a table row covers it.
        story_files = phase_story_files(phase.path)
        story_nums: set[int] = set(story_files)
        row_nums: set[int] = set()
        done_nums: set[int] = set()
        retired_nums: set[int] = set()
        for row in rows:
            story_target = link_target(row.story_file)
            story_path = (phase.path / story_target).resolve()
            story_num = story_num_from_file(row.story_file)
            row_status = normalize_status(row.status)
            retired = row_is_retired(row)
            if story_num is not None:
                story_nums.add(story_num)
                row_nums.add(story_num)
                if retired:
                    retired_nums.add(story_num)
                elif row_status in DONE_STATUSES:
                    done_nums.add(story_num)
            if retired:
                # Retired history makes no file or evidence demands.
                continue
            if not story_path.exists():
                issues.append(f"{status_file.relative_to(root)}: broken story link for {row.story_id}: {story_target}")
                continue
            status = header_status(story_path)
            if status and normalize_status(status) != row_status:
                issues.append(
                    f"{story_path.relative_to(root)}: header status {status!r} differs from phase table {row.status!r}"
                )
            if row_status in DONE_STATUSES:
                evidence_file: Path | None = None
                default_evidence = (
                    phase.path / f"evidence-story-{story_num:02d}.md"
                    if story_num is not None
                    else None
                )
                evidence_target = link_target(row.evidence)
                if "](" in row.evidence:
                    evidence_path = (phase.path / evidence_target).resolve()
                    if not evidence_path.exists():
                        issues.append(f"{status_file.relative_to(root)}: broken evidence link for {row.story_id}: {evidence_target}")
                    else:
                        evidence_file = evidence_path
                elif default_evidence is not None and default_evidence.exists():
                    # Empty cell, dash, or a legacy prose cell — the
                    # receipt on disk is what proves the story.
                    evidence_file = default_evidence
                elif row.evidence in {"-", "—", ""}:
                    issues.append(f"{status_file.relative_to(root)}: done story {row.story_id} has no evidence link")
                else:
                    issues.append(f"{status_file.relative_to(root)}: broken evidence link for {row.story_id}: {evidence_target}")
                if evidence_file is not None:
                    issues.extend(evidence_content_issues(evidence_file, phase.path, root))
        # A story file no row covers vouches for itself via its header.
        for num, path in story_files.items():
            if num not in row_nums and normalize_status(header_status(path)) in DONE_STATUSES:
                done_nums.add(num)
        for evidence in sorted(phase.path.glob("evidence-story-*.md")):
            m = re.match(r"^evidence-story-(\d+)\.md$", evidence.name)
            if not m:
                continue
            ev_num = int(m.group(1))
            if ev_num not in story_nums:
                issues.append(f"{rel(evidence, root)}: orphan evidence has no matching story row")
            elif ev_num not in done_nums and ev_num not in retired_nums:
                issues.append(f"{rel(evidence, root)}: evidence exists but matching story is not done")
        live_rows = [row for row in rows if not row_is_retired(row)]
        if (
            live_rows
            and all(normalize_status(row.status) in DONE_STATUSES for row in live_rows)
            and not (phase.path / "final-summary.md").exists()
        ):
            issues.append(f"{rel(phase.path, root)}: all stories are done but final-summary.md is missing")
    return issues

# ── structured health classification (WLA-5-04) ──────────────────────
#
# `check_project` / `project_warnings` speak in human strings; the
# workbench health console needs structure. Classification is by the
# exact phrases those functions emit — a unit test guards the coupling.

_ISSUE_KINDS = [
    ("current phase pointer is stale", "stale-pointer", "project"),
    ("missing current-phase-status.md", "missing-status-file", "phase"),
    ("all stories are done but final-summary.md is missing", "missing-final-summary", "phase"),
    ("broken story link", "broken-story-link", "story-evidence"),
    ("header status", "status-mismatch", "story-evidence"),
    ("has no evidence link", "missing-evidence-link", "story-evidence"),
    ("broken evidence link", "broken-evidence-link", "story-evidence"),
    ("missing evidence-story", "missing-evidence-file", "story-evidence"),
    ("orphan evidence has no matching story row", "orphan-evidence", "story-evidence"),
    ("evidence exists but matching story is not done", "premature-evidence", "story-evidence"),
    ("generator placeholder", "placeholder-evidence", "story-evidence"),
    ("evidence body is empty", "empty-evidence", "story-evidence"),
    ("broken asset reference", "broken-asset", "story-evidence"),
    ("could not be read", "unreadable-evidence", "story-evidence"),
]

_WARNING_KINDS = [
    ("multiple open phases detected", "multiple-open-phases", "phase"),
    ("narrative-only evidence", "narrative-only-evidence", "story-evidence"),
    ("story files not in the story table", "file-derived-stories", "phase"),
    ("appears older than current Delivery Workbench seams", "older-hook-snapshot", "hook-runtime"),
]

_EXPLANATIONS = {
    "stale-pointer": "The project README's Current phase link targets a file that does not exist; repoint it at the real current phase.",
    "multiple-open-phases": "More than one phase has open stories; agents cannot tell which phase is current. Close or re-sequence.",
    "older-hook-snapshot": "The installed pre-commit hook predates current framework seams; run update.sh (never edit hooks in place).",
    "broken-story-link": "The phase story table links a story file that does not exist on disk.",
    "broken-evidence-link": "The phase story table links an evidence file that does not exist on disk.",
    "status-mismatch": "The story header and the phase table disagree about the status; fix with dw story status.",
    "orphan-evidence": "An evidence file exists with no matching story row.",
    "premature-evidence": "Evidence exists but its story is not done; flip the story or remove the file.",
    "narrative-only-evidence": "Done stories whose evidence has no captured run; legal but unverifiable — prefer dw evidence capture.",
    "file-derived-stories": "Story files exist that no story-table row covers; readers derive them from the files. Add rows to make the table authoritative.",
}


def _classify(text: str, table: list[tuple[str, str, str]], default_kind: str) -> dict[str, str]:
    kind, category = default_kind, "project"
    for needle, k, c in table:
        if needle in text:
            kind, category = k, c
            break
    path, _, message = text.partition(": ")
    if not message:
        path, message = "", text
    entry = {
        "kind": kind,
        "category": category,
        "path": path,
        "message": message or text,
        "text": text,
    }
    if kind in _EXPLANATIONS:
        entry["explanation"] = _EXPLANATIONS[kind]
    if kind == "multiple-open-phases":
        _, _, folders = text.partition(": ")
        entry["phase_folders"] = [f.strip() for f in folders.split(",") if f.strip()]
    return entry


def classify_issue(text: str) -> dict[str, str]:
    entry = _classify(text, _ISSUE_KINDS, "other-issue")
    entry["severity"] = "error"
    return entry


def classify_warning(text: str) -> dict[str, str]:
    entry = _classify(text, _WARNING_KINDS, "other-warning")
    entry["severity"] = "warning"
    return entry


def hook_seam_explanations(snapshot: dict[str, object]) -> list[str]:
    notes: list[str] = []
    if not snapshot.get("pre_commit_exists"):
        notes.append("no .githooks/pre-commit installed — the commit gate is not active in this clone")
        return notes
    if not snapshot.get("has_config_seam"):
        notes.append("pre-commit lacks the pre-commit.config seam (project variable overrides will be ignored)")
    if not snapshot.get("has_local_seam"):
        notes.append("pre-commit lacks the pre-commit.local seam (project-specific rules will not run)")
    if not snapshot.get("has_work_log_capture"):
        notes.append("pre-commit lacks work-log capture (consented commits will not produce log entries)")
    if notes:
        notes.append("run update.sh against this repo to refresh the framework-owned hooks")
    return notes


def health_report(root: Path, projects: list[Project]) -> dict[str, object]:
    """Structured drift/validation snapshot for the health console."""
    from .gitio import config_value
    from .paths import work_log_root
    from .parse import hook_snapshot

    project_entries = []
    check_lines: list[str] = []
    for project in projects:
        issues = [classify_issue(i) for i in check_project(project, root)]
        warnings = [classify_warning(w) for w in project_warnings(project, root)]
        check_lines.extend(f"ERROR {i['text']}" for i in issues)
        project_entries.append(
            {
                "slug": project.slug,
                "issues": issues,
                "warnings": warnings,
                "mutation_safe": not issues,
            }
        )
    snapshot = hook_snapshot(root)
    return {
        "projects": project_entries,
        "total_issues": sum(len(p["issues"]) for p in project_entries),
        "total_warnings": sum(len(p["warnings"]) for p in project_entries),
        "mutation_safe": all(p["mutation_safe"] for p in project_entries),
        "hook_snapshot": snapshot,
        "hook_explanations": hook_seam_explanations(snapshot),
        "work_log_config": {
            "enabled": (config_value(root, "PMO_WORK_LOG_ENABLED") or "0"),
            "dir": str(work_log_root(root)),
            "project_slug": config_value(root, "PMO_WORK_LOG_PROJECT_SLUG") or "(inferred)",
            "exclude_regex": config_value(root, "PMO_WORK_LOG_EXCLUDE_REGEX") or "(none)",
        },
        "check_output": "\n".join(check_lines) if check_lines else "dw check: ok",
    }
