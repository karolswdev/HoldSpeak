// Parked by Betterment daily D4 (Today is one page): the Brief wing's
// cases from web/src/desk/__tests__/openGrammar.philo1306.test.tsx. The wing
// is parked in web/src/desk/pullouts/_parked/BriefWing.tsx (the PEOPLE
// overlay and the triage verbs). Not run (vitest excludes _parked).

/*
describe("PHILO-13-06: Intelligence BRIEF opens its rows; Brief → People works", () => {
  it("a row opens its decision and names the selection in words, not a raw id", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) =>
      (String(path).startsWith("/api/brief/latest") ? BRIEF : decisionRead(String(path))) as never));
    render(<BriefView header={null} />);
    const row = await screen.findByText("Freeze the old ledger on Nov 5");
    fireEvent.click(row);
    await waitFor(() => expect(openPrimitive).toHaveBeenCalledWith("decision:decision_9458"));
    expect(document.body.textContent).toContain("SELECTED · REVIEW DECISION");
    expect(document.body.textContent).not.toContain("decision_9458");
    expect(screen.getByRole("button", { name: "Acknowledge" })).toBeTruthy();
  });

  it("Open person opens People on that relationship", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) =>
      (String(path).startsWith("/api/brief/latest") ? BRIEF : null) as never));
    render(<BriefView header={null} />);
    fireEvent.click(await screen.findByTestId("person-row-rel-priya"));
    fireEvent.click(screen.getByTestId("verb-open-person"));
    expect(openPrimitive).toHaveBeenCalledWith("people:rel-priya");
    expect(openSurfaceOr).not.toHaveBeenCalledWith("open-people", "/", expect.anything());
  });

  it("a failed read withholds Acknowledge, Defer and Speak (A.11)", async () => {
    vi.mocked(apiFetch).mockImplementation(asHub(async () => {
      throw new ApiError(500, "injected", null);
    }));
    render(<BriefView header={null} />);
    await screen.findByText(/BRIEF DID NOT LOAD/);
    expect(screen.queryByRole("button", { name: "Acknowledge" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Defer" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Speak" })).toBeNull();
    expect(document.body.textContent).not.toContain("injected");
    await act(async () => undefined);
  });
});
*/
