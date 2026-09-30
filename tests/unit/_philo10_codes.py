"""PHILO-10-05 (Muad'Dib's ruling on #698): every code the channel services can emit, derived from the source.

Read by AST from the channel modules, never typed by hand:

* ``refused`` -- the first argument of ``ChannelRefused(...)``, the ``code=`` of a
  ``ValidationError`` / ``ServiceError`` raised there, and every channel.*
  operation's declared ``refusals`` (``holdspeak/channel_operations.py``);
* ``failed`` / ``unknown`` -- the second argument of ``Outcome("failed"|"unknown", ...)``,
  the pinned tables (``PINNED``, ``FAILED_ON_CREATE``), and the kernel's row reasons
  (``channel_send_ended_effect``'s ``row_reason`` default and call-site values);
* a code with a variable part (an f-string: an errno, an exception, a channel, an HTTP
  status) is a TEMPLATE, reported as a prefix (``create_``, ``github_exit_``);
* a code passed through a variable is followed to its source by a small declared
  table of FLOWS (below); a NEW variable site anywhere fails the fence until it is
  added, so the class stays closed.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODULES = [
    "holdspeak/services/channel_contract.py",
    "holdspeak/services/channel_cli.py",
    "holdspeak/services/channel_email.py",
    "holdspeak/services/channel_slack.py",
    "holdspeak/services/channel_service.py",
    "holdspeak/kernel/channel_send.py",
    "holdspeak/services/steward_contract.py",
]
CLI_CHANNELS = ("github", "jira", "confluence")

# Variable code sites: (module, the source text of the argument) -> the kinds it
# carries and the exception class (in that module) whose literal codes flow there.
FLOWS = {
    # _dispatch_one: the ChannelRefused private_payload_file raises (channel_contract.py).
    ("holdspeak/services/channel_cli.py", "exc.code"): ({"failed"}, "=payload_changed"),
    ("holdspeak/services/channel_cli.py", "reason"): ({"failed"}, "@assigned"),
    ("holdspeak/services/channel_cli.py", "pinned"): ({"failed"}, "@PINNED"),
    ("holdspeak/services/channel_contract.py", "self.FAILED_ON_CREATE[exc.errno]"): ({"failed"}, "@FAILED_ON_CREATE"),
    # send: a key read refused before the boundary (EmailKeyError), and the transport's
    # answer after it (EmailTransportError, which also carries the key-read codes).
    ("holdspeak/services/channel_email.py", "exc.code"): [({"refused"}, "EmailKeyError"),
                                                          ({"failed", "unknown"}, "EmailTransportError+EmailKeyError")],
    # Slack follows the same key-custody and transport path.  Its dispatch also
    # catches a pre-boundary ChannelRefused and records that as a failed send.
    ("holdspeak/services/channel_slack.py", "exc.code"): [({"refused"}, "SlackKeyError"),
                                                          ({"failed", "unknown"}, "SlackTransportError+SlackKeyError"),
                                                          ({"failed"}, "ChannelRefused")],
    ("holdspeak/services/channel_slack.py", "code"): (set(), "@assigned"),
    ("holdspeak/services/channel_email.py", "code"): (set(), "@assigned"),
    ("holdspeak/services/channel_email.py", "self.PINNED[status]"): ({"failed"}, "@PINNED"),
    # PHILO-10-07: Resend's pinned (status, name) table.
    ("holdspeak/services/channel_email.py", "self.PINNED[status, name]"): ({"failed"}, "@PINNED"),
    ("holdspeak/services/channel_service.py", "exc.code"): [({"refused"}, "EmailKeyError"),
                                                              ({"refused"}, "SlackKeyError")],
    # _close_as_row: a stored row's own reason read back (already one of the codes above).
    ("holdspeak/services/channel_service.py", 'row["reason"]'): (set(), "@stored"),
}


# Codex Astra r1 on #698 (finding 1): a code with a variable part is accepted ONLY
# as one of these exact f-strings (each takes its face word by prefix, or expands
# over the CLI channel names). Any other f-string, a ``.format()``, a ``+``, a call
# -- any code expression this derivation cannot read -- is UNSUPPORTED and fails
# the fence (``test_no_code_expression_is_unsupported``), so no formatted code can
# slip past it.
ALLOWED_TEMPLATES = {
    'f"create_{errno.errorcode.get(exc.errno or 0, \'error\').lower()}"',
    'f"write_{errno.errorcode.get(exc.errno or 0, \'error\').lower()}"',
    'f"dispatch_{type(exc).__name__.lower()}"',
    'f"recover_{type(exc).__name__.lower()}"',
    'f"unpinned_{status}"',
    'f"payload_too_large:{channel}"',
    'f"{self.name}_interrupted"',
    'f"{self.name}_cli_missing"',
    'f"{self.name}_cli_not_started"',
    'f"{self.name}_no_proof"',
    'f"{self.name}_exit_{code}"',
}
# A variable that carries a code into a source the derivation already reads
# (the ``code`` of EmailKeyError caught in the transport; a pinned() answer
# from its PINNED table). Anything else assigned to ``code`` / returned by
# ``pinned`` is unsupported.
ALLOWED_CARRIERS = {"exc.code", "_first_pinned(text, self.PINNED)"}


def _src(node: ast.AST, text: str) -> str:
    return ast.get_source_segment(text, node) or ""


def _template(node: ast.JoinedStr, text: str) -> list[str]:
    """An f-string code as its literal prefix, expanded over the CLI channel names."""
    first = node.values[0] if node.values else None
    if isinstance(first, ast.Constant):
        return [str(first.value)]
    seg = _src(node, text)
    if seg.startswith('f"{self.name}_'):
        rest = seg[len('f"{self.name}'):].split("{")[0].rstrip("\"'")
        return [f"{name}{rest}" for name in CLI_CHANNELS]
    if seg.startswith('f"{self.name}') or seg.startswith("f'{self.name}"):
        return [f"{name}_" for name in CLI_CHANNELS]
    raise AssertionError(f"an f-string code with no literal prefix: {seg}")


def _strings(node: ast.AST) -> list[str]:
    return [n.value for n in ast.walk(node) if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def emitted() -> dict[str, dict]:
    """{code: {"kinds": set, "template": bool, "where": [...]}} plus the variable sites seen."""
    codes: dict[str, dict] = {}
    variables: set[tuple[str, str]] = set()
    unsupported: list[str] = []

    def add(code: str, kind: str, where: str, template: bool = False) -> None:
        if not code:
            return
        entry = codes.setdefault(code, {"kinds": set(), "template": template, "where": []})
        entry["kinds"].add(kind)
        entry["where"].append(where)

    exc_codes: dict[str, dict[str, set]] = {}
    for rel in MODULES:
        text = (REPO / rel).read_text()
        tree = ast.parse(text)
        exc_codes[rel] = {}

        def read(arg: ast.AST, where: str, *, variable_ok: bool = True) -> list[tuple[str, bool]]:
            """The code(s) an expression carries: [(code, is_template)]; a variable is recorded; else UNSUPPORTED."""
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return [(arg.value, False)]
            if isinstance(arg, ast.Constant) and arg.value is None:
                return []
            seg = _src(arg, text)
            if isinstance(arg, ast.JoinedStr):
                if seg not in ALLOWED_TEMPLATES:
                    unsupported.append(f"{where}: f-string code {seg}")
                    return []
                return [(c, True) for c in _template(arg, text)]
            if variable_ok and isinstance(arg, (ast.Name, ast.Attribute, ast.Subscript)):
                variables.add((rel, seg))
                return []
            unsupported.append(f"{where}: code expression {seg}")
            return []
        for node in ast.walk(tree):
            if rel.endswith("steward_contract.py") and not (
                    isinstance(node, ast.Call) and getattr(node.func, "id", "") == "channel_send_ended_effect"):
                continue  # the steward module is read ONLY for the restart's row reason of a send
            if isinstance(node, ast.Call):
                fn = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
                where = f"{rel}:{node.lineno}"
                if fn in ("ChannelRefused", "EmailKeyError", "EmailTransportError", "SlackKeyError",
                          "SlackTransportError") and node.args:
                    for code, template in read(node.args[0], where):
                        exc_codes[rel].setdefault(fn, set()).add(code)
                        if fn == "ChannelRefused":
                            add(code, "refused", where, template=template)
                elif fn in ("ValidationError", "ServiceError", "NotFound"):
                    for kw in node.keywords:
                        if kw.arg == "code":
                            for code, template in read(kw.value, where, variable_ok=False):
                                add(code, "refused", where, template=template)
                elif fn == "Outcome" and len(node.args) >= 2:
                    state, arg = node.args[0], node.args[1]
                    kinds = {s for s in _strings(state) if s in ("failed", "unknown")}
                    if not kinds and not (isinstance(state, ast.Constant) and state.value == "sent"):
                        variables.add((rel, _src(arg, text)))
                        continue
                    for code, template in read(arg, where):
                        for k in kinds:
                            add(code, k, where, template=template)
                elif fn == "channel_send_ended_effect":
                    for kw in node.keywords:
                        if kw.arg == "row_reason":
                            for code, _t in read(kw.value, where, variable_ok=False):
                                add(code, "unknown", where)
            elif isinstance(node, ast.FunctionDef) and node.name == "channel_send_ended_effect":
                for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
                    if arg.arg == "row_reason" and default is not None:
                        for code, _t in read(default, f"{rel}:{node.lineno}", variable_ok=False):
                            add(code, "unknown", f"{rel}:{node.lineno}")
            elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in ("PINNED", "FAILED_ON_CREATE")
                                                      for t in node.targets):
                value = node.value
                if isinstance(value, ast.Dict):
                    items = value.values
                elif isinstance(value, ast.Tuple):
                    items = [e.elts[1] for e in value.elts if isinstance(e, ast.Tuple)]
                else:
                    items = []
                if not isinstance(value, (ast.Dict, ast.Tuple)) or any(
                        not (isinstance(e, ast.Tuple) and len(e.elts) == 2) for e in getattr(value, "elts", [])):
                    unsupported.append(f"{rel}:{node.lineno}: a pinned table that is not literal pairs")
                for item in items:
                    for code, _t in read(item, f"{rel}:{node.lineno}", variable_ok=False):
                        add(code, "failed", f"{rel}:{node.lineno}")
            elif rel.endswith("channel_cli.py") and isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "reason" for t in node.targets):
                # the value, or both arms of a conditional -- never a string inside a call
                arms = [node.value.body, node.value.orelse] if isinstance(node.value, ast.IfExp) else [node.value]
                for arm in arms:
                    for code, _t in read(arm, f"{rel}:{node.lineno}", variable_ok=False):
                        add(code, "failed", f"{rel}:{node.lineno}")
            elif isinstance(node, ast.FunctionDef) and node.name == "pinned":
                # a channel's own pinned() override answers a code directly (gh exit 4)
                for ret in ast.walk(node):
                    if isinstance(ret, ast.Return) and ret.value is not None:
                        if _src(ret.value, text) in ALLOWED_CARRIERS:
                            continue
                        for code, _t in read(ret.value, f"{rel}:{ret.lineno}", variable_ok=False):
                            add(code, "failed", f"{rel}:{ret.lineno}")
            elif isinstance(node, ast.FunctionDef) and node.name == "_classify":
                transport_error = ("EmailTransportError" if rel.endswith("channel_email.py")
                                    else "SlackTransportError" if rel.endswith("channel_slack.py") else None)
                for ret in ast.walk(node):
                    if isinstance(ret, ast.Return) and isinstance(ret.value, ast.Tuple) and transport_error:
                        for code, _t in read(ret.value.elts[0], f"{rel}:{ret.lineno}", variable_ok=False):
                            exc_codes[rel].setdefault(transport_error, set()).add(code)
                    elif isinstance(ret, ast.Return):
                        unsupported.append(f"{rel}:{ret.lineno}: _classify returns no (code, left) pair")
            elif rel.endswith(("channel_email.py", "channel_slack.py")) and isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple) and any(
                    isinstance(t, ast.Tuple) and t.elts and isinstance(t.elts[0], ast.Name) and t.elts[0].id == "code"
                    for t in node.targets):
                transport_error = ("EmailTransportError" if rel.endswith("channel_email.py") else "SlackTransportError")
                for code, _t in read(node.value.elts[0], f"{rel}:{node.lineno}", variable_ok=False):
                    exc_codes[rel].setdefault(transport_error, set()).add(code)
            elif rel.endswith(("channel_email.py", "channel_slack.py")) and isinstance(node, ast.Assign) and any(
                    isinstance(t, ast.Name) and t.id == "code" for t in node.targets):
                # the transport's own code variable (transmit): what it raises EmailTransportError with
                if _src(node.value, text) not in ALLOWED_CARRIERS:
                    transport_error = ("EmailTransportError" if rel.endswith("channel_email.py") else "SlackTransportError")
                    for code, _t in read(node.value, f"{rel}:{node.lineno}", variable_ok=False):
                        exc_codes[rel].setdefault(transport_error, set()).add(code)
    # Follow each declared flow to its source codes.
    for (rel, text_arg), flows in FLOWS.items():
      for kinds, source in (flows if isinstance(flows, list) else [flows]):
        for cls in source.split("+"):
            if cls.startswith("@"):
                continue
            if cls.startswith("="):
                for k in kinds:
                    add(cls[1:], k, f"{rel} (flow {text_arg})")
                continue
            source_modules = {
                "EmailKeyError": "holdspeak/services/channel_email.py",
                "EmailTransportError": "holdspeak/services/channel_email.py",
                "SlackKeyError": "holdspeak/services/channel_slack.py",
                "SlackTransportError": "holdspeak/services/channel_slack.py",
            }
            source = source_modules.get(cls)
            source_codes = exc_codes.get(source, {}).get(cls, set()) if source else set()
            for code in exc_codes.get(rel, {}).get(cls, set()) | source_codes:
                for k in kinds:
                    add(code, k, f"{rel} (flow {text_arg} <- {cls})")
    codes["__variables__"] = {"kinds": set(), "template": False, "where": sorted(variables)}
    codes["__unsupported__"] = {"kinds": set(), "template": False, "where": sorted(set(unsupported))}
    return codes


def declared_refusals() -> set[str]:
    """Every channel.* operation's declared refusals, as codes."""
    import holdspeak.operations  # noqa: F401  (the registry imports the channel descriptors)
    import holdspeak.channel_operations as ops_module

    out: set[str] = set()
    for value in vars(ops_module).values():
        if type(value).__name__ == "OperationDescriptor" and str(value.name).startswith("channel."):
            for entry in value.refusals:
                token = str(entry).split(":")[0].split()[-1] if str(entry).startswith("NotFound") else str(entry).split(" ")[0]
                token = token.rstrip(":")
                if token.startswith("payload_too_large"):
                    token = "payload_too_large:"
                if re.fullmatch(r"[a-z][a-z0-9_]*:?", token):
                    out.add(token)
    return out


