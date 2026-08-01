// HS-111-03 — re-pointed to the twin receipt slips (audit §3.5):
// CURRENT / INCOMING fact stacks, KEEP CURRENT / USE INCOMING verbs,
// the group label carrying SYNC CONFLICT · BOTH RETAINED. The wire
// contract under test is unchanged.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../lib/api";
import { MeetingConflictRecovery } from "./MeetingConflictRecovery";

vi.mock("../lib/api", () => ({
  apiFetch: vi.fn(),
  readableError: (error: unknown) =>
    error instanceof Error ? error.message : "Request failed.",
}));

const mockedApiFetch = vi.mocked(apiFetch);

const conflict = {
  id: "conflict-1",
  meeting_id: "meeting-1",
  local: {
    title: "Desktop title",
    capture_status: "finalized",
    provenance: "desktop",
    tags: ["delivery"],
    segments: [{ text: "Desktop transcript" }],
  },
  incoming: {
    title: "Device title",
    capture_status: "recoverable",
    provenance: "native",
    tags: ["planning"],
    segments: [{ text: "Device transcript" }, { text: "Device decision" }],
  },
};

describe("HS-93-06 Meeting conflict recovery", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
  });

  it("shows both retained versions and applies only the explicit choice", async () => {
    const onResolved = vi.fn();
    mockedApiFetch
      .mockResolvedValueOnce({ conflicts: [conflict] })
      .mockResolvedValueOnce({
        resolution: "use_incoming",
        deleted: false,
        meeting: { id: "meeting-1", title: "Device title" },
        remaining_conflicts: [],
      });

    render(
      <MeetingConflictRecovery meetingId="meeting-1" onResolved={onResolved} />,
    );

    // The group label carries the whole truth (rendered uppercase).
    expect(
      await screen.findByText("Sync conflict · both retained"),
    ).toBeInTheDocument();
    expect(screen.getByText("CURRENT")).toBeInTheDocument();
    expect(screen.getByText("INCOMING")).toBeInTheDocument();
    expect(screen.getByText(/Desktop transcript/)).toBeInTheDocument();
    expect(screen.getByText(/Device decision/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Use incoming" }));
    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenLastCalledWith(
        "/api/meetings/meeting-1/sync-conflicts/conflict-1/resolve",
        { method: "POST", json: { resolution: "use_incoming" } },
      ),
    );
    expect(onResolved).toHaveBeenCalledWith(
      expect.objectContaining({ resolution: "use_incoming", deleted: false }),
    );
    expect(
      screen.queryByText("Sync conflict · both retained"),
    ).not.toBeInTheDocument();
  });

  it("names an incoming tombstone as a destructive Meeting deletion", async () => {
    mockedApiFetch.mockResolvedValueOnce({
      conflicts: [
        {
          ...conflict,
          incoming: { deleted: true },
        },
      ],
    });

    render(<MeetingConflictRecovery meetingId="meeting-1" />);

    expect(await screen.findByText("TOMBSTONE")).toBeInTheDocument();
    expect(
      screen.getByText("Deleted, with its retained projections"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Use incoming" }),
    ).toBeInTheDocument();
  });

  it("states that both versions remain when recovery cannot load", async () => {
    mockedApiFetch.mockRejectedValueOnce(new Error("Hub unavailable."));
    render(<MeetingConflictRecovery meetingId="meeting-1" />);

    expect(
      await screen.findByText(
        "Hub unavailable. Both Meeting versions remain retained.",
      ),
    ).toBeInTheDocument();
  });
});
