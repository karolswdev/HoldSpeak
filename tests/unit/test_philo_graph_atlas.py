"""PHILO-2-01 (lane W2) - the state atlas keeps its own contract.

Every check here is a reference check, never a phrase-presence check: the atlas
validates against its schema, its ids resolve, its setup recipes name API pairs
that EXIST in the generated OpenAPI, its fixtures hash to what it claims, and
every source reference lands on a line that still holds the symbol it cites.
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).resolve().parents[2]
ATLAS_PATH = REPO / "docs/internal/philo/graph/atlas.json"
SCHEMA_PATH = REPO / "docs/internal/philo/graph/atlas.schema.json"
OPENAPI_PATH = REPO / "docs/generated/openapi.json"

# The seven families brief section 4 rules the initial atlas must cover.
BRIEF_FAMILIES = {
    "projections",
    "briefs",
    "meetings",
    "engines",
    "first_value",
    "desk_presentation",
    "time",
}
JOBS = [f"j{n}" for n in range(1, 12)]
RIG_PATH = REPO / "scripts/graph_walk.py"


def _rig():
    """The rig itself, imported (stdlib-only at module level), never retyped."""
    spec = importlib.util.spec_from_file_location("_graph_walk_for_atlas", RIG_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rig_predicate_kinds() -> set[str]:
    """The kinds the rig's evaluator actually implements.

    Read off `check_predicate`'s own source rather than its docstring, so a kind
    that is documented but not implemented cannot slip into the atlas.
    """
    source = inspect.getsource(_rig().check_predicate)
    return set(re.findall(r'kind == "([a-z_]+)"', source))


def _acts(case: dict) -> list[dict]:
    """Every act of a case: its setup steps and its trigger."""
    steps = list(case["setup"])
    if case.get("trigger"):
        steps.append(case["trigger"])
    return steps


# One CSS simple selector: an optional tag, then any run of #id, .class,
# [attr...] and :pseudo(...). Prose fails it -- "face:" has no pseudo name,
# and a bare word carries none of `.#[:` at all.
_SIMPLE = re.compile(
    r"^([a-zA-Z][a-zA-Z0-9-]*)?"
    r"([#.][A-Za-z0-9_-]+|\[[^\]]+\]|:{1,2}[a-zA-Z-]+(\([^)]*\))?)*$"
)


def _is_css_selector(text: str) -> bool:
    """True for something document.querySelector could take; False for prose."""
    if not text or not any(ch in text for ch in ".#[:"):
        return False
    for token in text.split():
        if token in (">", "+", "~", ","):
            continue
        if not _SIMPLE.match(token.rstrip(",")):
            return False
    return True


@pytest.fixture(scope="module")
def atlas() -> dict:
    return json.loads(ATLAS_PATH.read_text())


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def openapi() -> dict:
    return json.loads(OPENAPI_PATH.read_text())


def test_schema_is_a_valid_2020_12_schema(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)


def test_atlas_validates_against_its_schema(atlas: dict, schema: dict) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(atlas),
        key=lambda e: list(e.absolute_path),
    )
    assert not errors, "\n".join(
        f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:20]
    )


def test_ids_are_unique(atlas: dict) -> None:
    for bucket in ("cases", "states", "clocks", "excluded"):
        ids = [row["id"] for row in atlas[bucket]]
        duplicates = sorted({i for i in ids if ids.count(i) > 1})
        assert not duplicates, f"duplicate ids in {bucket}: {duplicates}"


def test_every_case_state_id_resolves(atlas: dict) -> None:
    known = {state["id"] for state in atlas["states"]}
    dangling = sorted(
        {case["state_id"] for case in atlas["cases"] if case["state_id"] not in known}
    )
    assert not dangling, f"cases point at states that do not exist: {dangling}"


def test_every_case_reference_inside_the_atlas_resolves(atlas: dict) -> None:
    """reachable_by and clocks.used_by may only name cases the atlas carries."""
    case_ids = {case["id"] for case in atlas["cases"]}
    dangling: list[str] = []
    for state in atlas["states"]:
        for ref in state["reachable_by"]:
            if ref.startswith("case.") and ref not in case_ids:
                dangling.append(f"{state['id']} -> {ref}")
    for clock in atlas["clocks"]:
        for ref in clock["used_by"]:
            if ref not in case_ids:
                dangling.append(f"{clock['id']} -> {ref}")
    assert not dangling, f"dangling case references: {dangling}"


def test_every_clock_a_case_uses_is_declared(atlas: dict) -> None:
    declared = {clock["id"] for clock in atlas["clocks"]}
    used = {
        step["clock"]
        for case in atlas["cases"]
        for step in _acts(case)
        if step["kind"] == "clock"
    }
    assert used <= declared, f"undeclared clocks: {sorted(used - declared)}"


def test_every_applicable_case_carries_one_trigger(atlas: dict) -> None:
    """W3's rig contract: the trigger is the act fired through the real entry
    point, held separately from setup so the `before` capture lands between them.
    A case that cannot be driven carries no trigger at all."""
    problems: list[str] = []
    for case in atlas["cases"]:
        has = "trigger" in case
        if case["applicability"] == "applicable" and not has:
            problems.append(f"{case['id']}: applicable with no trigger")
        if case["applicability"] != "applicable" and has:
            problems.append(f"{case['id']}: {case['applicability']} but carries a trigger")
    assert not problems, problems


def test_no_timer_edge_is_triggered_by_a_substitute_button(atlas: dict) -> None:
    """Brief section 7: a timer is not tested by clicking a substitute button."""
    problems: list[str] = []
    for case in atlas["cases"]:
        trigger = case.get("trigger")
        if not trigger:
            continue
        if any(edge.startswith("edge.timer.") for edge in case["edge_ids"]):
            if trigger["kind"] == "ui":
                problems.append(f"{case['id']}: a timer edge triggered through the face")
    assert not problems, problems


def test_every_api_setup_step_exists_in_the_generated_openapi(
    atlas: dict, openapi: dict
) -> None:
    paths = openapi["paths"]
    missing: list[str] = []
    for case in atlas["cases"]:
        for step in _acts(case):
            if step["kind"] != "api":
                continue
            path, method = step["path"], step["method"].lower()
            if path not in paths or method not in paths[path]:
                missing.append(f"{case['id']}: {step['method']} {path}")
    assert not missing, f"setup steps name routes that do not exist: {missing}"


def test_every_fixture_step_exists_and_hashes_as_claimed(atlas: dict) -> None:
    problems: list[str] = []
    for case in atlas["cases"]:
        for step in _acts(case):
            if step["kind"] != "fixture":
                continue
            fixture = REPO / step["path"]
            if not fixture.is_file():
                problems.append(f"{case['id']}: missing fixture {step['path']}")
                continue
            digest = hashlib.sha256(fixture.read_bytes()).hexdigest()
            if digest != step["sha256"]:
                problems.append(
                    f"{case['id']}: {step['path']} hashes {digest}, atlas claims {step['sha256']}"
                )
    assert not problems, problems


def test_every_source_reference_lands_on_its_symbol(atlas: dict) -> None:
    """A line number is evidence, not identity (brief section 1).

    The cited line must still hold the cited symbol, or the reference has
    drifted and the claim behind it is no longer proven.
    """
    problems: list[str] = []
    for state in atlas["states"]:
        for ref in state["sources"]:
            target = REPO / ref["path"]
            if not target.is_file():
                problems.append(f"{state['id']}: missing file {ref['path']}")
                continue
            lines = target.read_text(errors="replace").splitlines()
            if not 1 <= ref["line"] <= len(lines):
                problems.append(
                    f"{state['id']}: {ref['path']}:{ref['line']} is past the end of the file"
                )
                continue
            line = lines[ref["line"] - 1]
            if ref["symbol"] not in line:
                problems.append(
                    f"{state['id']}: {ref['path']}:{ref['line']} no longer holds "
                    f"{ref['symbol']!r} (line reads {line.strip()[:80]!r})"
                )
    assert not problems, "\n".join(problems)


def test_every_phase1_reference_resolves_to_a_record(atlas: dict) -> None:
    """Phase 1 references are inventory path plus record id (brief section 8)."""
    shards: dict[str, set[str]] = {}
    for shard in sorted((REPO / "docs/internal/philo/data").glob("*.json")):
        data = json.loads(shard.read_text())
        ids = {
            record["id"]
            for key in (
                "capabilities",
                "components",
                "integrations",
                "domain_model",
                "trust_boundaries",
            )
            for record in (data.get(key) or [])
            if record.get("id")
        }
        shards[str(shard.relative_to(REPO))] = ids

    problems: list[str] = []
    for state in atlas["states"]:
        for ref in state["phase1_refs"]:
            known = shards.get(ref["path"])
            if known is None:
                problems.append(f"{state['id']}: no such shard {ref['path']}")
            elif ref["record_id"] not in known:
                problems.append(
                    f"{state['id']}: {ref['path']} holds no record {ref['record_id']!r}"
                )
    assert not problems, problems


def test_every_selected_job_has_an_applicable_case_except_j8(atlas: dict) -> None:
    """J1-J11 are the owner-deferred selection ruled in story 01.

    J8 is the one job the rig cannot drive (native hotkey, other-application
    delivery), so it must carry an UNEXERCISED record with a reason, never an
    applicable case that would quietly claim it was walked.
    """
    by_job: dict[str, list[dict]] = {}
    for case in atlas["cases"]:
        by_job.setdefault(case["job"], []).append(case)

    for job in JOBS:
        cases = by_job.get(job, [])
        assert cases, f"{job} has no case at all"
        if job == "j8":
            assert all(
                case["applicability"] == "unreachable" and case.get("reason")
                for case in cases
            ), "j8 must be recorded unreachable with a reason, never applicable"
        else:
            assert any(
                case["applicability"] == "applicable" for case in cases
            ), f"{job} has no applicable case"


def test_every_brief_family_is_present(atlas: dict) -> None:
    families = {state["family"] for state in atlas["states"]}
    assert BRIEF_FAMILIES <= families, f"missing families: {sorted(BRIEF_FAMILIES - families)}"


def test_quiet_is_never_an_attention_state(atlas: dict) -> None:
    """Astra's finding 2: quiet is not a projection attention state."""
    offenders = [
        state["id"]
        for state in atlas["states"]
        if state["values"].get("attention_state") == "quiet"
    ]
    assert not offenders, offenders


