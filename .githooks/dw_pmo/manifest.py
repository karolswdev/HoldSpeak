"""Evidence manifests and manifest-bound asset streaming (HS-94-01).

``dw evidence manifest <project> <story> --json`` names every file
that proves one story — the story file, its evidence file(s), the
phase status table, the phase's final summary when closed, and the
phase's ``assets/`` files — each with size, MIME type, and sha256,
plus the captured runs parsed out of the evidence Markdown.

The manifest is the SOLE path authority: ``dw evidence asset``
streams bytes only for a member the manifest itself names, so a
consumer can never turn the CLI into an arbitrary file read.
Refusals are typed (`not_in_manifest`, `symlink`, `oversize`,
`outside_root`, `absent`) on stderr with a nonzero exit.
Versioned independently of ``feed_schema`` (PLATFORM-CONTRACT §5.3).
"""

from __future__ import annotations

import hashlib
import mimetypes
import sys
from pathlib import Path

from .evidence import evidence_path_for, parse_captured_runs
from .gitio import head_sha, write_tree
from .model import DwError, Phase, Project, StoryRow, die
from .parse import discover_phases, discover_projects, find_story, parse_story_rows
from .paths import read_text, rel

EVIDENCE_SCHEMA = 1
MAX_ASSET_BYTES = 16 * 1024 * 1024

# mimetypes is platform-tabled; pin the types the rails themselves
# produce so manifests are stable across machines.
_MEDIA_OVERRIDES = {
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".txt": "text/plain",
    ".log": "text/plain",
}


def _media_type(path: Path) -> str:
    override = _MEDIA_OVERRIDES.get(path.suffix.lower())
    if override:
        return override
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _asset_id(rel_path: str) -> str:
    return "a-" + hashlib.sha256(rel_path.encode("utf-8")).hexdigest()[:16]


def _bundle_id(project_slug: str, story_id: str, tree: str) -> str:
    raw = f"{project_slug}:{story_id}:{tree}".encode("utf-8")
    return "bundle-" + hashlib.sha256(raw).hexdigest()[:16]


