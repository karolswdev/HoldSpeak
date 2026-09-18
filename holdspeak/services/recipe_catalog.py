"""HS-200-17 — the prepared-recipe catalog and its compiler (contract C5).

**This is not** :mod:`holdspeak.services.recipe_service`.  That module owns
*Agents* — the user-authored saved prompts behind ``recipe.list`` /
``recipe.run`` — and it has owned the word "recipe" on the wire since
HS-116.  A **prepared recipe** is the other thing C5 names: one of three
*versioned descriptors, written in Python in this tree*, that binds an
already-shipped service to a supported execution path.  The two namespaces
never meet: prepared recipes live under ``practice_recipe.*`` on MCP and
``/automations/practice-recipes`` over HTTP.  ``test_phase200_recipe_catalog``
fences the separation.

What a descriptor is, and what it is NOT (ruling R17-1)
--------------------------------------------------------
A descriptor is *declared code*, not a DSL and not a workflow language.  It
declares six things C5 requires — input schema, source requirements, output,
execution owner, effects, supported triggers — and nothing it declares is
free-form: every execution step is a **qualified ref** into a module that
already ships, resolved by import at compile time.

Limits follow one rule, and it is narrower than it first reads. Where a
service enforces a cap, the descriptor points at **that service's own
constant** and reads it at compile time; it never transcribes the number,
because a transcribed number proves only that somebody can transcribe
(``reference_lying_test_doubles``). Where no service enforces a cap, there
are exactly two honest options and the descriptor must take one: a
``literal:`` bound that is really **passed to a step** (so a fence can see
it move), or **no limit at all**. What a descriptor may never carry is a
number nothing reads — ``weekly_update`` declared ``max_claims: 40`` in the
first cut, bound to no step and enforced by nothing, and counsel set it to 1
with every fence still green. Every declared input obeys the same rule: an
input no step binds is a configurable the plan cannot deliver.

The three recipes and the services they bind
--------------------------------------------
======================  =======================================================
``preparation_brief``   :class:`~holdspeak.services.preparation_brief_service.PreparationBriefService`
                        (HS-200-11)
``decision_review``     :class:`~holdspeak.services.follow_through_service.FollowThroughService`,
                        :class:`~holdspeak.services.decision_record_service.DecisionRecordService`
                        (HS-200-12/13) and the preparation manifest for coverage
``weekly_update``       :class:`~holdspeak.services.project_update_service.ProjectUpdateService`
                        — the Phase 162 Update Factory
======================  =======================================================

Typed gaps (ruling R17-5) reuse the vocabulary that already shipped
-------------------------------------------------------------------
A gap row is shaped like a C4 coverage row
(``needs_you_aggregate._coverage_row``) and its ``state`` is drawn from
``needs_you_aggregate.COVERAGE_STATES`` — the same five words the arrival
aggregate and the preparation manifest already use.  Two fields are added,
because C5 asks a question C4 does not: ``missing`` (what is not there) and
``supplied_by`` (what would supply it).  No fake all-clear: a plan with any
gap is ``ready == False``, and an empty gap list on a plan that was never
compiled against real sources is not reachable — :func:`compile_recipe`
always evaluates every required source against the coverage map it is
handed, and a source absent from that map is ``unavailable``, never
``available``.

One definition, two triggers
----------------------------
``trigger_kind`` takes the two tokens ``WatchService._evaluate_core`` already
uses (``holdspeak/services/watch_service.py:671``): ``"manual"`` and
``"scheduled"``.  Compiling the same descriptor under either token yields
plans carrying the identical ``recipe_id``, ``recipe_version`` and step
refs; only ``trigger``/``trigger_owner`` differ.  Phase 200 introduces no
second scheduler (C9): a descriptor *names* the owner that would supply a
scheduled firing, and reports a typed gap while that owner is not wired.
"""
from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .errors import ServiceError
from .needs_you_aggregate import COVERAGE_STATES

# ── the two trigger tokens, borrowed from the watch evaluation core ──────

TRIGGER_MANUAL = "manual"
TRIGGER_SCHEDULED = "scheduled"
TRIGGERS: tuple[str, ...] = (TRIGGER_MANUAL, TRIGGER_SCHEDULED)

