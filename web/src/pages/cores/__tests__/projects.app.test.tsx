/** The Projects window (Betterment P4, projects RECIPE): one row per project,
 * where it stands, its next date, its newest update; one press opens it.
 *
 * The hub's answers are recorded from the real routes on an isolated hub
 * (scripts/record_projects_go_wire.py); only `apiFetch` and the opener are
 * doubles. The clock is set to one hour after the recorded draft. */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import WIRE from "./fixtures/projects/recorded.json";

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
const opened = vi.hoisted(() => ({ rooms: [] as string[], surfaces: [] as string[] }));
vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>("../../../desk/shell");
  return {
    ...actual,
    openProjectRoom: (id: string) => { opened.rooms.push(id); },
    openSurfaceOr: (key: string) => { opened.surfaces.push(key); },
  };
});
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "offline", lastFrame: null, subscribe: () => () => undefined }),
  useOptionalRuntimeBus: () => ({ state: "offline", subscribe: () => () => undefined }),
}));

import { useDesk } from "../../../desk/store";
import { appWalk } from "../../../desk/walk/appWalks";
import { ProjectsCore } from "../ProjectsCore";

const gets = WIRE.gets as Record<string, unknown>;
const projects = (gets["/api/projects"] as { projects: { id: string; name: string }[] }).projects;
const draftAt = new Date(
  ((gets[`/api/projects/${WIRE.payments}/room`] as { updates: { recent: { created_at: string }[] } })
    .updates.recent[0].created_at),
);

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(draftAt.getTime() + 3_600_000));
  opened.rooms = [];
  opened.surfaces = [];
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string) =>
    path in gets ? Promise.resolve(structuredClone(gets[path])) : Promise.reject(new TypeError("Failed to fetch")));
});
afterEach(() => {
  vi.useRealTimers();
  useDesk.setState({ projects: [] } as never);
});


const rows = () => screen.getAllByTestId("projects-row");
const settle = async () => { await act(async () => { await Promise.resolve(); await Promise.resolve(); }); };
const seed = () => useDesk.setState({ projects: projects.map((p) => ({ id: p.id, name: p.name })) } as never);

describe("Projects as a native Room client", () => {
  it("keeps New project in the Rail head, including an empty desk", async () => {
    useDesk.setState({ projects: [] } as never);
    render(<ProjectsCore />); await settle();
    expect(screen.getByText("No projects yet")).toBeInTheDocument();
    fireEvent.click(within(screen.getByTestId("projects-rail")).getByRole("button", { name: "New project" }));
    expect(opened.surfaces).toEqual(["project-setup"]);
    expect(screen.queryByTestId("projects-status")).toBeNull();
  });

  it("ranks the real Room states, picks one into its Mast, and opens its Room", async () => {
    expect(appWalk("open-projects")?.open.app).toBe("surface-projects");
    seed(); render(<ProjectsCore />); await settle();
    const [payments, vendor] = rows();
    expect(within(payments).getByTestId("projects-state")).toHaveTextContent("At risk");
    expect(within(vendor).getByTestId("projects-state")).toHaveTextContent("New");
    expect(screen.getByTestId("projects-mast")).toHaveTextContent("Payments migration");
    expect(screen.getByTestId("projects-reason")).toHaveTextContent("1 milestone late");
    expect(screen.getByTestId("projects-next").textContent).toMatch(/^Target /);
    expect(screen.getByTestId("projects-update")).toHaveTextContent("Update drafted");
    expect(screen.getByTestId("projects-new-update")).toHaveTextContent("New update");
    expect(screen.getByTestId("projects-status")).toHaveTextContent("2 projects");
    fireEvent.click(within(vendor).getByRole("option"));
    expect(opened.rooms).toEqual([]);
    expect(screen.getByTestId("projects-mast")).toHaveTextContent("Vendor review");
    expect(screen.getByTestId("projects-next")).toHaveTextContent("No date set");
    expect(screen.getByTestId("projects-update")).toHaveTextContent("No update yet");
    fireEvent.click(screen.getByTestId("projects-open-selected"));
    expect(opened.rooms).toEqual([WIRE.vendor]);
  });

  it("retains a failed Room read as Not read and retries it in place", async () => {
    seed();
    const vendorPath = `/api/projects/${WIRE.vendor}/room`;
    let failed = true;
    apiFetch.mockImplementation((path: string) => path === vendorPath && failed
      ? Promise.reject(new Error("Offline")) : Promise.resolve(structuredClone(gets[path])));
    render(<ProjectsCore />); await settle();
    const vendor = rows().find((row) => row.textContent?.includes("Vendor review"))!;
    expect(within(vendor).getByTestId("projects-not-read")).toHaveTextContent("Not read");
    fireEvent.click(within(vendor).getByRole("option"));
    expect(screen.getByTestId("projects-ledger")).toHaveTextContent("Not read");
    failed = false; fireEvent.click(screen.getByRole("button", { name: "Retry" })); await settle();
    expect(screen.getByTestId("projects-ledger")).toHaveTextContent("New");
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("waits for one complete read before ranking, and ignores a late earlier batch", async () => {
    let finishPayments!: (value: unknown) => void;
    const slow = new Promise((resolve) => { finishPayments = resolve; });
    apiFetch.mockImplementation((path: string) => path === `/api/projects/${WIRE.payments}/room`
      ? slow : Promise.resolve(structuredClone(gets[path])));
    seed(); render(<ProjectsCore />); await settle();
    expect(screen.queryAllByTestId("projects-row")).toEqual([]);
    useDesk.setState({ projects: projects.filter((p) => p.id === WIRE.vendor) } as never); await settle();
    expect(rows()).toHaveLength(1);
    await act(async () => { finishPayments(structuredClone(gets[`/api/projects/${WIRE.payments}/room`])); });
    expect(rows()).toHaveLength(1);
    expect(rows()[0]).toHaveTextContent("Vendor review");
  });
});
