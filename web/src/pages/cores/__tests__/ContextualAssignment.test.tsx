import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ContextualAssignment } from "../ContextualAssignment";
import {
  getAssignmentEditor,
  saveAssignment,
} from "../assignmentExperience";

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn() }));
vi.mock("../../../desk/shell", () => ({ openSurfaceOr: shell.openSurfaceOr }));

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
  // PHILO-16 (C), ruling 2026-10-09 (Astra r1 M7): the atom is a READ; its
  // Change opens Runs on with this object's job selected, never the sheet.
  it("renders server-resolved facts and Change opens Runs on at the object's job", async () => {
    const { container } = render(<ContextualAssignment label="Project" capabilityId="ask.answer" scope={scope} />);
    expect(await screen.findByText("Uses subject · Quick Qwen")).toBeInTheDocument();
    expect(container.querySelector("select")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Change" }));
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-concierge", "/models", "ask.answer");
    expect(screen.queryByRole("heading", { name: "Project" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Save assignment" })).toBeNull();
    expect(saveAssignment).not.toHaveBeenCalled();
    expect(getAssignmentEditor).toHaveBeenLastCalledWith(scope, "ask.answer");
  });

  it.each([
    ["Recipe chat", "recipe.chat", { kind: "subject", subject_kind: "recipe", subject_id: "recipe-17", capability_id: "recipe.chat" }],
    ["Recipe run", "recipe.run", { kind: "subject", subject_kind: "recipe", subject_id: "recipe-17", capability_id: "recipe.run" }],
    ["Workbench item", "workbench.item", { kind: "subject", subject_kind: "workbench", subject_id: "workbench-17", capability_id: "workbench.item" }],
    ["Reference resolver", "voice.reference_resolve", { kind: "subject", subject_kind: "workbench", subject_id: "workbench-17", capability_id: "voice.reference_resolve" }],
  ] as const)("%s's Change opens Runs on at its capability's job", async (label, capabilityId, subjectScope) => {
    const scopedEditor = {
      ...editor,
      scope: subjectScope,
      selected_capability: { ...editor.selected_capability, id: capabilityId },
    };
    vi.mocked(getAssignmentEditor).mockResolvedValue(scopedEditor);
    render(<ContextualAssignment label={label} capabilityId={capabilityId} scope={subjectScope} />);
    fireEvent.click(await screen.findByRole("button", { name: "Change" }));
    expect(shell.openSurfaceOr).toHaveBeenLastCalledWith("open-concierge", "/models", capabilityId);
    expect(getAssignmentEditor).toHaveBeenLastCalledWith(subjectScope, capabilityId);
  });

  it("keeps the host surface alive for an incomplete server response", async () => {
    vi.mocked(getAssignmentEditor).mockResolvedValue({} as never);
    render(<ContextualAssignment label="Recipe run" capabilityId="recipe.run" scope={scope} />);
    expect(await screen.findByRole("status")).toHaveTextContent("Assignment unavailable");
  });
});
