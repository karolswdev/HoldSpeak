"""HS-152-02: Thread tool gate truth table, executor, classification census.

Eight truth-table rows; admit creates a kernel child whose parent is the
turn's operation; hold -> awaiting_decision -> approve executes with a receipt;
deny -> tool_denied; Allow-always writes one policy row and the next identical
call auto-admits; Allow-once writes none; elicitation hold + answer re-dispatch;
people tool result -> sensitive True; cancel mid-execute -> discarded;
classification fail-closed (every TOOLS name classified).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.thread_tools import (
    EXCLUDED_TOOLS,
    TOOL_NAMES,
    ThreadToolExecutor,
    ToolCallHandle,
    ToolResult,
    resolve_tool_decision,
    tool_class,
    tool_schemas_for,
    tool_sensitive,
)


OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "test_gate.db")


def _executor(
    db: Database,
    *,
    control_mode: str = "yolo",
    dispatch_result: Any = {"ok": True},
) -> ThreadToolExecutor:
    """Build a test executor with a fake dispatch function."""
    def fake_dispatch(name: str, args: dict, principal: Principal) -> Any:
        return dispatch_result

    return ThreadToolExecutor(
        db,
        dispatch_fn=fake_dispatch,
        principal=OWNER,
        control_mode_fn=lambda: control_mode,
    )


def _call(name: str = "desk.list", args: dict | None = None) -> dict[str, Any]:
    return {
        "id": f"call-{name.replace('.', '-')}",
        "name": name,
        "arguments": args or {},
    }


# ---------------------------------------------------------------------------
# Truth table: 8 rows
# ---------------------------------------------------------------------------

class TestTruthTable:
    """The 8-row truth table from the settled design D2."""

    def test_row1_allow_policy_any_mode_any_class_admits(self, db: Database) -> None:
        """policy=allow, control_mode=any, class=any -> admit."""
        assert resolve_tool_decision("allow", "safe", "effect_proposal") == "admit"
        assert resolve_tool_decision("allow", "neutral", "evidence_read") == "admit"
        assert resolve_tool_decision("allow", "yolo", "candidate_builder") == "admit"

    def test_row2_deny_policy_any_mode_any_class_denies(self, db: Database) -> None:
        """policy=deny, control_mode=any, class=any -> deny."""
        assert resolve_tool_decision("deny", "safe", "evidence_read") == "deny"
        assert resolve_tool_decision("deny", "neutral", "effect_proposal") == "deny"
        assert resolve_tool_decision("deny", "yolo", "candidate_builder") == "deny"

    def test_row3_ask_policy_any_mode_any_class_holds(self, db: Database) -> None:
        """policy=ask, control_mode=any, class=any -> hold."""
        assert resolve_tool_decision("ask", "safe", "evidence_read") == "hold"
        assert resolve_tool_decision("ask", "neutral", "effect_proposal") == "hold"
        assert resolve_tool_decision("ask", "yolo", "candidate_builder") == "hold"

    def test_row4_unset_yolo_any_class_admits(self, db: Database) -> None:
        """policy=unset, control_mode=yolo, class=any -> admit."""
        assert resolve_tool_decision(None, "yolo", "evidence_read") == "admit"
        assert resolve_tool_decision(None, "yolo", "candidate_builder") == "admit"
        assert resolve_tool_decision(None, "yolo", "effect_proposal") == "admit"

    def test_row5_unset_neutral_read_or_candidate_admits(self, db: Database) -> None:
        """policy=unset, control_mode=neutral, evidence_read|candidate_builder -> admit."""
        assert resolve_tool_decision(None, "neutral", "evidence_read") == "admit"
        assert resolve_tool_decision(None, "neutral", "candidate_builder") == "admit"

    def test_row6_unset_neutral_effect_holds(self, db: Database) -> None:
        """policy=unset, control_mode=neutral, effect_proposal -> hold."""
        assert resolve_tool_decision(None, "neutral", "effect_proposal") == "hold"

    def test_row7_unset_safe_read_admits(self, db: Database) -> None:
        """policy=unset, control_mode=safe, evidence_read -> admit."""
        assert resolve_tool_decision(None, "safe", "evidence_read") == "admit"

    def test_row8_unset_safe_candidate_or_effect_holds(self, db: Database) -> None:
        """policy=unset, control_mode=safe, candidate_builder|effect_proposal -> hold."""
        assert resolve_tool_decision(None, "safe", "candidate_builder") == "hold"
        assert resolve_tool_decision(None, "safe", "effect_proposal") == "hold"


# ---------------------------------------------------------------------------
# Executor: admit creates a kernel child whose parent is the turn's operation
# ---------------------------------------------------------------------------

class TestAdmitCreatesKernelChild:
    def test_admit_yolo_creates_handle_with_child(self, db: Database) -> None:
        executor = _executor(db, control_mode="yolo")
        handle = executor.admit("turn-op-1", "th_test1", _call("desk.list"))
        assert handle.state == "admitted"
        assert handle.kernel_child_id.startswith("child-")
        assert handle.turn_operation_id == "turn-op-1"
        assert handle.thread_id == "th_test1"
        assert handle.tool_class == "evidence_read"

    def test_admit_creates_tool_turn_rows_via_broker(self, db: Database) -> None:
        """When a broker is wired, admit goes through broker.submit."""
        submitted: list[dict] = []

        class FakeBroker:
            def submit(self, request: dict, principal: Principal) -> dict:
                submitted.append(request)
                return {"operation_id": "broker-child-123"}
            store = True  # pass hasattr check

        executor = ThreadToolExecutor(
            db,
            dispatch_fn=lambda n, a, p: {"ok": True},
            principal=OWNER,
            control_mode_fn=lambda: "yolo",
            broker=FakeBroker(),
        )
        handle = executor.admit("turn-op-2", "th_test2", _call("desk.get"))
        assert handle.kernel_child_id == "broker-child-123"
        assert len(submitted) == 1
        assert submitted[0]["arguments"]["tool"] == "desk.get"


# ---------------------------------------------------------------------------
# Hold -> awaiting_decision -> approve executes with a receipt
# ---------------------------------------------------------------------------

class TestHoldAndApprove:
    def test_hold_then_approve_executes(self, db: Database) -> None:
        executor = _executor(db, control_mode="safe")
        handle = executor.admit("turn-op-3", "th_test3", _call("desk.create"))
        assert handle.state == "awaiting_decision"
        executor.decide(handle, "approve")
        assert handle.state == "admitted"
        result = executor.execute(handle)
        assert result.kind == "data"
        assert result.receipt_id.startswith("tr-")
        assert handle.state == "completed"


# ---------------------------------------------------------------------------
# Deny -> tool_denied
# ---------------------------------------------------------------------------

class TestDenyResult:
    def test_deny_policy_produces_tool_denied(self, db: Database) -> None:
        db.threads.create_thread(title="T")
        threads = db.threads.list()
        thread = threads[0]
        db.threads.set_tool_policy(thread.id, "desk.list", "deny")
        executor = _executor(db, control_mode="yolo")
        handle = executor.admit("turn-op-4", thread.id, _call("desk.list"))
        assert handle.state == "denied"
        result = executor.execute(handle)
        assert result.kind == "tool_denied"
        assert result.payload == {"error": "tool_denied"}


# ---------------------------------------------------------------------------
# Allow-always writes one policy row; next identical call auto-admits
# ---------------------------------------------------------------------------

class TestAllowAlways:
    def test_allow_always_writes_policy_and_next_auto_admits(self, db: Database) -> None:
        thread = db.threads.create_thread(title="AA")
        # First call in safe mode -> hold
        executor = _executor(db, control_mode="safe")
        handle = executor.admit("turn-op-5", thread.id, _call("desk.create"))
        assert handle.state == "awaiting_decision"

        # Allow-always: caller writes policy row then approves
        db.threads.set_tool_policy(thread.id, "desk.create", "allow")
        executor.decide(handle, "approve")
        assert handle.state == "admitted"

        # Next identical call auto-admits because policy=allow
        handle2 = executor.admit("turn-op-6", thread.id, _call("desk.create"))
        assert handle2.state == "admitted"

        # Verify policy row exists
        policy = db.threads.effective_tool_policy(thread.id, "desk.create")
        assert policy == "allow"


# ---------------------------------------------------------------------------
# Allow-once writes no policy row
# ---------------------------------------------------------------------------

class TestAllowOnce:
    def test_allow_once_does_not_write_policy(self, db: Database) -> None:
        thread = db.threads.create_thread(title="AO")
        executor = _executor(db, control_mode="safe")
        handle = executor.admit("turn-op-7", thread.id, _call("desk.update"))
        assert handle.state == "awaiting_decision"

        # Allow-once: just approve, no policy row
        executor.decide(handle, "approve")
        assert handle.state == "admitted"

        # Next identical call still holds because no policy was written
        handle2 = executor.admit("turn-op-8", thread.id, _call("desk.update"))
        assert handle2.state == "awaiting_decision"

        # Verify no policy row
        policy = db.threads.effective_tool_policy(thread.id, "desk.update")
        assert policy is None


# ---------------------------------------------------------------------------
# Elicitation hold + answer re-dispatch
# ---------------------------------------------------------------------------

class TestElicitation:
    def test_elicitation_holds_and_answer_redispatches(self, db: Database) -> None:
        elicit_schema = {"type": "object", "properties": {"confirm": {"type": "boolean"}}}
        call_count = [0]

        def eliciting_dispatch(name: str, args: dict, principal: Principal) -> Any:
            call_count[0] += 1
            if call_count[0] == 1:
                return {"elicit": {"schema": elicit_schema, "prompt": "Confirm?"}}
            return {"confirmed": True, "answer_received": args.get("__answer")}

        executor = ThreadToolExecutor(
            db,
            dispatch_fn=eliciting_dispatch,
            principal=OWNER,
            control_mode_fn=lambda: "yolo",
        )
        handle = executor.admit("turn-op-9", "th_elicit", _call("desk.verb"))
        assert handle.state == "admitted"

        # First execution returns elicitation
        result = executor.execute(handle)
        assert result.kind == "elicitation"
        assert result.elicitation == {"schema": elicit_schema, "prompt": "Confirm?"}
        assert handle.state == "awaiting_decision"

        # Resolve with answer
        executor.decide(handle, "approve", answer={"confirm": True})
        assert handle.state == "admitted"
        assert handle.answer == {"confirm": True}

        # Re-execute with the answer
        result2 = executor.execute(handle)
        assert result2.kind == "data"
        assert result2.payload["answer_received"] == {"confirm": True}
        assert call_count[0] == 2


# ---------------------------------------------------------------------------
# People tool result -> sensitive True
# ---------------------------------------------------------------------------

class TestPeopleSensitive:
    def test_people_tool_result_is_sensitive(self, db: Database) -> None:
        executor = _executor(db, control_mode="yolo", dispatch_result={"readiness": "ok"})
        handle = executor.admit("turn-op-10", "th_people", _call("people.readiness"))
        assert handle.sensitive is True
        result = executor.execute(handle)
        assert result.sensitive is True

    def test_non_people_tool_result_is_not_sensitive(self, db: Database) -> None:
        executor = _executor(db, control_mode="yolo")
        handle = executor.admit("turn-op-11", "th_desk", _call("desk.list"))
        assert handle.sensitive is False
        result = executor.execute(handle)
        assert result.sensitive is False


# ---------------------------------------------------------------------------
# Cancel mid-execute -> discarded
# ---------------------------------------------------------------------------

class TestCancelMidExecute:
    def test_cancel_before_execute_discards(self, db: Database) -> None:
        executor = _executor(db, control_mode="yolo")
        handle = executor.admit("turn-op-12", "th_cancel", _call("desk.list"))
        executor.cancel(handle)
        result = executor.execute(handle)
        assert result.kind == "cancelled"
        assert handle.state == "discarded"


# ---------------------------------------------------------------------------
# Classification fail-closed: every TOOLS name is classified
# ---------------------------------------------------------------------------

class TestClassificationCensus:
    def test_every_mcp_tool_is_classified(self) -> None:
        """Fail-closed: if a new tool is added to TOOLS without being
        classified in the map, this test fails."""
        from holdspeak.mcp.tools import TOOLS as MCP_TOOLS

        mcp_names = {t["name"] for t in MCP_TOOLS}
        # #694: an excluded tool is classified too -- as egress, authority or
        # config in the owner's table (mcp/tool_authority.py).
        unclassified = mcp_names - TOOL_NAMES - EXCLUDED_TOOLS
        assert unclassified == set(), (
            f"Unclassified MCP tools (add them to thread_tools._TOOL_CLASSES): "
            f"{sorted(unclassified)}"
        )

    def test_no_phantom_classifications(self) -> None:
        """No classifications for tools that do not exist in the MCP catalogue."""
        from holdspeak.mcp.tools import TOOLS as MCP_TOOLS

        mcp_names = {t["name"] for t in MCP_TOOLS}
        phantom = TOOL_NAMES - mcp_names
        assert phantom == set(), (
            f"Phantom tool classifications (remove from thread_tools._TOOL_CLASSES): "
            f"{sorted(phantom)}"
        )

    def test_every_dispatched_tool_has_an_authority_row(self) -> None:
        """#694, the owner's ruling (2026-09-29): ONE table classes EVERY tool
        the MCP dispatch serves (the public list and every family) as work,
        egress, authority or config. A tool with no row fails here."""
        from holdspeak.mcp.tool_authority import TOOL_AUTHORITY
        from holdspeak.mcp.tools import FAMILIES, TOOLS as MCP_TOOLS

        dispatched = {t["name"] for t in MCP_TOOLS} | {t["name"] for f in FAMILIES for t in f.TOOLS}
        assert dispatched == set(TOOL_AUTHORITY), (
            f"unclassified={sorted(dispatched - set(TOOL_AUTHORITY))} "
            f"phantom={sorted(set(TOOL_AUTHORITY) - dispatched)}")
        assert set(TOOL_AUTHORITY.values()) <= {"work", "egress", "authority", "config"}

    #: The owner's named examples, each in its class (the ruling's words).
    RULED = {
        "egress": {"channel.send", "nudge.send"},
        "authority": {"project.archive", "project.configure_steward"},
        "config": {"model_library.define_endpoint", "inference_assignment.set", "inference_assignment.clear",
                   "project.setup.finalize", "thought.replace_default_context", "settings.update",
                   "provider.jira_add_connection"},
        "work": {"people.note.create", "desk.create", "project.draft_update", "zone.file", "channel.prepare",
                 "project.setup.start", "project.setup.answer"},  # a setup's drafting (prepare-then-press)
    }

    #: #694 (Codex Astra counsel r4, law 9): every function that WRITES a
    #: delegation or a schedule's authority, found by its writer (not by a tool
    #: name), and the MCP tools that reach it. A new writer fails the census
    #: until it is pinned here with its tools.
    MINTERS: dict[tuple[str, str], frozenset[str]] = {
        # the workbench schedule delegation (ScheduleDelegationService)
        ("holdspeak/services/schedule_delegation.py", "enable_from_owner"): frozenset(),  # no caller today
        ("holdspeak/services/schedule_delegation.py", "enable_from_owner_in_transaction"):
            frozenset({"workbench.create", "workbench.update"}),
        ("holdspeak/services/workbench_service.py", "create_workbench"): frozenset({"workbench.create"}),
        ("holdspeak/services/workbench_service.py", "update_workbench"): frozenset({"workbench.update"}),
        # the recording delegation receipt
        ("holdspeak/services/scheduled_recording_service.py", "create_schedule"):
            frozenset({"scheduled_recording.create"}),
        ("holdspeak/services/scheduled_recording_service.py", "update_schedule"):
            frozenset({"scheduled_recording.update"}),
        # the steward's unattended runs (its policy)
        ("holdspeak/services/steward_contract.py", "configure_policy"): frozenset({"project.configure_steward"}),
        ("holdspeak/services/steward_contract.py", "effect"): frozenset({"project.configure_steward"}),
        ("holdspeak/db/steward.py", "insert_policy"): frozenset({"project.configure_steward"}),
        ("holdspeak/db/steward.py", "insert_policy_in_transaction"): frozenset({"project.configure_steward"}),
        ("holdspeak/db/steward.py", "update_policy"): frozenset({"project.configure_steward"}),
        ("holdspeak/db/steward.py", "update_policy_in_transaction"): frozenset({"project.configure_steward"}),
        # the agent grants: HTTP only (/api/mcp/delegations), no MCP tool
        ("holdspeak/kernel/desk.py", "grant_effect"): frozenset(),
        ("holdspeak/kernel/desk.py", "effect"): frozenset(),
        ("holdspeak/kernel/project_grant.py", "grant_effect"): frozenset(),
        ("holdspeak/kernel/project_grant.py", "effect"): frozenset(),
    }

    def test_every_delegation_or_schedule_writer_is_authority_for_a_thread(self) -> None:
        import ast
        from pathlib import Path

        from holdspeak.mcp.tool_authority import ARGUMENT_AUTHORITY, TOOL_AUTHORITY

        repo = Path(__file__).resolve().parents[2]
        found: set[tuple[str, str]] = set()
        for path in sorted((repo / "holdspeak").rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for fn in ast.walk(tree):
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for node in ast.walk(fn):
                    minted = False
                    if isinstance(node, ast.Call):
                        callee = getattr(node.func, "attr", getattr(node.func, "id", ""))
                        minted = callee == "enable_from_owner_in_transaction" or any(
                            kw.arg == "unattended_enabled"
                            and not (isinstance(kw.value, ast.Constant) and not kw.value.value)
                            for kw in node.keywords)
                    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                        minted = node.value == "delegation_enabled" or (
                            "INSERT INTO kernel_" in node.value and "delegations" in node.value)
                    elif isinstance(node, ast.JoinedStr):
                        text = "".join(v.value for v in node.values if isinstance(v, ast.Constant))
                        minted = "INSERT INTO " in text and "agent_identity" in text and "delegator" in text
                    if minted:
                        found.add((path.relative_to(repo).as_posix(), fn.name))
                        break
        assert found == set(self.MINTERS), (
            f"new writers={sorted(found - set(self.MINTERS))} gone={sorted(set(self.MINTERS) - found)}")
        for site, tools in self.MINTERS.items():
            for tool in tools:
                assert TOOL_AUTHORITY[tool] != "work" or tool in ARGUMENT_AUTHORITY, (site, tool)

    def test_the_mixed_tools_decide_by_their_arguments(self) -> None:
        from holdspeak.mcp.tool_authority import call_class

        assert call_class("workbench.create", {"name": "x", "fields": {"schedule_enabled": True}}) == "authority"
        assert call_class("workbench.create", {"name": "x", "fields": {"recipe_id": "r"}}) == "work"
        assert call_class("workbench.update", {"workbench_id": "w", "fields": {"schedule": "0 9 * * 1"}}) == "authority"
        assert call_class("workbench.update", {"workbench_id": "w", "fields": {"name": "y"}}) == "work"
        assert call_class("scheduled_recording.create", {"cron_expr": "0 9 * * 1", "enabled": True}) == "authority"
        assert call_class("scheduled_recording.create", {"calendar_event_id": "e"}) == "authority"
        assert call_class("scheduled_recording.create", {"cron_expr": "0 9 * * 1"}) == "work"
        assert call_class("scheduled_recording.update", {"schedule_id": "s", "enabled": True}) == "authority"
        assert call_class("scheduled_recording.update", {"schedule_id": "s", "title": "t"}) == "work"

    def test_the_rulings_examples_are_in_their_class(self) -> None:
        from holdspeak.mcp.tool_authority import TOOL_AUTHORITY

        for cls, names in self.RULED.items():
            for name in names:
                assert TOOL_AUTHORITY[name] == cls, (name, TOOL_AUTHORITY[name], cls)

    def test_an_excluded_tool_is_never_a_thread_tool(self) -> None:
        """A thread runs its tools as the owner: egress, authority and config
        are never in the table, never in a palette, refused by name."""
        from holdspeak.mcp.tool_authority import TOOL_AUTHORITY
        from holdspeak.services.thread_tools import CHAT_PALETTE
        from holdspeak.services.thread_modes import MODE_SEEDS

        assert EXCLUDED_TOOLS == {n for n, c in TOOL_AUTHORITY.items() if c != "work"}
        assert TOOL_NAMES == {n for n, c in TOOL_AUTHORITY.items() if c == "work"}
        assert not (EXCLUDED_TOOLS & CHAT_PALETTE)
        for mode in MODE_SEEDS:
            assert not (EXCLUDED_TOOLS & mode.tools), mode.id
        for name in EXCLUDED_TOOLS:
            with pytest.raises(ValueError, match="the owner's press"):
                tool_class(name)

    def test_every_owner_press_descriptor_is_excluded(self) -> None:
        """A declared owner press (a Send, a nudge, the destinations, the
        delivery mark) is never classed work."""
        import holdspeak.operations as operations

        for descriptor in operations.DESCRIPTORS:
            if descriptor.owner_press:
                for exposure in descriptor.exposure:
                    if exposure.startswith("mcp:"):
                        assert exposure[len("mcp:"):] in EXCLUDED_TOOLS, descriptor.name

    def test_the_kernel_refuses_an_agent_by_one_set(self) -> None:
        """The codec's non-owner refusal reads one declared set (#694 r2)."""
        import inspect

        from holdspeak.kernel import project as rooms
        from holdspeak.kernel.project_codec import ProjectCodec

        assert "rooms.OWNER_ONLY_OPERATIONS" in inspect.getsource(ProjectCodec.authorize)
        assert rooms.OWNER_ONLY_OPERATIONS == (
            rooms.PROJECT_KERNEL_OPERATIONS - rooms.PROJECT_GRANT_OPERATIONS - rooms.AGENT_PREPARE_OPERATIONS)

    def test_unclassified_tool_raises(self) -> None:
        with pytest.raises(ValueError, match="Unclassified tool"):
            tool_class("nonexistent.tool")

    def test_tool_class_returns_valid_class(self) -> None:
        assert tool_class("desk.list") == "evidence_read"
        assert tool_class("desk.create") == "effect_proposal"
        assert tool_class("monday_brief.generate") == "candidate_builder"


