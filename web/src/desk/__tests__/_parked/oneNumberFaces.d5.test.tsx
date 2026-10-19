// Parked by Betterment daily D5 (Brief and The week retired into Today): cases
// cut from the file named below; they test the retired windows' sections
// (chair/_parked/ArrivalSections.tsx). Not run (vitest excludes _parked).
// From: web/src/desk/__tests__/oneNumberFaces.test.tsx

/*
  it("the Chair's Brief caption says the hub's count, not the Brief's own rows", async () => {
    const hub = desk.needsYou as Json;
    await act(async () => {
      render(<ChairHome />);
    });
    const section = await screen.findByTestId("arrival-brief");
    await waitFor(() =>
      expect(within(section).getByRole("heading").textContent).toBe(`BRIEF · ${hub.count} THINGS WAITING`));
    // The Brief's own open rows are a different list (changed and broke rows
    // too); the caption does not count them.
    const shown = within(section).getAllByTestId("arrival-brief-row").length;
    const folded = Number(
      within(section).queryByTestId("arrival-brief-more")?.textContent?.match(/^(\d+) more$/)?.[1] ?? 0,
    );
    expect(shown + folded).not.toBe(hub.count);
  });
*/
