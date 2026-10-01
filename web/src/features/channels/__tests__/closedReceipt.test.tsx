// PHILO-11-04 round four (Astra built-check r3, condition 1): UNKNOWN and a lost
// answer stay on their CLOSED row, with the egress chip, on the UPDATE host.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { ProjectUpdate } from "../../project-room/update/model";
import type { Destination, Send } from "../channels";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../pages/cores/connections/api")>("../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { PublishedWells } from "../SendWell";
import type { UpdateController } from "../../project-room/update/useUpdateController";
import { resetSendStore } from "../../../desk/surface/send";

const REF = "project_update:u1";
const dest = (id: string, name: string): Destination => ({
  id, name, channel: "file", account: {}, target: { folder: `/Users/karol/Reports/${id}` },
  synced: false, state: "active", created_at: "2026-09-28T10:00:00Z", parked_at: null,
});
const unknownSend = (): Send => ({
  id: "chs_u", document_ref: REF, destination_id: "chd_a", destination_name: "Folder Payments", channel: "file",
  account: {}, target: { folder: "/Users/karol/Reports/chd_a" }, payload_digest: "d", preview: { text: "# Update" },
  prepared_by: { kind: "owner", identity: "" }, prepare_operation_id: null, state: "unknown", reason: "no_answer",
  proof: null, file_path: null, created_at: "2026-09-28T10:00:00Z", dispatch_started_at: "2026-09-28T10:00:00Z",
  settled_at: "2026-09-28T10:00:01Z",
});
const update = { id: "u1", projectId: "p1", projectRevision: 1, reviewId: null, lifecycle: "published", draftRevision: 3,
  bodyMd: "# Update", claims: [], sourceManifestJson: "{}", generator: "deterministic", generatorHost: null,
  generatorModel: null, fallbackReason: null, createdAt: "", updatedAt: "", publishedAt: "", deliveries: [] } as unknown as ProjectUpdate;
const ctrl = {
  deliverTo: "", setDeliverTo: () => {}, deliverBusy: false, deliverLocked: false, deliverOutcome: { kind: "none" },
  markDelivered: async () => {}, reloadDeliveries: async () => {}, deliveriesReadFailed: false,
} as unknown as UpdateController;

let routes: Record<string, (init: RequestInit & { json?: Record<string, unknown> }) => unknown>;
beforeEach(() => {
  resetSendStore();
  apiFetch.mockReset();
  routes = {
    "GET /api/channels/destinations": () => ({ destinations: [dest("chd_a", "Folder Payments"), dest("chd_b", "Folder Other")] }),
    "GET /api/channels/sends": () => ({ sends: [] }),
    "POST /api/channels/preview": () => ({ payload_digest: "dig1", preview: { text: "# Update" } }),
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

describe("the update: UNKNOWN and no answer survive the click that leaves the row (Astra r3 C1)", () => {
  it("UNKNOWN, then the row is closed: LAST SEND UNKNOWN, its word and the egress stay on the row", async () => {
    let stored: Send[] = [];
    routes["GET /api/channels/sends"] = () => ({ sends: stored });
    routes["POST /api/channels/send"] = () => { stored = [unknownSend()]; return { send: stored[0] }; };
    render(<PublishedWells ctrl={ctrl} update={update} />);
    await pick("Folder Payments");
    await pressSend();
    await screen.findByTestId("send-unknown");
    fireEvent.click(within(rowOf("Folder Payments")).getByText("Folder Payments"));
    await waitFor(() => expect(screen.queryByTestId("send-open")).toBeNull());
    const row = rowOf("Folder Payments");
    expect(row.textContent).toContain("LAST SEND UNKNOWN");
    expect(row.textContent).toContain("NO ANSWER");
    expect(row.textContent).toContain("THIS DEVICE");
  });

  // A lost answer HOLDS its press (the Phase 10 press rule: Retry sends the same key), so its own
  // row does not close on a click; the click that leaves it is picking another row.
  it("no answer, then another row is picked: NO ANSWER · RESULT UNKNOWN and the egress stay on the first row", async () => {
    routes["POST /api/channels/send"] = () => { throw new TypeError("Failed to fetch"); };
    render(<PublishedWells ctrl={ctrl} update={update} />);
    await pick("Folder Payments");
    await pressSend();
    await screen.findByTestId("send-lost");
    await pick("Folder Other");
    await waitFor(() => expect(screen.getByTestId("send-open").getAttribute("data-destination")).toBe("Folder Other"));
    const row = rowOf("Folder Payments");
    expect(row.textContent).toContain("NO ANSWER · RESULT UNKNOWN");
    expect(row.textContent).toContain("THIS DEVICE");
  });
});
