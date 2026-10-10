/* PARKED (PHILO-17, owner 2026-10-10: "Yes, everything must become one
 * desk"). The Floor-only verbs, cut from verbRegistry.ts as they were. No
 * face draws zones or a desk-wide list now. Not compiled (tsconfig and
 * vitest exclude _parked). */
// @ts-nocheck
  {
    id: "desk.new-zone",
    label: "New Zone",
    menu: "desk",
    scope: "floor",
    group: "new",
    glyph: KIND_GLYPH.zone,
    keywords: ["create", "place"],
    needsZones: true,
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("zone"),
  },

  {
    id: "desk.toggle-view",
    label: () => (currentView() === "list" ? "Spatial view" : "List view"),
    menu: "desk",
    scope: "floor",
    group: "view",
    keywords: ["list", "spatial", "view"],
    ghost: never,
    run: () => {
      useDesk
        .getState()
        .setViewMode(currentView() === "list" ? "spatial" : "list");
    },
  },

  {
    id: "desk.arrange",
    label: "Arrange desk",
    scope: "floor",
    group: "floor",
    keywords: ["tidy", "clean"],
    ghost: () =>
      Object.keys(useDesk.getState().positions).length > 0
        ? null
        : "Nothing moved",
    run: () => useDesk.getState().tidyDesk(),
  },

  {
    id: "zone.focus",
    label: "Focus",
    scope: "object",
    ghost: (ctx) => {
      const o = selected(ctx);
      if (!o) return "Select a Zone";
      return o.kind === "directory" ? null : "Select a Zone";
    },
    run: (ctx) => {
      const o = selected(ctx);
      if (o?.kind === "directory") useDesk.getState().diveInto(o.id);
    },
  },

/** The view the toggle verb would LEAVE (HS-105-01 density default). */
function currentView(): "list" | "spatial" {
  const s = useDesk.getState();
  return defaultViewFor(
    s.viewMode,
    Object.values(s.items).reduce((n, l) => n + l.length, 0),
    typeof window !== "undefined" && window.innerWidth <= 720,
  );
}

