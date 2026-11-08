// PARKED 2026-11-08 (R1 "the brief", owner: the Room's Now face "looks like
// shit"): the "Update" chips block left the Now face. Its words are the Now
// status bar's (core/Cadence.tsx); a press there opens the automation. Its
// imports point at ../core/ paths as they were; not compiled (tsconfig
// excludes _parked).
// The update schedule row: when the project update runs, with which engine,
// its latest result and Every Friday at 15:00.
import { useState } from "react";
import { SurfaceSection, SurfaceState } from "../../../desk/surface";
import { Token } from "../../../desk/surface/Token";
import { useDesk } from "../../../desk/store";
import { readableError } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import type { RoomSnapshot } from "../model";
import { enableFridayUpdate } from "../update/api";
import type { useUpdateController } from "../update/useUpdateController";

export function UpdateLine({ room, updateCtrl, onReload }: {
  room: RoomSnapshot;
  updateCtrl: ReturnType<typeof useUpdateController>;
  onReload: () => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState("");
  if (room.updates.state !== "ok" || !room.updates.automation) return null;
  const automation = room.updates.automation;
  const latestResult = automation.latestResult;
  const hasNew = Boolean(latestResult?.new);
  const enableFriday = async () => {
    if (busy) return;
    setBusy(true);
    setFailure("");
    try {
      await enableFridayUpdate(automation.id);
      await onReload();
    } catch (reason) {
      setFailure(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  const openAutomation = () => useDesk.getState().openWorkbenchWindow(automation.id);
  const openResult = () => {
    if (latestResult?.updateId) {
      void updateCtrl.openAutomationResult(latestResult);
      return;
    }
    // Legacy artifacts have no project-update link. Open the ordinary
    // Automation result surface rather than guessing at an owner draft.
    openAutomation();
  };
  const when = automation.scheduleEnabled ? "Fridays 15:00" : "Only when pressed";
  const withEngine = automation.engineLabel;
  return (
    <SurfaceSection label="Update" data-testid="room-update-line">
      <div className="room-update-line">
        <Button dense variant="ghost" onClick={openAutomation} data-testid="room-update-when">{when}</Button>
        <Button dense variant="ghost" onClick={openAutomation} data-testid="room-update-with">{withEngine}</Button>
        {hasNew ? <Token className="surface-token" data-tone="ok" data-testid="room-update-new">NEW</Token> : null}
        <Button dense variant="ghost" onClick={openResult} data-testid="room-update-open">
          {latestResult?.updateId ? "Open latest" : "Open automation"}
        </Button>
        {!automation.scheduleEnabled ? (
          <Button dense variant="ghost" loading={busy} onClick={() => void enableFriday()} data-testid="room-update-friday">
            Every Friday at 15:00
          </Button>
        ) : null}
      </div>
      {failure ? <SurfaceState error={failure} onRetry={() => void enableFriday()} /> : null}
    </SurfaceSection>
  );
}
