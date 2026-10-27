import { wireDate } from "../../surface/format";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { holdObject, qualifiedRef } from "../../api";
import { decisionRecordSourceRef, openRef } from "../../openObject";
import { allObjects } from "../../world";
import { useDesk } from "../../store";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceState } from "../../surface/Surface";
import { countLabel } from "../../surface/count";
import { MicButton } from "../../surface";
import { StringGadget } from "../../surface/gadgets";
import { DecisionRecordSendSheet, DecisionRecordSendWells } from "../../documentSendsLazy";
import { spriteUrl } from "../../sprites";
import { openProjectRoom } from "../../shell";
import { Material } from "../../surface/Material";
import { FoldGadget, GadgetGroup, GadgetRow } from "../../surface/gadgets";
import { StateChip } from "../../surface";
import { CheckGadget } from "../../surface/gadgets";
import { Loading, StatusBar, ToolGlyph, Toolbar, countWords } from "../../surface/kit";
import { useWindowInterior } from "../../surface/interior";
import { useHasWindowBack, useWindowBack } from "../../surface/back";
import { useCompactViewport } from "../../useCompactViewport";
import { ObjectList, type ObjectListRow, type ObjectListSort } from "../../surface/objects/ObjectList";
import type { ObjectTone } from "../../surface/objects/kinds";
import "../attention-records.css";

type ReceiptSource = {
  source_type: string;
  source_ref: string;
  text?: string;
  speaker?: string;
  meeting_id?: string;
};

type ReceiptWork = { id: string; work_type: string; work_ref: string };
type ReceiptRevision = {
  id: string;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  created_at: string;
};

type Receipt = {
  id: string;
  /** W1-TRUTH: a Desk decision's title (the hub's `_decorate`); a meeting's
   *  decision has none. */
  title?: string | null;
  decision_text: string;
  rationale: string | null;
  alternatives: string | null;
  owner: string | null;
  review_date: string | null;
  lifecycle: string;
  status?: string | null;
  sources?: ReceiptSource[];
  work?: ReceiptWork[];
  revisions?: ReceiptRevision[];
  predecessor_id?: string | null;
  successor_id?: string | null;
  source_type?: string;
  source_id?: string;
  created_at?: string | null;
};

function receiptStatus(receipt: Receipt): "governing" | "superseded" | "related" {
  if (String(receipt.status ?? "").toLowerCase() === "proposed") return "related";
  if (receipt.lifecycle === "active") return "governing";
  if (receipt.lifecycle === "superseded") return "superseded";
  return "related";
}

/** PHILO-17: the plain word for a record's state (was `GOVERNING`). */
const RECEIPT_WORD = { governing: "CURRENT", superseded: "REPLACED", related: "RELATED" } as const;

/** PHILO-17: one decision on the desk (`GET /api/decisions?scope=all`): a
 *  meeting's decision names its meeting; a Desk decision names none. */
type DeskDecision = {
  source: "meeting" | "desk" | "record";
  id: string;
  /** W1-TRUTH: the row's name when the decision has a title. */
  title?: string | null;
  text: string;
  rationale?: string | null;
  decided_at?: string | null;
  lifecycle?: string | null;
  status?: string | null;
  meeting_id?: string | null;
  meeting_title?: string | null;
  record_id?: string | null;
};

/** The states in which a decision stands (an inclusion list: a disputed or
 *  an unknown state is not current). The server's `current=1` uses the same. */
const CURRENT = new Set(["recorded", "accepted", "active", "published"]);

/** The state word a row shows; empty when the decision stands. Its
 *  lifecycle is its record's when it has one (the ledger answers it). */
function stateWord(row: DeskDecision): string {
  if (String(row.status ?? "").toLowerCase() === "proposed") return "PROPOSED";
  const lifecycle = String(row.lifecycle ?? "").toLowerCase();
  if (CURRENT.has(lifecycle) || !lifecycle) return "";
  if (lifecycle === "superseded") return "REPLACED";
  if (lifecycle === "deprecated") return "RETIRED";
  return lifecycle.toUpperCase();
}

function fromReceipt(receipt: Receipt & { created_at?: string | null }): DeskDecision {
  return {
    source: "record", id: receipt.id, title: receipt.title ?? null, text: receipt.decision_text, rationale: receipt.rationale,
    decided_at: receipt.created_at ?? null, lifecycle: receipt.lifecycle, status: receipt.status, record_id: receipt.id,
  };
}

/** One page of the desk's decisions. */
const PAGE = 100;

/** A Desk decision opens its window; one the Desk did not load is held
 *  (read by its id) first, so the open is never dead. */
function openDeskDecision(id: string): void {
  const ref = qualifiedRef("decision", id);
  const open = () => openRef(`desk_decision:${id}`);
  const present = allObjects(useDesk.getState().items).some((o) => qualifiedRef(o.kind, o.id) === ref);
  if (present || !holdObject(ref)) { open(); return; }
  void useDesk.getState().refresh().then(open, open);
}

/** Window grammar: a decision's state as a dot and a word. Open: proposed,
 *  not decided yet. Accepted: it stands. Superseded: a newer one replaced
 *  it. W1-TRUTH: the same words as the decision's own window
 *  (DecisionPullout DECISION_STATES). */
