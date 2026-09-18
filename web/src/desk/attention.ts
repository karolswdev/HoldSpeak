// HS-200-15 — the attention ranking, the dedup and the reason token, as
// the arrival reads them. ONE pure module for every consumer.
//
// The rule mirrors `holdspeak/services/attention_ranking.py` line for
// line (D2(b), the owner's verdict Q1): five classes in rank order —
// OVERDUE · DUE TODAY · NOT RUN · NO DUE DATE · WAITING — ordered within
// the class by an observable time, tie-broken by the stable id. Severity
// is never a sort key. The wire carries `rankClass` for every Room row;
// the browser classifies only what it merges in itself (Door cards).
//
// The dedup key is the same too: the same Project and the same thing
// (title normalised: case, spacing, a leading issue key or PR number),
// merged only ACROSS sources whose refs agree or where one side has no
// ref. Two projections that share a source and carry distinct refs are
// never one obligation (counsel P0-1).

export type RankClass =
  | "overdue"
  | "due_today"
  | "not_run"
  | "no_due_date"
  | "waiting";

/** The closed vocabulary, in rank order. */
export const RANK_CLASSES: readonly RankClass[] = [
  "overdue",
  "due_today",
  "not_run",
  "no_due_date",
  "waiting",
];

/** The class as the face says it (the ranking key, stated on the face). */
export const RANK_LABEL: Record<RankClass, string> = {
  overdue: "OVERDUE",
  due_today: "DUE TODAY",
  not_run: "NOT RUN",
  no_due_date: "NO DUE DATE",
  waiting: "WAITING",
};

/** The first view shows at most this many rows (verdict Q1). */
export const ATTENTION_CAP = 5;

const RANK: Record<RankClass, number> = {
  overdue: 0,
  due_today: 1,
  not_run: 2,
  no_due_date: 3,
  waiting: 4,
};

const SEVERITY: Record<string, number> = { danger: 0, warning: 1, info: 2 };

/** One constituent projection of a merged row (the `N SOURCES` disclosure). */
export interface AttentionSource {
  id?: string | null;
  source: string;
  title?: string;
  why: string;
  severity?: string;
  fromLastObservation?: boolean;
  observedAt?: string | null;
  verbHref?: string | null;
}

/** What the ranking and the dedup read. Every attention row has these. */
export interface RankableItem {
  id?: string;
  projectId?: string;
  title: string;
  why: string;
  /** The Room's own change/observation stamp (ISO). `ageToken` carries the
   *  same ISO on older payloads. */
  since?: string;
  ageToken?: string;
  dueAt?: string | null;
  /** The wire's class, trusted when it is one of the five. */
  rankClass?: string;
  kind?: string | null;
  severity: string;
  source: string;
  sources?: AttentionSource[];
  dedupCount?: number;
  fromLastObservation?: boolean;
  observedAt?: string | null;
}

// ── time ───────────────────────────────────────────────────────────

