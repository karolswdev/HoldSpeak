"""Versioned, visible context for one refinement Thought (HS-141-05)."""
from __future__ import annotations

import base64
import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

from ..db.refinement_thoughts import RefinementThoughtRepository, _now, canonical_json
from ..db.relationships import qualified_ref
from ..principals import Principal, PrincipalKind
from .errors import ConflictError, NotFound, ValidationError

EVERYDAY_CONTEXT_REF = "knowledge:hs-seed-everyday-context"
MAX_VISIBLE = 8
MAX_LEAVES = 16
MAX_LEAF_BYTES = 12_000
MAX_CONTEXT_BYTES = 48_000
_OPEN = '<untrusted-refinement-context-json schema="holdspeak.context.v1">\n'
_CLOSE = '\n</untrusted-refinement-context-json>'


@dataclass(frozen=True)
class FrozenGroundingSnapshot:
    attachment_revision: int
    attachment_sha256: str
    material: str
    byte_count: int
    used_context: dict[str, Any] | None
    grounding_echo: dict[str, Any]

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        actual = len(self.material.encode("utf-8"))
        if actual != self.byte_count or actual > MAX_CONTEXT_BYTES:
            raise ValidationError("frozen context byte count is invalid",
                                  code="frozen_grounding_invalid",
                                  context={"observed": actual, "declared": self.byte_count,
                                           "allowed": MAX_CONTEXT_BYTES})


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _prompt_json(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return raw.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


class RefinementContextService:
    def __init__(self, db: Any) -> None:
        self._db = db

    @staticmethod
    def _owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ValidationError("thought context requires the authenticated owner", code="thought_owner_required")

    @staticmethod
    def _default_hash(revision: int, refs: list[str]) -> str:
        return _sha(canonical_json({"schema": "holdspeak.default-ai-context.v1",
                                    "revision": revision, "refs": refs}))

    def _verified_default(self, conn: Any) -> dict[str, Any]:
        row = conn.execute("SELECT * FROM refinement_default_context_current WHERE id=1").fetchone()
        if row is None:
            raise ConflictError("default AI context ledger is missing",
                                code="default_context_ledger_invalid")
        current = dict(row)
        invalid = lambda: ConflictError("default AI context ledger is invalid",
                                        code="default_context_ledger_invalid")
        try:
            head = int(current["revision"])
            rows = conn.execute(
                "SELECT * FROM refinement_default_context_revisions ORDER BY revision"
            ).fetchall()
            if [int(item["revision"]) for item in rows] != list(range(head + 1)):
                raise invalid()
            history: dict[int, dict[str, Any]] = {}
            for item in rows:
                revision = int(item["revision"])
                refs = json.loads(str(item["refs_json"]))
                labels = json.loads(str(item["labels_json"]))
                if (not isinstance(refs, list) or len(refs) > MAX_VISIBLE
                        or any(not isinstance(ref, str) for ref in refs)
                        or refs != sorted(set(refs))
                        or any((ref != EVERYDAY_CONTEXT_REF and not ref.startswith("note:"))
                               or qualified_ref(ref) != ref for ref in refs)):
                    raise invalid()
                if (not isinstance(labels, list) or len(labels) != len(refs)
                        or canonical_json(refs).decode("utf-8") != str(item["refs_json"])):
                    raise invalid()
                safe_labels: list[dict[str, Any]] = []
                for ref, label in zip(refs, labels, strict=True):
                    if (not isinstance(label, dict)
                            or set(label) != {"ref", "kind", "title", "leaf_count"}
                            or label.get("ref") != ref
                            or label.get("kind") != ref.partition(":")[0]
                            or not isinstance(label.get("title"), str)
                            or not label["title"]
                            or not isinstance(label.get("leaf_count"), int)
                            or isinstance(label["leaf_count"], bool)
                            or not 1 <= label["leaf_count"] <= MAX_LEAVES):
                        raise invalid()
                    safe_labels.append(dict(label))
                if sum(label["leaf_count"] for label in safe_labels) > MAX_LEAVES:
                    raise invalid()
                digest = self._default_hash(revision, refs)
                if (str(item["configuration_sha256"]) != digest
                        or canonical_json(safe_labels).decode("utf-8") != str(item["labels_json"])):
                    raise invalid()
                history[revision] = {"revision": revision,
                                     "configuration_sha256": digest,
                                     "refs": refs, "labels": safe_labels}
            rev0 = history.get(0)
            if (rev0 is None or rev0["refs"] != [] or rev0["labels"] != []
                    or rev0["configuration_sha256"] != self._default_hash(0, [])):
                raise invalid()
            active = history[head]
            if (str(current["configuration_sha256"]) != active["configuration_sha256"]
                    or str(current["refs_json"]) != canonical_json(active["refs"]).decode("utf-8")):
                raise invalid()
            transitions: dict[int, int] = {}
            actions = conn.execute(
                "SELECT * FROM refinement_default_context_actions ORDER BY created_at,action_id"
            ).fetchall()
            receipt_keys = {"id", "action", "scope", "prior_revision", "revision",
                            "configuration_sha256", "refs", "selections", "no_op",
                            "existing_thoughts_changed"}
            for action in actions:
                receipt = json.loads(str(action["receipt_json"]))
                prior, post = int(action["prior_revision"]), int(action["post_revision"])
                if (not isinstance(receipt, dict) or set(receipt) != receipt_keys
                        or prior not in history or post not in history
                        or receipt != {"id": str(action["action_id"]),
                            "action": "replace_default_context", "scope": "future_thoughts",
                            "prior_revision": prior, "revision": post,
                            "configuration_sha256": history[post]["configuration_sha256"],
                            "refs": history[post]["refs"],
                            "selections": history[post]["labels"],
                            "no_op": post == prior, "existing_thoughts_changed": 0}
                        or str(action["post_configuration_sha256"]) != history[post]["configuration_sha256"]
                        or str(action["request_sha256"]) != _sha(canonical_json({
                            "action": "replace_default_context", "expected_revision": prior,
                            "refs": history[post]["refs"]}))
                        or post not in {prior, prior + 1}):
                    raise invalid()
                if post == prior + 1:
                    transitions[post] = transitions.get(post, 0) + 1
            if any(transitions.get(revision) != 1 for revision in range(1, head + 1)):
                raise invalid()
        except ConflictError:
            raise
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise invalid() from exc
        return {**active, "history": history}

    @staticmethod
    def _default_thought() -> dict[str, str]:
        return {"id": "default-ai-context-policy", "working_note_id": "__none__"}

    def _default_projection_in_transaction(self, conn: Any) -> dict[str, Any]:
        current = self._verified_default(conn)
        prior = {str(item.get("ref")): item for item in current["labels"]
                 if isinstance(item, dict) and item.get("ref")}
        selections: list[dict[str, Any]] = []
        for ref in current["refs"]:
            try:
                item = self._resolve_manifest(
                    conn, self._default_thought(), [ref], 1, include_content=False
                )["visible"][0]
                selections.append({"ref": ref, "kind": item["kind"],
                                   "title": item["title"],
                                   "leaf_count": len(item["leaves"]),
                                   "state": "current"})
            except (ValidationError, NotFound) as exc:
                fallback = prior.get(ref, {})
                selections.append({"ref": ref,
                                   "kind": str(fallback.get("kind") or ref.partition(":")[0]),
                                   "title": str(fallback.get("title") or ref),
                                   "leaf_count": int(fallback.get("leaf_count") or 0),
                                   "state": "missing" if (isinstance(exc, NotFound)
                                       or getattr(exc, "code", "") == "context_missing") else "invalid"})
        return {"revision": current["revision"],
                "configuration_sha256": current["configuration_sha256"],
                "refs": list(current["refs"]), "selections": selections}

    def get_default_context(self, principal: Principal) -> dict[str, Any]:
        self._owner(principal)
        with self._db._connection() as conn:
            return {"default_context": self._default_projection_in_transaction(conn)}

    def replace_default_context(self, principal: Principal, *, request_id: str,
                                expected_revision: int, refs: list[str]) -> dict[str, Any]:
        self._owner(principal)
        if (not isinstance(request_id, str) or not request_id.strip()
                or not isinstance(expected_revision, int) or isinstance(expected_revision, bool)
                or not isinstance(refs, list)):
            raise ValidationError("default context request id, revision, and refs are required",
                                  code="default_context_request_required")
        request_id = request_id.strip()
        normalized: list[str] = []
        try:
            normalized = sorted(set(qualified_ref(ref) for ref in refs))
        except (TypeError, ValueError) as exc:
            raise ValidationError("default context accepts qualified refs only",
                                  code="default_context_ref_invalid") from exc
        semantic = {"action": "replace_default_context",
                    "expected_revision": expected_revision, "refs": normalized}
        request_hash = _sha(canonical_json(semantic))
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            current = self._verified_default(conn)
            prior = conn.execute(
                "SELECT * FROM refinement_default_context_actions WHERE request_id=?",
                (request_id,),
            ).fetchone()
            if prior is not None:
                if str(prior["request_sha256"]) != request_hash:
                    raise ConflictError("default context request id was reused",
                                        code="default_context_request_payload_mismatch")
                if current["revision"] != int(prior["post_revision"]):
                    raise ConflictError("default context request was superseded",
                                        code="default_context_request_superseded",
                                        context={"default_context": self._default_projection_in_transaction(conn)})
                return {"default_context": self._default_projection_in_transaction(conn),
                        "receipt": json.loads(str(prior["receipt_json"]))}
            if current["revision"] != expected_revision:
                raise ConflictError("default AI context changed elsewhere",
                                    code="default_context_revision_conflict",
                                    context={"default_context": self._default_projection_in_transaction(conn)})
            unchanged = normalized == current["refs"]
            post_revision = expected_revision
            digest = current["configuration_sha256"]
            if unchanged:
                labels = list(current["labels"])
            elif normalized:
                manifest = self._resolve_manifest(
                    conn, self._default_thought(), normalized, 1, include_content=False
                )
                labels = [{"ref": item["ref"], "kind": item["kind"],
                           "title": item["title"], "leaf_count": len(item["leaves"])}
                          for item in manifest["visible"]]
            else:
                labels = []
            now = _now()
            if not unchanged:
                post_revision += 1
                digest = self._default_hash(post_revision, normalized)
                refs_json = canonical_json(normalized).decode("utf-8")
                labels_json = canonical_json(labels).decode("utf-8")
                conn.execute(
                    "INSERT INTO refinement_default_context_revisions"
                    "(revision,configuration_sha256,refs_json,labels_json,created_at) VALUES(?,?,?,?,?)",
                    (post_revision, digest, refs_json, labels_json, now),
                )
                changed = conn.execute(
                    "UPDATE refinement_default_context_current SET revision=?,configuration_sha256=?,refs_json=?,updated_at=? WHERE id=1 AND revision=?",
                    (post_revision, digest, refs_json, now, expected_revision),
                )
                if changed.rowcount != 1:
                    raise ConflictError("default AI context changed elsewhere",
                                        code="default_context_revision_conflict")
            action_id = f"rdctx_{uuid.uuid4().hex[:12]}"
            receipt = {"id": action_id, "action": "replace_default_context",
                       "scope": "future_thoughts", "prior_revision": expected_revision,
                       "revision": post_revision, "configuration_sha256": digest,
                       "refs": normalized, "selections": labels, "no_op": unchanged,
                       "existing_thoughts_changed": 0}
            conn.execute(
                "INSERT INTO refinement_default_context_actions"
                "(action_id,request_id,request_sha256,prior_revision,post_revision,post_configuration_sha256,receipt_json,created_at) VALUES(?,?,?,?,?,?,?,?)",
                (action_id, request_id, request_hash, expected_revision, post_revision,
                 digest, canonical_json(receipt).decode("utf-8"), now),
            )
            return {"default_context": self._default_projection_in_transaction(conn),
                    "receipt": receipt}

    @staticmethod
    def _failure_from_attribution(
        attribution: Any, labels: list[dict[str, Any]], *, expected_code: str
    ) -> dict[str, Any] | None:
        if attribution is None:
            if expected_code:
                raise ValueError("missing failure attribution")
            return None
        if (not isinstance(attribution, dict)
                or set(attribution) != {"code", "affected", "leaf"}
                or attribution.get("code") != expected_code
                or expected_code not in {
                    "default_context_missing", "default_context_empty",
                    "default_context_kind_unsupported",
                    "default_context_self_reference",
                    "default_context_leaf_overlap", "default_context_too_large"}
                or not isinstance(attribution.get("affected"), list)
                or not attribution["affected"]):
            raise ValueError("invalid failure attribution")
        by_ref = {item["ref"]: item for item in labels}
        affected_refs: list[str] = []
        for affected in attribution["affected"]:
            if (not isinstance(affected, dict) or set(affected) != {"ref", "title"}
                    or not isinstance(affected.get("ref"), str)
                    or not isinstance(affected.get("title"), str)
                    or not affected["ref"] or not affected["title"]
                    or affected["ref"] in affected_refs
                    or affected["ref"] not in by_ref
                    or by_ref[affected["ref"]]["title"] != affected["title"]):
                raise ValueError("invalid affected default")
            affected_refs.append(affected["ref"])
        if affected_refs != sorted(affected_refs):
            raise ValueError("noncanonical affected defaults")
        failure: dict[str, Any] = {
            "code": expected_code,
            "selections": [by_ref[ref] for ref in affected_refs],
        }
        leaf = attribution["leaf"]
        if leaf is not None:
            if (not isinstance(leaf, dict)
                    or set(leaf) != {"visible_ref", "ref", "title"}
                    or leaf.get("visible_ref") not in affected_refs
                    or not isinstance(leaf.get("ref"), str) or not leaf["ref"]
                    or not isinstance(leaf.get("title"), str) or not leaf["title"]):
                raise ValueError("invalid attributed leaf")
            failure["leaf"] = {"ref": leaf["ref"], "title": leaf["title"]}
        return failure

    @classmethod
    def _failure_attribution(
        cls, failure: dict[str, Any] | None, labels: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        if failure is None:
            return None
        affected = sorted(
            ({"ref": str(item["ref"]), "title": str(item["title"])}
             for item in failure.get("selections", [])),
            key=lambda item: item["ref"],
        )
        leaf = failure.get("leaf")
        stored_leaf = None
        if leaf is not None:
            direct = next((item["ref"] for item in affected
                           if item["ref"] == leaf.get("ref")), None)
            stored_leaf = {"visible_ref": direct or affected[0]["ref"],
                           "ref": str(leaf["ref"]), "title": str(leaf["title"])}
        attribution = {"code": str(failure.get("code") or ""),
                       "affected": affected, "leaf": stored_leaf}
        cls._failure_from_attribution(
            attribution, labels, expected_code=attribution["code"]
        )
        return attribution

    def default_application_receipt_in_transaction(
        self, conn: Any, *, thought_id: str, create_request_id: str
    ) -> dict[str, Any]:
        policy = self._verified_default(conn)
        invalid = lambda: ConflictError(
            "default AI context application proof is invalid",
            code="default_context_application_proof_invalid",
        )
        row = conn.execute(
            "SELECT * FROM refinement_default_context_applications WHERE thought_id=? AND create_request_id=?",
            (thought_id, create_request_id),
        ).fetchone()
        if row is None:
            raise ConflictError(
                "default AI context application proof is unavailable",
                code="default_context_application_proof_unavailable",
                context={"thought_id": thought_id},
            )
        try:
            receipt = json.loads(str(row["receipt_json"]))
            attribution = json.loads(str(row["failure_json"]))
        except (TypeError, ValueError) as exc:
            raise invalid() from exc
        if (not isinstance(receipt, dict)
                or set(receipt) != {"id", "action", "scope", "thought_id",
                    "default_revision", "default_configuration_sha256", "status",
                    "attachment_zero_sha256", "attachment_revision",
                    "attachment_sha256", "attachments", "failure"}):
            raise invalid()
        expected = {
            "id": str(row["application_id"]), "action": "apply_default_context",
            "scope": "this_thought", "thought_id": str(row["thought_id"]),
            "default_revision": int(row["default_revision"]),
            "default_configuration_sha256": str(row["default_configuration_sha256"]),
            "status": str(row["status"]),
            "attachment_zero_sha256": str(row["attachment_zero_sha256"]),
            "attachment_revision": int(row["attachment_revision"]),
            "attachment_sha256": str(row["attachment_sha256"]),
        }
        if (any(receipt.get(key) != value for key, value in expected.items())
                or str(row["thought_id"]) != thought_id
                or str(row["create_request_id"]) != create_request_id):
            raise invalid()
        referenced = policy["history"].get(int(row["default_revision"]))
        if (referenced is None
                or str(row["default_configuration_sha256"]) != referenced["configuration_sha256"]):
            raise invalid()
        try:
            failure_raw = canonical_json(attribution)
            if (str(row["failure_json"]) != failure_raw.decode("utf-8")
                    or str(row["failure_sha256"]) != _sha(failure_raw)):
                raise ValueError("failure attribution hash mismatch")
            failure = self._failure_from_attribution(
                attribution, referenced["labels"],
                expected_code=str(row["error_code"] or ""),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise invalid() from exc
        if receipt.get("failure") != failure:
            raise invalid()
        receipt = {**receipt, "failure": failure}
        status = str(row["status"])
        if ((not referenced["refs"] and status != "empty")
                or (referenced["refs"] and status not in {"applied", "not_applied"})):
            raise invalid()
        zero_hash = RefinementThoughtRepository.empty_attachment_hash(thought_id)
        if str(row["attachment_zero_sha256"]) != zero_hash:
            raise invalid()
        attachments = receipt.get("attachments")
        if not isinstance(attachments, list):
            raise invalid()
        birth = conn.execute(
            "SELECT * FROM refinement_aggregate_commands WHERE thought_id=? AND aggregate_revision=1",
            (thought_id,),
        ).fetchone()
        thought = conn.execute(
            "SELECT * FROM refinement_thoughts WHERE id=? AND create_request_id=?",
            (thought_id, create_request_id),
        ).fetchone()
        if (thought is None or birth is None
                or str(birth["command_kind"]) not in {"create", "adopt_note"}
                or int(birth["canonical_version"]) != 2
                or int(birth["prior_attachment_revision"]) != 0
                or int(birth["next_attachment_revision"]) != 0
                or str(birth["attachment_sha256"] or "") != zero_hash):
            raise invalid()
        if status == "applied":
            if failure is not None or str(row["error_code"] or ""):
                raise invalid()
            application = conn.execute(
                "SELECT * FROM refinement_aggregate_commands WHERE thought_id=? AND aggregate_revision=2",
                (thought_id,),
            ).fetchone()
            if (application is None or str(application["command_kind"]) != "replace_attachments"
                    or int(application["canonical_version"]) != 2
                    or int(application["prior_attachment_revision"]) != 0
                    or int(application["next_attachment_revision"]) != int(row["attachment_revision"])
                    or str(application["attachment_sha256"] or "") != str(row["attachment_sha256"])):
                raise invalid()
            try:
                visible = self._verified_stored_visible(
                    conn, thought_id, int(row["attachment_revision"]),
                    str(row["attachment_sha256"]),
                )
            except ConflictError as exc:
                raise invalid() from exc
            expected_attachments = [{"ref": item["ref"], "title": item["title"],
                                     "leaf_count": len(item["leaves"])}
                                    for item in visible]
            if ([item["ref"] for item in visible] != referenced["refs"]
                    or attachments != expected_attachments
                    or int(row["attachment_revision"]) != 1):
                raise invalid()
        else:
            if (int(row["attachment_revision"]) != 0
                    or str(row["attachment_sha256"]) != zero_hash
                    or attachments != []):
                raise invalid()
            if status == "empty":
                if failure is not None or str(row["error_code"] or ""):
                    raise invalid()
            else:
                if failure is None:
                    raise invalid()
        return receipt

    @staticmethod
    def _default_failure(exc: Exception, labels: list[dict[str, Any]]) -> dict[str, Any] | None:
        if isinstance(exc, NotFound):
            code = "default_context_missing"
            missing_id = str(exc.context.get("id") or "")
            affected = [item for item in labels
                        if str(item.get("ref") or "").split(":", 1)[-1] == missing_id]
        elif isinstance(exc, ValidationError):
            mapping = {
                "context_missing": "default_context_missing",
                "context_empty": "default_context_empty",
                "context_kind_unsupported": "default_context_kind_unsupported",
                "context_self_reference": "default_context_self_reference",
                "context_leaf_overlap": "default_context_leaf_overlap",
                "context_too_large": "default_context_too_large",
            }
            code = mapping.get(exc.code, "")
            if not code:
                return None
            refs = {str(exc.context.get(key) or "") for key in
                    ("visible_ref", "first_ref", "second_ref")}
            affected = [item for item in labels if str(item.get("ref") or "") in refs]
        else:
            return None
        selections = affected or labels
        failure: dict[str, Any] = {"code": code, "selections": selections}
        if isinstance(exc, ValidationError) and exc.context.get("leaf_ref"):
            failure["leaf"] = {"ref": str(exc.context["leaf_ref"]),
                               "title": str(exc.context.get("leaf_title")
                                            or exc.context["leaf_ref"])}
        return failure

    def apply_default_at_birth_in_transaction(
        self, conn: Any, *, thought: dict[str, Any], create_request_id: str,
        working_sha256: str, occurred_at: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        current = self._verified_default(conn)
        zero_hash = RefinementThoughtRepository.empty_attachment_hash(str(thought["id"]))
        if (int(thought["aggregate_revision"]), int(thought["attachment_revision"]),
                str(thought["attachment_sha256"])) != (1, 0, zero_hash):
            raise ConflictError("Thought birth attachment head is invalid",
                                code="default_context_birth_invalid")
        status = "empty"
        failure: dict[str, Any] | None = None
        attachments: list[dict[str, Any]] = []
        updated = dict(thought)
        if current["refs"]:
            try:
                manifest = self._resolve_manifest(
                    conn, thought, list(current["refs"]), 1, include_content=False
                )
            except (ValidationError, NotFound) as exc:
                failure = self._default_failure(exc, list(current["labels"]))
                if failure is None:
                    raise
                status = "not_applied"
            else:
                status = "applied"
                changed = conn.execute(
                    "UPDATE refinement_thoughts SET aggregate_revision=2,attachment_revision=1,attachment_sha256=?,resume_order=?,updated_at=? WHERE id=? AND aggregate_revision=1 AND attachment_revision=0",
                    (manifest["attachment_sha256"], RefinementThoughtRepository.next_resume_order(conn),
                     occurred_at, thought["id"]),
                )
                if changed.rowcount != 1:
                    raise ConflictError("Thought changed during default application",
                                        code="default_context_birth_invalid")
                self._persist_manifest(conn, str(thought["id"]), 2, manifest, occurred_at)
                updated = dict(conn.execute(
                    "SELECT * FROM refinement_thoughts WHERE id=?", (thought["id"],)
                ).fetchone())
                RefinementThoughtRepository.insert_command(
                    conn, updated, command_kind="replace_attachments",
                    prior_working_revision=1, prior_lifecycle_revision=1,
                    prior_attachment_revision=0, working_sha256=working_sha256,
                    lifecycle_sha256=None, accepted_at=occurred_at,
                )
                attachments = [{"ref": item["ref"], "title": item["title"],
                                "leaf_count": len(item["leaves"])}
                               for item in manifest["visible"]]
        application_id = f"rdapp_{uuid.uuid4().hex[:12]}"
        attribution = self._failure_attribution(failure, list(current["labels"]))
        failure_raw = canonical_json(attribution)
        receipt = {"id": application_id, "action": "apply_default_context",
                   "scope": "this_thought", "thought_id": str(thought["id"]),
                   "default_revision": current["revision"],
                   "default_configuration_sha256": current["configuration_sha256"],
                   "status": status, "attachment_zero_sha256": zero_hash,
                   "attachment_revision": int(updated["attachment_revision"]),
                   "attachment_sha256": str(updated["attachment_sha256"]),
                   "attachments": attachments, "failure": failure}
        conn.execute(
            "INSERT INTO refinement_default_context_applications"
            "(application_id,thought_id,create_request_id,default_revision,default_configuration_sha256,status,attachment_zero_sha256,attachment_revision,attachment_sha256,error_code,failure_json,failure_sha256,receipt_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (application_id, thought["id"], create_request_id, current["revision"],
             current["configuration_sha256"], status, zero_hash,
             updated["attachment_revision"], updated["attachment_sha256"],
             str((failure or {}).get("code") or ""),
             failure_raw.decode("utf-8"), _sha(failure_raw),
             canonical_json(receipt).decode("utf-8"), occurred_at),
        )
        return updated, receipt

    def list_context(self, principal: Principal, thought_id: str, *, query: str = "",
                     view: str = "compact", cursor: str | None = None,
                     limit: int = 20) -> dict[str, Any]:
        self._owner(principal)
        if view not in {"compact", "browse"}:
            raise ValidationError("context view must be compact or browse", code="context_view_invalid")
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            raise ValidationError("context limit must be between 1 and 50", code="context_limit_invalid")
        with self._db._connection() as conn:
            thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if thought is None:
                raise NotFound("thought", thought_id)
            default_context = self._default_projection_in_transaction(conn)
            default_refs = set(default_context["refs"])
            attachments = self.project_in_transaction(conn, dict(thought))
            for item in attachments:
                item["is_default"] = item["ref"] in default_refs
            selected = {item["ref"]: item for item in attachments}
            pinned: list[dict[str, Any]] = []
            try:
                pinned.append(self._candidate(conn, EVERYDAY_CONTEXT_REF, thought, selected, default_refs))
            except (ValidationError, NotFound):
                pass
            recent: list[dict[str, Any]] = []
            rows = conn.execute(
                "SELECT visible_ref,MAX(rowid) recent_order FROM refinement_context_actions "
                "WHERE action_kind='attach' GROUP BY visible_ref "
                "ORDER BY recent_order DESC",
            ).fetchall()
            for row in rows:
                if len(recent) == 3:
                    break
                ref = str(row["visible_ref"])
                if ref == EVERYDAY_CONTEXT_REF:
                    continue
                try:
                    recent.append(self._candidate(conn, ref, thought, selected, default_refs))
                except (ValidationError, NotFound):
                    continue
            results: list[dict[str, Any]] = []
            next_cursor = None
            text = str(query or "").strip()
            query_bytes = len(text.encode("utf-8"))
            if query_bytes > 500:
                raise ValidationError("context query must be at most 500 UTF-8 bytes",
                                      code="context_query_too_large",
                                      context={"observed": query_bytes, "allowed": 500})
            if text or view == "browse":
                after_title, after_id = self._decode_cursor(cursor) if cursor else ("", "")
                values: list[Any] = [thought["working_note_id"]]
                clauses = ["deleted=0", "id!=?"]
                if text:
                    clauses.append("title LIKE ? ESCAPE '\\' COLLATE NOCASE")
                    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                    values.append(f"%{escaped}%")
                if cursor:
                    clauses.append("(title COLLATE NOCASE > ? COLLATE NOCASE OR (title COLLATE NOCASE = ? COLLATE NOCASE AND id > ?))")
                    values.extend([after_title, after_title, after_id])
                values.append(limit + 1)
                note_rows = conn.execute(
                    "SELECT id,title FROM notes WHERE " + " AND ".join(clauses)
                    + " ORDER BY title COLLATE NOCASE,id LIMIT ?", values,
                ).fetchall()
                page = note_rows[:limit]
                for note in page:
                    results.append(self._candidate(conn, f"note:{note['id']}", thought, selected, default_refs))
                if len(note_rows) > limit and page:
                    next_cursor = self._encode_cursor(str(page[-1]["title"]), str(page[-1]["id"]))
            return {"attachments": attachments, "default_context": default_context,
                    "pinned": pinned, "recent": recent,
                    "results": results, "next_cursor": next_cursor}

    def attach_context(self, principal: Principal, thought_id: str, *, visible_ref: str,
                       request_id: str, expected_aggregate_revision: int,
                       expected_working_revision: int, expected_attachment_revision: int,
                       workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._mutate(principal, thought_id, "attach", visible_ref, request_id,
                            expected_aggregate_revision, expected_working_revision,
                            expected_attachment_revision, workspace_cursor)

    def detach_context(self, principal: Principal, thought_id: str, *, visible_ref: str,
                       request_id: str, expected_aggregate_revision: int,
                       expected_working_revision: int, expected_attachment_revision: int,
                       workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._mutate(principal, thought_id, "detach", visible_ref, request_id,
                            expected_aggregate_revision, expected_working_revision,
                            expected_attachment_revision, workspace_cursor)

    def refresh_context(self, principal: Principal, thought_id: str, *, visible_ref: str,
                        request_id: str, expected_aggregate_revision: int,
                        expected_working_revision: int, expected_attachment_revision: int,
                        workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._mutate(principal, thought_id, "refresh", visible_ref, request_id,
                            expected_aggregate_revision, expected_working_revision,
                            expected_attachment_revision, workspace_cursor)

    def _mutate(self, principal: Principal, thought_id: str, action: str, raw_ref: str,
                request_id: str, expected_aggregate: int, expected_working: int,
                expected_attachment: int, workspace_cursor: dict[str, Any] | None = None) -> dict[str, Any]:
        self._owner(principal)
        request_id = str(request_id or "").strip()
        try:
            ref = qualified_ref(raw_ref)
        except ValueError as exc:
            raise ValidationError(str(exc), code="context_ref_invalid") from exc
        if not request_id or not all(isinstance(x, int) for x in (expected_aggregate, expected_working, expected_attachment)):
            raise ValidationError("context request id and cursors are required", code="context_request_required")
        semantic = {"action": action, "thought_id": thought_id, "ref": ref,
                    "aggregate": expected_aggregate, "working": expected_working,
                    "attachment": expected_attachment}
        request_hash = _sha(canonical_json(semantic))
        with self._db._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            thought_row = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if thought_row is None:
                raise NotFound("thought", thought_id)
            thought = dict(thought_row)
            prior = conn.execute("SELECT * FROM refinement_context_actions WHERE request_id=?", (request_id,)).fetchone()
            if prior is not None:
                if str(prior["request_sha256"]) != request_hash:
                    raise ConflictError("context request id was reused", code="context_request_payload_mismatch")
                if int(thought["aggregate_revision"]) != int(prior["post_aggregate_revision"]):
                    raise ConflictError("context request was superseded", code="context_request_superseded",
                                        context={"current": self._thought_dto(conn, thought)})
                return {"thought": self._thought_dto(conn, thought),
                        "receipt": self._receipt(conn, dict(prior), thought)}
            from .refinement_thought_service import RefinementThoughtService
            RefinementThoughtService(self._db)._validate_workspace_cursor_in_transaction(
                conn, thought, workspace_cursor
            )
            if thought["state"] != "working" or (int(thought["aggregate_revision"]), int(thought["working_revision"]), int(thought["attachment_revision"])) != (expected_aggregate, expected_working, expected_attachment):
                raise ConflictError("thought context changed elsewhere", code="thought_revision_conflict",
                                    context={"current": self._thought_dto(conn, thought)})
            prior_attachments = self.project_in_transaction(conn, thought)
            prior_target = next((item for item in prior_attachments if item["ref"] == ref), None)
            refs = [x["ref"] for x in self._stored_visible(conn, thought_id, expected_attachment)]
            if action == "attach" and ref not in refs:
                refs.append(ref)
            elif action == "detach":
                refs = [item for item in refs if item != ref]
            elif action == "refresh" and ref not in refs:
                raise ConflictError("context is not attached", code="context_not_attached")
            next_revision = expected_attachment + 1
            manifest = self._resolve_manifest(conn, thought, refs, next_revision, include_content=False)
            current_hash = str(thought.get("attachment_sha256") or RefinementThoughtRepository.empty_attachment_hash(thought_id))
            # Hash includes revision. Compare semantic visible hashes for a true no-op.
            current_items = self._stored_visible(conn, thought_id, expected_attachment)
            unchanged = [(x["ref"], x["visible_sha256"]) for x in current_items] == [
                (x["ref"], x["visible_sha256"]) for x in manifest["visible"]
            ]
            now = _now()
            post_aggregate, post_attachment, post_hash = expected_aggregate, expected_attachment, current_hash
            if not unchanged:
                post_aggregate, post_attachment, post_hash = expected_aggregate + 1, next_revision, manifest["attachment_sha256"]
                conn.execute("UPDATE refinement_thoughts SET aggregate_revision=?,attachment_revision=?,attachment_sha256=?,resume_order=?,updated_at=? WHERE id=? AND aggregate_revision=? AND attachment_revision=? AND state='working'",
                             (post_aggregate, post_attachment, post_hash, RefinementThoughtRepository.next_resume_order(conn), now,
                              thought_id, expected_aggregate, expected_attachment))
                updated = dict(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
                self._persist_manifest(conn, thought_id, post_aggregate, manifest, now)
                working = conn.execute("SELECT content_sha256 FROM refinement_working_revisions WHERE thought_id=? AND revision=?",
                                       (thought_id, expected_working)).fetchone()
                RefinementThoughtRepository.insert_command(conn, updated, command_kind="replace_attachments",
                    prior_working_revision=expected_working, prior_lifecycle_revision=int(thought["lifecycle_revision"]),
                    prior_attachment_revision=expected_attachment, working_sha256=str(working["content_sha256"]),
                    lifecycle_sha256=None, accepted_at=now)
                conn.execute("UPDATE refinement_invocations SET state='superseded',terminal_code='owner_context_changed',updated_at=?,terminal_at=? WHERE thought_id=? AND state IN ('reserved','in_flight','awaiting_projection','review_ready')",
                             (now, now, thought_id))
                thought = updated
                RefinementThoughtService._bump_continuity(conn, thought_id)
                thought = dict(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            action_id = f"rctx_{uuid.uuid4().hex[:12]}"
            post_attachments = self.project_in_transaction(conn, thought)
            post_target = next((item for item in post_attachments if item["ref"] == ref), None)
            target = prior_target if action == "detach" else post_target
            title = str(target["title"]) if target is not None else ref
            leaves = list(target["leaves"]) if target is not None else []
            receipt = {"id": action_id, "action": action, "scope": "this_thought",
                       "default_context_changed": False, "title": title, "ref": ref,
                       "leaf_count": len(leaves), "leaves": leaves,
                       "attachment_revision": post_attachment,
                       "attachment_sha256": post_hash}
            if workspace_cursor is not None:
                receipt["committed_post_cursor"] = {
                           "hub_id": RefinementThoughtService._workspace_hub_id(conn),
                           "thought_id": thought_id,
                           "aggregate_revision": int(thought["aggregate_revision"]),
                           "continuity_revision": int(thought["continuity_revision"]),
                       }
            conn.execute("INSERT INTO refinement_context_actions(action_id,request_id,request_sha256,thought_id,action_kind,visible_ref,prior_aggregate_revision,prior_attachment_revision,post_aggregate_revision,post_attachment_revision,post_attachment_sha256,receipt_json,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (action_id, request_id, request_hash, thought_id, action, ref, expected_aggregate,
                          expected_attachment, post_aggregate, post_attachment, post_hash,
                          canonical_json(receipt).decode("utf-8"), now))
            thought = dict(conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone())
            row = dict(conn.execute("SELECT * FROM refinement_context_actions WHERE action_id=?", (action_id,)).fetchone())
            return {"thought": self._thought_dto(conn, thought), "receipt": self._receipt(conn, row, thought)}

    def materialize(self, thought_id: str, attachment_revision: int,
                    attachment_sha256: str) -> FrozenGroundingSnapshot:
        with self._db._connection() as conn:
            conn.execute("BEGIN")
            thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
            if thought is None:
                raise NotFound("thought", thought_id)
            stored = self._verified_stored_visible(conn, thought_id, attachment_revision, attachment_sha256)
            refs = [x["ref"] for x in stored]
            manifest = self._resolve_manifest(conn, dict(thought), refs, attachment_revision, include_content=True)
            if manifest["attachment_sha256"] != attachment_sha256:
                raise self._stale_conflict(conn, dict(thought))
            return self._snapshot(manifest)

    def validate_frozen_in_transaction(self, conn: Any, thought_id: str,
                                       attachment_revision: int,
                                       attachment_sha256: str) -> None:
        thought = conn.execute("SELECT * FROM refinement_thoughts WHERE id=?", (thought_id,)).fetchone()
        if thought is None:
            raise NotFound("thought", thought_id)
        stored = self._verified_stored_visible(conn, thought_id, attachment_revision, attachment_sha256)
        refs = [x["ref"] for x in stored]
        manifest = self._resolve_manifest(conn, dict(thought), refs, attachment_revision, include_content=False)
        if manifest["attachment_sha256"] != attachment_sha256:
            raise self._stale_conflict(conn, dict(thought))

    def project_in_transaction(self, conn: Any, thought: dict[str, Any]) -> list[dict[str, Any]]:
        stored = self._verified_stored_visible(
            conn, str(thought["id"]), int(thought["attachment_revision"]),
            str(thought.get("attachment_sha256") or RefinementThoughtRepository.empty_attachment_hash(str(thought["id"]))),
        )
        result: list[dict[str, Any]] = []
        for item in stored:
            state = "current"
            try:
                current = self._resolve_manifest(conn, thought, [item["ref"]], 1, include_content=False)["visible"][0]
                if current["visible_sha256"] != item["visible_sha256"]:
                    state = "stale"
            except (ValidationError, NotFound):
                state = "missing"
            result.append({"ref": item["ref"], "kind": item["kind"], "title": item["title"],
                           "leaf_count": len(item["leaves"]), "state": state,
                           "leaves": [{"ref": x["ref"], "title": x["title"],
                                       "version_label": x["source_last_modified"],
                                       "content_sha256": x["leaf_content_sha256"]} for x in item["leaves"]]})
        return result

    def used_context_in_transaction(self, conn: Any, thought_id: str,
                                    revision: int) -> dict[str, Any] | None:
        visible = self._verified_stored_visible(conn, thought_id, revision, None)
        if not visible:
            return None
        attachments = [{"ref": x["ref"], "kind": x["kind"], "title": x["title"],
                        "leaf_count": len(x["leaves"]),
                        "leaves": [{"ref": leaf["ref"], "title": leaf["title"],
                                    "version_label": leaf["source_last_modified"]} for leaf in x["leaves"]]} for x in visible]
        leaves = sum(x["leaf_count"] for x in attachments)
        summary = "Used " + " · ".join(f"{x['title']} · {x['leaf_count']} note{'s' if x['leaf_count'] != 1 else ''}" for x in attachments)
        return {"visible_count": len(attachments), "leaf_count": leaves,
                "summary": summary, "attachments": attachments}

    def _candidate(self, conn: Any, ref: str, thought: Any,
                   selected: dict[str, dict[str, Any]],
                   default_refs: set[str] | None = None) -> dict[str, Any]:
        manifest = self._resolve_manifest(conn, dict(thought), [ref], 1, include_content=False)
        item = manifest["visible"][0]
        disabled_reason = ""
        selected_leaves = {leaf["ref"]: owner["title"] for owner in selected.values() for leaf in owner.get("leaves", [])}
        overlap = next((selected_leaves[x["ref"]] for x in item["leaves"] if x["ref"] in selected_leaves and ref not in selected), "")
        if overlap:
            disabled_reason = f"Included in {overlap}"
        return {"ref": ref, "kind": item["kind"], "title": item["title"],
                "leaf_count": len(item["leaves"]), "state": "current",
                "is_default": ref in (default_refs or set()),
                "selected": ref in selected, "disabled": bool(disabled_reason),
                "disabled_reason": disabled_reason}

    def _resolve_manifest(self, conn: Any, thought: dict[str, Any], refs: list[str],
                          revision: int, *, include_content: bool) -> dict[str, Any]:
        refs = sorted(dict.fromkeys(refs))
        if len(refs) > MAX_VISIBLE:
            raise ValidationError("too many visible context selections", code="context_too_large",
                                  context={"observed": len(refs), "allowed": MAX_VISIBLE})
        visible: list[dict[str, Any]] = []
        leaf_owner: dict[str, tuple[str, str]] = {}
        prompt_leaves: list[dict[str, str]] = []
        for ref in refs:
            kind, _, rid = ref.partition(":")
            if kind == "note":
                note = conn.execute("SELECT * FROM notes WHERE id=?", (rid,)).fetchone()
                if note is None or note["deleted"]:
                    missing_title = str(note["title"]) if note is not None else ref
                    raise ValidationError("context Note is unavailable", code="context_missing",
                                          context={"visible_ref": ref,
                                                   "visible_title": missing_title,
                                                   "leaf_ref": ref,
                                                   "leaf_title": missing_title})
                title = str(note["title"])
                if rid == str(thought["working_note_id"]):
                    raise ValidationError("a Thought cannot attach its own working Note",
                                          code="context_self_reference",
                                          context={"visible_ref": ref, "visible_title": title,
                                                   "leaf_ref": ref, "leaf_title": title})
                leaves = [self._leaf(note, ref, "")]
                modified = str(note["last_modified"])
            elif ref == EVERYDAY_CONTEXT_REF:
                kb = conn.execute("SELECT * FROM kbs WHERE id=? AND deleted=0", (rid,)).fetchone()
                if kb is None:
                    raise ValidationError("context is unavailable", code="context_missing",
                                          context={"visible_ref": ref, "visible_title": ref})
                title, modified = str(kb["name"]), str(kb["last_modified"])
                members = conn.execute("SELECT * FROM knowledge_memberships WHERE knowledge_id=? AND deleted=0 ORDER BY resource_ref", (rid,)).fetchall()
                if not members:
                    raise ValidationError("Everyday context has no supported Notes", code="context_empty",
                                          context={"visible_ref": ref, "visible_title": title})
                leaves = []
                for member in members:
                    member_ref = qualified_ref(member["resource_ref"])
                    if not member_ref.startswith("note:"):
                        raise ValidationError("Everyday context contains an unsupported item",
                                              code="context_kind_unsupported",
                                              context={"visible_ref": ref,
                                                       "visible_title": title,
                                                       "leaf_ref": member_ref,
                                                       "leaf_title": member_ref})
                    note_id = member_ref.split(":", 1)[1]
                    note = conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone()
                    if note is None or note["deleted"]:
                        missing_title = (str(note["title"])
                                         if note is not None else member_ref)
                        raise ValidationError("context Note is unavailable", code="context_missing",
                                              context={"visible_ref": ref,
                                                       "visible_title": title,
                                                       "leaf_ref": member_ref,
                                                       "leaf_title": missing_title})
                    leaf_title = str(note["title"])
                    if note_id == str(thought["working_note_id"]):
                        raise ValidationError("Everyday context contains this working Note",
                                              code="context_self_reference",
                                              context={"visible_ref": ref,
                                                       "visible_title": title,
                                                       "leaf_ref": member_ref,
                                                       "leaf_title": leaf_title})
                    leaves.append(self._leaf(note, member_ref, str(member["last_modified"])))
            else:
                raise ValidationError("context kind is not supported here", code="context_kind_unsupported",
                                      context={"visible_ref": ref, "visible_title": ref})
            leaves.sort(key=lambda x: x["ref"])
            for leaf in leaves:
                prior = leaf_owner.get(leaf["ref"])
                if prior:
                    raise ValidationError(f"{leaf['title']} is included in both {prior[1]} and {title}",
                                          code="context_leaf_overlap",
                                          context={"first_ref": prior[0], "first": prior[1],
                                                   "second_ref": ref, "second": title,
                                                   "leaf_ref": leaf["ref"],
                                                   "leaf_title": leaf["title"]})
                leaf_owner[leaf["ref"]] = (ref, title)
                prompt_leaf = {"content": leaf.pop("content"), "content_sha256": leaf["leaf_content_sha256"],
                               "ref": leaf["ref"], "title": leaf["title"]}
                block = _prompt_json(prompt_leaf).encode("utf-8")
                if len(block) > MAX_LEAF_BYTES:
                    raise ValidationError("context Note is too large", code="context_too_large",
                                          context={"visible_ref": ref, "visible_title": title,
                                                   "leaf_ref": leaf["ref"],
                                                   "leaf_title": leaf["title"],
                                                   "observed": len(block),
                                                   "allowed": MAX_LEAF_BYTES})
                prompt_leaves.append(prompt_leaf)
            membership = [{"leaf_ref": x["ref"],
                           "leaf_metadata_sha256": x["leaf_metadata_sha256"]} for x in leaves]
            visible_hash = _sha(canonical_json({"visible_ref": ref, "visible_kind": kind,
                "visible_title": title, "source_last_modified": modified, "membership": membership}))
            visible.append({"ref": ref, "kind": kind, "title": title, "source_last_modified": modified,
                            "visible_sha256": visible_hash, "leaves": leaves})
        if len(leaf_owner) > MAX_LEAVES:
            raise ValidationError("attached context has too many Notes", code="context_too_large",
                                  context={"observed": len(leaf_owner), "allowed": MAX_LEAVES})
        prompt_leaves.sort(key=lambda x: x["ref"])
        material = (_OPEN + _prompt_json(prompt_leaves) + _CLOSE) if prompt_leaves else ""
        size = len(material.encode("utf-8"))
        if size > MAX_CONTEXT_BYTES:
            raise ValidationError("attached context is too large", code="context_too_large",
                                  context={"observed": size, "allowed": MAX_CONTEXT_BYTES})
        identity = {"schema_version": 1, "thought_id": str(thought["id"]),
                    "attachment_revision": revision,
                    "visible": [{"visible_ref": x["ref"], "visible_sha256": x["visible_sha256"],
                                 "leaves": [{"leaf_ref": leaf["ref"], "leaf_metadata_sha256": leaf["leaf_metadata_sha256"]} for leaf in x["leaves"]]} for x in visible]}
        return {"revision": revision, "attachment_sha256": _sha(canonical_json(identity)),
                "visible": visible, "material": material if include_content else "", "byte_count": size}

    @staticmethod
    def _leaf(note: Any, ref: str, membership_modified: str) -> dict[str, Any]:
        tags = json.loads(note["tags_json"])
        content_hash = _sha(canonical_json({"ref": ref, "title": str(note["title"]),
            "body_markdown": str(note["body_markdown"]), "tags": tags,
            "last_modified": str(note["last_modified"]), "deleted": False}))
        title, source_modified = str(note["title"]), str(note["last_modified"])
        metadata_hash = RefinementThoughtRepository.attachment_leaf_metadata_hash(
            ref=ref, title=title, source_last_modified=source_modified,
            membership_last_modified=membership_modified,
            leaf_content_sha256=content_hash,
        )
        return {"ref": ref, "title": title, "source_last_modified": source_modified,
                "membership_last_modified": membership_modified, "leaf_content_sha256": content_hash,
                "leaf_metadata_sha256": metadata_hash,
                "content": str(note["body_markdown"])}

    @staticmethod
    def _persist_manifest(conn: Any, thought_id: str, aggregate_revision: int,
                          manifest: dict[str, Any], now: str) -> None:
        conn.execute("INSERT INTO refinement_attachment_revisions(thought_id,attachment_revision,aggregate_revision,attachment_sha256,visible_count,leaf_count,created_at) VALUES(?,?,?,?,?,?,?)",
                     (thought_id, manifest["revision"], aggregate_revision, manifest["attachment_sha256"],
                      len(manifest["visible"]), sum(len(x["leaves"]) for x in manifest["visible"]), now))
        for vi, item in enumerate(manifest["visible"]):
            conn.execute("INSERT INTO refinement_attachment_visible(thought_id,attachment_revision,ordinal,visible_ref,visible_kind,visible_title,source_last_modified,visible_sha256) VALUES(?,?,?,?,?,?,?,?)",
                         (thought_id, manifest["revision"], vi, item["ref"], item["kind"], item["title"], item["source_last_modified"], item["visible_sha256"]))
            for li, leaf in enumerate(item["leaves"]):
                conn.execute("INSERT INTO refinement_attachment_leaves(thought_id,attachment_revision,visible_ordinal,leaf_ordinal,leaf_ref,leaf_title,source_last_modified,membership_last_modified,leaf_content_sha256,leaf_metadata_sha256) VALUES(?,?,?,?,?,?,?,?,?,?)",
                             (thought_id, manifest["revision"], vi, li, leaf["ref"], leaf["title"], leaf["source_last_modified"], leaf["membership_last_modified"], leaf["leaf_content_sha256"], leaf["leaf_metadata_sha256"]))

    @staticmethod
    def _stored_visible(conn: Any, thought_id: str, revision: int,
                        include_leaves: bool = False) -> list[dict[str, Any]]:
        if revision == 0:
            return []
        rows = conn.execute("SELECT * FROM refinement_attachment_visible WHERE thought_id=? AND attachment_revision=? ORDER BY ordinal", (thought_id, revision)).fetchall()
        out = []
        for row in rows:
            item = {"ref": str(row["visible_ref"]), "kind": str(row["visible_kind"]),
                    "title": str(row["visible_title"]), "source_last_modified": str(row["source_last_modified"]),
                    "visible_sha256": str(row["visible_sha256"]), "leaves": []}
            if include_leaves:
                leaves = conn.execute("SELECT * FROM refinement_attachment_leaves WHERE thought_id=? AND attachment_revision=? AND visible_ordinal=? ORDER BY leaf_ordinal", (thought_id, revision, row["ordinal"])).fetchall()
                item["leaves"] = [{"ref": str(x["leaf_ref"]), "title": str(x["leaf_title"]),
                                   "source_last_modified": str(x["source_last_modified"]),
                                   "membership_last_modified": str(x["membership_last_modified"]),
                                   "leaf_content_sha256": str(x["leaf_content_sha256"]),
                                   "leaf_metadata_sha256": str(x["leaf_metadata_sha256"])} for x in leaves]
            out.append(item)
        return out

    def _verified_stored_visible(self, conn: Any, thought_id: str, revision: int,
                                 expected_hash: str | None) -> list[dict[str, Any]]:
        empty_hash = RefinementThoughtRepository.empty_attachment_hash(thought_id)
        if revision == 0:
            if expected_hash is not None and expected_hash != empty_hash:
                raise ConflictError("empty context hash is invalid", code="refinement_context_ledger_invalid")
            return []
        header = conn.execute(
            "SELECT * FROM refinement_attachment_revisions WHERE thought_id=? AND attachment_revision=?",
            (thought_id, revision),
        ).fetchone()
        if header is None:
            raise ConflictError("attached context revision is incomplete", code="refinement_context_ledger_invalid")
        header_hash = str(header["attachment_sha256"])
        if expected_hash is not None and header_hash != expected_hash:
            raise ConflictError("attached context revision hash does not match", code="refinement_context_ledger_invalid")
        command = conn.execute(
            "SELECT * FROM refinement_aggregate_commands WHERE thought_id=? AND aggregate_revision=?",
            (thought_id, int(header["aggregate_revision"])),
        ).fetchone()
        if (command is None or str(command["command_kind"]) != "replace_attachments"
                or int(command["canonical_version"]) != 2
                or int(command["next_attachment_revision"]) != revision
                or str(command["attachment_sha256"] or "") != header_hash):
            raise ConflictError("attached context revision header is invalid", code="refinement_context_ledger_invalid")
        visible_rows = conn.execute(
            "SELECT * FROM refinement_attachment_visible WHERE thought_id=? AND attachment_revision=? ORDER BY ordinal",
            (thought_id, revision),
        ).fetchall()
        if len(visible_rows) != int(header["visible_count"]) or len(visible_rows) > MAX_VISIBLE:
            raise ConflictError("attached context visible rows are incomplete", code="refinement_context_ledger_invalid")
        refs = [str(row["visible_ref"]) for row in visible_rows]
        if [int(row["ordinal"]) for row in visible_rows] != list(range(len(visible_rows))) or refs != sorted(refs):
            raise ConflictError("attached context visible ordinals are invalid", code="refinement_context_ledger_invalid")
        visible: list[dict[str, Any]] = []
        all_leaves: set[str] = set()
        identity_visible: list[dict[str, Any]] = []
        for row in visible_rows:
            ordinal, ref, kind = int(row["ordinal"]), str(row["visible_ref"]), str(row["visible_kind"])
            leaves_rows = conn.execute(
                "SELECT * FROM refinement_attachment_leaves WHERE thought_id=? AND attachment_revision=? AND visible_ordinal=? ORDER BY leaf_ordinal",
                (thought_id, revision, ordinal),
            ).fetchall()
            leaf_refs = [str(leaf["leaf_ref"]) for leaf in leaves_rows]
            if ([int(leaf["leaf_ordinal"]) for leaf in leaves_rows] != list(range(len(leaves_rows)))
                    or leaf_refs != sorted(leaf_refs)):
                raise ConflictError("attached context leaf ordinals are invalid", code="refinement_context_ledger_invalid")
            leaves: list[dict[str, Any]] = []
            membership: list[dict[str, str]] = []
            for leaf in leaves_rows:
                leaf_ref = str(leaf["leaf_ref"])
                if not leaf_ref.startswith("note:") or leaf_ref in all_leaves:
                    raise ConflictError("attached context leaves overlap or are invalid", code="refinement_context_ledger_invalid")
                item = {"ref": leaf_ref, "title": str(leaf["leaf_title"]),
                        "source_last_modified": str(leaf["source_last_modified"]),
                        "membership_last_modified": str(leaf["membership_last_modified"]),
                        "leaf_content_sha256": str(leaf["leaf_content_sha256"]),
                        "leaf_metadata_sha256": str(leaf["leaf_metadata_sha256"])}
                expected_metadata = RefinementThoughtRepository.attachment_leaf_metadata_hash(
                    ref=item["ref"], title=item["title"],
                    source_last_modified=item["source_last_modified"],
                    membership_last_modified=item["membership_last_modified"],
                    leaf_content_sha256=item["leaf_content_sha256"],
                )
                if item["leaf_metadata_sha256"] != expected_metadata:
                    raise ConflictError("attached context leaf metadata is invalid", code="refinement_context_ledger_invalid")
                all_leaves.add(leaf_ref)
                leaves.append(item)
                membership.append({"leaf_ref": leaf_ref, "leaf_metadata_sha256": expected_metadata})
            if kind not in {"note", "knowledge"} or (kind == "note" and (len(leaves) != 1 or leaf_refs != [ref])) or (kind == "knowledge" and not leaves):
                raise ConflictError("attached context membership is invalid", code="refinement_context_ledger_invalid")
            visible_hash = _sha(canonical_json({"visible_ref": ref, "visible_kind": kind,
                "visible_title": str(row["visible_title"]),
                "source_last_modified": str(row["source_last_modified"]),
                "membership": membership}))
            if visible_hash != str(row["visible_sha256"]):
                raise ConflictError("attached context visible hash is invalid", code="refinement_context_ledger_invalid")
            visible.append({"ref": ref, "kind": kind, "title": str(row["visible_title"]),
                            "source_last_modified": str(row["source_last_modified"]),
                            "visible_sha256": visible_hash, "leaves": leaves})
            identity_visible.append({"visible_ref": ref, "visible_sha256": visible_hash,
                "leaves": [{"leaf_ref": leaf["ref"], "leaf_metadata_sha256": leaf["leaf_metadata_sha256"]} for leaf in leaves]})
        if len(all_leaves) != int(header["leaf_count"]) or len(all_leaves) > MAX_LEAVES:
            raise ConflictError("attached context leaf count is invalid", code="refinement_context_ledger_invalid")
        computed = _sha(canonical_json({"schema_version": 1, "thought_id": thought_id,
            "attachment_revision": revision, "visible": identity_visible}))
        if computed != header_hash:
            raise ConflictError("attached context revision hash is invalid", code="refinement_context_ledger_invalid")
        return visible

    def _stale_conflict(self, conn: Any, thought: dict[str, Any]) -> ConflictError:
        attachments = self.project_in_transaction(conn, thought)
        names = [item["title"] for item in attachments if item["state"] != "current"]
        label = ", ".join(names) if names else "attached context"
        return ConflictError(f"attached context changed: {label}", code="refinement_context_stale",
                             context={"attachments": attachments, "names": names,
                                      "repair": "update_context"})

    def _snapshot(self, manifest: dict[str, Any]) -> FrozenGroundingSnapshot:
        attachments = [{"ref": x["ref"], "kind": x["kind"], "title": x["title"],
                        "leaf_count": len(x["leaves"]),
                        "leaves": [{"ref": leaf["ref"], "title": leaf["title"],
                                    "version_label": leaf["source_last_modified"]} for leaf in x["leaves"]]} for x in manifest["visible"]]
        leaf_count = sum(x["leaf_count"] for x in attachments)
        used = None
        if attachments:
            summary = "Used " + " · ".join(f"{x['title']} · {x['leaf_count']} note{'s' if x['leaf_count'] != 1 else ''}" for x in attachments)
            used = {"visible_count": len(attachments), "leaf_count": leaf_count,
                    "summary": summary, "attachments": attachments}
        echo = {"refs": [x["ref"] for x in attachments], "source_refs": [leaf["ref"] for x in attachments for leaf in x["leaves"]],
                "titles": [x["title"] for x in attachments], "attachment_sha256": manifest["attachment_sha256"],
                "selection": "explicit", "matched_count": leaf_count, "overflow_count": 0}
        if used is not None:
            echo["used_context"] = used
        return FrozenGroundingSnapshot(manifest["revision"], manifest["attachment_sha256"],
                                      manifest["material"], manifest["byte_count"], used, echo)

    def _receipt(self, conn: Any, action: dict[str, Any], thought: dict[str, Any]) -> dict[str, Any]:
        stored = str(action.get("receipt_json") or "").strip()
        if stored and stored != "{}":
            value = json.loads(stored)
            if isinstance(value, dict):
                return value
        attachments = self.project_in_transaction(conn, thought)
        target = next((x for x in attachments if x["ref"] == action["visible_ref"]), None)
        if target is None:
            title, leaves = str(action["visible_ref"]), []
        else:
            title, leaves = target["title"], target["leaves"]
        return {"id": str(action["action_id"]), "action": str(action["action_kind"]),
                "title": title, "ref": str(action["visible_ref"]), "leaf_count": len(leaves),
                "leaves": leaves, "attachment_revision": int(action["post_attachment_revision"]),
                "attachment_sha256": str(action["post_attachment_sha256"])}

    def _thought_dto(self, conn: Any, thought: dict[str, Any]) -> dict[str, Any]:
        from .refinement_thought_service import RefinementThoughtService
        return RefinementThoughtService(self._db)._dto_in_transaction(conn, dict(thought))

    @staticmethod
    def _encode_cursor(title: str, note_id: str) -> str:
        return base64.urlsafe_b64encode(canonical_json({"title": title, "id": note_id})).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(token: str) -> tuple[str, str]:
        try:
            raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
            value = json.loads(raw)
            return str(value["title"]), str(value["id"])
        except Exception as exc:
            raise ValidationError("context cursor is invalid", code="context_cursor_invalid") from exc


__all__ = ["RefinementContextService", "FrozenGroundingSnapshot", "EVERYDAY_CONTEXT_REF",
           "MAX_VISIBLE", "MAX_LEAVES", "MAX_LEAF_BYTES", "MAX_CONTEXT_BYTES"]
