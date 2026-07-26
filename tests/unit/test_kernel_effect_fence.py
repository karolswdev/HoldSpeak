"""HS-106-03: make the effect census and broker density limits executable.

The census is deliberately an explicit AST table, not a call-graph guess.  It
counts static statements in the five ratified families.  One logical action can
therefore produce several sites.  When this fence fires, inspect the statement
and amend the Article XI debt register deliberately; never hide it by weakening
a rule.
"""

from __future__ import annotations

import ast
import fnmatch
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_REPO = Path(__file__).resolve().parents[2]
_SOURCE = _REPO / "holdspeak"
_KERNEL = _SOURCE / "kernel"
_LEDGER = _KERNEL / "effect_ledger.json"

FAMILY_TMUX = "tmux_transport"
FAMILY_TYPER = "text_typer"
FAMILY_SUBPROCESS = "subprocess"
FAMILY_EGRESS = "egress"
FAMILY_RAW_DESKTOP = "raw_desktop"
_FAMILIES = {
    FAMILY_TMUX,
    FAMILY_TYPER,
    FAMILY_SUBPROCESS,
    FAMILY_EGRESS,
    FAMILY_RAW_DESKTOP,
}
_STATUSES = {"covered", "bypass", "mixed", "dormant"}

# The broker is intended to stay smaller than one Phase-79 concern module.
# Raising this number is an architecture decision; the ordinary response to a
# failure is to carve a typed concern module, not grow the broker.
_BROKER_MODULE_BUDGET = 300
_BROKER_INIT_BUDGET = 60


@dataclass(frozen=True)
class CallRule:
    """One explicit effect-family syntax rule.

    ``path_globs`` and ``scopes`` narrow indirect calls whose target name alone
    is not meaningful (the two ``actual(...)`` boundaries and coder steering's
    injected ``send(...)``).  Direct APIs remain broad so a newly introduced
    ambient call cannot hide in a new module.
    """

    family: str
    targets: tuple[str, ...]
    full_suffixes: tuple[str, ...] = ()
    path_globs: tuple[str, ...] = ("holdspeak/*.py", "holdspeak/**/*.py")
    scopes: tuple[str, ...] = ()

    def matches(self, *, path: str, scope: str, target: str, full: str) -> bool:
        if not any(fnmatch.fnmatchcase(path, pattern) for pattern in self.path_globs):
            return False
        if self.scopes and scope not in self.scopes:
            return False
        return target in self.targets and (
            not self.full_suffixes
            or any(full == suffix or full.endswith(f".{suffix}") for suffix in self.full_suffixes)
        )


