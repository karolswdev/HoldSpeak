/* PARKED (Betterment Q10 "Knowledge becomes drawers", 2026-10-19;
 * DECISIONS #2): New Knowledge leaves the New list. Each existing collection
 * shows as a drawer of the same name; the kb data and the kb.* tools stay.
 * The verb, cut from desk/verbRegistry.ts as it was. Not compiled (tsconfig
 * and vitest exclude _parked). */
// @ts-nocheck
  {
    id: "desk.new-knowledge",
    label: "New Knowledge",
    menu: "desk",
    scope: "floor",
    group: "new",
    glyph: KIND_GLYPH.kb,
    keywords: ["create", "kb"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("kb"),
  },
