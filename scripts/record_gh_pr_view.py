"""Record one real ``gh pr view --json`` answer for the PR read tests (Betterment MCP M6).

    uv run python scripts/record_gh_pr_view.py [--repo karolswdev/HoldSpeak] [--number 1301]

Runs the exact command ``GitHubProviderAdapter.pr_get`` runs, with the owner's
own ``gh`` sign-in, against one pull request of his own repository, and writes
its answer to ``tests/fixtures/automations/gh_pr_view.json``. The tests replay
it through an injected gh runner: no test calls GitHub.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "automations" / "gh_pr_view.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default="karolswdev/HoldSpeak")
    parser.add_argument("--number", type=int, default=1301)
    args = parser.parse_args()

    from holdspeak.services.github_provider import PR_VIEW_FIELDS

    command = ["gh", "pr", "view", str(args.number), "-R", args.repo, "--json", PR_VIEW_FIELDS]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)  # noqa: S603
    OUT.write_text(json.dumps({
        "about": "One real answer of the command GitHubProviderAdapter.pr_get runs, recorded by "
                 "scripts/record_gh_pr_view.py with the owner's gh sign-in. Never hand-edit it.",
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": command,
        "repository": args.repo,
        "number": args.number,
        "stdout": json.loads(completed.stdout),
    }, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
