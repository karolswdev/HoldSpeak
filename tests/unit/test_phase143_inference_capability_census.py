"""HSEGHS001HS104-143-01 — checked-in capability/physical-path baseline.

Phase 131's ``test_one_path_census`` is the fail-closed AST authority for
model-shaped production code.  This companion fixture deliberately pins its
*individual sites* to a proposed Phase 143 capability and source owner.  A
second call in an existing allowlisted function therefore cannot hide behind
that function's Phase 131 entry: it gets the key ``...#2``, has no row here and
fails this test.

The keys are line-free (owner ruling 2026-10-03; ``tests/unit/_line_free.py``):
file, enclosing scope, site, and an ordinal for a repeat in one scope.  An edit
above a site no longer turns the census red; a new site still does.  Comments
below that say "re-anchored" or name a line are history from the line-pinned
form.

``internal.*`` rows are non-assignable implementation capabilities.  They are
not a proposal for a generic owner-facing model picker; they identify shared
gateway/factory work whose eventual caller capability is frozen above the
adapter.  Story 02 replaces the proposed IDs with registry definitions.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

from tests.unit import _line_free
from tests.unit import test_one_path_census as one_path
from tests.unit._line_free import Record


@dataclass(frozen=True)
class ProposedRoute:
    capability_id: str
    source_owner: str
    admission: str


def _site_keys() -> dict[str, one_path.Site]:
    """Every Phase-131 AST site under its line-free key (``tests/unit/_line_free.py``)."""
    sites = one_path.census()
    by_record = {
        Record(site.path, site.line, index, f"{site.scope}|{site.target}|{site.kind}"): site
        for index, site in enumerate(sites)
    }
    ordered = sorted(by_record)
    seen: dict[str, int] = {}
    keyed: dict[str, one_path.Site] = {}
    for record in ordered:
        base = f"{record.path}|{record.tail}"
        seen[base] = seen.get(base, 0) + 1
        keyed[base if seen[base] == 1 else f"{base}#{seen[base]}"] = by_record[record]
    assert sorted(keyed) == _line_free.ordinal_keys(ordered)
    return keyed


def _runner_entrances() -> list[str]:
    """Every production reference to the runner's public ``invoke`` verb.

    Looking for the bound method as a value is intentional: cadence, decision,
    and delivery hand it to ``asyncio.to_thread`` rather than spelling a direct
    call.  There are no other production ``.invoke`` expressions today, so an
    unexpected one fails closed instead of relying on a receiver-name heuristic.
    """
    from holdspeak.operations import DESCRIPTORS

    declared = {descriptor.name for descriptor in DESCRIPTORS}

    def _names_an_operation(call: ast.Call) -> bool:
        # PHILO-5-01/02: ``OperationRegistry.invoke(principal, "<operation>", ...)``
        # is the application-operation contract, not the runner. It is told
        # apart by its second argument: a DECLARED operation name (or a choice
        # between two), which no InferenceRunner.invoke call takes.
        if len(call.args) < 2:
            return False
        name = call.args[1]
        options = [name.body, name.orelse] if isinstance(name, ast.IfExp) else [name]
        return all(isinstance(o, ast.Constant) and o.value in declared for o in options)

    entries: list[Record] = []
    for path in sorted(one_path.PRODUCTION.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        scopes = one_path._scope_index(tree)
        called = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
        contract = {
            id(node.func) for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "invoke" and _names_an_operation(node)
        }
        relative = path.relative_to(one_path.REPO).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "invoke" and id(node) not in contract:
                kind = "call" if id(node) in called else "ref"
                entries.append(Record(
                    relative, node.lineno, node.col_offset,
                    f"{scopes.get(id(node), '<module>')}|{kind}",
                ))
    return _line_free.ordinal_keys(entries)


# Generated from `one_path.census()` on 2026-08-21.  Keep one literal row per
# AST site, rather than a scope allowlist: a second invocation in a known scope
# is the key ``...#2`` and requires an intentional capability/owner review.
EXPECTED_CALL_SITES = frozenset("""
holdspeak/commands/dictation.py|_cmd_dry_run|build_pipeline|call
holdspeak/dictation_runner.py|run_pipeline_corrections_only|build_pipeline|call
holdspeak/dictation_runner.py|run_dictation_pipeline|build_pipeline|call
holdspeak/inference_targets.py|local_pinned_meeting_intel|_local_pinned_engine|call
holdspeak/inference_targets.py|_local_pinned_engine|MeetingIntel|call
holdspeak/inference_targets.py|build_intel_for_revision|_engine_for_revision|call
holdspeak/inference_targets.py|_engine_for_revision|MeetingIntel|call
holdspeak/inference_targets.py|_engine_for_revision|local_pinned_meeting_intel|call
holdspeak/inference_targets.py|_engine_for_revision|build_meeting_intel_for_profile|call
holdspeak/intel/engine.py|MeetingIntel._ensure_openai_client_loaded|OpenAI|call
holdspeak/intel/engine.py|MeetingIntel._ensure_local_model_loaded|Llama|call
holdspeak/intel/engine.py|MeetingIntel._ensure_runtime_loaded|_ensure_local_model_loaded|call
holdspeak/intel/engine.py|MeetingIntel._ensure_runtime_loaded|_ensure_openai_client_loaded|call
holdspeak/intel/engine.py|MeetingIntel._ensure_model_loaded|_ensure_runtime_loaded|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_text|create_chat_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_text|_remote_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_text|chat.completions.create|ref
holdspeak/intel/engine.py|MeetingIntel._chat_completion_stream|create_chat_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_stream|_remote_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_stream|chat.completions.create|ref
holdspeak/intel/engine.py|MeetingIntel._chat_completion_deltas|create_chat_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_deltas|_remote_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_deltas|chat.completions.create|ref
holdspeak/intel/engine.py|MeetingIntel.run_prompt_stream|_chat_completion_deltas|call
holdspeak/intel/engine.py|MeetingIntel.run_prompt|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel.run_prompt_messages|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel._analyze_once|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel._analyze_stream|_chat_completion_stream|call
holdspeak/intel/engine.py|MeetingIntel.generate_title|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel.generate_bookmark_label_with_context|_chat_completion_text|call
holdspeak/intel/mesh_relay.py|MeshRelayIntel._chat_completion_text|run_prompt|call
holdspeak/intel/providers.py|_configured_engine|MeshRelayIntel|call
holdspeak/intel/providers.py|_configured_engine|MeetingIntel|call
holdspeak/intel/providers.py|configured_meeting_intel|_configured_engine|call
holdspeak/intel/providers.py|build_meeting_intel_for_profile|_profile_engine|call
holdspeak/intel/providers.py|_profile_engine|MeshRelayIntel|call
holdspeak/intel/providers.py|_profile_engine|configured_meeting_intel|call
holdspeak/intel/providers.py|_profile_engine|MeetingIntel|call
holdspeak/intel/providers.py|_profile_engine|MeetingIntel|call#2
holdspeak/intel/providers.py|_profile_engine|configured_meeting_intel|call#2
holdspeak/kernel/executor.py|<module>|_install_claim_issuer|call
holdspeak/kernel/executor.py|ExecutorPlane.claim|_issue_claim_witness|call
holdspeak/kernel/inference_runner.py|InferenceRunner._attempt_stream|_issue_dispatch_context|call
holdspeak/kernel/inference_runner.py|InferenceRunner._attempt|_issue_dispatch_context|call
holdspeak/kernel/inference_runner.py|InferenceRunner.__init__|build_intel_for_revision|ref
holdspeak/kernel/prompt_adapter.py|CanonicalPromptAdapter.dispatch|run_prompt|call
holdspeak/kernel/prompt_adapter.py|StreamingPromptAdapter.dispatch|run_prompt|call
holdspeak/main.py|_run_meeting_mode|transcribe|call
holdspeak/main.py|_run_meeting_mode|transcribe|call#2
holdspeak/meeting_import.py|_transcribe_import_windows|transcribe|call
holdspeak/memory/engine.py|EmbeddingAdapter._local_model|Llama|call
holdspeak/memory/engine.py|EmbeddingAdapter._endpoint_vectors|_ensure_openai_client_loaded|call
holdspeak/memory/engine.py|EmbeddingAdapter._endpoint_vectors|_remote_completion|call
holdspeak/meeting_session/deferred_bound.py|bound_bookmark_label_dispatch.call|generate_bookmark_label_with_context|call
holdspeak/meeting_session/deferred_bound.py|bound_auto_title_dispatch.call|generate_title|call
holdspeak/meeting_session/deferred_bound.py|bound_analysis_dispatch.call|analyze|call
holdspeak/meeting_session/intel_routed_children.py|IntelRoutedChildMixin._admitted_live_window.call|analyze|call
holdspeak/meeting_session/intel_routed_children.py|IntelRoutedChildMixin._admitted_bookmark_label.call|generate_bookmark_label_with_context|call
holdspeak/meeting_session/intel_routed_children.py|IntelRoutedChildMixin._admitted_auto_title.call|generate_title|call
holdspeak/meeting_session/transcribe_loop.py|TranscribeLoopMixin._transcribe_audio|transcribe|call
holdspeak/plugins/dictation/assembly.py|_try_build_runtime|MeshRelayRuntime|call
holdspeak/plugins/dictation/builtin/intent_router.py|IntentRouter.run|classify|call
holdspeak/plugins/dictation/builtin/project_rewriter.py|ProjectRewriter.run|rewrite|ref
holdspeak/plugins/dictation/builtin/project_rewriter.py|ProjectRewriter.run|rewrite|ref#2
holdspeak/plugins/dictation/builtin/project_rewriter.py|ProjectRewriter.run|rewrite|call
holdspeak/plugins/dictation/runtime.py|_default_factories._llama_factory|LlamaCppRuntime|call
holdspeak/plugins/dictation/runtime.py|_default_factories._openai_factory|OpenAICompatibleRuntime|call
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.classify|classify|call
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.rewrite|rewrite|ref
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.rewrite|rewrite|ref#2
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.rewrite|rewrite|call
holdspeak/plugins/dictation/runtime_llama_cpp.py|LlamaCppRuntime.classify|create_completion|call
holdspeak/plugins/dictation/runtime_llama_cpp.py|LlamaCppRuntime.rewrite|create_completion|call
holdspeak/plugins/dictation/runtime_llama_cpp.py|LlamaCppRuntime._resolve_factories|Llama|ref
holdspeak/plugins/dictation/runtime_mesh_relay.py|MeshRelayRuntime._run|run_prompt|call
holdspeak/plugins/dictation/runtime_mesh_relay.py|MeshRelayRuntime.load|MeshRelayIntel|call
holdspeak/plugins/dictation/runtime_openai_compatible.py|OpenAICompatibleRuntime.classify|chat.completions.create|call
holdspeak/plugins/dictation/runtime_openai_compatible.py|OpenAICompatibleRuntime.rewrite|chat.completions.create|call
holdspeak/plugins/dictation/runtime_openai_compatible.py|OpenAICompatibleRuntime.load|OpenAI|ref
holdspeak/services/agent_turn_service.py|_PromptToolProviderTransport.dispatch|run_prompt|call
holdspeak/services/agent_turn_service.py|AgentTurnService.dispatch_plugin|_chat_completion_text|call
holdspeak/project_doc_suggestions.py|suggest_project_doc_update|rewrite|ref
holdspeak/project_doc_suggestions.py|suggest_project_doc_update|rewrite|ref#2
holdspeak/project_doc_suggestions.py|suggest_project_doc_update|rewrite|call
holdspeak/runtime/dictation_capture.py|DictationCaptureMixin._transcribe_and_type|transcribe|call
holdspeak/runtime/dictation_capture.py|DictationCaptureMixin.transcribe_audio_admitted|transcribe|call
holdspeak/runtime/dictation_capture.py|DictationCaptureMixin.transcribe_audio_admitted|transcribe|call#2
holdspeak/runtime/wake_glue.py|WakeWordGlueMixin._transcribe_wake_admitted|transcribe|call
holdspeak/speech_session/provider.py|ProviderAdmission.dispatch_through|bound_target|call
holdspeak/speech_session/provider.py|ProviderAdmission.target|bound_target|call
holdspeak/speech_session/provider.py|ProviderAdmission.rewrite.call|rewrite|call
holdspeak/speech_session/provider.py|ProviderAdmission.punctuate.call|rewrite|call
holdspeak/speech_session/provider.py|_ClassifyLeg.run.call|classify|call
holdspeak/speech_session/provider.py|_RoutedSpeechAdapter.dispatch|run_prompt|call
holdspeak/speech_session/provider.py|_RoutedSpeechAdapter.dispatch|run_prompt|call#2
holdspeak/speech_session/provider.py|_mesh_bound|MeshRelayRuntime|call
holdspeak/speech_session/provider.py|AdmittedDictationRuntime.classify|classify|call
holdspeak/speech_session/provider.py|AdmittedDictationRuntime.rewrite|rewrite|call
holdspeak/speech_session/revision_target.py|rebind|OpenAICompatibleRuntime|call
holdspeak/speech_session/revision_target.py|bound_target|rebind|call
holdspeak/target_profile.py|apply_model_assisted_target|rewrite|ref
holdspeak/target_profile.py|apply_model_assisted_target|rewrite|ref#2
holdspeak/target_profile.py|apply_model_assisted_target|rewrite|call
holdspeak/transcribe.py|_MlxTranscriber._model_holder_get._run|get_model|call
holdspeak/transcribe.py|_MlxTranscriber._silent_audio_load._run|transcribe|call
holdspeak/transcribe.py|_MlxTranscriber.transcribe._run|transcribe|call
holdspeak/transcribe.py|_FasterWhisperTranscriber.transcribe|transcribe|call
holdspeak/transcribe.py|Transcriber._timed_transcribe|transcribe|call
holdspeak/transcribe.py|Transcriber._timed_transcribe._run|transcribe|call
holdspeak/web/routes/dictation/_helpers.py|_run_dictation_dry_run_text|build_pipeline|call
holdspeak/web/routes/system/voice.py|build_voice_router.api_transcribe|transcribe|call
holdspeak/web/routes/system/voice_stream.py|build_voice_stream_router.ws_dictation_stream|transcribe|call
""".strip().splitlines())


# This is deliberately a second census.  The model-shaped AST vocabulary above
# proves physical leaves; this list proves every product/service entrance into
# the one public admission waist has a proposed Phase-143 source owner too.
# ``dynamic:...`` means the current family already carries the exact typed
# capability in its frozen plan/offer and Story 02 must preserve that provenance
# rather than replace it with a made-up generic slug.
PRODUCT_RUNNER_ENTRANCES: dict[str, ProposedRoute] = {
    "holdspeak/kernel/mesh_local_runner.py|MeshLocalRunner.execute|call": ProposedRoute(
        "dynamic:mesh dispatch offer capability", "kernel.mesh_local_runner", "InferenceRunner worker-local admission",
    ),
    "holdspeak/services/ask_service.py|AskService._invoke|call": ProposedRoute(
        "internal.semantic_dispatch", "services.ask_service", "InferenceRunner service child; capability supplied by semantic caller",
    ),
    # HS-162-03: line shift 1553 → 1566 from branch additions.
    "holdspeak/services/inference_adoption_service.py|RoutedInferenceCoordinator.execute|call": ProposedRoute(
        "dynamic:frozen InferenceRoutePlan capability", "services.inference_adoption_service", "InferenceRunner controller-owned routed child",
    ),
    "holdspeak/speech_session/child.py|run_admitted_speech_child|call": ProposedRoute(
        "dynamic:SpeechSessionPlan capability", "speech_session.child", "InferenceRunner admitted child",
    ),
    # HS-146-07: the snapshot adapter's direct-dispatch fallback (the ask
    # template) when no calendar.snapshot_extract assignment exists.
    "holdspeak/services/calendar_snapshot_service.py|extract_via_router|call": ProposedRoute(
        "calendar.snapshot_extract", "services.calendar_snapshot_service", "InferenceRunner direct dispatch fallback (routed path preferred when assigned)",
    ),
    # HS-153-03/05: chat practice capabilities (guardrail + compaction).
    # HS-153-06: line numbers shifted by M1 redaction + response_format + robust parser additions.
    # Memory slice 1: one admitted child per embedding batch and per question.
    "holdspeak/memory/engine.py|RouterEmbedder._invoke|call": ProposedRoute(
        "memory.embed", "memory.engine", "InferenceRunner admitted child",
    ),
    # Memory slice 3: one admitted child per chunk the extract job reads.
    "holdspeak/memory/extract.py|RouterExtractor.extract|call": ProposedRoute(
        "memory.extract", "memory.extract", "InferenceRunner admitted child",
    ),
    # Memory slice 4: one admitted child per consolidate batch.
    "holdspeak/memory/consolidate.py|RouterConsolidator.consolidate|call": ProposedRoute(
        "memory.consolidate", "memory.consolidate", "InferenceRunner admitted child",
    ),
    # Memory slice 5: one admitted child per page.
    "holdspeak/memory/pages.py|RouterPageWriter.write|call": ProposedRoute(
        "memory.page", "memory.page", "InferenceRunner admitted child",
    ),
    "holdspeak/services/thread_practice.py|run_guardrail|call": ProposedRoute(
        "chat.guardrail", "services.thread_practice", "InferenceRunner admitted child",
    ),
    "holdspeak/services/thread_practice.py|run_compact|call": ProposedRoute(
        "chat.compact", "services.thread_practice", "InferenceRunner admitted child",
    ),
    # HS-162-03: model drafter for project update drafting.
    "holdspeak/services/project_update_service.py|ProjectUpdateService._draft_with_model|call": ProposedRoute(
        "project.update_draft", "services.project_update_service", "InferenceRunner admitted child",
    ),
    # HS-200-11: model drafter for the preparation brief, constrained to the
    # deterministic outline; refuses (never falls back) when the route is not ready.
    # HS-200-16: moved down five lines by `build_manifest` carrying each row's
    # `kind`; RE-ANCHORED, the site unchanged -- same file, same qualname, same
    # call, same capability and owner. The entrance count is still 9.
    "holdspeak/services/preparation_brief_service.py|PreparationBriefService._draft_with_model|call": ProposedRoute(
        "project.brief_prepare", "services.preparation_brief_service", "InferenceRunner admitted child",
    ),
}


# ``OperationRegistry.invoke`` sites whose operation name is not a constant, so
# ``_names_an_operation`` cannot tell them from a runner call by the AST alone.
# Each row is read by hand: the receiver is the operation registry and the
# name comes from the declared desk-operation table or is a pass-through of
# ``invoke``'s own ``name``. Pinned per site, like every row above: a NEW
# variable-name ``.invoke`` still fails the census until someone reads it.
OPERATION_CONTRACT_VARIABLE_SITES: dict[str, str] = {
    # PHILO-7-01: primitive detail resource reads through DESK_OPERATIONS.
    "holdspeak/mcp/resources.py|read_resource|call": "_ops().invoke(principal, DESK_OPERATIONS[(kind, 'get')], ...)",
    # PHILO-7-01: MCP primitive list/get read through DESK_OPERATIONS.
    "holdspeak/mcp/tools.py|_primitive_list|call": "ops().invoke(principal, _desk_operation(kind, 'list'), {})",
    "holdspeak/mcp/tools.py|_primitive_get|call": "ops().invoke(principal, _desk_operation(kind, 'get'), ...)",
    # PHILO-7-02: invoke_receipted calls the registry's own invoke with its name.
    "holdspeak/operations.py|OperationRegistry.invoke_receipted|call": "self.invoke(principal, name, args)",
    "holdspeak/operations.py|OperationRegistry.invoke_receipted|call#2": "self.invoke(principal, name, args, held=held)",
}


# AskService._invoke remains a shared internal helper whose runner entrance
# cannot truthfully name one capability. Sequence and Workflow enter through
# the frozen-route coordinator above. This second census records semantic callers.
# Refinement is one
# ``thought.interview`` capability whose result contract branches to either a
# next-question or terminal synthesis; synthesis is not separately routable.
def _service_factories(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Function names in one module that hand back an Ask/Recipe service.

    Discovery runs to a FIXPOINT: a function returning ANOTHER factory's result
    is itself a factory.  HS-200-41 lifted ``AskService(...)`` out of
    ``build_ask_router`` into ``build_ask_service``, so the router's own
    ``service()`` helper returns a factory call rather than the constructor.  A
    single non-transitive pass went blind to the product's only HTTP Ask
    entrance while its ``.ask(...)`` call was still sitting there -- the one
    thing this census must never do.
    """
    def _returned(call: ast.Call) -> str:
        # HS-200-45: ``runtime_service("<field>", <builder>)`` is the
        # composition root's typed lookup -- it hands back the hub's live
        # instance OR the builder's result, the same type either way. Seeing
        # through it keeps a factory that moved behind the root visible; the
        # MCP ask family's ``_service()`` did exactly that and this census
        # went blind to its ``.ask(...)`` call, the one thing it must never do.
        if (isinstance(call.func, ast.Name) and call.func.id == "runtime_service"
                and len(call.args) >= 2 and isinstance(call.args[1], ast.Name)):
            return call.args[1].id
        return call.func.id if isinstance(call.func, ast.Name) else ""

    returned_names: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            returned_names.setdefault(node.name, set()).update(
                _returned(value.value) for value in ast.walk(node)
                if isinstance(value, ast.Return) and isinstance(value.value, ast.Call)
                and isinstance(value.value.func, ast.Name)
            )
    ask_factories: set[str] = set()
    recipe_factories: set[str] = set()
    growing = True
    while growing:
        growing = False
        for name, returned in returned_names.items():
            if name not in ask_factories and ({"AskService"} | ask_factories) & returned:
                ask_factories.add(name)
                growing = True
            if name not in recipe_factories and ({"RecipeService"} | recipe_factories) & returned:
                recipe_factories.add(name)
                growing = True
    return ask_factories, recipe_factories


