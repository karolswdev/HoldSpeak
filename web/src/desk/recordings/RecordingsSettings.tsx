/* Recordings (RECORDINGS-DESIGN-2026-10-28 §2.7): Settings ▸ Desk ▸
 * Recordings. One row: how long the hub keeps a recording and the space they
 * use, and Open folder (Finder). A recording older than the keep is parked
 * (`recordings/_parked/`), never deleted. */
import { useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { GadgetGroup, GadgetRow } from "../surface/gadgets";
import { openRecordingsFolder, readRecordings, sizeWords } from "./api";
import type { RecordingsPayload } from "./types";

export function RecordingsSettings() {
  const [payload, setPayload] = useState<RecordingsPayload | null>(null);
  const [opening, setOpening] = useState(false);
  useEffect(() => {
    let alive = true;
    void readRecordings().then((body) => { if (alive) setPayload(body); }).catch(() => undefined);
    return () => { alive = false; };
  }, []);
  const keep = payload?.usage.keep_days ?? 30;
  const used = payload?.usage.bytes ? ` · ${sizeWords(payload.usage.bytes)} used` : "";
  return (
    <GadgetGroup material="inset" label="Recordings">
      <GadgetRow label="Keep" fact={<span data-testid="settings-recordings-usage">{`${keep} days${used}`}</span>}>
        <Button
          variant="secondary"
          dense
          loading={opening}
          data-testid="settings-recordings-open-folder"
          title={payload?.folder || undefined}
          onClick={() => {
            setOpening(true);
            void openRecordingsFolder().catch(() => undefined).finally(() => setOpening(false));
          }}
        >
          Open folder
        </Button>
      </GadgetRow>
    </GadgetGroup>
  );
}
