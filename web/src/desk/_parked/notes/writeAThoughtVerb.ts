/* PARKED (Betterment Q8 "One note", 2026-10-18): "Write a thought" leaves
 * the Desk menu. New Note (⌃N) opens the same sticky and takes ⌃T. The verb,
 * cut from desk/verbRegistry.ts as it was. Not compiled (tsconfig and vitest
 * exclude _parked). */
// @ts-nocheck
  // PHILO-13-16 (C6) — the pop-key: a thought from any window in one key
  // press (⌃T). At 393 the same verb is in the Desk menu; no key is assumed.
  {
    id: "desk.new-thought",
    label: "Write a thought",
    menu: "desk",
    scope: "floor",
    group: "new",
    key: "⌃T",
    glyph: KIND_GLYPH.note,
    keywords: ["capture", "thought", "write", "idea"],
    ghost: never,
    run: async () => {
      const { openNewThought } = await import("./newThought");
      await openNewThought();
    },
  },
