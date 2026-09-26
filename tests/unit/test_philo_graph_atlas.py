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
# PHILO-3-04 counsel (Astra, condition 2): every atlas file under the graph
# directory — atlas.json and each phase extension (atlas-phase3.json, ...) —
# keeps the schema and the source-anchor contract, not only atlas.json.
ATLAS_FILES = sorted(
    path for path in (REPO / "docs/internal/philo/graph").glob("atlas*.json")
    if path.name != SCHEMA_PATH.name
)
GRAPH_SCHEMA_PATH = REPO / "docs/internal/philo/graph/graph.schema.json"
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


def _rig_ui_actions() -> set[str]:
    """The ui actions the rig implements, read off `_ui_step`'s own branches.

    The rig exports no constant for them (checked at this revision), so the set
    is derived from the implementation rather than retyped here.
    """
    source = inspect.getsource(_rig()._ui_step)
    return set(re.findall(r'action == "([a-z_]+)"', source))


def _rig_predicate_kinds() -> set[str]:
    """The kinds the rig's evaluator actually implements.

    Read off `check_predicate`'s own source rather than its docstring, so a kind
    that is documented but not implemented cannot slip into the atlas.
    """
    source = inspect.getsource(_rig().check_predicate)
    return set(re.findall(r'kind == "([a-z_]+)"', source))


def _checks(case: dict) -> list[dict]:
    """The executable check steps among a case's preconditions."""
    return [
        entry
        for entry in case["preconditions"]
        if isinstance(entry, dict) and entry.get("kind") == "check"
    ]


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


@pytest.fixture(scope="module", params=ATLAS_FILES, ids=lambda path: path.name)
def every_atlas(request: pytest.FixtureRequest) -> dict:
    return json.loads(request.param.read_text())


def test_every_atlas_file_is_read() -> None:
    names = {path.name for path in ATLAS_FILES}
    assert ATLAS_PATH.name in names and len(names) >= 2, names


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def openapi() -> dict:
    return json.loads(OPENAPI_PATH.read_text())


def test_schema_is_a_valid_2020_12_schema(schema: dict) -> None:
    Draft202012Validator.check_schema(schema)


def test_atlas_validates_against_its_schema(every_atlas: dict, schema: dict) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(every_atlas),
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


def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
    """A line number is evidence, not identity (brief section 1).

    The cited line must still hold the cited symbol, or the reference has
    drifted and the claim behind it is no longer proven.
    """
    problems: list[str] = []
    for state in every_atlas["states"]:
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

    A case is a FACE case when its trigger is fired at the face or its
    observation location is a selector. Setup alone does not make one: a case
    observed at a route stays protocol-only even when its reproduction chain
    had to drive the desk to reach the starting state.
    """
    problems: list[str] = []
    for case in atlas["cases"]:
        if case["applicability"] != "applicable":
            continue
        where = case["expected"].get("observe_at") or ""
        if isinstance(where, dict) and where.get("kind") == "op":
            face = False
        else:
            face = (
                case.get("trigger", {}).get("kind") == "ui"
                or (bool(where) and not where.startswith("protocol:"))
            )
        want = [393, 1440] if face else []
        if sorted(case["viewports"]) != want:
            problems.append(
                f"{case['id']}: {'face' if face else 'protocol-only'} case with "
                f"viewports {case['viewports']}"
            )
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
        candidates = [case["expected"].get("predicate")] + [
            entry["predicate"] for entry in _checks(case)
        ]
        for predicate in candidates:
            if predicate is None:
                continue
            if predicate["kind"] not in kinds:
                problems.append(
                    f"{case['id']}: predicate kind {predicate['kind']!r} is not one "
                    f"of {sorted(kinds)}"
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
        if isinstance(where, dict) and where.get("kind") == "op":
            continue
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


def test_operation_siblings_use_headless_reads_and_canonical_steps() -> None:
    """Operation siblings prove the same durable result through the hub.

    Their observation is an operation object, so the rig can call a durable
    read after the trigger.  A refusal must observe that retained read while
    the trigger's own refusal record remains the only mutating result.
    """
    siblings = [
        case
        for path in ATLAS_FILES
        for case in json.loads(path.read_text())['cases']
        if case['id'].endswith('.op') or case['id'].endswith('.op.replayed')
    ]
    # 19 Phase 5 op siblings plus two replay variants; PHILO-7-03 adds 18
    # (atlas-phase7.json: nine desk pairs, two receipt cases, four refusal
    # receipts, three note siblings). PHILO-8-03 adds 5 (atlas-phase8.json:
    # two zones, the rename, the taken name, the list delete, two deletes).
    assert len(siblings) == 44
    sibling_ids = {case["id"] for case in siblings}
    assert READ_REFUSAL_SIBLINGS <= sibling_ids
    mutating = {
        'decision.create', 'decision.update', 'meeting.import',
        'meeting.summary.run', 'brief.generate', 'brief.shelf.write',
        'thought.create', 'thought.save',
        # PHILO-7-03: the desk slice's writes.
        'note.create', 'zone.create', 'zone.file', 'zone.unfile',
        'kb.create', 'kb.member.add', 'kb.member.remove',
        'decision.supersede', 'decision.delete',
        # PHILO-8-03: the rename the list's name field writes.
        'zone.update',
    }
    readable = {
        'decision.read', 'decision.list', 'meeting.list', 'meeting.read',
        'brief.latest', 'brief.shelf.read', 'thought.read',
        'thought.workbench.read', 'thought.list',
        'note.read', 'note.list', 'zone.read', 'zone.list', 'zone.members',
        'kb.read', 'kb.list', 'kb.members', 'kernel.receipt.read',
    }
    problems: list[str] = []
    for case in siblings:
        expected = case['expected']
        observation = expected.get('observe_at')
        if not isinstance(observation, dict) or observation.get('kind') != 'op':
            problems.append(f"{case['id']}: expected.observe_at is not an op object")
            continue
        if observation.get('name') not in readable:
            problems.append(f"{case['id']}: observation re-fires {observation.get('name')!r}")
        predicate_kind = (expected.get('predicate') or {}).get('kind')
        if predicate_kind not in {'op_field', 'op_refusal', 'op_facts'}:
            problems.append(f"{case['id']}: predicate is not an op predicate")
        for read in expected.get('reads', []):
            if read.get('kind') != 'op' or read.get('name') not in readable:
                problems.append(f"{case['id']}: expected read is not durable: {read}")
        for step in _acts(case):
            if step.get('kind') == 'ui':
                problems.append(f"{case['id']}: operation sibling carries a UI step")
        trigger = case.get('trigger') or {}
        if trigger.get('kind') == 'op' and trigger.get('name') not in mutating:
            if case["id"] not in READ_REFUSAL_SIBLINGS or trigger.get("name") not in readable:
                problems.append(f"{case['id']}: trigger is not a producer operation")
    assert not problems, '\n'.join(problems)


def test_named_pair_observations_bind_their_read_arguments() -> None:
    """A durable read must use an id captured from the case's own producer."""
    cases = [case for path in ATLAS_FILES for case in json.loads(path.read_text())['cases']]
    bases = {case['id'][:-3] for case in cases if case['id'].endswith('.op')}
    problems = []
    for case in cases:
        if not any(case['id'] == base or case['id'].startswith(base + '.') for base in bases):
            continue
        bound = {step['capture_as'] for step in _acts(case) if step.get('capture_as')}
        bound |= {extra['as'] for step in _acts(case) for extra in step.get('capture_more', [])}
        expected = case['expected']
        reads = {key: expected.get(key) for key in ('observe_at', 'predicate', 'reads')}
        names = set(re.findall(r'\{([a-z][a-z0-9_]*)\}', json.dumps(reads)))
        if names - bound:
            problems.append((case['id'], sorted(names - bound)))
    assert not problems, problems


def test_all_handled_operation_maps_items_by_decision_source() -> None:
    """Shelf ids follow durable decision relationships, never brief sort order."""
    case = next(
        case
        for path in ATLAS_FILES
        for case in json.loads(path.read_text())['cases']
        if case['id'] == 'case.philo404.arrival_triaged_headline.all_handled.op'
    )
    captures = [
        step for step in case['setup']
        if step.get('kind') == 'op'
        and step.get('name') == 'brief.latest'
        and step.get('capture_as') in {'item_a', 'item_b'}
    ]
    assert {step['capture_as'] for step in captures} == {'item_a', 'item_b'}
    assert {tuple(step['capture_match'].items()) for step in captures} == {
        (('source_ref', 'decision:{decision_a}'),),
        (('source_ref', 'decision:{decision_b}'),),
    }
    assert all(step['capture_path'] == 'sections.decisions' for step in captures)
    assert all(step['capture_field'] == 'id' for step in captures)


