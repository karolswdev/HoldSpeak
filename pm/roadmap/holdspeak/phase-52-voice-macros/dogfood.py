#!/usr/bin/env python3
"""Phase 52 dogfood: prove voice command macros work both ways, no mic.

Drives ``dictation_runner.dispatch_voice_command`` directly:
  - off by default -> no command fires (byte-identical to no feature),
  - a non-keyword utterance is not handled (it would dictate normally),
  - a configured ``shell`` macro really runs (an ``echo`` into a temp file),
  - a configured ``type_text`` macro types via the (here injected) writer.

Run from anywhere:
    .venv/bin/python pm/roadmap/holdspeak/phase-52-voice-macros/dogfood.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from holdspeak.config import Config, MacrosConfig, VoiceMacro, VoiceMacroAction
from holdspeak.dictation_runner import dispatch_voice_command

PASS = True


def check(label: str, cond: bool) -> None:
    global PASS
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        PASS = False


print("== Phase 52 dogfood: voice command macros ==\n")

tmp = Path(tempfile.mkdtemp()) / "fired.txt"
cfg = Config()
cfg.dictation.macros = MacrosConfig(
    enabled=True,
    items=[
        VoiceMacro("log it", VoiceMacroAction("shell", f"echo hello-from-voice > {tmp}")),
        VoiceMacro("standup", VoiceMacroAction("type_text", "## Standup")),
    ],
)

print("-- 1. off by default: no command fires (byte-identical) --")
check("a macros-disabled config returns None", dispatch_voice_command("log it", config=Config()) is None)

print("\n-- 2. a non-keyword utterance is not a command --")
check("an unmatched phrase returns None", dispatch_voice_command("write the weekly report", config=cfg) is None)

print("\n-- 3. a shell command really fires on a keyword --")
res = dispatch_voice_command("Log it.", config=cfg)  # default real runner
check("the command was handled and ok", bool(res and res.handled and res.ok))
check("nothing was typed (handled = not dictated)", bool(res and res.handled))
fired = tmp.read_text(encoding="utf-8").strip() if tmp.exists() else ""
check("the echo actually ran (temp file written)", fired == "hello-from-voice")

print("\n-- 4. a type_text command types via the writer --")
typed: list[str] = []
res2 = dispatch_voice_command("standup", config=cfg, type_writer=typed.append)
check("the command was handled and ok", bool(res2 and res2.handled and res2.ok))
check("the snippet was typed", typed == ["## Standup"])

print()
print("RESULT: PASS" if PASS else "RESULT: FAIL")
sys.exit(0 if PASS else 1)
