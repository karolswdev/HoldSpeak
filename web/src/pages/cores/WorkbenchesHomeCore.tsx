import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { boundaryEgressLamp } from "../../desk/inferenceEgress";
import { spriteUrl } from "../../desk/sprites";
import { AgentAvatar } from "../../desk/components/AgentAvatar";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
} from "../../desk/surface/Surface";
import { countToken } from "../../desk/surface/count";
import { StateChip } from "../../desk/surface";
import { renderHeroSlot } from "./core-layout";
import { humanTime } from "../../desk/surface/format";
import type {
  CoreProps,
  WbSummary,
  RunSummary,
  WorkbenchesListResponse,
  WorkbenchRunsResponse,
} from "./core-types";

function humanSchedule(cron: string | null): string {
  if (!cron) return "Manual";
  const presets: Record<string, string> = {
    "0 7 * * *": "7 AM daily",
    "0 7 * * 1-5": "7 AM weekdays",
    "0 2 * * *": "2 AM nightly",
    "0 * * * *": "Every hour",
  };
  return presets[cron] || cron;
}

export function WorkbenchesHomeCore({ hero }: CoreProps) {
  const recipes = useDesk((s) => s.items.recipe);
  const [workbenches, setWorkbenches] = useState<WbSummary[]>([]);
  const [recentRuns, setRecentRuns] = useState<RunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [runsError, setRunsError] = useState("");

  const load = useCallback(async (quiet = false) => {
    if (!quiet) {
      setLoading(true);
      setLoadError("");
      setRunsError("");
    }
    try {
      const res = await apiFetch<WorkbenchesListResponse>("/api/workbenches");
      const wbs = (res.workbenches || []) as WbSummary[];
      setWorkbenches(wbs);
      setLoaded(true);
      setLoadError("");

      const allRuns: RunSummary[] = [];
      const failedIds = new Set<string>();
      const failures: string[] = [];
      for (const wb of wbs.slice(0, 10)) {
        try {
          const runsRes = await apiFetch<WorkbenchRunsResponse>(`/api/workbenches/${wb.id}/runs`);
          for (const run of (runsRes.runs || []).slice(0, 5)) {
            allRuns.push({ ...run, workbench_name: wb.name });
          }
        } catch (error) {
          failedIds.add(wb.id);
          failures.push(`${wb.name} · ${readableError(error)}`);
        }
      }
      setRecentRuns((previous) => [
        ...allRuns,
        ...previous.filter((run) => failedIds.has(run.workbench_id)),
      ].sort((a, b) => (b.started_at || "").localeCompare(a.started_at || "")).slice(0, 10));
      setRunsError(failures.length ? `Runs not loaded · ${failures.join("; ")}` : "");
    } catch (error) {
      setLoadError(`Workbenches not loaded · ${readableError(error)}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);
  useOnDeskChanged(() => void load(true));

  const createWorkbench = () => void useDesk.getState().createPrimitive("workbench");

  const verbs = (
    <Button variant="ghost" dense onClick={createWorkbench}>
      + Create
    </Button>
  );

  if (loading && !loaded) return <SurfaceState loading />;

  return (
    <>
      {renderHeroSlot(hero, verbs)}
      {loadError ? <SurfaceState error={loadError} onRetry={loading ? undefined : () => void load()} /> : null}
      {runsError ? <SurfaceState error={runsError} onRetry={loading ? undefined : () => void load()} /> : null}
      {loading ? <SurfaceState loading /> : null}

      {loaded && workbenches.length === 0 ? (
        <SurfaceState
          empty
          emptyLabel="No workbenches yet"
          emptyGlyph="⊞"
        />
      ) : (
        <div className="wb-home-grid">
          {workbenches.map((wb) => {
            const recipe = recipes.find((r) => r.id === wb.recipe_id);
            const assignment = wb.assignment_summary;
            const activeItems = wb.items?.filter((item) => !item.parked);
            const doneCount = activeItems?.filter((item) => item.status === "done").length;
            const failedCount = activeItems?.filter((item) => item.status === "failed").length;
            const claimedCount = activeItems?.filter((item) => item.status === "claimed").length;
            const needsYou = wb.pending_count > 0 || Boolean(failedCount) || (wb.last_run?.status === "failed");
            return (
              <Button
                key={wb.id}
                variant="chrome"
                className="wb-home-card"
                data-needs={needsYou ? "true" : undefined}
                onClick={() => useDesk.getState().openWorkbenchWindow(wb.id)}
              >
                <div className="wb-home-card-head">
                  {recipe ? (
                    <AgentAvatar
                      avatar={String(recipe.avatar || "")}
                      id={String(recipe.id)}
                      kind="agent"
                      size={16}
                    />
                  ) : (
                    <img src={spriteUrl("workbench", wb.id)} alt="" width={16} height={16} className="desk-chrome-sprite" />
                  )}
                  <span className="wb-home-card-name">{wb.name}</span>
                </div>
                <div className="wb-home-card-stats">
                  {countToken(wb.item_count, "ITEM") ? <span>{countToken(wb.item_count, "ITEM")}</span> : null}
                  {countToken(wb.pending_count, "PENDING") ? (
                    <span>{countToken(wb.pending_count, "PENDING")}</span>
                  ) : null}
                  {doneCount !== undefined && countToken(doneCount, "DONE") ? (
                    <span>{countToken(doneCount, "DONE")}</span>
                  ) : null}
                  {countToken(failedCount, "FAILED") ? <span>{countToken(failedCount, "FAILED")}</span> : null}
                  {countToken(claimedCount, "IN PROGRESS", "IN PROGRESS") ? <span>{countToken(claimedCount, "IN PROGRESS", "IN PROGRESS")}</span> : null}
                  {wb.item_count === 0 ? <span>Empty</span> : null}
                </div>
                <div className="wb-home-card-meta">
                  <span className="wb-home-card-assignment">
                    {assignment?.chain.length
                      ? `Uses ${assignment.source ? `${assignment.source} · ` : ""}${assignment.chain.join(" → ")}`
                      : assignment?.repair || "No default model"}
                  </span>
                  <span className="wb-home-card-schedule">
                    {wb.schedule_enabled ? humanSchedule(wb.schedule) : "Manual"}
                  </span>
                </div>
              </Button>
            );
          })}
        </div>
      )}

      {recentRuns.length > 0 ? (
        <div className="wb-home-runs">
          <SurfaceLedger count="RECENT RUNS">
            {recentRuns.map((run) => {
              const lamp = boundaryEgressLamp(run.egress_boundary);
              return (
                <SurfaceLedgerRow
                  key={run.id}
                  time={humanTime(run.started_at)}
                  primary={
                    <>
                      {run.workbench_name}
                      {" · "}
                      {run.items_completed}/{run.items_attempted} done
                      {run.items_failed ? ` · ${run.items_failed} failed` : ""}
                      {" · "}
                      {lamp.label}
                    </>
                  }
                  cells={
                    <StateChip
                      state={run.status === "completed" ? "success" : run.status === "running" ? "working" : run.status === "failed" ? "failure" : "idle"}
                      label={run.status ? run.status.replaceAll("_", " ").replace(/^./, (letter) => letter.toUpperCase()) : "Unknown"}
                      wrap
                    />
                  }
                  expands={false}
                  onToggle={() =>
                    useDesk.getState().openWorkbenchWindow(run.workbench_id)
                  }
                />
              );
            })}
          </SurfaceLedger>
        </div>
      ) : null}
      <SurfaceFooter />
    </>
  );
}