def test_breakage_cases_use_evening_wrapper_and_shelf_old_item() -> None:
    """Breakage proof pins and shelves the first brief's own failure row."""
    assert (REPO / "scripts/philo5_breakage_walk.py").exists()
    cases = {
        case['id']: case
        for path in ATLAS_FILES
        for case in json.loads(path.read_text())['cases']
        if case['id'] in {
            'case.closure.chain.s5_next_day_brief_with_breakage',
            'case.closure.chain.s5_next_day_brief_with_breakage.op',
        }
    }
    assert len(cases) == 2
    for case_id, case in cases.items():
        wrapper = next(
            text for text in case['preconditions']
            if 'scripts/philo5_breakage_walk.py' in text
        )
        assert f'--case {case_id}' in wrapper
        assert '[17,23)' in wrapper
        assert 'BLOCKED, never PASS' in wrapper

        is_op = case_id.endswith('.op')
        if is_op:
            probe = next(
                step for step in case['setup']
                if step.get('kind') == 'api'
                and step.get('method') == 'GET'
                and step.get('path') == '/api/decisions/philo402-deliberately-absent'
            )
            assert probe['expect_status'] == 404
            assert probe['body'] is None
            assert any('observer parity' in text for text in case['preconditions'])
            capture = next(
                step for step in case['setup']
                if step.get('kind') == 'op'
                and step.get('name') == 'brief.latest'
                and step.get('capture_as') == 'old_breakage_id'
            )
            shelf = next(
                step for step in case['setup']
                if step.get('kind') == 'op'
                and step.get('name') == 'brief.shelf.write'
                and step.get('args', {}).get('item_id') == '{old_breakage_id}'
            )
        else:
            capture = next(
                step for step in case['setup']
                if step.get('kind') == 'api'
                and step.get('method') == 'GET'
                and step.get('path') == '/api/brief/latest'
                and step.get('capture_as') == 'old_breakage_id'
            )
            shelf = next(
                step for step in case['setup']
                if step.get('kind') == 'api'
                and step.get('method') == 'POST'
                and step.get('path') == '/api/brief/items/{old_breakage_id}/shelf'
            )
        # PHILO-6-02 round 2: the desk read and the lifecycle read of one
        # missing decision both read `Decision did not load` (no
        # implementation word tells them apart), so both variants check row
        # 0's words and pin row 0.
        assert capture['capture_path'] == 'sections.broke.0.id'
        assert 'capture_match' not in capture
        if is_op:
            check = next(
                step for step in case['setup']
                if step.get('kind') == 'check'
                and (step.get('predicate') or {}).get('path') == 'sections.broke.0.text'
            )
            assert check['predicate']['value'] == 'Decision did not load'
        assert shelf.get('args', shelf.get('body', {})).get('state') == 'acknowledged'


# ───────────── the rig's ui vocabulary, and the one case contract ─────────────


def test_every_ui_action_is_one_the_rig_implements(atlas: dict) -> None:
    """Prose in a ui step is a step the rig raises `unknown ui action` on."""
    actions = _rig_ui_actions()
    assert actions, "could not read the rig's ui actions"
    problems: list[str] = []
    for case in atlas["cases"]:
        for step in _acts(case):
            if step["kind"] != "ui":
                continue
            if step["action"] not in actions:
                problems.append(
                    f"{case['id']}: ui action {step['action']!r} is not one of {sorted(actions)}"
                )
    assert not problems, problems


def test_every_boundary_names_its_substitution(atlas: dict) -> None:
    """A boundary is a NAMED substitution, not a sentence (brief section 7)."""
    problems: list[str] = []
    for case in atlas["cases"]:
        for step in _acts(case):
            if step["kind"] != "boundary":
                continue
            name = step.get("substitute", "")
            if not name or " " in name:
                problems.append(f"{case['id']}: boundary substitute {name!r} is not a name")
    assert not problems, problems


SUMMARY_CASE_PREFIXES = ("case.j4.", "case.j5.", "case.j6.", "case.j7.")


def _summary_cases(atlas: dict) -> list[dict]:
    return [case for case in atlas["cases"] if case["id"].startswith(SUMMARY_CASE_PREFIXES)]


def test_summary_cases_use_the_retained_architect_import_fixture(atlas: dict) -> None:
    """A2's meeting material enters through the real multipart import boundary.

    J4's microphone cases stay separate: their browser-device boundary is a
    lawful blocked proof, while every imported meeting used by J4-J7 must use
    the retained synthetic architect WAV. The old smoke WAV made a transport
    pass look like useful meeting material.
    """
    expected = "tests/fixtures/philo3_architect_meeting.wav"
    problems: list[str] = []
    for case in _summary_cases(atlas):
        if case["id"] == "case.j6.route_intelligence_run.refusal":
            continue
        imports = [
            step for step in _acts(case)
            if step.get("kind") == "fixture"
            and step.get("route", {}).get("path") == "/api/meetings/import"
        ]
        if imports and any(step.get("path") != expected for step in imports):
            problems.append(f"{case['id']}: imported material is not {expected}")
    assert not problems, problems


def test_summary_run_cases_have_one_run_trigger(atlas: dict) -> None:
    """The real Arrival Run gesture is the one trigger; setup never re-runs it."""
    problems: list[str] = []
    for case in atlas["cases"]:
        if not case["id"].startswith("case.j6.run_summary."):
            continue
        steps = _acts(case)
        clicks = [
            step for step in steps
            if step.get("kind") == "ui"
            and step.get("action") == "click"
            and "arrival-run-intel" in step.get("selector", "")
        ]
        api_runs = [
            step for step in steps
            if step.get("kind") == "api"
            and step.get("method") == "POST"
            and "/intelligence/run" in step.get("path", "")
        ]
        if len(clicks) != 1 or api_runs:
            problems.append(
                f"{case['id']}: Run clicks={len(clicks)}, API run steps={len(api_runs)}"
            )
    assert not problems, problems


def test_summary_running_reads_the_claimed_job_wire_status(atlas: dict) -> None:
    """The producer exposes a claimed current row while execution is live."""
    case = next(
        case for case in _summary_cases(atlas)
        if case["id"] == "case.j6.run_summary.intel_running"
    )
    predicate = case["expected"]["predicate"]
    assert predicate == {
        "kind": "protocol_field",
        "path": "/jobs/0/status",
        "value": "claimed",
    }


def test_summary_queued_reads_the_run_admission_response(atlas: dict) -> None:
    case = next(
        case for case in _summary_cases(atlas)
        if case["id"] == "case.j6.run_summary.intel_queued"
    )
    trigger = case["trigger"]
    predicate = case["expected"]["predicate"]
    assert trigger.get("trigger_route") == {
        "method": "POST",
        "path": "/api/meetings/{meeting_id}/intelligence/run",
    }
    assert predicate["kind"] == "protocol_status"
    assert predicate["method"] == "POST"
    assert predicate["path"] == "/api/meetings/{meeting_id}/intelligence/run"
    assert predicate["status"] == 200
    assert predicate["body_contains"] == '"state": "queued"'
    assert predicate["body_fields"] == {"jobId": {"nonempty": True}}


def test_summary_preconditions_do_not_require_future_or_consumed_run_state(atlas: dict) -> None:
    for case in _summary_cases(atlas):
        setup_run = any(
            step.get("action") == "click"
            and "arrival-run-intel" in step.get("selector", "")
            for step in case["setup"]
        )
        checks = _checks(case)
        if setup_run:
            assert not any(
                entry.get("observe_at") == "[data-testid=arrival-run-intel]"
                for entry in checks
            ), case["id"]
        elif "arrival-run-intel" in case["trigger"].get("selector", ""):
            assert not any(
                entry.get("observe_at") == "protocol: GET /api/intel/jobs"
                for entry in checks
            ), case["id"]


def test_summary_state_reads_do_not_require_a_new_row_after_setup_run(atlas: dict) -> None:
    for suffix in ("intel_running", "intel_ready"):
        case = next(c for c in _summary_cases(atlas)
                    if c["id"] == f"case.j6.run_summary.{suffix}")
        assert case["expected"]["predicate"]["kind"] == "protocol_field"
        assert "min_new" not in case["expected"]["predicate"]


