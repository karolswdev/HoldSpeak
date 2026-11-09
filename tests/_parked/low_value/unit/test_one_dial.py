# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_one_dial.py to restore.

# ruff: noqa


# --- test_intel_queue_signatures_carry_no_endpoint_triple: P8: source-text and signature scans for names banned by HS-112/Phase 143 (census fences)
def test_intel_queue_signatures_carry_no_endpoint_triple() -> None:
    import inspect

    import holdspeak.intel_queue as iq

    for fn in (iq.process_next_intel_job, iq.drain_intel_queue, iq.start_intel_queue_worker):
        params = set(inspect.signature(fn).parameters)
        assert not {"cloud_model", "cloud_api_key_env", "cloud_base_url"} & params, fn


# --- test_phase143_adopters_have_no_direct_one_dial_resolver: P8: source-text and signature scans for names banned by HS-112/Phase 143 (census fences)
def test_phase143_adopters_have_no_direct_one_dial_resolver() -> None:
    """Saved compatibility fields may migrate/project, never select a live model."""
    forbidden = (
        "resolve_inference_target(",
        "resolve_placement(",
        "resolve_workbench_deployment_revision(",
        "resolve_deployment_revision(",
    )
    for rel in (
        "holdspeak/services/recipe_service.py",
        "holdspeak/services/workbench_runner.py",
        "holdspeak/services/workbench_service.py",
        "holdspeak/services/support.py",
    ):
        text = (REPO / rel).read_text()
        assert not any(token in text for token in forbidden), rel


# --- test_census_no_legacy_endpoint_fields_in_web_src: P8: source-text and signature scans for names banned by HS-112/Phase 143 (census fences)
def test_census_no_legacy_endpoint_fields_in_web_src() -> None:
    banned_web = re.compile(
        r"intel_cloud_base_url|intel_cloud_model|intel_cloud_api_key_env"
        r"|openai_compatible_base_url|openai_compatible_model"
        r"|openai_compatible_api_key_env"
    )
    offenders = [
        str(path)
        for path in _files(REPO / "web" / "src", (".ts", ".tsx"))
        if "node_modules" not in str(path) and banned_web.search(path.read_text())
    ]
    assert offenders == []


# --- test_census_no_feature_code_readers_outside_config: P8: source-text and signature scans for names banned by HS-112/Phase 143 (census fences)
def test_census_no_feature_code_readers_outside_config() -> None:
    offenders = []
    for path in _files(REPO / "holdspeak", (".py",)):
        if path.name == "config.py" and path.parent.name == "holdspeak":
            continue  # declaration + the one migration shim
        # HS-117-12: config.py split into holdspeak/config/ package
        if "holdspeak/config/" in str(path):
            continue
        if _BANNED.search(path.read_text()):
            offenders.append(str(path))
    assert offenders == []
