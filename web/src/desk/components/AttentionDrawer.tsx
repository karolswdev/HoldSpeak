import { useEffect, useMemo, useState } from "react";
import {
  authorityBasisLabel,
  controlModeLabel,
  effectClassLabel,
  humanizeWireValue,
} from "../../lib/productLanguage";
import { useProjections } from "../projections";
import { CycleGadget, FoldGadget, StringGadget } from "../surface/gadgets";
import { SurfaceCode, SurfaceState } from "../surface/Surface";
import { openPrimitive, openSurfaceWhenReady } from "../shell";
import {
  DeskWindowFrame,
  announceLauncher,
  retractLauncher,
} from "./DeskWindow";
import { SystemShade } from "./SystemShade";

function when(raw: string) {
  const date = new Date(raw);
  return Number.isNaN(date.valueOf()) ? raw : date.toLocaleString();
}

export function AttentionDrawer() {
  const store = useProjections();
  // HS-101 B6 — the bell opens the system shade; the full Desk-memory
  // browser stays one verb away inside it.
  const [shadeOpen, setShadeOpen] = useState(false);
  const selected = useMemo(
    () => store.projections.find((row) => row.id === store.selectedId) ?? null,
    [store.projections, store.selectedId],
  );
  const needs = Number(store.counts.needs_attention || 0);
  const openSource = (row: (typeof store.projections)[number]) => {
    if (row.detail_url.startsWith("/history")) {
      openSurfaceWhenReady("review-meetings", row.subject_ref);
    } else if (row.detail_url === "/cadence") {
      openSurfaceWhenReady("configure-cadence", row.subject_ref);
    } else {
      openPrimitive(row.source_id);
    }
  };

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape" && store.open) store.setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [store.open]);

  // HS-97-07 — one shelf: the floating pill is gone; the dock carries
  // the launcher (and the needs-attention badge) instead.
  useEffect(() => {
    announceLauncher({
      id: "attention",
      label: "Desk memory",
      glyph: "◎",
      open: store.open,
      badge: needs > 0 ? needs : undefined,
      activate: () => setShadeOpen(true),
    });
    return () => retractLauncher("attention");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.open, needs]);

  return (
    <>
      <SystemShade
        open={shadeOpen}
        onClose={() => setShadeOpen(false)}
        onOpenMemory={() => store.setOpen(true)}
      />
      <DeskWindowFrame
        id="attention"
      glyph="◎"
        label="Desk memory"
        className="desk-attention-drawer"
        title="Desk memory"
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
              <StringGadget
                label="Search receipts"
                value={store.query}
                onChange={(next) => store.setQuery(next)}
              />
            </label>
            <label>
              <span>Show</span>
              <CycleGadget
                label="Show"
                value={store.kind}
                options={[
                  { value: "", label: "Everything" },
                  { value: "attention", label: "Needs / running" },
                  { value: "receipt", label: "Receipts" },
                ]}
                onChange={(next) =>
                  store.setKind(next as "" | "attention" | "receipt")
                }
              />
            </label>
            <button type="submit">Filter</button>
          </form>
          {store.error ? (
            <>
              <SurfaceState
                error="Desk memory unavailable"
                onRetry={() => void store.refresh(true)}
              />
              <FoldGadget title="RAW · DETAIL">
                <SurfaceCode>{store.error}</SurfaceCode>
              </FoldGadget>
            </>
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
                <button type="button" onClick={() => openSource(selected)}>
                  Open source
                </button>
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
                <SurfaceState
                  empty
                  emptyLabel="No matches"
                />
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
