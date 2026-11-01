"""Planning inference: a goal becomes a drafted Program (PG-LANG LANG6, 2026-10-31).

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §5 (§5.2
grounding, §5.4 sizing), §6.5 station 2, §9.3. A Program in Drafting, its
goal (his paragraphs, or the Note it came from) and its template go to ONE
inference call on the same machinery as shaping (``program_shaper``: the
``agent.plan`` assignment, else the Ask engine; the runner's one path; one
retry with the parser's words; an honest refusal). The engine answers the
WHOLE text with the steps added; the hub diffs it against the current text
with the LANG1 machinery and the service's checks, so a draft is the same
change rows a typed edit gets (source ``plan``). Nothing is written: Apply
is ``text_apply`` (in Drafting it plans, requires and updates).

Sizing (§5.4): each step is sized by rule (``program_sizing``); with a
budget, a step over the working share is ``step_too_big``, and the planner
is asked ONCE to split it. A step still too big after that keeps its row,
with the words "Too big for qwen · 41k of 32k" and the face's Split.

The hub keeps what is his and what the template set: the title, the goal,
``in``, ``template``, ``from`` and ``budget`` stay as they are, whatever the
engine wrote (§5.2: "the planner may not change what the template set, only
add"). A budget he gave the planner is written into the draft
(``budget 64k``), so Apply keeps the sizing it was planned for. A new
requirement the engine gave a number (``R3``) is read as ``R+``.
"""
from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from ..logging_config import get_logger
from . import program_shaper as shaper
from . import program_sizing as sizing

log = get_logger("program_planner")

CONTRACT = "program.plan"
CONTRACT_REVISION = "1"
TEMPERATURE = 0.2
#: §4.7 targets planning at 15 s p50, 40 s p95; the home engine thinks
#: before it answers (shaping took 25 s), and a draft is a whole text.
DEADLINE_SECONDS = 240
MIN_TOKENS, MAX_TOKENS, THINKING_TOKENS = 6000, 14000, 6000
GOAL_MAX = 8000
#: §5.4: at planning, with a budget: at most three owned files and a brief
#: under 400 words per step.
OWNS_MAX, BRIEF_WORDS_MAX = 3, 400
OVERVIEW_MAX, LIKELY_MAX, HEADINGS_MAX, RECENT_MAX = 40, 120, 30, 10
#: Not where a step's work lives: history, parked code, design assets, generated docs.
_NOT_WORK = ("pm/", "docs/", "parked/", "dogfood/", "aipi-lite/", "tests/_parked/", "tests/e2e/_parked/",
             "web/design/", "web/public/", ".githooks/", "uat/scenarios/")
_WORK_SUFFIXES = (".py", ".ts", ".tsx", ".css", ".swift", ".sh", ".toml", ".yaml", ".yml")
_STOP = frozenset("""about after again also always another because been before being both cannot could does doing
each even every from have here into just make made many more most much must need only other over same should
some such than that their them then there these they this those through under very want were what when where
which while will with within without would your yours itself it's isn't""".split())

PLAN_RULES = """RULES FOR A DRAFT
- Answer the WHOLE program text in "text": every line of the text now stays exactly as it is
  (the program block, every step, at the end); add the steps and the requirements the goal needs.
- Write each new step as 'step + <title>'. Its place in the text is its place in the plan;
  'after <n>' names an earlier step by its place (1 is the first step).
- One concern per step. Each step has an 'owns' line (the files or folders it changes: a path from
  the repository map when it exists, a new path when the file is new), a 'brief' of one to four '>'
  lines that says what the change does, and 'after' when it needs an earlier step.
- Add requirements with 'R+' where they are proven: on the step, or under 'at the end':
  check (a command in backticks the repository can run, "is green"), shot ("The <Window> window at
  393 has no clipped text."), word (what only the owner can judge), review (a rule a reader checks),
  measure (a number with a bound; two lines under it, four spaces in: 'run <command>' and
  'bound <metric> < <number> <unit>', for example 'bound total < 20 s').
  Only what the goal asks; never repeat a requirement the text has.
- Never change the title, the goal, 'in', 'template' or 'from'. Never remove or change an R line.
- Never write 'check off', 'review none', 'merge none', 'optional' or 'waived'.
- Leave out the agent line unless the goal names an agent: the program's agent builds each step.
- "say": one short line: the number of steps and what they do.
- "programs": [] when the goal is one goal. When it is two to four separate goals (each a change
  that could merge and ship on its own), list them in "programs" in the order they should run:
  each {"title": "<a short title>", "goal": "<one or two sentences, the owner's words where you can>",
  "hands": "<one line: what it gives the next program; \"\" for the last>",
  "text": "<that program's WHOLE text, made by these rules, with its own title and goal>"};
  "text" is then the first program's text. Never split one goal into programs."""

