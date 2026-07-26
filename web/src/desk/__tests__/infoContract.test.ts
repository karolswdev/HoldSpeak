/** HS-105-04 — the Info-contract guard: one derived surface, honest
 * measures, properties only where a REAL update path exists. */
import { describe, expect, it } from "vitest";
import { INFO, kindInfo, filedZones } from "../infoContract";
import { EMPTY_ITEMS, type Items } from "../api";
import type { WorldObject } from "../world";

const obj = (kind: string, ref: Record<string, unknown> = {}): WorldObject =>
  ({ kind, id: "x1", title: "X", ref } as unknown as WorldObject);

describe("the Info contract (HS-105-04)", () => {
  it("derives for every kind — unknown kinds get universal-only", () => {
    const fallback = kindInfo("mystery");
    expect(fallback.footprint(obj("mystery"), EMPTY_ITEMS)).toBeNull();
    expect(fallback.properties).toEqual([]);
  });

  it("footprints are honest: absent data is null, never zero", () => {
    expect(kindInfo("note").footprint(obj("note"), EMPTY_ITEMS)).toBeNull();
    expect(
      kindInfo("note").footprint(
        obj("note", { bodyMarkdown: "hello" }),
        EMPTY_ITEMS,
      ),
    ).toBe("5 characters");
    expect(
      kindInfo("kb").footprint(obj("kb", { memberIds: ["a"] }), EMPTY_ITEMS),
    ).toBe("1 member");
    expect(kindInfo("kb").footprint(obj("kb"), EMPTY_ITEMS)).toBeNull();
  });

  it("declares properties only where a real update path backs them", () => {
    // Today's whole honest vocabulary: the recipe's runs_on (the recipe
    // PUT's profile_id). Growing this list requires a real field first.
    const declared = Object.entries(INFO).flatMap(([kind, info]) =>
      info.properties.map((p) => `${kind}.${p.key}`),
    );
    expect(declared).toEqual(["recipe.runs_on"]);
  });

  it("filedZones matches by bare id and qualified ref", () => {
    const items: Items = {
      ...EMPTY_ITEMS,
      directory: [
        { kind: "directory", id: "d1", name: "Z", memberIds: ["note:x1"] },
        { kind: "directory", id: "d2", name: "Y", memberIds: ["other"] },
      ],
    };
    expect(filedZones(obj("note"), items).map((d) => d.id)).toEqual(["d1"]);
  });
});
