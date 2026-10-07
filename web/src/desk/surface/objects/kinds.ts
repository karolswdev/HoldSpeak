/** PHILO-14 B1 — the object vocabulary the object species share.
 *
 *  The kinds are the A boards' (docs/internal/philo/phase-14/canvas): every
 *  object on the desk is one of these, drawn by ONE sprite from the mold
 *  (`web/public/desk/sprites`, through `sprites.ts`). Lane A0 redraws the
 *  mold; the face reads the sprite through `objectSprite` (or passes its
 *  own `sprite` URL), so the redraw lands here once.
 */
import { SPRITE_BASE, spriteUrl, type SpriteState } from "../../sprites";

export type ObjectKind =
  | "project"
  | "meeting"
  | "decision"
  | "action"
  | "note"
  | "artifact"
  | "repository"
  | "agent"
  | "pr"
  | "person"
  | "conductor"
  | "smart"
  | "parked";

/** The KIND word of an object (the caption step: Get Info, the list's Kind
 *  column, an icon's accessible name). */
export const OBJECT_KIND_WORD: Readonly<Record<ObjectKind, string>> = {
  project: "PROJECT",
  meeting: "MEETING",
  decision: "DECISION",
  action: "ACTION ITEM",
  note: "NOTE",
  artifact: "ARTIFACT",
  repository: "REPOSITORY",
  agent: "AGENT",
  pr: "PULL REQUEST",
  person: "PERSON",
  conductor: "DRAWER",
  smart: "SMART DRAWER",
  parked: "DRAWER",
};

export function objectKindWord(kind: string): string {
  return OBJECT_KIND_WORD[kind as ObjectKind] ?? kind.toUpperCase();
}

/** The one sprite for an object of `kind` (the A boards' mapping; the mold
 *  has no action-item, PR, person, smart-drawer or Conductor sprite yet, so
 *  those borrow the nearest family — README S7). */
export function objectSprite(kind: string, id: string, state: SpriteState = "rest"): string {
  const drawer = (name: string) => `${SPRITE_BASE}${name}${state === "rest" ? "" : `_${state}`}.png`;
  switch (kind) {
    case "project":
    case "repository":
    case "conductor":
    case "smart":
      return drawer("drawer");
    case "parked":
      return `${SPRITE_BASE}drawer_stale.png`;
    case "action":
      return spriteUrl("story", id, state);
    case "pr":
      return spriteUrl("artifact", id, state);
    case "person":
      return spriteUrl("people", id, state);
    case "agent":
      return spriteUrl("coder", id, state);
    default:
      return spriteUrl(kind, id, state);
  }
}

/** The lamp tones an object wears. Never colour alone: every lamp sits
 *  beside a word (the row's), or the word is in the accessible name. */
export type ObjectTone = "ok" | "warn" | "fail" | "info" | "ask";

/** The LampGadget tone for an object tone. Since round 2 of B1 LampGadget
 *  carries all five tones, so this is the identity (kept for callers):
 *  an object is the same colour in the grid, the list and the Needs row. */
export function lampGadgetTone(tone: ObjectTone | undefined): ObjectTone {
  return tone ?? "ok";
}
