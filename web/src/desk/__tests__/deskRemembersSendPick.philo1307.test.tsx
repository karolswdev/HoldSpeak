/* PHILO-13-07 (B2, slice two) — the SEND well's destination pick is the
 * document's place: it returns after a reload, per document, and only onto
 * a destination that is still listed. The pick's preview is a read
 * (POST /api/channels/preview computes; it sends nothing). Red on 22287ab1. */
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../pages/cores/connections/api", async () => {
  const actual = await vi.importActual<typeof import("../../pages/cores/connections/api")>("../../pages/cores/connections/api");
  return { ...actual, fetchConnections: () => Promise.resolve({ tools: [] }) };
});

const KEY = "hs.desk.workspace.v1";
const stored = () => JSON.parse(localStorage.getItem(KEY) || "{}");
const folder = { id: "chd_f", name: "Team folder", channel: "file", account: {}, target: { folder: "/tmp/Team" },
  synced: false, state: "active", created_at: "2026-09-29T10:00:00Z", parked_at: null };
let destinations: unknown[] = [folder];
const sent: string[] = [];

beforeEach(() => {
  localStorage.clear();
  vi.resetModules();
  destinations = [folder];
  sent.length = 0;
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string, init: RequestInit = {}) => {
    const key = `${init.method ?? "GET"} ${path.split("?")[0]}`;
    if (key === "GET /api/channels/destinations") return Promise.resolve({ destinations });
    if (key === "GET /api/channels/sends") return Promise.resolve({ sends: [] });
    if (key === "POST /api/channels/preview") return Promise.resolve({ payload_digest: "d1", preview: { text: "# Doc" } });
    sent.push(key);
    return Promise.reject(new Error(`unrouted ${key}`));
  });
});

const DOC = { ref: "meeting_summary:m1", title: "Ledger sync summary", label: "SUMMARY" };
const openRow = () => screen.getAllByTestId("destination-row").find((r) => r.getAttribute("aria-expanded") === "true" || r.textContent?.includes("●"));

describe("B2: the SEND pick returns after a reload", () => {
  it("picked Team folder for one document comes back picked; another document starts unpicked; no send", async () => {
    let { SendWells } = await import("../surface/send");
    const first = render(<SendWells doc={DOC} />);
    const row = (await screen.findAllByTestId("destination-row"))[0];
    fireEvent.click(within(row).getByText("Team folder"));
    await waitFor(() => expect(stored().places[`send/pick/${DOC.ref}`]).toBe("chd_f"));
    first.unmount();

    vi.resetModules();
    ({ SendWells } = await import("../surface/send"));
    const second = render(<SendWells doc={DOC} />);
    await waitFor(() => expect(openRow()).toBeTruthy());
    second.unmount();
    const other = render(<SendWells doc={{ ...DOC, ref: "meeting_summary:m2" }} />);
    await screen.findAllByTestId("destination-row");
    expect(openRow()).toBeFalsy();
    other.unmount();
    expect(sent).toEqual([]);
  });

  it("a kept pick onto a destination that is gone is not restored", async () => {
    let { SendWells } = await import("../surface/send");
    const first = render(<SendWells doc={DOC} />);
    fireEvent.click(within((await screen.findAllByTestId("destination-row"))[0]).getByText("Team folder"));
    await waitFor(() => expect(stored().places[`send/pick/${DOC.ref}`]).toBe("chd_f"));
    first.unmount();
    destinations = [{ ...folder, id: "chd_other", name: "Other folder" }];
    vi.resetModules();
    ({ SendWells } = await import("../surface/send"));
    const second = render(<SendWells doc={DOC} />);
    await screen.findAllByTestId("destination-row");
    expect(openRow()).toBeFalsy();
    second.unmount();
  });
});
