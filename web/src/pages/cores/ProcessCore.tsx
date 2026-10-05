import { wireClock } from "../../desk/surface/format";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { Fragment, useEffect } from "react";
import { countLabel } from "../../desk/surface";
import { useLaunchers } from "../../desk/components/DeskWindow";
import { useProcessWindow } from "../../desk/processWindow";
import type { ProcessRow } from "../../desk/processWindowReducer";
import { humanizeWireValue } from "../../lib/productLanguage";
import { kindWord, looksLikeId } from "../../desk/windowName";
import { objectByRef } from "../../desk/world";
import { useDesk } from "../../desk/store";
import type { Items } from "../../desk/api";
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
  // The kernel stamps epoch SECONDS; `new Date(seconds)` read them as
  // milliseconds and printed a clock in January 1970.
  return wireClock(value, true);
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

/** What a row's target says on the face (STATUS: no raw ids on faces;
 * Astra, #869: never a blank where the identity is):
 *   - "" only for a target that repeats the operation's own name
 *     (`desk:channel.save_destination`): it names nothing new;
 *   - a record the desk holds reads by its NAME (`Freeze the old ledger`);
 *   - a record the desk does not hold keeps an inspectable identity: its
 *     kind and a short id token (`Decision c9edf1`), so two rows never look
 *     the same;
 *   - any other target (`agent:build`) reads as the hub sent it. */
export function shownTarget(row: Pick<ProcessRow, "kind" | "target">, items?: Items): string {
  const target = row.target.trim();
  if (!target) return "";
  const colon = target.indexOf(":");
  const kind = colon > 0 ? target.slice(0, colon) : "";
  const rest = colon > 0 ? target.slice(colon + 1) : target;
  if (rest === row.kind || target === row.kind) return "";
  const named = items ? objectByRef(items, target) : null;
  if (named?.title) return named.title;
  if (looksLikeId(rest) || /^[0-9a-f]{10,}$/i.test(rest)) {
    const hex = rest.replace(/^[a-z]{1,12}_/i, "").replace(/-/g, "");
    return `${kindWord(kind) || "Record"} ${hex.slice(0, 6)}`;
  }
  return target;
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
  const items = useDesk((state) => state.items);
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
              /* The row wraps (the species' `wrap`): at 393 the facts fall
                 under the name, so the target is never squeezed to nothing
                 (Astra, #869: it measured 3 px and two decisions looked the
                 same). */
              wrap
              primary={
                <>
                  {depth > 0 ? "└ " : ""}
                  {row.kind.toUpperCase()}
                  {shownTarget(row, items) ? (
                    <span className="process-target" data-testid="process-target">{` · ${shownTarget(row, items)}`}</span>
                  ) : null}
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
              <span className="surface-token">{countLabel("RUNS", total)}</span>
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
            cols="process"
            count={countLabel(section.label.toUpperCase(), section.rows.length)}
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
              : `KERNEL · CURSOR ${store.cursor} · ${countLabel("RUNS", total)}`}
          </span>
        }
      />
    </>
  );
}
