/** PHILO-8-01 — the Chair withholds New Zone (the owner's Q2 (c)), and the
 * F2 Rename of a zone starts a rename only where zones are shown. */
import { beforeEach, describe, expect, it } from "vitest";
import { VERBS, menuVerbs, offeredHere, verbById } from "../verbRegistry";
import { useChairState } from "../chairState";
import { useDesk } from "../store";

const zone = { kind: "directory", id: "dir_a", name: "Alpha", nameNormalized: "alpha", memberIds: [], createdAt: "" };

describe("the Chair withholds the zone verbs", () => {
  beforeEach(() => {
    useChairState.setState({ surface: "chair" });
    useDesk.setState({ renamingZoneId: null });
  });

  it("New Zone is not offered on the Chair, and is on the Floor", () => {
    const newZone = verbById("desk.new-zone")!;
    expect(offeredHere(newZone)).toBe(false);
    useChairState.setState({ surface: "floor" });
    expect(offeredHere(newZone)).toBe(true);
  });

  it("only New Zone is withheld: the other creation verbs stay on the Chair", () => {
    const withheld = menuVerbs("desk").filter((v) => !offeredHere(v)).map((v) => v.id);
    expect(withheld).toEqual(["desk.new-zone"]);
    expect(VERBS.filter((v) => v.needsZones).map((v) => v.id)).toEqual(["desk.new-zone"]);
  });

  it("F2 on a zone: ghosted on the Chair and starts no rename; on the Floor it starts the rename", () => {
    useDesk.setState({ items: { ...useDesk.getState().items, directory: [zone] as never } });
    const rename = verbById("object.rename")!;
    const ctx = { selectedRef: "zone:dir_a" };
    expect(rename.ghost(ctx)).toBe("Open the Floor");
    rename.run(ctx);
    expect(useDesk.getState().renamingZoneId).toBeNull();
    useChairState.setState({ surface: "floor" });
    expect(rename.ghost(ctx)).toBeNull();
    rename.run(ctx);
    expect(useDesk.getState().renamingZoneId).toBe("dir_a");
  });
});
