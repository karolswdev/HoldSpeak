import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({
  front: vi.fn(() => "surface-decisions"),
  api: vi.fn(),
}));
vi.mock("../../components/window/windowRegistry", async (original) => ({
  ...(await original<
    typeof import("../../components/window/windowRegistry")
  >()),
  useFrontWindowId: mocks.front,
}));
vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mocks.api,
}));
import { HelpMenu } from "../HelpMenu";
import {
  hydrateUiFeedback,
  resetUiFeedbackRuntimeForTests,
} from "../../feedback/runtime";
beforeEach(() => {
  mocks.front.mockReturnValue("surface-decisions");
  resetUiFeedbackRuntimeForTests();
  localStorage.setItem("hs:walk-voice", "off");
});
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
it.each([true, false])(
  "offers feedback only with the flag on (%s)",
  async (enabled) => {
    mocks.api.mockResolvedValue({ enabled });
    await act(async () => hydrateUiFeedback());
    render(<HelpMenu />);
    fireEvent.click(screen.getByRole("button", { name: "Help" }));
    expect(
      screen.getByRole("menuitem", { name: /Show me Decisions/ }),
    ).toBeVisible();
    expect(
      Boolean(screen.queryByRole("menuitem", { name: "Give feedback" })),
    ).toBe(enabled);
    fireEvent.click(
      screen.getByRole("menuitemcheckbox", { name: "Speak the guide" }),
    );
    await waitFor(() =>
      expect(localStorage.getItem("hs:walk-voice")).toBe("on"),
    );
  },
);
it("offers no dead guide for an app without a walk", () => {
  mocks.front.mockReturnValue("surface-components");
  render(<HelpMenu compact />);
  fireEvent.click(screen.getByRole("button", { name: "Help" }));
  expect(screen.queryByRole("menuitem", { name: /Show me/ })).toBeNull();
});
