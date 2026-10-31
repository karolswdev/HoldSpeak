import { beforeEach, describe, expect, it } from "vitest";
import {
  cancelWorkspaceLaunch,
  queueWorkspaceLaunch,
  resolveWorkspaceLaunch,
  selectWorkspaceSession,
  setWorkspaceSelection,
  workspaceSelectionSnapshot,
} from "../workspaceSelection";
import type { TerminalDescriptor } from "../types";

const descriptor = (id: string, launchId: string): TerminalDescriptor => ({
  id,
  label: id,
  session: id,
  key: `agent:${id}`,
  agent: "codex",
  command: "zsh",
  current_path: "/work",
  state: "working",
  target: { node_id: "local", target_id: id, target_generation: "generation" },
  pane_id: `%${id}`,
  context: {
    status: "bound",
    project: { id: "project-a", name: "Project A" },
    source: { id: "source-a", name: "Source A" },
    worktree: { id: `worktree-${id}`, branch: "feature/workspace" },
    launch: { id: launchId, profile_id: "codex", state: "working", role: "builder", origin_ref: null, attempt_id: "attempt" },
    program: null,
    mcp: null,
  },
});

beforeEach(() => {
  setWorkspaceSelection({
    projectId: null,
    sessionId: null,
    face: "sessions",
    pendingLaunch: null,
    pendingKind: null,
    pendingProjectId: null,
    pendingHandoffs: [],
  });
});

describe("connected workspace selection", () => {
  it("retains separate launch and queue handoffs until each exact record resolves", () => {
    queueWorkspaceLaunch("launch-a", "project-a", "launch");
    queueWorkspaceLaunch("queue-b", "project-b", "queue");
    expect(workspaceSelectionSnapshot().pendingHandoffs.map((row) => row.id)).toEqual(["launch-a", "queue-b"]);

    resolveWorkspaceLaunch("launch-a", descriptor("terminal-a", "launch-a"));
    expect(workspaceSelectionSnapshot().pendingHandoffs.map((row) => row.id)).toEqual(["queue-b"]);
    expect(workspaceSelectionSnapshot().sessionId).toBe("terminal-a");

    selectWorkspaceSession(descriptor("terminal-manual", "launch-manual"));
    expect(workspaceSelectionSnapshot().pendingHandoffs.map((row) => row.id)).toEqual(["queue-b"]);
  });

  it("does not let a late arrival redirect a newer user selection", () => {
    queueWorkspaceLaunch("launch-a", "project-a", "launch");
    selectWorkspaceSession(descriptor("terminal-current", "launch-current"));
    resolveWorkspaceLaunch("launch-a", descriptor("terminal-a", "launch-a"));
    expect(workspaceSelectionSnapshot().sessionId).toBe("terminal-current");
    expect(workspaceSelectionSnapshot().pendingHandoffs).toHaveLength(0);
  });

  it("cancels only the requested pending handoff", () => {
    queueWorkspaceLaunch("launch-a", "project-a", "launch");
    queueWorkspaceLaunch("launch-b", "project-b", "launch");
    cancelWorkspaceLaunch("launch-a");
    expect(workspaceSelectionSnapshot().pendingHandoffs.map((row) => row.id)).toEqual(["launch-b"]);
  });
});
