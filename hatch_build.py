"""Hatch build hooks for HoldSpeak.

The default ``holdspeak`` command serves the web runtime, so wheels built from
source must contain the Astro output under ``holdspeak/static/_built``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Build the Astro frontend before packaging the Python wheel."""

    def initialize(self, version: str, build_data: dict) -> None:
        _ = version
        _ = build_data
        project_root = Path(self.root)
        web_dir = project_root / "web"
        built_index = project_root / "holdspeak" / "static" / "_built" / "index.html"

        skip = os.environ.get("HOLDSPEAK_SKIP_WEB_BUILD", "").lower() in {"1", "true", "yes"}
        if skip:
            if built_index.is_file():
                return
            raise RuntimeError(
                "HOLDSPEAK_SKIP_WEB_BUILD is set, but holdspeak/static/_built/index.html "
                "is missing. Run `cd web && npm ci && npm run build` first."
            )

        npm = shutil.which("npm")
        if npm is None:
            if built_index.is_file():
                return
            raise RuntimeError(
                "npm is required to build the bundled HoldSpeak web UI from source. "
                "Install Node.js/npm, or build from a wheel that already includes "
                "holdspeak/static/_built."
            )

        install_cmd = [npm, "ci"] if (web_dir / "package-lock.json").is_file() else [npm, "install"]
        subprocess.run(install_cmd, cwd=web_dir, check=True)
        subprocess.run([npm, "run", "build"], cwd=web_dir, check=True)
