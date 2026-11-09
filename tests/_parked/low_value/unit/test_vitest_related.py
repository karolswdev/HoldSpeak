# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_vitest_related.py to restore.

# ruff: noqa


# --- test_why_names_each_rule_per_changed_file: P4: pins the wording of the selector's explanation line
def test_why_names_each_rule_per_changed_file(tmp_path):
    src = _tree(tmp_path)
    why: list[str] = []
    vr.related(["src/desk/a/AWin.tsx", "src/desk/surface/gadgets.css"], root=src, why=why)
    assert why[0] == "src/desk/a/AWin.tsx: 2 import it, 1 app files (folder desk/a), 0 name it"
    assert why[1] == "src/desk/surface/gadgets.css: 0 import it, 0 app files (no app), 1 name it"
