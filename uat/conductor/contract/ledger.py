"""The feature ledger and protocol-v2 target-qualified coverage math.

`uat/features.yaml` lists every shipped capability as a stable key with its
per-surface applicability (`yes|no|unknown`), the holdspeak phases that shipped
it, and its `phase_map` (every phase → covering keys, or `internal/no-uat-surface`).
A scenario cites ledger keys; a debrief computes coverage against them.

Coverage is honest about the three answers a surface cell can hold: `yes`
(applicable — counts toward the denominator), `no` (the surface genuinely lacks
it — excluded), `unknown` (not yet resolved — excluded from the denominator but
counted so a debrief can say how much is still unknown).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .targets import ExecutionSlot, TARGETS

SURFACES = ("web", "ipad", "iphone")
NO_UAT_MARKER = "internal/no-uat-surface"


def ledger_path() -> Path:
    override = os.environ.get("UAT_FEATURES_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "features.yaml"


def target_inventory_path() -> Path:
    override = os.environ.get("UAT_FEATURE_TARGETS_PATH")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3] / "uat" / "feature-targets.yaml"


class LedgerError(ValueError):
    pass


@dataclass
class Feature:
    key: str
    title: str = ""
    domain: str = ""
    phases: list[int] = field(default_factory=list)
    surfaces: dict[str, str] = field(default_factory=dict)
    targets: dict[str, set[str]] = field(default_factory=dict)
    recipes: list[str] = field(default_factory=list)
    priority: str = "unknown"
    status: str = "live"

    def applicable_on(self, surface: str) -> bool:
        return self.surfaces.get(surface) == "yes"

    def applicability_on_slot(self, slot: ExecutionSlot) -> str:
        """Return yes/no/unknown for an exact implementation-qualified slot.

        Web is safely inherited from the old web column because the
        implementation is unambiguous. Native rows require an explicit target
        inventory entry; an old `ipad: yes` alone is not enough to decide which
        Swift binary owns the feature.
        """
        if slot.target in self.targets:
            return "yes" if slot.form_factor in self.targets[slot.target] else "no"
        if slot.target == "web_react":
            return self.surfaces.get("web", "unknown")
        return "unknown"

    @property
    def retired(self) -> bool:
        return self.status == "retired"


@dataclass
class CoverageResult:
    covered: int
    total: int
    uncovered: list[str]

    @property
    def pct(self) -> float:
        return round(100.0 * self.covered / self.total, 1) if self.total else 0.0

    def to_dict(self) -> dict:
        return {
            "covered": self.covered,
            "total": self.total,
            "pct": self.pct,
            "uncovered": self.uncovered,
        }


class FeatureLedger:
    def __init__(self, features: list[Feature], phase_map: dict[str, list[str]], raw: dict | None = None):
        self.features = features
        self._by_key = {f.key: f for f in features}
        self.phase_map = phase_map
        self.raw = raw or {}

    @classmethod
    def load(cls, path: Path | None = None) -> "FeatureLedger":
        path = Path(path) if path else ledger_path()
        if not path.exists():
            raise LedgerError(f"feature ledger not found: {path}")
        doc = yaml.safe_load(path.read_text()) or {}
        inventory = target_inventory_path()
        if inventory.exists():
            target_doc = yaml.safe_load(inventory.read_text()) or {}
            doc = {**doc, "target_inventory": target_doc}
        return cls.from_dict(doc)

    @classmethod
    def from_dict(cls, doc: dict) -> "FeatureLedger":
        """Build a ledger from a sitting's immutable protocol snapshot."""
        features = []
        inventory = (doc.get("target_inventory") or {}).get("features") or {}
        for entry in doc.get("features") or []:
            target_entry = inventory.get(entry["key"], {})
            features.append(
                Feature(
                    key=entry["key"],
                    title=entry.get("title", ""),
                    domain=entry.get("domain", ""),
                    phases=list(entry.get("phases") or []),
                    surfaces={s: str(entry.get("surfaces", {}).get(s, "unknown")) for s in SURFACES},
                    targets={
                        str(target): {str(form) for form in (forms or [])}
                        for target, forms in target_entry.items()
                    },
                    recipes=list(entry.get("recipes") or []),
                    priority=entry.get("priority", "unknown"),
                    status=entry.get("status", "live"),
                )
            )
        return cls(features, doc.get("phase_map") or {}, raw=doc)

    # --- reads ------------------------------------------------------------

    def keys(self) -> set[str]:
        return set(self._by_key)

    def get(self, key: str) -> Feature | None:
        return self._by_key.get(key)

    def has(self, key: str) -> bool:
        return key in self._by_key

    def live(self) -> list[Feature]:
        return [f for f in self.features if not f.retired]

    # --- integrity --------------------------------------------------------

    def validate(self, *, phases_expected: int | None = None) -> list[str]:
        """Structural integrity: unique keys, valid surface cells, phase-exhaustive.

        Returns a list of error strings (empty = clean).
        """
        errors: list[str] = []
        seen: set[str] = set()
        for f in self.features:
            if f.key in seen:
                errors.append(f"duplicate ledger key: {f.key}")
            seen.add(f.key)
            for s in SURFACES:
                if f.surfaces.get(s) not in ("yes", "no", "unknown"):
                    errors.append(f"{f.key}: surface {s} must be yes|no|unknown, got {f.surfaces.get(s)!r}")
            for target, forms in f.targets.items():
                if target not in TARGETS:
                    errors.append(f"{f.key}: unknown target inventory key {target!r}")
                    continue
                allowed = set(TARGETS[target]["form_factors"])
                extra = set(forms) - allowed
                if extra:
                    errors.append(
                        f"{f.key}: invalid form factor(s) for {target}: "
                        f"{', '.join(sorted(extra))}"
                    )
        # Phase exhaustiveness: every phase in the map resolves to keys or the marker.
        for phase, keys in self.phase_map.items():
            if not keys:
                errors.append(f"phase {phase} maps to nothing (needs keys or {NO_UAT_MARKER})")
            for k in keys:
                if k != NO_UAT_MARKER and k not in self._by_key:
                    errors.append(f"phase {phase} cites unknown ledger key: {k}")
        if phases_expected is not None and len(self.phase_map) != phases_expected:
            errors.append(
                f"phase_map has {len(self.phase_map)} phases, expected {phases_expected}"
            )
        return errors

    # --- coverage ---------------------------------------------------------

    def coverage(self, cited_keys: set[str], surface: str) -> CoverageResult:
        """Coverage on one surface: applicable (yes) features cited by the pack."""
        applicable = [f for f in self.live() if f.applicable_on(surface)]
        covered = [f for f in applicable if f.key in cited_keys]
        uncovered = sorted(f.key for f in applicable if f.key not in cited_keys)
        return CoverageResult(len(covered), len(applicable), uncovered)

    def coverage_overall(self, cited_keys: set[str]) -> CoverageResult:
        """Coverage over all live features regardless of surface."""
        live = self.live()
        covered = [f for f in live if f.key in cited_keys]
        uncovered = sorted(f.key for f in live if f.key not in cited_keys)
        return CoverageResult(len(covered), len(live), uncovered)

    def coverage_slot(self, cited_keys: set[str], slot: ExecutionSlot) -> CoverageResult:
        applicable = [
            feature
            for feature in self.live()
            if feature.applicability_on_slot(slot) == "yes"
        ]
        covered = [feature for feature in applicable if feature.key in cited_keys]
        uncovered = sorted(
            feature.key for feature in applicable if feature.key not in cited_keys
        )
        return CoverageResult(len(covered), len(applicable), uncovered)

    def unknown_on_slot(self, slot: ExecutionSlot) -> int:
        return sum(
            feature.applicability_on_slot(slot) == "unknown"
            for feature in self.live()
        )

    def coverage_report(self, cited_keys: set[str]) -> dict[str, Any]:
        report: dict[str, Any] = {"overall": self.coverage_overall(cited_keys).to_dict()}
        for s in SURFACES:
            report[s] = self.coverage(cited_keys, s).to_dict()
        # How much of each surface is still 'unknown' — honest at v1.
        report["unknown_cells"] = {
            s: sum(1 for f in self.live() if f.surfaces.get(s) == "unknown") for s in SURFACES
        }
        return report
