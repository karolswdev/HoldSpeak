# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_github_templates.py to restore.

# ruff: noqa


# --- TestTemplateTruthTable::test_six_templates_exist: P1: a count fence on the template list (named six, asserts seven)
# (was a method of class TestTemplateTruthTable)
def test_six_templates_exist(self) -> None:
    """HS-169-04: branch_ci added as the 6th template; Conductor R4:
    open_issues as the 7th."""
    assert len(GITHUB_TEMPLATES) == 7
    assert TEMPLATE_IDS == {
        "watch.github.review_queue",
        "watch.github.ci_health",
        "watch.github.merge_flow",
        "watch.github.delivery_drift",
        "watch.github.release_readiness",
        "watch.github.open_issues",
        "watch.github.branch_ci",
    }


# --- TestAdapterThreading::test_adapter_injected_via_constructor: P1/P8: a constructor stores its argument; two preset tables agree
# (was a method of class TestAdapterThreading)
def test_adapter_injected_via_constructor(self, rig) -> None:
    """github_adapter is accessible on the service instance."""
    _db, _ps, svc, adapter = rig
    assert svc._github_adapter is adapter


# --- TestCadenceConsistency: P1/P8: a constructor stores its argument; two preset tables agree
class TestCadenceConsistency:
    """github_templates.CADENCE_PRESETS matches project_setup_service.CADENCE_PRESETS."""

    def test_cadence_presets_match(self) -> None:
        from holdspeak.github_templates import CADENCE_PRESETS as GH_PRESETS
        for key in ("active_work", "normal", "daily", "weekdays"):
            assert key in GH_PRESETS
            assert key in CADENCE_PRESETS
            # Values match
            for field in ("kind", "every_minutes"):
                assert GH_PRESETS[key].get(field) == CADENCE_PRESETS[key].get(field), (
                    f"Cadence preset {key!r}.{field} mismatch: "
                    f"templates={GH_PRESETS[key].get(field)} vs "
                    f"setup={CADENCE_PRESETS[key].get(field)}"
                )
