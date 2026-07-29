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
_STATUSES = {"covered", "bypass", "mixed", "dormant", "read", "exempt_computation"}

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
        resolved_target = full.rsplit(".", 1)[-1] if full else target
        return (target in self.targets or resolved_target in self.targets) and (
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
        ("press", "release", "type"),
        full_suffixes=(
            "pynput.keyboard.Controller().press",
            "pynput.keyboard.Controller().release",
            "pynput.keyboard.Controller().type",
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
    CallRule(FAMILY_SUBPROCESS, ("run_subprocess", "run_read_subprocess")),
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
        self.bindings: list[dict[str, str]] = [{}]
        self.ordinals: defaultdict[tuple[str, str], int] = defaultdict(int)
        self.sites: list[EffectSite] = []

    @property
    def scope(self) -> str:
        return ".".join(self.scope_stack) or "<module>"

    def _push_scope(self, name: str) -> None:
        self.scope_stack.append(name)
        self.bindings.append({})

    def _pop_scope(self) -> None:
        self.bindings.pop()
        self.scope_stack.pop()

    def _resolve_name(self, name: str) -> str:
        seen: set[str] = set()
        current = name
        while current not in seen:
            seen.add(current)
            bound = next(
                (scope[current] for scope in reversed(self.bindings) if current in scope),
                None,
            )
            if bound is None or bound == current:
                break
            current = bound
        return current

    def _resolved_expr(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return self._resolve_name(node.id)
        if isinstance(node, ast.Attribute):
            prefix = self._resolved_expr(node.value)
            return f"{prefix}.{node.attr}" if prefix else node.attr
        if isinstance(node, ast.Call):
            return f"{self._resolved_expr(node.func)}()"
        return ""

    def _bind(self, target: ast.expr, origin: str) -> None:
        if isinstance(target, ast.Name):
            if origin:
                self.bindings[-1][target.id] = origin
            else:
                self.bindings[-1].pop(target.id, None)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            local = alias.asname or alias.name.split(".", 1)[0]
            origin = alias.name if alias.asname else local
            self.bindings[-1][local] = origin

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            if alias.name == "*":
                continue
            local = alias.asname or alias.name
            origin = f"{module}.{alias.name}" if module else alias.name
            self.bindings[-1][local] = origin

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        origin = self._resolved_expr(node.value)
        for target in node.targets:
            self._bind(target, origin)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
            self._bind(node.target, self._resolved_expr(node.value))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._push_scope(node.name)
        self.generic_visit(node)
        self._pop_scope()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._push_scope(node.name)
        arguments = (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
        for argument in arguments:
            self.bindings[-1][argument.arg] = argument.arg
        if node.args.vararg is not None:
            self.bindings[-1][node.args.vararg.arg] = node.args.vararg.arg
        if node.args.kwarg is not None:
            self.bindings[-1][node.args.kwarg.arg] = node.args.kwarg.arg
        self.generic_visit(node)
        self._pop_scope()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        target = _call_target(node.func)
        full = self._resolved_expr(node.func)
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
    resolved_target = full.rsplit(".", 1)[-1] if full else target
    if resolved_target in process_targets and any(
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


def _unledgered_message(site: EffectSite) -> str:
    return (
        f"UNLEDGERED effect site: {site.label} "
        f"scope={site.scope} target={site.target} ordinal={site.ordinal}"
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


def test_new_model_or_transcription_network_call_still_requires_triage() -> None:
    source = (
        "def classify(runtime):\n"
        "    return runtime.chat.completions.create(model='new', messages=[])\n"
    )
    found = _classify_source(
        "holdspeak/plugins/dictation/runtime_openai_compatible_new.py", source
    )
    assert len(found) == 1
    message = _unledgered_message(found[0])
    assert "UNLEDGERED effect site" in message
    assert "runtime_openai_compatible_new.py" in message
    assert "target=create" in message


def test_import_and_callable_aliases_cannot_evade_any_effect_family() -> None:
    fixtures = (
        # Subprocess: plain from-import, aliased from-import, module alias, and
        # every process API named by the census scope.
        ("subprocess run from-import", "from subprocess import run\nrun(['true'])", FAMILY_SUBPROCESS),
        ("subprocess run alias", "from subprocess import run as sneaky\nsneaky(['true'])", FAMILY_SUBPROCESS),
        ("subprocess module alias", "import subprocess as sp\nsp.run(['true'])", FAMILY_SUBPROCESS),
        ("subprocess Popen alias", "from subprocess import Popen as launch\nlaunch(['true'])", FAMILY_SUBPROCESS),
        ("subprocess call alias", "from subprocess import call as invoke\ninvoke(['true'])", FAMILY_SUBPROCESS),
        ("subprocess check_output alias", "from subprocess import check_output as output\noutput(['true'])", FAMILY_SUBPROCESS),
        ("subprocess check_call alias", "from subprocess import check_call as checked\nchecked(['true'])", FAMILY_SUBPROCESS),
        # Tmux transport: both imported boundary names survive renaming.
        ("tmux text alias", "from holdspeak.tmux_transport import send_text_to_pane as push\npush(pane='p', text='x')", FAMILY_TMUX),
        ("tmux keys module alias", "import holdspeak.tmux_transport as tmux\ntmux.send_keys_to_pane(pane='p', keys=[])", FAMILY_TMUX),
        # TextTyper: class aliases and aliases of the bound method itself.
        ("TextTyper class alias", "from holdspeak.typer import TextTyper as Typer\nTyper().type_text('x')", FAMILY_TYPER),
        ("TextTyper bound method alias", "from holdspeak.typer import TextTyper as Typer\nwriter = Typer().type_text\nwriter('x')", FAMILY_TYPER),
        # Egress: HTTP, socket, and model-call aliases all retain provenance.
        ("urlopen alias", "from urllib.request import urlopen as fetch\nfetch('https://example.test')", FAMILY_EGRESS),
        ("urllib module alias", "import urllib.request as net\nnet.urlopen('https://example.test')", FAMILY_EGRESS),
        ("socket alias", "from socket import create_connection as connect\nconnect(('example.test', 443))", FAMILY_EGRESS),
        ("model method alias", "request = client.chat.completions.create\nrequest()", FAMILY_EGRESS),
        # Raw desktop: clipboard, pyautogui, AX/Quartz, and AppleScript process
        # aliases remain raw primitives rather than generic subprocess sites.
        ("clipboard alias", "from pyperclip import copy as stash\nstash('x')", FAMILY_RAW_DESKTOP),
        ("clipboard module alias", "import pyperclip as clipboard\nclipboard.copy('x')", FAMILY_RAW_DESKTOP),
        ("pyautogui alias", "from pyautogui import hotkey as chord\nchord('ctrl', 'v')", FAMILY_RAW_DESKTOP),
        ("pynput controller alias", "from pynput.keyboard import Controller as Keys\nkeyboard = Keys()\nkeyboard.press('x')", FAMILY_RAW_DESKTOP),
        ("Quartz alias", "from Quartz import CGEventPost as post\npost(0, event)", FAMILY_RAW_DESKTOP),
        ("AX alias", "from ApplicationServices import AXUIElementSetAttributeValue as set_ax\nset_ax(element, attr, value)", FAMILY_RAW_DESKTOP),
        ("AppleScript process alias", "from subprocess import run as execute\nexecute(['osascript', '-e', script])", FAMILY_RAW_DESKTOP),
    )

    for name, source, expected_family in fixtures:
        sites = _classify_source("holdspeak/alias_mutation.py", source)
        assert len(sites) == 1, f"{name} escaped or double-counted: {sites}"
        site = sites[0]
        assert site.family == expected_family, (
            f"{name} classified as {site.family}, expected {expected_family}"
        )
        message = _unledgered_message(site)
        assert "holdspeak/alias_mutation.py:" in message
        assert f"[{expected_family}]" in message
        assert f"target={site.target}" in message

    shadowed = "from subprocess import run\ndef harmless(run):\n    run(['not-the-import'])\n"
    assert not _classify_source("holdspeak/shadowed.py", shadowed), (
        "a function argument must shadow an imported effect name"
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
        _unledgered_message(site)
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


def test_effect_ledger_asserts_the_composed_family_counts() -> None:
    ledger = _load_ledger()
    entries = ledger["sites"]
    expected = ledger["expected"]

    families = Counter(entry["family"] for entry in entries)
    statuses = Counter(entry["status"] for entry in entries)
    covered = statuses["covered"]
    reads = statuses["read"]
    exempt = statuses["exempt_computation"]
    not_covered = len(entries) - covered - reads - exempt

    assert set(families) == _FAMILIES
    assert set(statuses) <= _STATUSES
    assert len(entries) == expected["total"] == sum(expected["families"].values()) == 21, (
        f"effect census must state 21 total sites, found {len(entries)}"
    )
    assert covered == expected["covered"] == 3, (
        f"effect census must state 3 covered sites, found {covered}"
    )
    assert reads == expected.get("reads", 0) == 0, (
        f"effect census must state 0 classified reads, found {reads}"
    )
    assert exempt == expected.get("exempt_computation", 0) == 0, (
        f"effect census must state 0 exempt computations, found {exempt}"
    )
    assert not_covered == expected["not_covered"] == 18, (
        f"effect census must state 18 not-covered sites, found {not_covered}"
    )
    assert dict(families) == expected["families"] == {
        FAMILY_TMUX: 2,
        FAMILY_TYPER: 1,
        FAMILY_SUBPROCESS: 3,
        FAMILY_EGRESS: 5,
        FAMILY_RAW_DESKTOP: 10,
    }, f"effect family breakdown changed: {dict(families)}"
    egress = [entry for entry in entries if entry["family"] == FAMILY_EGRESS]
    assert all(entry.get("classification") in {"egress", "model_invocation"} for entry in egress)
    assert all(entry.get("egress_boundary") for entry in egress)
    assert all(entry["reason"].strip() for entry in entries)
    debt = [
        entry
        for entry in entries
        if entry["status"] not in {"covered", "read", "exempt_computation"}
    ]
    assert all(entry.get("closing_condition", "").strip() for entry in debt), (
        "every debt site must name its closing condition: "
        + ", ".join(entry["id"] for entry in debt if not entry.get("closing_condition", "").strip())
    )
    assert len({entry["id"] for entry in entries}) == len(entries) == 21
    assert "No agent principal may reach" in ledger["legal_effect"]


def test_independent_audit_demotions_are_not_counted_as_covered() -> None:
    entries = {entry["id"]: entry for entry in _load_ledger()["sites"]}
    covered = {site_id for site_id, entry in entries.items() if entry["status"] == "covered"}

    assert covered == {"D09", "N03", "N04"}
    for site_id in {"T01", "T02", "C02", "C03", "C05", "N10", "N11", "N12"}:
        assert site_id not in covered, f"independent audit demoted {site_id} by name"
        assert entries[site_id]["closing_condition"].strip()


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
