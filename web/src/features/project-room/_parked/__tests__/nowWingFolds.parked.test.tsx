/* PARKED by Betterment P3 (2026-10-18): these Room tests read faces that
 * left the project window's Now wing (the folds Since you looked, Decisions
 * and owed, Files, Briefs, Pages; the SIGNALS plate; the head's chips; the
 * footer READ · NEXT CHECK receipt and Refresh). Their components are parked
 * in ../nowWingFolds.tsx. Not collected (vite.config.ts excludes _parked).
 * Each block is as it stood in its source file at origin/main b024b1118. */

// from room169.test.tsx

describe("HS-169-03: SINCE YOU LOOKED section", () => {
  it("renders groups and entries with phrases (not raw field names)", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    // Group headings
    const groups = screen.getAllByTestId("since-read-group");
    expect(groups.length).toBe(3); // GitHub, Jira, Room
    expect(screen.getByText("GitHub · 2 opened · 1 merged")).toBeTruthy();
    expect(screen.getByText("Jira · 1 moved")).toBeTruthy();
  });

  it("renders SINCE CREATED when readAt is null", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect(screen.getByText("Created just now")).toBeTruthy();
  });
});

describe("HS-169-03: DECISIONS & COMMITMENTS section", () => {
  it("renders decision and commitment rows", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    expect(screen.getByText(/use acli for Jira, never REST/)).toBeTruthy();
    expect(screen.getByText(/a review of #612/)).toBeTruthy();
  });

  it("hides entirely when both are empty", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) return Promise.resolve(quietRoomResponse());
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    // The section should not exist
    expect(screen.queryByText("DECISIONS & COMMITMENTS")).toBeNull();
  });
});

describe("HS-169-03: footer", () => {
  it("renders READ time in footer receipt", async () => {
    render(<WindowHarness scope="project:p1" />);
    const receipt = await screen.findByTestId("room-footer-receipt");
    // readAt from the wire is "2026-09-03T09:21:00"
    expect(receipt.textContent).toContain("READ");
  });

  it("renders Refresh button in footer", async () => {
    render(<WindowHarness scope="project:p1" />);
    const btn = await screen.findByTestId("room-refresh");
    expect(btn.textContent).toBe("Refresh");
  });
});

  it("renders target date chip when present", async () => {
    render(<WindowHarness scope="project:p1" />);
    const chip = await screen.findByTestId("room-target-chip");
    // PHILO-17 refit: plain words (the strip draws them in mono capitals).
    expect(chip.textContent).toMatch(/target/i);
    expect(chip.textContent).toMatch(/41 days/i);
  });

  it("renders OVERDUE when target is passed", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room/read")) return Promise.resolve({ read_at: new Date().toISOString() });
      if (url.includes("/room")) {
        return Promise.resolve(roomResponse({
          target: { state: "ok", targetAt: "2026-08-01", daysLeft: -34, passed: true },
        }));
      }
      return Promise.resolve(detailResponse(url));
    });

    render(<WindowHarness scope="project:p1" />);
    const chip = await screen.findByTestId("room-target-chip");
    expect(chip.textContent).toMatch(/overdue by 34 days/i);
    expect(chip.getAttribute("data-tone")).toBe("danger");
  });

  it("calls POST /room/read on Refresh", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");

    // Clear existing calls
    apiFetch.mockClear();
    apiFetch.mockImplementation((url: string) => Promise.resolve(response(url)));

    // Click Refresh
    const refreshBtn = screen.getByTestId("room-refresh");
    refreshBtn.click();

    await waitFor(() => {
      const readCalls = apiFetch.mock.calls.filter(
        (call: unknown[]) => String(call[0]).includes("/room/read"),
      );
      expect(readCalls.length).toBeGreaterThanOrEqual(1);
    });
  });

// from ProjectRoomCore.test.tsx

