import { wireDate } from "../surface/format";
import "./attention.css";
import { useEffect, useMemo, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  authorityBasisLabel,
  controlModeLabel,
  effectClassLabel,
  humanizeWireValue,
} from "../../lib/productLanguage";
import { useProjections } from "../projections";
import {
  dismissAftercare,
  useAftercare,
  useIntelligenceAttention,
} from "../intelligenceAttention";
import { openIntelligence } from "../intelligenceNavigation";
import { CycleGadget, FoldGadget, StringGadget } from "../surface/gadgets";
import { SurfaceCode, SurfaceState } from "../surface/Surface";
import { openPrimitive, openSurfaceWhenReady } from "../shell";
import {
  DeskWindowFrame,
  announceLauncher,
  retractLauncher,
} from "./DeskWindow";
import { MicButton } from "./MicButton";
import { SystemShade } from "./SystemShade";
import { OPEN_SYSTEM_SHADE_EVENT } from "../openObject";
import { refreshNeedsYou, useNeedsYou } from "../needsYou";
import { burstTimer } from "../burstTimer";
import { useRuntimeBus } from "../../runtime/RuntimeBus";

/** PHILO-13-03 (A2-W): a write anywhere on the Desk moves the ONE needs-you
 * number. The hub's `desk_changed` frame (debounced, as
 * `useDeskChangedRefresh` does) re-reads the shared snapshot fresh, so the
 * bell, the Dock and the Chair follow within a second -- never the minute
 * poll. */
export const NEEDS_YOU_CHANGED_DEBOUNCE_MS = 300;
function useNeedsYouOnDeskChanged(): void {
  const { subscribe } = useRuntimeBus();
  useEffect(() => {
    const burst = burstTimer(() => { void refreshNeedsYou(true); }, NEEDS_YOU_CHANGED_DEBOUNCE_MS);
    const unsubscribe = subscribe("desk_changed", burst.bump);
    return () => {
      burst.cancel();
      unsubscribe();
    };
  }, [subscribe]);
}

function when(raw: string) {
  const date = wireDate(raw);
  return !date ? raw : date.toLocaleString();
}

