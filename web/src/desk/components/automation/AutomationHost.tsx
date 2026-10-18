/** Betterment A3 — the one host of an automation's window. It is the
 * automation window; for an old queue automation, RAW swaps in the parked
 * queue view (WorkbenchWindow, kept whole, never deleted). */
import { lazy, Suspense, useState } from "react";
import { AutomationWindow } from "./AutomationWindow";

const ParkedQueueWindow = lazy(() =>
  import("../WorkbenchWindow").then((module) => ({ default: module.WorkbenchWindow })),
);

export function AutomationHost({
  workbenchId,
  origin,
}: {
  workbenchId: string;
  origin?: { x: number; y: number } | null;
}) {
  const [raw, setRaw] = useState(false);
  if (raw) {
    return (
      <Suspense fallback={null}>
        <ParkedQueueWindow workbenchId={workbenchId} origin={origin ?? null} />
      </Suspense>
    );
  }
  return <AutomationWindow workbenchId={workbenchId} origin={origin} onRaw={() => setRaw(true)} />;
}
