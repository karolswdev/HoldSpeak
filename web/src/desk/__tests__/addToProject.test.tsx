// PHILO-15 16 (B37): a meeting joins a Project. `Add to Project ▸` is one
// library Button that opens the DeskMenu species with the desk's Projects; a
// pick writes the link the hub has (`POST /api/projects/{id}/meetings/{mid}`);
// the receipt is one token. It sits on the meeting record's footer, the
// Chair's MEETING READY card and the Needs you rows of a meeting in no Project.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../lib/api";
import { AddToProject, linkMeetingPath, meetingProjectsPath } from "../AddToProject";
import { useDesk } from "../store";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});

const refresh = vi.fn(async () => undefined);
const PROJECTS = [
  { id: "p-ledger", name: "Payments ledger cutover", description: "", keywords: [], team_members: [], is_archived: false, meeting_count: 0, updated_at: "" },
  { id: "p-old", name: "Old archive", description: "", keywords: [], team_members: [], is_archived: true, meeting_count: 0, updated_at: "" },
  { id: "p-hiring", name: "Hiring loop", description: "", keywords: [], team_members: [], is_archived: false, meeting_count: 0, updated_at: "" },
];

const calls: Array<{ url: string; method?: string }> = [];
let linked: string[] = [];
let failLink = false;

beforeEach(() => {
  calls.length = 0;
  linked = [];
  failLink = false;
  refresh.mockClear();
  apiFetch.mockReset();
  apiFetch.mockImplementation((url: string, init?: { method?: string }) => {
    calls.push({ url, method: init?.method });
    if (url === meetingProjectsPath("m-sync")) {
      return Promise.resolve({ projects: linked.map((project_id) => ({ project_id })) });
    }
    if (init?.method === "POST" && url.startsWith("/api/projects/")) {
      if (failLink) return Promise.reject(new ApiError(404, "not found", { error: "Project not found" }));
      return Promise.resolve({ success: true, operation_id: "op-1", receipt: { outcome: "succeeded" } });
    }
    return Promise.resolve({});
  });
  useDesk.setState({ projects: PROJECTS as never, refresh: refresh as never });
});

describe("PHILO-15 16 Add to Project ▸", () => {
  it("one Button opens the Project list (archived ones left out); a pick links the meeting", async () => {
    render(<AddToProject meetingId="m-sync" />);
    const button = screen.getByRole("button", { name: "Add to Project ▸" });
    expect(button).toHaveAttribute("aria-haspopup", "menu");
    fireEvent.click(button);
    const menu = await screen.findByRole("menu", { name: "Add to Project" });
    const rows = Array.from(menu.querySelectorAll("[role^=menuitem]")).map((el) => el.textContent?.trim());
    expect(rows.join("|")).toContain("Payments ledger cutover");
    expect(rows.join("|")).toContain("Hiring loop");
    expect(rows.join("|")).not.toContain("Old archive");
    fireEvent.click(within(menu).getByText("Payments ledger cutover"));
    expect(await screen.findByTestId("add-to-project-receipt")).toHaveTextContent("IN PAYMENTS LEDGER CUTOVER");
    expect(calls.filter((c) => c.method === "POST").map((c) => c.url)).toEqual([linkMeetingPath("p-ledger", "m-sync")]);
    expect(refresh).toHaveBeenCalled();
  });

  it("a Project the meeting is in carries a check, and a second pick writes nothing", async () => {
    linked = ["p-ledger"];
    render(<AddToProject meetingId="m-sync" />);
    fireEvent.click(screen.getByRole("button", { name: "Add to Project ▸" }));
    const menu = await screen.findByRole("menu", { name: "Add to Project" });
    await waitFor(() => expect(within(menu).getByRole("menuitemcheckbox", { name: /Payments ledger cutover/ })).toHaveAttribute("aria-checked", "true"));
    fireEvent.click(within(menu).getByText("Payments ledger cutover"));
    expect(await screen.findByTestId("add-to-project-receipt")).toHaveTextContent("IN PAYMENTS LEDGER CUTOVER");
    expect(calls.filter((c) => c.method === "POST")).toEqual([]);
  });

  it("a refused link is named on its receipt", async () => {
    failLink = true;
    render(<AddToProject meetingId="m-sync" />);
    fireEvent.click(screen.getByRole("button", { name: "Add to Project ▸" }));
    fireEvent.click(within(await screen.findByRole("menu", { name: "Add to Project" })).getByText("Hiring loop"));
    const receipt = await screen.findByTestId("add-to-project-receipt");
    expect(receipt.textContent).toMatch(/^NOT ADDED/);
    expect(receipt).toHaveAttribute("data-tone", "danger");
  });

  it("no Project on the desk: no verb that does nothing", () => {
    useDesk.setState({ projects: [] as never });
    render(<AddToProject meetingId="m-sync" />);
    expect(screen.queryByRole("button", { name: "Add to Project ▸" })).toBeNull();
  });
});