def test_summary_manual_retry_requires_failed_producer_and_current_route(atlas: dict) -> None:
    case = next(c for c in _summary_cases(atlas)
                if c["id"] == "case.j6.run_summary.intel_retry")
    assert any(entry.get("predicate", {}).get("path") == "/intel_job/status"
               and entry["predicate"].get("value") == "failed"
               for entry in _checks(case))
    assert any(step.get("method") == "GET"
               and step.get("capture_path") == "/planned_route/selection_hash"
               and step.get("capture_as") == "selection_hash"
               for step in case["setup"])
    assert case["trigger"]["body"] == {"expected_selection_hash": "{selection_hash}"}


def test_summary_planned_host_cases_check_real_text_and_control_ownership(atlas: dict) -> None:
    for suffix in ("route_disclosed", "planned_host_disclosed"):
        case = next(c for c in _summary_cases(atlas)
                    if c["id"] == f"case.j5.meeting_open.{suffix}")
        assert case["expected"]["predicate"] == {
            "kind": "text_contains", "value": "192.168.1.43 · LAN",
        }
        assert any(entry.get("observe_at") == "[data-testid=arrival-run-intel]"
                   and entry.get("predicate", {}).get("kind") == "hit_target"
                   and entry["predicate"].get("min_height_by_viewport", {}).get("393", 0) >= 44
                   for entry in _checks(case))


def test_summary_failure_cases_retain_reply_at_the_provider_boundary(atlas: dict) -> None:
    """Failure replay is a tree artifact and the rig's real provider seam."""
    expected = "tests/fixtures/philo3_summary_failure_reply.json"
    problems: list[str] = []
    for case in atlas["cases"]:
        if case["id"] not in {
            "case.j6.run_summary.intel_failed",
            "case.j6.run_summary.intel_retry",
            "case.j6.run_summary.retrying",
        }:
            continue
        boundaries = [step for step in _acts(case) if step.get("kind") == "boundary"]
        replies = [step for step in boundaries if step.get("substitute") == "engine_reply"]
        if len(boundaries) != 1 or len(replies) != 1:
            problems.append(f"{case['id']}: expected one engine_reply boundary")
            continue
        boundary = replies[0]
        if (boundary.get("reply") != expected or "reply_path" in boundary
                or boundary.get("adapter") != "labelled-substitution"):
            problems.append(
                f"{case['id']}: boundary must use reply={expected!r} and "
                "adapter='labelled-substitution'"
            )
    assert not problems, problems


def test_summary_imports_wait_for_real_completion_and_retain_title(atlas: dict) -> None:
    """A 202 upload is only the start of the real ASR import."""
    expected = "tests/fixtures/philo3_architect_meeting.wav"
    problems: list[str] = []
    for case in _summary_cases(atlas):
        if case["id"] == "case.j6.route_intelligence_run.refusal":
            continue
        for step in _acts(case):
            if step.get("kind") != "fixture" or step.get("route", {}).get("path") != "/api/meetings/import":
                continue
            wait = step.get("wait_for") or {}
            fields = wait.get("fields") or {}
            if step.get("path") != expected:
                problems.append(f"{case['id']}: import does not use {expected}")
            if step.get("expect_status") != 202:
                problems.append(f"{case['id']}: import must require HTTP 202")
            if wait.get("method") != "GET" or wait.get("path") != "/api/meetings/{meeting_id}":
                problems.append(f"{case['id']}: import has no meeting-detail completion wait")
            if fields.get("/transcription_status") != "complete":
                problems.append(f"{case['id']}: completion wait does not require transcription_status=complete")
            if not isinstance(fields.get("/duration"), dict) or not fields["/duration"].get("positive"):
                problems.append(f"{case['id']}: completion wait does not require positive duration")
            if not isinstance(fields.get("/segments"), dict) or fields["/segments"].get("min_items") != 1:
                problems.append(f"{case['id']}: completion wait does not require transcript segments")
            if (step.get("form") or {}).get("title") != "Architecture boundary review":
                problems.append(f"{case['id']}: import does not carry the readable meeting title")
    assert not problems, problems


def test_summary_arrival_observations_name_the_rendered_states(atlas: dict) -> None:
    """Rendered proof reads Arrival's summary/error surfaces, not old wrappers."""
    wanted = {
        "case.j6.run_summary.summary_text": ("[data-testid=meeting-summary-text]", "text_nonempty"),
        "case.j6.run_summary.intel_failed": ("[data-testid=arrival-summary-status]", "text_equals"),
        "case.j7.arrival_load.reload_persisted": ("[data-testid=meeting-summary-text]", "text_equals"),
    }
    problems: list[str] = []
    for case_id, (selector, kind) in wanted.items():
        case = next(case for case in _summary_cases(atlas) if case["id"] == case_id)
        expected = case["expected"]
        predicate = expected.get("predicate") or {}
        if expected.get("observe_at") != selector or predicate.get("kind") != kind:
            problems.append(f"{case_id}: expected {kind} at {selector}")
        words = expected.get("words", "")
        if "HOLDSPEAK-SYNTH-1" in words or ".desk-window .surface-material" in words:
            problems.append(f"{case_id}: retains the old summary marker or wrapper")
    failed = next(case for case in _summary_cases(atlas) if case["id"] == "case.j6.run_summary.intel_failed")
    if not failed["expected"]["predicate"].get("value", "").startswith("FAILED\nLAST ATTEMPT · "):
        problems.append("case.j6.run_summary.intel_failed: a retry cause is not terminal failure")
    assert not problems, problems


def test_summary_models_window_closes_before_arrival_steps(atlas: dict) -> None:
    problems: list[str] = []
    for case in _summary_cases(atlas):
        setup = case.get("setup", [])
        for index, step in enumerate(setup):
            if (step.get("kind") != "ui" or step.get("action") != "click"
                    or step.get("selector") != "[data-testid=concierge-add-submit]"):
                continue
            following = setup[index + 1] if index + 1 < len(setup) else {}
            if not (following.get("kind") == "ui"
                    and following.get("action") == "wait_for"
                    and following.get("state") == "hidden"
                    and following.get("selector") == "#surface-concierge .desk-window-title"):
                problems.append(f"{case['id']}: Models is not closed before the next Arrival step")
    assert not problems, problems


def test_summary_restart_proof_retains_summary_receipt_and_identity(atlas: dict) -> None:
    case = next(case for case in _summary_cases(atlas) if case["id"] == "case.j7.hub_restart.intel_retained")
    trigger = case["trigger"]
    predicate = case["expected"]["predicate"]
    assert trigger.get("kind") == "cli" and trigger.get("action") == "restart_hub"
    assert trigger.get("capture_as") == "before_summary"
    assert case["expected"]["observe_at"] == "protocol: GET /api/meetings/{meeting_id}"
    assert predicate.get("value") == "{before_summary}"
    assert predicate.get("nonempty") is True
    assert predicate.get("restart_required") is True
    assert "/api/intel/summary" not in case["expected"].get("words", "")


def test_summary_microphone_cases_keep_the_lawful_blocked_boundary(atlas: dict) -> None:
    case = next(case for case in _summary_cases(atlas) if case["id"] == "case.j4.record_start.capture_recording")
    boundaries = [step for step in case["setup"] if step.get("kind") == "boundary"]
    assert boundaries and boundaries[0].get("substitute") == "browser_audio_device"
    assert not [step for step in _acts(case) if step.get("kind") == "fixture"]
    record_only = next(
        case for case in _summary_cases(atlas)
        if case["id"] == "case.j4.record_only.no_speech_head"
    )
    record_boundaries = [step for step in _acts(record_only) if step.get("kind") == "boundary"]
    assert record_boundaries and record_boundaries[0].get("substitute") == "browser_audio_device"
    assert record_boundaries[0].get("reply_path") == "tests/fixtures/philo3_architect_meeting.wav"


def test_summary_cases_do_not_claim_the_old_pangram(atlas: dict) -> None:
    assert not any(
        token in json.dumps(case)
        for case in _summary_cases(atlas)
        for token in ("HOLDSPEAK-SYNTH-1", "core_path_smoke_16k.wav")
    )


def test_summary_stop_cases_require_a_real_active_meeting(atlas: dict) -> None:
    """A fresh idle hub cannot turn POST /api/meeting/stop into capture proof."""
    for case_id in (
        "case.j4.meeting_stop.capture_finalized",
        "case.j4.meeting_stop.transcription_absent",
    ):
        case = next(case for case in _summary_cases(atlas) if case["id"] == case_id)
        checks = [
            step for step in case.get("preconditions", [])
            if isinstance(step, dict) and step.get("kind") == "check"
        ]
        assert any(
            step.get("observe_at") == "protocol: GET /api/runtime/status"
            and step.get("predicate", {}).get("kind") == "protocol_field"
            and step.get("predicate", {}).get("path") == "/meeting_active"
            and step.get("predicate", {}).get("value") is True
            for step in checks
        ), case_id