def _semantic_helper_calls(sources: dict[str, str] | None = None) -> list[str]:
    """Repository-wide Ask/Recipe semantic caller discovery.

    The service can arrive as a direct constructor, a local service variable, a
    factory returning the service, or RefinementCoordinator's injected
    ``_ask_factory``. Restricting this to today's transport files would make a
    new caller invisible precisely when it needs a capability decision.
    """
    sources = sources or {
        path.relative_to(one_path.REPO).as_posix(): path.read_text(encoding="utf-8")
        for path in one_path.PRODUCTION.rglob("*.py")
    }
    trees = {relative: ast.parse(source) for relative, source in sorted(sources.items())}
    # Repo-wide factory NAMES, so a caller that IMPORTS a factory is as visible
    # as one that defines it (HS-200-41).  ``/api/ask-tasks/{id}/resume``
    # imports ``build_ask_service`` from the ask transport and dispatches
    # through it under the saved invocation id; a per-file factory set never saw
    # that call, which is the exact shape -- a brand new semantic Ask entrance --
    # this census exists to force a capability decision about.  Fails closed: a
    # same-named non-factory import is a false positive that demands review,
    # never a silently missing row.
    factories = {relative: _service_factories(tree) for relative, tree in trees.items()}
    exported_ask = {name for local_ask, _ in factories.values() for name in local_ask}
    exported_recipe = {name for _, local_recipe in factories.values() for name in local_recipe}
    entries: list[Record] = []
    for relative, tree in trees.items():
        scopes = one_path._scope_index(tree)
        ask_aliases: set[str] = set()
        recipe_aliases: set[str] = set()
        ask_attributes: set[str] = set()
        recipe_attributes: set[str] = set()
        ask_factories, recipe_factories = (set(part) for part in factories[relative])
        imported = {
            alias.asname or alias.name
            for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        ask_factories |= imported & exported_ask
        recipe_factories |= imported & exported_recipe
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and isinstance(getattr(node, "value", None), ast.Call):
                value = node.value
                if isinstance(value.func, ast.Name) and value.func.id in {"AskService", "RecipeService"} | ask_factories | recipe_factories:
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    names = {target.id for target in targets if isinstance(target, ast.Name)}
                    attributes = {target.attr for target in targets if isinstance(target, ast.Attribute)}
                    if value.func.id in {"AskService"} | ask_factories:
                        ask_aliases.update(names)
                        ask_attributes.update(attributes)
                    else:
                        recipe_aliases.update(names)
                        recipe_attributes.update(attributes)
        for node in ast.walk(tree):
            if (
                relative.endswith("sequence_workflow_service.py")
                and isinstance(node, ast.Attribute)
                and node.attr == "_invoke"
            ):
                entries.append(Record(
                    relative, node.lineno, node.col_offset,
                    f"{scopes.get(id(node), '<module>')}|_invoke",
                ))
                continue
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            verb = node.func.attr
            receiver = node.func.value
            receiver_name = receiver.id if isinstance(receiver, ast.Name) else (
                receiver.func.id if isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name) else ""
            )
            direct_constructor = isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Name)
            receiver_attribute = receiver.attr if isinstance(receiver, ast.Attribute) else ""
            is_ask = verb == "ask" and (
                receiver_name in ask_factories | ask_aliases | {"AskService"}
                or receiver_attribute in ask_attributes
                or isinstance(receiver, ast.Call) and isinstance(receiver.func, ast.Attribute)
                and receiver.func.attr == "_ask_factory"
            )
            is_recipe = verb in {"run", "chat"} and (
                receiver_name in recipe_factories | recipe_aliases | {"RecipeService"}
                or receiver_attribute in recipe_attributes
                or direct_constructor and receiver_name == "RecipeService"
            )
            if is_ask or is_recipe:
                entries.append(Record(
                    relative, node.lineno, node.col_offset,
                    f"{scopes.get(id(node), '<module>')}|{verb}",
                ))
    return _line_free.ordinal_keys(entries)


