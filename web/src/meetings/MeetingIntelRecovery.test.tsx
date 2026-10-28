// HS-111-03 — re-pointed to the one-row attention slab (audit §3.5):
// state as a dot and a word, one quiet sentence (kept · not done), RETRY/SKIP verbs on the row
// (Window Program W4, the words: no caps tokens).
// HS-201-06 — the words are plain ones now (Constitution tenet 4,
// ASD-STE100); the wire contract under test is unchanged.
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  // HS-201-04: the recovery read model carries the disclosed route; the
  // Retry verb is withheld without one (a verb that cannot run is a lie).
  planned_route: {
    status: "ready",
    reason_code: null,
    selection_hash: "sha256:recovery",
    legs: [{ ordinal: 1, host: "local", boundary: "local" }],
  },
  run_receipt: null,
};

describe("HS-93-06 Meeting intelligence recovery", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
  });

  it("tokens the state, the retained work, and the remaining work", async () => {
    mockedApiFetch.mockResolvedValueOnce(failedRecovery);

    render(<MeetingIntelRecovery meetingId="meeting-1" />);

    expect(await screen.findByText("Partial")).toBeInTheDocument();
    // HS-201-06: whole words, no clipped jargon (was RETAINED 3 SEG / 2 ART).
    // W4 (the words): one sentence pair in sentence case, never caps tokens.
    const remaining = screen.getByText("Kept 3 segments and 2 artifacts. The artifacts did not finish.");
    expect(remaining).toBeInTheDocument();
    // The failure reason stays on the token, not as body prose.
    expect(remaining).toHaveAttribute("title", "Decision extraction timed out.");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Skip" })).toBeInTheDocument();
    expect(screen.queryByText("Ready")).not.toBeInTheDocument();
  });

  it("W4 (the words): a failed summary is a dot and a word and one quiet sentence", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      ...failedRecovery,
      state: "error",
      completed: [{ label: "Transcript", detail: "2 saved segments" }],
      remaining: { label: "Summary, topics, action items", detail: "The engine did not answer." },
    });
    render(<MeetingIntelRecovery meetingId="meeting-1" />);
    expect((await screen.findByTestId("recovery-state")).textContent).toBe("Failed");
    expect(screen.getByTestId("recovery-sentence").textContent).toBe(
      "Kept 2 segments. The summary, topics and action items did not finish.",
    );
    expect(document.body.textContent ?? "").not.toMatch(/ERROR|KEPT|NOT DONE/);
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
    expect(await screen.findByText("Skipped")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Skip" }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(onChanged).toHaveBeenCalled();
  });

  it("protects a running attempt from competing recovery actions", async () => {
    // HS-172: RUNNING state is now shown in the header chip; the legacy
    // recovery panel is suppressed (returns null). The component fetches
    // but renders nothing for running/queued states.
    mockedApiFetch.mockResolvedValueOnce({
      ...failedRecovery,
      state: "running",
      headline: "Meeting saved · intelligence running",
      job: { ...failedRecovery.job, status: "running" },
      actions: { retry: false, skip: false },
    });

    const { container } = render(<MeetingIntelRecovery meetingId="meeting-1" />);
    // Wait for fetch to complete.
    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalledTimes(1));
    // The panel should NOT render for running state.
    expect(container.querySelector(".meeting-intel-recovery")).toBeNull();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("reveals local outcome Retry on record revision without a route or another model run", async () => {
    const pending = {
      ...failedRecovery, local_publication: true, planned_route: { status: "off", legs: [] },
      remaining: { label: "Decisions and action items", detail: "Summary saved. Decisions and action items are not complete." },
    };
    mockedApiFetch.mockResolvedValueOnce({ ...failedRecovery, state: "queued" });
    const { rerender } = render(<MeetingIntelRecovery meetingId="meeting-1" revision={0} />);
    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalledTimes(1));
    mockedApiFetch.mockResolvedValueOnce(pending);
    rerender(<MeetingIntelRecovery meetingId="meeting-1" revision={1} />);
    const retry = await screen.findByRole("button", { name: "Retry" });
    expect(screen.getByText("Kept 3 segments and 2 artifacts. The decisions and action items did not finish.")).toBeInTheDocument();
    expect(screen.queryByTestId("recovery-route")).not.toBeInTheDocument();
    mockedApiFetch.mockResolvedValueOnce({ success: true, recovery: { ...pending, visible: false, state: "ready" } });
    fireEvent.click(retry);
    await waitFor(() => expect(mockedApiFetch).toHaveBeenLastCalledWith(
      "/api/meetings/meeting-1/intel-recovery/retry", { method: "POST" },
    ));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument());
  });

  it("drops an older recovery read after a newer record revision", async () => {
    let resolveOld!: (value: unknown) => void;
    mockedApiFetch.mockReturnValueOnce(new Promise((resolve) => { resolveOld = resolve; }));
    const { rerender } = render(<MeetingIntelRecovery meetingId="meeting-1" revision={0} />);
    mockedApiFetch.mockResolvedValueOnce({ ...failedRecovery, visible: false, state: "ready" });
    rerender(<MeetingIntelRecovery meetingId="meeting-1" revision={1} />);
    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalledTimes(2));
    resolveOld(failedRecovery);
    await waitFor(() => expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument());
  });

  it("keeps the action result when a revision read started during its POST finishes late", async () => {
    const pending = { ...failedRecovery, local_publication: true };
    let finishPost!: (value: unknown) => void;
    let finishRead!: (value: unknown) => void;
    mockedApiFetch.mockResolvedValueOnce(pending)
      .mockReturnValueOnce(new Promise((resolve) => { finishPost = resolve; }))
      .mockReturnValueOnce(new Promise((resolve) => { finishRead = resolve; }));
    const { rerender } = render(<MeetingIntelRecovery meetingId="meeting-1" revision={0} />);
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }));
    rerender(<MeetingIntelRecovery meetingId="meeting-1" revision={1} />);
    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalledTimes(3));
    await act(async () => { finishPost({ success: true, recovery: { ...pending, visible: false, state: "ready" } }); });
    await act(async () => { finishRead(pending); });
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("does not apply a previous meeting's action to the newly opened meeting", async () => {
    let finishPost!: (value: unknown) => void;
    const onChanged = vi.fn();
    mockedApiFetch.mockResolvedValueOnce({ ...failedRecovery, local_publication: true })
      .mockReturnValueOnce(new Promise((resolve) => { finishPost = resolve; }))
      .mockResolvedValueOnce({ ...failedRecovery, meeting_id: "meeting-2", visible: false, state: "ready" });
    const { rerender } = render(<MeetingIntelRecovery meetingId="meeting-1" onChanged={onChanged} />);
    fireEvent.click(await screen.findByRole("button", { name: "Retry" }));
    rerender(<MeetingIntelRecovery meetingId="meeting-2" onChanged={onChanged} />);
    await waitFor(() => expect(mockedApiFetch).toHaveBeenCalledTimes(3));
    await act(async () => { finishPost({ success: true, recovery: failedRecovery }); });
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
    expect(onChanged).not.toHaveBeenCalled();
  });
});
