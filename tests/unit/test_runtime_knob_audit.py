"""HS-25-06: audit two config knobs that were suspected of silently no-op'ing.

Outcome of the audit: both are real and reachable, so these tests pin their
behavior rather than removing the knobs.

- `eviction_idle_seconds` — `MlxRuntime._maybe_evict` actually unloads the model
  when set and idle; plumbed config -> assembly -> adapter.
- `intel_cloud_store` — forwarded to the cloud client as `store=True`. Whether a
  given endpoint *honors* it is advisory (documented in the meeting guide).
"""

from __future__ import annotations

import time
from types import SimpleNamespace

import holdspeak.intel as intel_module
from holdspeak.intel import MeetingIntel
from holdspeak.plugins.dictation.runtime_mlx import MlxRuntime


# --- eviction_idle_seconds ---------------------------------------------------


def _mlx(eviction_idle_seconds: int) -> MlxRuntime:
    # Seams keep this import-free (no real mlx-lm / outlines needed).
    return MlxRuntime(
        eviction_idle_seconds=eviction_idle_seconds,
        load_fn=lambda model: ("model", "tok"),
        generator_factory=lambda m, t, s: (lambda prompt, max_tokens=128: "{}"),
    )


def test_eviction_fires_after_idle_when_enabled():
    rt = _mlx(eviction_idle_seconds=10)
    rt._loaded = ("model", "tok")
    rt._last_used = time.monotonic() - 100  # idle well beyond the threshold
    rt._maybe_evict()
    assert rt._loaded is None  # model unloaded


def test_eviction_does_not_fire_within_idle_window():
    rt = _mlx(eviction_idle_seconds=10)
    rt._loaded = ("model", "tok")
    rt._last_used = time.monotonic()  # just used
    rt._maybe_evict()
    assert rt._loaded is not None


def test_eviction_disabled_never_evicts():
    rt = _mlx(eviction_idle_seconds=0)  # the default
    rt._loaded = ("model", "tok")
    rt._last_used = time.monotonic() - 10_000
    rt._maybe_evict()
    assert rt._loaded is not None  # disabled => model stays resident


# --- intel_cloud_store -------------------------------------------------------


def _fake_openai(monkeypatch, calls: list[dict]):
    class _FakeCompletions:
        def create(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))]
            )

    class _FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=_FakeCompletions())

    monkeypatch.setattr(intel_module, "OpenAI", _FakeOpenAI)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")


def test_cloud_store_true_is_forwarded(monkeypatch):
    calls: list[dict] = []
    _fake_openai(monkeypatch, calls)
    MeetingIntel(provider="cloud", cloud_store=True).analyze("hi", stream=False)
    assert calls and calls[0].get("store") is True


def test_cloud_store_false_is_omitted(monkeypatch):
    calls: list[dict] = []
    _fake_openai(monkeypatch, calls)
    MeetingIntel(provider="cloud", cloud_store=False).analyze("hi", stream=False)
    assert calls and "store" not in calls[0]
