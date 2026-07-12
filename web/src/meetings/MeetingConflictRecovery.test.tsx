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

    expect(
      await screen.findByRole("heading", {
        name: "Choose the Meeting version",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("Current on this desktop")).toBeInTheDocument();
    expect(screen.getByText("Incoming from synced device")).toBeInTheDocument();
    expect(screen.getByText(/Desktop transcript/)).toBeInTheDocument();
    expect(screen.getByText(/Device decision/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Use synced Meeting" }));
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
      screen.queryByRole("heading", { name: "Choose the Meeting version" }),
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

    expect(await screen.findByText("Meeting deleted")).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "Delete this Meeting from this device",
      }),
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
