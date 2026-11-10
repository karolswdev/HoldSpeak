# PARKED 20261109 (ops/connections): the hand-written ``provider.*`` MCP twins from
# ``mcp/families/project.py`` (their schemas, then their dispatch branches) and ``connection.list``'s row.
# The tools are produced from ``holdspeak/provider_operations.py`` (``mcp/families/declared.py``).
# Not imported; this text is not valid Python on its own. Restore with ``git revert``.
"""
    # ── provider driver tools (HS-165-03) ───────────────────────────
    {
        "name": "provider.list",
        "description": "List configured providers (native + GitHub) with their capabilities.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.list@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.github_connection",
        "description": "Get the GitHub provider connection status.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.github_connection@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.github_discover",
        "description": "Bounded discovery of GitHub repositories through the configured adapter.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.github_discover@1",
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional search query."},
                "cursor": {"type": "integer", "description": "Pagination cursor."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "description": "Page size (default 30)."},
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.github_validate_repo",
        "description": "Validate a GitHub repository by owner/repo string.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.github_validate_repo@1",
            "type": "object",
            "properties": {
                "owner_repo": {"type": "string", "description": "GitHub owner/repo (e.g. 'octocat/Hello-World')."},
            },
            "required": ["owner_repo"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.github_pr_get",
        "description": (
            "Read one GitHub pull request: its title, body, changed files with their line counts, "
            "and the reviews it asks for. Name it by its URL, or by owner_repo and number. Read only."
        ),
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.github_pr_get@1",
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The pull request's URL (https://github.com/owner/name/pull/123)."},
                "owner_repo": {"type": "string", "description": "GitHub owner/repo (e.g. 'octocat/Hello-World')."},
                "number": {"type": "integer", "minimum": 1, "description": "The pull request's number."},
            },
            "required": [],
            "additionalProperties": False,
        },
    },
    # ── Jira provider driver tools (HS-166-01) ─────────────────────
    {
        "name": "provider.jira_connections",
        "description": "List all Jira connections (site+email pairs) and their status.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_connections@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_add_connection",
        "description": "Add a Jira connection by site and email (no credentials stored).",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_add_connection@1",
            "type": "object",
            "properties": {
                "site": {"type": "string", "description": "Atlassian site (e.g. 'mysite' or 'mysite.atlassian.net')."},
                "email": {"type": "string", "description": "Account email address."},
            },
            "required": ["site", "email"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_connection",
        "description": "Recheck one Jira connection status (switch + auth status probe).",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_connection@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
            },
            "required": ["connection_ref"],
            "additionalProperties": False,
        },
    },
    # ── Jira discovery + search tools (HS-166-02) ─────────────────
    {
        "name": "provider.jira_discover",
        "description": "Discover Jira resources (projects, issue types, statuses) for a connection.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_discover@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "kind": {"type": "string", "description": "Resource kind: projects, issue_types, statuses.", "default": "projects"},
                "query": {"type": "string", "description": "Filter text (substring match on key/name for projects).", "default": ""},
                "project_key": {"type": "string", "description": "Project key (required for issue_types and statuses).", "default": ""},
                "cursor": {"type": "integer", "description": "Offset cursor for pagination."},
                "limit": {"type": "integer", "description": "Max items to return (capped at 100).", "default": 30},
            },
            "required": ["connection_ref"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_search",
        "description": "Search Jira issues by JQL query.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_search@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "jql": {"type": "string", "description": "JQL query (passed through verbatim)."},
                "limit": {"type": "integer", "description": "Max items to return (capped at 200).", "default": 50},
                "enrich": {"type": "boolean", "description": "Enrich each item with duedate, resolution, etc. via workitem view.", "default": False},
            },
            "required": ["connection_ref", "jql"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.jira_validate_scope",
        "description": "Validate a Jira project key (the validate_repo twin).",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.jira_validate_scope@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "project_key": {"type": "string", "description": "Jira project key (e.g. 'KAN')."},
            },
            "required": ["connection_ref", "project_key"],
            "additionalProperties": False,
        },
    },
    # ── Confluence provider driver tools (HS-174-07) ─────────────────
    {
        "name": "provider.confluence_connections",
        "description": "List all Confluence connections (site+email pairs) and their status.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.confluence_connections@1",
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.confluence_discover",
        "description": "Discover Confluence spaces for a connection.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.confluence_discover@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "kind": {"type": "string", "description": "Resource kind: spaces.", "default": "spaces"},
                "query": {"type": "string", "description": "Filter text (substring match on key/name).", "default": ""},
                "cursor": {"type": "integer", "description": "Offset cursor for pagination."},
                "limit": {"type": "integer", "description": "Max items to return (capped at 100).", "default": 30},
            },
            "required": ["connection_ref"],
            "additionalProperties": False,
        },
    },
    {
        "name": "provider.confluence_validate_space",
        "description": "Validate a Confluence space key.",
        "inputSchema": {
            "$id": "holdspeak://mcp/provider.confluence_validate_space@1",
            "type": "object",
            "properties": {
                "connection_ref": {"type": "string", "description": "Connection ref (site|email)."},
                "space_key": {"type": "string", "description": "Confluence space key (e.g. 'GOV')."},
            },
            "required": ["connection_ref", "space_key"],
            "additionalProperties": False,
        },
    },
    # ── provider driver tools (HS-165-03) ───────────────────────────
    # Mirrors: holdspeak/web/routes/providers.py

    if name == "provider.list":
        # Web parity: providers.py list_providers
        # HS-166-01: ONE shared helper, never duplicate the enumeration.
        return {"providers": collect_provider_manifests(
            github_adapter=_github_adapter(),
            jira_adapter=_jira_adapter(),
            confluence_adapter=_confluence_adapter(),
            principal=principal,
        )}

    if name == "provider.github_connection":
        # Web parity: providers.py:68 github_connection
        # Service seam: GitHubProviderAdapter.connection_status
        adapter = _github_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "GitHub provider is not configured",
                context={"status": 404},
            )
        return adapter.connection_status(principal)

    if name == "provider.github_discover":
        # Web parity: providers.py:104 github_discover
        # Service seam: GitHubProviderAdapter.discover
        adapter = _github_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "GitHub provider is not configured",
                context={"status": 404},
            )
        return adapter.discover(
            principal,
            query=arguments.get("query"),
            cursor=arguments.get("cursor"),
            limit=arguments.get("limit", 30),
        )

    if name == "provider.github_validate_repo":
        # Web parity: providers.py:132 github_validate_repo
        # Service seam: GitHubProviderAdapter.validate_repo
        adapter = _github_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "GitHub provider is not configured",
                context={"status": 404},
            )
        owner_repo = str(arguments.get("owner_repo", "")).strip()
        if not owner_repo:
            raise ValidationError("owner_repo is required")
        return adapter.validate_repo(principal, owner_repo)

    if name == "provider.github_pr_get":
        # Betterment MCP M6: MCP only (the review starter's agent reads the
        # PR it is about). Service seam: GitHubProviderAdapter.pr_get
        adapter = _github_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "GitHub provider is not configured",
                context={"status": 404},
            )
        return adapter.pr_get(
            principal,
            owner_repo=str(arguments.get("owner_repo") or ""),
            number=arguments.get("number"),
            url=str(arguments.get("url") or ""),
        )

    # ── Jira provider driver tools (HS-166-01) ──────────────────────
    # Mirrors: holdspeak/web/routes/providers.py Jira routes.
    # Serializers DELEGATE to the adapter (the 165 law: copies drift).

    if name == "provider.jira_connections":
        # Web parity: providers.py jira_connections
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        return {
            "connections": adapter.list_connections(principal),
            "known_accounts": adapter.known_accounts(principal),
        }

    if name == "provider.jira_add_connection":
        # Web parity: providers.py jira_add_connection
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        site = str(arguments.get("site", "")).strip()
        email = str(arguments.get("email", "")).strip()
        if not site or not email:
            raise ValidationError("site and email are required")
        return adapter.add_connection(principal, site, email)

    if name == "provider.jira_connection":
        # Web parity: providers.py jira_connection_recheck
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        if not ref:
            raise ValidationError("connection_ref is required")
        return adapter.connection_status(principal, ref)

    # ── Jira discovery + search tools (HS-166-02) ──────────────────
    # Mirrors: holdspeak/web/routes/providers.py Jira discover/search/validate routes.

    if name == "provider.jira_discover":
        # Web parity: providers.py jira_discover
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        if not ref:
            raise ValidationError("connection_ref is required")
        return adapter.discover(
            principal,
            ref,
            kind=arguments.get("kind", "projects"),
            query=arguments.get("query", ""),
            project_key=arguments.get("project_key", ""),
            cursor=arguments.get("cursor"),
            limit=arguments.get("limit", 30),
        )

    if name == "provider.jira_search":
        # Web parity: providers.py jira_search
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        jql = str(arguments.get("jql", "")).strip()
        if not ref or not jql:
            raise ValidationError("connection_ref and jql are required")
        return adapter.search(
            principal,
            ref,
            jql=jql,
            limit=arguments.get("limit", 50),
            enrich=bool(arguments.get("enrich", False)),
        )

    if name == "provider.jira_validate_scope":
        # Web parity: providers.py jira_validate_scope
        adapter = _jira_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Jira provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        project_key = str(arguments.get("project_key", "")).strip()
        if not ref or not project_key:
            raise ValidationError("connection_ref and project_key are required")
        return adapter.validate_scope(principal, ref, project_key)

    # ── Confluence provider driver tools (HS-174-07) ──────────────────
    # Mirrors: holdspeak/web/routes/providers.py Confluence routes.

    if name == "provider.confluence_connections":
        # Web parity: providers.py confluence_connections
        adapter = _confluence_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Confluence provider is not configured",
                context={"status": 404},
            )
        return {
            "connections": adapter.list_connections(principal),
        }

    if name == "provider.confluence_discover":
        # Web parity: providers.py confluence_discover
        adapter = _confluence_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Confluence provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        if not ref:
            raise ValidationError("connection_ref is required")
        return adapter.discover(
            principal,
            ref,
            kind=arguments.get("kind", "spaces"),
            query=arguments.get("query", ""),
            cursor=arguments.get("cursor"),
            limit=arguments.get("limit", 30),
        )

    if name == "provider.confluence_validate_space":
        # Web parity: providers.py confluence_validate_scope
        adapter = _confluence_adapter()
        if adapter is None:
            raise ServiceError(
                "provider_not_configured",
                "Confluence provider is not configured",
                context={"status": 404},
            )
        ref = str(arguments.get("connection_ref", "")).strip()
        space_key = str(arguments.get("space_key", "")).strip()
        if not ref or not space_key:
            raise ValidationError("connection_ref and space_key are required")
        return adapter.validate_scope(principal, ref, space_key)

"""
