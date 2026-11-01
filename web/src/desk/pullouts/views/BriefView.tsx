/** The brief's helpers, and Today's Since-yesterday fold (Betterment daily
 *  D4). The Brief wing it replaced (Generate, Refresh, Acknowledge, Defer,
 *  the PEOPLE overlay) is parked in `../_parked/BriefWing.tsx`; the shelf
 *  data stays. */
import { wireDate } from "../../surface/format";
import { useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { openSurfaceOr } from "../../shell";
import { BriefSendWells } from "../../documentSendsLazy";
import { refOpener } from "../../openObject";
import { openIntelligence } from "../../intelligenceNavigation";
import { StandingPagesSection, useStandingPages } from "../../standingPages";
import { DotWord } from "../../surface/kit";
import "../attention-records.css";

interface BriefItem {
  id: string;
  section: BriefSection;
  text: string;
  detail?: string | null;
  source_ref?: string | null;
  priority: number;
}

type BriefSection = "this_week" | "changed" | "broke" | "waiting" | "decisions";

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
const LOOKBACK_SECTIONS: readonly BriefSection[] = ["changed", "broke", "decisions"];

const _MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

/** SINCE FRIDAY / SINCE THURSDAY / ... from the lookback start day (local). */
export function sinceFridayLabel(periodStart: string | undefined): string {
  const d = parseLocal(periodStart);
  if (!d) return "SINCE FRIDAY";
  const days = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];
  return `SINCE ${days[d.getDay()]}`;
}

/** Source emblem chip from source_ref (for SINCE FRIDAY items). */

/** Replace YYYY-MM-DD in a string with MON DD (e.g. "SEP 04"). */
function humanizeDate(text: string): string {
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
  return d ? ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"][d.getDay()] : null;
}

/** `SEP 01 – 05` / `AUG 31 – SEP 05`: the local Monday of `generatedAt`'s
 * week through its local day (the brief's period, viewer's clock). */
export function periodLabelLocal(generatedAt: string | null | undefined): string | null {
  const gen = parseLocal(generatedAt);
  if (!gen) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  const daysSinceMonday = (gen.getDay() + 6) % 7;
  const monday = new Date(gen.getFullYear(), gen.getMonth(), gen.getDate() - daysSinceMonday);
  const monMonth = _MONTHS[monday.getMonth()];
  const genMonth = _MONTHS[gen.getMonth()];
  // A plain hyphen: the vocabulary guard forbids em/en dashes in rendered copy.
  if (monday.getMonth() === gen.getMonth()) return `${monMonth} ${pad(monday.getDate())}-${pad(gen.getDate())}`;
  return `${monMonth} ${pad(monday.getDate())} - ${genMonth} ${pad(gen.getDate())}`;
}

/** `SEP 05 08:00` in the viewer's local time: the brief's one clock
 *  (PHILO-6-02). The Arrival caption, the Arrival receipt and this view all
 *  render the producer's `generated_at` through it. */
