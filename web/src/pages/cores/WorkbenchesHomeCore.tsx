import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { boundaryEgressLamp } from "../../desk/inferenceEgress";
import { AgentAvatar } from "../../desk/components/AgentAvatar";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceState,
} from "../../desk/surface/Surface";
import { renderHeroSlot } from "./core-layout";
import { LampGadget } from "../../desk/surface/gadgets";
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
  const inferenceTargets = useDesk((s) => s.inferenceTargets);
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
    <button type="button" className="desk-chip" onClick={createWorkbench}>
      ＋ Create
    </button>
  );

  if (loading) return <SurfaceState loading />;

  return (
    <>
      {renderHeroSlot(hero, verbs)}

      {workbenches.length === 0 ? (
        <SurfaceState
          empty
          emptyLabel="No workbenches yet"
          emptyGlyph="⚙"
        />
      ) : (
        <div className="wb-home-grid">
          {workbenches.map((wb) => {
            const recipe = recipes.find((r) => r.id === wb.recipe_id);
            const target = inferenceTargets.find((t) => t.id === wb.profile_id);
            const lamp = boundaryEgressLamp(target?.boundary);
            const needsYou = wb.pending_count > 0 || (wb.last_run?.status === "failed");
            return (
              <button
                key={wb.id}
                type="button"
                className="wb-home-card"
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
                    <span className="wb-home-card-icon">⚙</span>
                  )}
                  <span className="wb-home-card-name">{wb.name}</span>
                  {needsYou ? <span className="wb-home-needs" title="Needs attention" /> : null}
                </div>
                <div className="wb-home-card-stats">
                  {wb.pending_count > 0 ? (
                    <span>{wb.pending_count} pending</span>
                  ) : null}
                  {wb.item_count - wb.pending_count > 0 ? (
                    <span>{wb.item_count - wb.pending_count} done</span>
                  ) : null}
                  {wb.item_count === 0 ? <span>0 items</span> : null}
                </div>
                <div className="wb-home-card-meta">
                  <LampGadget
                    label={lamp.label}
                    on={lamp.tone !== "fail"}
                    tone={lamp.tone as "ok" | "warn" | "fail"}
                  />
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
                      className="desk-chip"
                      data-tone={run.status === "completed" ? "ok" : "fail"}
                      style={{ fontSize: "9px", height: "18px", padding: "0 6px" }}
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
    </>
  );
}
