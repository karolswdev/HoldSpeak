"""Persistence for Watches, the typed service-event ledger, and Reactions."""
from __future__ import annotations

import json
from typing import Any

from .base import BaseRepository


class AutomationRepository(BaseRepository):
    table = "automations"

    @staticmethod
    def _payload(row: Any, *json_fields: str) -> dict[str, Any]:
        value = dict(row)
        for field in json_fields:
            raw = value.pop(f"{field}_json", None)
            try:
                value[field] = json.loads(raw) if raw else {}
            except (TypeError, json.JSONDecodeError):
                value[field] = {}
        for field in ("enabled", "auto_run"):
            if field in value:
                value[field] = bool(value[field])
        return value

    def create_watch(self, *, watch_id: str, connector_id: str, query_kind: str,
                     name: str, query: dict[str, Any], enabled: bool) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO connector_watches
                   (id,connector_id,query_kind,name,query_json,enabled)
                   VALUES (?,?,?,?,?,?)""",
                (watch_id, connector_id, query_kind, name,
                 json.dumps(query, sort_keys=True, separators=(",", ":")), int(enabled)),
            )
        return self.get_watch(watch_id) or {}

    def get_watch(self, watch_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM connector_watches WHERE id=?", (watch_id,)).fetchone()
        return self._payload(row, "query", "snapshot") if row else None

    def list_watches(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM connector_watches ORDER BY created_at,id").fetchall()
        return [self._payload(row, "query", "snapshot") for row in rows]

    def set_watch_enabled(self, watch_id: str, enabled: bool) -> bool:
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE connector_watches SET enabled=?,updated_at=datetime('now') WHERE id=?",
                (int(enabled), watch_id),
            )
        return bool(cur.rowcount)

    def record_refresh(self, watch_id: str, snapshot: dict[str, Any], events: list[dict[str, Any]]) -> None:
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            for event in events:
                self._insert_event(conn, event)
            conn.execute(
                """UPDATE connector_watches SET snapshot_json=?,last_success_at=datetime('now'),
                   last_error=NULL,updated_at=datetime('now') WHERE id=?""",
                (json.dumps(snapshot, sort_keys=True, separators=(",", ":")), watch_id),
            )

    @staticmethod
    def _insert_event(conn: Any, event: dict[str, Any]) -> bool:
        cur = conn.execute(
            """INSERT OR IGNORE INTO service_events
               (id,event_type,event_version,producer,subject_ref,source_revision,
                facts_json,refs_json,principal_kind,principal_identity,
                correlation_id,causation_id,privacy_class)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (event["id"], event["event_type"], event.get("event_version", 1),
             event["producer"], event["subject_ref"], event.get("source_revision", ""),
             json.dumps(event.get("facts", {}), sort_keys=True),
             json.dumps(event.get("refs", []), sort_keys=True),
             event["principal_kind"], event["principal_identity"],
             event.get("correlation_id", ""), event.get("causation_id", ""),
             event.get("privacy_class", "private")),
        )
        return bool(cur.rowcount)

    def append_event(self, event: dict[str, Any]) -> bool:
        with self._connection() as conn:
            return self._insert_event(conn, event)

    def append_event_in_transaction(self, conn: Any, event: dict[str, Any]) -> bool:
        return self._insert_event(conn, event)

    def record_refresh_error(self, watch_id: str, error: str) -> None:
        with self._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET last_error=?,updated_at=datetime('now') WHERE id=?",
                (error[:1000], watch_id),
            )

    def list_events(self, *, event_type: str | None = None, producer: str | None = None,
                    limit: int = 100) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if event_type:
            clauses.append("event_type=?")
            params.append(event_type)
        if producer:
            clauses.append("producer=?")
            params.append(producer)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(max(1, min(int(limit), 500)))
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM service_events{where} ORDER BY created_at DESC,id DESC LIMIT ?",
                params,
            ).fetchall()
        values = [self._payload(row, "facts", "refs") for row in rows]
        for value in values:
            value["event_version"] = int(value["event_version"])
        return values

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM service_events WHERE id=?", (event_id,)).fetchone()
        return self._payload(row, "facts", "refs") if row else None

    def create_reaction(self, *, reaction_id: str, name: str, watch_id: str | None,
                        event_pattern: str, workbench_id: str, title_template: str,
                        auto_run: bool, enabled: bool) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO connector_reactions
                   (id,name,watch_id,event_pattern,workbench_id,title_template,auto_run,enabled)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (reaction_id, name, watch_id, event_pattern, workbench_id,
                 title_template, int(auto_run), int(enabled)),
            )
        return self.get_reaction(reaction_id) or {}

    def get_reaction(self, reaction_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute("SELECT * FROM connector_reactions WHERE id=?", (reaction_id,)).fetchone()
        return self._payload(row) if row else None

    def list_reactions(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute("SELECT * FROM connector_reactions ORDER BY created_at,id").fetchall()
        return [self._payload(row) for row in rows]

    def set_reaction_enabled(self, reaction_id: str, enabled: bool) -> bool:
        with self._connection() as conn:
            cur = conn.execute(
                "UPDATE connector_reactions SET enabled=?,updated_at=datetime('now') WHERE id=?",
                (int(enabled), reaction_id),
            )
        return bool(cur.rowcount)

    def matching_reactions(self, watch_id: str | None, event_type: str) -> list[dict[str, Any]]:
        rows = self.list_reactions()
        return [row for row in rows if row["enabled"] and
                (not row["watch_id"] or row["watch_id"] == watch_id) and
                (row["event_pattern"] == event_type or
                 (row["event_pattern"].endswith(".*") and
                  event_type.startswith(row["event_pattern"][:-1])))]

    def has_projection(self, reaction_id: str, event_id: str) -> bool:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT 1 FROM reaction_event_projections WHERE reaction_id=? AND event_id=?",
                (reaction_id, event_id),
            ).fetchone()
        return row is not None

    def record_projection(self, reaction_id: str, event_id: str, *, item_id: str,
                          operation_id: str | None = None,
                          receipt_id: str | None = None) -> bool:
        with self._connection() as conn:
            cur = conn.execute(
                """INSERT OR IGNORE INTO reaction_event_projections
                   (reaction_id,event_id,item_id,operation_id,receipt_id)
                   VALUES (?,?,?,?,?)""",
                (reaction_id, event_id, item_id, operation_id, receipt_id),
            )
        return bool(cur.rowcount)

    def list_reaction_projections(self, reaction_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        """Return durable Reaction deliveries joined to their source events."""
        with self._connection() as conn:
            rows = conn.execute(
                """SELECT p.reaction_id,p.event_id,p.item_id,p.operation_id,p.receipt_id,p.projected_at,
                          e.event_type,e.subject_ref,e.source_revision,e.facts_json,e.refs_json,
                          e.correlation_id,e.causation_id,e.created_at AS event_created_at
                   FROM reaction_event_projections p
                   JOIN service_events e ON e.id=p.event_id
                   WHERE p.reaction_id=?
                   ORDER BY p.projected_at DESC,p.event_id DESC LIMIT ?""",
                (reaction_id, max(1, min(int(limit), 500))),
            ).fetchall()
        return [self._payload(row, "facts", "refs") for row in rows]

    # ── HS-159-01: WatchSpec@1 graduation CRUD ─────────────────────────

    def update_watch_spec(
        self,
        watch_id: str,
        *,
        schema_version: str | None = None,
        project_id: str | None = None,
        intent: str | None = None,
        provider_connection_id: str | None = None,
        subject_kind: str | None = None,
        trigger_kind: str | None = None,
        trigger_json: str | None = None,
        mode: str | None = None,
        state: str | None = None,
        revision: int | None = None,
        baseline_state: str | None = None,
        test_state: str | None = None,
        test_result_json: str | None = None,
        last_test_at: str | None = None,
        next_evaluation_at: str | None = None,
        last_evaluated_at: str | None = None,
    ) -> bool:
        """Update graduation columns on a connector_watches row (named-column)."""
        sets: list[str] = []
        params: list[Any] = []
        for col, val in (
            ("schema_version", schema_version),
            ("project_id", project_id),
            ("intent", intent),
            ("provider_connection_id", provider_connection_id),
            ("subject_kind", subject_kind),
            ("trigger_kind", trigger_kind),
            ("trigger_json", trigger_json),
            ("mode", mode),
            ("state", state),
            ("revision", revision),
            ("baseline_state", baseline_state),
            ("test_state", test_state),
            ("test_result_json", test_result_json),
            ("last_test_at", last_test_at),
            ("next_evaluation_at", next_evaluation_at),
            ("last_evaluated_at", last_evaluated_at),
        ):
            if val is not None:
                sets.append(f"{col}=?")
                params.append(val)
        if not sets:
            return False
        sets.append("updated_at=datetime('now')")
        params.append(watch_id)
        with self._connection() as conn:
            cur = conn.execute(
                f"UPDATE connector_watches SET {','.join(sets)} WHERE id=?",
                params,
            )
        return bool(cur.rowcount)

    # ── Setup sessions (§9.1) ──────────────────────────────────────────

    def create_setup_session(
        self,
        *,
        session_id: str,
        state: str = "active",
        stage: str = "",
        draft_schema: str = "",
        draft_json: str = "{}",
        project_id: str | None = None,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO project_setup_sessions
                   (id,state,stage,draft_schema,draft_json,project_id,expires_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (session_id, state, stage, draft_schema, draft_json,
                 project_id, expires_at),
            )
        return self.get_setup_session(session_id) or {}

    def get_setup_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_setup_sessions WHERE id=?",
                (session_id,),
            ).fetchone()
        return self._payload(row, "draft") if row else None

    def list_setup_sessions(self, *, state: str | None = None) -> list[dict[str, Any]]:
        where = " WHERE state=?" if state else ""
        params: list[Any] = [state] if state else []
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM project_setup_sessions{where} ORDER BY created_at DESC",
                params,
            ).fetchall()
        return [self._payload(row, "draft") for row in rows]

    # ── Setup answers (§9.1) ───────────────────────────────────────────

    def create_setup_answer(
        self,
        *,
        answer_id: str,
        session_id: str,
        question_id: str,
        answer_schema: str = "",
        answer_json: str = "{}",
        revision: int = 1,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO project_setup_answers
                   (id,session_id,question_id,answer_schema,answer_json,revision)
                   VALUES (?,?,?,?,?,?)""",
                (answer_id, session_id, question_id, answer_schema,
                 answer_json, revision),
            )
            row = conn.execute(
                "SELECT * FROM project_setup_answers WHERE id=?",
                (answer_id,),
            ).fetchone()
        return self._payload(row, "answer") if row else {}

    def list_setup_answers(self, session_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM project_setup_answers WHERE session_id=? "
                "ORDER BY question_id, revision",
                (session_id,),
            ).fetchall()
        return [self._payload(row, "answer") for row in rows]

    # ── Watch setup proposals (§9.1) ───────────────────────────────────

    def create_setup_proposal(
        self,
        *,
        proposal_id: str,
        session_id: str,
        provider_id: str = "",
        connection_id: str | None = None,
        spec_schema: str = "",
        spec_json: str = "{}",
        rationale_json: str = "{}",
        state: str = "proposed",
        test_state: str = "",
        test_result_json: str | None = None,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO watch_setup_proposals
                   (id,session_id,provider_id,connection_id,spec_schema,
                    spec_json,rationale_json,state,test_state,test_result_json)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (proposal_id, session_id, provider_id, connection_id,
                 spec_schema, spec_json, rationale_json, state,
                 test_state, test_result_json),
            )
        return self.get_setup_proposal(proposal_id) or {}

    def get_setup_proposal(self, proposal_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM watch_setup_proposals WHERE id=?",
                (proposal_id,),
            ).fetchone()
        return self._payload(row, "spec", "rationale", "test_result") if row else None

    # ── Provider connections (§9.2) ────────────────────────────────────

    def create_provider_connection(
        self,
        *,
        connection_id: str,
        provider_id: str = "",
        transport: str = "",
        external_connection_ref: str = "",
        state: str = "",
        capability_manifest_json: str = "{}",
        capability_revision: int = 0,
        discovery_state: str = "",
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO watch_provider_connections
                   (id,provider_id,transport,external_connection_ref,state,
                    capability_manifest_json,capability_revision,discovery_state)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (connection_id, provider_id, transport, external_connection_ref,
                 state, capability_manifest_json, capability_revision,
                 discovery_state),
            )
        return self.get_provider_connection(connection_id) or {}

    def get_provider_connection(self, connection_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM watch_provider_connections WHERE id=?",
                (connection_id,),
            ).fetchone()
        return self._payload(row, "capability_manifest") if row else None

    def list_provider_connections(self, *, provider_id: str | None = None) -> list[dict[str, Any]]:
        where = " WHERE provider_id=?" if provider_id else ""
        params: list[Any] = [provider_id] if provider_id else []
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM watch_provider_connections{where} "
                "ORDER BY created_at DESC",
                params,
            ).fetchall()
        return [self._payload(row, "capability_manifest") for row in rows]

    # ── Watch rules (§9.4) ─────────────────────────────────────────────

    def create_rule(
        self,
        *,
        rule_id: str,
        watch_id: str,
        ordinal: int = 0,
        condition_schema: str = "",
        condition_json: str = "{}",
        action_schema: str = "",
        action_json: str = "{}",
        enabled: bool = True,
        revision: int = 0,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO watch_rules
                   (id,watch_id,ordinal,condition_schema,condition_json,
                    action_schema,action_json,enabled,revision)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (rule_id, watch_id, ordinal, condition_schema,
                 condition_json, action_schema, action_json,
                 int(enabled), revision),
            )
        return self.get_rule(rule_id) or {}

    def get_rule(self, rule_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM watch_rules WHERE id=?",
                (rule_id,),
            ).fetchone()
        return self._payload(row, "condition", "action") if row else None

    def list_rules(self, watch_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM watch_rules WHERE watch_id=? ORDER BY ordinal",
                (watch_id,),
            ).fetchall()
        return [self._payload(row, "condition", "action") for row in rows]

    # ── Watch evaluations (§9.4) ───────────────────────────────────────

    def create_evaluation(
        self,
        *,
        evaluation_id: str,
        watch_id: str,
        watch_revision: int = 0,
        provider_capability_revision: int = 0,
        source_revision: str = "",
        trigger_kind: str = "",
        state: str = "",
        matched_rule_ids_json: str = "[]",
        observation_ids_json: str = "[]",
        started_at: str | None = None,
        completed_at: str | None = None,
        error_code: str | None = None,
        error_detail: str | None = None,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO watch_evaluations
                   (id,watch_id,watch_revision,provider_capability_revision,
                    source_revision,trigger_kind,state,matched_rule_ids_json,
                    observation_ids_json,started_at,completed_at,
                    error_code,error_detail)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (evaluation_id, watch_id, watch_revision,
                 provider_capability_revision, source_revision, trigger_kind,
                 state, matched_rule_ids_json, observation_ids_json,
                 started_at, completed_at, error_code, error_detail),
            )
        return self.get_evaluation(evaluation_id) or {}

    def get_evaluation(self, evaluation_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM watch_evaluations WHERE id=?",
                (evaluation_id,),
            ).fetchone()
        return self._payload(row, "matched_rule_ids", "observation_ids") if row else None

    def list_evaluations(self, watch_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM watch_evaluations WHERE watch_id=? "
                "ORDER BY started_at DESC LIMIT ?",
                (watch_id, max(1, min(int(limit), 500))),
            ).fetchall()
        return [self._payload(row, "matched_rule_ids", "observation_ids") for row in rows]

    # ── Watch effects (§9.4) ───────────────────────────────────────────

    def create_effect(
        self,
        *,
        effect_id: str,
        evaluation_id: str,
        rule_id: str,
        action_kind: str = "",
        target_ref: str = "",
        idempotency_key: str,
        arguments_sha256: str = "",
        state: str = "",
        operation_id: str | None = None,
        receipt_id: str | None = None,
        result_ref: str | None = None,
        verification_state: str = "",
        error_code: str | None = None,
        error_detail: str | None = None,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO watch_effects
                   (id,evaluation_id,rule_id,action_kind,target_ref,
                    idempotency_key,arguments_sha256,state,
                    operation_id,receipt_id,result_ref,verification_state,
                    error_code,error_detail)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (effect_id, evaluation_id, rule_id, action_kind, target_ref,
                 idempotency_key, arguments_sha256, state,
                 operation_id, receipt_id, result_ref, verification_state,
                 error_code, error_detail),
            )
        return self.get_effect(effect_id) or {}

    def get_effect(self, effect_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM watch_effects WHERE id=?",
                (effect_id,),
            ).fetchone()
        return dict(row) if row else None

    def list_effects(self, evaluation_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM watch_effects WHERE evaluation_id=? "
                "ORDER BY created_at",
                (evaluation_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    # ── Project sources (§5.4) ─────────────────────────────────────────

    def create_project_source(
        self,
        *,
        source_id: str,
        project_id: str,
        source_ref: str = "",
        label: str = "",
        semantic_role: str = "",
        materiality_policy_json: str = "{}",
        enabled: bool = True,
        freshness_state: str = "",
        revision: int = 0,
    ) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                """INSERT INTO project_sources
                   (id,project_id,source_ref,label,semantic_role,
                    materiality_policy_json,enabled,freshness_state,revision)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (source_id, project_id, source_ref, label, semantic_role,
                 materiality_policy_json, int(enabled), freshness_state,
                 revision),
            )
        return self.get_project_source(source_id) or {}

    def get_project_source(self, source_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM project_sources WHERE id=?",
                (source_id,),
            ).fetchone()
        return self._payload(row, "materiality_policy") if row else None

    def list_project_sources(self, project_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM project_sources WHERE project_id=? "
                "ORDER BY created_at",
                (project_id,),
            ).fetchall()
        return [self._payload(row, "materiality_policy") for row in rows]
