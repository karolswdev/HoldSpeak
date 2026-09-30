// PHILO-10-04: the SEND well's states, the one DELIVERY history and the list
// chips, against the wire client (apiFetch mocked by URL). The glass fence
// through the real hub is tests/e2e/test_philo10_04_send_face_glass.py.

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ProjectUpdate } from "../../project-room/update/model";
import type { UpdateController } from "../../project-room/update/useUpdateController";
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

import { ApiError } from "../../../lib/api";
import { DeliveryHistory, ListChips, updateDoc } from "../SendWell";
import { SendWell, latestFor, mergeKnown, resetSendStore, useSends } from "../../../desk/surface/send";

const FOLDER = "/Users/karol/Reports/Payments";
const dest = (over: Partial<Destination> = {}): Destination => ({
  id: "chd_1", name: "Folder Payments", channel: "file", account: {}, target: { folder: FOLDER },
  synced: false, state: "active", created_at: "2026-09-28T10:00:00Z", parked_at: null, ...over,
});
const send = (over: Partial<Send> = {}): Send => ({
  id: "chs_1", document_ref: "project_update:u1", destination_id: "chd_1", destination_name: "Folder Payments",
  channel: "file", account: {}, target: { folder: FOLDER }, payload_digest: "d", preview: { text: "# Update" },
  prepared_by: { kind: "owner", identity: "" }, prepare_operation_id: null, state: "sent", reason: null,
  proof: { path: `${FOLDER}/2026-09-28-payments-r1-abcd1234.md` }, file_path: `${FOLDER}/2026-09-28-payments-r1-abcd1234.md`,
  created_at: "2026-09-28T10:00:00Z", dispatch_started_at: "2026-09-28T10:00:00Z", settled_at: "2026-09-28T10:00:01Z",
  ...over,
});
const update = (over: Partial<ProjectUpdate> = {}): ProjectUpdate => ({
  id: "u1", projectId: "p1", projectRevision: 1, reviewId: null, lifecycle: "published", draftRevision: 3, bodyMd: "# Update",
  claims: [], sourceManifestJson: "{}", generator: "deterministic", generatorHost: null, generatorModel: null,
  fallbackReason: null, createdAt: "", updatedAt: "", publishedAt: "", deliveries: [], ...over,
});

type Route = (init: RequestInit & { json?: Record<string, unknown> }) => unknown;
let routes: Record<string, Route>;
function wireUp() {
  apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
    const key = `${init.method ?? "GET"} ${path.split("?")[0]}`;
    const r = routes[key];
    if (!r) return Promise.reject(new Error(`unrouted ${key}`));
    try { return Promise.resolve(r(init)); } catch (e) { return Promise.reject(e); }
  });
}

function Well({ u = update() }: { u?: ProjectUpdate }) {
  const read = useSends(updateDoc(u).ref);
  return <SendWell doc={updateDoc(u)} sendsRead={read} />;
}

beforeEach(() => {
  resetSendStore();
  apiFetch.mockReset();
  routes = {
    "GET /api/channels/destinations": () => ({ destinations: [dest()] }),
    "GET /api/channels/sends": () => ({ sends: [] }),
    "POST /api/channels/preview": () => ({ payload_digest: "dig1", preview: { text: "# Update\n\nBody" } }),
  };
  wireUp();
});
afterEach(() => vi.useRealTimers());

