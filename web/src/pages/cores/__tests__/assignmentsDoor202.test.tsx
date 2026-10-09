/* HS-202-02 job 5 — the assignments module has a door, and no shipped
 * placeholder is a stranger's home network.
 *
 * SURFACE-INVENTORY-2026-09-20.md §4: "The `assignments` settings module
 * has no door: `PREF_MODULES` declares nine, the ledger renders eight" and
 * "The owner's private LAN address is hardcoded as the shipped
 * Server-address placeholder (ConciergeCore.tsx:522)".
 */
import { describe, expect, it } from "vitest";
import prefsSource from "../settingsPrefs.tsx?raw";
// PHILO-16 (C): the address row lives in Runs on now; the parked Concierge
// keeps its own placeholder, and both are read.
import parkedConciergeSource from "../../../features/concierge/ConciergeCore.tsx?raw";
import runsOnSource from "../../../features/runson/RunsOnCore.tsx?raw";
const conciergeSource = `${parkedConciergeSource}\n${runsOnSource}`;
import { PREF_MODULES } from "../settingsPrefs";

describe("every declared settings module has a ledger row (HS-202-02)", () => {
  const rendered = new Set(
    Array.from(prefsSource.matchAll(/onToggle=\{\(\) => onOpen\("([a-z]+)"\)\}/g)).map(
      (m) => m[1],
    ),
  );

  // PHILO-16 (C): Assignments merged into the one Runs on row (id
  // `models`); the `assignments` id is an alias that opens the same window.
  it("renders the one Runs on row", () => {
    expect(rendered.has("models")).toBe(true);
    expect(prefsSource).toContain('primary="Runs on"');
  });

  it("leaves no declared module without a door", () => {
    const missing = PREF_MODULES.filter(
      (module) => !rendered.has(module.id),
    ).map((module) => module.id);
    expect(missing).toEqual([]);
  });
});

describe("the Server address placeholder is not the owner's network", () => {
  it("ships no private LAN address", () => {
    expect(conciergeSource).not.toMatch(/192\.168\.\d+\.\d+/);
    expect(conciergeSource).not.toMatch(/10\.\d+\.\d+\.\d+:/);
  });

  it("still shows the shape of an address", () => {
    expect(conciergeSource).toMatch(/placeholder="http:\/\//);
  });
});
