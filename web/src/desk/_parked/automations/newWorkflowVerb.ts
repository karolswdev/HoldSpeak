/* PARKED (Betterment A8, 2026-10-18; DECISIONS #2: "New Workflow" leaves the
 * New menu, one way to automate). The verb, cut from desk/verbRegistry.ts as
 * it was. Not compiled (tsconfig and vitest exclude _parked). */
// @ts-nocheck
  {
    id: "desk.new-workflow",
    label: "New Workflow",
    menu: "desk",
    scope: "floor",
    group: "new",
    glyph: KIND_GLYPH.workflow,
    keywords: ["create", "steps"],
    ghost: never,
    run: () => void useDesk.getState().createPrimitive("workflow"),
  },
