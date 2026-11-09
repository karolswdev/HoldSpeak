# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_connector_sdk.py to restore.

# ruff: noqa


# --- test_validate_manifest_returns_immutable_dataclass: P3: frozen-dataclass and runtime_checkable Protocol behaviour of Python
def test_validate_manifest_returns_immutable_dataclass():
    manifest = validate_manifest(_good_manifest())
    with pytest.raises(Exception):
        manifest.id = "other"  # type: ignore[misc]


# --- test_sdk_protocols_are_runtime_checkable: P3: frozen-dataclass and runtime_checkable Protocol behaviour of Python
def test_sdk_protocols_are_runtime_checkable():
    """A connector class implementing the right method satisfies the
    Protocol via duck-typing; isinstance() reports it correctly."""

    class FakeConnector:
        def preview(self, db, *, limit=25):  # noqa: ARG002
            return {}

        def enrich(self, db, *, limit=25):  # noqa: ARG002
            return {}

        def clear(self, db, *, capability):  # noqa: ARG002
            return 0

        def discover(self, db, *, limit=25):  # noqa: ARG002
            return []

        def snapshot(self, *, query_kind, query):  # noqa: ARG002
            return []

    instance = FakeConnector()
    assert isinstance(instance, Preview)
    assert isinstance(instance, Enrich)
    assert isinstance(instance, Clear)
    assert isinstance(instance, Discover)
    assert isinstance(instance, Snapshot)


# --- test_partial_implementations_are_partial_isinstance: P3: frozen-dataclass and runtime_checkable Protocol behaviour of Python
def test_partial_implementations_are_partial_isinstance():
    """A pack that only previews is a Preview, not an Enrich."""

    class PreviewOnly:
        def preview(self, db, *, limit=25):  # noqa: ARG002
            return {}

    instance = PreviewOnly()
    assert isinstance(instance, Preview)
    assert not isinstance(instance, Enrich)
    assert not isinstance(instance, Clear)
    assert not isinstance(instance, Snapshot)


# --- test_validate_manifest_default_dry_run_is_true: P1/P8: phase-9 constant sets and a default flag
def test_validate_manifest_default_dry_run_is_true():
    raw = _good_manifest()
    raw.pop("dry_run", None)
    manifest = validate_manifest(raw)
    assert manifest.dry_run is True


# --- test_known_constants_match_phase_9_shape: P1/P8: phase-9 constant sets and a default flag
def test_known_constants_match_phase_9_shape():
    """Sanity: the kinds + capabilities here cover what phase 9
    actually shipped, so phase-11 connector packs slot in cleanly."""
    assert {"cli_enrichment", "candidate_inference", "extension_events"} <= KNOWN_KINDS
    assert {"annotations", "candidates", "commands", "records", "snapshots"} <= KNOWN_CAPABILITIES
