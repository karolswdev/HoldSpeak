import { wireDate } from "../../surface/format";
import { useEffect, useRef, useState } from "react";
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
import { DecisionRecordSendWells } from "../../documentSendsLazy";
import { Material } from "../../surface/Material";
import { FoldGadget, GadgetGroup, GadgetRow } from "../../surface/gadgets";
import { StateChip } from "../../surface";
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
  decision_text: string;
  rationale: string | null;
  alternatives: string | null;
  owner: string | null;
  review_date: string | null;
  lifecycle: string;
  sources?: ReceiptSource[];
  work?: ReceiptWork[];
  revisions?: ReceiptRevision[];
  predecessor_id?: string | null;
  successor_id?: string | null;
  source_type?: string;
  source_id?: string;
};

function receiptStatus(receipt: Receipt): "governing" | "superseded" | "related" {
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
  text: string;
  rationale?: string | null;
  decided_at?: string | null;
  lifecycle?: string | null;
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
  const lifecycle = String(row.lifecycle ?? "").toLowerCase();
  if (CURRENT.has(lifecycle) || !lifecycle) return "";
  if (lifecycle === "superseded") return "REPLACED";
  if (lifecycle === "deprecated") return "RETIRED";
  return lifecycle.toUpperCase();
}

function fromReceipt(receipt: Receipt & { created_at?: string | null }): DeskDecision {
  return {
    source: "record", id: receipt.id, text: receipt.decision_text, rationale: receipt.rationale,
    decided_at: receipt.created_at ?? null, lifecycle: receipt.lifecycle, record_id: receipt.id,
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
}: {
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
  useEffect(() => () => { detailReads.current += 1; }, []);

  useEffect(() => {
    setQuery(initialQuery);
    setWhyOnly(initialWhyOnly);
  }, [initialQuery, initialWhyOnly]);

  // A work ref lists the records linked to that work; else the desk's
  // decisions, one page at a time, searched and filtered by the hub.
  const read = (offset: number, limit = PAGE): Promise<{ rows: DeskDecision[]; total: number }> => {
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
    const params = new URLSearchParams({ scope: "all", limit: String(limit), offset: String(offset) });
    if (query.trim()) params.set("q", query.trim());
    if (whyOnly) params.set("current", "true");
    return apiFetch<{ decisions?: DeskDecision[]; page?: { total?: number } }>(`/api/decisions?${params}`)
      .then((body) => {
        const rows = Array.isArray(body?.decisions) ? body.decisions : [];
        return { rows, total: Number(body?.page?.total ?? rows.length) };
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
  }, [query, workRef, whyOnly]);

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
    setDetailLoading(true);
    setDetailError("");
    void apiFetch<Receipt>(`/api/decision-records/${encodeURIComponent(receiptId)}`)
      .then((receipt) => { if (order === detailReads.current) setSelected(receipt); })
      .catch((reason) => { if (order === detailReads.current) setDetailError(readableError(reason)); })
      .finally(() => { if (order === detailReads.current) setDetailLoading(false); });
  };

  useEffect(() => {
    if (receiptId) openReceipt(receiptId);
  }, [receiptId]);

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

  if (chosen) {
    return (
      <MeetingDecisionDetail
        decision={chosen}
        onBack={showResults}
        onOpenMeeting={(meetingId) => openRef(`meeting:${meetingId}`)}
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
      <GadgetGroup label="Context" material="inset">
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
        <GadgetGroup label="Context" material="inset">
          {receipt.rationale ? <GadgetRow label="Rationale" controlWidth="full"><Material>{receipt.rationale}</Material></GadgetRow> : null}
          {receipt.alternatives ? <GadgetRow label="Alternatives" controlWidth="full"><Material>{receipt.alternatives}</Material></GadgetRow> : null}
          {receipt.owner ? <GadgetRow label="Owner" controlWidth="full">{receipt.owner}</GadgetRow> : null}
          {receipt.review_date ? <GadgetRow label="Review">{humanDate(receipt.review_date)}</GadgetRow> : null}
          {origin ? <GadgetRow label="Source" controlWidth="full">
            <Button variant="ghost" dense onClick={() => openRef(origin)}>Open decision</Button>
          </GadgetRow> : null}
        </GadgetGroup>
      ) : null}
      {/* PHILO-11-05a (canvas B5): the record's SEND well, after its fields. */}
      <DecisionRecordSendWells id={receipt.id} text={decisionText} />
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
  return ({ story: "story", project: "project", meeting: "meeting", decision: "decision", note: "note", workbench: "Workbench", thread: "thread" } as Record<string, string>)[type] ?? "work";
}
