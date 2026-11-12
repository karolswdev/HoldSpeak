"""The provider verbs on the one declared contract (2026-11-09, ops/connections).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``). Each row states one verb of the GitHub, Jira or Confluence
adapter (``services/github_provider.py``, ``jira_provider.py``,
``confluence_provider.py``) once, through ``services/provider_service.py``
(the adapter the hub composed, or ``provider_not_configured``): ``web/routes/providers.py`` produces the
routes, ``mcp/families/declared.py`` the tools. The hand-written ``provider.*``
twins in ``mcp/families/project.py`` are parked.

The classes (the owner's table, ``mcp/tool_authority.py``):

* a probe of a connection, a discovery and a validation ask the provider
  under his own sign-in: egress, owner only, his press;
* adding or removing a connection row changes the system: config, his press;
* the manifest list and the stored connection rows read local state: evidence
  for anyone the edge admits;
* ``provider.github_pr_get`` (the review starter's agent reads the PR it is
  about, MCP M6) stays an agents' work read, as the owner's 2026-09-29 table
  says ("reads of his connected providers post nothing of his"); an agent
  reads only the repository delegated to its launch, within a read budget
  (Codex on #2140, ``services/github_provider.py``);
* ``provider.jira_search`` is the owner's (Codex on #2140): an agent's
  search would choose his account, any JQL and ``acli auth switch``.

No credential is an argument: gh and acli hold their own sign-ins.
"""
from __future__ import annotations

from typing import Any

from holdspeak.operations import _CONTRACT_REFUSALS, Admission, OperationDescriptor

_ANY = "derived by the transport (HTTP auth middleware; MCP auth resolver); the edge decides who reaches it"
_OWNER = "derived by the transport (HTTP auth middleware; MCP auth resolver); owner only"
_REF = {"type": "string", "minLength": 1, "description": "The connection: site|email (connections[].connection_ref)."}


def _schema(properties: dict[str, Any], required: tuple[str, ...] = ()) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": list(required), "additionalProperties": False}


def _row(name: str, service: str, method: str, call: Any, description: str, *, result: str,
         http: tuple[str, str] | None = None, handler: str | None = None, properties: dict[str, Any] | None = None,
         required: tuple[str, ...] = (), write: bool = False, egress: bool = False, config: bool = False,
         refusals: tuple[str, ...] = (), blocking_io: bool = True) -> OperationDescriptor:
    owner = egress or config
    props = dict(properties or {})
    if "." in method:  # an adapter's verb: the call reaches that adapter, or refuses provider_not_configured
        call = _on_adapter(method.split(".", 1)[0], call)
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object", "properties": props},
        principal=_OWNER if owner else _ANY, effect="write" if write else "read", result=result,
        refusals=_CONTRACT_REFUSALS + (("owner_required",) if owner else ()) + refusals,
        completion="synchronous", service=service, method=method,
        exposure=((f"http:{http[0]} {http[1]}",) if http else ()) + (f"mcp:{name}",),
        owner_only=owner, owner_press=owner, blocking_io=blocking_io, call=call, http=http, handler=handler,
        tool_schema=_schema(props, required), authority="egress" if egress else "config" if config else "work",
        thread="effect_proposal" if owner or write else "evidence_read",
    )


