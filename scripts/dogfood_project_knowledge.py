#!/usr/bin/env python3
"""HS-47-03 dogfood: a fresh repo to working project-aware dictation, no file editing.

Drives the guided-setup endpoints the UI uses, against a fresh temp project, and
proves a Project Fact reaches dictation output end to end:

  1. detect the project (a bare repo with only a pyproject.toml),
  2. create starter Project Facts (writes .holdspeak/project.yaml),
  3. set the `stack` fact to a real value,
  4. add the "Project facts context" starter block (which references the fact),
  5. scaffold a starter Project Context set (.hs/ files),
  6. run a dry-run and confirm the fact is stamped into the final text.

Every write goes through the same HTTP endpoints the browser calls; nothing is
hand-edited on disk. No microphone is needed. The local model is stood in for by
a deterministic stub runtime (the same one the dry-run integration tests use), so
the intent-router matches without a real LLM. Run after building the web bundle
is not required (this is API-only).

    .venv/bin/python scripts/dogfood_project_knowledge.py
    .venv/bin/python scripts/dogfood_project_knowledge.py <transcript.txt>
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

# The curated context starter the UI ships (kept in lockstep with
# web/src/scripts/dictation-app.js STARTER_HS_FILES).
STARTER_HS_FILES = {
    "instructions.md": "# How HoldSpeak should rewrite for this project\n\n- Keep dictation terse and imperative.\n",
    "context.md": "# Project context\n\n- What this repo is: <one line>\n",
    "terms.md": "# Project vocabulary\n\n- <ProductName>: what we call it in writing.\n",
}

STACK_VALUE = "Rails 7 + Postgres 16"


class _StubRuntime:
    """Deterministic stand-in for the local model: always matches the first
    available block so the intent-router routes without a real LLM."""

    backend = "stub"

    def __init__(self, block_id: str | None = None) -> None:
        self.block_id = block_id

    def load(self) -> None:
        pass

    def info(self) -> dict:
        return {"backend": "stub"}

    def classify(self, prompt, schema, *, max_tokens=128, temperature=0.0):
        block_id = self.block_id or (schema.block_ids[0] if schema.block_ids else None)
        return {
            "matched": block_id is not None,
            "block_id": block_id,
            "confidence": 0.95 if block_id is not None else 0.0,
            "extras": {},
        }

    def rewrite(self, prompt, *, max_tokens=512, temperature=0.15):
        return "rewritten text"


def main(argv: list[str]) -> int:
    from fastapi.testclient import TestClient

    import holdspeak.config as config_module
    from holdspeak.config import Config
    from holdspeak.plugins.dictation import assembly as assembly_module
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    out_path = Path(argv[0]) if argv else None
    lines: list[str] = []

    def say(msg: str) -> None:
        print(msg)
        lines.append(msg)

    tmp = Path(tempfile.mkdtemp())
    root = tmp / "ledgerline"
    root.mkdir(parents=True)
    (root / "pyproject.toml").write_text('[project]\nname = "ledgerline"\n', encoding="utf-8")
    root_str = str(root)

    # A temp config (pipeline on) + a temp global blocks file so we never touch
    # the developer's real state.
    config_module.CONFIG_FILE = tmp / "config.json"
    cfg = Config()
    cfg.dictation.pipeline.enabled = True
    cfg.save(path=config_module.CONFIG_FILE)
    assembly_module.DEFAULT_GLOBAL_BLOCKS_PATH = tmp / "global-blocks.yaml"

    # The local model stand-in: route to our fact-consuming block.
    original_build_runtime = assembly_module.build_runtime
    assembly_module.build_runtime = lambda **_kwargs: _StubRuntime("project_facts_context")

    say("HS-47-03 dogfood — fresh repo to working project-aware dictation")
    say(f"  fresh project: {root_str} (only a pyproject.toml; no .holdspeak, no .hs)")
    say("")

    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=MagicMock(),
                on_stop=MagicMock(),
                get_state=MagicMock(return_value={}),
            )
        )
        client = TestClient(server.app)

        # 1. detect.
        r = client.get(f"/api/dictation/readiness?project_root={root_str}")
        assert r.status_code == 200, r.text
        say(f"1. detected project: {r.json()['project']['name']} (anchor: {r.json()['project']['anchor']})")

        # 2. starter facts (creates .holdspeak/project.yaml).
        r = client.post(f"/api/dictation/project-kb/starter?project_root={root_str}")
        assert r.status_code == 201, r.text
        kb_path = Path(r.json()["kb_path"])
        assert kb_path.exists(), kb_path
        say(f"2. created starter facts -> {kb_path}")

        # 3. set the `stack` fact to a real value (the row a user would type).
        r = client.put(
            f"/api/dictation/project-kb?project_root={root_str}",
            json={"kb": {"stack": STACK_VALUE, "task_focus": None, "constraints": None}},
        )
        assert r.status_code == 200, r.text
        say(f"3. set fact   stack = {STACK_VALUE!r}")

        # 4. add the fact-consuming starter block at project scope.
        r = client.post(
            f"/api/dictation/blocks/from-template?scope=project&project_root={root_str}",
            json={"template_id": "project_facts_context"},
        )
        assert r.status_code in (200, 201), r.text
        say("4. added block 'project_facts_context' (references {project.kb.stack})")

        # 5. scaffold a starter context set (.hs/ files).
        r = client.put(
            f"/api/dictation/project-hs?project_root={root_str}",
            json={"files": STARTER_HS_FILES},
        )
        assert r.status_code == 200, r.text
        hs_dir = root / ".hs"
        created = sorted(p.name for p in hs_dir.glob("*") if p.is_file())
        for name in STARTER_HS_FILES:
            assert (hs_dir / name).exists(), name
        say(f"5. scaffolded context -> .hs/ {created}")

        # 6. dry-run: the fact must reach the final text.
        r = client.post(
            "/api/dictation/dry-run",
            json={"utterance": "help me refactor the payments module", "project_root": root_str},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        final_text = body["final_text"]
        assert STACK_VALUE in final_text, f"fact not stamped; got: {final_text!r}"
        stages = [s["stage_id"] for s in body["stages"]]
        say("")
        say(f"6. dry-run utterance: 'help me refactor the payments module'")
        say(f"   stages: {stages}")
        say(f"   final text: {final_text!r}")
        say("")
        say(f"PASS: the fact {STACK_VALUE!r} reached dictation output with zero file editing.")
    finally:
        assembly_module.build_runtime = original_build_runtime

    if out_path is not None:
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nWrote transcript: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
