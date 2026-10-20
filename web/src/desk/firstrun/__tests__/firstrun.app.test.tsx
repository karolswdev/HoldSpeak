import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import FOUND from "../../__tests__/fixtures/setup-st3-st5/found.json";

const mocks = vi.hoisted(() => ({ apiFetch: vi.fn(), openPullout: vi.fn() }));

vi.mock("../../../lib/api", () => ({
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));
vi.mock("../../store", () => ({
  useDesk: Object.assign(() => undefined, { getState: () => ({ openPullout: mocks.openPullout }) }),
}));

import { FirstRun } from "../FirstRun";

beforeEach(() => {
  mocks.openPullout.mockReset();
  mocks.apiFetch.mockReset().mockImplementation(async (path: string) => {
    if (path === "/api/setup/found") return FOUND;
    if (path === "/api/setup/lan") return { rows: [] };
    if (path === "/api/settings") return { owner: { name: "Karol", aliases: [] }, _revision: "1" };
    return {};
  });
});

describe("current producer-backed first-run face", () => {
  it("uses Setup for first launch and leaves the owner an egress with optional rows absent", async () => {
    render(<FirstRun />);

    const face = await screen.findByTestId("setup-face");
    expect(face).toHaveTextContent("Ready, Karol.");
    expect(face).toHaveTextContent("Does not work");
    expect(screen.getByRole("button", { name: "Say one sentence" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Open my desk" }));
    await waitFor(() => expect(mocks.openPullout).toHaveBeenCalledWith("intelligence:desk"));
    expect(screen.queryByRole("button", { name: "Continue later" })).toBeNull();
  });

  it("shows a truthful retry state when the producer read fails", async () => {
    let failed = true;
    mocks.apiFetch.mockImplementation(async (path: string) => {
      if (path === "/api/setup/found") {
        if (failed) {
          failed = false;
          throw new Error("Setup inventory is unavailable");
        }
        return FOUND;
      }
      if (path === "/api/setup/lan") return { rows: [] };
      if (path === "/api/settings") return { owner: { name: "Karol", aliases: [] }, _revision: "1" };
      return {};
    });

    render(<FirstRun />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Setup inventory is unavailable");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(screen.getByTestId("setup-face")).toBeTruthy());
  });
});
