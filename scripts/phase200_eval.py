#!/usr/bin/env python3
"""Evaluate one model route against the Phase 200 quality corpus (HS-200-08).

Two subcommands:

``manifest``
    Rebuild ``tests/fixtures/phase200/corpus/manifest.json`` from the episode
    files.  The manifest never leads the episodes; it is derived from them.

``run``
    Drive each episode through the REAL product path for its category --
    the Interview thread, the meeting plugin chain, the Project update
    drafter -- with the selected model route, judge the outputs with the
    deterministic checks, and write a report.

The run is isolated: a temporary HOME, a temporary database, and a
temporary model root.  It never reads or writes the owner's data.

    # the owner's live route (see docs/internal/architect-assistant/proof/SCORING.md)
    uv run python scripts/phase200_eval.py run \
        --endpoint http://192.168.1.43:8080/v1 --model qwen2.5-32b-instruct \
        --report .tmp/phase200-eval.json

    # the harness itself, with the model substituted (no network)
    uv run python scripts/phase200_eval.py run --engine canned \
        --canned tests/fixtures/phase200/canned/harness.json --report .tmp/eval.json

An LLM judge is a supplementary column only.  It is off by default, it is
never consulted for a pass or fail, and a critical factual failure is a
failure however any judge scored it.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
import traceback
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Mapping
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tests.fixtures.phase200 import checks  # noqa: E402

#: An interrupt or an exit is the operator speaking, never a trial result.
#: Everything else -- including the deliberate ``BaseException`` failures the
#: plugin kernel raises so a provider fault cannot be laundered into a result
#: (holdspeak/plugins/intelligence.py, PluginProviderFailure) -- is data.
CONTROL_SIGNALS = (KeyboardInterrupt, SystemExit)

#: How the split was drawn.  Recorded in the manifest so a later reader can
#: see that it did not follow the results.
SPLIT_RULE = (
    "Each episode's split was assigned when the episode was authored (HS-200-08, "
    "corpus version 1), before any prompt or recipe change was measured against "
    "it. Held-out episodes are acceptance evidence: a tuning step that reaches "
    "for one raises HeldOutEpisodeError (tests/fixtures/phase200/checks.py, "
    "read_for_tuning). Every category keeps at least one third held out. Real "
    "failures may be added as train regression cases; the held-out set is only "
    "ever extended, never rewritten to match a result."
)


# ── Report assembly ───────────────────────────────────────────────────


def _identity() -> dict[str, Any]:
    """Build identity from HS-200-02, so a report names the code that ran."""
    try:
        from holdspeak import runtime_identity

        identity = runtime_identity.capture_runtime_identity()
        payload = identity.to_dict() if hasattr(identity, "to_dict") else dict(identity)
        return {
            key: payload.get(key)
            for key in ("backend_build", "frontend_build", "schema_version", "config_revision", "started_at")
            if key in payload
        }
    except Exception as exc:  # pragma: no cover - identity is best effort
        return {"error": f"{type(exc).__name__}: {exc}"}


def build_report(
    *,
    episodes: list[Mapping[str, Any]],
    outputs: dict[str, Mapping[str, Any]],
    route: Mapping[str, Any],
    engine: str,
    judge: Mapping[str, Any] | None = None,
    aborted: str = "",
    aborted_traceback: str = "",
) -> dict[str, Any]:
    """The report every gate reads: what ran, on what, and what it cost.

    ``aborted`` is the loud column (HS-200-08 follow-through): when the run
    died before every selected episode had its turn -- a hub that could not
    boot, a route that could not resolve, a leaf that raised past the trial
    guard -- the report still lands and NAMES the reason. A reader (and a
    test) must never have to infer an abort from a missing key.
    """
    results = [checks.check_episode(episode, outputs.get(episode["id"], {})) for episode in episodes]

    failures_by_kind: dict[str, int] = {}
    for result in results:
        for kind, count in result.failure_kinds().items():
            failures_by_kind[kind] = failures_by_kind.get(kind, 0) + count

    latencies = sorted(result.latency_ms for result in results if result.latency_ms)
    by_category: dict[str, dict[str, int]] = {}
    for category in checks.CATEGORIES:
        rows = [result for result in results if result.category == category]
        if not rows:
            continue
        by_category[category] = {
            "episodes": len(rows),
            "passed": len([row for row in rows if row.passed]),
            "critical": len([row for row in rows if row.critical]),
        }

    critical = [result for result in results if result.critical]
    report: dict[str, Any] = {
        "harness": "phase200_eval",
        "protocol_version": 1,
        "corpus_version": checks.CORPUS_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "engine": engine,
        "model": route.get("model", ""),
        "route": dict(route),
        "build": _identity(),
        "episodes": [result.to_dict() for result in results],
        "totals": {
            "episodes": len(results),
            "passed": len([result for result in results if result.passed]),
            "failed": len([result for result in results if not result.passed]),
            "critical_failures": len(critical),
            "by_category": by_category,
            "by_split": {
                split: len([result for result in results if result.split == split])
                for split in checks.SPLITS
            },
        },
        "failures_by_kind": dict(sorted(failures_by_kind.items())),
        "support_judgments": checks.support_judgments(outputs.values()),
        "latency_ms": {
            "count": len(latencies),
            "min": latencies[0] if latencies else 0.0,
            "median": latencies[len(latencies) // 2] if latencies else 0.0,
            "max": latencies[-1] if latencies else 0.0,
        },
        "review_effort": checks.review_effort(results),
        "aborted": aborted,
        "aborted_traceback": aborted_traceback if aborted else "",
        "verdict": "fail" if (aborted or critical or any(not r.passed for r in results)) else "pass",
        "critical_verdict": "fail" if critical else "pass",
        "judge": dict(judge) if judge else {"enabled": False, "note": "supplementary only; never gating"},
    }
    return report


def summarise(report: Mapping[str, Any]) -> str:
    totals = report["totals"]
    lines = [
        f"corpus {report['corpus_version']} · engine {report['engine']} · model {report['model'] or 'n/a'}",
        f"route: {json.dumps(report['route'], sort_keys=True)}",
        f"episodes {totals['episodes']} · passed {totals['passed']} · failed {totals['failed']} "
        f"· critical {totals['critical_failures']}",
        f"failures by kind: {json.dumps(report['failures_by_kind'], sort_keys=True) or '{}'}",
        f"support judgments: {json.dumps(report['support_judgments'], sort_keys=True) or '{}'}",
        f"review effort: {report['review_effort']['total']} item(s) to inspect",
        f"verdict: {report['verdict']} (critical: {report['critical_verdict']})",
    ]
    if report.get("aborted"):
        lines.insert(0, f"aborted: {report['aborted']}")
    return "\n".join(lines)


# ── The manifest subcommand ───────────────────────────────────────────


def command_manifest(args: argparse.Namespace) -> int:
    episodes = checks.load_corpus()
    manifest = checks.build_manifest(episodes, split_rule=SPLIT_RULE)
    text = json.dumps(manifest, indent=2) + "\n"
    if args.check:
        current = checks.MANIFEST_PATH.read_text() if checks.MANIFEST_PATH.exists() else ""
        if current != text:
            print("manifest is stale: uv run python scripts/phase200_eval.py manifest", file=sys.stderr)
            return 1
        print(f"manifest current: {manifest['episode_count']} episodes")
        return 0
    checks.MANIFEST_PATH.write_text(text)
    print(f"wrote {checks.MANIFEST_PATH} ({manifest['episode_count']} episodes)")
    for category, counts in manifest["counts"].items():
        print(f"  {category}: {counts['total']} ({counts['held_out']} held out)")
    return 0


# ── The run subcommand ────────────────────────────────────────────────


def _select(episodes: list[Mapping[str, Any]], args: argparse.Namespace) -> list[Mapping[str, Any]]:
    rows = list(episodes)
    if args.split != "all":
        rows = [episode for episode in rows if episode["split"] == args.split]
    if args.category != "all":
        rows = [episode for episode in rows if episode["category"] == args.category]
    if args.episode:
        wanted = {value.upper() for value in args.episode}
        rows = [episode for episode in rows if episode["id"].upper() in wanted]
    if args.limit:
        per_category: dict[str, int] = {}
        kept = []
        for episode in rows:
            seen = per_category.get(episode["category"], 0)
            if seen >= args.limit:
                continue
            per_category[episode["category"]] = seen + 1
            kept.append(episode)
        rows = kept
    return rows


def _drive(
    *,
    args: argparse.Namespace,
    episodes: list[Mapping[str, Any]],
    canned: Mapping[str, Any],
    outputs: dict[str, Any],
    route: dict[str, Any],
    collectors: Any,
) -> Mapping[str, Any] | None:
    """Boot the isolated hub, run every selected episode, return the judge column.

    Anything that escapes this is an ABORT: the run did not finish. Its caller
    still writes the report, naming the reason.
    """
    judge: Mapping[str, Any] | None = None
    with ExitStack() as stack:
        home = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix="holdspeak-phase200-eval-")))
        original_expanduser = os.path.expanduser

        def expanduser(path):
            value = os.fspath(path)
            if isinstance(value, str) and (value == "~" or value.startswith("~/")):
                return str(home) + value[1:]
            return original_expanduser(path)

        stack.enter_context(patch.object(Path, "home", return_value=home))
        stack.enter_context(patch("os.path.expanduser", side_effect=expanduser))

        hub = stack.enter_context(
            collectors.evaluation_hub(
                home=home,
                engine=args.engine,
                endpoint=args.endpoint,
                model=args.model,
                canned=canned,
            )
        )
        route.update(hub.route_facts())

        for repetition in range(args.repeat):
            for episode in episodes:
                key = episode["id"] if repetition == 0 else f"{episode['id']}#{repetition + 1}"
                started = time.monotonic()
                try:
                    output = hub.run_episode(episode)
                except CONTROL_SIGNALS:
                    raise
                except BaseException as exc:  # a failed trial is retained, never dropped
                    # BaseException, not Exception: the plugin kernel's provider
                    # failures are BaseException BY DESIGN (holdspeak/plugins/
                    # intelligence.py, PluginProviderFailure), and an `except
                    # Exception` here let one of them abort the whole run before
                    # a single line of report was written.
                    output = {
                        "error": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc(limit=6),
                    }
                output.setdefault("latency_ms", (time.monotonic() - started) * 1000.0)
                outputs[key] = output
                mark = "!" if output.get("error") else "."
                print(f"{mark} {key}", flush=True)

        if args.judge:
            # A supplementary column, asked of the same route after every
            # episode has run. It cannot change a verdict; see build_report.
            judge = hub.judge_outputs(list(episodes), outputs)
    return judge


def command_run(args: argparse.Namespace) -> int:
    from tests.fixtures.phase200 import collectors  # local: imports the product

    episodes = _select(checks.load_corpus(), args)
    if not episodes:
        print("no episodes selected", file=sys.stderr)
        return 2

    canned: dict[str, Any] = {}
    if args.engine == "canned":
        if not args.canned:
            print("--engine canned needs --canned <file>", file=sys.stderr)
            return 2
        canned = json.loads(Path(args.canned).read_text())
    elif not (args.endpoint and args.model):
        print("--engine route needs --endpoint and --model", file=sys.stderr)
        return 2

    outputs: dict[str, Any] = {}
    route: dict[str, Any] = {
        "engine": args.engine,
        "model": args.model or ("canned" if args.engine == "canned" else ""),
        "endpoint": args.endpoint or "",
        "plan_id": "",
        "boundary": "",
        "host": "",
    }

    judge: Mapping[str, Any] | None = None
    aborted = ""
    aborted_traceback = ""
    try:
        judge = _drive(
            args=args,
            episodes=episodes,
            canned=canned,
            outputs=outputs,
            route=route,
            collectors=collectors,
        )
    except CONTROL_SIGNALS:
        raise
    except BaseException as exc:
        # The run died before every episode had its turn. The report is still
        # written and NAMES the reason, so a reader never has to read an abort
        # out of a missing key.
        aborted = f"{type(exc).__name__}: {exc}"
        aborted_traceback = traceback.format_exc(limit=12)
        print(f"\nABORTED: {aborted}", file=sys.stderr, flush=True)

    repeated = [
        dict(episode, id=f"{episode['id']}#{index + 1}")
        for index in range(1, args.repeat)
        for episode in episodes
    ]
    report = build_report(
        episodes=list(episodes) + repeated,
        outputs=outputs,
        route=route,
        engine=args.engine,
        judge=judge,
        aborted=aborted,
        aborted_traceback=aborted_traceback,
    )
    report["repeat"] = args.repeat
    if args.raw:
        Path(args.raw).parent.mkdir(parents=True, exist_ok=True)
        Path(args.raw).write_text(json.dumps(outputs, indent=2, default=str) + "\n")
        report["raw_outputs"] = str(args.raw)

    text = json.dumps(report, indent=2, default=str) + "\n"
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(text)
        print(f"\nreport: {args.report}")
    else:
        print(text)
    print(summarise(report))
    if aborted:
        return 1
    return 0 if report["critical_verdict"] == "pass" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    manifest = sub.add_parser("manifest", help="rebuild the corpus manifest from the episode files")
    manifest.add_argument("--check", action="store_true", help="fail when the committed manifest is stale")
    manifest.set_defaults(func=command_manifest)

    run = sub.add_parser("run", help="evaluate a route against the corpus")
    run.add_argument("--engine", choices=("route", "canned"), default="route")
    run.add_argument("--endpoint", default="", help="an existing compatible endpoint, including /v1")
    run.add_argument("--model", default="", help="the actual endpoint model id")
    run.add_argument("--canned", default="", help="canned model outputs (--engine canned)")
    run.add_argument("--split", choices=("all", *checks.SPLITS), default="all")
    run.add_argument("--category", choices=("all", *checks.CATEGORIES), default="all")
    run.add_argument("--episode", action="append", default=[], help="run only these episode ids")
    run.add_argument("--limit", type=int, default=0, help="at most N episodes per category")
    run.add_argument("--repeat", type=int, default=1, help="repeat the selection N times to expose variability")
    run.add_argument(
        "--judge",
        action="store_true",
        help="add the supplementary model-judge column (off by default; never gating)",
    )
    run.add_argument("--report", default="", help="where to write the JSON report")
    run.add_argument("--raw", default="", help="where to write the raw per-episode outputs")
    run.set_defaults(func=command_run)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
