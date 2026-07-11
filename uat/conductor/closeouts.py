"""Fail-closed acceptance closeouts over independently generated debriefs.

A closeout is a read model. It scans debrief JSON, selects the newest required
campaign packet for the repository's exact clean commit, and checks the current
scenario contract. It never writes evidence, mutates a sitting, or changes PM
state. Old packets cannot be silently combined across product revisions.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import paths
from .contract.scenarios import Scenario, ScenarioError, load_pack


class CloseoutError(ValueError):
    pass


def closeouts_dir() -> Path:
    override = os.environ.get("UAT_CLOSEOUTS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return paths.repo_root() / "uat" / "closeouts"


@dataclass(frozen=True)
class MetricPolicy:
    key: str
    operator: str
    threshold: float | None = None


@dataclass(frozen=True)
class CampaignRequirement:
    pack: str
    required_slots: tuple[str, ...]
    require_paired_device_attestations: bool = False
    device_attestation_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepositoryRequirement:
    id: str
    path: str
    exists: bool = True
    line_prefix: str | None = None
    contains: str | None = None


@dataclass(frozen=True)
class CloseoutSpec:
    id: str
    title: str
    description: str
    campaigns: tuple[CampaignRequirement, ...]
    metric_policies: dict[str, MetricPolicy]
    repository_requirements: tuple[RepositoryRequirement, ...] = ()
    allowed_acceptance_statuses: tuple[str, ...] = ("passed",)
    allowed_verdicts: tuple[str, ...] = ("pass",)
    allowed_finding_triage: tuple[str, ...] = ()
    source: str = ""

    @classmethod
    def load(cls, closeout_id: str) -> "CloseoutSpec":
        if not closeout_id or any(
            ch not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for ch in closeout_id
        ):
            raise CloseoutError("closeout id contains unsupported characters")
        path = closeouts_dir() / f"{closeout_id}.yaml"
        if not path.exists():
            raise KeyError(closeout_id)
        try:
            doc = yaml.safe_load(path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise CloseoutError(f"ERROR {path}: invalid YAML: {exc}") from exc
        try:
            schema = int(doc.get("schema") or 0) if isinstance(doc, dict) else 0
        except (TypeError, ValueError):
            schema = 0
        if not isinstance(doc, dict) or schema != 1:
            raise CloseoutError(f"ERROR {path}: closeout schema must be 1")
        if str(doc.get("id") or "") != closeout_id:
            raise CloseoutError(f"ERROR {path}: id must be {closeout_id!r}")

        raw_campaigns = doc.get("campaigns")
        if not isinstance(raw_campaigns, list) or not raw_campaigns:
            raise CloseoutError(f"ERROR {path}: campaigns must be a non-empty list")
        campaigns: list[CampaignRequirement] = []
        for index, raw in enumerate(raw_campaigns):
            if not isinstance(raw, dict):
                raise CloseoutError(f"ERROR {path}: campaign {index} must be a mapping")
            pack = str(raw.get("pack") or "").strip()
            slots = tuple(
                str(item).strip() for item in (raw.get("required_slots") or [])
            )
            if not pack or not slots or any(not slot for slot in slots):
                raise CloseoutError(
                    f"ERROR {path}: campaign {index} needs pack and required_slots"
                )
            if len(slots) != len(set(slots)):
                raise CloseoutError(
                    f"ERROR {path}: campaign {pack!r} repeats a required slot"
                )
            campaigns.append(
                CampaignRequirement(
                    pack=pack,
                    required_slots=slots,
                    require_paired_device_attestations=bool(
                        raw.get("require_paired_device_attestations")
                    ),
                    device_attestation_fields=tuple(
                        str(item)
                        for item in (raw.get("device_attestation_fields") or [])
                    ),
                )
            )
        packs = [item.pack for item in campaigns]
        if len(packs) != len(set(packs)):
            raise CloseoutError(f"ERROR {path}: campaign packs must be unique")

        raw_policies = doc.get("metric_policies")
        if not isinstance(raw_policies, dict) or not raw_policies:
            raise CloseoutError(
                f"ERROR {path}: metric_policies must be a non-empty mapping"
            )
        policies: dict[str, MetricPolicy] = {}
        for key, raw in raw_policies.items():
            if not isinstance(raw, dict):
                raise CloseoutError(f"ERROR {path}: metric {key!r} must be a mapping")
            operator = str(raw.get("operator") or "").strip()
            if operator not in {"present", "eq", "lte", "gte"}:
                raise CloseoutError(
                    f"ERROR {path}: metric {key!r} has invalid operator"
                )
            threshold = raw.get("threshold")
            if operator != "present" and not _is_number(threshold):
                raise CloseoutError(
                    f"ERROR {path}: metric {key!r} needs a numeric threshold"
                )
            policies[str(key)] = MetricPolicy(
                key=str(key),
                operator=operator,
                threshold=float(threshold) if threshold is not None else None,
            )

        repository_requirements: list[RepositoryRequirement] = []
        for index, raw in enumerate(doc.get("repository_requirements") or []):
            if not isinstance(raw, dict):
                raise CloseoutError(
                    f"ERROR {path}: repository requirement {index} must be a mapping"
                )
            requirement_id = str(raw.get("id") or "").strip()
            requirement_path = str(raw.get("path") or "").strip()
            if (
                not requirement_id
                or not requirement_path
                or Path(requirement_path).is_absolute()
            ):
                raise CloseoutError(
                    f"ERROR {path}: repository requirement {index} needs an id and relative path"
                )
            repository_requirements.append(
                RepositoryRequirement(
                    id=requirement_id,
                    path=requirement_path,
                    exists=bool(raw.get("exists", True)),
                    line_prefix=(
                        str(raw["line_prefix"])
                        if raw.get("line_prefix") is not None
                        else None
                    ),
                    contains=(
                        str(raw["contains"])
                        if raw.get("contains") is not None
                        else None
                    ),
                )
            )
        requirement_ids = [item.id for item in repository_requirements]
        if len(requirement_ids) != len(set(requirement_ids)):
            raise CloseoutError(
                f"ERROR {path}: repository requirement ids must be unique"
            )

        spec = cls(
            id=closeout_id,
            title=str(doc.get("title") or closeout_id),
            description=str(doc.get("description") or ""),
            campaigns=tuple(campaigns),
            metric_policies=policies,
            repository_requirements=tuple(repository_requirements),
            allowed_acceptance_statuses=tuple(
                str(item)
                for item in (doc.get("allowed_acceptance_statuses") or ["passed"])
            ),
            allowed_verdicts=tuple(
                str(item) for item in (doc.get("allowed_verdicts") or ["pass"])
            ),
            allowed_finding_triage=tuple(
                str(item) for item in (doc.get("allowed_finding_triage") or [])
            ),
            source=str(path),
        )
        spec.validate_contract()
        return spec

    def validate_contract(self) -> None:
        valid_verdicts = {"pass", "fail", "partial", "observe", "skip"}
        if not self.allowed_verdicts or not set(self.allowed_verdicts).issubset(
            valid_verdicts
        ):
            raise CloseoutError(
                f"ERROR {self.source}: allowed_verdicts contains an unknown verdict"
            )
        valid_acceptance = {
            "passed",
            "passed-with-observations",
            "failed",
            "inconclusive",
            "in-progress",
            "invalid-protocol",
        }
        if not self.allowed_acceptance_statuses or not set(
            self.allowed_acceptance_statuses
        ).issubset(valid_acceptance):
            raise CloseoutError(
                f"ERROR {self.source}: allowed_acceptance_statuses contains an unknown state"
            )
        valid_triage = {"untriaged", "fix", "wont-fix", "by-design", "duplicate"}
        if not set(self.allowed_finding_triage).issubset(valid_triage):
            raise CloseoutError(
                f"ERROR {self.source}: allowed_finding_triage contains an unknown state"
            )
        prompted: set[str] = set()
        for campaign in self.campaigns:
            try:
                scenarios = load_pack(campaign.pack)
            except ScenarioError as exc:
                raise CloseoutError(
                    f"ERROR {self.source}: cannot load {campaign.pack}: {exc}"
                ) from exc
            actual_slots = {
                slot.id
                for scenario in scenarios
                for step in scenario.steps
                for slot in step.execution_slots(scenario)
            }
            if actual_slots != set(campaign.required_slots):
                raise CloseoutError(
                    f"ERROR {self.source}: {campaign.pack} slots are {sorted(actual_slots)}, "
                    f"not {sorted(campaign.required_slots)}"
                )
            prompted.update(
                prompt.key
                for scenario in scenarios
                for step in scenario.steps
                for prompt in step.measurements
                if prompt.required
            )
        missing = prompted - set(self.metric_policies)
        unused = set(self.metric_policies) - prompted
        if missing or unused:
            raise CloseoutError(
                f"ERROR {self.source}: metric policy drift; missing={sorted(missing)}, "
                f"unused={sorted(unused)}"
            )


@dataclass
class _Report:
    spec: CloseoutSpec
    repository_commit: str | None
    repository_clean: bool | None
    scanned_debriefs: int
    scan_errors: list[dict[str, str]] = field(default_factory=list)
    gaps: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    selected: list[dict[str, Any]] = field(default_factory=list)
    repository_requirements: list[dict[str, Any]] = field(default_factory=list)

    def gap(self, code: str, message: str, **context: Any) -> None:
        item = {"code": code, "message": message, **context}
        if item not in self.gaps:
            self.gaps.append(item)

    def to_dict(self) -> dict[str, Any]:
        ready = not self.gaps
        return {
            "schema": 1,
            "id": self.spec.id,
            "title": self.spec.title,
            "description": self.spec.description,
            "ready": ready,
            "status": "ready" if ready else "blocked",
            "repository": {
                "commit": self.repository_commit,
                "clean": self.repository_clean,
                "requirements": self.repository_requirements,
            },
            "selected_debriefs": self.selected,
            "metrics": self.metrics,
            "gaps": self.gaps,
            "scanned_debriefs": self.scanned_debriefs,
            "scan_errors": self.scan_errors,
            "policy_source": self.spec.source,
            "side_effects": "none; this report does not create evidence or change delivery state",
        }


class CloseoutEvaluator:
    def __init__(self, *, repo: Path | None = None, runs: Path | None = None):
        self.repo = Path(repo) if repo else paths.repo_root()
        self.runs = Path(runs) if runs else paths.runs_root()

    def list(self) -> list[dict[str, str]]:
        out = []
        for path in sorted(closeouts_dir().glob("*.yaml")):
            spec = CloseoutSpec.load(path.stem)
            out.append(
                {"id": spec.id, "title": spec.title, "description": spec.description}
            )
        return out

    def evaluate(self, closeout_id: str) -> dict[str, Any]:
        spec = CloseoutSpec.load(closeout_id)
        commit, clean = _repository_state(self.repo)
        packets, errors = self._scan_packets()
        return evaluate_packets(
            spec,
            packets,
            repository_commit=commit,
            repository_clean=clean,
            repository_requirement_results=_repository_requirements(spec, self.repo),
            scan_errors=errors,
        )

    def _scan_packets(self) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
        packets: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        if not self.runs.exists():
            return packets, errors
        for path in sorted(self.runs.glob("*/debrief/debrief.json")):
            try:
                packet = json.loads(path.read_text())
                if not isinstance(packet, dict):
                    raise ValueError("top level is not an object")
                packet = dict(packet)
                packet["_closeout_path"] = str(path)
                packets.append(packet)
            except (OSError, ValueError) as exc:
                errors.append({"path": str(path), "error": str(exc)})
        return packets, errors


def evaluate_packets(
    spec: CloseoutSpec,
    packets: list[dict[str, Any]],
    *,
    repository_commit: str | None,
    repository_clean: bool | None,
    repository_requirement_results: dict[str, dict[str, Any]] | None = None,
    scan_errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Pure closeout evaluation, also used by tests and external tooling."""
    report = _Report(
        spec=spec,
        repository_commit=repository_commit,
        repository_clean=repository_clean,
        scanned_debriefs=len(packets),
        scan_errors=scan_errors or [],
    )
    if not repository_commit:
        report.gap(
            "repository-commit-unavailable",
            "The repository commit could not be resolved.",
        )
    if repository_clean is not True:
        report.gap(
            "repository-not-clean",
            "Closeout requires a clean worktree so exercised bytes equal the named commit.",
        )
    requirement_results = repository_requirement_results or {}
    for requirement in spec.repository_requirements:
        result = requirement_results.get(requirement.id)
        if result is None:
            result = {
                "id": requirement.id,
                "path": requirement.path,
                "passed": False,
                "detail": "requirement was not evaluated",
            }
        report.repository_requirements.append(result)
        if not result.get("passed"):
            report.gap(
                "repository-prerequisite",
                f"Repository prerequisite {requirement.id!r} is not satisfied.",
                requirement=requirement.id,
                path=requirement.path,
                detail=result.get("detail"),
            )

    for requirement in spec.campaigns:
        matching = [
            packet
            for packet in packets
            if _mapping(packet.get("header")).get("pack") == requirement.pack
            and _mapping(packet.get("header")).get("git_commit") == repository_commit
        ]
        if not matching:
            commits = sorted(
                {
                    str(_mapping(packet.get("header")).get("git_commit") or "(missing)")
                    for packet in packets
                    if _mapping(packet.get("header")).get("pack") == requirement.pack
                }
            )
            report.gap(
                "campaign-debrief-missing",
                f"No {requirement.pack} debrief exists for the repository commit.",
                campaign=requirement.pack,
                available_commits=commits,
            )
            continue
        packet = max(
            matching,
            key=lambda item: str(
                _mapping(item.get("header")).get("generated_at") or ""
            ),
        )
        header = _mapping(packet.get("header"))
        report.selected.append(
            {
                "campaign": requirement.pack,
                "run_id": header.get("run_id"),
                "sitting_id": header.get("sitting_id"),
                "git_commit": header.get("git_commit"),
                "generated_at": header.get("generated_at"),
                "path": packet.get("_closeout_path"),
            }
        )
        _evaluate_campaign(report, requirement, packet)
    return report.to_dict()


