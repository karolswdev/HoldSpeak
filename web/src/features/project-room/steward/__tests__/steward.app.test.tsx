// Watch sources (the Steward posture), app-level: the real Project Room, the
// real Steward controller and posture, the real Desk store. Only apiFetch is
// mocked (plus the jsdom stand-in for the rich editor and a spy on the shell's
// opener). The steward answers below are VERBATIM captures from a real hub
// (2026-10-11: MeetingWebServer over an isolated database, the e2e seed: an
// overdue high-severity risk and the e2e policy; then a dead watch source).
// The room read is the shared fixture of StewardPosture.test.tsx.
//
// replaces: tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup (the face; the
//   Door-item effect and the same-watermark dedup are backend facts:
//   tests/unit/test_steward_effects.py::TestSTW005FaultInjection::test_door_item_dedup_same_watermark and
//   ::TestFollowThroughLaw::test_cross_watermark_no_second_door_item)
// replaces: tests/e2e/test_hs163_steward_glass.py::test_stop_mid_run (Stop on the Run-once path; the
//   interrupted landing is tests/unit/test_steward_engine.py::TestStopBetweenPhases::test_stop_mid_run_leads_to_interrupted and
//   tests/integration/test_steward_routes.py::TestStopMidRun::test_stop_lands_interrupted)
// replaces: tests/e2e/test_hs163_steward_glass.py::test_degraded_partial_coverage
// replaces: tests/e2e/test_hs163_steward_glass.py::test_run_history_and_policy

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TitleSlotContext } from "../../../../desk/surface/title";
import { WingSlotContext } from "../../../../desk/surface/wings";
import { useDesk } from "../../../../desk/store";
import { EMPTY_ITEMS } from "../../../../desk/api";
import { ProjectRoomCore } from "../../ProjectRoomCore";
import { ApiError } from "../../../../lib/api";
// The final diet lane's recorded wires (scripts/record_room_wires.py: the real
// hub through TestClient on each browser test's own seed; nothing typed).
import GATE from "./room-steward-wires/hs164_gate.json";
import CIRCUIT from "./room-steward-wires/hs164_circuit.json";
import P173 from "./room-steward-wires/policy173.json";

vi.mock("../../../../desk/components/DeskEditor", () => ({
  DeskEditor: ({ value, onChange, ariaLabel }: { value: string; onChange: (v: string) => void; ariaLabel?: string }) => (
    <textarea aria-label={ariaLabel || "Body"} value={value} onChange={(e) => onChange(e.target.value)} />
  ),
}));

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