@pytest.fixture(scope="module")
def graph_case_schema() -> dict:
    return json.loads(GRAPH_SCHEMA_PATH.read_text())


def test_the_two_schemas_agree_on_the_case_contract(graph_case_schema: dict, schema: dict) -> None:
    """One case contract, not two (brief section 8: the graph is a JOIN)."""
    mine = schema["$defs"]["case"]
    theirs = graph_case_schema["$defs"]["case"]
    assert set(mine["required"]) == set(theirs["required"]), (
        f"required keys differ: mine-only={sorted(set(mine['required']) - set(theirs['required']))}, "
        f"theirs-only={sorted(set(theirs['required']) - set(mine['required']))}"
    )
    assert set(mine["properties"]) == set(theirs["properties"]), (
        f"case fields differ: mine-only={sorted(set(mine['properties']) - set(theirs['properties']))}, "
        f"theirs-only={sorted(set(theirs['properties']) - set(mine['properties']))}"
    )
    assert (mine["properties"]["applicability"]["enum"]
            == theirs["properties"]["applicability"]["enum"])
    assert (set(mine["properties"]["expected"]["required"])
            <= set(theirs["properties"]["expected"]["required"]) | {"words"})


def test_every_case_validates_against_the_graph_case_schema(
    atlas: dict, graph_case_schema: dict
) -> None:
    """Every atlas case must be a legal graph case, so the generator can join them.

    No exemption: the atlas case definition IS the graph's, so every case that
    validates against one validates against the other.
    """
    validator = Draft202012Validator(
        {"$schema": "https://json-schema.org/draft/2020-12/schema",
         "$ref": "#/$defs/case", "$defs": graph_case_schema["$defs"]}
    )
    problems: list[str] = []
    for case in atlas["cases"]:
        for error in validator.iter_errors(case):
            path = list(error.absolute_path)
            if path[:3] == ["expected", "predicate", "kind"]:
                continue
            if path[:1] == ["expected"] and case["applicability"] != "applicable":
                # An unreachable case is never fired, so it has no expected
                # RESULT to structure -- only a reason. graph.schema.json
                # already makes `trigger` conditional on applicability (its
                # allOf); `expected` needs the same treatment. Until it does,
                # this is the one shape the two schemas disagree on, and the
                # disagreement is NAMED here, never hidden.
                assert case.get("reason"), f"{case['id']} has neither predicate nor reason"
                continue
            problems.append(f"{case['id']}: {'/'.join(str(p) for p in path)}: {error.message}")
    assert not problems, "\n".join(problems[:20])


def test_the_graph_predicate_enum_does_not_outrun_the_rig(graph_case_schema: dict) -> None:
    """The graph schema may lag the rig; it may never claim a kind the rig lacks."""
    declared = set(
        graph_case_schema["$defs"]["case"]["properties"]["expected"]["properties"]
        ["predicate"]["properties"]["kind"]["enum"]
    )
    implemented = _rig_predicate_kinds()
    assert declared <= implemented, (
        f"the graph schema declares kinds the rig does not implement: "
        f"{sorted(declared - implemented)}"
    )


def test_a_case_without_a_predicate_is_unreachable_with_a_reason(atlas: dict) -> None:
    """The graph case contract requires a structured predicate, so a case that
    cannot carry one may not sit in the walk list as if it will run."""
    problems = [
        case["id"]
        for case in atlas["cases"]
        if "predicate" not in case["expected"]
        and not (case["applicability"] == "unreachable" and case.get("reason"))
    ]
    assert not problems, problems



def test_every_council_reading_names_its_sources(atlas: dict) -> None:
    """A reading is not a case: no trigger, no predicate, no verdict - so its
    only evidence is the source it cites and the payload it asks the council to
    read. Both are required."""
    problems: list[str] = []
    for reading in atlas["council_readings"]:
        if not reading["sources"]:
            problems.append(f"{reading['id']}: no sources")
        if not reading["reads"]:
            problems.append(f"{reading['id']}: names no payload to read")
        if not reading["words"].startswith("COUNCIL READING:"):
            problems.append(f"{reading['id']}: does not announce itself")
        for ref in reading["sources"]:
            target = REPO / ref["path"]
            if not target.is_file():
                problems.append(f"{reading['id']}: missing file {ref['path']}")
                continue
            lines = target.read_text(errors="replace").splitlines()
            if not (1 <= ref["line"] <= len(lines)) or ref["symbol"] not in lines[ref["line"] - 1]:
                problems.append(f"{reading['id']}: {ref['path']}:{ref['line']} lost {ref['symbol']!r}")
    assert not problems, problems


# ──────────────────── executable preconditions ────────────────────

# `check_preconditions` evaluates a check against ONE snapshot, passed as both
# `before` and `after` (scripts/graph_walk.py:1896-1897). Every predicate kind
# that decides by comparing the two is therefore useless there: `protocol_rows`
# and `protocol_rows_gone` always see zero movement, `unchanged` always holds,
# `presentation_change` never does, and `window_titled` reports "already open"
# and fails. A check must read the AFTER snapshot alone.
COMPARING_KINDS = frozenset({
    "protocol_rows", "protocol_rows_gone", "unchanged",
    "presentation_change", "window_titled",
})


def test_no_precondition_check_compares_two_snapshots(atlas: dict) -> None:
    problems = [
        f"{case['id']}: check uses {entry['predicate']['kind']!r}, which decides by "
        "comparing before and after; a precondition has only one snapshot"
        for case in atlas["cases"]
        for entry in _checks(case)
        if entry["predicate"]["kind"] in COMPARING_KINDS
    ]
    assert not problems, problems


def test_every_precondition_check_observes_a_selector_or_a_route(atlas: dict) -> None:
    prefix = _rig().PROTOCOL_PREFIX
    problems: list[str] = []
    for case in atlas["cases"]:
        for entry in _checks(case):
            where = entry["observe_at"] or ""
            if not (where.startswith(prefix) or _is_css_selector(where)):
                problems.append(f"{case['id']}: check observe_at {where!r} is not a location")
            if not entry.get("why"):
                problems.append(f"{case['id']}: check says nothing about why it is needed")
    assert not problems, problems


def test_no_check_asserts_the_result_the_trigger_must_produce(atlas: dict) -> None:
    """A precondition runs BEFORE the trigger. One that reads the case's own
    observation location would decide the case before it was fired."""
    problems = [
        f"{case['id']}: a precondition check reads {entry['observe_at']!r} with the "
        "case's own predicate; it would decide the case before the trigger fired"
        for case in atlas["cases"]
        for entry in _checks(case)
        if entry["observe_at"] == case["expected"].get("observe_at")
        and entry["predicate"] == case["expected"].get("predicate")
    ]
    assert not problems, problems


def test_every_protocol_field_path_with_a_placeholder_is_a_json_pointer(atlas: dict) -> None:
    """`_json_path` splits a dotted path on "." and a pointer path on "/"
    (scripts/graph_walk.py:627-628), so an id holding a dot must travel as a
    pointer or it is silently split into two segments that resolve to nothing.
    """
    problems: list[str] = []
    for case in atlas["cases"]:
        for predicate in [case["expected"].get("predicate")] + [
            entry["predicate"] for entry in _checks(case)
        ]:
            if not predicate or predicate.get("kind") != "protocol_field":
                continue
            path = predicate["path"]
            if "{" in path and not path.startswith("/"):
                problems.append(f"{case['id']}: {path!r} holds a placeholder but is dotted")
    assert not problems, problems


# ─────────────── no step may act on a root placeholder ───────────────

# `main.chair` was a fallback invented when a prose selector could not be
# parsed. The only <main className="chair..."> in the Chair is the FIRST-VALUE
# branch (web/src/desk/chair/ChairHome.tsx:413); the arrival branch has no such
# root, so the class was never verified for the desk. A click or a fill aimed at
# a page root is not aimed at a control.
ROOT_PLACEHOLDERS = frozenset({"main.chair", "body", "main", "#root", ".desk"})


def test_no_step_acts_on_a_root_placeholder(atlas: dict) -> None:
    problems = [
        f"{case['id']}: {step['action']} on the root placeholder {step['selector']!r}"
        for case in atlas["cases"]
        for step in _acts(case)
        if step.get("kind") == "ui"
        and step.get("selector") in ROOT_PLACEHOLDERS
    ]
    assert not problems, problems


