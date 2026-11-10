// Shared Settings glyph selection; the preference kit owns the face.
import { spriteUrl } from "../../../desk/sprites";
import type { SettingsSectionId } from "./prefs";

const SPRITES = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/settings/`;
const WORLD: Partial<Record<SettingsSectionId, { kind: string; id: string; agent?: string }>> = {
  you: { kind: "person", id: "settings-you" },
  meetings: { kind: "meeting", id: "settings-meetings" },
  agents: { kind: "agent", id: "settings-agents", agent: "codex" },
};

/** The section's sprite: the desk's own sprite where the section is an
 *  object of the desk, the settings mold elsewhere. */
export function sectionSprite(id: SettingsSectionId, sprite: string): string {
  const world = WORLD[id];
  return world ? spriteUrl(world.kind, world.id, "rest", world.agent, 32) : `${SPRITES}${sprite}.png`;
}