// ── The real hub's answers, verbatim (captured 2026-10-11; see the header) ──
const POLICY_GET = {"policy": {"id": "pstpol_181d298b38b74b3b8432bbca4d38ae4a", "project_id": "proj-fa9cdfd90771", "eligible_effect_kinds": ["refresh_sources", "create_proposals", "apply_proposal_effects", "draft_update", "create_door_item"], "yolo_flags": {}, "max_retries": 3, "max_actions_per_run": 10, "cooldown_seconds": 0, "bounds": {}, "enabled": true, "unattended_enabled": false, "created_at": "2026-10-11T15:37:50+00:00", "updated_at": "2026-10-11T15:37:50+00:00"}};
const START_OK = {"success": true, "run_id": "pstrun_bb17e88c80ca52759d1cfcc96d035a87", "operation_id": "op_30a4541cef584ed4a9bb1a3e922a7940", "state": "claimed", "receipt": null};
const START_DEAD = {"success": true, "run_id": "pstrun_cfe2261116f856fcb0447232546c1660", "operation_id": "op_808d6f0a5fb04f3399a15e44cf7cbf30", "state": "claimed", "receipt": null};
const DETAIL_OK: { run: Record<string, unknown>; steps: Record<string, unknown>[]; [key: string]: unknown } = {"run": {"id": "pstrun_bb17e88c80ca52759d1cfcc96d035a87", "project_id": "proj-fa9cdfd90771", "policy_id": "pstpol_181d298b38b74b3b8432bbca4d38ae4a", "state": "completed", "phase": "record", "requested_by": "principal:owner-session", "watermark": "", "summary": {"outcome": "completed", "phases_completed": ["observe", "compare", "propose", "act", "verify", "record"], "phase_results": {"observe": {"coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}}}, "compare": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "propose": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "act": {"actions_taken": 5, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_323387aee30140e695ae58c0b0619716", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_523ea518c7304cb9a92dcc4b7bab668e", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_6eea9f0ea6f84ff6ac3a59193ef1777e", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_a95598a7c4c6471c856f483ff968b699", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_774d0c8cafff4067b576bbe1e83edbd3", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "applied", "step_id": "pststep_198d28153d3744b8a067859f77eb6bba", "attempt": 1, "result": {"effect": "create_door_item", "door_item_id": "ai_946cb59000814ff5a2879c907355080f", "source_item_id": "pitem_0ac6bbd7ce7746dd8b311278d499eda0", "source_item_type": "risk", "source_severity": "high"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}]}, "verify": {"source_count": 4, "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "actions_taken": 5, "verified_effects": 5, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_323387aee30140e695ae58c0b0619716", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_523ea518c7304cb9a92dcc4b7bab668e", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_6eea9f0ea6f84ff6ac3a59193ef1777e", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_a95598a7c4c6471c856f483ff968b699", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_774d0c8cafff4067b576bbe1e83edbd3", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "applied", "step_id": "pststep_198d28153d3744b8a067859f77eb6bba", "attempt": 1, "result": {"effect": "create_door_item", "door_item_id": "ai_946cb59000814ff5a2879c907355080f", "source_item_id": "pitem_0ac6bbd7ce7746dd8b311278d499eda0", "source_item_type": "risk", "source_severity": "high"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}], "has_real_effects": true}, "record": {"event_recorded": true}}}, "created_at": "2026-10-11T15:37:50+00:00", "updated_at": "2026-10-11T15:37:50+00:00", "started_at": "2026-10-11T15:37:50+00:00", "completed_at": "2026-10-11T15:37:50+00:00", "stop_requested_at": null}, "steps": [{"id": "pststep_49505182cb3744c286c082bff42dda7f", "phase": "observe", "seq": 0, "state": "completed", "effect_kind": "phase:observe", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:observe", "expected": {}, "observed": {"coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}}}, "receipt": {}, "error": null}, {"id": "pststep_00aefcaab4c24f8b996b282dbedcb25f", "phase": "compare", "seq": 1, "state": "completed", "effect_kind": "phase:compare", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:compare", "expected": {}, "observed": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "receipt": {}, "error": null}, {"id": "pststep_207d517dbeb34a0f90216c7b10114bd0", "phase": "propose", "seq": 2, "state": "completed", "effect_kind": "phase:propose", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:propose", "expected": {}, "observed": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "receipt": {}, "error": null}, {"id": "pststep_61c428c511544752bf896e5a44abe552", "phase": "act", "seq": 3, "state": "completed", "effect_kind": "phase:act", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:act", "expected": {}, "observed": {"actions_taken": 5, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_323387aee30140e695ae58c0b0619716", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_523ea518c7304cb9a92dcc4b7bab668e", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_6eea9f0ea6f84ff6ac3a59193ef1777e", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_a95598a7c4c6471c856f483ff968b699", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_774d0c8cafff4067b576bbe1e83edbd3", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "applied", "step_id": "pststep_198d28153d3744b8a067859f77eb6bba", "attempt": 1, "result": {"effect": "create_door_item", "door_item_id": "ai_946cb59000814ff5a2879c907355080f", "source_item_id": "pitem_0ac6bbd7ce7746dd8b311278d499eda0", "source_item_type": "risk", "source_severity": "high"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}]}, "receipt": {}, "error": null}, {"id": "pststep_323387aee30140e695ae58c0b0619716", "phase": "act", "seq": 4, "state": "completed", "effect_kind": "refresh_sources", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:refresh_sources", "expected": {"effect": "refresh_sources", "project_id": "proj-fa9cdfd90771"}, "observed": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}}, "partial": false}, "receipt": {"effect_kind": "refresh_sources", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_523ea518c7304cb9a92dcc4b7bab668e", "phase": "act", "seq": 5, "state": "completed", "effect_kind": "create_proposals", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:create_proposals", "expected": {"effect": "create_proposals", "project_id": "proj-fa9cdfd90771", "prior_review_id": "prev_a1c94a138d564e3aabad21e8db061eca"}, "observed": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}, "receipt": {"effect_kind": "create_proposals", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_6eea9f0ea6f84ff6ac3a59193ef1777e", "phase": "act", "seq": 6, "state": "completed", "effect_kind": "apply_proposal_effects", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:apply_proposal_effects", "expected": {"effect": "apply_proposal_effects", "proposal_count": 0}, "observed": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}, "receipt": {"effect_kind": "apply_proposal_effects", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_a95598a7c4c6471c856f483ff968b699", "phase": "act", "seq": 7, "state": "completed", "effect_kind": "draft_update", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:draft_update", "expected": {"effect": "draft_update", "project_id": "proj-fa9cdfd90771"}, "observed": {"effect": "draft_update", "update_id": "pupd_774d0c8cafff4067b576bbe1e83edbd3", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}, "receipt": {"effect_kind": "draft_update", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_198d28153d3744b8a067859f77eb6bba", "phase": "act", "seq": 8, "state": "completed", "effect_kind": "create_door_item", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:create_door_item", "expected": {"effect": "create_door_item", "project_id": "proj-fa9cdfd90771"}, "observed": {"effect": "create_door_item", "door_item_id": "ai_946cb59000814ff5a2879c907355080f", "source_item_id": "pitem_0ac6bbd7ce7746dd8b311278d499eda0", "source_item_type": "risk", "source_severity": "high"}, "receipt": {"effect_kind": "create_door_item", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_82c26a8c77334259b403433e6623c32f", "phase": "verify", "seq": 9, "state": "completed", "effect_kind": "phase:verify", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:verify", "expected": {}, "observed": {"source_count": 4, "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "actions_taken": 5, "verified_effects": 5, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_323387aee30140e695ae58c0b0619716", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_523ea518c7304cb9a92dcc4b7bab668e", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_6eea9f0ea6f84ff6ac3a59193ef1777e", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_a95598a7c4c6471c856f483ff968b699", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_774d0c8cafff4067b576bbe1e83edbd3", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "applied", "step_id": "pststep_198d28153d3744b8a067859f77eb6bba", "attempt": 1, "result": {"effect": "create_door_item", "door_item_id": "ai_946cb59000814ff5a2879c907355080f", "source_item_id": "pitem_0ac6bbd7ce7746dd8b311278d499eda0", "source_item_type": "risk", "source_severity": "high"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}], "has_real_effects": true}, "receipt": {}, "error": null}, {"id": "pststep_6b8ac0f8ba53482b996f27db676f344b", "phase": "record", "seq": 10, "state": "completed", "effect_kind": "phase:record", "idempotency_key": "pstrun_bb17e88c80ca52759d1cfcc96d035a87:record", "expected": {}, "observed": {"event_recorded": true}, "receipt": {}, "error": null}], "operation_id": "op_30a4541cef584ed4a9bb1a3e922a7940", "receipt": {"receipt_id": "rcpt_bb6eee5657f4453d8c3e4430e07b6cce", "operation_id": "op_30a4541cef584ed4a9bb1a3e922a7940", "state": "succeeded", "outcome": "completed", "result_ref": "steward_run:pstrun_bb17e88c80ca52759d1cfcc96d035a87", "created_at": 1791733070.75202, "actor_kind": "owner", "actor_identity": "owner-session", "delegator_kind": "", "delegator_identity": "", "authority_basis": "authenticated_principal+declared_capability+hard_prerequisites+interruption_policy", "target_ref": "project:proj-fa9cdfd90771"}};
const DETAIL_DEAD: { run: Record<string, unknown>; steps: Record<string, unknown>[]; [key: string]: unknown } = {"run": {"id": "pstrun_cfe2261116f856fcb0447232546c1660", "project_id": "proj-fa9cdfd90771", "policy_id": "pstpol_181d298b38b74b3b8432bbca4d38ae4a", "state": "completed", "phase": "record", "requested_by": "principal:owner-session", "watermark": "", "summary": {"outcome": "completed", "phases_completed": ["observe", "compare", "propose", "act", "verify", "record"], "phase_results": {"observe": {"coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}, "psrc_cw_missing_glass_001": {"state": "failed", "error": {"code": "watch_not_found", "message": "Watch cw_missing_glass_001 not found"}}}}, "compare": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "propose": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "act": {"actions_taken": 4, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_225a7456706e475781489de704ab4ad5", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}, "psrc_cw_missing_glass_001": {"state": "failed", "error": {"code": "watch_not_found", "message": "Watch cw_missing_glass_001 not found"}}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_f6e531ca2bbd4d9bb334c611f20c73c9", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_69079c8e66b94693a688284a0a5b8a61", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_6e3dcf140a934c70a5d42b02f2153928", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_152fae15a04c4f5d902abaf3b9b08cb6", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "skipped", "step_id": "pststep_f2fc4ab4fe814c1a97aefe004846c969", "attempt": 1, "result": {"effect": "create_door_item", "skipped": true, "reason": "no_eligible_items"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}]}, "verify": {"source_count": 5, "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "actions_taken": 4, "verified_effects": 4, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_225a7456706e475781489de704ab4ad5", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}, "psrc_cw_missing_glass_001": {"state": "failed", "error": {"code": "watch_not_found", "message": "Watch cw_missing_glass_001 not found"}}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_f6e531ca2bbd4d9bb334c611f20c73c9", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_69079c8e66b94693a688284a0a5b8a61", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_6e3dcf140a934c70a5d42b02f2153928", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_152fae15a04c4f5d902abaf3b9b08cb6", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "skipped", "step_id": "pststep_f2fc4ab4fe814c1a97aefe004846c969", "attempt": 1, "result": {"effect": "create_door_item", "skipped": true, "reason": "no_eligible_items"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}], "has_real_effects": true}, "record": {"event_recorded": true}}}, "created_at": "2026-10-11T15:37:50+00:00", "updated_at": "2026-10-11T15:37:50+00:00", "started_at": "2026-10-11T15:37:50+00:00", "completed_at": "2026-10-11T15:37:50+00:00", "stop_requested_at": null}, "steps": [{"id": "pststep_434cd468bb1c4c84ba7bbccaeeba9e06", "phase": "observe", "seq": 0, "state": "completed", "effect_kind": "phase:observe", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:observe", "expected": {}, "observed": {"coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}, "psrc_cw_missing_glass_001": {"state": "failed", "error": {"code": "watch_not_found", "message": "Watch cw_missing_glass_001 not found"}}}}, "receipt": {}, "error": null}, {"id": "pststep_1e0a79f97471470c925a19643f012161", "phase": "compare", "seq": 1, "state": "completed", "effect_kind": "phase:compare", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:compare", "expected": {}, "observed": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "receipt": {}, "error": null}, {"id": "pststep_385123481f6d4f4aa441f113798d99c4", "phase": "propose", "seq": 2, "state": "completed", "effect_kind": "phase:propose", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:propose", "expected": {}, "observed": {"review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "proposals": []}, "receipt": {}, "error": null}, {"id": "pststep_1aadd01291884bb7bf9e93de79852386", "phase": "act", "seq": 3, "state": "completed", "effect_kind": "phase:act", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:act", "expected": {}, "observed": {"actions_taken": 4, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_225a7456706e475781489de704ab4ad5", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}, "psrc_cw_missing_glass_001": {"state": "failed", "error": {"code": "watch_not_found", "message": "Watch cw_missing_glass_001 not found"}}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_f6e531ca2bbd4d9bb334c611f20c73c9", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_69079c8e66b94693a688284a0a5b8a61", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_6e3dcf140a934c70a5d42b02f2153928", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_152fae15a04c4f5d902abaf3b9b08cb6", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "skipped", "step_id": "pststep_f2fc4ab4fe814c1a97aefe004846c969", "attempt": 1, "result": {"effect": "create_door_item", "skipped": true, "reason": "no_eligible_items"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}]}, "receipt": {}, "error": null}, {"id": "pststep_225a7456706e475781489de704ab4ad5", "phase": "act", "seq": 4, "state": "completed", "effect_kind": "refresh_sources", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:refresh_sources", "expected": {"effect": "refresh_sources", "project_id": "proj-fa9cdfd90771"}, "observed": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}, "psrc_cw_missing_glass_001": {"state": "failed", "error": {"code": "watch_not_found", "message": "Watch cw_missing_glass_001 not found"}}}, "partial": false}, "receipt": {"effect_kind": "refresh_sources", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_f6e531ca2bbd4d9bb334c611f20c73c9", "phase": "act", "seq": 5, "state": "completed", "effect_kind": "create_proposals", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:create_proposals", "expected": {"effect": "create_proposals", "project_id": "proj-fa9cdfd90771", "prior_review_id": "prev_a1c94a138d564e3aabad21e8db061eca"}, "observed": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}, "receipt": {"effect_kind": "create_proposals", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_69079c8e66b94693a688284a0a5b8a61", "phase": "act", "seq": 6, "state": "completed", "effect_kind": "apply_proposal_effects", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:apply_proposal_effects", "expected": {"effect": "apply_proposal_effects", "proposal_count": 0}, "observed": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}, "receipt": {"effect_kind": "apply_proposal_effects", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_6e3dcf140a934c70a5d42b02f2153928", "phase": "act", "seq": 7, "state": "completed", "effect_kind": "draft_update", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:draft_update", "expected": {"effect": "draft_update", "project_id": "proj-fa9cdfd90771"}, "observed": {"effect": "draft_update", "update_id": "pupd_152fae15a04c4f5d902abaf3b9b08cb6", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}, "receipt": {"effect_kind": "draft_update", "outcome": "applied", "attempt": 1}, "error": null}, {"id": "pststep_f2fc4ab4fe814c1a97aefe004846c969", "phase": "act", "seq": 8, "state": "completed", "effect_kind": "create_door_item", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:create_door_item", "expected": {"effect": "create_door_item", "project_id": "proj-fa9cdfd90771"}, "observed": {"effect": "create_door_item", "skipped": true, "reason": "no_eligible_items"}, "receipt": {"effect_kind": "create_door_item", "outcome": "skipped", "attempt": 1}, "error": null}, {"id": "pststep_b5385a8f3e874fe3883afeb2f15e9810", "phase": "verify", "seq": 9, "state": "completed", "effect_kind": "phase:verify", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:verify", "expected": {}, "observed": {"source_count": 5, "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0, "actions_taken": 4, "verified_effects": 4, "effect_receipts": [{"effect_kind": "refresh_sources", "outcome": "applied", "step_id": "pststep_225a7456706e475781489de704ab4ad5", "attempt": 1, "result": {"effect": "refresh_sources", "coverage": {"native:meetings": {"state": "ok", "inserted": 0, "no_op": 0}, "native:resources": {"state": "ok", "inserted": 0, "no_op": 0}, "native:decisions": {"state": "ok", "inserted": 0, "no_op": 0}, "native:followthrough": {"state": "ok", "inserted": 0, "no_op": 0}, "psrc_cw_missing_glass_001": {"state": "failed", "error": {"code": "watch_not_found", "message": "Watch cw_missing_glass_001 not found"}}}, "partial": false}}, {"effect_kind": "create_proposals", "outcome": "applied", "step_id": "pststep_f6e531ca2bbd4d9bb334c611f20c73c9", "attempt": 1, "result": {"effect": "create_proposals", "review_id": "prev_a1c94a138d564e3aabad21e8db061eca", "proposal_count": 0}}, {"effect_kind": "apply_proposal_effects", "outcome": "applied", "step_id": "pststep_69079c8e66b94693a688284a0a5b8a61", "attempt": 1, "result": {"effect": "apply_proposal_effects", "applied": [], "skipped": []}}, {"effect_kind": "draft_update", "outcome": "applied", "step_id": "pststep_6e3dcf140a934c70a5d42b02f2153928", "attempt": 1, "result": {"effect": "draft_update", "update_id": "pupd_152fae15a04c4f5d902abaf3b9b08cb6", "lifecycle": "draft", "generator": "deterministic", "generator_host": null, "generator_model": null}}, {"effect_kind": "create_door_item", "outcome": "skipped", "step_id": "pststep_f2fc4ab4fe814c1a97aefe004846c969", "attempt": 1, "result": {"effect": "create_door_item", "skipped": true, "reason": "no_eligible_items"}}], "effects_skipped": [{"effect_kind": "github_comment", "reason": "not_in_eligible_effect_kinds"}, {"effect_kind": "prepare_send", "reason": "not_in_eligible_effect_kinds"}], "has_real_effects": true}, "receipt": {}, "error": null}, {"id": "pststep_b9631b6fc01149d7bdb376d840cb2632", "phase": "record", "seq": 10, "state": "completed", "effect_kind": "phase:record", "idempotency_key": "pstrun_cfe2261116f856fcb0447232546c1660:record", "expected": {}, "observed": {"event_recorded": true}, "receipt": {}, "error": null}], "operation_id": "op_808d6f0a5fb04f3399a15e44cf7cbf30", "receipt": {"receipt_id": "rcpt_68c9a186f94448c99fb0576881e37df2", "operation_id": "op_808d6f0a5fb04f3399a15e44cf7cbf30", "state": "succeeded", "outcome": "completed", "result_ref": "steward_run:pstrun_cfe2261116f856fcb0447232546c1660", "created_at": 1791733070.8729868, "actor_kind": "owner", "actor_identity": "owner-session", "delegator_kind": "", "delegator_identity": "", "authority_basis": "authenticated_principal+declared_capability+hard_prerequisites+interruption_policy", "target_ref": "project:proj-fa9cdfd90771"}};

type Json = Record<string, unknown>;
type Detail = { run: Json; steps: Json[] };

const PROJECT = "proj-fa9cdfd90771";
const RAW_ID = /p[a-z]+_[0-9a-f]{16,}/;

/** The room read (the shared fixture of StewardPosture.test.tsx, scoped to this project). */
function roomResponse(): Json {
  return {
    project_id: PROJECT,
    revision: 5,
    observed_at: "2026-10-11T15:37:00",
    nextCheckAt: null,
    project: {
      id: PROJECT, name: "Steward Glass Project", description: "Seeded", is_archived: false, meeting_count: 0,
      created_at: "2026-10-11T15:37:00", updated_at: "2026-10-11T15:37:00", purpose: "", outcome_text: "",
      owner_ref: null, lifecycle: "active", posture: "green", posture_reason: null, start_at: null, target_at: null,
      revision: 5,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 0, latest: null },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    needsYou: { state: "ok", items: [], count: 0 },
    sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
    health: { state: "ok", assessment: "on_track", reason: null, inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false } },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "ok" },
  };
}