SEMANTIC_HELPER_CALLERS: dict[str, ProposedRoute] = {
    "holdspeak/mcp/families/ask.py|dispatch|ask": ProposedRoute(
        "ask.answer", "mcp.families.ask", "AskService semantic caller",
    ),
        "holdspeak/services/refinement_coordinator.py|RefinementCoordinator._coordinate|ask": ProposedRoute(
        "thought.interview", "services.refinement_coordinator", "AskService semantic caller; question-or-synthesis result branch",
    ),
    "holdspeak/web/routes/primitives/ask.py|build_ask_router.api_ask|ask": ProposedRoute(
        "ask.answer", "web.routes.primitives.ask", "AskService semantic caller",
    ),
    # HS-200-41: the resume of a SAVED ask task.  Not a second Ask authority --
    # it imports ``build_ask_service`` and rides the SAME transport under the
    # invocation id the row already pinned (ruling B3), so the answer can be
    # claimed instead of paid for twice.  Same capability as the transport row
    # above, because it is the same operation reached a second way.
    "holdspeak/web/routes/projects.py|build_projects_router.api_resume_ask_task.dispatch|ask": ProposedRoute(
        "ask.answer", "web.routes.projects", "AskService semantic caller; saved-task resume through the ask transport",
    ),
    # PHILO-5-01/02: re-anchored after the operation contract moved dispatch
    # down; the recipe.run branch itself is unchanged. PHILO-7-01/02: moved
    # down again (852 -> 1008) with the desk operations; re-anchored, same
    # branch, same call.
    "holdspeak/mcp/tools.py|dispatch|run": ProposedRoute(
        "recipe.run", "mcp.tools", "RecipeService semantic caller",
    ),
    # HS-151-02: recipe.chat retired; mcp/tools.py:613 and recipes.py:115
    # no longer call RecipeService.chat — they return a 410 retired error.
    "holdspeak/web/routes/primitives/recipes.py|build_recipes_router.api_run_recipe|run": ProposedRoute(
        "recipe.run", "web.routes.primitives.recipes", "RecipeService semantic caller",
    ),
}