SPLIT_RULES = """SPLIT A STEP
- Replace only the steps named below, each by 2 to 4 'step +' steps in its place, that together own
  what it owned, each with its own brief of one to four '>' lines.
- The step that waited for it waits for the last part. Keep its own R lines on the last part.
- Every other line stays exactly as it is. Answer the WHOLE text in "text"."""


@dataclass
class PlanResult:
    """One planning answer (the brief's ``PlanResult``)."""

    proposed_text: str
    rows: list[Any]
    grounded_on: dict[str, Any]
    sizes: list[dict[str, Any]]
    engine: str
    latency_ms: int
    say: str = ""
    attempts: int = 1
    capability: str = shaper.CAPABILITY
    #: The printed text the rows are against (his base for Apply).
    base_text: str = ""
    budget: Optional[int] = None
    #: The steps the planner was asked to split (their place and size).
    split: list[dict[str, Any]] = field(default_factory=list)
    #: JRN1: the Programs the draft proposes (2 to 4), in their order; [] for one.
    programs: list[dict[str, Any]] = field(default_factory=list)
    prompts: list[dict[str, Any]] = field(default_factory=list, repr=False)


def _refused(code: str, detail: str, status: int = 409, **more: Any) -> Exception:
    from .program_service import ProgramRefused

    return ProgramRefused(code, detail, status=status, **more)


def token_cap(text: str) -> int:
    return max(MIN_TOKENS, min(MAX_TOKENS, len(text) // 3 + THINKING_TOKENS))


def response_format() -> dict[str, Any]:
    return {"type": "json_schema", "json_schema": {"name": "program_plan", "strict": True, "schema": {
        "type": "object", "additionalProperties": False, "required": ["say", "text", "programs"],
        "properties": {"say": {"type": "string", "maxLength": 300}, "text": {"type": "string"},
                       # JRN1: the draft proposes several Programs when the goal is several goals.
                       "programs": {"type": "array", "maxItems": 4, "items": {
                           "type": "object", "additionalProperties": False,
                           "required": ["title", "goal", "hands", "text"],
                           "properties": {"title": {"type": "string", "maxLength": 120},
                                          "goal": {"type": "string", "maxLength": 1200},
                                          "hands": {"type": "string", "maxLength": 300},
                                          "text": {"type": "string"}}}}}}}}


# ── grounding (§5.2) ─────────────────────────────────────────────────

def _git(root: str, *args: str) -> list[str]:
    try:
        proc = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=5)
    except Exception:
        return []
    return [line for line in proc.stdout.splitlines() if line] if proc.returncode == 0 else []


def _words(goal: str) -> set[str]:
    out = set()
    for word in re.findall(r"[A-Za-z][A-Za-z]{3,}", goal or ""):
        low = word.lower()
        if low in _STOP:
            continue
        out.add(low[:-1] if low.endswith("s") and len(low) > 4 else low)
    return out


def _tokens_word(root: str, path: str) -> str:
    return sizing.k_words(sizing.chars_tokens(sizing.path_bytes(root, path)))


def repo_ground(root: Optional[str], goal: str) -> dict[str, Any]:
    """The repository map of §5.2: the top folders with their file counts,
    the files the goal names or is likely about (with their size), the
    headings of CLAUDE.md or AGENTS.md, the last merged changes."""
    if not root or not Path(root).is_dir():
        return {"folders": [], "likely": [], "headings": [], "recent": []}
    files = [path for path in _git(root, "ls-files") if not path.startswith(_NOT_WORK)]
    counts: dict[str, int] = {}
    for path in files:
        parts = path.split("/")
        key = "/".join(parts[:2]) + "/" if len(parts) > 2 else (parts[0] + "/" if len(parts) > 1 else "")
        if key:
            counts[key] = counts.get(key, 0) + 1
    folders = [f"{name} {count} files" for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:OVERVIEW_MAX]]
    words = _words(goal)
    named = {path for path in files if path in (goal or "")}
    scored: list[tuple[int, str]] = []
    for path in files:
        if path not in named and not path.endswith(_WORK_SUFFIXES):
            continue
        low, name = path.lower(), path.rsplit("/", 1)[-1].lower()
        hits = sum(2 if word in name else 1 for word in words if word in low)
        if path in named:
            hits += 10
        if hits:
            scored.append((hits, path))
    scored.sort(key=lambda item: (-item[0], item[1]))
    likely = [f"{path}  ({_tokens_word(root, path)})" for _hits, path in scored[:LIKELY_MAX]]
    headings: list[str] = []
    for name in ("CLAUDE.md", "AGENTS.md"):
        target = Path(root) / name
        if target.is_file():
            try:
                lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                lines = []
            headings += [line.strip() for line in lines if line.startswith("## ")]
    recent = _git(root, "log", "--first-parent", f"-{RECENT_MAX}", "--format=%s")
    return {"folders": folders, "likely": likely, "headings": headings[:HEADINGS_MAX], "recent": recent[:RECENT_MAX]}


