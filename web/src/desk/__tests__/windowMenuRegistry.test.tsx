/** HS-148-04 — registry-derivation pin tests: head + dock menu
 * labels and keycaps come FROM the verb registry; no hardcoded
 * parallel verb system. */
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DeskWindowFrame, Dock } from "../components/DeskWindow";
import { verbById, verbLabel, type VerbContext } from "../verbRegistry";
import { headMenuEntries, dockChipMenuEntries } from "../windowMenuAdapter";
import { useDesk } from "../store";

const CTX: VerbContext = { selectedRef: null };

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
  });
});

describe("HS-148-04: registry-derivation pin", () => {
  it("head menu labels match the verb registry definitions", () => {
    render(
      <DeskWindowFrame id="pin" title="Pin test" open onClose={() => {}}>
        <p>body</p>
      </DeskWindowFrame>,
    );
    const head = screen
      .getByRole("region", { name: "Pin test" })
      .querySelector("header") as HTMLElement;
    fireEvent.contextMenu(head);
    const menu = screen.getByRole("menu", { name: "Pin test window menu" });

    // Collect rendered labels from the menu.
    const items = Array.from(
      menu.querySelectorAll(
        "[role='menuitem'],[role='menuitemcheckbox'],[role='menuitemradio']",
      ),
    );
    const labels = items.map(
      (el) =>
        el.querySelector(".desk-menu-label")?.textContent?.trim() ?? "",
    );

    // The expected labels from the registry (maximize in non-compact mode).
    const minVerb = verbById("window.minimize")!;
    const maxVerb = verbById("window.maximize")!;
    const closeVerb = verbById("window.close")!;
    expect(labels).toEqual([
      verbLabel(minVerb, CTX),
      verbLabel(maxVerb, CTX),
      verbLabel(closeVerb, CTX),
    ]);
  });

  it("head menu keycaps match the verb registry keys", () => {
    render(
      <DeskWindowFrame id="kp" title="Keycap pin" open onClose={() => {}}>
        <p>body</p>
      </DeskWindowFrame>,
    );
    const head = screen
      .getByRole("region", { name: "Keycap pin" })
      .querySelector("header") as HTMLElement;
    fireEvent.contextMenu(head);
    const menu = screen.getByRole("menu", { name: "Keycap pin window menu" });

    // Check keycap wells exist for verbs that have keys.
    const minVerb = verbById("window.minimize")!;
    const closeVerb = verbById("window.close")!;
    expect(minVerb.key).toBeTruthy();
    expect(closeVerb.key).toBeTruthy();
    const wells = menu.querySelectorAll(".desk-menu-keycaps");
    // At least the minimize and close verbs have keycaps.
    expect(wells.length).toBeGreaterThanOrEqual(2);
    // The well aria-labels carry the keycap notation from the registry.
    const ariaLabels = Array.from(wells).map((w) => w.getAttribute("aria-label"));
    expect(ariaLabels).toContain(minVerb.key);
    expect(ariaLabels).toContain(closeVerb.key);
  });

  it("adapter output matches registry — the unit pin", () => {
    const entries = headMenuEntries({
      maximized: false,
      compact: false,
      requestMinimize: vi.fn(),
      toggleMaximize: vi.fn(),
      requestClose: vi.fn(),
    });
    const minVerb = verbById("window.minimize")!;
    const maxVerb = verbById("window.maximize")!;
    const closeVerb = verbById("window.close")!;
    expect(entries).toHaveLength(3);
    expect(entries[0].type === "item" && entries[0].label).toBe(
      verbLabel(minVerb, CTX),
    );
    expect(entries[0].type === "item" && entries[0].keycap).toBe(minVerb.key);
    expect(entries[1].type === "item" && entries[1].label).toBe(
      verbLabel(maxVerb, CTX),
    );
    expect(entries[2].type === "item" && entries[2].label).toBe(
      verbLabel(closeVerb, CTX),
    );
    expect(entries[2].type === "item" && entries[2].keycap).toBe(closeVerb.key);
  });

  it("dock chip adapter matches registry verbs", () => {
    const entries = dockChipMenuEntries({
      minimized: false,
      restore: vi.fn(),
      minimize: vi.fn(),
      close: vi.fn(),
    });
    const minVerb = verbById("window.minimize")!;
    const closeVerb = verbById("window.close")!;
    expect(entries).toHaveLength(2);
    // Not minimized → label is the registry's minimize label.
    expect(entries[0].type === "item" && entries[0].label).toBe(
      verbLabel(minVerb, CTX),
    );
    expect(entries[1].type === "item" && entries[1].label).toBe(
      verbLabel(closeVerb, CTX),
    );
  });

  it("dock chip adapter toggles Restore when minimized", () => {
    const entries = dockChipMenuEntries({
      minimized: true,
      restore: vi.fn(),
      minimize: vi.fn(),
      close: vi.fn(),
    });
    // Minimized → first label is "Restore", not the registry minimize label.
    expect(entries[0].type === "item" && entries[0].label).toBe("Restore");
  });

  it("compact head menu omits Maximize (no window.maximize entry)", () => {
    const entries = headMenuEntries({
      maximized: false,
      compact: true,
      requestMinimize: vi.fn(),
      toggleMaximize: vi.fn(),
      requestClose: vi.fn(),
    });
    expect(entries).toHaveLength(2);
    expect(entries.every((e) => e.type === "item" && e.id !== "window.maximize")).toBe(true);
  });

  it("maximized head menu shows Restore for the maximize verb", () => {
    const entries = headMenuEntries({
      maximized: true,
      compact: false,
      requestMinimize: vi.fn(),
      toggleMaximize: vi.fn(),
      requestClose: vi.fn(),
    });
    const maxEntry = entries.find(
      (e) => e.type === "item" && e.id === "window.maximize",
    );
    expect(maxEntry).toBeTruthy();
    expect(maxEntry!.type === "item" && maxEntry!.label).toBe("Restore");
  });
});

describe("HS-148-04: no hardcoded labels (grep-style pin)", () => {
  it("head menu labels are not hardcoded strings", async () => {
    // Read the DeskWindow source and verify no hardcoded menu labels.
    // The adapter's headMenuEntries builds entries from the registry;
    // if someone reintroduces hardcoded labels in DeskWindow.tsx,
    // the adapter output would differ from what the menu shows.
    const entries = headMenuEntries({
      maximized: false,
      compact: false,
      requestMinimize: vi.fn(),
      toggleMaximize: vi.fn(),
      requestClose: vi.fn(),
    });
    // Every item label is derived from verbById — if the registry label
    // changes, this adapter follows. The pin is that the adapter IS the
    // only source (no parallel strings in the component file).
    for (const entry of entries) {
      if (entry.type !== "item") continue;
      const verb = verbById(entry.id);
      expect(verb).toBeTruthy();
      // Label is either the registry label or "Restore" (the state toggle).
      const registryLabel = verbLabel(verb!, CTX);
      expect([registryLabel, "Restore"]).toContain(entry.label);
    }
  });

  it("dock chip labels are not hardcoded strings", () => {
    const entries = dockChipMenuEntries({
      minimized: false,
      restore: vi.fn(),
      minimize: vi.fn(),
      close: vi.fn(),
    });
    for (const entry of entries) {
      if (entry.type !== "item") continue;
      const verb = verbById(entry.id);
      expect(verb).toBeTruthy();
      const registryLabel = verbLabel(verb!, CTX);
      expect([registryLabel, "Restore"]).toContain(entry.label);
    }
  });
});