#: The owner chain that supplies a recurring firing in this product today
#: (ruling R17-8: a descriptor may not name a trigger owner that cannot be
#: shown to fire; ruling R17-12: it names the specific adapter, not a
#: generic sweep).  End to end, and every link verified in the tree:
#:
#: 1. A ``connector_watches`` row carries ``evaluation_cadence_minutes`` and
#:    ``next_evaluation_at`` (``db/schema.py:2490-2492``) and is armed when
#:    it is created (HS-200-43; ``watch_service.py:118`` writes the first
#:    ``next_evaluation_at``, and ``list_due_watches`` selects only non-NULL
#:    ones, ``watch_service.py:72``).
#: 2. ``HeartbeatConductor`` is the wall clock: it ticks, compares elapsed
#:    against ``sweep_every_minutes`` and calls ``HeartbeatService.run_sweep``
#:    (``runtime/heartbeat.py:126-141``), which drives
#:    ``WatchService.evaluate_due`` (``watch_service.py:1003``).
#: 3. A due evaluation mints a ``watch_effects`` row whose ``action_kind``
#:    is ``project.steward.run_once`` (``watch_validation.py:59``).
#: 4. ``ProjectStewardService.run_due`` drains those effects
#:    (``project_steward_service.py:141-145``), gated by the project's
#:    ``unattended_enabled`` (``:225``, default OFF).
#:
#: ``ScheduledRecordingService`` is the other real clock — the only
#: zone-aware one (``scheduled_recording_service.py:177`` takes a ``tz``) —
#: and it belongs to recording, which is HS-200-22's business, not a
#: prepared recipe's.
#:
#: Two plausible-sounding owners are NOT owners, and the descriptors say so
#: rather than implying otherwise:
#:
#: * **Cadence** is a nudge projection, not a scheduler.  ``cadence_loops``
#:   is keyed ``(source_type, source_id)`` and carries no schedule and no
#:   next-fire column; ``CadenceService`` exposes no create operation and its
#:   ``run_now`` is a manual verb (``cadence_service.py:45-172``).
#: * **The steward** drains work but keeps no clock of its own:
#:   ``project.steward.trigger`` answers ``scheduler_not_wired``
#:   (``mcp/families/project.py:1681``) and ``steward_policies`` carries only
#:   ``cooldown_seconds`` (``db/schema.py:4139``).  It is the last link in
#:   the chain above, driven by the heartbeat, never the trigger owner.
#:
#: C9 separates the two roles, and so does a descriptor: the chain below
#: supplies the firing; the recipe's ``steps`` name the executor.
SCHEDULED_TRIGGER_OWNER = (
    "connector_watches interval -> HeartbeatService.run_sweep -> "
    "WatchService.evaluate_due -> watch_effects "
    "(action_kind='project.steward.run_once') -> "
    "ProjectStewardService.run_due"
)

# ── recipe ids ───────────────────────────────────────────────────────────

RECIPE_PREPARATION_BRIEF = "preparation_brief"
RECIPE_DECISION_REVIEW = "decision_review"
RECIPE_WEEKLY_UPDATE = "weekly_update"

# ── gap kinds ────────────────────────────────────────────────────────────
#
# The *kind* says which question failed; the *state* (a C4 coverage state)
# says how badly.  Both travel on every gap row.

GAP_MISSING_ADAPTER = "missing_adapter"
GAP_UNAVAILABLE_PREREQUISITE = "unavailable_prerequisite"
GAP_STALE_DESCRIPTOR = "stale_descriptor"
GAP_UNSUPPORTED_TRIGGER = "unsupported_trigger"
GAP_MISSING_INPUT = "missing_input"
GAP_KINDS: tuple[str, ...] = (
    GAP_MISSING_ADAPTER,
    GAP_UNAVAILABLE_PREREQUISITE,
    GAP_STALE_DESCRIPTOR,
    GAP_UNSUPPORTED_TRIGGER,
    GAP_MISSING_INPUT,
)


class CatalogError(ServiceError):
    """The descriptor table itself is wrong — a programming error, not a gap.

    A *gap* is a fact about the running installation (no model route, no
    scheduler, no Project).  A :class:`CatalogError` is a fact about this
    file: a ref that does not import, a bound parameter the target method
    does not take, a limit whose source constant does not exist.  It is
    raised, never returned, so the fence tests see it.

    It is a :class:`~holdspeak.services.errors.ServiceError` so both
    transports answer with a stable ``code`` instead of a bare string: over
    HTTP the automations route maps it, and over MCP the server's
    ServiceError handler carries the code through (counsel P2-2/P2-3).
    """

    def __init__(self, detail: str, code: str = "catalog_error") -> None:
        super().__init__(code, detail, context={"status": 500})


class UnknownRecipe(CatalogError):
    """No descriptor carries this id."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail, code="unknown_recipe")
        self.context["status"] = 404


# ── descriptor pieces ────────────────────────────────────────────────────


@dataclass(frozen=True)
class InputField:
    """One field of a recipe's input schema."""

    name: str
    type: str          # "string" | "integer"
    required: bool
    description: str
    default: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "default": self.default,
        }


@dataclass(frozen=True)
class SourceRequirement:
    """One source the recipe reads, and whether it can run without it."""

    #: A C4 coverage kind where one applies (``project``/``watch``/
    #: ``meeting``/``commitment``), else a named reader (``model_route``).
    kind: str
    required: bool
    description: str
    #: What would supply this source if it is missing — a settings screen, a
    #: connector, a story.  Never empty: R17-5 forbids a nameless gap.
    supplied_by: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "required": self.required,
            "description": self.description,
            "supplied_by": self.supplied_by,
        }


@dataclass(frozen=True)
class ExecutionStep:
    """One bound call into a service that already performs the work.

    ``qualified_ref`` is ``"module.path:Class.method"``.  It is resolved by
    import — :func:`resolve_step` returns the *real function object* — so a
    renamed method breaks the catalog test rather than shipping a descriptor
    that points at nothing.

    ``binds`` names the plan values passed as keyword arguments.  Every name
    must be a real parameter of the target method; :func:`resolve_step`
    checks that against :func:`inspect.signature`.
    """

    name: str
    qualified_ref: str
    binds: tuple[str, ...]
    #: The :class:`~holdspeak.runtime.composition.RuntimeServices` field the
    #: hub carries this service in, or ``""`` when the root does not carry it.
    runtime_field: str
    #: How a caller obtains the instance (prose, for the catalog listing).
    composed_by: str

    @property
    def module_path(self) -> str:
        return self.qualified_ref.split(":", 1)[0]

    @property
    def attr_path(self) -> str:
        return self.qualified_ref.split(":", 1)[1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "qualified_ref": self.qualified_ref,
            "binds": list(self.binds),
            "runtime_field": self.runtime_field,
            "composed_by": self.composed_by,
        }


