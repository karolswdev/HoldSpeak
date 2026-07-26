/** HS-105-02 — the drop matrix (the AppIcon rule): what a kind ACCEPTS
 * dropped onto it, and the NAMED verb release performs. Contract data —
 * the engine and every surface derive from this table; a kind pair not
 * listed here refuses. Verbs are consent-honest: a drop that would RUN
 * something lands the object as held context beside the run verb (the
 * human presses it); a drop that files is reversible by construction. */

/** What each target kind accepts, and the verb's label under the cursor. */
export interface DropRule {
  /** Source kinds this target accepts. */
  accepts: ReadonlySet<string>;
  /** The verb tag shown while hovering (states exactly what release does). */
  verb: string;
  /** The action id the engine dispatches on release. */
  action: "ground-into" | "file-knowledge";
}

const GROUNDABLE = new Set(["note", "kb", "meeting", "artifact"]);
const KNOWLEDGE_FILABLE = new Set(["note", "meeting", "artifact", "recipe"]);

export const DROP_MATRIX: Record<string, DropRule> = {
  recipe: {
    accepts: GROUNDABLE,
    verb: "Hold as source",
    action: "ground-into",
  },
  chain: { accepts: GROUNDABLE, verb: "Hold as source", action: "ground-into" },
  workflow: {
    accepts: GROUNDABLE,
    verb: "Hold as source",
    action: "ground-into",
  },
  kb: {
    accepts: KNOWLEDGE_FILABLE,
    verb: "Add to Knowledge",
    action: "file-knowledge",
  },
};

/** The rule when `dragged` hovers `target`, or null (an inert pair). */
export function dropRule(
  targetKind: string,
  draggedKind: string,
): DropRule | null {
  const rule = DROP_MATRIX[targetKind];
  return rule && rule.accepts.has(draggedKind) ? rule : null;
}
