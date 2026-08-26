import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CapabilityAssignmentsCore } from "../CapabilityAssignmentsCore";
import {
  clearAssignmentDefault,
  getAssignmentEditor,
  getAssignmentSummary,
  previewAssignmentDefault,
  saveAssignment,
  type AssignmentSummary,
} from "../assignmentExperience";

vi.mock("../assignmentExperience", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../assignmentExperience")>()),
  getAssignmentSummary: vi.fn(), getAssignmentEditor: vi.fn(),
  saveAssignment: vi.fn(), previewAssignmentDefault: vi.fn(), clearAssignmentDefault: vi.fn(),
}));

const entries = [{ ordinal: 1, profile_id: "quick", profile_revision: 1, label: "Quick Qwen", boundary: "local", readiness: "ready" }];
const rows = [
  ["global", "Default for AI work"], ["thoughts_notes", "Thoughts & notes"], ["writing_dictation", "Writing & dictation"],
  ["speech_recognition", "Speech recognition"], ["meetings", "Meetings"], ["agents_tools", "Agents & tools"], ["background", "Background"],
].map(([id, label]) => ({ id, label, editor_capability_id: "ask.answer", inherited_from: id === "global" ? null : "global", assignment: { id: "ia", revision: 1, scope: { kind: "global" as const }, entries, retry_policy_id: null, issues: [] }, status: "assigned", repair: null }));
function summary(overrides = []): AssignmentSummary {
  return { schema: "InferenceAssignmentSummary@1", rows, task_overrides: overrides, issue_count: 0 };
}
const editor = {
  schema: "AssignmentEditorProjection@1" as const, scope: { kind: "global" as const },
  selected_capability: { id: "ask.answer", revision: 1, label: "Ask", group: { id: "thoughts_notes", label: "Thoughts & notes" }, allowed_boundaries: ["local", "cloud"], fallback_dispositions: [] },
  draft_base_revision: 1, configured_assignment: { id: "ia", revision: 1, scope: { kind: "global" as const }, entries, retry_policy_id: null, issues: [] },
  effective: { status: "assigned" as const, inherited_from: "global" as const, assignment: { id: "ia", revision: 1, scope: { kind: "global" as const }, entries, retry_policy_id: null, issues: [] }, repair: null },
  candidates: [
    { profile_id: "quick", profile_revision: 1, label: "Quick Qwen", boundary: "local", readiness: "ready", status: "compatible" as const, issues: [] },
    { profile_id: "cloud", profile_revision: 1, label: "Deep Qwen", boundary: "cloud", readiness: "ready", status: "compatible" as const, issues: [] },
  ], retry_policy: { permitted_ids: ["retry.standard"], default_id: "retry.standard" },
};

const getSummary = vi.mocked(getAssignmentSummary);
const getEditor = vi.mocked(getAssignmentEditor);
beforeEach(() => { vi.clearAllMocks(); getSummary.mockResolvedValue(summary()); getEditor.mockResolvedValue(editor); vi.mocked(saveAssignment).mockResolvedValue({}); vi.mocked(previewAssignmentDefault).mockResolvedValue({ effective: editor.effective }); vi.mocked(clearAssignmentDefault).mockResolvedValue({}); });

describe("CapabilityAssignmentsCore", () => {
  it("renders exactly the bounded seven server rows with no per-row selects", async () => {
    const { container } = render(<CapabilityAssignmentsCore />);
    await screen.findByText("Background");
    expect(container.querySelectorAll(".capability-assignment-row")).toHaveLength(7);
    expect(container.querySelectorAll("select")).toHaveLength(0);
    expect(screen.getAllByText("Uses default · Quick Qwen")).toHaveLength(6);
  });

  it("sorts the single server issue first and keeps one Change affordance", async () => {
    const value = summary(); value.rows[5].repair = "Fix"; value.issue_count = 1; getSummary.mockResolvedValueOnce(value);
    const { container } = render(<CapabilityAssignmentsCore />);
    await screen.findByText("Agents & tools");
    expect(container.querySelector(".capability-assignment-row")?.textContent).toContain("Agents & tools");
    expect(screen.getAllByRole("button", { name: "Fix" })).toHaveLength(1);
  });

  it("keeps a hundred task capabilities behind the disclosure", async () => {
    const many = Array.from({ length: 100 }, (_, index) => ({ id: `task.${index}`, label: `Task ${index}`, group: { id: "thoughts_notes", label: "Thoughts & notes" }, has_override: false, effective: editor.effective, issues: [] }));
    getSummary.mockResolvedValueOnce(summary(many));
    const { container } = render(<CapabilityAssignmentsCore />);
    await screen.findByText("Assignments");
    expect(container.querySelectorAll(".capability-assignment-row")).toHaveLength(7);
    fireEvent.click(screen.getByText("Show task overrides"));
    fireEvent.click(screen.getByRole("button", { name: "All tasks" }));
    expect(await screen.findByText("Task 99")).toBeInTheDocument();
  });

  it("uses a server editor shell, previews before clear, and marks cloud candidates", async () => {
    render(<CapabilityAssignmentsCore />);
    fireEvent.click((await screen.findAllByRole("button", { name: "Change" }))[0]);
    await screen.findByRole("heading", { name: "Default for AI work" });
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.getAllByText("Egress")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Preview" }));
    await waitFor(() => expect(previewAssignmentDefault).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: "Use default" }));
    await waitFor(() => expect(clearAssignmentDefault).toHaveBeenCalled());
  });
});
