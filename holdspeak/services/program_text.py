"""The Program text (PG-LANG LANG1, 2026-10-31): parse, print and diff.

docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md §3. The
text is a readable, line-oriented view of one Program that round-trips with
its tables; the tables stay the truth. This module is pure (no I/O, no
database): :func:`print_program` writes the text of a Program as
``ProgramService.get`` answers it, :func:`parse_program_text` reads a text
into a :class:`ProgramText`, and :func:`diff_program_text` gives the change
rows between two texts (§3.8), each one with its verdict when the current
record is given (the frozen table of PG-REQ §8, ``step_fields``).

The rules, in short:

- one statement per line; two spaces of indent put a line under the last
  ``program``, ``step``, ``every step``, ``at the end`` or ``round`` header;
  four spaces put a line under the last requirement;
- two or more spaces and ``#`` to the end of a line is a **lamp**: the
  printer writes the state there, the parser ignores it; a line that starts
  with ``#`` is a lamp too (the version line ``# program text 1``);
- ``>`` lines are his words (a goal, a brief), kept byte for byte after
  ``> ``; no lamp is read on them;
- ``·`` joins short statements on one line (a step's agent and effort, its
  gates; the Program's flags);
- defaults are not printed: a field that says nothing is ``None`` in the
  model, and its value is the rule's (the template's step shape, the
  Program's agents, ``triage_effort``). ``parse(print(p))`` is the model of
  ``p``, field for field (§3.3).

Rounds (§6.2) are read into the model and printed back; ``program_rounds``
holds them (PG-LANG fields, 2026-10-31). His ``=`` answers, a round's state
(not ``asking``: the engine's) and new rounds apply; the ``?`` questions are
the engine's (LANG9 asks them) and a changed one is refused.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field, fields as dc_fields, replace
from typing import Any, Iterable, Mapping, Optional

from ..program_templates import get_template
from .program_requirements import bound_words, clean_spec, parse_bound

#: The format version the printer writes (§7.4).
VERSION = 1
VERSION_LINE = f"# program text {VERSION}"

KINDS = ("check", "review", "shot", "word", "measure")
CONTROLS = ("secure", "normal", "yolo")
EFFORTS = ("low", "medium", "high")
REVIEWS = ("none", "agent", "person")
DEPTHS = ("glance", "delta", "standard")
MERGES = ("level", "owner", "none")
ROUND_STATES = ("open", "asking", "done", "skipped")

#: The agents and the words they print as.
AGENT_WORDS = {"claude-default": "Claude Code", "codex-default": "Codex", "pi-default": "pi"}
_AGENT_ALIASES = {"claudecode": "claude-default", "claude": "claude-default", "codex": "codex-default",
                  "pi": "pi-default"}

#: Words of the version-1 grammar that no table holds yet. Every word of
#: §3.2 has a home since the PG-LANG fields lane (2026-10-31); a word added
#: to the grammar before its table goes here and is refused by name, never
#: dropped (§7.4).
_LATER_PROGRAM: tuple[str, ...] = ()
_LATER_STEP: tuple[str, ...] = ()
_LATER_REQ: tuple[str, ...] = ()
#: ``night 23:30–07:00 · at most 8 steps`` (an en dash or a hyphen).
_NIGHT = re.compile(r"^(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})(?:\s*·\s*at most (\d+) steps?)?$")
_TOKENS = re.compile(r"^(\d+)\s*(k|K)?$")

#: The lamp: two or more spaces, then ``#`` and the rest of the line.
_LAMP = re.compile(r"\s{2,}#(?:\s.*)?$")
_REQ = re.compile(r"^R(\d+|\+) ([a-z]+)( optional)?: (.*)$")
_STEP = re.compile(r"^step (\d+|\+) (.+)$")
_ROUND = re.compile(r"^round (.+?) · ([a-z]+)$")
_HEX = re.compile(r"^[0-9a-f]{7,64}$")

#: Lowering the bar (§4.5): the order of each gate, weakest first.
_DEPTH_RANK = {"glance": 0, "delta": 1, "standard": 2}
_CONTROL_RANK = {"secure": 0, "normal": 1, "yolo": 2}
_STRONG_KINDS = frozenset({"check", "shot", "measure"})


# ── the model ────────────────────────────────────────────────────────

Agent = tuple[str, Optional[str]]


@dataclass
class TextError:
    """A line the parser cannot read: a refusal by name (§3.9)."""

    line: int
    code: str
    words: str


@dataclass
class Requirement:
    rid: Optional[int]          # None: ``R+``, a new one
    kind: str
    text: str
    required: bool = True
    spec: dict[str, Any] = field(default_factory=dict)
    waived: Optional[str] = None
    line: int = field(default=0, compare=False)


@dataclass
class Amendment:
    text: str
    line: int = field(default=0, compare=False)


@dataclass
class Step:
    number: Optional[int]       # None: ``step +``, a new one
    title: str
    owns: list[str] = field(default_factory=list)
    after: list[int] = field(default_factory=list)
    agents: Optional[list[Agent]] = None    # None: the Program's
    effort: Optional[str] = None            # None: by rule (triage_effort)
    race: Optional[int] = None              # None: the template's
    when_idle: bool = False
    may_call: bool = False
    check: Optional[bool] = None            # None: the template's
    review: Optional[str] = None            # None: the template's (and the reviewer)
    depth: Optional[str] = None             # None: the template's
    merge: Optional[str] = None             # None: the template's
    for_person: Optional[str] = None
    origin: Optional[str] = None
    merged: Optional[dict[str, Any]] = None  # PG17: {pr_number, merged_at, pr_url, head_commit}
    budget: Optional[int] = None            # None: the Program's (§5.4)
    brief: str = ""
    amendments: list[Amendment] = field(default_factory=list)
    requirements: list[Requirement] = field(default_factory=list)
    line: int = field(default=0, compare=False)


@dataclass
class Question:
    text: str
    answer: Optional[str] = None


@dataclass
class Round:
    name: str
    state: str
    questions: list[Question] = field(default_factory=list)
    line: int = field(default=0, compare=False)


@dataclass
class Head:
    title: str = ""
    goal: str = ""
    repository: Optional[str] = None
    branch: Optional[str] = None
    project: Optional[str] = None
    control: Optional[str] = None
    check: Optional[str] = None             # "" = ``check none``
    agents: Optional[list[Agent]] = None    # None: the template's
    reviewer: Optional[Agent] = None        # None: the template's; ("none", None): no reviewer
    depth: Optional[str] = None             # ``reviewer X at <depth>``; None: the template's
    planner: Optional[str] = None           # an engine of the library (§4.3, §5.5); None: the desk's
    budget: Optional[int] = None            # tokens (§5.4); None: the first agent's engine window
    night: Optional[dict[str, Any]] = None  # {line, start, end, max_steps} (§5.5)
    within: list[str] = field(default_factory=list)  # the paths it may own at all (§5.5)
    delivery: Optional[str] = None          # "<project>/<phase>[/<story>]" of ``delivery dw`` (§8)
    rounds_before_start: bool = False       # §15.5: the rounds gate Start
    when_idle: bool = False
    may_call: bool = False
    may_hand_off: bool = False
    allow: list[str] = field(default_factory=list)
    spend: Optional[float] = None
    usage_warning: Optional[float] = None
    for_person: Optional[str] = None
    origin: Optional[str] = None
    template: Optional[str] = None
    line: int = field(default=0, compare=False)


@dataclass
class ProgramText:
    """One Program's definition as the text says it (lossless)."""

    head: Head = field(default_factory=Head)
    every_step: list[Requirement] = field(default_factory=list)
    at_end: list[Requirement] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    rounds: list[Round] = field(default_factory=list)
    version: int = VERSION
    errors: list[TextError] = field(default_factory=list, compare=False)

    def step(self, number: int) -> Optional[Step]:
        return next((step for step in self.steps if step.number == number), None)

    def requirements(self) -> list[tuple[str, Requirement]]:
        """Every requirement with its scope (``every step``, ``at the end``,
        ``step N``; a new step's are ``step +``)."""
        out = [("every step", row) for row in self.every_step] + [("at the end", row) for row in self.at_end]
        for step in self.steps:
            where = f"step {step.number}" if step.number is not None else "step +"
            out += [(where, row) for row in step.requirements]
        return out


# ── defaults (the rules the service uses) ────────────────────────────

def _shape(template: Optional[str]) -> dict[str, Any]:
    return dict((get_template(template) or {}).get("step") or {}) if template else {}


def template_agents(template: Optional[str]) -> list[Agent]:
    program = (get_template(template) or {}).get("program") or {} if template else {}
    return [(str(program.get("default_profile") or "claude-default"), program.get("default_engine") or None)]


def template_reviewer(template: Optional[str]) -> Agent:
    program = (get_template(template) or {}).get("program") or {} if template else {}
    profile = program.get("reviewer_profile")
    return (str(profile), program.get("reviewer_engine") or None) if profile else ("none", None)


def template_depth(template: Optional[str]) -> str:
    return str(_shape(template).get("review_depth") or "delta")


def program_depth(head: Head) -> str:
    """The review depth a step takes when it states none."""
    return head.depth or template_depth(head.template)


