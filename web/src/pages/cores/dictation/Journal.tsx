/** HS-176-03 — the Journal wing as a STREAM (settled design D2(b)).
 *
 * What changed from HS-111-02's ledger:
 *  1. Real-time push. The wing subscribes to the `dictation.journal.entry`
 *     frame on the ONE runtime bus (`runtime/RuntimeBus.tsx`) and prepends
 *     each new row, deduplicated by id. `useResource` had no interval and no
 *     subscription, so a new utterance never appeared until a remount.
 *  2. Row grammar to the boards: `LANDED IN <label>` · `N MS` · `APPLIED`
 *     (only when the row's STORED `corrections_applied` is non-empty, and
 *     with no count) · `TAUGHT` (only on the row he taught FROM), then the
 *     human source badge. `APPLIED` and `TAUGHT` share ONE fixed slot, so a
 *     row carrying neither never moves its neighbours.
 *  3. Nothing renders from `learning` / `best_correction_signal` — a
 *     read-time "would match" that painted rows recorded BEFORE the
 *     correction existed (ruling R2/R3). The wire no longer serves it.
 *  4. Four flat source tokens (the promoted `FilterTokens` species) driving
 *     the route's `source` param; no sparse rule, present on the quiet state.
 *  5. Scroll-to-load: 50 rows, then `?before=<oldest id>` appends older.
 *  6. No caption count — the footer's `N TODAY` is the one count per face
 *     (UX-CANON A.7). Two empty states, two true tokens: `NOTHING SPOKEN`
 *     (nothing ever spoken) vs `NOTHING MATCHES` (a filter/search miss).
 *  7. The live frame obeys the wing's own claims (counsel C2/C15/C16): a
 *     frame is prepended only when it matches the ACTIVE source filter — the
 *     same equality the wire applies (`db/journal.py:155-157`) — the active
 *     search is re-applied client-side over the prepended row, a frame that
 *     races the initial read is buffered and merged (never lost, never
 *     doubled), and a row whose search hit lives only in `final_text` says so.
 *  8. The opened row keeps EVERY verb (the 175 law, ruling R11): EditInPlace
 *     over the transcript plus Replay · Copy · Delete, and the replay
 *     preview — whose two sentences become tokens (`REPLAY · PREVIEW`,
 *     `NO TEXT`), because keeping the verbs is the law and keeping the prose
 *     would re-ratify an A.3 defect (C11 note).
 */
import "./journal.css";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { asRows, rowId, useResource } from "../../pageSupport";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import type {
  DictationJournalResponse,
  DictationJournalReplayResponse,
} from "../core-types";
import {
  deSnake,
  isSameStreamDay,
  presentValue,
  streamDate,
  streamTime,
} from "../../../desk/surface/format";
import { FilterTokens } from "../../../desk/surface";
import {
  ConfirmVerb,
  EditInPlace,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceState,
  SurfaceStreamDay,
} from "../../../desk/surface/Surface";
import { StringGadget } from "../../../desk/surface/gadgets";

type Row = Record<string, unknown>;

/** The page the stream loads, and the page each scroll-to-load appends. */
export const JOURNAL_PAGE = 50;

/** The four sources the recorder writes (`plugins/dictation/journal.py`),
 *  as the tokens above the stream. ALL is the empty wire value. */
const SOURCE_FILTERS = [
  { value: "", label: "ALL" },
  { value: "dictation", label: "DICTATION" },
  { value: "browser", label: "BROWSER" },
  { value: "hotkey", label: "HOTKEY" },
];

/** A human source badge — never the wire's `dry_run` (canon E.4). */
const SOURCE_BADGES: Record<string, string> = {
  dictation: "DICTATION",
  dry_run: "DRY RUN",
  browser: "BROWSER",
  hotkey: "HOTKEY",
};

export function journalUrl(source: string, before?: number): string {
  const params = new URLSearchParams({ limit: String(JOURNAL_PAGE) });
  if (source) params.set("source", source);
  if (before) params.set("before", String(before));
  return `/api/dictation/journal?${params.toString()}`;
}

export function sourceBadge(value: unknown): string {
  const raw = String(value ?? "");
  if (!raw) return "";
  return SOURCE_BADGES[raw] ?? deSnake(raw).toUpperCase();
}

/** `LANDED IN <label>` — the target profile's LABEL, never its id. The map
 *  comes from readiness (`target.overrides`, ruling R12); an id the map has
 *  not got still reads as words, never `claude_code`. */
export function landedLabel(row: Row, labels: Record<string, string>): string {
  const target = presentValue(row.target_profile);
  if (target) return (labels[target] ?? deSnake(target)).toUpperCase();
  if (String(row.source ?? "") === "dry_run") return "DRY RUN";
  return "";
}