def _evaluate_campaign(
    report: _Report, requirement: CampaignRequirement, packet: dict[str, Any]
) -> None:
    pack = requirement.pack
    header = _mapping(packet.get("header"))
    if packet.get("complete") is not True:
        report.gap(
            "campaign-incomplete", "The selected sitting is incomplete.", campaign=pack
        )
    if packet.get("acceptance_status") not in report.spec.allowed_acceptance_statuses:
        report.gap(
            "acceptance-status",
            f"Acceptance status {packet.get('acceptance_status')!r} is not closeable.",
            campaign=pack,
        )
    try:
        protocol_schema = int(header.get("protocol_schema") or 0)
    except (TypeError, ValueError):
        protocol_schema = 0
    if header.get("protocol_valid") is not True or protocol_schema < 2:
        report.gap(
            "invalid-protocol",
            "The debrief does not carry valid protocol-v2 identity.",
            campaign=pack,
        )
    if not str(header.get("protocol_hash") or "").strip():
        report.gap(
            "protocol-hash-missing",
            "The debrief has no immutable protocol hash.",
            campaign=pack,
        )

    expected_slots = set(requirement.required_slots)
    raw_sat_slots = header.get("execution_slots_sat")
    sat_slots = (
        {item for item in raw_sat_slots if isinstance(item, str)}
        if isinstance(raw_sat_slots, list)
        else set()
    )
    if not isinstance(raw_sat_slots, list) or len(sat_slots) != len(raw_sat_slots):
        report.gap(
            "packet-schema",
            "The execution_slots_sat field is not a list of slot strings.",
            campaign=pack,
        )
    if sat_slots != expected_slots:
        report.gap(
            "execution-slot-mismatch",
            "The exact required execution slots were not independently sat.",
            campaign=pack,
            expected=sorted(expected_slots),
            actual=sorted(sat_slots),
        )

    scenarios = load_pack(pack)
    expected: dict[tuple[str, int, str], tuple[Scenario, Any]] = {}
    for scenario in scenarios:
        for step in scenario.steps:
            for slot in step.execution_slots(scenario):
                expected[(scenario.id, step.index, slot.id)] = (scenario, step)
    actual: dict[tuple[str, int, str], dict[str, Any]] = {}
    duplicates: set[tuple[str, int, str]] = set()
    verdicts, verdict_shape_valid = _mapping_list(packet.get("verdicts"))
    if not verdict_shape_valid:
        report.gap(
            "packet-schema",
            "The debrief verdicts field is not a list of objects.",
            campaign=pack,
        )
    for verdict in verdicts:
        try:
            step_index = int(
                verdict.get("step_index")
                if verdict.get("step_index") is not None
                else -1
            )
        except (TypeError, ValueError):
            report.gap(
                "packet-schema", "A verdict has an invalid step index.", campaign=pack
            )
            continue
        key = (
            str(verdict.get("scenario_id") or ""),
            step_index,
            str(verdict.get("slot_id") or ""),
        )
        if key in actual:
            duplicates.add(key)
        actual[key] = verdict
    if duplicates:
        report.gap(
            "duplicate-verdicts",
            "The debrief contains duplicate verdict cells.",
            campaign=pack,
        )
    missing = set(expected) - set(actual)
    extra = set(actual) - set(expected)
    for scenario_id, step_index, slot_id in sorted(missing):
        report.gap(
            "verdict-missing",
            "A required scenario step has no exact-slot verdict.",
            campaign=pack,
            scenario=scenario_id,
            step_index=step_index,
            slot=slot_id,
        )
    if extra:
        report.gap(
            "unexpected-verdicts",
            "The debrief contains verdicts outside the current campaign contract.",
            campaign=pack,
            count=len(extra),
        )

    for key, (scenario, step) in expected.items():
        verdict = actual.get(key)
        if verdict is None:
            continue
        scenario_id, step_index, slot_id = key
        if verdict.get("verdict") not in report.spec.allowed_verdicts:
            report.gap(
                "verdict-not-closeable",
                f"Verdict {verdict.get('verdict')!r} cannot satisfy closeout.",
                campaign=pack,
                scenario=scenario_id,
                step_index=step_index,
                slot=slot_id,
            )
        measurements = _mapping(verdict.get("measurements"))
        for prompt in step.measurements:
            if not prompt.required:
                continue
            policy = report.spec.metric_policies[prompt.key]
            value = measurements.get(prompt.key)
            passed, normalized = _metric_passes(policy, value)
            metric = {
                "campaign": pack,
                "scenario": scenario.id,
                "step_index": step.index,
                "slot": slot_id,
                "key": prompt.key,
                "value": _safe_value(value),
                "operator": policy.operator,
                "threshold": policy.threshold,
                "passed": passed,
            }
            report.metrics.append(metric)
            if not passed:
                report.gap(
                    "metric-threshold",
                    f"Required metric {prompt.key!r} is missing, invalid, or outside policy.",
                    **{
                        k: metric[k]
                        for k in (
                            "campaign",
                            "scenario",
                            "step_index",
                            "slot",
                            "key",
                            "value",
                            "operator",
                            "threshold",
                        )
                    },
                    normalized_value=normalized,
                )

    required_features = {
        feature for scenario in scenarios for feature in scenario.features
    }
    coverage = _mapping(packet.get("coverage"))
    raw_covered = coverage.get("cited_features")
    covered = (
        {item for item in raw_covered if isinstance(item, str)}
        if isinstance(raw_covered, list)
        else set()
    )
    if not required_features.issubset(covered):
        report.gap(
            "journey-coverage",
            "Executed coverage does not credit every required journey.",
            campaign=pack,
            missing=sorted(required_features - covered),
        )

    findings, finding_shape_valid = _mapping_list(packet.get("findings"))
    if not finding_shape_valid:
        report.gap(
            "packet-schema",
            "The debrief findings field is not a list of objects.",
            campaign=pack,
        )
    for finding in findings:
        triage = str(finding.get("triage_state") or "untriaged")
        disposition = str(finding.get("disposition") or "").strip()
        if triage not in report.spec.allowed_finding_triage or not disposition:
            report.gap(
                "finding-unresolved",
                "Every observation must have a closeable triage state and disposition.",
                campaign=pack,
                finding_id=finding.get("id"),
                triage_state=triage,
            )

    if requirement.require_paired_device_attestations:
        sessions, session_shape_valid = _mapping_list(packet.get("device_sessions"))
        if not session_shape_valid:
            report.gap(
                "packet-schema",
                "The debrief device_sessions field is not a list of objects.",
                campaign=pack,
            )
        for slot in requirement.required_slots:
            target, form_factor = slot.split(":", 1)
            matches = [
                item
                for item in sessions
                if item.get("execution_target") == target
                and item.get("form_factor") == form_factor
                and item.get("pairing_verified") in (True, 1)
            ]
            complete_matches = [
                item
                for item in matches
                if all(
                    str(item.get(field) or "").strip()
                    for field in requirement.device_attestation_fields
                )
            ]
            if not complete_matches:
                report.gap(
                    "device-attestation-missing",
                    "Physical native evidence needs a matching pairing-verified device attestation.",
                    campaign=pack,
                    slot=slot,
                    required_fields=list(requirement.device_attestation_fields),
                )


