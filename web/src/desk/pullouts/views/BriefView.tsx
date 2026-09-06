import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { useWriteReceipt } from "../../hooks/useWriteReceipt";
import { refreshIntelligenceAttention } from "../../intelligenceAttention";
import { openSurfaceOr } from "../../shell";
import { SurfaceLedgerRow, SurfaceState } from "../../surface/Surface";
import { SurfaceFooter } from "../../surface/SurfaceFooter";
import { StateChip, countToken } from "../../surface";

interface BriefItem {
  id: string;
  section: BriefSection;
  text: string;
  detail?: string | null;
  source_ref?: string | null;
  priority: number;
}

type BriefSection = "this_week" | "changed" | "broke" | "waiting" | "decisions";

type ShelfState = "acknowledged" | "deferred";

interface PersonSection {
  relationship_id: string;
  display_name: string;
  they_owe_count: number;
  stalest_age_days: number | null;
  you_owe_count: number;
  agenda_backlog: number;
  next_one_on_one: { event_id: string; title: string; starts_at: string } | null;
}

type MondayBrief = {
  id: string;
  headline: string;
  sections: Partial<Record<BriefSection, BriefItem[]>>;
  is_empty: boolean;
  shelf?: Record<string, ShelfState>;
  person_sections?: PersonSection[];
  person_sections_state?: string;
  period_label?: string | null;
  generated_label?: string | null;
  period_start?: string;
  generated_at?: string;
};

const LOOKBACK_SECTIONS: readonly BriefSection[] = ["changed", "broke", "waiting", "decisions"];

const _MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];

/** SINCE FRIDAY / SINCE THURSDAY / ... from the lookback start day (local). */
export function sinceFridayLabel(periodStart: string | undefined): string {
  const d = parseLocal(periodStart);
  if (!d) return "SINCE FRIDAY";
  const days = ["SUNDAY", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"];
  return `SINCE ${days[d.getDay()]}`;
}

/** Source emblem chip from source_ref (for SINCE FRIDAY items). */
function sourceEmblem(sourceRef: string | null | undefined): string | null {
  if (!sourceRef) return null;
  const lower = sourceRef.toLowerCase();
  if (lower.startsWith("meeting:") || lower.startsWith("meeting_watch:")) return "MTG";
  if (lower.startsWith("calendar:") || lower.startsWith("calendar_event:")) return null;
  if (lower.includes("github") || lower.includes("gh")) return "GH";
  if (lower.includes("jira") || lower.includes("confluence")) return "J";
  if (lower.startsWith("decision:") || lower.startsWith("actuator_proposal:")) return null;
  if (lower.startsWith("pipeline:") || lower.startsWith("pipeline-event:")) return "SYS";
  return null;
}

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
  if (!iso) return null;
  const day = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso.trim());
  const d = day
    ? new Date(Number(day[1]), Number(day[2]) - 1, Number(day[3]))
    : new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
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

/** `GENERATED SEP 05 08:00` in the viewer's local time. */
export function generatedLabelLocal(generatedAt: string | null | undefined): string | null {
  const gen = parseLocal(generatedAt);
  if (!gen) return null;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `GENERATED ${_MONTHS[gen.getMonth()]} ${pad(gen.getDate())} ${pad(gen.getHours())}:${pad(gen.getMinutes())}`;
}

/** Parse a lookback item into kind token + primary + detail.
 *
 * Item text is e.g. "Review decision: Ania owns the API spec" or
 * "Commitment due 2026-09-04: Ania owns the API spec".
 * Kind = prefix before first ": " (uppercased, ISO dates humanized).
 * Primary = text after the colon. */
function parseLookbackItem(item: BriefItem): {
  kind: string | null;
  primary: string;
  detail: string | null;
} {
  const colonIdx = item.text.indexOf(": ");
  if (colonIdx > 0) {
    const rawKind = item.text.slice(0, colonIdx);
    const kind = humanizeDate(rawKind).toUpperCase();
    const primary = item.text.slice(colonIdx + 2);
    return { kind, primary, detail: item.detail ?? null };
  }
  return { kind: null, primary: item.text, detail: item.detail ?? null };
}

function sourceLabel(sourceRef: string): string {
  return sourceRef.replace(/:/g, " · ").replace(/_/g, " ");
}

/* ================================================================== */

