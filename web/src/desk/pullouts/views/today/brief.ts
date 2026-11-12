/** Shared brief words; the Today face draws them with the selection kit. */
import { wireDate } from "../../../surface";

export interface BriefItem {
  id: string;
  section: BriefSection;
  text: string;
  detail?: string | null;
  source_ref?: string | null;
  priority: number;
}

export type BriefSection =
  "this_week" | "changed" | "broke" | "waiting" | "decisions";

export type MondayBrief = {
  id: string;
  headline: string;
  sections: Partial<Record<BriefSection, BriefItem[]>>;
  is_empty: boolean;
  period_label?: string | null;
  generated_label?: string | null;
  period_start?: string;
  generated_at?: string;
  /** PHILO-17: the desk is newer than the brief (a meeting, a decision, an
   *  engine assignment, or a new day). The view makes the brief again. */
  stale?: boolean;
};

/** What changed (the waiting rows are Needs you's, above it in Today). */
const LOOKBACK_SECTIONS: readonly BriefSection[] = [
  "changed",
  "broke",
  "decisions",
];

const _MONTHS = [
  "JAN",
  "FEB",
  "MAR",
  "APR",
  "MAY",
  "JUN",
  "JUL",
  "AUG",
  "SEP",
  "OCT",
  "NOV",
  "DEC",
];

/** SINCE FRIDAY / SINCE THURSDAY / ... from the lookback start day (local). */
export function sinceFridayLabel(periodStart: string | undefined): string {
  const d = parseLocal(periodStart);
  if (!d) return "SINCE FRIDAY";
  const days = [
    "SUNDAY",
    "MONDAY",
    "TUESDAY",
    "WEDNESDAY",
    "THURSDAY",
    "FRIDAY",
    "SATURDAY",
  ];
  return `SINCE ${days[d.getDay()]}`;
}

/** Source emblem chip from source_ref (for SINCE FRIDAY items). */

/** Replace YYYY-MM-DD in a string with MON DD (e.g. "SEP 04"). */
export function humanizeDate(text: string): string {
  return text.replace(/\d{4}-(\d{2})-(\d{2})/g, (_match, mm, dd) => {
    const month = _MONTHS[parseInt(mm, 10) - 1] ?? mm;
    return `${month} ${dd}`;
  });
}

/** HS-175 counsel C8: parse an ISO value in the VIEWER's local time.
 * A bare `YYYY-MM-DD` is a calendar day, not UTC midnight (`new Date`
 * would shift it a day west of UTC); a timestamp parses as an instant. */
export function parseLocal(iso: string | null | undefined): Date | null {
  return wireDate(iso);
}

/** Extract day-of-week from an ISO date (local). */
export function dayToken(iso: string | null | undefined): string | null {
  const d = parseLocal(iso);
  return d
    ? ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"][d.getDay()]
    : null;
}

/** `SEP 01 – 05` / `AUG 31 – SEP 05`: the local Monday of `generatedAt`'s
 * week through its local day (the brief's period, viewer's clock). */
export function periodLabelLocal(
  generatedAt: string | null | undefined,
): string | null {
  const gen = parseLocal(generatedAt);
  if (!gen) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  const daysSinceMonday = (gen.getDay() + 6) % 7;
  const monday = new Date(
    gen.getFullYear(),
    gen.getMonth(),
    gen.getDate() - daysSinceMonday,
  );
  const monMonth = _MONTHS[monday.getMonth()];
  const genMonth = _MONTHS[gen.getMonth()];
  // A plain hyphen: the vocabulary guard forbids em/en dashes in rendered copy.
  if (monday.getMonth() === gen.getMonth())
    return `${monMonth} ${pad(monday.getDate())}-${pad(gen.getDate())}`;
  return `${monMonth} ${pad(monday.getDate())} - ${genMonth} ${pad(gen.getDate())}`;
}

/** `SEP 05 08:00` in the viewer's local time: the brief's one clock
 *  (PHILO-6-02). The Arrival caption, the Arrival receipt and this view all
 *  render the producer's `generated_at` through it. */