describe("ProjectRoomCore — FILES names its failed read", () => {
  it("draws RESOURCES · NOT READ with Retry, and Retry reads again", async () => {
    let resourceReads = 0;
    apiFetch.mockImplementation((url: string) => {
      if (url.endsWith("/api/projects/p1/resources")) {
        resourceReads += 1;
        return resourceReads === 1
          ? Promise.reject(new Error("read failed"))
          : Promise.resolve({ resources: [] });
      }
      return Promise.resolve(response(url));
    });
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    const unread = await screen.findByTestId("room-files-not-read");
    expect(unread.textContent).toContain("RESOURCES · NOT READ");
    screen.getByTestId("room-files-retry").click();
    await waitFor(() => expect(resourceReads).toBeGreaterThan(1));
    await waitFor(() => expect(screen.queryByTestId("room-files-not-read")).toBeNull());
  });
});

// from room.app.test.tsx (wires: ./room-wires/*.json in ../../__tests__)

describe("HS-173-03: HEALTH rows carry the wire's tones and tokens", () => {
  const pid = BARE_ROOM.project_id;

  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_rows_1440
  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_rows_393
  it("REVIEW WAIT, ISSUE AGING, CI and RELEASE with their tokens and the CHECKED caption", async () => {
    wire({ [room(pid)]: () => roomWith({ health: HEALTH_RED }) });
    render(<WindowHarness scope={`project:${pid}`} />);
    const review = await screen.findByTestId("health-row-review_wait");
    expect(review.textContent).toMatch(/review wait/i);
    expect(review.textContent).toContain("2.5 D MEDIAN");
    expect(review.textContent).toContain("2 WAITING");
    expect(screen.getByTestId("health-row-issue_aging").textContent).toMatch(/issue aging/i);
    expect(screen.getByTestId("health-row-issue_aging").textContent).toContain("1 > 14 D");
    expect(screen.getByTestId("health-row-ci").textContent).toContain("1 FLAKY");
    expect(screen.getByTestId("health-row-ci").textContent).toContain("QUEUE 2");
    expect(screen.getByTestId("health-row-release").textContent).toMatch(/release/i);
    expect(screen.getByTestId("health-row-release").textContent).toContain("1 BLOCKER");
    const lead = (k: string) => screen.getByTestId(`health-row-${k}`).querySelector(".room-signal-lamp")?.getAttribute("data-state");
    expect([lead("review_wait"), lead("issue_aging"), lead("ci"), lead("release")])
      .toEqual(["failure", "warning", "warning", "failure"]);
    expect(screen.getByTestId("health-checked").textContent).toMatch(/^CHECKED /);
    const body = screen.getByTestId("room-body");
    expect(rawButtons(body)).toEqual([]);
    expect(body.textContent).not.toMatch(/\b0\s+(?:NEEDS|SOURCES|DECISIONS|WAITING|FLAKY|QUEUE|BLOCKERS)/);
  });

  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_ready_1440
  // replaces: tests/e2e/test_hs173_health_glass.py::test_health_ready_393
  it("all green says CLEAR, PASSING and READY, never a zero", async () => {
    wire({ [room(pid)]: () => roomWith({ health: HEALTH_GREEN }) });
    render(<WindowHarness scope={`project:${pid}`} />);
    expect((await screen.findByTestId("health-row-issue_aging")).textContent).toContain("CLEAR");
    expect(screen.getByTestId("health-row-ci").textContent).toContain("PASSING");
    expect(screen.getByTestId("health-row-release").textContent).toContain("READY");
    const body = screen.getByTestId("room-body");
    expect(rawButtons(body)).toEqual([]);
    expect(body.textContent).not.toMatch(/\b0\s+(?:NEEDS|SOURCES|DECISIONS|WAITING|FLAKY|QUEUE|BLOCKERS)/);
  });
});

