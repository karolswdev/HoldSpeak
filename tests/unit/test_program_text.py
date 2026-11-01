"""PG-LANG LANG1 (2026-10-31): the Program text, parse, print and diff.

PROGRAM-LANGUAGE-2026-10-31.md §3: the grammar (each example of §3.7), the
round-trip rule (every recorded fixture, every template's planned Program,
500 generated Programs), the change rows of §3.8 with the frozen table's
reasons (§3.5), the refusals of §3.9, the rows that lower the bar (§4.5),
and ``text_apply`` through the service verbs (a dry run writes nothing; a
real apply writes each change, one summary checkpoint and one frame).
"""
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import pytest

from holdspeak.delivery.pi_launch import LibraryEngine, PiEngine
from holdspeak.program_templates import TEMPLATE_IDS
from holdspeak.services.program_service import FROZEN_BAR, FROZEN_READ, FROZEN_SET
from holdspeak.services.program_text import (
    Amendment, Head, ProgramText, Question, Requirement, Round, Step, canonical, diff_program_text, from_wire,
    guessed_spec, parse_night, parse_program_text, print_program, render, wire_lamps,
)
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

FIXTURES = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "programs" / "__fixtures__"
QWEN = LibraryEngine("engine-tailscale-karol-8080", "qwen3.8-27b on karol", PiEngine(
    endpoint="http://karol:8080/v1", model="qwen3.8-27b", context_window=32768, key_slot="",
    host="karol:8080", boundary="private"))


def _engines(engine_id: str):
    return QWEN if engine_id == QWEN.profile_id else None


