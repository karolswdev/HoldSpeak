"""Typed ``desktop.type_text`` codec and content-free native receipts."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Mapping

from ..principals import PrincipalKind
from .model import Admission, KernelRefused, OperationRequest, forbidden_content, valid_ref

_GENERATION = re.compile(r"^[A-Za-z0-9_.:-]{1,160}$")
_GESTURES = frozenset(
    {
        "hold_release",
        "preview_type",
        "companion_send",
        "wake_utterance",
        "wake_preview_type",
    }
)
_ALLOWED = frozenset(
    {
        "text",
        "submit",
        "expected_generation",
        "native_id",
        "gesture",
        "target_profile",
        "preview_ref",
        "macro_ref",
        "requested_target",
        "delivery_method",
    }
)


class DesktopTypeTextCodec:
    name = "desktop.type_text"
    version = 1

    def __init__(self, receipts: Any) -> None:
        self._receipts = receipts

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        unknown = set(args) - _ALLOWED
        if unknown:
            raise KernelRefused("operation_field_not_allowed", sorted(unknown)[0])
        text = args.get("text")
        submit = args.get("submit")
        generation = str(args.get("expected_generation") or "").strip()
        native_id = str(args.get("native_id") or "").strip()
        gesture = str(args.get("gesture") or "").strip()
        if (
            not isinstance(text, str)
            or not text.strip()
            or not isinstance(submit, bool)
            or not request.target_ref.startswith("desktop-input:")
            or not valid_ref(request.target_ref)
            or not _GENERATION.fullmatch(generation)
            or gesture not in _GESTURES
        ):
            raise KernelRefused("desktop_type_text_prerequisite_failed")
        try:
            uuid.UUID(native_id)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("desktop_type_text_native_id_invalid") from exc
        material = {
            "name": request.name,
            "version": request.version,
            "target_ref": request.target_ref,
            "placement": request.placement,
            "arguments": dict(args),
        }
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        payload_hash = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        refs = tuple(
            dict.fromkeys(
                (
                    *request.subject_refs,
                    *(
                        str(args[key])
                        for key in ("preview_ref", "macro_ref")
                        if str(args.get(key) or "") and valid_ref(str(args[key]))
                    ),
                    f"desktop-type:{native_id}",
                )
            )
        )
        return Admission(
            target_ref=request.target_ref,
            placement=request.placement,
            payload_hash=payload_hash,
            refs=refs,
            head=f"desktop text {len(text.encode('utf-8'))} bytes submit={submit}",
            ttl_seconds=30.0,
            native_id=native_id,
        )

    def authorize(
        self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str
    ) -> Admission:
        if principal.kind is not PrincipalKind.OWNER:
            raise KernelRefused("desktop_type_text_owner_gesture_required")
        return admission

    def admit(
        self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str
    ) -> None:
        return None

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    def record_receipt(
        self,
        *,
        request: OperationRequest,
        admission: Admission,
        operation_id: str,
        outcome: str,
        result_ref: str,
    ) -> dict[str, Any]:
        args = request.arguments
        metadata = {
            key: args[key]
            for key in (
                "target_profile",
                "preview_ref",
                "macro_ref",
                "requested_target",
                "delivery_method",
            )
            if args.get(key) not in (None, "")
        }
        return self._receipts.record(
            native_id=admission.native_id,
            operation_id=operation_id,
            target_ref=admission.target_ref,
            payload_sha256=admission.payload_hash,
            text_bytes=len(str(args["text"]).encode("utf-8")),
            submit=bool(args["submit"]),
            head=admission.head,
            authority_basis="direct_gesture",
            gesture=str(args["gesture"]),
            outcome=outcome,
            result_ref=result_ref,
            metadata=metadata,
        )

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        return self._receipts.get(native_id)

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        receipt = self._receipts.get(native_id)
        return [] if receipt is None else [receipt]

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        native = self._receipts.get(native_id)
        outcome = str((native or {}).get("outcome") or "unknown")
        generic = "ended" if outcome == "succeeded" else "failed" if native else "unknown"
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": self.name,
            "principal": operation["principal_identity"],
            "generic_state": generic,
            "domain_state": outcome,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
            "receipt_ref": f"desktop-type:{native_id}",
        }