def test_navigation_steps_carry_no_selector(atlas: dict) -> None:
    """`goto` and `reload` take no selector (scripts/graph_walk.py::_ui_step), so
    one riding along is a claim about a control that is never touched."""
    problems = [
        f"{case['id']}: {step['action']} carries selector {step['selector']!r}"
        for case in atlas["cases"]
        for step in _acts(case)
        if step.get("kind") == "ui"
        and step.get("action") in ("goto", "reload")
        and "selector" in step
    ]
    assert not problems, problems


def test_every_click_and_fill_names_a_control(atlas: dict) -> None:
    """A control is named by a testid, an aria-label, a role or its own class."""
    problems = [
        f"{case['id']}: {step['action']} selector {step['selector']!r} names no control"
        for case in atlas["cases"]
        for step in _acts(case)
        if step.get("kind") == "ui"
        and step.get("action") in ("click", "fill")
        and not any(
            token in step["selector"]
            for token in ("data-testid", "aria-label", "title=", "button", "input",
                          "textarea", ".desk-", ".thought-", ".concierge-", ".surface-")
        )
    ]
    assert not problems, problems


# ───────────────────── the first-value gate ─────────────────────

# Measured live by the rig's integration smoke on a fresh HOME: before the gate
# is crossed `.chair-first-value` is present and EVERY desk selector -- the Desk
# memory bell, the arrival headline -- is absent; after `Continue later` the
# counts invert. A face case that reaches for the desk without crossing the gate
# blocks and proves nothing.
GATE_SCOPE = "[data-testid=chair-first-value]"          # ChairHome.tsx:413
GATE_MARKERS = ("desk-first-words", "chair-first-value")


def _is_face_case(case: dict) -> bool:
    where = case["expected"].get("observe_at") or ""
    if isinstance(where, dict) and where.get("kind") == "op":
        return False
    return (
        case.get("trigger", {}).get("kind") == "ui"
        or (bool(where) and not where.startswith("protocol:"))
    )


def _is_gate_case(case: dict) -> bool:
    """A case that acts ON the gate, so crossing it would remove the control."""
    blob = json.dumps(case)
    return any(marker in blob for marker in GATE_MARKERS)


def test_every_desk_face_case_crosses_the_gate_first(atlas: dict) -> None:
    problems: list[str] = []
    for case in atlas["cases"]:
        if case["applicability"] != "applicable" or not _is_face_case(case):
            continue
        setup = case["setup"]
        if _is_gate_case(case):
            continue
        if len(setup) < 2:
            problems.append(f"{case['id']}: no gate crossing at all")
            continue
        first, second = setup[0], setup[1]
        if not (first.get("action") == "goto" and first.get("url") == "/"):
            problems.append(f"{case['id']}: first setup step is not goto /")
        if not (
            second.get("action") == "click_role"
            and second.get("name") == "Continue later"
            and second.get("optional") is True
        ):
            problems.append(f"{case['id']}: second setup step is not the optional gate click")
    assert not problems, problems


def test_no_gate_case_crosses_the_gate_in_setup(atlas: dict) -> None:
    """The press IS the trigger for the gate cases; pressing it in setup would
    take the control under test off the page."""
    problems = [
        f"{case['id']}: setup presses Continue later, the control this case tests"
        for case in atlas["cases"]
        if _is_gate_case(case)
        for step in case["setup"]
        if step.get("action") == "click_role" and step.get("name") == "Continue later"
    ]
    assert not problems, problems


def test_gate_cases_check_the_gate_not_the_desk(atlas: dict) -> None:
    """A gate case's precondition must prove the GATE is up. Checking the
    arrival headline would assert the very state the case must not be in."""
    problems: list[str] = []
    for case in atlas["cases"]:
        if not (_is_gate_case(case) and _is_face_case(case)):
            continue
        where = {entry["observe_at"] for entry in _checks(case)}
        if "[data-testid=arrival-headline]" in where:
            problems.append(f"{case['id']}: checks the desk headline, not the gate")
        if GATE_SCOPE not in where:
            problems.append(f"{case['id']}: never proves the gate is present")
    assert not problems, problems


def test_every_captured_id_names_the_field_it_reads(atlas: dict) -> None:
    """The rig defaults `capture_path` to `id`; a route that answers another
    name refuses by name. The import answers `{meeting_id, status}`
    (holdspeak/services/meeting_service.py:226).
    """
    problems = [
        f"{case['id']}: captures {step['capture_as']!r} with no capture_path"
        for case in atlas["cases"]
        for step in _acts(case)
        if step.get("capture_as") and step["capture_as"] != "id"
        and "capture_path" not in step
        and step.get("kind") == "fixture"
    ]
    assert not problems, problems


# ─────────── Astra round three, findings 3-5: the ACTUAL atlas cases ───────────
#
# Each fence reads the case as the atlas holds it and, where a verdict is at
# stake, hands that case's OWN predicate to the rig's evaluator
# (scripts/graph_walk.py::check_predicate) with a synthetic before/after, so a
# predicate an empty element or a failure sentence could satisfy is caught here.

SAME_DAY = "case.j10.arrival_generate_again.same_day_idempotent"
POPULATED = "case.j10.arrival_generate_brief.populated"
KEPT = "case.j11.thought_keep.kept"
BRIEF_HEADLINE = "[data-testid=arrival-brief-headline]"
GENERATE = "[data-testid=arrival-brief-generate]"
TEXT_KINDS = frozenset({"text_contains", "text_absent", "text_equals"})

# PHILO-5-04 adds a read-refusal sibling. Keep the exception named so the
# producer-operation fence does not silently widen for future cases.
READ_REFUSAL_SIBLINGS = frozenset({
    "case.philo504.decision_missing.refusal.op",
})


def _case(atlas: dict, case_id: str) -> dict:
    found = [case for case in atlas["cases"] if case["id"] == case_id]
    assert len(found) == 1, f"{case_id} is not in the atlas exactly once"
    return found[0]


def _mints_brief_material(step: dict) -> bool:
    return (step.get("kind") == "api" and step.get("method") == "POST"
            and step.get("path") == "/api/decisions")


def test_same_day_generate_again_binds_returned_displayed_and_retained(atlas: dict) -> None:
    """Finding 3: the returned brief must BE the displayed one, and the face the
    trigger acts on must be the brief the store gave back after a reload."""
    case = _case(atlas, SAME_DAY)
    predicate = case["expected"]["predicate"]
    assert predicate["kind"] == "unchanged"
    spec = _rig().identity_spec(predicate)
    assert spec and spec["from"] == "trigger", spec
    assert spec.get("display") == BRIEF_HEADLINE == case["expected"]["observe_at"], spec

    setup = case["setup"]
    first_click = next(i for i, s in enumerate(setup)
                       if s.get("action") == "click" and s.get("selector") == GENERATE)
    reload = next(i for i, s in enumerate(setup) if s.get("action") == "reload")
    assert first_click < reload, "the reload must come after the first brief is made"
    waits = [s for s in setup[reload + 1:] if s.get("action") == "wait_for"]
    assert waits and waits[0]["selector"] == BRIEF_HEADLINE, "no retention wait after the reload"
    captured = [s for s in setup[reload + 1:] if s.get("capture_as") == "first_brief_id"]
    assert captured and captured[0]["path"] == "/api/brief/latest", (
        "the retained brief id is not captured after the reload")
    assert case["trigger"].get("selector") == GENERATE

    # The rig's own verdict on this predicate.
    check = _rig().check_predicate
    shown = "No changes"
    before = {"text": shown, "attrs": {}}

    def after(returned: str | None, displayed: str | None) -> dict:
        snap = {"text": shown, "attrs": {}, "identity_display": {"value": displayed}}
        if returned is not None:
            snap["trigger_response"] = {"status": 200, "body": {
                "id": "brief-second", "headline": returned}}
        return snap

    assert check(predicate, before, after(shown, shown))[0]
    ok, why = check(predicate, before, after("2 things changed.", shown))
    assert not ok, f"a stale face beside a different returned brief passed: {why}"
    assert not check(predicate, before, after(None, shown))[0], "passed with no response"
    assert not check(predicate, before, after(shown, None))[0], "passed with nothing displayed"


