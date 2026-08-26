import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { CapabilityAssignmentsCore } from "../CapabilityAssignmentsCore";
import {
  clearAssignmentDefault,
  getAssignmentEditor,
  getAssignmentSummary,
  previewAssignmentDefault,
  saveAssignment,
  type AssignmentEditorProjection,
  type AssignmentEntry,
  type AssignmentSummary,
  type AssignmentSummaryRow,
  type AssignmentUseDefaultPreview,
} from "../assignmentExperience";

vi.mock("../assignmentExperience", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../assignmentExperience")>()),
  getAssignmentSummary: vi.fn(), getAssignmentEditor: vi.fn(),
  saveAssignment: vi.fn(), previewAssignmentDefault: vi.fn(), clearAssignmentDefault: vi.fn(),
}));

const entries: AssignmentEntry[] = [
  { ordinal: 1, profile_id: "quick", profile_revision: 1, label: "Quick Qwen", boundary: "local", readiness: "ready" },
];
function summaryRow(id: string, label: string): AssignmentSummaryRow {
  return {
    id,
    label,
    editor_capability_id: "ask.answer",
    inherited_from: id === "global" ? null : "global",
    assignment: { id: "ia", revision: 1, scope: { kind: "global" }, entries, retry_policy_id: null, issues: [] },
    status: "assigned",
    repair: null,
  };
}
const rows = [
  ["global", "Default for AI work"], ["thoughts_notes", "Thoughts & notes"], ["writing_dictation", "Writing & dictation"],
  ["speech_recognition", "Speech recognition"], ["meetings", "Meetings"], ["agents_tools", "Agents & tools"], ["background", "Background"],
].map(([id, label]) => summaryRow(id, label));
function summary(overrides: AssignmentSummary["task_overrides"] = []): AssignmentSummary {
  return { schema: "InferenceAssignmentSummary@1", rows, task_overrides: overrides, issue_count: 0 };
}
const editor: AssignmentEditorProjection = {
  schema: "AssignmentEditorProjection@1" as const, scope: { kind: "global" as const },
  selected_capability: { id: "ask.answer", revision: 1, label: "Ask", group: { id: "thoughts_notes", label: "Thoughts & notes" }, allowed_boundaries: ["local", "cloud"], fallback_dispositions: ["known_no_generation_transient"] },
  draft_base_revision: 1, configured_assignment: { id: "ia", revision: 1, scope: { kind: "global" as const }, entries, retry_policy_id: null, issues: [] },
  effective: { status: "assigned" as const, inherited_from: "global" as const, assignment: { id: "ia", revision: 1, scope: { kind: "global" as const }, entries, retry_policy_id: null, issues: [] }, repair: null },
  candidates: [
    { profile_id: "quick", profile_revision: 1, label: "Quick Qwen", boundary: "local", readiness: "ready", status: "compatible" as const, issues: [] },
    { profile_id: "cloud", profile_revision: 1, label: "Deep Qwen", boundary: "cloud", readiness: "ready", status: "compatible" as const, issues: [] },
  ], retry_policy: { permitted_ids: ["retry.standard"], default_id: "retry.standard" },
};
const preview: AssignmentUseDefaultPreview = {
  schema: "InferenceUseDefaultPreview@1",
  clears: { kind: "global" },
  expected_revision: 1,
  effective: editor.effective,
};

const getSummary = vi.mocked(getAssignmentSummary);
const getEditor = vi.mocked(getAssignmentEditor);
async function openFirst() {
  const opener = (await screen.findAllByRole("button", { name: "Change" }))[0];
  opener.focus();
  fireEvent.click(opener);
  await screen.findByRole("heading", { name: "Default for AI work" });
  return opener;
}
beforeEach(() => {
  vi.clearAllMocks();
  getSummary.mockResolvedValue(summary()); getEditor.mockResolvedValue(editor);
  vi.mocked(saveAssignment).mockResolvedValue({});
  vi.mocked(previewAssignmentDefault).mockResolvedValue(preview);
  vi.mocked(clearAssignmentDefault).mockResolvedValue({});
});

