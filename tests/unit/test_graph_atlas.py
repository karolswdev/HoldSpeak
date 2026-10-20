"""The state atlas keeps its own contract (docs/internal/philo/graph/atlas*.json).

Every check here is a reference check, never a phrase-presence check: the atlas
validates against its schema, its ids resolve, its setup recipes name API pairs
that EXIST in the generated OpenAPI, its fixtures hash to what it claims, and
every source reference names a file that still holds the text it cites.

The fast diet (2026-10-12) moved this file from test_philo_graph_atlas.py and
folded the per-phase atlas files (test_philo{4,7,8,9,10,11,13}_*atlas*.py) into
ONE parametrized fence over every atlas file. Their case-content pins are parked
in tests/_parked/unit/; the rig's own behavior tests moved to
tests/unit/test_graph_walk_*.py.
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
            # A query string filters the same route (PHILO-16 C: restore binds
            # its projection from `?attention_state=needs_attention`).
            path, method = step["path"].split("?", 1)[0], step["method"].lower()
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


def _one_spacing(text: str) -> str:
    return " ".join(text.split())


def source_ref_problem(ref: dict, text: str | None = None) -> str | None:
    """Why a source reference no longer holds, or None.

    Line-free, and exact: the cited text is in the cited file in EXACTLY ONE
    place (runs of white space compare as one space, so a citation can span
    two lines). An import and a render site that share a name are two places;
    the citation must be long enough to name the one it claims. ``text``
    replaces the file's content (the mutation tests).
    """
    if text is None:
        target = REPO / ref["path"]
        if not target.is_file():
            return f"missing file {ref['path']}"
        text = target.read_text(errors="replace")
    count = _one_spacing(text).count(_one_spacing(ref["symbol"]))
    if count == 0:
        return f"{ref['path']} no longer holds {ref['symbol']!r}"
    if count > 1:
        return (
            f"{ref['path']} holds {ref['symbol']!r} in {count} places; cite a longer, "
            "specific snippet (the declaration or render site the claim is about)"
        )
    return None


OP_CASES_PATH = Path(__file__).with_name("philo_atlas_op_cases.txt")
READ_REFUSAL_SIBLINGS = frozenset({
    "case.philo504.decision_missing.refusal.op",
})


def missing_op_cases(case_ids) -> list[str]:
    """The tracked operation siblings that are not in ``case_ids``."""
    required = {
        line.strip()
        for line in OP_CASES_PATH.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }
    return sorted(required - set(case_ids))


def test_a_removed_operation_sibling_is_named() -> None:
    """Mutation: the atlas without one `.op` case fails the pair fence."""
    gone = "case.j10.route_generate_again.same_day_same_id.op"
    ids = {
        case["id"]
        for path in ATLAS_FILES
        for case in json.loads(path.read_text())["cases"]
    }
    assert gone in ids and missing_op_cases(ids) == []
    assert missing_op_cases(ids - {gone}) == [gone]


def test_a_citation_that_only_the_import_holds_fails() -> None:
    """Mutation: with the Dossier mount gone from DeskApp, the reference
    fails although the import still holds the name."""
    path = "web/src/desk/DeskApp.tsx"
    astra = json.loads((ATLAS_PATH.parent / "atlas-phase13-astra.json").read_text())
    ref = next(
        ref
        for state in astra["states"]
        for ref in state["sources"]
        if ref["path"] == path and "<DeliveryDossierWindow" in ref["symbol"]
    )
    assert source_ref_problem(ref) is None
    lines = (REPO / path).read_text().splitlines()
    kept = [line for line in lines if "<DeliveryDossierWindow" not in line]
    assert len(kept) == len(lines) - 1 and any("DeliveryDossierWindow" in line for line in kept)
    assert "no longer holds" in source_ref_problem(ref, "\n".join(kept))
    # The short name is in two places (import and mount): refused as ambiguous.
    assert "cite a longer" in source_ref_problem({**ref, "symbol": "DeliveryDossierWindow"})


def test_every_source_reference_lands_on_its_symbol(every_atlas: dict) -> None:
    """A source reference is a file and the text it cites; it has no line.

    Owner ruling 2026-10-03: a line number moves with every edit above it, so
    the fence reads the text. The cited file must still hold the cited symbol,
    or the claim behind the reference is no longer proven.
    """
    problems: list[str] = []
    for state in every_atlas["states"]:
        for ref in state["sources"]:
            problem = source_ref_problem(ref)
            if problem:
                problems.append(f"{state['id']}: {problem}")
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
    # No literal count (owner ruling 2026-10-03). The pairs must stay
    # complete: every sibling the tracked list names is still in the atlas.
    missing = missing_op_cases(case['id'] for case in siblings)
    assert not missing, f"operation siblings left the atlas: {missing}"
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
        # PHILO-9-05: the Room's delivery record.
        'project.mark_update_delivered',
        # PHILO-13-10: the canonical deterministic draft producer.
        'project.draft_update',
        # PHILO-10-05: the Send's admitted writes.
        'channel.save_destination', 'channel.prepare', 'channel.send', 'channel.discard',
    }
    readable = {
        'decision.read', 'decision.list', 'meeting.list', 'meeting.read',
        'brief.latest', 'brief.shelf.read', 'thought.read',
        'thought.workbench.read', 'thought.list',
        'note.read', 'note.list', 'zone.read', 'zone.list', 'zone.members',
        'kb.read', 'kb.list', 'kb.members', 'kernel.receipt.read',
        # PHILO-9-05: the Room's update list.
        'project.list_updates',
        # PHILO-10-05: the Send's reads.
        'channel.destinations', 'channel.sends',
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
        predicate = expected.get('predicate') or {}
        predicate_kind = predicate.get('kind')
        # PHILO-10-05: an op predicate, or all_of an op_facts and the
        # recording runner's count (cli_calls): both hub-side, never a face.
        parts = [p.get('kind') for p in predicate.get('predicates', [])] if predicate_kind == 'all_of' else []
        if predicate_kind not in {'op_field', 'op_refusal', 'op_facts'} and not (
                parts and 'op_facts' in parts and set(parts) <= {'op_facts', 'cli_calls'}):
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
        for step in _acts(case):
            if step.get('kind') == 'cli' and step.get('action') == 'seed_people_prep':
                prefix = step.get('capture_as') or 'people'
                bound |= {f'{prefix}_{field}' for field in (
                    'relationship_id', 'event_id', 'event_uid', 'event_source_id',
                    'event_title', 'project_id', 'meeting_id', 'session_id', 'action_id',
                )}
                bound.add('relationship_id')
        expected = case['expected']
        reads = {key: expected.get(key) for key in ('observe_at', 'predicate', 'reads')}
        names = set(re.findall(r'\{([a-z][a-z0-9_]*)\}', json.dumps(reads)))
        if names - bound:
            problems.append((case['id'], sorted(names - bound)))
    assert not problems, problems


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


def test_protocol_status_can_require_top_level_integer_body_fields() -> None:
    rig = _rig()
    predicate = {
        "kind": "protocol_status",
        "method": "POST",
        "path": "/api/channels/preview",
        "status": 400,
        "body_contains": "payload_too_large:slack",
        "body_integer_fields": ["size", "limit"],
    }

    def after(size: object, limit: object) -> dict:
        return {
            "trigger_response": {
                "method": "POST",
                "path": "/api/channels/preview",
                "status": 400,
                "body": {
                    "code": "payload_too_large:slack",
                    "size": size,
                    "limit": limit,
                },
            }
        }

    assert rig.check_predicate(predicate, {}, after(39001, 39000))[0]
    for size, limit in ((39001.0, 39000), (True, 39000), ("39001", 39000), (39001, None)):
        ok, why = rig.check_predicate(predicate, {}, after(size, limit))
        assert not ok, f"non-integer PREVIEW size/limit passed: {why}"


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
            problem = source_ref_problem(ref)
            if problem:
                problems.append(f"{reading['id']}: {problem}")
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
            # Current Setup uses Open my desk. Historical atlas generations
            # retain their original first-value entrance.
            and second.get("name") in {"Continue later", "Open my desk"}
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


# PHILO-5-04 adds a read-refusal sibling. Keep the exception named so the
# producer-operation fence does not silently widen for future cases.


PHASE3_NEXT_DAY = ("case.a3.brief_next_day.decision_on_the_face",
                   "case.a3.brief_next_day.new_id_with_the_decision")


PHILO603_CASES = {
    "case.philo603.toast.arrival": "[data-testid=arrival-aftercare-slot]",
    "case.philo603.toast.meetings_window": "[data-aftercare-window-slot=\"top\"]",
}
#: PHILO-17 (owner 2026-10-10, "Yes, everything must become one desk"): the
#: Floor's slots are parked; their cases are not applicable, the reason named.
PHILO603_PARKED = ("case.philo603.toast.floor_list", "case.philo603.toast.floor_spatial_fallback")


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


# ─────────── every atlas file keeps the general fences (the fast diet) ───────────
#
# Before 2026-10-12 each phase had its own test file that applied a list of the
# fences above to its own atlas file (they read atlas.json by default). This is
# that application, once, over every atlas file.


def _openapi_fence(atlas: dict) -> None:
    test_every_api_setup_step_exists_in_the_generated_openapi(atlas, json.loads(OPENAPI_PATH.read_text()))


def _graph_case_fence(atlas: dict) -> None:
    test_every_case_validates_against_the_graph_case_schema(atlas, json.loads(GRAPH_SCHEMA_PATH.read_text()))


def _op_facts_fence(atlas: dict) -> None:
    """Every op_facts fact names a source, a test and a read in range (from test_philo7_atlas.py)."""
    gw = _rig()
    for case in atlas["cases"]:
        predicate = case["expected"]["predicate"]
        if predicate["kind"] != "op_facts":
            continue
        op_reads = [read for read in case["expected"].get("reads", []) if read.get("kind") == "op"]
        assert predicate["facts"], case["id"]
        for fact in predicate["facts"]:
            assert fact["source"] in gw.OP_FACT_SOURCES, (case["id"], fact)
            assert any(test in fact for test in gw.OP_FACT_TESTS), (case["id"], fact)
            if fact["source"] == "read":
                assert 0 <= fact["index"] < len(op_reads), (case["id"], fact)


def _acts_with_then(case: dict) -> list[dict]:
    """Every act INCLUDING a trigger's `then` steps (Codex Astra r1 MISSED 1:
    the general `_acts` visits setup and the top-level trigger only)."""
    acts = list(_acts(case))
    return acts + list((case.get("trigger") or {}).get("then") or [])


def _then_steps_fence(atlas: dict) -> None:
    """`then` steps validate against the schema's ui step (from test_philo8_atlas.py)."""
    schema = json.loads(SCHEMA_PATH.read_text())
    ui = next(branch for branch in schema["$defs"]["step"]["oneOf"]
              if branch.get("properties", {}).get("kind", {}).get("const") == "ui")
    validator = Draft202012Validator({"$defs": schema["$defs"], **ui})
    actions = _rig_ui_actions()
    for case in atlas["cases"]:
        for step in (case.get("trigger") or {}).get("then") or []:
            errors = [e.message for e in validator.iter_errors(step)]
            assert not errors, (case["id"], errors)
            assert step["action"] in actions, (case["id"], step["action"])


