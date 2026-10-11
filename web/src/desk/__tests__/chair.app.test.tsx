// The Chair app (test diet, 2026-10-11): the fresh arrival, moved off the
// browser. The real ChairHome, its real window store and the real menu bar;
// only `apiFetch` is mocked, with the hub's answers (the cold roster shape of
// `/api/inference/assignments`, as the Chair window fence uses it).
//
// replaces: tests/e2e/test_philo14_a1_fresh_arrival_glass.py::TestFreshArrival::test_the_fresh_desk_reaches_every_chair_window
// Facts that already have a successor elsewhere (cited, not repeated):
//  - the People drawer opens the People window on the desk (Enter):
//    web/src/desk/screen/__tests__/Screen.test.tsx:254-255
//  - Needs you from its drawer (Enter): chairWindows.philo1311.test.tsx:175-179
//  - 393 Go lists Needs you, Brief, The week, Capture first:
//    web/src/desk/components/window/phoneRing.test.tsx:198-206
//  - 393 the Dock's Speak opens Capture: chairWindows.philo1311.test.tsx:221-223
//  - TALK is one press on the screen: Screen.test.tsx:351
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../lib/api";
import { asHub } from "../../test/hubNeedsYou";

vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

/** A cold HOME: no engine is assigned, nothing needs him yet. */
function coldHub() {
  vi.mocked(apiFetch).mockImplementation(asHub(async (path: string) => {
    const p = String(path);
    if (p === "/api/inference/assignments")
      return {
        schema: "InferenceAssignmentSummary@1", rows: [], issue_count: 0,
        task_overrides: [{ id: "meeting.deferred_analysis", has_override: false, effective: { status: "unassigned" } }],
      };
    if (p.startsWith("/api/door")) return { board: {}, counts: {}, upcoming: [], calendar_configured: false };
    return null;
  }));
}

const region = (name: string) => screen.queryByRole("region", { name });

beforeEach(() => {
  localStorage.clear();
  vi.mocked(apiFetch).mockReset();
  coldHub();
});

describe("Chair app: the fresh arrival", () => {
  it("a desk that remembers nothing opens with no Chair window", async () => {
    vi.resetModules();
    const fresh = await import("../chair/chairWindows");
    for (const id of ["chair:needs", "chair:brief", "chair:week", "chair:capture"])
      expect(fresh.isChairWindowOpen(id), id).toBe(false);
    const { ChairHome } = await import("../chair/ChairHome");
    render(<ChairHome />);
    expect(document.querySelectorAll(".desk-window-shell.chair-window")).toHaveLength(0);
    expect(screen.getByTestId("desk-screen")).toBeTruthy();
  });

  it("1440: Window ▸ Chair reaches Needs you, Brief, The week and Capture; Needs you names the No engine SETUP row", async () => {
    vi.resetModules();
    const { ChairHome } = await import("../chair/ChairHome");
    const { DeskMenuBar } = await import("../components/DeskMenuBar");
    const { isChairWindowOpen } = await import("../chair/chairWindows");
    render(<><DeskMenuBar /><ChairHome /></>);
    expect(document.querySelectorAll(".desk-window-shell.chair-window")).toHaveLength(0);

    const pick = async (name: string) => {
      fireEvent.click(screen.getByRole("button", { name: "Window" }), { detail: 0 });
      const menu = screen.getByRole("menu", { name: "Window menu" });
      const chair = within(menu).getAllByRole("menuitem")
        .find((h) => h.getAttribute("aria-haspopup") === "menu" && /Chair/.test(h.textContent ?? ""));
      expect(chair, "Window holds the Chair submenu").toBeTruthy();
      fireEvent.click(chair!);
      const rows = within(menu).getAllByRole("menuitemcheckbox")
        .map((h) => h.querySelector(".desk-menu-label")?.textContent?.trim());
      const four = ["Needs you", "Brief", "The week", "Capture"];
      expect(rows.filter((label) => four.includes(label ?? ""))).toEqual(four);
      const row = within(menu).getAllByRole("menuitemcheckbox")
        .find((h) => h.querySelector(".desk-menu-label")?.textContent?.trim() === name)!;
      act(() => void fireEvent.click(row));
      await waitFor(() => expect(region(name), name).toBeTruthy());
    };

    await pick("Needs you");
    expect(isChairWindowOpen("chair:needs")).toBe(true);
    const setup = await waitFor(() => {
      const row = region("Needs you")!.querySelector('[data-testid="needs-row"][data-object-id^="blocker:"]');
      expect(row, "the SETUP row of the cold HOME").toBeTruthy();
      return row as HTMLElement;
    });
    expect(setup.textContent).toContain("No engine");
    expect(setup.textContent).toContain("Choose an engine");

    await pick("Brief");
    expect(within(region("Brief")!).getByTestId("arrival-brief")).toBeTruthy();
    await pick("The week");
    await pick("Capture");
    expect(within(region("Capture")!).getByTestId("arrival-capture-bar")).toBeTruthy();
  });
});
