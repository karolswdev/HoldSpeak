/** HS-112-03 — the Prefs Desk module: the desk's first destructive
 * verb confirms in-world with the kit's arming grammar (press → RESET
 * DESK? → press again), states in labels what resets and what
 * survives, and receipts the hub's counts. No modal, no confirm(). */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../../desk/store";
import { DeskModule, PREF_MODULES } from "../settingsPrefs";

describe("DeskModule (HS-112-03)", () => {
  const resetDesk = vi.fn(async () => ({ tombstoned: 7, seeded: 8 }));

  beforeEach(() => {
    resetDesk.mockClear();
    useDesk.setState({ resetDesk });
  });

  it("is a registered pref module", () => {
    expect(PREF_MODULES.some((m) => m.id === "desk")).toBe(true);
  });

  it("states what resets and what survives, as labels", () => {
    render(<DeskModule />);
    expect(
      screen.getByText(/RESETS · NOTES · KNOWLEDGE · AGENTS · WORKFLOWS · DRAWERS · LAYOUT/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/KEEPS · MEETINGS · JOURNAL · SETTINGS · RUNS-ON TARGETS/),
    ).toBeInTheDocument();
  });

  it("arms before it fires: first press asks, second press resets", async () => {
    const user = userEvent.setup();
    render(<DeskModule />);
    await user.click(screen.getByRole("button", { name: "RESET TO SEED" }));
    expect(resetDesk).not.toHaveBeenCalled(); // armed, not fired
    await user.click(screen.getByRole("button", { name: "RESET DESK?" }));
    expect(resetDesk).toHaveBeenCalledTimes(1);
    expect(await screen.findByRole("status")).toHaveTextContent(
      "TOMBSTONED 7 · SEEDED 8",
    );
  });

  it("a refused reset says so in the danger tone", async () => {
    resetDesk.mockResolvedValueOnce(null as never);
    const user = userEvent.setup();
    render(<DeskModule />);
    await user.click(screen.getByRole("button", { name: "RESET TO SEED" }));
    await user.click(screen.getByRole("button", { name: "RESET DESK?" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("RESET REFUSED");
  });
});