/** A run of the capture while it is still running (the poll's first answer). */
function running(detail: Detail): Detail {
  return {
    run: { ...detail.run, state: "running", phase: "observe", summary: {}, completed_at: null },
    steps: [],
  };
}

/** The hub as the face sees it: runs list, start, poll, stop, policy, watches. */
function hub(opts: { runsBefore: Json[]; runsAfter: Json[]; start: Json; polls: Detail[]; stopped?: Detail }) {
  let started = false;
  let stopSent = false;
  let poll = 0;
  apiFetch.mockImplementation((url: string, init?: { method?: string }) => {
    const method = init?.method ?? "GET";
    if (url.includes("/room/read")) return Promise.resolve({ read_at: "2026-10-11T15:37:00" });
    if (url.endsWith("/room")) return Promise.resolve(roomResponse());
    if (/\/api\/projects\/[^/]+\/steward\/runs$/.test(url)) {
      if (method === "POST") {
        started = true;
        return Promise.resolve(opts.start);
      }
      return Promise.resolve({ runs: started ? opts.runsAfter : opts.runsBefore });
    }
    if (url.endsWith("/stop") && method === "POST") {
      stopSent = true;
      return Promise.resolve({ success: true, run_id: opts.start.run_id });
    }
    if (/\/api\/steward\/runs\/[^/]+$/.test(url)) {
      if (stopSent && opts.stopped) return Promise.resolve(opts.stopped);
      const answer = opts.polls[Math.min(poll, opts.polls.length - 1)];
      poll += 1;
      return Promise.resolve(answer);
    }
    if (/\/steward\/policy$/.test(url)) return Promise.resolve(POLICY_GET);
    if (/\/api\/projects\/[^/]+\/watches$/.test(url)) return Promise.resolve({ watches: [] });
    if (url.includes("/meetings")) return Promise.resolve({ meetings: [] });
    if (url.startsWith("/api/decisions")) return Promise.resolve({ decisions: [] });
    if (url.includes("/artifacts")) return Promise.resolve({ artifacts: [] });
    if (url.includes("/since-last-meeting")) return Promise.resolve({ current_meeting: null, since_last_meeting: null });
    return Promise.resolve({});
  });
}

