"""Owner-only write boundary for local profile-key custody."""
from __future__ import annotations

from typing import Any

from ..intel.providers import profile_key_env
from ..principals import Principal, PrincipalKind
from ..profile_key_store import ProfileKeyStore, ProfileKeyStoreError
from .errors import NotFound, ServiceError, ValidationError


class ProfileKeyService:
    MAX_VALUE_LENGTH = 4096

    def __init__(self, db: Any, *, store: ProfileKeyStore | None = None) -> None:
        self._db = db
        self._store = store or ProfileKeyStore()

    def set(self, principal: Principal | None, profile_id: str, body: dict[str, Any]) -> dict[str, Any]:
        self._owner(principal)
        value = self._value(body)
        profile = self._profile(profile_id)
        try:
            self._store.set(profile_key_env(str(profile.id)), value)
        except ProfileKeyStoreError as exc:
            raise ServiceError("profile_key_store_unavailable", "Profile key store is unavailable", context={"status": 503}) from None
        return {"success": True, "secret": {"required": bool(profile.requires_key), "present": True}}

    def delete(self, principal: Principal | None, profile_id: str) -> dict[str, Any]:
        self._owner(principal)
        profile = self._profile(profile_id)
        try:
            self._store.delete(profile_key_env(str(profile.id)))
        except ProfileKeyStoreError as exc:
            raise ServiceError("profile_key_store_unavailable", "Profile key store is unavailable", context={"status": 503}) from None
        return {"success": True, "secret": {"required": bool(profile.requires_key), "present": False}}

    def _profile(self, profile_id: str) -> Any:
        profile = self._db.profiles.get(profile_id)
        if profile is None:
            raise NotFound("destination", profile_id)
        if str(getattr(profile, "kind", "")) != "openAICompatible":
            raise ValidationError("Only endpoint destinations can use a key")
        return profile

    @staticmethod
    def _owner(principal: Principal | None) -> None:
        if principal is None or principal.kind is not PrincipalKind.OWNER:
            raise ServiceError("owner_principal_required", "Owner access is required", context={"status": 403})

    def _value(self, body: dict[str, Any]) -> str:
        if set(body) != {"value"}:
            raise ValidationError("Expected only a key value")
        value = body.get("value")
        if not isinstance(value, str):
            raise ValidationError("Key value is invalid")
        value = value.strip()
        if not value or len(value) > self.MAX_VALUE_LENGTH or any(char in value for char in ("\x00", "\r", "\n")):
            raise ValidationError("Key value is invalid")
        return value
