"""Parked with ReactionService (the watch fold, 2026-11-08): an Automation event start is a WatchService watch.

Kept, not collected (tests/_parked/conftest.py). Each block names its source file.
"""


# --- from tests/unit/test_watch_jira_jql.py ---
class TestLegacyWatchGuard:
    """refresh_due_watches must not evaluate watches that are paused,
    retired, or bound to an archived project.

    The guard lives in the repo query (list_enabled_legacy_watches); the
    service's _GRADUATED_STATES belt is defense-in-depth.
    """

    @staticmethod
    def _make_svc(db, *, fetcher=None):
        if fetcher is None:
            def fetcher(principal, **kwargs):
                return [{"number": 1, "state": "open", "title": "PR"}]
        return ReactionService(db, snapshot_fetcher=fetcher)

    @staticmethod
    def _make_watch_due(db, watch_id: str, minutes_ago: int = 60):
        """Push updated_at back so a legacy watch is due."""
        from datetime import timedelta as _td
        old = (datetime.now(timezone.utc) - _td(minutes=minutes_ago)).isoformat(
            timespec="seconds"
        )
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET updated_at=? WHERE id=?",
                (old, watch_id),
            )

    @staticmethod
    def _insert_project(db, project_id: str, *, archived: bool = False):
        """Insert a minimal project row."""
        lifecycle = "archived" if archived else "active"
        is_archived = 1 if archived else 0
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, is_archived, lifecycle) "
                "VALUES (?, ?, ?, ?)",
                (project_id, f"proj-{project_id}", is_archived, lifecycle),
            )

    @staticmethod
    def _set_watch_state(db, watch_id: str, state: str):
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET state=? WHERE id=?",
                (state, watch_id),
            )

    @staticmethod
    def _set_watch_project(db, watch_id: str, project_id: str):
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET project_id=? WHERE id=?",
                (project_id, watch_id),
            )

    def test_paused_watch_active_project_not_evaluated(self, db):
        """A paused watch on an active project must NOT be returned by
        the due selection and NOT evaluated by refresh_due_watches."""
        import asyncio
        from datetime import timezone as _tz

        svc = self._make_svc(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-paused-active",
            query={"repository": "acme/app", "refresh_interval_minutes": 15},
        )
        self._insert_project(db, "proj-active-1", archived=False)
        self._set_watch_project(db, "watch-paused-active", "proj-active-1")
        self._set_watch_state(db, "watch-paused-active", "paused")
        self._make_watch_due(db, "watch-paused-active")

        # Repo level: list_enabled_legacy_watches must exclude it
        repo_watches = db.automations.list_enabled_legacy_watches()
        repo_ids = [w["id"] for w in repo_watches]
        assert "watch-paused-active" not in repo_ids, (
            "list_enabled_legacy_watches must exclude paused watches"
        )

        # Service level: refresh_due_watches must produce no outcome
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        outcome_ids = [o["watch_id"] for o in outcomes]
        assert "watch-paused-active" not in outcome_ids, (
            "refresh_due_watches must not evaluate a paused watch"
        )

    def test_active_watch_archived_project_not_evaluated(self, db):
        """An enabled legacy watch (state='') on an archived project
        must NOT be evaluated by refresh_due_watches."""
        import asyncio

        svc = self._make_svc(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-on-archived",
            query={"repository": "acme/app", "refresh_interval_minutes": 15},
        )
        self._insert_project(db, "proj-archived-1", archived=True)
        self._set_watch_project(db, "watch-on-archived", "proj-archived-1")
        # state stays '' (legacy); enabled stays 1
        self._make_watch_due(db, "watch-on-archived")

        # Repo level
        repo_watches = db.automations.list_enabled_legacy_watches()
        repo_ids = [w["id"] for w in repo_watches]
        assert "watch-on-archived" not in repo_ids, (
            "list_enabled_legacy_watches must exclude watches on archived projects"
        )

        # Service level
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        outcome_ids = [o["watch_id"] for o in outcomes]
        assert "watch-on-archived" not in outcome_ids, (
            "refresh_due_watches must not evaluate a watch on an archived project"
        )

    def test_active_watch_active_project_still_evaluated(self, db):
        """Regression: an enabled legacy watch (state='') on an active
        project must still be evaluated normally."""
        import asyncio

        svc = self._make_svc(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-healthy",
            query={"repository": "acme/app", "refresh_interval_minutes": 15},
        )
        self._insert_project(db, "proj-active-2", archived=False)
        self._set_watch_project(db, "watch-healthy", "proj-active-2")
        self._make_watch_due(db, "watch-healthy")

        # Repo level: must appear
        repo_watches = db.automations.list_enabled_legacy_watches()
        repo_ids = [w["id"] for w in repo_watches]
        assert "watch-healthy" in repo_ids, (
            "list_enabled_legacy_watches must include active watches on active projects"
        )

        # Service level: must be refreshed
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        outcome_ids = [o["watch_id"] for o in outcomes]
        assert "watch-healthy" in outcome_ids, (
            "refresh_due_watches must evaluate a healthy legacy watch"
        )
        status = {o["watch_id"]: o["status"] for o in outcomes}
        assert status["watch-healthy"] == "refreshed"


