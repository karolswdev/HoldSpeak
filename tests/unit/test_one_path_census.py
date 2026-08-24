"""HS-131-10 — the executable one-path census (the HS-104-02 / HS-87 house style).

Phase 131 put every model call behind ``InferenceRunner.invoke``. A shared helper
is not ONE path, though, unless a new door FAILS THE BUILD. This module is that
fence: an ``ast`` walk over production ``holdspeak/**`` that finds every
model-execution-shaped form — SDK client construction, completion/streaming
opens, local model loads, mesh relay, engine/runtime factories, Whisper
preload/transcribe leaves, runtime classify/rewrite, and the engine's public
execution verbs — including the FIRST-CLASS CALLABLE forms
(``asyncio.to_thread(intel.run_prompt, …)``, ``chat_fn = intel._chat_completion_text``,
``factory = OpenAI``) that a call-expression census would miss (Sol Amendment 2).

Every site lands in exactly ONE literal bucket:

* :data:`AUTHORIZED_GATEWAY` — the runner's own scopes (Sol Amendment 1 keeps the
  gateway separate from its consumers).
* :data:`ADAPTER_ALLOWLIST` — ONE ENTRY PER FUNCTION SCOPE (Sol: group labels are
  not reviewable fence entries), each with its one-line justification. The FACTORY
  entries require the runner's
  :class:`~holdspeak.kernel.dispatch_context.DispatchContext`; the EXECUTION-LEAF
  entries run inside an adapter dispatch that already carries it — except when
  reached from a named finding below, which is exactly why the findings block.
* :data:`ADMITTED_SEAM_CALLERS` — product callers that reach a model only THROUGH
  a seam that admits the child itself. Design §4 calls these "migrated callers;
  context must be threaded, never allowlisted", so they stay literal and separate
  from the adapter allowlist. Each entry names its admitting seam.
* :data:`NAMED_FINDINGS` — the blocking families from the Sol ruling (plus the two
  this census newly found), by ``file:line`` and finding id. They are not
  exceptions: while any of them stands, HS-131-10 is BLOCKED. The complete table
  and the owner's draft amendment paragraphs live in
  ``pm/roadmap/holdspeak/phase-131-one-admission-path/assets/hs-131-10/findings-inventory.md``.

Anything else fails with ``UNREGISTERED_MODEL_EXECUTION path:line scope target``.
Every list edit requires a recorded phase decision.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Iterator, NamedTuple

import pytest

REPO = Path(__file__).resolve().parents[2]
PRODUCTION = REPO / "holdspeak"

# --------------------------------------------------------------- the vocabulary
# The COMPLETE physical vocabulary (Sol Amendment 2). Deliberately narrower than
# general effect lint: this protects model execution, not all network code.
VOCABULARY: dict[str, frozenset[str]] = {
    "provider-completion": frozenset({
        "run_prompt", "_chat_completion_text", "_chat_completion_stream",
        "_remote_completion", "create_chat_completion", "create_completion",
    }),
    # The SDK's own wire verb, recognized as a RECEIVER CHAIN rather than as the
    # bare name `create` (which this repo uses for repositories, stores, and
    # services all over). A module that is handed an already-constructed client
    # and calls `client.chat.completions.create(...)` names no constructor, no
    # engine, and no factory — the pre-fix census saw NOTHING there, which is the
    # cheapest possible door: `def summarize(client, text)`.
    "sdk-completion-create": frozenset({
        "chat.completions.create", "completions.create", "responses.create",
        "audio.transcriptions.create",
    }),
    # The kernel's two unforgeable mints. They execute no model themselves, but
    # whoever calls them can BUILD one, so the census pins them to their single
    # legitimate scope exactly as it pins a physical leaf.
    #
    # Round 2 retired ``mint_claim_witness`` — a public function taking an
    # operation id and a warrant-shaped mapping, i.e. two literals any module
    # could type. Issuance is now a one-shot capability handed to `executor.py`
    # at import (``_install_claim_issuer``). The retired names stay in this
    # vocabulary so their REAPPEARANCE is a census failure, not a regression
    # nobody notices.
    "admission-mint": frozenset({
        "_install_claim_issuer", "_issue_claim_witness", "mint_claim_witness",
        "_issue_dispatch_context", "issue_dispatch_context",
    }),
    "local-model-load": frozenset({
        "_ensure_local_model_loaded", "_ensure_runtime_loaded",
        "_ensure_openai_client_loaded",
    }),
    "runtime-capability": frozenset({"classify", "rewrite"}),
    # MeetingIntel's public execution verbs: each one bottoms out in a completion,
    # so a caller naming them is as physical as naming `run_prompt`.
    "engine-capability": frozenset({
        "analyze", "generate_title", "generate_bookmark_label",
        "generate_bookmark_label_with_context",
    }),
    "transcribe-leaf": frozenset({"transcribe", "get_model"}),
    "sdk-construction": frozenset({"OpenAI", "AsyncOpenAI", "Llama"}),
    "engine-factory": frozenset({
        "MeetingIntel", "MeshRelayIntel", "MeshRelayRuntime",
        "OpenAICompatibleRuntime", "LlamaCppRuntime",
        # `build_configured_meeting_intel` no longer EXISTS (HS-131-14 privatized
        # the body to `_configured_engine` and deleted the public export), which is
        # exactly why the name stays here: the fence must fail on it coming BACK.
        "build_configured_meeting_intel", "configured_meeting_intel",
        "_configured_engine",
        "build_meeting_intel_for_profile",
        "build_intel_for_revision", "build_intel_for_target",
        "local_pinned_meeting_intel", "_engine_for_revision",
        "_local_pinned_engine", "_profile_engine", "rebind", "bound_target",
        "build_pipeline",
    }),
}
DANGEROUS: frozenset[str] = frozenset().union(*VOCABULARY.values())
FAMILY_OF: dict[str, str] = {
    name: family for family, names in VOCABULARY.items() for name in names
}


class Site(NamedTuple):
    path: str
    line: int
    scope: str
    target: str
    kind: str  # "call", or "ref" for a bound method / class passed as a VALUE

    @property
    def family(self) -> str:
        return FAMILY_OF[self.target]

    @property
    def where(self) -> tuple[str, str]:
        return (self.path, self.scope)

    @property
    def line_key(self) -> str:
        return f"{self.path}:{self.line} {self.target}"

    def named(self) -> str:
        return f"UNREGISTERED_MODEL_EXECUTION {self.path}:{self.line} {self.scope} {self.target}"


# ------------------------------------------------------------- the AST classifier


def _scope_index(tree: ast.AST) -> dict[int, str]:
    """The innermost enclosing def/class chain for every node, dotted."""
    index: dict[int, str] = {}

    def walk(node: ast.AST, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                for sub in ast.walk(child):
                    index[id(sub)] = name
                walk(child, name + ".")
            else:
                walk(child, prefix)

    walk(tree, "")
    return index


def _non_sites(tree: ast.AST) -> set[int]:
    """Forms that are NOT executable model work (design §1, Sol recorded note 3).

    Availability probes (``_intel_pkg.OpenAI is None``), ``isinstance``/``getattr``
    guards, annotations, and assignment TARGETS reach no provider, so admitting
    them would fill the ledger with false doors and hide the real ones.
    """
    excluded: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and any(
            isinstance(op, (ast.Is, ast.IsNot)) for op in node.ops
        ):
            for sub in ast.walk(node):
                excluded.add(id(sub))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {
            "isinstance", "issubclass", "hasattr", "getattr", "setattr"
        }:
            for argument in node.args[1:]:
                for sub in ast.walk(argument):
                    excluded.add(id(sub))
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                for sub in ast.walk(target):
                    excluded.add(id(sub))
        elif isinstance(node, ast.arg) and node.annotation is not None:
            for sub in ast.walk(node.annotation):
                excluded.add(id(sub))

    # A getter ASKED ABOUT rather than held (design §1: "availability probes are
    # not sites"). `_non_sites` already exempted the `is`/`is not` spelling; the
    # 2d getter rule made two more spellings visible in production, and both are
    # the same species — they answer "does this exist?" and never obtain a door:
    #
    #     not callable(getattr(engine, "run_prompt", None))          # a type test
    #     getattr(getattr(inner, "classify", None), "marker", False)  # a marker read
    #
    # Deliberately narrow: the getter must be the DIRECT argument of a predicate,
    # or the RECEIVER another probe reads through. A getter that is bound, called,
    # returned, or passed anywhere else is still a door, whatever holds it.
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        if node.func.id in {"callable", "isinstance", "issubclass", "hasattr", "bool"}:
            probed = node.args[:1]
        elif node.func.id in {"getattr", "setattr"}:
            probed = node.args[:1]  # the RECEIVER, which args[1:] above never covers
        else:
            continue
        for argument in probed:
            if isinstance(argument, ast.Call) and isinstance(argument.func, ast.Name) and (
                argument.func.id == "getattr"
            ):
                excluded.add(id(argument))
    return excluded


def _alias_map(tree: ast.AST) -> dict[str, str]:
    """Local name -> the name it was imported UNDER (Sol Amendment 2: aliases).

    ``from openai import OpenAI as _OAI`` then ``_OAI(...)`` is the same door as
    ``OpenAI(...)``; a census keyed on the written token would miss it. This repo
    already aliases on import in production (e.g.
    ``from ..intel.providers import run_egress as _run_egress``), so the evasion
    is not hypothetical — it is the house style.
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for entry in node.names:
                if entry.asname:
                    aliases[entry.asname] = entry.name.split(".")[-1]
    return aliases


#: The SDK receiver chains that ARE a model execution, whatever the receiver is
#: called. Matching the chain (not the bare verb) is what keeps
#: ``self._repo.create(...)``, ``_svc().create(...)`` and ``store.create(name)``
#: — all real, all over this repo — out of the ledger while still catching a
#: module that was simply HANDED a client.
SDK_CHAINS: tuple[tuple[str, ...], ...] = (
    ("chat", "completions", "create"),
    ("completions", "create"),
    ("responses", "create"),
    ("audio", "transcriptions", "create"),
)


def _sdk_chain(node: ast.Attribute) -> str | None:
    """The SDK receiver chain this attribute ends, if it ends one."""
    parts: list[str] = []
    cursor: ast.AST = node
    while isinstance(cursor, ast.Attribute) and len(parts) < 5:
        parts.append(cursor.attr)
        cursor = cursor.value
    parts.reverse()
    for chain in SDK_CHAINS:
        if len(parts) >= len(chain) and tuple(parts[-len(chain):]) == chain:
            return ".".join(chain)
    return None


