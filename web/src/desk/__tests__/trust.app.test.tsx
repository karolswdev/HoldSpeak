/* Trust (Privacy & Trust window), the face half (the test diet, 2026-10-11).
 *
 * The real TrustWindow and its store. Only `fetch` is a double, and it
 * answers with the live hub's own `/api/setup/status` answers, written by
 * tests/integration/test_desk_trust.py (which also proves they carry no
 * invented field): a saved folder on this device, then a synced folder too.
 */
import { render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TrustWindow, useTrustWindow } from "../components/TrustWindow";
import statusLocal from "./fixtures/trust-wire/status-local.json";
import statusSynced from "./fixtures/trust-wire/status-synced.json";

function answer(body: unknown) {
  vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/setup/status") {
      return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
    }
    return new Response(JSON.stringify({ error: "not routed" }), { status: 404, headers: { "content-type": "application/json" } });
  }));
}

function settingValue(window: HTMLElement, label: string): string {
  const row = within(window).getByText(label).closest(".surface-setting-row");
  return (row?.textContent ?? "").replace(label, "").trim();
}

function section(name: string): HTMLElement {
  const head = screen.getAllByText(name).find((el) => el.closest(".surface-section"));
  return head!.closest(".surface-section") as HTMLElement;
}

beforeEach(() => useTrustWindow.setState({ open: true }));
afterEach(() => {
  vi.unstubAllGlobals();
  useTrustWindow.setState({ open: false });
});

describe("Trust counts a saved destination and says where data goes", () => {
  it("a folder on this device: counted, THIS DEVICE, all data stays, no HOME path", async () => {
    // replaces: tests/e2e/test_honest_faces_glass.py::test_trust_counts_the_saved_destination
    answer(statusLocal);
    const { container } = render(<TrustWindow />);
    await waitFor(() => expect(screen.getAllByText("Team updates").length).toBeGreaterThan(0));
    const window = container.querySelector(".desk-trust-window") as HTMLElement;
    // Two saved destinations: the built-in HoldSpeak folder and Team updates.
    expect(settingValue(window, "Enabled destinations")).toBe("2");
    expect(window.textContent).toContain("All data stays on this device");
    expect(settingValue(window, "Current scope")).toBe("this device");
    expect(within(section("Team updates")).getByText("THIS DEVICE")).toBeTruthy();
    expect(within(section("HoldSpeak folder")).getByText("THIS DEVICE")).toBeTruthy();
    expect(window.textContent).not.toMatch(/\/Users\/|\/private\//);
  });

  it("a synced folder: the lede and the scope both say it leaves, and its lamp SENDS OUT", async () => {
    // replaces: tests/e2e/test_honest_faces_glass.py::test_trust_scope_names_a_saved_external_destination
    answer(statusSynced);
    const { container } = render(<TrustWindow />);
    await waitFor(() => expect(screen.getAllByText("Synced updates").length).toBeGreaterThan(0));
    const window = container.querySelector(".desk-trust-window") as HTMLElement;
    expect(window.textContent).toContain("External destinations configured");
    expect(window.textContent).not.toContain("All data stays on this device");
    expect(settingValue(window, "Current scope")).toContain("this device + external");
    const lamp = within(section("Synced updates")).getByText("SENDS OUT");
    expect(lamp.closest(".gadget-lamp")).toHaveAttribute("data-on", "true");
  });
});
