// Parked by betterment C8 (one Talk rule): Speak's Talk is never dimmed while
// speech is not set up; the press opens the setup in place
// (web/src/desk/components/Talk.tsx). Kept here, not deleted. Not imported.
import { Button } from "../../../../components/signal/Signal";
import { SYSTEM } from "../../../../desk/systemSprites";

/** Talk while speech is not set up: the same key, dimmed, with its reason. */
export function TalkWaiting() {
  return (
    <Button
      variant="chrome"
      className="desk-mic gadget-transport-key is-unsupported speak-talk-waiting"
      disabled
      title="Set up speech first"
      aria-label="Talk · Set up speech first"
      data-testid="speak-talk-waiting"
    >
      <span className="gadget-transport-glyph" aria-hidden="true">
        <img src={SYSTEM.micGlyph} alt="" width={16} height={16} className="desk-chrome-sprite" draggable={false} />
      </span>
      <span className="gadget-transport-word">Talk</span>
    </Button>
  );
}