# Apple is a separate executable product, so its providers cannot truthfully be
# called "behind InferenceRunner" today. This narrow source census is intentional:
# it inventories every Swift `ILLMProvider.complete`/llama completion expression
# plus the OpenAI-compatible wire open, and makes each current bypass explicit.
SWIFT_SOURCES = one_path.REPO / "apple" / "Sources"


def _swift_physical_leaves(sources: dict[str, str] | None = None) -> list[str]:
    """Repository-wide Swift provider/open inventory, including fallback values."""
    sources = sources or {
        path.relative_to(one_path.REPO).as_posix(): path.read_text(encoding="utf-8")
        for path in SWIFT_SOURCES.rglob("*.swift")
    }
    entries: list[Record] = []
    for relative, source in sorted(sources.items()):
        for line_no, line in enumerate(source.splitlines(), start=1):
            marker = ""
            if ".complete(" in line:
                marker = "Swift.complete"
            elif "llm.getCompletion(" in line:
                marker = "LLM.getCompletion"
            elif relative.startswith("apple/Sources/Providers/Inference/") and ".data(for:" in line:
                marker = "InferenceProvider.URLSession.data"
            if marker:
                entries.append(Record(relative, line_no, 0, marker))
    return _line_free.ordinal_keys(entries)


SWIFT_PHYSICAL_LEAVES: dict[str, ProposedRoute] = {
    "apple/Sources/InferenceLlama/LlamaProvider.swift|LLM.getCompletion": ProposedRoute(
        "apple.local_completion", "apple.inference_llama", "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope",
    ),
    "apple/Sources/Providers/Inference/OpenAIEndpointProvider.swift|InferenceProvider.URLSession.data": ProposedRoute(
        "apple.endpoint_completion", "apple.providers.inference", "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope",
    ),
    "apple/Sources/Providers/Inference/StructuredOutput.swift|Swift.complete": ProposedRoute(
        "apple.structured_output", "apple.providers.inference", "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope",
    ),
    "apple/Sources/Providers/Desktop/MeshServeWorker.swift|Swift.complete": ProposedRoute(
        "apple.mesh_serve", "apple.providers.desktop", "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope",
    ),
    "apple/Sources/RuntimeCore/Companion/CoderAnswer.swift|Swift.complete": ProposedRoute(
        "apple.coder_answer", "apple.runtimecore.companion", "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope",
    ),
    "apple/Sources/RuntimeCore/Workbench/BlueprintInterpreter.swift|Swift.complete": ProposedRoute(
        "apple.workbench.blueprint", "apple.runtimecore.workbench", "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope",
    ),
    "apple/Sources/RuntimeCore/Workbench/WorkflowRunner.swift|Swift.complete": ProposedRoute(
        "apple.workbench.workflow", "apple.runtimecore.workbench", "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope",
    ),
}


