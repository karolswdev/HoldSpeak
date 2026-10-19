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

describe("P4: the Projects window", () => {
  it("lists each project with its state and reason, its next date and its newest update", async () => {
    useDesk.setState({ projects: projects.map((p) => ({ id: p.id, name: p.name })) } as never);
    render(<ProjectsCore />);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });

    const [payments, vendor] = rows();
    // At risk first: the Room's own word and reason (a milestone is late).
    expect(within(payments).getByTestId("projects-open").textContent).toBe("Payments migration");
    expect(within(payments).getByTestId("projects-state").textContent).toBe("At risk");
    expect(within(payments).getByTestId("projects-reason").textContent).toBe("1 MILESTONE LATE");
    expect(within(payments).getByTestId("projects-next").textContent).toMatch(/^Target \w{3} \d{1,2} \w{3}$/);
    expect(within(payments).getByTestId("projects-new-update").textContent).toBe("New update");
    expect(within(payments).getByTestId("projects-update").textContent).toMatch(/^Update drafted /);
    // An empty project is New, never On track; no date or update is invented.
    expect(within(vendor).getByTestId("projects-state").textContent).toBe("New");
    expect(within(vendor).queryByTestId("projects-reason")).toBeNull();
    expect(within(vendor).queryByTestId("projects-next")).toBeNull();
    expect(within(vendor).queryByTestId("projects-update")).toBeNull();
  });

  it("one press on a name opens that project", async () => {
    useDesk.setState({ projects: projects.map((p) => ({ id: p.id, name: p.name })) } as never);
    render(<ProjectsCore />);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    fireEvent.click(screen.getByRole("button", { name: "Open Payments migration" }));
    expect(opened.rooms).toEqual([WIRE.payments]);
  });

  it("a Room that cannot be read says so; it never claims a state", async () => {
    useDesk.setState({ projects: projects.map((p) => ({ id: p.id, name: p.name })) } as never);
    apiFetch.mockImplementation((path: string) => path.endsWith(`${WIRE.vendor}/room`)
      ? Promise.reject(new TypeError("Failed to fetch"))
      : Promise.resolve(structuredClone(gets[path])));
    render(<ProjectsCore />);
    await act(async () => { await Promise.resolve(); await Promise.resolve(); });
    const vendor = rows().find((r) => r.textContent?.includes("Vendor review"))!;
    expect(within(vendor).getByTestId("projects-not-read").textContent).toBe("Not read");
    expect(within(vendor).queryByTestId("projects-state")).toBeNull();
  });

  it("with no project, the window offers New Project", () => {
    render(<ProjectsCore />);
    expect(screen.queryByTestId("projects-row")).toBeNull();
    fireEvent.click(screen.getByTestId("projects-new"));
    expect(opened.surfaces).toEqual(["project-setup"]);
  });
});
