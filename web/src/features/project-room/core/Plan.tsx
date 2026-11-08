// The Plan fold: the project's milestones and risks as a timeline.
import React, { useCallback, useEffect, useState } from "react";
import { DotWord, StateChip, SurfaceSection, type ObjectTone } from "../../../desk/surface";
import { apiFetch } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { useRoomRead } from "../roomReads";
import { pluralize } from "../steward/model";

/* ── ITEMS section (PHILO-9-03, the Q3 ruling; the ratified items canvas) ──
 * The project's milestones and risks (and any other item), read from the
 * existing `GET /api/projects/{id}/items`. No Add control: items enter by
 * owner-authenticated MCP (`project.item.create`). No verbs on a row.
 * Order: late milestones first (most late first), then open risks (by
 * severity), then planned milestones by date, then missed, then the closed
 * rest. Zero items (the read succeeded): the section is omitted. A failed
 * read is ITEMS UNAVAILABLE with Retry, never empty. */

type ItemRow = {
  id: string;
  item_type: string;
  title: string;
  lifecycle: string;
  severity: string | null;
  due_at: string | null;
  details_json: string | null;
};

// W3-B (atlas 2026-10-27): the Plan's dates are sentence-case sans (`Jul 15`).
const ITEM_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function dayNumber(ymd: string): number {
  const [y, m, d] = ymd.slice(0, 10).split("-").map(Number);
  return Math.round(new Date(y, m - 1, d).getTime() / 86_400_000);
}
function todayNumber(): number {
  const n = new Date();
  return Math.round(new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime() / 86_400_000);
}
/** Days late for a planned milestone past its date; 0 otherwise. */
function daysLate(item: ItemRow): number {
  if (item.item_type !== "milestone" || item.lifecycle !== "planned" || !item.due_at) return 0;
  return Math.max(0, todayNumber() - dayNumber(item.due_at));
}
const CLOSED = new Set(["reached", "missed", "dropped", "mitigated", "accepted", "closed", "resolved", "retired", "done"]);
const SEVERITY_ORDER: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };

function itemRank(item: ItemRow): [number, number] {
  const late = daysLate(item);
  if (late > 0) return [0, -late];
  if (item.lifecycle === "missed") return [3, 0];
  if (CLOSED.has(item.lifecycle)) return [4, 0];
  if (item.item_type === "risk") return [1, SEVERITY_ORDER[item.severity ?? ""] ?? 9];
  return [2, item.due_at ? dayNumber(item.due_at) : Number.MAX_SAFE_INTEGER];
}

/** The item's kind and state as plain pills (soft tint, round lamp). */
function ItemPills({ item }: { item: ItemRow }) {
  const late = daysLate(item);
  let details: Record<string, unknown> = {};
  try { details = item.details_json ? JSON.parse(item.details_json) : {}; } catch { details = {}; }
  // W3-B (atlas 2026-10-27): the row grammar of the Now wing (#1483): the
  // facts quiet at the row's right, the state a dot and a word (no pill).
  const states: { text: string; tone: ObjectTone | "idle" }[] = [];
  if (late > 0) states.push({ text: `${pluralize(late, "day", "days")} late`, tone: "fail" });
  else if (item.lifecycle === "missed") states.push({ text: "Missed", tone: "fail" });
  else if (item.lifecycle === "dropped") states.push({ text: "Dropped", tone: "idle" });
  else if (CLOSED.has(item.lifecycle)) states.push({ text: plainWord(item.lifecycle), tone: "ok" });
  else if (item.item_type === "risk") states.push({ text: "Open risk", tone: "warn" });
  const facts: string[] = [plainWord(item.item_type)];
  if (item.item_type === "risk") {
    if (details.likelihood) facts.push(`likelihood ${String(details.likelihood).toLowerCase()}`);
    if (details.impact) facts.push(`impact ${String(details.impact).toLowerCase()}`);
  }
  return (
    <span className="room-row-meta">
      <span className="room-row-facts">{facts.join(" · ")}</span>
      {states.map((t, i) => (
        <DotWord key={i} tone={t.tone} className="room-plan-state" data-testid="item-token">
          {t.text}
        </DotWord>
      ))}
    </span>
  );
}

function plainWord(word: string): string {
  if (word.length <= 2) return word.toUpperCase();
  const w = word.replace(/_/g, " ").toLowerCase();
  return w.charAt(0).toUpperCase() + w.slice(1);
}

/** The bead's tone on the plan rail. */
function itemBead(item: ItemRow): string {
  if (daysLate(item) > 0 || item.lifecycle === "missed") return "danger";
  if (item.lifecycle === "dropped") return "idle";
  if (CLOSED.has(item.lifecycle)) return "ok";
  if (item.item_type === "risk") return "warn";
  return "planned";
}

function railDate(ymd: string | null): string {
  if (!ymd) return "";
  const [, m, d] = ymd.slice(0, 10).split("-").map(Number);
  if (!m || !d) return "";
  return `${ITEM_MONTHS[m - 1]} ${d}`;
}

