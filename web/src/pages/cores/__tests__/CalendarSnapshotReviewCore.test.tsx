// HS-146-07 — Calendar snapshot review core tests.
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CalendarSnapshotReviewCore } from "../CalendarSnapshotReviewCore";
import CALENDAR_SOURCES from "../../../test/wire/calendar-sources.wire.json";

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (cause: unknown) =>
    cause instanceof Error ? cause.message : "Request failed",
}));

vi.mock("../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({
    verbs,
    receipt,
  }: {
    verbs?: React.ReactNode;
    receipt?: React.ReactNode;
  }) => (
    <div data-testid="surface-footer">
      <div className="surface-footer-receipt">{receipt}</div>
      <div className="surface-footer-verbs">{verbs}</div>
    </div>
  ),
}));

vi.mock("../../../desk/surface/Surface", async (importOriginal) => {
  const actual = (await importOriginal()) as Record<string, unknown>;
  return {
    ...actual,
    SurfaceSection: ({
      label,
      children,
    }: {
      label?: string;
      children: React.ReactNode;
    }) => (
      <section data-testid={`section-${label}`}>
        <h3>{label}</h3>
        {children}
      </section>
    ),
  };
});

const VALID_SCOPE = JSON.stringify({
  anchor_date: "2026-08-24",
  anchor_confidence: "visible_header",
  events: [
    {
      title: "Standup",
      weekday: "monday",
      start_time: "09:00",
      end_time: "09:30",
      location: "Room 1",
    },
    {
      title: "Review",
      weekday: "friday",
      start_time: "14:00",
      end_time: "15:00",
      location: null,
    },
  ],
});

beforeEach(() => apiFetch.mockReset());

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((accept) => {
    resolve = accept;
  });
  return { promise, resolve };
}

describe("CalendarSnapshotReviewCore: the empty window (W1-TRUTH, atlas 2026-10-27)", () => {
  it("with no screenshot it says so, with Import image and Check sources in its toolbar, never a red Can't read", async () => {
    apiFetch.mockImplementation(async (url: string) => (url === "/api/calendar/sources" ? structuredClone(CALENDAR_SOURCES.wire) : undefined));
    render(<CalendarSnapshotReviewCore />);
    // Atlas pass 3 #21: the empty face is the object, one line, one verb.
    const empty = screen.getByTestId("calendar-snapshot-empty");
    expect(empty.querySelector('[data-object="meeting"] img.surface-state-sprite')).toBeTruthy();
    expect(empty.querySelector(".surface-state-line")?.textContent).toBe("No screenshot yet");
    expect(within(empty).getAllByRole("button").map((b) => b.textContent)).toEqual(["Import image"]);
    const toolbar = screen.getByTestId("calendar-snapshot-toolbar");
    expect(within(toolbar).getByRole("button", { name: "Import image" })).toBeTruthy();
    expect(within(toolbar).getByRole("button", { name: "Check sources" })).toBeTruthy();
    expect(screen.queryByTestId("calendar-snapshot-refusal")).toBeNull();
    expect(screen.queryByText("Calendar snapshot", { selector: "h3" })).toBeNull();
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/calendar/sources"));
  });

  it("a desk with working feeds says how many are connected; Check sources reads them again", async () => {
    const working = structuredClone(CALENDAR_SOURCES.wire);
    working.sources = [
      { ...working.sources[0], status: "success" },
      { ...working.sources[0], id: "src_home", label: "HOME", status: "success" },
    ];
    apiFetch.mockImplementation(async (url: string) => (url === "/api/calendar/sources" ? structuredClone(working) : undefined));
    render(<CalendarSnapshotReviewCore />);
    expect((await screen.findByTestId("calendar-snapshot-sources")).textContent).toBe("2 sources connected");
    fireEvent.click(screen.getByRole("button", { name: "Check sources" }));
    await waitFor(() => expect(apiFetch.mock.calls.filter(([url]) => url === "/api/calendar/sources")).toHaveLength(2));
  });
});