@dataclass(frozen=True)
class Limit:
    """One bound on the recipe's work.

    ``source`` is either ``"module.path:CONSTANT"`` — read off the real
    module at compile time, so the catalog can never disagree with the
    service that enforces it — or ``"literal:<int>"`` for a bound no shipped
    constant owns (a wall-clock budget, say).
    """

    name: str
    source: str
    why: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "source": self.source, "why": self.why}


@dataclass(frozen=True)
class TriggerBinding:
    """Which owner supplies a firing of this kind, and whether it is wired.

    C9: Phase 200 adds no second scheduler.  ``available=False`` is the
    honest state for a trigger whose owner exists but is not yet bound to
    this recipe; ``supplied_by`` names what would bind it.
    """

    trigger: str
    owner: str
    available: bool
    supplied_by: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger,
            "owner": self.owner,
            "available": self.available,
            "supplied_by": self.supplied_by,
        }


@dataclass(frozen=True)
class RecipeDescriptor:
    """One versioned prepared recipe.  Frozen: a descriptor is a constant."""

    recipe_id: str
    version: int
    title: str
    inputs: tuple[InputField, ...]
    sources: tuple[SourceRequirement, ...]
    output: str
    output_owner: str
    steps: tuple[ExecutionStep, ...]
    effects: tuple[str, ...]
    triggers: tuple[TriggerBinding, ...]
    route_policy: str
    limits: tuple[Limit, ...]
    acceptance: tuple[str, ...]

    def input(self, name: str) -> InputField | None:
        for candidate in self.inputs:
            if candidate.name == name:
                return candidate
        return None

    def trigger(self, trigger_kind: str) -> TriggerBinding | None:
        for candidate in self.triggers:
            if candidate.trigger == trigger_kind:
                return candidate
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "recipe_id": self.recipe_id,
            "version": self.version,
            "title": self.title,
            "inputs": [f.to_dict() for f in self.inputs],
            "sources": [s.to_dict() for s in self.sources],
            "output": self.output,
            "output_owner": self.output_owner,
            "steps": [s.to_dict() for s in self.steps],
            "effects": list(self.effects),
            "triggers": [t.to_dict() for t in self.triggers],
            "route_policy": self.route_policy,
            "limits": [limit.to_dict() for limit in self.limits],
            "acceptance": list(self.acceptance),
        }


# ── the catalog ──────────────────────────────────────────────────────────
#
# Three descriptors, in the order C5 lists them.  Every ``qualified_ref``
# below points at a method that shipped before this story: nothing here is a
# new execution engine.

_PREPARATION_BRIEF = RecipeDescriptor(
    recipe_id=RECIPE_PREPARATION_BRIEF,
    version=1,
    title="Meeting preparation brief",
    inputs=(
        InputField("project_id", "string", True, "The Project to prepare for."),
        InputField("purpose", "string", True, "What the meeting is for, in the owner's words."),
        InputField(
            "generator", "string", False,
            "'model' drafts through the routed model; 'deterministic' does not leave the machine.",
            default="model",
        ),
    ),
    sources=(
        SourceRequirement(
            "project", True, "The Project Room projection the manifest is built from.",
            "Create the Project, or open an existing one, in the Project Room.",
        ),
        SourceRequirement(
            "watch", False, "Connector Watches whose snapshots supply observed revisions.",
            "Connect a source in Settings and attach it to the Project.",
        ),
        SourceRequirement(
            "meeting", False, "Linked meetings supplying decisions carried into the brief.",
            "Link a meeting to the Project.",
        ),
        SourceRequirement(
            "model_route", False,
            "A ready inference route; required only when generator='model'.",
            "Assign a model for the preparation capability in Settings > Models.",
        ),
    ),
    output="A draft preparation brief with a source manifest, bounded sections, and C2 claim axes.",
    output_owner="PreparationBriefService (project_briefs table)",
    steps=(
        ExecutionStep(
            name="prepare",
            qualified_ref="holdspeak.services.preparation_brief_service:PreparationBriefService.prepare",
            binds=("project_id", "purpose", "generator"),
            runtime_field="",
            composed_by=(
                "The hub carries it on its WebContext as project_brief_service; "
                "outside the hub it is built over composition.current().db."
            ),
        ),
    ),
    effects=(
        "Writes one draft row to project_briefs; the owner must keep() it to make it durable work.",
        "Sends the purpose and the drafted claims to the routed model when generator='model'.",
        "Sends nothing off the machine when generator='deterministic'.",
    ),
    triggers=(
        TriggerBinding(
            TRIGGER_MANUAL, "web:/api/projects/{project_id}/briefs/prepare", True,
            "Shipped in HS-200-11.",
        ),
        TriggerBinding(
            TRIGGER_SCHEDULED, SCHEDULED_TRIGGER_OWNER, False,
            "HS-200-21 must add a watch_effects action_kind for a prepared "
            "brief and drain it beside project.steward.run_once. No effect "
            "kind names this recipe today (holdspeak/watch_validation.py:59 "
            "is the registry).",
        ),
    ),
    route_policy=(
        "generator='model' refuses with a named ROUTE_* state rather than silently "
        "falling back to the deterministic drafter (preparation_brief_service.PreparationRefused)."
    ),
    limits=(
        Limit(
            "max_priorities",
            "holdspeak.services.preparation_brief_service:MAX_PRIORITIES",
            "The Outline refuses more; the model parser truncates to it.",
        ),
        Limit(
            "max_questions",
            "holdspeak.services.preparation_brief_service:MAX_QUESTIONS",
            "Open questions are bounded by the same Outline cap.",
        ),
        Limit(
            "max_obligations",
            "holdspeak.services.preparation_brief_service:MAX_OBLIGATIONS",
            "Obligations carried into the brief are bounded by the same Outline cap.",
        ),
    ),
    acceptance=(
        "The brief names its Project and its purpose.",
        "Every omitted source appears in the manifest with a reason and a repair path.",
        "No section exceeds its declared limit.",
        "An unavailable model route refuses and hands the purpose back untouched.",
    ),
)

