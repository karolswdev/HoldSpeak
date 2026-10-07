// PHILO-14 A1 — ChairHome renders the screen of objects after arrival; the
// first-run path (arrivalRequired) is untouched; a fresh desk opens with the
// four Chair windows closed (they open on demand).
import { render, screen } from "@testing-library/react";
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
  it("renders the screen and no Chair window on a fresh desk", async () => {
    const { ChairHome } = await import("../../chair/ChairHome");
    render(<ChairHome />);
    expect(screen.getByTestId("desk-screen")).toBeTruthy();
    expect(screen.getByTestId("chair-desk").getAttribute("data-layout")).toBe("screen");
    for (const name of ["Needs you", "Brief", "The week", "Capture"]) {
      expect(screen.queryByRole("region", { name })).toBeNull();
    }
    expect(screen.queryByTestId("chair-reopen-needs")).toBeNull();
    expect(screen.getByRole("button", { name: /^Needs you, SMART DRAWER/ })).toBeTruthy();
  });

  it("keeps the first-run path: no screen while arrival is required", async () => {
    const { ChairHome } = await import("../../chair/ChairHome");
    render(<ChairHome arrivalRequired />);
    expect(screen.getByTestId("first-run")).toBeTruthy();
    expect(screen.queryByTestId("desk-screen")).toBeNull();
  });
});
