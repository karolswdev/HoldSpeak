// HS-150-03 -- BriefView tests: person sections render with the correct
// manager verbs (Add to 1:1 agenda, Open person); receipt items keep
// Acknowledge/Defer/Speak; absence renders as L2 honesty line.

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Activity } from "react";
import { BriefView } from "./BriefView";

// ---------------------------------------------------------------------------
// mocks
// ---------------------------------------------------------------------------

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", () => ({
  apiFetch,
  // plainFailure reads `instanceof ApiError` on a failure.
  ApiError: class ApiError extends Error {
    status = 0;
  },
  readableError: (reason: unknown) =>
    reason instanceof Error ? reason.message : "Request failed",
}));

vi.mock("../../intelligenceAttention", async () => {
  const actual = await vi.importActual<typeof import("../../intelligenceAttention")>(
    "../../intelligenceAttention",
  );
  return {
    ...actual,
    refreshIntelligenceAttention: vi.fn(),
  };
});

const openSurfaceOr = vi.hoisted(() => vi.fn());

const openPrimitive = vi.hoisted(() => vi.fn());
vi.mock("../../shell", () => ({
  openSurfaceOr,
  openPrimitive,
}));

// ---------------------------------------------------------------------------
// fixtures
// ---------------------------------------------------------------------------

const briefWithPeople = {
  id: "brief-people",
  headline: "1 thing changed.",
  is_empty: false,
  shelf: {},
  period_label: "SEP 01 – 05",
  generated_label: "GENERATED SEP 05 08:00",
  period_start: "2026-09-04T17:00:00",
  sections: {
    this_week: [],
    changed: [
      {
        id: "item-1",
        section: "changed",
        text: "Meeting recorded: Standup",
        detail: null,
        source_ref: "meeting:m-1",
        priority: 50,
      },
    ],
    broke: [],
    waiting: [],
    decisions: [],
  },
  person_sections: [
    {
      relationship_id: "rel-ewa",
      display_name: "Ewa",
      they_owe_count: 2,
      stalest_age_days: 5,
      you_owe_count: 1,
      agenda_backlog: 3,
      next_one_on_one: { event_id: "ev-1", title: "Weekly 1:1", starts_at: "2026-09-01" },
    },
  ],
};

const briefWithUnavailablePeople = {
  ...briefWithPeople,
  person_sections: undefined,
  person_sections_state: "unavailable",
};

// These are deliberately timezone-less ISO values: generated_at is a source
// wall clock in the viewer's local time, so the test must exercise 00:33 and
// 08:00 without depending on the machine's UTC offset.
const localGeneratedCases = [
  { label: "hour 00", generatedAt: "2026-09-20T00:33:00", expected: "GENERATED SEP 20 00:33" },
  { label: "minute 00", generatedAt: "2026-09-20T08:00:00", expected: "GENERATED SEP 20 08:00" },
] as const;

function briefWithThisWeek(generatedAt: string) {
  return {
    ...briefWithPeople,
    id: `brief-this-week-${generatedAt}`,
    generated_at: generatedAt,
    sections: {
      ...briefWithPeople.sections,
      this_week: [
        {
          id: "week-meetings",
          section: "this_week" as const,
          text: "2 meetings this week",
          detail: null,
          source_ref: "calendar:week",
          priority: 60,
        },
        {
          id: "week-next",
          section: "this_week" as const,
          text: "Next: Sprint Planning at 09:00",
          detail: null,
          source_ref: "calendar:event:next",
          priority: 55,
        },
        {
          id: "week-armed",
          section: "this_week" as const,
          text: "0 armed",
          detail: null,
          source_ref: "calendar:armed",
          priority: 53,
        },
        {
          id: "week-due",
          section: "this_week" as const,
          text: "1 commitment due",
          detail: "Ania owns the API spec | 2026-09-20",
          source_ref: "meeting_watch:commitments_due",
          priority: 51,
        },
      ],
    },
  };
}

function mockBrief(brief: unknown = briefWithPeople) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/brief/latest") return Promise.resolve(brief);
    if (path === "/api/brief/generate") return Promise.resolve(brief);
    if (path.includes("/shelf")) return Promise.resolve({ ok: true });
    if (path.includes("/one-on-ones") && !path.includes("/agenda"))
      return Promise.resolve({ one_on_ones: [{ id: "session-1", state: "open" }] });
    if (path.includes("/agenda"))
      return Promise.resolve({ agenda_item: { id: "ai-1" } });
    return Promise.resolve({});
  });
}