export function generatedStampLocal(
  generatedAt: string | null | undefined,
): string | null {
  const gen = parseLocal(generatedAt);
  if (!gen) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${_MONTHS[gen.getMonth()]} ${pad(gen.getDate())} ${pad(gen.getHours())}:${pad(gen.getMinutes())}`;
}

/** PHILO-15 05: a source the producer could not read is a NOT READ row
 *  (`source_ref` `not_read:<source>`); such a brief is PARTIAL. */
const NOT_READ_REF = "not_read:";

export function briefIsPartial(
  sections:
    | Record<string, ReadonlyArray<{ source_ref?: string | null }> | undefined>
    | null
    | undefined,
): boolean {
  return Object.values(sections ?? {}).some((items) =>
    (items ?? []).some((item) =>
      String(item?.source_ref ?? "").startsWith(NOT_READ_REF),
    ),
  );
}

/** `GENERATED SEP 05 08:00` in the viewer's local time. */
export function generatedLabelLocal(
  generatedAt: string | null | undefined,
): string | null {
  const stamp = generatedStampLocal(generatedAt);
  return stamp ? `GENERATED ${stamp}` : null;
}

/** Parse a lookback item into kind token + primary + detail.
 *
 * Item text is e.g. "Review decision: Ania owns the API spec" or
 * "Commitment due 2026-09-04: Ania owns the API spec".
 * Kind = prefix before first ": " (sentence case, ISO dates humanized).
 * Primary = text after the colon. */
export function parseLookbackItem(item: BriefItem): {
  kind: string | null;
  primary: string;
  detail: string | null;
} {
  const colonIdx = item.text.indexOf(": ");
  if (colonIdx > 0) {
    const rawKind = item.text.slice(0, colonIdx);
    // Window grammar (2026-10-25 audit): the kind reads in sentence case
    // (`Meeting recorded`, `Commitment due Sep 04`), never mono caps.
    const humane = humanizeDate(rawKind).replace(
      /\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b/g,
      (month) => month.charAt(0) + month.slice(1).toLowerCase(),
    );
    const kind = humane.charAt(0).toUpperCase() + humane.slice(1);
    const primary = item.text.slice(colonIdx + 2);
    return { kind, primary, detail: item.detail ?? null };
  }
  return { kind: null, primary: item.text, detail: item.detail ?? null };
}

/** PHILO-17: a brief row that names a setup blocker (`blocker:<key>`, from
 *  the needs-you rule): its verb opens Runs on, or reads again for `unknown`. */
export function blockerKey(
  sourceRef: string | null | undefined,
): string | null {
  const match = /^blocker:(.+)$/.exec(String(sourceRef ?? ""));
  return match ? match[1] : null;
}

/** One kind of change, for the folded count line. */
export type SinceKind =
  "meeting" | "decision" | "promise" | "failed" | "unread" | "other";

/** A Since row's kind as a dot and a word: its colour by what changed. */
export const SINCE_TONE: Record<
  SinceKind,
  "ok" | "warn" | "fail" | "info" | "ask" | "idle"
> = {
  meeting: "info",
  decision: "ok",
  promise: "ask",
  failed: "fail",
  unread: "ask",
  other: "idle",
};
/** The language (2026-11-08): each row of Since … leads with its kind's
 *  20 px sprite (the kit row grammar). */
export const SINCE_SPRITE: Record<SinceKind, string> = {
  meeting: "meeting",
  decision: "decision",
  promise: "action-item",
  failed: "meeting",
  unread: "note",
  other: "note",
};
export const SINCE_GLYPHS = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/20/`;

export function sinceKind(
  item: Pick<BriefItem, "section" | "text"> & { source_ref?: string | null },
): SinceKind {
  if (String(item.source_ref ?? "").startsWith(NOT_READ_REF)) return "unread";
  if (item.section === "broke") return "failed";
  if (/^Meeting recorded:/.test(item.text)) return "meeting";
  if (/^Commitment due\b/.test(item.text)) return "promise";
  if (/^(Decision (confirmed|made)|Review decision):/.test(item.text))
    return "decision";
  return "other";
}

/** `2 meetings · 1 decision · 5 promises · 1 failed · 2 more`; a kind with
 *  none is left out (no counters of zero). Empty when nothing changed. */
export function sinceCounts(
  items: ReadonlyArray<
    Pick<BriefItem, "section" | "text"> & { source_ref?: string | null }
  >,
): string {
  const n: Record<SinceKind, number> = {
    meeting: 0,
    decision: 0,
    promise: 0,
    failed: 0,
    unread: 0,
    other: 0,
  };
  for (const item of items) n[sinceKind(item)] += 1;
  const word = (count: number, one: string, many: string) =>
    count ? `${count} ${count === 1 ? one : many}` : null;
  return [
    word(n.meeting, "meeting", "meetings"),
    word(n.decision, "decision", "decisions"),
    word(n.promise, "promise", "promises"),
    word(n.failed, "failed", "failed"),
    word(n.unread, "not read", "not read"),
    word(n.other, "more", "more"),
  ]
    .filter(Boolean)
    .join(" · ");
}

const WEEKDAYS = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

/** `Since yesterday`, or `Since Friday` when the brief looks back further
 *  (Monday). */
export function sinceLabel(
  periodStart: string | null | undefined,
  now: Date = new Date(),
): string {
  const start = parseLocal(periodStart);
  if (!start) return "Since yesterday";
  const yesterday = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate() - 1,
  );
  const same =
    start.getFullYear() === yesterday.getFullYear() &&
    start.getMonth() === yesterday.getMonth() &&
    start.getDate() === yesterday.getDate();
  return same ? "Since yesterday" : `Since ${WEEKDAYS[start.getDay()]}`;
}

/** The lookback rows of a brief: what changed, what broke, the decisions. */
export function lookbackItems(
  brief: Pick<MondayBrief, "sections"> | null | undefined,
): BriefItem[] {
  // PHILO-15 05: an unread source is never silent. Its NOT READ row sits in
  // WAITING but is not a Needs-you row: it limits what this brief can claim,
  // so it comes first here.
  const unread = (brief?.sections.waiting ?? []).filter((item) =>
    String(item.source_ref ?? "").startsWith(NOT_READ_REF),
  );
  return [
    ...unread,
    ...LOOKBACK_SECTIONS.flatMap((id) => brief?.sections[id] ?? []),
  ];
}