/** TODAY / YESTERDAY / the date — the board's day bands. */
export function journalDayLabel(date: Date | null, now?: Date): string {
  if (!date) return "UNDATED";
  const today = now ?? new Date();
  if (isSameStreamDay(date, today)) return "TODAY";
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  if (isSameStreamDay(date, yesterday)) return "YESTERDAY";
  return date
    .toLocaleDateString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
    })
    .toUpperCase();
}

/** The live frame's rule, IDENTICAL to the list's rule: the wire filters
 *  `source = ?` on exact equality (`holdspeak/db/journal.py:155-157`), so ALL
 *  (the empty value) takes every source — `dry_run` included — and any named
 *  token takes only its own. A HOTKEY frame under a BROWSER filter is a lie
 *  about what the wing is showing (counsel C2). */
export function frameMatchesSource(row: Row, source: string): boolean {
  if (!source) return true;
  return String(row.source ?? "") === source;
}

/** True when the active search matched ONLY `final_text`. The row's primary is
 *  the raw transcript, so without a mark a hit's visible text can lack the
 *  needle (counsel C15). `needle` is already trimmed and lower-cased. */
export function matchedFinalOnly(row: Row, needle: string): boolean {
  if (!needle) return false;
  if (String(row.transcript ?? "").toLowerCase().includes(needle)) return false;
  return String(row.final_text ?? "")
    .toLowerCase()
    .includes(needle);
}

function appliedIds(row: Row): number[] {
  const raw = row.corrections_applied;
  if (!Array.isArray(raw)) return [];
  return raw
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));
}

function taughtFrom(row: Row): boolean {
  return Boolean(row.taught_from ?? row.corrected);
}

function JournalRow({
  row,
  index,
  labels,
  needle,
  openId,
  onToggle,
  replays,
  onReplay,
  onEditTranscript,
  onRemove,
}: {
  row: Row;
  index: number;
  labels: Record<string, string>;
  needle: string;
  openId: string;
  onToggle: (id: string) => void;
  replays: Record<string, Row>;
  onReplay: (row: Row) => void;
  onEditTranscript: (row: Row, next: string) => void;
  onRemove: (row: Row) => void;
}) {
  const id = String(row.id ?? rowId(row, index));
  const replayResult = replays[id];
  const replayAfter =
    replayResult?.after && typeof replayResult.after === "object"
      ? (replayResult.after as Row)
      : replayResult;
  const replayText = String(replayAfter?.final_text ?? "");
  const landed = landedLabel(row, labels);
  const took = Number(row.total_ms ?? 0);
  const applied = appliedIds(row).length > 0;
  const taught = taughtFrom(row);
  const badge = sourceBadge(row.source);
  return (
    <SurfaceLedgerRow
      time={streamTime(streamDate(row.created_at ?? row.timestamp))}
      primary={String(row.transcript ?? "")}
      open={openId === id}
      onToggle={() => onToggle(id)}
      cells={
        <span className="journal-cells" data-searching={needle ? "true" : undefined}>
          <span className="surface-ledger-cell journal-landed">
            {landed ? `LANDED IN ${landed}` : ""}
          </span>
          <span className="surface-ledger-cell journal-ms">
            {took > 0 ? `${Math.round(took)} MS` : ""}
          </span>
          {/* ONE slot, held open when the row carries neither token. */}
          <span className="journal-mark">
            {applied ? (
              <span className="surface-token" data-chip data-tone="ok">
                APPLIED
              </span>
            ) : null}
            {taught ? (
              <span className="surface-token" data-chip>
                TAUGHT
              </span>
            ) : null}
            {/* The search's mark shares the SAME fixed slot, which widens for
                every row while a search runs (`[data-searching]`), so it
                never moves a neighbour and never costs the transcript a
                pixel when no search is running. It is drawn only where the
                hit lives in `final_text` alone — the row's visible text is
                the raw transcript, which then lacks the needle (C15). */}
            {matchedFinalOnly(row, needle) ? (
              <span className="surface-token">IN FINAL</span>
            ) : null}
          </span>
        </span>
      }
      trailing={
        badge ? (
          <span className="surface-token" data-chip>
            {badge}
          </span>
        ) : null
      }
    >
      <EditInPlace
        value={String(row.transcript ?? "")}
        label="transcript"
        multiline
        onCommit={(next) => void onEditTranscript(row, next)}
      />
      <div className="surface-row-verbs">
        {/* The board draws all three opened-row verbs quiet, Delete in the
            danger tone: `JournalRowOpen.dc.html`. */}
        <Button dense variant="ghost" onClick={() => void onReplay(row)}>
          Replay
        </Button>
        <Button
          dense
          variant="ghost"
          onClick={() =>
            void navigator.clipboard.writeText(String(row.transcript ?? ""))
          }
        >
          Copy
        </Button>
        <span className="journal-delete">
          <ConfirmVerb
            label="Delete"
            confirmLabel="Delete?"
            onConfirm={() => void onRemove(row)}
          />
        </span>
      </div>
      {replayResult ? (
        <div className="surface-preview" role="status">
          <span className="journal-preview-tokens">
            <span className="surface-preview-label">REPLAY · PREVIEW</span>
            {replayText ? null : (
              <span className="surface-token" data-chip>
                NO TEXT
              </span>
            )}
          </span>
          {replayText ? (
            <span className="surface-ledger-cell">{replayText}</span>
          ) : null}
          <div className="surface-actions">
            <Button
              dense
              variant="ghost"
              disabled={!replayText}
              onClick={() => void navigator.clipboard.writeText(replayText)}
            >
              Copy result
            </Button>
          </div>
        </div>
      ) : null}
    </SurfaceLedgerRow>
  );
}