function renderBriefView() {
  return render(
    <BriefView
      header={<div>Header</div>}
      onOpenFollowThrough={vi.fn()}
    />,
  );
}

// ---------------------------------------------------------------------------
// tests
// ---------------------------------------------------------------------------

describe("BriefView person sections", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders person section with display name and signals", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByTestId("person-sections")).toBeInTheDocument();
    });
    expect(screen.getByText("Ewa")).toBeInTheDocument();
  });

  it("renders four signals for a person row", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });

    // Click to expand the person row.
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByText(/They owe 2/)).toBeInTheDocument();
    });
    expect(screen.getByText(/You owe 1/)).toBeInTheDocument();
    expect(screen.getByText(/3 agenda/)).toBeInTheDocument();
    expect(screen.getByText(/Next: Weekly 1:1/)).toBeInTheDocument();
  });

  it("shows person verbs (Add to 1:1 agenda, Open person) when person selected", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });

    // Select the person.
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByTestId("verb-add-agenda")).toBeInTheDocument();
    });
    expect(screen.getByTestId("verb-open-person")).toBeInTheDocument();
    expect(screen.getByText("Add to 1:1 agenda")).toBeInTheDocument();
    expect(screen.getByText("Open person")).toBeInTheDocument();
  });

  it("'Add to 1:1 agenda' calls the existing people agenda endpoint", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByTestId("verb-add-agenda")).toBeInTheDocument();
    });
    await act(async () => {
      fireEvent.click(screen.getByTestId("verb-add-agenda"));
    });

    // Verify it called the sessions endpoint first, then the agenda endpoint.
    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        "/api/people/relationships/rel-ewa/one-on-ones",
      );
      expect(apiFetch).toHaveBeenCalledWith(
        "/api/people/one-on-ones/session-1/agenda",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("'Open person' calls openSurfaceOr with people focus", async () => {
    mockBrief();
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByText("Ewa")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Ewa"));

    await waitFor(() => {
      expect(screen.getByTestId("verb-open-person")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByTestId("verb-open-person"));

    // PHILO-17 (2b): THAT person, in their own window.
    expect(openPrimitive).toHaveBeenCalledWith("people:rel-ewa");
  });

  it("receipt items still show Acknowledge/Defer/Speak verbs", async () => {
    mockBrief();
    renderBriefView();

    // HS-175: lookback items are split into kind token + primary.
    // "Meeting recorded: Standup" -> kind "MEETING RECORDED", primary "Standup".
    await waitFor(() => {
      expect(screen.getByText("Standup")).toBeInTheDocument();
    });

    // Select the receipt item by clicking the primary text.
    fireEvent.click(screen.getByText("Standup"));

    await waitFor(() => {
      expect(screen.getByText("Acknowledge")).toBeInTheDocument();
    });
    expect(screen.getByText("Defer")).toBeInTheDocument();
    expect(screen.getByText("Speak")).toBeInTheDocument();
  });

  it("the latest person or item selection owns the row and footer", async () => {
    mockBrief();
    renderBriefView();
    fireEvent.click(await screen.findByText("Ewa"));
    expect(screen.getByTestId("verb-add-agenda")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Standup"));
    expect(screen.getByText("SELECTED · MEETING RECORDED · Standup")).toBeInTheDocument();
    expect(screen.queryByTestId("verb-add-agenda")).not.toBeInTheDocument();
    expect(screen.getByText("Standup").closest("[data-selected]")).not.toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Acknowledge" }));
    await waitFor(() => expect(screen.getByText("acknowledged")).toBeInTheDocument());
    expect(apiFetch).toHaveBeenCalledWith("/api/brief/items/item-1/shelf", {
      method: "POST", json: { state: "acknowledged" },
    });

    fireEvent.click(screen.getByText("Ewa"));
    expect(screen.getByText("PERSON · Ewa")).toBeInTheDocument();
    expect(screen.getByTestId("verb-add-agenda")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Acknowledge" })).not.toBeInTheDocument();
    expect(screen.getByText("Standup").closest("[data-selected]")).toBeNull();
  });

  it("a late agenda refusal names its original person while the item keeps the footer and Retry target", async () => {
    mockBrief();
    const answer = apiFetch.getMockImplementation()!;
    let refuse!: (cause: unknown) => void;
    apiFetch.mockImplementation((path: string, init?: unknown) => path === "/api/people/one-on-ones/session-1/agenda"
      ? new Promise((_resolve, reject) => { refuse = reject; }) : answer(path, init));
    renderBriefView();
    fireEvent.click(await screen.findByText("Ewa"));
    fireEvent.click(screen.getByRole("button", { name: "Add to 1:1 agenda" }));
    await waitFor(() => expect(refuse).toBeTypeOf("function"));
    fireEvent.click(screen.getByText("Standup"));
    await act(async () => refuse({ status: 503 }));

    expect(screen.getByText("SELECTED · MEETING RECORDED · Standup")).toBeInTheDocument();
    expect(screen.getByText(/EWA · ADD TO 1:1 AGENDA FAILED · HTTP 503/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Acknowledge" })).toBeInTheDocument();
    expect(screen.queryByTestId("verb-add-agenda")).not.toBeInTheDocument();
    apiFetch.mockImplementation(answer);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument());
    expect(apiFetch.mock.calls.filter(([path]) => path === "/api/people/relationships/rel-ewa/one-on-ones")).toHaveLength(2);
    expect(apiFetch.mock.calls.filter(([path]) => path === "/api/people/one-on-ones/session-1/agenda")).toHaveLength(2);
    expect(screen.getByText("SELECTED · MEETING RECORDED · Standup")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Ewa"));
    expect(screen.getByText("PERSON · Ewa")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Ewa"));
    expect(screen.queryByText("PERSON · Ewa")).not.toBeInTheDocument();
    expect(screen.getByTestId("brief-refresh")).toBeInTheDocument();
  });

  it("a late shelf refusal after person selection clears names the original item and preserves exact Retry", async () => {
    mockBrief();
    const answer = apiFetch.getMockImplementation()!;
    let refuse!: (cause: unknown) => void;
    apiFetch.mockImplementation((path: string, init?: unknown) => path === "/api/brief/items/item-1/shelf"
      ? new Promise((_resolve, reject) => { refuse = reject; }) : answer(path, init));
    renderBriefView();
    fireEvent.click(await screen.findByText("Standup"));
    fireEvent.click(screen.getByRole("button", { name: "Defer" }));
    await waitFor(() => expect(refuse).toBeTypeOf("function"));
    fireEvent.click(screen.getByText("Ewa"));
    expect(screen.getByText("PERSON · Ewa")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Ewa"));
    await act(async () => refuse({ status: 409 }));

    expect(screen.getByText(/STANDUP · DEFERRED FAILED · HTTP 409/)).toBeInTheDocument();
    expect(screen.queryByText("PERSON · Ewa")).not.toBeInTheDocument();
    expect(screen.queryByText("SELECTED · MEETING RECORDED · Standup")).not.toBeInTheDocument();
    expect(screen.getByTestId("brief-refresh")).toBeInTheDocument();
    apiFetch.mockImplementation(answer);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument());
    const shelfCalls = apiFetch.mock.calls.filter(([path]) => path === "/api/brief/items/item-1/shelf");
    expect(shelfCalls).toHaveLength(2);
    expect(shelfCalls.map(([, init]) => init)).toEqual([
      { method: "POST", json: { state: "deferred" } },
      { method: "POST", json: { state: "deferred" } },
    ]);
    expect(apiFetch.mock.calls.some(([path]) => String(path).includes("/agenda"))).toBe(false);
  });

  it("renders L2 unavailable line when sidecar is closed", async () => {
    mockBrief(briefWithUnavailablePeople);
    renderBriefView();

    await waitFor(() => {
      expect(screen.getByTestId("person-sections-unavailable")).toBeInTheDocument();
    });
    // PHILO-17: the words for why, and the one verb that fixes it.
    expect(screen.getByText("People is not open, so the brief has no people")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Open People" })).toBeInTheDocument();
  });
});

describe("BriefView THIS WEEK counters and generated clock", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each(localGeneratedCases)(
    "keeps a $label generated clock separate from zero counters",
    async ({ generatedAt, expected }) => {
      mockBrief(briefWithThisWeek(generatedAt));
      renderBriefView();

      await waitFor(() => {
        expect(screen.getByTestId("brief-generated-label")).toHaveTextContent(expected);
      });

      // These are actual BriefView labels from real this_week inputs. The
      // zero ARMED row is omitted while positive MEETINGS and DUE rows remain.
      expect(screen.getByTestId("brief-tw-meetings")).toHaveTextContent("2 MEETINGS");
      expect(screen.queryByTestId("brief-tw-armed")).not.toBeInTheDocument();
      expect(screen.getByTestId("brief-tw-due")).toHaveTextContent("1 DUE");
    },
  );
});

describe("BriefView PHILO-17: refresh, blocker verb, THIS WEEK rows, named triage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("makes a stale brief again once, and shows Refresh with nothing selected", async () => {
    const fresh = { ...briefWithPeople, id: "brief-fresh", stale: false };
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/brief/latest") return Promise.resolve({ ...briefWithPeople, stale: true });
      if (path === "/api/brief/generate") return Promise.resolve(fresh);
      return Promise.resolve({});
    });
    renderBriefView();

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith("/api/brief/generate", { method: "POST" });
    });
    expect(apiFetch.mock.calls.filter(([path]) => path === "/api/brief/generate")).toHaveLength(1);
    expect(await screen.findByTestId("brief-refresh")).toHaveTextContent("Refresh");
    // Nothing is selected, so no verb acts on an unnamed row.
    expect(screen.queryByText("Acknowledge")).not.toBeInTheDocument();
    expect(screen.queryByText("Defer")).not.toBeInTheDocument();

    await act(async () => {
      fireEvent.click(screen.getByTestId("brief-refresh"));
    });
    expect(apiFetch.mock.calls.filter(([path]) => path === "/api/brief/generate")).toHaveLength(2);
  });

  it.each([
    ["answers nothing", () => Promise.resolve(null)],
    ["fails", () => Promise.reject(new Error("hub down"))],
  ])("keeps the brief on the glass when a rebuild %s", async (_label, answer) => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/brief/latest") return Promise.resolve({ ...briefWithPeople, stale: true });
      if (path === "/api/brief/generate") return answer();
      return Promise.resolve({});
    });
    renderBriefView();
    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith("/api/brief/generate", { method: "POST" });
    });
    expect(await screen.findByText(/BRIEF NOT MADE AGAIN/)).toBeInTheDocument();
    expect(screen.getByText("Standup")).toBeInTheDocument();
    expect(screen.getByTestId("brief-refresh")).toBeInTheDocument();
  });

  it("does not make a fresh brief again by itself", async () => {
    mockBrief({ ...briefWithPeople, stale: false });
    renderBriefView();
    await screen.findByTestId("brief-refresh");
    expect(apiFetch).not.toHaveBeenCalledWith("/api/brief/generate", expect.anything());
  });

  it("the no-engine row's verb is a Button that opens Runs on", async () => {
    mockBrief({
      ...briefWithPeople,
      sections: {
        ...briefWithPeople.sections,
        waiting: [
          {
            id: "blocker-summary",
            section: "waiting",
            text: "No engine for summaries",
            detail: "Choose an engine",
            source_ref: "blocker:summary",
            priority: 120,
          },
        ],
      },
    });
    renderBriefView();

    const verb = await screen.findByTestId("brief-blocker-verb-summary");
    expect(verb.tagName).toBe("BUTTON");
    expect(verb).toHaveTextContent("Choose an engine");
    fireEvent.click(verb);
    expect(openSurfaceOr).toHaveBeenCalledWith("open-concierge", "/models", "summary");
  });

  it("draws a THIS WEEK item no composed row draws, and no empty heading", async () => {
    mockBrief({
      ...briefWithPeople,
      sections: {
        ...briefWithPeople.sections,
        this_week: [
          {
            id: "week-decisions",
            section: "this_week",
            text: "1 new decision from meetings",
            detail: null,
            source_ref: "meeting_watch:decisions",
            priority: 52,
          },
        ],
      },
    });
    renderBriefView();
    expect(await screen.findByTestId("brief-tw-other")).toHaveTextContent("1 new decision from meetings");

    mockBrief({
      ...briefWithPeople,
      sections: {
        ...briefWithPeople.sections,
        this_week: [
          { id: "w0", section: "this_week", text: "0 armed", detail: null, source_ref: "calendar:armed", priority: 53 },
        ],
      },
    });
    const second = renderBriefView();
    await waitFor(() => expect(second.container.querySelector("[data-testid='brief-since-friday']")).not.toBeNull());
    expect(second.container.querySelector("[data-testid='brief-this-week']")).toBeNull();
  });

  it("the triage receipt names the selected row", async () => {
    mockBrief();
    renderBriefView();
    fireEvent.click(await screen.findByText("Standup"));
    expect(await screen.findByText("SELECTED · MEETING RECORDED · Standup")).toBeInTheDocument();
    expect(screen.getByText("Acknowledge")).toBeInTheDocument();
    expect(screen.queryByTestId("brief-refresh")).not.toBeInTheDocument();
  });

  it.each(["read", "failed read"])("keeps the real open Send well and selected subject during a retained Brief resume %s", async (outcome) => {
    mockBrief();
    const respond = apiFetch.getMockImplementation()!;
    let reads = 0;
    let finish!: (value: unknown) => void;
    let fail!: (reason: Error) => void;
    const resumed = new Promise((resolve, reject) => { finish = resolve; fail = reject; });
    apiFetch.mockImplementation((path: string, ...args: unknown[]) => {
      if (path === "/api/brief/latest" && ++reads > 1) return resumed;
      return respond(path, ...args);
    });
    const face = (mode: "visible" | "hidden") => <Activity mode={mode}><BriefView header={null} /></Activity>;
    const view = render(face("visible"));
    fireEvent.click(await screen.findByRole("button", { name: "Standup" }));
    fireEvent.click(screen.getByTestId("brief-send-toggle"));
    // This is the actual lazy BriefSendWells/SendWell, not a mocked child.
    const well = await screen.findByTestId("send-well");
    const fold = screen.getByTestId("brief-send-fold");
    view.rerender(face("hidden"));
    view.rerender(face("visible"));
    await waitFor(() => expect(reads).toBe(2));
    expect(screen.getByTestId("brief-send-fold")).toBe(fold);
    expect(screen.getByTestId("brief-send-toggle")).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByTestId("send-well")).toBe(well);
    expect(screen.getByText("SELECTED · MEETING RECORDED · Standup")).toBeInTheDocument();
    await act(async () => {
      if (outcome === "read") finish(briefWithPeople);
      else fail(new Error("Resume read unavailable"));
      await resumed.catch(() => {});
    });
    expect(screen.getByTestId("send-well")).toBe(well);
    expect(screen.getByTestId("brief-send-toggle")).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("SELECTED · MEETING RECORDED · Standup")).toBeInTheDocument();
    expect(screen.queryByText(/BRIEF DID NOT LOAD/)).toBeNull();
  });

  it("leads with obligations, then changed work before week counts, and keeps source titles as library verbs", async () => {
    const brief = briefWithThisWeek("2026-09-20T08:00:00");
    const page = (slug: string, text: string) => ({ slug, question: slug, sentences: [{ text, refs: [] }], built_at: "2026-09-20T08:00:00", stale: false, new_sources: 0, model: "", boundary: "local" });
    apiFetch.mockImplementation((path: string) => Promise.resolve(path.startsWith("/api/memory/pages")
      ? { pages: [page("what-changed-this-week", "The platform plan changed."), page("what-i-owe", "Send the platform plan.")] }
      : path === "/api/brief/latest" ? brief : {}));
    renderBriefView();
    const history = await screen.findByTestId("brief-since-friday");
    const pages = screen.getAllByTestId("standing-page");
    expect(pages.map((node) => node.getAttribute("aria-label"))).toEqual(["What I owe", "What changed this week"]);
    expect(pages[0].compareDocumentPosition(history) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(history.compareDocumentPosition(screen.getByTestId("brief-this-week")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(screen.getByRole("button", { name: "Standup" }).className).toContain("btn");
    expect(screen.queryByTestId("brief-source-emblem")).toBeNull();
  });
});