def parse_tokens(value: Any) -> Optional[int]:
    """``64k`` = 65536; ``32768``; ``None`` when it is not a number of
    tokens (§3.2 TOKENS)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    found = _TOKENS.match(str(value or "").strip())
    if not found:
        return None
    tokens = int(found.group(1)) * (1024 if found.group(2) else 1)
    return tokens if tokens > 0 else None


def tokens_words(tokens: int) -> str:
    return f"{tokens // 1024}k" if tokens % 1024 == 0 else str(tokens)


def parse_night(value: Any) -> Optional[dict[str, Any]]:
    """``23:30–07:00 · at most 8 steps`` (or ``{start, end, max_steps}``) ->
    ``{line, start, end, max_steps}``; ``None`` when it is not a night."""
    if isinstance(value, Mapping):
        value = f"{value.get('start') or ''}–{value.get('end') or ''}" + (
            f" · at most {value['max_steps']} steps" if value.get("max_steps") else "")
    found = _NIGHT.match(" ".join(str(value or "").split()))
    if not found:
        return None
    hours = (int(found.group(1)), int(found.group(3)))
    minutes = (int(found.group(2)), int(found.group(4)))
    if any(hour > 23 for hour in hours) or any(minute > 59 for minute in minutes):
        return None
    start, end = f"{hours[0]:02d}:{minutes[0]:02d}", f"{hours[1]:02d}:{minutes[1]:02d}"
    most = int(found.group(5)) if found.group(5) else None
    if most is not None and most < 1:
        return None
    line = f"{start}–{end}" + (f" · at most {most} step{'s' if most != 1 else ''}" if most else "")
    return {"line": line, "start": start, "end": end, "max_steps": most}


def program_agents(head: Head) -> list[Agent]:
    return list(head.agents) if head.agents else template_agents(head.template)


def program_reviewer(head: Head) -> Agent:
    return head.reviewer if head.reviewer is not None else template_reviewer(head.template)


def step_agents(head: Head, step: Step) -> list[Agent]:
    """The step's ordered agents, as ``ProgramService.runs_on_of`` reads
    them: its own list; or its one agent, then the Program's others; else
    the Program's."""
    default = program_agents(head)
    if not step.agents:
        return default
    if len(step.agents) > 1:
        return list(step.agents)
    first = step.agents[0]
    return [first] + [agent for agent in default if agent != first]


def _minimal_agents(listed: list[Agent], default: list[Agent]) -> Optional[list[Agent]]:
    """The shortest statement that reads back as ``listed``."""
    if listed == default:
        return None
    first = listed[0]
    if listed == [first] + [agent for agent in default if agent != first]:
        return [first]
    return list(listed)


def triage(brief: str, owns: Iterable[str]) -> str:
    from .program_service import triage_effort

    return triage_effort(brief, owns)


def step_value(head: Head, step: Step, name: str) -> Any:
    """A step field's value: what the text says, else the rule's."""
    shape = _shape(head.template)
    value = getattr(step, name)
    if name == "agents":
        return step_agents(head, step)
    if value is not None:
        return value
    if name == "effort":
        return triage(step.brief, step.owns)
    if name == "race":
        race = int(shape.get("race") or 0)
        return 0 if race == 1 else race
    if name == "check":
        return bool(shape.get("gate_check", True))
    if name == "review":
        return "agent" if shape.get("gate_review") and program_reviewer(head)[0] != "none" else "none"
    if name == "depth":
        return program_depth(head)
    if name == "merge":
        return str(shape.get("gate_merge") or "level")
    return value


def guessed_spec(kind: str, text: str) -> dict[str, Any]:
    """The spec the kind rule fills from the sentence alone (§3.2: such a
    sub-line is not printed)."""
    try:
        return clean_spec(kind, {}, text)
    except Exception:
        return {}


# ── from the wire (``ProgramService.get``) ───────────────────────────

def _agent_of(entry: Mapping[str, Any]) -> Agent:
    return (str(entry.get("profile") or "claude-default"), entry.get("engine") or None)


def _req_of(row: Mapping[str, Any]) -> Requirement:
    return Requirement(rid=int(row.get("ordinal") or 0), kind=str(row.get("kind") or "review"),
                       text=str(row.get("text") or ""), required=bool(row.get("required", True)),
                       spec=dict(row.get("spec") or {}),
                       waived=(str(row.get("waived_reason") or "") or None) if row.get("state") == "waived" else None)


def from_wire(wire: Mapping[str, Any], steps: Optional[list[Mapping[str, Any]]] = None,
              requirements: Optional[list[Mapping[str, Any]]] = None) -> ProgramText:
    """The definition of a Program (as ``ProgramService.get`` answers it), in
    the canonical form the printer writes: a value equal to its default is
    ``None``."""
    template = str(wire.get("template") or "") or None
    default = wire.get("default") or {}
    listed = [_agent_of(row) for row in default.get("runs_on") or []] or [
        (str(default.get("profile") or "claude-default"), (default.get("engine") or {}).get("id")
         if isinstance(default.get("engine"), Mapping) else None)]
    reviewer_wire = wire.get("reviewer") or {}
    reviewer: Agent = (str(reviewer_wire.get("profile")), ((reviewer_wire.get("engine") or {}).get("id")
                       if isinstance(reviewer_wire.get("engine"), Mapping) else None)) \
        if reviewer_wire.get("profile") else ("none", None)
    place = wire.get("place") or {}
    person = place.get("person") or {}
    repository = wire.get("repository") or {}
    head = Head(
        title=str(wire.get("title") or ""), goal=str(wire.get("goal") or ""),
        repository=str(repository.get("label") or "") or None, branch=repository.get("base_branch") or None,
        project=((place.get("project") or {}).get("name") or None),
        control=str(wire.get("control") or "") or None,
        check=str(wire.get("check_command") or ""),
        agents=None, reviewer=None,
        when_idle=bool(wire.get("prefer_idle")), may_call=bool(wire.get("may_call")),
        may_hand_off=bool(wire.get("may_handoff")),
        allow=[str(item) for item in wire.get("allowed_profiles") or []],
        spend=float(wire["spend_limit_usd"]) if wire.get("spend_limit_usd") is not None else None,
        usage_warning=float(wire["usage_warning_share"]) if wire.get("usage_warning_share") is not None else None,
        for_person=(person.get("name") or wire.get("for_person_id") or None),
        origin=wire.get("origin_ref") or None, template=template,
        depth=wire.get("review_depth") or None,
        planner=((wire.get("planner") or {}).get("engine") or None) if isinstance(wire.get("planner"), Mapping) else None,
        budget=int(wire["budget_tokens"]) if wire.get("budget_tokens") else None,
        night=parse_night(wire["night"]) if isinstance(wire.get("night"), Mapping) else None,
        within=[str(item) for item in wire.get("within") or []],
        delivery=((wire.get("delivery") or {}).get("ref") or None) if isinstance(wire.get("delivery"), Mapping) else None,
        rounds_before_start=bool(wire.get("rounds_before_start")),
    )
    head.agents = None if listed == template_agents(template) else listed
    head.reviewer = None if reviewer == template_reviewer(template) else reviewer
    if head.depth == template_depth(template):
        head.depth = None
    reqs = list(requirements if requirements is not None else wire.get("requirements") or [])
    model = ProgramText(head=head)
    model.rounds = [Round(name=str(item.get("name") or ""), state=str(item.get("state") or "open"),
                          questions=[Question(str(question.get("text") or ""), question.get("answer") or None)
                                     for question in item.get("questions") or []])
                    for item in sorted(wire.get("rounds") or [], key=lambda row: int(row.get("order") or 0))]
    for row in sorted(reqs, key=lambda item: int(item.get("ordinal") or 0)):
        if row.get("step_id") or row.get("parent_id"):
            continue
        (model.every_step if row.get("scope") == "every_step" else model.at_end).append(_req_of(row))
    for raw in sorted(steps if steps is not None else wire.get("steps") or [], key=lambda item: int(item["ordinal"])):
        if raw.get("race_of"):
            continue
        step = Step(number=int(raw["ordinal"]), title=str(raw.get("title") or ""),
                    owns=[str(item) for item in raw.get("owns") or []],
                    after=sorted(int(value) for value in raw.get("after") or []),
                    brief=str(raw.get("brief") or ""))
        own = [_agent_of(row) for row in raw.get("runs_on") or []]
        if own:
            step.agents = _minimal_agents(own, program_agents(head))
        step.effort = raw.get("effort") or None
        if step.effort == triage(step.brief, step.owns):
            step.effort = None
        gate = raw.get("gate") or {}
        step.race = int(raw.get("race") or 0)
        step.check = bool(gate.get("check", True))
        step.review = str(gate.get("review") or "none")
        step.depth = str(gate.get("review_depth") or "delta")
        step.merge = str(gate.get("merge") or "level")
        for name in ("race", "check", "review", "depth", "merge"):
            probe = replace(step, **{name: None})
            if step_value(head, probe, name) == getattr(step, name):
                setattr(step, name, None)
        step.when_idle = bool(raw.get("prefer_idle")) and not head.when_idle
        step.may_call = bool(raw.get("may_call")) and not head.may_call
        step.for_person = raw.get("for_person") or raw.get("for_person_id") or None
        step.origin = raw.get("origin_ref") or None
        step.budget = int(raw["budget_tokens"]) if raw.get("budget_tokens") else None
        history = raw.get("history")
        if isinstance(history, Mapping) and history.get("pr_number"):
            step.merged = {key: history.get(key) for key in ("pr_number", "merged_at", "pr_url", "head_commit")}
        step.amendments = [Amendment(str(item.get("line") or "")) for item in raw.get("amendments") or []]
        step.requirements = [_req_of(row) for row in sorted(raw.get("requirements") or [],
                                                             key=lambda item: int(item.get("ordinal") or 0))
                             if not row.get("parent_id")]
        model.steps.append(step)
    return model


# ── printing ─────────────────────────────────────────────────────────

def agent_words(agent: Agent) -> str:
    profile, engine = agent
    words = AGENT_WORDS.get(profile, profile)
    return f"{words} on {engine}" if engine else words


def agents_words(agents: Iterable[Agent]) -> str:
    return ", then ".join(agent_words(agent) for agent in agents)


def _number(value: float) -> str:
    value = float(value)
    return str(int(value)) if value.is_integer() else repr(value)


def _quote(indent: str, text: str) -> list[str]:
    return [f"{indent}> {line}" if line else f"{indent}>" for line in text.split("\n")]


