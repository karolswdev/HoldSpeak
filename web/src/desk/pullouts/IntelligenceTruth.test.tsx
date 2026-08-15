import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { IntelligencePullout } from "./IntelligencePullout";
import { INTELLIGENCE_NAVIGATE } from "../intelligenceNavigation";
import { untriagedBriefItems } from "../intelligenceAttention";

/**
 * HS-132-08 — the Intelligence surface tells the truth.
 *
 * Three defects are pinned here: a segment click that left a dispatched drill
 * filter standing (so the board announced a clear week over live commitments),
 * an unnamed and undismissable filter, and Acknowledge/Defer that wrote
 * nothing.
 */

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../lib/api", () => ({
  apiFetch,
  readableError: (reason: unknown) =>
    reason instanceof Error ? reason.message : "Request failed",
}));

const object = {
  kind: "intelligence" as const,
  id: "desk",
  title: "Intelligence",
  ref: { kind: "intelligence" as const, id: "desk", name: "Intelligence" },
};

const brief = {
  id: "brief-1",
  headline: "One thing changed.",
  is_empty: false,
  shelf: {} as Record<string, string>,
  sections: {
    changed: [
      {
        id: "brief-item-1",
        section: "changed",
        text: "Meeting recorded: Launch review",
        detail: "45 min",
        source_ref: "meeting:meeting-1",
        priority: 50,
      },
    ],
    broke: [],
    waiting: [],
    decisions: [],
  },
};

const liveCard = {
  id: "card-1",
  text: "Send the revised proposal",
  owner: "Ada",
  due: "2099-08-08",
  source: "meeting",
  decision_id: null,
  provenance: null,
};

const boardWithNoOverdue = {
  now: [liveCard],
  waiting: [],
  unassigned: [],
  overdue: [],
};

const emptyBoard = { now: [], waiting: [], unassigned: [], overdue: [] };

function mockApi(board: unknown = boardWithNoOverdue, latest: unknown = brief) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/brief/latest") return Promise.resolve(latest);
    if (path === "/api/follow-through/board") return Promise.resolve(board);
    if (path.startsWith("/api/decision-records")) return Promise.resolve([]);
    return Promise.resolve({});
  });
}

function drillToOverdue() {
  act(() => {
    window.dispatchEvent(
      new CustomEvent(INTELLIGENCE_NAVIGATE, {
        detail: { view: "follow-through", overdueOnly: true },
      }),
    );
  });
}

describe("HS-132-08 the board never announces a false all clear", () => {
  beforeEach(() => {
    localStorage.clear();
    apiFetch.mockReset();
    mockApi();
  });

  it("the audit probe: drilling to overdue then tabbing back shows every lane", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    await screen.findByText(brief.headline);

    drillToOverdue();
    await screen.findByRole("button", { name: "Clear filter OVERDUE ONLY" });

    fireEvent.click(screen.getByRole("button", { name: "Brief" }));
    fireEvent.click(screen.getByRole("button", { name: "Follow-through" }));

    // The live commitment is on the board, and nothing reads clear.
    expect(await screen.findByText(liveCard.text)).toBeInTheDocument();
    expect(screen.getByText("Now")).toBeInTheDocument();
    expect(screen.queryByText(/ALL CLEAR/i)).toBeNull();
    expect(screen.queryByText(/no follow-through yet/i)).toBeNull();
  });

  it("names the active drill filter and dismisses it in one click", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    await screen.findByText(brief.headline);

    drillToOverdue();

    const token = await screen.findByRole("button", {
      name: "Clear filter OVERDUE ONLY",
    });
    // Filtered to a lane that holds nothing: the state names the FILTER, not
    // a clear board.
    expect(screen.queryByText(liveCard.text)).toBeNull();
    expect(
      screen.getByText("No overdue follow-through. Other lanes hold work."),
    ).toBeInTheDocument();

    fireEvent.click(token);

    expect(await screen.findByText(liveCard.text)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Clear filter OVERDUE ONLY" }),
    ).toBeNull();
  });

  it("the filtered empty state offers the way back to every lane", async () => {
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    await screen.findByText(brief.headline);
    drillToOverdue();

    fireEvent.click(await screen.findByRole("button", { name: "Show all lanes" }));

    expect(await screen.findByText(liveCard.text)).toBeInTheDocument();
  });

  it("an empty board still says so, without the retired ALL CLEAR string", async () => {
    mockApi(emptyBoard);
    render(<IntelligencePullout object={object} onClose={() => {}} />);
    await screen.findByText(brief.headline);

    fireEvent.click(screen.getByRole("button", { name: "Follow-through" }));

    expect(await screen.findByText("No follow-through yet")).toBeInTheDocument();
    expect(screen.queryByText(/ALL CLEAR/i)).toBeNull();
  });
});

describe("HS-132-08 brief triage is durable", () => {
  beforeEach(() => {
    localStorage.clear();
    apiFetch.mockReset();
    mockApi();
  });

  it("Acknowledge writes to the shelf and refreshes the attention channel", async () => {
    const refreshes: Event[] = [];
    window.addEventListener("holdspeak:intelligence-attention-refresh", (event) =>
      refreshes.push(event),
    );
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    fireEvent.click(await screen.findByText(brief.sections.changed[0].text));
    fireEvent.click(screen.getByRole("button", { name: "Acknowledge" }));

    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/api/brief/items/brief-item-1/shelf", {
        method: "POST",
        json: { state: "acknowledged" },
      }),
    );
    await waitFor(() => expect(refreshes.length).toBeGreaterThan(0));
    expect(await screen.findByText("acknowledged")).toBeInTheDocument();
  });

  it("a shelf read back from the hub survives the pullout closing", async () => {
    mockApi(boardWithNoOverdue, {
      ...brief,
      shelf: { "brief-item-1": "deferred" },
    });
    const first = render(<IntelligencePullout object={object} onClose={() => {}} />);
    expect(await screen.findByText("deferred")).toBeInTheDocument();
    first.unmount();

    render(<IntelligencePullout object={object} onClose={() => {}} />);

    expect(await screen.findByText("deferred")).toBeInTheDocument();
  });

  it("a refused write reports through the write-receipt channel", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/brief/latest") return Promise.resolve(brief);
      if (path === "/api/follow-through/board")
        return Promise.resolve(boardWithNoOverdue);
      if (path.endsWith("/shelf")) return Promise.reject(new Error("refused"));
      return Promise.resolve({});
    });
    render(<IntelligencePullout object={object} onClose={() => {}} />);

    fireEvent.click(await screen.findByText(brief.sections.changed[0].text));
    fireEvent.click(screen.getByRole("button", { name: "Defer" }));

    expect(await screen.findByText(/DEFERRED FAILED/)).toBeInTheDocument();
    expect(screen.queryByText("deferred")).toBeNull();
  });
});

describe("HS-132-08 the attention badge reflects triage", () => {
  it("counts only untouched brief items", () => {
    expect(untriagedBriefItems(brief)).toBe(1);
    expect(
      untriagedBriefItems({ ...brief, shelf: { "brief-item-1": "acknowledged" } }),
    ).toBe(0);
    expect(untriagedBriefItems({ ...brief, is_empty: true })).toBe(0);
    expect(untriagedBriefItems(null)).toBe(0);
  });
});
