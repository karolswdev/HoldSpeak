import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ContextualAssignment } from "../ContextualAssignment";
import {
  getAssignmentEditor,
  saveAssignment,
} from "../assignmentExperience";

vi.mock("../assignmentExperience", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../assignmentExperience")>()),
  getAssignmentEditor: vi.fn(), saveAssignment: vi.fn(),
  previewAssignmentDefault: vi.fn(), clearAssignmentDefault: vi.fn(),
}));

const scope = {
  kind: "subject" as const,
  subject_kind: "project",
  subject_id: "project-17",
  capability_id: "ask.answer",
};
const entry = { ordinal: 1, profile_id: "quick", profile_revision: 4, label: "Quick Qwen", boundary: "local", readiness: "ready" };
const editor = {
  schema: "AssignmentEditorProjection@1" as const,
  scope,
  selected_capability: { id: "ask.answer", revision: 8, label: "Ask", group: { id: "thoughts_notes", label: "Thoughts & notes" }, allowed_boundaries: ["local"], fallback_dispositions: [] },
  draft_base_revision: 11,
  configured_assignment: { id: "a1", revision: 11, scope, entries: [entry], retry_policy_id: null, issues: [] },
  effective: { status: "assigned" as const, inherited_from: "subject" as const, assignment: { id: "a1", revision: 11, scope, entries: [entry], retry_policy_id: null, issues: [] }, repair: null },
  candidates: [{ profile_id: "quick", profile_revision: 4, label: "Quick Qwen", boundary: "local", readiness: "ready", status: "compatible" as const, issues: [] }],
  retry_policy: { permitted_ids: ["retry.standard"], default_id: "retry.standard" },
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getAssignmentEditor).mockResolvedValue(editor);
  vi.mocked(saveAssignment).mockResolvedValue({});
});

describe("ContextualAssignment", () => {
  it("renders server-resolved facts and Change opens the exact pre-scoped editor", async () => {
    const { container } = render(<ContextualAssignment label="Project" capabilityId="ask.answer" scope={scope} />);
    expect(await screen.findByText("Uses subject · Quick Qwen")).toBeInTheDocument();
    expect(container.querySelector("select")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Change" }));
    await screen.findByRole("heading", { name: "Project" });
    expect(getAssignmentEditor).toHaveBeenLastCalledWith(scope, "ask.answer");
  });

  it("uses the shared canonical save path and reports a next-run-only receipt", async () => {
    render(<ContextualAssignment label="Project" capabilityId="ask.answer" scope={scope} />);
    fireEvent.click(await screen.findByRole("button", { name: "Change" }));
    await screen.findByRole("heading", { name: "Project" });
    fireEvent.click(screen.getByRole("button", { name: "Save assignment" }));
    await waitFor(() => expect(saveAssignment).toHaveBeenCalledWith(
      scope, 11, [{ profile_id: "quick", profile_revision: 4 }], null,
    ));
    expect(await screen.findByRole("status")).toHaveTextContent("Assignment changed to Quick Qwen. Next run.");
  });
});
