"""The repository drawer's and the roadmaps' verbs on the one declared contract (2026-11-09).

Carved beside ``holdspeak/operations.py`` (which imports it into
``DESCRIPTORS``), as ``meeting_operations.py`` is. Each row states one verb of
``RepositoryDrawerService`` or ``RoadmapService`` once: its call, its HTTP
method and path, and its MCP tool schema. ``web/routes/repositories.py`` and
``web/routes/roadmaps.py`` produce the routes, ``mcp/families/declared.py``
the tools, both through ``OperationRegistry.invoke``.

The writes (register, write a file, stage, commit, check out) change the
owner's own checkouts: they are owner-only. The reads are evidence.
Imported only through ``holdspeak.operations`` (it imports this module).
"""
from __future__ import annotations

from holdspeak.held_arguments import held_arguments, text, hidden, named, constant, normalizer, target

from typing import Any, Callable, Mapping, Optional

from holdspeak.operations import _CONTRACT_REFUSALS, OperationDescriptor

Call = Callable[[Any, Any, dict[str, Any]], Any]

_PRINCIPAL = "derived by the transport (HTTP auth middleware; MCP auth resolver) and passed to the service unchanged"
_ID = {"type": "string", "minLength": 1}
_REPO_REFUSALS = _CONTRACT_REFUSALS + (
    "RepositoryRefused: repository, worktree or file not found (404); path traversal refused (400); "
    "file changed before write (409); a git refusal in words",
    "owner_required: a write, from any principal but the owner",
)
_ROADMAP_REFUSALS = _CONTRACT_REFUSALS + ("NotFound: Roadmap not found",)
_WORKTREE = {"worktree_id": {"type": "string", "description": "Optional. A registered worktree of the repository; "
                                                               "default: its primary checkout."}}


def _op(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str, *,
        service: str, write: bool = False, properties: Optional[Mapping[str, Any]] = None,
        required: tuple[str, ...] = (), refusals: tuple[str, ...], result: str, facts: dict[str, Any] | None = None) -> OperationDescriptor:
    """One verb; its tool requires the path's ids (``{path:path}`` is ``path``) and ``required``."""
    ids = [part[1:-1].split(":", 1)[0] for part in http[1].split("/") if part.startswith("{")]
    tool = {**dict(facts or {}), "type": "object", "properties": {**{key: _ID for key in ids}, **dict(properties or {})},
            "required": ids + list(required), "additionalProperties": False}
    return OperationDescriptor(
        name=name, version=1, description=description, args_schema={"type": "object"}, principal=_PRINCIPAL,
        effect="write" if write else "read", result=result, refusals=refusals,
        completion="synchronous; a write is one desk_changed frame on the hub bus" if write else "synchronous",
        exposure=(f"http:{http[0]} {http[1]}", f"mcp:{name}"), service=service, method=method,
        call=call, http=http, handler=handler, tool_schema=tool,
        owner_only=write, blocking_io=service == "repository_drawer_service",
        # A read is evidence; the "repository." and "roadmap." families are MCP
        # and HTTP only (thread_modes._thread_side), so no palette grows.
        thread="effect_proposal" if write else "evidence_read",
    )


def _repo(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str,
          result: str, **kwargs: Any) -> OperationDescriptor:
    return _op(name, method, http, handler, call, description, service="repository_drawer_service",
               refusals=_REPO_REFUSALS, result=result, **kwargs)


def _road(name: str, method: str, http: tuple[str, str], handler: str, call: Call, description: str,
          result: str, **kwargs: Any) -> OperationDescriptor:
    return _op(name, method, http, handler, call, description, service="roadmap_service",
               refusals=_ROADMAP_REFUSALS, result=result, **kwargs)


def _scoped(args: dict[str, Any]) -> dict[str, Any]:
    """The write's worktree: the body's, and the query's (the route passes it as ``query_worktree_id``)."""
    return {"worktree_id": args.get("worktree_id"), "query_worktree_id": args.get("query_worktree_id")}