def _group(route: ProposedRoute, keys: str) -> tuple[ProposedRoute, tuple[str, ...]]:
    return route, tuple(keys.strip().splitlines())


# Deliberately no path/target heuristic and no default: every Phase-131 AST site
# occurs in exactly one literal group. The set-equality test below makes an
# unreviewed site (including one in a familiar module) a failure.
EXPLICIT_ROUTE_GROUPS = (
    _group(ProposedRoute("agent.tool_turn", "services.agent_turn_service", "InferenceRunner ToolTurn transport or admitted compatibility leaf"), """
holdspeak/services/agent_turn_service.py|_PromptToolProviderTransport.dispatch|run_prompt|call
holdspeak/services/agent_turn_service.py|AgentTurnService.dispatch_plugin|_chat_completion_text|call
"""),
    _group(ProposedRoute("internal.inference.dispatch", "inference_targets", "InferenceRunner gateway/context-gated adapter"), """
holdspeak/inference_targets.py|local_pinned_meeting_intel|_local_pinned_engine|call
holdspeak/inference_targets.py|_local_pinned_engine|MeetingIntel|call
holdspeak/inference_targets.py|build_intel_for_revision|_engine_for_revision|call
holdspeak/inference_targets.py|_engine_for_revision|MeetingIntel|call
holdspeak/inference_targets.py|_engine_for_revision|local_pinned_meeting_intel|call
holdspeak/inference_targets.py|_engine_for_revision|build_meeting_intel_for_profile|call
"""),
    _group(ProposedRoute("internal.inference.dispatch", "intel.engine", "InferenceRunner gateway/context-gated adapter"), """
holdspeak/intel/engine.py|MeetingIntel._ensure_openai_client_loaded|OpenAI|call
holdspeak/intel/engine.py|MeetingIntel._ensure_local_model_loaded|Llama|call
holdspeak/intel/engine.py|MeetingIntel._ensure_runtime_loaded|_ensure_local_model_loaded|call
holdspeak/intel/engine.py|MeetingIntel._ensure_runtime_loaded|_ensure_openai_client_loaded|call
holdspeak/intel/engine.py|MeetingIntel._ensure_model_loaded|_ensure_runtime_loaded|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_text|create_chat_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_text|_remote_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_text|chat.completions.create|ref
holdspeak/intel/engine.py|MeetingIntel._chat_completion_stream|create_chat_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_stream|_remote_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_stream|chat.completions.create|ref
holdspeak/intel/engine.py|MeetingIntel._chat_completion_deltas|create_chat_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_deltas|_remote_completion|call
holdspeak/intel/engine.py|MeetingIntel._chat_completion_deltas|chat.completions.create|ref
holdspeak/intel/engine.py|MeetingIntel.run_prompt_stream|_chat_completion_deltas|call
holdspeak/intel/engine.py|MeetingIntel.run_prompt|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel.run_prompt_messages|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel._analyze_once|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel._analyze_stream|_chat_completion_stream|call
holdspeak/intel/engine.py|MeetingIntel.generate_title|_chat_completion_text|call
holdspeak/intel/engine.py|MeetingIntel.generate_bookmark_label_with_context|_chat_completion_text|call
"""),
    _group(ProposedRoute("internal.inference.dispatch", "intel.mesh_relay", "InferenceRunner gateway/context-gated adapter"), """
holdspeak/intel/mesh_relay.py|MeshRelayIntel._chat_completion_text|run_prompt|call
"""),
    _group(ProposedRoute("internal.inference.dispatch", "intel.providers", "InferenceRunner gateway/context-gated adapter"), """
holdspeak/intel/providers.py|_configured_engine|MeshRelayIntel|call
holdspeak/intel/providers.py|_configured_engine|MeetingIntel|call
holdspeak/intel/providers.py|configured_meeting_intel|_configured_engine|call
holdspeak/intel/providers.py|build_meeting_intel_for_profile|_profile_engine|call
holdspeak/intel/providers.py|_profile_engine|MeshRelayIntel|call
holdspeak/intel/providers.py|_profile_engine|configured_meeting_intel|call
holdspeak/intel/providers.py|_profile_engine|MeetingIntel|call
holdspeak/intel/providers.py|_profile_engine|MeetingIntel|call#2
holdspeak/intel/providers.py|_profile_engine|configured_meeting_intel|call#2
"""),
    _group(ProposedRoute("internal.inference.dispatch", "kernel.executor", "InferenceRunner gateway/context-gated adapter"), """
holdspeak/kernel/executor.py|<module>|_install_claim_issuer|call
holdspeak/kernel/executor.py|ExecutorPlane.claim|_issue_claim_witness|call
"""),
    _group(ProposedRoute("internal.inference.dispatch", "kernel.inference_runner", "InferenceRunner gateway/context-gated adapter"), """
holdspeak/kernel/inference_runner.py|InferenceRunner._attempt_stream|_issue_dispatch_context|call
holdspeak/kernel/inference_runner.py|InferenceRunner._attempt|_issue_dispatch_context|call
holdspeak/kernel/inference_runner.py|InferenceRunner.__init__|build_intel_for_revision|ref
"""),
    _group(ProposedRoute("internal.inference.dispatch", "kernel.prompt_adapter", "InferenceRunner gateway/context-gated adapter"), """
holdspeak/kernel/prompt_adapter.py|CanonicalPromptAdapter.dispatch|run_prompt|call
holdspeak/kernel/prompt_adapter.py|StreamingPromptAdapter.dispatch|run_prompt|call
"""),
    _group(ProposedRoute("internal.speech.runtime_assembly", "speech_session", "InferenceRunner context-gated adapter"), """
holdspeak/commands/dictation.py|_cmd_dry_run|build_pipeline|call
holdspeak/dictation_runner.py|run_pipeline_corrections_only|build_pipeline|call
holdspeak/dictation_runner.py|run_dictation_pipeline|build_pipeline|call
holdspeak/plugins/dictation/assembly.py|_try_build_runtime|MeshRelayRuntime|call
holdspeak/plugins/dictation/runtime.py|_default_factories._llama_factory|LlamaCppRuntime|call
holdspeak/plugins/dictation/runtime.py|_default_factories._openai_factory|OpenAICompatibleRuntime|call
holdspeak/plugins/dictation/runtime_llama_cpp.py|LlamaCppRuntime._resolve_factories|Llama|ref
holdspeak/plugins/dictation/runtime_mesh_relay.py|MeshRelayRuntime._run|run_prompt|call
holdspeak/plugins/dictation/runtime_mesh_relay.py|MeshRelayRuntime.load|MeshRelayIntel|call
holdspeak/plugins/dictation/runtime_openai_compatible.py|OpenAICompatibleRuntime.load|OpenAI|ref
holdspeak/speech_session/provider.py|ProviderAdmission.dispatch_through|bound_target|call
holdspeak/speech_session/provider.py|ProviderAdmission.target|bound_target|call
holdspeak/speech_session/provider.py|_mesh_bound|MeshRelayRuntime|call
holdspeak/speech_session/revision_target.py|rebind|OpenAICompatibleRuntime|call
holdspeak/speech_session/revision_target.py|bound_target|rebind|call
holdspeak/web/routes/dictation/_helpers.py|_run_dictation_dry_run_text|build_pipeline|call
"""),
    _group(ProposedRoute("meeting.auto_title", "meeting_session", "InferenceRunner admitted child"), """
holdspeak/meeting_session/deferred_bound.py|bound_auto_title_dispatch.call|generate_title|call
holdspeak/meeting_session/intel_routed_children.py|IntelRoutedChildMixin._admitted_auto_title.call|generate_title|call
"""),
    _group(ProposedRoute("meeting.bookmark_label", "meeting_session", "InferenceRunner admitted child"), """
holdspeak/meeting_session/deferred_bound.py|bound_bookmark_label_dispatch.call|generate_bookmark_label_with_context|call
holdspeak/meeting_session/intel_routed_children.py|IntelRoutedChildMixin._admitted_bookmark_label.call|generate_bookmark_label_with_context|call
"""),
    _group(ProposedRoute("meeting.deferred_analysis", "meeting_session", "InferenceRunner admitted child"), """
holdspeak/meeting_session/deferred_bound.py|bound_analysis_dispatch.call|analyze|call
"""),
    _group(ProposedRoute("meeting.live_analysis", "meeting_session", "InferenceRunner admitted child"), """
holdspeak/meeting_session/intel_routed_children.py|IntelRoutedChildMixin._admitted_live_window.call|analyze|call
"""),
    _group(ProposedRoute("project_doc.suggest_update", "project_doc_suggestions", "InferenceRunner admitted child"), """
holdspeak/project_doc_suggestions.py|suggest_project_doc_update|rewrite|ref
holdspeak/project_doc_suggestions.py|suggest_project_doc_update|rewrite|ref#2
holdspeak/project_doc_suggestions.py|suggest_project_doc_update|rewrite|call
"""),
    _group(ProposedRoute("speech.intent_classify", "speech_session", "InferenceRunner admitted child"), """
holdspeak/plugins/dictation/builtin/intent_router.py|IntentRouter.run|classify|call
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.classify|classify|call
holdspeak/plugins/dictation/runtime_llama_cpp.py|LlamaCppRuntime.classify|create_completion|call
holdspeak/plugins/dictation/runtime_openai_compatible.py|OpenAICompatibleRuntime.classify|chat.completions.create|call
holdspeak/speech_session/provider.py|_ClassifyLeg.run.call|classify|call
holdspeak/speech_session/provider.py|_RoutedSpeechAdapter.dispatch|run_prompt|call
holdspeak/speech_session/provider.py|AdmittedDictationRuntime.classify|classify|call
"""),
    _group(ProposedRoute("speech.preload", "speech_session.transcription", "InferenceRunner via TranscriptionAdmission"), """
holdspeak/transcribe.py|_MlxTranscriber._model_holder_get._run|get_model|call
"""),
    _group(ProposedRoute("speech.punctuate", "speech_session", "InferenceRunner admitted child"), """
holdspeak/speech_session/provider.py|ProviderAdmission.punctuate.call|rewrite|call
"""),
    _group(ProposedRoute("speech.rewrite", "speech_session", "InferenceRunner admitted child"), """
holdspeak/plugins/dictation/builtin/project_rewriter.py|ProjectRewriter.run|rewrite|ref
holdspeak/plugins/dictation/builtin/project_rewriter.py|ProjectRewriter.run|rewrite|ref#2
holdspeak/plugins/dictation/builtin/project_rewriter.py|ProjectRewriter.run|rewrite|call
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.rewrite|rewrite|ref
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.rewrite|rewrite|ref#2
holdspeak/plugins/dictation/runtime_counters.py|CountingRuntime.rewrite|rewrite|call
holdspeak/plugins/dictation/runtime_llama_cpp.py|LlamaCppRuntime.rewrite|create_completion|call
holdspeak/plugins/dictation/runtime_openai_compatible.py|OpenAICompatibleRuntime.rewrite|chat.completions.create|call
holdspeak/speech_session/provider.py|ProviderAdmission.rewrite.call|rewrite|call
holdspeak/speech_session/provider.py|_RoutedSpeechAdapter.dispatch|run_prompt|call#2
holdspeak/speech_session/provider.py|AdmittedDictationRuntime.rewrite|rewrite|call
"""),
    _group(ProposedRoute("speech.target_classify", "target_profile", "InferenceRunner admitted child"), """
holdspeak/target_profile.py|apply_model_assisted_target|rewrite|ref
holdspeak/target_profile.py|apply_model_assisted_target|rewrite|ref#2
holdspeak/target_profile.py|apply_model_assisted_target|rewrite|call
"""),
    # Memory slice 1: the memory.embed adapter's two physical leaves (the
    # embedding-mode llama.cpp load and the endpoint client).  Both run only
    # inside EmbeddingAdapter.dispatch, for an admitted memory.embed child.
    _group(ProposedRoute("memory.embed", "memory.engine", "InferenceRunner admitted child"), """
holdspeak/memory/engine.py|EmbeddingAdapter._local_model|Llama|call
holdspeak/memory/engine.py|EmbeddingAdapter._endpoint_vectors|_ensure_openai_client_loaded|call
holdspeak/memory/engine.py|EmbeddingAdapter._endpoint_vectors|_remote_completion|call
"""),
    _group(ProposedRoute("speech.transcribe", "speech_session.transcription", "InferenceRunner via TranscriptionAdmission"), """
holdspeak/main.py|_run_meeting_mode|transcribe|call
holdspeak/main.py|_run_meeting_mode|transcribe|call#2
holdspeak/meeting_import.py|_transcribe_import_windows|transcribe|call
holdspeak/meeting_session/transcribe_loop.py|TranscribeLoopMixin._transcribe_audio|transcribe|call
holdspeak/runtime/dictation_capture.py|DictationCaptureMixin._transcribe_and_type|transcribe|call
holdspeak/runtime/dictation_capture.py|DictationCaptureMixin.transcribe_audio_admitted|transcribe|call
holdspeak/runtime/dictation_capture.py|DictationCaptureMixin.transcribe_audio_admitted|transcribe|call#2
holdspeak/runtime/wake_glue.py|WakeWordGlueMixin._transcribe_wake_admitted|transcribe|call
holdspeak/transcribe.py|_MlxTranscriber._silent_audio_load._run|transcribe|call
holdspeak/transcribe.py|_MlxTranscriber.transcribe._run|transcribe|call
holdspeak/transcribe.py|_FasterWhisperTranscriber.transcribe|transcribe|call
holdspeak/transcribe.py|Transcriber._timed_transcribe|transcribe|call
holdspeak/transcribe.py|Transcriber._timed_transcribe._run|transcribe|call
holdspeak/web/routes/system/voice.py|build_voice_router.api_transcribe|transcribe|call
holdspeak/web/routes/system/voice_stream.py|build_voice_stream_router.ws_dictation_stream|transcribe|call
"""),
)