function decisionState(row: DeskDecision): { word: string; tone: ObjectTone; rank: number } {
  const word = stateWord(row);
  if (word === "PROPOSED") return { word: "Open", tone: "ask", rank: 0 };
  if (!word) return { word: "Accepted", tone: "ok", rank: 1 };
  if (word === "REPLACED") return { word: "Superseded", tone: "info", rank: 2 };
  if (word === "RETIRED") return { word: "Retired", tone: "info", rank: 3 };
  return { word: word.charAt(0) + word.slice(1).toLowerCase(), tone: "warn", rank: 4 };
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** `Oct 24`: a list view's date in quiet sans. */
function dayWords(value: string | null | undefined): string {
  const date = value ? wireDate(value) : null;
  return date ? `${MONTHS[date.getMonth()]} ${date.getDate()}` : "";
}

const DECISION_SPRITE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/decision.png`;

const DECISION_COLUMNS = [
  { key: "when", word: "When", track: "88px" },
  { key: "where", word: "Where", track: "minmax(0, 0.7fr)" },
  { key: "state", word: "State", track: "124px" },
] as const;

/** `just now`, `4 min ago`, `3 h ago`, then the day (`Oct 24`). */
function sinceWord(at: Date, now: number = Date.now()): string {
  const minutes = Math.floor((now - at.getTime()) / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;
  if (minutes < 12 * 60) return `${Math.floor(minutes / 60)} h ago`;
  return `on ${MONTHS[at.getMonth()]} ${at.getDate()}`;
}

function humanDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = wireDate(value);
  return !date ? value : date.toLocaleDateString();
}

/** Every decision on the desk, with its date and its meeting; search in
 *  place; a row opens its record, its Desk window, or the decision itself. */
export function DecisionsView({
  initialQuery = "",
  initialWhyOnly = false,
  workRef,
  receiptId,
  decisionId,
  decisionNonce,
  windowed = false,
  recordIds,
  onBackToList,
}: {
  /** The Decisions window: only these records (`records:<id>,<id>`, the
   *  records that govern one piece of work), the first opened in the reader. */
  recordIds?: string;
  /** The Decisions window: the reader's ‹ Decisions also forgets the
   *  record the window was opened on (its scope), so a reload shows the list. */
  onBackToList?: () => void;
  /** Window grammar (the Decisions window): Toolbar [New decision] +
   *  search → the dense list view → the status bar. Today keeps its view. */
  windowed?: boolean;
  initialQuery?: string;
  /** The `Current only` filter (the navigation's `whyOnly`). */
  initialWhyOnly?: boolean;
  workRef?: string;
  receiptId?: string;
  /** PHILO-17: open this decision (a ledger row) in place, read by its id. */
  decisionId?: string;
  /** A new number per request: the same decision asked again opens again. */
  decisionNonce?: number;
}) {
  const openPullout = useDesk((state) => state.openPullout);
  const [query, setQuery] = useState(initialQuery);
  const [whyOnly, setWhyOnly] = useState(initialWhyOnly);
  const [results, setResults] = useState<DeskDecision[]>([]);
  const [total, setTotal] = useState(0);
  const [selected, setSelected] = useState<Receipt | null>(null);
  const [chosen, setChosen] = useState<DeskDecision | null>(null);
  const [loading, setLoading] = useState(true);
  const [more, setMore] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [requested, setRequested] = useState<{ kind: "record" | "decision"; id: string; label: string } | null>(null);
  const [detailError, setDetailError] = useState("");
  const detailReads = useRef(0);
  const [error, setError] = useState("");
  const [rowSelected, setRowSelected] = useState<string | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "when", dir: "desc" });
  const detailOpen = Boolean(chosen || selected || detailLoading || requested);
  // The record's reader runs edge to edge under its toolbar (it insets its
  // own words); a meeting's decision keeps the default inset.
  useWindowInterior(windowed ? (!detailOpen ? "list" : "editor") : null);
  const onlyRecords = (recordIds ?? "").split(",").map((id) => id.trim()).filter(Boolean);
  useEffect(() => () => { detailReads.current += 1; }, []);

  useEffect(() => {
    setQuery(initialQuery);
    setWhyOnly(initialWhyOnly);
  }, [initialQuery, initialWhyOnly]);

  // A work ref lists the records linked to that work; else the desk's
  // decisions, one page at a time, searched and filtered by the hub.
  const read = (offset: number, limit = PAGE): Promise<{ rows: DeskDecision[]; total: number }> => {
    if (onlyRecords.length) {
      // Only the records asked for, each read by its id; one that is gone is left out.
      return Promise.all(onlyRecords.map((id) => apiFetch<Receipt>(`/api/decision-records/${encodeURIComponent(id)}`)
        .then((receipt) => (receipt?.id ? fromReceipt(receipt) : null), () => null)))
        .then((found) => {
          const rows = found.filter((row): row is DeskDecision => Boolean(row))
            .filter((row) => !whyOnly || !stateWord(row))
            .filter((row) => !query.trim() || row.text.toLowerCase().includes(query.trim().toLowerCase()));
          return { rows: offset ? [] : rows, total: rows.length };
        });
    }
    const [workType, ...workRefParts] = workRef?.split(":") ?? [];
    const linkedWorkRef = workRefParts.join(":");
    if (workType && linkedWorkRef) {
      return apiFetch<Receipt[]>(
        `/api/decision-records/work/${encodeURIComponent(workType)}/${encodeURIComponent(linkedWorkRef)}`,
      ).then((receipts) => {
        const rows = (Array.isArray(receipts) ? receipts.map(fromReceipt) : [])
          .filter((row) => !whyOnly || !stateWord(row))
          .filter((row) => !query.trim() || row.text.toLowerCase().includes(query.trim().toLowerCase()));
        const count = rows.length;
        return { rows, total: count };
      });
    }
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (query.trim()) params.set("q", query.trim());
    return apiFetch<Receipt[]>(`/api/decision-records?${params}`)
      .then((records) => {
        // A pre-record hub (and the focused legacy harness) returns the
        // lifecycle envelope here. Keep its visible rows immediate.
        const legacyBody = records as unknown as { decisions?: DeskDecision[]; page?: { total?: number } };
        if (!Array.isArray(records) && Array.isArray(legacyBody?.decisions)) {
          const legacy = new URLSearchParams({ scope: "all", limit: String(limit), offset: String(offset) });
          if (query.trim()) legacy.set("q", query.trim());
          if (whyOnly) legacy.set("current", "true");
          const rows = legacyBody.decisions
            .filter((row) => !whyOnly || !stateWord(row))
            .filter((row) => !query.trim() || row.text.toLowerCase().includes(query.trim().toLowerCase()));
          return { rows, total: Number(legacyBody.page?.total ?? rows.length) };
        }
        // A detail-shaped compatibility answer is not the list transport.
        // Older test/hub adapters fall through to their ledger route; the
        // live canonical list has no expanded `sources` array here.
        if (!Array.isArray(records) || records.some((record) => Array.isArray(record.sources) || !record.source_type)) {
          throw new Error("Decisions not read. Saved decisions are unchanged. Retry.");
        }
        const rows = records.map(fromReceipt)
          .filter((row) => !whyOnly || !stateWord(row))
          .filter((row) => !query.trim() || row.text.toLowerCase().includes(query.trim().toLowerCase()));
        const count = rows.length;
        return { rows, total: count };
      })
      .catch(() => {
        // Compatibility read for a hub before the canonical list transport.
        const legacy = new URLSearchParams({ scope: "all", limit: String(limit), offset: String(offset) });
        if (query.trim()) legacy.set("q", query.trim());
        if (whyOnly) legacy.set("current", "true");
        return apiFetch<{ decisions?: DeskDecision[]; page?: { total?: number } }>(`/api/decisions?${legacy}`)
          .then((body) => {
            const rows = Array.isArray(body?.decisions) ? body.decisions : [];
            return { rows, total: Number(body?.page?.total ?? rows.length) };
          });
      });
  };
  // A decision made or changed in another window shows in this list. A quiet
  // re-read of what is shown: no loading state, and the last list stays when
  // it fails. Reads can answer out of order. Two rules decide which may land:
  // `query` -- a read made for an older search, filter or work ref never
  // lands; `order` -- of two reads for the same one, the one that started
  // later wins, and an earlier one that answers after it is dropped.
  const reads = useRef({ query: 0, started: 0, landed: 0 });
  const shown = useRef(0);
  shown.current = results.length;
  const beginRead = () => {
    const mine = { query: reads.current.query, order: ++reads.current.started };
    return () => {
      if (mine.query !== reads.current.query || mine.order < reads.current.landed) return false;
      reads.current.landed = mine.order;
      return true;
    };
  };
  useOnDeskChanged(() => {
    const lands = beginRead();
    void read(0, Math.min(500, Math.max(PAGE, shown.current)))
      .then(({ rows, total: all }) => {
        if (lands()) { setResults(rows); setTotal(all); }
      })
      .catch(() => undefined);
  });

  useEffect(() => {
    let active = true;
    reads.current.query += 1; // every read already on its way is obsolete
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError("");
      const lands = beginRead();
      void read(0)
        .then(({ rows, total: all }) => {
          if (lands()) { setResults(rows); setTotal(all); }
        })
        .catch((reason) => {
          if (lands()) {
            setResults([]);
            setTotal(0);
            setError(readableError(reason));
          }
        })
        .finally(() => {
          if (active) setLoading(false);
        });
    }, query.trim() ? 200 : 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [query, workRef, whyOnly, recordIds]);

  const showMore = () => {
    const lands = beginRead();
    setMore(true);
    void read(results.length)
      .then(({ rows, total: all }) => {
        if (lands()) { setResults((current) => [...current, ...rows]); setTotal(all); }
      })
      .catch((reason) => setError(readableError(reason)))
      .finally(() => setMore(false));
  };

  const showResults = () => {
    detailReads.current += 1;
    setSelected(null);
    setChosen(null);
    setRequested(null);
    setDetailLoading(false);
    setDetailError("");
  };

  const openReceipt = (receiptId: string, label = "Decision record") => {
    const order = ++detailReads.current;
    setChosen(null);
    setSelected(null);
    setRequested({ kind: "record", id: receiptId, label });
    // Back in the list, the record read last is the selected row.
    setRowSelected(`record-${receiptId}`);
    setDetailLoading(true);
    setDetailError("");
    void apiFetch<Receipt>(`/api/decision-records/${encodeURIComponent(receiptId)}`)
      .then((receipt) => { if (order === detailReads.current) setSelected(receipt); })
      .catch((reason) => { if (order === detailReads.current) setDetailError(readableError(reason)); })
      .finally(() => { if (order === detailReads.current) setDetailLoading(false); });
  };

  // The window opened again with no record (Go ▸ Decisions, the phone's
  // Back): the list, with the record read last still selected.
  const lastReceiptId = useRef(receiptId);
  useEffect(() => {
    if (receiptId) openReceipt(receiptId);
    else if (windowed && lastReceiptId.current) showResults();
    lastReceiptId.current = receiptId;
  }, [receiptId]);
  // WHY with several governing records: the reader opens on the first.
  useEffect(() => {
    if (onlyRecords[0]) openReceipt(onlyRecords[0]);
  }, [recordIds]);

  const openRow = (row: DeskDecision) => {
    if (row.record_id) openReceipt(row.record_id);
    else {
      showResults();
      if (row.source === "desk") openDeskDecision(row.id);
      else setChosen(row);
    }
  };

  // PHILO-17: a decision asked for by id (a ⌘K hit, a Brief row) is read by
  // its id, never looked up in the loaded page; each request opens it again.
  const readDecision = (id: string) => {
    const order = ++detailReads.current;
    setSelected(null);
    setChosen(null);
    setRequested({ kind: "decision", id, label: "Decision" });
    setDetailError("");
    setDetailLoading(true);
    const params = new URLSearchParams({ scope: "all", decision_id: id, limit: "1" });
    void apiFetch<{ decisions?: DeskDecision[] }>(`/api/decisions?${params}`)
      .then((body) => {
        if (order !== detailReads.current) return;
        const row = Array.isArray(body?.decisions) ? body.decisions[0] : undefined;
        if (row) openRow(row);
        else setDetailError("This decision is not on the desk.");
      })
      .catch((reason) => { if (order === detailReads.current) setDetailError(readableError(reason)); })
      .finally(() => { if (order === detailReads.current) setDetailLoading(false); });
  };
  useEffect(() => {
    if (decisionId) readDecision(decisionId);
  }, [decisionId, decisionNonce]);

  const openSource = (source: ReceiptSource) => {
    const meetingId = source.meeting_id ?? (source.source_type === "meeting" ? source.source_ref : "");
    if (meetingId) openRef(`meeting:${meetingId.replace(/^meeting:/, "")}`);
    else if (source.source_type === "desk") openDeskDecision(source.source_ref.replace(/^desk_decision:/, ""));
    else if (source.source_type === "artifact") openRef(`artifact:${source.source_ref.replace(/^artifact:/, "")}`);
  };

  // A page of rows, never zero where the Show more verb is drawn.
  const shownCount = results.length;

  if (chosen && windowed) {
    return (
      <MeetingDecisionReader
        decision={chosen}
        onBack={() => { showResults(); if (decisionId) onBackToList?.(); }}
        onOpenMeeting={(meetingId) => openRef(`meeting:${meetingId}`)}
      />
    );
  }

  if (chosen) {
    return (
      <MeetingDecisionDetail
        decision={chosen}
        onBack={showResults}
        onOpenMeeting={(meetingId) => openRef(`meeting:${meetingId}`)}
      />
    );
  }

  if ((selected || detailLoading || requested) && windowed) {
    return (
      <DecisionReader
        receipt={selected}
        loading={detailLoading}
        error={detailError}
        onRetry={() => {
          if (requested?.kind === "record") openReceipt(requested.id, requested.label);
          else if (requested) readDecision(requested.id);
        }}
        onBack={() => { showResults(); if (receiptId || decisionId) onBackToList?.(); }}
        onOpenReceipt={openReceipt}
        onOpenSource={openSource}
        onOpenWork={(work) => openPullout(qualifiedRef(work.work_type, work.work_ref))}
      />
    );
  }

  if (selected || detailLoading || requested) {
    return (
      <ReceiptDetail
        receipt={selected}
        loading={detailLoading}
        error={detailError}
        requestedLabel={requested?.label ?? "Decision record"}
        onRetry={() => {
          if (requested?.kind === "record") openReceipt(requested.id, requested.label);
          else if (requested) readDecision(requested.id);
        }}
        onBack={showResults}
        onOpenReceipt={openReceipt}
        onOpenSource={openSource}
        onOpenWork={(work) => openPullout(qualifiedRef(work.work_type, work.work_ref))}
      />
    );
  }

  if (windowed) {
    const rowKey = (row: DeskDecision) => `${row.source}-${row.id}`;
    const byKey = new Map(results.map((row) => [rowKey(row), row]));
    const listRows: ObjectListRow[] = results.map((row, index) => {
      const state = decisionState(row);
      const at = wireDate(row.decided_at ?? "")?.getTime();
      return {
        id: rowKey(row),
        kind: "decision",
        // W1-TRUTH: the Name column names the decision by its title; the
        // decision text names it only when it has no title.
        name: (row.title || "").trim() || row.text || "New decision",
        when: dayWords(row.decided_at),
        whenSort: at !== undefined && Number.isFinite(at) ? at * 1000 - index : -index,
        cells: { where: row.meeting_title || (row.source === "desk" ? "Desk" : row.meeting_id ? "Meeting" : "") },
        state: { label: state.word, tone: state.tone, testId: "decisions-state" },
        sortValues: { state: state.rank },
      };
    });
    const pick = rowSelected && byKey.has(rowSelected) ? rowSelected : null;
    const open = (key: string) => { const row = byKey.get(key); if (row) openRow(row); };
    const openCount = results.filter((row) => decisionState(row).word === "Open").length;
    return (
      <div className="receipts-view decisions-window-view">
        <Toolbar label="Decisions" data-testid="decisions-toolbar" trailing={<>
          <CheckGadget label="Current only" variant="token" checked={whyOnly} onChange={setWhyOnly} />
          <span className="decisions-search">
            <StringGadget label="Search decisions" type="search" value={query} onChange={setQuery} placeholder="Search decisions" />
          </span>
        </>}>
          <Button dense variant="primary" onClick={() => void useDesk.getState().createPrimitive("decision", {})} data-testid="decisions-new">
            <ToolGlyph kind="new" />New decision
          </Button>
          {onlyRecords.length ? (
            <Button dense variant="secondary" onClick={() => onBackToList?.()} data-testid="decisions-all">
              All decisions
            </Button>
          ) : null}
        </Toolbar>
        {error ? <SurfaceState error={error} /> : null}
        <div className="decisions-list">
          {loading ? <Loading data-testid="decisions-loading" /> : <SurfaceState
            empty={!results.length && !error}
            emptyLabel={query.trim() ? "No decisions match this search" : whyOnly ? "No current decisions" : "No decisions yet"}
            emptyImage={DECISION_SPRITE}
          >
            <ObjectList
              label="Decisions"
              density="dense"
              rows={listRows}
              columns={DECISION_COLUMNS.filter((column) => column.key !== "where" || listRows.some((row) => row.cells?.where))}
              sort={sort}
              onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key ? (current.dir === "asc" ? "desc" : "asc") : key === "when" ? "desc" : "asc" }))}
              selectedId={pick}
              onSelect={setRowSelected}
              onOpen={open}
              rowProps={() => ({ "data-testid": "decisions-row" })}
            />
          </SurfaceState>}
        </div>
        <StatusBar
          data-testid="decisions-status"
          verbs={pick || (!loading && shownCount > 0 && shownCount < total) ? <>
            {!loading && shownCount > 0 && shownCount < total ? (
              <Button variant="secondary" dense loading={more} onClick={showMore} data-testid="decisions-more">
                {shownCount > 0 ? `Show more (${shownCount} of ${total})` : "Show more"}
              </Button>
            ) : null}
            {pick ? (
              <Button dense variant="secondary" onClick={() => open(pick)} data-testid="decisions-open-selected">
                <ToolGlyph kind="open" />
                Open
              </Button>
            ) : null}
          </> : null}
          items={[
            { key: "count", text: countWords(total, "decision") },
            { key: "open", lamp: "ask" as const, text: countWords(openCount, "open", "open") },
          ]}
        />
      </div>
    );
  }

  return (
    <div className="receipts-view">
      <div className="receipts-search">
        <StringGadget
          label="Search decisions"
          type="search"
          value={query}
          onChange={setQuery}
          placeholder="Search decisions"
        />
        <MicButton onText={setQuery} />
      </div>
      <div className="receipts-search-actions">
        <Button
          variant="ghost"
          dense
          className={`receipts-why-filter${whyOnly ? " is-active" : ""}`}
          aria-pressed={whyOnly}
          onClick={() => setWhyOnly((value) => !value)}
        >
          Current only
        </Button>
      </div>
      {error ? <SurfaceState error={error} /> : null}
      <SurfaceLedger cols="facts" count={countLabel("DECISIONS", total)}>
        {loading ? (
          <SurfaceState loading />
        ) : results.length ? (
          <ul className="surface-ledger-rows receipts-results">
            {results.map((row) => {
              const word = stateWord(row);
              return (
                <SurfaceLedgerRow
                  key={`${row.source}-${row.id}`}
                  data-testid="decisions-row"
                  primary={row.text || "New decision"}
                  lineLabel={`Open decision ${row.text || "New decision"}`}
                  onToggle={() => openRow(row)}
                  wrap
                  cells={
                    <>
                      {/* PHILO-17: a row names when and where it was decided,
                          never its key. */}
                      <span className="surface-ledger-cell">{humanDate(row.decided_at)}</span>
                      <span className="surface-ledger-cell">
                        {row.meeting_title || (row.source === "desk" ? "Desk" : row.meeting_id ? "Meeting" : "")}
                      </span>
                      {word ? (
                        <span className="surface-ledger-cell">
                          <span className="surface-token" data-tone="muted">{word}</span>
                        </span>
                      ) : null}
                    </>
                  }
                />
              );
            })}
          </ul>
        ) : (
          <SurfaceState empty emptyLabel={query.trim() ? "No decisions match this search." : whyOnly ? "No current decisions." : "No decisions yet."} />
        )}
      </SurfaceLedger>
      {!loading && shownCount > 0 && shownCount < total ? (
        <Button variant="secondary" dense loading={more} onClick={showMore} data-testid="decisions-more">
          {shownCount > 0 ? `Show more (${shownCount} of ${total})` : "Show more"}
        </Button>
      ) : null}
    </div>
  );
}

/** PHILO-17: a decision a meeting recorded, opened in place: its words, why,
 *  when, and its meeting (one press away). */
function MeetingDecisionDetail({
  decision,
  onBack,
  onOpenMeeting,
}: {
  decision: DeskDecision;
  onBack: () => void;
  onOpenMeeting: (meetingId: string) => void;
}) {
  const word = stateWord(decision);
  const meetingId = decision.meeting_id ?? "";
  return (
    <article className="receipt-detail attention-record" data-testid="decision-detail">
      <div className="attention-record-verbs">
        <Button variant="ghost" dense onClick={onBack}>Results</Button>
        {word ? <StateChip state="idle" label={word} wrap /> : null}
      </div>
      <GadgetGroup label="Decision" material="inset"><Material>{decision.text}</Material></GadgetGroup>
      <GadgetGroup label="Decision context" material="inset">
        {decision.rationale ? <GadgetRow label="Rationale" controlWidth="full"><Material>{decision.rationale}</Material></GadgetRow> : null}
        {decision.decided_at ? <GadgetRow label="Decided">{humanDate(decision.decided_at)}</GadgetRow> : null}
        {decision.meeting_title || meetingId ? <GadgetRow label="Meeting" controlWidth="full">
          <span>{decision.meeting_title || "Meeting"}</span>
          {meetingId ? <Button variant="ghost" dense onClick={() => onOpenMeeting(meetingId)}>Open meeting</Button> : null}
        </GadgetRow> : null}
      </GadgetGroup>
    </article>
  );
}

/** Window grammar: a decision a meeting recorded that has no record yet,
 *  read in the Decisions window. Toolbar: ‹ Decisions, Open meeting. Body:
 *  the decision as the heading, its why as the words, the meeting as a fact.
 *  Status bar: the state as a dot and a word, and where it came from. */
function MeetingDecisionReader({
  decision,
  onBack,
  onOpenMeeting,
}: {
  decision: DeskDecision;
  onBack: () => void;
  onOpenMeeting: (meetingId: string) => void;
}) {
  const backRef = useRef(onBack);
  backRef.current = onBack;
  const compact = useCompactViewport();
  useWindowBack(compact ? { onBack: () => backRef.current(), testId: "decision-reader-back" } : null, [compact]);
  const viaFrame = useHasWindowBack() && compact;
  const meetingId = (decision.meeting_id ?? "").trim();
  const state = decisionState(decision);
  const decidedAt = decision.decided_at ? wireDate(decision.decided_at) : null;
  const when = decidedAt && state.word === "Accepted" ? ` ${sinceWord(decidedAt)}` : "";
  return (
    <div className="decision-reader-window" data-testid="decision-reader" data-from="meeting">
      <Toolbar label="Decision" data-testid="decision-reader-toolbar">
        {viaFrame ? null : (
          <Button dense variant="secondary" onClick={onBack} data-testid="decision-reader-back">
            <span aria-hidden="true">‹</span> Decisions
          </Button>
        )}
        {meetingId ? (
          <Button dense variant="secondary" onClick={() => onOpenMeeting(meetingId)} data-testid="decision-reader-meeting">
            <ToolGlyph kind="open" />Open meeting
          </Button>
        ) : null}
      </Toolbar>
      <article className="decision-reader" aria-labelledby={`decision-reader-title-${decision.id}`}>
        <h2 id={`decision-reader-title-${decision.id}`} className="decision-reader-title" data-testid="decision-reader-title">
          {decision.text}
        </h2>
        {decision.rationale ? <Material className="decision-reader-why">{decision.rationale}</Material> : null}
        {decision.meeting_title ? (
          <dl className="decision-reader-facts">
            <div className="decision-reader-fact">
              <dt>Meeting</dt>
              <dd>{decision.meeting_title}</dd>
            </div>
          </dl>
        ) : null}
      </article>
      <StatusBar
        data-testid="decision-reader-status"
        items={[
          { key: "state", lamp: state.tone, text: `${state.word}${when}`, testId: "decision-reader-state" },
          { key: "from", text: "From a meeting" },
        ]}
      />
    </div>
  );
}

/** A record's About and Why, as the from-desk producer writes them into its
 *  rationale (`About: …` then `Why: …`); any other rationale is the Why. */
function rationaleParts(rationale: string | null | undefined): { about: string; why: string } {
  const text = String(rationale || "");
  const about = text.match(/(?:^|\n\n)About:\s*([^\n]*(?:\n(?!Why:)[^\n]*)*)/i)?.[1]?.trim() || "";
  const why = text.match(/(?:^|\n\n)Why:\s*([\s\S]*)/i)?.[1]?.trim() || "";
  return { about, why: why || (!about ? text.trim() : "") };
}

/** Window grammar (the owner, 2026-10-25): a decision record read in the
 *  Decisions window. Toolbar: ‹ Decisions, Send…. Body: the decision as the
 *  reader's first heading, the Why as its words, About and the other facts as
 *  a quiet label/value grid, Evidence and History as folds. Status bar: the
 *  state as a dot and a word with when (`● Accepted just now`). No captions in
 *  mono capitals, no state chip. */
function DecisionReader({
  receipt,
  loading,
  error,
  onRetry,
  onBack,
  onOpenReceipt,
  onOpenSource,
  onOpenWork,
}: {
  receipt: Receipt | null;
  loading: boolean;
  error: string;
  onRetry: () => void;
  onBack: () => void;
  onOpenReceipt: (id: string, label?: string) => void;
  onOpenSource: (source: ReceiptSource) => void;
  onOpenWork: (work: ReceiptWork) => void;
}) {
  const [sending, setSending] = useState(false);
  useEffect(() => { setSending(false); }, [receipt?.id]);
  // On the phone the window's title-bar Back is the one Back: it returns to
  // the list (the toolbar then draws no ‹ Decisions of its own).
  const backRef = useRef(onBack);
  backRef.current = onBack;
  const compact = useCompactViewport();
  useWindowBack(compact ? { onBack: () => backRef.current(), testId: "decision-reader-back" } : null, [compact]);
  const viaFrame = useHasWindowBack() && compact;
  const proposed = String(receipt?.status || "").toLowerCase() === "proposed";
  const toolbar = (
    <Toolbar label="Decision" data-testid="decision-reader-toolbar">
      {viaFrame ? null : (
        <Button dense variant="secondary" onClick={onBack} data-testid="decision-reader-back">
          <span aria-hidden="true">‹</span> Decisions
        </Button>
      )}
      {receipt && !proposed ? (
        <Button dense variant="secondary" aria-expanded={sending} onClick={() => setSending((open) => !open)}
          data-testid="decision-reader-send">
          <ToolGlyph kind="send" />Send…
        </Button>
      ) : null}
    </Toolbar>
  );
  if (loading || error || !receipt) {
    return (
      <div className="decision-reader-window" data-testid="decision-reader">
        {toolbar}
        <div className="decision-reader">
          {loading ? <SurfaceState loading /> : <SurfaceState error={error || "Decision unavailable."} onRetry={onRetry} />}
        </div>
      </div>
    );
  }
  const { about, why } = rationaleParts(receipt.rationale);
  const state = decisionState(fromReceipt(receipt));
  const decidedAt = receipt.created_at ? wireDate(receipt.created_at) : null;
  const when = decidedAt && state.word === "Accepted" ? ` ${sinceWord(decidedAt)}` : "";
  const sourceLabel = (source: ReceiptSource): string | null => source.meeting_id || source.source_type === "meeting"
    ? "Open meeting" : source.source_type === "artifact" ? "Open artifact" : null;
  const sources = receipt.sources?.filter((source) => source.source_type !== "predecessor" && source.source_type !== "successor"
    && source.source_type !== "desk" && (source.text || sourceLabel(source))) ?? [];
  const predecessorId = receipt.predecessor_id;
  const successorId = receipt.successor_id;
  const history = Boolean(predecessorId || successorId || receipt.revisions?.length);
  const evidence = Boolean(sources.length || receipt.work?.length);
  const facts: Array<[string, ReactNode]> = [];
  // About: the Project the producer linked opens its Room; a name with no
  // link is the plain chip.
  const projectId = receipt.sources?.find((source) => source.source_type === "project")?.source_ref ?? "";
  const aboutFace = <>
    <img src={spriteUrl("project", projectId || about, "rest", null, 20)} alt="" width={20} height={20} draggable={false} />
    {about}
  </>;
  if (about) facts.push(["About", projectId ? (
    <Button dense variant="secondary" className="decision-reader-about" data-testid="decision-reader-about"
      onClick={() => openProjectRoom(projectId)}>{aboutFace}</Button>
  ) : (
    <span className="decision-reader-about" data-testid="decision-reader-about">{aboutFace}</span>
  )]);
  if (receipt.alternatives) facts.push(["Alternatives", receipt.alternatives]);
  if (receipt.owner) facts.push(["Owner", receipt.owner]);
  if (receipt.review_date) facts.push(["Review", humanDate(receipt.review_date)]);
  return (
    <div className="decision-reader-window" data-testid="decision-reader">
      {toolbar}
      <article className="decision-reader" aria-labelledby={`decision-reader-title-${receipt.id}`}>
        {sending ? (
          <DecisionRecordSendSheet id={receipt.id} text={receipt.decision_text} onBack={() => setSending(false)} />
        ) : (
          <>
            <h2 id={`decision-reader-title-${receipt.id}`} className="decision-reader-title" data-testid="decision-reader-title">
              {(receipt.title || "").trim() || receipt.decision_text}
            </h2>
            {(receipt.title || "").trim() && receipt.title!.trim() !== receipt.decision_text.trim() ? (
              <Material className="decision-reader-why">{receipt.decision_text}</Material>
            ) : null}
            {why ? <Material className="decision-reader-why">{why}</Material> : null}
            {facts.length ? (
              <dl className="decision-reader-facts">
                {facts.map(([label, value]) => (
                  <div key={label} className="decision-reader-fact">
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            ) : null}
            {evidence ? <FoldGadget title="Evidence">
              {sources.map((source, index) => <div key={`${source.source_type}-${source.source_ref}-${index}`} className="decision-reader-source">
                {source.speaker ? <span className="decision-reader-source-who">{source.speaker}</span> : null}
                {source.text ? <Material>{source.text}</Material> : null}
                {sourceLabel(source) ? <Button variant="ghost" dense onClick={() => onOpenSource(source)}>{sourceLabel(source)}</Button> : null}
              </div>)}
              {receipt.work?.length ? <div className="attention-record-verbs">{receipt.work.map((work) => (
                <Button key={work.id} variant="ghost" dense onClick={() => onOpenWork(work)}>
                  Open {workName(work.work_type)} · {work.work_ref}
                </Button>
              ))}</div> : null}
            </FoldGadget> : null}
            {history ? <FoldGadget title="History">
              {predecessorId || successorId ? <div className="attention-record-verbs">
                {predecessorId ? <Button variant="ghost" dense onClick={() => onOpenReceipt(predecessorId, "Previous decision")}>Previous decision</Button> : null}
                {successorId ? <Button variant="ghost" dense onClick={() => onOpenReceipt(successorId, "Next decision")}>Next decision</Button> : null}
              </div> : null}
              {receipt.revisions?.length ? <ol className="attention-record-revisions">
                {receipt.revisions.map((revision) => <li key={revision.id}>
                  <time dateTime={revision.created_at}>{humanDate(revision.created_at)}</time>
                  <span>{revision.field_name.replace(/_/g, " ")}</span>
                  <span>{revision.old_value || "—"} → {revision.new_value || "—"}</span>
                </li>)}
              </ol> : null}
            </FoldGadget> : null}
          </>
        )}
      </article>
      <StatusBar
        data-testid="decision-reader-status"
        items={[{ key: "state", lamp: state.tone, text: `${state.word}${when}`, testId: "decision-reader-state" }]}
      />
    </div>
  );
}

function ReceiptDetail({
  receipt,
  loading,
  error,
  requestedLabel,
  onRetry,
  onBack,
  onOpenReceipt,
  onOpenSource,
  onOpenWork,
}: {
  receipt: Receipt | null;
  loading: boolean;
  error: string;
  requestedLabel: string;
  onRetry: () => void;
  onBack: () => void;
  onOpenReceipt: (id: string, label?: string) => void;
  onOpenSource: (source: ReceiptSource) => void;
  onOpenWork: (work: ReceiptWork) => void;
}) {
  const back = <Button variant="ghost" dense onClick={onBack}>Results</Button>;
  if (loading || error || !receipt) return (
    <article className="receipt-detail attention-record">
      <div className="attention-record-verbs">{back}</div>
      <GadgetGroup label={requestedLabel} material="inset">
        {loading ? <SurfaceState loading /> : <SurfaceState error={error || "Decision unavailable."} onRetry={onRetry} />}
      </GadgetGroup>
    </article>
  );

  const sourceLabel = (source: ReceiptSource): string | null => source.meeting_id || source.source_type === "meeting"
    ? "Open meeting" : source.source_type === "desk" ? "Open decision" : source.source_type === "artifact" ? "Open artifact" : null;
  const sources = receipt.sources?.filter((source) => source.source_type !== "predecessor" && source.source_type !== "successor"
    && (source.text || sourceLabel(source))) ?? [];
  const origin = decisionRecordSourceRef(receipt.source_type, receipt.source_id);
  const decisionText = receipt.decision_text;
  const rationale = String(receipt.rationale || "");
  const about = rationale.match(/(?:^|\n\n)About:\s*([^\n]*(?:\n(?!Why:)[^\n]*)*)/i)?.[1]?.trim() || "";
  const why = rationale.match(/(?:^|\n\n)Why:\s*([\s\S]*)/i)?.[1]?.trim() || "";
  const proposed = String(receipt.status || "").toLowerCase() === "proposed";
  const predecessorId = receipt.predecessor_id;
  const successorId = receipt.successor_id;
  const history = Boolean(predecessorId || successorId || receipt.revisions?.length);
  const evidence = Boolean(sources.length || receipt.work?.length);
  return (
    <article className="receipt-detail attention-record">
      <div className="attention-record-verbs">
        {back}
        <StateChip wrap state={receiptStatus(receipt) === "governing" ? "success" : "idle"} label={RECEIPT_WORD[receiptStatus(receipt)]} />
      </div>
      <GadgetGroup label="Decision" material="inset"><Material>{decisionText}</Material></GadgetGroup>
      {receipt.rationale || receipt.alternatives || receipt.owner || receipt.review_date || origin ? (
        <GadgetGroup label="Decision context" material="inset">
          {about ? <GadgetRow label="About" controlWidth="full"><Material>{about}</Material></GadgetRow> : null}
          {why ? <GadgetRow label="Why" controlWidth="full"><Material>{why}</Material></GadgetRow> : null}
          {receipt.rationale && !about && !why ? <GadgetRow label="Rationale" controlWidth="full"><Material>{receipt.rationale}</Material></GadgetRow> : null}
          {receipt.alternatives ? <GadgetRow label="Alternatives" controlWidth="full"><Material>{receipt.alternatives}</Material></GadgetRow> : null}
          {receipt.owner ? <GadgetRow label="Owner" controlWidth="full">{receipt.owner}</GadgetRow> : null}
          {receipt.review_date ? <GadgetRow label="Review">{humanDate(receipt.review_date)}</GadgetRow> : null}
          {origin ? <GadgetRow label="Source" controlWidth="full">
            <Button variant="ghost" dense onClick={() => openRef(origin)}>Open decision</Button>
          </GadgetRow> : null}
        </GadgetGroup>
      ) : null}
      {/* PHILO-11-05a (canvas B5): the record's SEND well, after its fields. */}
      {!proposed ? <DecisionRecordSendWells id={receipt.id} text={decisionText} /> : null}
      {evidence ? <FoldGadget title="Evidence">
        {sources.map((source, index) => <GadgetGroup key={`${source.source_type}-${source.source_ref}-${index}`}
          label={source.speaker || "Source"} material="inset">
          {source.text ? <Material>{source.text}</Material> : null}
          {sourceLabel(source) ? <Button variant="ghost" dense onClick={() => onOpenSource(source)}>{sourceLabel(source)}</Button> : null}
        </GadgetGroup>)}
        {receipt.work?.length ? <GadgetGroup label="Affected work" material="inset">
          <div className="attention-record-verbs">{receipt.work.map((work) => (
            <Button key={work.id} variant="ghost" dense onClick={() => onOpenWork(work)}>
              Open {workName(work.work_type)} · {work.work_ref}
            </Button>
          ))}</div>
        </GadgetGroup> : null}
      </FoldGadget> : null}
      {history ? <FoldGadget title="History">
        {predecessorId || successorId ? <div className="attention-record-verbs">
          {predecessorId ? <Button variant="ghost" dense onClick={() => onOpenReceipt(predecessorId, "Previous decision")}>Previous decision</Button> : null}
          {successorId ? <Button variant="ghost" dense onClick={() => onOpenReceipt(successorId, "Next decision")}>Next decision</Button> : null}
        </div> : null}
        {receipt.revisions?.length ? <GadgetGroup label="Revisions" material="inset">
          <ol className="attention-record-revisions">
            {receipt.revisions.map((revision) => {
              const revDate = revision.created_at;
              const fieldName = revision.field_name.replace(/_/g, " ");
              const oldVal = revision.old_value;
              const newVal = revision.new_value;
              return <li key={revision.id}>
                <time dateTime={revDate}>{humanDate(revDate)}</time>
                <span>{fieldName}</span>
                <span>{oldVal || "—"} → {newVal || "—"}</span>
              </li>;
            })}
          </ol>
        </GadgetGroup> : null}
      </FoldGadget> : null}
    </article>
  );
}

function workName(type: string): string {
  return ({ story: "story", project: "project", meeting: "meeting", decision: "decision", note: "note", workbench: "automation", thread: "thread" } as Record<string, string>)[type] ?? "work";
}
