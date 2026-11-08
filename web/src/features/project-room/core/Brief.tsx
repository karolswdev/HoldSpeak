// R1 "the brief" (owner 2026-11-08): What changed. The latest published
// update's first lines as plain text, one quiet line with its time, who wrote
// it and Open the update; the kept update draft waits here with Continue
// (owner ruling 2026-11-07: the Room opens on Now).
import { useEffect, useState } from "react";
import { SurfaceSection, wireClock, wireDayClock } from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import type { RoomSnapshot } from "../model";
import { dayWords } from "../now/model";
import { useRoomRead } from "../roomReads";
import { fetchUpdate } from "../update/api";
import { plainLine, type ProjectUpdate } from "../update/model";
import type { useUpdateController } from "../update/useUpdateController";

/** The newest update draft the Room read holds (its recent updates), or
 *  null: the draft he was writing, offered with Continue. */
export function newestDraft(room: RoomSnapshot): { id: string; when: string } | null {
  if (room.updates.state !== "ok") return null;
  let best: Record<string, unknown> | null = null;
  for (const row of room.updates.recent) {
    if (row.lifecycle !== "draft" || !row.id) continue;
    const at = String(row.updated_at ?? row.created_at ?? "");
    if (!best || at > String(best.updated_at ?? best.created_at ?? "")) best = row;
  }
  if (!best) return null;
  return { id: String(best.id), when: wireDayClock(best.updated_at ?? best.created_at) };
}

const SECTION_NAMES = new Set([
  "Progress", "Decisions", "Risks & Blockers", "Dependencies", "Next Actions", "Source Coverage",
]);

/** The update's first lines as plain text: no headings, no list marks. */
export function briefLines(bodyMd: string, max = 3): string[] {
  const lines: string[] = [];
  for (const raw of bodyMd.split("\n")) {
    if (/^\s*#{1,6}\s/.test(raw)) continue;
    const text = plainLine(raw).replace(/^\s*(?:[-*+]|\d+[.)])\s+/, "").trim();
    if (!text || SECTION_NAMES.has(text)) continue;
    lines.push(text);
    if (lines.length >= max) break;
  }
  return lines;
}

/** Who wrote the update: the engine's name, your records, or you. */
export function briefAuthor(update: ProjectUpdate): string {
  if (update.generator === "model") return update.generatorModel || "an engine";
  if (update.generator === "deterministic") return "your records";
  if (update.generator.startsWith("agent:automation")) return "the update automation";
  return "you";
}

export function BriefSection({ room, updateCtrl }: {
  room: RoomSnapshot;
  updateCtrl: ReturnType<typeof useUpdateController>;
}) {
  const latest = room.updates.state === "ok" ? room.updates.latestPublished : null;
  const latestId = latest?.id ? String(latest.id) : "";
  const [read, setRead] = useState<{ id: string; update: ProjectUpdate | null } | null>(null);
  const resolved = !latestId || read?.id === latestId;
  useRoomRead("brief", resolved);
  useEffect(() => {
    if (!latestId) return;
    let live = true;
    fetchUpdate(latestId)
      .then((update) => { if (live) setRead({ id: latestId, update }); })
      .catch(() => { if (live) setRead({ id: latestId, update: null }); });
    return () => { live = false; };
  }, [latestId]);
  const keptDraft = updateCtrl.posture === "off" ? newestDraft(room) : null;
  if (!latestId && !keptDraft) return null;
  const update = read?.id === latestId ? read.update : null;
  const lines = update ? briefLines(update.bodyMd) : [];
  const at = latest?.published_at ?? latest?.created_at;
  const when = [dayWords(String(at ?? "")), wireClock(at)].filter(Boolean).join(" ");
  const meta = [when, update ? `by ${briefAuthor(update)}` : ""].filter(Boolean).join(" · ");
  return (
    <SurfaceSection label="What changed" className="room-brief" data-testid="room-what-changed">
      {latestId ? (
        <div className="room-brief-card">
          {lines.map((line, index) => (
            <p key={index} className="room-brief-line" data-testid="room-brief-line">{line}</p>
          ))}
          <p className="room-brief-meta" data-testid="room-brief-meta">
            {meta ? <span>{meta}</span> : null}
            {meta ? <span aria-hidden="true">·</span> : null}
            <Button variant="chrome" className="room-link" loading={updateCtrl.loading}
              onClick={() => void updateCtrl.continueDraft(latestId)} data-testid="room-brief-open">
              Open the update
            </Button>
          </p>
        </div>
      ) : null}
      {keptDraft ? (
        <p className="room-brief-meta room-brief-draft" data-testid="room-head-update-draft">
          <span>{keptDraft.when ? `Update draft · ${keptDraft.when}` : "Update draft"}</span>
          <span aria-hidden="true">·</span>
          <Button variant="chrome" className="room-link" loading={updateCtrl.loading}
            onClick={() => void updateCtrl.continueDraft(keptDraft.id)}
            data-testid="room-head-update-continue">Continue</Button>
        </p>
      ) : null}
    </SurfaceSection>
  );
}
