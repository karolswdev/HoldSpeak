"""Smoke test for scripts/ux_canon_scan.py.

Plants a tiny fixture tree in tmp_path with one hit per rule class,
runs the scanner, and asserts the JSON shape + at least one hit per class.
Also tests false-positive suppression (JSX comments, code fragments,
property access, boolean .length, import lines).
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ux_canon_scan.py"


def _load_scanner():
    """Import the scanner module in-process."""
    spec = importlib.util.spec_from_file_location("ux_canon_scan", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _plant_fixture(root: Path) -> None:
    """Create a minimal web/src tree with one planted violation per rule class."""
    src = root / "web" / "src"

    # A face file with all TSX violations planted
    face_dir = src / "features" / "test-face"
    face_dir.mkdir(parents=True)

    face_tsx = face_dir / "TestFace.tsx"
    face_tsx.write_text("""\
import React from "react";

// A1: raw <button>
export function TestFace() {
  const items = [1, 2, 3];
  return (
    <div>
      <button type="button" onClick={() => {}}>Click me</button>

      {/* A3-sentence: text > 60 chars ending with period */}
      <span>This is a very long sentence that exceeds sixty characters and ends with a period.</span>

      {/* A3-prose: <p> with text > 40 chars */}
      <p>This is a helper paragraph with more than forty characters of text content here.</p>

      {/* A4: modal */}
      <div role="dialog" aria-modal="true">Modal content</div>

      {/* A8: counter of zero */}
      <span>{items.length} items</span>

      {/* B: raw control */}
      <input type="text" placeholder="search" />

      {/* raw-ids: snake_case in rendered text */}
      <span>open_pull_requests</span>

      {/* emoji in JSX */}
      <span>\U0001F525 Hot</span>
    </div>
  );
}

// A9 trigger: provider fetch without the egress component
fetch("/api/providers/discover");
""")

    # A CSS file with DS6 and C violations
    face_css = face_dir / "test-face.css"
    face_css.write_text("""\
.test-rail {
  border-left: 3px solid var(--accent);
}

.test-collapse {
  font-size: 13px;
}
""")

    # A face with a text input but no MicButton (mic rule)
    mic_dir = src / "pages" / "cores"
    mic_dir.mkdir(parents=True)
    mic_face = mic_dir / "MicTestCore.tsx"
    mic_face.write_text("""\
import React from "react";

