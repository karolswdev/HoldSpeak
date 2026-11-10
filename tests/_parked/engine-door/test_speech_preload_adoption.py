# PARKED 2026-11-09 (door/speech-capture): the warm freezes no route plan and writes no principal-policy evidence: it asks the door's speech.transcribe chain and runs as the preload service (its identity is still proven in test_dictation_session_admission).
# Moved from tests/unit/test_speech_preload_adoption.py; its helpers are still there.

from tests.unit.test_speech_preload_adoption import *  # noqa: F401,F403


# HS-200-03: this machine must resolve an on-device dictation artifact
# from default configuration, or the session plan records the transcription
# capability UNRESOLVED and admission refuses `no_assignment`. That is the
# environment (no MLX runtime, no configured llama.cpp model), not a product
# defect, so the dependency is DECLARED and skips with its reason rather
# than failing as if the product were broken.
@pytest.mark.requires_local_dictation_route
def test_parentless_preload_is_closed_capability_only_and_local(tmp_path, monkeypatch):
    """Coverage 1/2: exact policy, capability source, no preload assignment."""
    db, broker, _host, _impl = _build_host(tmp_path, monkeypatch, legacy=False)
    calls: list[str] = []
    assignments = broker.inference_adoption_service.plans._assignments
    original_head = assignments._head

    def observed_head(conn: Any, assignment_key: str) -> Any:
        calls.append(assignment_key)
        return original_head(conn, assignment_key)

    monkeypatch.setattr(assignments, "_head", observed_head)
    admission = preload_service_admission(config_snapshot=Config())

    assert admission.principal.kind is PrincipalKind.SERVICE
    assert admission.principal.identity == "local-model-preload"
    assert admission.principal.authority_basis == "local-model-preload:assigned-speech-route"
    assert admission.source_route["source"]["inherited_from"] == "capability"
    assert calls == ["capability:speech.transcribe"]
    assert admission.preload_route["capability"]["id"] == "speech.preload"
    with db._connection() as conn:
        source_policy = conn.execute(
            "SELECT payload_json FROM inference_route_plan_principal_evidence WHERE plan_id=?",
            (admission.source_route["id"],),
        ).fetchone()["payload_json"]
        preload_policy = conn.execute(
            "SELECT payload_json FROM inference_route_plan_principal_evidence WHERE plan_id=?",
            (admission.preload_route["id"],),
        ).fetchone()["payload_json"]
        preload_assignments = conn.execute(
            "SELECT count(*) FROM inference_assignment_revisions WHERE capability_id='speech.preload'"
        ).fetchone()[0]
    assert '"assignment_sources":["capability"]' in source_policy
    assert '"policy_id":"local-model-preload@1"' in preload_policy
    assert '"allowed_boundaries":["local"]' in preload_policy
    assert preload_assignments == 0
