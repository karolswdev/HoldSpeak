// HS-111-03 — re-pointed to the one-row attention slab (audit §3.5):
// state token, RETAINED fact, REMAINING token, RETRY/SKIP verbs on
// the row. The wire contract under test is unchanged.
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

  it("tokens the state, the retained work, and the remaining work", async () => {
    mockedApiFetch.mockResolvedValueOnce(failedRecovery);

    render(<MeetingIntelRecovery meetingId="meeting-1" />);

    expect(await screen.findByText("PARTIAL")).toBeInTheDocument();
    // Retained counts token from the completed facts (3 SEG / 2 ART).
    expect(screen.getByText("RETAINED 3 SEG / 2 ART")).toBeInTheDocument();
    const remaining = screen.getByText(
      "REMAINING: ROUTED MEETING INTELLIGENCE",
    );
    expect(remaining).toBeInTheDocument();
    // The failure reason stays on the token, not as body prose.
    expect(remaining).toHaveAttribute("title", "Decision extraction timed out.");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Skip" })).toBeInTheDocument();
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
    fireEvent.click(await screen.findByRole("button", { name: "Skip" }));

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenLastCalledWith(
        "/api/meetings/meeting-1/intel-recovery/skip",
        { method: "POST" },
      ),
    );
    expect(await screen.findByText("SKIPPED")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Skip" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
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

    expect(await screen.findByText("RUNNING")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
