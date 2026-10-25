import { describe, expect, it } from "vitest";
import { readdirSync, readFileSync } from "node:fs";
import { resolve, basename } from "node:path";
import { allSpriteNames } from "../sprites";
import { SYSTEM } from "../systemSprites";

const SOURCE = resolve(__dirname, "../../../design/icons");
const PNG = resolve(__dirname, "../../../public/desk/sprites");
const names = (folder: string, extension: string) => readdirSync(folder)
  .filter((name) => name.endsWith(extension)).map((name) => basename(name, extension)).sort();

describe("shared illustrated icon source", () => {
  it("covers each registered world and system identity, plus every Settings icon", () => {
    expect(names(resolve(SOURCE, "world"), ".svg")).toEqual(allSpriteNames());
    expect(names(resolve(SOURCE, "system"), ".svg"))
      .toEqual(Object.values(SYSTEM).map((url) => basename(url, ".png")).sort());
    expect(names(resolve(SOURCE, "settings"), ".svg"))
      .toEqual(names(resolve(PNG, "settings"), ".png"));
  });

  it("keeps originals self-contained and free of embedded text or external images", () => {
    for (const family of ["world", "system", "settings"]) {
      for (const name of names(resolve(SOURCE, family), ".svg")) {
        const svg = readFileSync(resolve(SOURCE, family, `${name}.svg`), "utf8");
        expect(svg, `${family}/${name}`).toMatch(/viewBox="0 0 64 64"/);
        expect(svg, `${family}/${name}`).not.toMatch(/<(?:script|foreignObject|image|text)\b/i);
        expect(svg, `${family}/${name}`).not.toMatch(/(?:href\s*=|url\(\s*["']?)(?:["']?https?:|\/\/|file:)/i);
      }
    }
  });

  it("retains PNG size and alpha contracts for every exported base", () => {
    for (const family of ["world", "system", "settings"]) {
      for (const name of names(resolve(SOURCE, family), ".svg")) {
        // Icons D (2026-10-24): world and system also draw a 20 px glyph.
        const dirs = family === "world" ? ["", "32", "20"]
          : family === "system" ? ["system", "system/20"] : [family];
        for (const dir of dirs) {
          const file = readFileSync(resolve(PNG, dir, `${name}.png`));
          const size = dir.endsWith("20") ? 20
            : family === "world" ? (dir === "32" ? 32 : 64)
            : family === "settings" && name === "wallpaper" ? 64 : 32;
          expect([file.readUInt32BE(16), file.readUInt32BE(20)], `${dir}/${name}`)
            .toEqual([size, size]);
          expect(file[25], `${dir}/${name} must retain alpha`).toBe(6);
        }
      }
    }
  });
});

describe("Icons D construction (owner pick 2026-10-24)", () => {
  it("draws every source front-on and flat: no gradient, filter, tilt or skew", () => {
    for (const family of ["world", "system", "settings"]) {
      for (const name of names(resolve(SOURCE, family), ".svg")) {
        const svg = readFileSync(resolve(SOURCE, family, `${name}.svg`), "utf8");
        expect(svg, `${family}/${name}`).not.toMatch(/<(?:linearGradient|radialGradient|filter)\b/i);
        expect(svg, `${family}/${name}`).not.toMatch(/(?:rotate|skew|matrix)\(/i);
        // The optical levels ride on these root properties (gen-illustrated-icons.py LEVELS).
        expect(svg, `${family}/${name}`).toMatch(/--ow:1\.5px;--u:3\.25px;--nu:-3\.25px;--lw:1/);
      }
    }
  });
});
