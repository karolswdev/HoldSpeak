// HS-111-09 — the agent face is the automaton sprite family, never the
// 🤖 emoji (kit law: no emoji as icons). A user-set custom avatar (the
// recipe editor's free-text field) still renders as text; the DEFAULT is
// the same deterministic automaton the desk field already deals this id.
// Sizes must stay integer divisors of the 64px source (16/32/64) so the
// pixelated downscale samples uniformly.
import { spriteUrl } from "../sprites";
import { spriteStateCssClass } from "../../lib/spriteStates";
import { spriteVariantKey } from "../../lib/spriteVariants";

export function AgentAvatar({
  avatar,
  id,
  kind = "agent",
  size = 32,
  className,
  spriteState,
}: {
  /** The wire avatar (free text). Empty or the legacy robot default -> sprite. */
  avatar?: string | null;
  id: string;
  /** Sprite pool: "agent" (automaton) or "model" (cartridge). */
  kind?: "agent" | "model";
  size?: 16 | 32 | 64;
  className?: string;
  /** HS-118-07 — the primitive's sprite state for CSS hint class. */
  spriteState?: string | null;
}) {
  const custom = String(avatar || "").trim();
  if (custom && custom !== "\u{1F916}")
    return (
      <span className={className} aria-hidden="true">
        {custom}
      </span>
    );
  const cssHint = spriteStateCssClass(spriteState);
  return (
    <img
      src={spriteUrl(kind, id)}
      alt=""
      width={size}
      height={size}
      className={
        "desk-chrome-sprite" + (cssHint ? ` ${cssHint}` : "") + (className ? ` ${className}` : "")
      }
      draggable={false}
      aria-hidden="true"
      data-sprite-variant={spriteVariantKey(kind === "agent" ? "workbench" : kind, spriteState)}
    />
  );
}
