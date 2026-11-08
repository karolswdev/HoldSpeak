"""Parked 2026-11-08 (the test-speed subtraction): ledger "only shrinks" checks.

Each failed when a ledgered site was REPAIRED or PARKED (a placement), never
on a new fault: the ledgers still refuse a new site (their growth checks stay
live). Kept as text; not collected.
"""
\n\n# ── from tests/unit/test_kernel_effect_fence.py ──\n\ndef test_broker_debt_ledger_only_shrinks() -> None:
    """The re-baseline is a ratchet: a paid-off entry must leave the ledger.

    Without this, a module carved back under budget would keep its permission
    slip and could silently grow again.
    """
    stale: list[str] = []
    for relative, recorded in sorted(_BROKER_BUDGET_DEBT.items()):
        path = _REPO / relative
        if not path.exists():
            stale.append(f"{relative}: module is gone; drop its debt entry")
            continue
        budget = (
            _BROKER_INIT_BUDGET if path.name == "__init__.py" else _BROKER_MODULE_BUDGET
        )
        lines = _line_count(path)
        if lines <= budget:
            stale.append(
                f"{relative}: now {lines} lines, within the {budget}-line "
                "budget; delete its debt entry"
            )
        elif lines < recorded:
            stale.append(
                f"{relative}: now {lines} lines, below its recorded {recorded}; "
                "lower the debt entry to lock the gain in"
            )
    for relative, recorded in sorted(_BROKER_DRIVER_CONDITIONAL_DEBT.items()):
        path = _REPO / relative
        if not path.exists():
            stale.append(f"{relative}: module is gone; drop its debt entry")
            continue
        found = len(_driver_conditional_findings(path))
        if found == 0:
            stale.append(
                f"{relative}: no driver conditionals left; delete its debt entry"
            )
        elif found < recorded:
            stale.append(
                f"{relative}: now {found} driver conditionals, below its recorded "
                f"{recorded}; lower the debt entry to lock the gain in"
            )
    assert not stale, (
        "the HS-200-03 broker debt ledger has gone stale — it may only ever "
        "shrink:\n  " + "\n  ".join(stale)
    )
\n\n# ── from tests/unit/test_product_copy.py ──\n\ndef test_recorded_copy_debt_only_shrinks() -> None:
    """A repaired line must leave the ledger, or the permission slip outlives the fault."""
    live = {
        (str(item.path), item.rule_id, item.text)
        for item in violations(inventory(REPO))
    }
    stale = sorted(_recorded_copy_debt() - live)
    assert not stale, (
        "the HS-200-03 product-copy debt ledger has gone stale — delete these "
        f"repaired entries from {_COPY_DEBT_LEDGER.name}:\n  "
        + "\n  ".join(f"{path}: {rule}: {text}" for path, rule, text in stale)
    )
\n\n# ── from tests/unit/test_ux_canon_scan.py ──\n\n    def test_every_entry_still_matches_the_tree(self):
        """A stale ledger entry is a lie: the file and needle must exist."""
        mod = _load_scanner()
        src = Path(__file__).resolve().parents[2] / "web" / "src"
        stale = []
        for path, needle, _reason in mod.MIC_ALLOWLIST:
            target = src / path
            if not target.is_file() or needle not in target.read_text(errors="replace"):
                stale.append(f"{path} :: {needle}")
        assert not stale, "stale allowlist entries:\n  " + "\n  ".join(stale)