_DECISION_REVIEW = RecipeDescriptor(
    recipe_id=RECIPE_DECISION_REVIEW,
    version=1,
    title="Decision and commitment review",
    # Only project_id. A review window was declared here at first, and no
    # step could honour it: neither FollowThroughService.board nor
    # DecisionRecordService.list_records takes a time bound at all, so the
    # descriptor was advertising a configurable the plan could not deliver
    # (ruling R17-10). A window returns when a step can consume one.
    inputs=(
        InputField("project_id", "string", True, "The Project under review."),
    ),
    sources=(
        SourceRequirement(
            "project", True, "The Project the board and the manifest are scoped to.",
            "Create the Project, or open an existing one, in the Project Room.",
        ),
        SourceRequirement(
            "commitment", False, "Open commitments on the follow-through board.",
            "Commitments arrive from reviewed meeting outcomes (HS-200-12).",
        ),
        SourceRequirement(
            "meeting", False, "Meetings that sourced the decisions under review.",
            "Link a meeting to the Project and review its proposals.",
        ),
    ),
    output=(
        "Current decisions, unresolved obligations, and the evidence gaps behind them, "
        "each with its C4 coverage state."
    ),
    output_owner="FollowThroughService, DecisionRecordService and the preparation manifest (read-only)",
    steps=(
        ExecutionStep(
            name="obligations",
            qualified_ref="holdspeak.services.follow_through_service:FollowThroughService.board",
            binds=("project_id",),
            runtime_field="follow_through_service",
            composed_by="composition.service('follow_through_service', ...)",
        ),
        ExecutionStep(
            name="decisions",
            qualified_ref="holdspeak.services.decision_record_service:DecisionRecordService.list_records",
            binds=("limit",),
            runtime_field="",
            composed_by="Built over composition.current().db; the hub carries no wired instance.",
        ),
        ExecutionStep(
            name="coverage",
            qualified_ref="holdspeak.services.preparation_brief_service:PreparationBriefService.preview_manifest",
            binds=("project_id",),
            runtime_field="",
            composed_by=(
                "The hub carries it on its WebContext as project_brief_service; "
                "outside the hub it is built over composition.current().db."
            ),
        ),
    ),
    effects=(
        "Reads only. No row is written, no commitment is completed, no decision is accepted.",
        "Nothing leaves the machine: every step is a local projection.",
    ),
    triggers=(
        TriggerBinding(
            TRIGGER_MANUAL, "web:/api/follow-through + /api/projects/{project_id}/briefs/manifest",
            True, "Shipped in HS-200-12 and HS-200-13.",
        ),
        TriggerBinding(
            TRIGGER_SCHEDULED, SCHEDULED_TRIGGER_OWNER, False,
            "HS-200-33 must add a watch_effects action_kind for the review "
            "and drain it beside project.steward.run_once. Cadence cannot own "
            "this: cadence_loops is a projection of open loops keyed "
            "(source_type, source_id) with no schedule and no next-fire "
            "column, and CadenceService has no create operation "
            "(holdspeak/services/cadence_service.py:45-172).",
        ),
    ),
    route_policy="No model route is used. The review is deterministic.",
    limits=(
        Limit(
            "limit",
            "literal:200",
            "Decision records read per review. A caller's choice, really "
            "passed to list_records, which clamps it to its own ceiling.",
        ),
    ),
    acceptance=(
        "Every unresolved obligation names an owner or says the owner is unknown.",
        "A superseded decision is never presented as current.",
        "A source that could not be read appears as a coverage gap, not as an all-clear.",
    ),
)

