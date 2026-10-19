// Parked by Betterment daily D5 (Brief and The week retired into Today): cases
// cut from the file named below; they test the retired windows' sections
// (chair/_parked/ArrivalSections.tsx). Not run (vitest excludes _parked).
// From: web/src/desk/chair/__tests__/importFailedBadge.philo601.test.tsx

/*
  it("the Arrival row of the producer's failed import shows the FAILED badge", async () => {
    const meeting = fromWireMeeting(wire.list_row);
    expect(meeting).not.toBeNull();
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [meeting] } as never });
    render(<ChairHome />);
    const badge = await screen.findByTestId("arrival-meeting-badge");
    await waitFor(() => expect(badge.textContent).toBe("FAILED"));
    expect(badge.getAttribute("data-badge")).toBe("failed");
    expect(screen.getByTestId("arrival-meeting-row").textContent).not.toContain("SAVED");
  });
*/