def _wires() -> list[tuple[str, dict[str, Any]]]:
    """Every recorded Program answer (a whole Program, or one inside a
    press's answer)."""
    out = []
    for path in sorted(FIXTURES.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        nested = [value.get("program"), (value.get("applied") or {}).get("program")] if isinstance(value, dict) else []
        for wire in (value, *nested):
            if isinstance(wire, dict) and "steps" in wire and "control" in wire:
                out.append((path.name, wire))
    return out


def _rows(text_a: str, text_b: str, record: Any = None) -> list[tuple[str, str, str, str]]:
    return [(row.op, row.where, row.field, row.verdict) for row in diff_program_text(text_a, text_b, record=record)]


# ── the grammar: §3.7's five examples ────────────────────────────────

FAST_CYCLE = """# program text 1
program Hub loop budget
  in HoldSpeak · main · project HoldSpeak
  template fast cycle
  control yolo

every step
  R1 review: The change does only what its brief says.

step 1 Pipeline events index
  owns holdspeak/db/pipeline_events.py
  brief
  > Add the (kind, at) index; the Needs you scan reads 1.39M rows today.

step 2 Retention thread
  owns holdspeak/db/pipeline_events_retention.py
  brief
  > Prune READ receipts older than HOLDSPEAK_EVENT_RETENTION_DAYS in a daemon thread.

step 3 Loop watch
  owns holdspeak/web/loop_watch.py
  after 1
  brief
  > Log each handler that holds the event loop over 100 ms when HOLDSPEAK_LOOP_WATCH=1.
  R4 check: `uv run pytest -q tests/unit/test_hub_loop_budget.py` is green.
"""

OVERNIGHT = """program Words wave, part 3
  in HoldSpeak · main
  template overnight
  agent pi on qwen3.8-27b, then Claude Code
  budget 64k
  when idle · may call

step 1 Settings words
  owns web/src/desk/settings/
  brief
  > Every Settings label in ASD-STE100. Keep the ids.
"""

RACE = """program Faster sweep
  in HoldSpeak · main
  template race

step 1 Sweep in one browser
  race 2
  agent Claude Code, then Codex
  brief
  > Run every case of tests/e2e/test_desk_sweep.py in one browser context.
  R2 measure: The sweep takes under 6 minutes.
    run uv run pytest -q tests/e2e/test_desk_sweep.py --durations=0
    bound total < 6 min
"""

FROM_THE_DESK = """program Atlas wave 6
  in HoldSpeak · main · project HoldSpeak
  template from the desk

step 1 Cite the Calls window in the atlas
  from action:act-91c2
step 2 Cite the Line settings in the atlas
  from action:act-91c3
"""


def test_the_fast_cycle_example_reads_whole() -> None:
    model = parse_program_text(FAST_CYCLE)
    assert model.errors == []
    head = model.head
    assert (head.title, head.repository, head.branch, head.project, head.template, head.control) == (
        "Hub loop budget", "HoldSpeak", "main", "HoldSpeak", "fast-cycle", "yolo")
    assert [(row.rid, row.kind, row.text) for row in model.every_step] == [
        (1, "review", "The change does only what its brief says.")]
    three = model.step(3)
    assert three is not None and three.after == [1] and three.owns == ["holdspeak/web/loop_watch.py"]
    assert three.brief == "Log each handler that holds the event loop over 100 ms when HOLDSPEAK_LOOP_WATCH=1."
    # The kind rule fills the command from the backticks: no ``run`` line.
    assert three.requirements[0].spec == {"command": "uv run pytest -q tests/unit/test_hub_loop_budget.py"}
    # Defaults are not stated, so they stay None (the rule's value).
    assert (three.agents, three.effort, three.review, three.merge, three.check) == (None, None, None, None, None)


def test_the_overnight_example_reads_its_budget() -> None:
    model = parse_program_text(OVERNIGHT)
    assert model.errors == []
    assert model.head.budget == 65536  # 64k
    assert "  budget 64k\n" in render(model)
    assert model.head.agents == [("pi-default", "qwen3.8-27b"), ("claude-default", None)]
    assert (model.head.when_idle, model.head.may_call) == (True, True)  # one line, joined with ·


def test_the_race_example_reads_its_measure() -> None:
    model = parse_program_text(RACE)
    assert model.errors == []
    step = model.step(1)
    assert [(row.rid, row.kind, row.spec) for row in step.requirements] == [
        (2, "measure", {"command": "uv run pytest -q tests/e2e/test_desk_sweep.py --durations=0",
                        "metric": "total", "op": "<", "bound": 6, "unit": "min"})]
    assert render(model).endswith("    run uv run pytest -q tests/e2e/test_desk_sweep.py --durations=0\n"
                                  "    bound total < 6 min\n")
    assert step is not None and step.agents == [("claude-default", None), ("codex-default", None)]
    assert step.race is None  # the Race template's own 2: a default, not stated


def test_the_from_the_desk_example_keeps_each_origin() -> None:
    model = parse_program_text(FROM_THE_DESK)
    assert model.errors == []
    assert [(step.number, step.origin) for step in model.steps] == [(1, "action:act-91c2"), (2, "action:act-91c3")]


RUNNING_BASE = """# program text 1
program Running
  in app · main
  control normal

step 5 Projects routes                            # Findings · round 2
  owns holdspeak/web/routes/projects.py
  agent Claude Code
  R6 review: No new route skips the residual set.  # Unmet · round 2

step 6 The fan-out                                # Planned
  after 4, 5
"""

RUNNING_CHANGED = """# program text 1
program Running
  in app · main
  control normal

step 5 Projects routes
  owns holdspeak/web/routes/projects.py
  agent Claude Code, then Codex
  R6 review: No new route skips the residual set.
  + The fold route needs its residual-set entry.

step + The loop watch
  after 4
  agent pi on qwen3.8-27b · effort low
  brief
  > Log handlers over 100 ms.

step 6 The fan-out
  after 4, 5, 7
  merge owner
"""


def test_the_running_example_gives_the_rows_of_the_diff_form() -> None:
    """§3.8: the text alone (no record) gives every change as allowed, in
    reading order; ``after 4`` names a step outside the text, so that row
    names it."""
    rows = diff_program_text(RUNNING_BASE, RUNNING_CHANGED)
    shown = [(row.op, row.where, row.field) for row in rows if row.op != "read"]
    assert shown == [
        ("change", "step 5", "agent"), ("amend", "step 5", "amend"),
        ("add", "step 7", "step"), ("move", "step 7", "position"),
        ("change", "step 6", "after"), ("change", "step 6", "merge"),
    ]
    assert rows[0].before == "Claude Code" and rows[0].after == "Claude Code, then Codex"
    move = next(row for row in rows if row.op == "move")
    assert move.after == "before step 6"
    reads = [row for row in rows if row.op == "read"]
    assert {row.code for row in reads} == {"text_bad_value"}  # step 4 is not in this cut of the text


def test_lamps_are_ignored_and_his_words_are_kept_byte_for_byte() -> None:
    text = ("program P  # Running · 1 of 2 done\n  in app · main\n  goal\n  > # A heading, kept  # with its hash\n"
            "  >\n  >   indented line  \n\nstep 1 A    # Merged #12 · 41 min\n  brief\n  > Use `x`  # not a lamp here\n")
    model = parse_program_text(text)
    assert model.errors == []
    assert model.head.goal == "# A heading, kept  # with its hash\n\n  indented line  "
    assert model.step(1).title == "A" and model.step(1).brief == "Use `x`  # not a lamp here"


def test_the_version_line_and_the_refusals_by_name() -> None:
    assert parse_program_text("# program text 2\nprogram P\n").errors[0].code == "text_version"
    assert "version 2; this hub reads version 1" in parse_program_text("# program text 2\nprogram P\n").errors[0].words
    errors = parse_program_text("program P\n  budjet 12\n\nstep 1 A\n  effort huge\n").errors
    assert [(error.line, error.code) for error in errors] == [(2, "text_unknown_word"), (5, "text_bad_value")]
    assert errors[0].words == "Line 2: 'budjet' is not a word of the program text."
    assert errors[1].words == "Line 5: effort is low, medium or high."
    assert parse_program_text("step 1 A\n").errors[-1].words == "Line 1: the text has no 'program' line."


# ── the round-trip rule (§3.3) ───────────────────────────────────────

def test_every_recorded_program_round_trips() -> None:
    wires = _wires()
    assert len(wires) >= 20, [name for name, _ in wires]
    for name, wire in wires:
        text = print_program(wire)
        model = parse_program_text(text)
        assert model.errors == [], (name, model.errors)
        assert model == from_wire(wire), name                         # 1. parse(print(p)) is p
        assert render(model, wire_lamps(wire)) == text, name          # 2. print(parse(t)) is t
        assert diff_program_text(text, text, record=wire) == [], name  # 3. no change, no row
        assert text.startswith("# program text 1\n")


def test_the_journeys_texts_are_a_second_corpus() -> None:
    """PROGRAM-JOURNEYS-2026-10-31.md writes its texts to §3.2: each one
    reads, prints and reads again to the same model (lamps are ignored, so
    the bytes may differ). A word this hub does not store yet is refused by
    name and only that."""
    import re

    journeys = (Path(__file__).resolve().parents[2] / "docs" / "internal" / "betterment" / "programs"
                / "PROGRAM-JOURNEYS-2026-10-31.md").read_text(encoding="utf-8")
    texts = [block for block in re.findall(r"```\n(.*?)```", journeys, re.S) if re.search(r"^program ", block, re.M)]
    assert len(texts) >= 5
    for text in texts:
        model = parse_program_text(text)
        assert model.steps or model.every_step, text[:80]
        again = parse_program_text(render(model))
        assert again.errors == [] and again == model, text[:80]
        assert model.errors == [], (text[:80], model.errors)  # every word of §3.2 has a home


def test_every_templates_planned_program_round_trips(tmp_path) -> None:
    rig = Rig(tmp_path, engines=_engines)
    for template in TEMPLATE_IDS:
        pid = rig.service.create(OWNER, title=f"T {template}", goal="Two paragraphs.\n\nThe second one.",
                                 repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}", template=template)["id"]
        rig.service.plan(OWNER, pid, steps=[
            {"title": "Store", "brief": "Do the store.", "owns": ["holdspeak/db/programs.py"]},
            {"title": "Routes", "brief": "Do the routes.\n\nAll of them.", "after": [1], "gate_merge": "owner",
             "runs_on": ["codex", "claude"], "effort": "high"},
            {"title": "Copy on qwen", "brief": "Sweep.", "profile": "pi-default", "engine": QWEN.profile_id,
             "prefer_idle": True, "gate_check": False, "review_depth": "standard"},
        ])
        rig.service.require(OWNER, pid, text="`echo ok` is green", step_id=rig.step(pid, 2)["id"])
        rig.service.require(OWNER, pid, text="I tried it", kind="word", required=False,
                            spec={"walk": ["Open Programs at 393", "Press Plan it"]})
        rig.service.require(OWNER, pid, text="The routes answer fast", kind="measure", step_id=rig.step(pid, 1)["id"],
                            spec={"command": "sh bench.sh", "metric": "p95", "op": "<", "bound": 100, "unit": "ms"})
        rig.service.update(OWNER, pid, review_depth="standard", planner_engine=QWEN.profile_id, budget_tokens="64k",
                           night="23:30–07:00 · at most 8 steps", within=["holdspeak/", "docs/"],
                           rounds_before_start=True)
        rig.service.change_step(OWNER, pid, rig.step(pid, 1)["id"], budget_tokens=16384)
        rig.service.store.save_round({"program_id": pid, "name": "Architecture", "state": "asking", "ordinal": 1,
                                      "questions": [{"id": "q1", "text": "Hub or client?", "answer": None}],
                                      "updated_at": "2026-10-31T10:00:00Z"})
        wire = rig.program(pid)
        text = print_program(wire)
        model = parse_program_text(text)
        assert model.errors == [] and model == from_wire(wire), (template, text)
        assert diff_program_text(text, text, record=wire) == [], template
        assert rig.service.text_get(OWNER, pid)["text"] == text


def _random_text(rng: random.Random, template: Any) -> str:
    return " ".join(rng.choice(["the", "hub", "loop", "people", "route", "index", "step", "(x)", "`y`", "100", "ms"])
                    for _ in range(rng.randint(1, 8)))


def _random_requirement(rng: random.Random, rid: int) -> Requirement:
    kind = rng.choice(["check", "review", "shot", "word", "measure"])
    text = rng.choice(["`uv run pytest -q x.py` is green", "No route takes a lock", "The People window at 393 fits",
                       "I used it for a morning", "echo done prints done"])
    spec = guessed_spec(kind, text)
    if kind == "check" and rng.random() < 0.5:
        spec = {**spec, "command": "sh scripts/check.sh"}
    if kind == "check" and rng.random() < 0.3:
        spec = {**spec, "expect": r"\d+ passed"}
    if kind == "shot" and rng.random() < 0.5:
        spec = {"case": "programs", "width": rng.choice([393, 1440])}
    if kind == "measure":
        spec = {**spec, "command": rng.choice([spec.get("command") or "sh bench.sh", "sh bench.sh"]),
                **rng.choice([{"metric": "p95", "op": "<", "bound": 100, "unit": "ms"},
                              {"metric": "lost", "op": "=", "bound": 0, "unit": ""},
                              {"metric": "total", "op": "<=", "bound": 6.5, "unit": "min"}])}
        if rng.random() < 0.3:
            spec["expect"] = r"p95 \d+"
    if kind == "word" and rng.random() < 0.5:
        spec = {"walk": rng.sample(["Open Programs at 393", "Press Plan it", "See 6 steps"], rng.randint(1, 3))}
    return Requirement(rid=rid, kind=kind, text=text, required=rng.random() < 0.8, spec=spec,
                       waived=rng.choice([None, None, "Not this week."]))


def test_five_hundred_generated_programs_round_trip() -> None:
    rng = random.Random(1031)
    agents = [("claude-default", None), ("codex-default", None), ("pi-default", "engine-a"), ("pi-default", None)]
    for case in range(500):
        template = rng.choice([None, *TEMPLATE_IDS])
        rid = iter(range(1, 1000))
        head = Head(
            title=f"Program {case}", goal=rng.choice(["", "One line.", "Two\n\n> quoted  # kept\n  indent"]),
            repository="app", branch=rng.choice([None, "main", "dev"]), project=rng.choice([None, "HoldSpeak"]),
            control=rng.choice(["secure", "normal", "yolo"]), check=rng.choice(["", "sh check.sh"]),
            agents=rng.choice([None, [agents[0]], rng.sample(agents, 2)]),
            reviewer=rng.choice([None, ("none", None), ("codex-default", None)]),
            when_idle=rng.random() < 0.3, may_call=rng.random() < 0.3, may_hand_off=rng.random() < 0.3,
            allow=rng.choice([[], ["codex-default"], ["claude-default", "pi-default"]]),
            spend=rng.choice([None, 5.0, 2.5]), usage_warning=rng.choice([None, 0.9, 0.85]),
            for_person=rng.choice([None, "Alice"]), origin=rng.choice([None, "note:n-1"]), template=template,
            depth=rng.choice([None, "glance", "delta", "standard"]), planner=rng.choice([None, "qwen3.8-27b"]),
            budget=rng.choice([None, 65536, 32768, 50000]),
            night=rng.choice([None, parse_night("23:30–07:00 · at most 8 steps"), parse_night("01:00-05:30")]),
            within=rng.choice([[], ["web/src/desk/", "docs/"]]),
            delivery=rng.choice([None, "app/phase-3", "app/phase-3/story-01"]),
            rounds_before_start=rng.random() < 0.3,
        )
        model = ProgramText(head=head)
        model.rounds = rng.choice([[], [Round("Architecture", "done", [Question("Hub or client?", "The hub."),
                                                                       Question("Can it lose rows?", None)]),
                                        Round("Product", "asking", [Question("Who sees it first?")]),
                                        Round("Security", "open")]])
        model.every_step = [_random_requirement(rng, next(rid)) for _ in range(rng.randint(0, 2))]
        model.at_end = [_random_requirement(rng, next(rid)) for _ in range(rng.randint(0, 2))]
        for number in range(1, rng.randint(1, 7)):
            model.steps.append(Step(
                number=number, title=_random_text(rng, template) or "A step",
                owns=rng.sample(["a.py", "web/src/b.ts", "docs/c.md"], rng.randint(0, 3)),
                after=sorted(rng.sample(range(1, number), rng.randint(0, number - 1))) if number > 1 else [],
                agents=rng.choice([None, [rng.choice(agents)], rng.sample(agents, 2)]),
                effort=rng.choice([None, "low", "medium", "high"]), race=rng.choice([None, 0, 2, 3]),
                when_idle=rng.random() < 0.2, may_call=rng.random() < 0.2, check=rng.choice([None, True, False]),
                review=rng.choice([None, "none", "agent", "person"]), depth=rng.choice([None, "glance", "standard"]),
                merge=rng.choice([None, "level", "owner", "none"]), for_person=rng.choice([None, "Bob"]),
                origin=rng.choice([None, "action:a-1"]), budget=rng.choice([None, None, 16384, 20000]),
                merged=rng.choice([None, None, {"pr_number": 12, "merged_at": "2026-10-28T15:36:11Z",
                                               "pr_url": "https://github.com/a/b/pull/12", "head_commit": "82067a4"}]),
                brief=rng.choice(["", "Do it.", "First.\n\nSecond, with `code`."]),
                amendments=[Amendment(f"Line {n}.") for n in range(rng.randint(0, 2))],
                requirements=[_random_requirement(rng, next(rid)) for _ in range(rng.randint(0, 2))],
            ))
        model = canonical(model)
        text = render(model)
        back = parse_program_text(text)
        assert back.errors == [], (case, back.errors, text)
        assert back == model, (case, text)
        assert render(back) == text, case
        assert diff_program_text(text, text) == [], case


# ── the diff on a real record: frozen, refusals, lowers ──────────────

def _running(tmp_path, control: str = "normal") -> tuple[Rig, str]:
    """Six steps: 1 to 3 hand at once (Working), 4 to 6 wait (Planned)."""
    rig = Rig(tmp_path, engines=_engines, working_at_once=3)
    pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Stop the stalls.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", control=control, template="build-and-review",
                             reviewer_profile="codex-default")["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Indexes", "brief": "Add the indexes.", "owns": ["holdspeak/db/schema.py"]},
        {"title": "Retention", "brief": "Prune.", "owns": ["holdspeak/db/retention.py"]},
        {"title": "People routes", "brief": "Off the loop.", "owns": ["holdspeak/web/routes/people.py"]},
        {"title": "Projects routes", "brief": "Off the loop.", "after": [1]},
        {"title": "Calls routes", "brief": "Off the loop.", "after": [2]},
        {"title": "The fan-out", "brief": "One frame per change.", "after": [4, 5]},
    ])
    rig.service.start(OWNER, pid)
    assert [rig.step(pid, n)["state"] for n in range(1, 7)] == ["briefed"] * 3 + ["planned"] * 3
    return rig, pid