function Room() {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div>{wings}</div>
        <ProjectRoomCore scope={`project:${PROJECT}`} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

async function enterWatchSources(): Promise<HTMLElement> {
  render(<Room />);
  fireEvent.click(await screen.findByTestId("steward-verb"));
  const posture = await screen.findByTestId("steward-posture");
  await waitFor(() => expect(posture.getAttribute("data-phase")).toBe("list"));
  return posture;
}

function runButton(): HTMLButtonElement {
  return screen.getByTestId("steward-verb-run") as HTMLButtonElement;
}

async function runOnceToState(label: string): Promise<void> {
  fireEvent.click(runButton());
  await screen.findByTestId("steward-detail");
  await vi.advanceTimersByTimeAsync(2500);
  await waitFor(() => expect(screen.getByTestId("steward-run-state").textContent).toBe(label));
}

function visibleWords(el: HTMLElement): string[] {
  return (el.textContent ?? "").split(/\s+/).filter(Boolean);
}

beforeEach(() => {
  useDesk.setState({ windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [] });
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.clearAllMocks();
  vi.useRealTimers();
});

describe("Watch sources: run once on the seeded room", () => {
  it("Run once is on, the run completes with its phases and effects, and the history row speaks", async () => {
    hub({ runsBefore: [], runsAfter: [DETAIL_OK.run], start: START_OK, polls: [running(DETAIL_OK), DETAIL_OK] });
    await enterWatchSources();

    expect(runButton().disabled).toBe(false);
    expect(screen.queryByTestId("steward-run-disabled-reason")).toBeNull();

    await runOnceToState("Completed");
    const plan = screen.getByTestId("steward-run-plan").querySelectorAll(".surface-plan-step");
    expect(plan.length).toBe(6);
    // The run's effects, by their words (the seeded overdue risk earns a Door item).
    const effects = screen.getByTestId("steward-receipt-refs").textContent ?? "";
    expect(effects).toContain("Door item created");
    expect(effects).toContain("Drafted update");
    for (const word of visibleWords(screen.getByTestId("steward-posture"))) expect(word).not.toMatch(RAW_ID);

    fireEvent.click(within(screen.getByTestId("steward-detail")).getByRole("button", { name: "Back" }));
    await waitFor(() => expect(screen.getByTestId("steward-posture").getAttribute("data-phase")).toBe("list"));
    expect(screen.getAllByTestId("steward-list-item")).toHaveLength(1);
    expect(screen.getByTestId("steward-list-summary").textContent).toBe("5 effects");
    expect(screen.getByTestId("steward-footer-receipt").textContent).toBe("Runs 1");
    // Run once is on again for the re-run.
    expect(runButton().disabled).toBe(false);
    for (const word of visibleWords(screen.getByTestId("steward-posture"))) expect(word).not.toMatch(RAW_ID);
  });
});

describe("Watch sources: Stop", () => {
  it("while the run runs, Stop shows; pressed, the run lands Interrupted with its reason", async () => {
    const stopped: Detail = {
      run: {
        ...DETAIL_OK.run, state: "interrupted", phase: "observe", stop_requested_at: "2026-10-11T15:37:51+00:00",
        // ProjectStewardService.execute_phases, StopRequested branch: the summary it writes.
        summary: { outcome: "interrupted", reason: "stop_requested", interrupted_phase: "observe", phases_completed: [] },
      },
      steps: [],
    };
    hub({ runsBefore: [], runsAfter: [stopped.run], start: START_OK, polls: [running(DETAIL_OK)], stopped });
    await enterWatchSources();

    await runOnceToState("Running");
    const stop = screen.getByTestId("steward-verb-stop");
    expect(stop.textContent).toBe("Stop");
    fireEvent.click(stop);
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith(`/api/steward/runs/${START_OK.run_id}/stop`, expect.objectContaining({ method: "POST" })),
    );
    await vi.advanceTimersByTimeAsync(2500);
    await waitFor(() => expect(screen.getByTestId("steward-run-state").textContent).toBe("Interrupted"));
    expect(screen.getByTestId("steward-run-reason").textContent).toBe("Stopped by you");
    expect(screen.queryByTestId("steward-verb-stop")).toBeNull();
  });
});

