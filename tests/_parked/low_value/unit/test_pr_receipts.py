# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_pr_receipts.py to restore.

# ruff: noqa


# --- test_egress_census_gh_and_fetch_only: P8: a grep census of where the string gh appears in a package
def test_egress_census_gh_and_fetch_only() -> None:
    """The grep census: `gh` is named only in pr_receipts (this
    delivery package's one collector egress) and the fetch verb is
    the one git-network call."""
    pkg = REPO / "holdspeak" / "delivery"
    gh_files = set()
    for path in pkg.glob("*.py"):
        code = "\n".join(
            line for line in path.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        )
        if '"gh"' in code or "'gh'" in code:
            gh_files.add(path.name)
    assert gh_files == {"pr_receipts.py"}

    text = (pkg / "pr_receipts.py").read_text(encoding="utf-8")
    assert text.count('"fetch"') == 1  # one explicit egress verb
