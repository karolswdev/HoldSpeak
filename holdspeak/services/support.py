"""Linear execution of an iPad Workbench Blueprint `graph_json` on the hub.

The iPad Workbench (`apple/Sources/RuntimeCore/Workbench/Blueprint.swift`) saves a
Workflow's `graph_json` as a Swift-`Codable`, snake_case-keyed graph: a two-wire
Blueprints program (exec edges = control flow, data edges = typed values) with a
control-flow family (branch / for_each / while_loop / sequence).

The hub has no Blueprints interpreter. But the *common* Workbench output is a plain
linear pipeline — entry → model op → model op → … → output — and that we CAN run
faithfully by threading output→input through the existing persona/prompt run path
(`MeetingIntel.run_prompt`), reusing the same curated prompt templates the Swift
`BlueprintInterpreter.buildPrompt` uses.

This module is deliberately conservative: it ONLY runs a graph it can prove is an
*unambiguous single chain*. The instant it sees control flow or fan-out it CANNOT
linearize, it refuses (returns `linearizable=False`) so the route falls back to the
prompt + an honest warning rather than guessing an order for a branching program.

## The exact supported / unsupported boundary

A graph linearizes iff ALL of:

  * it parses: a dict with a `nodes` list; each node a dict with a string `id` and a
    `kind` that is a single-key tagged union (Swift's enum encoding) OR a bare string
    (e.g. `{"extract": "decisions"}` for `extract`); duplicate ids are rejected.
  * every node's kind is one of the **linear kinds**: `entry`, `source`, `merge`,
    `output` (pass-through) or `llm`, `extract`, `summarize`, `rewrite`, `keep_if`,
    `split_into_items` (single `then` exec-out, no fan).  Any `branch`, `for_each`,
    `while_loop`, `sequence` (named/multiple exec-outs) makes it NON-linear → refuse.
  * the exec edges (`exec_edges`) form a single simple chain: from `entry`, each node
    has at most one outgoing exec edge and at most one incoming exec edge, every exec
    edge endpoint is a known node, and following `then` from the entry visits every
    node exactly once (no fork, no join, no orphan, no cycle).

When it linearizes we run the model-op nodes in that order, threading each op's output
into the next op's input; pass-through nodes (entry/source/merge/output) carry the value
unchanged.  The run SOURCE for the first op is the request `input` (rendered through
`variables`).  We honour each node's prompt template exactly as the Swift interpreter does.
"""

from __future__ import annotations

from dataclasses import dataclass
import uuid
from typing import Any, Optional

from ..grounding import (
    GROUNDING_EXPANDS as _GROUNDING_EXPANDS,
    GROUNDING_MAX_REFS as _GROUNDING_MAX_REFS,
    hydrate_grounding_blocks as _hydrate_grounding,
    hydrate_grounding_blocks_detailed as _hydrate_grounding_detailed,
    meeting_digest as _meeting_digest,
)
from ..intel.providers import run_egress as _run_egress
from ..logging_config import get_logger

log = get_logger("services.support")

CANONICAL_SOURCE_TYPES: frozenset[str] = frozenset({"recipe", "input", "chain", "workflow", "invocation", "attempt"})
_SOURCE_TYPE_ALIASES: dict[str, str] = {"card": "input", "agent": "recipe"}

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def canonical_source_type(raw: Any) -> str:
    val = str(raw or "").strip().lower()
    return _SOURCE_TYPE_ALIASES.get(val, val)

def capability_descriptor(*, kind: str, name: str, readiness: str = "ready", detail: str = "", supported_placements: Optional[list[str]] = None, effect_classes: Optional[list[str]] = None, action_label: str = "", support: str = "supported") -> dict[str, Any]:
    return {"kind": kind, "input_schema": {"type": "object", "required": ["input"], "properties": {"input": {"type": "string", "help": "Material to work on."}}}, "input_help": "Choose or enter the material this capability should work on.", "supported_placements": supported_placements or ["this_machine"], "effect_classes": effect_classes or ["creates_artifact"], "readiness": {"state": readiness, "detail": detail}, "action_label": action_label or f"Run {name}", "support": support}

