// HS-101 B6 — the system shade (DESIGN_SYSTEM.md, "The interior
// canon", OS territory §1): ONE surface behind the bell for what
// happened while you were away. Groups are honest — real feeds, real
// counts, zero says zero. The full Desk-memory browser (search,
// filters, receipt detail) stays one verb away.
import { useEffect, useRef, useState } from "react";
import { apiFetch, type JsonRecord } from "../../lib/api";
import { useProjections } from "../projections";
import { humanTime } from "../surface/format";

type Correction = Record<string, unknown>;

export function SystemShade({
  open,
  onClose,
  onOpenMemory,
}: {
  open: boolean;
  onClose: () => void;
  onOpenMemory: () => void;
}) {
  const store = useProjections();
  const [corrections, setCorrections] = useState<Correction[] | null>(null);
  const panel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    void store.refresh(true);
    void apiFetch<JsonRecord>("/api/dictation/corrections")
      .then((data) => {
        const rows = Array.isArray(data.items)
          ? data.items
          : Array.isArray(data.corrections)
            ? data.corrections
            : [];
        setCorrections(rows as Correction[]);
      })
      .catch(() => setCorrections([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    const onPointer = (event: PointerEvent) => {
      if (panel.current && !panel.current.contains(event.target as Node)) {
        onClose();
      }
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointer);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointer);
    };
  }, [open, onClose]);

  if (!open) return null;

  const needs = store.projections
    .filter((row) => row.attention_state === "needs_attention")
    .slice(0, 4);
  const finished = store.projections
    .filter((row) => row.attention_state !== "needs_attention")
    .slice(0, 4);
  const learned = (corrections ?? []).slice(0, 3);

  return (
    <div className="desk-shade" ref={panel} role="group" aria-label="While you were away">
      <div className="desk-shade-head">
        <span className="desk-shade-title">While you were away</span>
        <button
          type="button"
          className="desk-shade-memory"
          onClick={() => {
            onClose();
            onOpenMemory();
          }}
        >
          Desk memory
        </button>
      </div>

      <section className="desk-shade-group" aria-label="Needs you">
        <h4>
          Needs you <b>· {store.counts.needs_attention || 0}</b>
        </h4>
        {needs.length ? (
          needs.map((row) => (
            <div className="desk-shade-item" key={row.id}>
              <span className="desk-shade-glyph" aria-hidden="true">
                ◎
              </span>
              <div className="desk-shade-what">
                <strong>{row.title}</strong>
                <small>
                  {row.subject_label} · {humanTime(row.timestamp)}
                </small>
                <span className="desk-shade-do">
                  <a href={row.detail_url}>Open</a>
                  <button
                    type="button"
                    onClick={() => void store.present(row.id, "acknowledge")}
                  >
                    Acknowledge
                  </button>
                  <button
                    type="button"
                    className="is-quiet"
                    onClick={() => void store.present(row.id, "dismiss")}
                  >
                    Dismiss
                  </button>
                </span>
              </div>
            </div>
          ))
        ) : (
          <p className="desk-shade-quiet">Nothing needs you</p>
        )}
      </section>

      <section className="desk-shade-group" aria-label="Finished">
        <h4>
          Finished <b>· {store.counts.receipts || 0}</b>
        </h4>
        {finished.length ? (
          finished.map((row) => (
            <div className="desk-shade-item" key={row.id}>
              <span className="desk-shade-glyph" aria-hidden="true">
                ✦
              </span>
              <div className="desk-shade-what">
                <strong>{row.title}</strong>
                <small>
                  {row.outcome || row.subject_label} · {humanTime(row.timestamp)}
                </small>
                <span className="desk-shade-do">
                  <a href={row.detail_url}>Open</a>
                </span>
              </div>
            </div>
          ))
        ) : (
          <p className="desk-shade-quiet">Nothing finished while you were away</p>
        )}
      </section>

      <section className="desk-shade-group" aria-label="Learned">
        <h4>
          Learned <b>· {(corrections ?? []).length}</b>
        </h4>
        {learned.length ? (
          learned.map((row, index) => (
            <div className="desk-shade-item" key={String(row.id ?? index)}>
              <span className="desk-shade-glyph" aria-hidden="true">
                ⌁
              </span>
              <div className="desk-shade-what">
                <strong>
                  “{String(row.gist ?? row.kind ?? "")}” →{" "}
                  {String(row.value ?? row.replacement ?? "")}
                </strong>
              </div>
            </div>
          ))
        ) : (
          <p className="desk-shade-quiet">No corrections taught yet</p>
        )}
      </section>
    </div>
  );
}