def _lamp(line: str, lamp: Optional[str]) -> str:
    if not lamp:
        return line
    return f"{line.ljust(48)}  # {lamp}" if len(line) < 48 else f"{line}  # {lamp}"


def _req_lines(indent: str, row: Requirement, lamp: Optional[str]) -> list[str]:
    rid = "R+" if row.rid is None else f"R{row.rid}"
    lines = [_lamp(f"{indent}{rid} {row.kind}{' optional' if not row.required else ''}: {row.text}", lamp)]
    sub = indent + "  "
    guessed = guessed_spec(row.kind, row.text)
    spec = dict(row.spec or {})
    if row.kind == "check":
        if spec.get("command") and spec.get("command") != guessed.get("command"):
            lines.append(f"{sub}run {spec['command']}")
        if spec.get("expect"):
            lines.append(f"{sub}expect {spec['expect']}")
    elif row.kind == "shot" and (spec.get("case"), spec.get("width")) != (guessed.get("case"), guessed.get("width")):
        if spec.get("case") or spec.get("width"):
            lines.append(f"{sub}shot {spec.get('case') or ''} at {spec.get('width') or ''}".rstrip())
    elif row.kind == "measure":
        if spec.get("command") and spec.get("command") != guessed.get("command"):
            lines.append(f"{sub}run {spec['command']}")
        if spec.get("expect"):
            lines.append(f"{sub}expect {spec['expect']}")
        if spec.get("metric"):
            lines.append(f"{sub}bound {bound_words(spec)}")
    elif row.kind == "word":
        lines += [f"{sub}walk {line}" for line in spec.get("walk") or []]
    if row.waived is not None:
        lines.append(f"{sub}waived: {row.waived}")
    return lines


def render(model: ProgramText, lamps: Optional[Mapping[str, str]] = None) -> str:
    """The text of ``model`` (defaults dropped); ``lamps`` by key
    (``program``, ``step N``, ``R N``, ``step N +i``)."""
    lamps = lamps or {}
    head = model.head
    out = [VERSION_LINE, _lamp(f"program {head.title}", lamps.get("program"))]
    if head.goal:
        out.append("  goal")
        out += _quote("  ", head.goal)
    if head.repository:
        place = head.repository + (f" · {head.branch}" if head.branch else "")
        if head.project:
            place += f" · project {head.project}"
        out.append(f"  in {place}")
    if head.template:
        out.append(f"  template {head.template.replace('-', ' ')}")
    if head.control:
        out.append(f"  control {head.control}")
    if head.check is not None:
        out.append(f"  check {head.check or 'none'}")
    if head.agents:
        out.append(f"  agent {agents_words(head.agents)}")
    if head.planner:
        out.append(f"  planner {head.planner}")
    if head.reviewer is not None or head.depth is not None:
        reviewer = program_reviewer(head)
        out.append(f"  reviewer {'none' if reviewer[0] == 'none' else agent_words(reviewer)}"
                   + (f" at {head.depth}" if head.depth is not None else ""))
    if head.budget:
        out.append(f"  budget {tokens_words(head.budget)}")
    flags = [word for word, on in (("when idle", head.when_idle), ("may call", head.may_call),
                                   ("may hand off", head.may_hand_off),
                                   ("rounds before start", head.rounds_before_start)) if on]
    if flags:
        out.append("  " + " · ".join(flags))
    if head.night:
        out.append(f"  night {head.night['line']}")
    if head.within:
        out.append(f"  within {', '.join(head.within)}")
    if head.allow:
        out.append(f"  allow {', '.join(agent_words((profile, None)) for profile in head.allow)}")
    if head.spend is not None:
        out.append(f"  spend up to ${_number(head.spend)}")
    if head.usage_warning is not None:
        out.append(f"  usage warning {_number(round(head.usage_warning * 100, 6))}%")
    if head.delivery:
        out.append(f"  delivery dw {head.delivery}")
    if head.for_person:
        out.append(f"  for {head.for_person}")
    if head.origin:
        out.append(f"  from {head.origin}")
    for title, rows in (("every step", model.every_step), ("at the end", model.at_end)):
        if rows:
            out += ["", title]
            for row in rows:
                out += _req_lines("  ", row, lamps.get(f"R{row.rid}") if row.rid is not None else None)
    for item in model.rounds:
        out += ["", f"round {item.name} · {item.state}"]
        for index, question in enumerate(item.questions, start=1):
            out.append(f"  ? {question.text}")
            if question.answer is not None:
                # The lamp names what the answer became (LANG9): `# → step 1 owns, R+ measure`.
                out.append(_lamp(f"  = {question.answer}", lamps.get(f"round {_fold(item.name)} ={index}")))
    for step in model.steps:
        number = "+" if step.number is None else str(step.number)
        out += ["", _lamp(f"step {number} {step.title}", lamps.get(f"step {step.number}"))]
        if step.merged:
            parts = [f"merged #{step.merged.get('pr_number')}"]
            parts += [str(step.merged[key]) for key in ("merged_at", "pr_url", "head_commit") if step.merged.get(key)]
            out.append("  " + " · ".join(parts))
        if step.owns:
            out.append(f"  owns {', '.join(step.owns)}")
        if step.after:
            out.append(f"  after {', '.join(str(value) for value in step.after)}")
        work = []
        if step.agents:
            work.append(f"agent {agents_words(step.agents)}")
        if step.effort:
            work.append(f"effort {step.effort}")
        if work:
            out.append("  " + " · ".join(work))
        if step.race is not None:
            out.append(f"  race {step.race}")
        if step.budget:
            out.append(f"  budget {tokens_words(step.budget)}")
        flags = [word for word, on in (("when idle", step.when_idle), ("may call", step.may_call)) if on]
        if flags:
            out.append("  " + " · ".join(flags))
        gates = []
        named = step.review == "person" and bool(step.for_person)
        if step.review is not None or step.depth is not None:
            review = step.review if step.review is not None else step_value(model.head, step, "review")
            review = step.for_person if named else review
            gates.append(f"review {review}" + (f" at {step.depth}" if step.depth is not None else ""))
        if step.merge is not None:
            gates.append(f"merge {step.merge}")
        if step.check is not None:
            gates.append("check on" if step.check else "check off")
        if gates:
            out.append("  " + " · ".join(gates))
        if step.for_person and not named:
            out.append(f"  for {step.for_person}")
        if step.origin:
            out.append(f"  from {step.origin}")
        if step.brief:
            out.append("  brief")
            out += _quote("  ", step.brief)
        for index, amendment in enumerate(step.amendments, start=1):
            out.append(_lamp(f"  + {amendment.text}", lamps.get(f"step {step.number} +{index}")))
        for row in step.requirements:
            out += _req_lines("  ", row, lamps.get(f"R{row.rid}") if row.rid is not None else None)
    return "\n".join(out) + "\n"


def _clock(stamp: Any) -> str:
    from datetime import datetime

    try:
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).astimezone().strftime("%H:%M")
    except ValueError:
        return ""


def wire_lamps(wire: Mapping[str, Any]) -> dict[str, str]:
    """The run, in lamps (§3.2): never a statement, never read back."""
    lamps: dict[str, str] = {}
    steps = [step for step in wire.get("steps") or [] if not step.get("race_of")]
    done = sum(1 for step in steps if step.get("state") in ("merged", "done"))
    lamps["program"] = " · ".join(part for part in (str(wire.get("state_word") or ""),
                                                     f"{done} of {len(steps)} done" if steps else "") if part)
    rows = list(wire.get("requirements") or [])
    for step in steps:
        words = [str(step.get("state_word") or step.get("state") or "")]
        if step.get("state") in ("merged", "done") and (step.get("pr") or {}).get("number"):
            words = [f"Merged #{step['pr']['number']}"]
        elif step.get("state") not in ("planned", "ready", "merged", "done", "parked") and step.get("agent"):
            words.append(str(step["agent"]))
        if step.get("elapsed"):
            words.append(str(step["elapsed"]))
        lamps[f"step {step['ordinal']}"] = " · ".join(word for word in words if word)
        for index, item in enumerate(step.get("amendments") or [], start=1):
            lamps[f"step {step['ordinal']} +{index}"] = (f"sent {_clock(item['sent_at'])}" if item.get("sent_at")
                                                         else "waits for a turn end")
        rows += [row for row in step.get("requirements") or [] if not row.get("parent_id")]
    for row in rows:
        if row.get("ordinal") is not None:
            lamps[f"R{row['ordinal']}"] = str(row.get("state_word") or "")
    for item in wire.get("rounds") or []:
        for index, question in enumerate(item.get("questions") or [], start=1):
            if question.get("answer") and question.get("became"):
                lamps[f"round {_fold(str(item.get('name') or ''))} ={index}"] = "→ " + ", ".join(map(str, question["became"]))
    return lamps


def print_program(program: Mapping[str, Any], steps: Optional[list[Mapping[str, Any]]] = None,
                  requirements: Optional[list[Mapping[str, Any]]] = None,
                  rounds: Optional[list[Round]] = None, *, lamps: bool = True) -> str:
    """The text of one Program as ``ProgramService.get`` answers it (its
    steps and requirements are on the wire; pass them to print others).
    ``rounds`` is the hook for the interview rounds (LANG9)."""
    model = from_wire(program, steps, requirements)
    if rounds:
        model.rounds = list(rounds)
    return render(model, wire_lamps(program) if lamps else None)


# ── parsing ──────────────────────────────────────────────────────────

def _fold(word: str) -> str:
    return "".join(str(word).split()).casefold()


def parse_agent(words: str) -> Agent:
    text = " ".join(str(words).split())
    name, _sep, engine = text.partition(" on ")
    profile = _AGENT_ALIASES.get(_fold(name), name.strip())
    return profile, (engine.strip() or None)


def parse_agents(words: str) -> list[Agent]:
    return [parse_agent(part) for part in re.split(r",\s*then\s+|,\s*", str(words)) if part.strip()]


