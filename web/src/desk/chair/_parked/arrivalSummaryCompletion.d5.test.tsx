// Parked by Betterment daily D5 (Brief and The week retired into Today): cases
// cut from the file named below; they test the retired windows' sections
// (chair/_parked/ArrivalSections.tsx). Not run (vitest excludes _parked).
// From: web/src/desk/chair/arrivalSummaryCompletion.test.tsx

/*
  it("renders imported duration and transcript from the producer detail", async () => {
    const imported = caseFor("imported_off");
    commonWire([imported]);
    seat(imported);
    render(<ChairHome />);

    expect(await screen.findByText("35 S")).toBeInTheDocument();
    expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent("16 WORDS");
    expect(screen.queryAllByText("We will ship the boundary change on Tuesday.")).toHaveLength(0);
    expect(screen.getByTestId("arrival-route")).not.toHaveTextContent("THIS DEVICE");
    expect(screen.getByTestId("arrival-run-intel")).toBeInTheDocument();
    expect(screen.queryByTestId("meeting-summary-text")).toBeNull();
  });

  it("renders the ready summary and transcript from the producer detail", async () => {
    const ready = caseFor("success");
    commonWire([ready]);
    seat(ready);
    render(<ChairHome />);

    const row = await screen.findByTestId("arrival-meeting-row");
    await waitFor(() => expect(row).toHaveTextContent("The team reviewed the budget."));
    expect(screen.getByTestId("arrival-attempts")).not.toHaveTextContent("THIS DEVICE");
    expect(row).toHaveTextContent("16 WORDS");
    expect(row.parentElement).not.toHaveAttribute("data-open");
    expect(screen.queryByRole("button", { name: /Transcript/ })).toBeNull();
    expect(screen.queryByTestId("meeting-summary-text")).toBeNull();
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
    expect(within(row).getByRole("button", { name: "Open" })).toBeInTheDocument();
  });

  it("keeps a failed lineage as RETRYING after its scheduled time and names the producer cause", async () => {
    const retry = caseFor("retry");
    commonWire([retry]);
    seat(retry);
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RETRYING"));
    expect(screen.getByTestId("arrival-display")).toHaveTextContent("1 needs you");
    expect(screen.getByTestId("arrival-attempts")).toBeInTheDocument();
    expectProducerCause(retry);
    expect(screen.queryByText("Nothing needs you")).toBeNull();
  });

  it("renders the terminal producer failure and keeps the named cause", async () => {
    const failed = caseFor("terminal_failure");
    commonWire([failed]);
    seat(failed);
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("FAILED"));
    expect(screen.getByTestId("arrival-attempts")).toBeInTheDocument();
    expectProducerCause(failed);
    expect(screen.getByTestId("arrival-display")).toHaveTextContent("1 needs you");
    expect(screen.queryByText("Nothing needs you")).toBeNull();
  });

  it("keeps a persisted summary visible with a later producer failure", async () => {
    const ready = caseFor("success");
    const failed = caseFor("terminal_failure");
    const mixed = {
      ...failed,
      detail: { ...failed.detail, intel: ready.detail.intel },
      list: { ...failed.list, intel_status: "error" },
    } as SummaryCase;
    commonWire([mixed]);
    seat(mixed);
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent("The team reviewed the budget."));
    expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("FAILED");
    expectProducerCause(mixed);
    expect(screen.getByTestId("arrival-attempts")).not.toHaveTextContent("THIS DEVICE");
    expect(screen.queryByTestId("meeting-summary-text")).toBeNull();
    expect(screen.getByTestId("arrival-meeting-row").parentElement).not.toHaveAttribute("data-open");
  });

  it("reads only the top three visible meeting details per desk refresh", async () => {
    const candidates = summaryWire.cases
      .slice(0, 4)
      .map((candidate, index) =>
        withTestIdentity(candidate, `${candidate.detail.id}-${candidate.state}-${index}`),
      );
    commonWire(candidates);
    seat(...candidates);
    render(<ChairHome />);

    await waitFor(() => expect(detailCalls()).toHaveLength(3));
    expect(new Set(detailCalls()).size).toBe(3);
    const expected = [...candidates]
      .sort((a, b) => new Date(String(b.list.started_at)).getTime() - new Date(String(a.list.started_at)).getTime())
      .slice(0, 3)
      .map((candidate) => `/api/meetings/${candidate.detail.id}`);
    expect(new Set(detailCalls())).toEqual(new Set(expected));
  });

  it("drops a stale response when the visible meeting identity changes", async () => {
    const ready = withTestIdentity(caseFor("success"), "m-summary-ready");
    const running = withTestIdentity(caseFor("running"), "m-summary-running");
    let resolveFirst!: (value: unknown) => void;
    const first = new Promise((resolve) => { resolveFirst = resolve; });
    commonWire([ready, running]);
    mockedApiFetch.mockImplementation(asHub(async (path: string) => {
      const value = String(path);
      if (value === `/api/meetings/${ready.detail.id}`) return first as never;
      if (value === `/api/meetings/${running.detail.id}`) return running.detail as never;
      if (value.startsWith("/api/meetings?")) return { meetings: [] } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      if (value === "/api/door") return { board: {}, upcoming: [] } as never;
      return null as never;
    }));
    seat(ready);
    render(<ChairHome />);
    seat(running);

    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RUNNING"));
    expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent("16 WORDS");
    resolveFirst(ready.detail);
    await waitFor(() => expect(screen.queryByText("The team reviewed the budget.")).toBeNull());
    expect(screen.queryByText("MEETING DETAIL IDENTITY CHANGED")).toBeNull();
  });

  it("keeps the closed summary excerpt through an unresolved desk refresh", async () => {
    const ready = withTestIdentity(caseFor("success"), "m-refresh-stable");
    const refreshed = {
      ...ready,
      detail: {
        ...ready.detail,
        intel: { ...ready.detail.intel, summary: "The team reviewed the launch." },
      },
    } as SummaryCase;
    let detailReads = 0;
    let resolveRefresh!: (value: unknown) => void;
    const pendingRefresh = new Promise((resolve) => { resolveRefresh = resolve; });
    mockedApiFetch.mockImplementation(asHub(async (path: string) => {
      const value = String(path);
      if (value === `/api/meetings/${ready.detail.id}`) {
        detailReads += 1;
        return detailReads === 1 ? ready.detail as never : pendingRefresh as never;
      }
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) {
        return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      }
      if (value === "/api/door") return { board: {}, upcoming: [] } as never;
      return null as never;
    }));
    seat(ready);
    render(<ChairHome />);

    await waitFor(() => expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent("The team reviewed the budget."));
    expect(screen.queryByRole("button", { name: /Transcript/ })).toBeNull();
    expect(screen.queryAllByText("We will ship the boundary change on Tuesday.")).toHaveLength(0);

    const updatedAt = Number(useDesk.getState().updatedAt ?? 0) + 1;
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [meetingFor(refreshed)] },
      updatedAt,
    } as never);
    await waitFor(() => expect(detailReads).toBe(2));
    expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent("The team reviewed the budget.");
    expect(screen.getByTestId("arrival-meeting-row").parentElement).not.toHaveAttribute("data-open");
    expect(screen.queryAllByText("We will ship the boundary change on Tuesday.")).toHaveLength(0);

    resolveRefresh(refreshed.detail);
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent("The team reviewed the launch."));
    expect(screen.getByTestId("arrival-meeting-row").parentElement).not.toHaveAttribute("data-open");
    expect(screen.queryByTestId("meeting-send-well")).toBeNull();
  });

  it("names a response whose identity does not match the requested meeting", async () => {
    const ready = withTestIdentity(caseFor("success"), "m-summary-expected");
    const running = withTestIdentity(caseFor("running"), "m-summary-reply");
    commonWire([ready, running]);
    mockedApiFetch.mockImplementation(asHub(async (path: string) => {
      const value = String(path);
      if (value === `/api/meetings/${ready.detail.id}`) return running.detail as never;
      if (value.startsWith("/api/meetings?")) return { meetings: [] } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      if (value === "/api/door") return { board: {}, upcoming: [] } as never;
      return null as never;
    }));
    seat(ready);
    render(<ChairHome />);

    expect(await screen.findByTestId("arrival-detail-error")).toHaveTextContent("SUMMARY READ FAILED");
    expect(screen.queryByTestId("arrival-detail-retained")).toBeNull();
    expect(screen.queryByText(ready.detail.id)).toBeNull();
    expect(screen.queryByText(running.detail.id)).toBeNull();
    const retainedRow = screen.getByTestId("arrival-meeting-row");
    expect(retainedRow).toHaveTextContent(ready.detail.title);
    const open = within(retainedRow).getByRole("button", { name: /^Open$/ });
    expect(open).toBeEnabled();
    expect(open).toHaveClass("btn");
  });

  it("clicks Run once, then follows desk_changed to a ready summary and durable receipt", async () => {
    const snapshots = [
      withTestIdentity(caseFor("imported_off"), "m-run-success"),
      withTestIdentity(caseFor("running"), "m-run-success"),
      withTestIdentity(caseFor("success"), "m-run-success"),
    ];
    let currentSnapshot = 0;
    commonWire(snapshots);
    const defaultFetch = mockedApiFetch.getMockImplementation()!;
    mockedApiFetch.mockImplementation(asHub(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value === "/api/meetings/m-run-success") {
        return snapshots[currentSnapshot].detail as never;
      }
      if (value.endsWith("/intelligence/run")) {
        return {
          job_id: "ij-run-success",
          state: "queued",
          drainer: "running",
          run_receipt: null,
        } as never;
      }
      return defaultFetch(path, init as never) as never;
    }));
    const refresh = vi.fn(async () => {
      currentSnapshot = Math.min(currentSnapshot + 1, snapshots.length - 1);
      const snapshot = snapshots[currentSnapshot];
      useDesk.setState({
        items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshot)] },
        updatedAt: Date.now(),
        refresh,
      } as never);
    });
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[0])] },
      updatedAt: Date.now(),
      refresh,
    } as never);
    render(
      <>
        <DeskChangedRefresh />
        <ChairHome />
      </>,
    );

    const run = await screen.findByTestId("arrival-run-intel");
    fireEvent.click(run);
    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalledWith(
      "/api/meetings/m-run-success/intelligence/run",
      { method: "POST", json: { expected_selection_hash: snapshots[0].list.planned_route.selection_hash } },
    ));
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RUNNING"));

    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent(
      "The team reviewed the budget.",
    ));
    expect(
      within(screen.getByTestId("arrival-meeting-row")).getByRole("button", {
        name: /^Open$/,
      }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("arrival-attempts")).not.toHaveTextContent("THIS DEVICE");
    expect(screen.queryAllByTestId("arrival-run-intel")).toHaveLength(0);
    expect(mockedApiFetch.mock.calls.filter(([path]) => String(path).endsWith("/intelligence/run"))).toHaveLength(1);
  });

  it("keeps the durable receipt and producer cause through retry to terminal failure", async () => {
    const snapshots = [
      withTestIdentity(caseFor("imported_off"), "m-run-failure"),
      withTestIdentity(caseFor("retry"), "m-run-failure"),
      withTestIdentity(caseFor("terminal_failure"), "m-run-failure"),
    ];
    let currentSnapshot = 0;
    commonWire(snapshots);
    const defaultFetch = mockedApiFetch.getMockImplementation()!;
    mockedApiFetch.mockImplementation(asHub(async (path: string, init?: unknown) => {
      const value = String(path);
      if (value === "/api/meetings/m-run-failure") {
        return snapshots[currentSnapshot].detail as never;
      }
      // PHILO-13-03: the Chair's R3 is the needs-you module's bounded
      // `summary_attention` read; the hub answers the meeting as it is now
      // (one row), never every lifecycle snapshot at once.
      if (value.startsWith("/api/meetings?summary_attention=true")) {
        return { meetings: [snapshots[currentSnapshot].list], total: 1 } as never;
      }
      // The Room rows of this hub (none); `asHub` composes the answer from
      // the sources of THIS mock, not from the default wire's.
      if (value.startsWith("/api/desk/needs-you")) {
        return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      }
      if (value.endsWith("/intelligence/run")) {
        return {
          job_id: "ij-run-failure",
          state: "queued",
          drainer: "running",
          run_receipt: null,
        } as never;
      }
      return defaultFetch(path, init as never) as never;
    }));
    const refresh = vi.fn(async () => {
      currentSnapshot = Math.min(currentSnapshot + 1, snapshots.length - 1);
      const snapshot = snapshots[currentSnapshot];
      useDesk.setState({
        items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshot)] },
        updatedAt: Date.now(),
        refresh,
      } as never);
    });
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[0])] },
      updatedAt: Date.now(),
      refresh,
    } as never);
    render(
      <>
        <DeskChangedRefresh />
        <ChairHome />
      </>,
    );

    fireEvent.click(await screen.findByTestId("arrival-run-intel"));
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RETRYING"));
    expect(screen.getByTestId("arrival-attempts")).not.toHaveTextContent("THIS DEVICE");
    expectProducerCause(snapshots[1]);

    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("FAILED"));
    expect(screen.getByTestId("arrival-attempts")).not.toHaveTextContent("THIS DEVICE");
    expectProducerCause(snapshots[2]);
    // PHILO-13-03: the head is the one needs-you snapshot, which re-reads on
    // the same debounced desk_changed frame; it follows within the wait.
    await waitFor(() => expect(screen.getByTestId("arrival-display")).toHaveTextContent("1 needs you"));
    expect(screen.queryAllByTestId("arrival-run-intel")).toHaveLength(0);
    expect(mockedApiFetch.mock.calls.filter(([path]) => String(path).endsWith("/intelligence/run"))).toHaveLength(1);
  });

  it("refreshes running to ready to retry to failed from desk_changed and keeps durable receipts", async () => {
    const snapshots = [
      caseFor("running"),
      caseFor("success"),
      caseFor("retry"),
      caseFor("terminal_failure"),
    ].map((candidate) => ({
      ...candidate,
      list: { ...candidate.list, id: "m-transition" },
      detail: { ...candidate.detail, id: "m-transition" },
    })) as SummaryCase[];
    let current = 0;
    const detailPaths: string[] = [];
    mockedApiFetch.mockImplementation(asHub(async (path: string) => {
      const value = String(path);
      if (value === "/api/meetings/m-transition") {
        detailPaths.push(value);
        return snapshots[current].detail as never;
      }
      if (value.startsWith("/api/meetings?")) return { meetings: [snapshots[current].list] } as never;
      if (value === "/api/inference/assignments") return { rows: [], task_overrides: [], issue_count: 0 } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
      if (value === "/api/door") return { board: {}, upcoming: [] } as never;
      return null as never;
    }));
    const refresh = vi.fn(async () => {
      useDesk.setState({
        items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[current])] },
        updatedAt: Date.now(),
      } as never);
    });
    useDesk.setState({
      items: { ...EMPTY_ITEMS, meeting: [meetingFor(snapshots[0])] },
      updatedAt: Date.now(),
      refresh,
    } as never);
    render(
      <>
        <DeskChangedRefresh />
        <ChairHome />
      </>,
    );
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RUNNING"));

    current = 1;
    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(1), { timeout: 1000 });
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-row")).toHaveTextContent("The team reviewed the budget."));
    expect(screen.getByTestId("arrival-attempts")).not.toHaveTextContent("THIS DEVICE");

    current = 2;
    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(2), { timeout: 1000 });
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("RETRYING"));
    expect(screen.getByTestId("arrival-attempts")).toBeInTheDocument();
    expectProducerCause(snapshots[current]);

    current = 3;
    emitRuntime("desk_changed");
    await waitFor(() => expect(refresh).toHaveBeenCalledTimes(3), { timeout: 1000 });
    await waitFor(() => expect(screen.getByTestId("arrival-meeting-badge")).toHaveTextContent("FAILED"));
    expect(screen.getByTestId("arrival-attempts")).toBeInTheDocument();
    expectProducerCause(snapshots[current]);
    expect(detailPaths).toHaveLength(4);
  });
*/