PROPOSED_ROUTES = {
    key: route for route, keys in EXPLICIT_ROUTE_GROUPS for key in keys
}


# Direct provider/Whisper model work, including the first-class SDK callback
# references that perform the eventual request.  The route string is deliberately
# literal: the baseline found zero legacy bypasses.
PHYSICAL_LEAF_KEYS = frozenset({
    key for key in EXPECTED_CALL_SITES
    if any(token in key for token in (
        "|create_chat_completion|", "|chat.completions.create|", "|create_completion|",
        "|MeshRelayIntel._chat_completion_text|run_prompt|", "|MeshRelayRuntime._run|run_prompt|",
        "|get_model|", "_silent_audio_load._run|transcribe|",
        "|_MlxTranscriber.transcribe._run|transcribe|", "|_FasterWhisperTranscriber.transcribe|transcribe|",
    ))
})


def test_phase143_call_site_fixture_is_complete_and_fail_closed() -> None:
    live = set(_site_keys())
    assert live == EXPECTED_CALL_SITES, (
        "Phase 143 inference/capability census changed; register every new site "
        "with exactly one proposed capability and source owner.\n"
        f"unregistered={sorted(live - EXPECTED_CALL_SITES)}\n"
        f"stale={sorted(EXPECTED_CALL_SITES - live)}"
    )
    # HS-146-07 adds the one vision prompt leaf (run_prompt_messages).
    # HS-151-02/D3: streaming seam adds _chat_completion_deltas (3 sites)
    # and _attempt_stream (1 site); line shifts update 6 existing sites.
    # HS-151-04: +1 StreamingPromptAdapter.dispatch run_prompt fallback, +1 line shift
    # Memory slice 1: +3, the memory.embed adapter's local load, its endpoint
    # client and the engine's egress-warranted remote call.
    assert len(live) == 112


