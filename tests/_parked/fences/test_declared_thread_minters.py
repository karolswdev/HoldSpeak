# PARKED 2026-11-09: syntactic reachability ignores arguments and misclassifies automation.make_one (an instruction copy) as a new delegation grant. Keep the existing fence until live caller bindings can state the property.
class TestDeclaredMinterReachability:
    def test_every_declared_delegation_or_schedule_writer_is_authority_for_a_thread(self) -> None:
        """Start at live declarations and follow their service calls to writers.

        This is a syntactic reachability check, not proof of arbitrary Python
        dispatch. The argument-aware runtime cases below exercise those calls.
        No writer-to-tool inventory needs an edit when a method moves.
        """
        import ast
        from collections import defaultdict

        from holdspeak.operations import DESCRIPTORS
        from holdspeak.mcp.tool_authority import ARGUMENT_AUTHORITY, TOOL_AUTHORITY
        from tests import _tree

        functions = {}
        by_name = defaultdict(set)
        by_class = defaultdict(set)

        def collect(path, node, cls=""):
            for child in ast.iter_child_nodes(node):
                owner = child.name if isinstance(child, ast.ClassDef) else cls
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    key = (path, child.lineno)
                    functions[key] = (child, cls)
                    by_name[child.name].add(key)
                    by_class[(cls, child.name)].add(key)
                collect(path, child, owner)

        for path in _tree.python_files("holdspeak", exclude=("_parked",)):
            collect(path, _tree.ast_of(path))

        writers = set()
        edges = defaultdict(set)
        for key, (fn, cls) in functions.items():
            for node in ast.walk(fn):
                if isinstance(node, ast.Call):
                    callee = getattr(node.func, "attr", getattr(node.func, "id", ""))
                    receiver = getattr(node.func, "value", None)
                    receiver_name = getattr(receiver, "attr", "")
                    if callee == "enable_from_owner_in_transaction" or any(
                        (kw.arg == "unattended_enabled"
                         or (kw.arg == "enabled" and receiver_name == "scheduled_recordings"
                             and callee in {"create", "update"}))
                        and not (isinstance(kw.value, ast.Constant) and not kw.value.value)
                        for kw in node.keywords
                    ):
                        writers.add(key)
                    # Resolve self calls in their class, module functions in
                    # their file, and uniquely named cross-service methods.
                    if isinstance(receiver, ast.Name) and receiver.id == "self":
                        targets = by_class[(cls, callee)]
                    else:
                        targets = {target for target in by_name[callee] if target[0] == key[0]}
                        if not targets and len(by_name[callee]) == 1:
                            targets = by_name[callee]
                    edges[key].update(targets)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if node.value == "delegation_enabled" or (
                        "INSERT INTO kernel_" in node.value and "delegations" in node.value
                    ):
                        writers.add(key)
                elif isinstance(node, ast.JoinedStr):
                    text = "".join(v.value for v in node.values if isinstance(v, ast.Constant))
                    if "INSERT INTO " in text and "agent_identity" in text and "delegator" in text:
                        writers.add(key)

        minters = defaultdict(set)
        for descriptor in DESCRIPTORS:
            if descriptor.tool_schema is None:
                continue
            cls = "".join(part.title() for part in descriptor.service.split("_"))
            pending = list(by_class[(cls, descriptor.method)])
            visited = set()
            while pending:
                key = pending.pop()
                if key in visited:
                    continue
                visited.add(key)
                if key in writers:
                    minters[key].add(descriptor.tool_name)
                pending.extend(edges[key] - visited)
        assert minters, "the live declarations reached no delegation writer"
        for site, tools in minters.items():
            for tool in tools:
                assert TOOL_AUTHORITY[tool] != "work" or tool in ARGUMENT_AUTHORITY, (site, tool)

