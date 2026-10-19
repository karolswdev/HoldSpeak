// Parked by Betterment daily D5 (Brief and The week retired into Today): cases
// cut from web/src/desk/chair/__tests__/chairWindows.philo1311.test.tsx that
// test the retired windows' content (the week's meeting ledger, its NO
// CALENDAR row and decisions, the Brief's dated title). Sections:
// chair/_parked/ArrivalSections.tsx. Not run (vitest excludes _parked).

/*
  it("no Run summary beside SUMMARY STORED (the stored fact drives the verb)", async () => {
    useDesk.setState({
      items: {
        meeting: [{
          kind: "meeting", id: "m-1", title: "Census standup",
          startedAt: "2026-09-19T09:00:00Z", endedAt: "2026-09-19T09:30:00Z",
          durationSeconds: 1800, intelStatus: "disabled", transcriptWords: 1204,
          hasSummary: true, plannedRoute: ROUTE, runReceipt: null,
        }],
      } as never,
    });
    render(<ChairHome />);
    const row = await screen.findByTestId("arrival-meeting-row");
    expect(within(row).getByTestId("arrival-meeting-badge").textContent).toBe("SUMMARY STORED");
    expect(within(row).queryByTestId("arrival-run-intel")).toBeNull();
    expect(within(row).getByRole("button", { name: "Open" })).toBeTruthy();
  });

  it("the ledger row: SUMMARY STORED from the detail read had a Run summary beside it", async () => {
    useDesk.setState({
      items: {
        meeting: [{
          kind: "meeting", id: "m-2", title: "Ledger cutover sync",
          startedAt: "2026-09-19T09:00:00Z", endedAt: "2026-09-19T09:30:00Z",
          durationSeconds: 1800, intelStatus: "disabled", transcriptWords: 40,
          plannedRoute: ROUTE, runReceipt: null,
        }],
      } as never,
    });
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string, init?: unknown) => {
      if (String(path) === "/api/meetings/m-2")
        return {
          id: "m-2", title: "Ledger cutover sync", started_at: "2026-09-19T09:00:00Z",
          ended_at: "2026-09-19T09:30:00Z", duration_seconds: 1800, intel_status: "disabled",
          transcriptWords: 40, planned_route: ROUTE,
          intel: { summary: "Dual-write is stable.", topics: [] },
          segments: [{ text: "Dual-write is stable.", speaker: "Me", start_time: 1 }],
        };
      return (base as (p: string, i?: unknown) => Promise<unknown>)(path, init);
    }));
    render(<ChairHome />);
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge").textContent).toBe("SUMMARY STORED"));
    const row = screen.getByTestId("arrival-meeting-row");
    expect(row).toHaveTextContent("Dual-write is stable.");
    expect(row.closest("li")).not.toHaveAttribute("data-open");
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
    expect(within(row).queryByTestId("arrival-run-intel")).toBeNull();
    expect(within(row).getByRole("button", { name: "Open" })).toBeTruthy();
  });

  it("a fresh desk with no calendar: one NO CALENDAR row with Connect", async () => {
    render(<ChairHome />);
    const week = await screen.findByRole("region", { name: "The week" });
    const row = await within(week).findByTestId("week-no-calendar");
    expect(row.textContent).toContain("NO CALENDAR");
    expect(within(row).getByRole("button", { name: "Connect calendar" }).textContent).toBe("Connect");
    expect(within(week).getByTestId("chair-window-body-week").children.length).toBeGreaterThan(0);
  });

  it("lists this week's decisions and the action items due by its end", async () => {
    const now = new Date();
    const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
    useDesk.setState({
      items: {
        meeting: [],
        decision: [{
          kind: "decision", id: "decision_sqlite", title: "Use SQLite for the local meeting ledger",
          status: "accepted", deciders: [], contextMarkdown: "", decisionMarkdown: "", alternatives: [],
          consequencesMarkdown: "", tags: [], createdAt: now.toISOString(),
        }],
      } as never,
    });
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      const p = String(path);
      if (p.startsWith("/api/desk/needs-you")) return NEEDS;
      if (p.startsWith("/api/door")) return {
        board: { now: [{ id: "ai-plan", source: "action_item", target_ref: "action_item:ai-plan", title: "Write the migration plan", due: today }] },
        counts: {}, upcoming: [], calendar_configured: false,
      };
      return null;
    }));
    render(<ChairHome />);
    const week = await screen.findByRole("region", { name: "The week" });
    const decision = await within(week).findByTestId("week-decision-row");
    expect(decision.textContent).toContain("Use SQLite for the local meeting ledger");
    expect(decision.textContent).toContain("DECIDED");
    const due = await within(week).findByTestId("week-due-row");
    expect(due.textContent).toContain("Write the migration plan");
    expect(within(week).getByTestId("week-no-calendar")).toBeTruthy();
  });

  it("renders `Brief · Wednesday 7 Oct 2026` in the title bar", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      const p = String(path);
      if (p.startsWith("/api/desk/needs-you")) return NEEDS;
      if (p.startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
      if (p === "/api/brief/latest") return {
        id: "brief-1", headline: "No changes", sections: {}, is_empty: true,
        generated_at: "2026-10-07T10:50:00-06:00", period_label: "OCT 06-07",
        title: "Brief · Wednesday 7 Oct 2026",
      };
      return null;
    }));
    render(<ChairHome />);
    const win = await screen.findByRole("region", { name: "Brief" });
    await waitFor(() =>
      expect(win.querySelector(".desk-window-title")?.textContent).toBe("Brief · Wednesday 7 Oct 2026"));
  });

describe("PHILO-15-09 B07 — The week is never empty", () => {

});

describe("PHILO-15-09 B04 — the Brief window title is dated", () => {
});
*/
