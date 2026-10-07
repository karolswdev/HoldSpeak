// The built-in "HoldSpeak folder" (owner ruling 2026-10-05, "strong defaults,
// batteries included"): every desk has it with no setup. In the SEND well it
// is one destination row, closed until he presses it (PHILO-15 lane 12, B23). In Settings -> Connections it has Check but
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
import { keepPlace } from "../../../desk/deskMemory";

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
  // PHILO-15 lane 12 (B23): the well waits. The folder is still the one row
  // with no setup, but nothing opens until he presses it; it reads by its
  // name (HoldSpeak/Sent), never a path; the `~` token is on hover.
  it("alone, it is one row, closed until he presses it; it reads by its name", async () => {
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    expect(screen.getAllByTestId("destination-row")).toHaveLength(1);
    expect(row.textContent).toContain("HoldSpeak folder");
    expect(row.textContent).toContain("HoldSpeak/Sent");
    expect(row.textContent).not.toContain("~/Documents");
    expect(row.textContent).not.toContain(SENT);
    expect(row.querySelector(".send-target")?.getAttribute("title")).toBe("~/Documents/HoldSpeak/Sent");
    expect(row.textContent).toContain("THIS DEVICE");
    expect(screen.queryByTestId("send-none")).toBeNull();
    // Closed: no preview read, no preview, no Send.
    await new Promise((r) => setTimeout(r, 30));
    expect(screen.queryByTestId("send-preview")).toBeNull();
    expect(previews).toEqual([]);
    fireEvent.click(within(row).getByText("HoldSpeak folder"));
    const preview = await screen.findByTestId("send-preview");
    expect(preview.textContent).toContain("HoldSpeak/Sent");
    expect(preview.textContent).not.toContain(SENT);
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

  it("a press opens the row, a second press closes it, and it stays closed", async () => {
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    fireEvent.click(within(row).getByText("HoldSpeak folder"));
    await screen.findByTestId("send-preview");
    fireEvent.click(within(row).getByText("HoldSpeak folder"));
    await waitFor(() => expect(screen.queryByTestId("send-preview")).toBeNull());
  });
});

describe("the built-in HoldSpeak folder in an iCloud Drive Documents folder", () => {
  it("the row's egress chip is ICLOUD (cloud), never THIS DEVICE", async () => {
    rows = [{ ...builtin(), synced: true, badge: "cloud", target: { ...builtin().target, cloud: "icloud" } }];
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    expect(row.textContent).toContain("ICLOUD");
    expect(row.textContent).not.toContain("THIS DEVICE");
    const chip = within(row).getAllByText("ICLOUD")[0];
    expect(chip.closest(".gadget-chip-egress")?.getAttribute("data-scope")).toBe("cloud");
  });

  it("plain Documents: THIS DEVICE", async () => {
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    expect(row.textContent).toContain("THIS DEVICE");
    expect(row.textContent).not.toContain("ICLOUD");
  });

  it("a SAVED receipt whose proof names iCloud shows the ICLOUD egress beside the path", async () => {
    const at = "2026-10-05T10:00:00Z";
    const sent = (egress?: string) => ({
      id: "chs_1", document_ref: DOC.ref, destination_id: "holdspeak-folder", destination_name: "HoldSpeak folder",
      channel: "file", account: {}, target: builtin().target, payload_digest: "d", preview: { text: "# Brief" },
      prepared_by: { kind: "owner", identity: "" }, prepare_operation_id: null, state: "sent", reason: null,
      proof: { path: `${SENT}/2026-10-05-brief.md`, ...(egress ? { egress } : {}) }, file_path: `${SENT}/2026-10-05-brief.md`,
      created_at: at, dispatch_started_at: at, settled_at: at,
    });
    let stored = [sent("icloud")];
    apiFetch.mockImplementation((path: string, init: RequestInit & { json?: Record<string, unknown> } = {}) => {
      const method = init.method ?? "GET";
      if (method === "GET" && path.startsWith("/api/channels/destinations")) return Promise.resolve({ destinations: rows });
      if (method === "GET" && path.startsWith("/api/channels/sends")) return Promise.resolve({ sends: stored });
      if (method === "POST" && path === "/api/channels/preview") return Promise.resolve({ payload_digest: "dig1", preview: { text: "# Brief" } });
      return Promise.reject(new Error(`unrouted ${method} ${path}`));
    });
    const { unmount } = render(<Well />);
    // B23: the well waits; he opens the row to read its receipt.
    fireEvent.click(within(await screen.findByTestId("destination-row")).getByText("HoldSpeak folder"));
    const receipt = await screen.findByTestId("send-sent");
    expect(receipt.textContent).toContain("SAVED");
    expect(receipt.textContent).toContain("ICLOUD");
    unmount();
    resetSendStore();
    keepPlace(`send/pick/${DOC.ref}`, ""); // B2's kept pick would reopen it; this desk starts closed
    stored = [sent()];
    render(<Well />);
    fireEvent.click(within(await screen.findByTestId("destination-row")).getByText("HoldSpeak folder"));
    const plain = await screen.findByTestId("send-sent");
    expect(plain.textContent).not.toContain("ICLOUD");
  });
});

describe("another sync service: never THIS DEVICE", () => {
  it.each([
    ["dropbox", "DROPBOX"],
    ["googledrive", "GOOGLE DRIVE"],
    ["onedrive", "ONEDRIVE"],
    ["synced", "SYNCED"],
    ["com.example.unknown", "SYNCED"],
  ])("a %s folder: the row's chip is %s (cloud scope)", async (provider, label) => {
    rows = [{ ...builtin(), synced: true, badge: "cloud", target: { ...builtin().target, cloud: provider } }];
    render(<Well />);
    const row = await screen.findByTestId("destination-row");
    expect(row.textContent).not.toContain("THIS DEVICE");
    const chip = within(row).getAllByText(label)[0];
    expect(chip.closest(".gadget-chip-egress")?.getAttribute("data-scope")).toBe("cloud");
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
