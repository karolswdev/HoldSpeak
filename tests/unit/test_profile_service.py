"""ProfileService: profile and inference-target discovery is owner custody.

Successor of the parked source pin
``test_phase143_routing_authority_census::test_profile_service_owner_gate_is_enforced_before_lookup_or_probe``:
the same rule, proved through the service. Every call made by a principal that
is not the owner is refused with ``owner_principal_required`` before any lookup,
write or probe, and the owner reaches the data.
"""
from __future__ import annotations

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.profile_service import ProfileService

OWNER = Principal(PrincipalKind.OWNER, "owner")

CALLS = {
    "list_profiles": lambda s, p: s.list_profiles(p),
    "get_profile": lambda s, p: s.get_profile(p, "anything"),
    "create_profile": lambda s, p: s.create_profile(p, {"name": "Intruder", "kind": "openAICompatible"}),
    "update_profile": lambda s, p: s.update_profile(p, "anything", {"name": "x"}),
    "delete_profile": lambda s, p: s.delete_profile(p, "anything"),
    "list_inference_targets": lambda s, p: s.list_inference_targets(p),
    "probe_inference_target": lambda s, p: s.probe_inference_target(p, "anything"),
    "get_inference_target": lambda s, p: s.get_inference_target(p, "anything"),
}


@pytest.fixture
def service(tmp_path) -> ProfileService:
    return ProfileService(Database(tmp_path / "profiles.db"))


@pytest.mark.parametrize("method", sorted(CALLS))
@pytest.mark.parametrize(
    "principal",
    [None, Principal(PrincipalKind.AGENT, "agent-x"), Principal(PrincipalKind.SERVICE, "svc")],
    ids=["none", "agent", "service"],
)
def test_a_non_owner_is_refused_before_any_lookup(service, method, principal) -> None:
    before = service.list_profiles(OWNER)["profiles"]
    with pytest.raises(ServiceError) as refused:
        CALLS[method](service, principal)
    assert refused.value.code == "owner_principal_required"
    assert refused.value.context.get("status") == 403
    # Nothing was written: a refused create left no row.
    assert service.list_profiles(OWNER)["profiles"] == before


def test_the_owner_reaches_profiles_and_targets(service) -> None:
    assert isinstance(service.list_profiles(OWNER)["profiles"], list)
    assert isinstance(service.list_inference_targets(OWNER)["targets"], list)
