// PHILO-15 04 (gap 14): Parked is a drawer of objects. The Parked icon opens
// one list of every parked object across kinds (meetings, Workbench items,
// Projects); a row opens where it lives; Restore uses the kind's own route
// and the one park receipt; a kind the hub could not read is named.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";
import { ParkedDrawer, parkedRow, type ParkedItem } from "../ParkedDrawer";
import { openParkedDrawer, useDrawers } from "../store";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});
const shell = vi.hoisted(() => ({ opened: [] as string[] }));
vi.mock("../../shell", async () => {
  const actual = await vi.importActual<typeof import("../../shell")>("../../shell");
  return { ...actual, openSurfaceOr: (key: string) => shell.opened.push(key) };
});

const ITEMS: ParkedItem[] = [
  { ref: "meeting:m-1", kind: "meeting", id: "m-1", name: "Vendor call", when: "2026-10-06T10:00:00", home: {} },
  { ref: "workbench_item:i-1", kind: "workbench_item", id: "i-1", name: "Draft the runbook", when: "2026-10-05T10:00:00", home: { workbench_id: "wb-1", workbench_name: "Ops" } },
  { ref: "project:p-old", kind: "project", id: "p-old", name: "Old migration", when: "2026-10-04T10:00:00", home: {} },
];

let parked: ParkedItem[] = [];
let notRead: string[] = [];
let partial: string[] = [];
const posts: string[] = [];

beforeEach(() => {
  parked = [...ITEMS];
  notRead = [];
  partial = [];
  posts.length = 0;
  shell.opened.length = 0;
  apiFetch.mockReset();
  apiFetch.mockImplementation(async (path: string, init?: { method?: string }) => {
    if (path === "/api/desk/parked") return { items: parked, not_read: notRead, partial };
    if (init?.method === "POST") {
      posts.push(path);
      parked = parked.filter((i) => !path.includes(encodeURIComponent(i.id)));
      return { meeting: { id: "m-1" }, item: { id: "i-1" }, success: true };
    }
    return {};
  });
  useDrawers.setState({ drawers: [], infos: [], parked: null, revision: 0, receipts: {} });
});
afterEach(() => vi.restoreAllMocks());

const rowOf = (name: RegExp) => screen.getByRole("button", { name });

describe("the Parked drawer", () => {
  it("the Parked icon's opener opens the drawer once", () => {
    openParkedDrawer();
    expect(useDrawers.getState().parked).toEqual({ origin: null });
    openParkedDrawer();
    expect(useDrawers.getState().parked).toEqual({ origin: null });
  });

  it("lists every parked object across kinds in one list", async () => {
    render(<ParkedDrawer origin={null} />);
    const list = await screen.findByRole("grid", { name: "Parked" });
    expect(within(list).getAllByRole("row")).toHaveLength(4); // the head + three rows
    expect(rowOf(/^Vendor call, MEETING/)).toBeTruthy();
    expect(rowOf(/^Draft the runbook, WORKBENCH ITEM/)).toBeTruthy();
    expect(rowOf(/^Old migration, PROJECT/)).toBeTruthy();
    expect(screen.getByText("3 OBJECTS")).toBeTruthy();
  });

  it("Restore uses each kind's own route and shows the park receipt", async () => {
    const refresh = vi.spyOn(useDesk.getState(), "refresh").mockResolvedValue(undefined as never);
    render(<ParkedDrawer origin={null} />);
    fireEvent.click(await screen.findByRole("button", { name: /^Old migration, PROJECT/ }));
    await act(async () => {
      fireEvent.click(screen.getByTestId("parked-restore"));
    });
    expect(posts).toEqual(["/api/projects/p-old/restore"]);
    await waitFor(() => expect(screen.getByTestId("parked-receipt").textContent).toMatch(/^RESTORED \d\d:\d\d/));
    await waitFor(() => expect(screen.queryByRole("button", { name: /^Old migration/ })).toBeNull());
    expect(refresh).toHaveBeenCalled();

    fireEvent.click(rowOf(/^Draft the runbook/));
    await act(async () => {
      fireEvent.click(screen.getByTestId("parked-restore"));
    });
    expect(posts[1]).toBe("/api/workbenches/wb-1/items/i-1/restore");
  });

  it("a refused restore says NOT RESTORED with Retry", async () => {
    apiFetch.mockImplementation(async (path: string, init?: { method?: string }) => {
      if (path === "/api/desk/parked") return { items: parked, not_read: [] };
      if (init?.method === "POST") throw new Error("409");
      return {};
    });
    render(<ParkedDrawer origin={null} />);
    fireEvent.click(await screen.findByRole("button", { name: /^Vendor call/ }));
    await act(async () => {
      fireEvent.click(screen.getByTestId("parked-restore"));
    });
    const receipt = await screen.findByTestId("parked-receipt");
    expect(receipt.textContent).toContain("NOT RESTORED");
    expect(within(receipt).getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("Open goes to where the object lives", async () => {
    const openWb = vi.spyOn(useDesk.getState(), "openWorkbenchWindow").mockImplementation(() => undefined);
    render(<ParkedDrawer origin={null} />);
    fireEvent.doubleClick(await screen.findByRole("button", { name: /^Vendor call/ }));
    expect(shell.opened).toEqual(["review-meetings"]);
    fireEvent.doubleClick(rowOf(/^Draft the runbook/));
    expect(openWb).toHaveBeenCalledWith("wb-1");
    fireEvent.doubleClick(rowOf(/^Old migration/));
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toContain("p-old");
  });

  it("a kind the hub could not read is named; nothing parked says so once", async () => {
    parked = [];
    notRead = ["workbench_item"];
    const { unmount } = render(<ParkedDrawer origin={null} />);
    expect((await screen.findByTestId("parked-not-read")).textContent).toBe("WORKBENCH ITEMS · NOT READ");
    unmount();
    notRead = [];
    render(<ParkedDrawer origin={null} />);
    expect(await screen.findByText("Nothing parked")).toBeTruthy();
    // no counter of zero
    expect(screen.queryByText(/0 OBJECTS/)).toBeNull();
  });

  it("a kind read part way shows its rows and says NOT READ · PARTIAL", async () => {
    notRead = ["meeting"];
    partial = ["meeting"];
    render(<ParkedDrawer origin={null} />);
    expect((await screen.findByTestId("parked-not-read")).textContent).toBe("MEETINGS · NOT READ · PARTIAL");
    expect(rowOf(/^Vendor call, MEETING/)).toBeTruthy();
  });

  it("a workbench item row wears its own kind word and the workbench sprite", () => {
    const row = parkedRow(ITEMS[1], new Date("2026-10-07T10:00:00"));
    expect(row.kindWord).toBe("WORKBENCH ITEM");
    expect(row.sprite).toMatch(/cartridge|workbench/);
  });
});
