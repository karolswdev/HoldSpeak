import { wireDate } from "../../surface/format";
import { useEffect, useRef, useState } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { holdObject, qualifiedRef } from "../../api";
import { openRef } from "../../openObject";
import { allObjects } from "../../world";
import { useDesk } from "../../store";
import { useOnDeskChanged } from "../../useDeskChangedRefresh";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceState } from "../../surface/Surface";
import { countLabel } from "../../surface/count";
import { MicButton } from "../../surface";
import { StringGadget } from "../../surface/gadgets";
import { DecisionRecordSendWells } from "../../documentSendsLazy";

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

function shortId(id: string): string {
  return id.replace(/^record-/, "").slice(0, 12);
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
  const [error, setError] = useState("");

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
        return { rows, total: rows.length };
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

  const openReceipt = (receiptId: string) => {
    setChosen(null);
    setDetailLoading(true);
    setError("");
    void apiFetch<Receipt>(`/api/decision-records/${encodeURIComponent(receiptId)}`)
      .then(setSelected)
      .catch((reason) => setError(readableError(reason)))
      .finally(() => setDetailLoading(false));
  };

  useEffect(() => {
    if (receiptId) openReceipt(receiptId);
  }, [receiptId]);

  const openRow = (row: DeskDecision) => {
    if (row.record_id) openReceipt(row.record_id);
    else if (row.source === "desk") openDeskDecision(row.id);
    else { setSelected(null); setChosen(row); }
  };

  // PHILO-17: a decision asked for by id (a ⌘K hit, a Brief row) is read by
  // its id, never looked up in the loaded page; each request opens it again.
  useEffect(() => {
    if (!decisionId) return;
    let live = true;
    const params = new URLSearchParams({ scope: "all", decision_id: decisionId, limit: "1" });
    void apiFetch<{ decisions?: DeskDecision[] }>(`/api/decisions?${params}`)
      .then((body) => {
        if (!live) return;
        const row = Array.isArray(body?.decisions) ? body.decisions[0] : undefined;
        if (row) openRow(row);
        else setError("This decision is not on the desk.");
      })
      .catch((reason) => { if (live) setError(readableError(reason)); });
    return () => { live = false; };
  }, [decisionId, decisionNonce]);

  const openSource = (source: ReceiptSource) => {
    const meetingId = source.meeting_id ?? (source.source_type === "meeting" ? source.source_ref : "");
    if (meetingId) openRef(`meeting:${meetingId}`);
  };

  if (chosen) {
    return (
      <MeetingDecisionDetail
        decision={chosen}
        onBack={() => setChosen(null)}
        onOpenMeeting={(meetingId) => openRef(`meeting:${meetingId}`)}
      />
    );
  }

  if (selected || detailLoading) {
    return (
      <ReceiptDetail
        receipt={selected}
        loading={detailLoading}
        error={error}
        onBack={() => {
          setSelected(null);
          setError("");
        }}
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
      {!loading && results.length < total ? (
        <Button variant="secondary" dense loading={more} onClick={showMore} data-testid="decisions-more">
          {`Show more (${results.length} of ${total})`}
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
    <article className="receipt-detail" data-testid="decision-detail">
      <Button variant="ghost" dense className="receipt-back" onClick={onBack}>← RESULTS</Button>
      <header className="receipt-detail-head">
        {word ? <span className="surface-token" data-tone="muted">{word}</span> : null}
        <h3>{decision.text}</h3>
      </header>
      <dl className="receipt-fields">
        <ReceiptField label="Rationale" value={decision.rationale} />
        <ReceiptField label="Decided" value={humanDate(decision.decided_at)} />
        <ReceiptField label="Meeting" value={decision.meeting_title || (meetingId ? "Meeting" : null)} />
      </dl>
      {meetingId ? (
        <Button variant="secondary" dense onClick={() => onOpenMeeting(meetingId)}>Open meeting</Button>
      ) : null}
    </article>
  );
}

function ReceiptDetail({
  receipt,
  loading,
  error,
  onBack,
  onOpenReceipt,
  onOpenSource,
  onOpenWork,
}: {
  receipt: Receipt | null;
  loading: boolean;
  error: string;
  onBack: () => void;
  onOpenReceipt: (id: string) => void;
  onOpenSource: (source: ReceiptSource) => void;
  onOpenWork: (work: ReceiptWork) => void;
}) {
  if (loading) return <SurfaceState loading />;
  if (!receipt) return <SurfaceState error={error || "Decision unavailable."} />;

  const provenance = receipt.sources?.find((source) => source.source_type === "segment");
  const decisionText = receipt.decision_text;
  const predecessorId = receipt.predecessor_id;
  const successorId = receipt.successor_id;
  return (
    <article className="receipt-detail">
      <Button variant="ghost" dense className="receipt-back" onClick={onBack}>← RESULTS</Button>
      <header className="receipt-detail-head">
        <span className="receipts-id">D-{shortId(receipt.id)}</span>
        <span className="surface-token" data-tone={receiptStatus(receipt) === "superseded" ? "muted" : "ok"}>
          {RECEIPT_WORD[receiptStatus(receipt)]}
        </span>
        <h3>{decisionText}</h3>
      </header>
      <dl className="receipt-fields">
        <ReceiptField label="Rationale" value={receipt.rationale} />
        <ReceiptField label="Alternatives" value={receipt.alternatives} />
        <ReceiptField label="Owner" value={receipt.owner} />
        <ReceiptField label="Review" value={humanDate(receipt.review_date)} />
      </dl>
      {/* PHILO-11-05a (canvas B5): the record's SEND well, after its fields. */}
      <DecisionRecordSendWells id={receipt.id} text={decisionText} />
      <section className="receipt-provenance" aria-label="Provenance">
        <h4>PROVENANCE</h4>
        {provenance?.text ? (
          <blockquote>
            <p>“{provenance.text}”</p>
            <footer>{provenance.speaker || "Meeting segment"}</footer>
          </blockquote>
        ) : <p className="quiet">No meeting-segment quote retained.</p>}
        {provenance?.meeting_id || receipt.sources?.some((source) => source.source_type === "meeting") ? (
          <Button variant="ghost" dense className="receipt-go" onClick={() => onOpenSource(provenance ?? receipt.sources!.find((source) => source.source_type === "meeting")!)}>
            [GO]
          </Button>
        ) : null}
      </section>
      <section className="receipt-work" aria-label="Affected work">
        <h4>AFFECTED WORK</h4>
        {receipt.work?.length ? receipt.work.map((work) => (
          <Button key={work.id} variant="ghost" dense className="receipt-work-chip" onClick={() => onOpenWork(work)}>
            {work.work_type}: {work.work_ref}
          </Button>
        )) : <p className="quiet">No affected work linked.</p>}
      </section>
      <section className="receipt-chain" aria-label="Supersession history">
        <h4>SUPERSESSION</h4>
        <div>
          {predecessorId ? <Button variant="ghost" dense onClick={() => onOpenReceipt(predecessorId!)}>← D-{shortId(predecessorId)}</Button> : <span>← ORIGIN</span>}
          <strong>THIS</strong>
          {successorId ? <Button variant="ghost" dense onClick={() => onOpenReceipt(successorId!)}>D-{shortId(successorId)} →</Button> : <span>CURRENT →</span>}
        </div>
      </section>
      <section className="receipt-revisions" aria-label="Revision timeline">
        <h4>REVISIONS</h4>
        {receipt.revisions?.length ? (
          <ol>
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
        ) : <p className="quiet">No revisions recorded.</p>}
      </section>
    </article>
  );
}

function ReceiptField({ label, value }: { label: string; value: string | null | undefined }) {
  return <><dt>{label}</dt><dd>{value || "—"}</dd></>;
}