def test_face_cases_carry_both_ruled_viewports(atlas: dict) -> None:
    """Brief section 4: exercise each applicable face case at 1440 and 393.

    A case whose setup touches the face is a face case; a protocol-only case
    has no invented viewport requirement.
    """
    problems: list[str] = []
    for case in atlas["cases"]:
        if case["applicability"] != "applicable":
            continue
        touches_face = any(step["kind"] == "ui" for step in _acts(case))
        if touches_face and sorted(case["viewports"]) != [393, 1440]:
            problems.append(f"{case['id']}: face case with viewports {case['viewports']}")
    assert not problems, problems


def test_unexercised_states_name_a_mechanism_and_a_cost(atlas: dict) -> None:
    """Brief section 4: record it as unexercised, with the missing mechanism and its cost."""
    problems: list[str] = []
    for state in atlas["states"]:
        for ref in state["reachable_by"]:
            if not ref.startswith("unexercised: "):
                continue
            body = ref[len("unexercised: ") :]
            if "Cost:" not in body:
                problems.append(f"{state['id']}: unexercised note names no cost")
            if len(body) < 60:
                problems.append(f"{state['id']}: unexercised note names no mechanism")
    assert not problems, problems


def test_source_commit_is_the_revision_the_atlas_was_derived_from(atlas: dict) -> None:
    assert len(atlas["source_commit"]) == 40
    assert atlas["source_commit"] == atlas["source_commit"].lower()


