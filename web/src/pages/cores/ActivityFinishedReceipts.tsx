import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import type { DeskProjection } from "../../desk/projections";
import { openSurface } from "../../desk/shell";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { SurfaceRow, SurfaceRows, SurfaceSection, SurfaceState } from "../../desk/surface/Surface";
import { EgressChip } from "../../desk/surface/gadgets";
import { deSnake, wireDayClock } from "../../desk/surface/format";
import { egressForEvent, receiptLabel } from "../../desk/surface/egress";
import { ActionNotice } from "../../desk/surface/patterns/ActionNotice";

type ReceiptPage = { offset: number; limit: number; total: number; has_more: boolean };
type ReceiptRead = { projections: DeskProjection[]; page: ReceiptPage };
const EMPTY_PAGE: ReceiptPage = { offset: 0, limit: 50, total: 0, has_more: false };

/** Only these exact source doors have a current canonical application. A
 * projection's event/source id is not, by itself, a desk primitive reference. */
function receiptDoor(row: DeskProjection): { key: string; scope?: string } | null {
  if (row.detail_url === "/cadence") return { key: "configure-cadence" };
  if (!row.detail_url.startsWith("/history?") || row.detail_url.includes("#")) return null;
  const params = new URLSearchParams(row.detail_url.slice("/history?".length));
  const meeting = params.get("meeting");
  if (params.size !== 1 || !meeting || row.subject_ref !== `meeting:${meeting}`) return null;
  return { key: "review-meetings", scope: row.subject_ref };
}

function receiptEgress(row: DeskProjection) {
  const destination = row.actual_destination ?? "";
  const local = ["", "this_machine", "this_device", "same_device", "local", "LOCAL", "configured_inference_target", "active_app"].includes(destination)
    || row.source_kind === "dictation_journal" || row.source_kind === "steering_audit";
  return egressForEvent({ origin: row.origin, caller: row.caller, host: local ? "" : destination });
}

/** Activity owns this bounded read and its paging. The shared projections
 * store keeps its query, kind, selection and pages for every other face. */
export function ActivityFinishedReceipts({ query }: { query: string }) {
  const needle = query.trim();
  const [rows, setRows] = useState<DeskProjection[]>([]);
  const [page, setPage] = useState(EMPTY_PAGE);
  const [loadedQuery, setLoadedQuery] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [failedOffset, setFailedOffset] = useState(0);
  const [unavailable, setUnavailable] = useState<Set<string>>(() => new Set());
  const generation = useRef(0);
  const latestQuery = useRef(needle);
  latestQuery.current = needle;
  const activeRequest = useRef<AbortController | null>(null);

  const read = useCallback(async (offset = 0, quiet = false) => {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    const request = ++generation.current;
    setBusy(true);
    if (!quiet) {
      setLoading(true);
      setError(false);
    }
    const params = new URLSearchParams({ kind: "receipt", attention_state: "resolved", offset: String(offset), limit: "50" });
    if (needle) params.set("q", needle);
    const current = () => request === generation.current && latestQuery.current === needle;
    try {
      const body = await apiFetch<ReceiptRead>(`/api/desk/projections?${params}`, { method: "GET", signal: controller.signal });
      if (!current()) return;
      setRows((previous) => offset === 0 ? body.projections : [...new Map([...previous, ...body.projections].map((row) => [row.id, row])).values()]);
      setPage(body.page);
      setLoadedQuery(needle);
      setError(false);
    } catch {
      if (!current()) return;
      setError(true);
      setFailedOffset(offset);
    } finally {
      if (current()) {
        setBusy(false);
        setLoading(false);
      }
    }
  }, [needle]);

  useEffect(() => {
    void read();
    return () => {
      generation.current += 1;
      activeRequest.current?.abort();
    };
  }, [read]);
  useOnDeskChanged(() => void read(0, true));

  const visible = rows.filter((row) => !needle || [row.subject_label, row.title, row.summary, row.reason_code, row.outcome].join(" ").toLowerCase().includes(needle.toLowerCase()));
  const openReceipt = (row: DeskProjection) => {
    const door = receiptDoor(row);
    try {
      if (door && openSurface(door.key, door.scope)) return;
    } catch {
      // The exact source remains here; never navigate to a generic fallback.
    }
    setUnavailable((previous) => new Set(previous).add(row.id));
  };

  return <SurfaceSection label="Finished" data-testid="activity-finished">
    {error ? <ActionNotice tone="warn" role="alert" action={busy ? undefined : { label: "Retry", onClick: () => void read(failedOffset) }}>
      {rows.length ? "Finished read failed · Shown receipts kept · Retry" : "Finished read failed · Records unchanged · Retry"}
    </ActionNotice> : null}
    {(error || loading) && visible.length > 0 ? <span className="surface-token">Last read</span> : null}
    {loading && visible.length === 0 ? <SurfaceState loading/> : null}
    {!loading && !error && visible.length === 0 ? <SurfaceState empty emptyLabel={needle ? "No matching receipts" : "No finished receipts"}/> : null}
    <SurfaceRows>{visible.map((row) => {
      const title = row.source_kind === "pipeline_event" ? receiptLabel({ title: deSnake(row.title) }) : row.title;
      const door = receiptDoor(row);
      const egress = receiptEgress(row);
      return <SurfaceRow key={row.id} id={`activity-receipt-${row.id}`} title={title}
        detail={[wireDayClock(row.timestamp), row.subject_label].filter(Boolean).join(" · ")}>
        <div className="surface-actions">
          <span className="gadget-chip">{deSnake(row.outcome)}</span>
          <EgressChip label={egress.label} scope={egress.scope}/>
          {door && !unavailable.has(row.id) ? <Button dense aria-label={`Open receipt: ${title}`} onClick={() => openReceipt(row)}>Open receipt</Button> : <span className="surface-token">Receipt view unavailable</span>}
        </div>
      </SurfaceRow>;
    })}</SurfaceRows>
    {loadedQuery === needle && page.has_more ? <Button dense variant="ghost" disabled={busy} onClick={() => void read(page.offset + page.limit)}>Load more</Button> : null}
  </SurfaceSection>;
}
