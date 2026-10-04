// Inventory C, gaps 7 and 8 (2026-10-03) — the Desk memory face draws what
// memory finds: an open action item under OWED with the existing owed row
// species and its one verb; a settled one under ALSO; a send as a row with
// no open (it has no window). The row shapes are the ones
// `RecallService.recall` answers (tests/unit/test_memory_findable_kinds.py
// reads them from the real route).
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../../lib/api";
import { RecallFace } from "../RecallFace";

vi.mock("../../../../lib/api", async (original) => ({
  ...await original<typeof import("../../../../lib/api")>(),
  apiFetch: vi.fn(),
}));
const openIntelligence = vi.hoisted(() => vi.fn());
vi.mock("../../../../desk/intelligenceNavigation", async (original) => ({
  ...await original<typeof import("../../../../desk/intelligenceNavigation")>(),
  openIntelligence,
}));
vi.mock("../../../../desk/components/MicButton", () => ({
  MicButton: ({ label }: { label: string }) => (
    <button type="button" className="desk-mic" aria-label={label} />
  ),
}));
vi.mock("../../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({ receipt }: { receipt?: React.ReactNode }) => <footer>{receipt}</footer>,
}));

const OWED_ACTION = {
  id: "act-1", ref: "action:act-1", action_item_id: "act-1",
  text: "Draft the quillfeather rollout checklist", owner: "Dana", owner_token: "OWNER · DANA",
  due_at: "2026-10-09", due_token: "DUE 10-09", due_tone: "idle", status: "pending",
  unknowns: [], next_action: "mark_done", project: null,
  decision_record_id: null, decision_state: null,
};
const DONE_ACTION = {
  kind: "action", source_ref: "action:act-2", title: "Send the quillfeather notes",
  snippet: "Dana  done", occurred_at: "2026-10-01T10:00:00", project_id: null,
};
const SEND = {
  kind: "send", source_ref: "send:csend_1", title: "Atlas — update r1 (2026-10-02)",
  snippet: "To Dana · file · sent", occurred_at: "2026-10-02T10:00:00", project_id: "p1",
};

function wire(payload: Record<string, unknown>) {
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { json?: unknown }) => {
    const p = String(path);
    if (p.startsWith("/api/memory/recall")) {
      return {
        query: "quillfeather", filter: "all", searched_at: "2026-10-03T09:20:00", projects_searched: 1,
        current: [], superseded: [], disputed: [], owed: [], meetings: [], briefs: [], also: [],
        remembered: 1, ...payload,
      };
    }
    if (p === "/api/follow-through/complete") return { card_id: (init?.json as { card_id: string }).card_id };
    return null;
  });
}

async function search(query: string) {
  fireEvent.change(screen.getByRole("searchbox", { name: "Search the Desk" }), { target: { value: query } });
  fireEvent.click(screen.getByRole("button", { name: "Search desk memory" }));
  await screen.findByTestId("recall-results");
}

describe("Desk memory draws what memory finds", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    openIntelligence.mockReset();
    localStorage.clear();
  });
  afterEach(() => localStorage.clear());

  it("an open action item is an OWED row with its one verb", async () => {
    wire({ owed: [OWED_ACTION] });
    render(<RecallFace />);
    await search("quillfeather");
    const row = screen.getByTestId("recall-owed-row");
    expect(within(row).getByTestId("recall-owed-title").textContent).toBe("Draft the quillfeather rollout checklist");
    fireEvent.click(within(row).getByRole("button", { name: "Mark done: Draft the quillfeather rollout checklist" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "act-1", verb: "done", payload: {} },
    }));
  });

  it("a settled action item under ALSO opens Follow-through; a send draws no open", async () => {
    wire({ also: [DONE_ACTION, SEND], remembered: 2 });
    render(<RecallFace />);
    await search("quillfeather");
    const tokens = screen.getAllByTestId("recall-also-meta").map((n) => n.textContent);
    expect(tokens).toEqual(["action", "send"]);

    fireEvent.click(screen.getByRole("button", { name: /Send the quillfeather notes/ }));
    expect(openIntelligence).toHaveBeenCalledWith({ view: "follow-through", followThroughId: "act-2" });

    expect(screen.getByText("Atlas — update r1 (2026-10-02)")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Atlas — update r1/ })).toBeNull();
  });

  it("a kind with two words reads as words", async () => {
    wire({ also: [{ ...SEND, kind: "project_update", source_ref: "project_update:u1" }] });
    render(<RecallFace />);
    await search("quillon");
    expect(screen.getByTestId("recall-also-meta").textContent).toBe("project update");
  });
});