# --- from tests/unit/test_watch_arming.py (TestArmOnEnable methods) ---
    def test_disabled_watch_is_never_selected(self, db: Any) -> None:
        """AC-2: disabling leaves no row the scheduler picks up.

        `list_due_watches` filters on `enabled = 1`, so the column is left
        as it is on disable -- this test is the proof the filter is real,
        not an assumption.
        """
        from holdspeak.services.reaction_service import ReactionService

        watch_id = _seed_watch(
            db, "w-toggle", state="active",
            next_evaluation_at=_now_iso(-5),
        )
        assert watch_id in _due_ids(db)

        ReactionService(db).set_watch_enabled(OWNER, watch_id, False)
        assert watch_id not in _due_ids(db), (
            "a disabled watch is still selectable by the scheduler"
        )

        # Re-enabling ARMS it (the legacy enable path, graduated row).
        # The column is cleared first so the assertion cannot pass on a
        # value the seed left behind.
        db.automations.update_watch_spec(watch_id, state="active")
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET next_evaluation_at=NULL "
                "WHERE id=?", (watch_id,),
            )
        ReactionService(db).set_watch_enabled(OWNER, watch_id, True)
        assert _next_eval(db, watch_id) is not None, (
            "enabling left the watch unarmed -- it can never be selected"
        )

    def test_enable_does_not_arm_a_legacy_row(self, db: Any) -> None:
        """A legacy (state='') watch stays owned by refresh_due_watches."""
        from holdspeak.services.reaction_service import ReactionService

        watch_id = _seed_watch(db, "w-legacy", state="", enabled=0)
        ReactionService(db).set_watch_enabled(OWNER, watch_id, True)

        assert _next_eval(db, watch_id) is None, (
            "enabling a legacy row armed it -- two schedulers on one row"
        )



# --- from tests/integration/test_web_automations_api.py ---
def test_owner_can_test_and_baseline_a_watch_without_client_snapshots(
    client: TestClient, automations_db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "holdspeak.services.watch_sources.fetch_watch_snapshot",
        lambda *args, **kwargs: [{"number": 17, "title": "Ship it", "state": "open"}],
    )
    created = client.post("/api/automations/watches", json={
        "connector_id": "github", "query_kind": "pull_requests",
        "name": "My requested reviews", "query": {"repository": "acme/widget"},
        "watch_id": "watch-review",
    })
    assert created.status_code == 201
    assert created.json()["watch"]["connector_id"] == "gh"

    paused = client.put("/api/automations/watches/watch-review/enabled", json={"enabled": False})
    assert paused.status_code == 200
    assert paused.json()["watch"]["enabled"] is False
    enabled = client.put("/api/automations/watches/watch-review/enabled", json={"enabled": True})
    assert enabled.status_code == 200

    tested = client.post("/api/automations/watches/watch-review/test")
    assert tested.status_code == 200
    assert tested.json()["baseline"] is True
    assert automations_db.automations.get_watch("watch-review")["snapshot"] == {}

    baseline = client.post("/api/automations/watches/watch-review/baseline")
    assert baseline.status_code == 200
    assert baseline.json()["baseline"] is True
    assert baseline.json()["events"] == []

    reaction = client.post("/api/automations/reactions", json={
        "reaction_id": "reaction-review", "watch_id": "watch-review",
        "event_pattern": "github.pr.review_requested", "workbench_id": "wb-review",
        "enabled": False,
    })
    assert reaction.status_code == 201
    assert reaction.json()["reaction"]["enabled"] is False
    enabled_reaction = client.put(
        "/api/automations/reactions/reaction-review/enabled", json={"enabled": True},
    )
    assert enabled_reaction.status_code == 200

    event = ServiceEventLedger(automations_db).append(
        Principal(PrincipalKind.OWNER, "test-owner"),
        event_type="github.pr.review_requested", producer="connector.gh.watch",
        subject_ref="gh:pull_requests:17", source_revision="v2",
        facts={"entity_title": "Ship it"}, refs=["watch:watch-review"],
    )

    watches = client.get("/api/automations/watches")
    assert watches.status_code == 200
    assert watches.json()["watches"][0]["last_success_at"]
    events = client.get("/api/automations/events?event_type=github.pr.review_requested")
    assert events.status_code == 200
    assert len(events.json()["events"]) == 1
    assert events.json()["events"][0]["id"] == event["id"]
    reactions = client.get("/api/automations/reactions")
    assert reactions.status_code == 200
    assert reactions.json()["reactions"][0]["id"] == "reaction-review"

    process = client.post("/api/automations/reactions/process", json={"limit": 10})
    assert process.status_code == 200
    assert process.json()["projections"][0]["reaction_id"] == "reaction-review"


