/** PHILO-14 B1 — the object vocabulary the object species share.
 *
 *  The kinds are the A boards' (docs/internal/philo/phase-14/canvas): every
 *  object on the desk is one of these, drawn by ONE sprite from the mold
 *  (`web/public/desk/sprites`, through `sprites.ts`). Lane A0 redraws the
 *  mold; the face reads the sprite through `objectSprite` (or passes its
 *  own `sprite` URL), so the redraw lands here once.
 */
import { spriteUrl, type SpriteSize, type SpriteState } from "../../sprites";
import { wireWords } from "../words";

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
  project: "Project",
  meeting: "Meeting",
  decision: "Decision",
  action: "Action item",
  note: "Note",
  artifact: "Artifact",
  repository: "Repository",
  agent: "Agent",
  pr: "Pull request",
  person: "Person",
  conductor: "Drawer",
  smart: "Smart drawer",
  parked: "Drawer",
};

/** Betterment A1: a desk kind whose stored name is not its word. */
const STORED_KIND_WORD: Readonly<Record<string, string>> = { workbench: "Automation" };

/** WORDS-VOCAB 2026-10-30: the kind word in sentence case (`Action item`);
 *  a kind the table does not know is said in words (`wireWords`). */
export function objectKindWord(kind: string): string {
  return OBJECT_KIND_WORD[kind as ObjectKind] ?? STORED_KIND_WORD[kind] ?? wireWords(kind);
}

/** The one sprite for an object of `kind`, at the icon size (64) or the
 *  list-row size (32, drawn at 32: PHILO-14 A0c). Every kind of the D1 mold
 *  has its own file in `sprites.ts` (A0b drew action item, PR, person and
 *  the drawers), so the kind reads through `spriteUrl` directly; only
 *  `agent` reads through the coder pool, by its agent name when given. */
export function objectSprite(
  kind: string,
  id: string,
  state: SpriteState = "rest",
  size: SpriteSize = 64,
  /** The agent name of an agent object (`claude`, `codex`): it picks the
   *  agent's own sprite (PHILO-14 A0c r2: Codex keeps its face everywhere). */
  agent?: string | null,
): string {
  return spriteUrl(kind === "agent" ? "coder" : kind, id, state, agent, size);
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
