"""Conductor K6: what an agent HoldSpeak launched may do, for the life of its launch.

The orchestrator's rulings on PR #903 (the owner wants the agent to do
meaningful work; egress, authority and config stay at his press):

1. **Memory recall.** A launch-bound credential reads ``memory.*`` while it
   is live (``principals.launch_reader``). What it reads passes the brief's
   People cut (``agent_brief._PeopleClassifier``): a hit, observation or page
   sentence whose source carries People content is left out.
2. **Decision proposals.** At launch the owner's press on Hand to agent
   grants the launch identity a desk delegation for ``decision.create`` only.
   The CONDUCTOR call gate admits only a ``proposed`` decision
   (``mcp/palettes.py``), so the decision waits for the owner. Every other
   desk write stays ``desk_delegation_required``; the tools that confirm on
   the owner's behalf are not in the palette. The grant is revoked when the
   credential goes.
3. **Item scope.** An item-state tool acts only on the launch's origin item
   and the items the agent created during the launch; any other id is
   refused ``not_this_launch``.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional

from ..logging_config import get_logger

log = get_logger("services.conductor_launch")

#: The one desk write a launch may make: a decision, always ``proposed``.
PROPOSAL_OPERATIONS: tuple[str, ...] = ("decision.create",)

#: Item-state tools and the argument that names the item.
SCOPED_ITEM_TOOLS: dict[str, str] = {
    "follow_through.complete": "card_id",
    "project.item.transition": "item_id",
    "project.item.update": "item_id",
}

NOT_THIS_LAUNCH = "not_this_launch"

_HOOK_INSTALLED = False


# ── the hub database (never a default database outside a hub) ──────────


def _hub_database() -> Any:
    from ..runtime import composition

    root = composition.installed()
    if root is None or getattr(root, "bare_root", True) or getattr(root, "db", None) is None:
        return None
    return root.db


# ── 2. the launch's decision-proposal grant ──────────────────────────────


def grant_decision_proposals(
    principal: Any, identity: str, *, ttl_seconds: float, database: Any = None,
) -> Optional[dict[str, Any]]:
    """Grant *identity* ``decision.create`` for the life of the launch.

    The owner's press on Hand to agent is the gesture: *principal* must be
    the OWNER. Returns the grant's kernel answer, or None when there is no
    hub database or no owner press (the launch runs; the agent's decision
    proposals are then refused ``desk_delegation_required``)."""
    from ..principals import PrincipalKind
    from . import desk_delegation

    if getattr(principal, "kind", None) is not PrincipalKind.OWNER:
        return None
    database = database or _hub_database()
    if database is None:
        return None
    install_revoke_hook()
    expires_at = desk_delegation._now(database) + float(ttl_seconds)
    return desk_delegation.grant(
        principal, identity, {"expires_at": expires_at},
        database=database, operations=PROPOSAL_OPERATIONS,
    )


def revoke_decision_grant(launch_id: str, identity: str, *, database: Any = None) -> bool:
    """End the launch's grant, if one is LIVE (a hook on the credential's revoke)."""
    from ..principals import Principal, PrincipalKind
    from . import desk_delegation

    database = database or _hub_database()
    if database is None or not desk_delegation.live_grant(identity, database=database):
        return False
    owner = Principal(PrincipalKind.OWNER, "conductor-launch")
    desk_delegation.revoke(owner, identity, "credential_revoked", database=database)
    return True


def install_revoke_hook() -> None:
    """Every revoke of a launch-bound credential also ends its grant."""
    global _HOOK_INSTALLED
    from ..principals import agent_credentials

    if _HOOK_INSTALLED:
        return
    agent_credentials.launch_revoked_hooks.append(
        lambda launch_id, identity: revoke_decision_grant(launch_id, identity)
    )
    _HOOK_INSTALLED = True


# ── 1. the People cut on memory reads ────────────────────────────────────


def _classifier(db: Any) -> Any:
    from .agent_brief import _PeopleClassifier

    return _PeopleClassifier(db)


def _people_kind(kind: Any) -> bool:
    from .agent_brief import PEOPLE_KINDS

    return str(kind or "") in PEOPLE_KINDS


def cut_memory(db: Any, method: str, result: Any) -> Any:
    """The People cut over one memory read's result (a launch reader's)."""
    if not isinstance(result, Mapping):
        return result
    people = _classifier(db)
    out = dict(result)
    if method == "search":
        kept = []
        for hit in result.get("hits") or []:
            refs = [str(hit.get("source_ref") or "")] + [str(r) for r in hit.get("evidence") or []]
            if _people_kind(hit.get("kind")) or any(people.carries_people(ref) for ref in refs if ref):
                continue
            kept.append(hit)
        cut = len(result.get("hits") or []) - len(kept)
        out["hits"] = kept
        page = dict(out.get("page") or {})
        if page:
            page["count"] = len(kept)
            page["total"] = max(0, int(page.get("total") or 0) - cut)
            out["page"] = page
        out["people_cut"] = cut
        return out
    if method == "observations":
        kept = [
            row for row in result.get("observations") or []
            if not any(
                people.carries_people(str((ev or {}).get("ref") or ""))
                for ev in row.get("evidence") or [] if (ev or {}).get("ref")
            )
        ]
        out["observations"] = kept
        out["count"] = len(kept)
        return out
    if method == "page":
        out["page"] = _cut_page(people, result.get("page"))
        return out
    if method == "standing_pages":
        pages = [_cut_page(people, page) for page in result.get("pages") or []]
        out["pages"] = [page for page in pages if page]
        return out
    return out


def _cut_page(people: Any, page: Any) -> Any:
    if not isinstance(page, Mapping):
        return page
    sentences = [s for s in page.get("sentences") or [] if people.sentence(s)]
    if not sentences:
        return None
    cut = dict(page)
    cut["sentences"] = sentences
    if "answer" in cut:
        cut["answer"] = "\n".join(f"- {s.get('text')}" for s in sentences)
    if "sources" in cut:
        refs = list(dict.fromkeys(r.get("ref") for s in sentences for r in s.get("refs") or []))
        cut["sources"] = [src for src in cut.get("sources") or [] if src.get("ref") in refs]
    return cut


# ── 3. item scope ────────────────────────────────────────────────────────


def item_refused(launch_id: str, name: str, arguments: Any) -> Optional[str]:
    """The item id a scoped tool names, when it is not this launch's."""
    key = SCOPED_ITEM_TOOLS.get(name)
    if key is None:
        return None
    from ..principals import agent_credentials

    item_id = str((arguments or {}).get(key) or "").strip() if isinstance(arguments, Mapping) else ""
    if agent_credentials.in_scope(launch_id, item_id):
        return None
    return item_id or "(none)"


def record_created(launch_id: str, name: str, result: Any) -> None:
    """An item the agent created joins the launch's scope."""
    from ..principals import agent_credentials

    if not isinstance(result, Mapping):
        return
    if name == "door.add_item":
        agent_credentials.scope_add(launch_id, str(result.get("id") or ""))
    elif name == "project.item.create":
        item = result.get("item") if isinstance(result.get("item"), Mapping) else result
        agent_credentials.scope_add(launch_id, str(item.get("id") or ""))


__all__ = [
    "NOT_THIS_LAUNCH",
    "PROPOSAL_OPERATIONS",
    "SCOPED_ITEM_TOOLS",
    "cut_memory",
    "grant_decision_proposals",
    "install_revoke_hook",
    "item_refused",
    "record_created",
    "revoke_decision_grant",
]
