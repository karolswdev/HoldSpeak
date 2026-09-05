/** HS-172-05 -- the Prep enrichment: summary rows, cap-at-three +N,
 * absent-at-zero, no pronoun strings (her/him/she/he), wing switch.
 *
 * Co-located vitest for the People 1:1 card brief enrichment.
 */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PeopleCore, prsSummaryLabel, capTokens } from "../PeopleCore";

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function stub(handlers: Record<string, (input: string, opts?: { method?: string; body?: string }) => Response | Promise<Response>>) {
  vi.stubGlobal("fetch", vi.fn(async (input: string, opts?: { method?: string; body?: string }) => {
    const url = String(input);
    // Match the most specific handler first.
    for (const [pattern, handler] of Object.entries(handlers)) {
      if (url === pattern || url.startsWith(pattern)) {
        return handler(input, opts);
      }
    }
    throw new Error(`Unexpected request: ${url}`);
  }));
}

afterEach(() => vi.unstubAllGlobals());

// ── Pure unit tests for helper functions ──

describe("prsSummaryLabel", () => {
  it("includes the name when short enough", () => {
    expect(prsSummaryLabel(2, "Ania")).toBe("2 PRS WAITING ON ANIA");
  });

  it("uses singular PR for count 1", () => {
    expect(prsSummaryLabel(1, "Ania")).toBe("1 PR WAITING ON ANIA");
  });

  it("drops the name when the label is too long", () => {
    const longName = "Aleksandra Magdalena Kowalski";
    const label = prsSummaryLabel(2, longName);
    expect(label).toBe("2 PRS WAITING");
  });

  it("never contains her/him/she/he", () => {
    for (const name of ["Hermione", "Sheila", "Hershey", "Shelby"]) {
      const label = prsSummaryLabel(1, name);
      // The label should NOT contain pronoun words separated by spaces.
      expect(label).not.toMatch(/\b(her|him|she|he)\b/i);
    }
  });
});

describe("capTokens", () => {
  it("returns empty string for empty array", () => {
    expect(capTokens([])).toBe("");
  });

  it("joins up to three tokens", () => {
    expect(capTokens(["#1", "#2", "#3"])).toBe("#1 · #2 · #3");
  });

  it("caps at three then +N", () => {
    expect(capTokens(["#1", "#2", "#3", "#4", "#5"])).toBe("#1 · #2 · #3 +2");
  });

  it("respects custom max", () => {
    expect(capTokens(["a", "b", "c", "d"], 2)).toBe("a · b +2");
  });

  it("single token", () => {
    expect(capTokens(["#612"])).toBe("#612");
  });
});

// ── Integration tests for the Prep lens ──

const WATCH_SUMMARY = {
  prs_waiting: [
    { title: "Fix migration", repo: "karolswdev/holdspeak", pr_number: 612, days_waiting: 5, url: "https://github.com/pr/612", room_id: "p1", room_name: "Platform" },
    { title: "Update types", repo: "karolswdev/holdspeak", pr_number: 618, days_waiting: 2, url: "https://github.com/pr/618", room_id: "p1", room_name: "Platform" },
  ],
  oldest_waiting_days: 5,
  open_assignments: [
    { summary: "PostgreSQL migration", key: "GOV-412", status: "In Progress", url: "https://jira/GOV-412", overdue: true, room_id: "p1", room_name: "Platform" },
  ],
};

const LAST_MEETING = {
  meeting_id: "m1",
  title: "Sprint Review",
  item_count: 5,
  open_count: 2,
};

function makeBrief(overrides: Record<string, unknown> = {}) {
  return {
    relationship_id: "r1",
    display_name: "Ania",
    open_commitments: [
      { id: "c1", body: "API spec", visibility: "shared_intent", state: "open", due: "2020-01-01" },
    ],
    agenda_items: [
      { id: "a1", body: "Discuss API contract timeline", visibility: "shared_intent", state: "open" },
      { id: "a2", body: "Review #612 priority", visibility: "shared_intent", state: "open" },
    ],
    grounding_note_count: 0,
    linked_meetings: [],
    unlinked_meeting_count: 0,
    watch_summary: WATCH_SUMMARY,
    last_meeting: LAST_MEETING,
    ...overrides,
  };
}

function stubWithBrief(briefOverrides: Record<string, unknown> = {}) {
  stub({
    "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
    "/api/people/relationships/r1/brief": () => json({ brief: makeBrief(briefOverrides) }),
    "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
    "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Ania", relationship_kind: "direct_report", calendar_links: [] } }),
    "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Ania", relationship_kind: "direct_report" }] }),
    "/api/door": () => json({ upcoming: [] }),
  });
}

