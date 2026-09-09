"""HS-63-06: transcriber construction is serialized.

The live closeout caught the second pre-existing production bug of the
phase: the boot-time warmup thread and the first meeting/dictation both
call `_ensure_transcriber_loaded`, and the unlocked check-then-construct
let TWO `_MlxTranscriber` instances exist. mlx_whisper caches the loaded
model per process, bound to the first instance's pinned thread, so the
second instance's transcribe died with the process-fatal "no Stream(gpu,
N) in current thread" (the Phase-60 crash class, one level up). This lock
proves construction is single-flight under a thundering herd.
"""
from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

import holdspeak.runtime.transcriber_state as transcriber_state
from holdspeak.transcribe import resolve_backend_or_raw
from holdspeak.web_runtime import WebRuntime


class SlowFakeTranscriber:
    """A double that stores what the REAL `Transcriber` stores.

    HS-200-05: the original double kept `backend` verbatim while the real class
    keeps `_resolve_backend(backend)`. That one-word difference is why this file
    stayed green for months across a bug that crashed the owner's hub on every
    utterance — the double could never reproduce the "mlx" vs "auto" asymmetry
    between the boot warm and a legacy dictation. A double that lies about the
    field a check reads proves nothing about the check.
    """

    def __init__(self, *, model_name, backend, language, built=None, delay=0.0):
        if delay:
            time.sleep(delay)  # widen the race window
        if built is not None:
            built.append(self)
        # Phase B reuses only an exact frozen model/backend/language
        # triple, so the test double must expose all three fields.
        self.model_name = model_name
        self.backend = resolve_backend_or_raw(backend)
        self.language = language


def _runtime(monkeypatch, built, *, backend="auto", delay=0.0):
    """A bare WebRuntime wired to the double, with `config.model.backend`."""

    def _factory(*, model_name, backend, language):
        return SlowFakeTranscriber(
            model_name=model_name,
            backend=backend,
            language=language,
            built=built,
            delay=delay,
        )

    monkeypatch.setattr(transcriber_state, "Transcriber", _factory)

    rt = WebRuntime.__new__(WebRuntime)
    rt.config = SimpleNamespace(
        model=SimpleNamespace(name="base", backend=backend, language="auto")
    )
    rt.transcriber = None
    rt._transcriber_init_lock = threading.Lock()
    rt._set_transcription_status = lambda *a, **k: None
    return rt


def test_concurrent_ensure_builds_exactly_one_transcriber(monkeypatch):
    built = []

    def _factory(*, model_name, backend, language):
        return SlowFakeTranscriber(
            model_name=model_name,
            backend=backend,
            language=language,
            built=built,
            delay=0.05,
        )

    monkeypatch.setattr(transcriber_state, "Transcriber", _factory)

    rt = WebRuntime.__new__(WebRuntime)
    rt.config = SimpleNamespace(model=SimpleNamespace(name="base", backend="auto", language="auto"))
    rt.transcriber = None
    rt._transcriber_init_lock = threading.Lock()
    rt._set_transcription_status = lambda *a, **k: None

    threads = [threading.Thread(target=rt._ensure_transcriber_loaded) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(built) == 1, (
        f"{len(built)} transcribers built under contention — two instances is "
        "a process-fatal MLX cross-thread crash in production"
    )
    assert rt.transcriber is built[0]


def test_boot_warm_is_reused_by_a_legacy_dictation(monkeypatch):
    """HS-200-05: the crash's actual trigger, in two calls.

    The boot warm is ROUTED and passes the resolved engine name it read from the
    speech material (`"mlx"`). A legacy dictation — the owner's desk, which lacks
    the `thoughts-writing-route-assignments` migration and so has no frozen route
    bundle — passes nothing and falls back to `config.model.backend` (`"auto"`).
    Those name the same engine. Before this fix the reuse check compared the
    stored, RESOLVED "mlx" against the requested, RAW "auto", never matched, and
    built a second `_MlxTranscriber` on a second pinned thread FOR EVERY
    UTTERANCE. Its "load" was a process-level mlx_whisper cache hit, so it
    inherited lazy arrays owned by the first thread's stream, and the first eval
    killed the hub with an uncatchable C++ throw.
    """
    built = []
    rt = _runtime(monkeypatch, built, backend="auto")

    warm = rt._ensure_transcriber_loaded(
        model_name="base", backend="mlx", language="auto"
    )
    dictation = rt._ensure_transcriber_loaded()

    assert len(built) == 1, (
        f"{len(built)} transcribers built for one engine — a second instance in "
        "one process is a process-fatal MLX cross-thread crash in production"
    )
    assert dictation is warm


def test_every_mlx_transcriber_shares_one_pinned_thread():
    """HS-200-05: the structural guard, independent of how instances arise.

    Everything mlx_whisper caches (`ModelHolder`, `mel_filters`, the lazy arrays
    on a cached model) is PROCESS-level, so a per-instance pinned thread cannot
    hold the invariant no matter how careful the construction path is. One
    executor per process is what makes the crash impossible — including through
    construction sites no lock covers (`web/routes/meeting_import.py`).
    """
    from holdspeak.transcribe import _mlx_executor

    assert _mlx_executor() is _mlx_executor()

    mlx = pytest.importorskip("mlx.core")
    pytest.importorskip("mlx_whisper")
    assert mlx is not None

    from holdspeak.transcribe import _MlxTranscriber

    a = _MlxTranscriber(model_name="base", language="auto")
    b = _MlxTranscriber(model_name="base", language="auto")
    assert a._mlx_thread is b._mlx_thread is _mlx_executor(), (
        "two transcribers pinned to different threads — the crash class is back"
    )