def template_card(template_id: Optional[str]) -> str:
    """The template's shape (§5.2): its gates, its reviewer and its default
    requirements (``requirements_for``), in words."""
    from ..program_templates import get_template, requirements_for

    shape = get_template(template_id) if template_id else None
    if shape is None:
        return "THE TEMPLATE\n- none: the repository's check gates each step."
    step = shape.get("step") or {}
    lines = [f"THE TEMPLATE: {shape['name']}", f"- {shape['description']}",
             f"- Each step: check {'on' if step.get('gate_check') else 'off'}; "
             f"review {'by the reviewer at ' + str(step.get('review_depth') or 'delta') if step.get('gate_review') else 'none'}; "
             f"merge by the {step.get('gate_merge') or 'level'}."]
    planted = requirements_for(shape)
    if planted:
        lines.append("- Its requirements (they are in the text already): "
                     + "; ".join(f"{row['kind']}: {row['text']}" for row in planted))
    return "\n".join(lines)


def messages(text: str, goal: str, ground: Mapping[str, Any], repo: Mapping[str, Any], template_id: Optional[str], *,
             budget: Optional[int], engine_word: str, error: Optional[str] = None,
             split: Optional[list[dict[str, Any]]] = None) -> tuple[str, str]:
    """The system and user prompt of ``program.plan@1``."""
    vocabulary = ground.get("vocabulary") or {}
    system_parts = [
        "You plan a HoldSpeak Program: from its owner's goal you write its steps and requirements in the "
        'Program text. You answer JSON only: {"say": "...", "text": "..."}.',
        shaper.GRAMMAR_CARD, SPLIT_RULES if split else PLAN_RULES, template_card(template_id),
        "VOCABULARY\n" + "\n".join(f"- {key.replace('_', ' ')}: {', '.join(map(str, values)) or 'none'}"
                                   for key, values in vocabulary.items()),
    ]
    if budget:
        share = sizing.share_of(budget)
        system_parts.append(
            f"SIZE\nThe agent that builds each step ({engine_word}) has a context of {sizing.k_words(budget)} tokens; "
            f"a step must fit in {sizing.k_words(share)} tokens with its brief and the files it owns. "
            f"So: one concern per step, at most {OWNS_MAX} owned files, a brief under {BRIEF_WORDS_MAX} words, "
            "effort low or medium only. The repository map gives each file's size in tokens.")
    system = "\n\n".join(system_parts)
    parts = ["THE PROGRAM TEXT NOW\n" + text.rstrip("\n"), "THE GOAL (the owner's words)\n" + goal.strip()]
    if repo.get("folders"):
        parts.append("THE REPOSITORY: TOP FOLDERS\n" + "\n".join(repo["folders"]))
    if repo.get("likely"):
        parts.append("FILES THE GOAL IS LIKELY ABOUT (size in tokens)\n" + "\n".join(repo["likely"]))
    if repo.get("headings"):
        parts.append("THE REPOSITORY'S WORKING AGREEMENTS (headings)\n" + "\n".join(repo["headings"]))
    if repo.get("recent"):
        parts.append("THE LAST CHANGES MERGED (how this repository cuts its work)\n"
                     + "\n".join(f"- {item}" for item in repo["recent"]))
    if ground.get("note"):
        parts.append("THE NOTE THE PROGRAM CAME FROM\n" + str(ground["note"]))
    if ground.get("open_actions"):
        parts.append("THE PROJECT'S OPEN ACTIONS\n" + "\n".join(f"- {item}" for item in ground["open_actions"]))
    if split:
        parts.append("THESE STEPS ARE TOO BIG\n" + "\n".join(
            f"- step {row['place']} {row['title']}: {row['words']} (owns {', '.join(row['owns']) or 'nothing'})"
            for row in split))
    if error:
        parts.append("YOUR LAST ANSWER COULD NOT BE READ. The parser said:\n" + error
                     + "\nAnswer again with the whole text, correct.")
    return system, "\n\n".join(parts)