def _numbers(words: str) -> Optional[list[int]]:
    parts = [part.strip() for part in str(words).split(",") if part.strip()]
    if not parts or not all(part.isdigit() for part in parts):
        return None
    return sorted({int(part) for part in parts})


class _Reader:
    def __init__(self, text: str) -> None:
        self.text = str(text or "")
        self.model = ProgramText()
        self.errors = self.model.errors
        self.block: Optional[str] = None   # program | every | end | step | round
        self.step: Optional[Step] = None
        self.round: Optional[Round] = None
        self.req: Optional[Requirement] = None
        self.quote: Optional[str] = None   # goal | brief
        self.quote_lines: list[str] = []
        self.seen_program = False
        self.skip_sub = False

    def error(self, line: int, code: str, words: str) -> None:
        self.errors.append(TextError(line, code, words))

    def unknown(self, number: int, word: str) -> None:
        self.error(number, "text_unknown_word", f"Line {number}: '{word}' is not a word of the program text.")

    def later(self, number: int, word: str) -> None:
        self.error(number, "text_unknown_word",
                   f"Line {number}: '{word}' is a word of the program text that this hub does not read yet.")

    def bad(self, number: int, words: str) -> None:
        self.error(number, "text_bad_value", f"Line {number}: {words}")

    def close_quote(self) -> None:
        if self.quote is None:
            return
        text = "\n".join(self.quote_lines)
        if self.quote == "goal":
            self.model.head.goal = text
        elif self.step is not None:
            self.step.brief = text
        self.quote, self.quote_lines = None, []

    def read(self) -> ProgramText:
        lines = self.text.split("\n")
        first = True
        for number, raw in enumerate(lines, start=1):
            raw = raw.rstrip("\r").replace("\t", "  ")
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            body = raw[indent:]
            if body.startswith(">"):
                if self.quote is None or indent != 2:
                    self.bad(number, "a '>' line belongs under goal or brief.")
                    continue
                self.quote_lines.append(body[2:] if body.startswith("> ") else body[1:])
                continue
            self.close_quote()
            if body.startswith("#"):
                found = re.match(r"^#\s*program text (\d+)\s*$", body)
                if found and first:
                    version = int(found.group(1))
                    self.model.version = version
                    if version != VERSION:
                        self.error(number, "text_version",
                                   f"This text is version {version}; this hub reads version {VERSION}.")
                first = False
                continue
            first = False
            body = _LAMP.sub("", body).rstrip()
            if not body:
                continue
            if indent != 4:
                self.skip_sub = False
            if indent == 0:
                self.header(number, body)
            elif indent == 2:
                self.statement(number, body)
            elif indent == 4:
                self.sub(number, body)
            else:
                self.bad(number, "indent with two spaces under a header, four under a requirement.")
        self.close_quote()
        if not self.seen_program:
            self.error(1, "text_unknown_word", "Line 1: the text has no 'program' line.")
        return self.model

    # headers ---------------------------------------------------------

    def header(self, number: int, body: str) -> None:
        self.step = self.round = self.req = None
        if body.startswith("program "):
            if self.seen_program:
                self.bad(number, "a text has one program.")
            self.seen_program = True
            self.block = "program"
            self.model.head.title = " ".join(body[len("program "):].split())
            self.model.head.line = number
            return
        if body == "every step":
            self.block = "every"
            return
        if body == "at the end":
            self.block = "end"
            return
        found = _STEP.match(body)
        if found:
            self.block = "step"
            ident = None if found.group(1) == "+" else int(found.group(1))
            if ident is not None and self.model.step(ident) is not None:
                self.bad(number, f"step {ident} is in the text twice.")
            self.step = Step(number=ident, title=" ".join(found.group(2).split()), line=number)
            self.model.steps.append(self.step)
            return
        found = _ROUND.match(body)
        if found:
            self.block = "round"
            state = found.group(2)
            if state not in ROUND_STATES:
                self.bad(number, "a round is open, asking, done or skipped.")
            self.round = Round(name=found.group(1).strip(), state=state, line=number)
            self.model.rounds.append(self.round)
            return
        self.block = None
        self.unknown(number, body.split(" ")[0])

    # statements ------------------------------------------------------

    def statement(self, number: int, body: str) -> None:
        if self.block == "program":
            self.program_line(number, body)
        elif self.block in ("every", "end"):
            row = self.requirement(number, body)
            if row is not None:
                (self.model.every_step if self.block == "every" else self.model.at_end).append(row)
        elif self.block == "step" and self.step is not None:
            self.step_line(number, body)
        elif self.block == "round" and self.round is not None:
            if body.startswith("? "):
                self.round.questions.append(Question(body[2:].strip()))
            elif body.startswith("= ") and self.round.questions:
                self.round.questions[-1].answer = body[2:].strip()
            else:
                self.bad(number, "a round holds '?' questions and '=' answers.")
        else:
            self.bad(number, "this line is under no header.")

    def requirement(self, number: int, body: str) -> Optional[Requirement]:
        found = _REQ.match(body)
        if not found:
            if re.match(r"^R(\d+|\+)(\s|$)", body):
                self.bad(number, "a requirement is 'R<n> <kind>: <sentence>' (check, review, shot, word or measure).")
            else:
                self.unknown(number, body.split(" ")[0])
            return None
        kind = found.group(2)
        if kind not in KINDS:
            self.bad(number, "a requirement is a check, a review, a shot, your word or a measure.")
            return None
        text = " ".join(found.group(4).split())
        row = Requirement(rid=None if found.group(1) == "+" else int(found.group(1)), kind=kind, text=text,
                          required=not found.group(3), spec=guessed_spec(kind, text), line=number)
        if row.rid is not None and any(other.rid == row.rid for _where, other in self.model.requirements()):
            self.bad(number, f"R{row.rid} is in the text twice.")
        self.req = row
        return row

    def sub(self, number: int, body: str) -> None:
        if self.skip_sub:
            return
        row = self.req
        if row is None:
            self.bad(number, "a line with four spaces belongs under a requirement.")
            return
        word, _sep, rest = body.partition(" ")
        rest = rest.strip()
        if word == "run" and row.kind in ("check", "measure") and rest:
            row.spec["command"] = rest
        elif word == "bound" and row.kind == "measure":
            bound = parse_bound(rest)
            if bound is None:
                self.bad(number, "a bound is '<metric> <op> <number> <unit>' ('p95 < 100 ms').")
                return
            row.spec.update(bound)
        elif word == "walk" and row.kind == "word" and rest:
            row.spec.setdefault("walk", []).append(" ".join(rest.split()))
        elif word == "expect" and row.kind in ("check", "measure") and rest:
            try:
                re.compile(rest)
            except re.error:
                self.bad(number, "the expected line is not a pattern.")
                return
            row.spec["expect"] = rest
        elif word == "shot" and row.kind == "shot":
            found = re.match(r"^(\S+) at (\d+)$", rest)
            if not found or int(found.group(2)) not in (393, 1440):
                self.bad(number, "a shot is '<window> at 393' or '<window> at 1440'.")
                return
            row.spec.update({"case": found.group(1).lower(), "width": int(found.group(2))})
        elif word == "waived:":
            row.waived = rest
        elif word in ("run", "expect", "bound", "walk", "shot") and rest:
            self.bad(number, {"run": "'run' belongs under a check or a measure.",
                              "expect": "'expect' belongs under a check or a measure.",
                              "bound": "'bound' belongs under a measure.", "walk": "'walk' belongs under your word.",
                              "shot": "'shot' belongs under a shot."}[word])
        elif word in _LATER_REQ:
            self.later(number, word)
        else:
            self.unknown(number, word)

    def program_line(self, number: int, body: str) -> None:
        head = self.model.head
        if body.startswith(("in ", "check ", "night ")) or body == "goal":
            parts = [body]
        else:
            parts = [part.strip() for part in body.split(" · ")]
        for part in parts:
            word, _sep, rest = part.partition(" ")
            rest = rest.strip()
            if part == "goal":
                self.quote, self.quote_lines = "goal", []
            elif word == "in" and rest:
                pieces = [piece.strip() for piece in rest.split(" · ")]
                head.repository = pieces[0]
                for piece in pieces[1:]:
                    if piece.startswith("project "):
                        head.project = piece[len("project "):].strip()
                    else:
                        head.branch = piece
            elif word == "control":
                if rest not in CONTROLS:
                    self.bad(number, "control is secure, normal or yolo.")
                else:
                    head.control = rest
            elif word == "check" and rest:
                head.check = "" if rest == "none" else rest
            elif word == "agent" and rest:
                head.agents = parse_agents(rest)
            elif word == "reviewer" and rest:
                found = re.match(r"^(.+?)(?:\s+at\s+(\S+))?$", rest)
                who, depth = (found.group(1), found.group(2)) if found else (rest, None)
                if depth is not None and depth not in DEPTHS:
                    self.bad(number, "the review depth is glance, delta or standard.")
                    continue
                head.reviewer = ("none", None) if who == "none" else parse_agent(who)
                head.depth = depth
            elif word == "planner" and rest:
                head.planner = rest
            elif word == "budget":
                tokens = parse_tokens(rest)
                if tokens is None:
                    self.bad(number, "the budget is a number of tokens ('budget 64k').")
                else:
                    head.budget = tokens
            elif part == "rounds before start":
                head.rounds_before_start = True
            elif word == "night":
                night = parse_night(rest)
                if night is None:
                    self.bad(number, "the night is '23:30–07:00 · at most 8 steps'.")
                else:
                    head.night = night
            elif word == "within" and rest:
                head.within = [item.strip() for item in rest.split(",") if item.strip()]
            elif word == "delivery":
                if not rest.startswith("dw ") or not rest[3:].strip():
                    self.bad(number, "delivery is 'delivery dw <project>/<phase>[/<story>]'.")
                else:
                    head.delivery = rest[3:].strip()
            elif part == "when idle":
                head.when_idle = True
            elif part == "may call":
                head.may_call = True
            elif part == "may hand off":
                head.may_hand_off = True
            elif word == "allow" and rest:
                head.allow = [agent[0] for agent in parse_agents(rest)]
            elif part.startswith("spend up to $"):
                try:
                    head.spend = float(part[len("spend up to $"):])
                except ValueError:
                    self.bad(number, "the spend limit is a number of dollars ('spend up to $5').")
            elif part.startswith("usage warning ") and part.endswith("%"):
                try:
                    head.usage_warning = float(part[len("usage warning "):-1]) / 100.0
                except ValueError:
                    self.bad(number, "the usage warning is a share ('usage warning 90%').")
            elif word == "for" and rest:
                head.for_person = rest
            elif word == "from" and rest:
                head.origin = rest
            elif word == "template" and rest:
                head.template = "-".join(rest.lower().split())
            elif any(part == later or part.startswith(later + " ") for later in _LATER_PROGRAM):
                self.later(number, next(later for later in _LATER_PROGRAM if part == later or part.startswith(later + " ")))
            else:
                self.unknown(number, word)

    def step_line(self, number: int, body: str) -> None:
        step = self.step
        assert step is not None
        if body.startswith("+ "):
            step.amendments.append(Amendment(" ".join(body[2:].split()), line=number))
            return
        if re.match(r"^R(\d+|\+)(\s|$)", body):
            row = self.requirement(number, body)
            if row is not None:
                step.requirements.append(row)
            return
        if body.startswith("merged #"):
            pieces = [piece.strip() for piece in body.split(" · ")]
            try:
                merged: dict[str, Any] = {"pr_number": int(pieces[0][len("merged #"):]), "merged_at": None,
                                          "pr_url": None, "head_commit": None}
            except ValueError:
                self.bad(number, "a merged step is 'merged #<PR> · <time>'.")
                return
            for piece in pieces[1:]:
                key = "pr_url" if piece.startswith("http") else "head_commit" if _HEX.match(piece) else "merged_at"
                merged[key] = piece
            step.merged = merged
            return
        self.req = None
        for part in [piece.strip() for piece in body.split(" · ")]:
            word, _sep, rest = part.partition(" ")
            rest = rest.strip()
            if part == "brief":
                self.quote, self.quote_lines = "brief", []
            elif word == "owns" and rest:
                step.owns = [item.strip() for item in rest.split(",") if item.strip()]
            elif word == "after":
                values = _numbers(rest)
                if values is None:
                    self.bad(number, "after names step numbers ('after 1, 2').")
                else:
                    step.after = values
            elif word == "agent" and rest:
                step.agents = parse_agents(rest)
            elif word == "effort":
                if rest not in EFFORTS:
                    self.bad(number, "effort is low, medium or high.")
                else:
                    step.effort = rest
            elif word == "race":
                if rest not in ("0", "2", "3"):
                    self.bad(number, "a race has 2 or 3 agents.")
                else:
                    step.race = int(rest)
            elif part == "when idle":
                step.when_idle = True
            elif part == "may call":
                step.may_call = True
            elif part in ("check off", "check on"):
                step.check = part == "check on"
            elif word == "review":
                found = re.match(r"^(.+?)(?: at (glance|delta|standard))?$", rest)
                if not found:
                    self.bad(number, "review is none, agent or a person, and at glance, delta or standard.")
                elif found.group(1) in REVIEWS:
                    step.review = found.group(1)
                    step.depth = found.group(2)
                else:
                    # ``review Alice``: a person reviews the PR (the step's person).
                    step.review, step.depth, step.for_person = "person", found.group(2), found.group(1).strip()
            elif word == "merge":
                if rest not in MERGES:
                    self.bad(number, "merge is level, owner or none.")
                else:
                    step.merge = rest
            elif word == "for" and rest:
                step.for_person = rest
            elif word == "from" and rest:
                step.origin = rest
            elif word == "budget":
                tokens = parse_tokens(rest)
                if tokens is None:
                    self.bad(number, "the budget is a number of tokens ('budget 32k').")
                else:
                    step.budget = tokens
            elif word in _LATER_STEP:
                self.later(number, word)
            else:
                self.unknown(number, word)


