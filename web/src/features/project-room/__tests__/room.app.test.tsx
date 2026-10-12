/**
 * The Room app (ProjectRoomCore and its wells): the test diet's vitest
 * successors for the Room's browser rows (owner, 2026-10-11: "each time we
 * run a test suite it fucking takes hours").
 *
 * Each `describe` names the browser test it replaces. The wire is the REAL
 * hub's: every constant below was recorded from a booted hub (the browser
 * tests' own seed helpers, `glass_infra._boot`, the real routes) or from the
 * real service (`ProjectService.room`), not written by hand. Only `apiFetch`
 * is mocked (and `desk/shell`'s window openers, which the Room calls to open
 * OTHER windows). The few answers that were not recorded say where their
 * shape comes from, by file:line.
 */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
import { ProjectRoomCore } from "../ProjectRoomCore";
import { RoomPeopleSection } from "../RoomPeopleSection";
import { ApiError } from "../../../lib/api";
// The final diet lane's recorded wires (scripts/record_room_wires.py: the real
// hub through TestClient on each browser test's own seed; nothing typed).
import U173 from "./room-wires/update173.json";
import C200 from "./room-wires/claims200.json";
import N10 from "./room-wires/nudge10.json";
import H175 from "./room-wires/hs175.json";
import S17 from "./room-wires/sources17.json";
import F17 from "./room-wires/files17.json";

vi.mock("../../../desk/ask", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/ask")>("../../../desk/ask");
  return { ...actual, runAsk: vi.fn() };
});

vi.mock("../../../desk/components/DeskEditor", () => ({
  DeskEditor: ({ value, onChange, ariaLabel }: { value: string; onChange: (v: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={ariaLabel || "Body"} data-testid="update-body-textarea" value={value}
      onChange={(e) => onChange(e.target.value)} />
  ),
}));

// The runtime bus, as roomInFlight.f2.test.tsx stands it in: subscriptions are
// kept so a test can deliver a frame the hub broadcast (a recorded one).
const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

const openSurfaceOr = vi.fn();
const openSurface = vi.fn();
vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>("../../../desk/shell");
  return {
    ...actual,
    openPrimitive: vi.fn(),
    openSurfaceOr: (...a: unknown[]) => openSurfaceOr(...a),
    openSurface: (...a: unknown[]) => openSurface(...a),
  };
});

