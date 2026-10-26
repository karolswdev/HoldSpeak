import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import recorded from "../../test/wire/desk-projections.remote-receipt.wire.json";
import { useProjections } from "../../desk/projections";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(), openSurface: vi.fn(), openPrimitive: vi.fn(),
  changed: null as (() => void) | null,
}));
vi.mock("../../lib/api", () => ({ apiFetch: mocks.apiFetch, readableError: String }));
vi.mock("../../desk/shell", () => ({ openSurface: mocks.openSurface, openPrimitive: mocks.openPrimitive }));
vi.mock("../../desk/useDeskChangedRefresh", () => ({ useOnDeskChanged: (reload: () => void) => { mocks.changed = reload; } }));

import { ActivityFinishedReceipts } from "./ActivityFinishedReceipts";

function wire() { return structuredClone(recorded.wire); }
// Window grammar: a receipt is a dense list row. Its name is the receipt's
// words and its subject; a press selects it, and the selection's Open
// receipt sits in the status bar (Enter or a double press opens).
const names = () => [...document.querySelectorAll("[data-testid^='activity-receipt-name-']")].map((n) => n.textContent ?? "");
const sweeps = () => names().filter((name) => name.startsWith("SWEEP 2 ROOMS"));
async function select(prefix: string) {
  const row = await waitFor(() => {
    const found = [...document.querySelectorAll<HTMLElement>("[id^='activity-receipt-']")]
      .find((li) => li.querySelector("[data-testid^='activity-receipt-name-']")?.textContent?.startsWith(prefix));
    expect(found).toBeTruthy();
    return found!;
  });
  fireEvent.click(row.querySelector("button")!);
  return row;
}
type Wire = ReturnType<typeof wire>;
function pending() {
  let resolve!: (value: Wire) => void;
  const promise = new Promise<Wire>((done) => { resolve = done; });
  return { promise, resolve };
}

// Controlled paging envelopes retain the recorded producer's row schema. The
// DB pagination contract itself is covered by test_desk_projections.py; these
// variations exercise the face's append, retry and stale-response behaviour.
function page(offset: number, count: number, more: boolean): Wire {
  const result = wire();
  result.projections = Array.from({ length: count }, (_, index) => ({
    ...result.projections[0], id: `pipeline:ev-shade-${offset + index}`,
    source_id: `ev-shade-${offset + index}`,
  }));
  result.page = { offset, limit: 50, total: 51, has_more: more };
  result.counts.receipts = 51;
  return result;
}

const shared = useProjections.getState();
beforeEach(() => {
  vi.clearAllMocks();
  mocks.changed = null;
  mocks.apiFetch.mockResolvedValue(wire());
  mocks.openSurface.mockReturnValue(true);
});
afterEach(() => {
  cleanup();
  useProjections.setState(shared, true);
});

