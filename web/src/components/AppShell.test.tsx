import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AppShell, PRIMARY_NAV } from "./AppShell";

vi.mock("../lib/api", () => ({
  apiFetch: vi.fn().mockResolvedValue({}),
  readableError: () => "Request failed",
}));

vi.mock("../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    subscribe: () => () => undefined,
  }),
  useRuntimeFrame: () => null,
}));

describe("Phase 93 primary navigation", () => {
  it("renders exactly five global destinations", () => {
    render(
      <MemoryRouter initialEntries={["/workbench"]}>
        <AppShell>
          <p>Focused workspace</p>
        </AppShell>
      </MemoryRouter>,
    );

    const navigation = screen.getByRole("navigation", {
      name: "Primary navigation",
    });
    const links = within(navigation).getAllByRole("link");
    expect(links.map((link) => link.textContent)).toEqual([
      "Desk",
      "Dictation",
      "Meetings",
      "Studio",
      "Settings",
    ]);
    expect(links).toHaveLength(5);
    expect(PRIMARY_NAV).toHaveLength(5);
    for (const removed of ["Activity", "Commands", "Cadence", "Workbench"]) {
      expect(
        within(navigation).queryByRole("link", { name: removed }),
      ).toBeNull();
    }
  });
});
