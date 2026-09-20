// HS-201-04, counsel fix round (Astra finding 1) — the route the face
// DISCLOSED is the route the request binds.
//
// The Meetings face can open a meeting the LIST never loaded: a deep link
// (`meeting:<id>`) fetches the detail on its own and shows that detail's
// `planned_route` beside the verb. The run gesture used to look the route
// up in the list rows instead, so for exactly this meeting it sent an
// EMPTY hash while the chip beside the button showed a real host.
//
// The fence reads the REQUEST: the hash on the wire must equal the hash of
// the route the face drew.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { forgetExecutedReceipts } from "../../../meetings/summaryRoute";
import { HistoryCore } from "../HistoryCore";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

const mockedApiFetch = vi.mocked(apiFetch);

const DETAIL_ROUTE = {
  status: "ready",
  reason_code: null,
  selection_hash: "sha256:from-the-detail",
  legs: [{ ordinal: 1, host: "192.168.1.43", boundary: "lan" }],
};

const DEEP_LINKED = {
  id: "m-deep",
  title: "Deep linked meeting",
  started_at: "2026-09-19T09:00:00Z",
  duration_seconds: 1800,
  capture_status: "finalized",
  intel_status: { state: "disabled" },
  transcriptWords: 1204,
  segments: [],
  planned_route: DETAIL_ROUTE,
  run_receipt: null,
};

function wire() {
  mockedApiFetch.mockImplementation(async (path: string) => {
    const url = String(path);
    // The LIST does not contain this meeting — the whole point.
    if (url.startsWith("/api/meetings?")) return { meetings: [] } as never;
    if (url === "/api/meetings/m-deep") return DEEP_LINKED as never;
    if (url.startsWith("/api/meetings/m-deep/")) return {} as never;
    return {} as never;
  });
}

describe("HS-201-04 a deep-linked meeting sends the route it showed", () => {
  beforeEach(() => {
    mockedApiFetch.mockReset();
    forgetExecutedReceipts();
  });

  it("puts the DISPLAYED selection hash on the run request", async () => {
    wire();
    render(<HistoryCore scope="meeting:m-deep" />);

    // The record shows the detail's own route beside its verb.
    const chip = await screen.findByTestId("detail-route");
    expect(chip.textContent).toContain("192.168.1.43 · LAN");

    fireEvent.click(await screen.findByTestId("detail-run-intelligence-btn"));

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenCalledWith(
        "/api/meetings/m-deep/intelligence/run",
        {
          method: "POST",
          json: { expected_selection_hash: "sha256:from-the-detail" },
        },
      ),
    );
  });
});
