import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { boundaryEgressLamp } from "../../desk/inferenceEgress";
import { spriteUrl } from "../../desk/sprites";
import { AgentAvatar } from "../../desk/components/AgentAvatar";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
} from "../../desk/surface/Surface";
import { countToken } from "../../desk/surface/count";
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

  const load = useCallback(async () => {
    try {
      const res = await apiFetch<WorkbenchesListResponse>("/api/workbenches");
      const wbs = (res.workbenches || []) as WbSummary[];
      setWorkbenches(wbs);

      const allRuns: RunSummary[] = [];
      for (const wb of wbs.slice(0, 10)) {
        try {
          const runsRes = await apiFetch<WorkbenchRunsResponse>(`/api/workbenches/${wb.id}/runs`);
          for (const run of (runsRes.runs || []).slice(0, 5)) {
            allRuns.push({ ...run, workbench_name: wb.name });
          }
        } catch { /* */ }
      }
      allRuns.sort((a, b) => (b.started_at || "").localeCompare(a.started_at || ""));
      setRecentRuns(allRuns.slice(0, 10));
    } catch { /* */ }
    setLoading(false);
  }, []);

  useEffect(() => { void load(); }, [load]);

  const createWorkbench = () => void useDesk.getState().createPrimitive("workbench");

  const verbs = (
    <Button variant="ghost" dense onClick={createWorkbench}>
      + Create
    </Button>
  );

  if (loading) return <SurfaceState loading />;

  return (
    <>
      {renderHeroSlot(hero, verbs)}

      {workbenches.length === 0 ? (
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
            const needsYou = wb.pending_count > 0 || (wb.last_run?.status === "failed");
            return (
              <button
                key={wb.id}
                type="button"
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
                  {countToken(wb.pending_count, "PENDING") ? (
                    <span>{countToken(wb.pending_count, "PENDING")}</span>
                  ) : null}
                  {countToken(wb.item_count - wb.pending_count, "DONE") ? (
                    <span>{countToken(wb.item_count - wb.pending_count, "DONE")}</span>
                  ) : null}
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
              </button>
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
                    <span
                      className="desk-chip wb-badge-compact"
                      data-tone={run.status === "completed" ? "ok" : "fail"}
                    >
                      {run.status === "completed" ? "OK" : "FAIL"}
                    </span>
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
