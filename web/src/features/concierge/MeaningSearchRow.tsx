// Meaning search: one row in THE SET. OFF / DOWNLOADING n% / INDEXING n of m / ON,
// and one verb (Turn on / Turn off). Composes the species THE SET already
// uses: SurfaceLedgerRow, StateChip, EgressChip, the library Button.
// Server truth: GET /api/memory/meaning-search (MeaningSearchService.status).

import { useCallback, useEffect, useRef, useState } from "react";
import { SurfaceLedgerRow, StateChip, EgressChip } from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { GROUP_GLYPHS, humanSize } from "./useConciergeController";

export interface MeaningSearchStatus {
  state: "off" | "downloading" | "indexing" | "on";
  percent: number;
  indexed: number;
  total: number;
  error: string;
  model: { label: string; size_bytes: number; on_device: boolean; source: string };
  egress: { destination: string; what: string } | null;
}

const PATH = "/api/memory/meaning-search";
const BUSY_POLL_MS = 1000;

export function meaningSearchChip(status: MeaningSearchStatus) {
  if (status.state === "on") return <StateChip state="success" label="ON" icon="●" />;
  if (status.state === "downloading")
    return <StateChip state="working" label={`DOWNLOADING ${status.percent}%`} icon="○" />;
  if (status.state === "indexing")
    return <StateChip state="working" label={`INDEXING ${status.indexed} OF ${status.total}`} icon="○" />;
  return <StateChip state="idle" label="OFF" />;
}

export function MeaningSearchRow() {
  const [status, setStatus] = useState<MeaningSearchStatus | null>(null);
  const [pressing, setPressing] = useState(false);
  const alive = useRef(true);

  const read = useCallback(async () => {
    try {
      const next = await apiFetch<MeaningSearchStatus>(PATH);
      if (alive.current && next && typeof next.state === "string") setStatus(next);
    } catch {
      /* No status read: the row draws nothing. It never guesses a state. */
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    void read();
    return () => { alive.current = false; };
  }, [read]);

  const busy = status?.state === "downloading" || status?.state === "indexing";
  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(() => { void read(); }, BUSY_POLL_MS);
    return () => window.clearInterval(timer);
  }, [busy, read]);

  const press = useCallback(async (verb: "turn-on" | "turn-off") => {
    setPressing(true);
    try {
      const next = await apiFetch<MeaningSearchStatus>(`${PATH}/${verb}`, { method: "POST" });
      if (alive.current && next && typeof next.state === "string") setStatus(next);
    } catch {
      await read();
    } finally {
      if (alive.current) setPressing(false);
    }
  }, [read]);

  if (!status) return null;
  const off = status.state === "off";
  const leaves = status.state === "downloading" || (off && status.egress !== null);
  const size = humanSize(status.model.size_bytes);

  return (
    <SurfaceLedgerRow
      lead={<span className="concierge-group-glyph">{GROUP_GLYPHS.background}</span>}
      primary={<span className="concierge-group-name">Meaning search</span>}
      cells={
        <span className="concierge-set-cells">
          <span className="concierge-cloud-actions">
            <Button
              dense
              variant={off ? "secondary" : "ghost"}
              loading={pressing}
              disabled={pressing}
              onClick={(e: React.MouseEvent) => { e.stopPropagation(); void press(off ? "turn-on" : "turn-off"); }}
              data-testid="meaning-search-verb"
            >
              {off ? "Turn on" : "Turn off"}
            </Button>
          </span>
          <span className="concierge-set-state" data-testid="meaning-search-state" data-state={status.state}>
            {meaningSearchChip(status)}
          </span>
          <span className="concierge-set-line2">
            {/* One short line at 393: the model name, or what the press downloads. */}
            {!leaves ? <span className="concierge-token">{status.model.label}</span> : null}
            {leaves && size ? <span className="concierge-token">{size}</span> : null}
            {off && leaves ? <span className="concierge-token">DOWNLOAD</span> : null}
            {leaves ? (
              <EgressChip
                label={status.model.source.toUpperCase()}
                scope="cloud"
                title={`Turn on downloads the model file from ${status.model.source}`}
              />
            ) : (
              <EgressChip label="THIS DEVICE" scope="local" />
            )}
            {status.error ? (
              <span className="concierge-add-engine-reason" role="alert" data-testid="meaning-search-error">
                {status.error}
              </span>
            ) : null}
          </span>
        </span>
      }
      expands={false}
      wrap
      data-testid="concierge-meaning-search"
    />
  );
}
