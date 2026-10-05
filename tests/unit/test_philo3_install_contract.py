"""PHILO-3-02: keep the documented base install ready for LAN summaries.

The endpoint client is a lightweight production dependency.  Since the owner
ruling of 2026-10-05 ("batteries included") the local model runtime
(llama-cpp-python) is core too; the speaker stack stays behind the optional
meeting extra.
"""

from __future__ import annotations

from importlib import metadata

from packaging.requirements import Requirement


def test_produced_core_metadata_has_endpoint_client_and_local_runtime() -> None:
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
    # Owner ruling 2026-10-05 ("batteries included"): the local runtime is core.
    assert "llama-cpp-python" in core
    assert "resemblyzer" not in core