# ── the hub's part: keep his words and the template's, size each step ─

def _keep_fixed(proposed: Any, seed: Any, budget: Optional[int], explicit: bool) -> Any:
    """The title, the goal, ``in``, ``template``, ``from`` and ``budget``
    stay as the seed has them; a budget he gave the planner is written in;
    a requirement the engine numbered that the text does not have is new."""
    head, base = proposed.head, seed.head
    for name in ("title", "goal", "repository", "branch", "project", "template", "origin", "budget"):
        setattr(head, name, getattr(base, name))
    if explicit and budget:
        head.budget = budget
    # A new requirement the engine numbered (``R3`` where the text has R1
    # and R2) is a new one: the apply gives it its number (§3.4).
    known = {row.rid for _where, row in seed.requirements() if row.rid is not None}
    for _where, row in proposed.requirements():
        if row.rid is not None and row.rid not in known:
            row.rid = None
    return proposed


def size_steps(service: Any, wire: Mapping[str, Any], model: Any, *, explicit_budget: Optional[int]) -> list[dict[str, Any]]:
    """The size of every step of a text (§5.4), in its place."""
    from .program_text import step_agents

    root = str((wire.get("repository") or {}).get("root") or "") or None
    out = []
    for place, step in enumerate(model.steps, start=1):
        agents = step_agents(model.head, step)
        agent = agents[0] if agents else ("claude-default", None)
        tokens = sizing.estimate(root, brief=step.brief, owns=step.owns,
                                 requirements=[row.text for row in step.requirements], profile=agent[0])
        budget, word = sizing.budget_of(service, explicit=explicit_budget, program_budget=model.head.budget,
                                        step_budget=step.budget, agent=agent,
                                        default_engine=_default_engine(wire))
        row = sizing.size(tokens, budget, word)
        row.update(place=place, number=step.number, title=step.title, owns=list(step.owns))
        out.append(row)
    return out


def _call(call: Callable[[dict[str, Any]], tuple[Optional[str], str]], system_user: Callable[[Optional[str]], tuple[str, str]],
          tokens: int, prompts: list[dict[str, Any]], label: str, started: float) -> tuple[Optional[dict[str, Any]], Optional[str], str]:
    """One planning call with the shaper's one retry: ``(answer, error, model)``."""
    answer, error, model = None, None, ""
    for attempt in (1, 2):
        system, user = system_user(error if attempt == 2 else None)
        payload = {"system_prompt": system, "user_prompt": user, "temperature": TEMPERATURE, "max_tokens": tokens,
                   "response_format": response_format()}
        prompts.append(payload)
        try:
            output, model = call(payload)
        except Exception as exc:
            log.warning(f"program planning call failed: {exc}")
            output = None
        engine = model or label
        if output is None:
            if time.monotonic() - started >= DEADLINE_SECONDS:
                raise _refused("engine_timeout", f"{engine} did not answer in {DEADLINE_SECONDS} s. The program is "
                                                 "unchanged. Try again.", status=504, engine=engine)
            raise _refused("engine_failed", f"{engine} did not answer. The program is unchanged. Try again.", status=502,
                           engine=engine)
        answer, error = shaper.read_answer(output)
        if answer is not None and answer.get("text"):
            return answer, None, model
        if answer is not None:
            answer, error = None, "The answer has no 'text'."
    return None, error, model


# ── the planner ──────────────────────────────────────────────────────