def _on_adapter(provider: str, call: Any) -> Any:
    def on(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        return call(service.adapter(provider), principal, args)

    return on


def _required(args: dict[str, Any], *names: str) -> list[str]:
    """The named string arguments, stripped; a missing one is refused by name."""
    from holdspeak.services.errors import ValidationError

    values = [str(args.get(name) or "").strip() for name in names]
    if not all(values):
        raise ValidationError(f"{' and '.join(names)} {'is' if len(names) == 1 else 'are'} required")
    return values


def _account_row(row: dict[str, Any], product: str) -> dict[str, Any]:
    """A stored connection row with its account and, when he must sign in again, the command (HS-166-04)."""
    ref = row.get("external_connection_ref") or row.get("connection_ref") or ""
    site, email = ref.split("|", 1) if "|" in ref else ("", "")
    enriched = {**row, "connection_ref": ref, "account": {"site": site, "email": email}}
    if row.get("state") == "owner_action_required":
        enriched["recovery"] = {"command": f"acli {product} auth login --site {site} --email {email} --token",
                                "hint": "Authenticate with your Atlassian API token"}
    else:
        enriched.setdefault("recovery", None)
    return enriched


def _removed(provider: str) -> Any:
    def call(service: Any, principal: Any, args: dict[str, Any]) -> Any:
        from holdspeak.services.errors import NotFound

        (ref,) = _required(args, "connection_ref")
        if not service.remove_connection(principal, ref):
            raise NotFound("account", ref)
        return {"removed": True, "provider": provider, "connection_ref": ref}

    return call


_DISCOVER_PAGE = {
    "query": {"type": "string", "description": "Filter text (a substring of the key or name)."},
    "cursor": {"type": "integer", "minimum": 0, "description": "The offset of the page."},
    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "The page size (default 30)."},
}
_ADD = {"site": {"type": "string", "minLength": 1, "description": "The Atlassian site (mysite or mysite.atlassian.net)."},
        "email": {"type": "string", "minLength": 1, "description": "The account's email address."}}
_P = "/api/providers"

