/* PARKED by R1 "the brief" (owner 2026-11-08: the Room's Now face "looks
 * like shit"): these room.app.test.tsx cases read faces that left the Now
 * face. UN-PARKED 2026-11-08 (the language): the five Prepare cases run
 * again from History's `Prepare a brief` (room.app.test.tsx, "Prepare a
 * brief lives in History") and the standing-pages case from History's Pages
 * row (desk/__tests__/memory.app.test.tsx). Still parked:
 * This week's Decided lines and their Committed word; the "Update" chips
 * line (core/UpdateLine.tsx, parked in ../UpdateLine.tsx); the Programs
 * fold (parked in ../roomProgramsFold.tsx). Their successors in
 * room.app.test.tsx: "R1: the Now face is the brief". Not collected
 * (vite.config.ts excludes _parked). Each block is as it stood in
 * room.app.test.tsx at origin/main 668ba266d; its constants (PREP_*, PREP2_*,
 * P7, COMMITTED, P13, roomProgramsFixture) are that file's. */

describe("#1891: a committed decision names its Person on the Decided line", () => {
  const pid = (COMMITTED.room as { project_id: string }).project_id;
  const table = (): Record<string, Answer> => ({
    [room(pid)]: () => clone(COMMITTED.room),
    [`GET /api/projects/${pid}/proposals`]: () => clone(COMMITTED.proposals),
  });

  it("draws Committed · <name> at the committed line's right, and nothing on the other", async () => {
    wire(table());
    render(<WindowHarness scope={`project:${pid}`} />);
    const week = await screen.findByTestId("room-this-week");
    const lines = within(week).getAllByTestId("this-week-line");
    const committed = lines.find((l) => l.textContent?.includes("Adopt quorumdb"))!;
    const quiet = lines.find((l) => l.textContent?.includes("Keep the nightly export"))!;
    const word = within(committed).getByTestId("this-week-committed");
    expect(word.textContent).toBe("Committed · Mira Okafor");
    expect(committed.lastElementChild).toBe(word);
    expect(within(quiet).queryByTestId("this-week-committed")).toBeNull();
    expect(quiet.textContent).not.toContain("Committed");
  });
});

