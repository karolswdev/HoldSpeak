"""Seed manifests — desk/context state injected through public routes.

A seed manifest (``uat/seeds/<name>.yaml``) declares desk primitives and meeting
imports. The seeder creates them through the SAME routes the web UI calls, so a
seeded object is indistinguishable from a user-made one. It covers **every desk
primitive type** the product exposes a create route for:

    notes:        # -> POST /api/notes
    kbs:          # knowledge blocks -> POST /api/kbs
    recipes:      # -> POST /api/recipes
    chains:       # -> POST /api/chains
    workflows:    # -> POST /api/workflows
    directories:  # the desk ZONES -> POST /api/directories   (alias: zones:)
    profiles:     # runtime profiles -> POST /api/profiles
    meetings:     # transcript import -> POST /api/meetings/import

Each item is passed through to its route as the JSON body. **Idempotency** is
the contract: every item carries a deterministic ``id`` so re-applying upserts
in place — no duplicate desk. Meetings are guarded by title.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .product_client import ProductClient

# The desk primitive types the seeder can create, in dependency-friendly order
# (containers before members), each mapped to its create route.
PRIMITIVE_ROUTES: dict[str, str] = {
    "directories": "/api/directories",  # the desk "zones"
    "kbs": "/api/kbs",
    "notes": "/api/notes",
    "recipes": "/api/recipes",
    "chains": "/api/chains",
    "workflows": "/api/workflows",
    "profiles": "/api/profiles",
}

# Friendly aliases accepted in a manifest.
_ALIASES = {"zones": "directories", "knowledge_blocks": "kbs"}


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
    primitives: dict[str, list[dict]] = field(default_factory=dict)
    meetings: list[dict] = field(default_factory=list)

    @classmethod
    def from_doc(cls, name: str, doc: dict) -> "SeedManifest":
        prims: dict[str, list[dict]] = {}
        for key, value in doc.items():
            canonical = _ALIASES.get(key, key)
            if canonical in PRIMITIVE_ROUTES:
                prims.setdefault(canonical, [])
                prims[canonical].extend(list(value or []))
        return cls(name=name, primitives=prims, meetings=list(doc.get("meetings") or []))


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
        return SeedManifest.from_doc(name, doc)


@dataclass
class SeedOutcome:
    manifest: str
    applied: dict[str, int] = field(default_factory=dict)
    meetings_imported: int = 0
    meetings_skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def bump(self, ptype: str) -> None:
        self.applied[ptype] = self.applied.get(ptype, 0) + 1

    def to_dict(self) -> dict:
        return {
            "manifest": self.manifest,
            "applied": self.applied,
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
        for ptype, route in PRIMITIVE_ROUTES.items():
            for item in manifest.primitives.get(ptype, []):
                self._apply_primitive(ptype, route, item, out)
        for meeting in manifest.meetings:
            self._apply_meeting(meeting, out)
        return out

    def _apply_primitive(self, ptype: str, route: str, item: Any, out: SeedOutcome) -> None:
        if not isinstance(item, dict):
            out.errors.append(f"{ptype} item is not a mapping: {item!r}")
            return
        if "id" not in item:
            out.errors.append(
                f"{ptype} item missing deterministic id (needed for idempotency): "
                f"{item.get('name', item)!r}"
            )
            return
        # `member_ids` is a filing edge for a zone (directory), not a create
        # field — post it, then file each member separately.
        member_ids = item.get("member_ids") if ptype == "directories" else None
        body = {k: v for k, v in item.items() if not (ptype == "directories" and k == "member_ids")}
        resp = self.client.post_json(route, body)
        if resp.status_code in (200, 201):
            out.bump(ptype)
            for mid in member_ids or []:
                r = self.client.put(f"/api/directories/{item['id']}/members/{mid}")
                if r.status_code not in (200, 201):
                    out.errors.append(f"zone {item['id']} file {mid}: HTTP {r.status_code}")
        else:
            out.errors.append(f"{ptype} {item['id']}: HTTP {resp.status_code} {resp.text[:140]}")

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
        resp = self.client.post_multipart("/api/meetings/import", file_path=path, data=data)
        if resp.status_code in (200, 202):
            out.meetings_imported += 1
        else:
            out.errors.append(
                f"meeting import {title!r}: HTTP {resp.status_code} {resp.text[:160]}"
            )
