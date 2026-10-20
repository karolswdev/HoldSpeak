// PHILO-14 A1 — ChairHome renders the screen of objects after arrival; the
// first-run path (arrivalRequired) is untouched; a fresh desk opens with the
// four Chair windows closed (they open on demand).
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../firstrun/FirstRun", () => ({ FirstRun: () => <div data-testid="first-run" /> }));

beforeEach(() => {
  localStorage.clear();
  vi.resetModules();
  vi.mocked(apiFetch).mockReset();
  vi.mocked(apiFetch).mockImplementation(async () => null);
});

describe("PHILO-14 A1 — the Chair is the screen", () => {
  it("keeps phone Go and adds the same real root drawers as a named Drawers section", async () => {
    const { EMPTY_ITEMS, fromWireDirectory, qualifiedRef } = await import("../../api");
    const { useDesk } = await import("../../store");
    const { GoHome } = await import("../GoHome");
    // Recorded real GET /api/directories, produced in root's isolated hub.
    const folder = fromWireDirectory({ id: "dir_b5c056b59f3e", name: "Platform", parent_id: null,
      member_ids: ["note:note_0b9ebdadf0fa"], created_at: "2026-10-16T01:39:56Z" })!;
    const child = fromWireDirectory({ id: "dir_3e8aa70e9523", name: "Architecture", parent_id: folder.id,
      member_ids: [], created_at: "2026-10-16T01:39:56Z" })!;
    const orphan = { ...child, id: "orphan", name: "Unfiled drawer", parentId: "missing-parent" };
    const openPullout = vi.fn();
    useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [child, folder, orphan] }, projects: [], selectedIds: [], openPullout });
    render(<GoHome />);
    expect(screen.getByRole("menu", { name: "Go menu" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Drawers" })).toBeInTheDocument();
    expect(screen.getByRole("menuitem", { name: /Meetings/ })).toBeInTheDocument();
    expect(screen.queryByRole("menuitem", { name: /Architecture/ })).toBeNull();
    const row = screen.getByRole("menuitem", { name: /Platform/ });
    expect(row).toHaveAttribute("data-object-id", qualifiedRef("directory", folder.id));
    fireEvent.click(row);
    expect(openPullout).toHaveBeenCalledWith(qualifiedRef("directory", folder.id));
    fireEvent.click(screen.getByRole("menuitem", { name: /Unfiled drawer/ }));
    expect(openPullout).toHaveBeenCalledWith(qualifiedRef("directory", orphan.id));
  });

  it("routes the same-name Meetings app and drawer to their exact existing destinations", async () => {
    const { EMPTY_ITEMS, fromWireDirectory, qualifiedRef } = await import("../../api");
    const { useDesk } = await import("../../store");
    const { VERBS } = await import("../../verbRegistry");
    const { GoHome } = await import("../GoHome");
    const saved = useDesk.getState();
    const app = VERBS.find((verb) => verb.id === "go.review-meetings")!;
    const run = vi.spyOn(app, "run").mockImplementation(() => {});
    const openPullout = vi.fn();
    // View-store name collision; actual directory writer proof belongs to root.
    const directory = fromWireDirectory({ id: "dir_b5c056b59f3e", name: "Meetings", parent_id: null, member_ids: [], created_at: "2026-10-16T01:39:56Z" })!;
    try {
      useDesk.setState({ items: { ...EMPTY_ITEMS, directory: [directory] }, projects: [], selectedIds: [], openPullout });
      render(<GoHome />);
      // Betterment P4: Projects (All projects) is drawn on an empty desk too.
      expect(screen.getAllByRole("heading").map((heading) => heading.textContent)).toEqual(["Apps", "Projects", "Work", "Drawers", "New"]);
      const appRow = within(screen.getByRole("heading", { name: "Apps" }).closest("section")!).getByRole("menuitem", { name: "Meetings" });
      const drawerRow = within(screen.getByRole("heading", { name: "Drawers" }).closest("section")!).getByRole("menuitem", { name: "Meetings" });
      expect(appRow).not.toHaveAttribute("data-object-id");
      expect(drawerRow).toHaveAttribute("data-object-id", qualifiedRef("directory", directory.id));
      fireEvent.click(appRow);
      expect(run).toHaveBeenCalledOnce();
      expect(run).toHaveBeenCalledWith({ selectedRef: null });
      expect(openPullout).not.toHaveBeenCalled();
      fireEvent.click(drawerRow);
      expect(openPullout).toHaveBeenCalledOnce();
      expect(openPullout).toHaveBeenCalledWith(qualifiedRef("directory", directory.id));
      expect(run).toHaveBeenCalledOnce();
    } finally {
      cleanup();
      run.mockRestore();
      useDesk.setState(saved, true);
    }
  });

  it("renders the screen and no Chair window on a fresh desk", async () => {
    const { ChairHome } = await import("../../chair/ChairHome");
    render(<ChairHome />);
    expect(screen.getByTestId("desk-screen")).toBeTruthy();
    expect(screen.getByTestId("chair-desk").getAttribute("data-layout")).toBe("screen");
    for (const name of ["Needs you", "Brief", "The week", "Capture"]) {
      expect(screen.queryByRole("region", { name })).toBeNull();
    }
    expect(screen.queryByTestId("chair-reopen-needs")).toBeNull();
    expect(screen.queryByRole("button", { name: /^Needs you, SMART DRAWER/ })).toBeNull();
  });

  it("keeps the first-run path: no screen while arrival is required", async () => {
    const { ChairHome } = await import("../../chair/ChairHome");
    render(<ChairHome arrivalRequired />);
    expect(screen.getByTestId("first-run")).toBeTruthy();
    expect(screen.queryByTestId("desk-screen")).toBeNull();
  });
});
