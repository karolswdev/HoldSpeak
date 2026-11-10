/** The desktop and phone share one Help menu and the registry's feedback verb. */
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { useFrontWindowId } from "../components/window/windowRegistry";
import { useWindowWalk } from "../components/window/listMenu";
import { useUiFeedbackState } from "../feedback/runtime";
import { verbById } from "../verbRegistry";
import { appWalk, startAppWalk } from "./appWalks";
import { guideVoice, setGuideVoice, subscribeGuideVoice } from "./voice";
export function HelpMenu({ compact = false }: { compact?: boolean }) {
  const front = useFrontWindowId();
  const declared = useWindowWalk(front) ?? front;
  const script = appWalk(declared);
  const feedback = useUiFeedbackState();
  const [voice, setVoice] = useState(guideVoice);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLButtonElement>(null);
  useEffect(() => subscribeGuideVoice(() => setVoice(guideVoice())), []);
  const rect = ref.current?.getBoundingClientRect();
  const give = verbById("desk.give-feedback");
  const entries: WorkMenuEntry[] = [
    ...(script
      ? [
          {
            type: "item" as const,
            id: "show-me",
            label: `Show me ${script.title}`,
            keycap: "?",
            onSelect: () => {
              void startAppWalk(declared!, front);
            },
          },
        ]
      : []),
    ...(feedback.enabled && give
      ? [
          {
            type: "item" as const,
            id: give.id,
            label: give.label as string,
            onSelect: () => give.run({ selectedRef: null }),
          },
        ]
      : []),
    {
      type: "item",
      id: "guide-voice",
      label: "Speak the guide",
      checked: voice,
      onSelect: () => setGuideVoice(!voice),
    },
  ];
  return (
    <span className="desk-verbbar-item" data-menu-id="help">
      <Button
        ref={ref}
        variant="chrome"
        className={`desk-verbbar-title${open ? " on" : ""}`}
        aria-label="Help"
        aria-haspopup="menu"
        aria-expanded={open}
        data-testid="desk-help"
        onClick={() => setOpen(!open)}
      >
        {compact ? "?" : "Help"}
      </Button>
      {open && rect ? (
        <WorkMenu
          label="Help menu"
          className="desk-verbbar-menu"
          x={rect.left}
          y={rect.bottom}
          entries={entries}
          autoFocus
          opener={ref.current}
          returnFocus={() => ref.current?.focus()}
          onClose={() => setOpen(false)}
        />
      ) : null}
    </span>
  );
}