describe("PHILO-17 sources: Park from FILES leaves PARKED · <name> with Restore in the Room", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_park_from_files_leaves_its_receipt_and_restore_in_the_room
  it("Get Info ▸ Park: the receipt and Restore stay in the Room; Restore brings the meeting back", async () => {
    const { DrawerInfoWindow } = await import("../../../desk/drawer/InfoWindow");
    const { useDrawers } = await import("../../../desk/drawer/store");
    useDesk.setState({ refresh: vi.fn(() => Promise.resolve()) } as never);
    let parked = false;
    wire({
      [room("p-lone")]: () => clone(LONE_ROOM),
      "GET /api/projects/p-lone/meetings": () => (parked ? { meetings: [] } : clone(LONE_MEETINGS)),
      "GET /api/projects/p-lone/repository": () => ({ ...clone(BARE_REPOSITORY), project_id: "p-lone" }),
      "DELETE /api/meetings/m-lone": () => { parked = true; return clone(PARK_DELETE); },
      "POST /api/meetings/m-lone/restore": () => { parked = false; return clone(RESTORE); },
    });
    function Desk() {
      const infos = useDrawers((s) => s.infos);
      return (
        <>
          <WindowHarness scope="project:p-lone" />
          {infos.map((info) => <DrawerInfoWindow key={info.ref} info={info} />)}
        </>
      );
    }
    render(<Desk />);
    const files = await screen.findByTestId("room-files");
    fireEvent.click(await within(files).findByRole("button", { name: /^Vendor call,/ }));
    fireEvent.click(within(files).getByTestId("room-files-info"));
    fireEvent.click(await screen.findByRole("button", { name: "Park" }), { detail: 1 });
    const receipt = await within(screen.getByTestId("room-files")).findByTestId("room-files-park-receipt");
    expect(receipt.querySelector("[role=status]")?.textContent).toBe("PARKED · Vendor call");
    expect(calls.some((c) => c.key === "DELETE /api/meetings/m-lone")).toBe(true);
    // The row leaving FILES rides the desk's refresh (stubbed here): that leg stays the browser's.
    fireEvent.click(within(receipt).getByRole("button", { name: "Restore" }));
    await waitFor(() => expect(calls.some((c) => c.key === "POST /api/meetings/m-lone/restore")).toBe(true));
    await waitFor(() => expect(screen.getByTestId("room-files-park-receipt").querySelector("[role=status]")?.textContent)
      .toMatch(/RESTORED/));
    useDrawers.getState().setReceipt("p-lone", null);
  });
});

describe("PHILO-17 sources: a parked meeting leaves FILES on the hub's own frame", () => {
  // replaces: tests/e2e/test_philo17_sources_glass.py::test_park_from_files_leaves_its_receipt_and_restore_in_the_room
  //   (the leg the earlier successor left to the browser: the row leaving FILES and coming back; the hub
  //   half is tests/integration/test_desk_project_room.py::test_park_from_files_parks_the_meeting_and_restore_brings_it_back_to_the_room)
  const { pid, before, park, park_frames, parked, restore, restore_frames, restored } = F17;
  const deliver = (frames: Array<{ type: string; data: unknown }>) =>
    act(() => { for (const f of frames) for (const h of bus.handlers.get(f.type) ?? []) h(f); });
  const row = () => screen.getByTestId("room-files").querySelector("[data-object-id='meeting:m-lone']");

  it("Park: PARKED · Vendor call, and the hub's desk_changed takes the row out; Restore and its frame bring it back", async () => {
    const { DrawerInfoWindow } = await import("../../../desk/drawer/InfoWindow");
    const { useDrawers } = await import("../../../desk/drawer/store");
    useDesk.setState({ refresh: vi.fn(() => Promise.resolve()) } as never);
    replay(before, {
      "DELETE /api/meetings/m-lone": () => { hubGets = parked; return park.answer; },
      "POST /api/meetings/m-lone/restore": () => { hubGets = restored; return restore.answer; },
    });
    function Desk() {
      const infos = useDrawers((s) => s.infos);
      return (
        <>
          <WindowHarness scope={`project:${pid}`} />
          {infos.map((info) => <DrawerInfoWindow key={info.ref} info={info} />)}
        </>
      );
    }
    render(<Desk />);
    const files = await screen.findByTestId("room-files");
    fireEvent.click(await within(files).findByRole("button", { name: /^Vendor call,/ }));
    fireEvent.click(within(files).getByTestId("room-files-info"));
    fireEvent.click(await screen.findByRole("button", { name: "Park" }), { detail: 1 });
    const receipt = await within(screen.getByTestId("room-files")).findByTestId("room-files-park-receipt");
    expect(receipt.querySelector("[role=status]")?.textContent).toBe("PARKED · Vendor call");
    expect(row()).not.toBeNull(); // nothing re-read yet: the hub's frame has not come
    deliver(park_frames);
    await waitFor(() => expect(row()).toBeNull(), { timeout: 3000 });
    expect(screen.getByTestId("room-files-park-receipt").querySelector("[role=status]")?.textContent).toBe("PARKED · Vendor call");

    fireEvent.click(within(screen.getByTestId("room-files-park-receipt")).getByRole("button", { name: "Restore" }));
    await waitFor(() => expect(screen.getByTestId("room-files-park-receipt").querySelector("[role=status]")?.textContent)
      .toMatch(/RESTORED/));
    deliver(restore_frames);
    await waitFor(() => expect(row()).not.toBeNull(), { timeout: 3000 });
    expect(misses).toEqual([]);
    useDrawers.getState().setReceipt(pid, null);
  });
});

