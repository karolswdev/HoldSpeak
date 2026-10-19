// Parked by Betterment daily D5 (Brief and The week retired into Today): cases
// cut from the file named below; they test the retired windows' sections
// (chair/_parked/ArrivalSections.tsx). Not run (vitest excludes _parked).
// From: web/src/desk/chair/arrivalRefresh.test.tsx

/*
  it("holds the Week marker through a retained detail refresh and ignores an old generation", async () => {
    const ids = ["m-refresh-a", "m-refresh-b"];
    const starts = ["2026-10-13T10:00:00Z", "2026-10-13T09:00:00Z"];
    const details = Object.fromEntries(ids.map((id, index) => [id, meetingDetailWire(id, starts[index])]));
    let detailCalls = 0;
    const deferred: Array<() => void> = [];
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
      const value = String(path);
      const detailId = value.match(/^\/api\/meetings\/([^/?]+)$/)?.[1];
      if (detailId) {
        const detail = details[decodeURIComponent(detailId)];
        detailCalls += 1;
        if (detailCalls <= ids.length) return detail as never;
        return new Promise((resolve) => {
          deferred.push(() => resolve(detail));
        }) as never;
      }
      if (value === "/api/door") return { board: {}, upcoming: [], calendar_configured: true } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      return null as never;
    }));
    const meetings = ids
      .map((id, index) => fromWireMeeting(meetingListWire(id, starts[index])))
      .filter((meeting): meeting is NonNullable<typeof meeting> => meeting !== null);
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: meetings }, updatedAt: 1 } as never);
    render(<ChairHome />);

    const line = await screen.findAllByTestId("arrival-meeting-row").then((rows) => rows[0]);
    const row = line.parentElement!;
    await waitFor(() => expect(line).toHaveTextContent("Summary for m-refresh-a"));
    const open = within(row).getByRole("button", { name: "Open" });
    expect(row).not.toHaveAttribute("data-open");
    expect(within(row).queryByRole("button", { name: /Transcript/ })).toBeNull();
    await waitFor(() => expect(screen.queryByTestId("arrival-week-reading")).toBeNull());

    // A desk refresh starts two replacement reads, but the last details stay
    // visible while those reads are pending.
    act(() => { useDesk.setState({ updatedAt: 2 }); });
    await waitFor(() => expect(detailCalls).toBe(4));
    expect(screen.getByTestId("arrival-week-reading")).toBeInTheDocument();
    expect(screen.getAllByTestId("arrival-meeting-row")[0]).toBe(line);
    expect(within(row).getByRole("button", { name: "Open" })).toBe(open);
    expect(line).toHaveTextContent("Summary for m-refresh-a");
    expect(row).not.toHaveAttribute("data-open");

    // Replace that generation before it answers. Completing the stale reads
    // must not lower the pending count for the current generation.
    act(() => { useDesk.setState({ updatedAt: 3 }); });
    await waitFor(() => expect(detailCalls).toBe(6));
    const stale = deferred.splice(0, ids.length);
    const current = deferred.splice(0, ids.length);
    await act(async () => { stale.forEach((release) => release()); });
    expect(screen.getByTestId("arrival-week-reading")).toBeInTheDocument();
    await act(async () => { current[0](); });
    expect(screen.getByTestId("arrival-week-reading")).toBeInTheDocument();
    await act(async () => { current[1](); });
    await waitFor(() => expect(screen.queryByTestId("arrival-week-reading")).toBeNull());
  });
*/
