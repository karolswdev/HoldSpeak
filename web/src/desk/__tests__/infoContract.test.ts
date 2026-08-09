/** HS-105-04 — the Info-contract guard: one derived surface, honest
 * measures, properties only where a REAL update path exists. */
import { describe, expect, it, vi } from "vitest";
import { INFO, kindInfo, filedZones } from "../infoContract";
import { EMPTY_ITEMS, type Items } from "../api";
import type { Directory } from "../../lib/primitives";
import type { WorldObject } from "../world";
import { useDesk } from "../store";

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

  it("recipe placement uses the HS-130-01 label + one empty-value meaning", () => {
    const runsOn = INFO.recipe.properties.find((p) => p.key === "runs_on");
    expect(runsOn).toBeDefined();
    // One scoped label vocabulary — the Agent-default scope reads
    // "Default runs on" (matching RecipeEditor's field label).
    expect(runsOn!.label).toBe("Default runs on");
    // Unset = INHERIT, never "This device". The empty choice reads the same
    // in InfoWindow as in RecipeEditor.
    const empty = runsOn!.choices(
      { kind: "recipe", id: "r1", ref: {} } as unknown as WorldObject,
      EMPTY_ITEMS,
    )[0];
    expect(empty).toEqual({ id: "", label: "Inherit default" });
  });

  it("recipe placement writes null for unset — the SAME token RecipeEditor writes", async () => {
    const runsOn = INFO.recipe.properties.find((p) => p.key === "runs_on")!;
    const updatePrimitive = vi.fn().mockResolvedValue(undefined);
    useDesk.setState({ updatePrimitive } as never);
    await runsOn.set(
      { kind: "recipe", id: "r1", ref: {} } as unknown as WorldObject,
      "",
    );
    expect(updatePrimitive).toHaveBeenCalledWith("recipe", "r1", {
      profile_id: null,
    });
  });

  it("filedZones matches by bare id and qualified ref", () => {
    const items: Items = {
      ...EMPTY_ITEMS,
      directory: [
        { kind: "directory", id: "d1", name: "Z", memberIds: ["note:x1"] } as Directory,
        { kind: "directory", id: "d2", name: "Y", memberIds: ["other"] } as Directory,
      ],
    };
    expect(filedZones(obj("note"), items).map((d) => d.id)).toEqual(["d1"]);
  });
});