# --- from tests/unit/test_mcp_registration_characterization.py ---
class TestReactionsToolNames:
    """Pin the Watch/Reaction tool names from the reactions family."""

    def test_reactions_tool_names(self):
        """The reactions family registers exactly these tool names."""
        tool_names = sorted(t["name"] for t in reactions.TOOLS)
        assert tool_names == [
            "event.list",
            "reaction.create",
            "reaction.list",
            "reaction.presets",
            "reaction.process",
            "reaction.set_enabled",
            "watch.create",
            "watch.list",
            "watch.preview",
            "watch.refresh",
            "watch.set_enabled",
        ]

    def test_every_reactions_tool_has_a_valid_schema(self):
        """Every reactions tool carries name, description, and inputSchema."""
        for tool in reactions.TOOLS:
            assert "name" in tool, "tool missing name"
            assert "description" in tool, f"{tool.get('name')} missing description"
            assert "inputSchema" in tool, f"{tool['name']} missing inputSchema"
            schema = tool["inputSchema"]
            assert schema.get("type") == "object", f"{tool['name']} schema type != object"
            assert "properties" in schema, f"{tool['name']} schema missing properties"

    def test_watch_create_schema_shape(self):
        """Pin watch.create as the representative schema (the tool the
        graduation will extend with Project-scoped Watch support)."""
        watch_create = next(
            t for t in reactions.TOOLS if t["name"] == "watch.create"
        )
        schema = watch_create["inputSchema"]
        props = schema["properties"]
        assert "connector_id" in props
        assert "query_kind" in props
        assert "name" in props
        assert "query" in props
        assert props["connector_id"]["enum"] == ["gh", "github", "jira"]
        assert props["query_kind"]["enum"] == ["pull_requests", "issues"]
        assert set(schema["required"]) == {"connector_id", "query_kind"}

    def test_reactions_tools_appear_in_aggregated_catalogue(self):
        """The aggregated TOOLS list in tools.py includes reactions tools."""
        from holdspeak.mcp.tools import TOOLS as ALL_TOOLS
        all_names = {t["name"] for t in ALL_TOOLS}
        reactions_names = {t["name"] for t in reactions.TOOLS}
        assert reactions_names.issubset(all_names), (
            f"Missing from catalogue: {reactions_names - all_names}"
        )


# --- from tests/unit/test_project_mcp_driver.py ---
def test_legacy_family_untouched() -> None:
    """The reactions family tools list is unchanged by this story."""
    from holdspeak.mcp.families import reactions
    legacy_names = {t["name"] for t in reactions.TOOLS}
    # The legacy family must still own these names
    assert "watch.list" in legacy_names
    assert "watch.create" in legacy_names
    assert "watch.refresh" in legacy_names
    assert "reaction.list" in legacy_names
    assert "reaction.create" in legacy_names
    # The graduated tools must NOT be in the legacy family
    assert "project.watch.inspect" not in legacy_names
    assert "project.watch.pause" not in legacy_names
