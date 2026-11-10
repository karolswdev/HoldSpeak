# PARKED: retired buckets follow the sync envelope's existing unknown-bucket rule.
@pytest.mark.parametrize(
    "bucket",
    (
        "inference_route_plan_principal_evidence",
        "inference_parent_route_bundles",
        "inference_parent_route_bundle_members",
        "inference_parent_stop_handoffs",
        "inference_parent_stop_handoff_executions",
        "inference_parent_stop_handoff_settlements",
    ),
)
def test_new_route_and_handoff_tables_are_hostile_sync_refused(
    tmp_path: Path, bucket: str,
) -> None:
    db = Database(tmp_path / f"hostile-{bucket}.db")
    with pytest.raises(ValidationError) as refused:
        SyncService(db).push(OWNER, {"notes": [], bucket: [{"forged": True}]})
    assert refused.value.code == "sync_hub_local_bucket_forbidden"
