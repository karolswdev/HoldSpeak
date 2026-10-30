import { wireClock } from "../../desk/surface/format";
import { useEffect, useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { useLaunchers } from "../../desk/components/DeskWindow";
import { useProcessWindow } from "../../desk/processWindow";
import type { ProcessRow } from "../../desk/processWindowReducer";
import { humanizeWireValue } from "../../lib/productLanguage";
import { StatusBar, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../../desk/surface/kit";
import { ObjectList, type ObjectListRow, type ObjectListSort, type ObjectListTone } from "../../desk/surface/objects/ObjectList";
import { useWindowInterior } from "../../desk/surface/interior";
import { spriteUrl } from "../../desk/sprites";
import { kindWord, looksLikeId } from "../../desk/windowName";
import { objectByRef } from "../../desk/world";
import { useDesk } from "../../desk/store";
import type { Items } from "../../desk/api";
import { SurfaceState } from "../../desk/surface/Surface";
import "./processes.css";
import type { CoreProps } from "./core-types";

/** The fixed HH:MM:SS clock cell (mono, tabular). */
function clockToken(value: string | number | ""): string {
  // The kernel stamps epoch SECONDS; `new Date(seconds)` read them as
  // milliseconds and printed a clock in January 1970.
  return wireClock(value, true);
}

/** What a row's target says on the face (STATUS: no raw ids on faces;
 * Astra, #869: never a blank where the identity is):
 *   - "" only for a target that repeats the operation's own name
 *     (`desk:channel.save_destination`): it names nothing new;
 *   - a record the desk holds reads by its NAME (`Freeze the old ledger`);
 *   - a record the desk does not hold keeps an inspectable identity: its
 *     kind and a short id token (`Decision c9edf1`), so two rows never look
 *     the same;
 *   - any other target (`agent:build`) reads as the hub sent it. */
export function shownTarget(row: Pick<ProcessRow, "kind" | "target">, items?: Items): string {
  const target = row.target.trim();
  if (!target) return "";
  const colon = target.indexOf(":");
  const kind = colon > 0 ? target.slice(0, colon) : "";
  const rest = colon > 0 ? target.slice(colon + 1) : target;
  if (rest === row.kind || target === row.kind) return "";
  const named = items ? objectByRef(items, target) : null;
  if (named?.title) return named.title;
  if (kind === "connection" && PROVIDER_WORDS[rest.toLowerCase()]) return PROVIDER_WORDS[rest.toLowerCase()];
  if (looksLikeId(rest) || /^[0-9a-f]{10,}$/i.test(rest)) {
    const hex = rest.replace(/^[a-z]{1,12}_/i, "").replace(/-/g, "");
    return `${kindWord(kind) || "Record"} ${hex.slice(0, 6)}`;
  }
  return target;
}

/** Window Program W4 (the words): a provider's own name. */
const PROVIDER_WORDS: Record<string, string> = {
  github: "GitHub", gh: "GitHub", jira: "Jira", confluence: "Confluence", calendar: "Calendar",
};

/** Window Program W4: who ran a process, in words (the wire's id is the
 *  hover title). The owner's session is `You`. */
export function principalWords(principal: string): string {
  const raw = principal.trim();
  if (!raw) return "";
  if (/^(owner|owner-session|local-owner)$/i.test(raw)) return "You";
  const head = raw.replace(/^[a-z]+:/i, "").replace(/[-_]?[0-9a-f]{8,}$/i, "");
  return humanizeWireValue(head.replace(/-/g, " ")) || "Agent";
}

/** Window Program W4: where a process ran, in words, never a machine id:
 *  `node:local` is `This Mac`, `node:inference-d380f9fc…` is `Engine`. */
export function placementWords(placement: string): string {
  const raw = placement.trim().replace(/^node:/i, "");
  if (!raw) return "";
  if (/^(local|local-desktop|actuator-local|this-device)$/i.test(raw)) return "This Mac";
  if (/^inference-[0-9a-f]{6,}$/i.test(raw)) return "Engine";
  if (/^hub([-_].*)?$/i.test(raw)) return "Hub";
  if (/^model-turn$/i.test(raw)) return "Engine";
  if (/^thread-turn$/i.test(raw)) return "Thread";
  const head = raw.replace(/[-_]?[0-9a-f]{8,}$/i, "");
  return head ? humanizeWireValue(head.replace(/-/g, " ")) : "";
}

/** PHILO-17 (the desk sweep): an operation name is one long word
 * (`channel.save_destination`, a code shown as written, 225 px in a 160 px
 * cell); it may break after each `.` and `_`, so it wraps in its cell and
 * never runs over the facts. */
export function breakableKind(kind: string): ReactNode[] {
  return kind
    .split(/(?<=[._])/)
    .flatMap((part, i) => (i ? [<wbr key={i} />, part] : [part]));
}

/** Window grammar (2026-10-24): an operation name in words: the wire
 *  name (`channel.save_destination`) reads `Channel save destination`. */
export function kindWords(kind: string): string {
  const words = kind.replace(/[._]+/g, " ").trim().toLowerCase();
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : "Operation";
}

/** A row's state as a dot and a word: running is live and green, a held
 *  decision asks for him, a failure is red, an ended run is the grey dot. */
function rowState(row: ProcessRow): { label: string; tone: ObjectListTone; live?: boolean } {
  if (row.latestEventType === "operation.awaiting_decision") return { label: "Needs you", tone: "ask" };
  const state = row.state.toLowerCase();
  if (state === "failed" || state === "refused") return { label: state === "refused" ? "Refused" : "Failed", tone: "fail" };
  if (state === "running" || state === "starting" || state === "claimed") return { label: "Running", tone: "ok", live: true };
  if (state === "waiting") return { label: "Waiting", tone: "warn" };
  if (state === "succeeded" || state === "completed" || state === "done") return { label: "Done", tone: "idle" };
  return { label: state ? humanizeWireValue(state) : "Unknown", tone: "idle" };
}

/** The D glyph of an operation, by what it works on. */
const KIND_SPRITE: Record<string, string> = {
  process: "agent", agent: "agent", coder: "agent", meeting: "meeting", note: "note", thought: "note",
  decision: "decision", project: "project", person: "person", people: "person", channel: "artifact",
  delivery: "artifact", connection: "model", setup: "model", inference: "model", memory: "memory",
};
function kindSprite(kind: string): string {
  const head = kind.split(/[._]/, 1)[0].toLowerCase();
  return spriteUrl(KIND_SPRITE[head] ?? "thread", kind, "rest", null, 20);
}

/* Each row is one line (2026-10-25 audit): What takes the free width and
 * ends in an ellipsis; For is as wide as its longest target (each row is its
 * own grid, so the width is measured here, not by `max-content`); Where ends
 * in an ellipsis with the full text on hover; Started is a fixed 8ch clock. */
function processColumns(targets: string[]) {
  const longest = Math.min(20, Math.max(4, ...targets.map((target) => target.length)));
  return [
    { key: "name", word: "What", track: "minmax(170px, 1.6fr)" },
    { key: "target", word: "For", track: `minmax(0, calc(${longest}ch + 20px))` },
    { key: "where", word: "Where", track: "minmax(0, 1fr)" },
    { key: "started", word: "Started", track: "calc(8ch + 20px)" },
    { key: "state", word: "State", track: "104px" },
  ];
}

/* Window grammar (2026-10-24): Processes reads title bar → Toolbar
 * [Refresh] → the dense list of every run the kernel holds (glyph · What ·
 * For · Where · Started · State as a dot and a word; a run that needs him
 * first) → StatusBar (`2 running · 1 needs you`, never a zero) with the
 * selected run's verb. Enter or a double press on a run that needs him
 * opens Desk memory (its answer), as the Answer verb did. The kernel has no
 * stop route, so the window offers no Stop (a dead verb is a bounce). */
export function ProcessCore(_props: CoreProps) {
  const store = useProcessWindow();
  const launchers = useLaunchers();
  const decisions = launchers.find((launcher) => launcher.id === "attention");
  const items = useDesk((state) => state.items);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sort, setSort] = useState<ObjectListSort>({ key: "order", dir: "asc" });
  useWindowInterior("list");

  useEffect(() => {
    useProcessWindow.getState().start();
    return () => useProcessWindow.getState().stop();
  }, []);

  const flat = useMemo(() => {
    const out: Array<{ row: ProcessRow; depth: number; group: number }> = [];
    const walk = (rows: ProcessRow[], depth: number, group: number) => {
      for (const row of rows) {
        out.push({ row, depth, group });
        if (row.children.length) walk(row.children, depth + 1, group);
      }
    };
    store.sections.forEach((section, index) => walk(section.rows, 0, index));
    return out;
  }, [store.sections]);
  const total = flat.length;
  const byId = new Map(flat.map((entry) => [entry.row.operationId, entry.row]));
  const openDecisions = () => decisions?.activate();
  const isDecision = (row: ProcessRow | undefined) => row?.latestEventType === "operation.awaiting_decision";

  // Atlas pass 3 (defect 8): at 393 the fold line is For · Where · Started;
  // For gives up its width (an ellipsis) so the clock stays on that line.
  const whereLength = new Map<string, number>();
  const rows: ObjectListRow[] = flat.map(({ row, depth, group }, index) => {
    const target = shownTarget(row, items);
    // Window Program W4 (the words): who and where in words; the wire's ids
    // are the hover title, never the face.
    const whereRaw = [row.principal, row.placement].map((v) => String(v ?? "").trim()).filter(Boolean).join(" · ");
    const where = [...new Set([
      principalWords(String(row.principal ?? "")),
      String(row.placementLabel ?? "").trim() || placementWords(String(row.placement ?? "")),
    ].filter(Boolean))].join(" · ");
    whereLength.set(row.operationId, where.length);
    return {
      id: row.operationId,
      kind: "process",
      name: `${depth > 0 ? "└ " : ""}${row.label || kindWords(row.kind)}`,
      sprite: kindSprite(row.kind),
      group,
      state: { ...rowState(row), testId: "process-state" },
      cells: {
        target: target ? <span className="process-target" data-testid="process-target">{target}</span> : "",
        where: where ? <span className="process-where" title={whereRaw}>{where}</span> : "",
        started: <span className="process-clock">{clockToken(row.timestamp)}</span>,
      },
      sortValues: { order: index, started: String(row.timestamp), target, where },
    };
  });
  const columns = processColumns(flat.map(({ row }) => shownTarget(row, items)));

  const count = (id: string) => store.sections.find((section) => section.id === id)?.rows.length ?? 0;
  const selected = selectedId ? byId.get(selectedId) : undefined;
  const items_: Array<StatusBarItem | null> = store.error ? [
    { key: "error", lamp: "fail", text: "Kernel unreachable" },
  ] : [
    { key: "needs", lamp: "ask", text: count("needs-you") ? `${count("needs-you")} ${count("needs-you") === 1 ? "needs" : "need"} you` : null },
    { key: "running", lamp: "ok", text: countWords(count("running"), "running", "running") },
    { key: "waiting", lamp: "warn", text: countWords(count("waiting"), "waiting", "waiting") },
    { key: "ended", text: count("recently-ended") ? `${count("recently-ended")} ended` : null },
    total ? null : { key: "watching", lamp: "ok", text: "Watching" },
  ];

  return (
    <>
      <Toolbar label="Processes" data-testid="process-toolbar">
        <Button dense variant="secondary" loading={store.inflight && !store.loading} onClick={() => void useProcessWindow.getState().poll()}
          data-testid="process-refresh">
          <ToolGlyph kind="retry" />
          Refresh
        </Button>
      </Toolbar>
      {store.error ? (
        <SurfaceState
          error={store.error}
          onRetry={() => void useProcessWindow.getState().poll()}
        />
      ) : total === 0 ? (
        <SurfaceState empty emptyLabel="No runs yet" emptyImage={spriteUrl("workflow", "processes")} emptyKind="process" />
      ) : (
        <div className="process-list" data-testid="process-list">
          <ObjectList
            label="Processes"
            density="dense"
            rows={rows}
            columns={columns.filter((column) => !["target", "where"].includes(column.key)
              || rows.some((row) => row.cells?.[column.key]))}
            sort={sort}
            onSort={(key: string) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }))}
            selectedId={selected ? selectedId : null}
            onSelect={setSelectedId}
            onOpen={(id) => { if (isDecision(byId.get(id))) openDecisions(); }}
            rowProps={(row) => ({
              "data-testid": "process-row",
              "data-operation": row.id,
              style: { "--process-facts": `calc(${(whereLength.get(row.id) ?? 0) + 11}ch + 24px)` } as CSSProperties,
            })}
          />
        </div>
      )}
      <StatusBar
        data-testid="process-status"
        items={items_}
        verbs={isDecision(selected) ? (
          <Button dense variant="secondary" onClick={openDecisions} data-testid="process-answer">
            <ToolGlyph kind="open" />
            Answer
          </Button>
        ) : null}
      />
    </>
  );
}
