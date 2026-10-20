/** PHILO-17 (doors): the next 1:1 moved from the Dock's People tile to the
 *  People drawer on the Screen. The four Dock cases (H-C3) restored against
 *  the new home, plus the drawer and icon faces. */
import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => {
  const people = {
    readiness: { readiness: "ready" as string },
    readinessError: null as Error | null,
  };
  const defaultApiFetch = async (path: string): Promise<unknown> => {
    if (path === "/api/people/readiness") {
      if (people.readinessError) throw people.readinessError;
      return people.readiness;
    }
    if (path === "/api/people/relationships") return { relationships: [{ id: "r1" }] };
    return { brief: { next_one_on_one: "2026-10-03T15:00:00Z" } };
  };
  const reloads: Array<() => void> = [];
  return { people, defaultApiFetch, apiFetch: vi.fn(defaultApiFetch), reloads };
});

vi.mock("../../../lib/api", () => ({ apiFetch: mocks.apiFetch }));
vi.mock("../../useDeskChangedRefresh", () => ({
  // The hub's desk_changed frame: the test calls the reload by hand.
  useOnDeskChanged: (reload: () => void) => {
    mocks.reloads.push(reload);
  },
}));

import { useNextOneOnOne, useNextOneOnOneRead } from "../nextOneOnOne";
import { composeScreen, type ScreenInputs } from "../compose";
import { DeskIcon } from "../../surface";
import { EMPTY_ITEMS } from "../../api";

const deskChanged = () => act(() => {
  mocks.reloads.at(-1)?.();
});

beforeEach(() => {
  mocks.apiFetch.mockReset();
  mocks.apiFetch.mockImplementation(mocks.defaultApiFetch);
  mocks.people.readiness = { readiness: "ready" };
  mocks.people.readinessError = null;
  mocks.reloads.length = 0;
});

describe("the next 1:1 read (moved from the Dock)", () => {
  it("reads the next 1:1 through the relationship brief", async () => {
    const { result } = renderHook(() => useNextOneOnOne());
    await waitFor(() => expect(result.current).toMatch(/^1:1 \d\d:\d\d$/));
    expect(mocks.apiFetch).toHaveBeenCalledWith("/api/people/relationships/r1/brief");
  });

  it.each([0, 1])("the Dock shows a 1:1 only on its local day (offset %i)", async (offset) => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(2026, 9, 3, 12));
    try {
      mocks.apiFetch.mockImplementation(async (path) => path.endsWith("/brief")
        ? { brief: { next_one_on_one: new Date(2026, 9, 3 + offset, 15).toISOString() } }
        : mocks.defaultApiFetch(path));
      const { result } = renderHook(() => useNextOneOnOneRead(true));
      await waitFor(() => expect(result.current.reading).toBe(false));
      if (offset === 0) expect(result.current.label).toBe("1:1 15:00");
      else expect(result.current.label).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("shows nothing when the People read fails", async () => {
    mocks.apiFetch.mockImplementation(async () => {
      throw new Error("people unavailable");
    });
    const { result } = renderHook(() => useNextOneOnOne());
    await waitFor(() => expect(mocks.apiFetch).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 0));
    expect(result.current).toBeNull();
  });

  it("reads People readiness before protected relationships", async () => {
    const { result } = renderHook(() => useNextOneOnOne());
    await waitFor(() => expect(result.current).toMatch(/^1:1/));
    const paths = mocks.apiFetch.mock.calls.map(([path]) => path);
    const readinessIndex = paths.indexOf("/api/people/readiness");
    const relationshipsIndex = paths.indexOf("/api/people/relationships");
    expect(readinessIndex).toBeGreaterThanOrEqual(0);
    expect(relationshipsIndex).toBeGreaterThanOrEqual(0);
    expect(readinessIndex).toBeLessThan(relationshipsIndex);
  });

  it.each([
    ["unconfigured", { readiness: "unconfigured" }],
    ["unavailable", { readiness: "unavailable" }],
  ] as const)("clears the stale 1:1 mark and gates relationships when People is %s", async (_label, readiness) => {
    const { result } = renderHook(() => useNextOneOnOne());
    await waitFor(() => expect(result.current).toMatch(/^1:1/));
    const relationshipReads = () => mocks.apiFetch.mock.calls
      .filter(([path]) => path === "/api/people/relationships").length;
    const before = relationshipReads();
    mocks.people.readiness = readiness;
    deskChanged();
    await waitFor(() => expect(result.current).toBeNull());
    expect(relationshipReads()).toBe(before);
  });

  it("clears the 1:1 mark and withholds relationships when the readiness request fails", async () => {
    const { result } = renderHook(() => useNextOneOnOne());
    await waitFor(() => expect(result.current).toMatch(/^1:1/));
    const relationshipReads = () => mocks.apiFetch.mock.calls
      .filter(([path]) => path === "/api/people/relationships").length;
    const before = relationshipReads();
    mocks.people.readinessError = new Error("readiness unavailable");
    deskChanged();
    await waitFor(() => expect(result.current).toBeNull());
    expect(relationshipReads()).toBe(before);
  });
});

describe("the People drawer wears it", () => {
  const inputs = (peopleCaption: string | null): ScreenInputs => ({
    items: EMPTY_ITEMS,
    projectCounts: {},
    needsCount: 0,
    needsRefs: new Set(),
    heldCalls: 0,
    sessions: [],
    flights: [],
    filed: new Set(),
    persons: [],
    membersLoaded: true,
    peopleCaption,
  });

  it("puts the caption on the People drawer only, and nothing without a next 1:1", () => {
    const withIt = composeScreen(inputs("1:1 15:00"));
    expect(withIt.find((o) => o.key === "drawer:people")?.caption).toBe("1:1 15:00");
    expect(withIt.filter((o) => o.caption).map((o) => o.key)).toEqual(["drawer:people"]);
    expect(composeScreen(inputs(null)).find((o) => o.key === "drawer:people")?.caption).toBeUndefined();
  });

  it("the icon draws the caption and says it in its name; no caption, no line", () => {
    const { rerender } = render(<DeskIcon id="drawer:people" kind="person" kindWord="DRAWER" name="People" caption="1:1 15:00" />);
    expect(screen.getByTestId("desk-icon-caption-drawer:people")).toHaveTextContent("1:1 15:00");
    expect(screen.getByRole("button", { name: "People, DRAWER, 1:1 15:00" })).toBeTruthy();
    rerender(<DeskIcon id="drawer:people" kind="person" kindWord="DRAWER" name="People" />);
    expect(screen.queryByTestId("desk-icon-caption-drawer:people")).toBeNull();
  });
});
