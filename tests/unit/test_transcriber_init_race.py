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

import holdspeak.runtime.transcriber_state as transcriber_state
from holdspeak.web_runtime import WebRuntime


def test_concurrent_ensure_builds_exactly_one_transcriber(monkeypatch):
    built = []

    class SlowFakeTranscriber:
        def __init__(self, *, model_name, backend, language):
            time.sleep(0.05)  # widen the race window
            built.append(self)
            self.model_name = model_name

    monkeypatch.setattr(transcriber_state, "Transcriber", SlowFakeTranscriber)

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
