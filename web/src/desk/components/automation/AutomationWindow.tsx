/** One automation in its own titled frame; the kit owns its bounded panes. */
import "./automation.css";
import { useCallback, useState } from "react";
import { BackSlotContext, type WindowBack } from "../../surface";
import { useDesk } from "../../store";
import { DeskWindowFrame } from "../DeskWindow";
import { AutomationBody } from "./AutomationBody";

/** The object fits the standard object-window pose. */
export const AUTOMATION_WINDOW_SIZE = { w: 900, h: 600 } as const;

export function AutomationWindow({
  workbenchId,
  origin,
}: {
  workbenchId: string;
  origin?: { x: number; y: number } | null;
}) {
  const [name, setName] = useState("Automation");
  const [back, setBack] = useState<WindowBack | null>(null);
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
      onBack={back?.onBack}
      backTestId={back?.testId}
      backLabel={back?.label}
      onClose={() => useDesk.getState().closeWorkbenchWindow(workbenchId)}
      className="desk-pullout automation-window"
    >
      <div className="desk-surface-body surface-host-body automation-host" data-surface-host="automation" data-interior="list">
        <BackSlotContext.Provider value={setBack}><AutomationBody key={workbenchId} workbenchId={workbenchId} onRead={onRead} /></BackSlotContext.Provider>
      </div>
    </DeskWindowFrame>
  );
}
