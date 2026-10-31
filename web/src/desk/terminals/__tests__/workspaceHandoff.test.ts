import { describe, expect, it } from "vitest";
import {
  MAX_CAPTURED_FILE_CONTENT,
  capturedWorkspaceFileContent,
  captureWorkspaceHandoff,
  workspaceHandoffScope,
  workspaceHandoffSourceWords,
  workspaceHandoffWords,
  type WorkspaceHandoffContext,
} from "../workspaceHandoff";

const context: WorkspaceHandoffContext = {
  project: { id: "project-ledger", name: "Ledger" },
  source: { id: "source-payments", title: "Payments repository" },
  worktree: { id: "worktree-review", branch: "feature/review" },
  file: { path: "src/ledger.ts", revision: "sha-1", content: "export const ready = true;" },
};

describe("workspace handoff preparation", () => {
  it("keeps source identity, worktree and file path in user-reviewed Note words without a file ref", () => {
    const words = workspaceHandoffWords("Review this file", context);
    expect(words).toContain("Repository source: Payments repository");
    expect(words).toContain("new work uses the Project's normal repository");
    expect(words).toContain("Source id: source-payments");
    expect(words).toContain("Captured worktree: worktree-review · feature/review");
    expect(words).toContain("File path: src/ledger.ts");
    expect(words).toContain("Read revision: sha-1");
    expect(words).toContain("export const ready = true;");
    expect(words).not.toContain("file:src/ledger.ts");
    expect(workspaceHandoffSourceWords(context)).toBe("Payments repository · src/ledger.ts");
  });

  it("bounds a captured read and says that it is shortened", () => {
    const captured = capturedWorkspaceFileContent("x".repeat(MAX_CAPTURED_FILE_CONTENT + 20));
    expect(captured.shortened).toBe(true);
    expect(captured.text).toContain("[… captured content shortened …]");
    expect(captured.text.length).toBeGreaterThan(MAX_CAPTURED_FILE_CONTENT);
    expect(workspaceHandoffWords("Do this", { ...context, file: { ...context.file!, content: "x".repeat(MAX_CAPTURED_FILE_CONTENT + 20) } })).toContain("shortened");
  });

  it("uses a separate durable scope for each Project, worktree and path", () => {
    // A disk revision changes the captured payload, not the owner's durable
    // words scope. The Start hand compares prepared words before reusing a
    // Note, so a changed read can make a new Note without hiding the draft.
    expect(workspaceHandoffScope(context)).toBe(workspaceHandoffScope({ ...context, file: { ...context.file!, revision: "sha-2" } }));
    expect(workspaceHandoffScope(context)).not.toBe(workspaceHandoffScope({ ...context, file: { ...context.file!, path: "src/other.ts" } }));
    expect(workspaceHandoffScope(context, "project-other")).not.toBe(workspaceHandoffScope(context));
  });

  it("captures request facts by value before an async hand", () => {
    const captured = captureWorkspaceHandoff(context)!;
    context.source!.title = "mutated after read";
    context.file!.content = "new bytes";
    expect(captured.source?.title).toBe("Payments repository");
    expect(captured.file?.content).toBe("export const ready = true;");
  });
});
