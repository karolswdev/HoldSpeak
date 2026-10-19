/* Betterment P4 (projects): the Projects window. One row per project: its
 * name, where it stands (the Room's own state word and reason), its next
 * date, its newest update. One press on the name opens the project.
 *
 * Each row reads the project's Room (`GET /api/projects/<id>/room`, the
 * read the project window makes), so the state here is the Room's state,
 * never a second rule. A row whose read fails says so; it never claims a
 * state it did not read. */
import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useDesk } from "../../desk/store";
import { openProjectRoom, openSurfaceOr } from "../../desk/shell";
import { useOnDeskChanged } from "../../desk/useDeskChangedRefresh";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState, SurfaceVerbs } from "../../desk/surface/Surface";
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
  const ids = projects.map((p) => p.id).join(",");

  const load = useCallback(() => {
    for (const id of ids ? ids.split(",") : []) {
      apiFetch<Record<string, unknown>>(`/api/projects/${encodeURIComponent(id)}/room`)
        .then((raw) => {
          const recent = ((raw.updates as { recent?: Update[] } | undefined)?.recent ?? [])[0] ?? null;
          setReads((now) => ({ ...now, [id]: { room: decodeRoomSnapshot(raw), update: recent } }));
        })
        .catch(() => setReads((now) => ({ ...now, [id]: "failed" })));
    }
  }, [ids]);
  useEffect(load, [load]);
  useOnDeskChanged(load);

  const newProject = (
    <Button dense variant={projects.length ? "secondary" : "primary"} data-testid="projects-new"
      onClick={() => openSurfaceOr("project-setup", "/")}>
      New Project
    </Button>
  );
  if (!projects.length) {
    return (
      <>
        <SurfaceState empty emptyLabel="No projects" />
        <SurfaceVerbs>{newProject}</SurfaceVerbs>
      </>
    );
  }

  const rows = projects
    .map((p) => {
      const read = reads[p.id];
      const room = read && read !== "failed" ? read.room : null;
      return { p, read, room, health: listHealth(room) };
    })
    .sort((a, b) =>
      (RANK[a.health?.word ?? ""] ?? 3) - (RANK[b.health?.word ?? ""] ?? 3) || a.p.name.localeCompare(b.p.name));

  return (
    <>
      <SurfaceVerbs>{newProject}</SurfaceVerbs>
      <SurfaceSection>
        <SurfaceLedger label="Projects">
          <ul className="surface-ledger-rows" data-testid="projects-list">
            {rows.map(({ p, read, room, health }) => {
              const reason = health?.reason ?? null;
              const next = room ? nextDate(room) : null;
              const update = read && read !== "failed" ? updateWords(read.update) : null;
              const tone = health?.tone === "fail" ? "danger" : health?.tone === "info" ? "info" : "ok";
              return (
                <SurfaceLedgerRow
                  key={p.id}
                  data-testid="projects-row"
                  kind="PRJ"
                  kindTitle="PROJECT"
                  wrap
                  expands={false}
                  lineLabel={`Open ${p.name}`}
                  onToggle={() => openProjectRoom(p.id)}
                  primary={
                    <>
                      <span className="projects-name" data-testid="projects-open">{p.name}</span>
                      <span className="projects-facts">
                        {read === "failed" || (room && !health) ? (
                          <span className="surface-token" data-testid="projects-not-read">Not read</span>
                        ) : health ? (
                          <span className="kit-pill" data-tone={tone} data-dot="" data-testid="projects-state">
                            {health.word === "BLOCKED" ? "Blocked" : health.word === "AT RISK" ? "At risk" : health.word === "NEW" ? "New" : "On track"}
                          </span>
                        ) : null}
                        {reason ? <span className="surface-token projects-reason" data-tone="danger" data-testid="projects-reason">{reason.toUpperCase()}</span> : null}
                        {next ? <span className="surface-token" data-tone={next.late ? "danger" : undefined} data-testid="projects-next">{next.words}</span> : null}
                        {update?.fresh ? <span className="kit-pill" data-tone="accent" data-testid="projects-new-update">New update</span> : null}
                        {update ? <span className="surface-token" data-testid="projects-update">{update.words}</span> : null}
                      </span>
                    </>
                  }
                />
              );
            })}
          </ul>
        </SurfaceLedger>
      </SurfaceSection>
    </>
  );
}