_WEEKLY_UPDATE = RecipeDescriptor(
    recipe_id=RECIPE_WEEKLY_UPDATE,
    version=1,
    title="Weekly Project update",
    inputs=(
        InputField("project_id", "string", True, "The Project to report on."),
        InputField(
            "generator", "string", False,
            "'deterministic' composes from the delta alone; 'model' drafts prose over it.",
            default="deterministic",
        ),
    ),
    sources=(
        SourceRequirement(
            "project", True, "The Project and its delta since the last published update.",
            "Create the Project, or open an existing one, in the Project Room.",
        ),
        SourceRequirement(
            "watch", False, "Connector Watch snapshots inside the observation window.",
            "Connect a source in Settings and attach it to the Project.",
        ),
        SourceRequirement(
            "model_route", False,
            "A ready inference route; required only when generator='model'.",
            "Assign a model for the update capability in Settings > Models.",
        ),
    ),
    output="An editable update draft whose claims carry support, acceptance, and coverage.",
    output_owner="ProjectUpdateService (the Phase 162 Update Factory)",
    steps=(
        ExecutionStep(
            name="draft",
            qualified_ref="holdspeak.services.project_update_service:ProjectUpdateService.draft_update",
            binds=("project_id", "generator"),
            runtime_field="project_update_service",
            composed_by="composition.service('project_update_service', ...)",
        ),
    ),
    effects=(
        "Writes one draft update; publishing is a separate owner act (publish_update).",
        "Sends the delta to the routed model when generator='model'.",
        "Sends nothing off the machine when generator='deterministic'.",
    ),
    triggers=(
        TriggerBinding(
            TRIGGER_MANUAL, "web:/api/projects/{project_id}/updates/draft", True,
            "Shipped in Phase 162.",
        ),
        TriggerBinding(
            TRIGGER_SCHEDULED, SCHEDULED_TRIGGER_OWNER, False,
            "The nearest to wired of the three: project.steward.run_once "
            "already exists as a watch_effects action_kind and "
            "ProjectStewardService.run_due already drains it "
            "(project_steward_service.py:141). HS-200-35 must point a watch "
            "interval at this Project and turn on unattended_enabled "
            "(default OFF, project_steward_service.py:225). The steward is "
            "the EXECUTOR at the end of that chain, not the trigger owner: "
            "project.steward.trigger answers 'scheduler_not_wired' "
            "(mcp/families/project.py:1681).",
        ),
    ),
    route_policy=(
        "generator='model' falls back to no prose rather than inventing claims; "
        "every claim keeps its C2 support axis independent of its kind."
    ),
    # No cap. ``ProjectUpdateService`` truncates nothing and defines no
    # claim ceiling, so this descriptor declares none: an absent limit is
    # honest, an invented one is a promise the product will not keep
    # (ruling R17-10). The first cut declared ``max_claims: 40``; counsel
    # set it to 1 and every fence stayed green, because nothing read it.
    limits=(),
    acceptance=(
        "Every sentence carries a claim kind and a support state.",
        "An unsupported sentence is never presented as checked fact.",
        "The update names the observation window it covers.",
    ),
)

CATALOG: dict[str, RecipeDescriptor] = {
    d.recipe_id: d
    for d in (_PREPARATION_BRIEF, _DECISION_REVIEW, _WEEKLY_UPDATE)
}


# ── reading the catalog ──────────────────────────────────────────────────


def list_descriptors() -> list[RecipeDescriptor]:
    """Every prepared recipe, in catalog order."""
    return list(CATALOG.values())


def get_descriptor(recipe_id: str) -> RecipeDescriptor:
    """The descriptor for *recipe_id*, or :class:`UnknownRecipe`."""
    try:
        return CATALOG[str(recipe_id)]
    except KeyError:
        raise UnknownRecipe(
            f"no prepared recipe {recipe_id!r}; the catalog holds "
            f"{sorted(CATALOG)}"
        ) from None


def catalog_payload() -> dict[str, Any]:
    """The wire shape both the HTTP route and the MCP family return."""
    return {
        "recipes": [d.to_dict() for d in list_descriptors()],
        "triggers": list(TRIGGERS),
        "coverage_states": list(COVERAGE_STATES),
        "gap_kinds": list(GAP_KINDS),
    }


# ── binding ──────────────────────────────────────────────────────────────


def resolve_step(step: ExecutionStep) -> Callable[..., Any]:
    """Import *step*'s qualified ref and return the real function object.

    Raises :class:`CatalogError` when the module, the class, or the method
    does not exist, and when ``binds`` names a parameter the method does not
    take.  Both are programming errors in this file, not facts about the
    installation, so they are raised rather than returned as gaps.
    """
    try:
        module = importlib.import_module(step.module_path)
    except Exception as exc:  # pragma: no cover - a broken import is fatal
        raise CatalogError(
            f"{step.qualified_ref}: module {step.module_path!r} does not import ({exc})"
        ) from exc
    target: Any = module
    for part in step.attr_path.split("."):
        target = getattr(target, part, None)
        if target is None:
            raise CatalogError(
                f"{step.qualified_ref}: {part!r} does not exist on {step.module_path}"
            )
    if not callable(target):
        raise CatalogError(f"{step.qualified_ref}: resolved to a non-callable")
    parameters = inspect.signature(target).parameters
    accepts_kwargs = any(
        p.kind is inspect.Parameter.VAR_KEYWORD for p in parameters.values()
    )
    for bound in step.binds:
        if bound not in parameters and not accepts_kwargs:
            raise CatalogError(
                f"{step.qualified_ref}: binds {bound!r}, which is not a parameter "
                f"of the method (it takes {sorted(parameters)})"
            )
    return target


def resolve_limits(descriptor: RecipeDescriptor) -> dict[str, int]:
    """Read every limit off the constant the executing service enforces.

    A ``literal:`` source is the only place a number is written here, and it
    is written only where no shipped constant owns the bound.
    """
    out: dict[str, int] = {}
    for limit in descriptor.limits:
        if limit.source.startswith("literal:"):
            out[limit.name] = int(limit.source.split(":", 1)[1])
            continue
        module_path, _, constant = limit.source.partition(":")
        try:
            module = importlib.import_module(module_path)
        except Exception as exc:
            raise CatalogError(
                f"limit {limit.name!r}: module {module_path!r} does not import ({exc})"
            ) from exc
        if not hasattr(module, constant):
            raise CatalogError(
                f"limit {limit.name!r}: {module_path} has no constant {constant!r}"
            )
        value = getattr(module, constant)
        if not isinstance(value, int) or isinstance(value, bool):
            raise CatalogError(
                f"limit {limit.name!r}: {limit.source} is {value!r}, not an int"
            )
        out[limit.name] = value
    return out


