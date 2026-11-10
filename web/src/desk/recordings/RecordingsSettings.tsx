/* One storage ledger, shared by Recordings and Settings. */
import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { readableError } from "../../lib/api";
import { openRecordingsFolder, readRecordings, sizeWords } from "./api";
import type { RecordingsPayload } from "./types";
import "./recordings.css";

export function RecordingsSettings({ payload: supplied }: { payload?: RecordingsPayload } = {}) {
  const [payload, setPayload] = useState<RecordingsPayload | null>(supplied ?? null);
  const [opening, setOpening] = useState(false);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState("");
  useEffect(() => {
    if (supplied) { setPayload(supplied); return; }
    let alive = true;
    void readRecordings().then((body) => { if (alive) setPayload(body); }).catch((reason) => { if (alive) setError(readableError(reason)); });
    return () => { alive = false; };
  }, [supplied]);
  return <section className="recordings-storage" aria-label="Recordings storage">
    <div className="recordings-storage-row"><span>Keep</span><span data-testid="settings-recordings-usage">{payload
      ? `${payload.usage.keep_days} days${payload.usage.bytes ? ` · ${sizeWords(payload.usage.bytes)} used` : ""}` : error || "Loading"}</span></div>
    <div className="recordings-storage-row"><span>{error || receipt || "Recordings folder"}</span>
      <Button dense loading={opening} data-testid="settings-recordings-open-folder" title={payload?.folder || undefined}
        onClick={() => { setOpening(true); setError(""); setReceipt(""); void openRecordingsFolder().then((answer) => {
          if (!answer.opened) throw new Error("The folder did not open"); setReceipt("Folder opened");
        }).catch((reason) => setError(readableError(reason))).finally(() => setOpening(false)); }}>Open folder</Button></div>
  </section>;
}
