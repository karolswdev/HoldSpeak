/** An automation's own window (`workbench:<id>`): the same native body the
 * Automations app shows in its pane (AutomationBody.tsx), in a desk window,
 * as ProgramWindow is for a Program. The old toolbar, list view and status
 * bar composition is gone: the mast carries the verbs, the plate the one
 * thing that matters now, the ledger the runs. */
import { useCallback, useState } from "react";
import { useDesk } from "../../store";
import { DeskWindowFrame } from "../DeskWindow";
import { AutomationBody } from "./AutomationBody";

/** The window opens large enough for the mast, the plate and the newest
 *  runs (RECIPE A3: at least 880 x 640 at 1440). */
export const AUTOMATION_WINDOW_SIZE = { w: 920, h: 680 } as const;

export function AutomationWindow({
  workbenchId,
  origin,
}: {
  workbenchId: string;
  origin?: { x: number; y: number } | null;
}) {
  const [name, setName] = useState("Automation");
  const onRead = useCallback((detail: { name?: string }) => setName(detail.name || "Automation"), []);
  return (
    <DeskWindowFrame
      id={`workbench:${workbenchId}`}
      glyph="⚒"
      label={name}
      kindWord="Automation"
      title={name}
      minW={480}
      minH={360}
      defaultW={AUTOMATION_WINDOW_SIZE.w}
      defaultH={AUTOMATION_WINDOW_SIZE.h}
      open
      origin={origin}
      onClose={() => useDesk.getState().closeWorkbenchWindow(workbenchId)}
      className="desk-pullout automation-window"
    >
      <div className="desk-surface-body surface-host-body automation-host" data-surface-host="automation" data-interior="editor">
        <AutomationBody workbenchId={workbenchId} onRead={onRead} />
      </div>
    </DeskWindowFrame>
  );
}