describe("People Prep enrichment HS-172-05", () => {
  it("renders the display step (name) and summary rows", async () => {
    stubWithBrief();
    render(<PeopleCore scope="people:r1:prep" />);
    const lens = await screen.findByTestId("people-prep-lens");
    expect(lens).toBeTruthy();

    // Display step: the name.
    expect(screen.getByTestId("prep-display-name")).toHaveTextContent("Ania");

    // PRS WAITING row.
    const prsRow = screen.getByTestId("prep-prs-row");
    expect(within(prsRow).getByTestId("prep-prs-label")).toHaveTextContent("2 PRS WAITING ON ANIA");
    expect(within(prsRow).getByTestId("prep-prs-days")).toHaveTextContent("5+ DAYS");
    expect(within(prsRow).getByTestId("prep-prs-numbers")).toHaveTextContent("#612 · #618");
    expect(within(prsRow).getByRole("button", { name: "Open" })).toBeTruthy();

    // ASSIGNMENTS row.
    const assignRow = screen.getByTestId("prep-assignments-row");
    expect(within(assignRow).getByTestId("prep-assignments-label")).toHaveTextContent("1 ASSIGNMENT OPEN");
    expect(within(assignRow).getByTestId("prep-assignments-keys")).toHaveTextContent("GOV-412");
    expect(within(assignRow).getByTestId("prep-assignments-overdue")).toHaveTextContent("OVERDUE");

    // COMMITMENTS OVERDUE row.
    const commitRow = screen.getByTestId("prep-commitments-row");
    expect(within(commitRow).getByTestId("prep-commitments-label")).toHaveTextContent("1 COMMITMENT OVERDUE");

    // LAST MEETING row.
    const meetingRow = screen.getByTestId("prep-meeting-row");
    expect(within(meetingRow).getByTestId("prep-meeting-items")).toHaveTextContent("5 ITEMS");
    expect(within(meetingRow).getByTestId("prep-meeting-open-count")).toHaveTextContent("2 OPEN");

    // Footer.
    expect(screen.getByText("THIS DEVICE")).toBeTruthy();
    expect(screen.getByTestId("prep-receipt").textContent).toMatch(/^PREPARED \d{2}:\d{2}$/);
  });

  it("absent-at-zero: no PRS row when zero PRs", async () => {
    stubWithBrief({
      watch_summary: { prs_waiting: [], oldest_waiting_days: 0, open_assignments: [] },
      last_meeting: null,
      open_commitments: [],
    });
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    expect(screen.queryByTestId("prep-prs-row")).toBeNull();
    expect(screen.queryByTestId("prep-assignments-row")).toBeNull();
    expect(screen.queryByTestId("prep-commitments-row")).toBeNull();
    expect(screen.queryByTestId("prep-meeting-row")).toBeNull();
  });

  it("cap-at-three +N for PR numbers", async () => {
    stubWithBrief({
      watch_summary: {
        prs_waiting: [
          { title: "A", repo: "r", pr_number: 1, days_waiting: 1, url: "", room_id: "p", room_name: "P" },
          { title: "B", repo: "r", pr_number: 2, days_waiting: 1, url: "", room_id: "p", room_name: "P" },
          { title: "C", repo: "r", pr_number: 3, days_waiting: 1, url: "", room_id: "p", room_name: "P" },
          { title: "D", repo: "r", pr_number: 4, days_waiting: 1, url: "", room_id: "p", room_name: "P" },
          { title: "E", repo: "r", pr_number: 5, days_waiting: 1, url: "", room_id: "p", room_name: "P" },
        ],
        oldest_waiting_days: 1,
        open_assignments: [],
      },
    });
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    const numbers = screen.getByTestId("prep-prs-numbers");
    expect(numbers.textContent).toBe("#1 · #2 · #3 +2");
  });

  it("no pronoun strings in any summary row text", async () => {
    stubWithBrief();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    const summaryRows = screen.getByTestId("prep-summary-rows");
    const text = summaryRows.textContent || "";
    // No word-boundary pronoun matches.
    expect(text).not.toMatch(/\b(her|him|she|he)\b/i);
  });

  it("warning token on days >= 3", async () => {
    stubWithBrief();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    const daysToken = screen.getByTestId("prep-prs-days");
    expect(daysToken.getAttribute("data-warning")).toBeTruthy();
  });

  it("no warning token when days < 3", async () => {
    stubWithBrief({
      watch_summary: {
        prs_waiting: [
          { title: "A", repo: "r", pr_number: 1, days_waiting: 1, url: "", room_id: "p", room_name: "P" },
        ],
        oldest_waiting_days: 1,
        open_assignments: [],
      },
    });
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    const daysToken = screen.getByTestId("prep-prs-days");
    expect(daysToken.getAttribute("data-warning")).toBeNull();
  });

  it("Open on PRS row switches to Now wing with per-entity PR rows", async () => {
    stubWithBrief();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    // Click Open on the PRS row.
    fireEvent.click(screen.getByTestId("prep-prs-open"));
    // Now wing should show with per-entity PR detail.
    const nowConcern = await screen.findByTestId("people-now-concern");
    expect(nowConcern).toBeTruthy();
    const detail = screen.getByTestId("now-prs-detail");
    expect(detail).toBeTruthy();
    // Each PR should be a row with its own Open.
    expect(screen.getByText(/#612/)).toBeTruthy();
    expect(screen.getByText(/#618/)).toBeTruthy();
    // Now tab should be selected.
    const nowTab = screen.getByRole("tab", { name: "Now" });
    expect(nowTab.getAttribute("aria-selected")).toBe("true");
  });

  it("Open on ASSIGNMENTS row switches to Now with assignment rows", async () => {
    stubWithBrief();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    fireEvent.click(screen.getByTestId("prep-assignments-open"));
    const detail = await screen.findByTestId("now-assignments-detail");
    expect(detail).toBeTruthy();
    expect(screen.getByText(/GOV-412/)).toBeTruthy();
  });

  it("AGENDA section shows items with count", async () => {
    stubWithBrief();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    const agenda = screen.getByTestId("prep-agenda");
    expect(agenda).toBeTruthy();
    expect(agenda.textContent).toContain("Discuss API contract timeline");
    expect(agenda.textContent).toContain("Review #612 priority");
  });

  it("AGENDA section absent when no items", async () => {
    stubWithBrief({ agenda_items: [] });
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    expect(screen.queryByTestId("prep-agenda")).toBeNull();
  });

  it("Open on LAST MEETING renders the meeting Open button", async () => {
    stubWithBrief();
    render(<PeopleCore scope="people:r1:prep" />);
    await screen.findByTestId("people-prep-lens");
    const meetingOpen = screen.getByTestId("prep-meeting-open");
    expect(meetingOpen).toBeTruthy();
    expect(meetingOpen.textContent).toBe("Open");
  });
});
