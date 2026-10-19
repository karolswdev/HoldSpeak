// Parked by Betterment daily D5 (Brief and The week retired into Today): cases
// cut from the file named below; they test the retired windows' sections
// (chair/_parked/ArrivalSections.tsx). Not run (vitest excludes _parked).
// From: web/src/desk/__tests__/chair.app.test.tsx

/*
  it("draws dots equal to the total, accents today, lists three rows with ROOM, ARMS and Cancel", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_week_strip
    hub(weekStripDoor());
    render(<ChairHome />);
    const strip = await screen.findByTestId("arrival-week-strip");

    const dots = screen.getAllByTestId("arrival-week-dot");
    expect(totalOf()).toBe(3);
    expect(dots).toHaveLength(3);
    expect(screen.getByTestId("arrival-week-total").textContent).toBe("3 MEETINGS THIS WEEK");
    // Today (WED) is accented and carries the dots.
    const today = strip.querySelectorAll("[data-today]");
    expect(today).toHaveLength(1);
    expect(today[0].textContent).toContain("WED");
    expect(today[0].querySelectorAll("[data-testid='arrival-week-dot']")).toHaveLength(3);

    // Ruling B10: the calendar section is captioned THIS WEEK, never MEETINGS.
    const section = screen.getByTestId("arrival-this-week");
    expect(section.textContent).toContain("THIS WEEK 3");
    expect(section.textContent).not.toContain("MEETINGS 3");
    expect(screen.getAllByTestId("arrival-meeting-row")).toHaveLength(3);
    expect(section.textContent?.toUpperCase()).toContain("ROOM · Q4 PLATFORM");

    const standup = rowOf("Standup");
    expect(within(standup).getByText("ARMS 10:55")).toBeInTheDocument();
    expect(within(standup).getAllByTestId("arrival-cancel-armed")).toHaveLength(1);
    expect(screen.getAllByTestId("arrival-cancel-armed")).toHaveLength(1);
    expect(screen.queryByTestId("arrival-orphan-row")).toBeNull();

    // Every verb in the week body is the library Button (A.1).
    const raw = Array.from(weekBody().querySelectorAll("button")).filter(
      (b) => !b.classList.contains("btn") && !b.classList.contains("surface-ledger-line"),
    );
    expect(raw.map((b) => b.className)).toEqual([]);
    // No counter of zero.
    expect(document.body.textContent).not.toContain("0 MEETING");
    // The drawer's quiet NEXT line names the next event, never the Room.
    await waitFor(() => expect(screen.getByTestId("needs-next").textContent).toBe("NEXT · 11:00 · Standup"));
  });

  it("an orphan armed recording sits below, ARMED with FROM (WORK), counted in neither the rows nor the strip", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_orphan
    hub(door([
      event("ev-standup2", "Standup", "2026-10-07T17:00:00+00:00", {
        ...armed("rec-standup2", "2026-10-07T16:55:00Z"),
        ...ROOM,
      }),
      event("ev-design2", "Design review", "2026-10-07T19:00:00+00:00"),
      // `_scheduled_recording_item` for an event that left the projection.
      {
        id: "rec-retro-orphan",
        source: "scheduled_recording",
        target_ref: "scheduled_recording:rec-retro-orphan",
        title: "Retro",
        starts_at: "2026-10-07T19:00:00Z",
        ends_at: "2026-10-07T20:00:00Z",
        location: null,
        meeting_url: null,
        state: "idle",
        from: { event_title: "Retro", source_label: "WORK" },
      },
    ], week({ WED: 2 })));
    render(<ChairHome />);
    const orphan = await screen.findByTestId("arrival-orphan-row");

    expect(screen.getByTestId("arrival-this-week").textContent).toContain("THIS WEEK 2");
    expect(screen.getAllByTestId("arrival-meeting-row")).toHaveLength(2);
    expect(orphan.textContent).toContain("ARMED");
    expect(orphan.textContent).toContain("FROM · Retro (WORK)");
    expect(orphan.textContent).not.toContain("()");
    expect(within(orphan).getAllByTestId("arrival-cancel-armed")).toHaveLength(1);
    expect(totalOf()).toBe(2);
  });

  it("the strip counts the week's shape (past included); the rows count only what is coming", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_past_future_mix
    // The hub half (week counts the past event, `upcoming` does not carry it)
    // is tests/unit/test_desk_chair.py::test_past_event_counts_in_the_strip_not_in_upcoming.
    hub(door([
      event("ev-future1", "Design review", "2026-10-07T17:00:00+00:00"),
      event("ev-future2", "Retro", "2026-10-07T20:00:00+00:00"),
    ], week({ WED: 3 })));
    render(<ChairHome />);
    await screen.findByTestId("arrival-week-strip");
    expect(totalOf()).toBe(3);
    expect(screen.getAllByTestId("arrival-week-dot")).toHaveLength(3);
    expect(screen.getAllByTestId("arrival-meeting-row")).toHaveLength(2);
  });

  it("a next-week event stays out of THIS WEEK and the strip's total", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_this_week_bound
    const base = weekStripDoor();
    base.upcoming.push(event("ev-next-week", "Next week planning", "2026-10-12T16:00:00+00:00"));
    hub(base);
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-this-week");
    expect(screen.getAllByTestId("arrival-this-week")).toHaveLength(1);
    expect(section.textContent).toContain("THIS WEEK 3");
    expect(section.textContent).not.toContain("Next week planning");
    expect(screen.getAllByTestId("arrival-meeting-row")).toHaveLength(3);
    expect(totalOf()).toBe(3);
    expect(screen.getAllByTestId("arrival-week-dot")).toHaveLength(3);
  });

  it("five or more on one day reads exactly 5+", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_week_overflow_reads_five_plus
    const base = weekStripDoor();
    base.week = week({ WED: 8 });
    hub(base);
    render(<ChairHome />);
    const overflow = await screen.findAllByTestId("arrival-week-overflow");
    expect(overflow).toHaveLength(1);
    expect(overflow[0].textContent).toBe("5+");
    expect(Number(overflow[0].getAttribute("data-count"))).toBe(8);
    const dots = screen.queryAllByTestId("arrival-week-dot").length;
    expect(totalOf()).toBe(8);
    expect(dots + Number(overflow[0].getAttribute("data-count"))).toBe(8);
    expect(document.body.textContent).not.toContain("8+");
  });

  it("Cancel on an idle event-born row posts the cancel and the row loses ARMS and Cancel", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_cancel_idle_event_born (face half)
    // The hub half: tests/unit/test_desk_chair.py::test_cancel_over_the_route_disables_and_receipts.
    hub(weekStripDoor(), (path, init) => {
      if (path === "/api/scheduled-recordings/rec-standup/cancel" && init?.method === "POST") {
        const after = weekStripDoor();
        const standup = after.upcoming[0];
        delete standup.armed;
        delete standup.armed_schedule_id;
        wire.door = after;
        return { success: true, cancelled: true, state: "cancelled", enabled: false, last_outcome: "owner_cancelled" };
      }
      return undefined;
    });
    render(<ChairHome />);
    await screen.findByTestId("arrival-this-week");
    fireEvent.click(within(rowOf("Standup")).getByTestId("arrival-cancel-armed"));

    await waitFor(() => {
      const row = rowOf("Standup");
      expect(row.textContent).not.toContain("ARMS");
      expect(within(row).queryByTestId("arrival-cancel-armed")).toBeNull();
    });
    expect(wire.paths.some(([p, i]) => p === "/api/scheduled-recordings/rec-standup/cancel" && (i as any)?.method === "POST")).toBe(true);
    expect(screen.queryByTestId("arrival-cancel-refused")).toBeNull();
    expect(screen.getAllByTestId("arrival-meeting-row")).toHaveLength(3);
  });

  it("a refused Cancel is named on the row (CAN'T CANCEL and the hub's reason); the row then reads RECORDING", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_cancel_refused_names_reason (face half)
    // The hub half: tests/unit/test_desk_chair.py::test_cancel_while_recording_is_refused_by_name.
    hub(weekStripDoor(), (path, init) => {
      if (path === "/api/scheduled-recordings/rec-standup/cancel" && init?.method === "POST") {
        const after = weekStripDoor();
        after.upcoming[0].armed.state = "recording";
        wire.door = after;
        // `_error_response` for the ConflictError the service raises.
        const body = { success: false, error: "Already recording; stop the meeting instead", code: "already_recording" };
        throw new ApiError(409, body.error, body);
      }
      return undefined;
    });
    render(<ChairHome />);
    await screen.findByTestId("arrival-this-week");
    fireEvent.click(within(rowOf("Standup")).getByTestId("arrival-cancel-armed"));

    const refused = await screen.findByTestId("arrival-cancel-refused");
    const words = (refused.textContent || "").toUpperCase();
    expect(words).toContain("CAN'T CANCEL");
    expect(words).toContain("STOP THE MEETING");
    expect(words).not.toContain("TRACEBACK");
    expect(refused.querySelectorAll(".surface-state-chip[data-state='failure']")).toHaveLength(1);
    await waitFor(() => {
      const row = rowOf("Standup");
      expect(row.textContent).toContain("RECORDING");
      expect(row.textContent).not.toContain("ARMS");
      expect(within(row).queryByTestId("arrival-cancel-armed")).toBeNull();
    });
  });

  it("Unlink beside ROOM calls DELETE on the event's link; the ROOM token leaves and ARMS stays", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_unlink_room (verb half)
    // The hover-at-1440 / visible-at-393 opacity stays a browser fact (CSS).
    hub(weekStripDoor(), (path, init) => {
      if (path === "/api/calendar/events/ev-standup/link" && init?.method === "DELETE") {
        const after = weekStripDoor();
        delete after.upcoming[0].project_id;
        delete after.upcoming[0].project_name;
        wire.door = after;
        return { unlinked: 1, event_id: "ev-standup", durable: true };
      }
      return undefined;
    });
    render(<ChairHome />);
    await screen.findByTestId("arrival-this-week");
    const standup = rowOf("Standup");
    expect(within(standup).getByTestId("arrival-meeting-room").textContent).toContain("Q4 PLATFORM");
    expect(screen.getAllByTestId("arrival-unlink-room")).toHaveLength(1);
    fireEvent.click(within(standup).getByTestId("arrival-unlink-room"));

    await waitFor(() => {
      const row = rowOf("Standup");
      expect(within(row).queryByTestId("arrival-meeting-room")).toBeNull();
      expect(within(row).queryByTestId("arrival-unlink-room")).toBeNull();
    });
    expect(wire.paths.some(([p, i]) => p === "/api/calendar/events/ev-standup/link" && (i as any)?.method === "DELETE")).toBe(true);
    expect(screen.queryByTestId("arrival-unlink-refused")).toBeNull();
    const row = rowOf("Standup");
    expect(row.textContent).toContain("ARMS");
    expect(row.textContent).not.toContain("ROOM");
    expect((screen.getByTestId("needs-next").textContent || "").toUpperCase()).not.toContain("Q4 PLATFORM");
  });

  it("prints the row time and ARMS in the local zone (-06:00), never UTC", async () => {
    // replaces: tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_local_clock_minus_six
    hub(weekStripDoor());
    render(<ChairHome />);
    await screen.findByTestId("arrival-this-week");
    const standup = rowOf("Standup");
    expect(standup.querySelector(".surface-ledger-time")?.textContent?.trim()).toBe("11:00");
    const arms = Array.from(standup.querySelectorAll(".surface-state-chip"))
      .map((c) => (c.textContent || "").replace("●", "").trim())
      .find((t) => t.startsWith("ARMS"));
    expect(arms).toBe("ARMS 10:55");
    expect(arms).not.toBe("ARMS 16:55");
  });

  it("a non-today row reads its local weekday", async () => {
    // replaces (part): tests/e2e/test_hs175_arrival_glass.py::TestArrivalWeekStrip::test_arrival_local_clock_minus_six
    // 2026-10-09T02:30Z is Thursday 20:30 in Denver; UTC would say FRI 02:30.
    hub(door([event("ev-late", "Late sync", "2026-10-09T02:30:00+00:00")], week({ THU: 1 })));
    render(<ChairHome />);
    await screen.findByTestId("arrival-this-week");
    expect(rowOf("Late sync").querySelector(".surface-ledger-time")?.textContent?.trim()).toBe("THU 20:30");
  });

  it("the scheduled brief: the date line says GENERATED and 06:00; Generate stays for a re-run", async () => {
    // replaces: tests/e2e/test_philo15_05_strong_defaults_glass.py::test_the_brief_generated_itself (the face half; the 393 Go ▸ Brief route is phoneRing.test.tsx:198-206)
    const gets = BRIEF.scheduled.gets as Record<string, unknown>;
    const waiting = ((gets["/api/brief/latest"] as Json).sections.waiting as Json[]).map((i) => i.text);
    expect(waiting.some((t: string) => t.startsWith("No engine"))).toBe(true);
    expect(waiting.some((t: string) => t.startsWith("NOT READ"))).toBe(false);
    replayBrief(gets);
    render(<ChairHome />);
    const date = await screen.findByTestId("arrival-brief-date", undefined, { timeout: 3000 });
    expect(date.textContent).toContain("GENERATED");
    expect(date.textContent).toContain("06:00");
    expect(date.textContent).not.toContain("PARTIAL");
    expect(screen.getByTestId("arrival-brief-generate").textContent).toBe("Generate");
  });

  it("a brief with unread sources: the date line ends · PARTIAL and the body names NOT READ · AI models and · Decisions", async () => {
    // replaces: tests/e2e/test_philo15_05_strong_defaults_glass.py::test_a_brief_with_an_unread_source_says_partial (the face half)
    replayBrief(BRIEF.partial.gets as Record<string, unknown>);
    render(<ChairHome />);
    const date = await screen.findByTestId("arrival-brief-date", undefined, { timeout: 3000 });
    expect(date.textContent).toContain("GENERATED");
    expect(date.textContent).toMatch(/ · PARTIAL$/);
    const body = screen.getByTestId("arrival-brief").textContent ?? "";
    expect(body).toContain("NOT READ · AI models");
    expect(body).toContain("NOT READ · Decisions");
  });

  it("an unfinished thought is a THOUGHTS row with Continue; the press opens its note", async () => {
    // replaces: tests/e2e/test_hs170_arrival_glass.py::TestArrivalGlass::test_arrival_needs_you_1440 (the THOUGHTS leg)
    // replaces: tests/e2e/test_hs141_chair_geometry.py::test_normal_chair_stays_inside_chrome_at_all_owner_widths (the thought-row leg)
    const answer = structuredClone(THOUGHTS_ONE.wire) as any;
    vi.mocked(unfinishedThoughts).mockImplementation(async () => structuredClone(answer));
    hub(door([], week({}, false)));
    const openPullout = vi.fn();
    const realOpen = useDesk.getState().openPullout;
    useDesk.setState({ openPullout } as never);
    try {
      render(<ChairHome />);
      const section = await within(weekBody()).findByTestId("arrival-thoughts");
      expect(section.textContent).toContain("THOUGHTS");
      const rows = within(section).getAllByTestId("arrival-thought-row");
      expect(rows).toHaveLength(1);
      expect(rows[0].textContent).toContain("Migrate the auth service");
      fireEvent.click(within(rows[0]).getByRole("button", { name: "Continue" }));
      expect(openPullout).toHaveBeenCalledWith(`note:${answer.items[0].working_note_id}`);
    } finally {
      useDesk.setState({ openPullout: realOpen } as never);
    }
  });

  it("no unfinished thought: no THOUGHTS section", async () => {
    // replaces: tests/e2e/test_hs170_arrival_glass.py::TestArrivalGlass::test_arrival_quiet_1440 (the THOUGHTS leg)
    vi.mocked(unfinishedThoughts).mockImplementation(async () => structuredClone(THOUGHTS_NONE.wire) as any);
    hub(door([], week({}, false)));
    render(<ChairHome />);
    await waitFor(() => expect(vi.mocked(unfinishedThoughts)).toHaveBeenCalled());
    await waitFor(() => expect(weekBody()).toBeTruthy());
    expect(screen.queryByTestId("arrival-thoughts")).toBeNull();
  });

describe("The week: the row verbs", () => {

});

describe("The Brief window on the recorded hub", () => {
  function replayBrief(gets: Record<string, unknown>) {
    const brief = gets["/api/brief/latest"] as { generated_at: string };
    // The viewer's clock: one hour after the brief was made, the same day.
    vi.setSystemTime(new Date(new Date(brief.generated_at).getTime() + 3600_000));
    vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(gets, String(path)) as never);
  }

});

describe("The week: THOUGHTS on the recorded hub", () => {
  afterEach(() => {
    vi.mocked(unfinishedThoughts).mockImplementation(async () => ({ items: [], next_cursor: null }));
  });

});
*/
