import { describe, expect, it } from "vitest";
import { parseMeetingStopOutcome } from "./meetingStopOutcome";

describe("meeting Stop outcome", () => {
  it("keeps the response Meeting id and distinguishes durable DB from JSON", () => {
    const outcome = parseMeetingStopOutcome({
      status: "stopped",
      meeting: { id: "meeting-1" },
      save: { database_saved: true, json_saved: false },
      save_error: "JSON export failed",
      device_cleanup_error: "Mic audio device did not close.",
    });

    expect(outcome).toMatchObject({
      captureStopped: true,
      meetingId: "meeting-1",
      databaseSaved: true,
      jsonSaved: false,
      captureStatus: "",
      saveStatus: "partial",
      saveError: "JSON export failed",
      deviceCleanupError: "Mic audio device did not close.",
      recoveryAvailable: false,
    });
  });

  it("does not fabricate saved or failed when the legacy response has no facts", () => {
    const outcome = parseMeetingStopOutcome({ success: true }, "live-1");

    expect(outcome).toMatchObject({
      captureStopped: null,
      meetingId: "live-1",
      databaseSaved: null,
      jsonSaved: null,
      captureStatus: "",
      saveStatus: "unknown",
      saveError: "",
      recoveryAvailable: false,
    });
  });

  it("keeps a failed save separate from a confirmed stopped capture", () => {
    const outcome = parseMeetingStopOutcome({
      status: "stopped",
      meeting: { meeting_id: "meeting-2" },
      save: { database_saved: false, json_saved: false },
      save_error: "disk full",
    });

    expect(outcome.captureStopped).toBe(true);
    expect(outcome.saveStatus).toBe("failed");
    expect(outcome.meetingId).toBe("meeting-2");
    expect(outcome.captureStatus).toBe("");
    expect(outcome.recoveryAvailable).toBe(false);
  });

  it("offers capture recovery only for a recoverable checkpoint with JSON retained", () => {
    const outcome = parseMeetingStopOutcome({
      status: "stopped",
      meeting: { id: "meeting-recoverable", capture_status: "recoverable" },
      save: { database_saved: false, json_saved: true },
      save_error: "database unavailable",
    });

    expect(outcome.recoveryAvailable).toBe(true);
  });

  it("does not turn an incomplete legacy save object into a failure", () => {
    const outcome = parseMeetingStopOutcome({
      status: "stopped",
      meeting: { id: "meeting-3" },
      save: { database_saved: true },
    });

    expect(outcome.saveStatus).toBe("unknown");
    expect(outcome.databaseSaved).toBe(true);
    expect(outcome.jsonSaved).toBeNull();
  });
});
