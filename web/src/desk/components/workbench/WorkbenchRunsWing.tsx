import type { WorkbenchRun } from "../../detail-types";
import { boundaryEgressLamp } from "../../inferenceEgress";
import { humanTime } from "../../surface/format";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
} from "../../surface/Surface";

export function WorkbenchRunsWing({
  runs,
  configured,
  running,
  openRunId,
  onToggleRun,
  onRun,
  onBindAgent,
}: {
  runs: WorkbenchRun[];
  configured: boolean;
  running: boolean;
  openRunId: string | null;
  onToggleRun: (runId: string) => void;
  onRun: () => void;
  onBindAgent: () => void;
}) {
  return (
    <div className="wb-runs-wing">
      <SurfaceLedger count={runs.length > 0 ? `${runs.length} RUNS` : "RUNS"}>
        {runs.length === 0 ? (
          <SurfaceState
            empty
            emptyLabel={configured ? "No runs yet" : "No agent bound"}
            emptyGlyph="○"
            actionLabel={configured ? "Run now" : "Bind an agent"}
            onAction={configured ? (running ? undefined : onRun) : onBindAgent}
          />
        ) : null}
        {runs.map((run) => {
          const runLamp = boundaryEgressLamp(run.egress_boundary);
          const totalTok = run.total_tokens;
          const completedAt = run.completed_at;
          const statusChip =
            run.status === "completed"
              ? { label: "COMPLETED", tone: "ok" }
              : run.status === "running"
                ? { label: "RUNNING", tone: "warn" }
                : { label: "FAILED", tone: "fail" };
          return (
            <SurfaceLedgerRow
              key={run.id}
              time={humanTime(run.started_at)}
              primary={
                <>
                  {run.items_completed}/{run.items_attempted} done
                  {run.items_failed ? ` · ${run.items_failed} failed` : ""}
                  {" · "}
                  {runLamp.label}
                  {run.model ? ` · ${run.model}` : ""}
                </>
              }
              cells={
                <span className="desk-chip" data-tone={statusChip.tone}>
                  {statusChip.label}
                </span>
              }
              open={openRunId === run.id}
              onToggle={() => onToggleRun(run.id)}
            >
              <div className="wb-run-detail">
                <dl className="surface-facts">
                  <div><dt>egress</dt><dd>{runLamp.label}</dd></div>
                  <div><dt>model</dt><dd>{run.model || "—"}</dd></div>
                  <div><dt>tokens</dt><dd>{totalTok.toLocaleString()}</dd></div>
                  {completedAt ? (
                    <div><dt>completed</dt><dd>{humanTime(completedAt)}</dd></div>
                  ) : null}
                </dl>
              </div>
            </SurfaceLedgerRow>
          );
        })}
      </SurfaceLedger>
    </div>
  );
}
