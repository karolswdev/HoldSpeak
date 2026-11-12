import { useWindowMast } from "../../desk/surface";
/* Projects selects a Room and reads its facts in the shared list grammar. */
import { useCallback } from "react";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { openProjectRoom, openSurfaceOr } from "../../desk/shell";
import { ROOM_CHANGE_KINDS, useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { ListApp, useListApp, InspectorFacts, countWords, type ListVerb, type ObjectListRow } from "../../desk/surface";
import { ShowMe } from "../../desk/walk/ShowMe";
import { wireDate } from "../../desk/surface/format";
import { decodeRoomSnapshot, healthReasonWords, roomHealthWord, type RoomSnapshot } from "../../features/project-room/model";
import type { CoreProps } from "./core-types";
type Update = { lifecycle: string; created_at: string; published_at?: string | null };


const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

/** `Thu 23 Oct`: a date in his words. */
export function dayWords(value: unknown): string {
  const d = wireDate(value);
  return d ? `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}` : "";
}

function dayNumber(d: Date): number {
  return Math.round(new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime() / 86_400_000);
}

/** The next date: the target, or an earlier planned milestone still ahead. */
export function nextDate(room: RoomSnapshot, now: Date = new Date()): { words: string; late: boolean } | null {
  const target = room.target.state === "ok" ? room.target : null;
  const today = dayNumber(now);
  const ahead = (room.items.state === "ok" ? room.items.focus : [])
    .filter((item) => item.itemType === "milestone" && item.dueAt)
    .map((item) => ({ item, at: wireDate(item.dueAt) }))
    .filter((x): x is { item: typeof x.item; at: Date } => x.at !== null && dayNumber(x.at) >= today)
    .sort((a, b) => a.at.getTime() - b.at.getTime())[0];
  const targetAt = target?.targetAt ? wireDate(target.targetAt) : null;
  if (ahead && (!targetAt || ahead.at.getTime() < targetAt.getTime()))
    return { words: `${ahead.item.title} ${dayWords(ahead.at)}`, late: false };
  if (targetAt && target) return target.passed
    ? { words: `Target passed ${dayWords(targetAt)}`, late: true }
    : { words: `Target ${dayWords(targetAt)}`, late: false };
  return null;
}

/** The newest update in words, and whether it is new (a draft from the last day). */
export function updateWords(update: Update | null, now: Date = new Date()): { words: string; fresh: boolean } | null {
  if (!update) return null;
  const published = update.lifecycle === "published";
  const at = wireDate(published ? update.published_at || update.created_at : update.created_at);
  if (!at) return null;
  const fresh = !published && now.getTime() - at.getTime() < 86_400_000;
  return { words: `${published ? "Update sent" : "Update drafted"} ${dayWords(at)}`, fresh };
}

type ListHealth = {
  word: "AT RISK" | "BLOCKED" | "ON TRACK" | "NEW";
  tone: "fail" | "ok" | "info";
  reason: string | null;
};

/** Use P3's Room state when the newer wire is present, with the legacy
 * assessment as a compatibility fallback for older wires. */
function listHealth(room: RoomSnapshot | null): ListHealth | null {
  if (!room || room.health.state !== "ok") return null;
  const health = room.health;
  if (health.projectState === "blocked") {
    return { word: "BLOCKED", tone: "fail", reason: health.stateReason || health.reason };
  }
  if (health.projectState === "at_risk") {
    return { word: "AT RISK", tone: "fail", reason: health.stateReason || healthReasonWords(health) };
  }
  if (health.projectState === "on_track") {
    return roomHealthWord(room)?.word === "NEW"
      ? { word: "NEW", tone: "info", reason: null }
      : { word: "ON TRACK", tone: "ok", reason: null };
  }
  const legacy = roomHealthWord(room);
  if (!legacy) return null;
  return {
    word: legacy.word,
    tone: legacy.tone,
    reason: legacy.word === "AT RISK" ? healthReasonWords(health) : null,
  };
}

const RANK: Record<string, number> = { BLOCKED: 0, "AT RISK": 1, "ON TRACK": 2, NEW: 3 };
const wordOf = (health: ListHealth | null) => ({ BLOCKED: "Blocked", "AT RISK": "At risk", "ON TRACK": "On track", NEW: "New" })[health?.word ?? "NEW"];

export function ProjectsCore(_props: CoreProps) {
  const projects = useDesk((s) => s.projects) ?? [];
  const read = useCallback(async () => ({ rows: (await Promise.all(projects.map(async project => {
    let room: RoomSnapshot | null = null, newest: Update | null = null;
    try {
      const raw = await apiFetch<Record<string, unknown>>(`/api/projects/${encodeURIComponent(project.id)}/room`);
      room = decodeRoomSnapshot(raw); newest = ((raw.updates as { recent?: Update[] } | undefined)?.recent ?? [])[0] ?? null;
    } catch { /* Keep the project and its Retry when a Room is not read. */ }
    const health = listHealth(room), update = updateWords(newest);
    const dateRead = room?.target.state === "ok" && room?.items.state === "ok", updateRead = room?.updates.state === "ok";
    const unread = !health || !dateRead || !updateRead;
    const attention = health?.tone === "fail" ? wordOf(health) : unread ? "Not read" : update?.fresh ? "New update" : "";
    return { ...project, health, attention, unread, reason: health?.reason ? quietReason(health.reason) : null,
      dateRead, updateRead, next: room ? nextDate(room) : null, update };
  }))).sort((a, b) => (RANK[a.health?.word ?? ""] ?? 4) - (RANK[b.health?.word ?? ""] ?? 4)) }), [projects]);
  const app = useListApp({ read, keyOf: row => row.id, search: (row, query) => row.name.toLocaleLowerCase().includes(query) });
  useOnDeskChanged(app.reload, ROOM_CHANGE_KINDS);
  const rows = app.rows;
  const shown = app.selected;
  const toRow = (row: typeof app.rows[number]): ObjectListRow => {
    return { id: row.id, name: row.name, kind: "project", nameTestId: "projects-open",
      state: row.attention ? { label: row.attention, tone: row.health?.tone === "fail" ? "fail" : "warn",
        testId: row.attention === "Not read" ? "projects-not-read" : "projects-state" } : row.health?.word === "ON TRACK" ? {label: "On track", tone: "ok"} : undefined,
      cells: { next: row.next?.words ?? "", updated: row.update?.words ?? "" } };
  };
  const verbs: ListVerb[] = [
    { enabled: () => true, id: "new-project", variant: "primary", label: "New project", key: "n", testId: "projects-new", run: () => openSurfaceOr("project-setup", "/") },
    { id: "open", label: "Open Room", key: "Enter", testId: "projects-open-selected", enabled: (row) => Boolean(row), run: (row) => { if (row) openProjectRoom(row.id); } },
    ...(rows.some((row) => row.unread) ? [{ id: "retry", label: "Retry", key: "r", enabled: (row: ObjectListRow | null) => Boolean(rows.find((entry) => entry.id === row?.id)?.unread), run: app.reload }] : []),
  ];
  useWindowMast({ line: app.page ? countWords(rows.length, "project") ?? undefined : undefined, figures: [{ value: rows.filter(row => row.attention).length, label: "wait on you", tone: "ask" }] });
  const needsOwner = rows.filter((row) => row.attention).length;
  return <ListApp app={app} label="Projects"
    ids={{ windowTestId: "projects-window", listTestId: "projects-list", paneTestId: "projects-pane", toolbarTestId: "projects-toolbar", statusTestId: "projects-status", loadingTestId: "projects-loading" }}
    words={{ find: "Find a project", empty: "No projects yet", noMatch: "No projects match", select: "Select a project", failed: "Projects not loaded" }}
    list={{ columns: [
      { key: "name", word: "Project", priority: 4, minWidth: 180, track: "2fr" },
      { key: "state", word: "State", priority: 3, minWidth: 110 },
      { key: "next", word: "Next", priority: 2, minWidth: 180 },
      { key: "updated", word: "Updated", priority: 1, minWidth: 220 },
    ], verbs, defaultVerb: "open", rowProps: () => ({ "data-testid": "projects-row" }) }} row={toRow}
    status={[
      { text: countWords(projects.length, "project") },
      shown && { text: "1 selected" },
      needsOwner > 0 && { text: `${needsOwner} needs you`, lamp: "warn" },
    ]} pane={() =>
      shown ? <InspectorFacts name={shown.name} rows={[
        ...(shown.attention ? [{ label: "State", value: shown.attention }] : []),
        ...(shown.reason ? [{ label: "Reason", value: <span data-testid="projects-reason">{shown.reason}</span> }] : []),
        { label: "Next date", value: <span data-testid="projects-next">{shown.next?.words ?? (shown.dateRead ? "No date set" : "Not read")}</span> },
        { label: "Newest update", value: <span data-testid="projects-update">{shown.update?.words ?? (shown.updateRead ? "No update yet" : "Not read")}
          {shown.update?.fresh ? <> · <span data-testid="projects-new-update">New update</span></> : null}</span> },
      ]} /> : null}>
    <ShowMe app="open-projects" />
  </ListApp>;
}

function quietReason(reason: string): string {
  if (/\p{Ll}/u.test(reason)) return reason;
  const lower = reason.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}