def parse_program_text(text: str) -> ProgramText:
    """Read a Program text. A line it cannot read is a :class:`TextError`
    on ``errors`` (a refusal by name); the rest is read."""
    model = _Reader(text).read()
    return canonical(model)


def canonical(model: ProgramText) -> ProgramText:
    """``model`` with every value that equals its default set to ``None``
    (what the printer would write for it)."""
    out = replace(model, head=replace(model.head), steps=[replace(step) for step in model.steps])
    head = out.head
    if head.agents is not None and head.agents == template_agents(head.template):
        head.agents = None
    if head.reviewer is not None and head.reviewer == template_reviewer(head.template):
        head.reviewer = None
    if head.depth is not None and head.depth == template_depth(head.template):
        head.depth = None
    for step in out.steps:
        if step.agents:
            step.agents = _minimal_agents(step_agents(head, step), program_agents(head))
        if step.effort is not None and step.effort == triage(step.brief, step.owns):
            step.effort = None
        for name in ("race", "check", "review", "depth", "merge"):
            value = getattr(step, name)
            if value is not None and step_value(head, replace(step, **{name: None}), name) == value:
                setattr(step, name, None)
    return out


# ── the diff (§3.8) ──────────────────────────────────────────────────

@dataclass
class Change:
    """One change row (§3.8). ``data`` is what the service applies; it is
    not on the wire."""

    id: str
    op: str                 # add | change | remove | move | amend | read
    where: str              # program | every step | at the end | step 5 | R6 | line 7
    field: str
    before: str = ""
    after: str = ""
    say: str = ""
    verdict: str = "allowed"    # allowed | refused | conflict | lowers
    reason: Optional[str] = None
    code: Optional[str] = None
    line: int = 0
    lowers_bar: bool = False
    data: dict[str, Any] = field(default_factory=dict, compare=False, repr=False)

    def refuse(self, code: str, reason: str) -> "Change":
        self.verdict, self.code, self.reason = "refused", code, reason
        return self

    def to_wire(self) -> dict[str, Any]:
        return {item.name: getattr(self, item.name) for item in dc_fields(self) if item.name != "data"}


#: The text's step field -> the frozen table's name (``step_fields``).
STEP_FIELD_NAMES = {
    "title": "title", "brief": "brief", "owns": "owns", "after": "after", "effort": "effort", "agents": "agent",
    "race": "race", "check": "gate_check", "review": "gate_review", "depth": "review_depth", "merge": "gate_merge",
    "for_person": "for_person", "may_call": "may_call", "when_idle": "prefer_idle", "budget": "budget",
}
#: The words the board's hover title adds to a frozen field's reason (§3.5).
_FROZEN_HINT = {"brief": "Add a line with + instead.", "agents": "Hand off instead."}
#: Step fields set only when the step is added (no service verb changes
#: them), and why.
_STEP_FIXED = {"origin": "it names what the step closes; add a step for another one",
               "merged": "it is the record of a merged PR"}
#: Program fields set only when the Program is made, and why.
_HEAD_FIXED = {"repository": "a program works in one repository; make a new program for another",
               "branch": "the steps branch from it and merge to it; make a new program for another",
               "origin": "it names what the program came from",
               "template": "a template shapes a program when it is made; change the fields it set instead"}
#: The Program fields ``ProgramService.update`` takes, in print order.
_HEAD_FIELDS = ("title", "goal", "repository", "branch", "project", "template", "control", "check", "agents",
                "planner", "reviewer", "depth", "budget", "when_idle", "may_call", "may_hand_off",
                "rounds_before_start", "night", "within", "allow", "spend", "usage_warning", "delivery",
                "for_person", "origin")
#: A Program field's words in a change row.
_HEAD_WORDS = {"depth": "review depth", "for_person": "for", "origin": "from", "allow": "allowed agents",
               "agents": "agent", "delivery": "delivery dw"}
#: Step fields whose unstated value follows the Program (a change of the
#: Program's line changes them too).
_FOLLOWS_HEAD = ("review", "depth", "when_idle", "may_call")


def _words(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, dict) and "line" in value:
        return str(value["line"])
    if isinstance(value, int) and not isinstance(value, bool) and value >= 1024:
        return tokens_words(value)
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list):
        if value and isinstance(value[0], tuple):
            return agents_words(value)
        return ", ".join(str(item) for item in value) or "none"
    if isinstance(value, tuple):
        return "none" if value[0] == "none" else agent_words(value)
    if isinstance(value, float):
        return _number(value)
    text = str(value)
    return (text[:57] + "…") if len(text) > 60 else text


def head_value(head: Head, name: str) -> Any:
    if name == "agents":
        return program_agents(head)
    if name == "reviewer":
        return program_reviewer(head)
    if name == "depth":
        return program_depth(head)
    return getattr(head, name)


def _lowers_head(name: str, before: Any, after: Any) -> bool:
    if name == "control":
        return _CONTROL_RANK.get(str(after), 0) > _CONTROL_RANK.get(str(before), 0)
    if name == "spend":
        return after is not None and (before is None or float(after) > float(before))
    if name == "depth":
        return _DEPTH_RANK.get(str(after), 1) < _DEPTH_RANK.get(str(before), 1)
    if name == "reviewer":
        return before[0] != "none" and after[0] == "none"
    if name == "check":
        return bool(before) and after == ""
    if name == "rounds_before_start":
        return bool(before) and not bool(after)
    if name == "within":
        # §4.5: a removed ``within`` line, or a list without a path it had.
        return bool(before) and (not after or any(path not in after for path in before))
    return False


def _lowers_step(name: str, before: Any, after: Any) -> bool:
    if name == "check":
        return bool(before) and not bool(after)
    if name == "review":
        return before in ("agent", "person") and after == "none"
    if name == "depth":
        return _DEPTH_RANK.get(str(after), 1) < _DEPTH_RANK.get(str(before), 1)
    if name == "merge":
        return before == "owner" and after in ("level", "none")
    return False