PROVIDER_OPERATIONS: tuple[OperationDescriptor, ...] = (
    # ── every provider ───────────────────────────────────────────────
    _row("provider.list", "provider_service", "providers", lambda s, p, a: {"providers": s.providers(p)},
         "List the providers (native, GitHub, Jira, Confluence) with their capabilities. It asks no provider.",
         result="{providers: [{provider_id, capabilities, ...}]}", http=("GET", _P), handler="list_providers",
         blocking_io=False),
    # ── GitHub ───────────────────────────────────────────────────────
    _row("provider.github_connection", "provider_service", "github.connection_status",
         lambda s, p, a: s.connection_status(p, hostname=a.get("hostname"), _owner_check=True), "Check the GitHub sign-in now (gh auth status) and store the answer.",
         result="{state, account, error_code, ...}", write=True, egress=True,
         properties={"hostname": {"type": "string", "description": "The GitHub host. Default: github.com."}}),
    _row("provider.github_discover", "provider_service", "github.discover",
         lambda s, p, a: s.discover(p, query=a.get("query"), cursor=a.get("cursor"), limit=a.get("limit") or 30),
         "List the GitHub repositories his sign-in reaches, one bounded page at a time (gh repo list).",
         result="{items: [{id, name, owner, visibility}], next_cursor, ...}", http=("GET", f"{_P}/github/discover"),
         handler="github_discover", properties=_DISCOVER_PAGE, egress=True),
    _row("provider.github_validate_repo", "provider_service", "github.validate_repo",
         lambda s, p, a: s.validate_repo(p, *_required(a, "owner_repo")),
         "Check that one GitHub repository exists and his sign-in reaches it (one bounded gh read).",
         result="{valid, error_code, error_detail}", egress=True,
         properties={"owner_repo": {"type": "string", "description": "owner/name, e.g. octocat/Hello-World."}},
         required=("owner_repo",)),
    _row("provider.github_pr_get", "provider_service", "github.pr_get",
         lambda s, p, a: s.pr_get(p, owner_repo=str(a.get("owner_repo") or ""), number=a.get("number"),
                                  url=str(a.get("url") or "")),
         "Read one GitHub pull request: its title, body, changed files with their line counts, and the reviews "
         "it asks for. Name it by its URL, or by owner_repo and number. Read only. An agent reads only the "
         "repository delegated to its launch, a bounded number of times.",
         result="{title, body, files: [{path, additions, deletions}], reviews, ...}",
         refusals=("repository_not_delegated", "read_budget_spent"),
         properties={"url": {"type": "string", "description": "The pull request's URL."},
                     "owner_repo": {"type": "string", "description": "owner/name."},
                     "number": {"type": "integer", "minimum": 1, "description": "The pull request's number."}}),
    OperationDescriptor(
        name="provider.github_remove", version=1,
        description="Remove the saved GitHub sign-in. Keep Projects and their sources. Owner HTTP press only.",
        args_schema=_schema({"connection_ref": {"type": "string", "minLength": 1},
                             "expected_checked_at": {"type": "string", "minLength": 1},
                             "command_id": {"type": "string", "minLength": 1}},
                            ("connection_ref", "expected_checked_at", "command_id")),
        principal=_OWNER, effect="write", result="{removed, provider, connection_ref}",
        refusals=_CONTRACT_REFUSALS + ("owner_required", "github_connection_changed", "github_credential_remove_failed"),
        completion="synchronous; the credential is removed and linked sources require sign-in",
        exposure=("http:DELETE /api/providers/github/connection",),
        http=("DELETE", "/api/providers/github/connection"), handler="github_remove_connection",
        http_only_reason="Owner credential custody: no agent tool may remove the owner's sign-in.",
        service="provider_service", method="github.remove_connection",
        call=_on_adapter("github", lambda s, p, a: s.remove_connection(p, a["connection_ref"], a["expected_checked_at"])),
        owner_only=True, owner_press=True, blocking_io=True, authority="config",
        admission=Admission("admitted", "Removes owner credential custody through its credential service."),
    ),
    # ── Jira ─────────────────────────────────────────────────────────
    _row("provider.jira_connections", "provider_service", "jira.list_connections",
         lambda s, p, a: {"connections": [_account_row(r, "jira") for r in s.list_connections(p)],
                          "known_accounts": s.known_accounts(p)},
         "List the Jira connections (site and email) as last checked, and the acli accounts on this Mac.",
         result="{connections: [{connection_ref, state, account, recovery}], known_accounts}",
         http=("GET", f"{_P}/jira/connections"), handler="jira_connections"),
    _row("provider.jira_add_connection", "provider_service", "jira.add_connection",
         lambda s, p, a: s.add_connection(p, *_required(a, "site", "email")),
         "Add a Jira connection by site and email. No credential is stored: acli keeps its own sign-in.",
         result="the connection row (state disconnected until checked)", http=("POST", f"{_P}/jira/connections"),
         handler="jira_add_connection", properties=_ADD, required=("site", "email"), write=True, config=True),
    _row("provider.jira_remove_connection", "provider_service", "jira.remove_connection", _removed("jira"),
         "Remove one Jira connection row. The acli sign-in stays.",
         result="{removed, provider, connection_ref}", http=("DELETE", f"{_P}/jira/connections/{{connection_ref}}"),
         handler="jira_remove_connection", properties={"connection_ref": _REF}, required=("connection_ref",),
         write=True, config=True, refusals=("not_found",)),
    _row("provider.jira_connection", "provider_service", "jira.connection_status",
         lambda s, p, a: s.connection_status(p, *_required(a, "connection_ref")),
         "Check one Jira connection now (acli auth switch, then auth status) and store the answer.",
         result="{state, account, error_code, ...}", write=True, egress=True,
         http=("POST", f"{_P}/jira/connections/{{connection_ref}}/recheck"), handler="jira_connection_recheck",
         properties={"connection_ref": _REF}, required=("connection_ref",)),
    _row("provider.jira_discover", "provider_service", "jira.discover",
         lambda s, p, a: s.discover(p, *_required(a, "connection_ref"), kind=a.get("kind") or "projects",
                                    query=a.get("query") or "", project_key=a.get("project_key") or "",
                                    cursor=a.get("cursor"), limit=a.get("limit") or 30),
         "List Jira projects, issue types or statuses for one connection, one bounded page at a time.",
         result="{items, next_cursor, ...}", http=("GET", f"{_P}/jira/discover"), handler="jira_discover",
         properties={"connection_ref": _REF, "kind": {"enum": ["projects", "issue_types", "statuses"]},
                     "project_key": {"type": "string", "description": "For issue_types and statuses."},
                     **_DISCOVER_PAGE},
         required=("connection_ref",), egress=True),
    _row("provider.jira_search", "provider_service", "jira.search",
         lambda s, p, a: s.search(p, *_required(a, "connection_ref"), jql=_required(a, "jql")[0],
                                  limit=a.get("limit") or 50, enrich=bool(a.get("enrich", False))),
         "Search Jira issues by JQL. Owner only: it runs acli under his sign-in and switches its account; "
         "no agent reads Jira until a read scoped to a delegated project exists.",
         result="{items, total, ...}", egress=True,
         properties={"connection_ref": _REF, "jql": {"type": "string", "description": "The JQL, verbatim."},
                     "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                     "enrich": {"type": "boolean", "description": "Add due date, resolution and more per item."}},
         required=("connection_ref", "jql")),
    _row("provider.jira_validate_scope", "provider_service", "jira.validate_scope",
         lambda s, p, a: s.validate_scope(p, *_required(a, "connection_ref", "project_key")),
         "Check that one Jira project key exists and the connection reaches it.",
         result="{valid, error_code, error_detail}", egress=True,
         properties={"connection_ref": _REF, "project_key": {"type": "string", "description": "e.g. KAN."}},
         required=("connection_ref", "project_key")),
    # ── Confluence ───────────────────────────────────────────────────
    _row("provider.confluence_connections", "provider_service", "confluence.list_connections",
         lambda s, p, a: {"connections": [_account_row(r, "confluence") for r in s.list_connections(p)]},
         "List the Confluence connections (site and email) as last checked.",
         result="{connections: [{connection_ref, state, account, recovery}]}",
         http=("GET", f"{_P}/confluence/connections"), handler="confluence_connections"),
    _row("provider.confluence_add_connection", "provider_service", "confluence.add_connection",
         lambda s, p, a: s.add_connection(p, *_required(a, "site", "email")),
         "Add a Confluence connection by site and email. No credential is stored: acli keeps its own sign-in.",
         result="the connection row (state disconnected until checked)",
         http=("POST", f"{_P}/confluence/connections"), handler="confluence_add_connection", properties=_ADD,
         required=("site", "email"), write=True, config=True),
    _row("provider.confluence_remove_connection", "provider_service", "confluence.remove_connection", _removed("confluence"),
         "Remove one Confluence connection row. The acli sign-in stays.",
         result="{removed, provider, connection_ref}",
         http=("DELETE", f"{_P}/confluence/connections/{{connection_ref}}"), handler="confluence_remove_connection",
         properties={"connection_ref": _REF}, required=("connection_ref",), write=True, config=True,
         refusals=("not_found",)),
    _row("provider.confluence_discover", "provider_service", "confluence.discover",
         lambda s, p, a: s.discover(p, *_required(a, "connection_ref"), kind=a.get("kind") or "spaces",
                                    query=a.get("query") or "", cursor=a.get("cursor"), limit=a.get("limit") or 30),
         "List the Confluence spaces one connection reaches, one bounded page at a time.",
         result="{items, next_cursor, ...}", http=("GET", f"{_P}/confluence/discover"), handler="confluence_discover",
         properties={"connection_ref": _REF, "kind": {"enum": ["spaces"]}, **_DISCOVER_PAGE},
         required=("connection_ref",), egress=True),
    _row("provider.confluence_validate_space", "provider_service", "confluence.validate_scope",
         lambda s, p, a: s.validate_scope(p, *_required(a, "connection_ref", "space_key")),
         "Check that one Confluence space key exists and the connection reaches it.",
         result="{valid, error_code, error_detail}", egress=True,
         properties={"connection_ref": _REF, "space_key": {"type": "string", "description": "e.g. GOV."}},
         required=("connection_ref", "space_key")),
)

def bare_provider_service() -> Any:
    """The off-hub (bare MCP) provider service: the project family's adapters, read at each call."""
    from holdspeak.mcp.families import project as family
    from holdspeak.services.provider_service import ProviderService

    adapters = {"github": family._github_adapter, "jira": family._jira_adapter, "confluence": family._confluence_adapter}
    return ProviderService(lambda name: adapters[name]())


__all__ = ["PROVIDER_OPERATIONS", "bare_provider_service"]
