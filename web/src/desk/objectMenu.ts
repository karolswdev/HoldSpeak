/** The right-click menu of one desk object, derived from the ONE verb
 * registry (HS-111-07); this module mints nothing. It moved out of the
 * parked floorMenu.ts (PHILO-17, one desk): the Screen uses it. */
import { menuVerbs, verbLabel, type Verb, type VerbContext } from "./verbRegistry";
import type { WorkMenuEntry } from "./components/DeskMenu";
import { objectByRef, type WorldObject } from "./world";
import { useDesk } from "./store";
import { primitiveCan } from "../lib/primitives";
import { handKindOf } from "./agentHand";
import { deleteSeatShown } from "./deleteSeat";
import { askableKind } from "./askAbout";
import { askAboutRef } from "./askAbout";
import { openPerson } from "./openObject";
import { useScreenMembersStore } from "./screen/members";
import { normalizeRef, SEED_DESK_DIRECTORY_ID } from "./screen/compose";

const KEEPABLE_KINDS = new Set(["meeting", "person", "people", "decision", "artifact", "repository", "thread"]);

function directoryHasRef(directoryId: string, targetRef: string): boolean {
  const directory = useDesk.getState().items.directory?.find((row) => row.id === directoryId);
  if (!directory) return false;
  const normalized = normalizeRef(targetRef);
  const bareId = targetRef.includes(":") ? targetRef.slice(targetRef.indexOf(":") + 1) : targetRef;
  return (directory.memberIds ?? []).some((member) => normalizeRef(member) === normalized || member === bareId);
}

function deskHasRef(targetRef: string): boolean {
  return directoryHasRef(SEED_DESK_DIRECTORY_ID, targetRef);
}

function targetKind(targetRef: string, object: WorldObject | null): string {
  return object?.kind ?? targetRef.split(":", 1)[0];
}

/** Object menus only list verbs the selected kind can run. State conditions
 * (for example a missing delete receipt) use the registry's ghost reason;
 * kind conditions are removed from this menu so every remaining row acts. */
/** A kind's capability; a kind that is not a primitive (a person's window) has none. */
function can(kind: string, capability: Parameters<typeof primitiveCan>[1]): boolean {
  try {
    return primitiveCan(kind as WorldObject["kind"], capability);
  } catch {
    return false;
  }
}

function offeredForKind(v: Verb, kind: WorldObject["kind"] | string): boolean {
  switch (v.id) {
    case "object.open":
      return true;
    case "object.file":
      return KEEPABLE_KINDS.has(kind);
    case "object.unfile":
      return KEEPABLE_KINDS.has(kind) || kind === "note";
    case "object.draft-update":
      return kind === "project";
    // Betterment Q5: Ask about this, on every object he can ask about.
    case "object.ask-about":
      return askableKind(kind);
    case "object.hand-to-agent":
      return can(kind, "hand") && handKindOf(kind as WorldObject["kind"]) !== null;
    case "object.edit":
      return can(kind, "edit");
    case "object.rename":
      return kind !== "directory" && can(kind, "rename");
    case "object.duplicate":
      return can(kind, "duplicate");
    case "object.delete":
      return can(kind, "delete") && deleteSeatShown();
    case "object.archive":
      return kind === "project" && can(kind, "archive");
    default:
      return true;
  }
}

function item(v: Verb, ctx: VerbContext): WorkMenuEntry {
  return {
    type: "item",
    id: v.id,
    label: verbLabel(v, ctx),
    glyph: v.glyph,
    keycap: v.key,
    ghost: v.ghost(ctx),
    onSelect: () => v.run(ctx),
  };
}

/** People relationships are protected data, so they are intentionally absent
 * from Items. The Screen member store is the existing privacy/readiness
 * source; this adapter gives a kept person the same live object verbs as an
 * ordinary Desk object without creating a second person ledger. */