export function Journal() {
  const { subscribe } = useRuntimeBus();
  const [source, setSource] = useState("");
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [exhausted, setExhausted] = useState(false);
  const [openId, setOpenId] = useState("");
  const [replays, setReplays] = useState<Record<string, Row>>({});
  const paging = useRef(false);
  const moreRef = useRef<HTMLDivElement | null>(null);
  /* The initial-read race (counsel C16). `load` ends with `setRows(items)`,
     which REPLACES the array — so a frame that lands between the GET and its
     resolution was prepended and then wiped. Every frame that arrives while a
     read is in flight is therefore also buffered here and merged, newest
     first and deduplicated by id, when that read resolves: never lost, never
     doubled. `seq` makes a superseded read (a fast filter change) drop its
     own result instead of clobbering the newer one. */
  const pending = useRef<Row[]>([]);
  const inFlight = useRef(false);
  const loadSeq = useRef(0);

  /* The label source for `LANDED IN <label>` (ruling R12): readiness carries
     `target.overrides = [{id,label}]`. A failed read costs nothing — the id
     still renders as words. */
  const readiness = useResource<Record<string, unknown>>(
    "/api/dictation/readiness",
    {},
  );
  const labels = useMemo(() => {
    const target = readiness.data?.target;
    const overrides =
      target && typeof target === "object"
        ? (target as Record<string, unknown>).overrides
        : null;
    const map: Record<string, string> = {};
    if (Array.isArray(overrides)) {
      for (const option of overrides) {
        if (!option || typeof option !== "object") continue;
        const entry = option as Record<string, unknown>;
        const id = String(entry.id ?? "");
        const label = String(entry.label ?? "");
        if (id && label) map[id] = label;
      }
    }
    return map;
  }, [readiness.data]);

  const load = useCallback(async () => {
    const seq = (loadSeq.current += 1);
    pending.current = [];
    inFlight.current = true;
    setLoading(true);
    setError("");
    try {
      const payload = await apiFetch<DictationJournalResponse>(
        journalUrl(source),
      );
      if (seq !== loadSeq.current) return;
      const items = asRows(payload, ["items"]);
      const seen = new Set(items.map((row) => String(row.id ?? "")));
      const raced = pending.current.filter(
        (row) => !seen.has(String(row.id ?? "")),
      );
      setRows(raced.length ? [...raced, ...items] : items);
      setTotal(Number(payload?.count ?? 0));
      setExhausted(items.length < JOURNAL_PAGE);
    } catch (reason) {
      if (seq === loadSeq.current) setError(readableError(reason));
    } finally {
      if (seq === loadSeq.current) {
        pending.current = [];
        inFlight.current = false;
        setLoading(false);
      }
    }
  }, [source]);

  useEffect(() => {
    void load();
  }, [load]);

  /* The push (design D3, "The bus seam"): one frame per stored row on the
     ONE runtime socket. Deduplicated by id, so a frame that races the
     initial read can never double a row — and gated on the ACTIVE source
     filter, so the wing never shows a row the filter excludes (C2). The
     ACTIVE SEARCH needs no gate here: `filtered` re-applies the needle over
     every row, the prepended one included, so a frame that misses the search
     is held out of the stream until the search clears. */
  useEffect(
    () =>
      subscribe("dictation.journal.entry", (frame) => {
        const entry = frame.data as Row | null;
        if (!entry || typeof entry !== "object") return;
        const id = String(entry.id ?? "");
        if (!id) return;
        if (!frameMatchesSource(entry, source)) return;
        if (inFlight.current)
          pending.current = [
            entry,
            ...pending.current.filter((row) => String(row.id ?? "") !== id),
          ];
        setRows((current) => {
          if (current.some((row) => String(row.id ?? "") === id))
            return current;
          return [entry, ...current];
        });
      }),
    [subscribe, source],
  );

  const loadOlder = useCallback(async () => {
    if (paging.current || exhausted || !rows.length) return;
    const oldest = Number(rows[rows.length - 1]?.id ?? 0);
    if (!oldest) return;
    paging.current = true;
    try {
      const payload = await apiFetch<DictationJournalResponse>(
        journalUrl(source, oldest),
      );
      const older = asRows(payload, ["items"]);
      setRows((current) => {
        const seen = new Set(current.map((row) => String(row.id ?? "")));
        return [
          ...current,
          ...older.filter((row) => !seen.has(String(row.id ?? ""))),
        ];
      });
      if (older.length < JOURNAL_PAGE) setExhausted(true);
    } catch {
      setExhausted(true);
    } finally {
      paging.current = false;
    }
  }, [exhausted, rows, source]);

  useEffect(() => {
    const node = moreRef.current;
    if (!node || typeof IntersectionObserver === "undefined") return;
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) void loadOlder();
    });
    observer.observe(node);
    return () => observer.disconnect();
  }, [loadOlder]);

  const needle = useMemo(() => query.trim().toLowerCase(), [query]);

  const filtered = useMemo(() => {
    if (!needle) return rows;
    return rows.filter(
      (row) =>
        String(row.transcript ?? "")
          .toLowerCase()
          .includes(needle) ||
        String(row.final_text ?? "")
          .toLowerCase()
          .includes(needle),
    );
  }, [needle, rows]);

  const days = useMemo(() => {
    const groups: { label: string; rows: Row[] }[] = [];
    for (const row of filtered) {
      const label = journalDayLabel(
        streamDate(row.created_at ?? row.timestamp),
      );
      const bucket = groups.at(-1);
      if (bucket && bucket.label === label) bucket.rows.push(row);
      else groups.push({ label, rows: [row] });
    }
    return groups;
  }, [filtered]);

  const remove = async (target: Row | "all") => {
    await apiFetch(
      target === "all"
        ? "/api/dictation/journal"
        : `/api/dictation/journal/${encodeURIComponent(String(target.id))}`,
      { method: "DELETE" },
    );
    await load();
  };
  const replay = async (row: Row) => {
    const result = await apiFetch<DictationJournalReplayResponse>(
      `/api/dictation/journal/${encodeURIComponent(String(row.id))}/replay`,
      { method: "POST" },
    );
    setReplays((current) => ({ ...current, [String(row.id)]: result }));
  };
  const editTranscript = async (row: Row, next: string) => {
    await apiFetch(
      `/api/dictation/journal/${encodeURIComponent(String(row.id))}`,
      { method: "PUT", json: { transcript: next } },
    );
    await load();
  };

  /* `Clear` wipes the journal, so it is withheld while there is nothing to
     wipe — a verb that does nothing is a lie (UX-CANON A.11). It returns as
     soon as the ledger holds a row (design D2(b).3). */
  const hasAny = total > 0 || rows.length > 0;
  /* Two empty states, two true tokens (A.3's one sanctioned exception). */
  const emptyLabel = hasAny ? "NOTHING MATCHES" : "NOTHING SPOKEN";

  return (
    <SurfaceSection className="speak-journal">
      <SurfaceLedger
        count={null}
        controls={
          <>
            <span className="journal-search-row">
              <StringGadget
                label="Search the journal"
                placeholder="search"
                value={query}
                onChange={setQuery}
              />
              {hasAny ? (
                <ConfirmVerb
                  label="Clear"
                  confirmLabel="Clear all?"
                  onConfirm={() => void remove("all")}
                />
              ) : null}
            </span>
            <FilterTokens
              className="journal-filters"
              label="Source filter"
              options={SOURCE_FILTERS}
              value={source}
              onChange={setSource}
            />
          </>
        }
      >
        <SurfaceState
          loading={loading}
          error={error}
          empty={!filtered.length}
          emptyLabel={emptyLabel}
          emptyGlyph="▤"
          onRetry={() => void load()}
        >
          {days.map((day) => (
            <SurfaceStreamDay key={day.label} label={day.label}>
              {day.rows.map((row, index) => (
                <JournalRow
                  key={rowId(row, index)}
                  row={row}
                  index={index}
                  labels={labels}
                  needle={needle}
                  openId={openId}
                  onToggle={(id) => setOpenId(openId === id ? "" : id)}
                  replays={replays}
                  onReplay={replay}
                  onEditTranscript={editTranscript}
                  onRemove={remove}
                />
              ))}
            </SurfaceStreamDay>
          ))}
          {exhausted ? null : (
            <div ref={moreRef} className="journal-more" aria-hidden="true" />
          )}
        </SurfaceState>
      </SurfaceLedger>
    </SurfaceSection>
  );
}