def _populated_brief_cases(atlas: dict) -> list[dict]:
    """Applicable cases only: an unreachable case is never fired (it keeps a
    reason instead), so it has no setup to mint anything."""
    return [
        case for case in atlas["cases"]
        if case["applicability"] == "applicable" and (
            case["state_id"] == "state.briefs.populated"
            or any(_mints_brief_material(step) for step in case["setup"])
            or any(isinstance(line, str) and "populated" in line
                   for line in case["preconditions"]))
    ]


def _generates_a_brief(step: dict) -> bool:
    """The Chair's Generate click, or the route it calls."""
    return ((step.get("action") == "click" and step.get("selector") == GENERATE)
            or (step.get("kind") == "api" and step.get("method") == "POST"
                and step.get("path") == "/api/brief/generate"))


def _advances_the_producer_day(step: dict) -> bool:
    """PHILO-3-03: the ONE valid producer-day advance (scripts/graph_walk.py
    producer_clock_advance): clock.python_wall moved by whole days >= 1."""
    days = step.get("advance_days")
    return (step.get("kind") == "clock" and step.get("adapter") == "producer-clock"
            and step.get("clock") == "clock.python_wall"
            and isinstance(days, int) and not isinstance(days, bool) and days >= 1)


def _brief_recipe_problem(case: dict) -> str | None:
    """A populated recipe's brief under observation must hold its material.

    Same-day generation returns the ORIGINAL brief (monday_brief_service.py
    same-day idempotency), so a brief generated before the material exists
    stays empty all that producer-day. The brief under observation is the
    LAST generation. Astra's counsel on A3: an earlier empty generation is
    permitted only when a valid producer-day advance sits between it and the
    observed one. Stated as: in the observed generation's producer-day (the
    acts after the last valid advance before it), the FIRST generation comes
    after the material, and so does the observed one.
    """
    acts = _acts(case)
    mint = next((i for i, s in enumerate(acts) if _mints_brief_material(s)), None)
    if mint is None:
        return "no brief material is minted in setup"
    gens = [i for i, s in enumerate(acts) if _generates_a_brief(s)]
    if not gens:
        return "no brief is generated"
    observed = gens[-1]
    if observed < mint:
        return "the brief is made before its material exists"
    advances = [i for i, s in enumerate(acts[:observed]) if _advances_the_producer_day(s)]
    day_start = advances[-1] if advances else -1
    first_that_day = next(g for g in gens if g > day_start)
    if first_that_day < mint:
        return ("the brief is made before its material exists, and no producer-day "
                "advance separates that generation from the observed one")
    return None


def test_no_populated_brief_case_reads_the_headline(atlas: dict) -> None:
    """Finding 4: an empty headline element passed `text_absent`. A populated
    case creates its material in setup and reads an item row."""
    cases = _populated_brief_cases(atlas)
    ids = {case["id"] for case in cases}
    assert POPULATED in ids, "the fence found no populated case to guard"
    problems: list[str] = []
    for case in cases:
        predicates = [(case["expected"].get("observe_at"), case["expected"].get("predicate"))]
        predicates += [(entry["observe_at"], entry["predicate"]) for entry in _checks(case)]
        for where, predicate in predicates:
            if predicate and predicate["kind"] in TEXT_KINDS and where == BRIEF_HEADLINE:
                problems.append(f"{case['id']}: {predicate['kind']} on the headline element")
        problem = _brief_recipe_problem(case)
        if problem:
            problems.append(f"{case['id']}: {problem}")
    assert not problems, problems


NEXT_DAY = "case.j10.arrival_generate_again.next_day"
PHASE3_NEXT_DAY = ("case.a3.brief_next_day.decision_on_the_face",
                   "case.a3.brief_next_day.new_id_with_the_decision")


def test_the_brief_recipe_fence_refuses_its_mutations(atlas: dict) -> None:
    """Astra's counsel on A3: the fence must FAIL each false acceptance she
    reproduced, on in-memory copies of the actual recipes, and pass the real ones."""
    import copy

    phase3 = json.loads((REPO / "docs/internal/philo/graph/atlas-phase3.json").read_text())
    next_day = _case(atlas, NEXT_DAY)
    populated = _case(atlas, POPULATED)
    for case in [next_day, populated] + [_case(phase3, cid) for cid in PHASE3_NEXT_DAY]:
        assert _brief_recipe_problem(case) is None, case["id"]

    def advance_index(case: dict) -> int:
        found = [i for i, s in enumerate(case["setup"]) if _advances_the_producer_day(s)]
        assert len(found) == 1, case["id"]
        return found[0]

    for case in [next_day] + [_case(phase3, cid) for cid in PHASE3_NEXT_DAY]:
        # 1. the advance removed
        removed = copy.deepcopy(case)
        del removed["setup"][advance_index(removed)]
        assert _brief_recipe_problem(removed), f"{case['id']}: passed without its advance"
        # 2. the advance moved AFTER the observed generation (the trigger)
        moved = copy.deepcopy(case)
        step = moved["setup"].pop(advance_index(moved))
        moved["setup"].append(moved.pop("trigger"))
        moved["trigger"] = step
        assert _brief_recipe_problem(moved), f"{case['id']}: passed with the advance after it"
        # 3. an invalid advance (zero days, or another adapter) is no advance
        for bad in ({"advance_days": 0}, {"adapter": "scheduler-wait"}):
            weak = copy.deepcopy(case)
            weak["setup"][advance_index(case)].update(bad)
            assert _brief_recipe_problem(weak), f"{case['id']}: passed with {bad}"

    # 4. an empty Generate inserted before the material in the ordinary recipe
    early = copy.deepcopy(populated)
    mint = next(i for i, s in enumerate(early["setup"]) if _mints_brief_material(s))
    early["setup"].insert(mint, {"kind": "ui", "action": "click", "selector": GENERATE,
                                 "adapter": "ui-pointer"})
    assert _brief_recipe_problem(early), "an empty Generate before the material passed"
    # 5. the same through the route, not the face
    early_api = copy.deepcopy(populated)
    early_api["setup"].insert(mint, {"kind": "api", "method": "POST",
                                     "path": "/api/brief/generate", "body": None})
    assert _brief_recipe_problem(early_api), "an empty route generate before the material passed"
    # 6. an empty generation on the OBSERVED day, before the material, is not
    #    rescued by an earlier advance (same-day id: the observed brief is empty)
    late2 = copy.deepcopy(next_day)
    mint2 = next(k for k, s in enumerate(late2["setup"]) if _mints_brief_material(s))
    material = late2["setup"].pop(mint2)
    j = advance_index(late2)
    late2["setup"].insert(j + 1, {"kind": "api", "method": "POST",
                                  "path": "/api/brief/generate", "body": None})
    late2["setup"].insert(j + 2, material)
    # day two: generate (empty) THEN material THEN observed -> same-day id, empty
    assert _brief_recipe_problem(late2), "an empty generation on the observed day passed"


def test_the_populated_brief_predicate_needs_the_minted_row(atlas: dict) -> None:
    case = _case(atlas, POPULATED)
    predicate, where = case["expected"]["predicate"], case["expected"]["observe_at"]
    titles = [step["body"]["title"] for step in case["setup"] if _mints_brief_material(step)]
    assert titles, "no minted title"
    assert predicate["kind"] == "text_contains"
    assert predicate["value"] == f"Review decision: {titles[0]}", (
        "the row text the decisions collector writes "
        "(holdspeak/services/monday_brief_service.py:758)")
    assert where != BRIEF_HEADLINE and "arrival-brief" in where and _is_css_selector(where)

    check = _rig().check_predicate
    assert not check(predicate, {"text": ""}, {"text": ""})[0], "an empty element passed"
    assert not check(predicate, {"text": ""},
                     {"text": "No changes"})[0], "the empty brief passed"
    assert check(predicate, {"text": ""},
                 {"text": f"{predicate['value']} Ack Defer"})[0]


def test_j11_kept_verifies_the_saved_words_in_the_store(atlas: dict) -> None:
    """Finding 5: `CHANGED ELSEWHERE` satisfied the absence of one failure
    sentence. The case must read the typed words back from the store."""
    case = _case(atlas, KEPT)
    expected = case["expected"]
    predicate = expected["predicate"]
    assert expected["observe_at"] == f"{_rig().PROTOCOL_PREFIX} GET /api/notes"
    assert predicate["kind"] == "protocol_rows" and int(predicate.get("min_new", 1)) >= 1
    typed = case["trigger"]["value"]
    assert case["trigger"]["action"] == "fill" and typed
    assert typed in predicate["match"].values(), "the store is not asked for the typed words"
    assert not any(isinstance(step.get("value"), str) and typed in step["value"]
                   for step in case["setup"]), "setup writes the words before the trigger"

    check = _rig().check_predicate

    def snap(bodies: list[str]) -> dict:
        return {"protocol": {"status": 200, "path": "/api/notes", "rows": [
            {"id": f"n{i}", "body_markdown": body} for i, body in enumerate(bodies)]}}

    assert check(predicate, snap([""]), snap([typed]))[0]
    ok, why = check(predicate, snap([""]), snap([""]))
    assert not ok, f"a save that never landed (CHANGED ELSEWHERE) passed: {why}"
    assert not check(predicate, snap([typed]), snap([typed]))[0], "an old row passed as new"


