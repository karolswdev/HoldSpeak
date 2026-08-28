// HS-139-05 / HS-143-13 — Settings uses owner-named destinations. The
// peer Assignments room has no /api/settings key because it consumes its own
// closed assignment projection. Module aliases from the retired roster resolve.
import { describe, expect, it } from "vitest";
import { MODULE_ALIASES, PREF_MODULES } from "../settingsPrefs";

describe("Settings face roster", () => {
  it("has the Models and Assignments peer destinations", () => {
    expect(PREF_MODULES).toHaveLength(8);
  });

  it("names every tile by what the owner does, not by subsystem", () => {
    const ids = PREF_MODULES.map((m) => m.id);
    expect(ids).toEqual([
      "voice",
      "sounds",
      "meetings",
      "rhythm",
      "models",
      "assignments",
      "integrations",
      "system",
    ]);
  });

  it("aliases every retired module to a successor", () => {
    const retired = [
      "appearance",
      "hotkey",
      "transcription",
      "voice-typing",
      "wake-word",
      "presence",
      "cadence",
      "devices",
      "delivery",
      "desk",
    ];
    const currentIds = new Set(PREF_MODULES.map((m) => m.id));
    for (const id of retired) {
      const resolved = MODULE_ALIASES[id];
      expect(resolved, `${id} has no alias`).toBeDefined();
      expect(currentIds.has(resolved!), `alias ${id} -> ${resolved} is not a current module`).toBe(true);
    }
  });

  it("no alias points at a module that no longer exists", () => {
    const currentIds = new Set(PREF_MODULES.map((m) => m.id));
    for (const [from, to] of Object.entries(MODULE_ALIASES)) {
      expect(currentIds.has(to), `alias ${from} -> ${to} invalid`).toBe(true);
    }
  });

  it("keeps the calendar source under the existing Meetings tile", () => {
    expect(PREF_MODULES.find((module) => module.id === "meetings")?.keys).toContain("calendar");
    expect(PREF_MODULES.filter((module) => module.id === "calendar")).toEqual([]);
  });

  it("every module has a glyph, sprite, and at least one key claim (except integrations)", () => {
    for (const m of PREF_MODULES) {
      expect(m.glyph, `${m.id} has no glyph`).toBeTruthy();
      expect(m.sprite, `${m.id} has no sprite`).toBeTruthy();
      if (m.id !== "integrations" && m.id !== "assignments" && m.id !== "system") {
        // system now claims device+mesh via keys
        expect(m.keys.length, `${m.id} has no keys`).toBeGreaterThan(0);
      }
    }
  });
});