_R = "/api/repositories/{repository_id}"
REPOSITORY_DRAWER_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _repo("repository.list", "list_repositories", ("GET", "/api/repositories"), "api_repositories",
          lambda s, p, a: s.list_repositories(p), "List the local git repositories the hub knows, with their branch.",
          "{repositories: [{kind, id, name, source_id, branch, created_at}]}"),
    _repo("repository.register", "register", ("POST", "/api/repositories"), "api_register_repository",
          lambda s, p, a: s.register(p, source_id=a.get("source_id"), path=a.get("path"), label=a.get("label")),
          "Add a local git checkout to the repository drawer (a path), or confirm a known one (source_id).",
          "{repository: {kind, id, name, source_id, branch, created_at}}", write=True,
          properties={"source_id": {"type": "string"}, "path": {"type": "string", "description": "The absolute "
                                                                                                "path of a git worktree root."},
                      "label": {"type": "string"}}, facts={**normalizer("holdspeak.services.repository_drawer_service:RepositoryDrawerService.registration_arguments"), **held_arguments('Register a repository',
                named('source_id', 'Repository', 'repository.list', {}, 'name', rows='repositories', match={'id': 'source_id'}),
                hidden('path', 'Checkout path', 'secret'),
                hidden('label', 'Requested name'))}),
    _repo("repository.tree", "tree", ("GET", _R + "/tree"), "api_repository_tree",
          lambda s, p, a: s.tree(p, a.get("repository_id"), a.get("path") or "", a.get("worktree_id")),
          "List the files of one directory of a repository (the root by default).", "{files: [{name, path, ...}]}",
          properties={"path": {"type": "string", "description": "A directory inside the repository."}, **_WORKTREE}),
    _repo("repository.read_file", "read_file", ("GET", _R + "/file/{path:path}"), "api_repository_file",
          lambda s, p, a: s.read_file(p, a.get("repository_id"), a.get("path"), a.get("worktree_id")),
          "Read one text file of a repository, with its sha256.", "{path, content, sha256}", properties=_WORKTREE),
    _repo("repository.write_file", "write_file", ("PUT", _R + "/file/{path:path}"), "api_repository_write_file",
          lambda s, p, a: s.write_file(p, a.get("repository_id"), a.get("path"), a.get("content"),
                                       a.get("expected_sha256"), **_scoped(a)),
          "Write one text file of a repository. With expected_sha256, refuse if the file changed since it was read.",
          "{path, written: true, sha256}", write=True, required=("content",),
          properties={"content": {"type": "string"}, "expected_sha256": {"type": "string"}, **_WORKTREE}, facts={**target('repository.write_file', "resolve_workspace_arguments"), **held_arguments('Write a repository file',
                named('repository_id', 'Repository', 'repository.list', {}, 'name', rows='repositories', match={'id': 'repository_id'}),
                text('path', 'Path'),
                constant('Kind', 'Text file'),
                hidden('content', 'Content', 'file bytes'),
                {**text('content', 'Size'), 'format': 'utf8_bytes'},
                hidden('expected_sha256', 'Saved file', 'token'),
                hidden('worktree_id', 'Worktree', 'secret'))}),
    _repo("repository.diff", "diff", ("GET", _R + "/diff"), "api_repository_diff",
          lambda s, p, a: s.diff(p, a.get("repository_id"), a.get("worktree_id"), a.get("path"), a.get("staged")),
          "Read the diff of a repository (one file with path; the staged changes with staged).",
          "{diff, truncated}",
          properties={"path": {"type": "string"}, "staged": {"type": "boolean"}, **_WORKTREE}),
    _repo("repository.stage", "stage", ("POST", _R + "/stage"), "api_repository_stage",
          lambda s, p, a: s.stage(p, a.get("repository_id"), a.get("paths"), **_scoped(a)),
          "Stage files of a repository for the next commit.", "{staged: [...]}", write=True, required=("paths",),
          properties={"paths": {"type": "array", "items": {"type": "string"}}, **_WORKTREE}, facts={**target('repository.stage', "resolve_workspace_arguments"), **held_arguments('Stage repository files',
                named('repository_id', 'Repository', 'repository.list', {}, 'name', rows='repositories', match={'id': 'repository_id'}),
                hidden('paths', 'Paths', 'secret'),
                {**text('paths', 'Files'), 'format': 'item_count'},
                hidden('worktree_id', 'Worktree', 'secret'))}),
    _repo("repository.commit", "commit", ("POST", _R + "/commit"), "api_repository_commit",
          lambda s, p, a: s.commit(p, a.get("repository_id"), a.get("message"), **_scoped(a),
              **({"expected_index": a["expected_index"]} if a.get("expected_index") is not None else {})),
          "Commit the staged changes of a repository with a message.", "the commit {sha, ...}", write=True,
          required=("message",), properties={"file_count": {"type": "integer"}, "expected_index": {"type": "string"}, "message": {"type": "string"}, **_WORKTREE}, facts={**target('repository.commit', 'resolve_commit_arguments'), **held_arguments('Commit repository files',
                named('repository_id', 'Repository', 'repository.list', {}, 'name', rows='repositories', match={'id': 'repository_id'}),
                text('message', 'Message'),
                hidden('worktree_id', 'Worktree', 'secret'),
                text('file_count', 'Files', owner_only=True),
                hidden('expected_index', 'Saved index', 'token'))}),
    _repo("repository.status", "status", ("GET", _R + "/status"), "api_repository_status",
          lambda s, p, a: s.status(p, a.get("repository_id"), a.get("worktree_id")),
          "Read the git status of a repository: its branch and its changed files.", "{branch, dirty, changes, ...}",
          properties=_WORKTREE),
    _repo("repository.branches", "branches", ("GET", _R + "/branches"), "api_repository_branches",
          lambda s, p, a: s.branches(p, a.get("repository_id"), a.get("worktree_id")),
          "List the local branches of a repository.", "{branches: [...]}", properties=_WORKTREE),
    _repo("repository.checkout", "checkout", ("POST", _R + "/checkout"), "api_repository_checkout",
          lambda s, p, a: s.checkout(p, a.get("repository_id"), a.get("branch"), **_scoped(a)),
          "Check out a branch of a repository.", "the new {branch, ...}", write=True, required=("branch",),
          properties={"branch": {"type": "string"}, **_WORKTREE}, facts={**target('repository.checkout', "resolve_workspace_arguments"), **{**normalizer('holdspeak.services.repository_drawer_service:RepositoryDrawerService.checkout_arguments'), **held_arguments('Change a repository branch',
                named('repository_id', 'Repository', 'repository.list', {}, 'name', rows='repositories', match={'id': 'repository_id'}),
                text('branch', 'Branch'),
                hidden('worktree_id', 'Worktree', 'secret'))}}),
)

