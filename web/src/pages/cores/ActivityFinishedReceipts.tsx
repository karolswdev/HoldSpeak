// Window grammar (2026-10-24): Activity's list view. One dense ObjectList:
// What (the object glyph of the thing acted on, the receipt's words), Who
// (You, or the REMOTE egress chip on a remote row only), When (relative,
// tabular), Outcome (a dot and a word). A press selects the row; Enter or a
// double press opens its receipt. The selection's Open receipt sits at the
// status bar's right; the status bar says the count in warm words.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import type { DeskProjection } from "../../desk/projections";
import { openSurface } from "../../desk/shell";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { SurfaceState } from "../../desk/surface/Surface";
import { deSnake } from "../../desk/surface/format";
import { receiptLabel } from "../../desk/surface/egress";
import { ActionNotice } from "../../desk/surface/patterns/ActionNotice";
import { StatusBar, ToolGlyph, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { ObjectList, type ObjectListRow, type ObjectListSort } from "../../desk/surface/objects/ObjectList";
import type { ObjectTone } from "../../desk/surface/objects/kinds";
import { SYSTEM } from "../../desk/systemSprites";

type ReceiptPage = { offset: number; limit: number; total: number; has_more: boolean };
type ReceiptRead = { projections: DeskProjection[]; page: ReceiptPage };
const EMPTY_PAGE: ReceiptPage = { offset: 0, limit: 50, total: 0, has_more: false };

/** One activity record (the watched pages), drawn in the same list. */
export type ActivityRecordRow = Record<string, unknown>;

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

/** The object the receipt acted on, for its row glyph. */
function subjectKind(row: DeskProjection): string {
  const ref = String(row.subject_ref ?? "");
  const head = ref.split(":", 1)[0];
  if (head === "meeting") return "meeting";
  if (head === "project") return "project";
  if (head === "note" || head === "thought") return "note";
  if (head === "agent" || head === "session" || head === "launch") return "agent";
  if (head === "person" || head === "relationship") return "person";
  if (head === "decision") return "decision";
  if (head === "action_item") return "action";
  if (head === "workbench") return "workbench";
  if (head === "service") return "workbench";
  return "artifact";
}

/** A receipt's outcome as a dot and a word (sentence case). */
function outcomeState(outcome: string): { label: string; tone: ObjectTone } {
  const word = deSnake(outcome || "").trim();
  const lower = word.toLowerCase();
  const tone: ObjectTone = /fail|error|refus|denied|blocked/.test(lower) ? "fail"
    : /warn|partial|skip|held/.test(lower) ? "warn"
      : /complet|final|done|sent|saved|ok|ran|success/.test(lower) ? "ok"
        : "info";
  return { label: lower ? lower.charAt(0).toUpperCase() + lower.slice(1) : "Done", tone };
}

/** `Just now`, `4 min ago`, `16:22` today, `Oct 22` before. */
export function relativeWhen(iso: unknown, now: Date = new Date()): string {
  const at = new Date(String(iso ?? ""));
  if (Number.isNaN(at.getTime())) return "";
  const minutes = Math.floor((now.getTime() - at.getTime()) / 60000);
  if (minutes >= 0 && minutes < 1) return "Just now";
  if (minutes >= 0 && minutes < 60) return `${minutes} min ago`;
  if (at.toDateString() === now.toDateString()) {
    return `${String(at.getHours()).padStart(2, "0")}:${String(at.getMinutes()).padStart(2, "0")}`;
  }
  return at.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

const COLUMNS = [
  { key: "name", word: "What" },
  { key: "who", word: "Who", track: "minmax(96px, 0.5fr)" },
  { key: "when", word: "When", track: "96px" },
  { key: "state", word: "Outcome", track: "minmax(110px, 0.4fr)" },
] as const;

/** Activity owns this bounded read and its paging. The shared projections
 * store keeps its query, kind, selection and pages for every other face. */
export function ActivityFinishedReceipts({ query, records = [] }: {
  query: string;
  /** The watched pages (Activity ▸ Records), drawn in the same list. */
  records?: readonly ActivityRecordRow[];
}) {
  const needle = query.trim();
  const [rows, setRows] = useState<DeskProjection[]>([]);
  const [page, setPage] = useState(EMPTY_PAGE);
  const [loadedQuery, setLoadedQuery] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [failedOffset, setFailedOffset] = useState(0);
  const [unavailable, setUnavailable] = useState<Set<string>>(() => new Set());
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "when", dir: "desc" });
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
  const titleOf = (row: DeskProjection) => row.source_kind === "pipeline_event" ? receiptLabel({ title: deSnake(row.title) }) : row.title;
  const openReceipt = (row: DeskProjection) => {
    const door = receiptDoor(row);
    try {
      if (door && openSurface(door.key, door.scope)) return;
    } catch {
      // The exact source remains here; never navigate to a generic fallback.
    }
    setUnavailable((previous) => new Set(previous).add(row.id));
  };

  const now = new Date();
  const byId = new Map(visible.map((row) => [row.id, row]));
  const listRows: ObjectListRow[] = (() => {
    const out: ObjectListRow[] = visible.map((row) => {
      const title = titleOf(row);
      // Owner ruling 2026-10-25: who did it in plain words; no address and
      // no scope word on the row (a remote caller's IP stays off the row).
      const fromElsewhere = row.origin === "remote" && Boolean(row.caller);
      const who: ReactNode = (
        <span className="activity-who">
          <span>{fromElsewhere ? "Another device" : "You"}</span>
        </span>
      );
      const at = new Date(row.timestamp).getTime();
      return {
        id: row.id,
        kind: subjectKind(row),
        name: row.subject_label ? `${title} · ${row.subject_label}` : title,
        when: relativeWhen(row.timestamp, now),
        whenSort: Number.isFinite(at) ? at : 0,
        cells: { who },
        sortValues: { who: fromElsewhere ? "Another device" : "You" },
        state: outcomeState(row.outcome),
        nameTestId: `activity-receipt-name-${row.id}`,
      };
    });
    for (const [index, record] of records.entries()) {
      const id = `record:${String(record.id ?? index)}`;
      const at = new Date(String(record.occurred_at ?? "")).getTime();
      const name = String(record.title ?? record.name ?? record.domain ?? record.url ?? "Page");
      if (needle && !JSON.stringify(record).toLowerCase().includes(needle.toLowerCase())) continue;
      out.push({
        id,
        kind: "artifact",
        name,
        when: relativeWhen(record.occurred_at, now),
        whenSort: Number.isFinite(at) ? at : 0,
        cells: { who: <span className="activity-who"><span>You</span></span> },
        sortValues: { who: "You" },
      });
    }
    return out;
  })();

  const selected = selectedId ? byId.get(selectedId) ?? null : null;
  const selectedTitle = selected ? titleOf(selected) : "";
  const door = selected ? receiptDoor(selected) : null;
  const today = visible.filter((row) => new Date(row.timestamp).toDateString() === now.toDateString()).length;
  const items: StatusBarItem[] = [
    { key: "today", text: countWords(today, "today", "today"), testId: "activity-today" },
    (error || loading) && visible.length > 0 ? { key: "last", lamp: "warn", text: "Last read" } : null,
  ].filter(Boolean) as StatusBarItem[];
  const verbs = (
    <>
      {selected ? (
        door && !unavailable.has(selected.id) ? (
          <Button dense variant="secondary" aria-label={`Open receipt: ${selectedTitle}`}
            data-testid="activity-open-receipt" onClick={() => openReceipt(selected)}>
            <ToolGlyph kind="open" />
            Open receipt
          </Button>
        ) : <span className="activity-unavailable" data-testid="activity-receipt-unavailable">Receipt view unavailable</span>
      ) : null}
      {loadedQuery === needle && page.has_more ? (
        <Button dense variant="ghost" disabled={busy} onClick={() => void read(page.offset + page.limit)}>Load more</Button>
      ) : null}
    </>
  );

  return (
    <div className="activity-list" data-testid="activity-finished">
      {error ? <ActionNotice tone="warn" role="alert" action={busy ? undefined : { label: "Retry", onClick: () => void read(failedOffset) }}>
        {rows.length ? "Finished read failed · Shown receipts kept · Retry" : "Finished read failed · Records unchanged · Retry"}
      </ActionNotice> : null}
      {loading && listRows.length === 0 ? <SurfaceState loading/> : null}
      {!loading && !error && listRows.length === 0
        ? <SurfaceState empty emptyImage={SYSTEM.dockDeskMemory} emptyLabel={needle ? "No matching receipts" : "No finished receipts"}/>
        : null}
      {listRows.length > 0 ? (
        <ObjectList
          label="Activity"
          density="dense"
          rows={listRows}
          columns={COLUMNS}
          sort={sort}
          onSort={(key: string) => setSort((current) => ({
            key,
            dir: current.key === key ? (current.dir === "asc" ? "desc" : "asc") : key === "when" ? "desc" : "asc",
          }))}
          selectedId={selectedId}
          onSelect={setSelectedId}
          onOpen={(id) => {
            const row = byId.get(id);
            if (row) openReceipt(row);
          }}
          rowProps={(row) => row.id.startsWith("record:")
            ? { id: `activity-${row.id.replace(":", "-")}` }
            : { id: `activity-receipt-${row.id}` }}
        />
      ) : null}
      <StatusBar data-testid="activity-status" items={items} verbs={verbs} />
    </div>
  );
}