// from room172proposals.test.tsx

describe("HS-172-03: Confirmed proposals in D&C", () => {
  it("renders proposal-derived decision with MTG emblem and CONFIRMED token", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() =>
      expect(screen.queryAllByTestId("decision-row")).toHaveLength(1),
    );

    const row = screen.getByTestId("decision-row");
    expect(row.textContent).toContain("Ania owns the API spec");

    // MTG emblem on proposal-derived decisions
    const lead = row.querySelector(".surface-ledger-lead");
    expect(lead?.textContent).toBe("MTG");

    const confirmedState = screen.getByTestId("confirmed-state");
    expect(confirmedState.textContent).toContain("CONFIRMED");

    // WAS token for changed due
    expect(row.textContent).toContain("WAS BY FRI");
  });

  it("merges commitment into its decision row -- one row, no 'You owe'", async () => {
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() =>
      expect(screen.queryAllByTestId("decision-row")).toHaveLength(1),
    );

    // Only 1 row total in D&C (the commitment is folded, not listed separately)
    const allRows = document.querySelectorAll(".surface-ledger-row");
    const dcSection = document.querySelector("h3")?.closest(".surface-section");
    // Find the DECISIONS & COMMITMENTS section
    const headers = Array.from(document.querySelectorAll(".surface-section h3"));
    const dcHeader = headers.find((h) => h.textContent?.includes("DECISIONS & COMMITMENTS"));
    expect(dcHeader).toBeTruthy();
    // Count should be 1 (merged), not 2
    expect(dcHeader?.textContent).toBe("DECISIONS & COMMITMENTS 1");

    // The merged row shows OWNER ANIA, BY FRI, CONFIRMED (not "You owe")
    const row = screen.getByTestId("decision-row");
    expect(row.textContent).toContain("OWNER ANIA");
    expect(row.textContent).toMatch(/BY\s+(FRI|SEP\s+12)/);
    expect(row.textContent).toContain("CONFIRMED");
    expect(row.textContent).not.toContain("You owe");
  });
});

