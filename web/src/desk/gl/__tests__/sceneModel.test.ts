// HS-95-01 — the GL world's pure scene model: same store in, same world
// out. These tests pin the geometry/state contract the renderer draws and
// the DOM overlays anchor to.
import { describe, expect, it } from "vitest";
import { EMPTY_ITEMS, type Items } from "../../api";
import { objUnit, worldObjects } from "../../world";
import {
  buildScene,
  clampLabel,
  hitTest,
  objectRect,
  ropeObjects,
  zoneRect,
  MAX_FLOATERS,
  type SceneInputs,
} from "../sceneModel";
import {
  clientToUnit,
  unitToClient,
  unitToLocal,
  OBJECT_CLAMP,
  ZONE_CLAMP,
  type WorldRect,
} from "../coords";

const RECT: WorldRect = { left: 100, top: 50, width: 1200, height: 800 };

function inputs(partial: Partial<SceneInputs> = {}): SceneInputs {
  return {
    items: EMPTY_ITEMS,
    divedZone: null,
    positions: {},
    zoneWidths: {},
    draggingId: null,
    hoverZoneId: null,
    renamingZoneId: null,
    newIds: [],
    editingId: null,
    selectedIds: [],
    subjectCounts: {},
    compact: false,
    worldWidth: RECT.width,
    ...partial,
  };
}

const someItems: Items = {
  ...EMPTY_ITEMS,
  note: [
    { kind: "note", id: "n1", title: "Standup notes from the long Tuesday" },
    { kind: "note", id: "n2", title: "Second" },
  ],
  meeting: [{ kind: "meeting", id: "m1", title: "Launch sync" }],
  directory: [
    {
      kind: "directory",
      id: "d1",
      title: "Reference",
      memberIds: ["note:n2"],
    } as any,
  ],
};

describe("buildScene", () => {
  it("projects the same objects worldObjects yields, with objUnit homes", () => {
    const scene = buildScene(inputs({ items: someItems }));
    const world = worldObjects(someItems, null);
    expect(scene.objects.map((o) => o.key).sort()).toEqual(
      world.map((o) => `${o.kind}:${o.id}`).sort(),
    );
    const m = scene.objects.find((o) => o.id === "m1")!;
    const w = world.findIndex((o) => o.id === "m1");
    expect(m.u).toEqual(objUnit(world[w], w, world.length, {}));
  });

  it("keeps a filed object off the stage and inside its zone's thumbs", () => {
    const scene = buildScene(inputs({ items: someItems }));
    expect(scene.objects.some((o) => o.id === "n2")).toBe(false);
    expect(scene.zones).toHaveLength(1);
    expect(scene.zones[0].thumbs.map((t) => t.id)).toEqual(["note:n2"]);
    expect(scene.zones[0].count).toBe(1);
  });

  it("caps at MAX_FLOATERS with the honest overflow", () => {
    const many: Items = {
      ...EMPTY_ITEMS,
      note: Array.from({ length: MAX_FLOATERS + 50 }, (_, i) => ({
        kind: "note" as const,
        id: `n${i}`,
        title: `Note ${i}`,
      })),
    };
    const scene = buildScene(inputs({ items: many }));
    expect(scene.objects).toHaveLength(MAX_FLOATERS);
    expect(scene.overflow).toEqual({
      shown: MAX_FLOATERS,
      total: MAX_FLOATERS + 50,
    });
  });

  it("carries drag/selection/new/editing state and attention counts", () => {
    const scene = buildScene(
      inputs({
        items: someItems,
        draggingId: "m1",
        selectedIds: ["note:n1"],
        newIds: ["m1"],
        editingId: "n1",
        subjectCounts: { "meeting:m1": { needs_attention: 3 } },
      }),
    );
    const m = scene.objects.find((o) => o.id === "m1")!;
    const n = scene.objects.find((o) => o.id === "n1")!;
    expect(m.dragging).toBe(true);
    expect(m.isNew).toBe(true);
    expect(m.attention).toBe(3);
    expect(n.selected).toBe(true);
    expect(n.editing).toBe(true);
  });

  it("gives zones saved positions/widths precedence over the default grid", () => {
    const scene = buildScene(
      inputs({
        items: someItems,
        positions: { "zone:d1": { x: 0.7, y: 0.6 } },
        zoneWidths: { d1: 420 },
      }),
    );
    expect(scene.zones[0].u).toEqual({ x: 0.7, y: 0.6 });
    expect(scene.zones[0].width).toBe(420);
  });

  it("clamps a saved zone width to the grip's own bounds", () => {
    const scene = buildScene(
      inputs({ items: someItems, zoneWidths: { d1: 9999 } }),
    );
    expect(scene.zones[0].width).toBe(560);
  });
});

