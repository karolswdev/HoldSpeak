"""Read-only access to the retained PHILO-11-06 proof programs.

Keep tracked inputs separate from the harness tests' temporary output paths.
This module reads the proof tree; it never writes there.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROOF = Path(__file__).resolve().parents[2] / "pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-06-proof"


def load_proof_module(filename: str):
    path = PROOF / filename
    spec = importlib.util.spec_from_file_location(f"philo11_{path.stem}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_proof_script(filename: str) -> str:
    return (PROOF / filename).read_text()