def _lowers_requirement(before: Requirement, after: Requirement) -> bool:
    if before.required and not after.required:
        return True
    if before.kind != "measure" and after.kind == "measure":
        return True  # a Measure does not gate until its verifier (LANG11)
    return before.kind in _STRONG_KINDS and after.kind == "review"


def _req_words(row: Requirement) -> str:
    rid = "R+" if row.rid is None else f"R{row.rid}"
    return f"{rid} {row.kind}{' optional' if not row.required else ''}: {row.text}"


def _as_model(value: Any) -> ProgramText:
    return value if isinstance(value, ProgramText) else parse_program_text(str(value or ""))


def _record_steps(record: Optional[Mapping[str, Any]]) -> dict[int, Mapping[str, Any]]:
    return {int(step["ordinal"]): step for step in (record or {}).get("steps") or [] if not step.get("race_of")}


def _frozen(record_step: Optional[Mapping[str, Any]], name: str) -> Optional[str]:
    if not record_step:
        return None
    frozen = record_step.get("frozen") or {}
    key = STEP_FIELD_NAMES.get(name, name)
    return frozen.get(key)


def _started(record_step: Optional[Mapping[str, Any]]) -> bool:
    return bool(record_step) and str(record_step.get("state") or "planned") not in ("planned", "ready")


def _weighted_lis(order: list[str], rank: Mapping[str, int], weight: Mapping[str, int]) -> set[str]:
    """The heaviest subsequence of ``order`` whose ranks increase: the steps
    that keep their place (a started step weighs most)."""
    best: list[int] = []
    prev: list[int] = []
    for index, item in enumerate(order):
        best.append(weight[item])
        prev.append(-1)
        for earlier in range(index):
            if rank[order[earlier]] < rank[item] and best[earlier] + weight[item] > best[index]:
                best[index], prev[index] = best[earlier] + weight[item], earlier
    if not order:
        return set()
    at = max(range(len(order)), key=lambda i: best[i])
    keep: set[str] = set()
    while at >= 0:
        keep.add(order[at])
        at = prev[at]
    return keep