def plan(service: Any, principal: Any, program_id: str, *, goal_text: Any = None, template: Any = None,
         budget: Any = None, text: Any = None, split: Any = None,
         invoke_fn: Optional[Callable[..., tuple[Optional[str], str]]] = None) -> PlanResult:
    """A goal → one call → the draft's change rows (nothing is written).

    ``text`` and ``split`` (a step's place in that text): Split on a draft
    row; only the split call is made, on the draft he sees."""
    from .program_service import _budget
    from .program_text import parse_program_text, print_program, render

    program = service._program(program_id)
    service._require_writer(principal, program, "plan")
    if program.get("state") != "drafting":
        raise _refused("plan_drafting_only", "Plan it works while the program is in Drafting. Shape it instead.")
    wire = service.get(principal, program["id"])
    printed = print_program(wire)
    seed = parse_program_text(shaper.stripped_text(printed))
    goal = str(goal_text).strip() if isinstance(goal_text, str) and goal_text.strip() else seed.head.goal
    if len(goal) > GOAL_MAX:
        raise _refused("goal_too_long", f"Give the goal in {GOAL_MAX} characters or fewer.", status=400)
    seed.head.goal = goal
    ground = shaper.grounding(service, wire)
    if not goal.strip() and not ground.get("note"):
        raise _refused("goal_required", "Write the goal first: two paragraphs are enough.", status=400)
    template_id = str(template or "").strip().replace(" ", "-").lower() or None
    if template_id and wire.get("template") and template_id != wire["template"]:
        raise _refused("field_fixed", "Program · template: it is set when the program is made; make a new program "
                                      "for another.")
    template_id = template_id or wire.get("template")
    explicit = _budget(budget, "The budget") if budget not in (None, "") else None
    seed_text = render(seed)
    repo = repo_ground(str((wire.get("repository") or {}).get("root") or "") or None, goal + "\n" + str(ground.get("note") or ""))
    capability, revision, profile, label = shaper.resolve_engine(service.db)
    call = invoke_fn or (lambda payload: shaper.invoke(service.db, principal, capability, revision, payload,
                                                       contract=CONTRACT, contract_revision=CONTRACT_REVISION,
                                                       deadline=DEADLINE_SECONDS))
    budget_now, engine_word = _program_budget(service, wire, seed, explicit)
    prompts: list[dict[str, Any]] = []
    started = time.monotonic()
    model = ""
    split_rows: list[dict[str, Any]] = []
    if text is not None and split is not None:
        draft = parse_program_text(str(text))
        if draft.errors or not draft.head.title:
            raise _refused("text_unreadable", "The draft could not be read. Plan it again.", status=400)
        if not explicit and draft.head.budget and not seed.head.budget:
            # The draft names the budget it was planned for (``budget 64k``): it stays.
            explicit = draft.head.budget
            budget_now, engine_word = _program_budget(service, wire, seed, explicit)
        draft = _keep_fixed(draft, seed, explicit, bool(explicit))
        proposed_text, say = render(draft), ""
    else:
        answer, error, model = _call(
            call, lambda error: messages(seed_text, goal, ground, repo, template_id, budget=budget_now,
                                         engine_word=engine_word, error=error),
            token_cap(seed_text + goal), prompts, label, started)
        if answer is None:
            raise _refused("engine_unusable", "The engine's answer could not be read. The program is unchanged. "
                                              "Try again.", status=502, engine=model or label, parse_error=error)
        draft = _keep_fixed(parse_program_text(answer["text"]), seed, explicit, bool(explicit))
        proposed_text, say = render(draft), answer["say"]
        proposed_programs = _programs(service, wire, seed, answer.get("programs") or [], explicit)
    sizes = size_steps(service, wire, draft, explicit_budget=explicit)
    wanted = [row for row in sizes if row["fits"] is False and (split is None or int(row["place"]) == int(split))]
    if text is not None and split is not None and not wanted:
        wanted = [row for row in sizes if int(row["place"]) == int(split)]
    if wanted:
        # §5.4: the planner is asked ONCE to split what does not fit.
        split_rows = [{key: row[key] for key in ("place", "title", "words", "owns", "tokens", "share")} for row in wanted]
        answer, error, split_model = _call(
            call, lambda error: messages(proposed_text, goal, ground, repo, template_id, budget=budget_now,
                                         engine_word=engine_word, error=error, split=split_rows),
            token_cap(proposed_text), prompts, label, started)
        model = split_model or model
        if answer is not None:
            draft = _keep_fixed(parse_program_text(answer["text"]), seed, explicit, bool(explicit))
            proposed_text = render(draft)
            say = say or answer["say"]
            sizes = size_steps(service, wire, draft, explicit_budget=explicit)
        else:
            log.warning(f"program planning split could not be read: {error}")
    latency = int((time.monotonic() - started) * 1000)
    engine = model or label
    if text is not None and split is not None:
        proposed_programs = []
    _base, _new, rows = shaper._rows_for(service, principal, program, wire, printed, proposed_text)
    for row in rows:
        row.data["source"] = "plan"
        step = row.data.get("step") if row.data.get("kind") == "add_step" else None
        if step is not None:
            place = next((i for i, item in enumerate(_new.steps, start=1) if item is step), None)
            if place is not None and place <= len(sizes):
                row.data["size"] = sizes[place - 1]
    grounded = {"capability": capability, "profile": profile, "goal_chars": len(goal), "note": bool(ground["note"]),
                "open_actions": len(ground["open_actions"]), "folders": len(repo["folders"]),
                "likely_files": len(repo["likely"]), "headings": len(repo["headings"]), "recent": len(repo["recent"]),
                "template": template_id, "budget": budget_now}
    return PlanResult(proposed_text=proposed_text, rows=rows, grounded_on=grounded, sizes=sizes, engine=engine,
                      latency_ms=latency, say=say, attempts=len(prompts), capability=capability, base_text=printed,
                      budget=budget_now, split=split_rows, programs=proposed_programs, prompts=prompts)


