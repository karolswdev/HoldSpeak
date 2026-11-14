/** The Projects window (Betterment P4, projects RECIPE): one row per project,
 * where it needs attention, its next date, its newest update; selection precedes open.
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

describe("Projects selection list", () => {
  it("keeps New project first on an empty desk and has no pane heading or card", async () => {
    useDesk.setState({ projects: [] } as never);
    render(<ProjectsCore />); await settle();
    expect(screen.getByText("No projects yet")).toBeInTheDocument();
    const bar = screen.getByRole("toolbar", { name: "Projects" });
    expect(within(bar).getAllByRole("button")[0]).toHaveAccessibleName("New project");
    fireEvent.click(within(bar).getByRole("button", { name: "New project" }));
    expect(opened.surfaces).toEqual(["project-setup"]);
    expect(screen.getByTestId("projects-window").querySelector("h1, h2, h3, .projects-plate, .surface-spine")).toBeNull();
    expect(screen.queryByTestId("projects-status")).toBeNull();
  });

  it("shows the hub state and selects before opening the Room", async () => {
    expect(appWalk("open-projects")?.open.app).toBe("surface-projects");
    seed(); render(<ProjectsCore />); await settle();
    const [payments, vendor] = rows();
    expect(within(payments).getByTestId("projects-state")).toHaveTextContent("At risk");
    expect(vendor.querySelector('[data-col="state"]')).toBeEmptyDOMElement();
    expect(vendor).not.toHaveTextContent("New");
    expect(screen.queryByRole("region", { name: "Projects facts" })).toBeNull();
    expect(screen.getByTestId("projects-status")).toHaveTextContent("2 projects");
    expect(screen.getByRole("button", { name: "Open Room" })).toBeDisabled();
    fireEvent.click(payments);
    expect(opened.rooms).toEqual([]);
    expect(screen.getByTestId("projects-pane")).toHaveTextContent("Payments migration");
    expect(screen.getByTestId("projects-reason")).toHaveTextContent("1 milestone late");
    expect(screen.getByTestId("projects-next").textContent).toMatch(/^Target /);
    expect(screen.getByTestId("projects-update")).toHaveTextContent("Update drafted");
    expect(screen.getByTestId("projects-new-update")).toHaveTextContent("New update");
    expect(screen.getByTestId("projects-status")).toHaveTextContent("2 projects");
    expect(screen.getByTestId("projects-status")).toHaveTextContent("1 needs you");
    fireEvent.keyDown(payments, { key: "Enter" });
    expect(opened.rooms).toEqual([WIRE.payments]);
    fireEvent.click(vendor);
    expect(screen.queryByTestId("projects-next")).toBeNull();
    expect(screen.queryByTestId("projects-update")).toBeNull();
    fireEvent.doubleClick(vendor);
    expect(opened.rooms).toEqual([WIRE.payments, WIRE.vendor]);
    expect(vendor.querySelector("button")).toBeNull();
  });

  it("uses literal Find and clears hidden selection without opening a Room", async () => {
    seed(); render(<ProjectsCore />); await settle();
    fireEvent.click(rows()[0]);
    const find = screen.getByRole("textbox", { name: "Find a project" });
    fireEvent.change(find, { target: { value: "VENDOR" } });
    expect(rows()).toHaveLength(1);
    expect(rows()[0]).toHaveTextContent("Vendor review");
    expect(screen.getByRole("button", { name: "Open Room" })).toBeDisabled();
    fireEvent.change(find, { target: { value: "[no-match]" } });
    expect(screen.queryAllByTestId("projects-row")).toHaveLength(0);
    expect(screen.getByTestId("projects-pane")).toHaveTextContent("No projects match");
    fireEvent.change(find, { target: { value: "" } });
    expect(rows()).toHaveLength(2);
    expect(opened.rooms).toEqual([]);
  });

  it("shares Open Room and New project with the right-click menu and row keys", async () => {
    seed(); render(<ProjectsCore />); await settle();
    const vendor = rows()[1];
    fireEvent.contextMenu(vendor, { clientX: 10, clientY: 10 });
    const menu = screen.getByRole("menu", { name: "Projects actions" });
    fireEvent.click(within(menu).getByRole("menuitem", { name: /Open Room/ }));
    expect(opened.rooms).toEqual([WIRE.vendor]);
    fireEvent.keyDown(vendor, { key: "n" });
    expect(opened.surfaces).toEqual(["project-setup"]);
  });

  it("retains failed Room facts and retries in place", async () => {
    seed();
    const vendorPath = `/api/projects/${WIRE.vendor}/room`;
    let failed = true;
    apiFetch.mockImplementation((path: string) => path === vendorPath && failed
      ? Promise.reject(new Error("Offline")) : Promise.resolve(structuredClone(gets[path])));
    render(<ProjectsCore />); await settle();
    const vendor = rows().find((row) => row.textContent?.includes("Vendor review"))!;
    expect(within(vendor).getByTestId("projects-not-read")).toHaveTextContent("Not read");
    fireEvent.click(vendor);
    expect(screen.getByTestId("projects-pane")).toHaveTextContent("Not read");
    failed = false; fireEvent.keyDown(vendor, { key: "r" }); await settle();
    expect(vendor).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByTestId("projects-next")).toBeNull();
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("keeps health warnings while exposing unavailable dates and their recovery", async () => {
    seed();
    apiFetch.mockImplementation((path: string) => {
      const wire = structuredClone(gets[path]) as Record<string, unknown>;
      if (path.endsWith("/room")) wire.target = { state: "degraded", error_code: "project_store_unavailable" };
      return Promise.resolve(wire);
    });
    render(<ProjectsCore />); await settle();
    expect(within(rows()[0]).getByTestId("projects-state")).toHaveTextContent("At risk");
    const vendor = rows().find((row) => row.textContent?.includes("Vendor review"))!;
    fireEvent.click(vendor);
    expect(screen.getByTestId("projects-next")).toHaveTextContent("Not read");
    const state = within(screen.getByTestId("projects-pane")).getByText("State", { selector: ".gadget-row-label" });
    expect(state.closest(".gadget-row")).toHaveTextContent("On track");
    expect(screen.getByRole("button", { name: "Retry" })).toBeEnabled();
  });

  it("waits for one complete read before ranking, and ignores a late earlier batch", async () => {
    let finishPayments!: (value: unknown) => void;
    const slow = new Promise((resolve) => { finishPayments = resolve; });
    apiFetch.mockImplementation((path: string) => path === `/api/projects/${WIRE.payments}/room`
      ? slow : Promise.resolve(structuredClone(gets[path])));
    seed(); render(<ProjectsCore />); await settle();
    expect(screen.queryAllByTestId("projects-row")).toEqual([]);
    act(() => useDesk.setState({ projects: projects.filter((p) => p.id === WIRE.vendor) } as never)); await settle();
    expect(rows()).toHaveLength(1);
    await act(async () => { finishPayments(structuredClone(gets[`/api/projects/${WIRE.payments}/room`])); });
    expect(rows()).toHaveLength(1);
    expect(rows()[0]).toHaveTextContent("Vendor review");
  });
});

 it("omits a column when none of the visible projects has its value", async () => {
  seed(); render(<ProjectsCore />); await settle();
  fireEvent.change(screen.getByRole("textbox", {name:"Find a project"}), {target:{value:"Vendor"}});
  expect(screen.getAllByRole("columnheader").map(head => head.textContent)).toEqual(["Project"]);
  expect(screen.queryByRole("region", {name:"Projects facts"})).toBeNull();
  expect(screen.getByTestId("projects-status")).toHaveTextContent("1 project");
  fireEvent.click(rows()[0]);
  expect(screen.queryByText("No date set")).toBeNull();
  expect(screen.getByTestId("projects-pane")).toHaveTextContent("Vendor review");
 });

 it("keeps the read Room facts for a selected project, including an honest missing meeting", async () => {
  seed(); render(<ProjectsCore />); await settle();
  fireEvent.click(rows()[0]);
  const pane = screen.getByTestId("projects-pane");
  for (const label of ["State", "Sources", "Last update", "Open items", "Next meeting"])
    expect(within(pane).getByText(label, {selector:".gadget-row-label"})).toBeVisible();
  expect(within(pane).getByText("No sources")).toBeVisible();
  expect(within(pane).getByText("1 open item")).toBeVisible();
  expect(within(pane).getByText("Not supplied")).toBeVisible();
  expect(pane).toHaveTextContent("Update drafted");
  fireEvent.click(rows()[1]);
  expect(pane).toHaveTextContent("New");
  expect(pane).toHaveTextContent("No updates");
  expect(pane).toHaveTextContent("No open items");
  expect(apiFetch.mock.calls.filter(([path]) => path === `/api/projects/${WIRE.vendor}/room`)).toHaveLength(1);
 });

 it("does not use a total that includes closed or omitted items as the open-item count", async () => {
  seed();
  apiFetch.mockImplementation((path: string) => {
    const raw=structuredClone(gets[path]) as Record<string,unknown>;
    if(path===`/api/projects/${WIRE.payments}/room`) {
      const items=raw.items as {total:number;focus:{lifecycle:string}[]};
      items.focus[0].lifecycle="closed";
    }
    if(path===`/api/projects/${WIRE.vendor}/room`) (raw.items as {total:number}).total=50;
    return Promise.resolve(raw);
  });
  render(<ProjectsCore />);await settle();
  fireEvent.click(rows()[0]);
  expect(screen.getByTestId("projects-pane")).toHaveTextContent("No open items");
  fireEvent.click(rows()[1]);
  const label=within(screen.getByTestId("projects-pane")).getByText("Open items",{selector:".gadget-row-label"});
  expect(label.closest('.gadget-row')).toHaveTextContent("Not supplied");
 });

 it("keeps an unavailable source count distinct from zero and retries it", async () => {
  seed();let failed=true;
  apiFetch.mockImplementation((path: string) => {
    const raw=structuredClone(gets[path]) as Record<string,unknown>;
    if(path===`/api/projects/${WIRE.vendor}/room` && failed) raw.sources={state:"degraded",error_code:"project_store_unavailable"};
    return Promise.resolve(raw);
  });
  render(<ProjectsCore />);await settle();fireEvent.click(rows().find(row=>row.textContent?.includes("Vendor review"))!);
  const label=within(screen.getByTestId("projects-pane")).getByText("Sources",{selector:".gadget-row-label"});
  expect(label.closest('.gadget-row')).toHaveTextContent("Not read");
  failed=false;fireEvent.click(screen.getByRole("button",{name:"Retry"}));await settle();
  expect(label.closest('.gadget-row')).toHaveTextContent("No sources");
 });
