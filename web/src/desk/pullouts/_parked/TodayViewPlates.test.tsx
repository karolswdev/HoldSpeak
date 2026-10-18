// Parked by Betterment daily D4 (Today is one page): the Owed and To decide
// plates left Today; their rows are the top of Needs you. Not run
// (vitest excludes _parked). The cases, verbatim, from
// web/src/desk/pullouts/views/TodayView.test.tsx:

/*
  it("MUST 4: the owed totals are ONE bounded read (the roster with counts), never one read per person", async () => {
    const calls = hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [] }),
      "/api/people/readiness": () => json({ readiness: "ready" }),
      "/api/people/relationships?counts=1": () => json({ relationships: [
        { id: "r1", you_owe_count: 2, owes_you_count: 0 }, { id: "r2", you_owe_count: 1, owes_you_count: 3 },
      ] }),
    });
    render(<TodayView />);
    const owed = await screen.findByTestId("today-owed");
    expect(owed.textContent).toContain("3you owe");
    expect(owed.textContent).toContain("3owed to you");
    expect(calls.filter(([url]) => url.startsWith("/api/people/relationships/"))).toHaveLength(0);
  });

  it("Confirm records the decision: the hub's next read has none, and the plate leaves", async () => {
    // replaces: tests/e2e/test_philo17_today_glass.py::test_confirm_records_the_decision (the face half;
    // the confirm route is tests/unit/test_desk_needs_you.py)
    let open = true;
    const calls = hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: open ? [{ proposalId: "pr1", title: "Freeze the ledger on Nov 12" }] : [] }),
      "/api/proposals/pr1/confirm": () => { open = false; return json({ ok: true }); },
    });
    render(<TodayView />);
    const plate = await screen.findByTestId("today-decide");
    expect(within(plate).getByText("Freeze the ledger on Nov 12")).toBeTruthy();
    fireEvent.click(within(plate).getByRole("button", { name: "Confirm" }));
    await waitFor(() => expect(screen.queryByTestId("today-decide")).toBeNull());
    expect(calls.some(([url, init]) => url === "/api/proposals/pr1/confirm" && init?.method === "POST")).toBe(true);
  });
  // From "draws the next meeting ... the owed and the decision" (the plates):
    const owed = await screen.findByTestId("today-owed");
    await waitFor(() => expect(owed.textContent).toContain("1you owe"));
    expect(owed.textContent).toContain("1owed to you");
    const decide = screen.getByTestId("today-decide");
    fireEvent.click(within(decide).getByRole("button", { name: "Open decision" }));
    expect(takeRoomProposalRequest("p1")).toBe("pr1");
    expect(calls.some(([url, init]) => url.includes("/proposals/") && init?.method === "POST")).toBe(false);
    fireEvent.click(within(decide).getByRole("button", { name: "Confirm" }));
    await waitFor(() => expect(calls.some(([url, init]) => url === "/api/proposals/pr1/confirm" && init?.method === "POST")).toBe(true));

  // From "MUST 3: a refused Confirm and a refused arm" (the Confirm half):
    fireEvent.click(await screen.findByRole("button", { name: "Confirm" }));
    expect(await screen.findByTestId("today-decide-failed")).toHaveTextContent("Not confirmed. Try again");
*/