def face_tables() -> dict[str, set[str]]:
    """The keys of the Send face's word tables (web/src/features/channels/channels.ts) and the library's."""
    ts = (REPO / "web/src/features/channels/channels.ts").read_text()
    lib = (REPO / "web/src/desk/surface/egress.ts").read_text()

    def keys(src: str, name: str) -> set[str]:
        m = re.search(rf"const {name}[^=]*=\s*\{{(.*?)\n\}};", src, re.S)
        assert m, name
        return set(re.findall(r"^\s*\"?([a-z0-9_:]+)\"?\s*:", m.group(1), re.M))

    def prefixes(name: str) -> set[str]:
        m = re.search(rf"const {name}[^=]*=\s*\[(.*?)\n\];", ts, re.S)
        assert m, name
        return set(re.findall(r'\["([a-z0-9_:]+)",', m.group(1)))

    return {"refused": keys(ts, "REFUSED") | keys(lib, "REFUSAL_WORDS"), "failed": keys(ts, "FAILED"),
            "unknown": keys(ts, "UNKNOWN"), "refused_prefix": prefixes("REFUSED_PREFIX"),
            "failed_prefix": prefixes("FAILED_PREFIX"), "unknown_prefix": prefixes("UNKNOWN_PREFIX")}


def missing() -> list[tuple[str, str]]:
    """Every (kind, code) the services emit with no face word."""
    codes = emitted()
    codes.pop("__variables__")
    codes.pop("__unsupported__")
    for code in declared_refusals():
        codes.setdefault(code, {"kinds": set(), "template": code.endswith(":"), "where": []})["kinds"].add("refused")
    tables = face_tables()
    out = []
    for code, entry in sorted(codes.items()):
        for kind in sorted(entry["kinds"]):
            if code in tables[kind]:
                continue
            if any(code.startswith(p) for p in tables[f"{kind}_prefix"]):
                continue
            out.append((kind, code))
    return out
