// The History wing: the changes as a list view by day, and the Writes fold.
import { useMemo, useState } from "react";
import { ListDay, ListRow, ListView, SurfaceState, Toolbar, humanTime } from "../../../desk/surface";
import { StringGadget } from "../../../desk/surface/gadgets";
import { StripMenuButton } from "../../../desk/surface/stripMenu";
import { receiptFace, receiptLabel, refusalWord } from "../../../desk/surface/egress";
import { wireDate } from "../../../desk/surface/format";
import { spriteUrl } from "../../../desk/sprites";
import { refOpener } from "../../../desk/openObject";
import { Button } from "../../../components/signal/Signal";
import { HistoryPages } from "./Pages";
import type { RoomChangeRow, RoomSnapshot } from "../model";
import { formatTimeShort, kindToPhrase, localDateStr } from "./format";

/* ── FILES section (PHILO-17 U30: the drawer's objects, in the Room) ── */

const RECEIPT_TONE: Record<string, "ok" | "fail" | "warn" | "idle"> = {
  success: "ok", failure: "fail", warning: "warn", idle: "idle",
};

export function ReceiptsSection({ room }: { room: RoomSnapshot }) {
  if (room.receipts.state !== "ok") return null;
  const { items } = room.receipts;
  if (items.length === 0) return null;

  // W1 (2026-10-27): the writes are the History list view's rows, in
  // sentence case; a refused or failed write says so as a dot and a word
  // with its plain reason (never a success chip, PHILO-9-03).
  return (
    <ListView label="Writes" className="room-writes">
      <ul className="kit-listrows">
        {items.map((item) => {
          const label = receiptLabel({ op: item.op, title: item.title, outcome: item.outcome });
          const face = receiptFace(item.outcome);
          return (
            <ListRow
              key={item.id}
              data-testid="receipt-row"
              name={
                <span className="surface-primary" data-outcome={item.outcome || "ok"} data-code={item.reason ?? undefined}>
                  {label}
                </span>
              }
              meta={face.word && item.reason ? <span data-testid="receipt-reason">{refusalWord(item.reason)}</span> : undefined}
              state={face.word ? { word: face.word, tone: RECEIPT_TONE[face.state], testId: "receipt-outcome" } : undefined}
              age={item.timestamp ? humanTime(item.timestamp) : undefined}
            />
          );
        })}
      </ul>
    </ListView>
  );
}

/* ── HISTORY wing ── */

interface HistoryEntry {
  id: string;
  kind: string;
  phrase: string;
  time: string;
  source: string;
  occurredAt: string;
  targetRef: string | null;
  itemId: string | null;
  itemType: string | null;
}

/* Window Program W1 (2026-10-27): the source filter is the toolbar's one
   menu (All ▾), in sentence case; the values stay the wire's groups. */
const HISTORY_FILTERS = [
  { value: "ALL", label: "All" },
  { value: "GITHUB", label: "GitHub" },
  { value: "JIRA", label: "Jira" },
  { value: "ROOM", label: "Room" },
];
const SOURCE_WORD: Record<string, string> = { ALL: "All", GITHUB: "GitHub", JIRA: "Jira", ROOM: "Room" };

function changeToHistoryEntry(c: RoomChangeRow): HistoryEntry {
  const phrase = kindToPhrase(c.kind);
  let source = "ROOM";
  if (c.kind.startsWith("github.") || c.kind.startsWith("pr.") || c.kind.startsWith("ci.")) source = "GITHUB";
  else if (c.kind.startsWith("jira.")) source = "JIRA";
  return {
    id: c.id, kind: c.kind,
    phrase: c.label || phrase,
    time: c.occurredAt ? formatTimeShort(c.occurredAt) : "",
    source,
    occurredAt: c.occurredAt || "",
    targetRef: c.targetRef ?? null,
    itemId: c.itemId ?? null,
    itemType: c.itemType ?? null,
  };
}

