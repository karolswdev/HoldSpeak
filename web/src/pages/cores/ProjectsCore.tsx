/* Betterment P4 (projects): the Projects window. One row per project: its
 * name, where it stands (the Room's own state word and reason), its next
 * date, its newest update.
 *
 * Window grammar (2026-10-24): Toolbar [New Project] → the dense list view
 * (Name · State · Risk · Next · Update) → StatusBar (`4 projects`). A press
 * selects a row; Enter or a double press opens the project.
 *
 * Each row reads the project's Room (`GET /api/projects/<id>/room`, the
 * read the project window makes), so the state here is the Room's state,
 * never a second rule. A row whose read fails says so; it never claims a
 * state it did not read. */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { openProjectRoom, openSurfaceOr } from "../../desk/shell";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { SurfaceState } from "../../desk/surface/Surface";
import { Loading, StatusBar, ToolGlyph, Toolbar, countWords } from "../../desk/surface/kit";
import { useWindowInterior } from "../../desk/surface/interior";
import { ObjectList, type ObjectListRow, type ObjectListSort } from "../../desk/surface/objects/ObjectList";
import { wireDate } from "../../desk/surface/format";
import { decodeRoomSnapshot, healthReasonWords, roomHealthWord, type RoomSnapshot } from "../../features/project-room/model";
import type { CoreProps } from "./core-types";
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

export function ProjectsCore(_props: CoreProps) {
  const projects = useDesk((s) => s.projects) ?? [];
  const [reads, setReads] = useState<Record<string, Read>>({});
  const round = useRef(0);
  const ids = projects.map((p) => p.id).join(",");

  const load = useCallback(() => {
    const current = ++round.current;
    void Promise.all((ids ? ids.split(",") : []).map(async (id): Promise<[string, Read]> => {
      try {
        const raw = await apiFetch<Record<string, unknown>>(`/api/projects/${encodeURIComponent(id)}/room`);
        const recent = ((raw.updates as { recent?: Update[] } | undefined)?.recent ?? [])[0] ?? null;
        return [id, { room: decodeRoomSnapshot(raw), update: recent }];
      } catch {
        return [id, "failed"];
      }
    })).then((batch) => {
      if (current === round.current) setReads(Object.fromEntries(batch));
    });
  }, [ids]);
  useEffect(() => {
    load();
    return () => { round.current++; };
  }, [load]);
  useOnDeskChanged(load);

  const [selected, setSelected] = useState<string | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "state", dir: "asc" });
  useWindowInterior("list");

  const newProject = (
    <Button dense variant="primary" data-testid="projects-new"
      onClick={() => openSurfaceOr("project-setup", "/")}>
      <ToolGlyph kind="new" />
      New Project
    </Button>
  );
  const open = selected && projects.some((p) => p.id === selected) ? selected : null;
  const toolbar = (
    <Toolbar label="Projects" data-testid="projects-toolbar">
      {newProject}
      {open ? (
        <Button dense variant="secondary" data-testid="projects-open-selected" onClick={() => openProjectRoom(open)}>
          <ToolGlyph kind="open" />
          Open
        </Button>
      ) : null}
    </Toolbar>
  );
  const complete = projects.length > 0 && projects.every((project) => reads[project.id] !== undefined);
  const rows = useMemo<ObjectListRow[]>(() => {
    if (!complete) return [];
    return projects.map((p) => {
      const read = reads[p.id];
      const room = read && read !== "failed" ? read.room : null;
      const health = listHealth(room);
      const reason = health?.reason ? quietReason(health.reason) : null;
      const next = room ? nextDate(room) : null;
      const update = read && read !== "failed" ? updateWords(read.update) : null;
      const notRead = read === "failed" || Boolean(room && !health);
      const word = health ? (health.word === "BLOCKED" ? "Blocked" : health.word === "AT RISK" ? "At risk" : health.word === "NEW" ? "New" : "On track") : null;
      return {
        id: p.id,
        kind: "project",
        name: p.name,
        nameTestId: "projects-open",
        state: notRead
          ? { label: "Not read", tone: "warn" as const, testId: "projects-not-read" }
          : word && health
            ? { label: word, tone: health.tone === "fail" ? "fail" as const : health.tone === "info" ? "info" as const : "ok" as const, testId: "projects-state" }
            : undefined,
        sortValues: {
          state: RANK[health?.word ?? ""] ?? 3,
          next: next?.words ?? "",
          update: update?.words ?? "",
          risk: reason ?? "",
        },
        cells: {
          risk: reason ? <span className="projects-reason" data-testid="projects-reason">{reason}</span> : "",
          next: next ? <span data-tone={next.late ? "danger" : undefined} className="projects-next" data-testid="projects-next">{next.words}</span> : "",
          update: update ? (
            <span className="projects-update-cell">
              {update.fresh ? <span className="kit-pill" data-tone="accent" data-dot="" data-testid="projects-new-update">New update</span> : null}
              <span data-testid="projects-update">{update.words}</span>
            </span>
          ) : "",
        },
      };
    });
  }, [complete, projects, reads]);

  if (!projects.length) {
    return (
      <>
        {toolbar}
        <SurfaceState empty emptyLabel="No projects yet" emptyImage={PROJECT_SPRITE} emptyKind="project"
          onAction={() => openSurfaceOr("project-setup", "/")} actionLabel="New Project" />
      </>
    );
  }

  // Rank one complete read. Partial replies otherwise move visible rows as
  // each Room arrives. On refresh, keep the previous complete read in place.
  if (!complete) {
    return <>{toolbar}<Loading data-testid="projects-loading" /></>;
  }

  return (
    <>
      {toolbar}
      <div className="projects-list" data-testid="projects-list">
        <ObjectList
          label="Projects"
          density="dense"
          rows={rows}
          columns={PROJECT_COLUMNS.filter((column) => column.key === "name" || column.key === "state"
            || rows.some((row) => row.cells?.[column.key]))}
          sort={sort}
          onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }))}
          selectedId={open}
          onSelect={setSelected}
          onOpen={(id) => openProjectRoom(id)}
          rowProps={() => ({ "data-testid": "projects-row" })}
        />
      </div>
      <StatusBar
        data-testid="projects-status"
        items={[
          { key: "count", text: countWords(projects.length, "project") },
          ...(["Blocked", "At risk"] as const).map((word) => ({
            key: word,
            lamp: "fail" as const,
            text: countWords(rows.filter((row) => row.state?.label === word).length, word.toLowerCase(), word.toLowerCase()),
          })),
        ]}
      />
    </>
  );
}

/** A reason in quiet sentence case: an all-caps wire word (`1 MILESTONE
 *  LATE`) reads `1 milestone late`; a mixed-case reason stays as written. */
function quietReason(reason: string): string {
  if (reason !== reason.toUpperCase()) return reason;
  const lower = reason.toLowerCase();
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}

const PROJECT_SPRITE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/project-drawer.png`;

// A column no row fills is not drawn (an empty column is a zero in
// another form, UX-CANON A.8).
const PROJECT_COLUMNS = [
  { key: "name", word: "Name", track: "minmax(180px, 1.3fr)" },
  { key: "state", word: "State", track: "112px" },
  { key: "risk", word: "Risk", track: "minmax(0, 1fr)" },
  { key: "next", word: "Next", track: "minmax(0, 0.7fr)" },
  { key: "update", word: "Update", track: "minmax(0, 0.7fr)" },
] as const;
