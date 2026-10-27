/** Window Program W1 (2026-10-27): the Speak wings' empty state — the D
 *  mic drawing, small, the true word ("Nothing said yet") and one quiet
 *  line of what will appear here. Drawn inside SurfaceState's empty
 *  material (`emptyContent`), so every wing keeps one empty grammar. */
import { SYSTEM_48 } from "../../../desk/systemSprites";

export function SpeakEmpty({ label, hint }: { label: string; hint: string }) {
  return (
    <span className="speak-empty" data-testid="speak-empty">
      <img className="speak-empty-glyph" src={SYSTEM_48.dockSpeak} alt="" aria-hidden width={40} height={40} draggable={false} />
      <span className="speak-empty-word">{label}</span>
      <span className="speak-empty-hint">{hint}</span>
    </span>
  );
}