def _tail(node: ast.AST, aliases: dict[str, str]) -> str | None:
    """The dotted call's / reference's final name, with import aliases resolved.

    An ``Attribute`` already carries the real member name — a MODULE alias
    (``import x.y as z``; ``z.run_prompt()``) cannot rename the attribute — so
    only bare ``Name`` loads need the alias map. An SDK receiver chain reports
    the CHAIN (``chat.completions.create``), because the bare verb is ambiguous
    and the receiver's local name is not the fact worth recording.
    """
    if isinstance(node, ast.Attribute):
        return _sdk_chain(node) or node.attr
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    return None


def _literal_getattr_target(
    receiver: ast.AST, name: str, aliases: dict[str, str]
) -> str | None:
    """What ``getattr(receiver, "name")`` resolves to, if it is a model verb.

    HS-131-10 round 2c (Terra MANDATORY 1). ``_non_sites`` deliberately excludes
    the ARGUMENTS of ``getattr`` — written to keep availability guards quiet, it
    also made the census blind to the one form that spells a model verb as a
    STRING::

        call = getattr(intel, "run_prompt")          # census saw nothing
        create = getattr(client.chat.completions, "create")

    Both are Sol Amendment 2 callable references wearing a different hat, and the
    fence has to fail closed on them. Resolution is deliberately narrow, in both
    directions:

    * a literal that is itself a known verb (``run_prompt``, ``transcribe``, …)
      is a site whatever the receiver is — the verb alone is the fact;
    * otherwise the literal only counts when ``receiver.<name>`` completes a
      full SDK receiver chain, so ``getattr(client.chat.completions, "create")``
      is a site and ``getattr(repo, "create")`` is not;
    * anything else — ``getattr(widget, "on_click")``, a non-literal name, a
      computed attribute — resolves to ``None`` and stays out of the ledger.
    """
    if name in DANGEROUS:
        return name
    parts: list[str] = []
    cursor: ast.AST = receiver
    while isinstance(cursor, ast.Attribute) and len(parts) < 5:
        parts.append(cursor.attr)
        cursor = cursor.value
    parts.reverse()
    parts.append(name)
    for chain in SDK_CHAINS:
        if len(parts) >= len(chain) and tuple(parts[-len(chain):]) == chain:
            return ".".join(chain)
    return None


def _literal_getattr(node: ast.AST, aliases: dict[str, str]) -> str | None:
    """The model verb a ``getattr(x, "literal")`` CALL resolves to, if any."""
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
    ):
        return None
    literal = node.args[1]
    if not (isinstance(literal, ast.Constant) and isinstance(literal.value, str)):
        return None
    return _literal_getattr_target(node.args[0], literal.value, aliases)


def sites_in_source(relative: str, source: str) -> Iterator[Site]:
    """Classify one module's source (a real file, or a synthetic mutation)."""
    tree = ast.parse(source)
    scopes = _scope_index(tree)
    excluded = _non_sites(tree)
    aliases = _alias_map(tree)
    called = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}

    for node in ast.walk(tree):
        if id(node) in excluded:
            continue
        if isinstance(node, ast.Call):
            scope = scopes.get(id(node), "<module>")
            # THE GETTER IS THE DOOR (HS-131-10 round 2d). Classified where it is
            # WRITTEN, exactly like the bound-method reference it is
            # (`chat_fn = intel._chat_completion_text`), and deliberately without
            # looking at what receives it.
            #
            # Round 2c tracked `name = getattr(...)` bindings through later calls,
            # which meant the ledger depended on the CONTAINER: `self._call = ...`,
            # `HOLDERS["x"] = ...`, `(a := ...)`, a tuple unpack, or handing the
            # getter straight to `asyncio.to_thread` all laundered the door
            # straight back open, and closing them one target shape at a time is a
            # game the author of the next shape always wins. The getter expression
            # is the one thing every container has in common, so that is what the
            # census records — one site per door, whatever holds it.
            getter = _literal_getattr(node, aliases)
            if getter is not None:
                # `getattr(intel, "run_prompt")(...)` fires where it is written;
                # anything else is a reference someone is holding for later.
                kind = "call" if id(node) in called else "ref"
                yield Site(relative, node.lineno, scope, getter, kind)
                continue
            target = _tail(node.func, aliases)
            if target in DANGEROUS:
                yield Site(relative, node.lineno, scope, target, "call")
        elif isinstance(node, (ast.Attribute, ast.Name)) and isinstance(
            getattr(node, "ctx", None), ast.Load
        ):
            if id(node) in called:
                continue
            target = _tail(node, aliases)
            if target in DANGEROUS:
                yield Site(relative, node.lineno, scopes.get(id(node), "<module>"), target, "ref")


