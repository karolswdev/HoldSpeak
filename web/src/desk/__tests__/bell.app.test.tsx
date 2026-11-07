// The bell: one number on the menubar. The test diet (2026-10-11) moved the
// Bell leg of tests/e2e/test_times_local_zone_glass.py here; that leg and the
// shade's sections rendered SystemShade, which no Desk mounts. They are parked
// with it (web/src/desk/_parked/attention/__tests__/bell.app.test.tsx).
//
// The zone is pinned to America/Denver at module top, the way
// web/src/pages/cores/__tests__/peoplePrepB4.test.tsx pins it.
process.env.TZ = "America/Denver";

import { act, render, screen, waitFor, within } from "@testing-library/react";
import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { useProjections } from "../projections";
import { recordedGet, type Gets } from "../../test/recordedHub";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));

vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
}));

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn(), openProjectRoom: vi.fn() }));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openSurfaceOr: shell.openSurfaceOr,
  openProjectRoom: shell.openProjectRoom,
}));

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  useProjections.setState({ projections: [], counts: {}, subject_counts: {} });
});

afterAll(() => {
  delete process.env.TZ;
});

/* ── Betterment daily D1: one number on the bell and the Project icon ──────────
 * The recon week (tests/fixtures/daily_week) on the real hub, today as its
 * Monday, after the nine keeps: the hub counts 4 (mine due today 2, to decide
 * 2; what Mira, Theo and Jun owe never counts). The recorded answer is
 * tests/unit/test_desk_needs_you.py::test_the_one_number_is_mine_due_today_and_to_decide
 * (fixtures/daily-week/needs-you.json). The bell said 11 and the Project icon
 * 12 in the recon (RECON.md §2). */
import dailyWeek from "./fixtures/daily-week/needs-you.json";
import { DeskChrome } from "../components/DeskChrome";
import { projectOpenHere, readNeedsYouAnswer, readProjectCounts, refreshNeedsYou, resetNeedsYou } from "../needsYou";
import { composeScreen } from "../screen/compose";
import { EMPTY_ITEMS } from "../api";

describe("Bell: the daily week's one number", () => {
  it("the bell, the members and the Project icon all say 4", async () => {
    resetNeedsYou();
    const gets: Gets = { "/api/desk/needs-you?fresh=1": dailyWeek.needsYou };
    vi.mocked(apiFetch).mockImplementation(async (path: string) => recordedGet(gets, path) as never);
    render(<DeskChrome />);
    await act(async () => { await refreshNeedsYou(true); });
    const bell = await screen.findByTestId("desk-bell");
    await waitFor(() => expect(bell.querySelector("strong")?.textContent).toBe("4"));

    const read = readNeedsYouAnswer(dailyWeek.needsYou as never);
    expect(read.count).toBe(4);
    expect(read.members.map((m) => m.item?.title).filter(Boolean).sort()).toEqual([
      "Do it", "Email Dana about the cutover window",
      "Review design doc on settlement retries",
      "Talk about the staff path in our next one-on-one",
    ]);

    const project = dailyWeek.projects.projects as Array<{ id: string; name: string }>;
    const counts = projectOpenHere({ projectCounts: readProjectCounts(dailyWeek.needsYou as never), unmutedItems: read.unmutedItems });
    expect(Object.values(counts)).toEqual([4]);
    // The Room's own count (it counts what others owe) is not the badge.
    expect(Object.values(dailyWeek.needsYou.roomCounts)).toEqual([9]);
    const screenObjects = composeScreen({
      items: { ...EMPTY_ITEMS, project: project.map((p) => ({ id: p.id, name: p.name })) },
      projectCounts: counts, needsCount: read.count, needsRefs: new Set(), heldCalls: 0,
      sessions: [], flights: [], filed: new Set(), persons: [], membersLoaded: true,
    } as never);
    const icon = (screenObjects as Array<{ kind?: string; lamp?: { count?: number } }>).find((o) => o.kind === "project");
    expect(icon?.lamp?.count).toBe(4);
  });
});

/* ── MENUBAR-STILL (2026-10-29): the count's slot is there before the read ──
 * The desk sweep's desk-1440 still fence saw the bell and the hub dot move
 * 27 px under load: the Needs-you read landed inside the 1.5 s watch and its
 * count mounted, so the bell grew. The slot is drawn before the read, the
 * count lands IN it, and the CSS gives the slot its full width at once. */
import chromeMenusCss from "../components/chrome-menus.css?raw";
import tokensCss from "../../styles/tokens.css?raw";

describe("Bell: the count's slot holds the bar still", () => {
  it("draws the empty slot before the Needs-you read and the count lands in the same slot", async () => {
    resetNeedsYou();
    let answer: (value: unknown) => void = () => undefined;
    const held = new Promise((resolve) => { answer = resolve; });
    vi.mocked(apiFetch).mockImplementation(async (path: string) => {
      if (path.startsWith("/api/desk/needs-you")) return (await held) as never;
      return recordedGet({}, path) as never;
    });
    render(<DeskChrome />);
    const bell = await screen.findByTestId("desk-bell");
    const slot = within(bell).getByTestId("desk-bell-slot");
    expect(slot.querySelector("strong")).toBeNull();
    expect(slot.textContent).toBe("");

    await act(async () => { answer(dailyWeek.needsYou); await held; });
    await waitFor(() => expect(slot.querySelector("strong")?.textContent).toBe("4"));
    expect(within(bell).getByTestId("desk-bell-slot")).toBe(slot);
  });

  it("gives the slot its two-digit width from the badge token, empty or full", () => {
    const rule = chromeMenusCss.match(/\.desk-menubar \.desk-bell-slot \{([^}]*)\}/);
    expect(rule?.[1]).toMatch(/min-width:\s*var\(--desk-badge-slot-w\)/);
    expect(rule?.[1]).toMatch(/flex:\s*0 0 auto/);
    expect(tokensCss).toMatch(/--desk-badge-slot-w:\s*calc\(var\(--desk-badge-h\) \+ 6px\)/);
  });
});
