/* PARKED (Betterment AG1, 2026-10-18; DECISIONS #3). The old Agents
 * application row, cut from desk/applications.ts as it was. Not compiled
 * (tsconfig and vitest exclude _parked). */
// @ts-nocheck
  // PARKED (PHILO-14 C4): the old Agents application. It folded into the
  // Conductor drawer; its route `/companion` stays alive, but it is in no
  // Dock, Go list, shortcut or mark menu. Nothing links to it.
  {
    action: "inspect-personas-and-coders",
    windowId: "surface-companion",
    label: "Agents",
    toolLabel: "Agents and coder sessions",
    description: "Use saved behavior and inspect live sessions.",
    glyph: "◉",
    href: "/companion",
    surface: {
      eyebrow: "Companion",
      minW: 560,
      load: () =>
        import("../pages/cores/CompanionCore").then((module) => ({
          default: module.CompanionCore,
        })),
    },
  },