export function MicTestCore() {
  return (
    <div>
      <input type="text" placeholder="Type here" />
    </div>
  );
}
""")


def test_scan_produces_valid_output(tmp_path: Path) -> None:
    """Run the scanner on a fixture tree and check the JSON shape."""
    _plant_fixture(tmp_path)

    json_out = tmp_path / "violations.json"
    md_out = tmp_path / "violations.md"
    ranking_out = tmp_path / "ranking.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root", str(tmp_path),
            "--json", str(json_out),
            "--md", str(md_out),
            "--ranking", str(ranking_out),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Script failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    # JSON exists and is valid
    assert json_out.exists(), "violations.json not created"
    data = json.loads(json_out.read_text())

    # Shape: top-level keys
    assert "totals" in data
    assert "faces" in data
    assert "per_rule" in data["totals"]
    assert "per_face" in data["totals"]

    # Shape: each violation has file, line, rule, text
    for face, violations in data["faces"].items():
        for v in violations:
            assert "file" in v
            assert "line" in v
            assert "rule" in v
            assert "text" in v
            assert isinstance(v["line"], int)

    # At least one hit per planted rule class
    rules_found = set()
    for face, violations in data["faces"].items():
        for v in violations:
            rules_found.add(v["rule"])

    expected_rules = {"A1", "A3-sentence", "A3-prose", "A4", "A8", "B",
                      "DS6", "raw-ids", "emoji", "A9", "mic"}
    missing = expected_rules - rules_found
    assert not missing, f"Missing planted rule classes: {missing}; found: {rules_found}"

    # MD files exist and are non-empty
    assert md_out.exists() and md_out.stat().st_size > 0
    assert ranking_out.exists() and ranking_out.stat().st_size > 0


def test_scan_empty_tree(tmp_path: Path) -> None:
    """Scanner on an empty web/src produces zero violations."""
    src = tmp_path / "web" / "src" / "features"
    src.mkdir(parents=True)

    json_out = tmp_path / "violations.json"
    md_out = tmp_path / "violations.md"
    ranking_out = tmp_path / "ranking.md"

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root", str(tmp_path),
            "--json", str(json_out),
            "--md", str(md_out),
            "--ranking", str(ranking_out),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    data = json.loads(json_out.read_text())
    assert data["faces"] == {}
    assert data["totals"]["per_rule"] == {}


# ---------------------------------------------------------------------------
# False-positive suppression tests (in-process via scan_file)
# ---------------------------------------------------------------------------

class TestA1SkipsComments:
    """A1 must not fire on JSX comments mentioning <button>."""

    def test_jsx_comment_not_flagged(self):
        mod = _load_scanner()
        line = '      {/* Condition 1: no raw <button>; visually-hidden submit */}'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a1 = [v for v in violations if v.rule == "A1"]
        assert not a1, f"A1 fired on JSX comment: {a1[0].text}"

    def test_line_comment_not_flagged(self):
        mod = _load_scanner()
        line = '      // no raw <button> here'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a1 = [v for v in violations if v.rule == "A1"]
        assert not a1

    def test_real_button_still_flagged(self):
        mod = _load_scanner()
        line = '      <button type="button" onClick={go}>Go</button>'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a1 = [v for v in violations if v.rule == "A1"]
        assert len(a1) == 1


class TestA3SkipsCode:
    """A3-sentence must not fire on TypeScript code fragments."""

    def test_usestate_code_not_flagged(self):
        """Generics boundary like useState<Visibility>(...) must not be treated as JSX text."""
        mod = _load_scanner()
        line = 'const [v, setV] = useState<Visibility>("leader_private"); const [busy, setBusy] = useState(false); const [projects, setProjects] = useState<Project[]>([]);'
        violations = mod.scan_file("pages/cores/Foo.tsx", line, [line])
        a3s = [v for v in violations if v.rule == "A3-sentence"]
        assert not a3s, f"A3-sentence fired on code: {a3s[0].text}"

    def test_ternary_code_not_flagged(self):
        mod = _load_scanner()
        line = '</> : thought.continuity && isRefining(thought.continuity.state) ? <div className="x">'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a3s = [v for v in violations if v.rule == "A3-sentence"]
        assert not a3s, f"A3-sentence fired on ternary code: {a3s[0].text}"

    def test_real_sentence_still_flagged(self):
        mod = _load_scanner()
        line = '<span>This is a very long sentence that exceeds sixty characters and ends with a period.</span>'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a3s = [v for v in violations if v.rule == "A3-sentence"]
        assert len(a3s) == 1


class TestRawIdsSkipsPropertyAccess:
    """raw-ids must not fire on property access like brief.open_commitments."""

    def test_property_access_not_flagged(self):
        mod = _load_scanner()
        line = '>{brief.open_commitments.length ? <SurfaceRows>'
        violations = mod.scan_file("pages/cores/Foo.tsx", line, [line])
        raw = [v for v in violations if v.rule == "raw-ids"
               and "open_commitments" in v.text]
        assert not raw, f"raw-ids fired on property access: {raw[0].text}"

    def test_dot_accessor_display_name(self):
        mod = _load_scanner()
        line = '>{row.display_name}<'
        violations = mod.scan_file("pages/cores/Foo.tsx", line, [line])
        raw = [v for v in violations if v.rule == "raw-ids"
               and "display_name" in v.text]
        assert not raw

    def test_bare_snake_still_flagged(self):
        mod = _load_scanner()
        line = '>open_pull_requests<'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        raw = [v for v in violations if v.rule == "raw-ids"
               and "open_pull_requests" in v.text]
        assert len(raw) == 1


class TestA8SkipsImportsAndBooleans:
    """A8 must not fire on import lines or boolean .length patterns."""

    def test_import_line_not_flagged(self):
        mod = _load_scanner()
        line = 'import { CitationChips, groundedMatchCount } from "../surface/citations";'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a8 = [v for v in violations if v.rule == "A8"]
        assert not a8, f"A8 fired on import: {a8[0].text}"

    def test_negation_boolean_not_flagged(self):
        mod = _load_scanner()
        line = '  empty={!rows.length}'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a8 = [v for v in violations if v.rule == "A8"]
        assert not a8, f"A8 fired on boolean !.length: {a8[0].text}"

    def test_disabled_boolean_not_flagged(self):
        mod = _load_scanner()
        line = '  disabled={!routines.length}'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a8 = [v for v in violations if v.rule == "A8"]
        assert not a8

    def test_arithmetic_length_not_flagged(self):
        mod = _load_scanner()
        line = '  selection: { anchor: from, head: from + text.length },'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a8 = [v for v in violations if v.rule == "A8"]
        assert not a8, f"A8 fired on arithmetic .length: {a8[0].text}"

    def test_unguarded_length_still_flagged(self):
        mod = _load_scanner()
        line = '  <span>{items.length} items</span>'
        violations = mod.scan_file("features/test/Foo.tsx", line, [line])
        a8 = [v for v in violations if v.rule == "A8"]
        assert len(a8) == 1


# ---------------------------------------------------------------------------
# The voice law, per element (HS-176-04, ruling R9)
# ---------------------------------------------------------------------------

class TestMicPerElement:
    """Rule `mic` counts every dictatable element, not once per file."""

    def _scan(self, rel: str, body: str):
        mod = _load_scanner()
        return [v for v in mod.scan_file(rel, body, body.splitlines())
                if v.rule == "mic"]

    def test_two_bare_inputs_are_two_violations(self):
        body = (
            'export function Face() {\n'
            '  return <div>\n'
            '    <input type="text" value={a} />\n'
            '    <input value={b} />\n'
            '  </div>;\n'
            '}\n'
        )
        hits = self._scan("features/test/Face.tsx", body)
        assert len(hits) == 2, [v.text for v in hits]
        assert [v.line for v in hits] == [3, 4]

    def test_textarea_is_matched(self):
        """Defect (i): the old flag never matched <textarea."""
        body = (
            'export function Face() {\n'
            '  return <textarea value={a} onChange={f} />;\n'
            '}\n'
        )
        hits = self._scan("desk/components/Face.tsx", body)
        assert len(hits) == 1
        assert "<textarea>" in hits[0].text

    def test_string_gadget_is_not_an_uncovered_input(self):
        """Defect (ii): a StringGadget renders its own mic."""
        body = (
            'export function Face() {\n'
            '  return <StringGadget label="Name" value={a} onChange={f} />;\n'
            '}\n'
        )
        assert self._scan("desk/components/Face.tsx", body) == []

    def test_mic_false_opt_out_is_a_violation(self):
        body = (
            'export function Face() {\n'
            '  return <StringGadget label="Name" mic={false} value={a} onChange={f} />;\n'
            '}\n'
        )
        hits = self._scan("desk/components/Face.tsx", body)
        assert len(hits) == 1
        assert "mic={false}" in hits[0].text

    def test_mic_false_opt_out_across_lines_is_a_violation(self):
        body = (
            'export function Face() {\n'
            '  return (\n'
            '    <PadGadget\n'
            '      label="Note"\n'
            '      value={a}\n'
            '      mic={false}\n'
            '      onChange={f}\n'
            '    />\n'
            '  );\n'
            '}\n'
        )
        hits = self._scan("desk/components/Face.tsx", body)
        assert len(hits) == 1
        assert hits[0].line == 3

    def test_mic_button_in_the_same_component_covers(self):
        body = (
            'export function Face() {\n'
            '  return <div>\n'
            '    <input type="text" value={a} />\n'
            '    <MicButton onText={f} />\n'
            '  </div>;\n'
            '}\n'
        )
        assert self._scan("desk/components/Face.tsx", body) == []

    def test_mic_button_in_another_component_does_not_cover(self):
        """Defect (iii): file scope hid a second component's bare input."""
        body = (
            'export function Composer() {\n'
            '  return <div><textarea value={a} /><MicButton onText={f} /></div>;\n'
            '}\n'
            'export function InlineEditor() {\n'
            '  return <textarea value={b} />;\n'
            '}\n'
        )
        hits = self._scan("desk/components/Face.tsx", body)
        assert len(hits) == 1
        assert hits[0].line == 5

    def test_non_text_types_are_not_candidates(self):
        body = (
            'export function Face() {\n'
            '  return <div>\n'
            '    <input type="checkbox" checked={a} />\n'
            '    <input type="password" value={b} />\n'
            '    <input type="file" onChange={f} />\n'
            '    <input type="radio" name="g" />\n'
            '    <input type="number" value={c} />\n'
            '    <input type="range" value={d} />\n'
            '    <input type="date" value={e} />\n'
            '  </div>;\n'
            '}\n'
        )
        assert self._scan("features/test/Face.tsx", body) == []

    def test_search_and_email_are_candidates(self):
        body = (
            'export function Face() {\n'
            '  return <div>\n'
            '    <input type="search" value={a} />\n'
            '    <input type="email" value={b} />\n'
            '  </div>;\n'
            '}\n'
        )
        assert len(self._scan("features/test/Face.tsx", body)) == 2

    def test_closed_jsx_comment_does_not_hide_the_element(self):
        """`{/* … */}<textarea>` is live code, not a comment."""
        body = (
            'export function Face() {\n'
            '  return <label>{/* UX-CANON: needs redesign */}<textarea value={a} /></label>;\n'
            '}\n'
        )
        assert len(self._scan("desk/components/Face.tsx", body)) == 1

    def test_commented_out_element_is_skipped(self):
        body = (
            'export function Face() {\n'
            '  // <input type="text" value={a} />\n'
            '  return null;\n'
            '}\n'
        )
        assert self._scan("desk/components/Face.tsx", body) == []

    def test_rule_is_not_gated_on_face_classification(self):
        """Defect (iv): a shared component outside the face dirs counts."""
        body = (
            'export function TextInput(props) {\n'
            '  return <input className="hs-control" {...props} />;\n'
            '}\n'
        )
        assert len(self._scan("components/widgets/TextInput.tsx", body)) == 1