def _metric_passes(policy: MetricPolicy, value: Any) -> tuple[bool, float | None]:
    if policy.operator == "present":
        if value is None or isinstance(value, bool):
            return False, None
        if isinstance(value, str) and not value.strip():
            return False, None
        number = _number(value)
        return number is not None, number
    number = _number(value)
    if number is None or policy.threshold is None:
        return False, number
    if policy.operator == "eq":
        return math.isclose(number, policy.threshold, rel_tol=0.0, abs_tol=1e-9), number
    if policy.operator == "lte":
        return number <= policy.threshold, number
    return number >= policy.threshold, number


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _is_number(value: Any) -> bool:
    return _number(value) is not None


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _mapping_list(value: Any) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(value, list):
        return [], False
    return [item for item in value if isinstance(item, dict)], all(
        isinstance(item, dict) for item in value
    )


def _safe_value(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def _repository_state(repo: Path) -> tuple[str | None, bool | None]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
        return commit or None, not bool(status.strip())
    except (OSError, subprocess.SubprocessError):
        return None, None


def _repository_requirements(
    spec: CloseoutSpec, repo: Path
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    root = repo.resolve()
    for requirement in spec.repository_requirements:
        candidate = (root / requirement.path).resolve()
        if candidate != root and root not in candidate.parents:
            results[requirement.id] = {
                "id": requirement.id,
                "path": requirement.path,
                "passed": False,
                "detail": "path escapes repository root",
            }
            continue
        exists = candidate.exists()
        passed = exists if requirement.exists else not exists
        detail = "present" if exists else "missing"
        if passed and (
            requirement.line_prefix is not None or requirement.contains is not None
        ):
            try:
                content = candidate.read_text()
            except OSError as exc:
                content = ""
                detail = str(exc)
                passed = False
            inspected = content
            if passed and requirement.line_prefix is not None:
                matching = next(
                    (
                        line
                        for line in content.splitlines()
                        if line.startswith(requirement.line_prefix)
                    ),
                    None,
                )
                passed = matching is not None
                detail = matching or f"no line starts with {requirement.line_prefix!r}"
                inspected = matching or ""
            if passed and requirement.contains is not None:
                passed = requirement.contains in inspected
                if not passed:
                    scope = "matched line" if requirement.line_prefix else "file"
                    detail = f"{scope} does not contain {requirement.contains!r}"
        results[requirement.id] = {
            "id": requirement.id,
            "path": requirement.path,
            "passed": passed,
            "detail": detail,
        }
    return results