# Ordering is classification precedence.  The AppleScript process invocation is
# a raw desktop primitive, not one of the plugin/connector subprocess rows.
_CALL_RULES = (
    CallRule(
        FAMILY_RAW_DESKTOP,
        ("run", "Popen", "call", "check_call", "check_output"),
        path_globs=("holdspeak/*.py", "holdspeak/**/*.py"),
    ),
    CallRule(
        FAMILY_RAW_DESKTOP,
        ("copy",),
        full_suffixes=("pyperclip.copy",),
    ),
    CallRule(
        FAMILY_RAW_DESKTOP,
        ("press", "release", "type"),
        path_globs=("holdspeak/typer.py",),
        scopes=(
            "TextTyper._paste_text",
            "TextTyper._type_text_slowly",
            "TextTyper._press_enter",
        ),
    ),
    CallRule(
        FAMILY_RAW_DESKTOP,
        ("write", "press", "hotkey", "keyDown", "keyUp"),
        full_suffixes=(
            "pyautogui.write",
            "pyautogui.press",
            "pyautogui.hotkey",
            "pyautogui.keyDown",
            "pyautogui.keyUp",
        ),
    ),
    CallRule(
        FAMILY_RAW_DESKTOP,
        ("CGEventPost", "AXUIElementSetAttributeValue"),
    ),
    CallRule(
        FAMILY_TMUX,
        ("send_text_to_pane", "send_keys_to_pane"),
    ),
    CallRule(
        FAMILY_TMUX,
        ("send",),
        path_globs=("holdspeak/coder_steering.py",),
        scopes=("deliver", "deliver_keys"),
    ),
    CallRule(FAMILY_TYPER, ("type_text",)),
    CallRule(FAMILY_SUBPROCESS, ("run_subprocess",)),
    CallRule(
        FAMILY_SUBPROCESS,
        ("actual",),
        path_globs=("holdspeak/connector_runtime.py",),
        scopes=("PermissionGate.run_subprocess",),
    ),
    CallRule(
        FAMILY_SUBPROCESS,
        ("run", "Popen", "call", "check_call", "check_output"),
        full_suffixes=(
            "subprocess.run",
            "subprocess.Popen",
            "subprocess.call",
            "subprocess.check_call",
            "subprocess.check_output",
        ),
    ),
    CallRule(FAMILY_EGRESS, ("open_outbound_socket",)),
    CallRule(
        FAMILY_EGRESS,
        ("actual",),
        path_globs=("holdspeak/connector_runtime.py",),
        scopes=("PermissionGate.open_outbound_socket",),
    ),
    CallRule(
        FAMILY_EGRESS,
        ("urlopen", "create_connection"),
        full_suffixes=("urlopen", "socket.create_connection"),
    ),
    CallRule(
        FAMILY_EGRESS,
        ("create",),
        full_suffixes=("chat.completions.create", "responses.create"),
    ),
)