describe("Watch sources: a dead source", () => {
  it("the run completes and says PARTIAL COVERAGE with how many sources answered", async () => {
    hub({ runsBefore: [DETAIL_OK.run], runsAfter: [DETAIL_OK.run, DETAIL_DEAD.run], start: START_DEAD, polls: [DETAIL_DEAD] });
    await enterWatchSources();

    await runOnceToState("Completed");
    const chip = screen.getByTestId("steward-coverage-degraded");
    expect(chip.textContent).toBe("Partial coverage: 4 of 5 sources answered");
    expect(chip.getAttribute("data-tone")).toBe("warn");
  });
});

describe("Watch sources: history and policy", () => {
  it("history rows have no raw ids, a chevron and a summary; Policy shows the effects and Watch on; a row opens its run", async () => {
    hub({ runsBefore: [DETAIL_OK.run, DETAIL_DEAD.run], runsAfter: [], start: START_OK, polls: [DETAIL_OK] });
    const posture = await enterWatchSources();

    const rows = screen.getAllByTestId("steward-list-item");
    expect(rows).toHaveLength(2);
    for (const row of rows) for (const word of visibleWords(row)) expect(word).not.toMatch(RAW_ID);
    expect(screen.getAllByTestId("steward-list-chevron")).toHaveLength(2);
    const summaries = screen.getAllByTestId("steward-list-summary").map((s) => s.textContent);
    expect(summaries).toEqual(["5 effects", "4 effects"]);
    expect(screen.getByTestId("steward-footer-receipt").textContent).toBe("Runs 2");

    fireEvent.click(screen.getByTestId("steward-verb-policy"));
    await screen.findByTestId("steward-policy");
    expect(posture.getAttribute("data-phase")).toBe("policy");
    expect(screen.getByTestId("steward-policy-effects")).toBeTruthy();
    expect(screen.getByTestId("steward-policy").querySelector('input[aria-label="Watch on"]')).not.toBeNull();

    fireEvent.click(within(screen.getByTestId("steward-policy")).getByRole("button", { name: "Back" }));
    await waitFor(() => expect(posture.getAttribute("data-phase")).toBe("list"));
    fireEvent.click(screen.getAllByTestId("steward-list-item")[0]);
    await screen.findByTestId("steward-detail");
    await waitFor(() => expect(screen.getByTestId("steward-run-state").textContent).toBe("Completed"));
    for (const word of visibleWords(posture)) expect(word).not.toMatch(RAW_ID);
  });
});