def diff_program_text(current: Any, proposed: Any, *, record: Optional[Mapping[str, Any]] = None) -> list[Change]:
    """The change rows from ``current`` to ``proposed`` (texts or models),
    in reading order. With ``record`` (the Program as ``ProgramService.get``
    answers it) each row has its verdict by the frozen table; without it
    every readable change is allowed."""
    base, new = _as_model(current), _as_model(proposed)
    rows: list[Change] = []
    closed = bool((record or {}).get("closed_at"))
    for error in new.errors:
        rows.append(Change(id=f"line-{error.line}", op="read", where=f"line {error.line}", field="line",
                           line=error.line, verdict="refused", code=error.code, reason=error.words))

    # the Program --------------------------------------------------------
    for name in _HEAD_FIELDS:
        before, after = head_value(base.head, name), head_value(new.head, name)
        if name == "check" and after is None:
            continue
        if before == after:
            continue
        words = _HEAD_WORDS.get(name, name.replace("_", " "))
        row = Change(id=f"program.{name.replace('_', '-')}", op="change", where="program", field=words,
                     before=_words(before), after=_words(after), line=new.head.line,
                     say=f"The program's {words} is now {_words(after)}.",
                     data={"kind": "head", "name": name, "value": after})
        row.lowers_bar = _lowers_head(name, before, after)
        if name in _HEAD_FIXED:
            row.refuse("field_fixed", f"Program · {words}: it is set when the program is made; {_HEAD_FIXED[name]}.")
        elif name == "title" and not after:
            row.refuse("text_bad_value", "A program needs a title.")
        elif closed:
            row.refuse("program_closed", "The program is closed.")
        rows.append(row)

    # the steps: identity, new ones, order ------------------------------
    by_record = _record_steps(record)
    base_numbers = [step.number for step in base.steps if step.number is not None]
    top = max(base_numbers, default=0)
    provisional: dict[int, Step] = {}
    label: dict[int, int] = {}          # id(step) -> its number in the text (new: max + k)
    for step in base.steps:
        if step.number is not None:
            label[id(step)] = step.number
    counter = top
    for step in new.steps:
        if step.number is None:
            counter += 1
            provisional[counter] = step
            label[id(step)] = counter
        else:
            label[id(step)] = step.number
    base_by = {step.number: step for step in base.steps if step.number is not None}
    new_by = {step.number: step for step in new.steps if step.number is not None}

    for number, step in base_by.items():
        if number in new_by:
            continue
        row = Change(id=f"step-{number}.remove", op="remove", where=f"step {number}", field="step",
                     before=step.title, line=step.line, say=f"Step {number}, {step.title}, is removed.",
                     data={"kind": "remove_step", "number": number})
        if _started(by_record.get(number)):
            row.refuse("step_stays", f"Step {number} started. It stays.")
        elif step.merged:
            row.refuse("step_stays", f"Step {number} is a merged PR. It stays.")
        elif closed:
            row.refuse("program_closed", "The program is closed.")
        rows.append(row)
    for number, step in new_by.items():
        if number not in base_by:
            rows.append(Change(id=f"step-{number}.unknown", op="read", where=f"step {number}", field="step",
                               line=step.line).refuse(
                "text_bad_value", f"Line {step.line}: there is no step {number}. Write 'step +' for a new step."))

    # ``after`` and order compare by identity (the step it points to). A
    # step removed in this text is no step for the new text's ``after``.
    def ident(number: int, *, base_side: bool = False) -> Optional[str]:
        if number in base_by and (base_side or number in new_by):
            return f"s{number}"
        if number in provisional and not base_side:
            return f"n{number}"
        return None

    for step in new.steps:
        number = label[id(step)]
        gone = [value for value in step.after if value in base_by and value not in new_by]
        missing = [value for value in step.after if (ident(value) is None or value == number) and value not in gone]
        if gone:
            rows.append(Change(id=f"step-{number}.after-removed", op="read", where=f"step {number}", field="after",
                               line=step.line).refuse(
                "text_bad_value", f"Step {number} · after: step {', '.join(map(str, gone))} is removed in this text."))
        if missing:
            rows.append(Change(id=f"step-{number}.after-unknown", op="read", where=f"step {number}", field="after",
                               line=step.line).refuse(
                "text_bad_value", f"Step {number} · after: there is no step {', '.join(map(str, missing))} before it."))

    order = [f"s{step.number}" if step.number is not None else f"n{label[id(step)]}" for step in new.steps
             if step.number is None or step.number in base_by]
    position = {key: index for index, key in enumerate(order)}
    for step in new.steps:
        number = label[id(step)]
        key = f"s{number}" if step.number is not None else f"n{number}"
        if key not in position:
            continue
        late = [value for value in step.after if ident(value) in position and position[ident(value)] > position[key]]
        if late:
            rows.append(Change(id=f"step-{number}.order", op="move", where=f"step {number}", field="position",
                               line=step.line).refuse(
                "order_invalid", f"Step {number} comes after step {late[0]}: it cannot move above it."))
    start = [f"s{n}" for n in base_numbers if n in new_by] + [f"n{n}" for n in provisional]
    rank = {key: index for index, key in enumerate(order)}
    # A started step weighs most (it keeps its place); a new step least (the
    # row says "step 7 before step 6", not "step 6 to the end").
    weight = {key: (1000 if key.startswith("s") and _started(by_record.get(int(key[1:]))) else
                    2 if key.startswith("s") else 1) for key in start}
    keep = _weighted_lis(start, rank, weight)
    for index, key in enumerate(order):
        if key in keep:
            continue
        number = int(key[1:])
        succ = order[index + 1] if index + 1 < len(order) else None
        succ_number = int(succ[1:]) if succ else None
        step = base_by.get(number) or provisional.get(number)
        line = (new_by.get(number) or provisional.get(number) or step).line if step else 0
        row = Change(id=f"step-{number}.move", op="move", where=f"step {number}", field="position",
                     before=f"step {number}", after=f"before step {succ_number}" if succ else "at the end", line=line,
                     say=f"Step {number} moves {'before step ' + str(succ_number) if succ else 'to the end'}.",
                     data={"kind": "move", "key": key, "before": succ})
        record_step = by_record.get(number) if key.startswith("s") else None
        if record_step is not None and _started(record_step):
            row.refuse("step_frozen", f"Step {number} started; it keeps its place.")
        elif key.startswith("n") and succ and succ.startswith("s") and _started(by_record.get(int(succ[1:]))):
            row.refuse("step_frozen", f"Step {int(succ[1:])} started. Add the step after it.")
        elif closed:
            row.refuse("program_closed", "The program is closed.")
        rows.append(row)

    # new steps ---------------------------------------------------------
    for number, step in provisional.items():
        parts = [step.title] + ([f"after {', '.join(map(str, step.after))}"] if step.after else [])
        if step.agents:
            parts.append(agents_words(step_agents(new.head, step)))
        parts.append(step_value(new.head, step, "effort"))
        row = Change(id=f"step-{number}.add", op="add", where=f"step {number}", field="step", after=" · ".join(parts),
                     line=step.line, say=f"A new step {number}, {step.title}.",
                     data={"kind": "add_step", "key": f"n{number}", "step": step})
        if not step.title:
            row.refuse("text_bad_value", f"Line {step.line}: a step needs a title.")
        elif step.amendments:
            row.refuse("step_not_started", f"Step {number} has not started: write its brief, not a '+' line.")
        elif step_value(new.head, step, "review") == "person" and not (step.for_person or new.head.for_person):
            row.refuse("person_required", f"Step {number}: a person review names the person ('for <name>').")
        elif closed:
            row.refuse("program_closed", "The program is closed.")
        rows.append(row)

    # existing steps: their fields --------------------------------------
    for number, step in new_by.items():
        old = base_by.get(number)
        if old is None:
            continue
        record_step = by_record.get(number)
        started = _started(record_step)
        for name in ("title", "brief", "owns", "after", "agents", "effort", "race", "check", "review", "depth",
                     "merge", "for_person", "may_call", "when_idle", "budget", "origin", "merged"):
            if name == "after":
                before = sorted(filter(None, (ident(value, base_side=True) for value in old.after)))
                after = sorted(filter(None, (ident(value) for value in step.after)))
                shown = (", ".join(map(str, old.after)) or "none", ", ".join(map(str, step.after)) or "none")
            elif name in ("may_call", "when_idle"):
                before = getattr(old, name) or getattr(base.head, name)
                after = getattr(step, name) or getattr(new.head, name)
                shown = (_words(before), _words(after))
            elif name == "budget":
                # None: the Program's budget; never resolved, so a Program
                # line does not rewrite each step.
                before, after = old.budget, step.budget
                shown = (_words(before) if before else "the program's", _words(after) if after else "the program's")
            else:
                before, after = step_value(base.head, old, name), step_value(new.head, step, name)
                shown = (_words(before), _words(after))
            if before == after:
                continue
            follows = name in _FOLLOWS_HEAD and not getattr(old, name) and not getattr(step, name)
            if follows and (_frozen(record_step, name) or (started and name == "review" and after != "agent")):
                # The Program's line changed and this step took the old value
                # from it; its state keeps that value (the text then states it).
                continue
            row = Change(id=f"step-{number}.{name.replace('_', '-')}", op="change", where=f"step {number}",
                         field={"agents": "agent", "for_person": "for", "may_call": "may call",
                                "when_idle": "when idle", "depth": "review depth"}.get(name, name),
                         before=shown[0], after=shown[1], line=step.line,
                         say=f"Step {number}'s {name.replace('_', ' ')} is now {shown[1]}.",
                         data={"kind": "step", "number": number, "name": name, "value": after,
                               "agents": step_agents(new.head, step) if name == "agents" else None})
            if name in ("check", "review", "depth", "merge"):
                row.lowers_bar = _lowers_step(name, before, after)
            reason = _frozen(record_step, name)
            if name == "agents" and started and record_step is not None:
                # Started: the first agent is set; only the agents after it change.
                first_before, first_after = (before[0] if before else None), (after[0] if after else None)
                reason = (record_step.get("frozen") or {}).get("agent") if first_before != first_after else (
                    (record_step.get("frozen") or {}).get("runs_on_then"))
            if name in _STEP_FIXED:
                row.refuse("field_fixed", f"Step {number} · {row.field}: it is set when the step is added; "
                                          f"{_STEP_FIXED[name]}.")
            elif reason:
                hint = f" {_FROZEN_HINT[name]}" if name in _FROZEN_HINT and reason != "It is merged" else ""
                row.refuse("step_frozen", f"Step {number} · {row.field}: {reason}.{hint}")
                row.data["reason"] = reason
            elif started and name == "review" and after != "agent":
                row.refuse("step_frozen", f"Step {number} · review: The bar does not come down while it runs.")
            elif started and name == "merge" and after == "none":
                row.refuse("step_frozen", f"Step {number} · merge: The worktree and the agent are set.")
            elif name == "title" and not after:
                row.refuse("text_bad_value", f"Line {step.line}: a step needs a title.")
            elif name == "review" and after == "person" and not (step.for_person or new.head.for_person):
                row.refuse("person_required", f"Step {number}: a person review names the person ('for <name>').")
            elif closed:
                row.refuse("program_closed", "The program is closed.")
            rows.append(row)
        # amendments: the sent ones stay; new lines are added.
        kept = [item.text for item in step.amendments[:len(old.amendments)]]
        if kept != [item.text for item in old.amendments]:
            sent = next((item for item in (record_step or {}).get("amendments") or [] if item.get("sent_at")), None)
            rows.append(Change(id=f"step-{number}.amend-stays", op="remove", where=f"step {number}", field="amend",
                               line=step.line).refuse(
                "amendment_stays", f"Step {number}: a '+' line stays. It was sent at {_clock(sent['sent_at'])}."
                if sent else f"Step {number}: a '+' line stays. It waits for a turn end."))
        for index, item in enumerate(step.amendments[len(old.amendments):], start=len(old.amendments) + 1):
            row = Change(id=f"step-{number}.amend-{index}", op="amend", where=f"step {number}", field="amend",
                         after=f"+ {item.text}", line=item.line, say=f"Step {number} gets one more line: {item.text}",
                         data={"kind": "amend", "number": number, "line": item.text})
            reason = _frozen(record_step, "amend")
            if record_step is not None and not started:
                row.refuse("step_not_started", f"Step {number} has not started: change its brief.")
            elif reason:
                row.refuse("step_frozen", f"Step {number} · amend: {reason}. Send it back with a line instead.")
            elif closed:
                row.refuse("program_closed", "The program is closed.")
            rows.append(row)

    # requirements --------------------------------------------------------
    def scope_key(where: str, owner: Optional[Step]) -> str:
        if owner is not None and owner.number is None:
            return f"step {label[id(owner)]}"
        return where

    old_reqs = {row.rid: (where, row) for where, row in base.requirements() if row.rid is not None}
    owners = {id(row): step for step in new.steps for row in step.requirements}
    seen: set[int] = set()
    for where, row in new.requirements():
        owner = owners.get(id(row))
        scope = scope_key(where, owner)
        number = label[id(owner)] if owner is not None else None
        record_step = by_record.get(number) if owner is not None and owner.number is not None else None
        if row.rid is None:
            change = Change(id=f"R+{row.line}", op="add", where=scope, field="requirement", after=_req_words(row),
                            line=row.line, say=f"A new requirement on {scope}: {row.text}",
                            data={"kind": "require", "scope": scope, "key": (f"n{number}" if owner is not None and
                                                                             owner.number is None else
                                                                             f"s{number}" if owner is not None else None),
                                  "row": row})
            reason = _frozen(record_step, "requirements")
            if reason:
                change.refuse("step_frozen", f"Step {number}: {reason}. Add it to the program instead.")
            elif row.waived is not None:
                change.refuse("text_bad_value", "A new requirement is not waived.")
            elif closed:
                change.refuse("program_closed", "The program is closed.")
            rows.append(change)
            continue
        seen.add(row.rid)
        found = old_reqs.get(row.rid)
        if found is None:
            rows.append(Change(id=f"R{row.rid}.unknown", op="read", where=f"R{row.rid}", field="requirement",
                               line=row.line).refuse(
                "text_bad_value", f"Line {row.line}: there is no R{row.rid}. Write R+ for a new requirement."))
            continue
        old_where, old = found
        if old_where != scope:
            rows.append(Change(id=f"R{row.rid}.scope", op="move", where=f"R{row.rid}", field="scope",
                               before=old_where, after=scope, line=row.line).refuse(
                "requirement_stays", f"R{row.rid} stays on {old_where}."))
            continue
        reason = _frozen(record_step, "requirements")
        if (old.kind, old.text, old.required, old.spec) != (row.kind, row.text, row.required, row.spec):
            change = Change(id=f"R{row.rid}.requirement", op="change", where=f"R{row.rid}", field="requirement",
                            before=_req_words(old), after=_req_words(row), line=row.line,
                            say=f"R{row.rid} now says: {row.text}",
                            data={"kind": "edit_requirement", "rid": row.rid, "row": row, "old": old})
            change.lowers_bar = _lowers_requirement(old, row)
            if old.waived is not None:
                change.refuse("requirement_waived", f"R{row.rid} is waived.")
            elif reason:
                change.refuse("step_frozen", f"Step {number}: {reason}.")
            elif closed:
                change.refuse("program_closed", "The program is closed.")
            rows.append(change)
        if old.waived != row.waived:
            change = Change(id=f"R{row.rid}.waive", op="change", where=f"R{row.rid}", field="waived",
                            before=old.waived or "", after=row.waived or "", line=row.line, lowers_bar=True,
                            say=f"R{row.rid} is waived: {row.waived}",
                            data={"kind": "waive", "rid": row.rid, "line": row.waived})
            if old.waived is not None:
                change.lowers_bar = False
                change.refuse("requirement_waived", f"R{row.rid} is waived. Its line stays.")
            elif not row.waived:
                change.refuse("line_required", f"R{row.rid}: say in one line why you waive it.")
            elif reason:
                change.refuse("step_frozen", f"Step {number}: {reason}.")
            elif closed:
                change.refuse("program_closed", "The program is closed.")
            rows.append(change)
    removed = {f"step {number}" for number in base_by if number not in new_by}
    for rid, (where, old) in old_reqs.items():
        if rid not in seen and where in removed:
            continue  # it goes with its step's block (the step's row says whether it may)
        if rid not in seen:
            rows.append(Change(id=f"R{rid}.remove", op="remove", where=f"R{rid}", field="requirement",
                               before=_req_words(old), line=old.line).refuse(
                "requirement_stays", f"R{rid} stays. Waive it with a line."))

    # rounds (§6.2): his answers and the rounds' states; the questions are
    # the engine's ---------------------------------------------------------
    rows += _round_rows(base, new, closed)

    for row in rows:
        if row.verdict == "allowed" and row.lowers_bar:
            row.verdict = "lowers"
    # Reading order; on one line a new step comes before its move.
    rows.sort(key=lambda row: (row.line or 0, 0 if row.op == "add" else 1))
    return rows


def _round_key(name: str) -> str:
    return _fold(name)