export function generatedStampLocal(generatedAt: string | null | undefined): string | null {
  const gen = parseLocal(generatedAt);
  if (!gen) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${_MONTHS[gen.getMonth()]} ${pad(gen.getDate())} ${pad(gen.getHours())}:${pad(gen.getMinutes())}`;
}

/** PHILO-15 05: a source the producer could not read is a NOT READ row
 *  (`source_ref` `not_read:<source>`); such a brief is PARTIAL. */
const NOT_READ_REF = "not_read:";

export function briefIsPartial(
  sections: Record<string, ReadonlyArray<{ source_ref?: string | null }> | undefined> | null | undefined,
): boolean {
  return Object.values(sections ?? {}).some((items) =>
    (items ?? []).some((item) => String(item?.source_ref ?? "").startsWith(NOT_READ_REF)),
  );
}

/** `GENERATED SEP 05 08:00` in the viewer's local time. */
export function generatedLabelLocal(generatedAt: string | null | undefined): string | null {
  const stamp = generatedStampLocal(generatedAt);
  return stamp ? `GENERATED ${stamp}` : null;
}

/** Parse a lookback item into kind token + primary + detail.
 *
 * Item text is e.g. "Review decision: Ania owns the API spec" or
 * "Commitment due 2026-09-04: Ania owns the API spec".
 * Kind = prefix before first ": " (sentence case, ISO dates humanized).
 * Primary = text after the colon. */
function parseLookbackItem(item: BriefItem): {
  kind: string | null;
  primary: string;
  detail: string | null;
} {
  const colonIdx = item.text.indexOf(": ");
  if (colonIdx > 0) {
    const rawKind = item.text.slice(0, colonIdx);
    // Window grammar (2026-10-25 audit): the kind reads in sentence case
    // (`Meeting recorded`, `Commitment due Sep 04`), never mono caps.
    const humane = humanizeDate(rawKind).replace(/\b(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\b/g,
      (month) => month.charAt(0) + month.slice(1).toLowerCase());
    const kind = humane.charAt(0).toUpperCase() + humane.slice(1);
    const primary = item.text.slice(colonIdx + 2);
    return { kind, primary, detail: item.detail ?? null };
  }
  return { kind: null, primary: item.text, detail: item.detail ?? null };
}

/** PHILO-17: a brief row that names a setup blocker (`blocker:<key>`, from
 *  the needs-you rule): its verb opens Runs on, or reads again for `unknown`. */
export function blockerKey(sourceRef: string | null | undefined): string | null {
  const match = /^blocker:(.+)$/.exec(String(sourceRef ?? ""));
  return match ? match[1] : null;
}

/** One kind of change, for the folded count line. */
export type SinceKind = "meeting" | "decision" | "promise" | "failed" | "unread" | "other";

/** A Since row's kind as a dot and a word: its colour by what changed. */
const SINCE_TONE: Record<SinceKind, "ok" | "warn" | "fail" | "info" | "ask" | "idle"> = {
  meeting: "info", decision: "ok", promise: "warn", failed: "fail", unread: "ask", other: "idle",
};

export function sinceKind(item: Pick<BriefItem, "section" | "text"> & { source_ref?: string | null }): SinceKind {
  if (String(item.source_ref ?? "").startsWith(NOT_READ_REF)) return "unread";
  if (item.section === "broke") return "failed";
  if (/^Meeting recorded:/.test(item.text)) return "meeting";
  if (/^Commitment due\b/.test(item.text)) return "promise";
  if (/^(Decision (confirmed|made)|Review decision):/.test(item.text)) return "decision";
  return "other";
}

/** `2 meetings · 1 decision · 5 promises · 1 failed · 2 more`; a kind with
 *  none is left out (no counters of zero). Empty when nothing changed. */
export function sinceCounts(
  items: ReadonlyArray<Pick<BriefItem, "section" | "text"> & { source_ref?: string | null }>,
): string {
  const n: Record<SinceKind, number> = { meeting: 0, decision: 0, promise: 0, failed: 0, unread: 0, other: 0 };
  for (const item of items) n[sinceKind(item)] += 1;
  const word = (count: number, one: string, many: string) => (count ? `${count} ${count === 1 ? one : many}` : null);
  return [
    word(n.meeting, "meeting", "meetings"),
    word(n.decision, "decision", "decisions"),
    word(n.promise, "promise", "promises"),
    word(n.failed, "failed", "failed"),
    word(n.unread, "not read", "not read"),
    word(n.other, "more", "more"),
  ].filter(Boolean).join(" · ");
}

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

/** `Since yesterday`, or `Since Friday` when the brief looks back further
 *  (Monday). */
export function sinceLabel(periodStart: string | null | undefined, now: Date = new Date()): string {
  const start = parseLocal(periodStart);
  if (!start) return "Since yesterday";
  const yesterday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
  const same = start.getFullYear() === yesterday.getFullYear() && start.getMonth() === yesterday.getMonth()
    && start.getDate() === yesterday.getDate();
  return same ? "Since yesterday" : `Since ${WEEKDAYS[start.getDay()]}`;
}

/** The lookback rows of a brief: what changed, what broke, the decisions. */
export function lookbackItems(brief: Pick<MondayBrief, "sections"> | null | undefined): BriefItem[] {
  // PHILO-15 05: an unread source is never silent. Its NOT READ row sits in
  // WAITING but is not a Needs-you row: it limits what this brief can claim,
  // so it comes first here.
  const unread = (brief?.sections.waiting ?? []).filter((item) =>
    String(item.source_ref ?? "").startsWith(NOT_READ_REF));
  return [...unread, ...LOOKBACK_SECTIONS.flatMap((id) => brief?.sections[id] ?? [])];
}

/** Memory on the Desk (canvas section 2, option B): the desk's standing
 *  pages, under what changed. Read only when the fold is open. */
function DeskPages() {
  const pages = useStandingPages("desk");
  return (
    <StandingPagesSection
      pages={[...pages.filter((page) => page.slug === "what-i-owe"), ...pages.filter((page) => page.slug !== "what-i-owe")]}
      presentation="questions"
    />
  );
}

/** Betterment daily D4: Since yesterday (Since Friday on Monday), in Today.
 *  Folded, one line of counts; unfolded, what changed, each row opening what
 *  it names. The brief is made when Today opens (the hub's `ensure` read);
 *  there is no Generate or Refresh. */
export function SinceYesterday({ brief, failed, now, defaultOpen = false, openRequest = 0, onRetry }: {
  brief: MondayBrief | null;
  /** A new number opens the fold (the "Show since yesterday" verb). */
  openRequest?: number;
  /** The read failed: one line and Retry. */
  failed: boolean;
  now: Date;
  defaultOpen?: boolean;
  onRetry(): void;
}) {
  const [open, setOpen] = useState(defaultOpen || openRequest > 0);
  useEffect(() => { if (openRequest > 0) setOpen(true); }, [openRequest]);
  const items = lookbackItems(brief);
  const label = sinceLabel(brief?.period_start, now);
  const counts = sinceCounts(items);
  if (failed && !brief) {
    return (
      <div className="today-fold" data-testid="today-since-failed" role="status">
        <span className="today-fold-label">{label}</span>
        <span className="kit-pill" data-tone="danger">The brief could not be read. Nothing changed. Press Retry.</span>
        <Button dense variant="ghost" onClick={onRetry}>Retry</Button>
      </div>
    );
  }
  if (!brief) return null;
  return (
    <section className="today-fold" data-testid="today-since" aria-label={label}>
      <Button variant="chrome" className="today-fold-head" aria-expanded={open} data-testid="today-since-toggle"
        onClick={() => setOpen((value) => !value)}>
        <span className="today-fold-label">{label}</span>
        <span className="today-fold-counts" data-testid="today-since-counts">{counts || "No changes"}</span>
      </Button>
      {open ? (
        <div className="today-fold-body" data-testid="today-since-rows">
          {items.map((item) => {
            const parsed = parseLookbackItem(item);
            const blocker = blockerKey(item.source_ref);
            if (blocker) {
              return (
                <div key={item.id} className="today-fold-row" data-testid="brief-blocker-row">
                  <span className="kit-pill" data-tone="warn">{parsed.primary}</span>
                  <Button dense onClick={() => openSurfaceOr("open-concierge", "/models", blocker)}
                    data-testid={`brief-blocker-verb-${blocker}`}>
                    {parsed.detail || "Choose engine"}
                  </Button>
                </div>
              );
            }
            const opener = refOpener(item.source_ref);
            return (
              <div key={item.id} className="today-fold-row" data-testid="brief-sf-row" data-kind={sinceKind(item)}>
                {opener ? (
                  <Button variant="chrome" className="today-fold-primary" onClick={() => opener()}>{parsed.primary}</Button>
                ) : <span className="today-fold-primary">{parsed.primary}</span>}
                <span className="today-fold-facts">
                  {parsed.kind ? <DotWord tone={SINCE_TONE[sinceKind(item)]} className="today-fold-state" data-testid="brief-sf-kind">{parsed.kind}</DotWord> : null}
                  {parsed.detail ? <span>{humanizeDate(parsed.detail)}</span> : null}
                </span>
              </div>
            );
          })}
          <div className="today-fold-verbs">
            {/* The Decisions door: it opens the Decisions window (2026-10-25). */}
            <Button dense variant="ghost" data-testid="today-since-decisions"
              onClick={() => openIntelligence({ view: "receipts" })}>Decisions</Button>
          </div>
          <DeskPages />
          <BriefSendFold brief={brief as Parameters<typeof BriefSendWells>[0]["brief"]} />
        </div>
      ) : null}
    </section>
  );
}

/** PHILO-17 (owner: the Send well was fully open under the brief): in the
 *  Brief the well starts folded, one row; Send opens it (the destination,
 *  the preview and the send itself), Hide folds it again. */
export function BriefSendFold({ brief }: { brief: Parameters<typeof BriefSendWells>[0]["brief"] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="intelligence-brief-send" data-testid="brief-send-fold">
      <div className="intelligence-brief-blocker">
        <span className="intelligence-brief-send-words">Send this brief</span>
        <Button dense variant={open ? "ghost" : "secondary"} aria-expanded={open} data-testid="brief-send-toggle"
          onClick={() => setOpen((value) => !value)}>
          {open ? "Hide" : "Send"}
        </Button>
      </div>
      {open ? <BriefSendWells brief={brief} /> : null}
    </div>
  );
}