describe("PHILO-15 08: a confirmed action's record reads as an action", () => {
  it("says Action:, carries ACTION, and offers no decision Send well", async () => {
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room") && !url.includes("/room/read")) {
        const room = roomWithProposals();
        (room.decisions.items[0] as Record<string, unknown>).kind = "action";
        return Promise.resolve(room);
      }
      if (url.includes("/proposals")) return Promise.resolve(proposalsApiResponse());
      if (url.includes("/suggested-sources")) return Promise.resolve(suggestedSourcesApiResponse());
      return Promise.resolve({});
    });
    render(<WindowHarness scope="project:p1" />);
    await waitFor(() => expect(screen.queryAllByTestId("decision-row")).toHaveLength(1));
    const row = screen.getByTestId("decision-row");
    expect(row.getAttribute("aria-label")).toBe("Action: Ania owns the API spec");
    expect(row.textContent).toContain("ACTION");
    expect(row.getAttribute("role")).toBeNull();
  });
});

describe("PHILO-11-05a: a Room decision row holds its record's SEND well", () => {
  it("the row unfolds in place; explicit Send opens one well for its decision_record", async () => {
    // The row's id is the record id (project_service.py: decisions items `id: rid`).
    const record = {
      id: "record-85f927aa", text: "Freeze the old ledger on Nov 3", at: "2026-09-05T09:41:00", url: null,
      lifecycle: "active", kind: "decision", source_type: "meeting", source_id: "dec-1",
    };
    apiFetch.mockImplementation((url: string) => {
      if (url.includes("/room") && !url.includes("/room/read")) {
        return Promise.resolve({ ...roomWithProposals(), decisions: { state: "ok", items: [record] }, commitments: { state: "ok", items: [] } });
      }
      if (url.startsWith("/api/channels/destinations")) return Promise.resolve({ destinations: [] });
      if (url.startsWith("/api/channels/sends")) return Promise.resolve({ sends: [] });
      if (url.includes("/proposals")) return Promise.resolve(proposalsApiResponse());
      if (url.includes("/suggested-sources")) return Promise.resolve(suggestedSourcesApiResponse());
      return Promise.resolve({});
    });
    render(<WindowHarness scope="project:p1" />);
    const row = await screen.findByTestId("decision-row");
    expect(document.querySelector("[data-seat=decision-record]")).toBeNull();
    fireEvent.click(row);
    const fold = await screen.findByTestId("send-fold");
    expect(fold.getAttribute("data-doc")).toBe("decision_record:record-85f927aa");
    expect(screen.queryByTestId("send-well")).toBeNull();
    expect(apiFetch.mock.calls.some(([url]) => String(url).startsWith("/api/channels/destinations"))).toBe(false);
    fireEvent.click(within(fold).getByRole("button", { name: /^Send$/ }));
    await waitFor(() => expect(document.querySelector("[data-seat=decision-record] [data-testid=send-well]")).not.toBeNull(), { timeout: 5000 });
    expect(document.querySelector("[data-seat=decision-record] [data-testid=send-well]")?.getAttribute("data-doc"))
      .toBe("decision_record:record-85f927aa");
    expect(document.querySelectorAll("[data-testid=send-well]")).toHaveLength(1);
    fireEvent.click(within(fold).getByRole("button", { name: /^Hide$/ }));
    expect(screen.queryByTestId("send-well")).toBeNull();
  });
});

// from room21MorningTruth.test.tsx

describe("B70: a done action says DONE", () => {
  it("the decision row of a done action reads DONE · <time>, not CONFIRMED", async () => {
    const doneAt = "2026-10-08T03:42:00+00:00";
    decisions = [{
      id: "dr-1", text: "Add a CODEOWNERS file", at: "2026-10-07T21:14:00", url: null, kind: "action",
      proposal_id: "p-1", source: "meeting", meeting_title: "Repo hygiene sync",
      confirmed_at: "2026-10-08T03:14:00+00:00", commitment_id: "c-1", done: true, done_at: doneAt,
    }];
    render(<WindowHarness scope="project:p1" />);
    await screen.findByTestId("room-body");
    expect((await screen.findByTestId("done-state")).textContent).toBe(`DONE · ${hhmm(doneAt)}`);
    expect(screen.queryByTestId("confirmed-state")).toBeNull();
  });
});