MAX_PROGRAMS = 4


def _programs(service: Any, wire: Mapping[str, Any], seed: Any, rows: list[Any],
              explicit: Optional[int]) -> list[dict[str, Any]]:
    """JRN1: the Programs a draft proposes (2 to 4, in their order), each with
    its own title, goal, what it hands the next, its whole text (the seed's
    ``in``, template, origin and budget kept), its steps and their sizes.
    Fewer than two readable ones is one Program: []."""
    from .program_text import parse_program_text, render

    out: list[dict[str, Any]] = []
    for row in rows[:MAX_PROGRAMS]:
        title = " ".join(str(row.get("title") or "").split())[:120]
        goal = str(row.get("goal") or "").strip()
        model = parse_program_text(str(row.get("text") or ""))
        if not title or model.errors or not model.head.title:
            continue
        model = _keep_fixed(model, seed, explicit, bool(explicit))
        model.head.title, model.head.goal = title, goal
        sizes = size_steps(service, wire, model, explicit_budget=explicit)
        out.append({"title": title, "goal": goal, "hands": " ".join(str(row.get("hands") or "").split())[:300],
                    "text": render(model), "steps": [step.title for step in model.steps], "sizes": sizes})
    return out if len(out) >= 2 else []


def apply_programs(service: Any, principal: Any, program_id: str, programs: Any, which: Any = "all") -> dict[str, Any]:
    """JRN1, Apply all / Apply this one: the first proposed Program is this
    one (its title, goal and steps); each other is a new Program in Drafting
    on the same repository and template, linked to the one before it
    (``origin_ref = program:<id>``), which it waits on: it starts after that
    one is Done. Apply this one (not the first) makes that one, linked to
    this Program."""
    from .program_text import print_program

    program = service._program(program_id)
    service._require_writer(principal, program, "plan")
    if program.get("state") != "drafting":
        raise _refused("plan_drafting_only", "The programs apply while this program is in Drafting.")
    rows = [row for row in (programs or []) if isinstance(row, Mapping)]
    if not rows or len(rows) > MAX_PROGRAMS:
        raise _refused("programs_invalid", f"Give one to {MAX_PROGRAMS} programs.", status=400)
    picked = list(range(len(rows))) if str(which) == "all" else [int(which)] if str(which).isdigit() else []
    if not picked or any(index >= len(rows) for index in picked):
        raise _refused("programs_invalid", "Name the program: all, or its place.", status=400)

    def _write(target_id: str, row: Mapping[str, Any]) -> None:
        from .program_text import parse_program_text, render

        wire = service.get(principal, target_id)
        printed = print_program(wire)
        # The steps and requirements are the proposal's; the head (title,
        # goal, in, template, from, budget) is the Program's own as made.
        own = parse_program_text(shaper.stripped_text(printed))
        text = render(_keep_fixed(parse_program_text(str(row.get("text") or "")), own, None, False))
        answer = service.text_apply(principal, target_id, text, dry_run=False, base=printed)
        if answer.get("refused"):
            raise _refused("programs_refused", f"The steps of {row.get('title')} were not written.",
                           changes=answer.get("changes"))

    made: list[dict[str, Any]] = []
    before = program["id"]
    for index in picked:
        row = rows[index]
        title = " ".join(str(row.get("title") or "").split()) or program["title"]
        goal = str(row.get("goal") or "").strip()
        if index == 0:
            service.update(principal, program["id"], title=title, goal=goal)
            _write(program["id"], {**row, "title": title})
            continue
        new = service.create(principal, title=title, goal=goal, repository=program.get("repo_root") or None,
                             project_id=program.get("project_id"), template=program.get("template") or None,
                             control=program.get("control"), check_command=program.get("check_command"),
                             origin_ref=f"program:{before if str(which) == 'all' else program['id']}")
        if program.get("budget_tokens"):
            # The budget it was planned for stays with each part.
            service.update(principal, new["id"], budget_tokens=program["budget_tokens"])
        _write(new["id"], row)
        made.append({"id": new["id"], "title": title})
        if str(which) == "all":
            before = new["id"]
    return {"program": service.get(principal, program["id"]), "made": made}