def _render_user_prompt(template: str, variables: dict[str, Any], user_input: str) -> str:
    if not template: return user_input
    mapping = dict(variables or {}); mapping.setdefault("input", user_input)
    class _Safe(dict):
        def __missing__(self, key: str) -> str: return "{" + key + "}"
    try: return template.format_map(_Safe(mapping))
    except Exception: return f"{template}\n\n{user_input}".strip()

def _persist_run_artifact(*, db: Any, kind: str, name: str, user_input: str, output: str, sources: list[dict[str, str]]) -> Optional[str]:
    try:
        artifact_id = _new_id("artifact"); head = " ".join(user_input.split())[:48]; title = f"{name}: {head}" if head else f"{name} run"
        db.plugins.record_artifact(artifact_id=artifact_id, meeting_id="", artifact_type="run_output", title=title, body_markdown=str(output or ""), status="draft", plugin_id=f"{kind}_run", plugin_version="1", sources=sources); return artifact_id
    except Exception as exc: log.error(f"Failed to persist run artifact: {exc}"); return None

SKILL_BUDGET_BYTES = 8192
def skills_for_recipe(db: Any, recipe_id: Optional[str]) -> str:
    if not recipe_id: return ""
    try: skills = db.skills.list_for_recipe(recipe_id, active_only=True)
    except Exception: return ""
    parts, dropped, total = [], [], 0
    for skill in skills:
        entry = f"## {skill.title}\n{skill.body}"; entry_bytes = len(entry.encode("utf-8"))
        if total + entry_bytes > SKILL_BUDGET_BYTES: dropped.append(skill.title); continue
        parts.append(entry); total += entry_bytes
    if dropped: log.warning(f"Skills dropped for recipe {recipe_id} (budget {SKILL_BUDGET_BYTES}B): " + ", ".join(dropped))
    return "# Skills\n\n" + "\n\n".join(parts) if parts else ""
def inject_skills(db: Any, system_prompt: str, recipe_id: Optional[str]) -> str:
    skills_text = skills_for_recipe(db, recipe_id); return system_prompt + "\n\n" + skills_text if skills_text and system_prompt else skills_text or system_prompt

# The run-egress badge rule is ONE function (`run_egress`, HS-130-04), re-exported
# here as `_run_egress` for the recipe pipeline and its tests.

def _context_material(db: Any, cid: str, kind: str, title: str) -> tuple[str, str]:
    kind = str(kind or "").strip().lower()
    try:
        if kind == "note":
            note = db.notes.get(cid)
            if note is not None and not getattr(note, "deleted", False): return note.title or title or cid, str(note.body_markdown or "")
        elif kind == "artifact":
            art = db.plugins.get_artifact(cid)
            if art is not None: return art.title or title or cid, str(art.body_markdown or "")
        elif kind == "meeting":
            state = db.meetings.get_meeting(cid)
            if state is not None: return state.title or title or cid, _meeting_digest(state)
        elif kind == "kb":
            kb = db.kbs.get(cid)
            if kb is not None and not getattr(kb, "deleted", False): return kb.name or title or cid, "\n".join(f"- {m}" for m in list(getattr(kb, "member_ids", None) or []))
    except Exception as exc: log.debug(f"ask context {kind}:{cid} unavailable: {exc}")
    return title or cid, ""

# Node kinds that are pure control flow / fan-out — their presence makes a graph
# NON-linear (the hub will not guess an order for these).
_CONTROL_FLOW_KINDS = frozenset(
    {"branch", "for_each", "while_loop", "sequence"}
)

# Pass-through control nodes: no model call, carry the threaded value unchanged.
_PASSTHROUGH_KINDS = frozenset({"entry", "source", "merge", "output"})

# Model-op nodes: each calls the engine. (`llm`/`extract`/`summarize`/`rewrite`.)
_MODEL_KINDS = frozenset({"llm", "extract", "summarize", "rewrite"})

# Pure local transforms (no model) we can also run inline in a linear chain.
_PURE_TRANSFORM_KINDS = frozenset({"keep_if", "split_into_items"})

_LINEAR_KINDS = _PASSTHROUGH_KINDS | _MODEL_KINDS | _PURE_TRANSFORM_KINDS

