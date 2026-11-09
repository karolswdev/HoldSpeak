/** Betterment A3 — the one host of an automation's window. The old queue
 * view behind RAW is parked (desk/_parked/automations/WorkbenchWindow_20261108.tsx):
 * every automation run is a Program (#2033). */
import { AutomationWindow } from "./AutomationWindow";

export function AutomationHost({
  workbenchId,
  origin,
}: {
  workbenchId: string;
  origin?: { x: number; y: number } | null;
}) {
  return <AutomationWindow workbenchId={workbenchId} origin={origin} />;
}