def _edit(text: str, *pairs: tuple[str, str]) -> str:
    for old, new in pairs:
        assert old in text, old
        text = text.replace(old, new, 1)
    return text


def test_each_frozen_field_is_a_refused_row_with_the_boards_words(tmp_path) -> None:
    rig, pid = _running(tmp_path)
    wire = rig.program(pid)
    text = rig.service.text_get(OWNER, pid)["text"]
    changed = _edit(text,
                    ("  > Add the indexes.", "  > Add the indexes, all four."),
                    ("step 1 Indexes                                    # Briefed · Claude Code · under a minute\n"
                     "  owns holdspeak/db/schema.py",
                     "step 1 Indexes\n  owns holdspeak/db/schema.py\n  agent Codex"),
                    ("step 2 Retention                                  # Briefed · Claude Code · under a minute\n"
                     "  owns holdspeak/db/retention.py",
                     "step 2 Retention\n  owns holdspeak/db/retention.py, holdspeak/db/more.py\n  review agent · check off"))
    rows = {row.id: row for row in diff_program_text(text, changed, record=wire)}
    assert rows["step-1.brief"].reason == f"Step 1 · brief: {FROZEN_READ}. Add a line with + instead."
    assert rows["step-1.agents"].reason == f"Step 1 · agent: {FROZEN_SET}. Hand off instead."
    assert rows["step-2.owns"].reason == f"Step 2 · owns: {FROZEN_READ}."
    check = rows["step-2.check"]
    assert check.reason == f"Step 2 · check: {FROZEN_BAR}." and check.lowers_bar
    assert {row.verdict for row in rows.values()} == {"refused"}
    assert {row.code for row in rows.values()} == {"step_frozen"}