def test_phase143_every_product_runner_entrance_has_one_owner() -> None:
    every = set(_runner_entrances())
    pinned = set(OPERATION_CONTRACT_VARIABLE_SITES)
    assert pinned <= every, (
        "a pinned operation-contract site moved or is gone; re-read it and "
        f"re-anchor: stale={sorted(pinned - every)}"
    )
    live = every - pinned
    expected = set(PRODUCT_RUNNER_ENTRANCES)
    assert live == expected, (
        "Phase 143 runner-entrance census changed; register the new public "
        "InferenceRunner.invoke caller with capability provenance and source owner.\n"
        f"unregistered={sorted(live - expected)}\n"
        f"stale={sorted(expected - live)}"
    )
    for proposed in PRODUCT_RUNNER_ENTRANCES.values():
        assert proposed.capability_id
        assert proposed.source_owner
        assert proposed.admission == "InferenceRunner admitted child" or "InferenceRunner" in proposed.admission


def test_phase143_shared_helpers_have_semantic_callers() -> None:
    live = set(_semantic_helper_calls())
    assert live == set(SEMANTIC_HELPER_CALLERS), (
        "shared Ask/Recipe helper callers changed; classify the public semantic "
        "operation rather than assigning the helper one false capability.\n"
        f"unregistered={sorted(live - set(SEMANTIC_HELPER_CALLERS))}\n"
        f"stale={sorted(set(SEMANTIC_HELPER_CALLERS) - live)}"
    )
    assert SEMANTIC_HELPER_CALLERS[
        "holdspeak/services/refinement_coordinator.py|RefinementCoordinator._coordinate|ask"
    ].capability_id == "thought.interview"

    architecture = (one_path.REPO / (
        "pm/roadmap/holdspeak/phase-143-intelligence-router/assets/architecture-contract.md"
    )).read_text(encoding="utf-8")
    repository = (one_path.REPO / (
        "pm/roadmap/holdspeak/phase-143-intelligence-router/assets/repository-census.md"
    )).read_text(encoding="utf-8")
    bootstrap_row = next(line for line in architecture.splitlines() if line.startswith("| Thoughts & notes |"))
    pointer_row = next(line for line in repository.splitlines() if line.startswith("| Thoughts pointer |"))
    assert "`thought.synthesis`" not in bootstrap_row
    assert "`thought.synthesis`" not in pointer_row