def census() -> list[Site]:
    """Every model-execution site in production ``holdspeak/`` (tests excluded)."""
    sites: list[Site] = []
    for path in sorted(PRODUCTION.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        sites.extend(
            sites_in_source(path.relative_to(REPO).as_posix(), path.read_text(encoding="utf-8"))
        )
    return sorted(sites)


# ------------------------------------------------------------ bucket 1: gateway
RUNNER = "holdspeak/kernel/inference_runner.py"
EXECUTOR = "holdspeak/kernel/executor.py"
#: The ONE authorized gateway. `_attempt` owns child admission/claim, the dispatch
#: context mint, and the engine-factory entrance; `_dispatch` owns adapter dispatch
#: and its causally linked egress (it names no vocabulary target of its own — it
#: calls `adapter.dispatch`, which is why it is declared, not inferred).
#:
#: The public `invoke` is the retry ORCHESTRATOR (one physical attempt, one child,
#: one receipt — Sol Amendment 3): it names no vocabulary target at all, which is
#: precisely why the gateway stays exactly two scopes and both of them are the
#: places where a physical thing is actually admitted or dispatched.
AUTHORIZED_GATEWAY: dict[tuple[str, str], str] = {
    (RUNNER, "InferenceRunner._attempt"): "the one admission + claim + context mint + engine-factory entrance",
    (RUNNER, "InferenceRunner._dispatch"): "the one adapter-dispatch and causally linked egress entrance",
}

#: The ONE claim-witness mint (HS-131-10 Terra finding A). Not the gateway and not
#: an adapter: it executes no model, but whoever can call it can mint the dispatch
#: context that BUILDS one, so it is pinned to the single scope where the kernel
#: has just verified a warrant's signature, revocation, expiry, payload binding,
#: and ancestor chain. A second caller — direct or aliased — fails the census.
CLAIM_WITNESS_MINT: dict[tuple[str, str], str] = {
    (EXECUTOR, "<module>"): "TAKES the process's one-shot witness issuer at import; `_install_claim_issuer` refuses every later caller",
    (EXECUTOR, "ExecutorPlane.claim"): "issues the single-use witness on a VERIFIED claim; the only source of a dispatch context",
}

#: NOT the gateway, and deliberately not an adapter either: the runner's own
#: constructor names `build_intel_for_revision` as a DEFAULT ARGUMENT VALUE. It
#: is a first-class reference (so the census sees it, by design) but it executes
#: nothing — binding a default cannot dispatch. Sol Amendment 1 requires the
#: gateway list to stay exactly two entries, so this gets its own one-line
#: bucket rather than diluting either list.
GATEWAY_FACTORY_BINDING: dict[tuple[str, str], str] = {
    (RUNNER, "InferenceRunner.__init__"): "binds `build_intel_for_revision` as the DEFAULT factory; executes nothing",
}

# ------------------------------------------------------ bucket 2: the allowlist
# ONE FUNCTION SCOPE PER ENTRY. `F:` = a context-requiring factory (runtime proof
# in test_one_path_context.py). `L:` = an execution leaf reached from a dispatch.
ADAPTER_ALLOWLIST: dict[tuple[str, str], str] = {
    ("holdspeak/inference_targets.py", "build_intel_for_revision"): "F: the runner's factory; validates the context against this exact revision, binds it through every branch",
    ("holdspeak/inference_targets.py", "_engine_for_revision"): "F: the per-branch construction body, reached only from the validating wrapper",
    ("holdspeak/inference_targets.py", "local_pinned_meeting_intel"): "F: same-device pinned engine; context-requiring",
    ("holdspeak/inference_targets.py", "_local_pinned_engine"): "F: the pinned construction body, reached only from the validating wrapper",
    ("holdspeak/intel/providers.py", "build_meeting_intel_for_profile"): "F: profile-shaped engine; context-requiring, matched to the deployment revision",
    ("holdspeak/intel/providers.py", "_profile_engine"): "F: the profile construction body, reached only from the validating wrapper",
    ("holdspeak/intel/providers.py", "configured_meeting_intel"): "F: the gate in front of the host-adapter seam; validates the context (or the ONE named legacy marker) BEFORE any provider object exists",
    ("holdspeak/intel/providers.py", "_configured_engine"): "F: the configured-placement construction body, reached only from the validating wrapper (HS-131-14 privatized it; it was the uncontextual `build_configured_meeting_intel`)",
    ("holdspeak/speech_session/revision_target.py", "rebind"): "F: rebuilds a dictation backend onto the frozen revision; context-requiring",
    ("holdspeak/speech_session/revision_target.py", "bound_target"): "F: agrees-or-rebind decision; forwards the child's context to rebind",
    ("holdspeak/speech_session/provider.py", "ProviderAdmission.target"): "F: reads the context off the runner-built engine and binds the dispatch target",
    ("holdspeak/speech_session/provider.py", "ProviderAdmission.dispatch_through"): "L: dispatches the target only after the provider child's admission",
    ("holdspeak/speech_session/provider.py", "_RoutedSpeechAdapter.dispatch"): "L: executes the runner-built engine for the controller-owned provider route",
    ("holdspeak/speech_session/provider.py", "_mesh_bound"): "F: binds the mesh backend to the runner's admitted envelope; constructs no relay of its own",
    ("holdspeak/plugins/dictation/assembly.py", "_try_build_runtime"): "F: dictation runtime assembly; the pipeline it yields is wrapped by the admitted seam",
    ("holdspeak/plugins/dictation/runtime.py", "_default_factories._llama_factory"): "F: the llama.cpp runtime factory seam",
    ("holdspeak/plugins/dictation/runtime.py", "_default_factories._openai_factory"): "F: the OpenAI-compatible runtime factory seam",
    ("holdspeak/plugins/dictation/runtime_mesh_relay.py", "MeshRelayRuntime.load"): "F: mesh backend construction inside the dictation adapter",
    ("holdspeak/plugins/dictation/runtime_openai_compatible.py", "OpenAICompatibleRuntime.load"): "F: SDK client construction inside the dictation adapter",
    ("holdspeak/plugins/dictation/runtime_openai_compatible.py", "OpenAICompatibleRuntime.classify"): "L: the dictation classify leg's ONE `chat.completions.create` (its compatibility twin is a SECOND admitted child, HS-131-09)",
    ("holdspeak/plugins/dictation/runtime_openai_compatible.py", "OpenAICompatibleRuntime.rewrite"): "L: the dictation rewrite leg's ONE `chat.completions.create`",
    ("holdspeak/plugins/dictation/runtime_llama_cpp.py", "LlamaCppRuntime._resolve_factories"): "F: local model class resolution inside the dictation adapter",
    ("holdspeak/intel/engine.py", "MeetingIntel._ensure_openai_client_loaded"): "L: the ONE cloud SDK client construction",
    ("holdspeak/intel/engine.py", "MeetingIntel._ensure_local_model_loaded"): "L: the ONE local llama.cpp load",
    ("holdspeak/intel/engine.py", "MeetingIntel._ensure_runtime_loaded"): "L: picks the local/cloud load for the resolved provider",
    ("holdspeak/intel/engine.py", "MeetingIntel._ensure_model_loaded"): "L: the legacy alias of the load entrance",
    ("holdspeak/intel/engine.py", "MeetingIntel._chat_completion_text"): "L: the ONE non-streaming completion open",
    ("holdspeak/intel/engine.py", "MeetingIntel._chat_completion_stream"): "L: the ONE streaming completion open",
    ("holdspeak/intel/engine.py", "MeetingIntel.run_prompt"): "L: the canonical prompt leaf an adapter dispatches",
    ("holdspeak/intel/engine.py", "MeetingIntel._analyze_once"): "L: the analysis leaf an admitted meeting child dispatches",
    ("holdspeak/intel/engine.py", "MeetingIntel._analyze_stream"): "L: the streaming analysis leaf an admitted meeting child dispatches",
    ("holdspeak/intel/engine.py", "MeetingIntel.generate_title"): "L: the auto-title leaf an admitted child dispatches",
    ("holdspeak/intel/engine.py", "MeetingIntel.generate_bookmark_label_with_context"): "L: the ONE bookmark-label leaf; both the live and the deferred admitted children dispatch it",
    ("holdspeak/intel/mesh_relay.py", "MeshRelayIntel._chat_completion_text"): "L: the mesh envelope leaf; carries the frozen revision + warrant",
    ("holdspeak/kernel/prompt_adapter.py", "CanonicalPromptAdapter.dispatch"): "L: the canonical adapter the runner hands an engine to",
    ("holdspeak/plugins/dictation/runtime_llama_cpp.py", "LlamaCppRuntime.classify"): "L: local constrained-decoding classify leaf",
    ("holdspeak/plugins/dictation/runtime_llama_cpp.py", "LlamaCppRuntime.rewrite"): "L: local rewrite leaf",
    ("holdspeak/plugins/dictation/runtime_mesh_relay.py", "MeshRelayRuntime._run"): "L: mesh relay leaf for the dictation legs",
    ("holdspeak/plugins/dictation/runtime_counters.py", "CountingRuntime.classify"): "L: the counting decorator around one classify leaf",
    ("holdspeak/plugins/dictation/runtime_counters.py", "CountingRuntime.rewrite"): "L: the counting decorator around one rewrite leaf",
    ("holdspeak/speech_session/provider.py", "AdmittedDictationRuntime.classify"): "L: the admitted seam's classify entrance (admits before it dispatches)",
    ("holdspeak/speech_session/provider.py", "AdmittedDictationRuntime.rewrite"): "L: the admitted seam's rewrite entrance (admits before it dispatches)",
    ("holdspeak/speech_session/provider.py", "_ClassifyLeg.run.call"): "L: the dispatch closure of ONE admitted classify attempt",
    ("holdspeak/speech_session/provider.py", "ProviderAdmission.rewrite.call"): "L: the dispatch closure of ONE admitted rewrite child",
    ("holdspeak/speech_session/provider.py", "ProviderAdmission.punctuate.call"): "L: the dispatch closure of ONE admitted punctuate child",
    ("holdspeak/meeting_session/intel_routed_children.py", "IntelRoutedChildMixin._admitted_live_window.call"): "L: the dispatch closure of ONE admitted live-analysis child",
    ("holdspeak/meeting_session/intel_routed_children.py", "IntelRoutedChildMixin._admitted_bookmark_label.call"): "L: the dispatch closure of ONE admitted bookmark-label child",
    ("holdspeak/meeting_session/intel_routed_children.py", "IntelRoutedChildMixin._admitted_auto_title.call"): "L: the dispatch closure of ONE admitted auto-title child",
    ("holdspeak/meeting_session/deferred_admission.py", "DeferredIntelJob.analyze.call"): "L: the dispatch closure of ONE admitted deferred-analysis child",
    ("holdspeak/meeting_session/deferred_admission.py", "DeferredIntelJob.bookmark_label.call"): "L: the dispatch closure of ONE admitted deferred bookmark-label child",
    ("holdspeak/meeting_session/deferred_admission.py", "DeferredIntelJob.auto_title.call"): "L: the dispatch closure of ONE admitted deferred auto-title child",
    ("holdspeak/meeting_session/deferred_bound.py", "bound_analysis_dispatch.call"): "L: C1 stored-route dispatch closure for ONE bound deferred-analysis child (HS-143-08/C1)",
    ("holdspeak/meeting_session/deferred_bound.py", "bound_bookmark_label_dispatch.call"): "L: C1 stored-route dispatch closure for ONE frozen bookmark-label child (HS-143-08/C1)",
    ("holdspeak/meeting_session/deferred_bound.py", "bound_auto_title_dispatch.call"): "L: C1 stored-route dispatch closure for ONE bound auto-title child (HS-143-08/C1)",
    ("holdspeak/transcribe.py", "Transcriber._timed_transcribe"): "L: the ONE transcription entrance every caller goes through",
    ("holdspeak/transcribe.py", "Transcriber._timed_transcribe._run"): "L: the timed backend call inside that entrance",
    ("holdspeak/transcribe.py", "_MlxTranscriber.transcribe._run"): "L: the MLX Whisper execution leaf",
    ("holdspeak/transcribe.py", "_MlxTranscriber._model_holder_get._run"): "L: the MLX Whisper PRELOAD leaf (its own admitted child)",
    ("holdspeak/transcribe.py", "_MlxTranscriber._silent_audio_load._run"): "L: the MLX Whisper warmup leaf (its own admitted child)",
    ("holdspeak/transcribe.py", "_FasterWhisperTranscriber.transcribe"): "L: the faster-whisper execution leaf",
}

# -------------------------------------------- bucket 3: admitted-seam callers
# Product callers that reach a model ONLY through a seam that admits the child
# itself (design §4 "migrated callers"). value = the admitting seam.
ADMITTED_SEAM_CALLERS: dict[tuple[str, str], str] = {
    ("holdspeak/main.py", "_run_meeting_mode"): "Transcriber.transcribe (admitted per HS-131-09)",
    ("holdspeak/meeting_import.py", "_transcribe_import_windows"): "Transcriber.transcribe",
    ("holdspeak/meeting_session/transcribe_loop.py", "TranscribeLoopMixin._transcribe_audio"): "Transcriber.transcribe",
    ("holdspeak/runtime/dictation_capture.py", "DictationCaptureMixin._transcribe_and_type"): "Transcriber.transcribe",
    ("holdspeak/runtime/dictation_capture.py", "DictationCaptureMixin.transcribe_audio_admitted"): "Transcriber.transcribe under the session's admitted transcription child",
    ("holdspeak/runtime/wake_glue.py", "WakeWordGlueMixin._transcribe_wake_admitted"): "Transcriber.transcribe under the wake session's admitted child",
    ("holdspeak/web/routes/system/voice.py", "build_voice_router.api_transcribe"): "the route refuses without the admitted seam, then calls Transcriber.transcribe",
    # HS-132-12 MOVED this seam, it did not change it: the streaming socket is
    # now its own concern module (`voice_stream.py`), composed by
    # `build_voice_router`. Same body, same admitting seam, new documented home.
    ("holdspeak/web/routes/system/voice_stream.py", "build_voice_stream_router.ws_dictation_stream"): "the stream refuses without the admitted seam, then calls Transcriber.transcribe",
    ("holdspeak/plugins/dictation/builtin/intent_router.py", "IntentRouter.run"): "AdmittedDictationRuntime.classify",
    ("holdspeak/plugins/dictation/builtin/project_rewriter.py", "ProjectRewriter.run"): "AdmittedDictationRuntime.rewrite",
    ("holdspeak/project_doc_suggestions.py", "suggest_project_doc_update"): "AdmittedDictationRuntime.rewrite",
    ("holdspeak/target_profile.py", "apply_model_assisted_target"): "AdmittedDictationRuntime.rewrite",
    ("holdspeak/dictation_runner.py", "run_dictation_pipeline"): "build_pipeline(admission=…) wraps the runtime in the admitted seam",
    ("holdspeak/dictation_runner.py", "run_pipeline_corrections_only"): "build_pipeline(admission=…) wraps the runtime in the admitted seam",
    ("holdspeak/web/routes/dictation/_helpers.py", "_run_dictation_dry_run_text"): "requires a caller-owned live text-entry admission before construction",
    ("holdspeak/commands/dictation.py", "_cmd_dry_run"): "requires the top-level CLI's derived owner and live text-entry admission before construction",
    ("holdspeak/intel_queue.py", "process_next_intel_job"): "DeferredIntelJob.analyze (an admitted deferred child)",
    # HS-131-14. The plugin dispatch handle is a CONSUMER of an admitted child, not
    # an adapter: it constructs nothing, resolves no placement, and holds no
    # configuration. It is handed the engine `InferenceRunner._attempt` already
    # built for the claimed child, and it re-proves that child's context — by
    # identity — plus its own liveness and cancellation signal before every
    # completion. Charter §Scope forbids a plugin scope on the ADAPTER_ALLOWLIST,
    # and this is the seam list, which is where a migrated caller belongs.
    ("holdspeak/plugins/intelligence.py", "PluginDispatch.chat"): "the runner-built engine of ONE admitted `inference.invoke` child; refuses by name before the leaf when the handle is released, cancelled, or no longer that child's",
}

# ------------------------------------------------------- bucket 4: the findings
# Sol Amendment 4's package, plus the TWO families this census newly found
# (`legacy-live-meeting-engine`, `bookmark-auto-label`). key = "path:line target".
NAMED_FINDINGS: dict[str, str] = {
    # HS-131-13 retired four rows of this ledger by DELETION and MIGRATION, never
    # by promotion: `cadence` (now an admitted `cadence.next-action-draft` parent
    # with one `inference.invoke` child), `decisions-route` (the duplicate route
    # seam is gone; the admitted Decision promotion service is the only path),
    # `delivery-legacy-factory` (the dormant helper is deleted), and the five
    # `legacy-uncontextual-factory` sites that sat inside `build_intel_for_target`
    # (the factory itself is deleted). Nothing moved to an allowlist.
    # HS-131-16 CLOSED `mesh-receiver` (2 sites) by ADMISSION, not by deletion of
    # the feature and not by an allowlist entry. `MeshServeWorker` used to accept
    # a hand-built envelope, construct an engine with `LEGACY_UNCONTEXTUAL`, and
    # call `run_prompt` directly. It now verifies a hub-signed Ed25519 dispatch
    # offer against a pinned public key, wins an atomic worker-local replay
    # reservation, lets its own kernel derive the principal from that offer, and
    # sends every physical attempt through the worker-local `InferenceRunner` —
    # which mints a real `DispatchContext` and ends each attempt in an immutable
    # receipt. No command scope entered `ADAPTER_ALLOWLIST`; the worker names no
    # factory and no completion verb at all.
    # HS-131-14 CLOSED two families here, both by deletion rather than promotion.
    #
    # `plugin-default-provider` (30 sites): every builtin's `_cached_provider`
    # fallback and the segment probe's default construction are GONE. A plugin now
    # consumes intelligence through the host-issued dispatch handle its invocation
    # carries, and an `llm` plugin with no handle refuses by name. No plugin scope
    # entered any list.
    #
    # `legacy-uncontextual-factory` (2 sites): `build_configured_meeting_intel()`
    # took NO context and validated nothing — its signature was literally `()` —
    # and it was PUBLIC and exported, which is how fifteen callers each built their
    # own engine. Its last caller migrated, so the body was privatized to
    # `_configured_engine`, dominated by the validating `configured_meeting_intel`
    # (asserted below), and the public name deleted. The name stays in the
    # vocabulary with zero permitted sites, so typing it again fails the fence.
    #
    # HS-131-17 CLOSED the last two families, and the ledger is now EMPTY.
    #
    # `legacy-live-meeting-engine` (session.py `MeetingIntel(**kwargs)`): deleted.
    # `MeetingSession.start()` no longer preflights a provider or constructs an
    # engine beside its frozen plan. It reads the plan's own placement readiness,
    # sets the explicit `_intel_live` state, and lets the FIRST actual child build
    # the exact frozen revision inside `InferenceRunner`.
    #
    # `bookmark-auto-label` (bookmarks.py `generate_bookmark_label`): admitted.
    # Automatic refinement goes through `_admitted_bookmark_label` — one trusted
    # `inference.invoke@1` child, one terminal receipt — and the context-only
    # engine leaf it used to call is deleted. Both names stay in the vocabulary
    # with zero permitted sites, so retyping either fails this fence (proved by
    # the two mutations at the end of this module).
}

#: EMPTY since HS-131-17. `dormant-mir` was the one family with no executable
#: site: a private `mir_routing_enabled=True` branch that would have routed
#: through an unadmitted path if it were ever switched on. Production never
#: switched it on — `WebRuntime._start_meeting` supplied no enable flag, plugin
#: host, database, or tuning — so the story removed the branch itself, along with
#: its constructor inputs, its plugin enumeration, and its post-close
#: `process_meeting_state()` dispatch. Routed meeting intelligence remains a
#: product path in the separately admitted deferred job.
FINDINGS_WITHOUT_A_SITE: dict[str, str] = {}

#: The complete blocking ledger — EMPTY as of HS-131-17. Every family left by
#: deletion or admission; none was ever promoted onto a list.
BLOCKING_FAMILIES: frozenset[str] = frozenset(NAMED_FINDINGS.values()) | frozenset(
    FINDINGS_WITHOUT_A_SITE.values()
)

#: The named legacy marker may appear ONLY in its own module and in the ONE named
#: legacy finding scope left. This is what keeps `LEGACY_UNCONTEXTUAL` from becoming
#: a general escape hatch: the family can only ever shrink, and HS-131-13 shrank it
#: by deleting `build_intel_for_target` rather than by exempting it.
#: EMPTY since HS-131-16. The mesh receiver was the last scope that passed the
#: marker, and it no longer builds an engine at all: it verifies a hub-signed
#: dispatch offer, reserves it, and hands the work to a worker-local
#: `InferenceRunner`, which issues a REAL context for every physical attempt. The
#: name deliberately stays in the vocabulary with zero permitted scopes, so
#: typing it again fails this fence instead of quietly reopening the family.
LEGACY_MARKER_SCOPES: frozenset[tuple[str, str]] = frozenset()

#: `F:` scopes that are NOT module-level public entry points: adapter methods and
#: private construction bodies. Each is reached only from an allowlisted factory
#: that has already validated the context (structurally asserted below; the
#: runtime half is `test_one_path_context.py`). Listed literally, and compared by
#: EXACT equality, so a new public factory cannot arrive unreviewed by looking
#: like adapter internals.
ADAPTER_INTERNAL_FACTORY_SCOPES: frozenset[tuple[str, str]] = frozenset({
    ("holdspeak/inference_targets.py", "_engine_for_revision"),
    ("holdspeak/inference_targets.py", "_local_pinned_engine"),
    ("holdspeak/intel/providers.py", "_profile_engine"),
    ("holdspeak/intel/providers.py", "_configured_engine"),
    ("holdspeak/speech_session/provider.py", "ProviderAdmission.target"),
    ("holdspeak/speech_session/provider.py", "_mesh_bound"),
    ("holdspeak/plugins/dictation/assembly.py", "_try_build_runtime"),
    ("holdspeak/plugins/dictation/runtime.py", "_default_factories._llama_factory"),
    ("holdspeak/plugins/dictation/runtime.py", "_default_factories._openai_factory"),
    ("holdspeak/plugins/dictation/runtime_mesh_relay.py", "MeshRelayRuntime.load"),
    ("holdspeak/plugins/dictation/runtime_openai_compatible.py", "OpenAICompatibleRuntime.load"),
    ("holdspeak/plugins/dictation/runtime_llama_cpp.py", "LlamaCppRuntime._resolve_factories"),
})

#: Public `F:` scopes that CONSTRUCT NOTHING themselves: they decide, then hand
#: every construction to the named validating factory. Structurally checked below
#: (their bodies may name no other physical target), so "it delegates" is a
#: verified property rather than a claim in a comment.
DELEGATING_FACTORY_SCOPES: dict[tuple[str, str], str] = {
    ("holdspeak/speech_session/revision_target.py", "bound_target"): "rebind",
}

#: The private construction bodies whose ONLY callers must be validating wrappers,
#: and the wrapper each one is dominated by. A private body that a second scope
#: learns to call has escaped its gate even though nothing about it changed.
DOMINATED_CONSTRUCTION_BODIES: dict[tuple[str, str], str] = {
    ("holdspeak/inference_targets.py", "_engine_for_revision"): "build_intel_for_revision",
    ("holdspeak/inference_targets.py", "_local_pinned_engine"): "local_pinned_meeting_intel",
    ("holdspeak/intel/providers.py", "_profile_engine"): "build_meeting_intel_for_profile",
    ("holdspeak/intel/providers.py", "_configured_engine"): "configured_meeting_intel",
}

#: The factory scopes whose bodies must NAME the validator (Sol Amendment 1).
CONTEXT_REQUIRING_FACTORIES: tuple[tuple[str, str], ...] = (
    ("holdspeak/inference_targets.py", "build_intel_for_revision"),
    ("holdspeak/inference_targets.py", "local_pinned_meeting_intel"),
    ("holdspeak/intel/providers.py", "build_meeting_intel_for_profile"),
    ("holdspeak/intel/providers.py", "configured_meeting_intel"),
    ("holdspeak/speech_session/revision_target.py", "rebind"),
)


def _bucket(site: Site) -> str | None:
    if site.where in AUTHORIZED_GATEWAY:
        return "gateway"
    if site.where in CLAIM_WITNESS_MINT:
        return "witness-mint"
    if site.where in GATEWAY_FACTORY_BINDING:
        return "gateway-binding"
    if site.line_key in NAMED_FINDINGS:
        return "finding"
    if site.where in ADAPTER_ALLOWLIST:
        return "allowlist"
    if site.where in ADMITTED_SEAM_CALLERS:
        return "seam"
    return None


# ----------------------------------------------------------------- the censuses


def test_every_model_execution_site_is_in_exactly_one_bucket() -> None:
    """THE fence. A new door — or a moved finding — fails here, by name."""
    sites = census()
    unregistered = [site.named() for site in sites if _bucket(site) is None]
    assert unregistered == [], (
        "unregistered model execution:\n  " + "\n  ".join(unregistered)
        + "\n\nAdmit it as an adapter (with its context requirement), record it as a "
        "NAMED FINDING with an owner story, or remove it. A fence exception is not "
        "an option (HS-131-10 charter, Scope/Out)."
    )
    counts = {
        name: 0
        for name in (
            "gateway", "witness-mint", "gateway-binding", "allowlist", "seam", "finding",
        )
    }
    for site in sites:
        counts[str(_bucket(site))] += 1
    assert sum(counts.values()) == len(sites)
    # Measured after HS-131-17 removed the last three sites, all by DELETION:
    # the live session's `MeetingIntel(**kwargs)` construction, its direct
    # `generate_bookmark_label` call, and the context-only engine leaf that call
    # reached (whose body held the `_chat_completion_text` open). The admitted
    # bookmark path adds NO site: `_admitted_bookmark_label` already existed and
    # its dispatch closure is already allowlisted.
    # HS-132-05 took one more site out, again by DELETION: the streaming
    # dictation socket's PER-CHUNK `transcribe(...)` (a full Whisper pass every
    # 600 ms, on the hotkey's own lock, producing a "partial" no client
    # consumed). The socket's final, whole-utterance pass remains, so the
    # `ws_dictation_stream` seam registration above still names a live site.
    # Phase 143 adds six audited routed provider/transcription entrances to the
    # historic 99-site census; every one is classified above rather than hidden.
    assert len(sites) == 105
    # THE headline: the blocking ledger is empty. Every model execution in
    # production is now the gateway, a reviewed adapter, or an admitted seam.
    assert counts["finding"] == 0
    assert BLOCKING_FAMILIES == frozenset()
    print(
        "one-path census:", len(sites), "sites",
        {**counts, "unregistered": 0},
        f"gateway_scopes={len(AUTHORIZED_GATEWAY)}",
        f"allowlist_scopes={len(ADAPTER_ALLOWLIST)}",
        f"seam_scopes={len(ADMITTED_SEAM_CALLERS)}",
        f"finding_families={len(BLOCKING_FAMILIES)}",
    )


def test_the_gateway_is_exactly_two_scopes_and_is_not_an_adapter() -> None:
    """Sol Amendment 1: separate the gateway from its consumers.

    The gateway is the pair of runner scopes that ADMIT and DISPATCH. Everything
    that physically constructs or executes is a consumer of it, on the reviewed
    adapter list. Collapsing the two lists is exactly how an adapter would come
    to be treated as an admission path.
    """
    assert set(AUTHORIZED_GATEWAY) == {
        (RUNNER, "InferenceRunner._attempt"),
        (RUNNER, "InferenceRunner._dispatch"),
    }
    # The public entrance is a pure orchestrator: it admits nothing, dispatches
    # nothing, and constructs nothing, so it holds no site at all.
    assert (RUNNER, "InferenceRunner.invoke") not in {site.where for site in census()}
    for bucket in (
        ADAPTER_ALLOWLIST, ADMITTED_SEAM_CALLERS, GATEWAY_FACTORY_BINDING, CLAIM_WITNESS_MINT,
    ):
        overlap = sorted(set(AUTHORIZED_GATEWAY) & set(bucket))
        assert overlap == [], f"gateway scope also listed as a consumer: {overlap}"
    assert sorted(set(ADAPTER_ALLOWLIST) & set(ADMITTED_SEAM_CALLERS)) == []
    assert sorted(set(ADAPTER_ALLOWLIST) & set(CLAIM_WITNESS_MINT)) == []


def test_every_declared_entry_still_exists() -> None:
    """A stale entry is as dangerous as a missing one: it hides the real door."""
    live_scopes = {site.where for site in census()}
    live_lines = {site.line_key for site in census()}
    stale_allowlist = sorted(entry for entry in ADAPTER_ALLOWLIST if entry not in live_scopes)
    stale_seams = sorted(entry for entry in ADMITTED_SEAM_CALLERS if entry not in live_scopes)
    stale_findings = sorted(key for key in NAMED_FINDINGS if key not in live_lines)
    assert stale_allowlist == [], f"allowlist entries with no site: {stale_allowlist}"
    assert stale_seams == [], f"seam entries with no site: {stale_seams}"
    assert stale_findings == [], (
        "findings whose file:line moved — RE-REVIEW them rather than bump the "
        f"number: {stale_findings}"
    )


def test_the_allowlist_holds_no_product_surface_or_domain_service() -> None:
    """Charter: "no route, command, plugin product surface, or domain service"."""
    forbidden = ("holdspeak/web/", "holdspeak/services/", "holdspeak/commands/")
    offenders = sorted(
        f"{path}:{scope}" for path, scope in ADAPTER_ALLOWLIST
        if path.startswith(forbidden) or path.startswith("holdspeak/plugins/builtin/")
    )
    assert offenders == [], f"product surfaces in the adapter allowlist: {offenders}"
    for entry, justification in ADAPTER_ALLOWLIST.items():
        assert justification.startswith(("F:", "L:")), entry
    for entry, seam in ADMITTED_SEAM_CALLERS.items():
        assert seam.strip(), entry


def test_the_context_mint_and_the_legacy_marker_are_pinned() -> None:
    """Unforgeability is structural: two mints, one scope each, two waivers.

    The witness mint (``executor.py``) and the context mint
    (``InferenceRunner._attempt``) are each pinned to ONE module. Every name is in
    the census vocabulary, so a second caller — including one that renames the
    function on import — appears here as a moved/extra site rather than as a quiet
    new way to manufacture the right to build an engine.

    Round 2 (Terra blocker 4) changed WHAT is pinned. There is no longer a
    ``mint_claim_witness(operation_id=..., warrant=...)`` to call: issuance is a
    capability, taken once by ``executor.py`` at import via the one-shot
    ``_install_claim_issuer`` and invoked from ``ExecutorPlane.claim`` under a
    module-local name. Both new names are pinned here, and the retired public
    names (``mint_claim_witness``, ``issue_dispatch_context``) stay in the
    vocabulary with ZERO permitted sites, so bringing either back fails the fence.
    """
    sites = census()
    retired = [
        site for site in sites
        if site.target in {"mint_claim_witness", "issue_dispatch_context"}
    ]
    assert retired == [], f"a retired public mint reappeared: {retired}"

    installs = [site for site in sites if site.target == "_install_claim_issuer"]
    assert [site.where for site in installs] == [(EXECUTOR, "<module>")], installs
    witness_mints = [site for site in sites if site.target == "_issue_claim_witness"]
    assert [site.where for site in witness_mints] == [
        (EXECUTOR, "ExecutorPlane.claim")
    ], witness_mints
    context_mints = [site for site in sites if site.target == "_issue_dispatch_context"]
    assert [site.where for site in context_mints] == [
        (RUNNER, "InferenceRunner._attempt")
    ], context_mints

    marker_scopes: set[tuple[str, str]] = set()
    for path in sorted(PRODUCTION.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(REPO).as_posix()
        if relative == "holdspeak/kernel/dispatch_context.py":
            continue  # its home
        source = path.read_text(encoding="utf-8")
        if "LEGACY_UNCONTEXTUAL" not in source:
            continue
        tree = ast.parse(source)
        scopes = _scope_index(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            passed = list(node.args) + [keyword.value for keyword in node.keywords]
            for value in passed:
                # PASSING the marker is a waiver (pinned); COMPARING it
                # (`context is LEGACY_UNCONTEXTUAL`) is the recognizer inside the
                # validating factories, which is the mechanism, not an escape.
                if isinstance(value, ast.Name) and value.id == "LEGACY_UNCONTEXTUAL":
                    marker_scopes.add((relative, scopes.get(id(node), "<module>")))
    # EXACT equality, not containment: a NEW scope passing the marker is an
    # escape, and a DECLARED scope that stopped passing it is a stale waiver that
    # would hide the next one. The family can only shrink by deleting its entry
    # here in the same edit.
    assert marker_scopes == LEGACY_MARKER_SCOPES, (
        "the legacy uncontextual marker escaped its named findings: "
        f"escaped={sorted(marker_scopes - LEGACY_MARKER_SCOPES)} "
        f"stale={sorted(LEGACY_MARKER_SCOPES - marker_scopes)}"
    )


def test_the_legacy_marker_can_never_satisfy_a_context_requirement() -> None:
    """The marker is a FINDING, not a key: it must refuse at the validator.

    The structural pin above proves only WHERE the marker may appear. This is the
    other half — that appearing there buys nothing. If
    ``require_dispatch_context`` ever accepted it, every pinned finding scope
    would silently become an admitted adapter.
    """
    from holdspeak.kernel.dispatch_context import (
        CONTEXT_REQUIRED,
        LEGACY_UNCONTEXTUAL,
        require_dispatch_context,
    )
    from holdspeak.kernel.model import KernelRefused

    with pytest.raises(KernelRefused) as refusal:
        require_dispatch_context(LEGACY_UNCONTEXTUAL)
    assert CONTEXT_REQUIRED in str(refusal.value)


def test_every_allowlisted_factory_names_the_validator() -> None:
    """Structural half of Sol Amendment 1 (the runtime half is the context suite)."""
    for path, scope in CONTEXT_REQUIRING_FACTORIES:
        tree = ast.parse((REPO / path).read_text(encoding="utf-8"))
        wanted = scope.split(".")[-1]
        body = next(
            node for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == wanted
        )
        source = ast.dump(body)
        # Either validator counts as validating, and `require_bound_context` is
        # the STRICTER one (round 2): it refuses a real context that arrives with
        # no expected revision, which is how a remote child's context used to be
        # enough to build a local engine. `require_dispatch_context` remains the
        # dispatch-leg validator, where the operation id is the binding.
        assert any(
            validator in source
            for validator in ("require_bound_context", "require_dispatch_context")
        ), f"{path}:{scope} does not validate its context"
        assert "context" in {argument.arg for argument in body.args.kwonlyargs} | {
            argument.arg for argument in body.args.args
        }, f"{path}:{scope} takes no context"


def test_no_public_factory_scope_can_escape_context_validation() -> None:
    """The laundering test (HS-131-10 Terra finding B).

    ``build_configured_meeting_intel()`` sat on the adapter allowlist with the
    signature ``()``. It validated nothing, could not tell an admitted child from
    a plugin, and its two engine constructors were bucketed "allowlisted adapter"
    on the strength of the list alone. The allowlist is a REVIEW record, not an
    argument — so the review is now mechanical:

    * every module-level public ``F:`` scope must be a context-requiring factory;
    * every other ``F:`` scope must be a declared adapter internal;
    * every private construction body must be dominated by its validating wrapper
      — nothing else in production may call it.

    An uncontextual factory that keeps constructing engines is then a FINDING (it
    is), never a list entry.
    """
    factories = {
        entry for entry, justification in ADAPTER_ALLOWLIST.items()
        if justification.startswith("F:")
    }
    validating = set(CONTEXT_REQUIRING_FACTORIES)
    public = {
        entry for entry in factories
        if "." not in entry[1] and not entry[1].startswith("_")
    }
    escaped = sorted(
        entry for entry in public
        if entry not in validating and entry not in DELEGATING_FACTORY_SCOPES
    )
    assert escaped == [], (
        "public factory scopes on the allowlist that never validate a context: "
        f"{escaped} — an uncontextual factory is a FINDING, not an adapter entry."
    )
    assert sorted(factories - public - ADAPTER_INTERNAL_FACTORY_SCOPES) == []
    assert sorted(ADAPTER_INTERNAL_FACTORY_SCOPES - factories) == []
    assert sorted(validating - factories) == []

    # A delegating scope earns its exemption only by constructing NOTHING: the
    # single physical name in its body is the validating factory it hands to.
    for entry, delegate in DELEGATING_FACTORY_SCOPES.items():
        assert (entry[0], delegate) in validating, entry
        targets = {site.target for site in census() if site.where == entry}
        assert targets == {delegate}, f"{entry} also names {sorted(targets - {delegate})}"

    for (path, scope), wrapper in DOMINATED_CONSTRUCTION_BODIES.items():
        assert (path, scope) in ADAPTER_INTERNAL_FACTORY_SCOPES
        name = scope.split(".")[-1]
        callers = {
            site.where for site in census()
            if site.target == name and site.where != (path, scope)
        }
        assert callers == {(path, wrapper)}, (
            f"{path}:{scope} is reached from {sorted(callers)}, not only from its "
            f"validating wrapper {wrapper}"
        )


def test_the_findings_ledger_is_the_complete_blocking_package() -> None:
    """The eleven-family package is CLOSED: nothing blocks, nothing was waived.

    Every family left by deletion or admission, never by promotion into a list.
    HS-131-13 closed `cadence`, `decisions-route`, `delivery-legacy-factory`;
    HS-131-14 closed `plugin-default-provider` and `legacy-uncontextual-factory`;
    HS-131-15 closed `dictation-dry-run` and `dictation-command`; HS-131-16 closed
    `mesh-receiver`; HS-131-17 closes the last three — `dormant-mir` (the branch
    deleted), `legacy-live-meeting-engine` (the parallel live engine deleted), and
    `bookmark-auto-label` (routed through the admitted child seam).
    """
    assert BLOCKING_FAMILIES == frozenset()
    assert NAMED_FINDINGS == {}
    assert FINDINGS_WITHOUT_A_SITE == {}
    # An empty ledger is only honest if the families did not simply move onto a
    # list. The meeting session's OWN modules — the two that held the closing
    # families — may not appear in the adapter allowlist at all, and neither may a
    # command scope; those were the remedies a closing family might have taken.
    forbidden = sorted(
        f"{path}:{scope}" for path, scope in ADAPTER_ALLOWLIST
        if path.startswith("holdspeak/commands/")
        or path in {
            "holdspeak/meeting_session/session.py",
            "holdspeak/meeting_session/bookmarks.py",
        }
    )
    assert forbidden == [], (
        f"a meeting-session or command scope on the adapter allowlist: {forbidden} "
        "— that is not an available remedy for a blocking family"
    )
    # The meeting entries that DO exist are exactly the admitted dispatch
    # closures HS-131-08 built: one per capability, live and deferred, each an
    # `L:` closure inside one claimed child. Nothing was added here to close a
    # family, and nothing here is a factory.
    meeting_entries = {
        (path, scope): justification
        for (path, scope), justification in ADAPTER_ALLOWLIST.items()
        if path.startswith("holdspeak/meeting_session/")
    }
    assert set(meeting_entries) == {
        ("holdspeak/meeting_session/intel_routed_children.py", "IntelRoutedChildMixin._admitted_live_window.call"),
        ("holdspeak/meeting_session/intel_routed_children.py", "IntelRoutedChildMixin._admitted_bookmark_label.call"),
        ("holdspeak/meeting_session/intel_routed_children.py", "IntelRoutedChildMixin._admitted_auto_title.call"),
        ("holdspeak/meeting_session/deferred_admission.py", "DeferredIntelJob.analyze.call"),
        ("holdspeak/meeting_session/deferred_admission.py", "DeferredIntelJob.bookmark_label.call"),
        ("holdspeak/meeting_session/deferred_admission.py", "DeferredIntelJob.auto_title.call"),
        ("holdspeak/meeting_session/deferred_bound.py", "bound_analysis_dispatch.call"),
        ("holdspeak/meeting_session/deferred_bound.py", "bound_bookmark_label_dispatch.call"),
        ("holdspeak/meeting_session/deferred_bound.py", "bound_auto_title_dispatch.call"),
    }
    assert all(
        justification.startswith("L:") and scope.endswith(".call")
        for (_path, scope), justification in meeting_entries.items()
    )
    # ...and the retired names are still DANGEROUS, so reintroducing one fails.
    for retired in ("MeetingIntel", "generate_bookmark_label", "build_configured_meeting_intel"):
        assert retired in DANGEROUS


def test_text_entry_build_pipeline_sites_are_admitted_seams_not_findings() -> None:
    """HS-131-15's two former findings must visibly thread their admission."""
    expected = {
        ("holdspeak/web/routes/dictation/_helpers.py", "_run_dictation_dry_run_text"): "dictation-dry-run",
        ("holdspeak/commands/dictation.py", "_cmd_dry_run"): "dictation-command",
    }
    sites = [site for site in census() if site.target == "build_pipeline"]
    assert {site.where for site in sites} >= set(expected)
    assert all(site.where not in NAMED_FINDINGS for site in sites)
    assert all(_bucket(site) == "seam" for site in sites if site.where in expected)

    # The seam ledger is not itself authority. A scope that remained on the list
    # after dropping `admission=...` would otherwise look admitted merely because
    # its name had not changed. Pin the executable keyword in both callers; the
    # mutation proof removes each one in turn and expects the named family here.
    for (path, scope), family in expected.items():
        tree = ast.parse((REPO / path).read_text(encoding="utf-8"))
        body = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == scope
        )
        calls = [
            node
            for node in ast.walk(body)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "build_pipeline"
        ]
        assert len(calls) == 1, f"{family}: expected one build_pipeline call"
        keywords = {keyword.arg: keyword.value for keyword in calls[0].keywords}
        assert "admission" in keywords, (
            f"{family}: build_pipeline lost its caller-owned admission"
        )
        assert not (
            isinstance(keywords["admission"], ast.Constant)
            and keywords["admission"].value is None
        ), f"{family}: build_pipeline hard-coded admission=None"


def test_the_owner_inventory_covers_every_finding() -> None:
    """The ledger above is worthless to the owner if the decision package omits a row.

    The inventory is the owner's decision artifact for the blocking families it
    found; it is authored into the story's evidence assets. This asserts the two
    never drift in the direction that matters: every family name AND every
    ``path:line`` still in the code-side ledger has to appear in it. The inventory
    is deliberately allowed to be a SUPERSET — it is the historical record of the
    eleven families HS-131-10 found, and a row that the amendment wave has since
    closed stays written down rather than being edited out of the owner's package.
    """
    inventory_path = (
        REPO / "pm/roadmap/holdspeak/phase-131-one-admission-path/assets/hs-131-10"
        / "findings-inventory.md"
    )
    if not inventory_path.exists():
        pytest.fail(
            "the owner's findings inventory is missing: "
            f"{inventory_path.relative_to(REPO)}\n"
            "HS-131-10 is BLOCKED while any family stands; the decision package "
            "that names them must ship with this fence, not after it."
        )
    inventory = inventory_path.read_text(encoding="utf-8")
    missing_families = sorted(f for f in BLOCKING_FAMILIES if f not in inventory)
    missing_sites = sorted(
        key for key in NAMED_FINDINGS if key.split(" ")[0] not in inventory
    )
    assert missing_families == [], f"families absent from the owner's inventory: {missing_families}"
    assert missing_sites == [], f"sites absent from the owner's inventory: {missing_sites}"


# ------------------------------------------------------------- mutation fixtures


SYNTHETIC_DIRECT_SDK = '''
"""A synthetic product module: the door this fence exists to close."""
from openai import OpenAI


def summarize_note(text: str) -> str:
    client = OpenAI(api_key="k")
    return client.chat.completions.create(model="m", messages=[]).choices[0].message.content
'''

SYNTHETIC_FIRST_CLASS_CALLABLE = '''
"""A synthetic product module: the CALLABLE-REFERENCE door (Sol Amendment 2)."""
import asyncio


async def summarize_note(intel, text: str) -> str:
    chat_fn = intel._chat_completion_text
    return await asyncio.to_thread(intel.run_prompt, system_prompt="s", user_prompt=text)
'''

SYNTHETIC_TRANSCRIBE = '''
"""A synthetic product module: an unadmitted Whisper leaf."""


def caption(backend, audio) -> str:
    return backend.transcribe(audio)
'''

SYNTHETIC_UNREGISTERED_ADAPTER = '''
"""A synthetic UNREGISTERED adapter: the right SHAPE, never reviewed onto the list."""


class RogueRuntime:
    def load(self):
        self._model = Llama(model_path="/rogue.gguf")

    def _run(self, prompt):
        return self._model.create_chat_completion(messages=[{"role": "user"}])
'''

SYNTHETIC_INDIRECT_SENDER = '''
"""A synthetic product module: the INDIRECT SENDER door (Sol Amendment 2)."""


def summarize(intel, egress, payload):
    return egress.run(sender=lambda: intel.run_prompt(system_prompt="s", user_prompt=payload))
'''

SYNTHETIC_EXISTING_CLIENT = '''
"""A synthetic product module: the CREATE-ONLY door.

No constructor, no factory, no engine — a route that is simply HANDED an
already-built client and calls the SDK's wire verb (and hands the same bound
method to a thread pool). The pre-fix census returned ZERO sites for this file.
"""
import asyncio


async def summarize(client, text):
    result = client.chat.completions.create(model="m", messages=[{"role": "user", "content": text}])
    return await asyncio.to_thread(client.chat.completions.create, model="m", messages=[]) or result
'''

SYNTHETIC_UNRELATED_CREATE = '''
"""NOT a door: the `create` verb this repo uses everywhere for its own stores."""


def record(repo, principal, payload, store, name):
    repo.create(principal, payload)
    store.create(name)
    return _svc().create(principal, payload)
'''

SYNTHETIC_FORGED_MINT = '''
"""A synthetic product module: minting the right to build an engine.

The witness/context mints execute no model themselves, so a call-shape census
that only knew physical verbs would wave this through — and its author would
then be able to construct any adapter in the codebase.

Round 2: at RUNTIME this module cannot work at all — `_install_claim_issuer`
was spent by `executor.py`'s import and refuses. The census still has to see it,
because "it would fail anyway" is not a fence: the next author writes the same
line against whatever the issuer is called then.
"""
from holdspeak.kernel.claim_witness import _install_claim_issuer as _mint
from holdspeak.kernel.dispatch_context import _issue_dispatch_context


def forge(revision):
    witness = _mint()(operation_id="op_invented", warrant={"signature": "looks-real"})
    return _issue_dispatch_context(witness=witness, revision=revision, warrant={"signature": "looks-real"})
'''

SYNTHETIC_GETATTR_BINDING = '''
"""A synthetic product module: the model verb spelled as a STRING, then hidden.

Three doors, three containers, one shape. `getattr(obj, "verb")` is a Sol
Amendment 2 callable reference whose name the AST holds as a Constant, and the
holder is an ATTRIBUTE, so neither a dotted-call census nor a Name-target
binding tracker sees anything here at all.
"""


class Door:
    def __init__(self, intel, client, backend):
        self._run = getattr(intel, "run_prompt")
        self._create = getattr(client.chat.completions, "create")
        self._transcribe = getattr(backend, "transcribe")

    def go(self, text, audio):
        self._create(model="m", messages=[])
        return self._run(user_prompt=text), self._transcribe(audio)
'''

SYNTHETIC_GETATTR_CONTAINERS = '''
"""Every other container that used to launder the same door."""
import asyncio

HOLDERS = {}
HOLDERS["go"] = getattr(intel, "run_prompt")


async def go(intel, backend, text):
    (walrus := getattr(intel, "run_prompt"))(user_prompt=text)
    pair = getattr(intel, "run_prompt"), getattr(backend, "transcribe")
    await asyncio.to_thread(getattr(intel, "run_prompt"), user_prompt=text)
    return getattr(intel, "run_prompt")(user_prompt=text), pair, walrus
'''

SYNTHETIC_GETATTR_INNOCENT = '''
"""The forms that must STAY quiet.

Precision is the whole value of the census. A rule that flagged every `getattr`
would bury the real doors in noise from widget handlers, repository verbs, and
the capability PROBES this codebase legitimately uses — probes ASK whether a
capability exists and never obtain it (design section 1).
"""


class Store:
    def go(self, widget, repo, engine, inner, row, name):
        self._h = getattr(widget, "on_click")
        self._mk = getattr(repo, "create")
        self._computed = getattr(repo, name)
        if not callable(getattr(engine, "run_prompt", None)):
            return None
        if getattr(getattr(inner, "classify", None), "accepts_response_format", False):
            return None
        if getattr(engine, "run_prompt", None) is None:
            return None
        return self._h(name), self._mk(row), self._computed(row)
'''

#: ``build_intel_for_target`` no longer EXISTS (HS-131-13 deleted it), and that is
#: exactly why it stays in the census vocabulary and in this mutation: the fence
#: must fail on the name coming BACK, not merely on it being absent today.
SYNTHETIC_ALIASED_IMPORT = '''
"""A synthetic product module: the RENAMED-ON-IMPORT door."""
from openai import OpenAI as _Client
from holdspeak.inference_targets import build_intel_for_target as _factory


def summarize(text):
    return _Client(api_key="k"), _factory(None)
'''

SYNTHETIC_REINTRODUCED_ROUTE_SEAM = '''
"""HS-131-13's own mutation: the exact route seam this story deleted.

The Decisions route used to build an engine from a MUTABLE resolved target and
hand `intel.run_prompt` to a thread pool, beside a service that already admits
its own child. Both halves must fail the census by name if anyone types them
again — the deleted code is not a fence.
"""
import asyncio

from holdspeak.inference_targets import build_intel_for_target


async def _generate_with_model(db, target, prompt):
    intel = build_intel_for_target(target, db)
    output = await asyncio.to_thread(intel.run_prompt, system_prompt="s", user_prompt=prompt)
    return str(output or "").strip(), intel
'''

SYNTHETIC_REINTRODUCED_PLUGIN_FALLBACK = '''
"""HS-131-14's own mutation: the plugin default-provider family, retyped.

Every LLM builtin used to carry exactly this: a `_cached_provider` that lazily
built the configured engine and then dispatched `_chat_completion_text` on it —
thirty sites, no admitted child behind any of them. The deleted code is not a
fence, so both halves must come back as unregistered, by name: the uncontextual
factory (whose symbol no longer exists) and the completion leaf, in both the
called and the first-class-reference spelling.
"""
from typing import Any


class RetypedPlugin:
    id = "retyped"
    required_capabilities = ["llm"]

    def __init__(self) -> None:
        self._cached_provider: Any = None

    def _call_intel(self, messages):
        if self._cached_provider is None:
            from holdspeak.intel import build_configured_meeting_intel

            self._cached_provider = build_configured_meeting_intel()
        chat = self._cached_provider._chat_completion_text
        return self._cached_provider._chat_completion_text(messages, temperature=0.2, max_tokens=800), chat
'''

SYNTHETIC_REINTRODUCED_LIVE_MEETING_ENGINE = '''
"""HS-131-17's own mutation: the parallel live meeting engine, retyped.

`MeetingSession.start()` used to preflight the provider runtime and construct a
long-lived `MeetingIntel` beside the already frozen plan, and `add_bookmark`
then handed that object to a background thread which called the context-only
`generate_bookmark_label` leaf directly. Both are deleted, and deleted code is
not a fence: retyping either must come back as unregistered, by name.
"""
import threading


class RetypedSession:
    def start(self):
        self._intel = MeetingIntel(provider="local")
        return self._intel

    def add_bookmark(self, bookmark, context):
        threading.Thread(target=self._label, args=(bookmark, context)).start()

    def _label(self, bookmark, context):
        bookmark.label = self._intel.generate_bookmark_label(context)
'''

#: Each mutation's EXACT expected census output (Sol Amendment 5: a mutation
#: proof must show the INTENDED guard fired, naming the intended site — "some
#: assertion failed" is not a proof). Written literally so a change in the
#: classifier's precision — a lost line number, a collapsed scope, a target
#: renamed to something vaguer — fails here instead of passing quietly.
MUTATIONS: tuple[tuple[str, str, list[str]], ...] = (
    (
        "holdspeak/web/routes/synthetic_door.py",
        SYNTHETIC_DIRECT_SDK,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/web/routes/synthetic_door.py:7"
            " summarize_note OpenAI",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/web/routes/synthetic_door.py:8"
            " summarize_note chat.completions.create",
        ],
    ),
    (
        # The door with NO constructor anywhere in the file.
        "holdspeak/web/routes/synthetic_existing_client.py",
        SYNTHETIC_EXISTING_CLIENT,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/web/routes/synthetic_existing_client.py:12"
            " summarize chat.completions.create",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/web/routes/synthetic_existing_client.py:13"
            " summarize chat.completions.create",
        ],
    ),
    (
        "holdspeak/services/synthetic_forged_mint.py",
        SYNTHETIC_FORGED_MINT,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_forged_mint.py:18"
            " forge _install_claim_issuer",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_forged_mint.py:19"
            " forge _issue_dispatch_context",
        ],
    ),
    (
        # Terra MANDATORY 1 (2c) + the attribute holders Terra found in 2d.
        # One site per door, at the GETTER — the container is irrelevant.
        "holdspeak/services/synthetic_getattr.py",
        SYNTHETIC_GETATTR_BINDING,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_getattr.py:13"
            " Door.__init__ run_prompt",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_getattr.py:14"
            " Door.__init__ chat.completions.create",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_getattr.py:15"
            " Door.__init__ transcribe",
        ],
    ),
    (
        "holdspeak/services/synthetic_callable.py",
        SYNTHETIC_FIRST_CLASS_CALLABLE,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_callable.py:7"
            " summarize_note _chat_completion_text",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_callable.py:8"
            " summarize_note run_prompt",
        ],
    ),
    (
        "holdspeak/web/routes/synthetic_whisper.py",
        SYNTHETIC_TRANSCRIBE,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/web/routes/synthetic_whisper.py:6"
            " caption transcribe",
        ],
    ),
    (
        "holdspeak/plugins/dictation/runtime_rogue.py",
        SYNTHETIC_UNREGISTERED_ADAPTER,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/plugins/dictation/runtime_rogue.py:7"
            " RogueRuntime.load Llama",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/plugins/dictation/runtime_rogue.py:10"
            " RogueRuntime._run create_chat_completion",
        ],
    ),
    (
        "holdspeak/services/synthetic_sender.py",
        SYNTHETIC_INDIRECT_SENDER,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_sender.py:6"
            " summarize run_prompt",
        ],
    ),
    (
        # The census reports the RESOLVED name, not the local alias, so the
        # allowlist/findings keys stay stable no matter what a module calls it.
        "holdspeak/services/synthetic_alias.py",
        SYNTHETIC_ALIASED_IMPORT,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_alias.py:8"
            " summarize OpenAI",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/services/synthetic_alias.py:8"
            " summarize build_intel_for_target",
        ],
    ),
    (
        # HS-131-13: the deleted Decisions route seam, retyped. Both halves —
        # the mutable-target factory AND the bound `run_prompt` handed to a
        # thread pool — must reappear as unregistered, by name.
        "holdspeak/web/routes/synthetic_decisions_seam.py",
        SYNTHETIC_REINTRODUCED_ROUTE_SEAM,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/web/routes/synthetic_decisions_seam.py:15"
            " _generate_with_model build_intel_for_target",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/web/routes/synthetic_decisions_seam.py:16"
            " _generate_with_model run_prompt",
        ],
    ),
    (
        # HS-131-14: the plugin fallback, retyped. Three doors in one method —
        # the uncontextual factory, the held completion reference, and the call.
        "holdspeak/plugins/builtin/synthetic_retyped_fallback.py",
        SYNTHETIC_REINTRODUCED_PLUGIN_FALLBACK,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/plugins/builtin/synthetic_retyped_fallback.py:25"
            " RetypedPlugin._call_intel build_configured_meeting_intel",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/plugins/builtin/synthetic_retyped_fallback.py:26"
            " RetypedPlugin._call_intel _chat_completion_text",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/plugins/builtin/synthetic_retyped_fallback.py:27"
            " RetypedPlugin._call_intel _chat_completion_text",
        ],
    ),
    (
        # HS-131-17: the deleted live meeting engine and the direct bookmark
        # label, retyped in the module they were deleted from. Neither name has a
        # finding to fall into any more, so both are simply unregistered.
        "holdspeak/meeting_session/synthetic_live_engine.py",
        SYNTHETIC_REINTRODUCED_LIVE_MEETING_ENGINE,
        [
            "UNREGISTERED_MODEL_EXECUTION holdspeak/meeting_session/synthetic_live_engine.py:15"
            " RetypedSession.start MeetingIntel",
            "UNREGISTERED_MODEL_EXECUTION holdspeak/meeting_session/synthetic_live_engine.py:22"
            " RetypedSession._label generate_bookmark_label",
        ],
    ),
)