/* ── The final diet lane: whole recorded Rooms, replayed ──────────────
 * A GET answers by its exact path, a press by `METHOD path`; a read the
 * recording does not hold is a failed read, listed in `misses`, which every
 * test asserts empty. */

const misses: string[] = [];
const sent: Array<{ key: string; json?: Json }> = [];
let hubGets: Record<string, unknown> = {};

function hubAnswer(value: unknown): Promise<unknown> {
  if (value && typeof value === "object" && "__status" in (value as Json)) {
    const { __status, body } = value as { __status: number; body: Json };
    return Promise.reject(new ApiError(__status, String(body?.message ?? `HTTP ${__status}`), body));
  }
  return Promise.resolve(JSON.parse(JSON.stringify(value)));
}

function replay(gets: Record<string, unknown>, presses: Record<string, (json?: Json) => unknown> = {}) {
  hubGets = gets;
  misses.length = 0;
  sent.length = 0;
  apiFetch.mockImplementation((url: string, init: { method?: string; json?: Json } = {}) => {
    const method = init.method ?? "GET";
    sent.push({ key: `${method} ${url}`, json: init.json });
    const press = presses[`${method} ${url}`];
    if (press) return Promise.resolve(press(init.json)).then(hubAnswer);
    const key = method === "GET" ? url : `${method} ${url}`;
    if (key in hubGets) return hubAnswer(hubGets[key]);
    misses.push(`${method} ${url}`);
    return Promise.reject(new ApiError(404, `not recorded: ${method} ${url}`, {}));
  });
}

