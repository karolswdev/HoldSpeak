/** HS-105-04 — the Info-contract guard: one derived surface, honest
 * measures, properties only where a REAL update path exists. */
import { describe, expect, it, vi } from "vitest";
import { INFO, kindInfo, filedZones, type InfoSummary } from "../infoContract";
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
    // HS-134-05: recipe placement is now a read-only summary with hand-off;
    // no kind exposes a writable property today.
    const declared = Object.entries(INFO).flatMap(([kind, info]) =>
      info.properties.map((p) => `${kind}.${p.key}`),
    );
    expect(declared).toEqual([]);
  });

  it("recipe has NO writable properties — HS-134-05 removed the write path", () => {
    expect(INFO.recipe.properties).toEqual([]);
  });

  it("recipe placement summary shows INHERITED when profileId is unset", () => {
    const placement = INFO.recipe.summaries?.find(
      (s: InfoSummary) => s.key === "placement",
    );
    expect(placement).toBeDefined();
    expect(placement!.label).toBe("Placement");
    // Absent profileId renders as INHERITED, not blank.
    expect(
      placement!.value(obj("recipe", {})),
    ).toBe("INHERITED");
    expect(
      placement!.value(obj("recipe", { profileId: null })),
    ).toBe("INHERITED");
    expect(
      placement!.value(obj("recipe", { profileId: "" })),
    ).toBe("INHERITED");
  });

  it("recipe placement summary shows the profile name when set", () => {
    useDesk.setState({
      profiles: [{ id: "p1", name: "Cloud GPT-4" }],
    } as never);
    const placement = INFO.recipe.summaries?.find(
      (s: InfoSummary) => s.key === "placement",
    );
    expect(
      placement!.value(obj("recipe", { profileId: "p1" })),
    ).toBe("Cloud GPT-4");
  });

  it("recipe placement hand-off opens the editor", () => {
    const openEditor = vi.fn();
    useDesk.setState({ openEditor } as never);
    const placement = INFO.recipe.summaries?.find(
      (s: InfoSummary) => s.key === "placement",
    );
    expect(placement!.handoff).toBeDefined();
    expect(placement!.handoff!.verb).toBe("Edit in Agent");
    const recipe = obj("recipe", {});
    placement!.handoff!.action(recipe);
    expect(openEditor).toHaveBeenCalledWith("x1");
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
