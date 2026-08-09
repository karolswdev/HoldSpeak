import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-109-06 — the process window: a read-only fold over kernel read + events.
// HS-111-06 — the process monitor face (audit §3.2): SurfaceLedger tables,
// states as surface-tokens (StatusPill died), the zero face renders every
// section head at 0 (an instrument panel, never a void). The wire —
// processWindow.ts + processWindowReducer.ts — is byte-untouched.
import { Fragment, useEffect } from "react";
import { useLaunchers } from "../../desk/components/DeskWindow";
import { useProcessWindow } from "../../desk/processWindow";
import type { ProcessRow } from "../../desk/processWindowReducer";
import { humanizeWireValue } from "../../lib/productLanguage";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { LampGadget } from "../../desk/surface/gadgets";
import type { CoreProps } from "./core-types";

/** The fixed HH:MM:SS clock cell (mono, tabular). */
function clockToken(value: string | number | ""): string {
  if (value === "" || value === null || value === undefined) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

/** State as the etched token it is — tone, never a colored pill. */
function stateTone(row: ProcessRow): "warn" | "danger" | "ok" | undefined {
  const state = row.state.toLowerCase();
  if (state === "failed" || state === "refused") return "danger";
  if (row.latestEventType === "operation.awaiting_decision" || state === "waiting")
    return "warn";
  if (state === "running" || state === "starting" || state === "claimed")
    return "ok";
  return undefined;
}

function stateToken(row: ProcessRow): string {
  if (row.latestEventType === "operation.awaiting_decision") return "NEEDS YOU";
  return row.state ? row.state.toUpperCase() : "UNKNOWN";
}

function LedgerRows({
  rows,
  openDecisions,
  depth = 0,
}: {
  rows: ProcessRow[];
  openDecisions: () => void;
  depth?: number;
}) {
  return (
    <>
      {rows.map((row) => {
        const isDecision =
          row.latestEventType === "operation.awaiting_decision";
        const facts = [
          row.principal ? humanizeWireValue(String(row.principal)) : "",
          row.placement ? humanizeWireValue(String(row.placement)) : "",
        ].filter(Boolean);
        return (
          <Fragment key={row.operationId}>
            <SurfaceLedgerRow
              time={clockToken(row.timestamp)}
              primary={
                <>
                  {depth > 0 ? "└ " : ""}
                  {row.kind.toUpperCase()}
                  {row.target ? ` · ${row.target}` : ""}
                </>
              }
              cells={
                <>
                  {facts.length ? (
                    <span className="surface-ledger-cell">
                      {facts.join(" · ")}
                    </span>
                  ) : null}
                  <span className="surface-ledger-cell">
                    <span className="surface-token" data-tone={stateTone(row)}>
                      {stateToken(row)}
                    </span>
                  </span>
                  {isDecision ? (
                    <span className="surface-ledger-cell">
                      <a
                        className="surface-token"
                        data-tone="warn"
                        href="/#attention"
                        onClick={(event) => {
                          event.preventDefault();
                          openDecisions();
                        }}
                      >
                        ANSWER
                      </a>
                    </span>
                  ) : null}
                </>
              }
            />
            {row.children.length ? (
              <LedgerRows
                rows={row.children}
                openDecisions={openDecisions}
                depth={depth + 1}
              />
            ) : null}
          </Fragment>
        );
      })}
    </>
  );
}

export function ProcessCore(_props: CoreProps) {
  const store = useProcessWindow();
  const launchers = useLaunchers();
  const decisions = launchers.find((launcher) => launcher.id === "attention");

  useEffect(() => {
    useProcessWindow.getState().start();
    return () => useProcessWindow.getState().stop();
  }, []);

  const total = store.sections.reduce(
    (count, section) => count + section.rows.length,
    0,
  );
  const openDecisions = () => decisions?.activate();
  return (
    <>
      <SurfaceVerbs
        status={
          store.error ? (
            "Kernel unavailable"
          ) : (
            <>
              <LampGadget label="WATCHING" on tone="ok" />
              <span className="surface-token">{`RUNS ${total}`}</span>
            </>
          )
        }
      />
      {store.error ? (
        <SurfaceState
          error={store.error}
          onRetry={() => void useProcessWindow.getState().poll()}
        />
      ) : (
        /* Every section renders AT ZERO — even before the first page
           lands, the monitor's frame IS the instrument; silence is
           never an empty window (audit P2). */
        store.sections.map((section) => (
          <SurfaceLedger
            key={section.id}
            count={`${section.label.toUpperCase()} ${section.rows.length}`}
          >
            {section.rows.length ? (
              <ul className="surface-ledger-rows">
                <LedgerRows rows={section.rows} openDecisions={openDecisions} />
              </ul>
            ) : null}
          </SurfaceLedger>
        ))
      )}
      {/* HS-129-05 — the kernel fact uses the shared receipt slot. */}
      <SurfaceFooter
        receipt={
          <span className="surface-footer-receipt-line" role="status">
            {store.error
              ? `KERNEL UNREACHABLE · CURSOR ${store.cursor}`
              : `KERNEL · CURSOR ${store.cursor} · RUNS ${total}`}
          </span>
        }
      />
    </>
  );
}
