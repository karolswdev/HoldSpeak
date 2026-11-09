# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_automation_name_guard.py to restore.

# ruff: noqa


# --- test_the_scanner_reads_literals_jsx_and_skips_code: P2: tests the guard's own scanner, not the face
def test_the_scanner_reads_literals_jsx_and_skips_code() -> None:
    sample = (
        'const a = "New Workbench"; // Workbench in a comment\n'
        "const b = `${n} workbench runs`;\n"
        'const c = "workbench"; const d = "/api/workbenches"; const e = "desk-workbench-window";\n'
        "const f = /run this workbench/i; const g = <p>Open the Workbench</p>;\n"
        'const h = "Delivery Workbench project"; type W = WorkbenchWindow;\n'
    )
    literals, code = split(sample)
    shown = [text for _, text in literals if _shown(text)]
    assert shown == ["New Workbench", " workbench runs"]
    jsx = [m.group(1) for m in JSX_TEXT.finditer(code) if WORD.search(m.group(1))]
    assert jsx == ["Open the Workbench"]