describe("coords (the shared GL/DOM transform)", () => {
  it("round-trips unit → client → unit inside the clamps", () => {
    const u = { x: 0.31, y: 0.62 };
    const c = unitToClient(u, RECT);
    const back = clientToUnit(c.x, c.y, RECT, OBJECT_CLAMP);
    expect(back.x).toBeCloseTo(u.x, 10);
    expect(back.y).toBeCloseTo(u.y, 10);
  });

  it("applies the DOM world's exact drag clamps", () => {
    const beyond = clientToUnit(RECT.left - 500, RECT.top - 500, RECT);
    expect(beyond).toEqual({ x: 0.04, y: 0.04 });
    const zone = clientToUnit(
      RECT.left + RECT.width * 2,
      RECT.top + RECT.height * 2,
      RECT,
      ZONE_CLAMP,
    );
    expect(zone).toEqual({ x: 0.96, y: 0.94 });
  });

  it("anchors a DOM overlay to the same pixel the GL sprite draws at", () => {
    const u = { x: 0.5, y: 0.25 };
    const local = unitToLocal(u, RECT);
    const client = unitToClient(u, RECT);
    expect(client.x - RECT.left).toBeCloseTo(local.x, 10);
    expect(client.y - RECT.top).toBeCloseTo(local.y, 10);
    // A resize moves both the same way (the "stays glued" criterion).
    const grown: WorldRect = { ...RECT, width: 1600 };
    expect(unitToClient(u, grown).x - grown.left).toBeCloseTo(
      unitToLocal(u, grown).x,
      10,
    );
  });
});

describe("hitTest (DOM stacking parity: zones above resting objects)", () => {
  const scene = buildScene(
    inputs({
      items: someItems,
      positions: {
        m1: { x: 0.5, y: 0.5 },
        n1: { x: 0.2, y: 0.8 },
        "zone:d1": { x: 0.5, y: 0.48 },
      },
    }),
  );

  it("hits the object at its column box", () => {
    const r = objectRect(scene.objects.find((o) => o.id === "n1")!, RECT);
    const hit = hitTest(scene, RECT, r.cx, r.cy);
    expect(hit.type).toBe("object");
    if (hit.type === "object") expect(hit.object.id).toBe("n1");
  });

  it("prefers the overlapping zone over the object beneath", () => {
    const zr = zoneRect(scene.zones[0], RECT);
    const hit = hitTest(scene, RECT, zr.cx, zr.top + zr.height - 8);
    expect(["zone", "zone-grip"]).toContain(hit.type);
  });

  it("resolves the grip corner and the title row distinctly", () => {
    const zr = zoneRect(scene.zones[0], RECT);
    const grip = hitTest(scene, RECT, zr.left + zr.width - 8, zr.top + zr.height - 8);
    expect(grip.type).toBe("zone-grip");
    const title = hitTest(scene, RECT, zr.cx, zr.top + 12);
    expect(title.type).toBe("zone-title");
  });

  it("ignores the dragged object for the drop hit-test", () => {
    const r = objectRect(scene.objects.find((o) => o.id === "m1")!, RECT);
    const hit = hitTest(scene, RECT, r.cx, r.cy, { ignoreObjectId: "m1" });
    expect(hit.type).not.toBe("object");
  });

  it("ropes by rendered center, in selection refs", () => {
    const roped = ropeObjects(scene, RECT, {
      left: RECT.left,
      top: RECT.top + RECT.height * 0.7,
      right: RECT.left + RECT.width * 0.5,
      bottom: RECT.top + RECT.height,
    });
    expect(roped).toEqual(["note:n1"]);
  });
});

describe("clampLabel (the two-line ellipsis contract)", () => {
  const measure = (s: string) => s.length * 6;

  it("keeps short titles verbatim", () => {
    expect(clampLabel("Launch sync", measure, 118)).toBe("Launch sync");
  });

  it("wraps to two lines", () => {
    const out = clampLabel("Standup notes from Tuesday", measure, 90);
    expect(out.split("\n")).toHaveLength(2);
    expect(out).not.toContain("…");
  });

  it("ellipsizes what two lines cannot hold", () => {
    const out = clampLabel(
      "A very long meandering title that keeps going well past two lines of space",
      measure,
      90,
    );
    const lines = out.split("\n");
    expect(lines).toHaveLength(2);
    expect(lines[1].endsWith("…")).toBe(true);
    expect(measure(lines[1])).toBeLessThanOrEqual(90 + 6);
  });
});