class TestMicAllowlist:
    """The named allowlist is the census's ledger, with a reason each."""

    def test_allowlisted_element_is_not_a_violation(self):
        mod = _load_scanner()
        body = (
            'export function CronRow() {\n'
            '  return <StringGadget label="Cron expression" mic={false} value={a} onChange={f} />;\n'
            '}\n'
        )
        hits = [v for v in mod.scan_file(
            "desk/components/ScheduleCreateWindow.tsx", body, body.splitlines())
            if v.rule == "mic"]
        assert hits == []

    def test_the_allowlist_is_file_scoped(self):
        """The same needle in another file is still a violation."""
        mod = _load_scanner()
        body = (
            'export function CronRow() {\n'
            '  return <StringGadget label="Cron expression" mic={false} value={a} onChange={f} />;\n'
            '}\n'
        )
        hits = [v for v in mod.scan_file(
            "desk/components/OtherWindow.tsx", body, body.splitlines())
            if v.rule == "mic"]
        assert len(hits) == 1

    def test_r13_utterance_well_is_allowlisted_in_advance(self):
        """HS-176-05 sets mic={false} on the Speak face's well (ruling R13)."""
        mod = _load_scanner()
        body = (
            'export function SpeakFace() {\n'
            '  return <PadGadget label="Utterance" mic={false} value={a} onChange={f} />;\n'
            '}\n'
        )
        hits = [v for v in mod.scan_file(
            "pages/cores/dictation/SpeakFace.tsx", body, body.splitlines())
            if v.rule == "mic"]
        assert hits == []

    def test_every_entry_names_a_reason(self):
        mod = _load_scanner()
        for path, needle, reason in mod.MIC_ALLOWLIST:
            assert path and needle and len(reason) > 10, (path, needle, reason)

    def test_every_entry_still_matches_the_tree(self):
        """A stale ledger entry is a lie: the file and needle must exist."""
        mod = _load_scanner()
        src = Path(__file__).resolve().parents[2] / "web" / "src"
        stale = []
        for path, needle, _reason in mod.MIC_ALLOWLIST:
            target = src / path
            if not target.is_file() or needle not in target.read_text(errors="replace"):
                stale.append(f"{path} :: {needle}")
        assert not stale, "stale allowlist entries:\n  " + "\n  ".join(stale)

    def test_the_ledger_matches_the_census(self):
        """23 census elements (19 raw + 4 opt-outs) + the R13 well = 24."""
        mod = _load_scanner()
        assert len(mod.MIC_ALLOWLIST) == 24
        assert len({(p, n) for p, n, _ in mod.MIC_ALLOWLIST}) == 24
