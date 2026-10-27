// HS-111-09 — the system sheet has NO orphans, in either direction:
// every registered sprite exists on disk, and every banked system png
// is registered (HS-110-02 half-landed once; this lock keeps the canon
// table and the desk from disagreeing again).
import { describe, expect, it } from "vitest";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { basename, resolve } from "node:path";
import { DOCK_SPRITES, DOCK_SPRITES_48, SYSTEM, SYSTEM_48, dockSprite48 } from "./systemSprites";
import { DOCK_APPLICATIONS } from "./applications";

const DIR = resolve(__dirname, "../../public/desk/sprites/system");

describe("system sprite sheet", () => {
  const registered = Object.values(SYSTEM).map((url) => basename(url));

  it("every registered system sprite exists on disk", () => {
    for (const file of registered)
      expect(existsSync(resolve(DIR, file)), `missing ${file}`).toBe(true);
  });

  it("every banked system png is registered (no orphans)", () => {
    const banked = readdirSync(DIR).filter((f) => f.endsWith(".png"));
    expect(banked.sort()).toEqual([...registered].sort());
  });
});

// The floating dock (2026-10-26): the 48 px dock set has no orphans either,
// and every Dock item that has a 32 px sprite has its 48 px drawing.
describe("the 48 px dock set", () => {
  const DIR48 = resolve(DIR, "48");
  const registered = Object.values(SYSTEM_48).map((url) => basename(url));

  it("every registered 48 px sprite exists on disk, and every banked one is registered", () => {
    for (const file of registered)
      expect(existsSync(resolve(DIR48, file)), `missing 48/${file}`).toBe(true);
    const banked = readdirSync(DIR48).filter((f) => f.endsWith(".png"));
    expect(banked.sort()).toEqual([...registered].sort());
  });

  it("draws each Dock item and the Record orb at 48 from the same source name", () => {
    for (const [id, url] of Object.entries(DOCK_SPRITES))
      expect(basename(DOCK_SPRITES_48[id] ?? ""), id).toBe(basename(url));
    // The phone's Capture door (no 32 px Dock sprite) wears the Record orb.
    expect(DOCK_SPRITES_48["chair:capture"]).toBe(SYSTEM_48.recordOrb);
    expect(basename(SYSTEM_48.recordOrb)).toBe(basename(SYSTEM.recordOrb));
  });

  it("maps a 32 or 20 px system URL to its 48 px drawing, and leaves others alone", () => {
    expect(dockSprite48(SYSTEM.dockPeople)).toBe(SYSTEM_48.dockPeople);
    expect(dockSprite48(SYSTEM.dockPeople.replace("/system/", "/system/20/"))).toBe(SYSTEM_48.dockPeople);
    expect(dockSprite48(SYSTEM.menuBell)).toBe(SYSTEM.menuBell);
    expect(dockSprite48("/thread.png")).toBe("/thread.png");
  });
});

// PHILO-15 lane 12 (B19): every Dock item wears a sprite, never a text
// glyph. The applications come from DOCK_APPLICATIONS (+ People, which the
// Dock adds), the launchers from every announceLauncher call in the source.
describe("every Dock item has a sprite file", () => {
  function launcherIds(): string[] {
    const root = resolve(__dirname, "..");
    const ids = new Set<string>();
    const walk = (dir: string) => {
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const path = resolve(dir, entry.name);
        if (entry.isDirectory()) {
          if (entry.name !== "__tests__" && entry.name !== "node_modules") walk(path);
        } else if (/\.tsx?$/.test(entry.name) && !/\.test\.tsx?$/.test(entry.name)) {
          const text = readFileSync(path, "utf8");
          for (const m of text.matchAll(/announceLauncher\(\{\s*id:\s*"([^"]+)"/g)) ids.add(m[1]);
        }
      }
    };
    walk(root);
    return [...ids].sort();
  }

  it("finds the launchers it fences", () => {
    expect(launcherIds()).toEqual(["attention", "delivery-board", "panes"]);
  });

  it("maps every application and launcher to a file on disk", () => {
    const items = [
      ...DOCK_APPLICATIONS.map((application) => application.windowId),
      "surface-people",
      ...launcherIds(),
    ];
    for (const id of items) {
      const url = DOCK_SPRITES[id];
      expect(url, `Dock item ${id} has no sprite`).toBeTruthy();
      expect(existsSync(resolve(DIR, basename(url))), `missing ${basename(url)} for ${id}`).toBe(true);
    }
    expect(existsSync(resolve(DIR, basename(SYSTEM.floorGrid)))).toBe(true);
  });
});
