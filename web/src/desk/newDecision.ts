/** New decision (the owner, 2026-10-25; the native Decisions app,
 * 2026-11-08): the composer is the plate of the Decisions window, never a
 * second window. Its scope is `new` (or `new:project:<id>` with a Project in
 * front as its About), and the keys of its kept draft. A leaf module: the
 * store and the window's core both read it, so neither imports the other. */
export const NEW_DECISION_SCOPE = "new";

/** The Decisions window's scope for the composer, with the Project in front. */
export function newDecisionScope(projectId?: string | null): string {
  const id = String(projectId ?? "").trim();
  return id ? `${NEW_DECISION_SCOPE}:project:${id}` : NEW_DECISION_SCOPE;
}

/** True when the scope asks for the composer. */
export function isNewDecisionScope(scope: string | null | undefined): boolean {
  return scope === NEW_DECISION_SCOPE || Boolean(scope?.startsWith(`${NEW_DECISION_SCOPE}:`));
}

/** The unfinished title and Why, kept in the workspace document so they
 * return after a reload (PHILO-13-07 B2). A fresh New decision forgets them. */
export const NEW_DECISION_DRAFT = {
  title: "desk/new-decision/title",
  why: "desk/new-decision/why",
} as const;