def unreachable_declarations(descriptor: RecipeDescriptor) -> list[str]:
    """Inputs and limits no step binds, i.e. things nothing can read.

    Ruling R17-10.  A ``literal:`` limit or an input that reaches no step is
    invisible: counsel changed ``weekly_update``'s ``max_claims`` from 40 to
    1 and every fence stayed green, because nothing read it.  A limit whose
    source is a real service constant is exempt -- it documents a bound the
    service enforces on its own, whether or not a step passes it.
    """
    bound: set[str] = set()
    for step in descriptor.steps:
        bound.update(step.binds)
    out: list[str] = []
    for spec in descriptor.inputs:
        if spec.name not in bound:
            out.append(f"input {spec.name!r}")
    for limit in descriptor.limits:
        if limit.source.startswith("literal:") and limit.name not in bound:
            out.append(f"limit {limit.name!r}")
    return out


def runtime_field_is_real(step: ExecutionStep) -> bool:
    """``True`` when the step names a field the composition root carries.

    An empty ``runtime_field`` is lawful (the root does not carry every
    service); a *non-empty* one that the root does not carry is a typo, and
    ``composition.service`` would raise ``KeyError`` at run time.
    """
    if not step.runtime_field:
        return True
    from holdspeak.runtime.composition import SERVICE_FIELDS

    return step.runtime_field in SERVICE_FIELDS


# ── typed gaps ───────────────────────────────────────────────────────────


def gap(
    *,
    kind: str,
    state: str,
    subject: str,
    missing: str,
    supplied_by: str,
    reason: str = "",
) -> dict[str, Any]:
    """One typed gap, shaped like a C4 coverage row plus C5's two questions.

    ``missing`` says what is not there; ``supplied_by`` says what would
    supply it.  R17-5: a gap with either field empty is a fake all-clear
    wearing a gap's clothes, so both are required here and fenced in the
    tests.
    """
    if kind not in GAP_KINDS:
        raise CatalogError(f"unknown gap kind {kind!r}")
    if state not in COVERAGE_STATES:
        raise CatalogError(
            f"gap state {state!r} is not one of the C4 coverage states "
            f"{list(COVERAGE_STATES)}"
        )
    if not missing.strip() or not supplied_by.strip():
        raise CatalogError(
            f"gap {kind}/{subject}: both 'missing' and 'supplied_by' are required"
        )
    return {
        "kind": kind,
        "state": state,
        "subject": subject,
        "missing": missing,
        "supplied_by": supplied_by,
        "reason": reason,
    }


# ── the compiled plan ────────────────────────────────────────────────────


@dataclass(frozen=True)
class CompiledPlan:
    """One configuration plan (C5).

    ``plan_id`` is derived from the descriptor identity and the resolved
    inputs, so replaying the same request under the same trigger yields the
    same identity rather than a second plan (C6's replay rule).  The trigger
    is deliberately *outside* the hash: a manual run and its later scheduled
    counterpart are the same plan reached two ways, which is exactly what
    the acceptance criterion asks the catalog to prove.
    """

    plan_id: str
    revision: int
    recipe_id: str
    recipe_version: int
    trigger: str
    trigger_owner: str
    inputs: dict[str, Any]
    source_scope: list[dict[str, Any]]
    route_policy: str
    limits: dict[str, int]
    acceptance: list[str]
    steps: list[dict[str, Any]]
    effects: list[str]
    gaps: list[dict[str, Any]] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        """No gap stands between this plan and a run."""
        return not self.gaps

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "revision": self.revision,
            "recipe_id": self.recipe_id,
            "recipe_version": self.recipe_version,
            "trigger": self.trigger,
            "trigger_owner": self.trigger_owner,
            "inputs": dict(self.inputs),
            "source_scope": list(self.source_scope),
            "route_policy": self.route_policy,
            "limits": dict(self.limits),
            "acceptance": list(self.acceptance),
            "steps": list(self.steps),
            "effects": list(self.effects),
            "gaps": list(self.gaps),
            "ready": self.ready,
        }


