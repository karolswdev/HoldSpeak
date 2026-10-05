"""Typed ``voice_reference_resolve`` codec for kernel-admitted voice resolution.

HS-118-05: voice resolver calls go through the kernel for egress tracking
and terminal receipts.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .model import Admission, KernelRefused, OperationRequest


_REQUIRED_FIELDS = frozenset({"workbench_id", "profile_id", "transcript_hash"})


@dataclass(frozen=True)
class VoiceResolveAdmission(Admission):
    workbench_id: str = ""
    profile_id: str = ""
    transcript_hash: str = ""


class VoiceResolveCodec:
    """Validates voice resolution request, builds admission."""

    name = "voice_reference_resolve"
    version = 1

    def parse(self, request: OperationRequest) -> VoiceResolveAdmission:
        args = dict(request.arguments)
        missing = _REQUIRED_FIELDS - set(args)
        if missing:
            raise KernelRefused("missing_arguments", f"Missing: {missing}")

        workbench_id = str(args["workbench_id"]).strip()
        profile_id = str(args["profile_id"]).strip()
        transcript_hash = str(args["transcript_hash"]).strip()

        payload = json.dumps(
            {"workbench_id": workbench_id, "profile_id": profile_id, "transcript_hash": transcript_hash},
            separators=(",", ":"),
            sort_keys=True,
        )
        digest = "sha256:" + hashlib.sha256(payload.encode()).hexdigest()

        return VoiceResolveAdmission(
            target_ref=f"workbench:{workbench_id}",
            placement="propose",
            payload_hash=digest,
            refs=(f"workbench:{workbench_id}", f"profile:{profile_id}"),
            head=f"voice-resolve:{workbench_id}:{transcript_hash[:16]}",
            ttl_seconds=30.0,
            native_id=f"voice-resolve-{workbench_id}-{transcript_hash[:16]}",
            workbench_id=workbench_id,
            profile_id=profile_id,
            transcript_hash=transcript_hash,
        )

    def admit(
        self,
        request: OperationRequest,
        admission: Any,
        principal: Any,
        operation_id: str,
    ) -> None:
        """No side-effects on admission -- resolution happens outside the codec."""

    def decide(
        self,
        native_id: str,
        decision: str,
        principal: Any,
        reason: str = "",
    ) -> None:
        """Voice resolves auto-decide; no explicit owner decision needed."""
