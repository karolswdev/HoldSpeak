# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_css_void_shadow_lists.py to restore.

# ruff: noqa


# --- test_scan_catches_the_known_shape: P2: tests the guard's own scanner on a typed sample
def test_scan_catches_the_known_shape(tmp_path: Path) -> None:
    css = ":root{--void:none;--chain:var(--void)}\n.a{box-shadow: var(--chain), 0 1px 2px red}\n"
    defs = {}
    for m in _DEF.finditer(css):
        defs.setdefault(m.group(1), set()).add(m.group(2).strip())
    void = _void_tokens(defs)
    assert void == {"--void", "--chain"}
    items = _split_top("var(--chain), 0 1px 2px red", ",")
    assert _bare_token(items[0]) == "--chain"
