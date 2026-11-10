// Parked: the shared selection list replaces the Projects rail, mast and card.
/* Projects is a client of the Room read: one rail, one picked project. */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch } from "../../../lib/api";
import { useDesk } from "../../../desk/store";
import { openProjectRoom, openSurfaceOr } from "../../../desk/shell";
import { ROOM_CHANGE_KINDS, useOnDeskChanged } from "../../../desk/useDeskChangedRefresh";
import { Rail, Mast, Spine, SurfaceState, DotWord, StatusBar, countWords, type SpineTone } from "../../../desk/surface";
import { useWindowInterior } from "../../../desk/surface/interior";
import { ShowMe } from "../../../desk/walk/ShowMe";
import { wireDate } from "../../../desk/surface/format";
import { decodeRoomSnapshot, healthReasonWords, roomHealthWord, type RoomSnapshot } from "../../../features/project-room/model";
import type { CoreProps } from "../core-types";
import "./projects.css";
type Update = { lifecycle: string; created_at: string; published_at?: string | null };
type Read = { room: RoomSnapshot; update: Update | null } | "failed";

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
const toneOf = (health: ListHealth | null): SpineTone => !health ? "graphite" : health.tone === "fail" ? "coral" : health.tone === "ok" ? "moss" : "steel";
const wordOf = (health: ListHealth | null) => ({ BLOCKED: "Blocked", "AT RISK": "At risk", "ON TRACK": "On track", NEW: "New" })[health?.word ?? "NEW"];

export function ProjectsCore(_props: CoreProps) {
  useWindowInterior("list");
  const projects = useDesk((s) => s.projects) ?? [];
  const [reads, setReads] = useState<Record<string, Read>>({});
  const [picked, setPicked] = useState<string | null>(null);
  const round = useRef(0);
  const ids = projects.map((p) => p.id).join(",");
  const load = useCallback(() => {
    const current = ++round.current;
    void Promise.all((ids ? ids.split(",") : []).map(async (id): Promise<[string, Read]> => {
      try {
        const raw = await apiFetch<Record<string, unknown>>(`/api/projects/${encodeURIComponent(id)}/room`);
        return [id, { room: decodeRoomSnapshot(raw), update: ((raw.updates as { recent?: Update[] } | undefined)?.recent ?? [])[0] ?? null }];
      } catch { return [id, "failed"]; }
    })).then((batch) => { if (current === round.current) setReads(Object.fromEntries(batch)); });
  }, [ids]);
  useEffect(() => { load(); return () => { round.current++; }; }, [load]);
  useOnDeskChanged(load, ROOM_CHANGE_KINDS);
  const complete = projects.every((p) => reads[p.id] !== undefined);
  const rows = complete ? projects.map((project) => {
    const read = reads[project.id];
    const room = read && read !== "failed" ? read.room : null;
    const health = listHealth(room);
    return { ...project, health, tone: toneOf(health), word: health ? wordOf(health) : "Not read",
      reason: health?.reason ? quietReason(health.reason) : null,
      dateRead: room?.target.state === "ok" && room?.items.state === "ok", updateRead: room?.updates.state === "ok",
      next: room ? nextDate(room) : null, update: read && read !== "failed" ? updateWords(read.update) : null };
  }).sort((a, b) => (RANK[a.health?.word ?? ""] ?? 4) - (RANK[b.health?.word ?? ""] ?? 4)) : [];
  const shown = rows.find((p) => p.id === picked) ?? rows[0];
  const newProject = () => openSurfaceOr("project-setup", "/");
  return <div className="projects-frame" data-testid="projects-window">
    <div className="projects-body surface-rail-layout">
      <Rail label="Projects" data-testid="projects-rail" picked={shown?.id ?? null} onPick={setPicked}
        head={<Button dense variant="primary" data-testid="projects-new" onClick={newProject}>New project</Button>}
        items={rows.map((p) => ({ id: p.id, label: <span data-testid="projects-open">{p.name}</span>,
          facts: p.next?.words, state: <span data-testid={p.health ? "projects-state" : "projects-not-read"} data-tone={p.tone}>{p.word}</span>,
          spine: { tone: p.tone }, rowData: { "data-testid": "projects-row" } }))}>
        {!projects.length ? <SurfaceState empty emptyLabel="No projects yet" emptyImage={PROJECT_SPRITE} emptyKind="project" />
          : !complete ? <SurfaceState loading data-testid="projects-loading" /> : undefined}
      </Rail>
      <article className="projects-object" data-testid="projects-pane">
        <Mast kind="project" id={shown?.id} title={shown?.name ?? "Your next project"}
          facts={shown ? [shown.word, shown.next?.words, shown.update?.words].filter(Boolean).join(" · ") : undefined} data-testid="projects-mast">
          {shown ? <Button dense variant="primary" data-testid="projects-open-selected" onClick={() => openProjectRoom(shown.id)}>Open Room</Button> : null}
          <ShowMe app="open-projects" />
        </Mast>
        <Spine tone={shown?.tone ?? "idle"} />
        <section className="projects-plate" data-testid="projects-plate">
          <span className="projects-caption">{shown?.word ?? "Start here"}</span>
          <h3 data-testid="projects-reason">{shown?.reason ?? (shown ? "The work is in its Room" : "Make a project")}</h3>
          {!shown ? <Button dense variant="primary" onClick={newProject}>New project</Button> : null}
        </section>
        {shown ? <dl className="projects-ledger" data-testid="projects-ledger">
          <dt>Standing</dt><dd><DotWord tone={shown.health?.tone ?? "warn"}>{shown.word}</DotWord>
            {!shown.health ? <Button dense variant="secondary" onClick={load}>Retry</Button> : null}</dd>
          <dt>Next date</dt><dd data-testid="projects-next">{shown.next?.words ?? (shown.dateRead ? "No date set" : "Not read")}</dd>
          <dt>Newest update</dt><dd data-testid="projects-update">{shown.update?.words ?? (shown.updateRead ? "No update yet" : "Not read")}
            {shown.update?.fresh ? <span className="projects-fresh" data-testid="projects-new-update">New update</span> : null}</dd>
        </dl> : null}
      </article>
    </div>
    <StatusBar data-testid="projects-status" items={[{ text: countWords(projects.length, "project") }]} />
  </div>;
}

function quietReason(reason: string): string {
  if (/\p{Ll}/u.test(reason)) return reason;
  const lower = reason.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}
const PROJECT_SPRITE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/project-drawer.png`;