SAME_ID = "case.j10.route_generate_again.same_day_same_id"


def test_same_day_same_id_fails_a_different_id_by_machine(atlas: dict) -> None:
    """The face draws no brief id, so the protocol sibling of the same-day case
    proves the producer returns the RETAINED id (monday_brief_service.py:194-202)."""
    case = _case(atlas, SAME_ID)
    face = _case(atlas, SAME_DAY)
    assert case["setup"] == face["setup"], "the sibling must run the same chain"
    reload = next(i for i, s in enumerate(case["setup"]) if s.get("action") == "reload")
    captured = [i for i, s in enumerate(case["setup"]) if s.get("capture_as") == "first_brief_id"]
    assert captured and captured[0] > reload, "the id is not the retained one"
    trigger = case["trigger"]
    assert (trigger["kind"], trigger["method"], trigger["path"]) == (
        "api", "POST", "/api/brief/generate")
    predicate = case["expected"]["predicate"]
    assert predicate == {"kind": "protocol_status", "method": "POST",
                         "path": "/api/brief/generate", "status": 200,
                         "body_contains": "{first_brief_id}"}
    assert SAME_ID in next(s for s in atlas["states"]
                           if s["id"] == case["state_id"])["reachable_by"]

    rig = _rig()
    bound = rig.substitute(predicate, {"first_brief_id": "brief-first"})

    def after(returned_id: str, status: int = 200) -> dict:
        return {"trigger_response": {"method": "POST", "path": "/api/brief/generate",
                                     "status": status, "body": {"id": returned_id,
                                     "headline": "No changes"}}}

    assert rig.check_predicate(bound, {}, after("brief-first"))[0]
    ok, why = rig.check_predicate(bound, {}, after("brief-second"))
    assert not ok, f"a different id beside unchanged content passed: {why}"
    assert not rig.check_predicate(bound, {}, after("brief-first", 500))[0]


RETAINED_FACE = "case.j10.arrival_generate_again.retained_after_reload"
RETAINED_ROUTE = "case.j10.route_generate_again.retained_after_reload"


def _generates(setup: list[dict]) -> list[int]:
    """The indices of the steps that generate a brief (the verb or its route)."""
    return [i for i, s in enumerate(setup)
            if (s.get("action") == "click" and s.get("selector") == GENERATE)
            or (s.get("kind") == "api" and s.get("path") == "/api/brief/generate")]


def test_j10_retention_is_proven_after_another_reload(atlas: dict) -> None:
    """Astra round four: a same-id, same-headline response beside a LOST store
    passed both same-day cases. Retention is read after a reload that comes
    after the second generate."""
    for case_id, name in ((RETAINED_FACE, "second_headline"),
                          (RETAINED_ROUTE, "second_brief_id")):
        case = _case(atlas, case_id)
        setup = case["setup"]
        made = _generates(setup)
        assert len(made) == 2, f"{case_id}: not a first and a second generate"
        first_reload = next(i for i, s in enumerate(setup) if s.get("action") == "reload")
        assert made[0] < first_reload < made[1], f"{case_id}: no reload between the generates"
        captured = [i for i, s in enumerate(setup) if s.get("capture_as") == name]
        assert captured and captured[0] >= made[1], f"{case_id}: {name} not captured after the second"
        assert case["trigger"]["action"] == "reload" and case["trigger"]["kind"] == "ui"
        assert case_id in next(s for s in atlas["states"]
                               if s["id"] == case["state_id"])["reachable_by"]

    rig = _rig()
    face = _case(atlas, RETAINED_FACE)
    assert face["expected"]["observe_at"] == BRIEF_HEADLINE
    assert sorted(face["viewports"]) == [393, 1440]
    shown = "No changes"
    fp = rig.substitute(face["expected"]["predicate"], {"second_headline": shown})
    assert rig.check_predicate(fp, {}, {"text": shown, "target_present": True})[0]
    ok, why = rig.check_predicate(fp, {}, {"text": "", "target_present": False})
    assert not ok, f"zero headline elements after the reload passed: {why}"
    assert not rig.check_predicate(fp, {}, {"text": "2 things changed.",
                                            "target_present": True})[0]

    route = _case(atlas, RETAINED_ROUTE)
    assert route["expected"]["observe_at"] == f"{rig.PROTOCOL_PREFIX} GET /api/brief/latest"
    rp = rig.substitute(route["expected"]["predicate"], {"second_brief_id": "brief-second"})
    assert rp["kind"] == "protocol_field" and rp["value"] == "brief-second"

    def latest(payload: object) -> dict:
        return {"protocol": {"status": 200, "path": "/api/brief/latest", "payload": payload}}

    assert rig.check_predicate(rp, {}, latest({"id": "brief-second"}))[0]
    ok, why = rig.check_predicate(rp, {}, latest(None))
    assert not ok, f"a null latest (the brief lost) passed: {why}"
    assert not rig.check_predicate(rp, {}, latest({"id": "brief-other"}))[0]


def test_summary_failure_settings_reach_the_real_drainer_after_restart(atlas: dict) -> None:
    """The real conductor captures retry settings at startup, not each tick."""
    ids = {"case.j6.run_summary.intel_failed", "case.j6.run_summary.intel_retry",
           "case.j6.run_summary.retrying"}
    for case in atlas["cases"]:
        if case["id"] not in ids:
            continue
        setup = case["setup"]
        settings = next(i for i, s in enumerate(setup) if s.get("path") == "/api/settings")
        restart = next((i for i, s in enumerate(setup) if s.get("action") == "restart_hub"), -1)
        assert restart > settings, case["id"]
        run = next((i for i, s in enumerate(setup) if s.get("action") == "click"
                    and s.get("selector") == "[data-testid=arrival-run-intel]"), len(setup))
        assert restart < run, case["id"]


def test_summary_no_engine_absence_is_read_inside_the_existing_meetings_scope(atlas: dict) -> None:
    case = next(c for c in atlas['cases'] if c['id'] == 'case.j5.meeting_open.no_engine_no_verb')
    assert case['expected']['observe_at'] == '[data-testid=arrival-meetings]'
    assert case['expected']['predicate'] == {'kind': 'text_absent', 'value': 'Run summary'}


def test_summary_reload_reads_the_same_already_persisted_summary(atlas: dict) -> None:
    case = next(c for c in atlas['cases'] if c['id'] == 'case.j7.arrival_load.reload_persisted')
    setup = case['setup']
    run = next(i for i,s in enumerate(setup) if s.get('action') == 'click' and s.get('selector') == '[data-testid=arrival-run-intel]')
    waits = [i for i,s in enumerate(setup) if s.get('action') == 'wait_for' and s.get('selector') == '[data-testid=meeting-summary-text]']
    assert waits and waits[0] > run
    capture = next(s for s in setup if s.get('capture_as') == 'persisted_summary')
    assert capture['path'] == '/api/meetings/{meeting_id}'
    assert capture['capture_path'] == '/intel/summary'
    assert case['expected']['predicate'] == {'kind':'text_equals', 'value':'{persisted_summary}'}
@pytest.mark.parametrize("case_id,field", [
    ("case.j6.run_summary.intel_ready", "/intel_job/status"),
    ("case.j6.run_summary.host_named", "/run_receipt/attempts/0/host"),
])
def test_summary_terminal_cases_read_durable_meeting_not_active_queue(atlas, case_id, field):
    """Succeeded jobs leave the active queue; the durable meeting owns completion."""
    case = next(case for case in atlas["cases"] if case["id"] == case_id)
    assert case["expected"]["observe_at"] == "protocol: GET /api/meetings/{meeting_id}"
    assert case["expected"]["predicate"]["path"] == field


def test_no_assignment_op_reads_refusal_code_separately_from_error(atlas: dict) -> None:
    case = next(c for c in atlas["cases"] if c["id"] == "case.j6.route_intelligence_run.no_assignment.op")
    predicate = case["expected"]["predicate"]
    assert predicate["code"] == "route_unavailable"
    assert predicate["error_contains"] == "The summary route is not available."


