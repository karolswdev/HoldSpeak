import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DoorCore, AddSourcesWell } from "../DoorCore";
import { useDesk } from "../../../../desk/store";
import { ApiError } from "../../../../lib/api";
import D174 from "./room-door-wires/door174.json";
import D169 from "./room-door-wires/door169.json";
const io = vi.hoisted(() => ({ api: vi.fn(), open: vi.fn() }));
vi.mock("../../../../lib/api", async original => ({ ...await original<typeof import("../../../../lib/api")>(), apiFetch: (...args: unknown[]) => io.api(...args) }));
vi.mock("../../../../desk/shell", async original => ({ ...await original<typeof import("../../../../desk/shell")>(), openSurface: (...args: unknown[]) => io.open(...args) }));
let connected = true, fail = false;
const close = vi.fn();
function press(name: string) { fireEvent.click(screen.getAllByRole("button", { name }).at(-1)!); }
beforeEach(() => {
  connected = true; fail = false; io.api.mockReset(); io.open.mockReset(); close.mockReset(); useDesk.setState({ closeSurfaceWindow: close });
  io.api.mockImplementation(async (url: string, init?: { method?: string; json?: Record<string, unknown> }) => {
    if (url === "/api/connections") return connected ? D169.gets[url] : D174.not_connected[url];
    if (url.startsWith("/api/providers/github/discover")) return D169.gets["/api/providers/github/discover"];
    if (url.includes("/api/providers/jira/discover")) return Object.entries(D169.gets).find(([path]) => path.includes("/jira/discover"))?.[1];
    if (url === "/api/projects/door/count") return init?.json?.provider === "github" ? D169.counts.github.answer : D169.counts.jira.answer;
    if (url === "/api/projects/door") { if (fail) throw new ApiError(503, "Injected failure", {}); return D169.create.answer; }
    if (url.includes("/repository")) return D169.register.answer;
    return {};
  });
});
describe("Door fields and source selection", () => {
  it("keeps Name and Links visible while connections load", async () => {
    let resolve!: (value: unknown) => void; io.api.mockImplementation(() => new Promise(answer => { resolve = answer; }));
    render(<DoorCore />); const name = screen.getByRole("textbox", { name: "Project name" }), links = screen.getByRole("textbox", { name: "Source links" });
    fireEvent.change(name, { target: { value: "Ledger cutover" } }); resolve(D169.gets["/api/connections"]);
    await screen.findByRole("row", { name: /GitHub/ }); expect(screen.getByRole("textbox", { name: "Project name" })).toBe(name); expect(screen.getByRole("textbox", { name: "Source links" })).toBe(links);
  });
  it("cancels without creating a project", async () => {
    render(<DoorCore />); await screen.findByRole("grid", { name: "New project" }); press("Cancel");
    expect(close).toHaveBeenCalledWith("surface-project-setup"); expect(io.api.mock.calls.some(([url]) => url === "/api/projects/door")).toBe(false);
  });
  it("creates a blank project, opens its Room and closes the Door", async () => {
    render(<DoorCore />); fireEvent.change(screen.getByRole("textbox", { name: "Project name" }), { target: { value: "Ledger cutover" } }); press("Create project");
    await waitFor(() => expect(io.open).toHaveBeenCalledWith("open-project-memory", `project:${D169.create.answer.projectId}`));
    expect(close).toHaveBeenCalledWith("surface-project-setup");
    expect(io.api.mock.calls.find(([url]) => url === "/api/projects/door")?.[1].json.sources).toEqual([]);
  });
  it("keeps the name after a failed create and retries the current name", async () => {
    fail = true; render(<DoorCore />); const name = screen.getByRole("textbox", { name: "Project name" });
    fireEvent.change(name, { target: { value: "First name" } }); press("Create project"); await screen.findByText(/Injected failure/);
    expect(name).toHaveValue("First name"); fireEvent.change(name, { target: { value: "Revised name" } }); fail = false; press("Create project");
    await waitFor(() => expect(io.api.mock.calls.filter(([url]) => url === "/api/projects/door").at(-1)?.[1].json.outcome).toBe("Revised name"));
  });
  it("selects a repository and keeps its watch choices in the inspector", async () => {
    render(<DoorCore />); fireEvent.click(await screen.findByRole("row", { name: /GitHub/ }));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Source" })).toHaveTextContent("HoldSpeak"));
    fireEvent.change(screen.getByRole("combobox", { name: "Source" }), { target: { value: "karolswdev/HoldSpeak" } });
    expect(screen.getByRole("checkbox", { name: "Open PRs" })).toBeChecked(); expect(screen.getByRole("checkbox", { name: "CI" })).toBeChecked();
    expect(screen.getByRole("textbox", { name: "Base branch" })).toBeInTheDocument(); expect(screen.getByRole("textbox", { name: "Labels" })).toBeInTheDocument();
    expect(document.querySelector(".object-list-row button")).toBeNull();
  });
  it("names a source that needs sign-in without claiming it is signed in", async () => {
    connected = false; render(<DoorCore />); await screen.findByRole("row", { name: /GitHub/ });
    fireEvent.click(await screen.findByRole("row", { name: /Confluence/ })); expect(screen.getByRole("button", { name: "Connect" })).toBeEnabled(); expect(screen.queryByText(/Signed in as/)).toBeNull();
  });
  it("Add sources cancels inside the existing Room without creating a project", async () => {
    const cancel = vi.fn(); render(<AddSourcesWell projectId="project" onAdded={() => {}} onCancel={cancel} />); await screen.findByRole("grid", { name: "Add sources" }); press("Cancel");
    expect(cancel).toHaveBeenCalledOnce(); expect(io.api.mock.calls.some(([url]) => url === "/api/projects/door")).toBe(false);
  });
});
