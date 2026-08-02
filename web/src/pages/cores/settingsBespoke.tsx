// HS-101 round 5 / HS-111-01 — bespoke configuration components. A
// complex idea gets a component shaped like the idea, on the gadget kit:
//  - HotkeyCapture: a key is pressed, not typed — mapped to exactly the
//    key names the hub accepts (holdspeak/hotkey.py). Listening is
//    inverted video with a block cursor; a refusal lands in the Prefs
//    status bar (never row prose).
// HS-112-01 — RuntimeDestination died: endpoint/model identity lives in
// the Prefs `models` module (`settingsModels.tsx`), the one dial.
import { useEffect, useState } from "react";
import { GadgetGroup, GadgetRow } from "../../desk/surface/gadgets";

/* ── the hotkey: pressed, not typed ────────────────────────────── */

// The hub's accepted set (holdspeak/hotkey.py _key_name_map) — the
// capture can only ever write a name the listener understands.
const CODE_TO_NAME: Record<string, string> = {
  AltRight: "alt_r",
  AltLeft: "alt_l",
  ControlRight: "ctrl_r",
  ControlLeft: "ctrl_l",
  MetaRight: "cmd_r",
  MetaLeft: "cmd_l",
  ShiftRight: "shift_r",
  ShiftLeft: "shift_l",
  CapsLock: "caps_lock",
};
for (let n = 1; n <= 12; n += 1) CODE_TO_NAME[`F${n}`] = `f${n}`;

const NAME_TO_DISPLAY: Record<string, string> = {
  alt_r: "⌥R",
  alt_l: "⌥L",
  ctrl_r: "⌃R",
  ctrl_l: "⌃L",
  cmd_r: "⌘R",
  cmd_l: "⌘L",
  shift_r: "⇧R",
  shift_l: "⇧L",
  caps_lock: "⇪",
};
for (let n = 1; n <= 12; n += 1) NAME_TO_DISPLAY[`f${n}`] = `F${n}`;

export function HotkeyCapture({
  value,
  onCommit,
  onRefuse,
}: {
  value: Record<string, unknown>;
  onCommit: (next: { key: string; display: string }) => void;
  /** The refusal (names the accepted set) — lands in the status bar. */
  onRefuse?: (refusal: string) => void;
}) {
  const [listening, setListening] = useState(false);
  useEffect(() => {
    if (!listening) return;
    const onKey = (event: KeyboardEvent) => {
      event.preventDefault();
      event.stopPropagation();
      if (event.key === "Escape") {
        setListening(false);
        return;
      }
      const name = CODE_TO_NAME[event.code];
      if (!name) {
        onRefuse?.(
          `${event.code} can't be a hold key: use a modifier (⌥ ⌃ ⌘ ⇧, left or right), ⇪, or F1–F12`,
        );
        return;
      }
      setListening(false);
      onCommit({ key: name, display: NAME_TO_DISPLAY[name] ?? name });
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [listening, onCommit, onRefuse]);
  const current = String(value.display || value.key || "unset");
  return (
    <GadgetGroup>
      <GadgetRow label="Push-to-talk key" fact="hold · release types">
        <button
          type="button"
          className={"gadget-keycap" + (listening ? " is-listening" : "")}
          aria-label={
            listening
              ? "Listening for the hold key. Esc cancels."
              : `Push-to-talk key: ${current}. Press to change.`
          }
          onClick={() => {
            onRefuse?.("");
            setListening((v) => !v);
          }}
        >
          {listening ? "" : current}
        </button>
      </GadgetRow>
    </GadgetGroup>
  );
}