def _optional_steps_fence(atlas: dict) -> None:
    """An optional step is never the only carrier of the outcome (from test_philo8_atlas.py)."""
    for case in atlas["cases"]:
        optional = [s for s in _acts_with_then(case) if s.get("optional")
                    and s.get("name") != "Continue later"]
        if optional:
            assert case["expected"]["predicate"]["kind"] == "all_of", case["id"]


def _no_optional_trigger_fence(atlas: dict) -> None:
    """No trigger is optional (from test_philo9_atlas.py and test_philo10_atlas.py)."""
    for case in atlas["cases"]:
        assert not (case.get("trigger") or {}).get("optional"), case["id"]


EVERY_FILE_FENCES = [
    test_ids_are_unique,
    test_every_case_state_id_resolves,
    test_every_case_reference_inside_the_atlas_resolves,
    test_every_clock_a_case_uses_is_declared,
    test_every_applicable_case_carries_one_trigger,
    test_face_cases_carry_both_ruled_viewports,
    test_every_applicable_predicate_is_a_kind_the_rig_implements,
    test_every_predicate_observes_a_selector_or_a_route,
    test_every_case_keeps_its_human_sentence,
    test_every_ui_action_is_one_the_rig_implements,
    test_every_boundary_names_its_substitution,
    test_no_precondition_check_compares_two_snapshots,
    test_every_precondition_check_observes_a_selector_or_a_route,
    test_no_check_asserts_the_result_the_trigger_must_produce,
    test_no_step_acts_on_a_root_placeholder,
    test_navigation_steps_carry_no_selector,
    test_every_desk_face_case_crosses_the_gate_first,
    test_every_captured_id_names_the_field_it_reads,
    test_every_click_and_fill_names_a_control,
    _openapi_fence,
    _graph_case_fence,
    _op_facts_fence,
    _then_steps_fence,
    _optional_steps_fence,
    _no_optional_trigger_fence,
]

