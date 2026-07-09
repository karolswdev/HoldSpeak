"""The committed features.yaml is in sync with its derivation."""

from __future__ import annotations

from uat.tools import build_ledger


def test_committed_ledger_is_up_to_date():
    # The generator proposes; the committed YAML is canon — but they must agree,
    # so a drifted inventory can't leave the ledger silently stale.
    assert build_ledger.main(["--check"]) == 0


def test_every_holdspeak_phase_is_mapped():
    phase_index = build_ledger.load_phase_index()
    content = build_ledger.generate()
    import yaml

    doc = yaml.safe_load(content)
    phase_map = doc["phase_map"]
    # Every phase in the index appears in the map (none silently absent).
    for phase in phase_index:
        assert str(phase) in phase_map
