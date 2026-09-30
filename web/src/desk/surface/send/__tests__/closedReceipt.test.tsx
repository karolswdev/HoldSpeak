// PHILO-11-04 round four (Astra built-check r3, condition 1): UNKNOWN and a lost
// answer stay on their CLOSED row, with the egress chip, on a brief (a non-update
// document). The update host's twin: features/channels/__tests__/closedReceipt.test.tsx.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Destination, Send } from "../../../../features/channels/channels";

const apiFetch = vi.fn();
vi.mock("../../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../lib/api")>("../../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../../pages/cores/connections/api")>("../../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { SendWells, resetSendStore } from "..";

const REF = "monday_brief:b1";
const dest = (id: string, name: string): Destination => ({
  id, name, channel: "file", account: {}, target: { folder: `/Users/karol/Reports/${id}` },
  synced: false, state: "active", created_at: "2026-09-29T10:00:00Z", parked_at: null,
});
const unknownSend = (): Send => ({
  id: "chs_u", document_ref: REF, destination_id: "chd_a", destination_name: "Team folder", channel: "file",
  account: {}, target: { folder: "/Users/karol/Reports/chd_a" }, payload_digest: "d", preview: { text: "# Brief" },
  prepared_by: { kind: "owner", identity: "" }, prepare_operation_id: null, state: "unknown", reason: "no_answer",
  proof: null, file_path: null, created_at: "2026-09-29T10:00:00Z", dispatch_started_at: "2026-09-29T10:00:00Z",
  settled_at: "2026-09-29T10:00:01Z",
});

let routes: Record<string, (init: RequestInit & { json?: Record<string, unknown> }) => unknown>;
beforeEach(() => {
  resetSendStore();
  apiFetch.mockReset();
  routes = {
    "GET /api/channels/destinations": () => ({ destinations: [dest("chd_a", "Team folder"), dest("chd_b", "Other folder")] }),
    "GET /api/channels/sends": () => ({ sends: [] }),
    "POST /api/channels/preview": () => ({ payload_digest: "dig1", preview: { text: "# Brief" } }),
  };
  apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
    const r = routes[`${init.method ?? "GET"} ${path.split("?")[0]}`];
    if (!r) return Promise.reject(new Error(`unrouted ${path}`));
    try { return Promise.resolve(r(init)); } catch (e) { return Promise.reject(e); }
  });
});

const rowOf = (name: string) => screen.getAllByTestId("destination-row").find((r) => r.textContent?.includes(name))!;
const pick = async (name: string) => {
  await screen.findAllByTestId("destination-row");
  fireEvent.click(within(rowOf(name)).getByText(name));
};
const pressSend = async () => {
  const verb = await screen.findByTestId("send-verb");
  await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
  fireEvent.click(verb);
};
const DOC = { ref: REF, title: "Brief Sep 29", label: "BRIEF SEP 29" };

describe("a brief: UNKNOWN and no answer survive the click that leaves the row (Astra r3 C1)", () => {
  it("UNKNOWN, then the row is closed: LAST SEND UNKNOWN, its word and the egress stay on the row", async () => {
    let stored: Send[] = [];
    routes["GET /api/channels/sends"] = () => ({ sends: stored });
    routes["POST /api/channels/send"] = () => { stored = [unknownSend()]; return { send: stored[0] }; };
    render(<SendWells doc={DOC} />);
    await pick("Team folder");
    await pressSend();
    await screen.findByTestId("send-unknown");
    fireEvent.click(within(rowOf("Team folder")).getByText("Team folder"));
    await waitFor(() => expect(screen.queryByTestId("send-open")).toBeNull());
    const row = rowOf("Team folder");
    expect(row.textContent).toContain("LAST SEND UNKNOWN");
    expect(row.textContent).toContain("NO ANSWER");
    expect(row.textContent).toContain("THIS DEVICE");
  });

  // A lost answer HOLDS its press (Retry sends the same key), so its own row does not close on a
  // click; the click that leaves it is picking another row.
  it("no answer, then another row is picked: NO ANSWER · RESULT UNKNOWN and the egress stay on the first row", async () => {
    routes["POST /api/channels/send"] = () => { throw new TypeError("Failed to fetch"); };
    render(<SendWells doc={DOC} />);
    await pick("Team folder");
    await pressSend();
    await screen.findByTestId("send-lost");
    await pick("Other folder");
    await waitFor(() => expect(screen.getByTestId("send-open").getAttribute("data-destination")).toBe("Other folder"));
    const row = rowOf("Team folder");
    expect(row.textContent).toContain("NO ANSWER · RESULT UNKNOWN");
    expect(row.textContent).toContain("THIS DEVICE");
  });
});
