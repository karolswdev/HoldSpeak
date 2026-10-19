// Parked by Betterment daily D5 (Brief and The week retired into Today): cases
// cut from the file named below; they test the retired windows' sections
// (chair/_parked/ArrivalSections.tsx). Not run (vitest excludes _parked).
// From: web/src/desk/__tests__/openGrammar.philo1306.test.tsx

/*
  it("a brief row opens its decision; a row with nothing to open draws no open", async () => {
    render(<ChairHome />);
    const rows = await screen.findAllByTestId("arrival-brief-row");
    const decision = rows.find((r) => r.textContent?.includes("Freeze the old ledger"))!;
    expect(decision.getAttribute("role")).toBe("button");
    fireEvent.click(decision);
    await waitFor(() => expect(openPrimitive).toHaveBeenCalledWith("decision:decision_9458"));

    const meeting = rows.find((r) => r.textContent?.includes("Ledger cutover sync"))!;
    fireEvent.click(meeting);
    // PHILO-17: the meeting record is inside the Meetings surface.
    expect(openSurfaceOr).toHaveBeenCalledWith(
      "review-meetings", "/history", "meeting:p13-cutover-sync",
    );

    const coverage = rows.find((r) => r.textContent?.includes("Coverage line"))!;
    expect(coverage.getAttribute("role")).toBeNull();
    expect(coverage.getAttribute("tabindex")).toBeNull();
    expect(coverage.hasAttribute("data-inert")).toBe(true);
    vi.mocked(openPrimitive).mockReset();
    vi.mocked(openSurfaceOr).mockReset();
    fireEvent.click(coverage);
    expect(openPrimitive).not.toHaveBeenCalled();
    expect(openSurfaceOr).not.toHaveBeenCalled();
  });

  it("a decision a meeting recorded opens itself in Intelligence (no Desk window exists for it)", async () => {
    const meetingBorn = { id: "bi-mdec", section: "decisions", text: "Review decision: Cursor pagination for every list endpoint", source_ref: "decision:mdec-cursor", priority: 300, created_at: "2026-10-01T07:30:00" };
    chairBrief = { ...BRIEF, sections: { ...BRIEF.sections, decisions: [meetingBorn, ...BRIEF.sections.decisions] } };
    const asked: unknown[] = [];
    const hear = (e: Event) => asked.push((e as CustomEvent).detail);
    window.addEventListener("holdspeak:intelligence-navigate", hear);
    try {
      render(<ChairHome />);
      const rows = await screen.findAllByTestId("arrival-brief-row");
      fireEvent.click(rows.find((r) => r.textContent?.includes("Cursor pagination"))!);
      await waitFor(() => expect(asked).toEqual([expect.objectContaining({ view: "receipts", decisionId: "mdec-cursor" })]));
      expect(openSurfaceOr).not.toHaveBeenCalledWith("review-meetings", "/history", "meeting:p13-api-review");
      expect(openPrimitive).not.toHaveBeenCalled();
    } finally {
      window.removeEventListener("holdspeak:intelligence-navigate", hear);
    }
  });

  it("Ack on a brief row triages only; it does not open the row", async () => {
    render(<ChairHome />);
    const rows = await screen.findAllByTestId("arrival-brief-row");
    const decision = rows.find((r) => r.textContent?.includes("Freeze the old ledger"))!;
    fireEvent.click(within(decision).getByRole("button", { name: "Ack" }));
    expect(openPrimitive).not.toHaveBeenCalled();
  });

  it("a calendar row opens its person at Prep, else its Project's Room, else nothing", async () => {
    useDrawers.setState({ drawers: [], infos: [] });
    render(<ChairHome />);
    const rows = await screen.findAllByTestId("arrival-meeting-row");
    const oneOnOne = rows.find((r) => r.textContent?.includes("1:1 Priya"))!;
    fireEvent.click(oneOnOne);
    // PHILO-17 (2b): THAT person, in her own window, on Prep.
    expect(openPrimitive).toHaveBeenCalledWith("people:rel-priya");
    expect(takePersonLens("rel-priya")).toBe("prep");

    const sync = rows.find((r) => r.textContent?.includes("Ledger cutover sync"))!;
    fireEvent.click(sync);
    // PHILO-17 U30: a Project opens its Room (one home), never a drawer.
    expect(openProjectRoom).toHaveBeenCalledWith("proj-ledger");
    expect(useDrawers.getState().drawers).toEqual([]);

    // Unlink beside the ROOM token is its own verb, never the row's open.
    vi.mocked(openProjectRoom).mockReset();
    fireEvent.click(within(sync).getByTestId("arrival-unlink-room"));
    expect(openProjectRoom).not.toHaveBeenCalled();

    const arch = rows.find((r) => r.textContent?.includes("Architecture review"))!;
    expect(arch.hasAttribute("data-inert")).toBe(true);
    expect(arch.getAttribute("role")).toBeNull();
  });
*/