describe("the SEND well", () => {
  it("no destination: NO DESTINATION + Add destination, never a counter", async () => {
    routes["GET /api/channels/destinations"] = () => ({ destinations: [] });
    render(<Well />);
    const none = await screen.findByTestId("send-none");
    expect(none.textContent).toContain("NO DESTINATION");
    expect(within(none).getByTestId("send-add-destination").textContent).toBe("Add destination");
  });

  it("a destinations read with no answer is named, never the empty state", async () => {
    routes["GET /api/channels/destinations"] = () => { throw new TypeError("Failed to fetch"); };
    render(<Well />);
    expect((await screen.findByTestId("destinations-unreadable")).textContent).toContain("CANNOT READ DESTINATIONS");
    expect(screen.queryByTestId("send-none")).toBeNull();
  });

  it("A1: the pick opens the preview and Send in place; the folder keeps its case", async () => {
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    expect(row.textContent).toContain("~/Reports/Payments");
    expect(row.textContent).toContain("THIS DEVICE");
    fireEvent.click(within(row).getByText("Folder Payments"));
    const preview = await screen.findByTestId("send-preview");
    expect(preview.textContent).toContain("Folder");
    expect(preview.textContent).toContain(FOLDER);
    expect(preview.textContent).not.toMatch(/[{}<]/);
    expect(screen.getByTestId("send-verb").textContent).toBe("Send");
  });

  it("Send settles SAVED + the exact path; a double click is one press", async () => {
    let calls = 0;
    let stored: Send[] = [];
    routes["GET /api/channels/sends"] = () => ({ sends: stored });
    routes["POST /api/channels/send"] = (init) => {
      calls += 1;
      expect(init.json).toMatchObject({ document_ref: "project_update:u1", destination_id: "chd_1", preview_digest: "dig1" });
      stored = [send()];
      return { send: stored[0] };
    };
    render(<Well />);
    fireEvent.click(within(await screen.findByTestId("destination-row")).getByText("Folder Payments"));
    const verb = await screen.findByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(verb); fireEvent.click(verb);
    const sent = await screen.findByTestId("send-sent");
    expect(sent.textContent).toContain("SAVED");
    expect(within(sent).getByTestId("proof").textContent).toBe(`${FOLDER}/2026-09-28-payments-r1-abcd1234.md`);
    expect(calls).toBe(1);
    expect(screen.getByTestId("send-last-sent").textContent).toContain("SAVED");
    expect(screen.getByTestId("send-verb").textContent).toBe("Send again");
  });

  it("a refusal names its code and NOTHING SENT", async () => {
    routes["POST /api/channels/send"] = () => {
      throw new ApiError(409, "changed", { success: false, error_code: "destination_changed" });
    };
    render(<Well />);
    fireEvent.click(within(await screen.findByTestId("destination-row")).getByText("Folder Payments"));
    const verb = await screen.findByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(verb);
    const refused = await screen.findByTestId("send-refused");
    expect(refused.textContent).toContain("REFUSED");
    expect(refused.textContent).toContain("DESTINATION CHANGED");
    expect(refused.textContent).toContain("NOTHING SENT");
  });

  it("G2: a preview refused by name shows its word and the size, never NO ANSWER (PHILO-11-04)", async () => {
    routes["POST /api/channels/preview"] = () => {
      throw new ApiError(400, "too large", {
        success: false, code: "payload_too_large:slack", error_code: "payload_too_large:slack", size: 41099, limit: 39000,
      });
    };
    render(<Well />);
    fireEvent.click(within(await screen.findByTestId("destination-row")).getByText("Folder Payments"));
    const refused = await screen.findByTestId("preview-refused");
    expect(refused.textContent).toContain("TOO LARGE FOR SLACK");
    expect(refused.textContent).toContain("41,099 / 39,000 CHARACTERS");
    expect(refused.textContent).toContain("NOTHING SENT");
    expect(screen.getByTestId("send-open").textContent).not.toContain("NO ANSWER");
  });

  it("a lost answer keeps the key: Retry sends the SAME command_id", async () => {
    const keys: string[] = [];
    let lose = true;
    let stored: Send[] = [];
    routes["GET /api/channels/sends"] = () => ({ sends: stored });
    routes["POST /api/channels/send"] = (init) => {
      keys.push(String(init.json?.command_id));
      if (lose) { lose = false; throw new TypeError("Failed to fetch"); }
      stored = [send()];  // the hub's replay answers the settled row
      return { send: stored[0] };
    };
    render(<Well />);
    fireEvent.click(within(await screen.findByTestId("destination-row")).getByText("Folder Payments"));
    const verb = await screen.findByTestId("send-verb");
    await waitFor(() => expect((verb as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(verb);
    expect((await screen.findByTestId("send-lost")).textContent).toContain("NO ANSWER · RESULT UNKNOWN");
    fireEvent.click(screen.getByTestId("send-retry"));
    await screen.findByTestId("send-sent");
    expect(keys).toHaveLength(2);
    expect(keys[0]).toBe(keys[1]);
  });

  it("A3: prepared sends first, ONE open; an ended one stays as its result", async () => {
    routes["GET /api/channels/sends"] = () => ({ sends: [
      send({ id: "chs_a", state: "prepared", prepare_operation_id: "op_a", prepared_by: { kind: "agent", identity: "remote-agent" },
        dispatch_started_at: null, settled_at: null, proof: null, file_path: null }),
      send({ id: "chs_b", state: "prepared", prepare_operation_id: "op_b", prepared_by: { kind: "owner", identity: "" },
        dispatch_started_at: null, settled_at: null, proof: null, file_path: null }),
      send({ id: "chs_c", state: "discarded", prepare_operation_id: "op_c", dispatch_started_at: null, proof: null }),
    ] });
    render(<Well />);
    const list = await screen.findByTestId("prepared-list");
    expect(within(list).getAllByTestId("prepared-row")).toHaveLength(2);
    expect(within(list).getAllByTestId("prepared-open")).toHaveLength(1);
    expect(within(list).getAllByTestId("prepared-by").map((e) => e.textContent)).toEqual(["BY REMOTE-AGENT", "BY YOU", "BY YOU"]);
    expect(within(list).getByTestId("prepared-result").textContent).toContain("DISCARDED");
    expect(list.textContent).toContain("REV 3");
    // The prepared well precedes the destinations.
    const well = screen.getByTestId("send-well");
    const order = [...well.querySelectorAll("[data-testid=prepared-list], [data-testid=destination-list]")].map((e) => e.getAttribute("data-testid"));
    expect(order).toEqual(["prepared-list", "destination-list"]);
  });

  it("a running send: SENDING on the row and its destination; Send not enabled", async () => {
    routes["GET /api/channels/sends"] = () => ({ sends: [
      send({ id: "chs_r", state: "dispatching", prepare_operation_id: "op_r", settled_at: null, proof: null }),
    ] });
    render(<Well />);
    expect((await screen.findByTestId("prepared-running")).textContent).toContain("SENDING");
    expect(screen.getByTestId("send-last-running").textContent).toContain("SENDING");
    fireEvent.click(within(screen.getByTestId("destination-row")).getByText("Folder Payments"));
    const verb = await screen.findByTestId("send-verb");
    await act(async () => { await new Promise((r) => setTimeout(r, 20)); });
    expect((verb as HTMLButtonElement).disabled).toBe(true);
  });

  it("a draft has no SEND well (the posture renders the wells only when published)", () => {
    // The posture's rule is `lifecycle === "published"`; the history below
    // is the only DELIVERY face, and it needs a published update.
    expect(update({ lifecycle: "draft" }).lifecycle).not.toBe("published");
  });
});

describe("latestFor: ONE source, by dispatch_seq (Codex Astra r1 F3 on #697)", () => {
  it("an equal clock is ordered by the hub's dispatch sequence", () => {
    const at = "2026-09-28T10:00:00.000000+00:00";
    const sends = [
      send({ id: "a", state: "failed", reason: "permission_denied", dispatch_started_at: at, dispatch_seq: 2 }),
      send({ id: "b", state: "sent", dispatch_started_at: at, dispatch_seq: 1 }),
    ];
    expect(latestFor(sends, "chd_1")?.id).toBe("a");
  });
});

describe("mergeKnown: a stale or failed read never hides a returned result (r1 F1 on #697)", () => {
  it("keeps the returned FAILED over a read that predates it, and a read never replaces an ended row with a running one", () => {
    const old = send({ id: "old", state: "sent", dispatch_seq: 1 });
    const failed = send({ id: "new", state: "failed", reason: "permission_denied", dispatch_seq: 2 });
    const merged = mergeKnown("project_update:u1", [old], [failed]);
    expect(latestFor(merged, "chd_1")?.state).toBe("failed");
    const running = { ...failed, state: "dispatching" as const };
    expect(mergeKnown("project_update:u1", [old, running], [failed]).find((s) => s.id === "new")?.state).toBe("failed");
    // PHILO-11-04 (Astra r1 F1 on #708): rows of another document never enter, from the read or the cache.
    expect(mergeKnown("project_update:u2", [old], [failed]).map((s) => s.id)).toEqual([]);
  });
});

describe("latestFor: ONE source, by dispatch_started_at", () => {
  it("a newer failure beats an older success, whatever the preparation order", () => {
    const sends = [
      send({ id: "prep", state: "failed", reason: "permission_denied", created_at: "2026-09-28T09:00:00Z",
        dispatch_started_at: "2026-09-28T10:05:00Z" }),
      send({ id: "inline", state: "sent", created_at: "2026-09-28T10:00:00Z", dispatch_started_at: "2026-09-28T10:00:00Z" }),
      send({ id: "waiting", state: "prepared", dispatch_started_at: null }),
    ];
    expect(latestFor(sends, "chd_1")?.id).toBe("prep");
  });
});

const ctrl = (over: Partial<UpdateController> = {}) => ({
  deliverTo: "", setDeliverTo: () => {}, deliverBusy: false, deliverLocked: false,
  deliverOutcome: { kind: "none" }, markDelivered: async () => {}, reloadDeliveries: async () => {},
  deliveriesReadFailed: false, ...over,
}) as unknown as UpdateController;

describe("the one DELIVERY history (A2)", () => {
  const rows = [
    { id: "d1", updateId: "u1", deliveredAt: "2026-09-28T10:00:01Z", deliveredTo: "Folder Payments", operationId: "o1",
      outcome: "sent", channel: "file", proof: { path: `${FOLDER}/a.md` }, sendId: "chs_1" },
    { id: "d2", updateId: "u1", deliveredAt: "2026-09-28T10:01:00Z", deliveredTo: "Long path folder", operationId: "o2",
      outcome: "unknown", channel: "file", proof: null, sendId: "chs_2" },
    { id: "d3", updateId: "u1", deliveredAt: "2026-09-28T10:02:00Z", deliveredTo: "Priya", operationId: "o3",
      outcome: "confirmed", channel: "manual", proof: null, sendId: null },
  ];

  it("head DELIVERY N counts isDelivered rows; words per channel; manual kept", () => {
    render(<DeliveryHistory ctrl={ctrl()} update={update({ deliveries: rows })}
      sends={[send({ id: "chs_2", state: "unknown", reason: "create_enametoolong" })]} />);
    const section = screen.getByTestId("delivery-section");
    expect(section.querySelector("h3")?.textContent).toBe("DELIVERY 2");
    const r = screen.getAllByTestId("delivery-row");
    expect(r[0].textContent).toContain("SAVED");
    expect(r[0].textContent).toContain(`${FOLDER}/a.md`);
    expect(r[1].textContent).toContain("RESULT UNKNOWN · CHECK Long path folder");
    expect(r[2].textContent).toContain("DELIVERED");
    expect(r[2].textContent).toContain("MANUAL");
    expect(section.textContent).not.toContain("DELIVERED 2");
  });

  it("a history read with no answer is named with Retry", () => {
    render(<DeliveryHistory ctrl={ctrl({ deliveriesReadFailed: true })} update={update()} sends={[]} />);
    expect(screen.getByTestId("history-unreadable").textContent).toContain("CANNOT READ HISTORY");
  });

  it("list chips: PREPARED ×K, RESULT UNKNOWN ×M, DELIVERY ×N; none at zero", async () => {
    routes["GET /api/channels/sends"] = () => ({ sends: [send({ state: "prepared", prepare_operation_id: "op" })] });
    const { container } = render(<ListChips update={update({ deliveries: rows })} />);
    expect((await screen.findByTestId("update-prepared-chip")).textContent).toContain("PREPARED ×1");
    expect(screen.getByTestId("update-unknown-chip").textContent).toContain("RESULT UNKNOWN ×1");
    expect(screen.getByTestId("update-delivered-chip").textContent).toContain("DELIVERY ×2");
    expect(container.textContent).not.toContain("DELIVERED");
  });

  it("no chip at zero", async () => {
    const { container } = render(<ListChips update={update()} />);
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });
    expect(container.textContent).toBe("");
  });
});
