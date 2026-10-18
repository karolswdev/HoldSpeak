/* PARKED (Betterment AG1, 2026-10-18; DECISIONS #3: "New Agent" leaves the
 * Desk menu). The verb, cut from desk/verbRegistry.ts as it was. Not
 * compiled (tsconfig and vitest exclude _parked). */
// @ts-nocheck
  {
    id: "desk.new-agent",
    label: "New Agent",
    menu: "desk",
    scope: "floor",
    group: "new",
    glyph: KIND_GLYPH.recipe,
    keywords: ["create", "recipe"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("recipe"),
  },