ROADMAP_OPERATIONS: tuple[OperationDescriptor, ...] = (
    _road("roadmap.list", "list_roadmaps", ("GET", "/api/roadmaps"), "api_roadmaps",
          lambda s, p, a: s.list_roadmaps(p),
          "List the Delivery Workbench roadmaps of this checkout (pm/roadmap/), each with its health and current phase.",
          "{roadmaps: [{slug, name, phaseCount, currentPhase, health, issues, nextStoryId, ...}]}"),
    _road("roadmap.get", "get_roadmap", ("GET", "/api/roadmaps/{slug}"), "api_roadmap",
          lambda s, p, a: s.get_roadmap(p, a.get("slug")),
          "Read one roadmap with its phases and stories.", "{slug, name, phases, healthIssues, ...}"),
    _road("roadmap.health", "health", ("GET", "/api/roadmaps/{slug}/health"), "api_roadmap_health",
          lambda s, p, a: s.health(p, a.get("slug")),
          "Check one roadmap now (dw check): its health and its issues.", "{health, issues}"),
    _road("roadmap.next", "next_story", ("GET", "/api/roadmaps/{slug}/next"), "api_roadmap_next",
          lambda s, p, a: s.next_story(p, a.get("slug")),
          "Read the next story of one roadmap (dw next).", "{next: {...} | null}"),
)

REPOSITORY_OPERATIONS: tuple[OperationDescriptor, ...] = REPOSITORY_DRAWER_OPERATIONS + ROADMAP_OPERATIONS

__all__ = ["REPOSITORY_DRAWER_OPERATIONS", "REPOSITORY_OPERATIONS", "ROADMAP_OPERATIONS"]
