import { useEffect, useState } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { qualifiedRef } from "../../api";
import { useDesk } from "../../store";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceState } from "../../surface/Surface";

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

function shortId(id: string): string {
  return id.replace(/^receipt-/, "").slice(0, 12);
}

function humanDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

/** Search-first, in-place decision history for the Intelligence pullout. */
export function ReceiptsView() {
  const openPullout = useDesk((state) => state.openPullout);
  const [query, setQuery] = useState("");
  const [whyOnly, setWhyOnly] = useState(false);
  const [results, setResults] = useState<Receipt[]>([]);
  const [selected, setSelected] = useState<Receipt | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let current = true;
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError("");
      const endpoint = query.trim()
        ? `/api/receipts/search?q=${encodeURIComponent(query.trim())}`
        : "/api/receipts";
      void apiFetch<Receipt[]>(endpoint)
        .then((receipts) => {
          if (current) setResults(Array.isArray(receipts) ? receipts : []);
        })
        .catch((reason) => {
          if (current) {
            setResults([]);
            setError(readableError(reason));
          }
        })
        .finally(() => {
          if (current) setLoading(false);
        });
    }, query.trim() ? 200 : 0);
    return () => {
      current = false;
      window.clearTimeout(timer);
    };
  }, [query]);

  const visibleResults = whyOnly
    ? results.filter((receipt) => receiptStatus(receipt) === "governing")
    : results;

  const openReceipt = (receiptId: string) => {
    setDetailLoading(true);
    setError("");
    void apiFetch<Receipt>(`/api/receipts/${encodeURIComponent(receiptId)}`)
      .then(setSelected)
      .catch((reason) => setError(readableError(reason)))
      .finally(() => setDetailLoading(false));
  };

  const openSource = (source: ReceiptSource) => {
    const meetingId = source.meeting_id ?? (source.source_type === "meeting" ? source.source_ref : "");
    if (meetingId) openPullout(qualifiedRef("meeting", meetingId));
  };

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
      <label className="receipts-search">
        <span className="receipts-search-prefix" aria-hidden="true">WHY</span>
        <span className="sr-only">Search decision receipts</span>
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search decisions"
          aria-label="Search decision receipts"
        />
      </label>
      <div className="receipts-search-actions">
        <button
          type="button"
          className={`receipts-why-filter${whyOnly ? " is-active" : ""}`}
          aria-pressed={whyOnly}
          onClick={() => setWhyOnly((value) => !value)}
        >
          WHY ONLY
        </button>
        {whyOnly ? <span>GOVERNING RECEIPTS</span> : <span>ALL RECEIPTS</span>}
      </div>
      {error ? <SurfaceState error={error} /> : null}
      <SurfaceLedger cols="facts" count={`RECEIPTS ${visibleResults.length}`}>
        {loading ? (
          <SurfaceState loading />
        ) : visibleResults.length ? (
          <ul className="surface-ledger-rows receipts-results">
            {visibleResults.map((receipt) => {
              const status = receiptStatus(receipt);
              return (
                <SurfaceLedgerRow
                  key={receipt.id}
                  primary={receipt.decision_text}
                  lineLabel={`Open receipt ${receipt.decision_text}`}
                  onToggle={() => openReceipt(receipt.id)}
                  cells={
                    <>
                      <span className="surface-ledger-cell receipts-id">R-{shortId(receipt.id)}</span>
                      <span className="surface-ledger-cell">{receipt.owner || "UNASSIGNED"}</span>
                      <span className="surface-ledger-cell">
                        <span className="surface-token" data-tone={status === "superseded" ? "muted" : "ok"}>
                          {status.toUpperCase()}
                        </span>
                      </span>
                    </>
                  }
                />
              );
            })}
          </ul>
        ) : (
          <SurfaceState empty emptyLabel={whyOnly ? "No governing receipts." : "No receipts match this search."} />
        )}
      </SurfaceLedger>
    </div>
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
  if (!receipt) return <SurfaceState error={error || "Receipt unavailable."} />;

  const provenance = receipt.sources?.find((source) => source.source_type === "segment");
  return (
    <article className="receipt-detail">
      <button type="button" className="receipt-back" onClick={onBack}>← RESULTS</button>
      <header className="receipt-detail-head">
        <span className="receipts-id">R-{shortId(receipt.id)}</span>
        <span className="surface-token" data-tone={receiptStatus(receipt) === "superseded" ? "muted" : "ok"}>
          {receiptStatus(receipt).toUpperCase()}
        </span>
        <h3>{receipt.decision_text}</h3>
      </header>
      <dl className="receipt-fields">
        <ReceiptField label="Rationale" value={receipt.rationale} />
        <ReceiptField label="Alternatives" value={receipt.alternatives} />
        <ReceiptField label="Owner" value={receipt.owner} />
        <ReceiptField label="Review" value={humanDate(receipt.review_date)} />
      </dl>
      <section className="receipt-provenance" aria-label="Provenance">
        <h4>PROVENANCE</h4>
        {provenance?.text ? (
          <blockquote>
            <p>“{provenance.text}”</p>
            <footer>{provenance.speaker || "Meeting segment"}</footer>
          </blockquote>
        ) : <p className="quiet">No meeting-segment quote retained.</p>}
        {provenance?.meeting_id || receipt.sources?.some((source) => source.source_type === "meeting") ? (
          <button type="button" className="receipt-go" onClick={() => onOpenSource(provenance ?? receipt.sources!.find((source) => source.source_type === "meeting")!)}>
            [GO]
          </button>
        ) : null}
      </section>
      <section className="receipt-work" aria-label="Affected work">
        <h4>AFFECTED WORK</h4>
        {receipt.work?.length ? receipt.work.map((work) => (
          <button key={work.id} type="button" className="receipt-work-chip" onClick={() => onOpenWork(work)}>
            {work.work_type}: {work.work_ref}
          </button>
        )) : <p className="quiet">No affected work linked.</p>}
      </section>
      <section className="receipt-chain" aria-label="Supersession chain">
        <h4>SUPERSESSION</h4>
        <div>
          {receipt.predecessor_id ? <button type="button" onClick={() => onOpenReceipt(receipt.predecessor_id!)}>← R-{shortId(receipt.predecessor_id)}</button> : <span>← ORIGIN</span>}
          <strong>THIS</strong>
          {receipt.successor_id ? <button type="button" onClick={() => onOpenReceipt(receipt.successor_id!)}>R-{shortId(receipt.successor_id)} →</button> : <span>CURRENT →</span>}
        </div>
      </section>
      <section className="receipt-revisions" aria-label="Revision timeline">
        <h4>REVISIONS</h4>
        {receipt.revisions?.length ? (
          <ol>
            {receipt.revisions.map((revision) => (
              <li key={revision.id}>
                <time dateTime={revision.created_at}>{humanDate(revision.created_at)}</time>
                <span>{revision.field_name}</span>
                <span>{revision.old_value || "—"} → {revision.new_value || "—"}</span>
              </li>
            ))}
          </ol>
        ) : <p className="quiet">No revisions recorded.</p>}
      </section>
    </article>
  );
}

function ReceiptField({ label, value }: { label: string; value: string | null | undefined }) {
  return <><dt>{label}</dt><dd>{value || "—"}</dd></>;
}
