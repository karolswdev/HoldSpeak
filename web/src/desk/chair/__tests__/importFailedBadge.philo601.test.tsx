// PHILO-6-01 — the honest import badge: the wire and rendered links.
//
// The producer link (tests/unit/test_philo6_01_import_badge.py) mints a
// failed import through the REAL import route and worker, and keeps the
// fixture below equal to that wire. This file adapts that wire through the
// REAL `fromWireMeeting` and renders the Arrival row. Before the repair the
// badge fell through `intelBadge`'s fallback and read SAVED.
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));

import wire from "./fixtures/philo6/import-failed-meeting.json";
import { EMPTY_ITEMS, fromWireMeeting } from "../../api";
import { useDesk } from "../../store";
import { ChairHome } from "../ChairHome";
import { intelBadge } from "../intelBadge";

const MEETING_ID = wire.list_row.id;

describe("PHILO-6-01 a failed import reads FAILED, never SAVED", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path) === `/api/meetings/${MEETING_ID}` ? wire.detail : null,
    );
  });

  it("the wire adapter carries import_failed from the list row and the detail", () => {
    expect(fromWireMeeting(wire.list_row)?.intelStatus).toBe("import_failed");
    expect(fromWireMeeting(wire.detail)?.intelStatus).toBe("import_failed");
  });

  it("the Arrival row of the producer's failed import shows the FAILED badge", async () => {
    const meeting = fromWireMeeting(wire.list_row);
    expect(meeting).not.toBeNull();
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [meeting] } as never });
    render(<ChairHome />);
    const badge = await screen.findByTestId("arrival-meeting-badge");
    await waitFor(() => expect(badge.textContent).toBe("FAILED"));
    expect(badge.getAttribute("data-badge")).toBe("failed");
    expect(screen.getByTestId("arrival-meeting-row").textContent).not.toContain("SAVED");
  });

  it("names the states the badge covers; the failure states are FAILED", () => {
    // The producer's writes (holdspeak/db/intel.py, meeting_session/*,
    // services/meeting_service.py) with the badge each one reads as.
    const covered: Record<string, string> = {
      complete: "RAN",
      ready: "RAN",
      running: "RUNNING",
      queued: "QUEUED",
      pending: "QUEUED",
      error: "FAILED",
      failed: "FAILED",
      import_failed: "FAILED",
      partial: "PARTIAL",
      skipped: "SKIPPED",
      disabled: "OFF",
    };
    for (const [state, badge] of Object.entries(covered)) {
      expect(intelBadge(state), state).toBe(badge);
    }
    expect(intelBadge(null)).toBe("SAVED");
  });
});