function WindowHarness({ scope }: { scope: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div data-testid="wing-slot">{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

/* ── the recorded wire ─────────────────────────────────────────────── */

// Recorded 2026-10-11 by scratch rigs over the browser tests' seeds on a booted
// hub (isolated HOME): test_philo17_sources_glass (bare / older / lone-meeting
// projects), test_hs172_room_glass (_seed_all, then POST confirm),
// test_hs200_preparation_brief_glass (_seed_sources, _seed_decisions,
// _define_route), test_philo10_01_unknown_send_face (one sent, one ENAMETOOLONG
// send). Long temp folder paths are shortened to /tmp/rig/...; nothing else changed.
const BARE_ROOM = {"project_id": "proj-652bc245db48", "revision": 1, "observed_at": "2026-10-11T09:15:17.510489", "nextCheckAt": null, "project": {"id": "proj-652bc245db48", "name": "Ledger cutover", "description": "", "keywords": [], "team_members": [], "context": {}, "detection_threshold": 0.4, "is_archived": false, "meeting_count": 0, "created_at": "2026-10-11T09:15:17.510489", "updated_at": "2026-10-11T09:15:17.510489", "purpose": "Ledger cutover", "outcome_text": "Ledger cutover", "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 1, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 0, "latest": null, "state": "ok"}, "resources": {"count": 0, "latest": null, "state": "ok"}, "changes": {"recent": [{"id": "pchg_ca4d87ddceaa1bbfac7db934c27a5738", "project_id": "proj-652bc245db48", "project_revision": 1, "change_kind": "project.created", "target_ref": "project:proj-652bc245db48", "actor_ref": "principal:owner-session", "command_id": "pcmd_a4ab9769f839", "before_hash": null, "after_hash": "a306157a978e5d310a2e9886afe798d1", "summary_json": "{\"name\": \"Ledger cutover\", \"source\": \"setup\", \"watches_activated\": 0}", "created_at": "2026-10-11T15:15:17.510489+00:00"}], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [], "count": 0, "state": "ok"}, "sources": {"items": [], "count": 0, "nextCheckAt": null, "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": null, "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [], "state": "ok"}, "commitments": {"items": [], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [{"id": "5f31eba3-7e0b-4bbd-a311-5157388a8a22", "op": "create_from_setup", "label": "ProjectService.create_from_setup", "title": "ProjectService.create_from_setup", "outcome": "ok", "reason": null, "origin": null, "caller": null, "identity": null, "at": 1791731717.510411, "timestamp": 1791731717.510411}], "state": "ok"}};
const CONNECTIONS_NOT_SIGNED_IN = {"tools": [{"provider_id": "github", "state": "owner_action_required", "account": null, "next_action": {"kind": "sign_in", "label": "Sign in"}, "recovery_hint": "gh auth login", "error_detail": "gh auth login", "last_checked_at": "2026-10-11T15:15:17.529799+00:00", "checked_age_seconds": 0, "egress_host": "github.com"}, {"provider_id": "jira", "state": "never_checked", "account": null, "next_action": {"kind": "add_account", "label": "Add account"}, "recovery_hint": "acli jira auth login --site <site> --email <email> --token", "error_detail": null, "last_checked_at": null, "checked_age_seconds": null, "egress_host": null, "connections": []}, {"provider_id": "confluence", "state": "never_checked", "account": null, "next_action": {"kind": "setup", "label": "Set up"}, "recovery_hint": "acli confluence auth login --site <site> --email <email> --token", "error_detail": null, "last_checked_at": null, "checked_age_seconds": null, "egress_host": null, "connections": []}, {"provider_id": "calendar", "state": "not_configured", "account": null, "next_action": {"kind": "open_module", "label": "Set up"}, "recovery_hint": null, "error_detail": null, "last_checked_at": null, "checked_age_seconds": null, "egress_host": null}, {"provider_id": "models", "state": "not_configured", "account": {"assigned": 0, "total": 7, "summary_host": null}, "next_action": {"kind": "open_module", "label": "Open Models"}, "recovery_hint": null, "error_detail": null, "last_checked_at": null, "checked_age_seconds": null, "egress_host": null}]};
const BARE_REPOSITORY = {"project_id": "proj-652bc245db48", "repository": null, "registered": false, "cloned": false, "registered_at": null, "cloned_at": null, "folder": null, "watched": [], "host": "github.com", "store": "read"};
const OLDER_ROOM = {"project_id": "proj-4791815aa95e", "revision": 1, "observed_at": "2026-10-11T09:15:18.694456", "nextCheckAt": "2026-10-11T15:16:00+00:00", "project": {"id": "proj-4791815aa95e", "name": "Ledger cutover", "description": "", "keywords": [], "team_members": [], "context": {}, "detection_threshold": 0.4, "is_archived": false, "meeting_count": 0, "created_at": "2026-10-11T09:15:18.694456", "updated_at": "2026-10-11T09:15:18.694456", "purpose": "Ledger cutover", "outcome_text": "Ledger cutover", "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 1, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 0, "latest": null, "state": "ok"}, "resources": {"count": 0, "latest": null, "state": "ok"}, "changes": {"recent": [{"id": "pchg_fc3d11a96990fc05726c67bf8116559a", "project_id": "proj-4791815aa95e", "project_revision": 1, "change_kind": "project.created", "target_ref": "project:proj-4791815aa95e", "actor_ref": "principal:owner-session", "command_id": "pcmd_94d21e50c3c2", "before_hash": null, "after_hash": "a306157a978e5d310a2e9886afe798d1", "summary_json": "{\"name\": \"Ledger cutover\", \"source\": \"setup\", \"watches_activated\": 2}", "created_at": "2026-10-11T15:15:18.694456+00:00"}], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [], "count": 0, "state": "ok"}, "sources": {"items": [{"watchId": "watch_89ef3e21e055", "watchIds": ["watch_89ef3e21e055", "watch_dc3b1483821f"], "provider": "github", "scope": "acme/app", "tokens": ["CLEAR"], "checkedAt": "2026-10-11T15:15:18+00:00", "nextCheckAt": "2026-10-11T15:16:00+00:00", "host": "github.com", "state": "live", "plainReason": null, "suggested": false, "freshness": "available", "freshnessReason": null, "missedCheckAt": "2026-10-11T15:15:18+00:00"}], "count": 1, "nextCheckAt": "2026-10-11T15:16:00+00:00", "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": "2026-10-11 15:15:18", "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [], "state": "ok"}, "commitments": {"items": [], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [{"id": "32712cb8-86c6-46cb-bc97-89b3d8f58d43", "op": "create_from_setup", "label": "ProjectService.create_from_setup", "title": "ProjectService.create_from_setup", "outcome": "ok", "reason": null, "origin": null, "caller": null, "identity": null, "at": 1791731718.6943948, "timestamp": 1791731718.6943948}], "state": "ok"}};
const OLDER_REPOSITORY_BEFORE = {"project_id": "proj-4791815aa95e", "repository": null, "registered": false, "cloned": false, "registered_at": null, "cloned_at": null, "folder": null, "watched": ["acme/app"], "host": "github.com", "store": "read"};
const OLDER_REGISTER = {"project_id": "proj-4791815aa95e", "repository": "acme/app", "registered": true, "cloned": false, "registered_at": "2026-10-11T15:15:18.719580+00:00", "cloned_at": null, "folder": null, "watched": ["acme/app"], "host": "github.com", "store": "read", "operation_id": "op_89529badc8b54742a4bd126b9af42f7e", "receipt": {"receipt_id": "rcpt_81acf505fea04b0d9ec34837f7c0b554", "operation_id": "op_89529badc8b54742a4bd126b9af42f7e", "state": "succeeded", "outcome": "succeeded", "result_ref": "project:proj-4791815aa95e", "created_at": 1791731718.7209458, "actor_kind": "owner", "actor_identity": "owner-session", "delegator_kind": "", "delegator_identity": "", "authority_basis": "authenticated_principal+declared_capability+hard_prerequisites+interruption_policy", "target_ref": "project:proj-4791815aa95e"}};
const OLDER_REPOSITORY_AFTER = {"project_id": "proj-4791815aa95e", "repository": "acme/app", "registered": true, "cloned": false, "registered_at": "2026-10-11T15:15:18.719580+00:00", "cloned_at": null, "folder": null, "watched": ["acme/app"], "host": "github.com", "store": "read"};
const LONE_ROOM = {"project_id": "p-lone", "revision": 0, "observed_at": "2026-10-11T09:15:17.544106", "nextCheckAt": null, "project": {"id": "p-lone", "name": "Vendor review", "description": "One meeting.", "keywords": ["vendor"], "team_members": [], "context": {}, "detection_threshold": 0.4, "is_archived": false, "meeting_count": 1, "created_at": "2026-10-11T09:15:17.544106", "updated_at": "2026-10-11T09:15:17.544106", "purpose": null, "outcome_text": null, "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 0, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 1, "latest": {"id": "m-lone", "title": "Vendor call", "started_at": "2026-10-11T13:15:17+00:00", "duration_seconds": 1800.0, "intel_status": "completed", "source": "manual", "confidence": 1.0}, "state": "ok"}, "resources": {"count": 1, "latest": {"id": "p-lone|meeting:m-lone", "project_id": "p-lone", "resource_ref": "meeting:m-lone", "relationship": "member", "source": "manual", "confidence": 1.0, "created_at": "2026-10-11T15:15:17.544904+00:00", "last_modified": "2026-10-11T15:15:17.544904+00:00", "deleted": false}, "state": "ok"}, "changes": {"recent": [], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [], "count": 0, "state": "ok"}, "sources": {"items": [], "count": 0, "nextCheckAt": null, "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": null, "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [], "state": "ok"}, "commitments": {"items": [], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [], "state": "ok"}};
const LONE_MEETINGS = {"meetings": [{"id": "m-lone", "title": "Vendor call", "started_at": "2026-10-11T13:15:17+00:00", "duration_seconds": 1800.0, "intel_status": "completed", "source": "manual", "confidence": 1.0}]};
const PARK_DELETE = {"parked": "m-lone"};
const RESTORE = {"meeting": {"id": "m-lone", "parked": false, "started_at": "2026-10-11T07:15:17", "ended_at": "2026-10-11T07:45:17", "duration": 1800.0, "formatted_duration": "30:00", "title": "Vendor call", "tags": [], "segments": [{"text": "We pick the vendor.", "speaker": "Me", "speaker_id": null, "start_time": 1.0, "end_time": 4.0, "is_bookmarked": false, "device_id": null}], "bookmarks": [], "intel": {"timestamp": 1.0, "topics": ["vendor"], "action_items": [], "summary": "Pick it."}, "intel_status": {"state": "completed", "detail": null, "requested_at": null, "completed_at": null}, "mic_label": "Me", "remote_label": "Remote", "web_url": null, "capture_status": "finalized", "capture_failure": null, "transcription_status": "active", "transcription_status_detail": null, "capture_checkpoint_at": null, "capture_checkpoint_seconds": 0.0, "provenance": "desktop", "calendar_event_id": null, "transcriptWords": 4, "unclearSpans": 0, "sync_modified_at": "2026-10-11T09:15:17.544562", "devices": [], "planned_route": {"status": "unavailable", "reason_code": "no assignment", "selection_hash": null, "legs": []}, "run_receipt": null, "last_refusal": null, "intel_job": null, "intel_model_host": null}};
const P172_ROOM_BEFORE = {"project_id": "proj-692be627db7c", "revision": 1, "observed_at": "2026-09-05T10:00:00", "nextCheckAt": null, "project": {"id": "proj-692be627db7c", "name": "Ship the Q4 platform on schedule", "description": "", "keywords": [], "team_members": [], "context": {}, "detection_threshold": 0.5, "is_archived": false, "meeting_count": 1, "created_at": "2026-09-01T00:00:00", "updated_at": "2026-09-05T10:00:00", "purpose": null, "outcome_text": null, "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 1, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 1, "latest": {"id": "mtg-3d657557f308", "title": "Standup", "started_at": "2026-09-05T09:35:00", "duration_seconds": 1800.0, "intel_status": "complete", "source": "auto", "confidence": 0.0}, "state": "ok"}, "resources": {"count": 0, "latest": null, "state": "ok"}, "changes": {"recent": [], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [{"source": "proposal", "kind": "proposal", "title": "Marek owns the PostgreSQL migration", "why": "PROPOSED · Standup", "since": "2026-09-05T09:35:00", "url": null, "verb": "confirm", "verbHref": "/api/proposals/prop-2e17068ce8c4450f/confirm", "severity": "info", "proposal_id": "prop-2e17068ce8c4450f", "proposal_kind": "action", "host": "192.168.1.43", "speaker_label": "Marek", "due_hint": "Fri", "owner_hint": "Marek", "original_text": "Marek owns the PostgreSQL migration", "meeting_id": "mtg-3d657557f308", "action_item_id": null, "meeting_title": "Standup", "meeting_started_at": "2026-09-05T09:35:00", "created_at": "2026-09-05T09:35:00"}, {"source": "proposal", "kind": "proposal", "title": "cut-over on the 12th", "why": "PROPOSED · Standup", "since": "2026-09-05T09:35:00", "url": null, "verb": "confirm", "verbHref": "/api/proposals/prop-207fb27a5cf6433d/confirm", "severity": "info", "proposal_id": "prop-207fb27a5cf6433d", "proposal_kind": "decision", "host": "192.168.1.43", "speaker_label": null, "due_hint": null, "owner_hint": null, "original_text": "cut-over on the 12th", "meeting_id": "mtg-3d657557f308", "action_item_id": null, "meeting_title": "Standup", "meeting_started_at": "2026-09-05T09:35:00", "created_at": "2026-09-05T09:35:00"}], "count": 2, "state": "ok"}, "sources": {"items": [], "count": 0, "nextCheckAt": null, "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": null, "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [], "state": "ok"}, "commitments": {"items": [], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [], "state": "ok"}};
const P172_ROOM_AFTER = {"project_id": "proj-692be627db7c", "revision": 1, "observed_at": "2026-09-05T10:00:00", "nextCheckAt": null, "project": {"id": "proj-692be627db7c", "name": "Ship the Q4 platform on schedule", "description": "", "keywords": [], "team_members": [], "context": {}, "detection_threshold": 0.5, "is_archived": false, "meeting_count": 1, "created_at": "2026-09-01T00:00:00", "updated_at": "2026-09-05T10:00:00", "purpose": null, "outcome_text": null, "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 1, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 1, "latest": {"id": "mtg-3d657557f308", "title": "Standup", "started_at": "2026-09-05T09:35:00", "duration_seconds": 1800.0, "intel_status": "complete", "source": "auto", "confidence": 0.0}, "state": "ok"}, "resources": {"count": 0, "latest": null, "state": "ok"}, "changes": {"recent": [], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [{"source": "proposal", "kind": "proposal", "title": "cut-over on the 12th", "why": "PROPOSED · Standup", "since": "2026-09-05T09:35:00", "url": null, "verb": "confirm", "verbHref": "/api/proposals/prop-207fb27a5cf6433d/confirm", "severity": "info", "proposal_id": "prop-207fb27a5cf6433d", "proposal_kind": "decision", "host": "192.168.1.43", "speaker_label": null, "due_hint": null, "owner_hint": null, "original_text": "cut-over on the 12th", "meeting_id": "mtg-3d657557f308", "action_item_id": null, "meeting_title": "Standup", "meeting_started_at": "2026-09-05T09:35:00", "created_at": "2026-09-05T09:35:00"}, {"source": "commitment", "kind": "commitment", "title": "Marek owns the PostgreSQL migration", "why": "WAITING ON MAREK", "since": "2026-10-11T15:15:17.565441+00:00", "due_at": "Fri", "url": null, "verb": "mark_done", "severity": "info", "commitment_id": "commitment-653d31fb4cd54dfe", "action_item_id": "action-03dd6e195a8f418f", "decision_record_id": "record-74bb0061f86e4637", "decision_lifecycle": "active", "owner": "Marek", "unknowns": [], "next_action": "mark_done"}], "count": 2, "state": "ok"}, "sources": {"items": [], "count": 0, "nextCheckAt": null, "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": null, "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [{"id": "record-74bb0061f86e4637", "text": "Marek owns the PostgreSQL migration", "at": "2026-10-11T15:15:17.565441+00:00", "url": null, "lifecycle": "active", "kind": "action", "source_type": "meeting", "source_id": "dec-42e8ef6759264018", "proposal_id": "prop-2e17068ce8c4450f", "source": "meeting", "meeting_title": "Standup", "confirmed_at": "2026-10-11T15:15:17.565472+00:00", "commitment_id": "commitment-653d31fb4cd54dfe"}], "state": "ok"}, "commitments": {"items": [{"id": "commitment-653d31fb4cd54dfe", "text": "Marek owns the PostgreSQL migration", "dueAt": "Fri", "owner": "Marek", "kind": "action", "action_item_id": "action-03dd6e195a8f418f"}], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [], "state": "ok"}};
const P172_PROPOSALS = {"project_id": "proj-692be627db7c", "proposals": [{"id": "prop-2e17068ce8c4450f", "meeting_id": "mtg-3d657557f308", "project_id": "proj-692be627db7c", "kind": "action", "text": "Marek owns the PostgreSQL migration", "owner_hint": "Marek", "due_hint": "Fri", "owner": "Marek", "due": "Fri", "owner_supplied": null, "due_supplied": null, "source_artifact_id": null, "source_plugin": "decision_capture", "segment_timestamp": null, "speaker_label": "Marek", "model_host": "192.168.1.43", "state": "proposed", "original_text": "Marek owns the PostgreSQL migration", "decision_record_id": null, "rationale": null, "commitment_id": null, "created_at": "2026-09-05T09:35:00", "decided_at": null, "retry_key": null, "extraction_revision": null, "job_id": null, "job_attempt": null, "extraction_model": null, "span_start": null, "span_end": null, "segment_index": null, "claim_kind": "proposal", "support": "unknown", "support_record": null, "acceptance": "unreviewed", "unknowns": [], "edited_at": null, "text_edited": false, "action_item_id": null, "deferred_until": null}, {"id": "prop-207fb27a5cf6433d", "meeting_id": "mtg-3d657557f308", "project_id": "proj-692be627db7c", "kind": "decision", "text": "cut-over on the 12th", "owner_hint": null, "due_hint": null, "owner": null, "due": null, "owner_supplied": null, "due_supplied": null, "source_artifact_id": null, "source_plugin": "decision_capture", "segment_timestamp": null, "speaker_label": null, "model_host": "192.168.1.43", "state": "proposed", "original_text": "cut-over on the 12th", "decision_record_id": null, "rationale": null, "commitment_id": null, "created_at": "2026-09-05T09:35:00", "decided_at": null, "retry_key": null, "extraction_revision": null, "job_id": null, "job_attempt": null, "extraction_model": null, "span_start": null, "span_end": null, "segment_index": null, "claim_kind": "proposal", "support": "unknown", "support_record": null, "acceptance": "unreviewed", "unknowns": [], "edited_at": null, "text_edited": false, "action_item_id": null, "deferred_until": null}]};
const P172_PROPOSALS_AFTER = {"project_id": "proj-692be627db7c", "proposals": [{"id": "prop-2e17068ce8c4450f", "meeting_id": "mtg-3d657557f308", "project_id": "proj-692be627db7c", "kind": "action", "text": "Marek owns the PostgreSQL migration", "owner_hint": "Marek", "due_hint": "Fri", "owner": "Marek", "due": "Fri", "owner_supplied": null, "due_supplied": null, "source_artifact_id": null, "source_plugin": "decision_capture", "segment_timestamp": null, "speaker_label": "Marek", "model_host": "192.168.1.43", "state": "confirmed", "original_text": "Marek owns the PostgreSQL migration", "decision_record_id": "record-74bb0061f86e4637", "rationale": null, "commitment_id": "commitment-653d31fb4cd54dfe", "created_at": "2026-09-05T09:35:00", "decided_at": "2026-10-11T15:15:17.565472+00:00", "retry_key": null, "extraction_revision": null, "job_id": null, "job_attempt": null, "extraction_model": null, "span_start": null, "span_end": null, "segment_index": null, "claim_kind": "proposal", "support": "unknown", "support_record": null, "acceptance": "accepted", "unknowns": [], "edited_at": null, "text_edited": false, "action_item_id": null, "deferred_until": null}, {"id": "prop-207fb27a5cf6433d", "meeting_id": "mtg-3d657557f308", "project_id": "proj-692be627db7c", "kind": "decision", "text": "cut-over on the 12th", "owner_hint": null, "due_hint": null, "owner": null, "due": null, "owner_supplied": null, "due_supplied": null, "source_artifact_id": null, "source_plugin": "decision_capture", "segment_timestamp": null, "speaker_label": null, "model_host": "192.168.1.43", "state": "proposed", "original_text": "cut-over on the 12th", "decision_record_id": null, "rationale": null, "commitment_id": null, "created_at": "2026-09-05T09:35:00", "decided_at": null, "retry_key": null, "extraction_revision": null, "job_id": null, "job_attempt": null, "extraction_model": null, "span_start": null, "span_end": null, "segment_index": null, "claim_kind": "proposal", "support": "unknown", "support_record": null, "acceptance": "unreviewed", "unknowns": [], "edited_at": null, "text_edited": false, "action_item_id": null, "deferred_until": null}]};
const P172_SUGGESTED = {"suggestions": [{"id": "ssug_274754f4073b", "project_id": "proj-692be627db7c", "meeting_id": "mtg-3d657557f308", "provider": "github", "reference": "karolswdev/hs-infra", "status": "pending", "created_at": "2026-09-05T09:35:00"}]};
const P172_CONFIRM = {"success": true, "proposal_id": "prop-2e17068ce8c4450f", "state": "confirmed", "original_text": "Marek owns the PostgreSQL migration", "decision_id": "dec-42e8ef6759264018", "decision_record_id": "record-74bb0061f86e4637", "action_item_id": "action-03dd6e195a8f418f", "commitment_id": "commitment-653d31fb4cd54dfe", "replayed": false, "proposal": {"id": "prop-2e17068ce8c4450f", "meeting_id": "mtg-3d657557f308", "project_id": "proj-692be627db7c", "kind": "action", "text": "Marek owns the PostgreSQL migration", "owner_hint": "Marek", "due_hint": "Fri", "owner": "Marek", "due": "Fri", "owner_supplied": null, "due_supplied": null, "source_artifact_id": null, "source_plugin": "decision_capture", "segment_timestamp": null, "speaker_label": "Marek", "model_host": "192.168.1.43", "state": "confirmed", "original_text": "Marek owns the PostgreSQL migration", "decision_record_id": "record-74bb0061f86e4637", "rationale": null, "commitment_id": "commitment-653d31fb4cd54dfe", "created_at": "2026-09-05T09:35:00", "decided_at": "2026-10-11T15:15:17.565472+00:00", "retry_key": null, "extraction_revision": null, "job_id": null, "job_attempt": null, "extraction_model": null, "span_start": null, "span_end": null, "segment_index": null, "claim_kind": "proposal", "support": "unknown", "support_record": null, "acceptance": "accepted", "unknowns": [], "edited_at": null, "text_edited": false, "action_item_id": null, "deferred_until": null}};
const PREP_ROOM = {"project_id": "proj-aafa9fe3637d", "revision": 1, "observed_at": "2026-10-11T09:15:17.574613", "nextCheckAt": "2026-10-11T15:16:00+00:00", "project": {"id": "proj-aafa9fe3637d", "name": "Q4 platform", "description": "Seeded.", "keywords": [], "team_members": [], "context": {}, "detection_threshold": 0.4, "is_archived": false, "meeting_count": 1, "created_at": "2026-10-11T09:15:17.574613", "updated_at": "2026-10-11T09:15:17.574613", "purpose": null, "outcome_text": null, "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 1, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 1, "latest": {"id": "mtg_fa412695fa", "title": "Cut-over sync", "started_at": "2026-10-11T09:15:17", "duration_seconds": null, "intel_status": "disabled", "source": "auto", "confidence": 0.0}, "state": "ok"}, "resources": {"count": 0, "latest": null, "state": "ok"}, "changes": {"recent": [{"id": "pchg_f71cef077487817aa18144ced2b3b0b6", "project_id": "proj-aafa9fe3637d", "project_revision": 1, "change_kind": "project.created", "target_ref": "project:proj-aafa9fe3637d", "actor_ref": "principal:owner-session", "command_id": "dump-prep", "before_hash": null, "after_hash": "537d7c3db9796346e11bde9d6c0d40e3", "summary_json": "{\"name\": \"Q4 platform\"}", "created_at": "2026-10-11T15:15:17.574613+00:00"}], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [], "count": 0, "state": "ok"}, "sources": {"items": [{"watchId": "w_confluence_0050da41f5", "provider": "confluence", "scope": "", "tokens": [], "checkedAt": "2026-10-11T14:15:17+00:00", "nextCheckAt": null, "host": "", "state": "cant_check", "plainReason": "Confluence rejected the token (401)", "suggested": false, "watchIds": ["w_confluence_0050da41f5"], "freshness": "failed", "freshnessReason": "Confluence rejected the token (401)"}, {"watchId": "w_gh_fa84288c0a", "provider": "github", "scope": "karolswdev/HoldSpeak", "tokens": ["2 OPEN PRS"], "checkedAt": "2026-10-11T15:13:17+00:00", "nextCheckAt": "2026-10-11T16:15:17+00:00", "host": "github.com", "state": "live", "plainReason": null, "suggested": false, "watchIds": ["w_gh_fa84288c0a"], "freshness": "available", "freshnessReason": null}, {"watchId": "w_jira_accbb45f6e", "provider": "jira", "scope": "KAN", "tokens": ["CLEAR"], "checkedAt": "2026-10-10T19:15:17+00:00", "nextCheckAt": "2026-10-11T15:16:00+00:00", "host": "acme.atlassian.net", "state": "live", "plainReason": null, "suggested": false, "watchIds": ["w_jira_accbb45f6e"], "freshness": "stale", "freshnessReason": "not checked recently", "missedCheckAt": "2026-10-10T20:15:17+00:00"}, {"watchId": "w_aa3f6b42be09", "provider": "meeting", "scope": "MEETINGS", "tokens": [], "checkedAt": "2026-10-11T15:13:17+00:00", "nextCheckAt": "2026-10-11T16:15:17+00:00", "host": "", "state": "live", "plainReason": null, "suggested": false, "watchIds": ["w_aa3f6b42be09"], "freshness": "available", "freshnessReason": null}], "count": 4, "nextCheckAt": "2026-10-11T15:16:00+00:00", "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": "2026-10-11T09:15:17", "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [{"id": "decrec_cur_ab9474c9", "text": "Cut-over runs on the read replica first", "at": "2026-10-11T09:15:17", "url": null, "lifecycle": "active", "kind": "decision", "source_type": "meeting", "source_id": "mtg_fa412695fa"}, {"id": "decrec_old_d775ece3", "text": "Cut-over runs under a full freeze", "at": "2026-10-11T09:15:17", "url": null, "lifecycle": "superseded", "kind": "decision", "source_type": "meeting", "source_id": "mtg_fa412695fa", "successor_id": "decrec_cur_ab9474c9"}], "state": "ok"}, "commitments": {"items": [], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [{"id": "618197af-ef7e-447a-887d-ad2017c41893", "op": "create_project", "label": "ProjectService.create_project", "title": "ProjectService.create_project", "outcome": "ok", "reason": null, "origin": null, "caller": null, "identity": null, "at": 1791731717.574568, "timestamp": 1791731717.574568}], "state": "ok"}};
const PREP_ROUTE = {"route": {"state": "ready", "token": "READY", "host": "127.0.0.1", "model": "QWEN3 35B", "boundary": "private_network", "reason": "", "repair": "Set up model", "invoke": {"sent": false, "operation_id": "", "outcome": "", "send_phase": "", "host": ""}}};
const PREP_MANIFEST = {"manifest": {"project_id": "proj-aafa9fe3637d", "project_revision": 1, "purpose": "", "prepared_at": "2026-10-11T15:15:17.641050+00:00", "calendar": {"present": false}, "coverage": {"expected": 4, "available": 2, "complete": false}, "sources": [{"source_id": "w_confluence_0050da41f5", "kind": "confluence", "label": "CONFLUENCE", "state": "failed", "observed_at": "2026-10-11T14:15:17+00:00", "revision": "2026-10-11T14:15:17+00:00", "reason": "Confluence rejected the token (401)", "repair": {"token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect", "href": "/settings"}, "tokens": [], "host": "", "watch_ids": ["w_confluence_0050da41f5"]}, {"source_id": "w_gh_fa84288c0a", "kind": "github", "label": "karolswdev/HoldSpeak", "state": "available", "observed_at": "2026-10-11T15:13:17+00:00", "revision": "2026-10-11T15:13:17+00:00", "reason": null, "repair": null, "tokens": ["2 OPEN PRS"], "host": "github.com", "watch_ids": ["w_gh_fa84288c0a"]}, {"source_id": "w_jira_accbb45f6e", "kind": "jira", "label": "KAN", "state": "stale", "observed_at": "2026-10-10T19:15:17+00:00", "revision": "2026-10-10T19:15:17+00:00", "reason": "missed its check", "repair": {"token": "STALE", "verb": "Retry", "href": "/"}, "tokens": ["CLEAR"], "host": "acme.atlassian.net", "watch_ids": ["w_jira_accbb45f6e"]}, {"source_id": "w_aa3f6b42be09", "kind": "meeting", "label": "MEETINGS", "state": "available", "observed_at": "2026-10-11T15:13:17+00:00", "revision": "2026-10-11T15:13:17+00:00", "reason": null, "repair": null, "tokens": [], "host": "", "watch_ids": ["w_aa3f6b42be09"]}], "omitted": [{"source_id": "w_confluence_0050da41f5", "kind": "confluence", "label": "CONFLUENCE", "state": "failed", "observed_at": "2026-10-11T14:15:17+00:00", "revision": "2026-10-11T14:15:17+00:00", "reason": "Confluence rejected the token (401)", "repair": {"token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect", "href": "/settings"}, "tokens": [], "host": "", "watch_ids": ["w_confluence_0050da41f5"]}, {"source_id": "w_jira_accbb45f6e", "kind": "jira", "label": "KAN", "state": "stale", "observed_at": "2026-10-10T19:15:17+00:00", "revision": "2026-10-10T19:15:17+00:00", "reason": "missed its check", "repair": {"token": "STALE", "verb": "Retry", "href": "/"}, "tokens": ["CLEAR"], "host": "acme.atlassian.net", "watch_ids": ["w_jira_accbb45f6e"]}], "decisions": [{"ref": "decision_record:decrec_cur_ab9474c9", "text": "Cut-over runs on the read replica first", "lifecycle": "current", "at": "2026-10-11T09:15:17", "meeting_title": "", "kind": "decision"}, {"ref": "decision_record:decrec_old_d775ece3", "text": "Cut-over runs under a full freeze", "lifecycle": "superseded", "at": "2026-10-11T09:15:17", "meeting_title": "", "kind": "decision", "successor_ref": "decision_record:decrec_cur_ab9474c9"}], "commitments": [], "not_included": []}};
const DRAFT = {"success": true, "update": {"id": "pupd_9b433950cfde42f699275f28b38d0340", "project_id": "proj-6a51f32af028", "project_revision": 1, "review_id": null, "lifecycle": "draft", "draft_revision": 1, "body_md": "Nothing to report.\n", "claims_json": "[{\"acceptance\":\"unreviewed\",\"kind\":\"observation\",\"refs\":[],\"section\":\"progress\",\"span_id\":\"s_nothing_0\",\"support\":\"unknown\",\"text\":\"Nothing to report.\"}]", "source_manifest_json": "{\"caveats\":[],\"closure_keys\":[],\"closure_lines\":{},\"observation_ids\":[],\"project_revision\":1,\"week_source_refs\":[]}", "generator": "deterministic", "generator_host": null, "generator_model": null, "created_at": "2026-10-11T15:16:05+00:00", "updated_at": "2026-10-11T15:16:05+00:00", "published_at": null, "fallback_reason": null, "fallback_receipt": null, "generatorHost": null, "generatorModel": null}};
const PUT = {"success": true, "update": {"id": "pupd_9b433950cfde42f699275f28b38d0340", "project_id": "proj-6a51f32af028", "project_revision": 1, "review_id": null, "lifecycle": "draft", "draft_revision": 1, "body_md": "## Progress\n\nThe ledger cutover is on track.\n", "claims_json": "[{\"acceptance\":\"unreviewed\",\"kind\":\"observation\",\"refs\":[],\"section\":\"progress\",\"span_id\":\"s_nothing_0\",\"support\":\"unknown\",\"text\":\"Nothing to report.\"},{\"acceptance\":\"accepted\",\"kind\":\"observation\",\"refs\":[],\"section\":\"progress\",\"span_id\":\"s_owner_0\",\"support\":\"unknown\",\"support_record\":{\"checked_at\":\"2026-10-11T15:16:05+00:00\",\"fields\":[\"owner_text\"],\"method\":\"reviewer\",\"reviewer_ref\":\"principal:owner-session\"},\"text\":\"The ledger cutover is on track.\"}]", "source_manifest_json": "{\"caveats\":[],\"closure_keys\":[],\"closure_lines\":{},\"observation_ids\":[],\"project_revision\":1,\"week_source_refs\":[]}", "generator": "deterministic", "generator_host": null, "generator_model": null, "created_at": "2026-10-11T15:16:05+00:00", "updated_at": "2026-10-11T15:16:05+00:00", "published_at": null, "fallback_reason": null, "fallback_receipt": null, "generatorHost": null, "generatorModel": null}};
const UPDATES_AFTER_SENDS = {"updates": [{"id": "pupd_9b433950cfde42f699275f28b38d0340", "project_id": "proj-6a51f32af028", "project_revision": 1, "review_id": null, "lifecycle": "published", "draft_revision": 1, "body_md": "## Progress\n\nThe ledger cutover is on track.\n", "claims_json": "[{\"acceptance\":\"unreviewed\",\"kind\":\"observation\",\"refs\":[],\"section\":\"progress\",\"span_id\":\"s_nothing_0\",\"support\":\"unknown\",\"text\":\"Nothing to report.\"},{\"acceptance\":\"accepted\",\"kind\":\"observation\",\"refs\":[],\"section\":\"progress\",\"span_id\":\"s_owner_0\",\"support\":\"unknown\",\"support_record\":{\"checked_at\":\"2026-10-11T15:16:05+00:00\",\"fields\":[\"owner_text\"],\"method\":\"reviewer\",\"reviewer_ref\":\"principal:owner-session\"},\"text\":\"The ledger cutover is on track.\"}]", "source_manifest_json": "{\"caveats\":[],\"closure_keys\":[],\"closure_lines\":{},\"observation_ids\":[],\"project_revision\":1,\"week_source_refs\":[]}", "generator": "deterministic", "generator_host": null, "generator_model": null, "created_at": "2026-10-11T15:16:05+00:00", "updated_at": "2026-10-11T15:16:05+00:00", "published_at": "2026-10-11T15:16:05+00:00", "fallback_reason": null, "fallback_receipt": null, "deliveries": [{"id": "pdel_7857c7929be1ff54", "update_id": "pupd_9b433950cfde42f699275f28b38d0340", "project_id": "proj-6a51f32af028", "delivered_at": "2026-10-11T15:16:05.497310+00:00", "delivered_to": "Team folder", "operation_id": "op_fb671c10bd2d44659ce048ccc993a2d0", "channel": "file", "send_id": "chs_a7c54e9943ba72f6a1fd0b0d", "outcome": "sent", "proof_json": "{\"path\":\"/tmp/rig/out/2026-10-11-payments-ledger-cutover-rev-1-a7c54e99.md\",\"sha256\":\"5d693599bdc8e5705c8afca4d73fb4c1ab0d08c12107816d765e6e17a28bb137\",\"size\":96}"}, {"id": "pdel_98fb8320e68a2581", "update_id": "pupd_9b433950cfde42f699275f28b38d0340", "project_id": "proj-6a51f32af028", "delivered_at": "2026-10-11T15:16:05.509279+00:00", "delivered_to": "Long path folder", "operation_id": "op_dd2e6cd549c04b3eae9c2ef540b6ab9a", "channel": "file", "send_id": "chs_7073506004319d530451886b", "outcome": "unknown", "proof_json": null}], "generatorHost": null, "generatorModel": null}], "latest_published_update_id": "pupd_9b433950cfde42f699275f28b38d0340"};
const SENDS = {"sends": [{"id": "chs_a7c54e9943ba72f6a1fd0b0d", "document_ref": "project_update:pupd_9b433950cfde42f699275f28b38d0340", "destination_id": "chd_1bdb01472e331722831a73f5", "destination_name": "Team folder", "channel": "file", "badge": "local", "account": {}, "target": {"folder": "/tmp/rig/out", "display": "/tmp/rig/out"}, "target_digest": "dc34555c7a2b84148e0a463b7e17e0f0def288fc6db100bea8066994b7126376", "payload_digest": "5d693599bdc8e5705c8afca4d73fb4c1ab0d08c12107816d765e6e17a28bb137", "document_json": {"label": "REV 1", "slug": "payments-ledger-cutover", "title": "Payments ledger cutover — update r1 (2026-10-11)"}, "size": 96, "preview": {"text": "# Payments ledger cutover · Update · 2026-10-11\n\n## Progress\n\nThe ledger cutover is on track.\n"}, "prepared_by": {"kind": "owner", "identity": "owner-session"}, "prepare_operation_id": "op_a9b805bbcecb4f1abb622c38ef34be72", "send_operation_id": "op_fb671c10bd2d44659ce048ccc993a2d0", "state": "sent", "reason": null, "proof": {"path": "/tmp/rig/out/2026-10-11-payments-ledger-cutover-rev-1-a7c54e99.md", "sha256": "5d693599bdc8e5705c8afca4d73fb4c1ab0d08c12107816d765e6e17a28bb137", "size": 96}, "file_path": "/tmp/rig/out/2026-10-11-payments-ledger-cutover-rev-1-a7c54e99.md", "created_at": "2026-10-11T15:16:05+00:00", "dispatch_started_at": "2026-10-11T15:16:05.497310+00:00", "settled_at": "2026-10-11T15:16:05+00:00", "dispatch_seq": 1, "egress": null}, {"id": "chs_7073506004319d530451886b", "document_ref": "project_update:pupd_9b433950cfde42f699275f28b38d0340", "destination_id": "chd_02d023251142bdc30f74f62e", "destination_name": "Long path folder", "channel": "file", "badge": "local", "account": {}, "target": {"folder": "/tmp/rig/deep", "display": "/tmp/rig/deep"}, "target_digest": "bee5bceec57a03c7beb09e426ed6d7107d87382ae4be1b0eac095fa9592a7ac7", "payload_digest": "5d693599bdc8e5705c8afca4d73fb4c1ab0d08c12107816d765e6e17a28bb137", "document_json": {"label": "REV 1", "slug": "payments-ledger-cutover", "title": "Payments ledger cutover — update r1 (2026-10-11)"}, "size": 96, "preview": {"text": "# Payments ledger cutover · Update · 2026-10-11\n\n## Progress\n\nThe ledger cutover is on track.\n"}, "prepared_by": {"kind": "owner", "identity": "owner-session"}, "prepare_operation_id": "op_ef7f5d0d58174f5385d4c66883175aae", "send_operation_id": "op_dd2e6cd549c04b3eae9c2ef540b6ab9a", "state": "unknown", "reason": "create_enametoolong", "proof": null, "file_path": "/tmp/rig/deep/2026-10-11-payments-ledger-cutover-rev-1-70735060.md", "created_at": "2026-10-11T15:16:05+00:00", "dispatch_started_at": "2026-10-11T15:16:05.509279+00:00", "settled_at": "2026-10-11T15:16:05+00:00", "dispatch_seq": 2, "egress": null}]};

const clone = <T,>(v: T): T => JSON.parse(JSON.stringify(v)) as T;

/* ── the router: `METHOD path` → the hub's answer ──────────────────── */

type Init = { method?: string; json?: Record<string, unknown> };
type Answer = (init: Init, url: string) => unknown;
let routes: Record<string, Answer> = {};
const calls: Array<{ key: string; json?: Record<string, unknown> }> = [];

/** The reads every Room makes beside /room, answered as the existing Room
 *  rigs answer them (room172proposals.test.tsx, room175sources.test.tsx). */
function fallback(path: string): unknown {
  if (path.endsWith("/room/read")) return { read_at: new Date().toISOString() };
  if (path.endsWith("/meetings")) return { meetings: [] };
  if (path.startsWith("/api/decisions")) return { decisions: [] };
  if (path.includes("/artifacts")) return { artifacts: [] };
  if (path.includes("/since-last-meeting")) return { current_meeting: null, since_last_meeting: null };
  if (path.endsWith("/proposals")) return { proposals: [] };
  if (path.endsWith("/suggested-sources")) return { suggestions: [] };
  if (path.endsWith("/nudges")) return { nudges: [] };
  return {};
}

function wire(table: Record<string, Answer>) {
  routes = table;
  apiFetch.mockImplementation((url: string, init: Init = {}) => {
    const path = url.split("?")[0];
    const key = `${init.method ?? "GET"} ${path}`;
    calls.push({ key, json: init.json });
    const answer = routes[key];
    try {
      return Promise.resolve(answer ? answer(init, url) : fallback(path));
    } catch (error) {
      return Promise.reject(error);
    }
  });
}

const room = (id: string) => `GET /api/projects/${id}/room`;

/** UX-CANON A.1, the browser rigs' `_assert_no_raw_button`, verbatim. */
function rawButtons(root: Element): string[] {
  return Array.from(root.querySelectorAll("button"))
    .filter((b) => !(b.classList.contains("btn") || b.classList.contains("btn--chrome")
      || b.classList.contains("signal-button") || b.classList.contains("surface-ledger-line")
      || b.classList.contains("surface-edit-in-place") || b.closest(".gadget-string")
      || b.closest(".mic-button") || b.classList.contains("desk-mic")))
    .map((b) => b.outerHTML.slice(0, 120));
}

beforeEach(() => {
  calls.length = 0;
  sessionStorage.clear();
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
});
afterEach(() => {
  vi.clearAllMocks();
});

/* ── HS-172-03/06: proposals, Edit, Confirm, suggested sources ───────── */

describe("HS-172: proposals in OPEN HERE, Confirm into DECISIONS, suggested sources", () => {
  // replaces: tests/e2e/test_hs172_room_glass.py::TestRoomProposalsGlass::test_proposals_1440
  // replaces: tests/e2e/test_hs172_room_glass.py::TestRoomProposalsGlass::test_proposals_393
  // replaces: tests/e2e/test_hs172_room_glass.py::TestRoomProposalsGlass::test_suggested_1440
  // replaces: tests/e2e/test_hs172_room_glass.py::TestRoomProposalsGlass::test_suggested_393
  // (the text-wrap clip check is the generic sweep's, T3)
  const pid = P172_ROOM_BEFORE.project_id;
  const table = (after = false): Record<string, Answer> => ({
    [room(pid)]: () => clone(after ? P172_ROOM_AFTER : P172_ROOM_BEFORE),
    [`GET /api/projects/${pid}/proposals`]: () => clone(after ? P172_PROPOSALS_AFTER : P172_PROPOSALS),
    [`GET /api/projects/${pid}/suggested-sources`]: () => clone(P172_SUGGESTED),
  });

  it("draws both proposals with their verbs, the suggested source, no raw button, no zero, no LOCAL", async () => {
    wire(table());
    render(<WindowHarness scope={`project:${pid}`} />);
    await waitFor(() => expect(screen.getAllByTestId("proposal-row")).toHaveLength(2));
    const body = screen.getByTestId("room-body");
    expect(screen.getAllByTestId("proposal-confirm")).toHaveLength(2);
    expect(screen.getAllByTestId("suggested-source-row")).toHaveLength(1);
    expect(screen.getByTestId("suggested-ref").textContent).toBe("karolswdev/hs-infra");
    expect(rawButtons(body)).toEqual([]);
    expect(body.textContent).not.toMatch(/\b0\s+(?:NEEDS|SOURCES|DECISIONS|items|proposals)/);
    expect(body.textContent).not.toContain("LOCAL");
  });

  // replaces: tests/e2e/test_hs172_room_glass.py::TestRoomProposalsGlass::test_edit_1440
  it("Edit unfolds the edit well under the row", async () => {
    wire(table());
    render(<WindowHarness scope={`project:${pid}`} />);
    await waitFor(() => expect(screen.getAllByTestId("proposal-row")).toHaveLength(2));
    fireEvent.click(screen.getAllByTestId("proposal-edit")[0]);
    expect(await screen.findByTestId("proposal-edit-well")).toBeTruthy();
  });

  // replaces: tests/e2e/test_hs172_room_glass.py::TestRoomProposalsGlass::test_confirmed_1440
  it("Confirm posts to the proposal's confirm route and the Room re-reads: the decision row is there", async () => {
    let confirmed = false;
    wire({
      ...table(),
      [`POST /api/proposals/${P172_PROPOSALS.proposals[0].id}/confirm`]: () => {
        confirmed = true;
        Object.assign(routes, table(true));
        return clone(P172_CONFIRM);
      },
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    await waitFor(() => expect(screen.getAllByTestId("proposal-row")).toHaveLength(2));
    expect(screen.queryByTestId("decision-row")).toBeNull();
    const first = screen.getAllByTestId("proposal-row")
      .find((r) => r.textContent?.includes("Marek owns the PostgreSQL migration"))!;
    fireEvent.click(within(first.closest("li") ?? first).getByTestId("proposal-confirm"));
    const row = await screen.findByTestId("decision-row");
    expect(confirmed).toBe(true);
    expect(row.textContent).toContain("Marek owns the PostgreSQL migration");
    expect(screen.getAllByTestId("proposal-row")).toHaveLength(1);
  });
});

/* ── HS-172-07: the PEOPLE section ─────────────────────────────────── */

describe("HS-172-07: PEOPLE shows resolved names with monograms and Open, never a login", () => {
  // replaces: tests/e2e/test_hs172_room_people_glass.py::test_room_people_1440
  // replaces: tests/e2e/test_hs172_room_people_glass.py::test_room_people_393 (the Room half)
  // The shape is `room_people_preparation`'s (holdspeak/services/room_people_service.py:337-346
  // `_row`, :192-212 `_facts_for`, :443-452 the return): the browser rig's monkeypatch
  // carried the same rows (its `gaps` key `locked` is not the service's; the service says
  // `unreadable`). The reviewer logins (ania-dev, marek-k) never cross the wire.
  const fact = (count: number, watch: string) => ({
    kind: "prs_waiting", count,
    source: { kind: "watch", watch_id: watch, connector_id: "gh", label: "karolswdev/HoldSpeak" },
  });
  const PEOPLE = {
    state: "ready", expected: 2, resolved: 2, gaps: { ambiguous: 0, not_linked: 0, unreadable: 0 },
    people: [
      { relationship_id: "rel-ania", display_name: "Ania Kowalska", link: "linked", commitments: [],
        facts: [fact(2, "w-172-prs")], omitted_sources: [], prs_waiting: 2 },
      { relationship_id: "rel-marek", display_name: "Marek Kubiak", link: "linked", commitments: [],
        facts: [fact(1, "w-172-prs")], omitted_sources: [], prs_waiting: 1 },
    ],
    unresolved: [],
  };

  it("names, monograms AK and MK, two Open verbs, no zero counter, no raw login", async () => {
    wire({ "GET /api/projects/proj-172-people/people": () => clone(PEOPLE) });
    const { container } = render(<RoomPeopleSection projectId="proj-172-people" />);
    await screen.findByText("Ania Kowalska");
    const text = container.textContent ?? "";
    expect(text).toContain("Marek Kubiak");
    const leads = Array.from(container.querySelectorAll("[data-testid=room-people-row] .surface-ledger-lead"))
      .map((el) => el.textContent);
    expect(leads).toEqual(["AK", "MK"]);
    expect(screen.getAllByTestId("room-people-open")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Open: Ania Kowalska" })).toBeTruthy();
    expect(text).not.toContain("ania-dev");
    expect(text).not.toContain("marek-k");
    for (const line of (container as HTMLElement).innerText?.split("\n") ?? text.split(/(?=\d+ )/)) {
      expect(line.trim()).not.toMatch(/^0 .*(PR|OVERDUE|ASSIGNMENT)/);
    }
    expect(text).not.toMatch(/\b0 (PRS?|ASSIGNMENTS?|OVERDUE)/);
    expect(rawButtons(container)).toEqual([]);
    fireEvent.click(screen.getByRole("button", { name: "Open: Marek Kubiak" }));
    expect(openSurfaceOr).toHaveBeenCalledWith("open-people", "/", "people:rel-marek");
  });
});

/* ── HS-173-03: HEALTH ─────────────────────────────────────────────── */

// Recorded from `ProjectService.room` (holdspeak/services/project_service.py:710)
// over tests/e2e/_hs173_seed.seed_health_room: the default seed (RED) and the
// browser test's all-green seed (GREEN), 2026-10-11.
const HEALTH_RED = {
  assessment: "on_track", reason: null,
  inputs: { overdue: 0, overdueMilestones: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false },
  signals: {
    review_wait: { present: true, tone: "red", median_days: 2.5, waiting_count: 2,
      per_reviewer: [{ login: "alice", median_days: 4.0, count: 1 }, { login: "bob", median_days: 2.5, count: 2 }] },
    issue_aging: { present: true, tone: "amber", aged_count: 1, threshold_days: 14 },
    ci: { present: true, tone: "amber", failures_last_3: 1, flaky_branch_count: 1, queue: 2 },
    release: { present: true, tone: "red", composite: "red",
      signals: { review_wait: "red", ci: "amber", blockers: "green", overdue: "green" },
      blockers_count: 1, blockers: ["review_wait", "ci"] },
  },
  checked_at: "2026-10-11 15:11:37", merge_queue_depth: 2, people: [], state: "ok",
};
const HEALTH_GREEN = {
  assessment: "on_track", reason: null,
  inputs: { overdue: 0, overdueMilestones: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false },
  signals: {
    review_wait: { present: true, tone: "green", median_days: 0.3, waiting_count: 1,
      per_reviewer: [{ login: "alice", median_days: 0.3, count: 1 }] },
    issue_aging: { present: true, tone: "green", aged_count: 0, threshold_days: 14 },
    ci: { present: true, tone: "green", failures_last_3: 0, flaky_branch_count: 0, queue: 0 },
    release: { present: true, tone: "green", composite: "green",
      signals: { review_wait: "green", ci: "green", blockers: "green", overdue: "green" },
      blockers_count: 0, blockers: [] },
  },
  checked_at: "2026-10-11 15:11:43", merge_queue_depth: 0, people: [], state: "ok",
};

function roomWith(sections: Record<string, unknown>) {
  return { ...clone(BARE_ROOM), ...clone(sections) };
}

describe("HS-173-03: HEALTH rows carry the wire's tones and tokens", () => {
  const pid = BARE_ROOM.project_id;

  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_rows_1440
  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_rows_393
  it("REVIEW WAIT, ISSUE AGING, CI and RELEASE with their tokens and the CHECKED caption", async () => {
    wire({ [room(pid)]: () => roomWith({ health: HEALTH_RED }) });
    render(<WindowHarness scope={`project:${pid}`} />);
    const review = await screen.findByTestId("health-row-review_wait");
    expect(review.textContent).toMatch(/review wait/i);
    expect(review.textContent).toContain("2.5 D MEDIAN");
    expect(review.textContent).toContain("2 WAITING");
    expect(screen.getByTestId("health-row-issue_aging").textContent).toMatch(/issue aging/i);
    expect(screen.getByTestId("health-row-issue_aging").textContent).toContain("1 > 14 D");
    expect(screen.getByTestId("health-row-ci").textContent).toContain("1 FLAKY");
    expect(screen.getByTestId("health-row-ci").textContent).toContain("QUEUE 2");
    expect(screen.getByTestId("health-row-release").textContent).toMatch(/release/i);
    expect(screen.getByTestId("health-row-release").textContent).toContain("1 BLOCKER");
    const lead = (k: string) => screen.getByTestId(`health-row-${k}`).querySelector(".room-signal-lamp")?.getAttribute("data-state");
    expect([lead("review_wait"), lead("issue_aging"), lead("ci"), lead("release")])
      .toEqual(["failure", "warning", "warning", "failure"]);
    expect(screen.getByTestId("health-checked").textContent).toMatch(/^CHECKED /);
    const body = screen.getByTestId("room-body");
    expect(rawButtons(body)).toEqual([]);
    expect(body.textContent).not.toMatch(/\b0\s+(?:NEEDS|SOURCES|DECISIONS|WAITING|FLAKY|QUEUE|BLOCKERS)/);
  });

  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_ready_1440
  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_ready_393
  it("all green says CLEAR, PASSING and READY, never a zero", async () => {
    wire({ [room(pid)]: () => roomWith({ health: HEALTH_GREEN }) });
    render(<WindowHarness scope={`project:${pid}`} />);
    expect((await screen.findByTestId("health-row-issue_aging")).textContent).toContain("CLEAR");
    expect(screen.getByTestId("health-row-ci").textContent).toContain("PASSING");
    expect(screen.getByTestId("health-row-release").textContent).toContain("READY");
    const body = screen.getByTestId("room-body");
    expect(rawButtons(body)).toEqual([]);
    expect(body.textContent).not.toMatch(/\b0\s+(?:NEEDS|SOURCES|DECISIONS|WAITING|FLAKY|QUEUE|BLOCKERS)/);
  });
});

/* ── HS-173-04: the nudge card and its receipt ─────────────────────── */

describe("HS-173-04: Nudge unfolds the card; Send leaves a SENT receipt", () => {
  // Recorded from `ProjectService.room` and `ProjectStewardService._nudge_from_step`
  // over the browser test's `_seed_nudge_project_and_step` (with its
  // `_patch_resolve_review_people`), 2026-10-11.
  const NEEDS = { items: [{ source: "github", kind: "review_bottleneck", title: "Ania Kowalska",
    why: "REVIEW BOTTLENECK · 3.0 D MEDIAN · 1 PRS WAITING", since: "", url: null, verb: "nudge",
    severity: "warning", relationship_id: "rel-ania-test", median_days: 3.0, count: 1 }], count: 1, state: "ok" };
  const PEOPLE = [{ relationship_id: "rel-ania-test", display_name: "Ania Kowalska", login: "ania-k",
    median_days: 3.0, count: 1, nudge: { step_id: "step1", state: "proposed", pr_number: 612, sent_at: null } }];
  const STEP = { step_id: "step1", state: "proposed", effect_kind: "github_comment", repo: "org/repo", pr_number: 612,
    pr_title: "Rig settles animations before every shot", pr_url: "https://github.com/org/repo/pull/612",
    reviewer_login: "ania-k", days: 3,
    comment_text: "This PR has been waiting for review for 3 days. Flagged by HoldSpeak.", host: "github.com",
    receipt: {}, created_at: "2026-10-11T15:12:18+00:00", completed_at: null };
  // Not recorded (the send needs gh): the route answers `{"success": True, **result, **kernel_fields}`
  // (holdspeak/web/routes/steward.py:228) over `_settle_nudge`'s sent answer
  // (holdspeak/services/project_steward_service.py:2087-2090).
  const SENT = { success: true, operation_id: "op_nudge_1", receipt: { effect_kind: "github_comment", pr_number: 612,
    reviewer_login: "ania-k", outcome: "applied", reviewer: "Ania Kowalska",
    comment_url: "https://github.com/org/repo/pull/612#issuecomment-123456",
    text: STEP.comment_text } };
  const pid = BARE_ROOM.project_id;
  const table = (): Record<string, Answer> => ({
    [room(pid)]: () => roomWith({ needsYou: NEEDS, health: { ...HEALTH_RED, people: PEOPLE } }),
    [`GET /api/projects/${pid}/nudges`]: () => ({ nudges: [clone(STEP)] }),
    "POST /api/nudges/step1/send": () => clone(SENT),
  });

  // replaces: tests/e2e/test_hs173_health_glass.py::test_nudge_card_1440
  // replaces: tests/e2e/test_hs173_health_glass.py::test_nudge_card_393
  it("the bottleneck row has Nudge; the card names who, PR #612, GITHUB.COM, Send and Dismiss", async () => {
    wire(table());
    render(<WindowHarness scope={`project:${pid}`} />);
    expect(await screen.findByTestId("bottleneck-row")).toBeTruthy();
    fireEvent.click(await screen.findByTestId("nudge-verb"));
    const card = await screen.findByTestId("nudge-card");
    expect(screen.getByTestId("nudge-card-who").textContent).toBe("Ania Kowalska");
    expect(screen.getByTestId("nudge-card-pr").textContent).toContain("#612");
    expect(card.textContent).toContain("GITHUB.COM");
    expect(screen.getByTestId("nudge-send")).toBeTruthy();
    expect(screen.getByTestId("nudge-dismiss")).toBeTruthy();
    expect(rawButtons(screen.getByTestId("room-body"))).toEqual([]);
  });

  // replaces: tests/e2e/test_hs173_health_glass.py::test_nudge_sent_1440
  // replaces: tests/e2e/test_hs173_health_glass.py::test_nudge_sent_393
  it("Send posts the comment and leaves SENT · name · #612 · GITHUB.COM, no Undo; the row says NUDGED JUST NOW", async () => {
    wire(table());
    render(<WindowHarness scope={`project:${pid}`} />);
    fireEvent.click(await screen.findByTestId("nudge-verb"));
    fireEvent.click(await screen.findByTestId("nudge-send"));
    const receipt = await screen.findByTestId("nudge-receipt-row");
    const text = (receipt.textContent ?? "").toUpperCase();
    expect(text).toContain("SENT");
    expect(text).toContain("ANIA KOWALSKA");
    expect(receipt.textContent).toContain("#612");
    expect(text).toContain("GITHUB.COM");
    expect(text).not.toContain("UNDO");
    expect(screen.getByTestId("nudge-cooldown").textContent).toBe("NUDGED JUST NOW");
    expect(calls.find((c) => c.key === "POST /api/nudges/step1/send")?.json).toEqual({ text: STEP.comment_text });
    expect(rawButtons(screen.getByTestId("room-body"))).toEqual([]);
  });
});

/* ── PHILO-10-01: an UNKNOWN send is never a delivery (the face half) ── */

describe("PHILO-10-01: an UNKNOWN send is not counted as a delivery", () => {
  // replaces: tests/e2e/test_philo10_01_unknown_send_face.py::TestUnknownSendFace::test_an_unknown_send_is_never_shown_as_delivered (face half)
  // The hub half (ENAMETOOLONG settles UNKNOWN, no proof) is the T1 successor's.
  // The update row and its sends are the hub's own answers after one sent and
  // one ENAMETOOLONG send (GET /api/projects/{id}/updates, GET /api/channels/sends).
  it("the list chips count one DELIVERY and one RESULT UNKNOWN; the history row says CHECK and its lead warns", async () => {
    const { decodeUpdate } = await import("../update/model");
    const { DeliveryHistory, ListChips } = await import("../../channels/SendWell");
    const update = decodeUpdate(clone(UPDATES_AFTER_SENDS.updates[0]) as Record<string, unknown>);
    wire({ "GET /api/channels/sends": () => clone(SENDS) });
    const ctrl = {
      deliverTo: "", setDeliverTo: () => {}, deliverBusy: false, deliverLocked: false,
      deliverOutcome: { kind: "none" }, markDelivered: async () => {}, reloadDeliveries: async () => {},
      deliveriesReadFailed: false,
    } as never;

    const list = render(<ListChips update={update} />);
    const unknown = await screen.findByTestId("update-unknown-chip");
    const chip = (el: Element) => el.querySelector(".surface-state-chip")!;
    expect(chip(unknown).getAttribute("aria-label")).toBe("RESULT UNKNOWN ×1");
    expect(chip(unknown).getAttribute("data-state")).toBe("warning");
    expect(chip(screen.getByTestId("update-delivered-chip")).getAttribute("aria-label")).toBe("DELIVERY ×1");
    list.unmount();

    render(<DeliveryHistory ctrl={ctrl} update={update} sends={clone(SENDS.sends) as never} />);
    const section = screen.getByTestId("delivery-section");
    expect(section.querySelector("h3")?.textContent).toBe("DELIVERY 1");
    const rows = screen.getAllByTestId("delivery-row");
    expect(rows.map((r) => r.querySelector("[data-outcome]")?.getAttribute("data-outcome"))).toEqual(["sent", "unknown"]);
    expect(rows.map((r) => r.querySelector("[data-outcome] .surface-state-chip")?.getAttribute("data-state")))
      .toEqual(["success", "warning"]);
    expect(rows[0].textContent).toContain("Team folder");
    expect(rows[0].textContent).toContain("SAVED");
    expect(rows[0].textContent).toContain("/tmp/rig/out/2026-10-11-payments-ledger-cutover-rev-1-a7c54e99.md");
    expect(rows[1].textContent).toContain("RESULT UNKNOWN · CHECK Long path folder");
    expect(rows[1].textContent).toContain("FILE NOT CONFIRMED");
    expect(rows[1].textContent).not.toContain("SAVED");
    expect(rawButtons(section)).toEqual([]);
  });
});

/* ── HS-200-11: Prepare states its coverage before the run ─────────── */

describe("HS-200-11: the Prepare face states coverage, sources and the route before the run", () => {
  // replaces: tests/e2e/test_hs200_preparation_brief_glass.py::test_prepare_face_states_coverage_before_the_run
  // (the purpose textarea's no-clip box is the generic sweep's, T3)
  const pid = PREP_ROOM.project_id;

  it("COVERAGE · 2 OF 4, SOURCES 4 with both gaps and their repairs, CARRIED FORWARD 1, the route READY on THIS DEVICE", async () => {
    wire({
      [room(pid)]: () => clone(PREP_ROOM),
      [`GET /api/projects/${pid}/briefs/route`]: () => clone(PREP_ROUTE),
      [`GET /api/projects/${pid}/briefs/manifest`]: () => clone(PREP_MANIFEST),
      [`GET /api/projects/${pid}/briefs`]: () => ({ briefs: [] }),
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    const result = await screen.findByTestId("room-ask-result");
    fireEvent.change(within(result).getByRole("combobox"), { target: { value: "brief" } });
    const coverage = await screen.findByTestId("prepare-coverage");
    const posture = screen.getByTestId("prepare-posture");
    const words = (el: Element) => el.querySelector(".surface-state-chip")?.getAttribute("aria-label");
    expect(screen.getByTestId("prepare-head-name").textContent?.trim()).toBe("Prepare a brief");
    expect(words(coverage)).toBe("COVERAGE · 2 OF 4");
    expect(coverage.getAttribute("data-complete")).toBe("false");
    expect(screen.getByTestId("prepare-purpose-by-hand").textContent?.trim()).toBe("PURPOSE SET BY HAND");
    expect(screen.getByTestId("prepare-no-calendar").textContent?.trim()).toBe("NO CALENDAR");
    const route = await screen.findByTestId("prepare-route");
    expect(route.getAttribute("data-state")).toBe("ready");
    expect(screen.getByTestId("prepare-route-model").textContent?.trim()).toBe("QWEN3 35B");
    expect(route.textContent).toContain("THIS DEVICE");
    expect(route.textContent).not.toContain("127.0.0.1");

    const captions = Array.from(posture.querySelectorAll(".surface-section-head h3")).map((h) => h.textContent?.trim());
    expect(captions[0]).toBe("SOURCES 4");
    expect(captions).toContain("CARRIED FORWARD 1");
    const states = screen.getAllByTestId("prepare-source-state");
    expect(states.map((s) => s.getAttribute("data-state")).sort()).toEqual(["available", "available", "failed", "stale"]);
    expect(states.map(words)).toContain("CREDENTIAL EXPIRED · CONFLUENCE");
    expect(screen.getAllByTestId("prepare-source-repair").map((b) => b.textContent?.trim()).sort()).toEqual(["Reconnect", "Retry"]);
    const observed = screen.getAllByTestId("prepare-source-observed").map((o) => o.textContent?.trim() ?? "");
    expect(observed).toHaveLength(4);
    expect(observed.every((t) => t.startsWith("OBSERVED "))).toBe(true);

    // An empty purpose: Prepare is refused; the purpose is a textarea that persists.
    expect((screen.getByTestId("prepare-verb") as HTMLButtonElement).disabled).toBe(true);
    const purpose = screen.getByRole("textbox", { name: "Purpose" });
    expect(purpose.tagName).toBe("TEXTAREA");
    fireEvent.change(purpose, { target: { value: "Architecture review, cut-over sequencing, rollback rehearsal" } });
    await waitFor(() => expect((screen.getByTestId("prepare-verb") as HTMLButtonElement).disabled).toBe(false));
    expect(sessionStorage.getItem("hs.room.prepareDrafts")).toContain("rollback rehearsal");
    // The route probe sends nothing: no prepare request left the face.
    expect(calls.filter((c) => c.key.endsWith("/briefs/prepare"))).toEqual([]);
    expect(Array.from(posture.querySelectorAll("button")).filter((b) => !(b.getAttribute("aria-label") || b.textContent || "").trim())).toEqual([]);
  });
});

/* ── PHILO-17 sources: Add source, sign in, Park receipt, Register ───── */

describe("PHILO-17 sources: the Room's SOURCES on a bare project", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_room_add_source_and_sign_in (the Room half;
  // the Go ▸ Projects leg is the desk menu's, not the Room's)
  const pid = BARE_ROOM.project_id;

  it("SOURCES opens Add source; GitHub says NOT SIGNED IN; Connect opens the sign-in well with the command and Copy, no Settings", async () => {
    wire({
      [room(pid)]: () => clone(BARE_ROOM),
      [`GET /api/projects/${pid}/repository`]: () => clone(BARE_REPOSITORY),
      "GET /api/connections": () => clone(CONNECTIONS_NOT_SIGNED_IN),
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    const well = await screen.findByTestId("room-add-sources");
    const gh = await within(well).findByTestId("door-row-github");
    expect(within(well).getAllByTestId("door-row-jira")).toHaveLength(1);
    const text = (gh.textContent ?? "").toUpperCase();
    expect(text).toContain("NOT SIGNED IN");
    expect(text).not.toContain("UNREACHABLE");
    expect(screen.queryByTestId("room-add-source")).toBeNull(); // open already: no second Add source
    fireEvent.click(within(gh).getByTestId("door-connect-github"));
    const signIn = await within(well).findByTestId("signin-well-github");
    expect(signIn.textContent).toContain("gh auth login");
    expect(within(signIn).getAllByRole("button", { name: "Copy" })).toHaveLength(1);
    expect(openSurface).not.toHaveBeenCalled();
    expect(openSurfaceOr).not.toHaveBeenCalled();
    expect(Object.keys(useDesk.getState().windowsById).filter((id) => id.includes("settings"))).toEqual([]);
  });
});

describe("PHILO-17 sources: Park from FILES leaves PARKED · <name> with Restore in the Room", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_park_from_files_leaves_its_receipt_and_restore_in_the_room
  it("Get Info ▸ Park: the receipt and Restore stay in the Room; Restore brings the meeting back", async () => {
    const { DrawerInfoWindow } = await import("../../../desk/drawer/InfoWindow");
    const { useDrawers } = await import("../../../desk/drawer/store");
    useDesk.setState({ refresh: vi.fn(() => Promise.resolve()) } as never);
    let parked = false;
    wire({
      [room("p-lone")]: () => clone(LONE_ROOM),
      "GET /api/projects/p-lone/meetings": () => (parked ? { meetings: [] } : clone(LONE_MEETINGS)),
      "GET /api/projects/p-lone/repository": () => ({ ...clone(BARE_REPOSITORY), project_id: "p-lone" }),
      "DELETE /api/meetings/m-lone": () => { parked = true; return clone(PARK_DELETE); },
      "POST /api/meetings/m-lone/restore": () => { parked = false; return clone(RESTORE); },
    });
    function Desk() {
      const infos = useDrawers((s) => s.infos);
      return (
        <>
          <WindowHarness scope="project:p-lone" />
          {infos.map((info) => <DrawerInfoWindow key={info.ref} info={info} />)}
        </>
      );
    }
    render(<Desk />);
    const files = await screen.findByTestId("room-files");
    fireEvent.click(await within(files).findByRole("button", { name: /^Vendor call,/ }));
    fireEvent.click(within(files).getByTestId("room-files-info"));
    fireEvent.click(await screen.findByRole("button", { name: "Park" }), { detail: 1 });
    const receipt = await within(screen.getByTestId("room-files")).findByTestId("room-files-park-receipt");
    expect(receipt.querySelector("[role=status]")?.textContent).toBe("PARKED · Vendor call");
    expect(calls.some((c) => c.key === "DELETE /api/meetings/m-lone")).toBe(true);
    // The row leaving FILES rides the desk's refresh (stubbed here): that leg stays the browser's.
    fireEvent.click(within(receipt).getByRole("button", { name: "Restore" }));
    await waitFor(() => expect(calls.some((c) => c.key === "POST /api/meetings/m-lone/restore")).toBe(true));
    await waitFor(() => expect(screen.getByTestId("room-files-park-receipt").querySelector("[role=status]")?.textContent)
      .toMatch(/RESTORED/));
    useDrawers.getState().setReceipt("p-lone", null);
  });
});

describe("PHILO-17 sources: an older project registers its repository in the Room", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_an_older_project_registers_its_repository_in_the_room
  it("Register posts the watched repository; the verb leaves once the hub says registered", async () => {
    const pid = OLDER_ROOM.project_id;
    let registered = false;
    wire({
      [room(pid)]: () => clone(OLDER_ROOM),
      [`GET /api/projects/${pid}/repository`]: () => clone(registered ? OLDER_REPOSITORY_AFTER : OLDER_REPOSITORY_BEFORE),
      [`POST /api/projects/${pid}/repository`]: () => { registered = true; return clone(OLDER_REGISTER); },
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    const register = await screen.findByTestId("room-register");
    expect(register.getAttribute("title")).toBe("Register acme/app");
    fireEvent.click(register);
    await waitFor(() => expect(screen.queryByTestId("room-register")).toBeNull());
    expect(calls.find((c) => c.key === `POST /api/projects/${pid}/repository`)?.json).toEqual({ repository: "acme/app" });
    expect(screen.queryByTestId("room-register-failure")).toBeNull();
  });
});

/* ── PHILO-14 A5b: a proposal request reveals, and never writes ────── */

describe("PHILO-14 A5b: a proposal request over the Room", () => {
  const pid = P172_ROOM_BEFORE.project_id;
  const proposalId = P172_PROPOSALS.proposals[1].id; // "cut-over on the 12th"
  const draft = () => ({ ...clone(DRAFT.update), project_id: pid });
  const base = (): Record<string, Answer> => ({
    [room(pid)]: () => clone(P172_ROOM_BEFORE),
    [`GET /api/projects/${pid}/proposals`]: () => clone(P172_PROPOSALS),
    [`GET /api/projects/${pid}/updates`]: () => ({ updates: [draft()], latest_published_update_id: null }),
  });
  const puts = () => calls.filter((c) => c.key === `PUT /api/updates/${DRAFT.update.id}`);
  // The row is the `li` (data-selected); its line carries the testid and is what scrolls
  // (desk/surface/Surface.tsx: SurfaceLedgerRow `selected`).
  const selected = () => document.querySelector(".surface-ledger-row[data-selected] [data-testid=proposal-row]");

  async function openEditor() {
    fireEvent.click(await screen.findByTestId("updates-verb"));
    fireEvent.click((await screen.findAllByTestId("update-list-item"))[0]);
    return (await screen.findByTestId("update-body-textarea")) as HTMLTextAreaElement;
  }

  for (const save of ["pending", "failed"] as const) {
    // replaces: tests/e2e/test_philo14_a2b_paths_glass.py::TestA2bPathsGlass::test_a_proposal_request_never_saves_the_update_draft
    it(`a proposal request never writes the draft (the save of A ${save}); his newest words stay unsaved`, async () => {
      const { openProjectProposal } = await import("../../../desk/openObject");
      const { ApiError } = await import("../../../lib/api");
      let release!: () => void;
      wire({
        ...base(),
        [`PUT /api/updates/${DRAFT.update.id}`]: (init) => {
          if (save === "failed") throw new ApiError(500, "injected failure", { detail: "injected failure" });
          // The hub answers the PUT with the saved update (the recorded PUT answer, its body the one sent).
          const answer = { ...clone(PUT), update: { ...clone(PUT.update), body_md: String(init.json?.body_md) } };
          return new Promise((resolve) => { release = () => resolve(answer); });
        },
      });
      render(<WindowHarness scope={`project:${pid}`} />);
      await waitFor(() => expect(screen.getAllByTestId("proposal-row")).toHaveLength(2));
      let editor = await openEditor();
      fireEvent.change(editor, { target: { value: `${editor.value} AAA-saved-words` } });
      fireEvent.click(screen.getByTestId("update-verb-save"));
      if (save === "failed") await screen.findByText(/NOT SAVED/);
      await waitFor(() => expect(puts()).toHaveLength(1));
      fireEvent.change(editor, { target: { value: `${editor.value} BBB-newer-words` } });

      act(() => openProjectProposal(pid, proposalId));
      await waitFor(() => expect(selected()).not.toBeNull());
      expect(selected()!.textContent).toContain("cut-over on the 12th");
      expect(screen.queryByTestId("update-posture")).toBeNull();
      expect(puts()).toHaveLength(1);
      expect(String(puts()[0].json?.body_md)).not.toContain("BBB");
      if (save === "pending") await act(async () => { release(); await Promise.resolve(); });

      fireEvent.click(screen.getByTestId("updates-verb"));
      editor = (await screen.findByTestId("update-body-textarea")) as HTMLTextAreaElement;
      expect(editor.value).toContain("AAA-saved-words");
      expect(editor.value).toContain("BBB-newer-words");
      expect(screen.getByTestId("update-footer-receipt").textContent).toContain("UNSAVED");
      if (save === "failed") expect(screen.getByText(/NOT SAVED/)).toBeTruthy();
      expect(puts()).toHaveLength(1);
    });
  }

  for (const away of ["history", "update"] as const) {
    // replaces: tests/e2e/test_philo14_a2b_paths_glass.py::TestA2bPathsGlass::test_a_proposal_reopened_over_history_is_revealed
    // (the row's on-screen box is the one geometric leg; here: the wing, the selection and the scroll call)
    it(`the same proposal asked for again over ${away} returns to the ROOM wing, selected, scrolled into view`, async () => {
      const { openProjectProposal } = await import("../../../desk/openObject");
      const scrolled: Element[] = [];
      const original = Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView = function (this: Element) { scrolled.push(this); };
      try {
        wire(base());
        render(<WindowHarness scope={`project:${pid}`} />);
        await waitFor(() => expect(screen.getAllByTestId("proposal-row")).toHaveLength(2));
        act(() => openProjectProposal(pid, proposalId));
        await waitFor(() => expect(selected()).not.toBeNull());
        await waitFor(() => expect(scrolled).toContain(selected()));
        const wings = screen.getByTestId("wing-slot");
        if (away === "history") {
          fireEvent.click(within(wings).getByRole("tab", { name: "History" }));
          await screen.findByTestId("room-history");
        } else {
          fireEvent.click(screen.getByRole("button", { name: "Draft update" }));
          await screen.findByTestId("update-posture");
        }
        await waitFor(() => expect(selected()).toBeNull());
        scrolled.length = 0;

        act(() => openProjectProposal(pid, proposalId));
        await waitFor(() => expect(selected()).not.toBeNull());
        expect(selected()!.textContent).toContain("cut-over on the 12th");
        expect(within(screen.getByTestId("wing-slot")).getByRole("tab", { name: "Room" }).getAttribute("aria-selected")).toBe("true");
        // The row's own mount scrolls it (nearest) and the Room's request
        // reveal scrolls it (center): every scroll is the selected row.
        await waitFor(() => expect(scrolled.length).toBeGreaterThan(0));
        expect(scrolled.every((el) => el === selected())).toBe(true);
        expect(screen.queryByTestId("update-posture")).toBeNull();
      } finally {
        Element.prototype.scrollIntoView = original;
      }
    });
  }

  it("the same proposal asked for again while its row is drawn scrolls it into view again", async () => {
    // The test diet: the Room's once-per-request reveal looked for
    // `[data-testid=proposal-row][data-selected]`, which never matched (the
    // mark is on the li), so a second request for a row already selected
    // and drawn scrolled nothing. Its line is `aria-current`.
    const { openProjectProposal } = await import("../../../desk/openObject");
    const scrolled: Element[] = [];
    const original = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function (this: Element) { scrolled.push(this); };
    try {
      wire(base());
      render(<WindowHarness scope={`project:${pid}`} />);
      await waitFor(() => expect(screen.getAllByTestId("proposal-row")).toHaveLength(2));
      act(() => openProjectProposal(pid, proposalId));
      await waitFor(() => expect(selected()).not.toBeNull());
      await waitFor(() => expect(scrolled).toContain(selected()));
      scrolled.length = 0;

      act(() => openProjectProposal(pid, proposalId));
      await waitFor(() => expect(scrolled).toEqual([selected()]));
    } finally {
      Element.prototype.scrollIntoView = original;
    }
  });
});

/* ── round 2: recorded wire (2026-10-11, scratch rig dump_hub3.py on a booted hub) ──
 * Prepare: the parked test_hs200_preparation_brief_glass seeds (_seed_decisions, _seed_sources,
 * _define_route to its FakeLLM): a board answer (_board_reply) then Keep; a prose answer (409);
 * an 8 s answer stopped at 1 s (the stop answer, then the prepare's own 409).
 * Daily loop: the parked test_phase200_daily_loop's import control (`/api/meetings/import` with a
 * DAY1_START `started_at_ms`), its DECISION_TEXT / COMMITMENT_TEXT proposals (written with
 * db.proposals.create_proposal, not its plugin fixture), both confirmed through POST confirm, the
 * action with a due DATE. */
const PREP2_ROOM = {"project_id": "proj-3dca10cdb85f", "revision": 1, "observed_at": "2026-10-11T10:31:10.782296", "nextCheckAt": "2026-10-11T16:32:00+00:00", "project": {"id": "proj-3dca10cdb85f", "name": "Q4 platform", "description": "Seeded.", "keywords": [], "team_members": [], "context": {}, "detection_threshold": 0.4, "is_archived": false, "meeting_count": 1, "created_at": "2026-10-11T10:31:10.782296", "updated_at": "2026-10-11T10:31:10.782296", "purpose": null, "outcome_text": null, "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 1, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 1, "latest": {"id": "mtg_8a1466583b", "title": "Cut-over sync", "started_at": "2026-10-11T10:31:10", "duration_seconds": null, "intel_status": "disabled", "source": "auto", "confidence": 0.0}, "state": "ok"}, "resources": {"count": 0, "latest": null, "state": "ok"}, "changes": {"recent": [{"id": "pchg_d64cdf07f672647c62cbb02a75c1992f", "project_id": "proj-3dca10cdb85f", "project_revision": 1, "change_kind": "project.created", "target_ref": "project:proj-3dca10cdb85f", "actor_ref": "principal:owner-session", "command_id": "dump3", "before_hash": null, "after_hash": "537d7c3db9796346e11bde9d6c0d40e3", "summary_json": "{\"name\": \"Q4 platform\"}", "created_at": "2026-10-11T16:31:10.782296+00:00"}], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [], "count": 0, "state": "ok"}, "sources": {"items": [{"watchId": "w_confluence_c02207ca1b", "provider": "confluence", "scope": "", "tokens": [], "checkedAt": "2026-10-11T15:31:10+00:00", "nextCheckAt": null, "host": "", "state": "cant_check", "plainReason": "Confluence rejected the token (401)", "suggested": false, "watchIds": ["w_confluence_c02207ca1b"], "freshness": "failed", "freshnessReason": "Confluence rejected the token (401)"}, {"watchId": "w_gh_840dac7968", "provider": "github", "scope": "karolswdev/HoldSpeak", "tokens": ["2 OPEN PRS"], "checkedAt": "2026-10-11T16:29:10+00:00", "nextCheckAt": "2026-10-11T17:31:10+00:00", "host": "github.com", "state": "live", "plainReason": null, "suggested": false, "watchIds": ["w_gh_840dac7968"], "freshness": "available", "freshnessReason": null}, {"watchId": "w_jira_9cea93e916", "provider": "jira", "scope": "KAN", "tokens": ["CLEAR"], "checkedAt": "2026-10-10T20:31:10+00:00", "nextCheckAt": "2026-10-11T16:32:00+00:00", "host": "acme.atlassian.net", "state": "live", "plainReason": null, "suggested": false, "watchIds": ["w_jira_9cea93e916"], "freshness": "stale", "freshnessReason": "not checked recently", "missedCheckAt": "2026-10-10T21:31:10+00:00"}, {"watchId": "w_9376efe3da13", "provider": "meeting", "scope": "MEETINGS", "tokens": [], "checkedAt": "2026-10-11T16:29:10+00:00", "nextCheckAt": "2026-10-11T17:31:10+00:00", "host": "", "state": "live", "plainReason": null, "suggested": false, "watchIds": ["w_9376efe3da13"], "freshness": "available", "freshnessReason": null}], "count": 4, "nextCheckAt": "2026-10-11T16:32:00+00:00", "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": "2026-10-11T10:31:10", "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [{"id": "decrec_cur_e66c0c7d", "text": "Cut-over runs on the read replica first", "at": "2026-10-11T10:31:10", "url": null, "lifecycle": "active", "kind": "decision", "source_type": "meeting", "source_id": "mtg_8a1466583b"}, {"id": "decrec_old_31573f97", "text": "Cut-over runs under a full freeze", "at": "2026-10-11T10:31:10", "url": null, "lifecycle": "superseded", "kind": "decision", "source_type": "meeting", "source_id": "mtg_8a1466583b", "successor_id": "decrec_cur_e66c0c7d"}], "state": "ok"}, "commitments": {"items": [], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [{"id": "80030cf0-1283-427b-ae3a-7cbbd8ede43b", "op": "create_project", "label": "ProjectService.create_project", "title": "ProjectService.create_project", "outcome": "ok", "reason": null, "origin": null, "caller": null, "identity": null, "at": 1791736270.7735019, "timestamp": 1791736270.7735019}], "state": "ok"}};
const PREP2_ROUTE = {"route": {"state": "ready", "token": "READY", "host": "127.0.0.1", "model": "QWEN3 35B", "boundary": "private_network", "reason": "", "repair": "Set up model", "invoke": {"sent": false, "operation_id": "", "outcome": "", "send_phase": "", "host": ""}}};
const PREP2_MANIFEST = {"manifest": {"project_id": "proj-3dca10cdb85f", "project_revision": 1, "purpose": "", "prepared_at": "2026-10-11T16:31:11.157159+00:00", "calendar": {"present": false}, "coverage": {"expected": 4, "available": 2, "complete": false}, "sources": [{"source_id": "w_confluence_c02207ca1b", "kind": "confluence", "label": "CONFLUENCE", "state": "failed", "observed_at": "2026-10-11T15:31:10+00:00", "revision": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect", "href": "/settings"}, "tokens": [], "host": "", "watch_ids": ["w_confluence_c02207ca1b"]}, {"source_id": "w_gh_840dac7968", "kind": "github", "label": "karolswdev/HoldSpeak", "state": "available", "observed_at": "2026-10-11T16:29:10+00:00", "revision": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "tokens": ["2 OPEN PRS"], "host": "github.com", "watch_ids": ["w_gh_840dac7968"]}, {"source_id": "w_jira_9cea93e916", "kind": "jira", "label": "KAN", "state": "stale", "observed_at": "2026-10-10T20:31:10+00:00", "revision": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"token": "STALE", "verb": "Retry", "href": "/"}, "tokens": ["CLEAR"], "host": "acme.atlassian.net", "watch_ids": ["w_jira_9cea93e916"]}, {"source_id": "w_9376efe3da13", "kind": "meeting", "label": "MEETINGS", "state": "available", "observed_at": "2026-10-11T16:29:10+00:00", "revision": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "tokens": [], "host": "", "watch_ids": ["w_9376efe3da13"]}], "omitted": [{"source_id": "w_confluence_c02207ca1b", "kind": "confluence", "label": "CONFLUENCE", "state": "failed", "observed_at": "2026-10-11T15:31:10+00:00", "revision": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect", "href": "/settings"}, "tokens": [], "host": "", "watch_ids": ["w_confluence_c02207ca1b"]}, {"source_id": "w_jira_9cea93e916", "kind": "jira", "label": "KAN", "state": "stale", "observed_at": "2026-10-10T20:31:10+00:00", "revision": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"token": "STALE", "verb": "Retry", "href": "/"}, "tokens": ["CLEAR"], "host": "acme.atlassian.net", "watch_ids": ["w_jira_9cea93e916"]}], "decisions": [{"ref": "decision_record:decrec_cur_e66c0c7d", "text": "Cut-over runs on the read replica first", "lifecycle": "current", "at": "2026-10-11T10:31:10", "meeting_title": "", "kind": "decision"}, {"ref": "decision_record:decrec_old_31573f97", "text": "Cut-over runs under a full freeze", "lifecycle": "superseded", "at": "2026-10-11T10:31:10", "meeting_title": "", "kind": "decision", "successor_ref": "decision_record:decrec_cur_e66c0c7d"}], "commitments": [], "not_included": []}};
const PREPARE_OK = {"success": true, "brief": {"id": "pbrief_0563f59277ef3374ed2b0bb8", "project_id": "proj-3dca10cdb85f", "project_revision": 1, "purpose": "Architecture review, cut-over sequencing", "lifecycle": "draft", "manifest_revision": 1, "manifest": {"calendar": {"present": false}, "commitments": [], "coverage": {"available": 2, "complete": false, "expected": 4}, "decisions": [{"at": "2026-10-11T10:31:10", "kind": "decision", "lifecycle": "current", "meeting_title": "", "ref": "decision_record:decrec_cur_e66c0c7d", "text": "Cut-over runs on the read replica first"}, {"at": "2026-10-11T10:31:10", "kind": "decision", "lifecycle": "superseded", "meeting_title": "", "ref": "decision_record:decrec_old_31573f97", "successor_ref": "decision_record:decrec_cur_e66c0c7d", "text": "Cut-over runs under a full freeze"}], "not_included": [{"ref": "source:w_gh_840dac7968", "section": "priorities", "title": "Extra priority four", "why": "over the bound of 3 for DECIDE TODAY"}, {"ref": "source:w_gh_840dac7968", "section": "priorities", "title": "Extra priority five", "why": "over the bound of 3 for DECIDE TODAY"}], "omitted": [{"host": "", "kind": "confluence", "label": "CONFLUENCE", "observed_at": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"href": "/settings", "token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect"}, "revision": "2026-10-11T15:31:10+00:00", "source_id": "w_confluence_c02207ca1b", "state": "failed", "tokens": [], "watch_ids": ["w_confluence_c02207ca1b"]}, {"host": "acme.atlassian.net", "kind": "jira", "label": "KAN", "observed_at": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"href": "/", "token": "STALE", "verb": "Retry"}, "revision": "2026-10-10T20:31:10+00:00", "source_id": "w_jira_9cea93e916", "state": "stale", "tokens": ["CLEAR"], "watch_ids": ["w_jira_9cea93e916"]}], "prepared_at": "2026-10-11T16:31:11.263927+00:00", "project_id": "proj-3dca10cdb85f", "project_revision": 1, "purpose": "Architecture review, cut-over sequencing", "sources": [{"host": "", "kind": "confluence", "label": "CONFLUENCE", "observed_at": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"href": "/settings", "token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect"}, "revision": "2026-10-11T15:31:10+00:00", "source_id": "w_confluence_c02207ca1b", "state": "failed", "tokens": [], "watch_ids": ["w_confluence_c02207ca1b"]}, {"host": "github.com", "kind": "github", "label": "karolswdev/HoldSpeak", "observed_at": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "revision": "2026-10-11T16:29:10+00:00", "source_id": "w_gh_840dac7968", "state": "available", "tokens": ["2 OPEN PRS"], "watch_ids": ["w_gh_840dac7968"]}, {"host": "acme.atlassian.net", "kind": "jira", "label": "KAN", "observed_at": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"href": "/", "token": "STALE", "verb": "Retry"}, "revision": "2026-10-10T20:31:10+00:00", "source_id": "w_jira_9cea93e916", "state": "stale", "tokens": ["CLEAR"], "watch_ids": ["w_jira_9cea93e916"]}, {"host": "", "kind": "meeting", "label": "MEETINGS", "observed_at": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "revision": "2026-10-11T16:29:10+00:00", "source_id": "w_9376efe3da13", "state": "available", "tokens": [], "watch_ids": ["w_9376efe3da13"]}]}, "manifest_sha256": "a62939ca5a6aec34233490b37f0b512629e2c1fc04de3b3fb383b8fd21258773", "integrity": "verified", "outline": {"obligations": [], "priorities": [{"span_id": "s_priorities_0", "text": "Cut-over runs on the read replica first"}, {"span_id": "s_priorities_1", "text": "Two open pull requests wait on the runbook"}, {"span_id": "s_priorities_2", "text": "Rehearse the rollback on the replica"}], "questions": [{"span_id": "s_questions_0", "text": "Priya expects the cut-over at 95% by 2026-12-31"}, {"span_id": "s_questions_1", "text": "Sprint velocity improved over the trailing average"}]}, "body_md": "## DECIDE TODAY\n- Cut-over runs on the read replica first\n- Two open pull requests wait on the runbook\n- Rehearse the rollback on the replica\n\n## ASK THEM\n- Priya expects the cut-over at 95% by 2026-12-31\n- Sprint velocity improved over the trailing average", "claims_json": "[{\"acceptance\":\"accepted\",\"kind\":\"decision\",\"refs\":[\"decision_record:decrec_cur_e66c0c7d\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_0\",\"support\":\"supported\",\"support_record\":{\"fields\":[\"decision_text\",\"lifecycle\"],\"method\":\"field_mapping\",\"source_refs\":[\"decision_record:decrec_cur_e66c0c7d\"],\"source_version\":\"project:proj-3dca10cdb85f@1\"},\"text\":\"Cut-over runs on the read replica first\"},{\"acceptance\":\"superseded\",\"kind\":\"decision\",\"refs\":[\"decision_record:decrec_old_31573f97\"],\"section\":\"superseded\",\"span_id\":\"s_superseded_0\",\"support\":\"source_linked\",\"text\":\"Cut-over runs under a full freeze\",\"unknowns\":[{\"type\":\"superseded_by\",\"value\":\"decision_record:decrec_cur_e66c0c7d\"}]},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_1\",\"support\":\"source_linked\",\"text\":\"Two open pull requests wait on the runbook\"},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_2\",\"support\":\"source_linked\",\"text\":\"Rehearse the rollback on the replica\"},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"questions\",\"span_id\":\"s_questions_0\",\"support\":\"source_linked\",\"text\":\"Priya expects the cut-over at 95% by 2026-12-31\",\"unknowns\":[{\"type\":\"deadline\",\"value\":\"2026-12-31\"},{\"type\":\"number\",\"value\":\"95%\"}]},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[],\"section\":\"questions\",\"span_id\":\"s_questions_1\",\"support\":\"unknown\",\"text\":\"Sprint velocity improved over the trailing average\",\"verified\":false}]", "generator": "model:ia_5a50d584c4ef4b5a8949428cef30868f", "generator_host": "127.0.0.1", "generator_model": "QWEN3 35B", "elapsed_ms": 1770, "created_at": "2026-10-11T16:31:11.263927+00:00", "updated_at": "2026-10-11T16:31:11.263927+00:00", "kept_at": null}};
const KEEP = {"success": true, "brief": {"id": "pbrief_0563f59277ef3374ed2b0bb8", "project_id": "proj-3dca10cdb85f", "project_revision": 1, "purpose": "Architecture review, cut-over sequencing", "lifecycle": "kept", "manifest_revision": 1, "manifest": {"calendar": {"present": false}, "commitments": [], "coverage": {"available": 2, "complete": false, "expected": 4}, "decisions": [{"at": "2026-10-11T10:31:10", "kind": "decision", "lifecycle": "current", "meeting_title": "", "ref": "decision_record:decrec_cur_e66c0c7d", "text": "Cut-over runs on the read replica first"}, {"at": "2026-10-11T10:31:10", "kind": "decision", "lifecycle": "superseded", "meeting_title": "", "ref": "decision_record:decrec_old_31573f97", "successor_ref": "decision_record:decrec_cur_e66c0c7d", "text": "Cut-over runs under a full freeze"}], "not_included": [{"ref": "source:w_gh_840dac7968", "section": "priorities", "title": "Extra priority four", "why": "over the bound of 3 for DECIDE TODAY"}, {"ref": "source:w_gh_840dac7968", "section": "priorities", "title": "Extra priority five", "why": "over the bound of 3 for DECIDE TODAY"}], "omitted": [{"host": "", "kind": "confluence", "label": "CONFLUENCE", "observed_at": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"href": "/settings", "token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect"}, "revision": "2026-10-11T15:31:10+00:00", "source_id": "w_confluence_c02207ca1b", "state": "failed", "tokens": [], "watch_ids": ["w_confluence_c02207ca1b"]}, {"host": "acme.atlassian.net", "kind": "jira", "label": "KAN", "observed_at": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"href": "/", "token": "STALE", "verb": "Retry"}, "revision": "2026-10-10T20:31:10+00:00", "source_id": "w_jira_9cea93e916", "state": "stale", "tokens": ["CLEAR"], "watch_ids": ["w_jira_9cea93e916"]}], "prepared_at": "2026-10-11T16:31:11.263927+00:00", "project_id": "proj-3dca10cdb85f", "project_revision": 1, "purpose": "Architecture review, cut-over sequencing", "sources": [{"host": "", "kind": "confluence", "label": "CONFLUENCE", "observed_at": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"href": "/settings", "token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect"}, "revision": "2026-10-11T15:31:10+00:00", "source_id": "w_confluence_c02207ca1b", "state": "failed", "tokens": [], "watch_ids": ["w_confluence_c02207ca1b"]}, {"host": "github.com", "kind": "github", "label": "karolswdev/HoldSpeak", "observed_at": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "revision": "2026-10-11T16:29:10+00:00", "source_id": "w_gh_840dac7968", "state": "available", "tokens": ["2 OPEN PRS"], "watch_ids": ["w_gh_840dac7968"]}, {"host": "acme.atlassian.net", "kind": "jira", "label": "KAN", "observed_at": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"href": "/", "token": "STALE", "verb": "Retry"}, "revision": "2026-10-10T20:31:10+00:00", "source_id": "w_jira_9cea93e916", "state": "stale", "tokens": ["CLEAR"], "watch_ids": ["w_jira_9cea93e916"]}, {"host": "", "kind": "meeting", "label": "MEETINGS", "observed_at": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "revision": "2026-10-11T16:29:10+00:00", "source_id": "w_9376efe3da13", "state": "available", "tokens": [], "watch_ids": ["w_9376efe3da13"]}]}, "manifest_sha256": "a62939ca5a6aec34233490b37f0b512629e2c1fc04de3b3fb383b8fd21258773", "integrity": "verified", "outline": {"obligations": [], "priorities": [{"span_id": "s_priorities_0", "text": "Cut-over runs on the read replica first"}, {"span_id": "s_priorities_1", "text": "Two open pull requests wait on the runbook"}, {"span_id": "s_priorities_2", "text": "Rehearse the rollback on the replica"}], "questions": [{"span_id": "s_questions_0", "text": "Priya expects the cut-over at 95% by 2026-12-31"}, {"span_id": "s_questions_1", "text": "Sprint velocity improved over the trailing average"}]}, "body_md": "## DECIDE TODAY\n- Cut-over runs on the read replica first\n- Two open pull requests wait on the runbook\n- Rehearse the rollback on the replica\n\n## ASK THEM\n- Priya expects the cut-over at 95% by 2026-12-31\n- Sprint velocity improved over the trailing average", "claims_json": "[{\"acceptance\":\"accepted\",\"kind\":\"decision\",\"refs\":[\"decision_record:decrec_cur_e66c0c7d\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_0\",\"support\":\"supported\",\"support_record\":{\"fields\":[\"decision_text\",\"lifecycle\"],\"method\":\"field_mapping\",\"source_refs\":[\"decision_record:decrec_cur_e66c0c7d\"],\"source_version\":\"project:proj-3dca10cdb85f@1\"},\"text\":\"Cut-over runs on the read replica first\"},{\"acceptance\":\"superseded\",\"kind\":\"decision\",\"refs\":[\"decision_record:decrec_old_31573f97\"],\"section\":\"superseded\",\"span_id\":\"s_superseded_0\",\"support\":\"source_linked\",\"text\":\"Cut-over runs under a full freeze\",\"unknowns\":[{\"type\":\"superseded_by\",\"value\":\"decision_record:decrec_cur_e66c0c7d\"}]},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_1\",\"support\":\"source_linked\",\"text\":\"Two open pull requests wait on the runbook\"},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_2\",\"support\":\"source_linked\",\"text\":\"Rehearse the rollback on the replica\"},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"questions\",\"span_id\":\"s_questions_0\",\"support\":\"source_linked\",\"text\":\"Priya expects the cut-over at 95% by 2026-12-31\",\"unknowns\":[{\"type\":\"deadline\",\"value\":\"2026-12-31\"},{\"type\":\"number\",\"value\":\"95%\"}]},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[],\"section\":\"questions\",\"span_id\":\"s_questions_1\",\"support\":\"unknown\",\"text\":\"Sprint velocity improved over the trailing average\",\"verified\":false}]", "generator": "model:ia_5a50d584c4ef4b5a8949428cef30868f", "generator_host": "127.0.0.1", "generator_model": "QWEN3 35B", "elapsed_ms": 1770, "created_at": "2026-10-11T16:31:11.263927+00:00", "updated_at": "2026-10-11T16:31:13.051264+00:00", "kept_at": "2026-10-11T16:31:13.051264+00:00"}};
const BRIEFS_KEPT = {"briefs": [{"id": "pbrief_0563f59277ef3374ed2b0bb8", "project_id": "proj-3dca10cdb85f", "project_revision": 1, "purpose": "Architecture review, cut-over sequencing", "lifecycle": "kept", "manifest_revision": 1, "manifest": {"calendar": {"present": false}, "commitments": [], "coverage": {"available": 2, "complete": false, "expected": 4}, "decisions": [{"at": "2026-10-11T10:31:10", "kind": "decision", "lifecycle": "current", "meeting_title": "", "ref": "decision_record:decrec_cur_e66c0c7d", "text": "Cut-over runs on the read replica first"}, {"at": "2026-10-11T10:31:10", "kind": "decision", "lifecycle": "superseded", "meeting_title": "", "ref": "decision_record:decrec_old_31573f97", "successor_ref": "decision_record:decrec_cur_e66c0c7d", "text": "Cut-over runs under a full freeze"}], "not_included": [{"ref": "source:w_gh_840dac7968", "section": "priorities", "title": "Extra priority four", "why": "over the bound of 3 for DECIDE TODAY"}, {"ref": "source:w_gh_840dac7968", "section": "priorities", "title": "Extra priority five", "why": "over the bound of 3 for DECIDE TODAY"}], "omitted": [{"host": "", "kind": "confluence", "label": "CONFLUENCE", "observed_at": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"href": "/settings", "token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect"}, "revision": "2026-10-11T15:31:10+00:00", "source_id": "w_confluence_c02207ca1b", "state": "failed", "tokens": [], "watch_ids": ["w_confluence_c02207ca1b"]}, {"host": "acme.atlassian.net", "kind": "jira", "label": "KAN", "observed_at": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"href": "/", "token": "STALE", "verb": "Retry"}, "revision": "2026-10-10T20:31:10+00:00", "source_id": "w_jira_9cea93e916", "state": "stale", "tokens": ["CLEAR"], "watch_ids": ["w_jira_9cea93e916"]}], "prepared_at": "2026-10-11T16:31:11.263927+00:00", "project_id": "proj-3dca10cdb85f", "project_revision": 1, "purpose": "Architecture review, cut-over sequencing", "sources": [{"host": "", "kind": "confluence", "label": "CONFLUENCE", "observed_at": "2026-10-11T15:31:10+00:00", "reason": "Confluence rejected the token (401)", "repair": {"href": "/settings", "token": "CREDENTIAL EXPIRED · CONFLUENCE", "verb": "Reconnect"}, "revision": "2026-10-11T15:31:10+00:00", "source_id": "w_confluence_c02207ca1b", "state": "failed", "tokens": [], "watch_ids": ["w_confluence_c02207ca1b"]}, {"host": "github.com", "kind": "github", "label": "karolswdev/HoldSpeak", "observed_at": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "revision": "2026-10-11T16:29:10+00:00", "source_id": "w_gh_840dac7968", "state": "available", "tokens": ["2 OPEN PRS"], "watch_ids": ["w_gh_840dac7968"]}, {"host": "acme.atlassian.net", "kind": "jira", "label": "KAN", "observed_at": "2026-10-10T20:31:10+00:00", "reason": "missed its check", "repair": {"href": "/", "token": "STALE", "verb": "Retry"}, "revision": "2026-10-10T20:31:10+00:00", "source_id": "w_jira_9cea93e916", "state": "stale", "tokens": ["CLEAR"], "watch_ids": ["w_jira_9cea93e916"]}, {"host": "", "kind": "meeting", "label": "MEETINGS", "observed_at": "2026-10-11T16:29:10+00:00", "reason": null, "repair": null, "revision": "2026-10-11T16:29:10+00:00", "source_id": "w_9376efe3da13", "state": "available", "tokens": [], "watch_ids": ["w_9376efe3da13"]}]}, "manifest_sha256": "a62939ca5a6aec34233490b37f0b512629e2c1fc04de3b3fb383b8fd21258773", "integrity": "verified", "outline": {"obligations": [], "priorities": [{"span_id": "s_priorities_0", "text": "Cut-over runs on the read replica first"}, {"span_id": "s_priorities_1", "text": "Two open pull requests wait on the runbook"}, {"span_id": "s_priorities_2", "text": "Rehearse the rollback on the replica"}], "questions": [{"span_id": "s_questions_0", "text": "Priya expects the cut-over at 95% by 2026-12-31"}, {"span_id": "s_questions_1", "text": "Sprint velocity improved over the trailing average"}]}, "body_md": "## DECIDE TODAY\n- Cut-over runs on the read replica first\n- Two open pull requests wait on the runbook\n- Rehearse the rollback on the replica\n\n## ASK THEM\n- Priya expects the cut-over at 95% by 2026-12-31\n- Sprint velocity improved over the trailing average", "claims_json": "[{\"acceptance\":\"accepted\",\"kind\":\"decision\",\"refs\":[\"decision_record:decrec_cur_e66c0c7d\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_0\",\"support\":\"supported\",\"support_record\":{\"fields\":[\"decision_text\",\"lifecycle\"],\"method\":\"field_mapping\",\"source_refs\":[\"decision_record:decrec_cur_e66c0c7d\"],\"source_version\":\"project:proj-3dca10cdb85f@1\"},\"text\":\"Cut-over runs on the read replica first\"},{\"acceptance\":\"superseded\",\"kind\":\"decision\",\"refs\":[\"decision_record:decrec_old_31573f97\"],\"section\":\"superseded\",\"span_id\":\"s_superseded_0\",\"support\":\"source_linked\",\"text\":\"Cut-over runs under a full freeze\",\"unknowns\":[{\"type\":\"superseded_by\",\"value\":\"decision_record:decrec_cur_e66c0c7d\"}]},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_1\",\"support\":\"source_linked\",\"text\":\"Two open pull requests wait on the runbook\"},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"priorities\",\"span_id\":\"s_priorities_2\",\"support\":\"source_linked\",\"text\":\"Rehearse the rollback on the replica\"},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[\"source:w_gh_840dac7968\"],\"section\":\"questions\",\"span_id\":\"s_questions_0\",\"support\":\"source_linked\",\"text\":\"Priya expects the cut-over at 95% by 2026-12-31\",\"unknowns\":[{\"type\":\"deadline\",\"value\":\"2026-12-31\"},{\"type\":\"number\",\"value\":\"95%\"}]},{\"acceptance\":\"unreviewed\",\"kind\":\"inference\",\"refs\":[],\"section\":\"questions\",\"span_id\":\"s_questions_1\",\"support\":\"unknown\",\"text\":\"Sprint velocity improved over the trailing average\",\"verified\":false}]", "generator": "model:ia_5a50d584c4ef4b5a8949428cef30868f", "generator_host": "127.0.0.1", "generator_model": "QWEN3 35B", "elapsed_ms": 1770, "created_at": "2026-10-11T16:31:11.263927+00:00", "updated_at": "2026-10-11T16:31:13.051264+00:00", "kept_at": "2026-10-11T16:31:13.051264+00:00"}]};
const PREPARE_PROSE_409 = {"route": {"state": "unusable_output", "token": "OUTPUT UNUSABLE", "host": "127.0.0.1", "model": "QWEN3 35B", "boundary": "private_network", "reason": "the model output could not be read as a brief", "repair": "Set up model", "invoke": {"sent": true, "operation_id": "op_1b88fd57fc9f4b76b2d595125c2a96ba", "outcome": "succeeded", "send_phase": "provider_returned", "host": "127.0.0.1"}}, "purpose": "Architecture review, cut-over sequencing", "error": "the model output could not be read as a brief", "error_code": "preparation_refused"};
const STOP = {"attempt_id": "att-stop", "stopped": true, "disposition": "refused"};
const PREPARE_STOPPED_409 = {"route": {"state": "stopped", "token": "STOPPED", "host": "127.0.0.1", "model": "QWEN3 35B", "boundary": "private_network", "reason": "stopped by the owner", "repair": "Set up model", "invoke": {"sent": true, "operation_id": "op_6371a9d72a4b45afabcd1c9ccb16658c", "outcome": "succeeded", "send_phase": "provider_returned", "host": "127.0.0.1"}}, "purpose": "Architecture review, cut-over sequencing", "error": "stopped by the owner", "error_code": "preparation_refused"};
const LOOP_ROOM = {"project_id": "proj-bd0a7c7aa9d7", "revision": 1, "observed_at": "2026-10-11T10:31:22.484827", "nextCheckAt": null, "project": {"id": "proj-bd0a7c7aa9d7", "name": "Q4 Platform", "description": "", "keywords": [], "team_members": [], "context": {}, "detection_threshold": 0.4, "is_archived": false, "meeting_count": 1, "created_at": "2026-10-11T10:31:22.484827", "updated_at": "2026-10-11T10:31:22.484827", "purpose": null, "outcome_text": null, "owner_ref": null, "lifecycle": "active", "posture": null, "posture_reason": null, "start_at": null, "target_at": null, "review_cadence_json": null, "next_review_at": null, "template_key": null, "modules_json": null, "revision": 1, "last_review_id": null, "last_review_at": null}, "items": {"focus": [], "totals_by_type": {}, "total": 0, "state": "ok"}, "meetings": {"count": 1, "latest": {"id": "28233437", "title": "Architecture review", "started_at": "2026-10-10T17:00:00+00:00", "duration_seconds": 1980.0, "intel_status": "queued", "source": "manual", "confidence": 1.0}, "state": "ok"}, "resources": {"count": 1, "latest": {"id": "proj-bd0a7c7aa9d7|meeting:28233437", "project_id": "proj-bd0a7c7aa9d7", "resource_ref": "meeting:28233437", "relationship": "member", "source": "manual", "confidence": 1.0, "created_at": "2026-10-11T16:31:22.597929+00:00", "last_modified": "2026-10-11T16:31:22.597929+00:00", "deleted": false}, "state": "ok"}, "changes": {"recent": [{"id": "pchg_fc7317bc156dd27b6527a2a41705ee6d", "project_id": "proj-bd0a7c7aa9d7", "project_revision": 1, "change_kind": "project.created", "target_ref": "project:proj-bd0a7c7aa9d7", "actor_ref": "principal:owner-session", "command_id": "dump3-loop", "before_hash": null, "after_hash": "6bd9e50bc66524706a8e505ed4b2a6f3", "summary_json": "{\"name\": \"Q4 Platform\"}", "created_at": "2026-10-11T16:31:22.484827+00:00"}], "state": "ok"}, "review": {"last_accepted_at": null, "pending_count": 0, "open_review_id": null, "state": "ok"}, "needsYou": {"items": [{"source": "proposal", "kind": "proposal", "title": "Rollback runbook is rehearsed on the read replica first", "why": "PROPOSED · Architecture review", "since": "2026-10-11T16:31:22.598944+00:00", "url": null, "verb": "confirm", "verbHref": "/api/proposals/prop-e5ba4f1741c248e7/confirm", "severity": "info", "proposal_id": "prop-e5ba4f1741c248e7", "proposal_kind": "decision", "host": null, "speaker_label": null, "due_hint": null, "owner_hint": null, "original_text": "Rollback runbook is rehearsed on the read replica first", "meeting_id": "28233437", "action_item_id": null, "meeting_title": "Architecture review", "meeting_started_at": "2026-10-10T11:00:00", "created_at": "2026-10-11T16:31:22.598944+00:00"}, {"source": "proposal", "kind": "proposal", "title": "Draft the rollback runbook", "why": "PROPOSED · Architecture review", "since": "2026-10-11T16:31:22.601477+00:00", "url": null, "verb": "confirm", "verbHref": "/api/proposals/prop-a72f85931924445c/confirm", "severity": "info", "proposal_id": "prop-a72f85931924445c", "proposal_kind": "action", "host": null, "speaker_label": null, "due_hint": null, "owner_hint": "Marek", "original_text": "Draft the rollback runbook", "meeting_id": "28233437", "action_item_id": null, "meeting_title": "Architecture review", "meeting_started_at": "2026-10-10T11:00:00", "created_at": "2026-10-11T16:31:22.601477+00:00"}], "count": 2, "state": "ok"}, "sources": {"items": [], "count": 0, "nextCheckAt": null, "quietUntil": null, "state": "ok"}, "health": {"assessment": "on_track", "reason": null, "inputs": {"overdue": 0, "overdueMilestones": 0, "ciFailing": false, "reviewWaitingDays": null, "targetPassed": false}, "signals": {"review_wait": {"present": false, "tone": "green", "median_days": 0.0, "waiting_count": 0, "per_reviewer": []}, "issue_aging": {"present": false, "tone": "green", "aged_count": 0, "threshold_days": 14}, "ci": {"present": false, "tone": "green", "failures_last_3": 0, "flaky_branch_count": 0, "queue": 0}, "release": {"present": false, "tone": "green", "composite": "green", "signals": {"review_wait": "green", "ci": "green", "blockers": "green", "overdue": "green"}, "blockers_count": 0, "blockers": []}}, "checked_at": null, "merge_queue_depth": 0, "people": [], "state": "ok"}, "sinceRead": {"readAt": null, "groups": [], "state": "ok"}, "decisions": {"items": [], "state": "ok"}, "commitments": {"items": [], "state": "ok"}, "target": {"targetAt": null, "daysLeft": null, "passed": false, "state": "ok"}, "updates": {"count": 0, "counts": {}, "recent": [], "latest_published": null, "state": "ok"}, "steward": {"latest_run": null, "enabled": false, "unattended_enabled": false, "state": "ok"}, "receipts": {"items": [{"id": "9c99d534-0ebc-4325-a3d2-a5bae0fca257", "op": "create_project", "label": "ProjectService.create_project", "title": "ProjectService.create_project", "outcome": "ok", "reason": null, "origin": null, "caller": null, "identity": null, "at": 1791736282.484575, "timestamp": 1791736282.484575}], "state": "ok"}};
const LOOP_PROPOSALS = {"project_id": "proj-bd0a7c7aa9d7", "proposals": [{"id": "prop-a72f85931924445c", "meeting_id": "28233437", "project_id": "proj-bd0a7c7aa9d7", "kind": "action", "text": "Draft the rollback runbook", "owner_hint": "Marek", "due_hint": null, "owner": "Marek", "due": null, "owner_supplied": null, "due_supplied": null, "source_artifact_id": null, "source_plugin": "action_owner_enforcer", "segment_timestamp": null, "speaker_label": null, "model_host": null, "state": "proposed", "original_text": "Draft the rollback runbook", "decision_record_id": null, "rationale": null, "commitment_id": null, "created_at": "2026-10-11T16:31:22.601477+00:00", "decided_at": null, "retry_key": null, "extraction_revision": null, "job_id": null, "job_attempt": null, "extraction_model": null, "span_start": null, "span_end": null, "segment_index": null, "claim_kind": "proposal", "support": "unknown", "support_record": null, "acceptance": "unreviewed", "unknowns": [{"type": "due", "value": "unknown"}], "edited_at": null, "text_edited": false, "action_item_id": null, "deferred_until": null}, {"id": "prop-e5ba4f1741c248e7", "meeting_id": "28233437", "project_id": "proj-bd0a7c7aa9d7", "kind": "decision", "text": "Rollback runbook is rehearsed on the read replica first", "owner_hint": null, "due_hint": null, "owner": null, "due": null, "owner_supplied": null, "due_supplied": null, "source_artifact_id": null, "source_plugin": "decision_capture", "segment_timestamp": null, "speaker_label": null, "model_host": null, "state": "proposed", "original_text": "Rollback runbook is rehearsed on the read replica first", "decision_record_id": null, "rationale": null, "commitment_id": null, "created_at": "2026-10-11T16:31:22.598944+00:00", "decided_at": null, "retry_key": null, "extraction_revision": null, "job_id": null, "job_attempt": null, "extraction_model": null, "span_start": null, "span_end": null, "segment_index": null, "claim_kind": "proposal", "support": "unknown", "support_record": null, "acceptance": "unreviewed", "unknowns": [], "edited_at": null, "text_edited": false, "action_item_id": null, "deferred_until": null}]};
const LOOP_MANIFEST = {"manifest": {"project_id": "proj-bd0a7c7aa9d7", "project_revision": 1, "purpose": "", "prepared_at": "2026-10-11T16:31:22.818503+00:00", "calendar": {"present": false}, "coverage": {"expected": 0, "available": 0, "complete": true}, "sources": [], "omitted": [], "decisions": [{"ref": "decision_record:record-146c8a35e94f4ae8", "text": "Rollback runbook is rehearsed on the read replica first", "lifecycle": "current", "at": "2026-10-11T16:31:22.718849+00:00", "meeting_title": "Architecture review", "kind": "decision"}], "commitments": [{"ref": "commitment:commitment-5426e612f9a84f01", "text": "Draft the rollback runbook", "owner": "Marek", "due_at": "2026-10-13", "kind": "action"}], "not_included": []}};
const LOOP_ROUTE = {"route": {"state": "ready", "token": "READY", "host": "127.0.0.1", "model": "QWEN3 35B", "boundary": "private_network", "reason": "", "repair": "Set up model", "invoke": {"sent": false, "operation_id": "", "outcome": "", "send_phase": "", "host": ""}}};

/* ── HS-200-11 round 2: Prepare pressed, through to its outcomes ───── */

describe("HS-200-11: Prepare pressed — sent, kept, refused and stopped as the hub answers", () => {
  const pid = PREP2_ROOM.project_id;
  const PURPOSE = "Architecture review, cut-over sequencing";
  const prepareKey = `POST /api/projects/${pid}/briefs/prepare`;
  const table = (prepare: Answer): Record<string, Answer> => ({
    [room(pid)]: () => clone(PREP2_ROOM),
    [`GET /api/projects/${pid}/briefs/route`]: () => clone(PREP2_ROUTE),
    [`GET /api/projects/${pid}/briefs/manifest`]: () => clone(PREP2_MANIFEST),
    [`GET /api/projects/${pid}/briefs`]: (_init, url) => (url.includes("lifecycle=kept") && kept ? clone(BRIEFS_KEPT) : { briefs: [] }),
    [prepareKey]: prepare,
    [`POST /api/briefs/${PREPARE_OK.brief.id}/keep`]: () => { kept = true; return clone(KEEP); },
    [`POST /api/projects/${pid}/briefs/stop`]: () => clone(STOP),
  });
  let kept = false;
  const refuse = async (payload: unknown) => {
    const { ApiError } = await import("../../../lib/api");
    return new ApiError(409, String((payload as { error: string }).error), clone(payload));
  };
  async function pressPrepare() {
    render(<WindowHarness scope={`project:${pid}`} />);
    fireEvent.change(within(await screen.findByTestId("room-ask-result")).getByRole("combobox"), { target: { value: "brief" } });
    await screen.findByTestId("prepare-coverage");
    await waitFor(() => expect(screen.getByTestId("prepare-route").getAttribute("data-state")).toBe("ready"));
    fireEvent.change(screen.getByRole("textbox", { name: "Purpose" }), { target: { value: PURPOSE } });
    await waitFor(() => expect((screen.getByTestId("prepare-verb") as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByTestId("prepare-verb"));
  }
  beforeEach(() => { kept = false; });

  // replaces: tests/e2e/_parked/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read
  // (the face's receipt, egress and Keep legs at :754-:771; the claims ledger is the T1 successor's)
  it("a sent and answered request: Brief ready, the receipt names the model on THIS DEVICE, Keep keeps it and the receipt stays", async () => {
    wire(table(() => clone(PREPARE_OK)));
    await pressPrepare();
    expect(calls.find((c) => c.key === prepareKey)?.json).toMatchObject({ purpose: PURPOSE, generator: "model" });
    await screen.findByTestId("prepare-document");
    expect(screen.getByTestId("prepare-head-name").textContent?.trim()).toBe("Brief ready");
    const lifecycle = () => screen.getByTestId("prepare-lifecycle").querySelector(".surface-state-chip")?.getAttribute("aria-label");
    expect(lifecycle()).toBe("DRAFT");
    expect(screen.getByTestId("prepare-footer-egress").textContent?.trim()).toBe("THIS DEVICE");
    const receipt = screen.getByTestId("prepare-footer-receipt").textContent?.trim() ?? "";
    expect(receipt.startsWith("QWEN3 35B")).toBe(true);
    expect(screen.getByTestId("prepare-head").textContent).not.toContain("NOTHING SENT");
    expect(screen.getAllByTestId("prepare-discard")).toHaveLength(1);

    const keep = screen.getByTestId("prepare-keep");
    fireEvent.click(keep);
    await waitFor(() => expect(lifecycle()).toBe("KEPT"));
    expect(screen.getByTestId("prepare-head-name").textContent?.trim()).toBe("Brief ready");
    expect(screen.getByTestId("prepare-keep").getAttribute("aria-disabled")).toBe("true");
    expect(screen.queryByTestId("prepare-discard")).toBeNull();
    expect(screen.getByTestId("prepare-footer-receipt").textContent?.trim()).toBe(receipt);
    fireEvent.click(screen.getByTestId("prepare-keep"));
    expect(calls.filter((c) => c.key.endsWith("/keep"))).toHaveLength(1); // a second press writes nothing
  });

  // replaces: tests/e2e/_parked/test_hs200_preparation_brief_glass.py::test_a_sent_and_answered_request_is_never_reported_as_nothing_sent
  // (the prose leg, :933-:945; the HTTP 500 leg reads NOT ANSWERED by the same refusalReceipt)
  it("P0: a kernel success with a prose answer reads SENT · 127.0.0.1 · NOTHING USABLE RECEIVED, never NOTHING SENT", async () => {
    const error = await refuse(PREPARE_PROSE_409);
    wire(table(() => { throw error; }));
    await pressPrepare();
    const sent = await screen.findByTestId("prepare-sent-token");
    expect(screen.getByTestId("prepare-head").textContent).not.toContain("NOTHING SENT");
    expect(sent.textContent?.trim()).toBe("SENT · 127.0.0.1 · NOTHING USABLE RECEIVED");
    expect(screen.getByTestId("prepare-footer-egress").textContent?.trim()).toBe("THIS DEVICE");
    expect(screen.getByTestId("prepare-footer-receipt").textContent?.trim()).toBe("SENT · 127.0.0.1 · NOTHING USABLE RECEIVED");
    expect(screen.getByTestId("prepare-route").querySelector(".surface-state-chip")?.getAttribute("aria-label")).toBe("OUTPUT UNUSABLE");
    expect(screen.getByTestId("prepare-purpose-kept").textContent?.trim()).toBe("PURPOSE KEPT");
    expect((screen.getByRole("textbox", { name: "Purpose" }) as HTMLTextAreaElement).value).toBe(PURPOSE);
    expect(screen.queryByTestId("prepare-document")).toBeNull();
  });

  // replaces: tests/e2e/_parked/test_hs200_preparation_brief_glass.py::test_stop_leaves_no_orphan_draft (the face half, :1030-:1040)
  it("Stop: the request had left, the face is back on Prepare with his purpose, and no draft is drawn", async () => {
    let answer!: () => void;
    const error = await refuse(PREPARE_STOPPED_409);
    wire(table(() => new Promise((_resolve, reject) => { answer = () => reject(error); })));
    await pressPrepare();
    await screen.findByTestId("prepare-running");
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    await waitFor(() => expect(screen.getByTestId("prepare-posture").getAttribute("data-posture")).toBe("prepare"));
    const stopped = await screen.findByTestId("prepare-stopped");
    expect(stopped.textContent?.trim().startsWith("STOPPED · REQUEST HAD LEFT")).toBe(true);
    const stopCall = calls.find((c) => c.key.endsWith("/briefs/stop"));
    expect(stopCall?.json?.attempt_id).toBe(calls.find((c) => c.key === prepareKey)?.json?.attempt_id);
    await act(async () => { answer(); await Promise.resolve(); });
    expect(screen.queryByTestId("prepare-document")).toBeNull();
    expect(screen.getByTestId("prepare-posture").getAttribute("data-posture")).toBe("prepare");
    expect((screen.getByRole("textbox", { name: "Purpose" }) as HTMLTextAreaElement).value).toBe(PURPOSE);
  });
});

/* ── HS-200-16: the daily loop's dates and record kinds on the face ── */

describe("HS-200-16: a meeting from an earlier day, its decision and its commitment", () => {
  const pid = LOOP_ROOM.project_id;
  const meetingDay = String(LOOP_ROOM.needsYou.items[0].meeting_started_at).slice(5, 10).replace("T", ""); // MM-DD
  const writtenDay = String(LOOP_ROOM.needsYou.items[0].created_at).slice(5, 10);

  // replaces: tests/e2e/_parked/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days
  // (the day-1 proposal-caption fence, :1112-:1133)
  it("the proposal caption dates the row by its MEETING, not by the day the row was written", async () => {
    expect(meetingDay).not.toBe(writtenDay); // the recorded fixture holds two distinct days
    wire({
      [room(pid)]: () => clone(LOOP_ROOM),
      [`GET /api/projects/${pid}/proposals`]: () => clone(LOOP_PROPOSALS),
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    await waitFor(() => expect(screen.getAllByTestId("proposal-caption")).toHaveLength(2));
    for (const caption of screen.getAllByTestId("proposal-caption")) {
      expect(caption.textContent).toContain(`Architecture review ${meetingDay}`);
      expect(caption.textContent).not.toContain(writtenDay);
    }
  });

  // replaces: tests/e2e/_parked/test_phase200_daily_loop.py::test_a_project_carries_work_across_two_working_days
  // (the CARRIED FORWARD fences, :1571 due DATE and :1609 record kinds)
  it("CARRIED FORWARD: the due is a DATE (DUE MM-DD, never a clock); the commitment is CMT, never DEC or CURRENT", async () => {
    wire({
      [room(pid)]: () => clone(LOOP_ROOM),
      [`GET /api/projects/${pid}/proposals`]: () => clone(LOOP_PROPOSALS),
      [`GET /api/projects/${pid}/briefs/route`]: () => clone(LOOP_ROUTE),
      [`GET /api/projects/${pid}/briefs/manifest`]: () => clone(LOOP_MANIFEST),
      [`GET /api/projects/${pid}/briefs`]: () => ({ briefs: [] }),
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    fireEvent.change(within(await screen.findByTestId("room-ask-result")).getByRole("combobox"), { target: { value: "brief" } });
    const carried = await screen.findByTestId("prepare-carried");
    const posture = screen.getByTestId("prepare-posture");
    const captions = Array.from(posture.querySelectorAll(".surface-section-head h3")).map((h) => h.textContent?.trim());
    expect(captions.filter((c) => c?.startsWith("CARRIED FORWARD"))).toEqual(["CARRIED FORWARD 2"]);
    const due = LOOP_MANIFEST.manifest.commitments[0].due_at; // "YYYY-MM-DD"
    const dueTokens = Array.from(carried.querySelectorAll(".surface-token")).map((t) => t.textContent?.trim() ?? "")
      .filter((t) => t.startsWith("DUE"));
    expect(dueTokens).toEqual([`DUE ${due.slice(5)}`]);
    expect(dueTokens.join(" ")).not.toMatch(/\d\d:\d\d/);
    const rows = Array.from(carried.querySelectorAll("li")).map((li) => ({
      emblem: li.querySelector(".prepare-emblem")?.textContent?.trim(),
      text: li.querySelector(".surface-primary")?.textContent?.trim(),
      chips: Array.from(li.querySelectorAll(".surface-state-chip")).map((c) => c.getAttribute("aria-label") || c.textContent?.trim()),
    }));
    const decision = rows.find((r) => r.text === LOOP_MANIFEST.manifest.decisions[0].text)!;
    const commitment = rows.find((r) => r.text === LOOP_MANIFEST.manifest.commitments[0].text)!;
    expect(decision.emblem).toBe("DEC");
    expect(commitment.emblem).toBe("CMT");
    expect(commitment.chips).not.toContain("CURRENT");
  });
});

/* ── The final diet lane: replays of whole recorded Rooms ─────────────
 *
 * Each answer below is the hub's own, recorded by scripts/record_room_wires.py
 * on the browser test's own seed (the room-wires/*.json files). `replay`
 * answers a GET by its exact path (query included) and a press by
 * `METHOD path`; a read the recording does not hold is a failed read and is
 * listed in `misses`, which every test asserts empty: the face asked the
 * hub nothing the recording did not answer. */

type Gets = Record<string, unknown>;
type Press = (init: Init) => unknown;
const misses: string[] = [];
let hubGets: Gets = {};

function hubAnswer(value: unknown): Promise<unknown> {
  if (value && typeof value === "object" && "__status" in (value as Record<string, unknown>)) {
    const { __status, body } = value as { __status: number; body: Record<string, unknown> };
    return Promise.reject(new ApiError(__status, String(body?.message ?? body?.detail ?? `HTTP ${__status}`), body));
  }
  return Promise.resolve(clone(value));
}

function replay(gets: Gets, presses: Record<string, Press> = {}) {
  hubGets = gets;
  misses.length = 0;
  apiFetch.mockImplementation((url: string, init: Init = {}) => {
    const method = init.method ?? "GET";
    calls.push({ key: `${method} ${url.split("?")[0]}`, json: init.json });
    const press = presses[`${method} ${url}`];
    if (press) return Promise.resolve(press(init)).then(hubAnswer);
    const key = method === "GET" ? url : `${method} ${url}`;
    if (key in hubGets) return hubAnswer(hubGets[key]);
    misses.push(`${method} ${url}`);
    return Promise.reject(new ApiError(404, `not recorded: ${method} ${url}`, {}));
  });
}

const chipLabels = (testId: string) =>
  Array.from(document.querySelectorAll(`[data-testid="${testId}"] .surface-state-chip`)).map((el) => el.getAttribute("aria-label") ?? "");
const tokenTexts = (testId: string) =>
  Array.from(document.querySelectorAll(`[data-testid="${testId}"]`)).map((el) => (el.textContent ?? "").trim());

async function openFirstUpdate() {
  fireEvent.click(await screen.findByTestId("updates-verb"));
  await screen.findByTestId("update-posture");
  const items = await screen.findAllByTestId("update-list-item");
  fireEvent.click(items[0]);
  return screen.findByTestId("update-editor");
}

describe("HS-173-02: the Update editor names who drafted it", () => {
  // replaces: tests/e2e/test_hs173_update_glass.py::test_model_draft_footer_and_claims_1440
  // replaces: tests/e2e/test_hs173_update_glass.py::test_model_draft_footer_393 (the same DOM fact; the rig's 393 leg asserted the model token only)
  it("a model draft: the footer names QWEN3 32B Q6 and the LAN host; 1 UNSUPPORTED, 3 LINKED · MIGRATED; PR #612, KAN-7, MTG 09-05", async () => {
    const { pid, gets } = U173.model;
    replay(gets);
    render(<WindowHarness scope={`project:${pid}`} />);
    await openFirstUpdate();
    expect(screen.getByTestId("update-footer-model").textContent).toContain("QWEN3 32B Q6");
    const host = Array.from(document.querySelectorAll(".gadget-chip-egress")).find((c) => (c.textContent ?? "").includes("192.168.1.43"));
    expect(host?.textContent).toContain("LAN");
    const support = chipLabels("update-claim-support");
    expect(support.filter((s) => s === "UNSUPPORTED")).toHaveLength(1);
    expect(support.filter((s) => s === "LINKED · MIGRATED")).toHaveLength(3);
    expect(screen.queryAllByTestId("update-claim-unverified")).toHaveLength(0);
    const refs = tokenTexts("update-claim-ref");
    for (const label of ["PR #612", "KAN-7", "MTG 09-05"]) expect(refs).toContain(label);
    expect(misses).toEqual([]);
  });

  // replaces: tests/e2e/test_hs173_update_glass.py::test_deterministic_no_model_footer
  it("a deterministic draft: no model token, no UNVERIFIED badge, its one citation reads LINKED · MIGRATED", async () => {
    const { pid, gets } = U173.deterministic;
    replay(gets);
    render(<WindowHarness scope={`project:${pid}`} />);
    await openFirstUpdate();
    expect(screen.queryByTestId("update-footer-model")).toBeNull();
    expect(screen.queryAllByTestId("update-claim-unverified")).toHaveLength(0);
    expect(chipLabels("update-claim-support")).toEqual(["LINKED · MIGRATED"]);
    expect(misses).toEqual([]);
  });
});

describe("HS-200-06: the three claim axes on the Update face", () => {
  // replaces: tests/e2e/test_hs200_claim_support_glass.py::test_real_draft_supported_then_edited_1440 (the face;
  // the draft and the edit are the hub's: tests/integration/test_phase200_claim_support.py::TestAxesOnTheWire::test_drafted_claims_carry_all_three_axes
  // and ::test_edit_through_the_wire_invalidates_support)
  it("a real draft edited in one sentence: every claim OBSERVATION; that sentence LINKED · EDITED, the rest SUPPORTED; his words ACCEPTED", async () => {
    const { pid, gets, drafted } = C200.real;
    const claims = JSON.parse(drafted.claims_json) as Array<{ text: string }>;
    const edited = claims.filter((c) => c.text === claims[0].text).length;
    replay(gets);
    render(<WindowHarness scope={`project:${pid}`} />);
    await openFirstUpdate();
    const kinds = tokenTexts("update-claim-kind");
    expect(kinds.length).toBeGreaterThan(0);
    expect(new Set(kinds)).toEqual(new Set(["OBSERVATION"]));
    const support = chipLabels("update-claim-support");
    expect(support.filter((s) => s === "LINKED · EDITED")).toHaveLength(edited);
    expect(support.filter((s) => s === "SUPPORTED")).toHaveLength(claims.length - edited);
    expect(chipLabels("update-claim-acceptance")).toEqual([...Array(claims.length).fill("UNREVIEWED"), "ACCEPTED"]);
    expect(misses).toEqual([]);
  });

  // replaces: tests/e2e/test_hs200_claim_support_glass.py::test_mixed_claims_axes_1440
  // replaces: tests/e2e/test_hs200_claim_support_glass.py::test_mixed_claims_axes_393 (the same DOM asserts at 393)
  it("every state the service serves: kinds, support, acceptance and the typed unknowns, in order", async () => {
    const { pid, gets } = C200.mixed;
    replay(gets);
    render(<WindowHarness scope={`project:${pid}`} />);
    await openFirstUpdate();
    expect(tokenTexts("update-claim-kind")).toEqual(["OBSERVATION", "INFERENCE", "INFERENCE", "DECISION", "INFERENCE"]);
    expect(chipLabels("update-claim-support")).toEqual(["SUPPORTED", "LINKED", "UNSUPPORTED", "SUPPORTED", "LINKED · MIGRATED"]);
    expect(chipLabels("update-claim-acceptance")).toEqual(["UNREVIEWED", "UNREVIEWED", "UNREVIEWED", "ACCEPTED", "UNREVIEWED"]);
    expect(chipLabels("update-claim-unknown")).toEqual([
      "DEADLINE 2026-12-31 · NO SOURCE", "NAME Priya · NO SOURCE", "NUMBER 95% · NO SOURCE",
    ]);
    expect(misses).toEqual([]);
  });
});

describe("PHILO-10-02: a nudge whose answer never came back is never offered again", () => {
  // replaces: tests/e2e/test_philo10_02_nudge_unknown_glass.py::test_the_unknown_nudge_is_never_offered_again_1440
  // replaces: tests/e2e/test_philo10_02_nudge_unknown_glass.py::test_the_unknown_nudge_is_never_offered_again_393 (the same DOM asserts at 393)
  // The hub half (one gh call, the step persisted unknown, a second Send refused):
  // tests/unit/test_philo10_cli_channels.py::test_f4_a_nudge_whose_gh_times_out_is_unknown_and_never_offered_again
  const { pid, step, before, send, after } = N10;
  const sendKey = `POST /api/nudges/${step}/send`;
  const sends = () => calls.filter((c) => c.key === sendKey);
  function unknownAndNoSend() {
    const row = screen.getByTestId("nudge-unknown-row");
    const text = (row.textContent ?? "").toUpperCase();
    expect(text).toContain("RESULT UNKNOWN");
    expect(text).toContain("CHECK #612");
    expect(text).toContain("GITHUB.COM");
    expect(screen.queryByTestId("nudge-send")).toBeNull();
  }

  it("Send, close and reopen while in flight, the answer lands UNKNOWN; a remount and a reload read the persisted step: no Send", async () => {
    let land!: () => void;
    const inFlight = new Promise<void>((resolve) => { land = resolve; });
    replay(before, {
      [sendKey]: () => inFlight.then(() => { hubGets = after; return send.answer; }),
    });
    const view = render(<WindowHarness scope={`project:${pid}`} />);
    fireEvent.click(await screen.findByTestId("nudge-verb"));
    fireEvent.click(await screen.findByTestId("nudge-send"));
    fireEvent.click(screen.getByTestId("nudge-verb")); // close
    fireEvent.click(screen.getByTestId("nudge-verb")); // reopen: busy, no second post
    const again = screen.queryByTestId("nudge-send");
    if (again) fireEvent.click(again);
    expect(sends()).toHaveLength(1);
    await act(async () => { land(); await inFlight; });
    await screen.findByTestId("nudge-unknown-row");
    unknownAndNoSend();
    expect(rawButtons(screen.getByTestId("room-body"))).toEqual([]);
    fireEvent.click(screen.getByTestId("nudge-verb")); // close
    fireEvent.click(screen.getByTestId("nudge-verb")); // reopen: a remount of the card
    unknownAndNoSend();
    view.unmount();

    // The reload: a fresh Room over the hub's reads after the send.
    replay(after);
    render(<WindowHarness scope={`project:${pid}`} />);
    fireEvent.click(await screen.findByTestId("nudge-verb"));
    await screen.findByTestId("nudge-unknown-row");
    unknownAndNoSend();
    expect(sends()).toHaveLength(1);
    expect(misses).toEqual([]);
  });
});

describe("HS-175-04: the meeting source row in SOURCES", () => {
  const { pid, before, pause, paused, resume, resumed, empty, watch } = H175;
  const meetingRow = () => screen.getByTestId("source-meeting-row");
  const verb = () => within(meetingRow()).getByTestId("source-meeting-verb");
  const zeroCounters = (root: Element) => (root.textContent ?? "").match(/\b0\s+(?:NEEDS|SOURCES|MEETINGS|DECISIONS|items)/g) ?? [];

  // replaces: tests/e2e/test_hs175_room_glass.py::TestRoomMeetingSourceGlass::test_meeting_source_1440
  // replaces: tests/e2e/test_hs175_room_glass.py::TestRoomMeetingSourceGlass::test_meeting_source_393 (the same DOM asserts at 393)
  it("MTG, MEETINGS, the hub's NEXT token, CHECKED, no egress; Pause gives PAUSED + Resume, Resume gives Pause back", async () => {
    const pauseKey = `POST /api/watches/${watch}/pause`;
    const resumeKey = `POST /api/watches/${watch}/resume`;
    replay(before, {
      [pauseKey]: () => { hubGets = paused; return pause.answer; },
      [resumeKey]: () => { hubGets = resumed; return resume.answer; },
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    await screen.findByTestId("source-meeting-row");
    expect(screen.getAllByTestId("source-meeting-row")).toHaveLength(1);
    expect(meetingRow().querySelector(".surface-ledger-lead")?.textContent?.trim()).toBe("MTG");
    expect(within(meetingRow()).getByTestId("source-scope").textContent?.trim()).toBe("MEETINGS");
    const wired = ((before as Record<string, unknown>)[`/api/projects/${pid}/room`] as { sources: { items: Array<{ provider: string; tokens: string[] }> } })
      .sources.items.find((s) => s.provider === "meeting")!;
    expect(wired.tokens.some((t) => t.startsWith("NEXT "))).toBe(true);
    const tokens = within(meetingRow()).getAllByTestId("source-meeting-token").map((t) => t.textContent?.trim());
    expect(tokens).toEqual(wired.tokens);
    // The CHECKED chip is on the row's second line (a sibling of the testid line, inside its li).
    expect(screen.getAllByTestId("source-meeting-checked")[0].textContent).toMatch(/CHECKED|NEVER/);
    expect(meetingRow().querySelectorAll(".surface-egress-chip, [data-scope]")).toHaveLength(0);
    const sources = Array.from(document.querySelectorAll(".surface-section-head, .surface-section-label"))
      .map((s) => (s.textContent ?? "").trim()).find((t) => t.startsWith("SOURCES"));
    expect(Number(/SOURCES\s+(\d+)/.exec(sources ?? "")?.[1] ?? 0)).toBeGreaterThanOrEqual(2);

    expect(verb().textContent).toBe("Pause");
    fireEvent.click(verb());
    await waitFor(() => expect(screen.getAllByTestId("source-paused")[0].textContent).toContain("PAUSED"));
    expect(verb().textContent).toBe("Resume");
    fireEvent.click(verb());
    await waitFor(() => expect(verb().textContent).toBe("Pause"));
    expect(screen.queryAllByTestId("source-paused")).toHaveLength(0);
    expect(rawButtons(screen.getByTestId("room-body"))).toEqual([]);
    expect(zeroCounters(screen.getByTestId("room-body"))).toEqual([]);
    expect(misses).toEqual([]);
  });

  // replaces: tests/e2e/test_hs175_room_glass.py::TestRoomMeetingSourceGlass::test_no_meetings_no_row
  it("a Room with no linked meeting draws no meeting row and no zero counter", async () => {
    replay(empty.gets);
    render(<WindowHarness scope={`project:${empty.pid}`} />);
    await screen.findByTestId("room-body");
    await waitFor(() => expect(calls.some((c) => c.key === `POST /api/projects/${empty.pid}/room/read`)).toBe(true));
    expect(screen.queryByTestId("source-meeting-row")).toBeNull();
    expect(zeroCounters(screen.getByTestId("room-body"))).toEqual([]);
    expect(misses).toEqual([]);
  });
});

describe("PHILO-17 sources: Add a repository in the Room", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_add_a_repository_and_it_stays_after_reload (the face; the hub
  //   half: tests/integration/test_desk_project_room.py::test_a_repository_added_in_the_room_stays_and_the_same_one_again_is_already_watched)
  const { pid, before, count, add, after, again } = S17;
  const doorKey = "POST /api/projects/door";
  const posts = () => calls.filter((c) => c.key === doorKey);

  async function pickAndAdd() {
    const well = await screen.findByTestId("room-add-sources");
    fireEvent.click(await within(well).findByTestId("door-trigger-github"));
    fireEvent.click(await within(well).findByTestId("door-pick-acme/app"));
    const addButton = within(well).getByTestId("room-add-sources-add") as HTMLButtonElement;
    await waitFor(() => expect(addButton.disabled).toBe(false));
    fireEvent.click(addButton);
    return well;
  }

  it("pick acme/app, Add: the well closes and SOURCES holds acme/app; the same again says Already watched", async () => {
    let added = 0;
    replay(before, {
      "POST /api/projects/door/count": () => count.answer,
      [doorKey]: () => {
        added += 1;
        if (added === 1) { hubGets = after; return add.answer; }
        return again.answer;
      },
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    await pickAndAdd();
    await waitFor(() => expect(screen.queryByTestId("room-add-sources")).toBeNull());
    expect(posts()[0].json).toEqual(add.request);
    expect(calls.find((c) => c.key === "POST /api/projects/door/count")?.json).toEqual(count.request);
    await waitFor(() => expect(screen.getAllByTestId("source-scope").map((e) => e.textContent?.trim())).toContain("acme/app"));

    fireEvent.click(screen.getByTestId("room-add-source"));
    const well = await pickAndAdd();
    await within(well).findByText("Already watched");
    expect(posts()).toHaveLength(2);
    expect(screen.getAllByTestId("source-scope").filter((e) => e.textContent?.trim() === "acme/app")).toHaveLength(1);
    expect(misses).toEqual([]);
  });
});

describe("PHILO-17 sources: a parked meeting leaves FILES on the hub's own frame", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_park_from_files_leaves_its_receipt_and_restore_in_the_room
  //   (the leg the earlier successor left to the browser: the row leaving FILES and coming back; the hub
  //   half is tests/integration/test_desk_project_room.py::test_park_from_files_parks_the_meeting_and_restore_brings_it_back_to_the_room)
  const { pid, before, park, park_frames, parked, restore, restore_frames, restored } = F17;
  const deliver = (frames: Array<{ type: string; data: unknown }>) =>
    act(() => { for (const f of frames) for (const h of bus.handlers.get(f.type) ?? []) h(f); });
  const row = () => screen.getByTestId("room-files").querySelector("[data-object-id='meeting:m-lone']");

  it("Park: PARKED · Vendor call, and the hub's desk_changed takes the row out; Restore and its frame bring it back", async () => {
    const { DrawerInfoWindow } = await import("../../../desk/drawer/InfoWindow");
    const { useDrawers } = await import("../../../desk/drawer/store");
    useDesk.setState({ refresh: vi.fn(() => Promise.resolve()) } as never);
    replay(before, {
      "DELETE /api/meetings/m-lone": () => { hubGets = parked; return park.answer; },
      "POST /api/meetings/m-lone/restore": () => { hubGets = restored; return restore.answer; },
    });
    function Desk() {
      const infos = useDrawers((s) => s.infos);
      return (
        <>
          <WindowHarness scope={`project:${pid}`} />
          {infos.map((info) => <DrawerInfoWindow key={info.ref} info={info} />)}
        </>
      );
    }
    render(<Desk />);
    const files = await screen.findByTestId("room-files");
    fireEvent.click(await within(files).findByRole("button", { name: /^Vendor call,/ }));
    fireEvent.click(within(files).getByTestId("room-files-info"));
    fireEvent.click(await screen.findByRole("button", { name: "Park" }), { detail: 1 });
    const receipt = await within(screen.getByTestId("room-files")).findByTestId("room-files-park-receipt");
    expect(receipt.querySelector("[role=status]")?.textContent).toBe("PARKED · Vendor call");
    expect(row()).not.toBeNull(); // nothing re-read yet: the hub's frame has not come
    deliver(park_frames);
    await waitFor(() => expect(row()).toBeNull(), { timeout: 3000 });
    expect(screen.getByTestId("room-files-park-receipt").querySelector("[role=status]")?.textContent).toBe("PARKED · Vendor call");

    fireEvent.click(within(screen.getByTestId("room-files-park-receipt")).getByRole("button", { name: "Restore" }));
    await waitFor(() => expect(screen.getByTestId("room-files-park-receipt").querySelector("[role=status]")?.textContent)
      .toMatch(/RESTORED/));
    deliver(restore_frames);
    await waitFor(() => expect(row()).not.toBeNull(), { timeout: 3000 });
    expect(misses).toEqual([]);
    useDrawers.getState().setReceipt(pid, null);
  });
});
