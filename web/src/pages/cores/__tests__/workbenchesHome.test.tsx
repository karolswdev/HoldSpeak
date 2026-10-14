import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkbenchesHomeCore } from "../WorkbenchesHomeCore";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), open: vi.fn() }));
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
  it("shows a failed list read with Retry, then the actual empty collection", async () => {
    mocks.apiFetch.mockRejectedValueOnce(new Error("Hub unavailable")).mockResolvedValue({ workbenches: [] });
    render(<WorkbenchesHomeCore />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Workbenches not loaded · Hub unavailable");
    expect(screen.queryByText("No workbenches yet")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("No workbenches yet")).toBeVisible();
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
    expect(await screen.findByRole("alert")).toHaveTextContent("Workbenches not loaded · List unavailable");
    expect(screen.getByRole("button", { name: /Alpha.*PENDING/ })).toBeVisible();
    expect(screen.getByRole("button", { name: /Beta.*PENDING/ })).toBeVisible();
    expect(screen.getByText(/Alpha · 1\/2 done/)).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Runs not loaded · Alpha · Alpha runs unavailable"));
    expect(screen.getByText(/Alpha · 1\/2 done/)).toBeVisible();
    expect(screen.queryByText("No workbenches yet")).toBeNull();
  });
});