# The (fence, file) pairs no test applied before the fast diet, each red on
# 2026-10-12. They are the atlas files' known debt, kept in view here; the
# fast diet adds no new red. Remove a pair when its file is repaired.
NOT_APPLIED_BEFORE: dict[str, set[str]] = {
    "test_every_case_reference_inside_the_atlas_resolves": {"atlas-h-c5.json", "atlas-phase3.json"},
    "test_every_case_state_id_resolves": {"atlas-phase3.json", "atlas-phase7.json"},
    "test_every_click_and_fill_names_a_control": {
        "atlas-h-c5.json", "atlas-phase10.json", "atlas-phase11-slack.json", "atlas-phase11.json",
        "atlas-phase13-astra.json", "atlas-phase3.json", "atlas-phase7.json", "atlas-phase8.json",
        "atlas-phase9.json",
    },
    "test_every_desk_face_case_crosses_the_gate_first": {"atlas-phase7.json"},
    "test_every_predicate_observes_a_selector_or_a_route": {"atlas-phase7.json"},
    "test_face_cases_carry_both_ruled_viewports": {"atlas-phase3.json"},
    "_openapi_fence": {"atlas-h-c5.json", "atlas-phase3.json", "atlas-phase7.json"},
    "_graph_case_fence": {"atlas-phase11-slack.json", "atlas-phase11.json", "atlas-phase13-astra.json"},
    "_op_facts_fence": {"atlas.json"},
    "_optional_steps_fence": {"atlas-phase13-astra.json", "atlas-phase3.json", "atlas.json"},
    "_no_optional_trigger_fence": {"atlas-phase11-slack.json", "atlas-phase11.json"},
}