@pytest.mark.parametrize("relative,source,expected", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_a_synthetic_door_fails_with_the_exact_named_message(
    relative: str, source: str, expected: list[str]
) -> None:
    """Every mutation form produces its EXACT ``UNREGISTERED_MODEL_EXECUTION`` line.

    Covers the direct SDK construction, the first-class-callable reference, an
    unadmitted Whisper leaf, an adapter-SHAPED class that was never reviewed onto
    the allowlist (shape is not admission), and a physical call hidden behind an
    indirect ``sender=`` closure.
    """
    sites = list(sites_in_source(relative, source))
    assert sites, f"{relative}: the census saw no door at all"
    unregistered = sorted(site.named() for site in sites if _bucket(site) is None)
    assert unregistered == sorted(expected)


def test_the_sdk_verb_is_recognized_by_its_receiver_chain_not_by_its_name() -> None:
    """Precision, in both directions, is what makes the create-only door closable.

    The census has to see ``client.chat.completions.create`` in a module that
    constructs nothing — and must NOT see the ``.create`` this repo uses for
    repositories, stores, and services, or the ledger fills with false doors and
    the real one hides in the noise.
    """
    seen = {
        (site.target, site.kind, site.line)
        for site in sites_in_source(
            "holdspeak/web/routes/x.py", SYNTHETIC_EXISTING_CLIENT
        )
    }
    assert ("chat.completions.create", "call", 12) in seen    # called directly
    assert ("chat.completions.create", "ref", 13) in seen     # handed to a thread pool
    assert len(seen) == 2
    assert {site.family for site in sites_in_source("x.py", SYNTHETIC_EXISTING_CLIENT)} == {
        "sdk-completion-create"
    }
    assert list(sites_in_source("holdspeak/services/x.py", SYNTHETIC_UNRELATED_CREATE)) == []



def test_a_model_verb_spelled_as_a_string_is_still_a_door() -> None:
    """Terra MANDATORY 1 + 2d: `getattr(obj, "verb")` must fail CLOSED.

    The census returned ZERO sites for every one of these, so a product module
    could hold `run_prompt`, the SDK's `create`, or `transcribe` and execute a
    model with nothing in the ledger. Round 2c closed the `name = getattr(...)`
    form by tracking bindings; Terra then walked straight around it with
    `self._call = getattr(...)`, because the tracker only accepted `ast.Name`
    targets.

    So the rule no longer looks at the container at all: the GETTER is the door,
    recorded where it is written, exactly like the bound-method reference it is
    (`chat_fn = intel._chat_completion_text`). One site per door.
    """
    seen = {
        (site.target, site.kind, site.line)
        for site in sites_in_source(
            "holdspeak/services/x.py", SYNTHETIC_GETATTR_BINDING
        )
    }
    assert seen == {
        ("run_prompt", "ref", 13),
        ("chat.completions.create", "ref", 14),
        ("transcribe", "ref", 15),
    }, seen


def test_no_container_can_launder_the_getter() -> None:
    """Subscript, walrus, tuple, `to_thread`, and immediate invocation.

    Closing container shapes one at a time is a game the author of the next
    shape always wins, which is why 2d stopped playing it. Each of these holds
    the same door a different way and each is recorded exactly once.
    """
    sites = list(
        sites_in_source("holdspeak/services/x.py", SYNTHETIC_GETATTR_CONTAINERS)
    )
    assert [site.target for site in sites].count("run_prompt") == 5
    assert [site.target for site in sites].count("transcribe") == 1
    assert len(sites) == 6, [site.named() for site in sites]
    # The one that fires where it is written says so; the rest are held.
    assert sorted(site.kind for site in sites) == ["call", "ref", "ref", "ref", "ref", "ref"]


def test_the_getattr_rule_does_not_broaden_to_unrelated_dynamic_attributes() -> None:
    """...and precision in the other direction, which is what makes it usable.

    Unrelated verbs, repository `create`, a computed (non-literal) name, and the
    three capability-PROBE spellings this repo really uses — `callable(...)`, a
    marker read through the getter, and an `is None` guard — all stay out. A
    probe asks whether a capability exists; it never obtains the door.
    """
    assert list(
        sites_in_source("holdspeak/services/x.py", SYNTHETIC_GETATTR_INNOCENT)
    ) == []


def test_the_callable_reference_forms_are_classified_as_references_not_calls() -> None:
    """A call-expression-only census would miss both of these entirely."""
    callable_sites = {
        (site.target, site.kind)
        for site in sites_in_source("holdspeak/services/x.py", SYNTHETIC_FIRST_CLASS_CALLABLE)
    }
    assert ("_chat_completion_text", "ref") in callable_sites
    assert ("run_prompt", "ref") in callable_sites
    # The indirect sender's call, by contrast, is a real call expression even
    # though it only ever runs through someone else's `sender()` invocation.
    sender_sites = {
        (site.target, site.kind)
        for site in sites_in_source("holdspeak/services/y.py", SYNTHETIC_INDIRECT_SENDER)
    }
    assert ("run_prompt", "call") in sender_sites


def test_an_allowlisted_scope_does_not_launder_a_different_module() -> None:
    """The allowlist key is (path, scope) — a scope NAME alone admits nothing.

    Without this, any new module could adopt an allowlisted function name (say
    ``build_intel_for_revision``) and inherit its admission.
    """
    laundered = '''
def build_intel_for_revision(revision):
    return MeetingIntel(provider="local")
'''
    sites = list(sites_in_source("holdspeak/services/impostor.py", laundered))
    assert [site.named() for site in sites] == [
        "UNREGISTERED_MODEL_EXECUTION holdspeak/services/impostor.py:3"
        " build_intel_for_revision MeetingIntel"
    ]


# ------------------------------------------- HS-131-17: the live meeting fence


def test_the_live_meeting_session_names_no_model_execution_at_all() -> None:
    """The positive half of closing the last two meeting families.

    A live `MeetingSession` holds its frozen plan, its parent context, and an
    explicit liveness flag — never an engine. So the two modules that used to
    construct and call one hold no census site: `session.py` builds nothing at
    start, and `bookmarks.py` reaches a label only through the admitted seam
    (whose dispatch closure lives in `intel_admission.py` and is allowlisted).
    """
    for module in ("session.py", "bookmarks.py"):
        relative = f"holdspeak/meeting_session/{module}"
        sites = [site for site in census() if site.path == relative]
        assert sites == [], f"{relative} named model execution again: {sites}"

    # The dormant MIR branch is GONE, not merely disabled by default: no switch,
    # no plugin host, and no import of the routing pipeline it used to call after
    # the live parent had already closed.
    session_tree = ast.parse(
        (REPO / "holdspeak/meeting_session/session.py").read_text(encoding="utf-8")
    )
    names = {
        node.id for node in ast.walk(session_tree) if isinstance(node, ast.Name)
    } | {
        node.attr for node in ast.walk(session_tree) if isinstance(node, ast.Attribute)
    }
    for retired in ("mir_routing_enabled", "_mir_plugin_host", "process_meeting_state"):
        assert retired not in names, f"the dormant MIR branch came back: {retired}"
    imported = {
        node.module or "" for node in ast.walk(session_tree) if isinstance(node, ast.ImportFrom)
    }
    assert not any("plugins.pipeline" in module for module in imported)
    bookmarks_source = (REPO / "holdspeak/meeting_session/bookmarks.py").read_text(encoding="utf-8")
    assert "_admitted_bookmark_label" in bookmarks_source


# ------------------------------------------------- HS-131-16: the receiver fence


def test_the_mesh_receiver_names_no_model_execution_at_all() -> None:
    """The positive half of closing `mesh-receiver`: zero sites, not a waiver.

    A family can leave :data:`NAMED_FINDINGS` by being deleted or admitted. This
    one was ADMITTED, and the shape of that admission is visible right here: the
    worker constructs nothing, so the census finds no factory and no completion
    verb in its module. If a future edit reintroduces either, the mutation proof
    below is what fails.
    """
    sites = [site for site in census() if site.path == "holdspeak/commands/mesh_serve.py"]
    assert sites == [], f"the mesh receiver named model execution again: {sites}"

    # And it reaches the model through the ONE gateway, structurally: the worker
    # hands its injectable factory to the worker-local runner rather than calling
    # it, and never imports the legacy marker again.
    source = (REPO / "holdspeak/commands/mesh_serve.py").read_text(encoding="utf-8")
    assert "LEGACY_UNCONTEXTUAL" not in source
    assert "run_prompt" not in source
    assert "build_meeting_intel_for_profile" not in source
    runner_source = (REPO / "holdspeak/kernel/mesh_local_runner.py").read_text(encoding="utf-8")
    assert "InferenceRunner(" in runner_source


def test_a_direct_receiver_run_prompt_fails_the_fence() -> None:
    """The mutation proof: restore the side door and the census must name it.

    A disposable edit puts a direct ``engine.run_prompt(...)`` back into the
    receiver. The fence has to fail BEFORE the source is restored — a green suite
    that only ever saw the fixed tree proves nothing about the fence — and the
    file must come back byte-identical, verified by digest.
    """
    target = REPO / "holdspeak/commands/mesh_serve.py"
    original = target.read_bytes()
    before = hashlib.sha256(original).hexdigest()
    anchor = "    def claim_once(self) -> Optional[tuple[dict[str, Any], Any]]:"
    mutation = (
        "    def _mutation_direct_dispatch(self, engine: Any) -> str:\n"
        '        return str(engine.run_prompt(system_prompt="", user_prompt=""))\n\n'
    )
    text = original.decode("utf-8")
    assert anchor in text, "the mutation anchor moved; re-review this proof"
    try:
        target.write_text(text.replace(anchor, mutation + anchor, 1), encoding="utf-8")
        sites = [site for site in census() if site.path == "holdspeak/commands/mesh_serve.py"]
        assert len(sites) == 1, sites
        site = sites[0]
        assert site.target == "run_prompt"
        assert site.scope == "MeshServeWorker._mutation_direct_dispatch"
        # Unregistered: not a gateway, not an allowlist entry, not a seam, and
        # NOT a finding — the family is gone, so there is nothing to fall into.
        assert _bucket(site) is None
        assert site.named().startswith("UNREGISTERED_MODEL_EXECUTION")
        assert site.line_key not in NAMED_FINDINGS
    finally:
        target.write_bytes(original)
    assert hashlib.sha256(target.read_bytes()).hexdigest() == before
    assert [site for site in census() if site.path == "holdspeak/commands/mesh_serve.py"] == []