def test_removals_unknown_ids_and_moves_of_started_steps_are_refused(tmp_path) -> None:
    rig, pid = _running(tmp_path)
    wire = rig.program(pid)
    text = rig.service.text_get(OWNER, pid)["text"]
    lines = text.split("\n")
    # Remove every-step R1, the whole of step 6 (Planned: allowed) and of step
    # 2 (started: it stays); name a step 9; put step 3 first.
    cut = "\n".join(line for line in lines if not line.startswith("  R1 "))
    cut = cut.split("\nstep 6 The fan-out")[0] + "\n\nstep 9 Ghost\n"
    two = cut[cut.index("\nstep 2 Retention"):cut.index("\nstep 3 ")]
    cut = cut.replace(two, "")
    three = cut[cut.index("step 3 People routes"):cut.index("\nstep 4 ")]
    cut = cut.replace(three + "\n", "").replace("step 1 Indexes", three + "\nstep 1 Indexes")
    rows = {row.id: row for row in diff_program_text(text, cut, record=wire)}
    assert rows["R1.remove"].code == "requirement_stays" and rows["R1.remove"].reason == "R1 stays. Waive it with a line."
    assert rows["step-6.remove"].verdict == "allowed" and rows["step-6.remove"].data["kind"] == "remove_step"
    assert (rows["step-2.remove"].code, rows["step-2.remove"].reason) == ("step_stays", "Step 2 started. It stays.")
    # Step 5 came after step 2: the text names a step it removes.
    assert rows["step-5.after-removed"].reason == "Step 5 · after: step 2 is removed in this text."
    assert rows["step-9.unknown"].reason.endswith("there is no step 9. Write 'step +' for a new step.")
    moved = [row for row in rows.values() if row.op == "move"]
    assert moved and all(row.verdict == "refused" for row in moved), moved