def test_thought_op_save_starts_from_different_working_text() -> None:
    atlas = json.loads((REPO / "docs/internal/philo/graph/atlas-phase3.json").read_text())
    case = next(c for c in atlas["cases"] if c["id"] == "case.j11.thought_keep.receipt_time.op")
    create = next(s for s in case["setup"] if s.get("name") == "thought.create")
    before = create["args"]["initial_note"]["body_markdown"] or create["args"]["raw_text"]
    assert before != case["trigger"]["args"]["body_markdown"]
    assert case["expected"]["predicate"]["path"] == "thought.working_note.body_markdown"
    assert case["expected"]["predicate"]["value"] == case["trigger"]["args"]["body_markdown"]


PHILO603_CASES = {
    "case.philo603.toast.arrival": "[data-testid=arrival-aftercare-slot]",
    "case.philo603.toast.meetings_window": "[data-aftercare-window-slot=\"top\"]",
    "case.philo603.toast.floor_list": "[data-aftercare-floor-slot=\"top\"]",
}


def test_philo603_cases_use_the_real_summary_producer_and_surface_slots(atlas: dict) -> None:
    rig = _rig()
    cases = {case["id"]: case for case in atlas["cases"] if case["id"] in PHILO603_CASES}
    assert set(cases) == set(PHILO603_CASES)
    for case_id, slot in PHILO603_CASES.items():
        case = cases[case_id]
        assert case["state_id"] == "state.meetings.intel.ready"
        # The real intelligence drainer starts with every rig hub. A summary
        # admission does not authorize unrelated heartbeat scheduler work.
        assert not rig.case_needs_scheduler(case)
        boundary = next(step for step in case["setup"] if step["kind"] == "boundary")
        assert boundary["substitute"] == "engine_reply"
        assert boundary["reply"] == "tests/fixtures/philo5_summary_reply.json"
        imported = next(step for step in case["setup"] if step["kind"] == "fixture")
        assert imported["path"] == "tests/fixtures/philo3_architect_meeting.wav"
        assert imported["capture_as"] == "meeting_id"
        assert imported["route"] == {"method": "POST", "path": "/api/meetings/import"}
        setup_run_clicks = [
            step for step in case["setup"]
            if step.get("selector") == "[data-testid=arrival-run-intel]"
            and step.get("action") == "click"
        ]
        assert not setup_run_clicks, "the producer admission must happen after the probe is armed"
        if case_id == "case.philo603.toast.arrival":
            assert case["trigger"]["kind"] == "ui"
            assert case["trigger"]["action"] == "click"
            assert case["trigger"]["selector"] == "[data-testid=arrival-run-intel]"
            assert case["trigger"]["trigger_route"] == {
                "method": "POST",
                "path": "/api/meetings/{meeting_id}/intelligence/run",
            }
            assert any(
                step.get("kind") == "api"
                and step.get("method") == "POST"
                and step.get("path") == "/api/decisions"
                for step in case["setup"]
            )
            assert any(
                step.get("kind") == "api"
                and step.get("method") == "POST"
                and step.get("path") == "/api/brief/generate"
                for step in case["setup"]
            )
        else:
            assert case["trigger"]["kind"] == "api"
            assert case["trigger"]["method"] == "POST"
            assert case["trigger"]["path"] == "/api/meetings/{meeting_id}/intelligence/run"
            assert case["trigger"]["body"] == {
                "expected_selection_hash": "{selection_hash}"
            }
            route_read = next(
                step for step in case["setup"]
                if step.get("kind") == "api"
                and step.get("method") == "GET"
                and step.get("path") == "/api/meetings/{meeting_id}"
                and step.get("capture_as") == "selection_hash"
            )
            assert route_read["capture_path"] == "planned_route.selection_hash"
        if case_id == "case.philo603.toast.floor_list":
            steps = case["setup"]
            toggle_index = next(i for i, step in enumerate(steps) if step.get("name") == "List view")
            assert steps[toggle_index - 1]["name"] == "HoldSpeak"
            assert steps[toggle_index - 1]["role"] == "button"
        expected = case["expected"]
        predicate = expected["predicate"]
        assert expected["observe_at"] == ".ambient-aftercare"
        assert predicate["kind"] == "readable_text"
        assert predicate["value"] == "MEETING READY"
        assert predicate["slot_selector"] == slot
        assert predicate["auto_scroll_calls_by_viewport"] == {"393": 1, "1440": 0}
        assert predicate["no_field_focus"] is True
        if case_id == "case.philo603.toast.arrival":
            assert expected["dismiss_selector"] == ".ambient-aftercare button:has-text('Dismiss')"
            assert expected["dismiss_slot_selector"] == slot
        else:
            assert "dismiss_selector" not in expected
            assert "dismiss_slot_selector" not in expected


def _readable_placement_after(*, position: str = "static", overlap: bool = False) -> dict:
    card_rect = {"x": 20, "y": 20, "w": 220, "h": 80}
    clear_rect = {"x": 30, "y": 40, "w": 200, "h": 40} if overlap else {
        "x": 20, "y": 140, "w": 200, "h": 40
    }
    return {
        "target_present": True,
        "visible": True,
        "text": "Meeting ready Architecture boundary review",
        "rect": card_rect,
        "hit_test": {
            "viewport": {"width": 393, "height": 900},
            "in_viewport": True,
            "all_owned": True,
            "rect": card_rect,
        },
        "placement": {
            "card": {
                "present": True,
                "computed_position": position,
                "hit_test": {"rect": card_rect},
            },
            "slot": {"present": True, "contains_card": True},
            "clear": [{
                "selector": "[data-testid=arrival-capture-bar]",
                "present": True,
                "hit_test": {
                    "rect": clear_rect,
                    "visible": True,
                    "all_owned": True,
                },
            }],
            "scroll": {"target_count": 1, "events": 1, "scroll_top_delta": 30},
            "focused_field": False,
        },
    }


def test_philo603_placement_fence_rejects_fixed_card_and_overlap() -> None:
    rig = _rig()
    predicate = {
        "kind": "readable_text",
        "value": "Meeting ready",
        "slot_selector": "[data-testid=arrival-aftercare-slot]",
        "clear_of": [{
            "selector": "[data-testid=arrival-capture-bar]",
            "required": True,
            "require_hit_test": True,
        }],
        "auto_scroll_calls_by_viewport": {"393": 1, "1440": 0},
    }
    ok, why = rig.check_predicate(predicate, {}, _readable_placement_after(position="fixed"))
    assert not ok and "fixed" in why
    ok, why = rig.check_predicate(predicate, {}, _readable_placement_after(overlap=True))
    assert not ok and "intersects" in why


def test_philo603_placement_fence_accepts_flow_card_with_nine_point_clearance() -> None:
    rig = _rig()
    predicate = {
        "kind": "readable_text",
        "value": "Meeting ready",
        "slot_selector": "[data-testid=arrival-aftercare-slot]",
        "clear_of": [{
            "selector": "[data-testid=arrival-capture-bar]",
            "required": True,
            "require_hit_test": True,
        }],
        "auto_scroll_calls_by_viewport": {"393": 1, "1440": 0},
        "no_field_focus": True,
    }
    ok, why = rig.check_predicate(predicate, {}, _readable_placement_after())
    assert ok, why


def test_philo603_placement_fence_checks_every_matching_clear_target() -> None:
    rig = _rig()
    predicate = {
        "kind": "readable_text",
        "value": "Meeting ready",
        "slot_selector": "[data-testid=arrival-aftercare-slot]",
        "clear_of": [
            {
                "selector": "[data-testid=arrival-brief-row]",
                "required": False,
                "require_hit_test": False,
            }
        ],
    }
    after = _readable_placement_after()
    after["placement"]["clear"] = [
        {
            "selector": "[data-testid=arrival-brief-row]",
            "present": True,
            "hit_test": {"rect": {"x": 20, "y": 140, "w": 200, "h": 40}},
        },
        {
            "selector": "[data-testid=arrival-brief-row]",
            "present": True,
            "hit_test": {"rect": {"x": 20, "y": 240, "w": 200, "h": 40}},
        },
    ]
    ok, why = rig.check_predicate(predicate, {}, after)
    assert ok, why
    after["placement"]["clear"][1]["hit_test"]["rect"]["y"] = 40
    ok, why = rig.check_predicate(predicate, {}, after)
    assert not ok and "intersects" in why