# ── Per-node provenance the iPad Blueprint model carries (and we must not drop) ──
#
# Each `BPNode` (apple/Sources/RuntimeCore/Workbench/Blueprint.swift) carries a
# `failure_policy`, and the node inspector adds a `runs_on` (model preference). The
# raw on-the-wire values are the Swift enum raw strings; `None`/unset means inherit
# the run default (== "auto" target, == the runner's default policy), which stays
# byte-identical to the pre-provenance behaviour.
#
# Workflow execution owns only truthful local dispositions. Old Swift wire names
# are decoded at this boundary; neither alias grants retry or route-selection
# authority. The routed controller remains the sole owner of actual attempts.
_FAILURE_POLICIES = frozenset({"carry", "hold", "skip"})
_FAILURE_POLICY_ALIASES = {
    "fallbackOnDevice": "carry",
    "retryThenQueue": "hold",
}
# Where a model-op node prefers to run (`ModelPref`). "desktop" pins the step to
# the paired desktop (the mesh dispatch, HSM-15-02): ON the hub that simply means
# "run here", so the trail preserves the pin instead of folding it to "auto".
_RUN_TARGETS = frozenset({"auto", "onDevice", "endpoint", "desktop"})


def _norm_failure_policy(raw: Any) -> Optional[str]:
    """Decode old wire aliases to canonical local failure disposition words.

    ``fallbackOnDevice`` was always a hub carry-through, not a fallback route;
    it becomes ``carry``. ``retryThenQueue`` becomes ``hold`` so the caller gets
    a typed refusal after the controller settles its admitted attempt. It never
    creates local retry or queue authority.
    """
    if not isinstance(raw, str):
        return None
    value = _FAILURE_POLICY_ALIASES.get(raw, raw)
    return value if value in _FAILURE_POLICIES else None


def _norm_run_target(raw: Any) -> str:
    """Normalize a node's raw `runs_on` to a known target; default "auto".

    Accepts the iPad `ModelPref` raw string (`auto`/`onDevice`/`endpoint`/`desktop`).
    Unset / unrecognised → "auto" (follow the hub's configured provider —
    byte-identical).
    """
    if isinstance(raw, str) and raw in _RUN_TARGETS:
        return raw
    return "auto"


@dataclass(frozen=True)
class GraphNode:
    """One parsed Blueprint node: id, kind tag, kind payload, and per-node provenance.

    `failure_policy` (None == inherit the run default) and `runs_on` (the resolved
    target, default "auto") are the per-node fields the iPad Blueprint carries; the
    linear runner honours a faithful subset of them and surfaces them in the run steps.
    """

    id: str
    kind: str
    payload: Any  # the value beside the kind tag (dict, str, or {} for nullary kinds)
    failure_policy: Optional[str] = None  # carry | hold | skip | None
    runs_on: str = "auto"  # auto | onDevice | endpoint


@dataclass(frozen=True)
class LinearPlan:
    """The result of trying to linearize a graph_json."""

    linearizable: bool
    reason: str = ""  # why it could NOT linearize (when linearizable is False)
    # The ordered nodes (entry → … → output), only set when linearizable.
    ordered: tuple[GraphNode, ...] = ()


def _node_kind(raw_kind: Any) -> Optional[tuple[str, Any]]:
    """Decode a node's `kind` field into (tag, payload).

    Swift encodes an enum-with-associated-values as a single-key object
    (`{"llm": {"name": .., "prompt": ..}}`, `{"extract": "decisions"}`) and a bare
    case as `{"summarize": {}}`. We also accept a plain string kind
    (`"summarize"`) defensively. Returns None if the shape is unrecognisable.
    """
    if isinstance(raw_kind, str):
        return (raw_kind, {})
    if isinstance(raw_kind, dict) and len(raw_kind) == 1:
        (tag, payload), = raw_kind.items()
        if isinstance(tag, str):
            return (tag, payload)
    return None


