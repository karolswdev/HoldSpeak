// PARKED by Betterment setup ST1 (2026-10-18): Accounts no longer shows the
// `Runs on 4 of 7 assigned` engine row; Engines is its one home, and Settings
// ▸ Meetings says "Summaries run on … Engines ›". Kept here, not deleted
// (CLAUDE.md: never delete; park). Excluded from tsc (tsconfig `_parked`).
import { Button } from "../../../components/signal/Signal";
import { StateChip } from "../../../desk/surface";
import type { ChipState } from "../../../desk/surface";
import type { ConnectionTool } from "../connections/api";

export function ModelsCard({
  tool,
  onOpen,
}: {
  tool: ConnectionTool | undefined;
  onOpen: () => void;
}) {
  const assigned = tool?.account?.assigned ?? 0;
  const total = tool?.account?.total ?? 7;
  // PHILO-15 B33: summaries that run on the route (the default or a pick)
  // are in use even when no group row is assigned.
  const summaryHost = tool?.account?.summary_host ?? null;
  const hasAssigned = assigned > 0;
  const inUse = hasAssigned || Boolean(summaryHost);
  const state: ChipState = inUse ? "active" : "idle";
  const label = hasAssigned ? "Assigned" : summaryHost ? "In use" : "Unassigned";
  const summary = hasAssigned
    ? `${assigned} of ${total} assigned`
    : summaryHost
      ? `Summaries · ${summaryHost}`
      : "Unassigned";

  return <div className="connections-engines" data-testid="connections-models"><span className="connections-tool-label">Engines</span>{summary !== label ? <span className="connections-tool-summary">{summary}</span> : <StateChip wrap state={state} label={label}/>}<Button dense variant="ghost" onClick={onOpen}>Choose engines</Button></div>;
}