def test_the_rows_that_lower_the_bar(tmp_path) -> None:
    rig, pid = _running(tmp_path)
    wire = rig.program(pid)
    text = rig.service.text_get(OWNER, pid)["text"]
    changed = _edit(text,
                    ("  control normal", "  control yolo"),
                    ("  R2 review: Each new behaviour has a test.", "  R2 review optional: Each new behaviour has a test."),
                    ("  > Off the loop.\n\nstep 5", "  > Off the loop.\n  review none · merge none\n\nstep 5"),
                    ("  R1 review: The change does only what its brief says.",
                     "  R1 review: The change does only what its brief says.\n    waived: Not this week."))
    rows = {row.id: row for row in diff_program_text(text, changed, record=wire)}
    lowers = {key for key, row in rows.items() if row.lowers_bar}
    assert lowers == {"program.control", "R2.requirement", "step-4.review", "R1.waive"}, rows
    assert {rows[key].verdict for key in lowers} == {"lowers"}
    assert rows["step-4.merge"].verdict == "allowed" and not rows["step-4.merge"].lowers_bar  # level -> none
    # Raising the bar is not lowering it.
    back = diff_program_text(changed.replace("control yolo", "control secure"), changed, record=None)
    assert any(row.id == "program.control" and row.lowers_bar for row in back)
    assert not any(row.lowers_bar for row in diff_program_text(changed, text.replace("control normal", "control secure")))


# ── text_apply through the service ───────────────────────────────────

def test_a_dry_run_writes_nothing(tmp_path) -> None:
    rig, pid = _running(tmp_path)
    got = rig.service.text_get(OWNER, pid)
    before = (rig.program(pid)["revision"], len(rig.service.store.list_checkpoints(pid)), len(rig.frames))
    changed = _edit(got["text"], ("  merge owner", "  merge owner") if "merge owner" in got["text"] else
                    ("  > One frame per change.", "  > One frame per change.\n  merge owner"))
    answer = rig.service.text_apply(OWNER, pid, changed, dry_run=True)
    assert answer["applied"] is False and answer["text"] == got["text"]
    assert [(row["op"], row["where"], row["field"], row["verdict"]) for row in answer["changes"]] == [
        ("change", "step 6", "merge", "allowed")]
    assert answer["patch"].count("\n+  merge owner") == 1
    assert (rig.program(pid)["revision"], len(rig.service.store.list_checkpoints(pid)), len(rig.frames)) == before


