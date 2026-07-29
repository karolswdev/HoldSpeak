// HS-109-06 — the process window: a read-only fold over kernel read + events.
import { useEffect } from "react";
import { StatusPill } from "../../components/signal/Signal";
import { useLaunchers } from "../../desk/components/DeskWindow";
import { useProcessWindow } from "../../desk/processWindow";
import type { ProcessRow } from "../../desk/processWindowReducer";
import {
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { humanTime } from "../../desk/surface/format";
import type { CoreProps } from "./ActivityCore";

function label(value: string): string {
  const words = value.replace(/[._-]+/g, " ").trim();
  return words ? words.replace(/^./, (first) => first.toUpperCase()) : "Unknown";
}

function tone(row: ProcessRow): "neutral" | "success" | "warning" | "error" | "live" {
  const state = row.state.toLowerCase();
  if (state === "failed" || state === "refused") return "error";
  if (state === "ended" || state === "succeeded" || state === "complete") return "success";
  if (state === "running" || state === "starting" || state === "claimed") return "live";
  if (row.latestEventType === "operation.awaiting_decision" || state === "waiting")
    return "warning";
  return "neutral";
}

function ProcessOperationRow({
  row,
  openDecisions,
}: {
  row: ProcessRow;
  openDecisions: () => void;
}) {
  const isDecision = row.latestEventType === "operation.awaiting_decision";
  const detail = [
    row.principal,
    row.placement,
    row.head,
    ...row.refs.filter((ref) => ref !== row.target),
  ].filter(Boolean);
  return (
    <SurfaceRow
      glyph={row.children.length ? "⌄" : "·"}
      title={
        <>
          {label(row.kind)}
          {row.target ? ` · ${row.target}` : ""}
        </>
      }
      detail={detail.join(" · ")}
      meta={
        <span className="process-row-state">
          <StatusPill tone={tone(row)}>{label(row.state)}</StatusPill>
          <time>{humanTime(row.timestamp)}</time>
        </span>
      }
      verbs={
        isDecision ? (
          <a
            className="btn btn--ghost btn--sm"
            href="/#attention"
            onClick={(event) => {
              event.preventDefault();
              openDecisions();
            }}
          >
            Review
          </a>
        ) : undefined
      }
      quiet={row.state === "ended" || row.state === "succeeded"}
    >
      {row.children.length ? (
        <SurfaceRows>
          {row.children.map((child) => (
            <ProcessOperationRow
              key={child.operationId}
              row={child}
              openDecisions={openDecisions}
            />
          ))}
        </SurfaceRows>
      ) : null}
    </SurfaceRow>
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

  const total = store.sections.reduce((count, section) => count + section.rows.length, 0);
  const openDecisions = () => decisions?.activate();
  return (
    <>
      <SurfaceVerbs
        status={
          store.error
            ? "Kernel unavailable"
            : store.inflight
              ? "Watching…"
              : `${total} ${total === 1 ? "run" : "runs"}`
        }
      />
      <SurfaceState
        loading={store.loading}
        error={store.error}
        onRetry={() => void useProcessWindow.getState().poll()}
      >
        {store.sections.map((section) => (
          <SurfaceSection
            key={section.id}
            label={`${section.label} · ${section.rows.length}`}
          >
            {section.rows.length ? (
              <SurfaceRows>
                {section.rows.map((row) => (
                  <ProcessOperationRow
                    key={row.operationId}
                    row={row}
                    openDecisions={openDecisions}
                  />
                ))}
              </SurfaceRows>
            ) : null}
          </SurfaceSection>
        ))}
      </SurfaceState>
    </>
  );
}