def parse_graph(graph_json: Any) -> Optional[list[GraphNode]]:
    """Parse a graph_json's `nodes` into GraphNodes, or None if it isn't a graph.

    A graph is a dict with a list `nodes`; each node a dict with a string `id` and a
    decodable `kind`. Duplicate ids → None (an ill-formed graph we won't run).
    """
    if not isinstance(graph_json, dict):
        return None
    raw_nodes = graph_json.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        return None
    out: list[GraphNode] = []
    seen: set[str] = set()
    for raw in raw_nodes:
        if not isinstance(raw, dict):
            return None
        node_id = raw.get("id")
        if not isinstance(node_id, str) or not node_id:
            return None
        if node_id in seen:
            return None
        seen.add(node_id)
        decoded = _node_kind(raw.get("kind"))
        if decoded is None:
            return None
        tag, payload = decoded
        out.append(GraphNode(
            id=node_id,
            kind=tag,
            payload=payload,
            failure_policy=_norm_failure_policy(raw.get("failure_policy")),
            runs_on=_norm_run_target(raw.get("runs_on")),
        ))
    return out


def _parse_exec_edges(graph_json: dict[str, Any]) -> Optional[list[tuple[str, str, str]]]:
    """Parse `exec_edges` into (from_node, from_name, to_node) triples.

    Swift shape: `{"from": {"node": .., "name": ..}, "to": ..}`. Returns None on a
    malformed edge list (we'd rather refuse than mis-order).
    """
    raw_edges = graph_json.get("exec_edges")
    if raw_edges is None:
        return []
    if not isinstance(raw_edges, list):
        return None
    out: list[tuple[str, str, str]] = []
    for e in raw_edges:
        if not isinstance(e, dict):
            return None
        frm = e.get("from")
        to = e.get("to")
        if not isinstance(frm, dict) or not isinstance(to, str):
            return None
        fn = frm.get("node")
        name = frm.get("name")
        if not isinstance(fn, str) or not isinstance(name, str):
            return None
        out.append((fn, name, to))
    return out


def linearize(graph_json: Any) -> LinearPlan:
    """Decide whether `graph_json` is an unambiguous single chain, and if so order it.

    See the module docstring for the exact boundary. Never raises on bad input —
    returns `LinearPlan(linearizable=False, reason=...)`.
    """
    nodes = parse_graph(graph_json)
    if nodes is None:
        return LinearPlan(False, "graph_json is not a parseable node graph")

    by_id = {n.id: n for n in nodes}

    # 1) Reject any control-flow / fan-out kind, or an unknown kind.
    for n in nodes:
        if n.kind in _CONTROL_FLOW_KINDS:
            return LinearPlan(
                False,
                f"node '{n.id}' is control-flow ('{n.kind}'); cannot linearize",
            )
        if n.kind not in _LINEAR_KINDS:
            return LinearPlan(
                False, f"node '{n.id}' has unsupported kind '{n.kind}'"
            )

    edges = _parse_exec_edges(graph_json)  # type: ignore[arg-type]
    if edges is None:
        return LinearPlan(False, "exec_edges are malformed")

    # 2) Every exec edge must reference known nodes and fire the linear "then" out.
    out_count: dict[str, int] = {n.id: 0 for n in nodes}
    in_count: dict[str, int] = {n.id: 0 for n in nodes}
    succ: dict[str, str] = {}
    for fn, name, to in edges:
        if fn not in by_id or to not in by_id:
            return LinearPlan(False, "an exec edge references an unknown node")
        if name != "then":
            # A named exec-out other than the linear "then" implies control flow.
            return LinearPlan(
                False, f"exec-out '{name}' on '{fn}' is not a linear edge"
            )
        out_count[fn] += 1
        in_count[to] += 1
        succ[fn] = to

    # 3) No node may fork (>1 out) or join (>1 in) — that's not a single chain.
    for nid in by_id:
        if out_count[nid] > 1:
            return LinearPlan(False, f"node '{nid}' fans out (multiple exec edges)")
        if in_count[nid] > 1:
            return LinearPlan(False, f"node '{nid}' is a join (multiple inbound edges)")

    # 4) Determine the chain head: the single node with no inbound edge. Prefer the
    #    declared `entry` if present and consistent; else the unique zero-in node.
    heads = [nid for nid in by_id if in_count[nid] == 0]
    if len(heads) != 1:
        return LinearPlan(
            False, "graph has no single chain head (0 or >1 unrooted nodes)"
        )
    head = heads[0]
    declared_entry = graph_json.get("entry") if isinstance(graph_json, dict) else None
    if isinstance(declared_entry, str) and declared_entry in by_id and declared_entry != head:
        return LinearPlan(False, "declared entry is not the chain head")

    # 5) Walk the chain from the head; it must visit every node exactly once.
    ordered: list[GraphNode] = []
    visited: set[str] = set()
    cur: Optional[str] = head
    while cur is not None:
        if cur in visited:  # cycle guard
            return LinearPlan(False, "exec graph has a cycle")
        visited.add(cur)
        ordered.append(by_id[cur])
        cur = succ.get(cur)
    if len(visited) != len(by_id):
        return LinearPlan(
            False, "graph is not fully connected as a single chain"
        )

    return LinearPlan(True, ordered=tuple(ordered))