/** PHILO-17 refit: the project's items, read once for the head and the plan. */
export type ItemsRead = { items: ItemRow[] | null; failed: boolean; retry: () => void };

export function useRoomItems(projectId: string, revision: number): ItemsRead {
  const [items, setItems] = useState<ItemRow[] | null>(null);
  // A failed read is UNAVAILABLE, never empty (Codex Astra canvases r1 F7).
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!projectId) return;
    let live = true;
    apiFetch<{ items: ItemRow[] }>(`/api/projects/${encodeURIComponent(projectId)}/items?limit=200`)
      .then((r) => { if (live) { setFailed(false); setItems(r.items ?? []); } })
      .catch(() => { if (live) { setFailed(true); setItems(null); } });
    return () => { live = false; };
  }, [projectId, revision, attempt]);
  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { items, failed, retry };
}

/** The late milestones, most late first. */
function lateOf(items: ItemRow[] | null): ItemRow[] | null {
  if (!items) return null;
  return items.filter((i) => daysLate(i) > 0).sort((a, b) => daysLate(b) - daysLate(a));
}

/** PHILO-17 refit: the PLAN, the project as a timeline (the Today spine):
 *  a paper well, the dates in the gutter, a dotted rail with a bead per
 *  item, NOW between the past and the future, and the most late milestone
 *  as the focus plate (a Workbench title bar). No verbs: items enter by MCP. */
export function ItemsSection({ read }: { read: ItemsRead }) {
  const { items, failed, retry } = read;
  useRoomRead("items", items !== null || failed);
  if (failed) {
    return (
      <SurfaceSection
        label="Plan"
        actions={
          <Button dense variant="ghost" onClick={retry} data-testid="items-retry">
            Retry
          </Button>
        }
      >
        <span data-testid="items-unavailable">
          <StateChip state="unreachable" label="ITEMS UNAVAILABLE" />
        </span>
      </SurfaceSection>
    );
  }
  if (items === null) return null;
  if (items.length === 0) return null;
  const focus = lateOf(items)?.[0] ?? null;
  // Dated items by date; the undated after them (risks first, by severity).
  const dated = items.filter((i) => i.due_at).sort((a, b) =>
    dayNumber(a.due_at as string) - dayNumber(b.due_at as string) || a.title.localeCompare(b.title));
  const undated = items.filter((i) => !i.due_at).sort((a, b) => {
    const [ra, sa] = itemRank(a);
    const [rb, sb] = itemRank(b);
    return ra - rb || sa - sb || a.title.localeCompare(b.title);
  });
  const today = todayNumber();
  const nowAt = dated.findIndex((i) => dayNumber(i.due_at as string) > today);
  const nodes: React.ReactNode[] = [];
  const nowNode = (
    <li key="now" className="room-plan-now" data-testid="room-plan-now" aria-label="Today">
      <span className="room-plan-time">Today</span>
      <span className="room-plan-now-bead" aria-hidden="true" />
      <span className="room-plan-now-line" aria-hidden="true" />
    </li>
  );
  dated.forEach((item, index) => {
    if (index === nowAt) nodes.push(nowNode);
    nodes.push(<PlanNode key={item.id} item={item} focus={item === focus} />);
  });
  if (nowAt === -1 && dated.length) nodes.push(nowNode);
  for (const item of undated) nodes.push(<PlanNode key={item.id} item={item} focus={item === focus} />);
  return (
    <SurfaceSection label="Plan" count={items.length || null}>
      <ol className="room-plan" data-testid="items-section" aria-label="Plan">
        {nodes}
      </ol>
    </SurfaceSection>
  );
}

function PlanNode({ item, focus }: { item: ItemRow; focus: boolean }) {
  const late = daysLate(item);
  if (focus) {
    return (
      <li className="room-plan-node" data-kind="focus" data-testid="item-row" data-item-id={item.id} tabIndex={-1} aria-label={item.title}>
        <span className="room-plan-time">{railDate(item.due_at)}</span>
        <span className="room-plan-bead" data-tone="danger" aria-hidden="true" />
        <article className="room-focus" aria-label={`Late: ${item.title}`} data-testid="room-late-plate">
          <header className="room-focus-bar">
            <span className="room-focus-label">Late</span>
            <span className="room-focus-in">{pluralize(late, "day", "days")}</span>
          </header>
          <div className="room-focus-body">
            <span className="room-focus-title">{item.title}</span>
            <ItemPills item={item} />
          </div>
        </article>
      </li>
    );
  }
  return (
    <li className="room-plan-node" data-kind={itemBead(item)} data-testid="item-row" data-item-id={item.id} tabIndex={-1} aria-label={item.title}>
      <span className="room-plan-time">{railDate(item.due_at)}</span>
      <span className="room-plan-bead" data-tone={itemBead(item)} aria-hidden="true" />
      <div className="room-plan-row">
        <span className="room-row-title" title={item.title}>{item.title}</span>
        <ItemPills item={item} />
      </div>
    </li>
  );
}