def _round_rows(base: ProgramText, new: ProgramText, closed: bool) -> list[Change]:
    rows: list[Change] = []
    old_by = {_round_key(item.name): item for item in base.rounds}
    new_by = {_round_key(item.name): item for item in new.rounds}
    seen: set[str] = set()
    for item in new.rounds:
        key = _round_key(item.name)
        where = f"round {item.name}"
        if key in seen:
            rows.append(Change(id=f"round-{key}.twice", op="read", where=where, field="round", line=item.line).refuse(
                "text_bad_value", f"Line {item.line}: round {item.name} is in the text twice."))
            continue
        seen.add(key)
        old = old_by.get(key)
        if old is None:
            row = Change(id=f"round-{key}.add", op="add", where=where, field="round", after=f"{item.name} · {item.state}",
                         line=item.line, say=f"A new round, {item.name}.", data={"kind": "round", "name": item.name})
            if item.questions:
                row.refuse("round_question", f"Round {item.name}: the engine asks the questions. Add the round with "
                                             "no '?' lines.")
            elif item.state == "asking":
                row.refuse("round_state", f"Round {item.name}: the engine sets asking. Write open.")
            elif closed:
                row.refuse("program_closed", "The program is closed.")
            rows.append(row)
            continue
        if item.state != old.state:
            row = Change(id=f"round-{key}.state", op="change", where=where, field="state", before=old.state,
                         after=item.state, line=item.line, say=f"Round {item.name} is now {item.state}.",
                         data={"kind": "round", "name": item.name})
            if item.state == "asking":
                row.refuse("round_state", f"Round {item.name}: the engine sets asking. Write open.")
            elif closed:
                row.refuse("program_closed", "The program is closed.")
            rows.append(row)
        if [question.text for question in item.questions] != [question.text for question in old.questions]:
            rows.append(Change(id=f"round-{key}.questions", op="change", where=where, field="question",
                               line=item.line, data={"kind": "round", "name": item.name}).refuse(
                "round_question", f"Round {item.name}: the engine asked it. A '?' line stays as it is."))
            continue
        for index, (question, before) in enumerate(zip(item.questions, old.questions), start=1):
            if question.answer == before.answer:
                continue
            row = Change(id=f"round-{key}.answer-{index}", op="change", where=where, field="answer",
                         before=before.answer or "", after=question.answer or "", line=item.line,
                         say=f"Round {item.name}: the answer to '{question.text}' is now {question.answer or 'none'}.",
                         data={"kind": "round", "name": item.name})
            if old.state == "done":
                row.refuse("round_done", f"Round {item.name} is done. Open it again to change an answer.")
            elif closed:
                row.refuse("program_closed", "The program is closed.")
            rows.append(row)
    for key, old in old_by.items():
        if key in new_by:
            continue
        row = Change(id=f"round-{key}.remove", op="remove", where=f"round {old.name}", field="round", before=old.name,
                     line=old.line, say=f"Round {old.name} is removed.", data={"kind": "round", "name": old.name})
        if old.questions:
            row.refuse("round_stays", f"Round {old.name} has questions. It stays; write 'round {old.name} · skipped'.")
        elif closed:
            row.refuse("program_closed", "The program is closed.")
        rows.append(row)
    common = [_round_key(item.name) for item in new.rounds if _round_key(item.name) in old_by]
    if common != [key for key in (_round_key(item.name) for item in base.rounds) if key in new_by]:
        rows.append(Change(id="rounds.order", op="move", where="rounds", field="order",
                           before=", ".join(item.name for item in base.rounds),
                           after=", ".join(item.name for item in new.rounds), say="The rounds are in a new order.",
                           line=next((item.line for item in new.rounds), 0), data={"kind": "round_order"}))
    return rows


def patch(current: str, proposed: str) -> str:
    """The unified line diff of two texts (for agents and the Text view's
    gutter)."""
    return "".join(difflib.unified_diff(str(current).splitlines(keepends=True), str(proposed).splitlines(keepends=True),
                                        fromfile="current", tofile="proposed"))


def allowed_model(base: ProgramText, proposed: ProgramText, rows: list[Change],
                  allow: Iterable[str] = ()) -> ProgramText:
    """``proposed`` with every refused or conflicting change put back as it
    is in ``base`` (§3.6): one more apply of its text is "Apply the rest".
    A row that lowers the bar stays in the text unless ``allow`` is given
    and omits it; it applies only with its own id in ``allow_lower``."""
    allow = set(allow)
    blocked = [row for row in rows if row.verdict in ("refused", "conflict") or
               (allow and row.verdict == "lowers" and row.id not in allow)]
    out = replace(proposed, head=replace(proposed.head), steps=[replace(step) for step in proposed.steps],
                  every_step=list(proposed.every_step), at_end=list(proposed.at_end), errors=[],
                  rounds=[replace(item, questions=[replace(question) for question in item.questions])
                          for item in proposed.rounds])
    base_by = {step.number: step for step in base.steps if step.number is not None}
    base_reqs = {row.rid: (where, row) for where, row in base.requirements() if row.rid is not None}
    for row in blocked:
        kind = row.data.get("kind")
        if kind == "head":
            setattr(out.head, row.data["name"], getattr(base.head, row.data["name"]))
        elif kind == "step":
            step = next((item for item in out.steps if item.number == row.data["number"]), None)
            if step is not None and row.data["number"] in base_by:
                name, was = row.data["name"], base_by[row.data["number"]]
                value = getattr(was, name)
                if value in (None, False) and name in _FOLLOWS_HEAD:
                    # It followed the Program's line in the base: state it.
                    value = step_value(base.head, was, name) if name in ("review", "depth") else (
                        getattr(was, name) or getattr(base.head, name))
                setattr(step, name, value)
        elif kind == "add_step":
            out.steps = [item for item in out.steps if item is not row.data["step"]]
        elif kind == "amend":
            step = next((item for item in out.steps if item.number == row.data["number"]), None)
            if step is not None:
                step.amendments = [item for item in step.amendments if item.text != row.data["line"]]
        elif kind == "move":
            out.steps = _base_order(base, out.steps)
        elif kind == "round":
            key = _round_key(row.data["name"])
            was = next((item for item in base.rounds if _round_key(item.name) == key), None)
            at = next((index for index, item in enumerate(out.rounds) if _round_key(item.name) == key), None)
            if was is None and at is not None:
                out.rounds.pop(at)
            elif was is not None and at is not None:
                out.rounds[at] = replace(was, questions=[replace(question) for question in was.questions])
            elif was is not None:
                out.rounds.append(replace(was, questions=[replace(question) for question in was.questions]))
        elif kind == "round_order":
            rank = {_round_key(item.name): index for index, item in enumerate(base.rounds)}
            out.rounds.sort(key=lambda item: rank.get(_round_key(item.name), len(rank)))
        elif kind in ("edit_requirement", "waive"):
            _swap_requirement(out, row.data["rid"], base_reqs[row.data["rid"]][1])
        elif kind == "require":
            _drop_requirement(out, row.data["row"])
        elif row.op == "remove" and row.field == "step":
            number = int(row.where.split(" ")[1])
            if number in base_by and all(item.number != number for item in out.steps):
                out.steps.append(replace(base_by[number]))
                out.steps = _base_order(base, out.steps)
        elif row.op == "remove" and row.field == "requirement":
            rid = int(row.where[1:])
            where, old = base_reqs[rid]
            _restore_requirement(out, where, old)
        elif row.field == "amend" and row.op == "remove":
            number = int(row.where.split(" ")[1])
            step = next((item for item in out.steps if item.number == number), None)
            if step is not None and number in base_by:
                extra = step.amendments[len(base_by[number].amendments):]
                step.amendments = list(base_by[number].amendments) + extra
        elif row.op == "read" and row.field == "requirement" and row.id.endswith(".unknown"):
            # LANG5: "R4" for a requirement the base has no R4 for (a real
            # engine's slip for "R+"): put back is the line left out.
            rid = int(row.where[1:])
            for held in [out.every_step, out.at_end] + [step.requirements for step in out.steps]:
                held[:] = [item for item in held if not (item.rid == rid and item.line == row.line)]
        elif row.op == "read" and row.field in ("step", "requirement", "after", "line"):
            continue
    return out


def _base_order(base: ProgramText, steps: list[Step]) -> list[Step]:
    """Existing steps in their base order; each new step after the step it
    followed in the proposed text."""
    rank = {step.number: index for index, step in enumerate(base.steps)}
    existing = sorted((step for step in steps if step.number is not None), key=lambda step: rank.get(step.number, 1 << 30))
    out = list(existing)
    previous: Optional[Step] = None
    for step in steps:
        if step.number is None:
            at = out.index(previous) + 1 if previous is not None and previous in out else 0
            out.insert(at, step)
        previous = step
    return out


def _swap_requirement(model: ProgramText, rid: int, old: Requirement) -> None:
    for rows in [model.every_step, model.at_end] + [step.requirements for step in model.steps]:
        for index, row in enumerate(rows):
            if row.rid == rid:
                rows[index] = replace(old)
                return


def _drop_requirement(model: ProgramText, target: Requirement) -> None:
    for rows in [model.every_step, model.at_end] + [step.requirements for step in model.steps]:
        if any(row is target for row in rows):
            rows[:] = [row for row in rows if row is not target]
            return


def _restore_requirement(model: ProgramText, where: str, old: Requirement) -> None:
    if where == "every step":
        model.every_step.append(replace(old))
    elif where == "at the end":
        model.at_end.append(replace(old))
    else:
        number = int(where.split(" ")[1])
        step = next((item for item in model.steps if item.number == number), None)
        if step is not None:
            step.requirements.append(replace(old))


__all__ = [
    "AGENT_WORDS", "Amendment", "Change", "Head", "ProgramText", "Question", "Requirement", "Round", "Step",
    "TextError", "VERSION", "VERSION_LINE", "agent_words", "agents_words", "allowed_model", "canonical",
    "diff_program_text", "from_wire", "parse_agent", "parse_agents", "parse_program_text", "patch", "print_program",
    "program_agents", "program_reviewer", "render", "step_agents", "step_value", "template_agents",
    "template_reviewer", "wire_lamps",
]
