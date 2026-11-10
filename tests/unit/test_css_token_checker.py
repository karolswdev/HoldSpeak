"""The CSS gate checks live values, without reviving parked material."""
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def test_token_gate_ignores_parked_css_but_rejects_live_literals(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy(ROOT / "web/scripts/validate-tokens.cjs", scripts)
    (tmp_path / "token-allowlist.json").write_text('{"entries": []}')
    source = tmp_path / "src"
    source.mkdir()
    parked = source / "_parked"
    parked.mkdir()
    (parked / "retired.css").write_text(".old { color: #123456; }")
    live = source / "live.css"
    live.write_text(".live { color: var(--text); }")
    command = ["node", str(scripts / "validate-tokens.cjs")]
    passed = subprocess.run(command, capture_output=True, text=True)
    assert passed.returncode == 0, passed.stderr
    live.write_text(".live { color: #123456; transition: opacity 160ms; z-index: 2; }")
    failed = subprocess.run(command, capture_output=True, text=True)
    assert failed.returncode == 1
    assert "src/live.css:1" in failed.stderr
    assert "hex color" in failed.stderr
    assert "ms duration" in failed.stderr
    assert "z-index literal" in failed.stderr
    assert "retired.css" not in failed.stderr
