/** The New decision window (the owner, 2026-10-25): its window id and the
 * keys of its kept draft. A leaf module: the store and the window's core
 * both read it, so neither imports the other. */
export const NEW_DECISION_WINDOW = "surface-new-decision";

/** The unfinished title and Why, kept in the workspace document so they
 * return after a reload (PHILO-13-07 B2). A fresh New Decision forgets them. */
export const NEW_DECISION_DRAFT = {
  title: "desk/new-decision/title",
  why: "desk/new-decision/why",
} as const;
