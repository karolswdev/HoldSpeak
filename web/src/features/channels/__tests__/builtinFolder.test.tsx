// The built-in "HoldSpeak folder" (owner ruling 2026-10-05, "strong defaults,
// batteries included"): every desk has it with no setup. In the SEND well it
// is one destination row; when it is the only destination it is picked, so
// the preview and Send are open. In Settings -> Connections it has Check but
// no Edit and no Remove. The hub side is tests/unit/test_builtin_send_folder.py;
// the glass is tests/e2e/test_builtin_send_folder_glass.py.

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Destination } from "../channels";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../../pages/cores/connections/api")>("../../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

import { SendWell, resetSendStore, useSends } from "../../../desk/surface/send";
import { Destinations } from "../../../pages/cores/connections/Destinations";

const SENT = "/home/karol/Documents/HoldSpeak/Sent"; // a Linux HOME: the hub's display token is the row's text
const builtin = (): Destination => ({
  id: "holdspeak-folder", name: "HoldSpeak folder", channel: "file", account: {}, builtin: true,
  target: { builtin: "documents", folder: SENT, display: "~/Documents/HoldSpeak/Sent" }, synced: false, state: "active", badge: "local",
  created_at: "2026-10-05T10:00:00Z", parked_at: null,
});
const saved = (): Destination => ({
  id: "chd_1", name: "Team folder", channel: "file", account: {}, target: { folder: "/Users/karol/Team" },
  synced: false, state: "active", badge: "local", created_at: "2026-10-05T11:00:00Z", parked_at: null,
});

let rows: Destination[] = [];
const previews: string[] = [];
beforeEach(() => {
  resetSendStore();
  rows = [builtin()];
  previews.length = 0;
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
    const method = init.method ?? "GET";
    if (method === "GET" && path.startsWith("/api/channels/destinations")) return Promise.resolve({ destinations: rows });
    if (method === "GET" && path.startsWith("/api/channels/sends")) return Promise.resolve({ sends: [] });
    if (method === "POST" && path === "/api/channels/preview") {
      previews.push(String(init.json?.destination_id));
      return Promise.resolve({ payload_digest: "dig1", preview: { text: "# Brief" } });
    }
    return Promise.reject(new Error(`unrouted ${method} ${path}`));
  });
});

const DOC = { ref: "monday_brief:2026-10-05", title: "Monday brief", label: "Brief" };
function Well() {
  const read = useSends(DOC.ref);
  return <SendWell doc={DOC} sendsRead={read} />;
}

describe("the built-in HoldSpeak folder in the SEND well", () => {
  it("alone, it is one row, picked: the preview and Send are open with no click", async () => {
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    expect(screen.getAllByTestId("destination-row")).toHaveLength(1);
    expect(row.textContent).toContain("HoldSpeak folder");
    expect(row.textContent).toContain("~/Documents/HoldSpeak/Sent");
    expect(row.textContent).toContain("THIS DEVICE");
    expect(screen.queryByTestId("send-none")).toBeNull();
    const preview = await screen.findByTestId("send-preview");
    expect(preview.textContent).toContain(SENT);
    await waitFor(() => expect((screen.getByTestId("send-verb") as HTMLButtonElement).disabled).toBe(false));
    expect(previews).toEqual(["holdspeak-folder"]);
  });

  it("with another destination, nothing is picked until he picks", async () => {
    rows = [builtin(), saved()];
    render(<Well />);
    await waitFor(() => expect(screen.getAllByTestId("destination-row")).toHaveLength(2));
    expect(screen.queryByTestId("send-preview")).toBeNull();
    expect(previews).toEqual([]);
  });

  it("a click on the picked row closes it, and it stays closed", async () => {
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    await screen.findByTestId("send-preview");
    fireEvent.click(within(row).getByText("HoldSpeak folder"));
    await waitFor(() => expect(screen.queryByTestId("send-preview")).toBeNull());
  });
});

describe("the built-in HoldSpeak folder in Settings -> Connections", () => {
  it("has Check, and no Edit and no Remove; a saved folder keeps both", async () => {
    rows = [builtin(), saved()];
    render(<Destinations />);
    const [first, second] = await screen.findAllByTestId("dest-row");
    fireEvent.click(within(first).getByText("HoldSpeak folder"));
    const open = await screen.findByTestId("dest-open");
    expect(within(open).getByTestId("dest-check")).toBeTruthy();
    expect(within(open).queryByTestId("dest-edit")).toBeNull();
    expect(within(open).queryByTestId("dest-remove")).toBeNull();
    fireEvent.click(within(second).getByText("Team folder"));
    await waitFor(() => expect(within(screen.getByTestId("dest-open")).getByTestId("dest-edit")).toBeTruthy());
    expect(within(screen.getByTestId("dest-open")).getByTestId("dest-remove")).toBeTruthy();
  });
});
