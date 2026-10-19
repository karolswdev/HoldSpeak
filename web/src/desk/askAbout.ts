/** Betterment Q5 — Ask about this, from everywhere.
 *
 * One verb on every object: it opens Ask with the object in About and an
 * empty question. It replaces Object ▸ Ask AI, Ask this project and Continue
 * in thread. On a person it reads "Ask about Mira".
 *
 * The object is a desk item, or the thing a window shows that the desk does
 * not hold as an item: a person (`people:<id>`, a person is not a desk item)
 * or an older meeting. Their names come from the window that shows them. */
import { useDesk } from "./store";
import { objectByRef } from "./world";
import { qualifiedRef } from "./api";
import { primitiveCan, type PrimitiveKind } from "../lib/primitives";
import { windowRegistry } from "./components/window/windowRegistry";
import type { AskContext } from "./ask";

/** One About chip: what the object is, by its name and qualified ref. */
export type AboutChip = Required<AskContext>;

/** The kinds Ask about this is offered on (beyond every kind that can be asked). */
const ABOUT_KINDS = new Set(["meeting", "note", "artifact", "decision", "recipe", "project", "directory", "kb", "people"]);

export function askableKind(kind: string): boolean {
  if (ABOUT_KINDS.has(kind)) return true;
  try {
    return primitiveCan(kind as PrimitiveKind, "ask");
  } catch {
    return false;
  }
}

/** The name an open window shows, without its kind word. */
function windowName(id: string): string {
  return (windowRegistry.get(id)?.label ?? "").trim();
}

/** The object Ask about this asks about, or null when the ref names nothing
 *  it can ask about (the People roster, a kind with no answer). */
export function aboutTarget(ref: string | null | undefined): AboutChip | null {
  const clean = String(ref ?? "").trim();
  if (!clean) return null;
  const object = objectByRef(useDesk.getState().items, clean);
  if (object) {
    if (!askableKind(object.kind) || (object.kind === "people" && object.id === "people")) return null;
    return { id: object.id, kind: object.kind, title: String(object.title || ""), ref: qualifiedRef(object.kind, object.id) };
  }
  const [kind, ...rest] = clean.split(":");
  const id = rest.join(":").split("#", 1)[0];
  if (!id) return null;
  if (kind === "people" && id !== "people" && !id.startsWith("project:")) {
    return { id, kind: "people", title: windowName(`pullout:people:${id}`) || "This person", ref: `people:${id}` };
  }
  if (kind === "meeting") {
    const shown = windowName(`pullout:meeting:${id}`);
    return { id, kind: "meeting", title: shown || "This meeting", ref: `meeting:${id}` };
  }
  return null;
}

/** The verb's words: "Ask about Mira" on a person, else "Ask about this". */
export function askAboutLabel(target: AboutChip | null): string {
  if (target?.kind === "people") {
    const first = target.title.trim().split(/\s+/, 1)[0];
    if (first && target.title !== "This person") return `Ask about ${first}`;
  }
  return "Ask about this";
}

/** Open Ask about the object `ref` names. */
export function askAboutRef(ref: string | null | undefined): boolean {
  const target = aboutTarget(ref);
  if (!target) return false;
  useDesk.getState().askAbout([target]);
  return true;
}