function parseStamp(value: string | null | undefined): Date | null {
  if (!value || typeof value !== "string") return null;
  const text = value.trim();
  if (!text) return null;
  // A bare date is a local day, never a UTC midnight that lands yesterday.
  const day = /^(\d{4})-(\d{2})-(\d{2})$/.exec(text);
  const parsed = day
    ? new Date(Number(day[1]), Number(day[2]) - 1, Number(day[3]))
    : new Date(text);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

function epoch(value: string | null | undefined): number {
  const parsed = parseStamp(value);
  return parsed ? parsed.getTime() : Number.POSITIVE_INFINITY;
}

function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

function observedSince(item: RankableItem): string | undefined {
  return item.since || item.ageToken || item.observedAt || undefined;
}

// ── classification ────────────────────────────────────────────────

function isRankClass(value: unknown): value is RankClass {
  return typeof value === "string" && value in RANK;
}

/** The rank class of one row, from observable facts only. */
export function attentionClass(item: RankableItem, now: Date = new Date()): RankClass {
  const due = parseStamp(item.dueAt);
  if (due) {
    const dueDay = startOfDay(due);
    const today = startOfDay(now);
    if (dueDay < today) return "overdue";
    if (dueDay === today) return "due_today";
    return "waiting";
  }
  const why = (item.why || "").trim().toUpperCase();
  if (why.startsWith("OVERDUE")) return "overdue";
  if (why.startsWith("DUE TODAY")) return "due_today";
  if (why.startsWith("NOT RUN") || item.kind === "intel_not_run") return "not_run";
  if (why.startsWith("WAITING")) return "waiting";
  return "no_due_date";
}

/** The wire's class when it is lawful, else the browser's own reading. */
export function rankClassOf(item: RankableItem, now: Date = new Date()): RankClass {
  return isRankClass(item.rankClass) ? item.rankClass : attentionClass(item, now);
}

function withinClassKey(cls: RankClass, item: RankableItem): number {
  const due = item.dueAt ?? undefined;
  const since = observedSince(item);
  switch (cls) {
    case "overdue":
      return epoch(due || since);
    case "due_today":
      return epoch(due);
    case "not_run":
      return epoch(since);
    case "no_due_date": {
      const stamp = epoch(since);
      return stamp === Number.POSITIVE_INFINITY ? stamp : -stamp;
    }
    default:
      return epoch(since || due);
  }
}

/** The complete, deterministic ranking key. */
export function sortKey(item: RankableItem, now: Date): [number, number, string] {
  const cls = rankClassOf(item, now);
  return [RANK[cls], withinClassKey(cls, item), item.id ?? ""];
}

function compareKeys(a: [number, number, string], b: [number, number, string]): number {
  if (a[0] !== b[0]) return a[0] - b[0];
  if (a[1] !== b[1]) return a[1] < b[1] ? -1 : 1;
  return a[2] < b[2] ? -1 : a[2] > b[2] ? 1 : 0;
}

/** Rank attention rows: returns NEW objects stamped with `rankClass`. */
export function rankAttention<T extends RankableItem>(
  items: readonly T[],
  now: Date = new Date(),
): T[] {
  const stamped = items.map((item) => ({ ...item, rankClass: rankClassOf(item, now) }));
  stamped.sort((a, b) => compareKeys(sortKey(a, now), sortKey(b, now)));
  return stamped;
}

// ── dedup ─────────────────────────────────────────────────────────

const LEADING_REF = /^(?:#\d+|[A-Z][A-Z0-9]+-\d+)\s+/;

/** The comparable form of a title (`toLowerCase`, mirrored by Python's
 *  `str.lower`). */
export function normalizeTitle(title: string | null | undefined): string {
  const text = String(title ?? "").trim().replace(/\s+/g, " ");
  return text.replace(LEADING_REF, "").toLowerCase();
}

/** The projection's own ref (`KAN-7`, `#612`), or "" when it has none. */
export function projectionRef(item: RankableItem): string {
  const text = String(item.title ?? "").trim().replace(/\s+/g, " ");
  const match = LEADING_REF.exec(text);
  return match ? match[0].trim().toUpperCase() : "";
}

function mayMerge(a: RankableItem, b: RankableItem): boolean {
  if ((a.source || "") === (b.source || "")) return false;
  const ra = projectionRef(a);
  const rb = projectionRef(b);
  return !ra || !rb || ra === rb;
}

function clusters<T extends RankableItem>(group: T[]): T[][] {
  const out: T[][] = [];
  for (const row of group) {
    const home = out.find((cluster) => cluster.every((member) => mayMerge(row, member)));
    if (home) home.push(row);
    else out.push([row]);
  }
  return out;
}

function projection(item: RankableItem): AttentionSource {
  return {
    id: item.id,
    source: item.source,
    title: item.title,
    why: item.why,
    severity: item.severity,
    fromLastObservation: Boolean(item.fromLastObservation),
    observedAt: item.observedAt ?? null,
    verbHref: (item as { verbHref?: string | null }).verbHref ?? null,
  };
}

function headKey(item: RankableItem, now: Date): [number, number, number, string] {
  const [rank, within, id] = sortKey(item, now);
  return [rank, within, SEVERITY[item.severity] ?? 2, id];
}

function merge<T extends RankableItem>(group: T[], now: Date): T {
  const ordered = [...group].sort((a, b) => {
    const ka = headKey(a, now);
    const kb = headKey(b, now);
    for (let i = 0; i < 4; i += 1) {
      if (ka[i] !== kb[i]) return ka[i] < kb[i] ? -1 : 1;
    }
    return 0;
  });
  const head: T = { ...ordered[0] };
  // A row that already arrived merged (the wire) keeps its projections;
  // a browser-side merge of wire rows flattens them.
  const sources: AttentionSource[] = [];
  for (const row of ordered) {
    if (row.sources && row.sources.length > 0) sources.push(...row.sources);
    else sources.push(projection(row));
  }
  head.sources = sources;
  head.dedupCount = sources.length;
  head.severity = ordered
    .map((row) => row.severity)
    .sort((a, b) => (SEVERITY[a] ?? 2) - (SEVERITY[b] ?? 2))[0];
  const remembered = ordered.filter((row) => row.fromLastObservation);
  if (remembered.length === ordered.length) {
    head.fromLastObservation = true;
    head.observedAt =
      remembered
        .map((row) => row.observedAt ?? "")
        .sort()
        .reverse()[0] || null;
  } else {
    delete head.fromLastObservation;
    delete head.observedAt;
  }
  return head;
}

/** Collapse duplicate projections of one obligation into ONE row. */
export function dedupAttention<T extends RankableItem>(
  items: readonly T[],
  now: Date = new Date(),
): T[] {
  const byTitle = new Map<string, T[]>();
  for (const item of items) {
    const key = normalizeTitle(item.title);
    const bucket = byTitle.get(key);
    if (bucket) bucket.push(item);
    else byTitle.set(key, [item]);
  }
  const out: T[] = [];
  for (const [key, group] of byTitle) {
    if (!key) {
      for (const row of group) out.push(merge([row], now));
      continue;
    }
    const withProject = new Map<string, T[]>();
    let orphans: T[] = [];
    for (const row of group) {
      const pid = row.projectId || "";
      if (!pid) {
        orphans.push(row);
        continue;
      }
      const bucket = withProject.get(pid);
      if (bucket) bucket.push(row);
      else withProject.set(pid, [row]);
    }
    if (withProject.size === 1 && orphans.length > 0) {
      const [only] = withProject.values();
      only.push(...orphans);
      orphans = [];
    }
    for (const rows of withProject.values()) {
      for (const cluster of clusters(rows)) out.push(merge(cluster, now));
    }
    if (orphans.length > 0) {
      if (withProject.size === 0) {
        for (const cluster of clusters(orphans)) out.push(merge(cluster, now));
      } else for (const row of orphans) out.push(merge([row], now));
    }
  }
  return out;
}

/** The one call the arrival makes: dedup, then rank. */
export function rankAndDedup<T extends RankableItem>(items: readonly T[], now: Date = new Date()): T[] {
  return rankAttention(dedupAttention(items, now), now);
}

// ── the tokens the face draws ──────────────────────────────────────

/** `40 MIN` · `3 H` · `2 DAYS` · `1 DAY` — the age of a stamp, or "". */
export function ageToken(value: string | null | undefined, now: Date = new Date()): string {
  const stamp = parseStamp(value);
  if (!stamp) return "";
  const ms = Math.max(0, now.getTime() - stamp.getTime());
  const minutes = Math.floor(ms / 60000);
  if (minutes < 1) return "JUST NOW";
  if (minutes < 60) return `${minutes} MIN`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} H`;
  const days = Math.floor(hours / 24);
  return days === 1 ? "1 DAY" : `${days} DAYS`;
}

/** `OBSERVED 08:41` today, `OBSERVED 09-06 08:41` on another day, or
 *  `NEVER OBSERVED` — the observation stamp as the boards draw it. */
export function observedAtToken(value: string | null | undefined, now: Date = new Date()): string {
  const stamp = parseStamp(value);
  if (!stamp) return "NEVER OBSERVED";
  const hh = String(stamp.getHours()).padStart(2, "0");
  const mi = String(stamp.getMinutes()).padStart(2, "0");
  if (sameDay(stamp, now)) return `OBSERVED ${hh}:${mi}`;
  const mm = String(stamp.getMonth() + 1).padStart(2, "0");
  const dd = String(stamp.getDate()).padStart(2, "0");
  return `OBSERVED ${mm}-${dd} ${hh}:${mi}`;
}

const AGE_SEGMENT = /^(?:\d+\s*(?:D|H|M|MIN|DAYS?|HOURS?|MINUTES?)|JUST NOW)$/i;

/** The reason segments a source wrote, minus any age it appended. */
function reasonDetail(why: string): string[] {
  return why
    .split("·")
    .map((part) => part.trim())
    .filter((part) => part && !AGE_SEGMENT.test(part));
}

/** The reason token for one row: the class, the source's own detail when
 *  it adds to the class, and the observable age —
 *  `OVERDUE · 2 DAYS` · `DUE TODAY` · `NOT RUN · 2 DAYS` ·
 *  `NO DUE DATE · CI RED · CHANGED 40 MIN AGO` · `WAITING ON YOUR REVIEW · 3 DAYS`. */
export function reasonToken(item: RankableItem, now: Date = new Date()): string {
  const cls = rankClassOf(item, now);
  const label = RANK_LABEL[cls];
  const detail = reasonDetail((item.why || "").toUpperCase());
  const parts: string[] = [];
  // A source whose head phrase already begins with the class word states
  // the class in its own words (`WAITING ON YOUR REVIEW`), said once.
  if (detail[0] && detail[0].startsWith(label)) {
    parts.push(detail[0]);
    parts.push(...detail.slice(1));
  } else {
    parts.push(label);
    parts.push(...detail);
  }
  const since = observedSince(item);
  const due = item.dueAt ?? undefined;
  switch (cls) {
    case "overdue": {
      const stamp = parseStamp(due || since);
      if (stamp) {
        const days = Math.max(1, Math.floor((startOfDay(now) - startOfDay(stamp)) / 86400000));
        parts.push(days === 1 ? "1 DAY" : `${days} DAYS`);
      }
      break;
    }
    case "due_today":
      break;
    case "no_due_date": {
      const age = ageToken(since, now);
      if (age) parts.push(`CHANGED ${age}${age === "JUST NOW" ? "" : " AGO"}`);
      break;
    }
    default: {
      const age = ageToken(since, now);
      if (age) parts.push(age);
    }
  }
  // Dedup adjacent repeats (`WAITING · WAITING` from a bare why).
  return parts.filter((part, i) => part && parts[i - 1] !== part).join(" · ");
}

/** `NEEDS YOU 5 OF 17` when capped, `NEEDS YOU 17` otherwise, `NEEDS YOU`
 *  at zero (never `NEEDS YOU 0`). */
export function attentionCaption(shown: number, total: number, label = "NEEDS YOU"): string {
  if (total <= 0) return label;
  if (shown < total) return `${label} ${shown} OF ${total}`;
  return `${label} ${total}`;
}