function RoomOf({ pid }: { pid: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div>{wings}</div>
        <ProjectRoomCore scope={`project:${pid}`} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

async function enterSteward(pid: string): Promise<HTMLElement> {
  render(<RoomOf pid={pid} />);
  fireEvent.click(await screen.findByTestId("steward-verb"));
  const posture = await screen.findByTestId("steward-posture");
  await waitFor(() => expect(posture.getAttribute("data-phase")).toBe("list"));
  return posture;
}

async function enterPolicy(): Promise<HTMLElement> {
  fireEvent.click(screen.getByTestId("steward-verb-policy"));
  return screen.findByTestId("steward-policy");
}

describe("HS-164-06: unattended runs say Scheduled", () => {
  // replaces: tests/e2e/test_hs164_unattended_glass.py::test_gate_a_two_unattended_runs (the face; the two
  //   ticks are tests/integration/test_desk_project_room.py::test_two_conductor_ticks_make_two_completed_unattended_runs_with_no_duplicate_door_item)
  // replaces: tests/e2e/test_hs164_unattended_glass.py::test_dedup_across_ticks (DUP: tests/unit/test_steward_run_due.py::TestSameWatermarkDedup::test_second_effect_same_watermark_resolves)
  // replaces: tests/e2e/test_hs164_unattended_glass.py::test_opt_out_mid_cadence (DUP: tests/unit/test_steward_run_due.py::TestNoOptInSkip::test_no_optin_skips)
  it("two conductor runs in the history, each SCHEDULED; the first opens Completed, Scheduled, with its plan; no raw id", async () => {
    replay(GATE.gets);
    const posture = await enterSteward(GATE.pid);
    const rows = screen.getAllByTestId("steward-list-item");
    expect(rows.length).toBeGreaterThanOrEqual(2);
    const chips = screen.getAllByTestId("steward-run-provenance").map((c) => (c.textContent ?? "").trim().toLowerCase());
    expect(chips.filter((t) => t === "scheduled").length).toBeGreaterThanOrEqual(2);
    fireEvent.click(rows[0]);
    await screen.findByTestId("steward-detail");
    await waitFor(() => expect(screen.getByTestId("steward-run-state").textContent?.trim().toLowerCase()).toBe("completed"));
    expect(screen.getByTestId("steward-run-provenance").textContent?.trim().toLowerCase()).toBe("scheduled");
    expect(screen.getByTestId("steward-run-plan").querySelectorAll(".surface-plan-step").length).toBeGreaterThanOrEqual(1);
    for (const word of visibleWords(posture)) expect(word).not.toMatch(RAW_ID);
    expect(misses).toEqual([]);
  });
});

describe("HS-164-06: a source whose circuit opened, and healed", () => {
  // replaces: tests/e2e/test_hs164_unattended_glass.py::test_circuit_open_and_recovery (the face; the circuit
  //   itself: tests/unit/test_steward_conductor.py::TestCircuitOpenIntervention::test_circuit_open_emits_intervention and
  //   TestCadenceProjections::test_degraded_loop_healed_on_circuit_close)
  it("Policy shows the circuit open with its failure streak; after the healing tick, no circuit row", async () => {
    replay(CIRCUIT.opened);
    const view = render(<RoomOf pid={CIRCUIT.pid} />);
    fireEvent.click(await screen.findByTestId("steward-verb"));
    await screen.findByTestId("steward-posture");
    await enterPolicy();
    await screen.findByTestId("steward-circuit-row");
    expect(screen.getAllByTestId("steward-circuit-state")[0].textContent?.trim().toLowerCase()).toBe("circuit open");
    const streak = screen.queryAllByTestId("steward-circuit-streak");
    expect(streak.length).toBeGreaterThanOrEqual(1);
    expect(streak[0].textContent?.toLowerCase()).toContain("failure");
    expect(misses).toEqual([]);
    view.unmount();

    replay(CIRCUIT.healed);
    render(<RoomOf pid={CIRCUIT.pid} />);
    fireEvent.click(await screen.findByTestId("steward-verb"));
    await screen.findByTestId("steward-posture");
    const policy = await enterPolicy();
    expect(screen.queryAllByTestId("steward-circuit-row")).toHaveLength(0);
    for (const word of visibleWords(policy)) expect(word).not.toMatch(RAW_ID);
    expect(misses).toEqual([]);
  });
});

describe("HS-173-04: the Reviewer nudge row, checked and saved", () => {
  // replaces: tests/e2e/test_hs173_policy_glass.py::test_sixth_row_unchecked_with_badge_1440
  // replaces: tests/e2e/test_hs173_policy_glass.py::test_check_reveals_template_and_save
  // replaces: tests/e2e/test_hs173_policy_glass.py::test_policy_stacking_393 (its one assert, the row's label, is a DOM fact)
  const { pid, before, save, after } = P173;
  const putKey = `PUT /api/projects/${pid}/steward/policy`;
  const boxes = () => Array.from(screen.getByTestId("steward-policy-effects").querySelectorAll<HTMLInputElement>('input[type="checkbox"]'));

  it("a new project: Reviewer nudge unchecked with github.com and PER-NUDGE APPROVAL; checked, Save, Back, Policy: still checked with its text", async () => {
    replay(before, { [putKey]: () => { hubGets = { ...before, ...after }; return save.answer; } });
    await enterSteward(pid);
    await enterPolicy();
    expect(screen.getByTestId("steward-policy-kind-label-github_comment").textContent).toBe("Reviewer nudge");
    const egress = Array.from(screen.getByTestId("steward-policy-effects").querySelectorAll(".gadget-chip-egress"))
      .map((c) => c.textContent ?? "");
    expect(egress.some((t) => t.includes("github.com"))).toBe(true);
    expect(screen.getByTestId("steward-policy-nudge-approval").textContent).toContain("Per-nudge approval");
    expect(boxes().length).toBeGreaterThanOrEqual(6);
    expect(boxes()[5].checked).toBe(false);
    expect(screen.queryByTestId("steward-policy-nudge-template")).toBeNull();

    fireEvent.click(boxes()[5]);
    await screen.findByTestId("steward-policy-nudge-template");
    fireEvent.click(screen.getByTestId("steward-verb-save-policy"));
    await waitFor(() => expect(sent.filter((c) => c.key === putKey)).toHaveLength(1));
    // The face sent exactly the body the hub answered (the recording's request).
    expect(sent.find((c) => c.key === putKey)?.json).toEqual(save.request);

    fireEvent.click(within(screen.getByTestId("steward-policy")).getByRole("button", { name: "Back" }));
    await waitFor(() => expect(screen.getByTestId("steward-posture").getAttribute("data-phase")).toBe("list"));
    await enterPolicy();
    await waitFor(() => expect(boxes()[5].checked).toBe(true));
    expect(screen.getByTestId("steward-policy-nudge-template")).toBeTruthy();
    expect(misses).toEqual([]);
  });
});
