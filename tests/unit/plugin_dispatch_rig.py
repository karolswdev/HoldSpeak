"""What a TEST needs to hold an admitted plugin dispatch handle (HS-131-14).

The point of the story is that a plugin cannot reach a model without a handle the
HOST minted over an engine the runner built for a claimed child. A rig that forged
one would make that claim true of production and false of its proof, so this does
the real thing: it takes a genuine
:class:`~holdspeak.kernel.dispatch_context.DispatchContext` from
:mod:`tests.unit.admitted_context` (a real kernel submit/decide/claim), binds it to
a stub engine exactly as ``InferenceRunner._attempt`` binds it to the real one, and
mints the handle through the host's own private issuer.

What is stubbed is only the PROVIDER: ``StubEngine._chat_completion_text`` stands in
for the completion leaf, so a plugin test asserts parsing and refusal behaviour
without a model, while every authority check on the path is the real one.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace
from typing import Any, Callable, Optional

from holdspeak.kernel.dispatch_context import bind_dispatch_context, release_dispatch_context
from holdspeak.plugins.intelligence import (
    PLUGIN_DISPATCH_KEY,
    PluginDispatch,
    _issue_plugin_dispatch,
)
from tests.unit.admitted_context import admitted_context


def frozen_revision(rid: str = "dep_plugin", destination: str = "plugin-destination") -> Any:
    """A frozen-revision stand-in: the context mint reads these two fields."""
    return SimpleNamespace(id=rid, destination_id=destination)


class StubEngine:
    """The engine an admitted child built: one chat seam and a call log."""

    def __init__(self, respond: Any = "") -> None:
        self._respond = respond
        self.calls: list[dict[str, Any]] = []

    def _chat_completion_text(
        self, messages: Any, *, temperature: float, max_tokens: int
    ) -> Any:
        self.calls.append(
            {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        )
        if callable(self._respond):
            return self._respond(messages, temperature=temperature, max_tokens=max_tokens)
        return self._respond


class DeafEngine:
    """An engine with no chat seam at all (the incompatible case)."""

    def analyze(self, *_args: Any, **_kwargs: Any) -> Any:  # pragma: no cover - never called
        raise AssertionError("an incompatible engine must never be dispatched on")


def admitted_engine(
    respond: Any = "",
    *,
    rid: str = "dep_plugin",
    destination: str = "plugin-destination",
    attempt: int = 1,
    engine: Any = None,
) -> tuple[Any, Any]:
    """An engine carrying a REAL issued context, as the runner leaves it."""
    revision = frozen_revision(rid, destination)
    context = admitted_context(revision=revision, attempt_ordinal=attempt)
    built = StubEngine(respond) if engine is None else engine
    bind_dispatch_context(built, context)
    return built, context


def admitted_dispatch(
    respond: Any = "",
    *,
    cancellation: Optional[threading.Event] = None,
    rid: str = "dep_plugin",
    destination: str = "plugin-destination",
    attempt: int = 1,
    engine: Any = None,
) -> tuple[PluginDispatch, Any, Any]:
    """``(handle, engine, context)`` for one admitted plugin run."""
    built, context = admitted_engine(
        respond, rid=rid, destination=destination, attempt=attempt, engine=engine
    )
    handle = _issue_plugin_dispatch(engine=built, cancellation=cancellation)
    return handle, built, context


def unbind(engine: Any, context: Any) -> None:
    """End the attempt exactly as the runner's ``finally`` does."""
    release_dispatch_context(engine, context)


class BoundPlugin:
    """A plugin plus the admitted handle its invocation carries.

    ``run(context)`` is the plugin's own signature: the handle goes in under the
    reserved key, which is precisely what :class:`~holdspeak.plugins.host.PluginHost`
    does for one worker invocation.
    """

    def __init__(self, plugin: Any, respond: Any = "", **kwargs: Any) -> None:
        self.plugin = plugin
        self.dispatch, self.engine, self.context = admitted_dispatch(respond, **kwargs)

    def run(self, context: dict[str, Any]) -> Any:
        return self.plugin.run({**context, PLUGIN_DISPATCH_KEY: self.dispatch})


def intel_plugin(plugin: Any, respond: Any = "", **kwargs: Any) -> BoundPlugin:
    """The one-liner every builtin's test suite uses instead of a provider stub."""
    return BoundPlugin(plugin, respond, **kwargs)


def with_dispatch(context: dict[str, Any], dispatch: Any) -> dict[str, Any]:
    """A run context carrying ``dispatch`` (including a deliberately bad one)."""
    return {**context, PLUGIN_DISPATCH_KEY: dispatch}


__all__ = [
    "BoundPlugin",
    "DeafEngine",
    "StubEngine",
    "admitted_dispatch",
    "admitted_engine",
    "frozen_revision",
    "intel_plugin",
    "unbind",
    "with_dispatch",
]