def _plan_id(recipe_id: str, version: int, inputs: Mapping[str, Any]) -> str:
    material = json.dumps(
        {"recipe": recipe_id, "version": version, "inputs": dict(sorted(inputs.items()))},
        sort_keys=True, separators=(",", ":"),
    )
    return "plan_" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def compile_recipe(
    recipe_id: str,
    *,
    version: int | None = None,
    trigger: str = TRIGGER_MANUAL,
    inputs: Mapping[str, Any] | None = None,
    coverage: Mapping[str, str] | None = None,
) -> CompiledPlan:
    """Bind a descriptor to one concrete request.

    *version* is the version the CALLER believes it is configuring.  When it
    disagrees with the descriptor in the tree the plan carries a
    ``stale_descriptor`` gap and is not ready — a saved plan cannot silently
    start meaning something else after the descriptor is revised.

    *coverage* maps a :class:`SourceRequirement` kind to a C4 coverage state.
    A required source that is absent from the map is ``unavailable``, never
    ``available``: an unobserved source is not an all-clear (C4).

    Every gap is returned on the plan; nothing raises for an installation
    fact.  Only a broken descriptor raises (:class:`CatalogError`).
    """
    descriptor = get_descriptor(recipe_id)
    supplied = dict(inputs or {})
    coverage = dict(coverage or {})
    gaps: list[dict[str, Any]] = []

    # 1. Descriptor version --------------------------------------------
    if version is not None and int(version) != descriptor.version:
        gaps.append(gap(
            kind=GAP_STALE_DESCRIPTOR,
            state="stale",
            subject=f"{descriptor.recipe_id}@{version}",
            missing=(
                f"version {version} of this recipe; the tree ships version "
                f"{descriptor.version}"
            ),
            supplied_by=(
                "Recompile the plan against the current descriptor and re-read "
                "its inputs; a revised descriptor may take different fields."
            ),
            reason="descriptor_revised",
        ))

    # 2. Trigger --------------------------------------------------------
    binding = descriptor.trigger(trigger)
    trigger_owner = ""
    if trigger not in TRIGGERS:
        gaps.append(gap(
            kind=GAP_UNSUPPORTED_TRIGGER,
            state="unavailable",
            subject=str(trigger),
            missing=f"trigger {trigger!r} is not a trigger kind ({list(TRIGGERS)})",
            supplied_by="Phase 200 introduces no second scheduler (C9).",
            reason="unknown_trigger_kind",
        ))
    elif binding is None:
        gaps.append(gap(
            kind=GAP_UNSUPPORTED_TRIGGER,
            state="unavailable",
            subject=f"{descriptor.recipe_id}:{trigger}",
            missing=f"this recipe declares no {trigger!r} trigger",
            supplied_by="Declare a TriggerBinding on the descriptor first.",
            reason="trigger_not_declared",
        ))
    else:
        trigger_owner = binding.owner
        if not binding.available:
            gaps.append(gap(
                kind=GAP_UNAVAILABLE_PREREQUISITE,
                state="unavailable",
                subject=f"{descriptor.recipe_id}:{trigger}",
                missing=f"{binding.owner} supplies no firing for this recipe yet",
                supplied_by=binding.supplied_by,
                reason="trigger_owner_not_wired",
            ))

    # 3. Inputs ---------------------------------------------------------
    resolved: dict[str, Any] = {}
    for spec in descriptor.inputs:
        if spec.name in supplied and str(supplied[spec.name]).strip() != "":
            resolved[spec.name] = supplied[spec.name]
        elif spec.required:
            gaps.append(gap(
                kind=GAP_MISSING_INPUT,
                state="unavailable",
                subject=spec.name,
                missing=f"required input {spec.name!r} ({spec.description})",
                supplied_by="The caller supplies it with the run request.",
                reason="input_required",
            ))
        else:
            resolved[spec.name] = spec.default

    # 4. Adapters -------------------------------------------------------
    steps: list[dict[str, Any]] = []
    for step in descriptor.steps:
        row = step.to_dict()
        try:
            resolve_step(step)
        except CatalogError as exc:
            # A ref that does not resolve is a catalog bug and re-raises; a
            # service whose optional dependency is absent is a gap.  Only the
            # latter can reach here, because resolve_step raises for the
            # former before the descriptor ever ships (fenced in the tests).
            gaps.append(gap(
                kind=GAP_MISSING_ADAPTER,
                state="unavailable",
                subject=step.qualified_ref,
                missing=str(exc),
                supplied_by=step.composed_by,
                reason="adapter_unresolvable",
            ))
            row["bound"] = False
        else:
            row["bound"] = True
        if not runtime_field_is_real(step):
            gaps.append(gap(
                kind=GAP_MISSING_ADAPTER,
                state="unavailable",
                subject=step.qualified_ref,
                missing=(
                    f"the composition root carries no field "
                    f"{step.runtime_field!r}"
                ),
                supplied_by=(
                    "Add the field to RuntimeServices, or set runtime_field='' "
                    "and compose the service over composition.current().db."
                ),
                reason="runtime_field_unknown",
            ))
            row["bound"] = False
        steps.append(row)

    # 5. Source scope ---------------------------------------------------
    source_scope: list[dict[str, Any]] = []
    for source in descriptor.sources:
        state = coverage.get(source.kind, "" if not source.required else "unavailable")
        if state and state not in COVERAGE_STATES:
            raise CatalogError(
                f"coverage[{source.kind!r}] = {state!r} is not a C4 coverage state"
            )
        row = source.to_dict()
        row["state"] = state or "unavailable"
        source_scope.append(row)
        if source.required and row["state"] != "available":
            gaps.append(gap(
                kind=GAP_UNAVAILABLE_PREREQUISITE,
                state=row["state"],
                subject=source.kind,
                missing=f"a {source.kind} source in the 'available' state ({source.description})",
                supplied_by=source.supplied_by,
                reason="required_source_not_available",
            ))

    return CompiledPlan(
        plan_id=_plan_id(descriptor.recipe_id, descriptor.version, resolved),
        revision=1,
        recipe_id=descriptor.recipe_id,
        recipe_version=descriptor.version,
        trigger=trigger,
        trigger_owner=trigger_owner,
        inputs=resolved,
        source_scope=source_scope,
        route_policy=descriptor.route_policy,
        limits=resolve_limits(descriptor),
        acceptance=list(descriptor.acceptance),
        steps=steps,
        effects=list(descriptor.effects),
        gaps=gaps,
    )


#: Worst-first, so reducing many rows to one state can never read better
#: than the sources behind it.
_WORST_FIRST: tuple[str, ...] = (
    "forbidden", "failed", "unavailable", "stale", "available",
)


def worst_state(states: list[str]) -> str:
    """The worst of *states*, or ``unavailable`` when there are none.

    No rows means the kind was never observed, and an unobserved source is
    not an all-clear (C4).
    """
    for candidate in _WORST_FIRST:
        if candidate in states:
            return candidate
    return "unavailable"


