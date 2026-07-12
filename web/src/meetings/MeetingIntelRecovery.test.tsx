import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../lib/api";
import { MeetingIntelRecovery } from "./MeetingIntelRecovery";

vi.mock("../lib/api", () => ({
  apiFetch: vi.fn(),
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed.",
}));

const mockedApiFetch = vi.mocked(apiFetch);

const failedRecovery = {
  meeting_id: "meeting-1",
  visible: true,
  state: "partial",
  headline: "Meeting saved · intelligence incomplete",
  completed: [
    { label: "Meeting", detail: "Saved" },
    { label: "Transcript", detail: "3 saved segments" },
    {
      label: "Meeting analysis",
      detail: "Summary, topics, and action items saved",
    },
    { label: "Artifacts", detail: "2 saved artifacts" },
  ],
  remaining: {
    label: "Routed meeting intelligence",
    detail: "Decision extraction timed out.",
  },
  job: {
    status: "failed",
    attempts: 3,
    requested_at: "2026-07-11T12:00:00",
    updated_at: "2026-07-11T12:01:00",
  },
  actions: { retry: true, skip: true },
};

describe("HS-93-06 Meeting intelligence recovery", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
  });

  it("names completed and remaining work without claiming Ready", async () => {
    mockedApiFetch.mockResolvedValueOnce(failedRecovery);

    render(<MeetingIntelRecovery meetingId="meeting-1" />);

    expect(
      await screen.findByRole("heading", {
        name: "Meeting saved · intelligence incomplete",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("3 saved segments")).toBeInTheDocument();
    expect(screen.getByText("2 saved artifacts")).toBeInTheDocument();
    expect(screen.getByText("Routed meeting intelligence")).toBeInTheDocument();
    expect(
      screen.getByText("Decision extraction timed out."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Retry remaining" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Skip remaining" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Ready")).not.toBeInTheDocument();
  });

  it("skips only remaining work and keeps Retry available", async () => {
    const onChanged = vi.fn();
    mockedApiFetch.mockResolvedValueOnce(failedRecovery).mockResolvedValueOnce({
      success: true,
      recovery: {
        ...failedRecovery,
        state: "skipped",
        headline: "Meeting saved · intelligence skipped",
        remaining: {
          ...failedRecovery.remaining,
          detail:
            "Meeting saved. Retained: 3 transcript segments, summary, topics, and action items, 2 artifacts. Remaining intelligence skipped.",
        },
        job: null,
        actions: { retry: true, skip: false },
      },
    });

    render(
      <MeetingIntelRecovery meetingId="meeting-1" onChanged={onChanged} />,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Skip remaining" }),
    );

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenLastCalledWith(
        "/api/meetings/meeting-1/intel-recovery/skip",
        { method: "POST" },
      ),
    );
    expect(
      await screen.findByRole("heading", {
        name: "Meeting saved · intelligence skipped",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Skip remaining" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Retry remaining" }),
    ).toBeInTheDocument();
    expect(onChanged).toHaveBeenCalled();
  });

  it("protects a running attempt from competing recovery actions", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      ...failedRecovery,
      state: "running",
      headline: "Meeting saved · intelligence running",
      job: { ...failedRecovery.job, status: "running" },
      actions: { retry: false, skip: false },
    });

    render(<MeetingIntelRecovery meetingId="meeting-1" />);

    expect(
      await screen.findByText("Wait for the running attempt to finish."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