function personMenuEntries(ref: string): WorkMenuEntry[] | null {
  const match = /^people:([^:]+)$/.exec(ref);
  if (!match) return null;
  if (match[1] === "people") return [];
  const person = useScreenMembersStore.getState().people?.persons.find((candidate) => candidate.id === match[1]);
  // A protected person that the existing People read did not return is not a
  // generic primitive. Withhold every verb rather than drawing a dead Open.
  if (!person) return [];
  const personRef = `people:${person.id}`;
  const entries: WorkMenuEntry[] = [
    { type: "item", id: "object.open", label: "Open", glyph: "▷", onSelect: () => openPerson(person.id) },
    { type: "item", id: "person.ask-about", label: `Ask about ${person.name.split(/\s+/, 1)[0]}`, glyph: "✦", onSelect: () => { askAboutRef(personRef); } },
    { type: "item", id: "person.prep", label: "Prep 1:1", glyph: "▸", onSelect: () => openPerson(person.id, "prep") },
  ];
  if (deskHasRef(personRef)) {
    entries.push({
      type: "item",
      id: "person.remove-from-desk",
      label: "Remove from desk",
      glyph: "↩",
      onSelect: () => { void useDesk.getState().removeFromDir(person.id, SEED_DESK_DIRECTORY_ID, "people"); },
    });
  } else {
    entries.push({
      type: "item",
      id: "person.keep-on-desk",
      label: "Keep on desk",
      glyph: "↳",
      onSelect: () => { void useDesk.getState().fileIntoDir(person.id, SEED_DESK_DIRECTORY_ID, "people"); },
    });
  }
  return entries;
}

/** The object menu: the object.* verbs, the danger group after a separator.
 *
 * Betterment Q5: a row that does not apply is not shown: no greyed row with
 * its excuse. A ref the desk does not hold as an item (a person's window, an
 * older meeting) offers only the verbs that work without one. */
export function objectMenuEntries(target: { ref: string }): WorkMenuEntry[] {
  const personEntries = personMenuEntries(target.ref);
  if (personEntries) return personEntries;
  const ctx: VerbContext = { selectedRef: target.ref };
  const verbs = menuVerbs("object");
  const object = objectByRef(useDesk.getState().items, target.ref);
  const kind = targetKind(target.ref, object);
  const offered = verbs
    .filter((v) => offeredForKind(v, kind))
    .filter((v) => {
      if (v.id === "object.file") return !deskHasRef(target.ref);
      if (v.id === "object.unfile") return kind === "note" || deskHasRef(target.ref);
      return true;
    })
    .filter((v) => !v.ghost(ctx));
  const ordinary = offered.filter((v) => v.group !== "danger");
  const danger = offered.filter((v) => v.group === "danger");
  return [
    ...ordinary.map((v) => item(v, ctx)),
    ...(danger.length ? [{ type: "sep" as const, id: "object.danger-sep" }] : []),
    ...danger.map((v) => item(v, ctx)),
  ];
}

/** PHILO-17 (owner 2026-10-10, "Yes, everything must become one desk"): the
 * object a pullout window shows (`pullout:<ref>`), when the desk knows it.
 * Agents, workflows, Knowledge and Sequences are not on the desk, so their
 * windows carry their object verbs (Delete through the one receipt). */
export function windowObjectRef(winId: string | null): string | null {
  if (!winId) return null;
  // Betterment Q5: the Meetings window shows one meeting; its Object menu is that meeting's.
  if (winId === "surface-meetings") {
    const scope = String(useDesk.getState().windowsById?.[winId]?.scope ?? "");
    return scope.startsWith("meeting:") && scope.length > "meeting:".length ? scope : null;
  }
  if (!winId.startsWith("pullout:")) return null;
  const ref = winId.slice("pullout:".length);
  if (objectByRef(useDesk.getState().items, ref)) return ref;
  // A person is not a desk item; her window is still hers (Betterment Q5).
  if (ref.startsWith("people:") && ref !== "people:people" && !ref.startsWith("people:project:")) return ref;
  return ref.startsWith("meeting:") && ref.length > "meeting:".length ? ref : null;
}

/** The window menu's `Object ▸`: the object verbs of the window's object.
 * Delete closes the window first, so its receipt on the desk is in view. */
export function windowObjectEntry(winId: string | null, closeWindow: () => void): WorkMenuEntry | null {
  const ref = windowObjectRef(winId);
  if (!ref) return null;
  const entries = objectMenuEntries({ ref }).map((e) =>
    e.type === "item" && e.id === "object.delete" && !e.ghost
      ? { ...e, onSelect: () => { closeWindow(); e.onSelect(); } }
      : e,
  );
  return { type: "sub", id: "window-object", label: "Object", entries };
}
