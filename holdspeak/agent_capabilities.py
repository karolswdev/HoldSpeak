"""The agent capability ledger (HS-104-01).

Before any gate holds a call or any card prints a number, the system
states — per agent adapter — whether each capability is
``authoritative``, ``inferred``, or ``unavailable`` (Article VI:
honest by construction). The ledger is DATA, hand-written and
reviewed in the same commit as the code that changes a standing;
nothing here is detected at runtime, because a computed table is
just another inference.

Three parts:

- ``LEDGER`` — the frozen declaration table, adapter → capability →
  standing, covering every adapter that exists today.
- ``require_capability(adapter, capability)`` — the one enforcement
  hook. Consumers that render or act on a capability MUST call it;
  it raises :class:`CapabilityUnavailableError` (typed, naming the
  adapter and the standing) when the ledger cannot vouch. The
  chokepoint census pins its call sites.
- ``LEDGER_CONSUMERS`` — the registered consumers list the doctor
  check walks: a consumer registered against an ``unavailable``
  capability turns the "Agent capabilities" doctor line red before
  the lying surface ever ships.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType


class Capability(str, Enum):
    """The fixed capability vocabulary. Extending it is a reviewed edit."""

    TOOL_HOOKS = "tool_hooks"
    SESSION_IDENTITY = "session_identity"
    USAGE_TOKENS = "usage_tokens"
    REPO_HEAD = "repo_head"
    BLOCKING = "blocking"  # can the adapter STOP a call, or only observe it


class Standing(str, Enum):
    AUTHORITATIVE = "authoritative"
    INFERRED = "inferred"
    UNAVAILABLE = "unavailable"


ADAPTERS = ("tmux-pane", "delivery-node", "mesh-node", "claude-code-hooks")

# The declaration table. Every cell is a reviewed claim:
#
# - tmux-pane (coder_steering.py): the pane content is what tmux
#   serves — but WHO runs inside is a guess from the pane title/cwd,
#   tokens never cross the wire, and a pane can be interrupted (C-c)
#   yet never intercepted, so blocking is unavailable, not inferred.
# - delivery-node (delivery/node_link.py): the node introduces itself
#   with an authenticated hello and every attempt rides the command
#   envelope, so identity and the assigned worktree head are the
#   hub's own records. It exposes no tool hooks and reports no usage.
# - mesh-node (intel/mesh_relay.py): a relayed inference endpoint.
#   The hub knows which node it addressed (its own registry — hence
#   inferred, not vouched by the far side) and nothing else.
# - claude-code-hooks (coder_gate.py + gate_routes.py, HS-104-02):
#   PreToolUse fires before the call and the hook blocks on the
#   decision, so tool_hooks and blocking are authoritative — flipped
#   in the same commit as the gate itself. The hook's session_id is
#   self-reported by the agent process (inferred). Usage and repo
#   head stay unavailable until a story implements them.
LEDGER: MappingProxyType[str, MappingProxyType[Capability, Standing]] = MappingProxyType({
    "tmux-pane": MappingProxyType({
        Capability.TOOL_HOOKS: Standing.UNAVAILABLE,
        Capability.SESSION_IDENTITY: Standing.INFERRED,
        Capability.USAGE_TOKENS: Standing.UNAVAILABLE,
        Capability.REPO_HEAD: Standing.INFERRED,
        Capability.BLOCKING: Standing.UNAVAILABLE,
    }),
    "delivery-node": MappingProxyType({
        Capability.TOOL_HOOKS: Standing.UNAVAILABLE,
        Capability.SESSION_IDENTITY: Standing.AUTHORITATIVE,
        Capability.USAGE_TOKENS: Standing.UNAVAILABLE,
        Capability.REPO_HEAD: Standing.AUTHORITATIVE,
        Capability.BLOCKING: Standing.UNAVAILABLE,
    }),
    "mesh-node": MappingProxyType({
        Capability.TOOL_HOOKS: Standing.UNAVAILABLE,
        Capability.SESSION_IDENTITY: Standing.INFERRED,
        Capability.USAGE_TOKENS: Standing.UNAVAILABLE,
        Capability.REPO_HEAD: Standing.UNAVAILABLE,
        Capability.BLOCKING: Standing.UNAVAILABLE,
    }),
    "claude-code-hooks": MappingProxyType({
        Capability.TOOL_HOOKS: Standing.AUTHORITATIVE,
        Capability.SESSION_IDENTITY: Standing.INFERRED,
        # HS-104-05: the Stop hook reports session totals read from
        # the agent's own transcript — the adapter's own record.
        Capability.USAGE_TOKENS: Standing.AUTHORITATIVE,
        Capability.REPO_HEAD: Standing.UNAVAILABLE,
        Capability.BLOCKING: Standing.AUTHORITATIVE,
    }),
})

LEDGER_SCHEMA_VERSION = 1


class CapabilityError(Exception):
    """Base for ledger refusals."""


class UnknownAdapterError(CapabilityError):
    def __init__(self, adapter: str) -> None:
        self.adapter = adapter
        super().__init__(
            f"unknown agent adapter {adapter!r}; the ledger declares {', '.join(ADAPTERS)}"
        )


class CapabilityUnavailableError(CapabilityError):
    """The ledger cannot vouch: the standing is ``unavailable``."""

    def __init__(self, adapter: str, capability: Capability, standing: Standing) -> None:
        self.adapter = adapter
        self.capability = capability
        self.standing = standing
        super().__init__(
            f"adapter {adapter!r} declares {capability.value!r} as "
            f"{standing.value!r}; refusing to act on a capability the "
            "ledger cannot vouch for"
        )


def standing_for(adapter: str, capability: Capability) -> Standing:
    """The declared standing, or :class:`UnknownAdapterError`."""
    try:
        row = LEDGER[adapter]
    except KeyError:
        raise UnknownAdapterError(adapter) from None
    return row[Capability(capability)]


def require_capability(adapter: str, capability: Capability) -> Standing:
    """The enforcement hook downstream stories MUST route through.

    Returns the standing (``authoritative`` or ``inferred`` — callers
    that must distinguish label their surface with the return value)
    and raises :class:`CapabilityUnavailableError` when the ledger
    says ``unavailable``. The census pins every call site.
    """
    standing = standing_for(adapter, capability)
    if standing is Standing.UNAVAILABLE:
        raise CapabilityUnavailableError(adapter, Capability(capability), standing)
    return standing


@dataclass(frozen=True)
class LedgerConsumer:
    """A code path that acts on a declared capability.

    Registered here in the same commit that adds the consumer, so the
    doctor check can refuse a consumer the ledger cannot back.
    """

    consumer: str  # dotted code-path name, greppable
    adapter: str
    capability: Capability


LEDGER_CONSUMERS: tuple[LedgerConsumer, ...] = (
    # HS-104-02: the tool-call gate's two capability-bearing routes.
    LedgerConsumer(
        "web.routes.system.gate_routes.receive", "claude-code-hooks", Capability.TOOL_HOOKS
    ),
    LedgerConsumer(
        "web.routes.system.gate_routes.decide", "claude-code-hooks", Capability.BLOCKING
    ),
    # HS-104-05: session receipts' reported tier — the usage receiver
    # and the tier assembly both act on reported tokens.
    LedgerConsumer(
        "web.routes.system.gate_routes.usage", "claude-code-hooks", Capability.USAGE_TOKENS
    ),
    LedgerConsumer(
        "session_receipts.build_receipt", "claude-code-hooks", Capability.USAGE_TOKENS
    ),
)


def consumer_violations(
    consumers: tuple[LedgerConsumer, ...] | None = None,
) -> list[str]:
    """Every registered consumer whose capability the ledger disowns."""
    out: list[str] = []
    for c in LEDGER_CONSUMERS if consumers is None else consumers:
        try:
            standing = standing_for(c.adapter, c.capability)
        except UnknownAdapterError:
            out.append(f"{c.consumer}: adapter {c.adapter!r} not in the ledger")
            continue
        if standing is Standing.UNAVAILABLE:
            out.append(
                f"{c.consumer}: requires {c.capability.value!r} on "
                f"{c.adapter!r} but the ledger declares it unavailable"
            )
    return out


def capabilities_payload() -> dict:
    """The whole table, for ``GET /api/agents/capabilities``."""
    return {
        "ledger_schema": LEDGER_SCHEMA_VERSION,
        "adapters": [
            {
                "adapter": adapter,
                "capabilities": {
                    cap.value: standing.value for cap, standing in row.items()
                },
            }
            for adapter, row in LEDGER.items()
        ],
    }
