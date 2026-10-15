import type { WorkbenchRun } from "../../detail-types";
import { boundaryEgressLamp } from "../../inferenceEgress";
import { humanTime } from "../../surface/format";
import { GadgetGroup } from "../../surface/gadgets";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
} from "../../surface/Surface";

export function WorkbenchRunsWing({
  runs,
  configured,
  running,
  loading = false,
  error,
  onRetry,
  openRunId,
  onToggleRun,
  onRun,
  onBindAgent,
  engineMissing = false,
  onChooseEngine,
}: {
  runs: WorkbenchRun[];
  configured: boolean;
  running: boolean;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  openRunId: string | null;
  onToggleRun: (runId: string) => void;
  onRun: () => void;
  onBindAgent: () => void;
  engineMissing?: boolean;
  onChooseEngine?: () => void;
}) {
  return (
    <div className="wb-runs-wing">
      <GadgetGroup label={runs.length > 0 ? `RUNS ${runs.length}` : "RUNS"} material="inset">
      {error ? <SurfaceState error={error} onRetry={loading ? undefined : onRetry} /> : null}
      {loading && !runs.length && !error ? <SurfaceState loading /> : null}
      <SurfaceLedger>
        {runs.length === 0 && !loading && !error ? (
          <SurfaceState
            empty
            emptyLabel={!configured ? "No agent bound" : engineMissing ? "No engine" : "No runs yet"}
            emptyGlyph="○"
            actionLabel={!configured ? "Bind an agent" : engineMissing ? "Choose engine" : "Run now"}
            onAction={!configured ? onBindAgent : engineMissing ? onChooseEngine : (running ? undefined : onRun)}
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
      </GadgetGroup>
    </div>
  );
}