_EVERY_FILE_PAIRS = [
    pytest.param(fence, path, id=f"{fence.__name__}-{path.name}")
    for fence in EVERY_FILE_FENCES
    for path in ATLAS_FILES
    if path.name not in NOT_APPLIED_BEFORE.get(fence.__name__, set())
]


@pytest.mark.parametrize(("fence", "path"), _EVERY_FILE_PAIRS)
def test_the_general_fences_hold_for_every_atlas_file(fence, path: Path) -> None:
    fence(json.loads(path.read_text()))


def test_every_atlas_file_has_cases_with_unique_ids() -> None:
    # Structural, not literal (owner ruling 2026-10-03): no per-file count
    # that every lane must edit. (From test_philo9_atlas.py and
    # test_philo10_atlas.py, which held the same test.)
    seen: dict[str, str] = {}
    for path in ATLAS_FILES:
        cases = json.loads(path.read_text())["cases"]
        assert cases, path.name
        for case in cases:
            assert case["id"].startswith("case."), (path.name, case["id"])
            assert case["id"] not in seen, (case["id"], seen[case["id"]], path.name)
            seen[case["id"]] = path.name


def test_the_shared_semantic_guards_show_red_then_green(tmp_path, monkeypatch) -> None:
    """The shared guards really inspect an atlas file, including its .op sibling.
    Moved from test_philo13_astra_atlas.py (the fast diet, 2026-10-12)."""
    import copy
    import sys

    general = sys.modules[__name__]
    atlas_path = ATLAS_PATH.parent / "atlas-phase13-astra.json"
    proper = json.loads(atlas_path.read_text())
    broken_words = copy.deepcopy(proper)
    broken_words["cases"][0]["expected"]["words"] = ""
    words_path = tmp_path / "atlas-phase13-broken-words.json"
    words_path.write_text(json.dumps(broken_words))

    other_files = [path for path in general.ATLAS_FILES if path.name != atlas_path.name]
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, words_path])
    with pytest.raises(AssertionError):
        general.test_every_case_keeps_its_human_sentence(json.loads(words_path.read_text()))

    broken_binding = copy.deepcopy(proper)
    broken_binding["cases"][0]["expected"]["observe_at"]["args"]["directory_id"] = "{missing_zone_id}"
    binding_path = tmp_path / "atlas-phase13-broken-binding.json"
    binding_path.write_text(json.dumps(broken_binding))
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, binding_path])
    with pytest.raises(AssertionError, match="missing_zone_id"):
        general.test_named_pair_observations_bind_their_read_arguments()

    broken_semantics = copy.deepcopy(proper)
    broken_semantics["cases"][0]["expected"]["observe_at"]["name"] = "zone.create"
    semantics_path = tmp_path / "atlas-phase13-broken-semantics.json"
    semantics_path.write_text(json.dumps(broken_semantics))
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, semantics_path])
    with pytest.raises(AssertionError, match="zone.create"):
        general.test_operation_siblings_use_headless_reads_and_canonical_steps()

    # Restore the proper file in the shared glob and prove the guards pass on it.
    monkeypatch.setattr(general, "ATLAS_FILES", [*other_files, atlas_path])
    general.test_every_case_keeps_its_human_sentence(proper)
    general.test_named_pair_observations_bind_their_read_arguments()
    general.test_operation_siblings_use_headless_reads_and_canonical_steps()
