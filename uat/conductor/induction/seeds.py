"""Seed manifests — desk/context state injected through public routes.

A seed manifest (``uat/seeds/<name>.yaml``) describes notes, KBs, and
meeting imports. The seeder applies them through the SAME routes the web UI
calls (``POST /api/notes``, ``POST /api/kbs``, ``POST /api/meetings/import``)
so a seeded object is indistinguishable from a user-made one.

**Idempotency** is the contract. Notes and KBs carry a deterministic ``id``,
so re-applying upserts in place — no duplicate desks. Meeting imports are
guarded by title: if a meeting with the seed's title already exists, the
import is skipped (re-importing the same transcript would otherwise dedup or
duplicate).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .product_client import ProductClient


def seeds_dir() -> Path:
    override = os.environ.get("UAT_SEEDS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "seeds"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


class SeedError(ValueError):
    pass


@dataclass
class SeedManifest:
    name: str
    notes: list[dict] = field(default_factory=list)
    kbs: list[dict] = field(default_factory=list)
    meetings: list[dict] = field(default_factory=list)


class SeedRegistry:
    def __init__(self, directory: Path | None = None):
        self.directory = Path(directory) if directory else seeds_dir()

    def names(self) -> list[str]:
        if not self.directory.exists():
            return []
        return sorted(p.stem for p in self.directory.glob("*.yaml"))

    def load(self, name: str) -> SeedManifest:
        path = self.directory / f"{name}.yaml"
        if not path.exists():
            raise SeedError(f"unknown seed manifest: {name!r} (looked in {self.directory})")
        doc = yaml.safe_load(path.read_text()) or {}
        if not isinstance(doc, dict):
            raise SeedError(f"seed {name!r} must be a mapping")
        return SeedManifest(
            name=name,
            notes=list(doc.get("notes") or []),
            kbs=list(doc.get("kbs") or []),
            meetings=list(doc.get("meetings") or []),
        )


@dataclass
class SeedOutcome:
    manifest: str
    notes_applied: int = 0
    kbs_applied: int = 0
    meetings_imported: int = 0
    meetings_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "manifest": self.manifest,
            "notes_applied": self.notes_applied,
            "kbs_applied": self.kbs_applied,
            "meetings_imported": self.meetings_imported,
            "meetings_skipped": self.meetings_skipped,
            "errors": self.errors,
        }


class Seeder:
    """Applies a seed manifest to one booted run over HTTP."""

    def __init__(self, client: ProductClient):
        self.client = client

    def apply(self, manifest: SeedManifest) -> SeedOutcome:
        out = SeedOutcome(manifest=manifest.name)

        for note in manifest.notes:
            if "id" not in note:
                out.errors.append(f"note missing deterministic id: {note.get('title')!r}")
                continue
            resp = self.client.post_json(
                "/api/notes",
                {
                    "id": note["id"],
                    "title": note.get("title", ""),
                    "body_markdown": note.get("body_markdown", ""),
                    "tags": note.get("tags", []),
                },
            )
            if resp.status_code in (200, 201):
                out.notes_applied += 1
            else:
                out.errors.append(f"note {note['id']}: HTTP {resp.status_code} {resp.text[:120]}")

        for kb in manifest.kbs:
            if "id" not in kb:
                out.errors.append(f"kb missing deterministic id: {kb.get('name')!r}")
                continue
            resp = self.client.post_json(
                "/api/kbs",
                {
                    "id": kb["id"],
                    "name": kb.get("name", ""),
                    "member_ids": kb.get("member_ids", []),
                },
            )
            if resp.status_code in (200, 201):
                out.kbs_applied += 1
            else:
                out.errors.append(f"kb {kb['id']}: HTTP {resp.status_code} {resp.text[:120]}")

        for meeting in manifest.meetings:
            self._apply_meeting(meeting, out)

        return out

    def _existing_titles(self) -> set[str]:
        try:
            data = self.client.get_json("/api/meetings", params={"limit": 200})
            return {m.get("title") for m in data.get("meetings", [])}
        except Exception:
            return set()

    def _apply_meeting(self, meeting: dict, out: SeedOutcome) -> None:
        transcript = meeting.get("transcript")
        if not transcript:
            out.errors.append("meeting seed missing 'transcript' path")
            return
        title = meeting.get("title") or Path(transcript).stem
        if title in self._existing_titles():
            out.meetings_skipped += 1
            return
        path = repo_root() / transcript
        if not path.exists():
            out.errors.append(f"transcript not found: {transcript}")
            return
        data: dict[str, Any] = {"title": title}
        if meeting.get("tags"):
            data["tags"] = ",".join(meeting["tags"])
        if meeting.get("speaker"):
            data["speaker"] = meeting["speaker"]
        if meeting.get("started_at_ms"):
            data["started_at_ms"] = meeting["started_at_ms"]
        resp = self.client.post_multipart(
            "/api/meetings/import", file_path=path, data=data
        )
        if resp.status_code in (200, 202):
            out.meetings_imported += 1
        else:
            out.errors.append(
                f"meeting import {title!r}: HTTP {resp.status_code} {resp.text[:160]}"
            )
