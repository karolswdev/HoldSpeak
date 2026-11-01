// JRN2 (PROGRAM-JOURNEYS-2026-10-31, the dreaming night; LANG12 #1687): the
// Tonight verb on a Door task row and in a note line's menu. The answers are
// the hub's own, recorded through the real route by
// tests/integration/test_desk_program_night.py (HOLDSPEAK_WIRE_WRITE=1).
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import addedFixture from "../__fixtures__/tonight.added.json";
import refusedFixture from "../__fixtures__/tonight.refused.json";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn() }));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));

import { ApiError } from "../../../lib/api";
import { TonightVerb } from "../TonightVerb";

afterEach(() => { cleanup(); mocks.apiFetch.mockReset(); });

describe("the Tonight verb (JRN2)", () => {
  it("a Door task goes to tonight; the row then says Tonight · in the night program", async () => {
    mocks.apiFetch.mockResolvedValue(addedFixture);
    render(<TonightVerb kind="action" itemId="action-1" name="The Notes toolbar wraps at 520." />);
    fireEvent.click(screen.getByRole("button", { name: "Tonight: The Notes toolbar wraps at 520." }));
    await waitFor(() => expect(screen.getByTestId("tonight-done").textContent).toBe(`Tonight · in ${addedFixture.program.title}`));
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/programs/tonight", { method: "POST", json: { kind: "action", item_id: "action-1" } });
    expect(screen.queryByTestId("tonight-verb")).toBeNull();
  });

  it("a note line sends its words; a hub with no night program says so in its own words, and the verb stays", async () => {
    mocks.apiFetch.mockRejectedValue(new ApiError(refusedFixture.status, "Conflict", refusedFixture.body));
    render(<TonightVerb kind="note" itemId="note-1" line="Fix the toolbar wrap" name="Fix the toolbar wrap" />);
    fireEvent.click(screen.getByTestId("tonight-verb"));
    await waitFor(() => expect(screen.getByTestId("tonight-failed").textContent).toBe(refusedFixture.body.detail));
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/programs/tonight",
      { method: "POST", json: { kind: "note", item_id: "note-1", line: "Fix the toolbar wrap" } });
    expect(screen.getByTestId("tonight-verb")).toBeTruthy();
  });
});