# These are the census's inspected, deliberate scope exclusions.  Keeping them
# explicit means a newly added process or network statement fails even when it
# lands outside today's plugin/connector denominator.  Selectors are line-
# independent so harmless edits above a call do not create false drift.
_EXCLUDED_CALLS: dict[tuple[str, str, str, int], str] = {
    ("holdspeak/tmux_transport.py", "_run_tmux", "run", 1): "raw tmux implementation traced from T01-T04",
    ("holdspeak/coder_steering.py", "_default_runner", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/target_profile.py", "_collect_macos_hints", "run", 1): "read-only frontmost-app probe",
    ("holdspeak/target_profile.py", "_run_text", "run", 1): "read-only Linux target-profile probe",
    ("holdspeak/meeting_recorder.py", "MeetingRecorder._start_system_ffmpeg", "Popen", 1): "process site outside plugin/connector scope",
    ("holdspeak/audio_devices.py", "_pactl_stdout", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/meeting_import.py", "_decode_with_ffmpeg", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/agent_summarizer.py", "summarize_agent_session", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/delivery/dossiers.py", "_default_runner", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/delivery/factory_launch.py", "_default_git_runner", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/delivery/pr_receipts.py", "_default_runner", "run", 1): "process site outside plugin/connector scope, added after census snapshot",
    ("holdspeak/delivery/registry.py", "_default_git_runner", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/delivery/collector.py", "_default_runner", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/agent_context/hooks.py", "_read_tmux_display", "run", 1): "process site outside plugin/connector scope",
    ("holdspeak/coder_steering_relay.py", "_default_opener", "urlopen", 1): "placement transport, not a second terminal-input effect",
    ("holdspeak/commands/node_serve.py", "_default_http_post", "urlopen", 1): "delivery-node operation-state transport",
    ("holdspeak/commands/mesh_serve.py", "_default_http_post", "urlopen", 1): "inference-mesh operation-state transport",
    ("holdspeak/commands/doctor.py", "_check_meeting_intel_cloud_preflight", "urlopen", 1): "setup/diagnostic network probe",
    ("holdspeak/setup_runtime.py", "_default_http_get", "urlopen", 1): "setup/diagnostic network probe",
    ("holdspeak/setup_runtime.py", "_default_http_json", "urlopen", 1): "setup/diagnostic network probe",
    ("holdspeak/coder_gate.py", "_send", "urlopen", 1): "loopback gate protocol transport outside census egress scope",
}

_SKIP_DIRS = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "assets",
    "generated",
    "static",
    "vendor",
    "vendored",
}


@dataclass(frozen=True)
class EffectSite:
    family: str
    path: str
    line: int
    scope: str
    target: str
    ordinal: int

    @property
    def key(self) -> tuple[str, str, str, int]:
        return (self.path, self.scope, self.target, self.ordinal)

    @property
    def label(self) -> str:
        return f"{self.path}:{self.line} [{self.family}]"


class _EffectVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.scope_stack: list[str] = []
        self.ordinals: defaultdict[tuple[str, str], int] = defaultdict(int)
        self.sites: list[EffectSite] = []

    @property
    def scope(self) -> str:
        return ".".join(self.scope_stack) or "<module>"

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.scope_stack.append(node.name)
        self.generic_visit(node)
        self.scope_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        target = _call_target(node.func)
        full = _dotted_expr(node.func)
        ordinal_key = (self.scope, target)
        self.ordinals[ordinal_key] += 1
        ordinal = self.ordinals[ordinal_key]

        family = _classify_call(
            path=self.relative_path,
            scope=self.scope,
            target=target,
            full=full,
            node=node,
        )
        if family is not None:
            site = EffectSite(
                family=family,
                path=self.relative_path,
                line=node.lineno,
                scope=self.scope,
                target=target,
                ordinal=ordinal,
            )
            if site.key not in _EXCLUDED_CALLS:
                self.sites.append(site)
        self.generic_visit(node)


def _call_target(function: ast.expr) -> str:
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        return function.attr
    return type(function).__name__


def _dotted_expr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _dotted_expr(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    if isinstance(node, ast.Call):
        return f"{_dotted_expr(node.func)}()"
    return ""


def _literal_strings(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }


def _classify_call(
    *, path: str, scope: str, target: str, full: str, node: ast.Call
) -> str | None:
    process_targets = {"run", "Popen", "call", "check_call", "check_output"}
    if target in process_targets and any(
        "osascript" in value.lower() for value in _literal_strings(node)
    ):
        return FAMILY_RAW_DESKTOP

    # The first raw-desktop rule is intentionally restricted here: ordinary
    # subprocess calls continue into the subprocess rule below.
    for index, rule in enumerate(_CALL_RULES):
        if index == 0:
            continue
        if rule.matches(path=path, scope=scope, target=target, full=full):
            return rule.family
    return None


def _classify_source(relative_path: str, source: str) -> list[EffectSite]:
    tree = ast.parse(source, filename=relative_path)
    visitor = _EffectVisitor(relative_path)
    visitor.visit(tree)
    return visitor.sites


def _source_paths() -> list[Path]:
    return sorted(
        path
        for path in _SOURCE.rglob("*.py")
        if not any(part in _SKIP_DIRS for part in path.relative_to(_SOURCE).parts)
    )


def _walk_effect_sites() -> list[EffectSite]:
    sites: list[EffectSite] = []
    for path in _source_paths():
        relative = path.relative_to(_REPO).as_posix()
        sites.extend(_classify_source(relative, path.read_text(encoding="utf-8")))
    return sorted(sites, key=lambda site: (site.path, site.line, site.family))


def _load_ledger() -> dict[str, Any]:
    return json.loads(_LEDGER.read_text(encoding="utf-8"))


def _ledger_key(entry: dict[str, Any]) -> tuple[str, str, str, int]:
    selector = entry["selector"]
    return (
        entry["path"],
        selector["scope"],
        selector["target"],
        selector["ordinal"],
    )


def test_effect_family_classifier_fixtures() -> None:
    fixtures = (
        ("holdspeak/scratch.py", "send_text_to_pane(pane='p', text='x')", FAMILY_TMUX),
        ("holdspeak/scratch.py", "typer.type_text('x')", FAMILY_TYPER),
        ("holdspeak/scratch.py", "import subprocess\nsubprocess.run(['true'])", FAMILY_SUBPROCESS),
        ("holdspeak/scratch.py", "import urllib.request\nurllib.request.urlopen('https://example.test')", FAMILY_EGRESS),
        ("holdspeak/scratch.py", "import pyperclip\npyperclip.copy('x')", FAMILY_RAW_DESKTOP),
    )
    for path, source, expected in fixtures:
        found = _classify_source(path, source)
        assert [site.family for site in found] == [expected], (
            f"fixture for {expected} classified as "
            f"{[site.family for site in found]}"
        )


def test_effect_ledger_is_complete_and_current() -> None:
    ledger = _load_ledger()
    entries = ledger["sites"]
    actual = _walk_effect_sites()

    ledger_by_key = {_ledger_key(entry): entry for entry in entries}
    actual_by_key = {site.key: site for site in actual}
    assert len(ledger_by_key) == len(entries), "effect ledger contains duplicate selectors"
    assert len(actual_by_key) == len(actual), "source walker produced duplicate selectors"

    unledgered = [actual_by_key[key] for key in actual_by_key.keys() - ledger_by_key.keys()]
    missing = [ledger_by_key[key] for key in ledger_by_key.keys() - actual_by_key.keys()]
    family_mismatches = [
        (ledger_by_key[key], actual_by_key[key])
        for key in ledger_by_key.keys() & actual_by_key.keys()
        if ledger_by_key[key]["family"] != actual_by_key[key].family
    ]

    failures = [
        f"UNLEDGERED effect site: {site.label} "
        f"scope={site.scope} target={site.target} ordinal={site.ordinal}"
        for site in sorted(unledgered, key=lambda item: (item.path, item.line))
    ]
    failures.extend(
        f"MISSING ledgered effect site: {entry['id']} "
        f"{entry['path']}:{entry['census_line']} [{entry['family']}] "
        f"selector={entry['selector']}"
        for entry in sorted(missing, key=lambda item: item["id"])
    )
    failures.extend(
        f"FAMILY CHANGED for {entry['id']}: ledger={entry['family']} "
        f"source={site.family} at {site.path}:{site.line}"
        for entry, site in family_mismatches
    )
    assert not failures, "effect census drift:\n  " + "\n  ".join(failures)


def test_effect_ledger_asserts_the_ratified_40_4_36_counts() -> None:
    ledger = _load_ledger()
    entries = ledger["sites"]
    expected = ledger["expected"]

    families = Counter(entry["family"] for entry in entries)
    statuses = Counter(entry["status"] for entry in entries)
    covered = statuses["covered"]
    not_covered = len(entries) - covered

    assert set(families) == _FAMILIES
    assert set(statuses) <= _STATUSES
    assert len(entries) == expected["total"] == 40, (
        f"effect census must state 40 total sites, found {len(entries)}"
    )
    assert covered == expected["covered"] == 4, (
        f"effect census must state 4 covered sites, found {covered}"
    )
    assert not_covered == expected["not_covered"] == 36, (
        f"effect census must state 36 not-covered sites, found {not_covered}"
    )
    assert dict(families) == expected["families"] == {
        FAMILY_TMUX: 4,
        FAMILY_TYPER: 8,
        FAMILY_SUBPROCESS: 5,
        FAMILY_EGRESS: 13,
        FAMILY_RAW_DESKTOP: 10,
    }, f"effect family breakdown changed: {dict(families)}"
    assert all(entry["reason"].strip() for entry in entries)
    assert len({entry["id"] for entry in entries}) == 40
    assert "No agent principal may reach" in ledger["legal_effect"]


def _broker_modules() -> list[Path]:
    return sorted(_KERNEL.glob("*.py"))


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def test_kernel_broker_modules_stay_within_line_budget() -> None:
    offenders: list[str] = []
    for path in _broker_modules():
        budget = _BROKER_INIT_BUDGET if path.name == "__init__.py" else _BROKER_MODULE_BUDGET
        lines = _line_count(path)
        if lines > budget:
            offenders.append(
                f"kernel broker module over {budget}-line budget: "
                f"{path.relative_to(_REPO)}: {lines} lines"
            )
    assert not offenders, (
        "broker density guard failed — carve a typed concern module; don't bump "
        "the budget:\n  " + "\n  ".join(offenders)
    )


_DRIVER_WORDS = re.compile(
    r"driver|terminal|actuator|inference|operation\.(?:type|kind|family)",
    re.IGNORECASE,
)
_DRIVER_CLASS = re.compile(
    r"(?:Terminal|Actuator|Inference)\w*Driver|\w+Driver|"
    r"ProcessInput\w*|DesktopType\w*|External\w*Operation"
)
_DRIVER_LITERALS = {
    "terminal",
    "terminal_input",
    "actuator",
    "actuator_egress",
    "inference",
    "inference_run",
}
_DRIVER_OPERATION_PREFIXES = ("process.", "desktop.", "external.", "inference.")


def _source_mentions_driver_dispatch(node: ast.AST) -> bool:
    rendered = ast.unparse(node)
    if _DRIVER_WORDS.search(rendered) or _DRIVER_CLASS.search(rendered):
        return True
    literals = {value.lower() for value in _literal_strings(node)}
    return bool(literals & _DRIVER_LITERALS) or any(
        value.startswith(_DRIVER_OPERATION_PREFIXES) for value in literals
    )


def _driver_conditional_findings(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    try:
        relative = path.relative_to(_REPO).as_posix()
    except ValueError:
        relative = path.as_posix()
    findings: set[tuple[int, str]] = set()

    for node in ast.walk(tree):
        kind: str | None = None
        subject: ast.AST | None = None
        if isinstance(node, ast.If):
            kind, subject = "if dispatch", node.test
        elif isinstance(node, ast.IfExp):
            kind, subject = "ternary dispatch", node.test
        elif isinstance(node, ast.Match):
            kind, subject = "match dispatch", node
        elif isinstance(node, ast.Subscript):
            # Catches HANDLERS[driver.kind] and drivers[operation.type] style
            # table dispatch even though neither form contains a literal if.
            kind, subject = "table dispatch", node
        elif isinstance(node, ast.Call):
            full = _dotted_expr(node.func)
            if (
                _call_target(node.func) in {"isinstance", "issubclass", "type"}
                or full.endswith(".get")
                or full.endswith(".register")
                or full.endswith(".dispatch")
            ):
                kind, subject = "type/registry dispatch", node
        elif isinstance(node, ast.Dict):
            if any(
                isinstance(key, ast.Constant) and key.value in _DRIVER_LITERALS
                for key in node.keys
                if key is not None
            ):
                kind, subject = "driver-keyed dispatch table", node

        if kind is not None and subject is not None and _source_mentions_driver_dispatch(subject):
            findings.add((node.lineno, kind))

    return [
        f"driver-specific conditional in broker module: {relative}:{line} ({kind})"
        for line, kind in sorted(findings)
    ]


def test_kernel_broker_has_zero_driver_specific_conditionals() -> None:
    findings = [
        finding
        for path in _broker_modules()
        for finding in _driver_conditional_findings(path)
    ]
    assert not findings, (
        "broker driver-conditional census expected zero; typed operation modules "
        "must own driver behavior:\n  " + "\n  ".join(findings)
    )


def test_driver_conditional_census_catches_non_if_dispatch(tmp_path: Path) -> None:
    cases = {
        "ternary.py": "result = terminal if driver.kind == 'terminal' else inference\n",
        "match.py": "match driver.kind:\n    case 'terminal':\n        result = 1\n",
        "table.py": "result = handlers[driver.kind]\n",
        "operation_table.py": "result = handlers[operation.type]\n",
        "registry.py": "result = registry.dispatch(driver)\n",
    }
    for name, source in cases.items():
        path = tmp_path / name
        path.write_text(source, encoding="utf-8")
        findings = _driver_conditional_findings(path)
        assert findings, f"non-if driver dispatch fixture escaped: {name}"
