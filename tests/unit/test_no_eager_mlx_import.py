"""Fence: importing the hub module tree must not eagerly import MLX.

On Apple Silicon, MLX and llama.cpp's ggml-metal are two independent Metal
GPU runtimes.  They can coexist while both are alive, but when ggml-metal
tears down (``ggml_metal_free``) it can invalidate GPU stream state that
MLX holds -- the process aborts with a C++ ``std::runtime_error``:

    ``There is no Stream(gpu, N) in current thread.``

The hub process uses BOTH runtimes: mlx-whisper for transcription and
llama-cpp-python for local meeting intelligence / chat turns.  To prevent
the crash, the Llama instance is cached at process level (see
``holdspeak.intel.engine._LLAMA_PROCESS_CACHE``), and MLX must NOT be
imported eagerly at module scope -- only inside the transcriber's
``__init__`` or ``warm`` methods, which run on a dedicated thread.

This fence asserts that importing the hub's server entry-point module tree
does NOT pull ``mlx``, ``mlx.core``, ``mlx_whisper``, or ``mlx_lm`` into
``sys.modules``.  A violation means something added a module-scope import
of one of these packages, which would re-introduce the dual-Metal crash.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest


# The packages that MUST NOT appear in sys.modules after importing the
# hub module tree.  Only the top-level names matter -- if ``mlx.core`` is
# loaded, ``mlx`` is too.
_FORBIDDEN = frozenset({"mlx", "mlx.core", "mlx_whisper", "mlx_lm"})


def test_hub_import_does_not_load_mlx():
    """Importing holdspeak.intel and holdspeak.transcribe must not import MLX.

    We run this in a subprocess so the test's own process state cannot
    mask an eager import that already happened.
    """
    script = textwrap.dedent("""\
        import sys
        # Import the modules that the hub process loads at startup.
        import holdspeak.intel  # noqa: F401
        import holdspeak.transcribe  # noqa: F401
        # Report which forbidden modules got loaded.
        forbidden = {"mlx", "mlx.core", "mlx_whisper", "mlx_lm"}
        loaded = sorted(forbidden & set(sys.modules))
        if loaded:
            print("EAGER_MLX_IMPORT:" + ",".join(loaded))
            sys.exit(1)
        else:
            print("OK")
            sys.exit(0)
    """)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        stdout = result.stdout.strip()
        if stdout.startswith("EAGER_MLX_IMPORT:"):
            modules = stdout.split(":", 1)[1]
            pytest.fail(
                f"Hub module-scope imports eagerly loaded MLX packages: "
                f"{modules}. This will cause a Metal GPU crash when "
                f"mlx-whisper and llama-cpp-python coexist in the hub "
                f"process. Move the import inside the function that "
                f"needs it (lazy import)."
            )
        else:
            pytest.fail(
                f"Subprocess failed (exit {result.returncode}):\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )


def test_llama_cache_prevents_metal_teardown():
    """MeetingIntel must cache the Llama instance so ggml_metal_free never fires.

    Two ``MeetingIntel`` instances for the same model path must share the
    same ``_llm`` object, and the process-level cache must hold a
    reference after both instances go out of scope.
    """
    from unittest.mock import MagicMock, patch

    from holdspeak.intel.engine import (
        MeetingIntel,
        _LLAMA_CACHE_LOCK,
        _LLAMA_PROCESS_CACHE,
    )

    # Clear the cache before the test.
    with _LLAMA_CACHE_LOCK:
        _LLAMA_PROCESS_CACHE.clear()

    fake_llama_instance = MagicMock(name="FakeLlama")
    fake_llama_cls = MagicMock(return_value=fake_llama_instance)

    model_path = "/tmp/test-model.gguf"
    with (
        patch("holdspeak.intel.Llama", fake_llama_cls),
        patch("holdspeak.intel._IMPORT_ERROR", None),
        patch("pathlib.Path.exists", return_value=True),
    ):
        # First instance creates the Llama.
        engine1 = MeetingIntel(provider="local", model_path=model_path)
        engine1._ensure_local_model_loaded()
        assert engine1._llm is fake_llama_instance
        assert fake_llama_cls.call_count == 1

        # Second instance reuses the cached Llama.
        engine2 = MeetingIntel(provider="local", model_path=model_path)
        engine2._ensure_local_model_loaded()
        assert engine2._llm is fake_llama_instance
        assert fake_llama_cls.call_count == 1  # no second construction

    # The cache retains the reference.
    with _LLAMA_CACHE_LOCK:
        resolved = str(MeetingIntel(
            provider="local", model_path=model_path
        )._resolved_model_path())
        assert resolved in _LLAMA_PROCESS_CACHE
        assert _LLAMA_PROCESS_CACHE[resolved] is fake_llama_instance

    # Cleanup.
    with _LLAMA_CACHE_LOCK:
        _LLAMA_PROCESS_CACHE.clear()
