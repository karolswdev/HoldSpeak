"""The owner's remote access and engine profiles: HTTP-only declared operations.

There is no tool schema here. A credential, a grant and a raw engine profile
belong to the owner; declaring their routes does not offer a new agent tool.
"""

from __future__ import annotations

from typing import Any, Callable

from holdspeak.operations import OperationDescriptor, _CONTRACT_REFUSALS
from holdspeak.services.errors import ValidationError


def _row(
    name: str,
    service: str,
    method: str,
    verb: str,
    path: str,
    handler: str,
    call: Callable[..., Any],
    result: str,
    *,
    status: int = 200,
) -> OperationDescriptor:
    write = verb != "GET"
    return OperationDescriptor(
        name=name,
        version=1,
        description=f"The owner's {method.replace('_', ' ')}.",
        args_schema={"type": "object"},
        principal="authenticated owner from the transport",
        effect="write" if write else "read",
        result=result,
        refusals=_CONTRACT_REFUSALS
        + ("owner_required", "ValidationError", "NotFound", "ConflictError"),
        completion="synchronous; the answer is the stored state or the probe observation",
        exposure=(f"http:{verb} {path}",),
        service=service,
        method=method,
        call=call,
        http=(verb, path),
        handler=handler,
        http_status=status,
        owner_only=True,
        owner_press=write,
        blocking_io=True,
        authority="egress" if method == "probe_profile" else "authority",
    )


_R = "/api/settings/remote"
_D = _R + "/delegations/{agent_identity}"
REMOTE_ACCESS_OPERATIONS = (
    _row(
        "settings.remote.get",
        "remote_access_service",
        "get_remote_settings",
        "GET",
        _R,
        "get_remote_settings",
        lambda s, p, a: s.get_remote_settings(p),
        "remote settings and credential metadata",
    ),
    _row(
        "settings.remote.update",
        "remote_access_service",
        "update_remote_settings",
        "PUT",
        _R,
        "update_remote_settings",
        lambda s, p, a: s.update_remote_settings(p, a),
        "{success, enabled, bind_host, port}",
    ),
    _row(
        "settings.remote.credential.create",
        "remote_access_service",
        "issue_credential",
        "POST",
        _R + "/credentials",
        "issue_credential",
        lambda s, p, a: s.issue_credential(
            p, {**a, "identity": a.get("agent_identity")}
        ),
        "one-time token, id, identity, palette and expiry; never recorded",
    ),
    _row(
        "settings.remote.credential.delete",
        "remote_access_service",
        "revoke_credential",
        "DELETE",
        _R + "/credentials/{credential_id}",
        "revoke_credential",
        lambda s, p, a: s.revoke_credential(p, a.get("credential_id")),
        "credential and grants revoked",
    ),
    _row(
        "settings.remote.delegation.put",
        "remote_access_service",
        "grant_delegation",
        "PUT",
        _D,
        "grant_delegation",
        lambda s, p, a: s.grant_delegation(p, a.get("agent_identity"), _body(a)),
        "desk grant",
    ),
    _row(
        "settings.remote.delegation.delete",
        "remote_access_service",
        "revoke_delegation",
        "DELETE",
        _D,
        "revoke_delegation",
        lambda s, p, a: s.revoke_delegation(p, a.get("agent_identity"), _body(a)),
        "desk revoke",
    ),
    _row(
        "settings.remote.project_delegation.put",
        "remote_access_service",
        "grant_project_delegation",
        "PUT",
        _D + "/projects/{project_id}",
        "grant_project_delegation",
        lambda s, p, a: s.grant_project_delegation(
            p, a.get("agent_identity"), a.get("project_id"), _body(a)
        ),
        "project grant",
    ),
    _row(
        "settings.remote.project_delegation.delete",
        "remote_access_service",
        "revoke_project_delegation",
        "DELETE",
        _D + "/projects/{project_id}",
        "revoke_project_delegation",
        lambda s, p, a: s.revoke_project_delegation(
            p, a.get("agent_identity"), a.get("project_id"), _body(a)
        ),
        "project revoke",
    ),
)


def _body(args: dict[str, Any]) -> Any:
    # Grant codecs must see a malformed/non-object body to receipt its refusal.
    return args.get("body", {})


def _integer(args: dict[str, Any], key: str) -> int | None:
    raw = args.get(key)
    try:
        return None if raw is None else int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{key} must be an integer", context={"response": {"error": f"{key} must be an integer"}}) from exc


_P = "/api/model-profiles"
PROFILE_OPERATIONS = (
    _row(
        "settings.profile.list",
        "owner_service",
        "list_profiles",
        "GET",
        _P,
        "api_list_model_profiles",
        lambda s, p, a: s.list_profiles(p),
        "profile list",
    ),
    _row(
        "settings.profile.create",
        "owner_service",
        "create_profile",
        "POST",
        _P,
        "api_create_model_profile",
        lambda s, p, a: {"profile": s.create_profile(p, a)},
        "{profile}",
        status=201,
    ),
    _row(
        "settings.profile.get",
        "owner_service",
        "get_profile",
        "GET",
        _P + "/{profile_id}",
        "api_get_model_profile",
        lambda s, p, a: {
            "profile": s.get_profile(
                p, a.get("profile_id"), revision=_integer(a, "revision")
            )
        },
        "{profile}",
    ),
    _row(
        "settings.profile.revise",
        "owner_service",
        "revise_profile",
        "POST",
        _P + "/{profile_id}/revisions",
        "api_revise_model_profile",
        lambda s, p, a: {"profile": s.revise_profile(p, a)},
        "{profile}",
        status=201,
    ),
    _row(
        "settings.profile.delete",
        "owner_service",
        "delete_profile",
        "DELETE",
        _P + "/{profile_id}",
        "api_delete_model_profile",
        lambda s, p, a: s.delete_profile(
            p, a.get("profile_id"), expected_revision=_integer(a, "expected_revision")
        ),
        "deleted profile",
    ),
    _row(
        "settings.profile.bind",
        "owner_service",
        "bind_profile",
        "POST",
        _P + "/{profile_id}/binding",
        "api_bind_model_profile",
        lambda s, p, a: {"binding": s.bind_profile(p, a)},
        "{binding}",
        status=201,
    ),
    _row(
        "settings.profile.probe",
        "owner_service",
        "probe_profile",
        "POST",
        _P + "/{profile_id}/probe",
        "api_probe_model_profile",
        lambda s, p, a: {"observation": s.probe_profile(p, a)},
        "{observation}",
        status=201,
    ),
    _row(
        "settings.profile.unbind",
        "owner_service",
        "unbind_profile",
        "DELETE",
        _P + "/{profile_id}/binding",
        "api_unbind_model_profile",
        lambda s, p, a: s.unbind_profile(
            p,
            a.get("profile_id"),
            expected_binding_revision=_integer(a, "expected_binding_revision"),
        ),
        "unbound profile",
    ),
)
