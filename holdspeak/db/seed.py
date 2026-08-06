"""The architect's desk seed + reset-to-seed (HS-112-03).

The product-side sibling of the UAT seed rig (``uat/conductor/induction/
seeds.py`` — the proven pattern, deliberately not imported: the quarantine
runs both ways). The manifest ships inside the package
(``holdspeak/seeds/fresh-desk.yaml``); this module applies it through the
same repositories the primitive routes wrap, so a seeded object is
indistinguishable from a user-made one.

Idempotency is the contract: every item carries a deterministic
``hs-desk-*`` id, so re-applying upserts in place — never a duplicate desk.
Nothing here runs at boot; the seed is an explicit act (CLI verb, route,
or the reset).

Reset TOMBSTONES, never purges: ``/api/sync/pull`` ships
``include_deleted=True`` so tombstones propagate last-write-wins to paired
devices — a hard purge would simply be resurrected by the next push.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from ..config import CONFIG_FILE, Config

if TYPE_CHECKING:  # pragma: no cover
    from .core import Database

SEEDS_DIR = Path(__file__).resolve().parent.parent / "seeds"
DEFAULT_SEED = "fresh-desk"

# Manifest sections in dependency order (containers before members), each
# mapped to the membership ref kind (`kind:id`, the filing wire contract).
_SECTION_KINDS: dict[str, str] = {
    "directories": "zone",
    "kbs": "knowledge",
    "notes": "note",
    "recipes": "persona",
    "chains": "sequence",
    "workflows": "workflow",
}


class SeedError(ValueError):
    pass


@dataclass
class SeedReport:
    manifest: str
    applied: dict[str, int] = field(default_factory=dict)
    profiles_seeded: int = 0
    profiles_adopted: dict[str, str] = field(default_factory=dict)
    workbenches_seeded: int = 0
    filed: int = 0

    @property
    def total(self) -> int:
        return self.profiles_seeded + self.workbenches_seeded + sum(self.applied.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest": self.manifest,
            "applied": dict(self.applied),
            "profiles_seeded": self.profiles_seeded,
            "profiles_adopted": dict(self.profiles_adopted),
            "workbenches_seeded": self.workbenches_seeded,
            "filed": self.filed,
            "total": self.total,
        }


@dataclass
class ResetReport:
    tombstoned: dict[str, int] = field(default_factory=dict)
    seed: SeedReport | None = None

    @property
    def tombstoned_total(self) -> int:
        return sum(self.tombstoned.values())

    def to_dict(self) -> dict[str, Any]:
        return {
            "tombstoned": dict(self.tombstoned),
            "tombstoned_total": self.tombstoned_total,
            "seed": self.seed.to_dict() if self.seed else None,
        }


def load_manifest(name: str = DEFAULT_SEED) -> dict[str, Any]:
    path = SEEDS_DIR / f"{name}.yaml"
    if not path.exists():
        raise SeedError(f"unknown packaged seed: {name!r} (looked in {SEEDS_DIR})")
    doc = yaml.safe_load(path.read_text()) or {}
    if not isinstance(doc, dict):
        raise SeedError(f"seed {name!r} must be a mapping")
    return doc


def apply_seed(
    db: "Database", name: str = DEFAULT_SEED, *, adopt: bool = True
) -> SeedReport:
    """Upsert the packaged seed into repositories (idempotent by id)."""
    manifest = load_manifest(name)
    report = SeedReport(manifest=name)

    first_profile_id: str | None = None
    for item in manifest.get("profiles") or []:
        if not isinstance(item, dict) or not str(item.get("id") or "").strip():
            raise SeedError(
                "profiles item missing deterministic id "
                f"(the idempotency contract): {item!r}"
            )
        profile_id = str(item["id"]).strip()
        db.profiles.upsert(
            profile_id=profile_id,
            name=str(item.get("name") or ""),
            kind=str(item.get("kind") or "onDevice"),
            model_file=str(item.get("model_file") or ""),
            base_url=str(item.get("base_url") or ""),
            model=str(item.get("model") or ""),
            node=str(item.get("node") or ""),
            context_limit=int(item.get("context_limit") or 16384),
            requires_key=bool(item.get("requires_key", False)),
        )
        report.profiles_seeded += 1
        if first_profile_id is None:
            first_profile_id = profile_id

    if adopt and first_profile_id:
        report.profiles_adopted = _adopt_profiles(first_profile_id)

    for item in manifest.get("workbenches") or []:
        if not isinstance(item, dict) or not str(item.get("id") or "").strip():
            raise SeedError(
                "workbenches item missing deterministic id "
                f"(the idempotency contract): {item!r}"
            )
        wb_id = str(item["id"]).strip()
        db.workbenches.upsert(
            workbench_id=wb_id,
            name=str(item.get("name") or ""),
            recipe_id=item.get("recipe_id") or None,
            profile_id=item.get("profile_id") or None,
            resolver_profile_id=item.get("resolver_profile_id") or None,
        )
        report.workbenches_seeded += 1

    # Deterministic id -> qualified membership ref, derived from the section
    # each item is declared in (the UAT rig's same refs contract).
    refs: dict[str, str] = {
        str(item["id"]): f"{kind}:{item['id']}"
        for section, kind in _SECTION_KINDS.items()
        for item in manifest.get(section) or []
        if isinstance(item, dict) and item.get("id")
    }

    filings: list[tuple[str, str]] = []  # (qualified member ref, directory id)
    for section in _SECTION_KINDS:
        for item in manifest.get(section) or []:
            if not isinstance(item, dict) or not str(item.get("id") or "").strip():
                raise SeedError(
                    f"{section} item missing deterministic id "
                    f"(the idempotency contract): {item!r}"
                )
            _apply_item(db, section, item)
            report.applied[section] = report.applied.get(section, 0) + 1
            if section == "directories":
                for mid in item.get("member_ids") or []:
                    ref = str(mid) if ":" in str(mid) else refs.get(str(mid), "")
                    if not ref:
                        raise SeedError(
                            f"zone {item['id']} files unknown member: {mid!r}"
                        )
                    filings.append((ref, str(item["id"])))

    for ref, directory_id in filings:
        db.directory_memberships.upsert(primitive_id=ref, directory_id=directory_id)
        report.filed += 1
    return report


def _adopt_profiles(profile_id: str) -> dict[str, str]:
    """Adopt a seeded profile only where the owner has no selection yet."""
    config = Config.load(CONFIG_FILE)
    adopted: dict[str, str] = {}
    if config.dictation.runtime.profile_id is None:
        config.dictation.runtime.profile_id = profile_id
        adopted["dictation.runtime.profile_id"] = profile_id
    if config.meeting.intel_profile_id is None:
        config.meeting.intel_profile_id = profile_id
        adopted["meeting.intel_profile_id"] = profile_id
    if adopted:
        config.save(CONFIG_FILE)
    return adopted


def _apply_item(db: "Database", section: str, item: dict[str, Any]) -> None:
    item_id = str(item["id"]).strip()
    if section == "directories":
        db.directories.upsert(
            directory_id=item_id,
            name=str(item.get("name") or ""),
            parent_id=item.get("parent_id") or None,
        )
    elif section == "notes":
        db.notes.upsert(
            note_id=item_id,
            title=str(item.get("title") or ""),
            body_markdown=str(item.get("body_markdown") or ""),
            tags=[str(tag) for tag in item.get("tags") or []],
        )
    elif section == "kbs":
        db.kbs.upsert(kb_id=item_id, name=str(item.get("name") or ""))
    elif section == "recipes":
        db.recipes.upsert(
            recipe_id=item_id,
            name=str(item.get("name") or ""),
            role=str(item.get("role") or ""),
            system_prompt=str(item.get("system_prompt") or ""),
            user_template=str(item.get("user_template") or ""),
        )
    elif section == "chains":
        db.chains.upsert(
            chain_id=item_id,
            name=str(item.get("name") or ""),
            steps=[str(step) for step in item.get("steps") or []],
        )
    elif section == "workflows":
        db.workflows.upsert(
            workflow_id=item_id,
            name=str(item.get("name") or ""),
            prompt=str(item.get("prompt") or ""),
            graph_json=item.get("graph_json") or None,
        )
    else:  # pragma: no cover — _SECTION_KINDS is the closed roster
        raise SeedError(f"unknown seed section: {section}")


def reset_desk(db: "Database", name: str = DEFAULT_SEED) -> ResetReport:
    """Tombstone every live desk primitive, then re-apply the packaged seed.

    Repository ``.delete()`` only (tombstone; the sync contract above).
    What survives, by design: the meetings archive, the dictation journal,
    settings/config, and profiles — none are desk primitives.
    """
    report = ResetReport()
    sweeps = [
        ("notes", db.notes),
        ("kbs", db.kbs),
        ("recipes", db.recipes),
        ("chains", db.chains),
        ("workflows", db.workflows),
        ("workbenches", db.workbenches),
    ]
    for label, repo in sweeps:
        count = 0
        for record in repo.list(limit=2000):
            if repo.delete(record.id):
                count += 1
        report.tombstoned[label] = count

    count = 0
    for membership in db.directory_memberships.list(limit=5000):
        if db.directory_memberships.delete(membership.primitive_id):
            count += 1
    report.tombstoned["directory_memberships"] = count

    # Directories last: their delete also tombstones remaining memberships
    # and re-roots child zones, so nothing strands.
    count = 0
    for directory in db.directories.list(limit=2000):
        if db.directories.delete(directory.id):
            count += 1
    report.tombstoned["directories"] = count

    report.seed = apply_seed(db, name)
    return report
