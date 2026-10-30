"""The web build id includes binary assets that ship with the frontend."""

from __future__ import annotations

import json
import os
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web"
SOURCE_CONFIG = WEB / "vite.config.ts"
SOURCE_PNG_A = WEB / "public" / "desk" / "sprites" / "32" / "agent-pi.png"
SOURCE_PNG_B = WEB / "public" / "desk" / "sprites" / "32" / "agent-codex.png"

NODE_SCRIPT = r"""
import { join } from "node:path";
import { mkdirSync, readFileSync } from "node:fs";
import { loadConfigFromFile } from "vite";

const [fixture, runName] = process.argv.slice(1);
const { config, error } = await loadConfigFromFile(
  { command: "build", mode: "test" },
  join(fixture, "vite.config.ts"),
  fixture,
);
if (error) throw error;

const stamp = config.plugins
  .flat(Infinity)
  .find((plugin) => plugin?.name === "holdspeak-build-stamp");
if (!stamp || typeof stamp.writeBundle !== "function") {
  throw new Error("holdspeak-build-stamp plugin was not loaded from the real Vite config");
}

const output = join(fixture, `output-${runName}`);
mkdirSync(output, { recursive: true });
await stamp.writeBundle({ dir: output }, {});
process.stdout.write(readFileSync(join(output, "build-id.json"), "utf8"));
"""


def _assert_32px_png(path: Path) -> None:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack(">II", data[16:24]) == (32, 32)


def _stamp_id(fixture: Path, run_name: str) -> str:
    node = shutil.which("node")
    assert node, "Node is required to load the real Vite config"
    environment = os.environ.copy()
    result = subprocess.run(
        [node, "--input-type=module", "-e", NODE_SCRIPT, str(fixture), run_name],
        cwd=WEB,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)["build_id"]


def test_web_build_id_changes_when_a_shipped_png_changes() -> None:
    _assert_32px_png(SOURCE_PNG_A)
    _assert_32px_png(SOURCE_PNG_B)

    with tempfile.TemporaryDirectory(prefix=".build-stamp-", dir=WEB) as raw_fixture:
        fixture = Path(raw_fixture)
        (fixture / "src").mkdir()
        public = fixture / "public"
        public.mkdir()
        shutil.copyfile(SOURCE_CONFIG, fixture / "vite.config.ts")
        icon = public / "icon.png"

        shutil.copyfile(SOURCE_PNG_A, icon)
        first = _stamp_id(fixture, "first")
        same_inputs = _stamp_id(fixture, "same-inputs")
        assert first == same_inputs

        shutil.copyfile(SOURCE_PNG_B, icon)
        changed_asset = _stamp_id(fixture, "changed-asset")
        assert changed_asset != first
