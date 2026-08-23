"""Atomic parent + multi-route bundle and durable Stop-handoff authority.

The kernel operation shell is admitted first by the existing broker boundary.
The parent row, every declared route, and the immutable bundle manifest then
commit in one SQLite transaction.  A synchronous bundle refusal terminalizes
the shell; existing ParentRun startup recovery handles a process-loss orphan as
indeterminate.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Callable
from typing import Any, Mapping, Sequence

from ..kernel.model import KernelRefused
from ..kernel.parent_run import ParentRun
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, ValidationError
from .inference_fallback_controller import INFERENCE_FALLBACK_AUTHORITY
from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()


def _safe(value: Any, *, field: str) -> str:
    clean = str(value or "").strip()
    if not clean or len(clean) > 192 or any(
        character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:-"
        for character in clean
    ):
        raise ValidationError(f"{field} is invalid", code="inference_parent_route_bundle_invalid")
    return clean


def _safe_preload_candidate(value: Any) -> str:
    """Accept a registry-safe ID or a namespaced model repository, never a path."""
    clean = str(value or "").strip()
    if "/" not in clean:
        return _safe(clean, field="preload_candidate_id")
    parts = clean.split("/")
    if len(parts) != 2 or any(_safe(part, field="preload_candidate_id") != part for part in parts):
        raise ValidationError(
            "preload_candidate_id is invalid",
            code="inference_parent_route_bundle_invalid",
        )
    return clean


def _principal_material(principal: Principal) -> dict[str, Any]:
    return {
        "kind": principal.name,
        "identity": principal.identity,
        "authority_basis": principal.authority_basis,
        "allowed_operations": [
            {"name": name, "version": version}
            for name, version in sorted(principal.allowed_operations)
        ],
    }


@dataclass(frozen=True)
class HandoffEvidenceProvider:
    """Conn-only displaced-work evidence callbacks.

    Callbacks may write durable state only through the supplied connection; they
    must not use network, queues, second connections, or non-rollbackable side
    effects. Dispatchers claim activated work only after the enclosing
    transaction commits.
    """

    id: str
    revision: int
    freeze: Callable[[Any, str, Mapping[str, Any]], Mapping[str, Any]]
    reconstruct: Callable[[Any, str], Mapping[str, Any]]
    activate: Callable[[Any, str], Any]


class InferenceParentRouteBundleService:
    """Composition-only bundle and Stop handoff authority.

    Handoff callbacks write only through the supplied connection: no network,
    queue, second-connection, or non-rollbackable side effects. Dispatchers
    claim activated work only after the enclosing transaction commits.
    """

    def __init__(
        self,
        broker: Any,
        adoption: Any,
        *,
        handoff_evidence_providers: Sequence[HandoffEvidenceProvider] = (),
    ) -> None:
        self._broker = broker
        self._db = broker.database
        self._parents = broker.parent_run_controller
        self._adoption = adoption
        self._plans = adoption.plans
        self._controller = adoption.controller
        self._handoff_evidence_providers = {
            provider.id: provider for provider in handoff_evidence_providers
        }
        if len(self._handoff_evidence_providers) != len(handoff_evidence_providers):
            raise ValueError("duplicate handoff evidence provider")
        for provider in handoff_evidence_providers:
            _safe(provider.id, field="handoff_provider_id")
            if (
                provider.revision < 1
                or not callable(provider.freeze)
                or not callable(provider.reconstruct)
                or not callable(provider.activate)
            ):
                raise ValueError("invalid handoff evidence provider")

    def start(
        self,
        principal: Principal,
        *,
        command_id: str,
        parent_kind: str,
        definition_ref: str,
        definition_revision: str,
        input_snapshot: Mapping[str, Any],
        deadline_at: float,
        routes: Sequence[Mapping[str, Any]],
        lifecycle_child_budget: int = 0,
        budget_groups: Sequence[Mapping[str, Any]] | None = None,
        derived_preload: Mapping[str, Any] | None = None,
        requested_remote_device_ids: Sequence[str] = (),
    ) -> dict[str, Any]:
        if principal.kind not in {PrincipalKind.OWNER, PrincipalKind.SERVICE}:
            raise ValidationError(
                "Parent route bundle principal is invalid.",
                code="inference_parent_route_bundle_invalid",
            )
        command = _safe(command_id, field="command_id")
        if not routes or type(lifecycle_child_budget) is not int or lifecycle_child_budget < 0:
            raise ValidationError(
                "Parent route declaration is invalid.",
                code="inference_parent_route_bundle_invalid",
            )
        # Route plans serialize deadlines at microsecond precision; normalize
        # the parent fence to that same exact value before either authority is
        # written so reconstruction never depends on float sub-microseconds.
        deadline = datetime.fromtimestamp(float(deadline_at)).timestamp()
        if deadline <= time.time():
            raise ValidationError(
                "Parent route deadline has elapsed.",
                code="inference_parent_route_bundle_invalid",
            )
        declarations: list[dict[str, str]] = []
        seen_keys: set[str] = set()
        seen_capabilities: set[str] = set()
        for raw in routes:
            if not isinstance(raw, Mapping) or set(raw) != {
                "key",
                "capability_id",
                "invocation_id",
            }:
                raise ValidationError(
                    "Parent route declaration is invalid.",
                    code="inference_parent_route_bundle_invalid",
                )
            item = {
                "key": _safe(raw["key"], field="route_key"),
                "capability_id": _safe(raw["capability_id"], field="capability_id"),
                "invocation_id": _safe(raw["invocation_id"], field="invocation_id"),
            }
            if item["key"] in seen_keys or item["capability_id"] in seen_capabilities:
                raise ValidationError(
                    "Parent route declarations must be unique.",
                    code="inference_parent_route_bundle_invalid",
                )
            seen_keys.add(item["key"])
            seen_capabilities.add(item["capability_id"])
            declarations.append(item)
        derived = self._derived_preload_declaration(derived_preload, declarations)
        if derived is not None:
            declarations.append(derived["declaration"])
        groups = self._budget_groups(budget_groups, declarations)
        remote_devices = self._requested_remote_devices(requested_remote_device_ids)
        if groups and lifecycle_child_budget:
            raise ValidationError(
                "Aggregate bundles do not use a separate lifecycle budget.",
                code="inference_parent_route_bundle_invalid",
            )
        request = {
            "schema": "InferenceParentRouteBundleRequest@1",
            "command_id": command,
            "feature_principal_sha256": _sha256(_principal_material(principal)),
            "parent_kind": str(parent_kind),
            "definition_ref": str(definition_ref),
            "definition_revision": str(definition_revision),
            "input_snapshot_sha256": _sha256(dict(input_snapshot)),
            "deadline_at": deadline,
            "lifecycle_child_budget": lifecycle_child_budget,
            "routes": declarations,
            **({"budget_groups": groups} if groups else {}),
            **({"derived_preload": derived["request"]} if derived is not None else {}),
            **({"requested_remote_device_ids": remote_devices} if remote_devices else {}),
        }
        request_hash = _sha256(request)
        resolved_policy_fingerprints: list[dict[str, Any]] = []
        for declaration in declarations:
            if derived is not None and declaration["key"] == derived["declaration"]["key"]:
                policy = self._plans._registry.retry_policy("retry.internal.lifecycle").canonical_dict()
            else:
                policy = self._plans.resolve_route_plan_for_feature(
                    ROUTE_PLANNING_AUTHORITY,
                    feature_principal=principal,
                    parent_kind=str(parent_kind),
                    capability_id=declaration["capability_id"],
                    invocation_id=declaration["invocation_id"],
                    deadline_at=deadline,
                )["retry_policy"]
            resolved_policy_fingerprints.append(
                {
                    "id": policy["id"],
                    "revision": policy["revision"],
                    "sha256": policy["sha256"],
                    "total_physical_attempts": policy["total_physical_attempts"],
                }
            )
        declared_child_budget = (
            sum(int(group["allocation"]) for group in groups)
            if groups
            else lifecycle_child_budget + sum(
                int(policy["total_physical_attempts"])
                for policy in resolved_policy_fingerprints
            )
        )
        parent = self._parents.start(
            principal,
            kind=str(parent_kind),
            definition_ref=str(definition_ref),
            definition_revision=str(definition_revision),
            input_snapshot=dict(input_snapshot),
            deadline_at=deadline,
            child_budget=declared_child_budget,
            idempotency_key=command,
            _defer_persist=True,
        )
        shell_only = parent.context is None
        try:
            with self._db._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                replay = conn.execute(
                    "SELECT * FROM inference_parent_route_bundles WHERE command_id=?",
                    (command,),
                ).fetchone()
                if replay is not None:
                    if str(replay["request_sha256"]) != request_hash:
                        raise ConflictError(
                            "Parent route bundle command changed.",
                            code="inference_parent_route_bundle_conflict",
                        )
                    bundle = self._bundle_from_row(conn, replay)
                    conn.commit()
                    row = conn.execute(
                        "SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?",
                        (bundle["parent_operation_id"],),
                    ).fetchone()
                    return {
                        "parent": ParentRun(
                            str(row["operation_id"]),
                            str(row["native_id"]),
                            self._parents._context(row),
                            replayed=True,
                        ),
                        "bundle": bundle,
                    }
                members: list[dict[str, Any]] = []
                derived_preloads: list[dict[str, Any]] = []
                child_budget = 0 if groups else lifecycle_child_budget
                routes_by_key: dict[str, dict[str, Any]] = {}
                for ordinal, declaration in enumerate(declarations, 1):
                    if derived is not None and declaration["key"] == derived["declaration"]["key"]:
                        source = routes_by_key[derived["source_key"]]
                        route = self._plans.freeze_derived_preload_for_transcription_in_transaction(
                            ROUTE_PLANNING_AUTHORITY,
                            conn,
                            command_id=f"{command}-route-{ordinal}",
                            feature_principal=principal,
                            parent_kind=str(parent_kind),
                            transcription_route_plan_id=str(source["id"]),
                        )
                    else:
                        route = self._plans.freeze_route_plan_for_feature_in_transaction(
                            ROUTE_PLANNING_AUTHORITY,
                            conn,
                            command_id=f"{command}-route-{ordinal}",
                            feature_principal=principal,
                            parent_kind=str(parent_kind),
                            capability_id=declaration["capability_id"],
                            invocation_id=declaration["invocation_id"],
                            deadline_at=deadline,
                        )
                    routes_by_key[declaration["key"]] = route
                    evidence = conn.execute(
                        "SELECT sha256 FROM inference_route_plan_principal_evidence WHERE plan_id=?",
                        (route["id"],),
                    ).fetchone()
                    if evidence is None:
                        raise ConflictError(
                            "Route principal evidence is missing.",
                            code="inference_parent_route_bundle_integrity_invalid",
                        )
                    frozen_policy = {
                        "id": route["retry_policy"]["id"],
                        "revision": route["retry_policy"]["revision"],
                        "sha256": route["retry_policy"]["sha256"],
                        "total_physical_attempts": route["retry_policy"]["total_physical_attempts"],
                    }
                    if frozen_policy != resolved_policy_fingerprints[ordinal - 1]:
                        raise ConflictError(
                            "Parent route policy changed during admission.",
                            code="inference_parent_route_bundle_integrity_invalid",
                        )
                    attempts = int(route["retry_policy"]["total_physical_attempts"])
                    if not groups:
                        child_budget += attempts
                    member = {
                        "ordinal": ordinal,
                        "key": declaration["key"],
                        "capability_id": declaration["capability_id"],
                        "route_plan_id": route["id"],
                        "route_plan_sha256": route["sha256"],
                        "principal_policy_sha256": str(evidence["sha256"]),
                        "maximum_physical_attempts": attempts,
                    }
                    if derived is not None and declaration["key"] == derived["declaration"]["key"]:
                        source = routes_by_key[derived["source_key"]]
                        derived_preloads.append(
                            self._derived_preload_evidence(conn, derived, source, route)
                        )
                    members.append(member)
                child_budget = declared_child_budget if groups else child_budget
                if child_budget != declared_child_budget:
                    raise ConflictError(
                        "Parent route budget changed during admission.",
                        code="inference_parent_route_bundle_integrity_invalid",
                    )
                now = self._parents._clock()
                row = self._parents._persist_parent(
                    conn,
                    operation_id=parent.operation_id,
                    native_id=parent.native_id,
                    kind=str(parent_kind),
                    definition_ref=str(definition_ref),
                    definition_revision=str(definition_revision),
                    input_snapshot=dict(input_snapshot),
                    deadline_at=deadline,
                    child_budget=child_budget,
                    now=now,
                )
                bundle_id = "iprb_" + hashlib.sha256(
                    f"{command}:{request_hash}".encode()
                ).hexdigest()
                material = {
                    "schema": "InferenceParentRouteBundle@1",
                    "id": bundle_id,
                    "parent_operation_id": parent.operation_id,
                    "parent_kind": str(parent_kind),
                    "parent_deadline_at": deadline,
                    "parent_child_budget": child_budget,
                    "lifecycle_child_budget": lifecycle_child_budget,
                    "feature_principal_sha256": request["feature_principal_sha256"],
                    "members": members,
                    **({"budget_groups": groups} if groups else {}),
                    **({"requested_remote_device_ids": remote_devices} if remote_devices else {}),
                    **({"derived_preloads": derived_preloads} if derived_preloads else {}),
                }
                digest = _sha256(material)
                conn.execute(
                    "INSERT INTO inference_parent_route_bundles VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        bundle_id,
                        command,
                        request_hash,
                        parent.operation_id,
                        deadline,
                        child_budget,
                        lifecycle_child_budget,
                        request["feature_principal_sha256"],
                        _canonical(material),
                        digest,
                        now,
                    ),
                )
                for member in members:
                    conn.execute(
                        "INSERT INTO inference_parent_route_bundle_members VALUES (?,?,?,?,?,?,?,?,?)",
                        (
                            f"{bundle_id}:{member['ordinal']}",
                            bundle_id,
                            member["ordinal"],
                            member["key"],
                            member["capability_id"],
                            member["route_plan_id"],
                            member["route_plan_sha256"],
                            member["principal_policy_sha256"],
                            member["maximum_physical_attempts"],
                        ),
                    )
                conn.commit()
            if row is None:
                raise ConflictError(
                    "Parent route bundle has no parent context.",
                    code="inference_parent_route_bundle_integrity_invalid",
                )
            return {
                "parent": ParentRun(
                    parent.operation_id,
                    str(row["native_id"]),
                    self._parents._context(row),
                ),
                "bundle": {**material, "sha256": digest},
            }
        except Exception:
            if shell_only:
                try:
                    self._broker.receipt(
                        parent.operation_id,
                        "refused",
                        "parent-route-bundle:admission-failed",
                        self._parents._node,
                    )
                except KernelRefused:
                    pass
            raise

    @staticmethod
    def _requested_remote_devices(values: Sequence[str]) -> list[str]:
        if isinstance(values, (str, bytes)):
            raise ValidationError(
                "Requested remote devices are invalid.",
                code="inference_parent_route_bundle_invalid",
            )
        normalized = sorted({_safe(value, field="requested_remote_device_id") for value in values})
        return normalized

    @staticmethod
    def _derived_preload_declaration(
        value: Mapping[str, Any] | None, declarations: Sequence[Mapping[str, str]]
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, Mapping) or set(value) != {
            "key", "source_key", "candidate_material", "strategy_sequence"
        }:
            raise ValidationError(
                "Derived preload declaration is invalid.",
                code="inference_parent_route_bundle_invalid",
            )
        key = _safe(value["key"], field="route_key")
        source_key = _safe(value["source_key"], field="derived_preload_source_key")
        if key == source_key or any(item["key"] == key for item in declarations):
            raise ValidationError(
                "Derived preload declaration is invalid.",
                code="inference_parent_route_bundle_invalid",
            )
        source = next((item for item in declarations if item["key"] == source_key), None)
        if source is None or source["capability_id"] != "speech.transcribe":
            raise ValidationError(
                "Derived preload requires the transcription route.",
                code="inference_parent_route_bundle_invalid",
            )
        candidates = value["candidate_material"]
        strategies = value["strategy_sequence"]
        if (
            not isinstance(candidates, list)
            or not isinstance(strategies, list)
            or not strategies
            or any(
                not isinstance(item, Mapping) or set(item) != {"id", "revision"}
                for item in candidates
            )
            or any(not isinstance(item, str) or not item for item in strategies)
            or len(strategies) != len(set(strategies))
        ):
            raise ValidationError(
                "Derived preload declaration is invalid.",
                code="inference_parent_route_bundle_invalid",
            )
        candidate_material = [
            {
                "id": _safe_preload_candidate(item["id"]),
                "revision": _safe(item["revision"], field="preload_candidate_revision"),
            }
            for item in candidates
        ]
        request = {
            "key": key,
            "source_key": source_key,
            "candidate_material": candidate_material,
            "strategy_sequence": [_safe(item, field="preload_strategy") for item in strategies],
        }
        return {
            "declaration": {
                "key": key,
                "capability_id": "speech.preload",
                "invocation_id": source["invocation_id"],
            },
            "source_key": source_key,
            "request": request,
        }

    @staticmethod
    def _budget_groups(
        values: Sequence[Mapping[str, Any]] | None,
        declarations: Sequence[Mapping[str, str]],
    ) -> list[dict[str, Any]]:
        if values is None:
            return []
        if isinstance(values, (str, bytes)) or not values:
            raise ValidationError(
                "Aggregate budget groups are invalid.",
                code="inference_parent_route_bundle_invalid",
            )
        bound: set[str] = set()
        normalized: list[dict[str, Any]] = []
        for raw in values:
            if not isinstance(raw, Mapping) or set(raw) != {"id", "allocation", "member_keys"}:
                raise ValidationError(
                    "Aggregate budget groups are invalid.",
                    code="inference_parent_route_bundle_invalid",
                )
            identifier = _safe(raw["id"], field="budget_group_id")
            allocation = raw["allocation"]
            keys = raw["member_keys"]
            if (
                type(allocation) is not int
                or allocation < 0
                or not isinstance(keys, list)
                or not keys
                or any(not isinstance(key, str) for key in keys)
            ):
                raise ValidationError(
                    "Aggregate budget groups are invalid.",
                    code="inference_parent_route_bundle_invalid",
                )
            member_keys = sorted(_safe(key, field="route_key") for key in keys)
            if len(member_keys) != len(set(member_keys)) or bound.intersection(member_keys):
                raise ValidationError(
                    "Aggregate budget groups are invalid.",
                    code="inference_parent_route_bundle_invalid",
                )
            bound.update(member_keys)
            normalized.append(
                {"id": identifier, "allocation": allocation, "member_keys": member_keys}
            )
        expected = {item["key"] for item in declarations}
        by_key = {item["key"]: item["capability_id"] for item in declarations}
        if (
            bound != expected
            or len({item["id"] for item in normalized}) != len(normalized)
            or any(
                item["allocation"] == 0
                and any(by_key[key] != "speech.preload" for key in item["member_keys"])
                for item in normalized
            )
        ):
            raise ValidationError(
                "Aggregate budget groups must bind every route exactly once.",
                code="inference_parent_route_bundle_invalid",
            )
        return sorted(normalized, key=lambda item: item["id"])

    @staticmethod
    def _derived_preload_evidence(
        conn: Any, derived: Mapping[str, Any], source: Mapping[str, Any], preload: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Freeze construction material from the selected speech deployment.

        Caller configuration can choose neither a preload candidate nor a model
        after the speech route has frozen.  The closed legacy migration map makes
        the model component recoverable from the frozen artifact identity; the
        language claim is read from the exact frozen profile revision.
        """
        deployment = source["entries"][0]
        deployment_row = conn.execute(
            "SELECT engine,model,artifact_id FROM deployment_revisions WHERE id=?",
            (deployment["deployment_revision_id"],),
        ).fetchone()
        profile_row = conn.execute(
            """SELECT capability_manifest_json FROM model_profile_revisions
                 WHERE profile_id=? AND revision=?""",
            (deployment["profile_id"], deployment["profile_revision"]),
        ).fetchone()
        if deployment_row is None or profile_row is None:
            raise ConflictError(
                "Derived preload deployment is missing.",
                code="inference_parent_route_bundle_integrity_invalid",
            )
        engine = str(deployment_row["engine"])
        model_identity = str(deployment_row["model"] or "")
        artifact = str(deployment_row["artifact_id"] or model_identity)
        prefix = f"builtin-whisper-{engine}-"
        speech_deployment = (
            engine in {"mlx", "faster-whisper"} and model_identity.startswith(prefix)
        )
        model = model_identity.removeprefix(prefix) if speech_deployment else model_identity
        language = "auto"
        if speech_deployment:
            try:
                claims = json.loads(str(profile_row["capability_manifest_json"]))["claims"]
                language = next(
                    str(item).removeprefix("speech_language:")
                    for item in claims
                    if str(item).startswith("speech_language:")
                )
            except (KeyError, TypeError, ValueError, StopIteration) as exc:
                raise ConflictError(
                    "Derived preload language evidence is missing.",
                    code="inference_parent_route_bundle_integrity_invalid",
                ) from exc
        if engine == "mlx" and speech_deployment:
            from ..transcribe import _model_repo_candidates

            candidates = [
                {"id": candidate, "revision": "mlx-candidate-v1"}
                for candidate in _model_repo_candidates(model)
            ]
            strategies = ["model-holder", "silent-audio"]
        elif engine == "faster-whisper" and speech_deployment:
            candidates = [{"id": model_identity, "revision": "legacy-model-config-v1"}]
            strategies = ["constructor"]
        else:
            # Historical fixture/read-only routes can reconstruct their existing
            # non-Whisper transcriber but have no physical preload to derive.
            candidates = []
            strategies = ["constructor"]
        return {
            "schema": "InferenceDerivedPreloadEvidence@1",
            "preload_route_key": derived["declaration"]["key"],
            "preload_route_plan_id": preload["id"],
            "preload_route_plan_sha256": preload["sha256"],
            "transcription_route_key": derived["source_key"],
            "transcription_route_plan_id": source["id"],
            "transcription_route_plan_sha256": source["sha256"],
            "deployment_revision_id": deployment["deployment_revision_id"],
            "engine": engine,
            "model": model,
            "language": language,
            "model_artifact": artifact,
            "candidate_material": candidates,
            "candidate_material_sha256": _sha256(candidates),
            "strategy_sequence": strategies,
        }

    def get(self, bundle_id: str) -> dict[str, Any]:
        with self._db._connection() as conn:
            row = conn.execute(
                "SELECT * FROM inference_parent_route_bundles WHERE id=?",
                (_safe(bundle_id, field="bundle_id"),),
            ).fetchone()
            if row is None:
                raise ValidationError(
                    "Parent route bundle is unknown.",
                    code="inference_parent_route_bundle_unknown",
                )
            return self._bundle_from_row(conn, row)

    def fence_cancel(
        self,
        principal: Principal,
        *,
        command_id: str,
        bundle_id: str,
        in_transaction_effect: Callable[[Any], None] | None = None,
    ) -> dict[str, Any]:
        """Fence a live bundle and commit an optional same-database effect with it.

        Stop's deferred-aftercare upsert is supplied here so either the parent
        fence and row both commit, or neither does.  The callback receives the
        service's ``BEGIN IMMEDIATE`` connection and must issue no transaction
        control of its own.
        """
        command = _safe(command_id, field="command_id")
        bundle_identifier = _safe(bundle_id, field="bundle_id")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute(
                    "SELECT * FROM inference_parent_route_bundles WHERE id=?", (bundle_identifier,)
                ).fetchone()
                if row is None:
                    raise ValidationError(
                        "Parent route bundle is unknown.",
                        code="inference_parent_route_bundle_unknown",
                    )
                bundle = self._bundle_from_row(conn, row)
                parent = conn.execute(
                    """SELECT p.*,o.principal_kind,o.principal_identity
                         FROM kernel_parent_runs p JOIN kernel_operations o
                           ON o.operation_id=p.operation_id
                        WHERE p.operation_id=?""",
                    (bundle["parent_operation_id"],),
                ).fetchone()
                if parent is None or (principal.name, principal.identity) != (
                    str(parent["principal_kind"]), str(parent["principal_identity"])
                ):
                    raise ValidationError(
                        "Parent Stop authority is required.",
                        code="inference_parent_stop_handoff_denied",
                    )
                # A prior Stop can leave the parent fenced or terminal.  Replaying
                # Stop then makes no new reservation, transition, or cancellation
                # request; it is a genuine no-op from durable bundle evidence.
                parent_state = str(parent["state"])
                if parent_state not in {"OPEN", "CANCELLING"}:
                    if in_transaction_effect is not None:
                        in_transaction_effect(conn)
                    conn.commit()
                    return {
                        "schema": "InferenceParentBundleFence@1",
                        "bundle_id": bundle_identifier,
                        "parent_operation_id": str(parent["operation_id"]),
                        "parent_fence": {
                            "schema": "ParentHandoffFence@1",
                            "operation_id": str(parent["operation_id"]),
                            "prior_epoch": int(parent["execution_epoch"]),
                            "post_epoch": int(parent["execution_epoch"]),
                            "state": parent_state,
                        },
                        "route_stops": [],
                        "child_signals": [],
                    }
                stopped: list[dict[str, Any]] = []
                # The first fence owns every still-active execution.  `stopping`
                # rows were already given their exact Stop command, so a replay
                # must not mint another durable command merely to signal them again.
                executions = conn.execute(
                    """SELECT e.id FROM inference_route_executions e
                         JOIN inference_parent_route_bundle_members m
                           ON m.route_plan_id=e.route_plan_id
                        WHERE m.bundle_id=? AND e.state='active'
                        ORDER BY m.ordinal,e.started_at,e.id""",
                    (bundle_identifier,),
                ).fetchall()
                child_invocations: list[tuple[str, str]] = []
                for ordinal, execution in enumerate(executions, 1):
                    stopped_result = self._controller.request_stop_in_transaction(
                        INFERENCE_FALLBACK_AUTHORITY,
                        conn,
                        command_id=f"{command}-route-{ordinal}",
                        execution_id=str(execution["id"]),
                    )
                    stopped.append(stopped_result["effect"])
                    if str(stopped_result["execution"]["state"]) == "stopping":
                        child = conn.execute(
                            """SELECT child_invocation_id FROM inference_route_attempts
                               WHERE execution_id=? AND state='dispatch_intent'
                               ORDER BY physical_attempt_ordinal DESC LIMIT 1""",
                            (str(execution["id"]),),
                        ).fetchone()
                        if child is not None and str(child["child_invocation_id"] or ""):
                            child_invocations.append(
                                (str(execution["id"]), str(child["child_invocation_id"]))
                            )
                fence = self._parents.fence_for_handoff_in_transaction(
                    conn, principal, operation_id=str(parent["operation_id"])
                )
                if in_transaction_effect is not None:
                    in_transaction_effect(conn)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        # Durable Stop/fence commits before this best-effort physical signal.  The
        # controller has already sealed every affected execution, so a cancellation
        # failure cannot reopen admission or permit a late winner to publish.
        child_signals: list[dict[str, str]] = []
        for execution_id, child_invocation_id in child_invocations:
            try:
                from ..kernel.runtime import _as_principal

                with _as_principal(principal):
                    signal = self._broker.inference_runner.cancel(child_invocation_id)
            except Exception as exc:
                signal = f"error:{type(exc).__name__}"
            child_signals.append({
                "execution_id": execution_id,
                "child_invocation_id": child_invocation_id,
                "signal": str(signal),
            })
        return {
            "schema": "InferenceParentBundleFence@1",
            "bundle_id": bundle_identifier,
            "parent_operation_id": str(parent["operation_id"]),
            "parent_fence": dict(fence),
            "route_stops": stopped,
            "child_signals": child_signals,
        }

    def request_stop_handoff(
        self,
        principal: Principal,
        *,
        command_id: str,
        bundle_id: str,
        evidence_provider_id: str,
        planning_reference: str,
    ) -> dict[str, Any]:
        command = _safe(command_id, field="command_id")
        provider = self._handoff_evidence_providers.get(
            _safe(evidence_provider_id, field="evidence_provider_id")
        )
        if provider is None:
            raise ValidationError(
                "Stop handoff evidence owner is unavailable.",
                code="inference_parent_stop_handoff_invalid",
            )
        request = {
            "schema": "InferenceParentStopHandoffRequest@1",
            "command_id": command,
            "bundle_id": _safe(bundle_id, field="bundle_id"),
            "evidence_provider_id": provider.id,
            "evidence_provider_revision": provider.revision,
            "planning_reference": _safe(
                planning_reference, field="planning_reference"
            ),
        }
        request_hash = _sha256(request)
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            replay = conn.execute(
                "SELECT * FROM inference_parent_stop_handoffs WHERE command_id=?",
                (command,),
            ).fetchone()
            if replay is not None:
                if str(replay["request_sha256"]) != request_hash:
                    raise ConflictError(
                        "Stop handoff command changed.",
                        code="inference_parent_stop_handoff_conflict",
                    )
                effect = self._handoff_from_row(conn, replay)
                settlement = conn.execute(
                    "SELECT * FROM inference_parent_stop_handoff_settlements WHERE command_id=?",
                    (command,),
                ).fetchone()
                if settlement is not None:
                    settled = self._validated_handoff_settlement(settlement, effect)
                    self._reconstruct_handoff_evidence(
                        conn, replay, expected_state="active"
                    )
                    conn.commit()
                    return settled
                self._reconstruct_handoff_evidence(
                    conn, replay, expected_state="reserved"
                )
                conn.commit()
                return effect
            bundle_row = conn.execute(
                "SELECT * FROM inference_parent_route_bundles WHERE id=?",
                (request["bundle_id"],),
            ).fetchone()
            if bundle_row is None:
                raise ValidationError(
                    "Parent route bundle is unknown.",
                    code="inference_parent_stop_handoff_invalid",
                )
            bundle = self._bundle_from_row(conn, bundle_row)
            parent = conn.execute(
                "SELECT p.*,o.principal_kind,o.principal_identity FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id WHERE p.operation_id=?",
                (bundle_row["parent_operation_id"],),
            ).fetchone()
            if parent is None or (principal.name, principal.identity) != (
                str(parent["principal_kind"]),
                str(parent["principal_identity"]),
            ):
                raise ValidationError(
                    "Parent Stop authority is required.",
                    code="inference_parent_stop_handoff_denied",
                )
            if _sha256(_principal_material(principal)) != bundle[
                "feature_principal_sha256"
            ]:
                raise ValidationError(
                    "Parent Stop principal evidence changed.",
                    code="inference_parent_stop_handoff_denied",
                )
            executions = [
                str(row["id"])
                for row in conn.execute(
                    """SELECT e.id FROM inference_route_executions e
                       JOIN inference_parent_route_bundle_members m
                         ON m.route_plan_id=e.route_plan_id
                      WHERE m.bundle_id=? AND e.state IN ('active','stopping')
                      ORDER BY m.ordinal,e.started_at,e.id""",
                    (request["bundle_id"],),
                ).fetchall()
            ]
            effects: list[dict[str, Any]] = []
            for ordinal, execution_id in enumerate(executions, 1):
                stopped = self._controller.request_stop_in_transaction(
                    INFERENCE_FALLBACK_AUTHORITY,
                    conn,
                    command_id=f"{command}-route-{ordinal}",
                    execution_id=execution_id,
                )
                effects.append(stopped["effect"])
            fence = self._parents.fence_for_handoff_in_transaction(
                conn, principal, operation_id=str(parent["operation_id"])
            )
            before = conn.total_changes
            frozen = provider.freeze(
                conn,
                request["planning_reference"],
                {
                    "command_id": command,
                    "bundle": bundle,
                    "parent_operation_id": str(parent["operation_id"]),
                },
            )
            if conn.total_changes == before:
                raise ConflictError(
                    "Stop handoff owner did not persist its effect.",
                    code="inference_parent_stop_handoff_integrity_invalid",
                )
            evidence = self._validate_handoff_evidence(
                frozen,
                planning_reference=request["planning_reference"],
                expected_state="reserved",
            )
            state = (
                "pending_physical_settlement"
                if any(item["elected_state"] == "stopping" for item in effects)
                else "committed"
            )
            effect = {
                "schema": "InferenceParentStopHandoffEffect@1",
                "command_id": command,
                "bundle_id": request["bundle_id"],
                "parent_operation_id": str(parent["operation_id"]),
                "state": state,
                "parent_fence": fence,
                "evidence_provider_id": provider.id,
                "evidence_provider_revision": provider.revision,
                "planning_reference": request["planning_reference"],
                "evidence_ref": evidence["evidence_ref"],
                "evidence_sha256": evidence["evidence_sha256"],
                "route_stops": effects,
            }
            now = self._parents._clock()
            conn.execute(
                "INSERT INTO inference_parent_stop_handoffs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    command,
                    request_hash,
                    request["bundle_id"],
                    parent["operation_id"],
                    provider.id,
                    provider.revision,
                    request["planning_reference"],
                    evidence["evidence_ref"],
                    evidence["evidence_sha256"],
                    state,
                    _canonical(effect),
                    _sha256(effect),
                    now,
                ),
            )
            for ordinal, (execution_id, stop) in enumerate(zip(executions, effects), 1):
                conn.execute(
                    "INSERT INTO inference_parent_stop_handoff_executions VALUES (?,?,?,?,?)",
                    (
                        command,
                        ordinal,
                        execution_id,
                        f"{command}-route-{ordinal}",
                        stop["elected_state"],
                    ),
                )
            if state == "committed":
                self._settle_and_activate(conn, command, effect, provider)
            conn.commit()
            return effect

    def reconcile_stop_handoff(self, *, command_id: str) -> dict[str, Any]:
        command = _safe(command_id, field="command_id")
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM inference_parent_stop_handoffs WHERE command_id=?",
                (command,),
            ).fetchone()
            if row is None:
                raise ValidationError(
                    "Stop handoff is unknown.",
                    code="inference_parent_stop_handoff_invalid",
                )
            effect = self._handoff_from_row(conn, row)
            provider = self._handoff_evidence_provider(row)
            settlement = conn.execute(
                "SELECT * FROM inference_parent_stop_handoff_settlements WHERE command_id=?",
                (command,),
            ).fetchone()
            if settlement is not None:
                settled = self._validated_handoff_settlement(settlement, effect)
                self._reconstruct_handoff_evidence(
                    conn, row, expected_state="active"
                )
                conn.commit()
                return settled
            self._reconstruct_handoff_evidence(conn, row, expected_state="reserved")
            executions = conn.execute(
                """SELECT e.state,e.terminal_disposition
                     FROM inference_parent_stop_handoff_executions h
                     JOIN inference_route_executions e ON e.id=h.execution_id
                    WHERE h.command_id=? ORDER BY h.ordinal""",
                (command,),
            ).fetchall()
            for execution in executions:
                state = str(execution["state"])
                disposition = execution["terminal_disposition"]
                if state in {"active", "stopping"}:
                    conn.commit()
                    return effect
                if state == "stopped":
                    if disposition != "owner_cancelled":
                        raise ConflictError(
                            "Stop handoff execution settlement is invalid.",
                            code="inference_parent_stop_handoff_integrity_invalid",
                        )
                    continue
                if state != "terminal" or not isinstance(disposition, str):
                    raise ConflictError(
                        "Stop handoff execution settlement is invalid.",
                        code="inference_parent_stop_handoff_integrity_invalid",
                    )
                if disposition in {
                    "dispatch_outcome_unknown",
                    "physical_outcome_unknown",
                    "effect_indeterminate",
                }:
                    conn.commit()
                    return effect
                if disposition not in {
                    "preflight_unavailable",
                    "known_no_generation_transient",
                    "provider_permanent",
                    "invalid_typed_output",
                    "invalid_tool_call",
                    "context_overflow",
                    "local_capacity_unavailable",
                    "tool_unavailable_or_stale",
                    "permission_denied",
                    "policy_refused",
                    "owner_cancelled",
                    "deadline_exhausted",
                    "owner_terminal",
                }:
                    raise ConflictError(
                        "Stop handoff execution settlement is invalid.",
                        code="inference_parent_stop_handoff_integrity_invalid",
                    )
            settled = self._settle_and_activate(conn, command, effect, provider)
            conn.commit()
            return settled

    def _handoff_evidence_provider(self, row: Any) -> HandoffEvidenceProvider:
        provider = self._handoff_evidence_providers.get(
            str(row["evidence_provider_id"])
        )
        if provider is None or provider.revision != int(
            row["evidence_provider_revision"]
        ):
            raise ConflictError(
                "Stop handoff evidence owner is unavailable.",
                code="inference_parent_stop_handoff_integrity_invalid",
            )
        return provider

    def _reconstruct_handoff_evidence(
        self, conn: Any, row: Any, *, expected_state: str
    ) -> dict[str, str]:
        provider = self._handoff_evidence_provider(row)
        before = conn.total_changes
        reconstructed = self._validate_handoff_evidence(
            provider.reconstruct(conn, str(row["evidence_ref"])),
            planning_reference=str(row["planning_reference"]),
            expected_state=expected_state,
        )
        if (
            conn.total_changes != before
            or reconstructed["evidence_ref"] != str(row["evidence_ref"])
            or reconstructed["evidence_sha256"] != str(row["evidence_sha256"])
        ):
            raise ConflictError(
                "Stop handoff evidence changed.",
                code="inference_parent_stop_handoff_integrity_invalid",
            )
        return reconstructed

    @staticmethod
    def _validate_handoff_evidence(
        value: Any, *, planning_reference: str, expected_state: str
    ) -> dict[str, str]:
        if (
            expected_state not in {"reserved", "active"}
            or not isinstance(value, Mapping)
            or set(value)
            != {"schema", "planning_reference", "evidence_ref", "evidence_sha256", "state"}
            or value["schema"] != "InferenceParentHandoffEvidence@1"
            or value["planning_reference"] != planning_reference
            or value["state"] != expected_state
            or not str(value["evidence_ref"])
            or not str(value["evidence_sha256"]).startswith("sha256:")
        ):
            raise ConflictError(
                "Stop handoff evidence is invalid.",
                code="inference_parent_stop_handoff_integrity_invalid",
            )
        return {key: str(item) for key, item in value.items()}

    @staticmethod
    def _validated_handoff_settlement(
        settlement: Any, effect: Mapping[str, Any]
    ) -> dict[str, Any]:
        try:
            settled = json.loads(str(settlement["effect_json"]))
            if (
                str(settlement["effect_sha256"]) != _sha256(settled)
                or settled != {**dict(effect), "state": "committed"}
            ):
                raise ValueError("settlement")
            return settled
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Stop handoff settlement changed.",
                code="inference_parent_stop_handoff_integrity_invalid",
            ) from exc

    def _settle_and_activate(
        self,
        conn: Any,
        command_id: str,
        effect: Mapping[str, Any],
        provider: HandoffEvidenceProvider,
    ) -> dict[str, Any]:
        row = conn.execute(
            "SELECT * FROM inference_parent_stop_handoffs WHERE command_id=?",
            (command_id,),
        ).fetchone()
        if row is None:
            raise ConflictError(
                "Stop handoff is missing.",
                code="inference_parent_stop_handoff_integrity_invalid",
            )
        existing = conn.execute(
            "SELECT * FROM inference_parent_stop_handoff_settlements WHERE command_id=?",
            (command_id,),
        ).fetchone()
        if existing is not None:
            settled = self._validated_handoff_settlement(existing, effect)
            self._reconstruct_handoff_evidence(conn, row, expected_state="active")
            return settled
        self._reconstruct_handoff_evidence(conn, row, expected_state="reserved")
        settled = {**dict(effect), "state": "committed"}
        conn.execute(
            "INSERT INTO inference_parent_stop_handoff_settlements VALUES (?,?,?,?)",
            (
                command_id,
                _canonical(settled),
                _sha256(settled),
                self._parents._clock(),
            ),
        )
        before = conn.total_changes
        provider.activate(conn, str(row["evidence_ref"]))
        if conn.total_changes == before:
            raise ConflictError(
                "Stop handoff owner did not activate its effect.",
                code="inference_parent_stop_handoff_integrity_invalid",
            )
        self._reconstruct_handoff_evidence(conn, row, expected_state="active")
        return settled

    def _handoff_from_row(self, conn: Any, row: Any) -> dict[str, Any]:
        try:
            effect = json.loads(str(row["effect_json"]))
            if (
                set(effect)
                != {
                    "schema", "command_id", "bundle_id", "parent_operation_id", "state",
                    "parent_fence", "evidence_provider_id", "evidence_provider_revision",
                    "planning_reference", "evidence_ref", "evidence_sha256", "route_stops",
                }
                or effect["schema"] != "InferenceParentStopHandoffEffect@1"
                or str(row["effect_sha256"]) != _sha256(effect)
                or effect["command_id"] != str(row["command_id"])
                or effect["bundle_id"] != str(row["bundle_id"])
                or effect["parent_operation_id"] != str(row["parent_operation_id"])
                or effect["evidence_provider_id"] != str(row["evidence_provider_id"])
                or effect["evidence_provider_revision"] != int(row["evidence_provider_revision"])
                or effect["planning_reference"] != str(row["planning_reference"])
                or effect["evidence_ref"] != str(row["evidence_ref"])
                or effect["evidence_sha256"] != str(row["evidence_sha256"])
                or effect["state"] != str(row["state"])
                or effect["state"] not in {"committed", "pending_physical_settlement"}
            ):
                raise ValueError("handoff")
            fence = effect["parent_fence"]
            if (
                not isinstance(fence, dict)
                or set(fence) != {"schema", "operation_id", "prior_epoch", "post_epoch", "state"}
                or fence["schema"] != "ParentHandoffFence@1"
                or fence["operation_id"] != effect["parent_operation_id"]
                or type(fence["prior_epoch"]) is not int
                or type(fence["post_epoch"]) is not int
                or fence["post_epoch"] != fence["prior_epoch"] + 1
                or fence["state"] != "CANCELLING"
            ):
                raise ValueError("parent fence")
            if not isinstance(effect["route_stops"], list):
                raise ValueError("route stops")
            executions = conn.execute(
                "SELECT execution_id,stop_command_id,elected_state FROM inference_parent_stop_handoff_executions WHERE command_id=? ORDER BY ordinal",
                (row["command_id"],),
            ).fetchall()
            if len(executions) != len(effect["route_stops"]):
                raise ValueError("handoff executions")
            for stored, stop in zip(executions, effect["route_stops"]):
                if (
                    not isinstance(stop, dict)
                    or set(stop) != {"schema", "execution_id", "observed_state", "observed_revision", "elected_state"}
                    or str(stored["execution_id"]) != stop["execution_id"]
                    or str(stored["stop_command_id"]) == ""
                    or str(stored["elected_state"]) != stop["elected_state"]
                ):
                    raise ValueError("handoff execution")
                command = conn.execute(
                    "SELECT * FROM inference_route_execution_commands WHERE command_id=?",
                    (stored["stop_command_id"],),
                ).fetchone()
                if (
                    command is None
                    or str(command["action"]) != "stop"
                    or str(command["execution_id"]) != stop["execution_id"]
                    or str(command["effect_sha256"]) != _sha256(stop)
                    or json.loads(str(command["effect_json"])) != stop
                ):
                    raise ValueError("handoff stop provenance")
            return effect
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Stop handoff evidence changed.",
                code="inference_parent_stop_handoff_integrity_invalid",
            ) from exc

    @staticmethod
    def _validate_derived_preloads(
        conn: Any, evidence_rows: Any, members: Sequence[Mapping[str, Any]]
    ) -> None:
        if not isinstance(evidence_rows, list) or len(evidence_rows) != 1:
            raise ValueError("derived preload")
        evidence = evidence_rows[0]
        fields = {
            "schema", "preload_route_key", "preload_route_plan_id",
            "preload_route_plan_sha256", "transcription_route_key",
            "transcription_route_plan_id", "transcription_route_plan_sha256",
            "deployment_revision_id", "engine", "model", "language", "model_artifact",
            "candidate_material", "candidate_material_sha256", "strategy_sequence",
        }
        if (
            not isinstance(evidence, Mapping)
            or set(evidence) != fields
            or evidence["schema"] != "InferenceDerivedPreloadEvidence@1"
            or not isinstance(evidence["model"], str) or not evidence["model"]
            or not isinstance(evidence["language"], str) or not evidence["language"]
            or not isinstance(evidence["candidate_material"], list)
            or any(
                not isinstance(item, Mapping)
                or set(item) != {"id", "revision"}
                or _safe_preload_candidate(item["id"]) != item["id"]
                or _safe(item["revision"], field="preload_candidate_revision") != item["revision"]
                for item in evidence["candidate_material"]
            )
            or evidence["candidate_material_sha256"] != _sha256(evidence["candidate_material"])
            or not isinstance(evidence["strategy_sequence"], list)
            or not evidence["strategy_sequence"]
            or any(
                not isinstance(item, str)
                or _safe(item, field="preload_strategy") != item
                for item in evidence["strategy_sequence"]
            )
            or len(evidence["strategy_sequence"]) != len(set(evidence["strategy_sequence"]))
        ):
            raise ValueError("derived preload")
        by_key = {str(item["key"]): item for item in members}
        transcription = by_key.get(str(evidence["transcription_route_key"]))
        preload = by_key.get(str(evidence["preload_route_key"]))
        if (
            transcription is None or preload is None
            or transcription["capability_id"] != "speech.transcribe"
            or preload["capability_id"] != "speech.preload"
            or transcription["route_plan_id"] != evidence["transcription_route_plan_id"]
            or transcription["route_plan_sha256"] != evidence["transcription_route_plan_sha256"]
            or preload["route_plan_id"] != evidence["preload_route_plan_id"]
            or preload["route_plan_sha256"] != evidence["preload_route_plan_sha256"]
        ):
            raise ValueError("derived preload bind")
        row = conn.execute(
            "SELECT engine,model,artifact_id FROM deployment_revisions WHERE id=?",
            (evidence["deployment_revision_id"],),
        ).fetchone()
        source_route = conn.execute(
            "SELECT 1 FROM inference_route_plan_entries WHERE plan_id=? AND deployment_revision_id=?",
            (transcription["route_plan_id"], evidence["deployment_revision_id"]),
        ).fetchone()
        preload_route = conn.execute(
            "SELECT 1 FROM inference_route_plan_entries WHERE plan_id=? AND deployment_revision_id=?",
            (preload["route_plan_id"], evidence["deployment_revision_id"]),
        ).fetchone()
        if (
            row is None or source_route is None or preload_route is None
            or str(row["engine"]) != evidence["engine"]
            or str(row["artifact_id"] or row["model"] or "") != evidence["model_artifact"]
        ):
            raise ValueError("derived preload deployment")

    def _bundle_from_row(self, conn: Any, row: Any) -> dict[str, Any]:
        try:
            material = json.loads(str(row["payload_json"]))
            digest = _sha256(material)
            members = [
                dict(item)
                for item in conn.execute(
                    """SELECT ordinal,route_key AS key,capability_id,route_plan_id,
                              route_plan_sha256,principal_policy_sha256,
                              maximum_physical_attempts
                         FROM inference_parent_route_bundle_members
                        WHERE bundle_id=? ORDER BY ordinal""",
                    (row["id"],),
                ).fetchall()
            ]
            required = {
                "schema", "id", "parent_operation_id", "parent_kind",
                "parent_deadline_at", "parent_child_budget", "lifecycle_child_budget",
                "feature_principal_sha256", "members",
            }
            optional = {"budget_groups", "requested_remote_device_ids", "derived_preloads"}
            if (
                not required.issubset(material)
                or set(material) - required - optional
                or material["schema"] != "InferenceParentRouteBundle@1"
                or material["members"] != members
                or digest != str(row["sha256"])
                or material["id"] != str(row["id"])
                or material["parent_operation_id"] != str(row["parent_operation_id"])
                or material["parent_deadline_at"] != float(row["parent_deadline_at"])
                or material["parent_child_budget"] != int(row["parent_child_budget"])
                or material["lifecycle_child_budget"] != int(row["lifecycle_child_budget"])
                or material["feature_principal_sha256"] != str(row["feature_principal_sha256"])
            ):
                raise ValueError("bundle")
            groups = self._budget_groups(material.get("budget_groups"), members) if "budget_groups" in material else []
            if groups:
                if (
                    material["lifecycle_child_budget"] != 0
                    or material["parent_child_budget"]
                    != sum(int(group["allocation"]) for group in groups)
                ):
                    raise ValueError("aggregate budget")
            elif material["parent_child_budget"] != (
                sum(item["maximum_physical_attempts"] for item in members)
                + material["lifecycle_child_budget"]
            ):
                raise ValueError("bundle budget")
            if "requested_remote_device_ids" in material and (
                self._requested_remote_devices(material["requested_remote_device_ids"])
                != material["requested_remote_device_ids"]
            ):
                raise ValueError("requested remote devices")
            for member in members:
                principal_evidence = conn.execute(
                    "SELECT sha256 FROM inference_route_plan_principal_evidence WHERE plan_id=?",
                    (member["route_plan_id"],),
                ).fetchone()
                route = self._plans._route_from_row(
                    conn,
                    conn.execute(
                        "SELECT * FROM inference_route_plans WHERE id=?",
                        (member["route_plan_id"],),
                    ).fetchone(),
                )
                if (
                    route["sha256"] != member["route_plan_sha256"]
                    or route["capability"]["id"] != member["capability_id"]
                    or principal_evidence is None
                    or str(principal_evidence["sha256"])
                    != member["principal_policy_sha256"]
                    or datetime.fromisoformat(
                        str(route["deadline_at"]).replace("Z", "+00:00")
                    ).timestamp()
                    > float(material["parent_deadline_at"])
                ):
                    raise ValueError("member")
            if "derived_preloads" in material:
                self._validate_derived_preloads(conn, material["derived_preloads"], members)
            parent = conn.execute(
                "SELECT kind,deadline_at,child_budget FROM kernel_parent_runs WHERE operation_id=?",
                (material["parent_operation_id"],),
            ).fetchone()
            command = conn.execute(
                "SELECT request_sha256,parent_operation_id FROM inference_parent_route_bundles WHERE command_id=?",
                (row["command_id"],),
            ).fetchone()
            if (
                parent is None
                or str(parent["kind"]) != material["parent_kind"]
                or float(parent["deadline_at"]) != material["parent_deadline_at"]
                or int(parent["child_budget"]) != material["parent_child_budget"]
                or command is None
                or str(command["request_sha256"]) != str(row["request_sha256"])
                or str(command["parent_operation_id"])
                != material["parent_operation_id"]
            ):
                raise ValueError("parent bundle cross bind")
            return {**material, "sha256": digest}
        except (KeyError, TypeError, ValueError, ValidationError, json.JSONDecodeError) as exc:
            raise ConflictError(
                "Parent route bundle integrity could not be verified.",
                code="inference_parent_route_bundle_integrity_invalid",
            ) from exc


__all__ = ["HandoffEvidenceProvider", "InferenceParentRouteBundleService"]