def _program_budget(service: Any, wire: Mapping[str, Any], seed: Any, explicit: Optional[int]) -> tuple[Optional[int], str]:
    """The budget of the Program's first agent (a draft with no steps yet)."""
    from .program_text import program_agents

    agents = program_agents(seed.head)
    agent = agents[0] if agents else ("claude-default", None)
    return sizing.budget_of(service, explicit=explicit, program_budget=seed.head.budget, step_budget=None, agent=agent,
                            default_engine=_default_engine(wire))


def _default_engine(wire: Mapping[str, Any]) -> Optional[str]:
    engine = (wire.get("default") or {}).get("engine")
    return str(engine.get("id")) if isinstance(engine, Mapping) and engine.get("id") else None


def _counts(rows: list[Any]) -> tuple[int, int]:
    steps = sum(1 for row in rows if row.data.get("kind") == "add_step" and row.verdict != "refused")
    reqs = sum(1 for row in rows if row.field == "requirement" and row.op == "add" and row.verdict != "refused")
    return steps, reqs


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def plan_draft(service: Any, principal: Any, program_id: str, *, goal: Any = None, template: Any = None,
               budget: Any = None, text: Any = None, split: Any = None,
               invoke_fn: Optional[Callable[..., tuple[Optional[str], str]]] = None) -> dict[str, Any]:
    """The REST and MCP answer: the draft's rows in the ``text_apply``
    answer shape (the well draws it as it is; each row has ``source:
    "plan"`` and an added step its ``size``), the engine and its time."""
    result = plan(service, principal, program_id, goal_text=goal, template=template, budget=budget, text=text,
                  split=split, invoke_fn=invoke_fn)
    program = service._program(program_id)
    wire = service.get(principal, program["id"])
    out = shaper._answer(service, principal, program, wire, result.base_text, result.proposed_text, result.rows)
    for row, item in zip(result.rows, out["changes"]):
        item["source"] = "plan"
        item["size"] = row.data.get("size")
    steps, reqs = _counts(result.rows)
    too_big = [row for row in result.sizes if row["fits"] is False]
    words = " · ".join(part for part in (_plural(steps, "step") if steps else "",
                                         _plural(reqs, "requirement") if reqs else "",
                                         f"{len(too_big)} too big" if too_big else "") if part)
    out.update(say=result.say or words, counts={"steps": steps, "requirements": reqs, "too_big": len(too_big)},
               words=words, engine=result.engine, latency_ms=result.latency_ms,
               seconds=round(result.latency_ms / 1000, 1), grounded_on=result.grounded_on, sizes=result.sizes,
               budget=result.budget, share=sizing.share_of(result.budget) if result.budget else None,
               split=result.split, attempts=result.attempts, capability=result.capability,
               proposed_text=result.proposed_text, base=result.base_text, source="plan",
               programs=result.programs)
    return out


__all__ = ["CONTRACT", "DEADLINE_SECONDS", "PLAN_RULES", "PlanResult", "SPLIT_RULES", "apply_programs", "messages", "plan", "plan_draft",
           "repo_ground", "response_format", "size_steps", "template_card", "token_cap"]
