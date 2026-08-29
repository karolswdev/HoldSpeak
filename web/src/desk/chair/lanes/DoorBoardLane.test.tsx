import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DoorBoardLane, commandForDoorVerb, computeScrollHint, type DoorProjection } from "./DoorBoardLane";
import { useSurfaceWindows } from "../../components/SurfaceWindows";
import { useDesk } from "../../store";

const apiFetch = vi.hoisted(() => vi.fn());
const newDeliveryId = vi.hoisted(() => vi.fn(() => "door-request-id"));
const openIntelligence = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", () => ({
  apiFetch,
  newDeliveryId,
  readableError: (cause: unknown) => cause instanceof Error ? cause.message : "Request failed",
}));
vi.mock("../../intelligenceNavigation", () => ({ openIntelligence }));
vi.mock("../../surface/gadgets", () => ({
  StringGadget: ({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) => (
    <label>{label}<input aria-label={label} value={value} onChange={(event) => onChange(event.target.value)} /></label>
  ),
}));

const projection: DoorProjection = {
  board: {
    overdue: [{
      id: "action-1", text: "Ship Door", source: "action_item", target_ref: "action_item:action-1",
      owner: "Ada", due: "2020-01-01", stale_score: 4,
      lawful_verbs: [
        { name: "follow_through.complete", arguments: { card_id: "action-1", verb: "done" } },
        { name: "follow_through.complete", arguments: { card_id: "action-1", verb: "snooze" }, required_arguments: ["payload.until"] },
        { name: "follow_through.complete", arguments: { card_id: "action-1", verb: "delegate" }, required_arguments: ["payload.to"] },
      ],
    }],
    now: [{
      id: "loop-1", text: "Close weekly loop", source: "cadence_loop", target_ref: "cadence_loop:loop-1",
      lawful_verbs: [
        { name: "cadence.set_status", arguments: { loop_id: "loop-1", status: "closed" } },
        { name: "cadence.set_status", arguments: { loop_id: "loop-1", status: "killed" } },
      ],
    }],
    waiting: [{
      id: "people-1", text: "Reply to Jordan", source: "people_commitment", target_ref: "people:relationship-1",
      lawful_verbs: [
        { name: "people.commitment.transition", arguments: { commitment_id: "commitment-1", verb: "done" } },
        { name: "unknown.route", arguments: { id: "nope" } },
      ],
    }],
    unassigned: [{ id: "plain-1", text: "No action", source: "action_item", target_ref: "action_item:plain-1", lawful_verbs: [] }],
    active: [{
      id: "thought-1", title: "Think through the Door", body_preview: "A working line", source: "thought",
      target_ref: "thought:thought-1", open_ref: "note:note-1", continuity_state: "review_ready",
      updated_at: "2026-08-27T10:00:00Z",
      lawful_verbs: [{ name: "thought.complete", arguments: { thought_id: "thought-1", expected_aggregate_revision: 7, expected_lifecycle_revision: 3 }, required_arguments: ["request_id"] }],
    }],
  },
  counts: { overdue: 7, now: 6, waiting: 5, active: 4, upcoming_today: 99 },
  upcoming: [{
    id: "calendar-1", source: "calendar_event", target_ref: "calendar_event:calendar-1",
    title: "HS-144-04 owns this", starts_at: "2099-08-28T10:00:00Z",
    ends_at: "2099-08-28T10:30:00Z", location: "Door room",
    meeting_url: "https://meet.example/door", state: "scheduled",
  }],
  calendar_configured: true,
};

function mockDoor(value: DoorProjection = projection) {
  apiFetch.mockImplementation((path: string) => {
    if (path === "/api/door") return Promise.resolve(value);
    return Promise.resolve({});
  });
}

function renderLane() {
  const onOpenInWindow = vi.fn();
  return { onOpenInWindow, ...render(<DoorBoardLane onOpenInWindow={onOpenInWindow} />) };
}

beforeEach(() => {
  vi.clearAllMocks();
  mockDoor();
});
afterEach(() => {
  useDesk.setState({ scheduledRecordings: [], scheduleCreateWindow: null });
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("DoorBoardLane", () => {
  it("renders the exact five server columns in visual order with server counts", async () => {
    renderLane();
    await screen.findByText("Ship Door");
    expect(Array.from(document.querySelectorAll(".door-board-column h4")).map((node) => node.textContent))
      .toEqual(["Overdue", "Now", "Waiting", "Unassigned", "Active"]);
    expect(screen.getByText("7 overdue · 6 now · 5 waiting · 4 active")).toBeInTheDocument();
    expect(screen.getByLabelText("7 overdue items")).toBeInTheDocument();
    expect(screen.getByText("HS-144-04 owns this")).toBeInTheDocument();
    expect(screen.getByText("EVENT")).toBeInTheDocument();
    expect(screen.getByText(/action item · owner Ada · overdue/)).toBeInTheDocument();
    expect(screen.getByText(/thought · review ready · updated/)).toBeInTheDocument();
  });

  it("keeps the Brief capability as an explicit Door-header entry", async () => {
    renderLane();
    await screen.findByText("Ship Door");
    fireEvent.click(screen.getByRole("button", { name: "Brief" }));
    expect(openIntelligence).toHaveBeenCalledWith({ view: "brief" });
  });

  it("uses only the fixed route adapter table", () => {
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "done" } }))
      .toEqual({ endpoint: "/api/follow-through/complete", body: { card_id: "a", verb: "done", payload: {} } });
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "snooze" } }))
      .toBeNull();
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "snooze" } }, { until: "2026-09-01" }))
      .toEqual({ endpoint: "/api/follow-through/complete", body: { card_id: "a", verb: "snooze", payload: { until: "2026-09-01" } } });
    expect(commandForDoorVerb({ name: "follow_through.complete", arguments: { card_id: "a", verb: "delegate" } }, { to: "Jordan" }))
      .toEqual({ endpoint: "/api/follow-through/complete", body: { card_id: "a", verb: "delegate", payload: { to: "Jordan" } } });
    expect(commandForDoorVerb({ name: "cadence.set_status", arguments: { loop_id: "a b", status: "closed" } }))
      .toEqual({ endpoint: "/api/cadence/loops/a%20b/close" });
    expect(commandForDoorVerb({ name: "cadence.set_status", arguments: { loop_id: "a b", status: "killed" } }))
      .toEqual({ endpoint: "/api/cadence/loops/a%20b/kill" });
    expect(commandForDoorVerb({ name: "thought.complete", arguments: { thought_id: "thought-1", expected_aggregate_revision: 7, expected_lifecycle_revision: 3 } }))
      .toEqual({ endpoint: "/api/thoughts/thought-1/complete", body: { request_id: "door-request-id", expected_aggregate_revision: 7, expected_lifecycle_revision: 3 } });
    expect(commandForDoorVerb({ name: "people.commitment.transition", arguments: { commitment_id: "people-1", verb: "dismiss" } }))
      .toEqual({ endpoint: "/api/people/commitments/people-1/transition", body: { verb: "dismiss" } });
    expect(commandForDoorVerb({ name: "unknown.route", arguments: {} })).toBeNull();
  });

  it("does not send incomplete snooze data and expands only its own card", async () => {
    renderLane();
    await screen.findByText("Ship Door");
    fireEvent.click(screen.getByRole("button", { name: "Snooze" }));
    expect(screen.getByLabelText("Until")).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText("Until"), { target: { value: "2026-09-01" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/follow-through/complete", {
      method: "POST", json: { card_id: "action-1", verb: "snooze", payload: { until: "2026-09-01" } },
    }));
  });

  it("revalidates after a write and seats a retryable refusal in flow", async () => {
    apiFetch.mockImplementation((path: string) => {
      if (path === "/api/door") return Promise.resolve(projection);
      return Promise.reject(new Error("verb refused"));
    });
    renderLane();
    await screen.findByText("Ship Door");
    fireEvent.click(within(screen.getByText("Ship Door").closest("article")!).getByRole("button", { name: "Done" }));
    expect(await screen.findByText("DONE FAILED · WRITE REFUSED")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(apiFetch.mock.calls.filter(([path]) => path === "/api/follow-through/complete")).toHaveLength(2));
  });

  it("maps the visible People descriptor to the Slice 0 transition route", async () => {
    renderLane();
    await screen.findByText("Reply to Jordan");
    fireEvent.click(within(screen.getByText("Reply to Jordan").closest("article")!).getByRole("button", { name: "Done" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith("/api/people/commitments/commitment-1/transition", {
      method: "POST", json: { verb: "done" },
    }));
    expect(screen.queryByRole("button", { name: "unknown.route" })).toBeNull();
  });

  it("renders designed empty and initial-error states", async () => {
    const empty: DoorProjection = {
      ...projection,
      board: { overdue: [], now: [], waiting: [], unassigned: [], active: [] },
      upcoming: [],
    };
    mockDoor(empty);
    const { unmount } = renderLane();
    expect(await screen.findByText("Door clear")).toBeInTheDocument();
    expect(screen.getByText("No future time scheduled.")).toBeInTheDocument();
    unmount();
    apiFetch.mockRejectedValue(new Error("Door unavailable"));
    renderLane();
    const error = await screen.findByText("Door unavailable");
    expect(error.closest(".door-board-section")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Brief" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  });

  it("keeps the server's mixed chronology and kind truth without a client sort", async () => {
    const mixed: DoorProjection = {
      ...projection,
      upcoming: [
        {
          id: "recording-1", source: "scheduled_recording", target_ref: "scheduled_recording:recording-1",
          title: "Capture the review", starts_at: "2099-08-27T12:00:00Z", ends_at: "2099-08-27T12:30:00Z",
          location: null, meeting_url: null, state: "idle",
        },
        {
          id: "calendar-2", source: "calendar_event", target_ref: "calendar_event:calendar-2",
          title: "Calendar follows server order", starts_at: "2099-08-27T11:00:00Z", ends_at: "2099-08-27T11:30:00Z",
          location: "North room", meeting_url: "https://meet.example/north", state: "scheduled",
        },
      ],
    };
    mockDoor(mixed);
    renderLane();
    await screen.findByText("Capture the review");
    const rows = Array.from(document.querySelectorAll<HTMLElement>(".door-upcoming-row"));
    expect(rows.map((row) => row.textContent)).toEqual([
      expect.stringContaining("SCHEDULED RECORDING"),
      expect.stringContaining("EVENT"),
    ]);
    expect(rows[0]).toHaveTextContent("Capture the review");
    expect(rows[1]).toHaveTextContent("Calendar follows server order");
    expect(rows[1]).toHaveTextContent("North room");
    expect(within(rows[1]).getByRole("link", { name: "Meeting link" })).toHaveAttribute("href", "https://meet.example/north");
  });

  it("renders a calendar-less schedule normally, with no orphaned calendar chrome", async () => {
    const calendarLess: DoorProjection = {
      ...projection,
      board: { overdue: [], now: [], waiting: [], unassigned: [], active: [] },
      upcoming: [{
        id: "recording-only", source: "scheduled_recording", target_ref: "scheduled_recording:recording-only",
        title: "One future recording", starts_at: "2099-08-27T12:00:00Z", ends_at: "2099-08-27T12:15:00Z",
        location: null, meeting_url: null, state: "idle",
      }],
    };
    mockDoor(calendarLess);
    renderLane();
    expect(await screen.findByText("One future recording")).toBeInTheDocument();
    expect(screen.getByText("SCHEDULED RECORDING")).toBeInTheDocument();
    expect(screen.queryByText(/calendar unavailable/i)).toBeNull();
    expect(screen.queryByText("EVENT")).toBeNull();
  });

  it("opens the existing schedule-create verb and revalidates only after its store list changes", async () => {
    const openScheduleCreate = vi.spyOn(useDesk.getState(), "openScheduleCreate");
    renderLane();
    await screen.findByText("HS-144-04 owns this");
    fireEvent.click(screen.getByRole("button", { name: "Schedule recording" }));
    expect(openScheduleCreate).toHaveBeenCalledTimes(1);
    expect(apiFetch.mock.calls.filter(([path]) => path === "/api/scheduled-recordings")).toHaveLength(0);
    expect(apiFetch.mock.calls.filter(([path]) => path === "/api/door")).toHaveLength(1);

    useDesk.setState({ scheduledRecordings: [{ id: "post-save" }] as never });
    await waitFor(() => expect(apiFetch.mock.calls.filter(([path]) => path === "/api/door")).toHaveLength(2));
    expect(apiFetch.mock.calls.filter(([path]) => path === "/api/scheduled-recordings")).toHaveLength(0);
  });

  /* HS-145-01 — scroll-hint pure function. */
  it("computeScrollHint returns none when nothing clips", () => {
    expect(computeScrollHint(0, 800, 800)).toBe("none");
    expect(computeScrollHint(0, 700, 800)).toBe("none");
  });
  it("computeScrollHint returns right at the left edge", () => {
    expect(computeScrollHint(0, 1120, 393)).toBe("right");
  });
  it("computeScrollHint returns left at the right edge", () => {
    expect(computeScrollHint(727, 1120, 393)).toBe("left");
  });
  it("computeScrollHint returns both at a mid-scroll position", () => {
    expect(computeScrollHint(200, 1120, 393)).toBe("both");
  });
  it("sets data-scroll-hint on the populated viewport wrapper", async () => {
    renderLane();
    await screen.findByText("Ship Door");
    const wrap = document.querySelector(".door-board-hint-wrap");
    expect(wrap).not.toBeNull();
    expect(wrap!.hasAttribute("data-scroll-hint")).toBe(true);
  });

  /* HS-145-02 — connect-calendar affordance. */
  it("shows connect-calendar affordance when calendar is not configured and rail is empty", async () => {
    const unconfigured: DoorProjection = {
      ...projection,
      upcoming: [],
      calendar_configured: false,
    };
    mockDoor(unconfigured);
    renderLane();
    expect(await screen.findByText("No calendar connected.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Connect calendar" })).toBeInTheDocument();
    expect(screen.queryByText("No future time scheduled.")).toBeNull();
  });

  it("shows quiet empty message when calendar is configured and rail is empty", async () => {
    const configured: DoorProjection = {
      ...projection,
      upcoming: [],
      calendar_configured: true,
    };
    mockDoor(configured);
    renderLane();
    expect(await screen.findByText("No future time scheduled.")).toBeInTheDocument();
    expect(screen.queryByText("No calendar connected.")).toBeNull();
    expect(screen.queryByRole("button", { name: "Connect calendar" })).toBeNull();
  });

  /* HS-146-04 — provenance chip rules. */
  it("shows provenance chips on EVENT rows when >1 distinct source_id", async () => {
    const multi: DoorProjection = {
      ...projection,
      upcoming: [
        {
          id: "cal-a", source: "calendar_event", target_ref: "calendar_event:cal-a",
          title: "Work standup", starts_at: "2099-08-28T09:00:00Z", ends_at: "2099-08-28T09:30:00Z",
          location: null, meeting_url: null, state: "scheduled",
          source_id: "src-work", source_label: "Work",
        },
        {
          id: "cal-b", source: "calendar_event", target_ref: "calendar_event:cal-b",
          title: "Personal dentist", starts_at: "2099-08-28T11:00:00Z", ends_at: "2099-08-28T11:30:00Z",
          location: null, meeting_url: null, state: "scheduled",
          source_id: "src-personal", source_label: "Personal",
        },
        {
          id: "rec-1", source: "scheduled_recording", target_ref: "scheduled_recording:rec-1",
          title: "Some recording", starts_at: "2099-08-28T10:00:00Z", ends_at: "2099-08-28T10:30:00Z",
          location: null, meeting_url: null, state: "idle",
        },
      ],
    };
    mockDoor(multi);
    renderLane();
    await screen.findByText("Work standup");
    // Both EVENT rows carry their provenance chip text (uppercase).
    expect(screen.getByText("WORK")).toBeInTheDocument();
    expect(screen.getByText("PERSONAL")).toBeInTheDocument();
    // The chips live inside the door-upcoming-provenance class.
    const chips = document.querySelectorAll(".door-upcoming-provenance");
    expect(chips).toHaveLength(2);
    // The scheduled_recording row must NOT get a chip.
    const recRow = document.querySelector('[data-upcoming-source="scheduled_recording"]');
    expect(recRow?.querySelector(".door-upcoming-provenance")).toBeNull();
  });

  it("omits provenance chips when only 1 source_id exists", async () => {
    const single: DoorProjection = {
      ...projection,
      upcoming: [
        {
          id: "cal-only", source: "calendar_event", target_ref: "calendar_event:cal-only",
          title: "Only event", starts_at: "2099-08-28T09:00:00Z", ends_at: "2099-08-28T09:30:00Z",
          location: null, meeting_url: null, state: "scheduled",
          source_id: "src-one", source_label: "Work",
        },
      ],
    };
    mockDoor(single);
    renderLane();
    await screen.findByText("Only event");
    expect(document.querySelectorAll(".door-upcoming-provenance")).toHaveLength(0);
  });

  it("connect-calendar click opens Settings scoped to Meetings", async () => {
    const openSurfaceWindow = vi.spyOn(useSurfaceWindows.getState(), "openSurfaceWindow");
    const unconfigured: DoorProjection = {
      ...projection,
      upcoming: [],
      calendar_configured: false,
    };
    mockDoor(unconfigured);
    renderLane();
    await screen.findByText("No calendar connected.");
    fireEvent.click(screen.getByRole("button", { name: "Connect calendar" }));
    expect(openSurfaceWindow).toHaveBeenCalledWith("configure-settings", "meetings");
  });

  /* HS-147-02 — RECORD THIS / ARMED+CANCEL? on calendar event rows. */
  describe("event arm/cancel (HS-147-02)", () => {
    it("renders RECORD THIS button on unarmed calendar_event rows", async () => {
      mockDoor();
      renderLane();
      await screen.findByText("HS-144-04 owns this");
      const btn = screen.getByTestId("door-record-this");
      expect(btn).toBeInTheDocument();
      expect(btn).toHaveTextContent("Record this");
    });

    it("does not render RECORD THIS on scheduled_recording rows", async () => {
      const withRec: DoorProjection = {
        ...projection,
        upcoming: [
          {
            id: "rec-1", source: "scheduled_recording", target_ref: "scheduled_recording:rec-1",
            title: "A recording", starts_at: "2099-08-28T12:00:00Z", ends_at: "2099-08-28T12:30:00Z",
            location: null, meeting_url: null, state: "idle",
          },
        ],
      };
      mockDoor(withRec);
      renderLane();
      await screen.findByText("A recording");
      expect(screen.queryByTestId("door-record-this")).toBeNull();
      expect(screen.queryByTestId("door-armed-chip")).toBeNull();
    });

    it("arms an event recording via POST with calendar_event_id on RECORD THIS click", async () => {
      apiFetch.mockImplementation((path: string, opts?: { method?: string; json?: unknown }) => {
        if (path === "/api/door") return Promise.resolve(projection);
        if (path === "/api/scheduled-recordings" && opts?.method === "POST") {
          return Promise.resolve({ success: true, schedule: { id: "sched-new" } });
        }
        if (path === "/api/scheduled-recordings") {
          return Promise.resolve({ success: true, schedules: [] });
        }
        return Promise.resolve({});
      });
      renderLane();
      await screen.findByText("HS-144-04 owns this");
      fireEvent.click(screen.getByTestId("door-record-this"));
      await waitFor(() => {
        expect(apiFetch).toHaveBeenCalledWith("/api/scheduled-recordings", {
          method: "POST",
          json: { calendar_event_id: "calendar-1" },
        });
      });
    });

    it("renders ARMED chip and CANCEL? verb when armed_schedule_id is present", async () => {
      const armed: DoorProjection = {
        ...projection,
        upcoming: [{
          id: "calendar-armed", source: "calendar_event", target_ref: "calendar_event:calendar-armed",
          title: "Armed meeting", starts_at: "2099-08-28T10:00:00Z", ends_at: "2099-08-28T10:30:00Z",
          location: null, meeting_url: null, state: "scheduled",
          armed_schedule_id: "sched-42",
        }],
      };
      mockDoor(armed);
      renderLane();
      await screen.findByText("Armed meeting");
      expect(screen.getByTestId("door-armed-chip")).toHaveTextContent("ARMED");
      expect(screen.getByTestId("door-cancel-prompt")).toHaveTextContent("Cancel?");
      expect(screen.queryByTestId("door-record-this")).toBeNull();
    });

    it("two-beat cancel: first tap shows confirm, second fires DELETE", async () => {
      const armed: DoorProjection = {
        ...projection,
        upcoming: [{
          id: "calendar-armed", source: "calendar_event", target_ref: "calendar_event:calendar-armed",
          title: "Armed meeting", starts_at: "2099-08-28T10:00:00Z", ends_at: "2099-08-28T10:30:00Z",
          location: null, meeting_url: null, state: "scheduled",
          armed_schedule_id: "sched-42",
        }],
      };
      apiFetch.mockImplementation((path: string, opts?: { method?: string }) => {
        if (path === "/api/door") return Promise.resolve(armed);
        if (path.startsWith("/api/scheduled-recordings/sched-42") && opts?.method === "DELETE") {
          return Promise.resolve({ success: true });
        }
        if (path === "/api/scheduled-recordings") {
          return Promise.resolve({ success: true, schedules: [] });
        }
        return Promise.resolve({});
      });
      renderLane();
      await screen.findByText("Armed meeting");
      // Beat 1: CANCEL? prompt
      fireEvent.click(screen.getByTestId("door-cancel-prompt"));
      // Beat 2: confirm Cancel button appears
      const confirm = screen.getByTestId("door-cancel-confirm");
      expect(confirm).toHaveTextContent("Cancel");
      fireEvent.click(confirm);
      await waitFor(() => {
        expect(apiFetch).toHaveBeenCalledWith("/api/scheduled-recordings/sched-42", {
          method: "DELETE",
        });
      });
    });

    it("renders in-flow refusal when arming fails with a typed code", async () => {
      const errorPayload = { success: false, error: "Event already ended", code: "event_already_ended" };
      apiFetch.mockImplementation((path: string, opts?: { method?: string }) => {
        if (path === "/api/door") return Promise.resolve(projection);
        if (path === "/api/scheduled-recordings" && opts?.method === "POST") {
          const err = new Error("Event already ended");
          (err as unknown as Record<string, unknown>).payload = errorPayload;
          return Promise.reject(err);
        }
        return Promise.resolve({});
      });
      renderLane();
      await screen.findByText("HS-144-04 owns this");
      fireEvent.click(screen.getByTestId("door-record-this"));
      const refusal = await screen.findByTestId("door-arm-refusal");
      expect(refusal).toHaveTextContent("EVENT ENDED");
    });

    it("renders in-flow refusal for event_already_armed conflict", async () => {
      const errorPayload = { success: false, error: "Already armed", code: "event_already_armed" };
      apiFetch.mockImplementation((path: string, opts?: { method?: string }) => {
        if (path === "/api/door") return Promise.resolve(projection);
        if (path === "/api/scheduled-recordings" && opts?.method === "POST") {
          const err = new Error("Already armed");
          (err as unknown as Record<string, unknown>).payload = errorPayload;
          return Promise.reject(err);
        }
        return Promise.resolve({});
      });
      renderLane();
      await screen.findByText("HS-144-04 owns this");
      fireEvent.click(screen.getByTestId("door-record-this"));
      const refusal = await screen.findByTestId("door-arm-refusal");
      expect(refusal).toHaveTextContent("ALREADY ARMED");
    });

    it("renders cancel refusal in-flow when DELETE fails", async () => {
      const armed: DoorProjection = {
        ...projection,
        upcoming: [{
          id: "calendar-armed", source: "calendar_event", target_ref: "calendar_event:calendar-armed",
          title: "Armed meeting", starts_at: "2099-08-28T10:00:00Z", ends_at: "2099-08-28T10:30:00Z",
          location: null, meeting_url: null, state: "scheduled",
          armed_schedule_id: "sched-42",
        }],
      };
      const errorPayload = { success: false, error: "Not found", code: "not_found" };
      apiFetch.mockImplementation((path: string, opts?: { method?: string }) => {
        if (path === "/api/door") return Promise.resolve(armed);
        if (path.startsWith("/api/scheduled-recordings/sched-42") && opts?.method === "DELETE") {
          const err = new Error("Not found");
          (err as unknown as Record<string, unknown>).payload = errorPayload;
          return Promise.reject(err);
        }
        return Promise.resolve({});
      });
      renderLane();
      await screen.findByText("Armed meeting");
      fireEvent.click(screen.getByTestId("door-cancel-prompt"));
      fireEvent.click(screen.getByTestId("door-cancel-confirm"));
      const refusal = await screen.findByTestId("door-arm-refusal");
      expect(refusal).toHaveTextContent("EVENT NOT FOUND");
    });

    it("has stable data-testid selectors on all arm/cancel elements", async () => {
      const armed: DoorProjection = {
        ...projection,
        upcoming: [
          {
            id: "cal-unarmed", source: "calendar_event", target_ref: "calendar_event:cal-unarmed",
            title: "Unarmed event", starts_at: "2099-08-28T09:00:00Z", ends_at: "2099-08-28T09:30:00Z",
            location: null, meeting_url: null, state: "scheduled",
          },
          {
            id: "cal-armed", source: "calendar_event", target_ref: "calendar_event:cal-armed",
            title: "Armed event", starts_at: "2099-08-28T10:00:00Z", ends_at: "2099-08-28T10:30:00Z",
            location: null, meeting_url: null, state: "scheduled",
            armed_schedule_id: "sched-99",
          },
        ],
      };
      mockDoor(armed);
      renderLane();
      await screen.findByText("Unarmed event");
      // All arm actions containers
      expect(screen.getAllByTestId("door-arm-actions")).toHaveLength(2);
      // Unarmed row has RECORD THIS
      expect(screen.getByTestId("door-record-this")).toBeInTheDocument();
      // Armed row has chip + cancel prompt
      expect(screen.getByTestId("door-armed-chip")).toBeInTheDocument();
      expect(screen.getByTestId("door-cancel-prompt")).toBeInTheDocument();
    });
  });

  /* HS-149-01 L2 — People store state line. */
  describe("people store state (HS-149-01 L2)", () => {
    it("renders a quiet named state line when people_store_state is not ready", async () => {
      const locked: DoorProjection = { ...projection, people_store_state: "locked" };
      mockDoor(locked);
      renderLane();
      await screen.findByText("Ship Door");
      expect(screen.getByTestId("door-people-state")).toHaveTextContent("People store locked");
    });

    it("renders no state line when people_store_state is ready", async () => {
      const ready: DoorProjection = { ...projection, people_store_state: "ready" };
      mockDoor(ready);
      renderLane();
      await screen.findByText("Ship Door");
      expect(screen.queryByTestId("door-people-state")).toBeNull();
    });

    it("renders no state line when people_store_state is absent", async () => {
      mockDoor(projection);
      renderLane();
      await screen.findByText("Ship Door");
      expect(screen.queryByTestId("door-people-state")).toBeNull();
    });

    it("renders the unconfigured label for unconfigured state", async () => {
      const unconfigured: DoorProjection = { ...projection, people_store_state: "unconfigured" };
      mockDoor(unconfigured);
      renderLane();
      await screen.findByText("Ship Door");
      expect(screen.getByTestId("door-people-state")).toHaveTextContent("People not set up");
    });

    it("renders unavailable label for unavailable state", async () => {
      const unavail: DoorProjection = { ...projection, people_store_state: "unavailable" };
      mockDoor(unavail);
      renderLane();
      await screen.findByText("Ship Door");
      expect(screen.getByTestId("door-people-state")).toHaveTextContent("People store unavailable");
    });
  });
});
