// PHILO-6-01 round 2 — the complete Arrival row of a failed import names the
// IMPORT as what failed (Astra's check on built, finding 2).
//
// Round one mapped `import_failed` to the FAILED badge, and the badge helper
// also opens the expanded status well. That well was headed SUMMARY, so the
// row read SUMMARY · FAILED when the IMPORT failed. The fixture is the REAL
// import worker's wire (tests/unit/test_philo6_01_import_badge.py holds it
// equal); the real `fromWireMeeting` adapts it.
import { render, screen, waitFor, within } from "@testing-library/react";
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

const MEETING_ID = wire.list_row.id;
const CAUSE = wire.detail.intel_status.detail;

describe("PHILO-6-01 round 2: the failed import's row names the IMPORT", () => {
  beforeEach(() => {
    mocks.apiFetch.mockReset();
    mocks.apiFetch.mockImplementation(async (path: string) =>
      String(path) === `/api/meetings/${MEETING_ID}` ? wire.detail : null,
    );
  });

  it("badge FAILED, well head IMPORT, the import's cause, and no summary claim", async () => {
    const meeting = fromWireMeeting(wire.list_row);
    expect(meeting).not.toBeNull();
    useDesk.setState({ items: { ...EMPTY_ITEMS, meeting: [meeting] } as never });
    render(<ChairHome />);
    const row = await screen.findByTestId("arrival-meeting-row");
    await waitFor(() =>
      expect(within(row).getByTestId("arrival-meeting-badge").textContent).toBe("FAILED"),
    );
    // The complete row: the ledger line and its open well.
    const item = (row.closest("li") ?? row) as HTMLElement;
    const status = await within(item).findByTestId("arrival-summary-status");
    const text = item.textContent ?? "";
    // The well names what failed: the import.
    expect(text).toContain("IMPORT");
    expect(within(item).getByTestId("arrival-status-well-head").textContent).toBe("IMPORT");
    // The cause line is the import worker's.
    expect(status.textContent).toContain(CAUSE);
    // Round 3 (UX-CANON A.3; Astra's round-two check, finding 3): the cause
    // is the SHORT class -- never the worker's temp file, a path, a sentence.
    const errorFact = Array.from(status.querySelectorAll("*"))
      .map((node) => node.textContent ?? "")
      .find((line) => line.startsWith("LAST ERROR · "));
    expect(errorFact).toBe("LAST ERROR · NO TRANSCRIPT LINES");
    expect((errorFact ?? "").length).toBeLessThanOrEqual(60);
    expect(status.textContent ?? "").not.toMatch(/tmp|\.(vtt|srt|txt|wav)\b|[/\\]/i);
    // No summary claim anywhere in the row.
    expect(text).not.toContain("SUMMARY");
    expect(text).not.toContain("SAVED");
  });
});
