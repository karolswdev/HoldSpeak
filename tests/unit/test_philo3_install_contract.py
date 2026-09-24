"""PHILO-3-02: keep the documented base install ready for LAN summaries.

The endpoint client is a lightweight production dependency.  The local model
compiler and speaker stack remain behind the optional meeting extra so the
ordinary source install does not pull those heavyweight runtimes.
"""

from __future__ import annotations

from importlib import metadata

from packaging.requirements import Requirement


def test_produced_core_metadata_has_endpoint_client_only() -> None:
    """Inspect the installed distribution metadata produced by the backend.

    ``uv run pytest`` installs the editable project before collection, so this
    reads the same ``METADATA`` that a wheel or editable build exposes.  The
    optional markers are intentionally ignored: ``openai`` must be an
    unconditional requirement while local model and speaker runtimes stay
    optional.
    """
    requirements = [
        Requirement(value)
        for value in (metadata.distribution("holdspeak").requires or [])
    ]
    core = {
        requirement.name.lower()
        for requirement in requirements
        if requirement.marker is None
    }

    assert "openai" in core
    assert "llama-cpp-python" not in core
    assert "resemblyzer" not in core
