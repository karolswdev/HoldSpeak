/** HS-112-03 — the Prefs Desk module: the desk's first destructive
 * verb confirms in-world with the kit's arming grammar (press → Reset
 * the desk? → press again), states in labels what resets and what
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

  it("is absorbed into the system tile (HS-139-05)", () => {
    // "desk" was a standalone tile; HS-139-05 merged it into "system".
    expect(PREF_MODULES.some((m) => m.id === "system")).toBe(true);
    expect(PREF_MODULES.some((m) => m.id === "desk")).toBe(false);
  });

  it("states what resets and what survives, as labels", () => {
    render(<DeskModule />);
    expect(
      screen.getByText(/CLEARS THE DESK · PUTS BACK THE DEFAULT ITEMS/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/KEEPS · MEETINGS · JOURNAL · SETTINGS · RUNS ON/),
    ).toBeInTheDocument();
  });

  it("arms before it fires: first press asks, second press resets", async () => {
    const user = userEvent.setup();
    render(<DeskModule />);
    await user.click(screen.getByRole("button", { name: "Reset desk to defaults" }));
    expect(resetDesk).not.toHaveBeenCalled(); // armed, not fired
    await user.click(screen.getByRole("button", { name: "Reset the desk?" }));
    expect(resetDesk).toHaveBeenCalledTimes(1);
    expect(await screen.findByRole("status")).toHaveTextContent(
      "CLEARED 7 · ADDED 8",
    );
  });

  it("a refused reset says so in the danger tone", async () => {
    resetDesk.mockResolvedValueOnce(null as never);
    const user = userEvent.setup();
    render(<DeskModule />);
    await user.click(screen.getByRole("button", { name: "Reset desk to defaults" }));
    await user.click(screen.getByRole("button", { name: "Reset the desk?" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("RESET REFUSED");
  });
});
