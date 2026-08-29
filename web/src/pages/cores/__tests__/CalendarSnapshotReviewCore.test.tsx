// HS-146-07 — Calendar snapshot review core tests.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CalendarSnapshotReviewCore } from "../CalendarSnapshotReviewCore";

const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../../../lib/api", () => ({
  apiFetch,
  readableError: (cause: unknown) =>
    cause instanceof Error ? cause.message : "Request failed",
}));

vi.mock("../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({ verbs }: { verbs?: React.ReactNode }) => (
    <div data-testid="surface-footer">{verbs}</div>
  ),
}));

vi.mock("../../../desk/surface/Surface", async (importOriginal) => {
  const actual = await importOriginal() as Record<string, unknown>;
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

vi.mock("../../../components/signal/Signal", () => ({
  Button: ({
    children,
    onClick,
    disabled,
    ...rest
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    disabled?: boolean;
    dense?: boolean;
  }) => (
    <button onClick={onClick} disabled={disabled} {...rest}>
      {children}
    </button>
  ),
}));

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

  it("CONFIRM disabled without valid anchor", () => {
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
    const confirm = screen.getByText("CONFIRM");
    expect(confirm).toBeTruthy();
    expect((confirm as HTMLButtonElement).disabled).toBe(true);
  });

  it("CONFIRM enabled with valid anchor", () => {
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    const confirm = screen.getByText("CONFIRM");
    expect((confirm as HTMLButtonElement).disabled).toBe(false);
  });

  it("shows unreadable refusal in-flow", () => {
    const errorScope = JSON.stringify({
      error: "unreadable_screenshot",
      events: [],
    });
    render(<CalendarSnapshotReviewCore scope={errorScope} />);
    expect(
      screen.getByText(
        "Could not read the screenshot as a calendar. Try a clearer image.",
      ),
    ).toBeTruthy();
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
    const confirm = screen.getByText("CONFIRM");
    fireEvent.click(confirm);
    await waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    const [url, opts] = apiFetch.mock.calls[0];
    expect(url).toBe("/api/calendar/snapshot/confirm");
    const body = JSON.parse(opts.body);
    expect(body.anchor_date).toBe("2026-08-24");
    expect(body.events).toHaveLength(2);
  });

  it("shows done state after successful confirm", async () => {
    apiFetch.mockResolvedValue({
      success: true,
      events_count: 2,
      source_label: "O365 SNAPSHOT",
    });
    render(<CalendarSnapshotReviewCore scope={VALID_SCOPE} />);
    fireEvent.click(screen.getByText("CONFIRM"));
    await waitFor(() =>
      expect(
        screen.getByText("2 events imported as O365 SNAPSHOT"),
      ).toBeTruthy(),
    );
  });
});
