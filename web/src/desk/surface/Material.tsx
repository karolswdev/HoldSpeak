// Written material shares the reading species with full agent documents.
// Known note doors retain their real library Button actions.
import { ReadingDocument } from "./ReadingDocument";
import { openSurfaceOr } from "../shell";

/** The doors a note may open. Each one is a real opener the desk has. */
export const NOTE_DOORS: Record<string, () => void> = {
  "record-live": () => openSurfaceOr("record-live", "/live"),
  dictate: () => openSurfaceOr("dictate", "/dictation"),
  needs: () => void import("../screen/open").then((m) => m.openNeedsYouDrawer()),
  "open-people": () => openSurfaceOr("open-people", "/"),
};

function noteDoor(name: string): (() => void) | undefined {
  return Object.prototype.hasOwnProperty.call(NOTE_DOORS, name) ? NOTE_DOORS[name] : undefined;
}

/** True when the text has a door link the desk can open. */
export function hasNoteDoor(text: string): boolean {
  return [...text.matchAll(/\]\(door:([a-z-]+)\)/g)].some((m) => Boolean(noteDoor(m[1])));
}

/** Written material shares its document grammar with full agent text. */
export function Material({ children, className }: { children: string; className?: string }) {
  return <ReadingDocument className={`surface-material${className ? ` ${className}` : ""}`} noteDoors={NOTE_DOORS}>{children}</ReadingDocument>;
}
