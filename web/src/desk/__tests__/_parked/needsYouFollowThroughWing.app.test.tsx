// Parked by Betterment daily D4: the Follow-through wing's case from
// web/src/desk/__tests__/needsYou.app.test.tsx. Not run.

/*
  it("Review's destination: Follow-through opens ON that card, its verbs showing", async () => {
    // replaces: tests/e2e/test_chair_review_verb_glass.py::test_review_opens_the_card_in_follow_through
    // (the press dispatching { view: "follow-through", followThroughId } is
    // arrivalAttention.test.tsx "an owned item not reviewed yet reads TO REVIEW, and Review opens it".)
    const board = {
      now: [], waiting: [], overdue: [],
      unassigned: [producerCard("ai-owned", OWNED, "Priya"), producerCard("ai-other", "Book the room", null)],
    };
    // The hub's own answers for the Today view's reads too: a null meetings
    // read is a lie the hub never tells, and Today's load threw on it after
    // the test ended (an unhandled rejection under load).
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      const value = String(path);
      if (value.split("?", 1)[0] === "/api/follow-through/board") return board as never;
      if (value.startsWith("/api/meetings")) return { meetings: [] } as never;
      if (value.startsWith("/api/desk/needs-you")) return { count: 0, projects: [], items: [], next: null, coverage: [], complete: true } as never;
      return null as never;
    });
    const openPullout = vi.fn();
    const realOpen = useDesk.getState().openPullout;
    useDesk.setState({ openPullout } as never);
    try {
      render(<IntelligencePullout object={{ kind: "intelligence", id: "desk", title: "Intelligence",
        ref: { kind: "intelligence", id: "desk", name: "Intelligence" } } as never} onClose={() => {}} />);
      expect(screen.queryByLabelText(`Verbs for ${OWNED}`)).toBeNull();
      act(() => openIntelligence({ view: "follow-through", followThroughId: "ai-owned" }));
      expect(openPullout).toHaveBeenCalledWith("intelligence:desk");
      const verbs = await screen.findByLabelText(`Verbs for ${OWNED}`);
      expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/board?focus_id=ai-owned");
      const task = screen.getByText(OWNED).closest(".surface-ledger-row") as HTMLElement;
      expect(within(task).getByRole("button", { name: "Mark done" })).toBeTruthy();
      expect(within(task).getByRole("button", { name: `Details for ${OWNED}` })).toHaveAttribute("aria-expanded", "true");
      expect(within(verbs).getByRole("button", { name: "Assign" })).toBeTruthy();
      // Only that card is open.
      expect(screen.queryByLabelText("Verbs for Book the room")).toBeNull();
    } finally {
      useDesk.setState({ openPullout: realOpen } as never);
    }
  });*/
