import { useEffect, useMemo } from "react";
import {
  authorityBasisLabel,
  controlModeLabel,
  effectClassLabel,
  humanizeWireValue,
} from "../../lib/productLanguage";
import { useProjections } from "../projections";
import { DeskWindowFrame } from "./DeskWindow";

function when(raw: string) {
  const date = new Date(raw);
  return Number.isNaN(date.valueOf()) ? raw : date.toLocaleString();
}

export function AttentionDrawer() {
  const store = useProjections();
  const selected = useMemo(
    () => store.projections.find((row) => row.id === store.selectedId) ?? null,
    [store.projections, store.selectedId],
  );
  const needs = Number(store.counts.needs_attention || 0);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && store.open) store.setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [store.open]);

  return (
    <>
      <button
        type="button"
        className="desk-attention-launch"
        aria-controls="desk-memory-drawer"
        aria-expanded={store.open}
        onClick={() => store.setOpen(!store.open)}
      >
        <span aria-hidden="true">◎</span>
        Desk memory
        {needs > 0 ? (
          <strong aria-label={`${needs} need attention`}>{needs}</strong>
        ) : null}
      </button>
      <DeskWindowFrame
        id="attention"
      glyph="◎"
        label="Desk memory"
        className="desk-attention-drawer"
        eyebrow="Attention and Receipts"
        title={<h2 className="desk-panel-title">Desk memory</h2>}
        entrance={false}
        open={store.open}
        onClose={() => store.setOpen(false)}
      >
          <div className="desk-attention-counts" aria-live="polite">
            <span>
              <b>{needs}</b> need attention
            </span>
            <span>
              <b>{store.counts.receipts || 0}</b> Receipts
            </span>
            <span>
              <b>{store.page.total}</b> matching
            </span>
          </div>
          <form
            className="desk-attention-filters"
            onSubmit={(event) => {
              event.preventDefault();
              void store.refresh(true);
            }}
          >
            <label>
              <span>Search</span>
              <input
                value={store.query}
                onChange={(event) => store.setQuery(event.target.value)}
              />
            </label>
            <label>
              <span>Show</span>
              <select
                value={store.kind}
                onChange={(event) =>
                  store.setKind(
                    event.target.value as "" | "attention" | "receipt",
                  )
                }
              >
                <option value="">Everything</option>
                <option value="attention">Needs / running</option>
                <option value="receipt">Receipts</option>
              </select>
            </label>
            <button type="submit">Filter</button>
          </form>
          {store.error ? (
            <div className="desk-attention-error" role="alert">
              <span>{store.error}</span>
              <button type="button" onClick={() => void store.refresh(true)}>
                Retry
              </button>
            </div>
          ) : null}
          {selected ? (
            <section
              className="desk-receipt-detail"
              aria-label={`${selected.title} detail`}
            >
              <button type="button" onClick={() => store.select(null)}>
                ← Back to list
              </button>
              <small>{selected.subject_label}</small>
              <h3>{selected.title}</h3>
              <p>{selected.summary}</p>
              <dl>
                <div>
                  <dt>Reason</dt>
                  <dd>{humanizeWireValue(String(selected.reason_code))}</dd>
                </div>
                <div>
                  <dt>Decision</dt>
                  <dd>{humanizeWireValue(String(selected.decision_kind))}</dd>
                </div>
                <div>
                  <dt>Destination</dt>
                  <dd>{selected.actual_destination || "not reached"}</dd>
                </div>
                <div>
                  <dt>Authority</dt>
                  <dd>
                    {selected.authority_basis
                      ? authorityBasisLabel(selected.authority_basis)
                      : "not required"}
                  </dd>
                </div>
                {selected.control_mode ? (
                  <div>
                    <dt>Control posture</dt>
                    <dd>
                      {controlModeLabel(selected.control_mode)}
                      {selected.policy_version
                        ? ` · ${selected.policy_version}`
                        : ""}
                    </dd>
                  </div>
                ) : null}
                {selected.effect_class ? (
                  <div>
                    <dt>Effect</dt>
                    <dd>{effectClassLabel(selected.effect_class)}</dd>
                  </div>
                ) : null}
                <div>
                  <dt>Attempt / outcome</dt>
                  <dd>
                    {selected.attempt ?? "—"} · {selected.outcome}
                  </dd>
                </div>
                <div>
                  <dt>When</dt>
                  <dd>{when(selected.timestamp)}</dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>
                    {selected.source_kind} · {selected.source_id}
                  </dd>
                </div>
              </dl>
              <div className="desk-receipt-actions">
                <a href={selected.detail_url}>Open source</a>
                {selected.attention_state === "needs_attention" ? (
                  <button
                    type="button"
                    onClick={() =>
                      void store.present(selected.id, "acknowledge")
                    }
                  >
                    Acknowledge
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => void store.present(selected.id, "dismiss")}
                >
                  Dismiss card
                </button>
              </div>
            </section>
          ) : (
            <>
              <ol className="desk-attention-list">
                {store.projections.map((row) => (
                  <li key={row.id}>
                    <button type="button" onClick={() => store.select(row.id)}>
                      <span
                        className={`desk-projection-mark is-${row.severity}`}
                        aria-hidden="true"
                      />
                      <span>
                        <small>
                          {row.subject_label} · {when(row.timestamp)}
                        </small>
                        <strong>{row.title}</strong>
                        <em>{row.actual_destination || row.outcome}</em>
                      </span>
                    </button>
                  </li>
                ))}
              </ol>
              {!store.loading && store.projections.length === 0 ? (
                <p className="desk-attention-empty">
                  Nothing matches. Receipts remain in their source journals.
                </p>
              ) : null}
              {store.page.has_more ? (
                <button
                  className="desk-attention-more"
                  type="button"
                  disabled={store.loading}
                  onClick={() => void store.loadMore()}
                >
                  {store.loading
                    ? "Loading…"
                    : `Load older (${store.page.total - store.projections.length} remain)`}
                </button>
              ) : null}
            </>
          )}
      </DeskWindowFrame>
    </>
  );
}
