"""Parked 2026-11-08: WorkbenchWindow is parked (web/src/desk/_parked/automations/,
#2039), so scripts/ux_canon_scan.py no longer names its "New item instruction"
exemption. The test, verbatim from tests/unit/test_ux_canon_scan.py. Kept, not
collected.
"""
# ruff: noqa


def test_workbench_instruction_keeps_one_named_grammar_mic_authority() -> None:
    scanner = _load_scanner()
    content = '''export function WorkbenchWindow() {
      return <div>
        <MicButton onText={writeInstructionAndResolveReferences} />
        <PadGadget label="New item instruction" mic={false} />
        <PadGadget label="Unrelated instruction" mic={false} />
      </div>;
    }'''
    rel = "desk/components/WorkbenchWindow.tsx"
    found = scanner.scan_mic(rel, content, content.splitlines())
    assert len(found) == 1
    assert 'label="Unrelated instruction"' in content.splitlines()[found[0].line - 1]
    # The named label does not excuse a different face's missing capture path.
    elsewhere = scanner.scan_mic("features/x/Row.tsx", content, content.splitlines())
    assert len(elsewhere) == 2