def _member(root: Path, path: Path, role: str, label: str) -> dict:
    rel_path = rel(path, root)
    return {
        "asset_id": _asset_id(rel_path),
        "role": role,
        "label": label,
        "path": rel_path,
        "media_type": _media_type(path),
        "bytes": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _locate_story(
    project: Project, story_selector: str
) -> tuple[Phase, StoryRow, int, Path]:
    for phase in discover_phases(project):
        try:
            row, story_num, story_path = find_story(project, phase, story_selector)
        except DwError:
            continue
        return phase, row, story_num, story_path
    die(f"story not found in {project.slug}: {story_selector}")


def _evidence_paths(phase: Phase, story_num: int) -> list[Path]:
    """The canonical evidence file first, plus the other padding when
    a legacy tree carries both."""
    canonical = evidence_path_for(phase, story_num)
    paths = [canonical] if canonical.exists() else []
    for candidate in (
        phase.path / f"evidence-story-{story_num:02d}.md",
        phase.path / f"evidence-story-{story_num}.md",
    ):
        if candidate.exists() and candidate not in paths:
            paths.append(candidate)
    return paths


def build_manifest(root: Path, project: Project, story_selector: str) -> dict:
    phase, row, story_num, story_path = _locate_story(project, story_selector)
    members: list[dict] = []
    trace: dict[str, str | None] = {
        "story_asset_id": None,
        "evidence_asset_id": None,
        "phase_status_asset_id": None,
        "final_summary_asset_id": None,
    }

    if story_path.is_file():
        member = _member(root, story_path, "story_markdown", "Story")
        members.append(member)
        trace["story_asset_id"] = member["asset_id"]

    evidence_text = ""
    for i, evidence_path in enumerate(_evidence_paths(phase, story_num)):
        member = _member(root, evidence_path, "evidence_markdown", "Evidence")
        members.append(member)
        if i == 0:
            trace["evidence_asset_id"] = member["asset_id"]
            evidence_text = read_text(evidence_path)

    status_file = phase.path / "current-phase-status.md"
    if status_file.is_file():
        member = _member(root, status_file, "phase_status", "Phase status")
        members.append(member)
        trace["phase_status_asset_id"] = member["asset_id"]

    final_summary = phase.path / "final-summary.md"
    if final_summary.is_file():
        member = _member(root, final_summary, "final_summary", "Final summary")
        members.append(member)
        trace["final_summary_asset_id"] = member["asset_id"]

    # Assets: regular files only — a symlink is never a member, so it
    # can never be streamed.
    asset_count = 0
    assets_dir = phase.path / "assets"
    if assets_dir.is_dir():
        for path in sorted(assets_dir.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            members.append(_member(root, path, "asset", path.name))
            asset_count += 1

    runs = parse_captured_runs(evidence_text)
    tree = write_tree(root) or "unknown"
    return {
        "evidence_schema": EVIDENCE_SCHEMA,
        "bundle_id": _bundle_id(project.slug, row.story_id, tree),
        "source_revision": {
            "head_sha": head_sha(root),
            "index_tree": tree,
        },
        "project": project.slug,
        "phase": phase.number,
        "story_id": row.story_id,
        "status": row.status,
        "summary": {
            "passing_captures": sum(1 for r in runs if r["exit_code"] == 0),
            "failing_captures": sum(
                1 for r in runs if r["exit_code"] not in (0, None)
            ),
            "assets": asset_count,
        },
        "members": members,
        "captured_runs": runs,
        "trace": trace,
    }


def _manifest_for_ref(root: Path, ref: str) -> dict:
    """Resolve `<bundle-or-story>`: a story selector in any project
    first, then a bundle id (recomputed — bundle ids are derived from
    the story identity and the current index tree, never stored)."""
    for project in discover_projects(root):
        for phase in discover_phases(project):
            try:
                row, _num, _path = find_story(project, phase, ref)
            except DwError:
                continue
            return build_manifest(root, project, row.story_id)
    if ref.startswith("bundle-"):
        tree = write_tree(root) or "unknown"
        for project in discover_projects(root):
            for phase in discover_phases(project):
                for row in parse_story_rows(
                    phase.path / "current-phase-status.md"
                ):
                    if _bundle_id(project.slug, row.story_id, tree) == ref:
                        return build_manifest(root, project, row.story_id)
    die(f"no story or evidence bundle matches {ref!r}")


def _refuse(code: str, detail: str) -> int:
    print(f"dw: evidence asset refused ({code}): {detail}", file=sys.stderr)
    return 1


def stream_asset(root: Path, bundle_or_story: str, asset_ref: str) -> int:
    """Stream one manifest member's bytes to stdout.

    `asset_ref` may be the member's `asset_id` or its manifest-listed
    path — matched exactly against the freshly built manifest, which
    is the sole path authority. Everything else refuses, typed.
    """
    manifest = _manifest_for_ref(root, bundle_or_story)
    member = None
    for candidate in manifest["members"]:
        if asset_ref in (candidate["asset_id"], candidate["path"]):
            member = candidate
            break
    if member is None:
        return _refuse(
            "not_in_manifest",
            f"{asset_ref!r} is not a member of {manifest['bundle_id']}; "
            "the manifest is the sole path authority",
        )
    raw = root / member["path"]
    target = raw.resolve()
    allowed = root.resolve()
    if target != allowed and allowed not in target.parents:
        return _refuse("outside_root", f"{member['path']} escapes the repository")
    if raw.is_symlink() or target.is_symlink():
        return _refuse("symlink", f"{member['path']} is a symlink")
    if not target.is_file():
        return _refuse("absent", f"{member['path']} does not exist")
    size = target.stat().st_size
    if size > MAX_ASSET_BYTES:
        return _refuse(
            "oversize",
            f"{member['path']} is {size} bytes; the ceiling is {MAX_ASSET_BYTES}",
        )
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            sys.stdout.buffer.write(chunk)
    sys.stdout.buffer.flush()
    return 0