def test_phase143_semantic_census_rejects_new_ask_or_recipe_caller() -> None:
    mutated = _semantic_helper_calls({"holdspeak/rogue_semantic.py": """
from holdspeak.services.ask_service import AskService
from holdspeak.services.recipe_service import RecipeService
class Rogue:
    def __init__(self):
        self.ask_service = AskService(db)
        self.recipe_service = RecipeService(db)
    def go(self):
        self.ask_service.ask(principal, "unregistered")
        self.recipe_service.chat(principal, "recipe", question="unregistered")
"""})
    assert set(mutated) == {
        "holdspeak/rogue_semantic.py|Rogue.go|ask",
        "holdspeak/rogue_semantic.py|Rogue.go|chat",
    }
    assert not set(mutated) <= set(SEMANTIC_HELPER_CALLERS)


def test_phase143_swift_physical_leaves_remain_explicit_held_scope() -> None:
    """The owner descope holds the seven leaves in view; it does not erase them."""
    live = set(_swift_physical_leaves())
    assert live == set(SWIFT_PHYSICAL_LEAVES), (
        "Apple physical inference inventory changed; name its capability, source "
        "owner, and HELD scope status.\n"
        f"unregistered={sorted(live - set(SWIFT_PHYSICAL_LEAVES))}\n"
        f"stale={sorted(set(SWIFT_PHYSICAL_LEAVES) - live)}"
    )
    held = "HELD — owner ruling 2026-08-25: Swift/Apple is out of Story 143-10 scope"
    assert all(route.admission == held for route in SWIFT_PHYSICAL_LEAVES.values())
    assert len(SWIFT_PHYSICAL_LEAVES) == 7
    workflow = SWIFT_PHYSICAL_LEAVES[
        "apple/Sources/RuntimeCore/Workbench/WorkflowRunner.swift|Swift.complete"
    ]
    assert workflow.source_owner == "apple.runtimecore.workbench"


def test_phase143_swift_census_rejects_fallback_or_new_provider_open() -> None:
    mutated = _swift_physical_leaves({
        "apple/Sources/Providers/Inference/RogueProvider.swift": """
let output = try await fallback.complete(prompt: prompt)
let data = try await URLSession.shared.data(for: request)
""",
    })
    assert set(mutated) == {
        "apple/Sources/Providers/Inference/RogueProvider.swift|Swift.complete",
        "apple/Sources/Providers/Inference/RogueProvider.swift|InferenceProvider.URLSession.data",
    }
    assert not set(mutated) <= set(SWIFT_PHYSICAL_LEAVES)


def test_phase143_every_censused_site_has_one_capability_and_source_owner() -> None:
    live = set(_site_keys())
    declared_keys = [key for _, keys in EXPLICIT_ROUTE_GROUPS for key in keys]
    assert set(PROPOSED_ROUTES) == live == EXPECTED_CALL_SITES
    assert len(declared_keys) == len(set(declared_keys)), "a call site has two proposed routes"
    for proposed in PROPOSED_ROUTES.values():
        assert proposed.capability_id
        assert proposed.source_owner
        assert proposed.admission
        # Phase 143's canonical registry owns stable ASCII IDs; internal rows are
        # intentionally non-assignable implementation capabilities.
        assert proposed.capability_id.replace(".", "").replace("_", "").isalnum()


def test_phase143_physical_leaves_have_no_legacy_bypass() -> None:
    sites = _site_keys()
    assert PHYSICAL_LEAF_KEYS <= set(sites)
    assert all(one_path._bucket(sites[key]) == "allowlist" for key in PHYSICAL_LEAF_KEYS)
    assert all("InferenceRunner" in PROPOSED_ROUTES[key].admission for key in PHYSICAL_LEAF_KEYS)
    assert one_path.NAMED_FINDINGS == {}
    assert one_path.BLOCKING_FAMILIES == frozenset()


def test_line_free_keys_ignore_line_movement_and_name_a_second_site() -> None:
    """Mutation: an edit above a site changes no key; a second same site adds one."""
    source = """
class Rogue:
    def go(self):
        self.ask_service = AskService(db)
        self.ask_service.ask(principal, "one")
"""
    one = _semantic_helper_calls({"holdspeak/rogue.py": source})
    moved = _semantic_helper_calls({"holdspeak/rogue.py": "\n\n# an edit above\n" + source})
    two = _semantic_helper_calls({
        "holdspeak/rogue.py": source + '        self.ask_service.ask(principal, "two")\n',
    })
    assert one == moved == ["holdspeak/rogue.py|Rogue.go|ask"]
    assert two == ["holdspeak/rogue.py|Rogue.go|ask", "holdspeak/rogue.py|Rogue.go|ask#2"]
