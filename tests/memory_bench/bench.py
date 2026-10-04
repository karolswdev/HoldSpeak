"""Run the benchmark questions against one database and give the measures."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
FIXTURE = HERE / "vectors.npz"
BASELINE = HERE / "baseline.json"
GOLDEN = HERE / "keyword_golden.json"


def load_questions() -> list[dict[str, Any]]:
    return json.loads((HERE / "questions.json").read_text())["questions"]


def _base(ref: str) -> str:
    return ref.split("#", 1)[0]


def run(db: Any, refs: dict[str, str], *, limit: int = 10) -> dict[str, Any]:
    """Ask every question through ``db.memory.search``.

    Returns the measures per group and the ranked refs per question.
    """
    groups: dict[str, dict[str, float]] = {}
    ranked: dict[str, list[str]] = {}
    for question in load_questions():
        try:
            hits = db.memory.search(
                question["q"], project_id=question.get("project"), limit=limit
            ).hits
        except ValueError:
            hits = []
        got = list(dict.fromkeys(_base(hit.source_ref) for hit in hits))
        ranked[question["id"]] = got
        expected = {refs[label] for label in question["expect"]}
        position = next((index for index, ref in enumerate(got, start=1) if ref in expected), 0)
        group = groups.setdefault(
            question["group"], {"n": 0, "recall@5": 0.0, "recall@10": 0.0, "mrr": 0.0}
        )
        group["n"] += 1
        group["recall@5"] += 1.0 if 0 < position <= 5 else 0.0
        group["recall@10"] += 1.0 if 0 < position <= 10 else 0.0
        group["mrr"] += (1.0 / position) if position else 0.0
    for group in groups.values():
        count = group["n"] or 1
        for key in ("recall@5", "recall@10", "mrr"):
            group[key] = round(group[key] / count, 4)
    return {"groups": groups, "ranked": ranked}


def table(label: str, measures: dict[str, Any]) -> str:
    lines = [f"memory bench — {label}"]
    for name, group in sorted(measures["groups"].items()):
        lines.append(
            f"  {name:<11} n={int(group['n']):<3} recall@5={group['recall@5']:.3f}"
            f"  recall@10={group['recall@10']:.3f}  mrr={group['mrr']:.3f}"
        )
    return "\n".join(lines)


def keyword_snapshot(db: Any, refs: dict[str, str]) -> dict[str, Any]:
    """The full ``memory.search`` answer for every question, made stable.

    A thread id is minted at random and a thread time is the wall clock, so
    both are replaced by the corpus label.  Everything else is the answer
    as the callers get it.  ``keyword_golden.json`` holds this snapshot made
    by the search code BEFORE the memory index existed; the test compares the
    no-engine answer with it, value for value.
    """
    labels = sorted(
        ((ref.split(":", 1)[1], label) for label, ref in refs.items() if ref.startswith("thread:")),
        key=lambda pair: -len(pair[0]),
    )
    snapshot: dict[str, Any] = {}
    for question in load_questions():
        for scope in (None, question.get("project")) if question.get("project") else (None,):
            try:
                answer = db.memory.search(question["q"], project_id=scope, limit=50).to_dict()
            except ValueError as exc:
                answer = {"error": str(exc)}
            text = json.dumps(answer, sort_keys=True, ensure_ascii=False)
            for thread_id, label in labels:
                text = text.replace(thread_id, label)
            stable = json.loads(text)
            for hit in stable.get("hits", []):
                if hit["kind"] == "thread":
                    hit["occurred_at"] = "<thread time>"
                    hit["source_ref"] = hit["source_ref"].split("#", 1)[0]
            snapshot[f"{question['id']}|{scope or ''}"] = stable
    return snapshot
