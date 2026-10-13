"""Shared meeting-glass helpers: the displayed host label, the record's one
host, and the fixture import transcriber.

Was in tests/e2e/test_hs201_summary_face_glass.py (parked by the test diet,
push 2, 2026-10-12). Used by tests/e2e/test_first_use_smoke.py and
tests/e2e/test_philo17_autoflow_glass.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

FIXTURE_WAV = Path(__file__).resolve().parents[1] / "fixtures" / "core_path_smoke_16k.wav"


def _chip_label(host: str) -> str:
    """The label the ONE canonical mapper draws for a host.

    Mirrors `web/src/desk/surface/egress.ts::egressFor` for the hosts this
    rig can produce, so the rig asserts the DISPLAYED truth: the face must
    never print the wire word `same_device` at a person.
    """
    if host in ("local", "LOCAL", "this_device", "same_device", "this machine"):
        return "THIS DEVICE"
    # PHILO-17 U16: a loopback host is THIS DEVICE, by the transport's rule.
    from holdspeak.loopback_http import is_loopback_engine_host

    if is_loopback_engine_host(host):
        return "THIS DEVICE"
    return host


# PHILO-17 U16 (Astra r1 M3): the record names its run's host ONCE -- on its
# summary slab, or on the window foot when the foot already names that host
# (the slab then does not repeat it). Never both, never neither.
RECORD_HOST_JS = """([scope, label]) => {
  const base = document.querySelector(scope);
  const root = (base && (base.closest('.desk-surface-window') || base)) || document;
  const said = ['[data-testid=summary-record-attempts]', '.surface-footer-egress']
    .map(sel => root.querySelector(sel)).filter(Boolean)
    .filter(el => (el.textContent || '').includes(label));
  return said.length === 1;
}"""


# PHILO-17 ("A meeting opens in one window"): the record is the meeting's own
# window, the front one when its row (or any door) opened it.
RECORD = ".desk-object-window.is-front"


def _wait_record_host(page: Any, label: str, scope: str = RECORD, timeout: int = 30_000) -> None:
    page.wait_for_function(RECORD_HOST_JS, arg=[scope, label], timeout=timeout)


class _FixtureImportTranscriber:
    """Stands in for Whisper on the import path. Never loads a model."""

    def transcribe(self, audio, **_admission):
        return "The quick brown fox jumps over the lazy dog."
