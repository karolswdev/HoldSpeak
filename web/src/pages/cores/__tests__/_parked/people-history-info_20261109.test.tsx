// Parked: History and Info disclosure pages retired; facts are in the mast.
  it("History shows no zero counters and Info hides fields that are not set", async () => {
    spy({
      "/api/people/readiness": () => json({ readiness: "ready", store: "encrypted" }),
      "/api/people/relationships": () => json({ relationships: [{ id: "r1", display_name: "Maya Chen", relationship_kind: "direct_report" }] }),
      "/api/people/relationships/r1": () => json({ relationship: { id: "r1", display_name: "Maya Chen", relationship_kind: "direct_report", commitments: [] } }),
      "/api/people/relationships/r1/one-on-ones": () => json({ one_on_ones: [] }),
      "/api/people/relationships/r1/brief": () => json({ brief: { relationship_id: "r1", open_commitments: [], agenda_items: [] } }),
      "/api/door": () => json({ upcoming: [] }),
    });
    render(<PeopleCore scope="people:r1" />);
    fireEvent.click(await screen.findByRole("button", { name: "History" }));
    expect(screen.queryByTestId("people-history-facts")).toBeNull();
    expect(document.body.textContent).not.toContain("—");
    fireEvent.click(screen.getByRole("button", { name: "Info" }));
    expect(screen.queryByText("Role context")).toBeNull();
    expect(screen.queryByText("Not set")).toBeNull();
  });
