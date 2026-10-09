// PHILO-16 (C), Astra r1 M7: the retired assignment sheet is not reachable
// from the live Ask face. Its Change opens Runs on at Ask's job.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn() }));
vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openSurfaceOr: shell.openSurfaceOr,
}));

const scope = { kind: "capability", capability_id: "ask.answer" };
const entry = { ordinal: 1, profile_id: "quick", profile_revision: 4, label: "Quick Qwen", boundary: "local", readiness: "ready" };
const editor = {
  schema: "AssignmentEditorProjection@1",
  scope,
  selected_capability: { id: "ask.answer", revision: 8, label: "Ask", group: { id: "thoughts_notes", label: "Thoughts & notes" }, allowed_boundaries: ["local"], fallback_dispositions: [] },
  draft_base_revision: 1,
  configured_assignment: null,
  effective: { status: "assigned", inherited_from: "global", assignment: { id: "a1", revision: 1, scope, entries: [entry], retry_policy_id: null, issues: [] }, repair: null },
  candidates: [],
  retry_policy: { permitted_ids: [], default_id: "retry.standard" },
};

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  shell.openSurfaceOr.mockReset();
  useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askOpen: true, pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve({
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: () => Promise.resolve(String(url).includes("/api/inference/assignments/editor") ? editor : {}),
  })));
});

describe("AskPanel's assignment atom (PHILO-16 C)", () => {
  it("Change opens Runs on at Ask's job, never the parked sheet", async () => {
    render(<AskPanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Change" }));
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-concierge", "/models", "ask.answer");
    expect(screen.queryByRole("button", { name: "Save assignment" })).toBeNull();
  });
});