export function AttentionDrawer() {
  const store = useProjections();
  // HS-101 B6 — the bell opens the system shade; the full Desk-memory
  // browser stays one verb away inside it.
  const [shadeOpen, setShadeOpen] = useState(false);
  // Conductor R1: a Needs you row of a held tool call opens the shade.
  useEffect(() => {
    const open = () => setShadeOpen(true);
    window.addEventListener(OPEN_SYSTEM_SHADE_EVENT, open);
    return () => window.removeEventListener(OPEN_SYSTEM_SHADE_EVENT, open);
  }, []);
  const selected = useMemo(
    () => store.projections.find((row) => row.id === store.selectedId) ?? null,
    [store.projections, store.selectedId],
  );
  // Alias snake_case wire properties to camelCase for the face (UX-CANON raw-ids).
  const subjectLabel = selected?.subject_label;
  const reasonCode = selected ? String(selected.reason_code) : "";
  const decisionKind = selected ? String(selected.decision_kind) : "";
  const actualDest = selected?.actual_destination;
  const effectCls = selected?.effect_class;
  const needs = Number(store.counts.needs_attention || 0);
  // PHILO-13-03 (canvas C1-1): the Desk memory icon carries the ONE
  // needs-you number; the window's own counts stay below.
  const { count: needsYouCount } = useNeedsYou();
  useNeedsYouOnDeskChanged();
  const intelligence = useIntelligenceAttention();
  // HS-132-08 — a finished meeting is desk attention, not mascot business.
  const aftercare = useAftercare();
  /* A verb only where a door exists: a pipeline receipt with nothing behind
     it carries no door (holdspeak/db/projections.py) and gets no Open. */
  const hasDoor = (row: (typeof store.projections)[number]) =>
    Boolean(row.detail_url) && row.detail_url !== "/";
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
      badge: needsYouCount > 0 ? needsYouCount : undefined,
      activate: () => setShadeOpen(true),
    });
    return () => retractLauncher("attention");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [store.open, needsYouCount]);

  return (
    <>
      <SystemShade
        open={shadeOpen}
        onClose={() => setShadeOpen(false)}
        onOpenMemory={() => openSurfaceWhenReady("open-project-memory")}
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
            <Button dense variant="ghost" type="submit">Filter</Button>
              <MicButton draftScope="attention-search" onText={(t: string) => store.setQuery(t)} />
          </form>
          {aftercare ? (
            <section className="desk-attention-intelligence" aria-label="Meeting aftercare">
              <h3>Aftercare</h3>
              <Button
                dense
                onClick={() => {
                  openSurfaceWhenReady("review-meetings", `meeting:${aftercare.meetingId}`);
                  dismissAftercare();
                }}
              >
                {aftercare.title} · {aftercare.openTotal} open
              </Button>
              <Button dense variant="ghost" onClick={() => dismissAftercare()}>
                Dismiss
              </Button>
            </section>
          ) : null}
          {intelligence.briefReady || intelligence.overdue || intelligence.review ? (
            <section className="desk-attention-intelligence" aria-label="Intelligence attention">
              <h3>Intelligence</h3>
              {intelligence.briefReady ? <Button dense variant="ghost" onClick={() => openIntelligence({ view: "brief" })}>Brief ready</Button> : null}
              {intelligence.overdue ? <Button dense onClick={() => openIntelligence({ view: "follow-through", overdueOnly: true })}>{intelligence.overdue} overdue</Button> : null}
              {intelligence.review ? <Button dense variant="ghost" onClick={() => openIntelligence({ view: "receipts", whyOnly: true })}>{intelligence.review} receipt review{intelligence.review === 1 ? "" : "s"}</Button> : null}
            </section>
          ) : null}
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
              <Button dense variant="ghost" onClick={() => store.select(null)}>
                Back to list
              </Button>
              <small>{subjectLabel}</small>
              <h3>{selected.title}</h3>
              <p>{selected.summary}</p>
              <dl>
                <div>
                  <dt>Reason</dt>
                  <dd>{humanizeWireValue(reasonCode)}</dd>
                </div>
                <div>
                  <dt>Decision</dt>
                  <dd>{humanizeWireValue(decisionKind)}</dd>
                </div>
                <div>
                  <dt>Destination</dt>
                  <dd>{actualDest || "not reached"}</dd>
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
                {effectCls ? (
                  <div>
                    <dt>Effect</dt>
                    <dd>{effectClassLabel(effectCls)}</dd>
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
                    {humanizeWireValue(String(selected.source_kind))}
                  </dd>
                </div>
              </dl>
              <div className="desk-receipt-actions">
                {hasDoor(selected) ? (
                  <Button dense variant="ghost" onClick={() => openSource(selected)}>
                  Open source
                </Button>
                ) : null}
                {selected.attention_state === "needs_attention" ? (
                  <Button
                    dense
                    variant="ghost"
                    onClick={() =>
                      void store.present(selected.id, "acknowledge")
                    }
                  >
                    Acknowledge
                  </Button>
                ) : null}
                <Button
                  dense
                  variant="ghost"
                  onClick={() => void store.present(selected.id, "dismiss")}
                >
                  Dismiss card
                </Button>
              </div>
            </section>
          ) : (
            <>
              <ol className="desk-attention-list">
                {store.projections.map((row) => {
                  const rowLabel = row.subject_label;
                  const rowDest = row.actual_destination;
                  return (
                  <li key={row.id}>
                    <Button variant="ghost" onClick={() => store.select(row.id)}>
                      <span
                        className={`desk-projection-mark is-${row.severity}`}
                        aria-hidden="true"
                      />
                      <span>
                        <small>
                          {rowLabel} · {when(row.timestamp)}
                        </small>
                        <strong>{row.title}</strong>
                        <em>{rowDest || row.outcome}</em>
                      </span>
                    </Button>
                  </li>
                  );
                })}
              </ol>
              {!store.loading && store.projections.length === 0 ? (
                <SurfaceState
                  empty
                  emptyLabel="No matches"
                />
              ) : null}
              {store.page.has_more ? (
                store.loading ? (
                  <SurfaceState loading />
                ) : (
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => void store.loadMore()}
                  >
                    Load older
                  </Button>
                )
              ) : null}
            </>
          )}
      </DeskWindowFrame>
    </>
  );
}
