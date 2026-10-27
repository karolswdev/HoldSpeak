// PARKED 2026-10-26 (floor lane). Owner, on his live desk: "who thought it was
// a good idea to have that lame ass 'talk' shit (bottom left, above the dock)
// and the trash can being there". Not mounted, not imported. Kept so a later
// ruling can bring either back.
//
// 1. The floor Talk orb (Astra's P3 on #939): Screen.tsx drew it at the
//    screen's foot-left at 1440. Speak is now the Dock's Speak tile, the menu
//    bar, ⌥R and ⌘K; a focused field keeps its own mic. Its styles stay in
//    components/talk.css and screen/screen.css (`.desk-screen-talk`).
// 2. The floor Archive icon (compose.ts, role "parked"): layout.ts put it at
//    the bottom right, where the Mac keeps the Trash. Go ▸ Archive
//    (`desk.open-archive`) and ⌘K "Open Archive" open the same window
//    (drawer/ParkedDrawer.tsx).
import { Talk } from "../../components/Talk";
import { openNewThought } from "../../newThought";
import { objectSprite } from "../../surface";
import type { ScreenObject } from "../compose";

export function ParkedFloorTalk() {
  return (
    <span className="desk-screen-talk arrival-capture-talk" data-testid="desk-screen-talk">
      {/* Betterment C8: the one Talk rule (desk/components/Talk.tsx). */}
      <Talk onText={(text) => void openNewThought(text)} label="Talk" setupTestId="desk-screen-talk-setup" />
    </span>
  );
}

export function parkedArchiveFloorObject(): ScreenObject {
  return {
    key: "drawer:parked",
    role: "parked",
    kind: "parked",
    name: "Archive",
    sprite: objectSprite("parked", "parked", "rest", 64),
    spriteSelected: objectSprite("parked", "parked", "sel", 64),
    target: { type: "parked" },
  };
}
