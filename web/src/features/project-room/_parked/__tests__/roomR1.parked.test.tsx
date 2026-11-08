/* PARKED by R1 "the brief" (owner 2026-11-08: the Room's Now face "looks
 * like shit"): these room.app.test.tsx cases read faces that left the Now
 * face. The Prepare posture's only Room entry was the Ask well's Result
 * cycle (Answer / Preparation brief), which R1 removed with the Ask card;
 * This week's Decided lines and their Committed word; the "Update" chips
 * line (core/UpdateLine.tsx, parked in ../UpdateLine.tsx); the Programs
 * fold (parked in ../roomProgramsFold.tsx). Their successors in
 * room.app.test.tsx: "R1: the Now face is the brief". Not collected
 * (vite.config.ts excludes _parked). Each block is as it stood in
 * room.app.test.tsx at origin/main 668ba266d; its constants (PREP_*, PREP2_*,
 * P7, COMMITTED, P13, roomProgramsFixture) are that file's. */

describe("HS-200-11: the Prepare face states coverage, sources and the route before the run", () => {
  // replaces: tests/e2e/test_hs200_preparation_brief_glass.py::test_prepare_face_states_coverage_before_the_run
  // (the purpose textarea's no-clip box is the generic sweep's, T3)
  const pid = PREP_ROOM.project_id;

  it("COVERAGE · 2 OF 4, SOURCES 4 with both gaps and their repairs, CARRIED FORWARD 1, the route READY on THIS DEVICE", async () => {
    wire({
      [room(pid)]: () => clone(PREP_ROOM),
      [`GET /api/projects/${pid}/briefs/route`]: () => clone(PREP_ROUTE),
      [`GET /api/projects/${pid}/briefs/manifest`]: () => clone(PREP_MANIFEST),
      [`GET /api/projects/${pid}/briefs`]: () => ({ briefs: [] }),
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    const result = await screen.findByTestId("room-ask-result");
    fireEvent.change(within(result).getByRole("combobox"), { target: { value: "brief" } });
    const coverage = await screen.findByTestId("prepare-coverage");
    const posture = screen.getByTestId("prepare-posture");
    const words = (el: Element) => el.querySelector(".surface-state-chip")?.getAttribute("aria-label");
    expect(screen.getByTestId("prepare-head-name").textContent?.trim()).toBe("Prepare a brief");
    expect(words(coverage)).toBe("Coverage · 2 of 4");
    expect(coverage.getAttribute("data-complete")).toBe("false");
    expect(screen.getByTestId("prepare-purpose-by-hand").textContent?.trim()).toBe("Purpose set by hand");
    expect(screen.getByTestId("prepare-no-calendar").textContent?.trim()).toBe("No calendar");
    const route = await screen.findByTestId("prepare-route");
    expect(route.getAttribute("data-state")).toBe("ready");
    expect(screen.getByTestId("prepare-route-model").textContent?.trim()).toBe("QWEN3 35B");
    // Same-device work has no passive egress badge on the face.
    expect(route.textContent).not.toContain("This device");

    const captions = Array.from(posture.querySelectorAll(".surface-section-head h3")).map((h) => h.textContent?.trim());
    expect(captions[0]).toBe("Sources 4");
    expect(captions).toContain("Carried forward 1");
    const states = screen.getAllByTestId("prepare-source-state");
    expect(states.map((s) => s.getAttribute("data-state")).sort()).toEqual(["available", "available", "failed", "stale"]);
    expect(states.map(words)).toContain("Credential expired · Confluence");
    expect(screen.getAllByTestId("prepare-source-repair").map((b) => b.textContent?.trim()).sort()).toEqual(["Reconnect", "Retry"]);
    const observed = screen.getAllByTestId("prepare-source-observed").map((o) => o.textContent?.trim() ?? "");
    expect(observed).toHaveLength(4);
    expect(observed.every((t) => t.startsWith("Observed "))).toBe(true);

    // An empty purpose: Prepare is refused; the purpose is a textarea that persists.
    expect((screen.getByTestId("prepare-verb") as HTMLButtonElement).disabled).toBe(true);
    const purpose = screen.getByRole("textbox", { name: "Purpose" });
    expect(purpose.tagName).toBe("TEXTAREA");
    fireEvent.change(purpose, { target: { value: "Architecture review, cut-over sequencing, rollback rehearsal" } });
    await waitFor(() => expect((screen.getByTestId("prepare-verb") as HTMLButtonElement).disabled).toBe(false));
    expect(sessionStorage.getItem("hs.room.prepareDrafts")).toContain("rollback rehearsal");
    // The route probe sends nothing: no prepare request left the face.
    expect(calls.filter((c) => c.key.endsWith("/briefs/prepare"))).toEqual([]);
    expect(Array.from(posture.querySelectorAll("button")).filter((b) => !(b.getAttribute("aria-label") || b.textContent || "").trim())).toEqual([]);
  });
});

describe("HS-200-11: Prepare pressed — sent, kept, refused and stopped as the hub answers", () => {
  const pid = PREP2_ROOM.project_id;
  const PURPOSE = "Architecture review, cut-over sequencing";
  const prepareKey = `POST /api/projects/${pid}/briefs/prepare`;
  const table = (prepare: Answer): Record<string, Answer> => ({
    [room(pid)]: () => clone(PREP2_ROOM),
    [`GET /api/projects/${pid}/briefs/route`]: () => clone(PREP2_ROUTE),
    [`GET /api/projects/${pid}/briefs/manifest`]: () => clone(PREP2_MANIFEST),
    [`GET /api/projects/${pid}/briefs`]: (_init, url) => (url.includes("lifecycle=kept") && kept ? clone(BRIEFS_KEPT) : { briefs: [] }),
    [prepareKey]: prepare,
    [`POST /api/briefs/${PREPARE_OK.brief.id}/keep`]: () => { kept = true; return clone(KEEP); },
    [`POST /api/projects/${pid}/briefs/stop`]: () => clone(STOP),
  });
  let kept = false;
  const refuse = async (payload: unknown) => {
    const { ApiError } = await import("../../../lib/api");
    return new ApiError(409, String((payload as { error: string }).error), clone(payload));
  };
  async function pressPrepare() {
    render(<WindowHarness scope={`project:${pid}`} />);
    fireEvent.change(within(await screen.findByTestId("room-ask-result")).getByRole("combobox"), { target: { value: "brief" } });
    await screen.findByTestId("prepare-coverage");
    await waitFor(() => expect(screen.getByTestId("prepare-route").getAttribute("data-state")).toBe("ready"));
    fireEvent.change(screen.getByRole("textbox", { name: "Purpose" }), { target: { value: PURPOSE } });
    await waitFor(() => expect((screen.getByTestId("prepare-verb") as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(screen.getByTestId("prepare-verb"));
  }
  beforeEach(() => { kept = false; });

  // replaces: tests/e2e/_parked/test_hs200_preparation_brief_glass.py::test_running_then_kept_brief_with_claims_and_not_read
  // (the face's receipt, egress and Keep legs at :754-:771; the claims ledger is the T1 successor's)
  it("a sent and answered request: Brief ready, the receipt names the model, Keep keeps it and the receipt stays", async () => {
    wire(table(() => clone(PREPARE_OK)));
    await pressPrepare();
    expect(calls.find((c) => c.key === prepareKey)?.json).toMatchObject({ purpose: PURPOSE, generator: "model" });
    await screen.findByTestId("prepare-document");
    expect(screen.getByTestId("prepare-head-name").textContent?.trim()).toBe("Brief ready");
    const lifecycle = () => screen.getByTestId("prepare-lifecycle").querySelector(".surface-state-chip")?.getAttribute("aria-label");
    expect(lifecycle()).toBe("Draft");
    expect(screen.queryByTestId("prepare-footer-egress")).toBeNull();
    const receipt = screen.getByTestId("prepare-footer-receipt").textContent?.trim() ?? "";
    expect(receipt.startsWith("QWEN3 35B")).toBe(true);
    expect(screen.getByTestId("prepare-head").textContent).not.toContain("NOTHING SENT");
    expect(screen.getAllByTestId("prepare-discard")).toHaveLength(1);

    const keep = screen.getByTestId("prepare-keep");
    fireEvent.click(keep);
    await waitFor(() => expect(lifecycle()).toBe("Kept"));
    expect(screen.getByTestId("prepare-head-name").textContent?.trim()).toBe("Brief ready");
    expect(screen.getByTestId("prepare-keep").getAttribute("aria-disabled")).toBe("true");
    expect(screen.queryByTestId("prepare-discard")).toBeNull();
    expect(screen.getByTestId("prepare-footer-receipt").textContent?.trim()).toBe(receipt);
    fireEvent.click(screen.getByTestId("prepare-keep"));
    expect(calls.filter((c) => c.key.endsWith("/keep"))).toHaveLength(1); // a second press writes nothing
  });

  // replaces: tests/e2e/_parked/test_hs200_preparation_brief_glass.py::test_a_sent_and_answered_request_is_never_reported_as_nothing_sent
  // (the prose leg, :933-:945; the HTTP 500 leg reads NOT ANSWERED by the same refusalReceipt)
  it("P0: a kernel success with a prose answer reads SENT · QWEN3 35B · NOTHING USABLE RECEIVED, never NOTHING SENT", async () => {
    const error = await refuse(PREPARE_PROSE_409);
    wire(table(() => { throw error; }));
    await pressPrepare();
    const sent = await screen.findByTestId("prepare-sent-token");
    expect(screen.getByTestId("prepare-head").textContent).not.toContain("Nothing sent");
    // Owner ruling 2026-10-25: the engine by name; never its address.
    expect(sent.textContent?.trim()).toBe("Sent · QWEN3 35B · Nothing usable received");
    expect(screen.queryByTestId("prepare-footer-egress")).toBeNull();
    expect(screen.getByTestId("prepare-footer-receipt").textContent?.trim()).toBe("Sent · QWEN3 35B · Nothing usable received");
    expect(screen.getByTestId("prepare-route").querySelector(".surface-state-chip")?.getAttribute("aria-label")).toBe("Output unusable");
    expect(screen.getByTestId("prepare-purpose-kept").textContent?.trim()).toBe("Purpose kept");
    expect((screen.getByRole("textbox", { name: "Purpose" }) as HTMLTextAreaElement).value).toBe(PURPOSE);
    expect(screen.queryByTestId("prepare-document")).toBeNull();
  });

  // replaces: tests/e2e/_parked/test_hs200_preparation_brief_glass.py::test_stop_leaves_no_orphan_draft (the face half, :1030-:1040)
  it("Stop: the request had left, the face is back on Prepare with his purpose, and no draft is drawn", async () => {
    let answer!: () => void;
    const error = await refuse(PREPARE_STOPPED_409);
    wire(table(() => new Promise((_resolve, reject) => { answer = () => reject(error); })));
    await pressPrepare();
    await screen.findByTestId("prepare-running");
    fireEvent.click(screen.getByRole("button", { name: "Stop" }));
    await waitFor(() => expect(screen.getByTestId("prepare-posture").getAttribute("data-posture")).toBe("prepare"));
    const stopped = await screen.findByTestId("prepare-stopped");
    expect(stopped.textContent?.trim().startsWith("Stopped · Request had left")).toBe(true);
    const stopCall = calls.find((c) => c.key.endsWith("/briefs/stop"));
    expect(stopCall?.json?.attempt_id).toBe(calls.find((c) => c.key === prepareKey)?.json?.attempt_id);
    await act(async () => { answer(); await Promise.resolve(); });
    expect(screen.queryByTestId("prepare-document")).toBeNull();
    expect(screen.getByTestId("prepare-posture").getAttribute("data-posture")).toBe("prepare");
    expect((screen.getByRole("textbox", { name: "Purpose" }) as HTMLTextAreaElement).value).toBe(PURPOSE);
  });
});

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

// from "HS-200-16: a meeting from an earlier day, its decision and its commitment"
// (it opened the Prepare posture from the Ask well's Result cycle)
  it("CARRIED FORWARD: the due is a DATE (DUE MM-DD, never a clock); the commitment is CMT, never DEC or CURRENT", async () => {
    wire({
      [room(pid)]: () => clone(LOOP_ROOM),
      [`GET /api/projects/${pid}/proposals`]: () => clone(LOOP_PROPOSALS),
      [`GET /api/projects/${pid}/briefs/route`]: () => clone(LOOP_ROUTE),
      [`GET /api/projects/${pid}/briefs/manifest`]: () => clone(LOOP_MANIFEST),
      [`GET /api/projects/${pid}/briefs`]: () => ({ briefs: [] }),
    });
    render(<WindowHarness scope={`project:${pid}`} />);
    await openNeedsYou();
    fireEvent.change(within(await screen.findByTestId("room-ask-result")).getByRole("combobox"), { target: { value: "brief" } });
    const carried = await screen.findByTestId("prepare-carried");
    const posture = screen.getByTestId("prepare-posture");
    const captions = Array.from(posture.querySelectorAll(".surface-section-head h3")).map((h) => h.textContent?.trim());
    expect(captions.filter((c) => c?.startsWith("Carried forward"))).toEqual(["Carried forward 2"]);
    const due = LOOP_MANIFEST.manifest.commitments[0].due_at; // "YYYY-MM-DD"
    const dueTokens = Array.from(carried.querySelectorAll(".surface-token")).map((t) => t.textContent?.trim() ?? "")
      .filter((t) => t.startsWith("Due"));
    expect(dueTokens).toEqual([`Due ${due.slice(5)}`]);
    expect(dueTokens.join(" ")).not.toMatch(/\d\d:\d\d/);
    const rows = Array.from(carried.querySelectorAll("li")).map((li) => ({
      emblem: li.querySelector(".prepare-emblem")?.textContent?.trim(),
      text: li.querySelector(".surface-primary")?.textContent?.trim(),
      chips: Array.from(li.querySelectorAll(".surface-state-chip")).map((c) => c.getAttribute("aria-label") || c.textContent?.trim()),
    }));
    const decision = rows.find((r) => r.text === LOOP_MANIFEST.manifest.decisions[0].text)!;
    const commitment = rows.find((r) => r.text === LOOP_MANIFEST.manifest.commitments[0].text)!;
    expect(decision.emblem).toBe("DEC");
    expect(commitment.emblem).toBe("CMT");
    expect(commitment.chips).not.toContain("Current");
  });
// from web/src/desk/__tests__/memory.app.test.tsx, "Memory on the Desk: standing pages where the work lives"
// (the Room's This week drew the project's standing pages; R1 took This week off the Now face)
  it("the Atlas Room: This week reads Risks and Changed from the project's pages, each line with its source", async () => {
    // replaces: tests/e2e/test_memory_faces_glass.py::test_memory_on_the_desk (face half: pages)
    // Betterment P3: the pages are promoted into the Now wing's This week
    // (Decided comes from the decision records, the one store for decisions).
    render(<ProjectRoomCore scope="project:atlas" />);
    const section = await screen.findByTestId("room-this-week");
    const groups = within(section).getAllByTestId("this-week-group");
    expect(groups.map((g) => g.getAttribute("aria-label"))).toEqual(["Open", "Risks", "Changed"]);
    const changed = within(groups[2]).getAllByTestId("this-week-line");
    expect(changed).toHaveLength(4);
    const cutover = changed.find((l) => l.textContent?.includes("Cutover date is 10-17"))!;
    expect(within(cutover).getByTestId("memory-ref").textContent).toBe("Note 10-11");
    expect(section.textContent).not.toContain("Harbor");
    expect(section.textContent).not.toMatch(/Rewrite/i);
  });