def observed_coverage(
    project_service: Any,
    principal: Any,
    project_id: str,
    *,
    now: Any = None,
) -> dict[str, str]:
    """The REAL coverage state of each C4 source kind for one Project.

    Ruling R17-9: this DELEGATES. Watch, meeting and commitment states come
    from :func:`needs_you_aggregate.room_coverage`, the producer the arrival
    aggregate itself uses, reduced to the worst row per kind. Nothing here
    re-derives a state from a table.

    The first cut of this function did re-derive, from ``connector_watches``
    by hand, and diverged from the producer three ways: an aged watch read
    ``available``, a never-read one read ``stale``, and a watch the Room had
    already marked ``cant_check`` read ``available`` -- a fake all-clear on
    a source the product knows it cannot read. That is the defect this
    docstring exists to prevent a second time.

    ``project`` is the one state ``room_coverage`` does not supply (the
    aggregate builds that row inline, entangled with its last-known memory),
    so it is assembled from the same two seams the aggregate uses and from
    nothing else: the Room read, classified with the producer's own
    :func:`needs_you_aggregate._classify_read_failure` (unreadable is
    ``failed`` or ``forbidden``, missing is ``unavailable``); and
    ``list_projects``, the aggregate's expected-source set, which excludes
    an archived Project. A Room that reads fine for a Project the set no
    longer names is ``unavailable``, not ``available``.
    """
    from .needs_you_aggregate import (
        COVERAGE_KINDS,
        _classify_read_failure,
        room_coverage,
    )

    states: dict[str, str] = {kind: "unavailable" for kind in COVERAGE_KINDS}
    project_id = str(project_id or "")
    if not project_id:
        return states

    try:
        room = project_service.room(principal, project_id)
    except Exception as exc:
        state, _reason = _classify_read_failure(exc)
        states["project"] = state
        return states

    # The expected-source set is the producer's own: the aggregate iterates
    # ``list_projects``, which excludes an archived Project. A Project the
    # set does not name is not an available source, and the Room payload
    # carries no archived flag to read instead -- so ask the same seam
    # rather than reaching for ``is_archived`` by hand.
    try:
        listed = {
            str(row.get("id") or "")
            for row in project_service.list_projects(principal)
        }
    except Exception as exc:
        # Classified, not flattened. ``build_aggregate`` runs the same read
        # and classifies its failure with ``_classify_read_failure``
        # (needs_you_aggregate.py:410), so an authority refusal is
        # ``forbidden`` and a broken read is ``failed`` -- neither is
        # ``unavailable``, which means "nobody looked". Swallowing the
        # distinction here would be the P0 again in a second place:
        # silently disagreeing with the producer about a C4 state.
        state, _reason = _classify_read_failure(exc)
        states["project"] = state
        return states
    if project_id not in listed:
        states["project"] = "unavailable"
        return states

    needs = (room or {}).get("needsYou") or {}
    states["project"] = (
        "available" if str(needs.get("state") or "") == "ok" else "failed"
    )

    rows = room_coverage(
        room, project_id, str(room.get("name") or ""), now=now,
    )
    for kind in COVERAGE_KINDS:
        if kind == "project":
            continue
        matching = [str(row["state"]) for row in rows if row.get("kind") == kind]
        if matching:
            states[kind] = worst_state(matching)
    return states


def call_arguments(plan: CompiledPlan, step_name: str) -> dict[str, Any]:
    """The keyword arguments *step_name* is called with under *plan*.

    Each name in the step's ``binds`` is resolved from the plan's inputs
    first, then its limits.  A name in neither is a catalog bug.
    """
    descriptor = get_descriptor(plan.recipe_id)
    for step in descriptor.steps:
        if step.name != step_name:
            continue
        out: dict[str, Any] = {}
        for bound in step.binds:
            if bound in plan.inputs:
                out[bound] = plan.inputs[bound]
            elif bound in plan.limits:
                out[bound] = plan.limits[bound]
            else:
                raise CatalogError(
                    f"{step.qualified_ref}: binds {bound!r}, which is neither an "
                    f"input nor a limit of {plan.recipe_id}"
                )
        return out
    raise CatalogError(f"{plan.recipe_id} has no step {step_name!r}")


__all__ = [
    "CATALOG",
    "CatalogError",
    "CompiledPlan",
    "ExecutionStep",
    "GAP_KINDS",
    "GAP_MISSING_ADAPTER",
    "GAP_MISSING_INPUT",
    "GAP_STALE_DESCRIPTOR",
    "GAP_UNAVAILABLE_PREREQUISITE",
    "GAP_UNSUPPORTED_TRIGGER",
    "InputField",
    "Limit",
    "RECIPE_DECISION_REVIEW",
    "RECIPE_PREPARATION_BRIEF",
    "RECIPE_WEEKLY_UPDATE",
    "RecipeDescriptor",
    "SCHEDULED_TRIGGER_OWNER",
    "SourceRequirement",
    "TRIGGERS",
    "TRIGGER_MANUAL",
    "TRIGGER_SCHEDULED",
    "TriggerBinding",
    "UnknownRecipe",
    "call_arguments",
    "catalog_payload",
    "compile_recipe",
    "get_descriptor",
    "list_descriptors",
    "observed_coverage",
    "worst_state",
    "resolve_limits",
    "resolve_step",
    "runtime_field_is_real",
    "unreachable_declarations",
]
