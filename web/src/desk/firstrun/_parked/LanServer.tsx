/* PHILO-15 10 (B09): "Use a server on my network" on first run.
 *
 * The Local AI card had one verb, a 2.9 GB download. An owner with a model
 * server on his network had no way to name it here. This row is the
 * Concierge's own add-engine row (address + key, Check, Use this for
 * summaries), composed on the card: one component, two faces. */
import { useEffect, useRef } from "react";
import { AddEngineRow } from "../../features/concierge/ConciergeCore";
import {
  receiptLine,
  useConciergeController,
} from "../../features/concierge/useConciergeController";
import { Receipt } from "../surface";

export interface LanUsed {
  engine: string;
  host: string;
}

export function LanServerRow({ onUsed }: { onUsed: (used: LanUsed) => void }) {
  const ctrl = useConciergeController();
  const opened = useRef(false);
  useEffect(() => {
    if (opened.current) return;
    opened.current = true;
    ctrl.addEngine();
  }, [ctrl]);
  const receipt = ctrl.applyReceipt;
  useEffect(() => {
    if (receipt?.kind === "summaries") onUsed({ engine: receipt.engine, host: receipt.host });
  }, [receipt, onUsed]);
  if (receipt?.kind === "summaries") {
    return (
      <div className="firstrun-lan" data-testid="firstrun-lan-receipt">
        <Receipt status="ok" label={receiptLine(receipt)} />
      </div>
    );
  }
  return (
    <div className="firstrun-lan" data-testid="firstrun-lan">
      {ctrl.addEngineOpen ? <AddEngineRow ctrl={ctrl} lead={ctrl.addEngineState === "READY"} /> : null}
    </div>
  );
}
