/** What an agent used and did (MCP M2; Betterment Q7): the hub's `used`
 *  record of an automation result or an Ask answer, and its words. */

/** One object an agent touched: its qualified ref, title and kind. */
export interface UsedRow {
  ref: string;
  label: string;
  kind?: string;
  /** Ask hub gap 2: a read with no desk record keeps what its tool said
   *  (a pull request's state; a time when the tool returned one). */
  state?: string;
  at?: string;
  /** The captured before/after rows of one revision-safe desk window Undo. */
  window_undo?: WindowUndo;
}

export interface WindowUndoState {
  id: string;
  app?: string;
  object_ref?: string | null;
  geometry?: Record<string, string | number> | null;
  minimized?: boolean;
  room?: string | null;
  revision?: number;
}

export interface WindowUndoEntry {
  id: string;
  before: WindowUndoState | null;
  after: WindowUndoState | null;
  after_revision?: number;
}

export interface WindowUndo {
  group: string;
  primary?: boolean;
  windows: WindowUndoEntry[];
}

export interface AgentUse {
  looked_at?: UsedRow[];
  /** `undo`: the agent made it, so Undo takes it back. */
  wrote?: Array<UsedRow & { undo?: boolean }>;
  /** A send the agent prepared; he presses Send. */
  prepared?: Array<UsedRow & { send_id?: string; destination?: string }>;
  /** Plain words for a grouped window action, for example "Opened 2 windows · Tiled". */
  wrote_summary?: string;
}

const KIND_NOUNS: Record<string, [string, string]> = {
  meeting: ["meeting", "meetings"],
  note: ["note", "notes"],
  decision: ["decision", "decisions"],
  knowledge: ["knowledge base", "knowledge bases"],
  zone: ["zone", "zones"],
  sequence: ["sequence", "sequences"],
  workflow: ["workflow", "workflows"],
  project: ["project", "projects"],
  people: ["person", "people"],
  person: ["person", "people"],
  workbench: ["automation", "automations"],
  artifact: ["result", "results"],
  action_item: ["task", "tasks"],
};

/** `1 send`, `2 sends`. */
export function sendWords(n: number): string {
  return n === 1 ? "1 send" : `${n} sends`;
}

/** `3 meetings, 1 note`: the rows counted by kind, in first-seen order. */
export function usedWords(rows: UsedRow[]): string {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const kind = row.kind || row.ref.split(":", 1)[0] || "";
    counts.set(kind, (counts.get(kind) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([kind, n]) => {
      const [one, many] = KIND_NOUNS[kind] ?? ["item", "items"];
      return `${n} ${n === 1 ? one : many}`;
    })
    .join(", ");
}

/** The hub's `used` record, read in one place (null when it is not one). */
export function parseUse(raw: unknown): AgentUse | null {
  if (!raw || typeof raw !== "object") return null;
  const value = raw as Record<string, unknown>;
  const rows = (list: unknown) =>
    Array.isArray(list)
      ? list.filter((row): row is Record<string, unknown> => Boolean(row) && typeof row === "object" && typeof (row as Record<string, unknown>).ref === "string")
      : [];
  const base = (row: Record<string, unknown>): UsedRow => ({
    ref: String(row.ref),
    label: String(row.label || ""),
    ...(row.kind ? { kind: String(row.kind) } : {}),
    ...(row.window_undo && typeof row.window_undo === "object"
      ? { window_undo: row.window_undo as WindowUndo }
      : {}),
  });
  return {
    looked_at: rows(value.looked_at).map((row) => ({
      ...base(row),
      ...(typeof row.state === "string" && row.state ? { state: row.state } : {}),
      ...(typeof row.at === "string" && row.at ? { at: row.at } : {}),
    })),
    wrote: rows(value.wrote).map((row) => ({ ...base(row), undo: row.undo === true })),
    prepared: rows(value.prepared).map((row) => ({
      ...base(row),
      send_id: String(row.send_id || ""),
      destination: String(row.destination || ""),
    })),
    ...(typeof value.wrote_summary === "string" ? { wrote_summary: value.wrote_summary } : {}),
  };
}
