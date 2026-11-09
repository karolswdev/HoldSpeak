# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_intel_egress_invariant.py to restore.

# ruff: noqa


# --- test_hs_131_census_callers_cannot_execute_intel_outside_admitted_runner: P8: greps caller modules' source for forbidden call names
def test_hs_131_census_callers_cannot_execute_intel_outside_admitted_runner():
    """The migrated seams may select a placement, never build or resolve
    a mutable Intel target for provider execution themselves.

    HS-131-13 added the last three: the Cadence service (migrated onto an admitted
    domain parent), the Decisions route (its duplicate model seam deleted), and the
    Delivery service (its dormant `prepare_pr_review` deleted). The forbidden names
    include `build_intel_for_target`, which no longer exists — so this also pins
    that none of these modules brings it back."""
    root = Path(__file__).resolve().parents[2]
    callers = (
        "holdspeak/rails_observer.py",
        "holdspeak/services/decision_lifecycle_service.py",
        "holdspeak/web/routes/delivery_prs.py",
        "holdspeak/services/workbench_service.py",
        "holdspeak/services/cadence_service.py",
        "holdspeak/services/delivery_service.py",
        "holdspeak/web/routes/decisions.py",
    )
    for relative in callers:
        source = (root / relative).read_text()
        for forbidden in ("build_intel_for_target(", "resolve_inference_target("):
            assert forbidden not in source, (
                f"{relative} executes {forbidden}; all provider dispatch must enter "
                "InferenceRunner with its admitted deployment revision"
            )