# ─────────────────────── the rig's expected-result contract ───────────────────


def test_every_applicable_predicate_is_a_kind_the_rig_implements(atlas: dict) -> None:
    """A predicate written in prose is recorded `blocked`, never a verdict.

    The kind set comes from scripts/graph_walk.py::check_predicate itself.
    """
    kinds = _rig_predicate_kinds()
    assert kinds, "could not read the rig's predicate kinds"
    problems: list[str] = []
    for case in atlas["cases"]:
        predicate = case["expected"].get("predicate")
        if predicate is None:
            continue
        if predicate["kind"] not in kinds:
            problems.append(
                f"{case['id']}: predicate kind {predicate['kind']!r} is not one of {sorted(kinds)}"
            )
    assert not problems, problems


def test_every_predicate_observes_a_selector_or_a_route(atlas: dict) -> None:
    """observe_at is a CSS selector, or `protocol: METHOD /path` (the rig's
    PROTOCOL_PREFIX). Anything else is prose the rig cannot aim at."""
    prefix = _rig().PROTOCOL_PREFIX
    problems: list[str] = []
    for case in atlas["cases"]:
        if "predicate" not in case["expected"]:
            continue
        where = case["expected"]["observe_at"]
        if where.startswith(prefix):
            method, _, path = where[len(prefix) :].strip().partition(" ")
            if not path.startswith("/"):
                problems.append(f"{case['id']}: {where!r} names no route path")
            if method.upper() not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                problems.append(f"{case['id']}: {where!r} names no HTTP method")
            continue
        if not _is_css_selector(where):
            problems.append(f"{case['id']}: observe_at {where!r} is not a selector")
    assert not problems, problems


def test_protocol_predicates_ask_for_a_new_row(atlas: dict) -> None:
    """`min_new: 0` would pass on an unexplained zero diff (brief section 3)."""
    problems = [
        case["id"]
        for case in atlas["cases"]
        if case["expected"].get("predicate", {}).get("kind") == "protocol_rows"
        and int(case["expected"]["predicate"].get("min_new", 1)) < 1
    ]
    assert not problems, problems


def test_every_case_keeps_its_human_sentence(atlas: dict) -> None:
    """`words` is the prose the owner and the council read; it is never dropped."""
    problems = [case["id"] for case in atlas["cases"] if not case["expected"].get("words")]
    assert not problems, problems