# ---------------------------------------------------------------------------
# Tool schemas rendering
# ---------------------------------------------------------------------------

class TestToolSchemas:
    def test_renders_subset_of_tools(self) -> None:
        schemas = tool_schemas_for({"desk.list", "desk.get"})
        assert len(schemas) == 2
        names = {s["function"]["name"] for s in schemas}
        assert names == {"desk.list", "desk.get"}
        for s in schemas:
            assert s["type"] == "function"
            assert "parameters" in s["function"]

    def test_empty_set_returns_empty(self) -> None:
        schemas = tool_schemas_for(set())
        assert schemas == []


# ---------------------------------------------------------------------------
# Thread tool policy repository
# ---------------------------------------------------------------------------

class TestToolPolicyRepository:
    def test_set_and_effective(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Policy")
        db.threads.set_tool_policy(thread.id, "desk.list", "allow")
        assert db.threads.effective_tool_policy(thread.id, "desk.list") == "allow"

    def test_newest_wins(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Newest")
        db.threads.set_tool_policy(thread.id, "desk.list", "allow")
        time.sleep(0.01)  # Ensure distinct set_at
        db.threads.set_tool_policy(thread.id, "desk.list", "deny")
        assert db.threads.effective_tool_policy(thread.id, "desk.list") == "deny"

    def test_unset_returns_none(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Unset")
        assert db.threads.effective_tool_policy(thread.id, "desk.list") is None

    def test_invalid_decision_raises(self, db: Database) -> None:
        thread = db.threads.create_thread(title="Invalid")
        with pytest.raises(ValueError, match="Invalid tool policy decision"):
            db.threads.set_tool_policy(thread.id, "desk.list", "invalid")


# ---------------------------------------------------------------------------
# on_decided callback hook
# ---------------------------------------------------------------------------

class TestOnDecidedHook:
    def test_on_decided_called(self, db: Database) -> None:
        decided_ids: list[str] = []
        executor = _executor(db, control_mode="safe")
        executor.on_decided = lambda cid: decided_ids.append(cid)
        handle = executor.admit("turn-op-hook", "th_hook", _call("desk.create"))
        assert handle.state == "awaiting_decision"
        executor.decide(handle, "approve")
        assert decided_ids == [handle.call_id]
