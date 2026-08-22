"""Owner projection and adoption seam for Phase 143 capability definitions."""
from __future__ import annotations

from typing import Any, Callable

from ..inference_capabilities import (
    InferenceCapabilityDefinition,
    InferenceCapabilityRegistry,
    process_inference_capability_registry,
)
from ..principals import Principal, PrincipalKind
from .errors import ServiceError


class InferenceCapabilityApplicationService:
    """One transport-neutral view over the process-composed registry.

    It intentionally has no database, profile, binding, assignment, deployment,
    or runner collaborator.  Story 04+ will ask this service to validate an
    exact capability before they resolve any of those mutable/executable facts.
    """

    def __init__(self, registry: InferenceCapabilityRegistry | None = None) -> None:
        self._registry = registry or process_inference_capability_registry()

    @property
    def registry(self) -> InferenceCapabilityRegistry:
        return self._registry

    @staticmethod
    def _require_owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError(
                "inference_capability_owner_required",
                "Owner access is required.",
                context={"status": 403},
            )

    def get_capabilities(self, principal: Principal) -> dict[str, Any]:
        self._require_owner(principal)
        return self._registry.owner_projection()

    def get_capability(self, principal: Principal, capability_id: str) -> dict[str, Any]:
        self._require_owner(principal)
        try:
            return self._registry.capability_projection(capability_id)
        except ValueError as exc:
            raise ServiceError(
                "unknown_inference_capability",
                "That intelligence capability is not registered on this hub.",
                context={"status": 404},
            ) from exc

    def require_before_profile_resolution(
        self,
        capability_id: str,
        profile_resolver: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> tuple[InferenceCapabilityDefinition, Any]:
        """The future resolver seam, intentionally ordered capability then profile."""
        return self._registry.require_before_profile_resolution(
            capability_id, profile_resolver, *args, **kwargs
        )


__all__ = ["InferenceCapabilityApplicationService"]