export function BriefView({ header, onOpenFollowThrough }: { header: ReactNode; onOpenFollowThrough?: (id: string) => void }) {
  const [brief, setBrief] = useState<MondayBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [shelf, setShelf] = useState<Record<string, ShelfState>>({});
  const [shelving, setShelving] = useState(false);
  const [selectedPersonId, setSelectedPersonId] = useState<string | null>(null);
  const [addingAgenda, setAddingAgenda] = useState(false);
  const { attempt, receipt } = useWriteReceipt();

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const latest = await apiFetch<MondayBrief | null>("/api/brief/latest");
      setBrief(latest);
      setShelf(latest?.shelf ?? {});
    } catch (requestError) {
      setError(readableError(requestError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const generate = async () => {
    setGenerating(true);
    setError("");
    try {
      const generated = await apiFetch<MondayBrief>("/api/brief/generate", { method: "POST" });
      setBrief(generated);
      setShelf(generated?.shelf ?? {});
    } catch (requestError) {
      setError(readableError(requestError));
    } finally {
      setGenerating(false);
    }
  };

  /* ── Derived data ─────────────────────────────────────────────── */

  const thisWeekItems = brief?.sections["this_week"] ?? [];
  const hasThisWeek = thisWeekItems.length > 0;
  const lookbackItems = LOOKBACK_SECTIONS.flatMap((id) => brief?.sections[id] ?? []);
  const hasLookback = lookbackItems.length > 0;
  const allItems = [...thisWeekItems, ...lookbackItems];
  const selected = allItems.find((item) => item.id === selectedId);
  const selectedPerson = brief?.person_sections?.find((p) => p.relationship_id === selectedPersonId);

  /* ── THIS WEEK composed rows ──────────────────────────────────── */

  const twMeetings = thisWeekItems.find((i) => i.source_ref === "calendar:week");
  const twNext = thisWeekItems.find((i) => i.text.startsWith("Next:"));
  const twArmed = thisWeekItems.find((i) => i.source_ref === "calendar:armed");
  const twDue = thisWeekItems.find((i) => i.source_ref === "meeting_watch:commitments_due");

  const meetingCount = (() => {
    if (!twMeetings) return 0;
    const m = twMeetings.text.match(/^(\d+)\s+meeting/);
    return m ? parseInt(m[1], 10) : 0;
  })();

  const nextToken = (() => {
    if (!twNext) return null;
    const m = twNext.text.match(/^Next:\s+(.+?)\s+at\s+(\d{2}:\d{2})$/);
    if (m) return `NEXT ${m[1].toUpperCase()} ${m[2]}`;
    return `NEXT ${twNext.text.replace(/^Next:\s+/i, "").toUpperCase()}`;
  })();

  const armedCount = (() => {
    if (!twArmed) return 0;
    const m = twArmed.text.match(/^(\d+)\s+armed/);
    return m ? parseInt(m[1], 10) : 0;
  })();

  const dueCount = (() => {
    if (!twDue) return 0;
    const m = twDue.text.match(/^(\d+)\s+commitment/);
    return m ? parseInt(m[1], 10) : 0;
  })();

  // Detail format from backend: "commitment text | YYYY-MM-DD"
  const dueDetailParts = (twDue?.detail ?? "").split(" | ");
  const dueCommitmentText = dueDetailParts[0] || null;
  const dueDayToken = dueDetailParts[1] ? dayToken(dueDetailParts[1]) : null;

  /* ── meetingsLabel / armedLabel / dueLabel via countToken (A.8) ── */

  const meetingsLabel = countToken(meetingCount, "MEETING", "MEETINGS");
  const armedLabel = countToken(armedCount, "ARMED");
  const dueLabel = countToken(dueCount, "DUE");

  /* ── Triage shelf ─────────────────────────────────────────────── */

  const addToAgenda = async (personId: string) => {
    setAddingAgenda(true);
    await attempt("add to 1:1 agenda", async () => {
      const sessionsResp = await apiFetch<{ one_on_ones: Array<{ id: string; state: string }> }>(
        `/api/people/relationships/${encodeURIComponent(personId)}/one-on-ones`,
      );
      let sessionId: string | undefined;
      const openSession = sessionsResp.one_on_ones?.find((s) => s.state !== "closed");
      if (openSession) { sessionId = openSession.id; }
      else {
        const created = await apiFetch<{ one_on_one: { id: string } }>(
          `/api/people/relationships/${encodeURIComponent(personId)}/one-on-ones`,
          { method: "POST", json: { visibility: "shared_intent" } },
        );
        sessionId = created.one_on_one.id;
      }
      await apiFetch(
        `/api/people/one-on-ones/${encodeURIComponent(sessionId)}/agenda`,
        { method: "POST", json: { body: "Follow up from brief", visibility: "shared_intent", state: "open", source: { kind: "brief" } } },
      );
      refreshIntelligenceAttention();
    });
    setAddingAgenda(false);
  };

  const setShelfState = async (state: ShelfState) => {
    const itemId = selectedId;
    if (!itemId) return;
    const next: ShelfState | null = shelf[itemId] === state ? null : state;
    setShelving(true);
    const result = await attempt(
      next === null ? "clear triage" : next,
      () => apiFetch(`/api/brief/items/${encodeURIComponent(itemId)}/shelf`, { method: "POST", json: { state: next } }),
    );
    setShelving(false);
    if (!result.ok) return;
    setShelf((current) => {
      const updated = { ...current };
      if (next === null) delete updated[itemId];
      else updated[itemId] = next;
      return updated;
    });
    refreshIntelligenceAttention();
  };

  /* ── Body ─────────────────────────────────────────────────────── */

  const body = loading ? (
    <SurfaceState loading />
  ) : error ? (
    <SurfaceState error={error} onRetry={() => void load()} />
  ) : !brief ? (
    <SurfaceState
      empty
      emptyLabel="No brief generated."
      onAction={() => void generate()}
      actionLabel={generating ? "Generating..." : "Generate"}
    />
  ) : brief.is_empty ? (
    <SurfaceState empty emptyLabel="Nothing material changed" />
  ) : (
    <>
      {/* ── HEAD: period (display, ONCE) + generated (caption) ──
          HS-175 counsel C8: both formatted HERE from generated_at in the
          viewer's local time; the hub's labels are the fallback. */}
      {(() => {
        const period = periodLabelLocal(brief.generated_at) ?? brief.period_label;
        return period ? (
          <div className="intelligence-brief-period" data-testid="brief-period-label" role="heading" aria-level={2}>
            {period}
          </div>
        ) : null;
      })()}
      {(() => {
        const generated = generatedLabelLocal(brief.generated_at) ?? brief.generated_label;
        return generated ? (
          <div className="intelligence-brief-generated" data-testid="brief-generated-label">
            {generated}
          </div>
        ) : null;
      })()}

      {/* ── THIS WEEK (absent when empty per A.8) ──────────────── */}
      {hasThisWeek ? (
        <div className="intelligence-brief-section" data-testid="brief-this-week">
          <div className="intelligence-brief-section-caption">THIS WEEK</div>

          {/* MEETINGS row with NEXT token (countToken = null at zero) */}
          {meetingsLabel ? (
            <div className="intelligence-brief-tw-row" data-testid="brief-tw-meetings">
              <span className="intelligence-brief-tw-primary">{meetingsLabel}</span>
              {nextToken ? (
                <span className="intelligence-brief-tw-token" data-testid="brief-tw-next">{nextToken}</span>
              ) : null}
            </div>
          ) : null}

          {/* ARMED row (countToken = null at zero) */}
          {armedLabel ? (
            <div className="intelligence-brief-tw-row" data-testid="brief-tw-armed">
              <span className="intelligence-brief-tw-primary">{armedLabel}</span>
            </div>
          ) : null}

          {/* DUE row with commitment text + day token */}
          {dueLabel ? (
            <div className="intelligence-brief-tw-row intelligence-brief-tw-due" data-testid="brief-tw-due">
              <div className="intelligence-brief-tw-due-head">
                <span className="intelligence-brief-tw-primary">{dueLabel}</span>
              </div>
              {dueCommitmentText ? (
                <div className="intelligence-brief-tw-due-detail">
                  <span className="intelligence-brief-tw-detail-text">{dueCommitmentText}</span>
                  {dueDayToken ? (
                    <span className="intelligence-brief-tw-token" data-testid="brief-tw-due-day">{dueDayToken}</span>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      {/* ── SINCE FRIDAY: flat rows, no folds, no "00" ─────────── */}
      {hasLookback ? (
        <div className="intelligence-brief-section" data-testid="brief-since-friday">
          <div className="intelligence-brief-section-caption">{sinceFridayLabel(brief.period_start)}</div>
          <div className="intelligence-brief-flat" data-testid="brief-lookback-rows">
            {lookbackItems.map((item) => {
              const state = shelf[item.id];
              const isOpen = selectedId === item.id;
              const emblem = sourceEmblem(item.source_ref);
              const parsed = parseLookbackItem(item);
              return (
                <div key={item.id} className="intelligence-brief-sf-row" data-testid="brief-sf-row">
                  {parsed.kind ? (
                    <span className="intelligence-brief-sf-kind" data-testid="brief-sf-kind">{parsed.kind}</span>
                  ) : null}
                  <div className="intelligence-brief-sf-body">
                    <span className="intelligence-brief-sf-primary"
                      role="button"
                      tabIndex={0}
                      onClick={() => {
                        const ftId = item.source_ref?.match(/^(?:follow-through|action_item):(.+)$/)?.[1];
                        if (ftId && onOpenFollowThrough) onOpenFollowThrough(ftId);
                        else setSelectedId(isOpen ? null : item.id);
                      }}
                      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") e.currentTarget.click(); }}
                    >
                      {parsed.primary}
                    </span>
                    {parsed.detail ? (
                      <span className="intelligence-brief-sf-detail">{humanizeDate(parsed.detail)}</span>
                    ) : null}
                  </div>
                  {emblem ? (
                    <span className="surface-token" data-chip data-testid="brief-source-emblem">{emblem}</span>
                  ) : null}
                  {state ? (
                    <span className="intelligence-brief-shelf-state">{state}</span>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {/* ── People overlay ──────────────────────────────────────── */}
      {brief.person_sections && brief.person_sections.length > 0 ? (
        <div className="intelligence-brief-person-sections" data-testid="person-sections">
          <div className="intelligence-brief-section-caption">PEOPLE</div>
          <div className="intelligence-brief-flat">
            {brief.person_sections.map((person) => {
              const signals: string[] = [];
              if (person.they_owe_count > 0) {
                const age = person.stalest_age_days != null ? ` (${person.stalest_age_days}d)` : "";
                signals.push(`They owe ${person.they_owe_count}${age}`);
              }
              if (person.you_owe_count > 0) signals.push(`You owe ${person.you_owe_count}`);
              if (person.agenda_backlog > 0) signals.push(`${person.agenda_backlog} agenda`);
              if (person.next_one_on_one) signals.push(`Next: ${person.next_one_on_one.title || "1:1"}`);
              const isOpen = selectedPersonId === person.relationship_id;
              return (
                <SurfaceLedgerRow
                  key={person.relationship_id}
                  primary={person.display_name}
                  open={isOpen}
                  onToggle={() => setSelectedPersonId(isOpen ? null : person.relationship_id)}
                  lineLabel={`Person: ${person.display_name}`}
                  data-testid={`person-row-${person.relationship_id}`}
                >
                  <div className="intelligence-brief-item-detail intelligence-brief-person-detail" data-testid={`person-signals-${person.relationship_id}`}>
                    {signals.map((s, i) => <p key={i}>{s}</p>)}
                  </div>
                </SurfaceLedgerRow>
              );
            })}
          </div>
        </div>
      ) : brief.person_sections_state === "unavailable" ? (
        <div className="intelligence-brief-person-unavailable" data-testid="person-sections-unavailable">
          <StateChip state="idle" label="PEOPLE · UNAVAILABLE" />
        </div>
      ) : null}
    </>
  );

  return (
    <>
      <div className="desk-pullout-body desk-surface-body intelligence-pullout">
        {header}
        <section className="intelligence-view intelligence-brief" aria-live="polite">
          {body}
        </section>
      </div>
      <SurfaceFooter
        receipt={
          receipt ??
          (selectedPerson
            ? `PERSON · ${selectedPerson.display_name}`
            : selected
              ? `SELECTED · ${sourceLabel(selected.source_ref ?? selected.id)}`
              : undefined)
        }
        verbs={
          selectedPerson ? (
            <>
              <Button dense disabled={addingAgenda} onClick={() => void addToAgenda(selectedPerson.relationship_id)} data-testid="verb-add-agenda">
                Add to 1:1 agenda
              </Button>
              <Button dense variant="ghost" onClick={() => openSurfaceOr("people", "/people", selectedPerson.relationship_id)} data-testid="verb-open-person">
                Open person
              </Button>
            </>
          ) : (
            <>
              <Button dense disabled={!selected || shelving} aria-pressed={selectedId ? shelf[selectedId] === "acknowledged" : undefined} onClick={() => void setShelfState("acknowledged")}>
                Acknowledge
              </Button>
              <Button dense variant="ghost" disabled={!selected || shelving} aria-pressed={selectedId ? shelf[selectedId] === "deferred" : undefined} onClick={() => void setShelfState("deferred")}>
                Defer
              </Button>
              <Button dense variant="ghost" disabled={!selected} onClick={() => selected && openSurfaceOr("dictate", "/dictation", selected.source_ref ?? undefined)}>
                Speak
              </Button>
            </>
          )
        }
      />
    </>
  );
}
