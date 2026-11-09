# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_ask_runner_migration.py to restore.

# ruff: noqa


# --- test_ask_service_ast_fence_and_ask_materializer_forged_permit: P8: AST scan of ask_service.py for call names; the forged-permit half duplicates test_ask_service_obligations
def test_ask_service_ast_fence_and_ask_materializer_forged_permit(rig):
    db, broker, _ = rig
    source = Path(__file__).parents[2] / "holdspeak" / "services" / "ask_service.py"
    tree = ast.parse(source.read_text())
    ask = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AskService")
    method = next(node for node in ask.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "ask")
    calls = {node.func.attr for node in ast.walk(method) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    imports = {alias.name for node in ast.walk(method) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not ({"run_prompt", "build_intel_for_target", "build_intel_for_revision", "record_artifact"} & calls)
    assert "RunLifecycle" not in imports
    with db._connection() as conn:
        with pytest.raises(KernelRefused, match="projection_publication_permit_invalid"):
            materialize(conn, object(), object())
