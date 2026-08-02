// HS-111-09 — the system sheet has NO orphans, in either direction:
// every registered sprite exists on disk, and every banked system png
// is registered (HS-110-02 half-landed once; this lock keeps the canon
// table and the desk from disagreeing again).
import { describe, expect, it } from "vitest";
import { existsSync, readdirSync } from "node:fs";
import { basename, resolve } from "node:path";
import { SYSTEM } from "./systemSprites";

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
