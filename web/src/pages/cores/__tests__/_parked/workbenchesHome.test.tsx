import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkbenchesHomeCore } from "../WorkbenchesHomeCore";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), open: vi.fn(), reload: null as (() => void) | null }));
vi.mock("../../../desk/useDeskChangedRefresh", () => ({ useOnDeskChanged: (reload: () => void) => { mocks.reload = reload; } }));
vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => error instanceof Error ? error.message : "Failed",
}));
vi.mock("../../../desk/store", () => {
  const state = { items: { recipe: [] }, openWorkbenchWindow: mocks.open };
  return { useDesk: Object.assign((select: (s: typeof state) => unknown) => select(state), { getState: () => state }) };
});

const ALPHA = { id: "alpha", name: "Alpha", recipe_id: null, pending_count: 1, item_count: 2, schedule_enabled: false };
const BETA = { ...ALPHA, id: "beta", name: "Beta" };
const RUN = { id: "run-alpha", workbench_id: "alpha", started_at: "2026-10-14T13:00:00Z", items_completed: 1, items_attempted: 2, items_failed: 0, status: "completed", egress_boundary: "on_device" };

beforeEach(() => { vi.clearAllMocks(); });

describe("Workbenches read truth", () => {
  it("counts only actual done items and names running and terminal run states", async () => {
    const bench = { ...ALPHA, item_count: 5, pending_count: 1, items: [
      { status: "pending" }, { status: "claimed" }, { status: "done" }, { status: "failed" }, { status: "dismissed" },
      { status: "done", parked: true },
    ] };
    const runs = ["running", "completed", "failed", "cancelled"].map((status) => ({ ...RUN, id: status, status }));
    mocks.apiFetch.mockImplementation((path: string) => Promise.resolve(path === "/api/workbenches" ? { workbenches: [bench, BETA] } : { runs: path.includes("alpha") ? runs : [] }));
    render(<WorkbenchesHomeCore />);
    const alpha = await screen.findByRole("button", { name: /Alpha.*PENDING/ });
    expect(within(alpha).getByText("1 DONE")).toBeInTheDocument();
    expect(within(alpha).getByText("5 ITEMS")).toBeInTheDocument();
    expect(within(alpha).getByText("1 FAILED")).toBeInTheDocument();
    expect(within(alpha).getByText("1 IN PROGRESS")).toBeInTheDocument();
    expect(within(alpha).queryByText("4 DONE")).toBeNull();
    const beta = screen.getByRole("button", { name: /Beta.*PENDING/ });
    expect(within(beta).getByText("2 ITEMS")).toBeInTheDocument();
    expect(beta).not.toHaveTextContent("DONE");
    expect(await screen.findByText("Running", { exact: true })).toHaveClass("surface-state-chip");
    expect(screen.getByText("Completed", { exact: true })).toBeInTheDocument();
    expect(screen.getByText("Failed", { exact: true })).toBeInTheDocument();
    expect(screen.getByText("Cancelled", { exact: true })).toBeInTheDocument();
    expect(screen.queryByText("FAIL", { exact: true })).toBeNull();
  });

  it("keeps all-failed work visible and marked for attention without inventing DONE", async () => {
    const bench = { ...ALPHA, item_count: 3, pending_count: 0, items: [{ status: "failed" }, { status: "failed" }, { status: "failed" }] };
    mocks.apiFetch.mockImplementation((path: string) => Promise.resolve(path === "/api/workbenches" ? { workbenches: [bench] } : { runs: [] }));
    render(<WorkbenchesHomeCore />);
    const alpha = await screen.findByRole("button", { name: /Alpha.*3 ITEMS/ });
    expect(alpha).toHaveAttribute("data-needs", "true");
    expect(within(alpha).getByText("3 FAILED")).toBeInTheDocument();
    expect(alpha).not.toHaveTextContent("DONE");
    expect(alpha).not.toHaveTextContent("PENDING");
  });
  it("updates the still-open list after a Desk write and keeps the last rows on a failed reread", async () => {
    let workbenches: typeof ALPHA[] = [];
    let fail = false;
    mocks.apiFetch.mockImplementation((path: string) => path === "/api/workbenches"
      ? fail ? Promise.reject(new Error("Hub unavailable")) : Promise.resolve({ workbenches })
      : Promise.resolve({ runs: [] }));
    render(<WorkbenchesHomeCore />);
    await screen.findByText("An automation does one job for you, again and again.");
    workbenches = [ALPHA];
    act(() => mocks.reload?.());
    await screen.findByRole("button", { name: /Alpha.*PENDING/ });
    expect(screen.queryByText("An automation does one job for you, again and again.")).toBeNull();
    fail = true;
    act(() => mocks.reload?.());
    expect(await screen.findByRole("alert")).toHaveTextContent("Automations not loaded · Hub unavailable");
    expect(screen.getByRole("button", { name: /Alpha.*PENDING/ })).toBeVisible();
  });

  it("shows a failed list read with Retry, then the actual empty collection", async () => {
    mocks.apiFetch.mockRejectedValueOnce(new Error("Hub unavailable")).mockResolvedValue({ workbenches: [] });
    render(<WorkbenchesHomeCore />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Automations not loaded · Hub unavailable");
    expect(screen.queryByText("An automation does one job for you, again and again.")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("An automation does one job for you, again and again.")).toBeVisible();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("names partial run failures and keeps known workbenches and runs across Retry failures", async () => {
    let attempt = 0;
    mocks.apiFetch.mockImplementation((path: string) => {
      if (path === "/api/workbenches") {
        attempt += 1;
        return attempt === 2 ? Promise.reject(new Error("List unavailable")) : Promise.resolve({ workbenches: [ALPHA, BETA] });
      }
      if (path === "/api/workbenches/alpha/runs") return attempt === 3
        ? Promise.reject(new Error("Alpha runs unavailable")) : Promise.resolve({ runs: [RUN] });
      if (path === "/api/workbenches/beta/runs") return attempt === 1
        ? Promise.reject(new Error("Beta runs unavailable")) : Promise.resolve({ runs: [] });
      throw new Error(path);
    });
    render(<WorkbenchesHomeCore />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Runs not loaded · Beta · Beta runs unavailable");
    const alpha = screen.getByRole("button", { name: /Alpha.*PENDING/ });
    expect(alpha).toHaveClass("btn--chrome");
    fireEvent.click(alpha);
    expect(mocks.open).toHaveBeenCalledWith("alpha");
    expect(screen.getByText(/Alpha · 1\/2 done/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Automations not loaded · List unavailable");
    expect(screen.getByRole("button", { name: /Alpha.*PENDING/ })).toBeVisible();
    expect(screen.getByRole("button", { name: /Beta.*PENDING/ })).toBeVisible();
    expect(screen.getByText(/Alpha · 1\/2 done/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Runs not loaded · Alpha · Alpha runs unavailable"));
    expect(screen.getByText(/Alpha · 1\/2 done/)).toBeVisible();
    expect(screen.queryByText("An automation does one job for you, again and again.")).toBeNull();
  });
});