describe("CalendarSnapshotReviewCore", () => {
  it("renders events from valid scope", () => {
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    expect(screen.getByDisplayValue("Standup")).toBeTruthy();
    expect(screen.getByDisplayValue("Review")).toBeTruthy();
    expect(screen.getByDisplayValue("2026-08-24")).toBeTruthy();
  });

  it("shows editable anchor field", () => {
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const input = screen.getByDisplayValue("2026-08-24");
    expect(input).toBeTruthy();
    fireEvent.change(input, { target: { value: "2026-09-07" } });
    expect(screen.getByDisplayValue("2026-09-07")).toBeTruthy();
  });

  it("Confirm disabled without valid anchor", () => {
    const noAnchor = JSON.stringify({
      anchor_date: null,
      anchor_confidence: "absent",
      events: [
        {
          title: "Meeting",
          weekday: "tuesday",
          start_time: "10:00",
          end_time: "11:00",
        },
      ],
    });
    render(<CalendarSnapshotReviewCore scope={noAnchor} />);
    const confirm = screen.getByText("Confirm");
    expect(confirm).toBeTruthy();
    expect((confirm as HTMLButtonElement).disabled).toBe(true);
  });

  it("Confirm enabled with valid anchor", () => {
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const confirm = screen.getByText("Confirm");
    expect((confirm as HTMLButtonElement).disabled).toBe(false);
  });

  it("shows unreadable refusal in-flow", () => {
    const errorScope = JSON.stringify({
      error: "unreadable_screenshot",
      events: [],
    });
    render(<CalendarSnapshotReviewCore scope={errorScope} />);
    // UX-CANON A10: a token pair, never a sentence.
    expect(screen.getByTestId("calendar-snapshot-refusal").textContent).toBe(
      "Can't read Not a calendar image",
    );
  });

  // replaces (the calendar leg): tests/e2e/test_finish_face_polish_glass.py::TestFinishFacePolish::test_the_named_faces_say_names_and_plain_reasons
  it("names the no-model refusal in plain words, never the hub's code (B0-L1)", () => {
    render(
      <CalendarSnapshotReviewCore
        scope={JSON.stringify({
          error: "no_vision_model_assigned",
          events: [],
        })}
      />,
    );
    const refusal = screen.getByTestId("calendar-snapshot-refusal");
    expect(refusal.textContent).toBe("Can't read No vision model");
    expect(refusal.textContent).not.toMatch(/_/);
  });

  it("never prints an unknown code with underscores", () => {
    render(
      <CalendarSnapshotReviewCore
        scope={JSON.stringify({ error: "vision_engine_timed_out", events: [] })}
      />,
    );
    expect(screen.getByTestId("calendar-snapshot-refusal").textContent).toBe(
      "Can't read Vision engine timed out",
    );
  });

  it("cancel (closing window) writes nothing", () => {
    // The review surface has no CANCEL button that writes anything.
    // Closing the window (handled by SurfaceWindows) writes nothing.
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    // No writes to the API without explicit CONFIRM click
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("confirm sends events to the confirm endpoint", async () => {
    apiFetch.mockResolvedValue({
      success: true,
      events_count: 2,
      source_label: "O365 SNAPSHOT",
    });
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const confirm = screen.getByText("Confirm");
    fireEvent.click(confirm);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    const [url, opts] = apiFetch.mock.calls[0];
    expect(url).toBe("/api/calendar/snapshot/confirm");
    const body = JSON.parse(opts.body);
    expect(body.anchor_date).toBe("2026-08-24");
    expect(body.events).toEqual(JSON.parse(VALID_SCOPE).events);
  });

  it("shows done state after successful confirm", async () => {
    apiFetch.mockResolvedValue({
      success: true,
      events_count: 2,
      source_label: "O365 SNAPSHOT",
    });
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    fireEvent.click(screen.getByText("Confirm"));
    const receipt = await screen.findByTestId("calendar-snapshot-receipt");
    expect(receipt).toHaveTextContent("Saved");
    expect(receipt).toHaveTextContent("2 events");
    expect(receipt).toHaveTextContent("O365 SNAPSHOT");
  });

  it("keeps every text field mounted and focused through successive keystrokes", async () => {
    const user = userEvent.setup();
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const edits = [
      ["Week of", "2026-08-24", " "],
      ["Event 1 title", "Standup", " ready"],
      ["Event 1 start", "09:00", "1"],
      ["Event 1 end", "09:30", "2"],
      ["Event 1 location", "Room 1", " west"],
    ];
    for (const [name, initial, suffix] of edits) {
      const field = screen.getByRole("textbox", { name });
      await user.type(field, suffix);
      expect(screen.getByRole("textbox", { name })).toBe(field);
      expect(field).toHaveValue(initial + suffix);
      expect(field).toHaveFocus();
    }
    const weekday = screen.getByRole("combobox", { name: "Event 1 weekday" });
    weekday.focus();
    await user.keyboard("{End}{Enter}");
    expect(weekday).toHaveValue("sunday");
    expect(weekday).toHaveFocus();
  });

  it("arms Remove and preserves the next event's fields and focus when a preceding row goes", () => {
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const secondFields = ["title", "start", "end", "location"].map((field) =>
      screen.getByRole("textbox", { name: `Event 2 ${field}` }),
    );
    const weekday = screen.getByRole("combobox", { name: "Event 2 weekday" });
    const remove = screen.getByRole("button", { name: "Remove event 1" });
    secondFields[0].focus();
    fireEvent.click(remove);
    expect(remove).toHaveTextContent("Remove?");
    expect(screen.getByDisplayValue("Standup")).toBeTruthy();
    fireEvent.click(remove);
    expect(screen.queryByDisplayValue("Standup")).toBeNull();
    ["title", "start", "end", "location"].forEach((field, index) => {
      expect(screen.getByRole("textbox", { name: `Event 1 ${field}` })).toBe(
        secondFields[index],
      );
    });
    expect(screen.getByRole("combobox", { name: "Event 1 weekday" })).toBe(
      weekday,
    );
    expect(secondFields[0]).toHaveValue("Review");
    expect(secondFields[0]).toHaveFocus();
  });

  it("keeps the review mounted, freezes all controls, and admits one pending Confirm", async () => {
    const pending = deferred<{
      success: boolean;
      events_count: number;
      source_label: string;
    }>();
    apiFetch.mockReturnValue(pending.promise);
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const title = screen.getByRole("textbox", { name: "Event 1 title" });
    const anchor = screen.getByRole("textbox", { name: "Week of" });
    const confirm = screen.getByRole("button", { name: "Confirm" });
    act(() => {
      confirm.click();
      confirm.click();
    });
    expect(apiFetch).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("textbox", { name: "Event 1 title" })).toBe(title);
    expect(screen.getByRole("textbox", { name: "Week of" })).toBe(anchor);
    expect(screen.getByText("Saving")).toBeTruthy();
    expect(confirm).toBeDisabled();
    expect(confirm).toHaveAttribute("aria-busy", "true");
    screen
      .getAllByRole("textbox")
      .forEach((field) => expect(field).toBeDisabled());
    screen
      .getAllByRole("combobox")
      .forEach((field) => expect(field).toBeDisabled());
    screen
      .getAllByRole("button")
      .forEach((button) => expect(button).toBeDisabled());
    fireEvent.change(title, { target: { value: "Changed while pending" } });
    expect(title).toHaveValue("Standup");
    await act(async () => {
      pending.resolve({
        success: true,
        events_count: 2,
        source_label: "Team calendar",
      });
      await pending.promise;
    });
    expect(screen.getByTestId("calendar-snapshot-receipt")).toHaveTextContent(
      "Team calendar",
    );
  });

  it("keeps the reviewed anchor and events after refusal and retries the identical payload", async () => {
    apiFetch
      .mockResolvedValueOnce({ success: false, error: "calendar_unavailable" })
      .mockResolvedValueOnce({
        success: true,
        events_count: 1,
        source_label: "Team calendar",
      });
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const title = screen.getByRole("textbox", { name: "Event 1 title" });
    const anchor = screen.getByRole("textbox", { name: "Week of" });
    fireEvent.change(title, { target: { value: "Ready for release" } });
    fireEvent.change(anchor, { target: { value: "2026-10-19 " } });
    const remove = screen.getByRole("button", { name: "Remove event 2" });
    fireEvent.click(remove);
    fireEvent.click(remove);
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    const retry = await screen.findByRole("button", { name: "Retry" });
    expect(
      screen.getByTestId("calendar-snapshot-save-refusal"),
    ).toHaveTextContent("Can't save Calendar unavailable");
    expect(screen.getByRole("textbox", { name: "Event 1 title" })).toBe(title);
    expect(title).toHaveValue("Ready for release");
    expect(anchor).toHaveValue("2026-10-19 ");
    expect(title).not.toBeDisabled();
    const firstBody = apiFetch.mock.calls[0][1].body;
    expect(JSON.parse(firstBody)).toEqual({
      anchor_date: "2026-10-19",
      events: [
        { ...JSON.parse(VALID_SCOPE).events[0], title: "Ready for release" },
      ],
    });
    fireEvent.click(retry);
    await screen.findByTestId("calendar-snapshot-receipt");
    expect(apiFetch).toHaveBeenCalledTimes(2);
    expect(apiFetch.mock.calls[1][1].body).toBe(firstBody);
  });

  it("retains the draft on a rejected request and lets an edit submit newer work", async () => {
    apiFetch
      .mockRejectedValueOnce(new Error("Calendar unavailable"))
      .mockResolvedValueOnce({
        success: true,
        events_count: 2,
        source_label: "Revised calendar",
      });
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const title = screen.getByRole("textbox", { name: "Event 1 title" });
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    await screen.findByRole("button", { name: "Retry" });
    expect(title).toHaveValue("Standup");
    fireEvent.change(title, { target: { value: "Revised standup" } });
    expect(screen.queryByTestId("calendar-snapshot-save-refusal")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    await screen.findByTestId("calendar-snapshot-receipt");
    expect(JSON.parse(apiFetch.mock.calls[1][1].body).events[0].title).toBe(
      "Revised standup",
    );
  });

  it("places the wrapping refusal beside Retry in the footer outside the scrolling review", async () => {
    apiFetch.mockResolvedValue({
      success: false,
      error: "calendar_unavailable",
    });
    const { container } = render(
      <CalendarSnapshotReviewCore scope={VALID_SCOPE} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    const refusal = await screen.findByTestId("calendar-snapshot-save-refusal");
    const footer = screen.getByTestId("surface-footer");
    const receipt = footer.querySelector(".surface-footer-receipt");
    const verbs = footer.querySelector(".surface-footer-verbs");
    expect(receipt).toContainElement(refusal);
    expect(verbs).toContainElement(
      screen.getByRole("button", { name: "Retry" }),
    );
    expect(refusal).toHaveAttribute("role", "alert");
    expect(refusal).toHaveClass("surface-footer-receipt-line");
    expect(refusal).toHaveAttribute("data-wrap");
    expect(refusal).toHaveTextContent("Can't save Calendar unavailable");
    expect(
      container.querySelector(".calendar-snapshot-fields"),
    ).not.toContainElement(refusal);
    expect(screen.queryByTestId("section-Save")).toBeNull();
  });

  it("disables Confirm after removing every draft event without a zero counter", () => {
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    for (let index = 0; index < 2; index++) {
      const remove = screen.getByRole("button", { name: "Remove event 1" });
      fireEvent.click(remove);
      fireEvent.click(remove);
    }
    expect(screen.getByRole("button", { name: "Confirm" })).toBeDisabled();
    expect(screen.queryByText(/EVENTS 0|0 events/i)).toBeNull();
    expect(apiFetch).not.toHaveBeenCalled();
  });

  it("never invents a source or event count absent from the accepted response", async () => {
    apiFetch.mockResolvedValue({ success: true });
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    const receipt = await screen.findByTestId("calendar-snapshot-receipt");
    expect(receipt).toHaveTextContent("Saved");
    expect(receipt).not.toHaveTextContent("O365");
    expect(receipt).not.toHaveTextContent(/events/i);
  });
});
