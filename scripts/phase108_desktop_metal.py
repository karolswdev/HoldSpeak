#!/usr/bin/env python3
"""Exercise the Phase 108 desktop executor against a real TextEdit window."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from holdspeak.db import get_database, reset_database
from holdspeak.desktop_typing import type_text_from_owner_gesture
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.typer import TextTyper


def _osascript(source: str) -> str:
    completed = subprocess.run(
        ["osascript", "-e", source],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        raise RuntimeError(
            (completed.stderr or completed.stdout or "osascript failed").strip()
        )
    return completed.stdout


def main() -> int:
    if sys.platform != "darwin":
        print("FAIL desktop confinement metal proof requires macOS")
        return 1

    marker = f"HS108_CONFINED_DESKTOP_{uuid.uuid4().hex[:12]}"
    with tempfile.TemporaryDirectory(prefix="holdspeak-phase108-") as temp:
        reset_database()
        database = get_database(Path(temp) / "phase108.db")
        broker = kernel_runtime._configure(database)
        _osascript(
            'tell application "TextEdit"\n'
            "activate\n"
            "make new document\n"
            "end tell\n"
            "delay 0.6"
        )
        try:
            result = type_text_from_owner_gesture(
                marker,
                typer=TextTyper(),
                gesture="hold_release",
                submit=False,
                requested_target="focused",
                delivery_method="phase108_metal",
            )
            landed = _osascript(
                'tell application "TextEdit" to get text of front document'
            ).strip()
            receipt = broker.store.receipt(result["operation_id"])
            if marker not in landed:
                raise RuntimeError("the confined desktop marker did not land")
            if not receipt or receipt["state"] != "succeeded":
                raise RuntimeError("the kernel terminal receipt was not succeeded")
            print(
                json.dumps(
                    {
                        "marker_landed": True,
                        "operation_id": result["operation_id"],
                        "target_ref": result["target_ref"],
                        "native_state": result["native_receipt"]["outcome"],
                        "kernel_state": receipt["state"],
                        "kernel_outcome": receipt["outcome"],
                    },
                    sort_keys=True,
                )
            )
        finally:
            try:
                _osascript(
                    'tell application "TextEdit" to close front document saving no'
                )
            finally:
                kernel_runtime._dispose(broker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
