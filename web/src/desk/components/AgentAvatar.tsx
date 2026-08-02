// HS-111-09 — the agent face is the automaton sprite family, never the
// 🤖 emoji (kit law: no emoji as icons). A user-set custom avatar (the
// recipe editor's free-text field) still renders as text; the DEFAULT is
// the same deterministic automaton the desk field already deals this id.
// Sizes must stay integer divisors of the 64px source (16/32/64) so the
// pixelated downscale samples uniformly.
import { spriteUrl } from "../sprites";

export function AgentAvatar({
  avatar,
  id,
  kind = "agent",
  size = 32,
  className,
}: {
  /** The wire avatar (free text). Empty or the legacy 🤖 default → sprite. */
  avatar?: string | null;
  id: string;
  /** Sprite pool: "agent" (automaton) or "model" (cartridge). */
  kind?: "agent" | "model";
  size?: 16 | 32 | 64;
  className?: string;
}) {
  const custom = String(avatar || "").trim();
  if (custom && custom !== "🤖")
    return (
      <span className={className} aria-hidden="true">
        {custom}
      </span>
    );
  return (
    <img
      src={spriteUrl(kind, id)}
      alt=""
      width={size}
      height={size}
      className={
        "desk-chrome-sprite" + (className ? ` ${className}` : "")
      }
      draggable={false}
      aria-hidden="true"
    />
  );
}