describe("Activity Finished receipts", () => {
  it("reads the recorded receipt locally and opens its exact Rhythm door without a write", async () => {
    useProjections.setState({ query: "other face", kind: "attention", selectedId: "other-row" });
    const before = useProjections.getState();
    const view = render(<ActivityFinishedReceipts query=""/>);
    const row = await select("SWEEP 2 ROOMS");
    expect(row.getAttribute("aria-selected")).toBe("true");
    const open = screen.getByRole("button", { name: "Open receipt: SWEEP 2 ROOMS" });
    expect(open.closest(".kit-statusbar-verbs")).not.toBeNull();
    expect(view.container.querySelector("[id='activity-receipt-pipeline:ev-shade-0']")).not.toBeNull();
    // Who (owner ruling 2026-10-25): plain words, never the caller's IP,
    // never a REMOTE scope word, no egress chip on any row.
    expect(screen.getByText("Another device")).toBeInTheDocument();
    expect(view.container.textContent).not.toContain("192.168.1.43");
    expect(view.container.textContent).not.toMatch(/REMOTE/);
    expect(view.container.querySelector(".gadget-chip-egress")).toBeNull();
    const url = new URL(mocks.apiFetch.mock.calls[0][0], "http://desk.test");
    expect(Object.fromEntries(url.searchParams)).toEqual({ kind: "receipt", attention_state: "resolved", offset: "0", limit: "50" });
    fireEvent.click(open);
    expect(mocks.openSurface).toHaveBeenCalledWith("configure-cadence", undefined);
    expect(sweeps()).toEqual(["SWEEP 2 ROOMS · Heartbeat"]);
    expect(useProjections.getState()).toBe(before);
    expect(mocks.apiFetch.mock.calls.every((call) => call[1].method === "GET")).toBe(true);
    expect(mocks.openPrimitive).not.toHaveBeenCalled();
  });

  it.each(["this_machine", "configured_inference_target"])("keeps symbolic local destination %s quiet", async (destination) => {
    const result = wire();
    Object.assign(result.projections[0], { origin: "local", caller: "", actual_destination: destination });
    mocks.apiFetch.mockResolvedValue(result);
    const view = render(<ActivityFinishedReceipts query=""/>);
    await waitFor(() => expect(sweeps()).toHaveLength(1));
    expect(view.container.querySelector(".gadget-chip-egress")).toBeNull();
    expect(screen.queryByTestId("activity-remote")).toBeNull();
  });

  it("keeps an outgoing destination off the row (owner ruling 2026-10-25)", async () => {
    const result = wire();
    Object.assign(result.projections[0], { origin: "local", caller: "", actual_destination: "192.168.1.44" });
    mocks.apiFetch.mockResolvedValue(result);
    const view = render(<ActivityFinishedReceipts query=""/>);
    await waitFor(() => expect(sweeps()).toHaveLength(1));
    expect(view.container.textContent).not.toContain("192.168.1.44");
    expect(view.container.querySelector(".gadget-chip-egress")).toBeNull();
  });

  it("retains read rows through failure and Retry repeats only the failed GET", async () => {
    render(<ActivityFinishedReceipts query=""/>);
    await waitFor(() => expect(sweeps()).toHaveLength(1));
    mocks.apiFetch.mockRejectedValueOnce(new Error("offline"));
    act(() => mocks.changed?.());
    expect(await screen.findByRole("alert")).toHaveTextContent("Finished read failed · Shown receipts kept · Retry");
    expect(sweeps()).toHaveLength(1);
    expect(screen.getByText("Last read")).toBeInTheDocument();
    mocks.apiFetch.mockResolvedValueOnce(wire());
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(new Set(mocks.apiFetch.mock.calls.map((call) => call[0])).size).toBe(1);
    expect(mocks.apiFetch.mock.calls.every((call) => call[1].method === "GET")).toBe(true);
  });

  it("names a failed first read without claiming an empty or successful list", async () => {
    mocks.apiFetch.mockRejectedValue(new Error("offline"));
    render(<ActivityFinishedReceipts query=""/>);
    expect(await screen.findByRole("alert")).toHaveTextContent("Finished read failed · Records unchanged · Retry");
    expect(screen.queryByText("No finished receipts")).toBeNull();
    expect(screen.queryByRole("button", { name: /Open receipt/ })).toBeNull();
  });

  it.each(["", "/", "/unknown", "https://example.test/cadence", "/cadence?wrong=1", "/history?kind=dictation"])("names unsupported door %s without a fallback", async (detail_url) => {
    const result = wire();
    result.projections[0].detail_url = detail_url;
    mocks.apiFetch.mockResolvedValue(result);
    render(<ActivityFinishedReceipts query=""/>);
    await select("SWEEP 2 ROOMS");
    expect(await screen.findByText("Receipt view unavailable")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Open receipt/ })).toBeNull();
    expect(mocks.openSurface).not.toHaveBeenCalled();
    expect(mocks.openPrimitive).not.toHaveBeenCalled();
  });

  it("names an unregistered canonical door and keeps its row", async () => {
    mocks.openSurface.mockReturnValue(false);
    render(<ActivityFinishedReceipts query=""/>);
    await select("SWEEP 2 ROOMS");
    fireEvent.click(screen.getByRole("button", { name: "Open receipt: SWEEP 2 ROOMS" }));
    expect(screen.getByText("Receipt view unavailable")).toBeInTheDocument();
    expect(sweeps()).toHaveLength(1);
    expect(mocks.openPrimitive).not.toHaveBeenCalled();
  });

  it("opens only the exact meeting named by its source door", async () => {
    const result = wire();
    Object.assign(result.projections[0], { source_kind: "meeting", subject_ref: "meeting:m1", detail_url: "/history?meeting=m1", title: "Meeting saved" });
    mocks.apiFetch.mockResolvedValue(result);
    const view = render(<ActivityFinishedReceipts query=""/>);
    const row = await select("Meeting saved");
    // Enter on the selected row opens it (the list's own open).
    fireEvent.keyDown(row.querySelector("button")!, { key: "Enter" });
    expect(mocks.openSurface).toHaveBeenCalledWith("review-meetings", "meeting:m1");
    view.unmount();
    result.projections[0].detail_url = "/history?meeting=other";
    mocks.apiFetch.mockResolvedValue(result);
    render(<ActivityFinishedReceipts query=""/>);
    await select("Meeting saved");
    expect(await screen.findByText("Receipt view unavailable")).toBeInTheDocument();
    expect(mocks.openSurface).toHaveBeenCalledTimes(1);
  });

  it("keeps the page offset after failure and retries that page before appending", async () => {
    mocks.apiFetch.mockResolvedValueOnce(page(0, 50, true));
    render(<ActivityFinishedReceipts query=""/>);
    await screen.findByRole("button", { name: "Load more" });
    mocks.apiFetch.mockRejectedValueOnce(new Error("offline"));
    fireEvent.click(screen.getByRole("button", { name: "Load more" }));
    await screen.findByRole("alert");
    expect(sweeps()).toHaveLength(50);
    mocks.apiFetch.mockResolvedValueOnce(page(50, 1, false));
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(sweeps()).toHaveLength(51));
    expect(mocks.apiFetch.mock.calls.slice(1).map((call) => new URL(call[0], "http://desk.test").searchParams.get("offset"))).toEqual(["50", "50"]);
    expect(screen.queryByRole("button", { name: "Load more" })).toBeNull();
  });

  it("ignores an old query response after the new query read settles", async () => {
    const old = pending();
    mocks.apiFetch.mockReturnValueOnce(old.promise);
    const view = render(<ActivityFinishedReceipts query=""/>);
    const empty = wire();
    empty.projections = [];
    empty.counts.receipts = 0;
    empty.page.total = 0;
    mocks.apiFetch.mockResolvedValueOnce(empty);
    view.rerender(<ActivityFinishedReceipts query="absent"/>);
    await screen.findByText("No matching receipts");
    await act(async () => old.resolve(wire()));
    expect(sweeps()).toHaveLength(0);
    expect(new URL(mocks.apiFetch.mock.calls[1][0], "http://desk.test").searchParams.get("q")).toBe("absent");
  });

  it("ignores a pending page after a newer refresh replaces the read", async () => {
    mocks.apiFetch.mockResolvedValueOnce(page(0, 50, true));
    render(<ActivityFinishedReceipts query=""/>);
    await screen.findByRole("button", { name: "Load more" });
    const oldPage = pending();
    mocks.apiFetch.mockReturnValueOnce(oldPage.promise);
    fireEvent.click(screen.getByRole("button", { name: "Load more" }));
    expect(screen.getByRole("button", { name: "Load more" })).toBeDisabled();
    mocks.apiFetch.mockResolvedValueOnce(wire());
    act(() => mocks.changed?.());
    await waitFor(() => expect(sweeps()).toHaveLength(1));
    await act(async () => oldPage.resolve(page(50, 1, false)));
    expect(sweeps()).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Load more" })).toBeNull();
  });
});
