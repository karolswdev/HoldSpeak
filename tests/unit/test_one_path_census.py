"""HS-131-10, reduced 2026-11-09 (fences diet): one admission path for model execution.

An ``ast`` walk over production ``holdspeak/**`` finds every model-execution-shaped
form: SDK client construction, completion opens (also the SDK's
``client.chat.completions.create`` receiver chain), local model loads, engine
factories, Whisper leaves, the kernel's admission mints, and the first-class
callable forms (``asyncio.to_thread(intel.run_prompt, ...)``, ``getattr(x, "run_prompt")``).

The properties, with no hand-kept site list:

* no route, command or domain service builds an engine, constructs an SDK client,
  opens an SDK completion or loads a model; it reaches a model only through an
  admitted seam;
* the admission mints live only in the kernel (the claim witness in
  ``kernel/executor.py``, the dispatch context in ``kernel/inference_runner.py``),
  and the retired public mints never come back;
* every ``build_pipeline`` call passes an admission;
* the legacy uncontextual marker is passed nowhere and satisfies no validator.

The per-scope allowlist, seam list and findings ledger are parked in
``tests/_parked/fences/test_one_path_census.py`` (shape: each legitimate move
needed an entry).
"""
from __future__ import annotations

import ast
import functools
from pathlib import Path
from typing import Iterator, NamedTuple

import pytest

from tests import _tree

REPO = Path(__file__).resolve().parents[2]
PRODUCTION = REPO / "holdspeak"

# --------------------------------------------------------------- the vocabulary
# The COMPLETE physical vocabulary (Sol Amendment 2). Deliberately narrower than
# general effect lint: this protects model execution, not all network code.
VOCABULARY: dict[str, frozenset[str]] = {
    "provider-completion": frozenset({
        "run_prompt", "_chat_completion_text", "_chat_completion_stream", "_chat_completion_deltas",
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


def sites_in_source(relative: str, source: str, tree: ast.AST | None = None) -> Iterator[Site]:
    """Classify one module's source (a real file, or a synthetic mutation)."""
    tree = ast.parse(source) if tree is None else tree
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


#: A file whose text names none of these words holds no site (every target is
#: one of DANGEROUS, written as a name, an attribute, an import or a getattr
#: literal), so the walker skips it. ``create`` alone is too common; the SDK
#: chain is found by its other words.
_PREFILTER = frozenset(
    part for name in DANGEROUS for part in name.split(".") if part != "create"
)


def _may_hold_a_site(text: str) -> bool:
    return any(word in text for word in _PREFILTER)


@functools.lru_cache(maxsize=1)
def _census() -> tuple[Site, ...]:
    sites: list[Site] = []
    for path in _tree.python_files("holdspeak"):
        text = _tree.text_of(path)
        if not _may_hold_a_site(text):
            continue
        relative = path.relative_to(_tree.ROOT).as_posix()
        sites.extend(sites_in_source(relative, text, _tree.ast_of(path)))
    return tuple(sorted(sites))


def census() -> list[Site]:
    """Every model-execution site in production ``holdspeak/`` (parked code included, as before)."""
    return list(_census())


# ------------------------------------------------------------------ the properties

PRODUCT_SURFACES = ("holdspeak/web/", "holdspeak/services/", "holdspeak/commands/")
BUILDING_FAMILIES = frozenset({
    "sdk-construction", "sdk-completion-create", "local-model-load", "admission-mint",
    "engine-factory",
})


def test_no_route_command_or_service_builds_an_engine() -> None:
    """A product surface reaches a model through an admitted seam, never by building one."""
    offenders = [
        site.named()
        for site in census()
        if site.path.startswith(PRODUCT_SURFACES)
        and site.family in BUILDING_FAMILIES
        and site.target != "build_pipeline"  # checked below: it must carry its admission
    ]
    assert offenders == [], "a product surface builds an engine:\n  " + "\n  ".join(offenders)


def test_the_admission_mints_live_only_in_the_kernel() -> None:
    sites = census()
    retired = [site for site in sites if site.target in {"mint_claim_witness", "issue_dispatch_context"}]
    assert retired == [], f"a retired public mint reappeared: {retired}"
    homes = {
        "_install_claim_issuer": {"holdspeak/kernel/executor.py"},
        "_issue_claim_witness": {"holdspeak/kernel/executor.py"},
        "_issue_dispatch_context": {"holdspeak/kernel/inference_runner.py"},
    }
    for target, home in homes.items():
        found = {site.path for site in sites if site.target == target}
        assert found == home, f"{target} is reached from {sorted(found)}"


def test_every_build_pipeline_call_carries_an_admission() -> None:
    calls = 0
    for path in _tree.python_files("holdspeak", exclude=("_parked",)):
        for node in _tree.walk(path):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "build_pipeline"):
                continue
            calls += 1
            keywords = {keyword.arg: keyword.value for keyword in node.keywords}
            where = f"{path.relative_to(_tree.ROOT)}:{node.lineno}"
            assert "admission" in keywords, f"{where}: build_pipeline lost its admission"
            assert not (isinstance(keywords["admission"], ast.Constant)
                        and keywords["admission"].value is None), f"{where}: admission=None"
    assert calls, "the census found no build_pipeline call at all"


def test_the_legacy_marker_is_passed_nowhere() -> None:
    passed: list[str] = []
    for path in _tree.python_files("holdspeak"):
        relative = path.relative_to(_tree.ROOT).as_posix()
        if relative == "holdspeak/kernel/dispatch_context.py" or "LEGACY_UNCONTEXTUAL" not in _tree.text_of(path):
            continue
        for node in _tree.walk(path):
            if isinstance(node, ast.Call):
                values = list(node.args) + [keyword.value for keyword in node.keywords]
                if any(isinstance(v, ast.Name) and v.id == "LEGACY_UNCONTEXTUAL" for v in values):
                    passed.append(f"{relative}:{node.lineno}")
    assert passed == [], f"the legacy uncontextual marker is passed at {passed}"


# --------------------------------------------------- the walker sees every door form

SYNTHETIC_FIRST_CLASS_CALLABLE = '''
"""A synthetic product module: the CALLABLE-REFERENCE door (Sol Amendment 2)."""
import asyncio


async def summarize_note(intel, text: str) -> str:
    chat_fn = intel._chat_completion_text
    return await asyncio.to_thread(intel.run_prompt, system_prompt="s", user_prompt=text)
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