describe("CapabilityAssignmentsCore", () => {
  it("renders exactly the bounded seven server rows with no per-row selects", async () => {
    const { container } = render(<CapabilityAssignmentsCore />);
    await screen.findByText("Background");
    expect(container.querySelectorAll(".capability-assignment-row")).toHaveLength(7);
    expect(container.querySelectorAll("select")).toHaveLength(0);
    expect(screen.getAllByText("Uses default · Quick Qwen")).toHaveLength(6);
  });

  it("sorts a server issue first with exactly one Fix affordance", async () => {
    const value = summary(); value.rows[5].repair = "Fix"; value.issue_count = 1; getSummary.mockResolvedValueOnce(value);
    const { container } = render(<CapabilityAssignmentsCore />);
    await screen.findByText("Agents & tools");
    expect(container.querySelector(".capability-assignment-row")?.textContent).toContain("Agents & tools");
    expect(screen.getAllByRole("button", { name: "Fix" })).toHaveLength(1);
    expect(screen.getAllByText("Fix")).toHaveLength(1);
  });

  it("keeps a hundred task capabilities behind the disclosure", async () => {
    const many: AssignmentSummary["task_overrides"] = Array.from({ length: 100 }, (_, index) => ({ id: `task.${index}`, label: `Task ${index}`, group: { id: "thoughts_notes", label: "Thoughts & notes" }, has_override: false, effective: editor.effective, issues: [] }));
    getSummary.mockResolvedValueOnce(summary(many));
    const { container } = render(<CapabilityAssignmentsCore />);
    await screen.findByText("Assignments");
    expect(container.querySelectorAll(".capability-assignment-row")).toHaveLength(7);
    fireEvent.click(screen.getByText("Show task overrides"));
    fireEvent.click(screen.getByRole("button", { name: "All tasks" }));
    expect(await screen.findByText("Task 99")).toBeInTheDocument();
  });

  it("renders the server chain, uses a local draft, and submits one ordered CAS body", async () => {
    render(<CapabilityAssignmentsCore />);
    await openFirst();
    expect(screen.getAllByText("Quick Qwen").length).toBeGreaterThanOrEqual(2);
    const cloud = screen.getByRole("radio", { name: /Deep Qwen/ });
    fireEvent.click(cloud);
    expect(saveAssignment).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Move Deep Qwen up" }));
    expect(screen.getByText("Deep Qwen is now position 1.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Save assignment" }));
    await waitFor(() => expect(saveAssignment).toHaveBeenCalledWith(
      { kind: "global" }, 1,
      [{ profile_id: "cloud", profile_revision: 1 }, { profile_id: "quick", profile_revision: 1 }], null,
    ));
    expect(await screen.findByRole("status")).toHaveTextContent("Assignment changed to Deep Qwen → Quick Qwen. Next run.");
  });

  it("uses the server preview revision before clear and discards it on conflict", async () => {
    vi.mocked(previewAssignmentDefault).mockResolvedValueOnce({ ...preview, expected_revision: 7 });
    vi.mocked(clearAssignmentDefault).mockRejectedValueOnce(new ApiError(409, "Assignment changed. Refresh before clearing.", {}));
    render(<CapabilityAssignmentsCore />);
    await openFirst();
    fireEvent.click(screen.getByRole("button", { name: "Preview" }));
    expect(await screen.findByText("Will use Quick Qwen")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Use default" }));
    await waitFor(() => expect(clearAssignmentDefault).toHaveBeenCalledWith({ kind: "global" }, "ask.answer", 7));
    expect(await screen.findByText("Assignment changed. Refresh before clearing.")).toBeInTheDocument();
    expect(screen.queryByText("Will use Quick Qwen")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await waitFor(() => expect(getEditor).toHaveBeenCalledTimes(2));
  });

  it("reorders a draft by drag without creating a slot-level mutation", async () => {
    const { container } = render(<CapabilityAssignmentsCore />);
    await openFirst();
    fireEvent.click(screen.getByRole("radio", { name: /Deep Qwen/ }));
    const legs = container.querySelectorAll(".assignment-draft-list > li");
    const transfer = { setData: vi.fn(), getData: vi.fn(() => "1") };
    fireEvent.dragStart(legs[1], { dataTransfer: transfer });
    fireEvent.drop(legs[0], { dataTransfer: transfer });
    expect(transfer.setData).toHaveBeenCalledWith("text/plain", "1");
    expect(container.querySelector(".assignment-draft-list > li strong")?.textContent).toBe("Deep Qwen");
    expect(saveAssignment).not.toHaveBeenCalled();
  });

  it("keeps candidate arrows as roving selection, never an action or save", async () => {
    render(<CapabilityAssignmentsCore />);
    await openFirst();
    const quick = screen.getByRole("radio", { name: /Quick Qwen/ });
    quick.focus();
    fireEvent.keyDown(quick, { key: "ArrowDown" });
    await waitFor(() => expect(screen.getByRole("radio", { name: /Deep Qwen/ })).toHaveAttribute("aria-checked", "true"));
    expect(saveAssignment).not.toHaveBeenCalled();
    expect(screen.getAllByRole("button", { name: "Save assignment" })).toHaveLength(1);
  });

  it("returns exact focus on Escape and maps Mod+Enter to the sole primary", async () => {
    render(<CapabilityAssignmentsCore />);
    const opener = await openFirst();
    const close = screen.getByRole("button", { name: "Close" });
    expect(close).toHaveFocus();
    const primary = screen.getByRole("button", { name: "Save assignment" });
    primary.focus();
    fireEvent.keyDown(primary, { key: "Tab" });
    expect(close).toHaveFocus();
    fireEvent.keyDown(screen.getByLabelText("Default for AI work assignment"), { key: "Escape" });
    await waitFor(() => expect(opener).toHaveFocus());
    fireEvent.click(opener);
    await screen.findByRole("heading", { name: "Default for AI work" });
    fireEvent.keyDown(screen.getByLabelText("Default for AI work assignment"), { key: "Enter", ctrlKey: true });
    await waitFor(() => expect(saveAssignment).toHaveBeenCalledTimes(1));
  });
});