describe("P7: the project update automation line", () => {
  const pid = P7.manual.project_id;
  const automation = P7.manual.updates.automation!;

  it("keeps manual state after a refused Friday press, then retries the same automation", async () => {
    let enabled = false;
    let refused = true;
    wire({
      [room(pid)]: () => clone(enabled ? P7.scheduled : P7.manual),
      [`PUT /api/workbenches/${automation.id}`]: () => {
        if (refused) throw new ApiError(400, P7.refusal.error, clone(P7.refusal));
        enabled = true;
        return clone(P7.friday);
      },
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    const line = await screen.findByTestId("room-update-line");
    expect(within(line).getByTestId("room-update-with")).toHaveTextContent(automation.engine_label);
    fireEvent.click(within(line).getByTestId("room-update-friday"));
    await within(line).findByText(P7.refusal.error);
    expect(within(line).getByTestId("room-update-when")).toHaveTextContent("Only when pressed");
    refused = false;
    fireEvent.click(within(line).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(within(line).getByTestId("room-update-when")).toHaveTextContent("Fridays 15:00"));
    expect(within(line).getByTestId("room-update-with")).toHaveTextContent(P7.scheduled.updates.automation!.engine_label);
    expect(calls.filter((call) => call.key === `PUT /api/workbenches/${automation.id}`)).toEqual([
      { key: `PUT /api/workbenches/${automation.id}`, json: { schedule: "0 15 * * 5", schedule_enabled: true } },
      { key: `PUT /api/workbenches/${automation.id}`, json: { schedule: "0 15 * * 5", schedule_enabled: true } },
    ]);
  });

  it("opens the exact newest stored update from the line", async () => {
    const { plainUpdateText } = await import("../update/model");
    const result = P7.completed.updates.automation.latest_result;
    let read = false;
    wire({
      [room(pid)]: () => clone(read ? P7.read : P7.completed),
      [`GET /api/updates/${result.update_id}`]: () => clone(P7.delivered),
      [`POST /api/workbenches/${automation.id}/results/${result.artifact_id}/open`]: () => {
        read = true;
        return clone(P7.opened);
      },
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    const line = await screen.findByTestId("room-update-line");
    expect(within(line).getByTestId("room-update-new")).toHaveTextContent("New");
    fireEvent.click(within(line).getByTestId("room-update-open"));
    await screen.findByTestId("update-editor");
    expect(screen.getByLabelText("Update body")).toHaveValue(plainUpdateText(P7.delivered.update.body_md));
    await waitFor(() => expect(within(line).queryByText("NEW")).not.toBeInTheDocument());
    expect(calls).toContainEqual({ key: `GET /api/updates/${result.update_id}` });
    expect(calls).toContainEqual({
      key: `POST /api/workbenches/${automation.id}/results/${result.artifact_id}/open`,
      json: undefined,
    });
  });
});

describe("Room fold 2026-11-08: the Programs fold is always on the Now tab", () => {
  const hand = P13.creationHandoff;
  const projectA = P13.projects.a;
  const made = hand.create.response.body as { id: string };
  // The Room read with the recorded Programs section that has step dots.
  const withDots = { ...clone(hand.roomAfter), programs: clone(roomProgramsFixture) };

  /** The fold draws: neither it nor a parent is display: none (the project
   *  CSS is loaded; vitest `css: true`). */
  const drawn = (el: Element) => {
    for (let node: Element | null = el; node; node = node.parentElement) {
      if (getComputedStyle(node).display === "none") return false;
    }
    return true;
  };

  beforeEach(() => {
    useDesk.setState({ pullouts: [] });
  });

  it("a project with Programs: the fold is drawn and open, rows carry the step dots, a press opens the Program", async () => {
    wire({ [room(projectA)]: () => clone(withDots) });
    render(<WindowHarness scope={`project:${projectA}`} />);
    const fold = await screen.findByTestId("room-fold-programs");
    expect(drawn(fold)).toBe(true);
    const details = fold.querySelector("details")!;
    expect(details.open).toBe(true);
    const summary = details.querySelector("summary")!;
    expect(summary.textContent).toContain("Programs");
    expect(summary.textContent).toContain(String(roomProgramsFixture.programs.length));
    const rows = within(fold).getAllByTestId("room-program-row");
    expect(rows).toHaveLength(roomProgramsFixture.programs.length);
    const first = roomProgramsFixture.programs[0];
    expect(rows[0].textContent).toContain(first.title);
    expect(within(rows[0]).getByTestId("room-program-state").textContent).toContain(first.state_word);
    const track = within(rows[0]).getByTestId("room-program-track");
    expect(track.querySelectorAll(".pg-station")).toHaveLength(first.track.length);
    fireEvent.click(within(rows[0]).getByTestId("room-program-open"));
    expect(useDesk.getState().pullouts.map((p) => p.id)).toEqual([`program:${first.id}`]);
    expect(calls.filter((c) => c.key.includes("/api/programs"))).toEqual([]);
    expect(rawButtons(document.body)).toEqual([]);
    expect(made.id).toBeTruthy();
  });

  it("a project with none: the fold is drawn, says No Programs yet, and New program opens Programs scoped to the project", async () => {
    const empty = P13.roomEmpty as { project_id: string };
    const opened: Array<[string, string | undefined]> = [];
    const real = useDesk.getState().openSurfaceWindow;
    useDesk.setState({ openSurfaceWindow: (key: string, scope?: string) => { opened.push([key, scope]); } });
    try {
      wire({ [room(empty.project_id)]: () => clone(empty) });
      render(<WindowHarness scope={`project:${empty.project_id}`} />);
      const fold = await screen.findByTestId("room-fold-programs");
      expect(drawn(fold)).toBe(true);
      const summary = fold.querySelector("summary")!;
      expect(summary.textContent).toContain("Programs");
      expect(summary.querySelector(".gadget-fold-token")).toBeNull();
      expect(within(fold).getByTestId("room-programs-empty").textContent).toBe("No Programs yet");
      fireEvent.click(within(fold).getByTestId("room-programs-new"));
      expect(opened).toEqual([["open-programs", `project:${empty.project_id}`]]);
      expect(calls.filter((c) => c.key.includes("/api/programs"))).toEqual([]);
      expect(rawButtons(document.body)).toEqual([]);
    } finally {
      useDesk.setState({ openSurfaceWindow: real });
    }
  });

  it.each([[1440, false], [393, true]])("at %i the fold is in the Now tab's DOM, after Files", async (_width, compactView) => {
    const media = vi.spyOn(window, "matchMedia").mockImplementation((query: string) => ({
      matches: compactView && query.includes("max-width"), media: query, onchange: null,
      addListener: () => {}, removeListener: () => {}, addEventListener: () => {}, removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList);
    try {
      const empty = P13.roomEmpty as { project_id: string };
      wire({ [room(empty.project_id)]: () => clone(empty) });
      render(<WindowHarness scope={`project:${empty.project_id}`} />);
      const fold = await screen.findByTestId("room-fold-programs");
      expect(within(screen.getByTestId("room-folds")).getByTestId("room-fold-programs")).toBe(fold);
      expect(drawn(fold)).toBe(true);
      const order = Array.from(screen.getByTestId("room-folds").querySelectorAll("[data-room-slot]"))
        .map((el) => el.getAttribute("data-room-slot"));
      expect(order.indexOf("programs")).toBe(order.indexOf("files") + 1);
    } finally {
      media.mockRestore();
    }
  });
});