def test_an_apply_lands_each_change_through_its_verb(tmp_path) -> None:
    """The running example on a record (§3.7, §3.8, §16): a started step's
    later agent, a '+' line, a new step placed before the fan-out, the
    fan-out waits for it and merges on his press, a requirement on the new
    step."""
    rig, pid = _running(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    changed = _edit(text,
                    ("  owns holdspeak/web/routes/people.py\n",
                     "  owns holdspeak/web/routes/people.py\n  agent Claude Code, then Codex\n"),
                    ("  > Off the loop.\n\nstep 4", "  > Off the loop.\n  + Also the avatar route.\n\nstep 4"),
                    ("\nstep 6 The fan-out", "\nstep + The loop watch\n  after 4\n  agent pi on "
                     f"{QWEN.profile_id} · effort low\n  brief\n  > Log handlers over 100 ms.\n"
                     "  R+ review: It logs nothing below 100 ms.\n\nstep 6 The fan-out"),
                    ("  after 4, 5\n", "  after 4, 5, 7\n  merge owner\n"))
    preview = rig.service.text_apply(OWNER, pid, changed, dry_run=True)
    assert [(row["op"], row["where"], row["field"], row["verdict"]) for row in preview["changes"]] == [
        ("change", "step 3", "agent", "allowed"), ("amend", "step 3", "amend", "allowed"),
        ("add", "step 7", "step", "allowed"), ("move", "step 7", "position", "allowed"),
        ("add", "step 7", "requirement", "allowed"),
        ("change", "step 6", "after", "allowed"), ("change", "step 6", "merge", "allowed"),
    ]
    checkpoints, frames = len(rig.service.store.list_checkpoints(pid)), len(rig.frames)
    answer = rig.service.text_apply(OWNER, pid, changed, dry_run=False)
    assert answer["applied"] is True
    wire = answer["program"]
    titles = [(step["ordinal"], step["title"], step["after"]) for step in wire["steps"]]
    assert titles == [(1, "Indexes", []), (2, "Retention", []), (3, "People routes", []), (4, "Projects routes", [1]),
                      (5, "Calls routes", [2]), (6, "The loop watch", [4]), (7, "The fan-out", [4, 5, 6])]
    three, six, seven = wire["steps"][2], wire["steps"][5], wire["steps"][6]
    assert [entry["profile"] for entry in three["runs_on"]] == ["claude-default", "codex-default"]
    assert [item["line"] for item in three["amendments"]] == ["Also the avatar route."]
    assert (six["profile"], six["engine"]["id"], six["effort"]) == ("pi-default", QWEN.profile_id, "low")
    assert [row["text"] for row in six["requirements"] if not row.get("parent_id")] == ["It logs nothing below 100 ms."]
    assert seven["gate"]["merge"] == "owner"
    # The new text reads back as what he wrote (the numbers follow the order).
    assert diff_program_text(answer["text"], rig.service.text_get(OWNER, pid)["text"]) == []
    lines = [row["line"] for row in rig.service.store.list_checkpoints(pid)][: len(rig.service.store.list_checkpoints(pid)) - checkpoints]
    assert lines[0].startswith("Changed by the text: 7 changes (lines ")
    assert "Added to the brief by the owner: Also the avatar route." in lines
    text_frames = [payload for frame, payload in rig.frames[frames:] if frame == "program_changed" and payload.get("text")]
    assert len(text_frames) == 1, rig.frames[frames:]


def test_a_refused_row_or_an_unpassed_lowering_writes_nothing(tmp_path) -> None:
    rig, pid = _running(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    revision = rig.program(pid)["revision"]
    refused = _edit(text, ("  > Add the indexes.", "  > Add the indexes, all four."),
                    ("  > One frame per change.", "  > One frame per change.\n  merge owner"))
    answer = rig.service.text_apply(OWNER, pid, refused, dry_run=False)
    assert answer["applied"] is False and answer["refused"] == 1
    assert rig.program(pid)["revision"] == revision
    # "Apply the rest": the allowed text puts the refused line back.
    assert "  > Add the indexes.\n" in answer["allowed_text"] and "merge owner" in answer["allowed_text"]
    lowering = _edit(text, ("  control normal", "  control yolo"))
    answer = rig.service.text_apply(OWNER, pid, lowering, dry_run=False)
    assert answer["applied"] is False and answer["lowers"] == ["program.control"]
    assert rig.program(pid)["control"] == "normal"
    answer = rig.service.text_apply(OWNER, pid, lowering, dry_run=False, allow_lower=["program.control"])
    assert answer["applied"] is True and rig.program(pid)["control"] == "yolo"


def test_a_field_changed_since_he_read_it_is_a_conflict(tmp_path) -> None:
    rig, pid = _running(tmp_path)
    base = rig.service.text_get(OWNER, pid)["text"]
    rig.service.change_step(OWNER, pid, rig.step(pid, 6)["id"], gate_merge="none")
    mine = _edit(base, ("  > One frame per change.", "  > One frame per change.\n  merge owner"))
    answer = rig.service.text_apply(OWNER, pid, mine, base=base, dry_run=True)
    row = next(row for row in answer["changes"] if row["id"] == "step-6.merge")
    assert (row["verdict"], row["code"]) == ("conflict", "text_conflict")
    assert row["reason"] == "Step 6's merge changed since you read it: now none."


def test_the_amendment_line_and_the_agents_own_changes(tmp_path) -> None:
    """A '+' under a Planned step is refused (change its brief); an agent's
    requirement edit is refused (his only)."""
    from holdspeak.principals import Principal, PrincipalKind

    rig, pid = _running(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    planned = _edit(text, ("  > One frame per change.", "  > One frame per change.\n  + And the counts."))
    row = next(row for row in rig.service.text_apply(OWNER, pid, planned)["changes"] if row["op"] == "amend")
    assert (row["code"], row["reason"]) == ("step_not_started", "Step 6 has not started: change its brief.")
    agent = Principal(PrincipalKind.AGENT, "agent:orchestrator")
    edit = _edit(text, ("R2 review: Each new behaviour has a test.", "R2 review: Each new behaviour has two tests."))
    row = next(row for row in rig.service.text_apply(agent, pid, edit)["changes"] if row["id"] == "R2.requirement")
    assert row["code"] == "owner_required"


def test_print_program_takes_the_wire_with_its_steps_and_requirements(tmp_path) -> None:
    rig, pid = _running(tmp_path)
    wire = rig.program(pid)
    assert print_program(wire, wire["steps"], wire["requirements"]) == print_program(wire)
    bare = print_program(wire, lamps=False)
    assert "#" not in bare.replace("# program text 1", "")
    assert parse_program_text(bare) == parse_program_text(print_program(wire))


@pytest.mark.parametrize("line, field, value", [
    ("  reviewer Codex at standard", "depth", "standard"),
    ("  planner qwen3.8-27b", "planner", "qwen3.8-27b"),
    ("  budget 32768", "budget", 32768),
    ("  night 23:30-7:00 · at most 8 steps", "night",
     {"line": "23:30–07:00 · at most 8 steps", "start": "23:30", "end": "07:00", "max_steps": 8}),
    ("  within web/src/desk/, docs/", "within", ["web/src/desk/", "docs/"]),
    ("  delivery dw holdspeak/phase-201/story-03", "delivery", "holdspeak/phase-201/story-03"),
    ("  when idle · rounds before start", "rounds_before_start", True),
])
def test_each_program_word_of_the_grammar_reads(line: str, field: str, value: Any) -> None:
    model = parse_program_text(f"program P\n{line}\n")
    assert model.errors == [] and getattr(model.head, field) == value
    assert parse_program_text(render(model)) == model


@pytest.mark.parametrize("line, words", [
    ("  reviewer Codex at deep", "Line 2: the review depth is glance, delta or standard."),
    ("  budget lots", "Line 2: the budget is a number of tokens ('budget 64k')."),
    ("  night 25:00–07:00", "Line 2: the night is '23:30–07:00 · at most 8 steps'."),
    ("  delivery jira X-1", "Line 2: delivery is 'delivery dw <project>/<phase>[/<story>]'."),
])
def test_a_bad_value_of_a_new_word_is_refused_by_name(line: str, words: str) -> None:
    errors = parse_program_text(f"program P\n{line}\n").errors
    assert [(error.code, error.words) for error in errors] == [("text_bad_value", words)]


# ── PG-LANG fields: each statement the text could not write applies ──

class _People:
    def display_names(self) -> dict[str, str]:
        return {"p-alice": "Alice"}


def _drafting(tmp_path, *, template: str = "build-and-review") -> tuple[Rig, str]:
    rig = Rig(tmp_path, engines=_engines, people=lambda: _People())
    (rig.repo / ".githooks").mkdir(exist_ok=True)
    (rig.repo / ".githooks" / "dw").write_text("#!/bin/sh\n", encoding="utf-8")
    pid = rig.service.create(OWNER, title="Fields", goal="All of them.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template=template, reviewer_profile="codex-default")["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Store", "brief": "Do the store.", "owns": ["holdspeak/db/programs.py"]},
        {"title": "Routes", "brief": "Do the routes.", "after": [1]},
        {"title": "Faces", "brief": "Do the faces.", "after": [2]},
    ])
    return rig, pid


def _apply(rig: Rig, pid: str, text: str, *, readback: bool = True, **kw: Any) -> dict[str, Any]:
    answer = rig.service.text_apply(OWNER, pid, text, dry_run=False, **kw)
    assert answer["applied"] is True, [row for row in answer["changes"] if row["verdict"] != "allowed"]
    again = rig.service.text_get(OWNER, pid)["text"]
    if readback and "R+ " not in text and "step + " not in text:  # a new one reads back with its number
        assert diff_program_text(text, again) == [], (text, again)  # it reads back as he wrote it
    return answer


def test_the_program_fields_apply_and_read_back(tmp_path) -> None:
    rig, pid = _drafting(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    changed = _edit(text, ("\n\nevery step", "\n  planner " + QWEN.profile_id + "\n  reviewer Codex at standard\n"
                           "  budget 64k\n  rounds before start\n  night 23:30–07:00 · at most 8 steps\n"
                           "  within holdspeak/, docs/\n  delivery dw app/phase-3/story-01\n  for Alice\n\nevery step"))
    preview = rig.service.text_apply(OWNER, pid, changed)
    assert [(row["field"], row["after"], row["verdict"]) for row in preview["changes"]] == [
        ("planner", QWEN.profile_id, "allowed"), ("review depth", "standard", "allowed"), ("budget", "64k", "allowed"),
        ("rounds before start", "yes", "allowed"), ("night", "23:30–07:00 · at most 8 steps", "allowed"),
        ("within", "holdspeak/, docs/", "allowed"), ("delivery dw", "app/phase-3/story-01", "allowed"),
        ("for", "Alice", "allowed"),
        ("review depth", "standard", "allowed"), ("review depth", "standard", "allowed"),
        ("review depth", "standard", "allowed"),
    ], preview["changes"]
    wire = _apply(rig, pid, changed)["program"]
    assert (wire["review_depth"], wire["planner"]["engine"], wire["budget_tokens"]) == ("standard", QWEN.profile_id, 65536)
    assert wire["night"] == {"line": "23:30–07:00 · at most 8 steps", "start": "23:30", "end": "07:00", "max_steps": 8}
    assert (wire["within"], wire["delivery"], wire["rounds_before_start"], wire["for_person_id"]) == (
        ["holdspeak/", "docs/"], {"kind": "dw", "ref": "app/phase-3/story-01", "linked": False}, True, "p-alice")
    assert {step["gate"]["review_depth"] for step in wire["steps"]} == {"standard"}
    # A new step takes the Program's depth.
    rig.service.plan(OWNER, pid, steps=[{"title": "Docs"}])
    assert rig.step(pid, 4)["gate"]["review_depth"] == "standard"
    # Taking the lines out clears them; ``check none`` and ``reviewer none`` lower the bar.
    text = rig.service.text_get(OWNER, pid)["text"]
    bare = "\n".join("  check none" if line.startswith("  check ") else line for line in text.split("\n")
                     if not line.startswith(("  planner", "  budget", "  rounds before", "  night", "  within",
                                             "  delivery")))
    bare = _edit(bare, ("  reviewer Codex at standard", "  reviewer none at standard"))
    preview = rig.service.text_apply(OWNER, pid, bare)
    lowers = set(preview["lowers"])
    assert {"program.reviewer", "program.check", "program.rounds-before-start"} <= lowers, preview["changes"]
    assert {f"step-{n}.review" for n in (1, 2, 3, 4)} <= lowers
    wire = _apply(rig, pid, bare, allow_lower=preview["lowers"])["program"]
    assert (wire["planner"], wire["budget_tokens"], wire["night"], wire["within"], wire["delivery"]) == (
        None, None, None, [], None)
    assert (wire["reviewer"]["profile"], wire["check_command"], wire["rounds_before_start"]) == (None, None, False)
    assert {step["gate"]["review"] for step in wire["steps"]} == {"none"}


def test_delivery_needs_the_rails_and_the_fixed_fields_say_why(tmp_path) -> None:
    rig, pid = _drafting(tmp_path)
    (rig.repo / ".githooks" / "dw").unlink()
    text = rig.service.text_get(OWNER, pid)["text"]
    changed = "\n".join("  in other · dev" if line.startswith("  in ") else line for line in text.split("\n"))
    changed = _edit(changed, ("\n\nevery step", "\n  delivery dw app/phase-3\n\nevery step"),
                    ("  template build and review", "  template race"))
    rows = {row["id"]: row for row in rig.service.text_apply(OWNER, pid, changed)["changes"]}
    assert (rows["program.delivery"]["code"], rows["program.delivery"]["reason"]) == (
        "delivery_no_rails", "This repository has no Delivery Workbench.")
    assert rows["program.repository"]["reason"] == ("Program · repository: it is set when the program is made; "
                                                    "a program works in one repository; make a new program for another.")
    assert rows["program.template"]["code"] == "field_fixed" and "change the fields it set" in rows["program.template"]["reason"]


def test_the_step_fields_apply_budget_when_idle_and_a_named_reviewer(tmp_path) -> None:
    rig, pid = _drafting(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    changed = _edit(text, ("  owns holdspeak/db/programs.py\n", "  owns holdspeak/db/programs.py\n  budget 32k\n"
                                                                 "  when idle\n  review Alice · merge owner\n"))
    wire = _apply(rig, pid, changed)["program"]
    one = wire["steps"][0]
    assert (one["budget_tokens"], one["prefer_idle"], one["gate"]["review"], one["for_person_id"]) == (
        32768, True, "person", "p-alice")


def test_a_planned_block_taken_out_removes_the_step(tmp_path) -> None:
    rig, pid = _drafting(tmp_path)
    rig.service.require(OWNER, pid, text="`echo ok` is green", step_id=rig.step(pid, 2)["id"])
    text = rig.service.text_get(OWNER, pid)["text"]
    cut = text[:text.index("\nstep 2 Routes")] + text[text.index("\nstep 3 Faces"):]
    rows = {row.id: row for row in diff_program_text(text, cut, record=rig.program(pid))}
    assert rows["step-3.after-removed"].code == "text_bad_value"  # step 3 still names step 2
    cut = cut.replace("  after 2\n", "  after 1\n")
    preview = rig.service.text_apply(OWNER, pid, cut)
    assert [(row["op"], row["where"], row["verdict"]) for row in preview["changes"]] == [
        ("remove", "step 2", "allowed"), ("change", "step 3", "allowed")], preview["changes"]
    wire = _apply(rig, pid, cut, readback=False)["program"]  # the numbers follow the order again
    assert [(step["ordinal"], step["title"], step["after"]) for step in wire["steps"]] == [
        (1, "Store", []), (2, "Faces", [1])]
    assert "Removed step 2, Routes" in [row["line"] for row in rig.service.store.list_checkpoints(pid)]
    # Its requirement is set aside, never counted, and its R number is not used again.
    assert all(row["text"] != "`echo ok` is green" for row in wire["requirements"])
    before = max(int(row["ordinal"]) for row in rig.service.requirements(pid))
    rig.service.require(OWNER, pid, text="A new one", kind="word")
    new = next(row for row in rig.service.requirements(pid) if row["text"] == "A new one")
    assert int(new["ordinal"]) == before + 1
    gone = next(row for row in rig.service.requirements(pid) if row["text"] == "`echo ok` is green")
    assert (gone["state"], gone["required"], gone["waived_reason"]) == ("waived", False, "Step 2 was removed")


def test_rounds_apply_his_answers_and_states_never_a_question(tmp_path) -> None:
    rig, pid = _drafting(tmp_path)
    rig.service.store.save_round({"program_id": pid, "name": "Architecture", "state": "asking", "ordinal": 1,
                                  "questions": [{"id": "q1", "text": "Does the cache live in the hub?", "answer": None},
                                                {"id": "q2", "text": "Can the event log lose rows?", "answer": None}],
                                  "updated_at": "2026-10-31T10:00:00Z"})
    text = rig.service.text_get(OWNER, pid)["text"]
    assert "round Architecture · asking\n  ? Does the cache live in the hub?\n  ? Can the event log lose rows?\n" in text
    changed = _edit(text, ("  ? Can the event log lose rows?\n", "  ? Can the event log lose rows?\n  = No.\n"),
                    ("\n\nstep 1 ", "\n\nround Security · open\n\nround Product · skipped\n\nstep 1 "))
    preview = rig.service.text_apply(OWNER, pid, changed)
    assert [(row["op"], row["where"], row["field"], row["verdict"]) for row in preview["changes"]] == [
        ("change", "round Architecture", "answer", "allowed"), ("add", "round Security", "round", "allowed"),
        ("add", "round Product", "round", "allowed")], preview["changes"]
    wire = _apply(rig, pid, changed)["program"]
    assert [(item["name"], item["state"], item["asked"], item["answered"]) for item in wire["rounds"]] == [
        ("Architecture", "asking", 2, 1), ("Security", "open", 0, 0), ("Product", "skipped", 0, 0)]
    answered = wire["rounds"][0]["questions"][1]
    assert (answered["id"], answered["answer"], answered["answered_by"]) == ("q2", "No.", "owner")
    # The engine's question, a round set to asking, a round with questions taken out: refused by name.
    text = rig.service.text_get(OWNER, pid)["text"]
    bad = _edit(text, ("  ? Does the cache live in the hub?", "  ? Does the cache live in the client?"),
                ("round Security · open", "round Security · asking"))
    rows = {row["id"]: row for row in rig.service.text_apply(OWNER, pid, bad)["changes"]}
    assert rows["round-architecture.questions"]["reason"] == ("Round Architecture: the engine asked it. "
                                                              "A '?' line stays as it is.")
    assert rows["round-security.state"]["code"] == "round_state"
    gone = text[:text.index("round Architecture")] + text[text.index("round Security"):]
    rows = {row["id"]: row for row in rig.service.text_apply(OWNER, pid, gone)["changes"]}
    assert rows["round-architecture.remove"]["code"] == "round_stays"
    # A done round's answers stay until he opens it again.
    done = _edit(text, ("round Architecture · asking", "round Architecture · done"))
    _apply(rig, pid, done)
    text = rig.service.text_get(OWNER, pid)["text"]
    rows = {row["id"]: row for row in rig.service.text_apply(OWNER, pid, _edit(text, ("  = No.", "  = Yes.")))["changes"]}
    assert rows["round-architecture.answer-2"]["code"] == "round_done"


def test_measure_and_walk_lines_apply_as_requirements(tmp_path) -> None:
    rig, pid = _drafting(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    changed = _edit(text, ("\nstep 1 Store", "\nat the end\n  R+ word: I used the board for a morning.\n"
                                             "    walk Open Programs at 393\n    walk Press Plan it\n\nstep 1 Store"),
                    ("  > Do the store.\n", "  > Do the store.\n  R+ measure: The store answers fast.\n"
                                            "    run sh bench.sh\n    bound p95 < 100 ms\n"))
    wire = _apply(rig, pid, changed)["program"]
    word = next(row for row in wire["requirements"] if row["kind"] == "word")
    assert word["spec"] == {"walk": ["Open Programs at 393", "Press Plan it"]}
    measure = next(row for row in wire["steps"][0]["requirements"] if row["kind"] == "measure")
    assert measure["spec"] == {"command": "sh bench.sh", "metric": "p95", "op": "<", "bound": 100, "unit": "ms"}
    assert (measure["state"], measure["state_word"], measure["kind_word"]) == ("not_yet", "Not measured yet", "Measure")
    # A measure with no bound cannot be proven here.
    text = rig.service.text_get(OWNER, pid)["text"]
    rows = rig.service.text_apply(OWNER, pid, _edit(text, ("  > Do the routes.\n", "  > Do the routes.\n"
                                                           "  R+ measure: It is fast.\n")))["changes"]
    assert [(row["code"], row["reason"]) for row in rows] == [
        ("requirement_unprovable", "A measure needs a command and a bound.")]
    # LANG11: a measure gates like a check, so making a check a measure does
    # not lower the bar; making it a review still does.
    rows = diff_program_text(
        "program P\n\nat the end\n  R1 check: `echo ok` is green.\n",
        "program P\n\nat the end\n  R1 measure: `echo ok` is green.\n    bound n < 3\n")
    assert [(row.id, row.verdict) for row in rows] == [("R1.requirement", "allowed")]
    rows = diff_program_text(
        "program P\n\nat the end\n  R1 measure: `echo ok` is green.\n    bound n < 3\n",
        "program P\n\nat the end\n  R1 review: `echo ok` is green.\n")
    assert [(row.id, row.verdict) for row in rows] == [("R1.requirement", "lowers")]


def test_only_the_owner_writes_a_round(tmp_path) -> None:
    from holdspeak.principals import Principal, PrincipalKind

    rig, pid = _drafting(tmp_path)
    text = rig.service.text_get(OWNER, pid)["text"]
    agent = Principal(PrincipalKind.AGENT, "agent:orchestrator")
    rows = rig.service.text_apply(agent, pid, _edit(text, ("\n\nstep 1 ", "\n\nround Security · open\n\nstep 1 ")))
    assert [(row["id"], row["code"]) for row in rows["changes"]] == [("round-security.add", "owner_required")]
