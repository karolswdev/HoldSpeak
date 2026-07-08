"""Mutation planning and guarded application.

Every mutation is a two-step primitive:

1. ``plan_*`` builds a :class:`MutationPlan` — pure reads, all refusal
   checks, no writes. The plan records each target's current content as
   a fingerprint.
2. ``apply_plan`` re-verifies the fingerprints (stale targets are
   refused before any write), writes atomically with rollback, and
   returns the changed files plus post-apply validation issues.

``preview_plan`` renders a plan as a JSON-safe dict without touching
disk. The CLI builds and applies in one breath; the workbench's
preview -> diff -> apply -> revalidate flow uses the same primitives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .model import DONE_STATUSES, STORY_RE, STORY_STATUSES, Phase, Project, die


_SLUG_RE_STRICT = __import__("re").compile(r"^[a-z0-9][a-z0-9-]*$")


def validate_slug(slug: str) -> str:
    """User-supplied slugs must stay in the slugify alphabet — a slug is
    a filename fragment, never a path."""
    if not _SLUG_RE_STRICT.match(slug):
        die(f"invalid slug {slug!r}: lowercase letters, digits, and hyphens only")
    return slug


def validate_story_status(status: str) -> str:
    status = status.strip().lower()
    if status not in STORY_STATUSES:
        allowed = ", ".join(sorted(STORY_STATUSES))
        die(f"unknown story status {status!r}; allowed: {allowed}")
    return status
from .parse import find_story, get_project, parse_story_rows
from .paths import ensure_under, read_text, rel, roadmap_dir, slugify, write_text
from .render import (
    evidence_link_for,
    render_evidence,
    render_final_summary,
    render_phase_template,
    render_story_template,
    replace_phase_index_content,
    replace_story_table_content,
    update_phase_index_status_content,
    update_story_header_status_content,
    update_story_table_row_content,
)
from .validate import check_project


@dataclass
class FileChange:
    path: Path
    new_content: str
    existed: bool
    old_content: str | None


@dataclass
class MutationPlan:
    kind: str
    root: Path
    project_slug: str
    changes: list[FileChange] = field(default_factory=list)
    create_dirs: list[Path] = field(default_factory=list)
    summary: dict[str, object] = field(default_factory=dict)


def write_changes(root: Path, changes: dict[Path, str], create_dirs: list[Path] | None = None) -> None:
    """Write a small PMO change set and restore originals if a later write fails."""
    allowed = roadmap_dir(root)
    normalized: dict[Path, str] = {}
    originals: dict[Path, str | None] = {}
    for path, content in changes.items():
        ensure_under(path, allowed)
        if path.exists() and path.is_dir():
            die(f"refusing to overwrite directory: {path}")
        normalized[path] = content
        originals[path] = read_text(path) if path.exists() else None

    created_dirs: list[Path] = []
    try:
        for directory in create_dirs or []:
            ensure_under(directory, allowed)
            if directory.exists() and not directory.is_dir():
                die(f"refusing to create directory over file: {directory}")
            if not directory.exists():
                directory.mkdir(parents=True)
                created_dirs.append(directory)
        for path, content in normalized.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            write_text(path, content)
    except Exception:
        for path, original in originals.items():
            try:
                if original is None:
                    if path.exists():
                        path.unlink()
                else:
                    write_text(path, original)
            except OSError:
                pass
        for directory in reversed(created_dirs):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise


def _change(path: Path, new_content: str) -> FileChange:
    existed = path.exists()
    return FileChange(
        path=path,
        new_content=new_content,
        existed=existed,
        old_content=read_text(path) if existed else None,
    )


def plan_fingerprint(plan: MutationPlan) -> str:
    """Deterministic digest over the plan's inputs and outputs.

    Binds the previewed intent to the exact before/after content of
    every target, so an apply can refuse a preview that no longer
    matches the working tree (WLA-5-07 consumes this).
    """
    import hashlib

    h = hashlib.sha256()
    h.update(plan.kind.encode("utf-8"))
    h.update(plan.project_slug.encode("utf-8"))
    for change in sorted(plan.changes, key=lambda c: str(c.path)):
        h.update(rel(change.path, plan.root).encode("utf-8"))
        h.update(b"1" if change.existed else b"0")
        h.update((change.old_content or "").encode("utf-8"))
        h.update(change.new_content.encode("utf-8"))
    return f"sha256:{h.hexdigest()}"


def preview_plan(plan: MutationPlan, include_content: bool = False, include_diff: bool = False) -> dict[str, object]:
    """Render a plan without writing anything."""
    import difflib

    files = []
    for change in plan.changes:
        entry = {
            "path": rel(change.path, plan.root),
            "action": "update" if change.existed else "create",
            "changed": change.new_content != (change.old_content or ""),
            "bytes_before": len(change.old_content.encode("utf-8")) if change.old_content is not None else 0,
            "bytes_after": len(change.new_content.encode("utf-8")),
        }
        if include_content:
            entry["new_content"] = change.new_content
        if include_diff:
            entry["diff"] = "\n".join(
                difflib.unified_diff(
                    (change.old_content or "").splitlines(),
                    change.new_content.splitlines(),
                    fromfile=f"a/{entry['path']}",
                    tofile=f"b/{entry['path']}",
                    lineterm="",
                )
            )
        files.append(entry)
    return {
        "kind": plan.kind,
        "project": plan.project_slug,
        "fingerprint": plan_fingerprint(plan),
        "no_op": all(not f["changed"] for f in files),
        "create_dirs": [rel(d, plan.root) for d in plan.create_dirs],
        "files": files,
        "summary": plan.summary,
    }


def projected_issues(plan: MutationPlan) -> list[str] | None:
    """Validation issues the project would have after applying the plan.

    Mirrors the project's roadmap directory into a scratch root,
    overlays the planned contents, and runs the same validator. Returns
    None when projection is not feasible (never blocks a preview).
    """
    import shutil
    import tempfile

    try:
        project = get_project(plan.root, plan.project_slug)
        scratch = Path(tempfile.mkdtemp(prefix="dw-projection.")).resolve()
        try:
            mirror_project_dir = scratch / rel(project.path, plan.root)
            shutil.copytree(project.path, mirror_project_dir)
            for directory in plan.create_dirs:
                (scratch / rel(directory, plan.root)).mkdir(parents=True, exist_ok=True)
            for change in plan.changes:
                target = scratch / rel(change.path, plan.root)
                target.parent.mkdir(parents=True, exist_ok=True)
                write_text(target, change.new_content)
            mirrored = get_project(scratch, plan.project_slug)
            return check_project(mirrored, scratch)
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    except Exception:
        return None


def apply_plan(plan: MutationPlan, validate_after: bool = True) -> dict[str, object]:
    """Verify fingerprints, write with rollback, revalidate."""
    for change in plan.changes:
        exists_now = change.path.exists()
        if exists_now != change.existed:
            die(f"stale mutation target (existence changed since plan): {rel(change.path, plan.root)}")
        if change.existed and read_text(change.path) != (change.old_content or ""):
            die(f"stale mutation target (content changed since plan): {rel(change.path, plan.root)}")

    write_changes(
        plan.root,
        {change.path: change.new_content for change in plan.changes},
        create_dirs=plan.create_dirs or None,
    )

    issues: list[str] = []
    if validate_after:
        project = get_project(plan.root, plan.project_slug)
        issues = check_project(project, plan.root)

    from .events import emit

    summary = plan.summary or {}
    if plan.kind == "story-status":
        emit(
            plan.root, "story_status", project=plan.project_slug,
            story=summary.get("story_id"),
            detail={"from": summary.get("previous_status"), "to": summary.get("status")},
        )
    elif plan.kind == "story-create":
        emit(
            plan.root, "story_status", project=plan.project_slug,
            story=summary.get("story_id"),
            detail={"from": None, "to": summary.get("status", "backlog")},
        )
    elif plan.kind == "phase-create":
        emit(plan.root, "phase_created", project=plan.project_slug,
             detail={"phase": summary.get("phase_number")})
    elif plan.kind == "phase-close":
        emit(plan.root, "phase_closed", project=plan.project_slug,
             detail={"phase": summary.get("phase_number")})

    return {
        "kind": plan.kind,
        "project": plan.project_slug,
        "changed": [rel(change.path, plan.root) for change in plan.changes],
        "created_dirs": [rel(d, plan.root) for d in plan.create_dirs],
        "summary": plan.summary,
        "issues": issues,
    }


def plan_story_status(
    root: Path,
    project: Project,
    phase: Phase,
    story_selector: str,
    status: str,
    evidence_body: str = "",
    force: bool = False,
) -> MutationPlan:
    status = validate_story_status(status)
    row, story_num, story_path = find_story(project, phase, story_selector)
    status_file = phase.path / "current-phase-status.md"
    evidence_path = phase.path / f"evidence-story-{story_num:02d}.md"
    if status in DONE_STATUSES and not evidence_path.exists() and not evidence_body:
        die("refusing to mark story done without evidence; pass --evidence-body or --evidence-from-file")
    if evidence_path.exists() and evidence_body and not force:
        die(f"evidence already exists; pass --force to replace: {rel(evidence_path, root)}")

    evidence_link = evidence_link_for(story_num) if (evidence_body or status in DONE_STATUSES) else None
    plan = MutationPlan(kind="story-status", root=root, project_slug=project.slug)
    plan.changes.append(_change(story_path, update_story_header_status_content(story_path, status)))
    plan.changes.append(
        _change(status_file, update_story_table_row_content(status_file, row.story_id, status=status, evidence=evidence_link))
    )
    if evidence_body:
        plan.changes.append(_change(evidence_path, render_evidence(row, story_num, evidence_body)))
    plan.summary = {
        "story_id": row.story_id,
        "status": status,
        "previous_status": row.status,
        "story_path": rel(story_path, root),
        "evidence_path": rel(evidence_path, root),
    }
    return plan


def plan_story_evidence(
    root: Path,
    project: Project,
    phase: Phase,
    story_selector: str,
    body: str = "",
    force: bool = False,
) -> MutationPlan:
    row, story_num, _story_path = find_story(project, phase, story_selector)
    evidence_path = phase.path / f"evidence-story-{story_num:02d}.md"
    status_file = phase.path / "current-phase-status.md"
    if evidence_path.exists() and body and not force:
        die(f"evidence already exists; pass --force to replace: {rel(evidence_path, root)}")
    plan = MutationPlan(kind="story-evidence", root=root, project_slug=project.slug)
    plan.changes.append(
        _change(status_file, update_story_table_row_content(status_file, row.story_id, evidence=evidence_link_for(story_num)))
    )
    if body or not evidence_path.exists():
        plan.changes.append(_change(evidence_path, render_evidence(row, story_num, body)))
    plan.summary = {
        "story_id": row.story_id,
        "evidence_path": rel(evidence_path, root),
    }
    return plan


def plan_phase_create(
    root: Path,
    project: Project,
    number: int,
    title: str,
    slug: str | None = None,
    status: str = "not-started",
    goal: str | None = None,
) -> MutationPlan:
    slug = validate_slug(slug) if slug else slugify(title)
    phase_dir = project.path / f"phase-{number}-{slug}"
    ensure_under(phase_dir, roadmap_dir(root))
    if phase_dir.exists():
        die(f"phase directory already exists: {phase_dir}")
    goal = goal or f"Deliver {title}."
    row = f"| {number} | {goal} | {status} | [{phase_dir.name}](./{phase_dir.name}/) |"
    readme = project.path / "README.md"
    plan = MutationPlan(kind="phase-create", root=root, project_slug=project.slug)
    plan.create_dirs = [phase_dir]
    plan.changes.append(_change(phase_dir / "current-phase-status.md", render_phase_template(project, number, title, goal)))
    plan.changes.append(_change(readme, replace_phase_index_content(readme, row, number)))
    plan.summary = {
        "phase_number": number,
        "phase_dir": rel(phase_dir, root),
    }
    return plan


def plan_story_create(
    root: Path,
    project: Project,
    phase: Phase,
    title: str,
    slug: str | None = None,
    status: str = "backlog",
) -> MutationPlan:
    status = validate_story_status(status)
    if slug:
        slug = validate_slug(slug)
    existing = []
    for story in phase.path.glob("story-*.md"):
        m = STORY_RE.match(story.name)
        if m:
            existing.append(int(m.group(1)))
    number = max(existing, default=0) + 1
    slug = slug or slugify(title)
    story_file = phase.path / f"story-{number:02d}-{slug}.md"
    ensure_under(story_file, roadmap_dir(root))
    if story_file.exists():
        die(f"story file already exists: {story_file}")
    story_id = f"{project.prefix}-{phase.number}-{number:02d}"
    row = f"| {story_id} | {title} | {status} | [{story_file.stem}](./{story_file.name}) | - |"
    status_file = phase.path / "current-phase-status.md"
    plan = MutationPlan(kind="story-create", root=root, project_slug=project.slug)
    plan.changes.append(_change(story_file, render_story_template(project, phase, number, title, status)))
    plan.changes.append(_change(status_file, replace_story_table_content(status_file, row)))
    plan.summary = {
        "story_id": story_id,
        "story_path": rel(story_file, root),
    }
    return plan


def plan_phase_close(
    root: Path,
    project: Project,
    phase: Phase,
    summary_body: str = "",
    status: str = "done",
    force: bool = False,
) -> MutationPlan:
    status = status.strip().lower()
    rows = parse_story_rows(phase.path / "current-phase-status.md")
    open_rows = [row for row in rows if row.status not in DONE_STATUSES]
    if open_rows and not force:
        ids = ", ".join(row.story_id for row in open_rows)
        die(f"refusing to close phase with non-done stories: {ids}")
    summary_path = phase.path / "final-summary.md"
    ensure_under(summary_path, roadmap_dir(root))
    if summary_path.exists() and not force:
        die(f"final summary already exists; pass --force to replace: {rel(summary_path, root)}")
    summary_body = summary_body.strip()
    if not summary_body:
        summary_body = "Phase closed by `dw phase close`; see story evidence files for proof."
    readme = project.path / "README.md"
    plan = MutationPlan(kind="phase-close", root=root, project_slug=project.slug)
    plan.changes.append(_change(summary_path, render_final_summary(phase, summary_body)))
    plan.changes.append(_change(readme, update_phase_index_status_content(readme, phase.number, status)))
    plan.summary = {
        "phase_number": phase.number,
        "summary_path": rel(summary_path, root),
        "status": status,
    }
    return plan
