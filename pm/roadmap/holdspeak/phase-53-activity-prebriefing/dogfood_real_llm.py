#!/usr/bin/env python3
"""Phase 53 real-metal dogfood (HS-53-07): the closed pre-briefing loop on a live LLM.

This is the proof the no-LLM dogfood could not give: that clicking "Dictate with
this" on an activity nudge *demonstrably changes what the model writes*. It drives
the **real** project-rewriter against the `.43` homelab llama.cpp endpoint
(Qwen3.5-9B-Q6), over the same `.hs`-grounded demo fixture the HS-39 enrichment
e2e uses, and runs the identical generic dictation twice:

  - CONTROL:   no selection. activity = {target}.
  - TREATMENT: a selected github_issue record pinned at records[0]
               (exactly what `build_activity_context(selected_record_id=...)`
               produces after the dictation runner consumes the pin).

The selected issue is about something the demo project's `.hs` never mentions
(an `--since` flag on an `export` command; issue #412). So if the treatment
output references it and the control does not, the selected record provably
reached the model — the loop is closed end to end on real metal.

Opt-in / auto-skip: runs only when the endpoint is reachable (env override
`HOLDSPEAK_DICTATION_E2E_BASE_URL` / `_MODEL`, else the `.43` defaults).

    .venv/bin/python pm/roadmap/holdspeak/phase-53-activity-prebriefing/dogfood_real_llm.py
"""
from __future__ import annotations

import os
import socket
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

DEFAULT_BASE_URL = "http://192.168.1.43:8080/v1"
DEFAULT_MODEL = "Qwen3.5-9B-UD-Q6_K_XL.gguf"
BASE_URL = os.environ.get("HOLDSPEAK_DICTATION_E2E_BASE_URL", DEFAULT_BASE_URL)
MODEL = os.environ.get("HOLDSPEAK_DICTATION_E2E_MODEL", DEFAULT_MODEL)

DEMO_PROJECT = REPO_ROOT / "tests" / "fixtures" / "dictation_demo_project"

# A generic dictation that names nothing about the selected issue. Any reference
# to the issue in the output can only have come from the selected record.
# A realistic-length dictation (the rewriter caps a draft at ~4x the input, a
# real product guard). The subject is named only as "the issue I was just
# looking at" — so any concrete reference to #412 can only come from the
# selected record, not the words spoken.
SPOKEN = (
    "hey claude give me a quick one or two sentence reminder of what i need to "
    "do next for the issue i was just looking at so i can paste it into my "
    "notes, keep it short"
)

# The selected ActivityRecord — deliberately off-topic for the payments/ledger
# demo .hs, so its tokens are unmistakable in the output.
SELECTED_RECORD = {
    "id": 412,
    "source_browser": "safari",
    "source_profile": "work",
    "url": "https://github.com/karolswdev/HoldSpeak/issues/412",
    "title": "Add a --since flag to the export command",
    "domain": "github.com",
    "visit_count": 3,
    "first_seen_at": None,
    "last_seen_at": None,
    "entity_type": "github_issue",
    "entity_id": "karolswdev/HoldSpeak#412",
    "project_id": None,
}
# Tokens that can only appear if the selected record reached the model. Kept to
# the unmistakable ones (the issue number and the flag/command names) so a
# control run can't match them by chance off the payments/ledger .hs context.
ISSUE_TOKENS = ("412", "--since", "since flag", "export command")

PASS = True


def check(label: str, cond: bool) -> None:
    global PASS
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        PASS = False


def reachable(base_url: str) -> bool:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=2.0):
            return True
    except OSError:
        return False


def run_once(*, selected: bool) -> str:
    """Run the real project-rewriter once; return the rewritten text."""
    from holdspeak.config import DictationConfig, DictationPipelineConfig, LLMRuntimeConfig
    from holdspeak.plugins.dictation.assembly import build_pipeline
    from holdspeak.plugins.dictation.contracts import Utterance
    from holdspeak.plugins.dictation.project_root import detect_project_for_cwd

    cfg = DictationConfig(
        pipeline=DictationPipelineConfig(
            enabled=True,
            stages=["project-rewriter"],  # isolate the rewrite under test
            rewrite_passes=1,
            target_profile_override="claude_code",
            max_total_latency_ms=120_000,
        ),
        runtime=LLMRuntimeConfig(
            backend="openai_compatible",
            openai_compatible_model=MODEL,
            openai_compatible_base_url=BASE_URL,
            openai_compatible_timeout_seconds=90.0,
        ),
    )
    project = detect_project_for_cwd(DEMO_PROJECT, prefer_agent_session=False)
    if project is None:
        raise RuntimeError(f"no project detected under {DEMO_PROJECT}")

    build = build_pipeline(cfg, project_root=DEMO_PROJECT)
    if build.runtime_status != "loaded":
        raise RuntimeError(f"runtime not loaded: {build.runtime_status} ({build.runtime_detail})")

    target = {"id": "claude_code", "label": "Claude Code", "confidence": 0.95, "source": "override"}
    activity: dict = {"target": target}
    if selected:
        # Exactly the shape build_activity_context(selected_record_id=412) emits.
        activity["selected_record_id"] = 412
        activity["records"] = [SELECTED_RECORD]

    run = build.pipeline.run(
        Utterance(
            raw_text=SPOKEN,
            audio_duration_s=0.0,
            transcribed_at=datetime.now(),
            project=project,
            activity=activity,
        )
    )
    return run.final_text


def main() -> int:
    print("== Phase 53 real-metal dogfood: dictate-with-this on a live LLM ==\n")
    print(f"  endpoint: {BASE_URL}  model: {MODEL}\n")
    if not reachable(BASE_URL):
        print(f"SKIP: endpoint {BASE_URL} not reachable (set HOLDSPEAK_DICTATION_E2E_BASE_URL).")
        return 0

    print("-- CONTROL: no selection --")
    control = run_once(selected=False)
    print(f"  output: {control}\n")

    print("-- TREATMENT: 'Dictate with this' on github_issue karolswdev/HoldSpeak#412 --")
    treatment = run_once(selected=True)
    print(f"  output: {treatment}\n")

    c_low, t_low = control.lower(), treatment.lower()
    c_hits = [tok for tok in ISSUE_TOKENS if tok in c_low]
    t_hits = [tok for tok in ISSUE_TOKENS if tok in t_low]

    print("-- assertions --")
    check("both runs produced non-empty output", bool(control.strip()) and bool(treatment.strip()))
    check(
        f"TREATMENT references the selected issue (matched: {t_hits or 'none'})",
        bool(t_hits),
    )
    check(
        f"CONTROL does NOT reference the issue (matched: {c_hits or 'none'})",
        not c_hits,
    )
    check("the selection changed the output", control.strip() != treatment.strip())

    print()
    print("RESULT: PASS" if PASS else "RESULT: FAIL")
    return 0 if PASS else 1


if __name__ == "__main__":
    sys.exit(main())