/** Today / Yesterday / Mon, Oct 20: the list view's day captions. */
function historyDayLabel(d: Date, now: Date = new Date()): string {
  if (Number.isNaN(d.getTime())) return "Undated";
  if (localDateStr(d) === localDateStr(now)) return "Today";
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (localDateStr(d) === localDateStr(yesterday)) return "Yesterday";
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

function groupByDay(entries: HistoryEntry[]): { label: string; date: string; entries: HistoryEntry[] }[] {
  const groups: { label: string; date: string; entries: HistoryEntry[] }[] = [];
  for (const entry of entries) {
    const d = new Date(entry.occurredAt);
    const dateStr = localDateStr(d);
    const last = groups[groups.length - 1];
    if (last && last.date === dateStr) {
      last.entries.push(entry);
    } else {
      groups.push({ label: historyDayLabel(d), date: dateStr, entries: [entry] });
    }
  }
  return groups;
}

/** The row's 20 px object glyph: the thing the change touched. */
const HISTORY_SPRITES = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/20/`;
function historyGlyph(entry: HistoryEntry): string {
  const ref = entry.targetRef ?? "";
  const name =
    entry.source === "GITHUB" ? "pull-request"
      : entry.source === "JIRA" ? "action-item"
        : ref.startsWith("meeting:") ? "meeting"
          : ref.startsWith("decision:") || entry.itemType === "decision" ? "decision"
            : ref.startsWith("note:") ? "note"
              : entry.itemId ? "action-item"
                : "project-drawer";
  return `${HISTORY_SPRITES}${name}.png`;
}

/** The status bar's one line: `42 events · since Oct 1`. */
export function historyEventsWords(changes: RoomChangeRow[]): string {
  const count = changes.length;
  if (!count) return "No history yet";
  const times = changes
    .map((c) => (c.occurredAt ? wireDate(c.occurredAt) : null))
    .filter((d): d is Date => Boolean(d))
    .map((d) => d.getTime());
  const words = `${count} ${count === 1 ? "event" : "events"}`;
  if (!times.length) return words;
  const first = new Date(Math.min(...times));
  const since = localDateStr(first) === localDateStr(new Date())
    ? "today"
    : first.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return `${words} · since ${since}`;
}

export function HistoryWing({
  room,
  itemIds,
  onOpenItem,
  onRetry,
  onPrepare,
}: {
  room: RoomSnapshot;
  itemIds: string[];
  onOpenItem: (id: string) => void;
  onRetry: () => void;
  /** The language, 2026-11-08: `Prepare a brief` opens the Prepare posture. */
  onPrepare: () => void;
}) {
  const available = room.changes.state === "ok";
  const changes = room.changes.state === "ok" ? room.changes.recent : [];
  const allEntries = useMemo(() => changes.map(changeToHistoryEntry), [changes]);

  const [sourceFilter, setSourceFilter] = useState("ALL");

  const filtered = useMemo(() => {
    if (sourceFilter === "ALL") return allEntries;
    return allEntries.filter((e) => e.source === sourceFilter);
  }, [allEntries, sourceFilter]);

  const [searchQuery, setSearchQuery] = useState("");
  const searchFiltered = useMemo(() => {
    if (!searchQuery.trim()) return filtered;
    const q = searchQuery.trim().toLowerCase();
    return filtered.filter((e) => e.phrase.toLowerCase().includes(q));
  }, [filtered, searchQuery]);

  const days = useMemo(() => groupByDay(searchFiltered), [searchFiltered]);
  const clearFilters = () => {
    setSourceFilter("ALL");
    setSearchQuery("");
  };

  return (
    <div className="room-history" data-testid="room-history">
      {/* Window Program W1 (2026-10-27): History is a list view, not the
          old dashboard: the toolbar holds the source menu and the search;
          days are quiet captions; a row is glyph · what happened · where ·
          the time. No headline, no caps pills, no box. */}
      <Toolbar
        label="History"
        className="room-history-toolbar"
        trailing={
          <span className="room-history-search">
            <StringGadget
              type="search"
              label="Search history"
              placeholder="Search history…"
              value={searchQuery}
              onChange={setSearchQuery}
              micDraftScope="room-history-search"
            />
          </span>
        }
      >
        {available && allEntries.length ? (
          <StripMenuButton
            label="Source"
            choices={HISTORY_FILTERS}
            value={sourceFilter}
            onChange={setSourceFilter}
            variant="secondary"
          />
        ) : null}
        <Button dense variant="secondary" onClick={onPrepare} data-testid="room-history-prepare">
          Prepare a brief
        </Button>
      </Toolbar>
      {/* The project's standing pages: one head row (the language, 2026-11-08). */}
      <HistoryPages projectId={room.projectId} />
      {!available ? (
        <SurfaceState error="History unavailable" onRetry={onRetry} />
      ) : !allEntries.length ? (
        <SurfaceState empty emptyLabel="No history yet" emptyImage={spriteUrl("project", room.projectId)} emptyKind="project" />
      ) : !searchFiltered.length ? (
        <SurfaceState empty
          emptyLabel={searchQuery.trim() ? "No matching changes" : `No changes from ${SOURCE_WORD[sourceFilter] ?? sourceFilter}`}
          actionLabel="Clear filters" onAction={clearFilters} />
      ) : (
        <ListView label="History" className="room-history-list">
          {days.map((day) => (
            <ListDay key={day.date || day.label} label={day.label}>
              {day.entries.map((entry) => (
                <HistoryEntryRow key={entry.id} entry={entry} itemIds={itemIds} onOpenItem={onOpenItem} />
              ))}
            </ListDay>
          ))}
        </ListView>
      )}
    </div>
  );
}

/** PHILO-13-06 (B1): an activity row opens the object it touched; a row
 *  about the Room itself names nothing to open and draws no verb. */
function HistoryEntryRow({ entry, itemIds, onOpenItem }: {
  entry: HistoryEntry;
  itemIds: string[];
  onOpenItem: (id: string) => void;
}) {
  // Item changes name the recorded item inside this Room. A parked/missing
  // item has no destination; other object refs keep their existing opener.
  const open = entry.itemId
    ? (itemIds.includes(entry.itemId) ? () => onOpenItem(entry.itemId!) : null)
    : entry.targetRef?.startsWith("project:") ? null : refOpener(entry.targetRef);
  // W1: the row itself opens what it touched (one press); a row about the
  // Room itself names nothing to open.
  return (
    <ListRow
      glyph={historyGlyph(entry)}
      name={entry.phrase}
      nameTestId="history-entry"
      meta={SOURCE_WORD[entry.source] ?? entry.source}
      age={entry.time}
      onOpen={open ?? undefined}
      openLabel={open ? `Open: ${entry.phrase}` : undefined}
      openTestId={open ? "history-entry-open" : undefined}
    />
  );
}
