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
    Amendment, Head, ProgramText, Requirement, Step, canonical, diff_program_text, from_wire, guessed_spec,
    parse_program_text, print_program, render, wire_lamps,
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


def test_the_overnight_example_names_the_word_this_hub_does_not_read_yet() -> None:
    model = parse_program_text(OVERNIGHT)
    assert [(error.line, error.code) for error in model.errors] == [(5, "text_unknown_word")]
    assert "'budget'" in model.errors[0].words and "does not read yet" in model.errors[0].words
    assert model.head.agents == [("pi-default", "qwen3.8-27b"), ("claude-default", None)]
    assert (model.head.when_idle, model.head.may_call) == (True, True)  # one line, joined with ·


def test_the_race_example_names_measure_as_not_read_yet() -> None:
    model = parse_program_text(RACE)
    assert [error.code for error in model.errors] == ["text_unknown_word"]
    assert "'measure'" in model.errors[0].words
    step = model.step(1)
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
        for error in model.errors:
            assert ("does not read yet" in error.words or "review depth is set on each step" in error.words), error


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
        rig.service.require(OWNER, pid, text="I tried it", kind="word", required=False)
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
    kind = rng.choice(["check", "review", "shot", "word"])
    text = rng.choice(["`uv run pytest -q x.py` is green", "No route takes a lock", "The People window at 393 fits",
                       "I used it for a morning", "echo done prints done"])
    spec = guessed_spec(kind, text)
    if kind == "check" and rng.random() < 0.5:
        spec = {**spec, "command": "sh scripts/check.sh"}
    if kind == "check" and rng.random() < 0.3:
        spec = {**spec, "expect": r"\d+ passed"}
    if kind == "shot" and rng.random() < 0.5:
        spec = {"case": "programs", "width": rng.choice([393, 1440])}
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
        )
        model = ProgramText(head=head)
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
                origin=rng.choice([None, "action:a-1"]),
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
    # Remove every-step R1 and the whole of step 6; name a step 9; put step 3 first.
    cut = "\n".join(line for line in lines if not line.startswith("  R1 "))
    cut = cut.split("\nstep 6 The fan-out")[0] + "\n\nstep 9 Ghost\n"
    three = cut[cut.index("step 3 People routes"):cut.index("\nstep 4 ")]
    cut = cut.replace(three + "\n", "").replace("step 1 Indexes", three + "\nstep 1 Indexes")
    rows = {row.id: row for row in diff_program_text(text, cut, record=wire)}
    assert rows["R1.remove"].code == "requirement_stays" and rows["R1.remove"].reason == "R1 stays. Waive it with a line."
    assert rows["step-6.remove"].code == "step_stays"
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


@pytest.mark.parametrize("line, code", [
    ("  reviewer Codex at delta", "text_bad_value"),
    ("  planner qwen3.8-27b", "text_unknown_word"),
    ("  night 23:30–07:00 · at most 8 steps", "text_unknown_word"),
])
def test_program_words_this_hub_does_not_store_are_refused_by_name(line: str, code: str) -> None:
    model = parse_program_text(f"program P\n{line}\n")
    assert [error.code for error in model.errors][:1] == [code]