# ── Prompt templates (mirror BlueprintInterpreter.buildPrompt) ────────────────


def _extract_artifact_type(payload: Any) -> str:
    """The artifact type for an `extract` node from its decoded kind payload.

    Swift encodes `case extract(ArtifactType)` (a single unlabeled associated
    value) as `{"extract": {"_0": "<rawValue>"}}`, so the decoded payload is the
    inner `{"_0": "decisions"}` object. We also accept a bare string payload
    (`{"extract": "decisions"}`) defensively. Anything else → "" (no type).
    """
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        inner = payload.get("_0")
        if isinstance(inner, str):
            return inner
    return ""


def build_node_prompt(node: GraphNode, input_text: str) -> str:
    """Build a model-op node's prompt from its kind + the threaded input.

    Byte-for-byte mirrors the Swift `BlueprintInterpreter.buildPrompt` so a graph
    run on the hub matches a graph run on the iPad.
    """
    if node.kind == "llm":
        prompt = ""
        if isinstance(node.payload, dict):
            prompt = str(node.payload.get("prompt") or "")
        return prompt.replace("{input}", input_text)
    if node.kind == "summarize":
        return (
            "Summarize the following into a tight, faithful summary. "
            "No preamble, just the summary.\n\n" + input_text
        )
    if node.kind == "rewrite":
        tone = ""
        if isinstance(node.payload, dict):
            tone = str(node.payload.get("tone") or "")
        elif isinstance(node.payload, str):
            tone = node.payload
        return (
            f"Rewrite the following text in a {tone} tone, preserving every fact "
            "and detail. Return only the rewritten text.\n\n" + input_text
        )
    if node.kind == "extract":
        # `extract(ArtifactType)` is a single UNLABELED associated value, so Swift's
        # synthesized Codable wraps the raw value under "_0":
        #   {"extract": {"_0": "decisions"}}
        # Accept that real wire shape first, then a bare string defensively.
        artifact_type = _extract_artifact_type(node.payload)
        readable = artifact_type.replace("_", " ")
        return (
            f"From the following, extract the {readable}. Return only that "
            "artifact, no preamble.\n\n" + input_text
        )
    return input_text


def apply_pure_transform(node: GraphNode, input_text: str) -> str:
    """Run a pure (no-model) transform node inline, mirroring the Swift interpreter."""
    if node.kind == "keep_if":
        keyword = ""
        if isinstance(node.payload, dict):
            keyword = str(node.payload.get("keyword") or "")
        needle = keyword.lower()
        if not needle:
            return input_text
        return "\n".join(
            line for line in input_text.split("\n") if needle in line.lower()
        )
    if node.kind == "split_into_items":
        items = [
            line.strip()
            for line in input_text.split("\n")
            if line.strip()
        ]
        return "\n".join(items)
    return input_text


# ── Per-node provenance the hub honours / surfaces ───────────────────────────


def resolved_failure_policy(node: GraphNode, default: str = "hold") -> str:
    """Return the canonical local disposition, never a retry instruction."""
    return node.failure_policy or default


def on_node_error(node: GraphNode, carried_input: str) -> Optional[str]:
    """Apply only local workflow semantics after controller settlement.

    ``carry`` and ``skip`` preserve input. ``hold`` deliberately returns no
    value: the service emits a named typed refusal, rather than pretending it
    can retry, queue, or fall back to another deployment.
    """
    policy = resolved_failure_policy(node)
    if policy in {"carry", "skip"}:
        return carried_input
    return None
