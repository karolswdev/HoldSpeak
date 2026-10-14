/* HS-200-13: the Memory face: recall (posture 5).
 *
 * Built to the ratified boards `P5Recall` (1440), `P5RecallPhone` (393) and
 * `P5RecallQuiet` (the miss), design D2(e):
 *
 *   head     : `3 remembered` (display, once) + `REF · FREEZE WINDOW` +
 *               `SEARCHED 09:20`; before the first search only the token
 *               `SEARCH THE DESK`; `SEARCHING` while the last content dims;
 *               `CANT SEARCH · <reason>` with `Retry` when the read failed.
 *   well     : StringGadget with its mic (`Dictate into the search`) +
 *               `Search` (`Search memory`).
 *   filters  : `All · Decisions · Commitments · Briefs · Meetings`, the
 *               same five at both widths, roved Left/Right.
 *   CURRENT  : the accented card: the decision at primary step, the three
 *               axes, the Project button, the rationale at body step, then
 *               SOURCE + `MTG 09-07 · 11:31` + `Open source`; the ONE filled
 *               primary is `Carry into brief` (it reads `CARRIED` once done
 *               and keeps focus).
 *   SUPERSEDED: the same object dimmed, `SUPERSEDED BY DEC 09-07`,
 *               discoverable, never current (story 13 AC2).
 *   DISPUTED : the same object, `DISPUTED`, never accented.
 *   OWED     : library rows with owner/date and recorded source, and ONE
 *               next action: `Name an owner`, `Set a date`, or `Done`
 *               (only when owner and date are known: AC3/AC4).  Naming and
 *               dating unfold a well under the row (no modals, A.4).
 *   the miss : `Nothing matches`, the glyph and one true line; the
 *               filters stay; `Clear` is withheld (A.11).
 *
 * Two board verbs are withheld here, on canon: `Open: the decision` (no
 * decision-record face exists to open; the Room via the Project button and
 * the transcript via `Open source` are the two real destinations, A.11) and
 * the footer's `Unfinished` / `Repairs` wings (not built on this window yet;
 * a wing that leads nowhere is a lie, A.11).
 */
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { Button } from "../../../components/signal/Signal";
import { openSourceRef } from "../../../desk/surface/citations";
import {
  FilterTokens,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  StringGadget,
  NO_WINDOW_REF_KINDS,
  useRovingRows,
} from "../../../desk/surface";
import { openRef } from "../../../desk/openObject";
import { ProjectButton } from "../../../desk/surface/patterns";
import { countLabel } from "../../../desk/surface/count";
import {
  axisTone,
  displayLine,
  missLine,
  NEXT_ACTION_VERB,
  RECALL_FILTERS,
  searchedToken,
  type DecisionCard,
  type MemoryHitRow,
  type OwedRow,
  type RecallFilter,
} from "./model";
import { useRecallController, type RecallController } from "./useRecallController";
import { BeliefCard } from "./BeliefCard";
import { useMemoryChanges } from "../../../desk/memoryChanges";
import "./recall.css";
import { openProjectRoom } from "../../../desk/shell";

/** Render the trusted FTS marker grammar without injecting result HTML. */
export function MemorySnippet({ value }: { value: string }) {
  const parts = value.split(/(<mark>.*?<\/mark>)/gi);
  return (
    <>
      {parts.map((part, index) =>
        /^<mark>.*<\/mark>$/i.test(part) ? (
          <mark className="project-memory-highlight" key={index}>
            {part.replace(/^<mark>|<\/mark>$/gi, "")}
          </mark>
        ) : (
          part
        ),
      )}
    </>
  );
}

function openProject(projectId: string) {
  openProjectRoom(projectId); // PHILO-17 U30: a Project opens its Room (one home)
}

function Chip({ label, tone, testid }: { label: string; tone?: string; testid?: string }) {
  return (
    <span className="surface-token" data-chip data-tone={tone} data-testid={testid}>
      {label}
    </span>
  );
}

/* ── a decision card (current / superseded / disputed: one object, three inks) ── */

function DecisionCardView({
  card,
  primary,
  ctrl,
}: {
  card: DecisionCard;
  /** The one filled primary on the face: the first CURRENT card's Carry. */
  primary: boolean;
  ctrl: RecallController;
}) {
  const stateWord =
    card.state === "current" ? "the current decision"
    : card.state === "superseded" ? "the superseded decision"
    : "the disputed decision";
  const carrying = ctrl.busy === `carry:${card.id}`;
  return (
    <article
      className="recall-card"
      data-state={card.state}
      data-recall-row
      data-testid="recall-card"
      aria-label={`${card.text}: ${stateWord}`}
    >
      <div className="recall-card-line">
        <span className="surface-primary recall-card-title" data-testid="recall-card-title">
          {card.text}
        </span>
        {card.state === "current" ? (
          <Button
            dense
            variant={card.carried ? "secondary" : primary ? "primary" : "secondary"}
            loading={carrying}
            aria-label={card.carried ? `Carried into brief: ${card.text}` : "Carry into brief"}
            aria-pressed={card.carried || undefined}
            data-carried={card.carried || undefined}
            data-testid="recall-carry"
            onClick={() => {
              if (!card.carried) void ctrl.carry(card.id, card.project?.id ?? null);
            }}
          >
            {card.carried ? "CARRIED" : "Carry into brief"}
          </Button>
        ) : null}
      </div>
      <div className="recall-card-chips">
        <Chip label={card.dec_token} testid="recall-dec-token" />
        {card.axes.map((axis) => (
          <Chip key={axis} label={axis} tone={axisTone(axis)} testid="recall-axis" />
        ))}
        {card.state === "superseded" && card.successor ? (
          <span className="surface-token recall-superseded-by" data-testid="recall-superseded-by">
            SUPERSEDED BY {card.successor.dec_token}
          </span>
        ) : null}
        {card.project ? (
          <ProjectButton
            name={card.project.name}
            onOpen={() => openProject(card.project!.id)}
            data-testid="recall-project"
          />
        ) : null}
      </div>
      {card.rationale ? (
        <div className="recall-rationale" data-testid="recall-rationale">
          {card.rationale}
        </div>
      ) : null}
      {card.state === "disputed" && card.dispute_reason ? (
        <div className="recall-rationale" data-testid="recall-dispute-reason">
          {card.dispute_reason}
        </div>
      ) : null}
      {card.source ? (
        <div className="recall-source">
          <span className="surface-token">SOURCE</span>
          <Chip label={card.source.token} testid="recall-source-token" />
          <Button
            dense
            variant="ghost"
            aria-label={`Open source: ${card.source.token.split(" · ")[0]}`}
            data-testid="recall-open-source"
            onClick={() => openSourceRef(card.source!.scope)}
          >
            Open source
          </Button>
        </div>
      ) : null}
    </article>
  );
}

/* ── an owed row: work, recorded identity, one next action ── */

function OwedRowView({ row, ctrl }: { row: OwedRow; ctrl: RecallController }) {
  const [well, setWell] = useState<"owner" | "date" | null>(null);
  const [value, setValue] = useState("");
  const verb = NEXT_ACTION_VERB[row.next_action];
  const busy = ctrl.busy.endsWith(`:${row.action_item_id}`);

  const act = () => {
    if (row.next_action === "mark_done") {
      void ctrl.markDone(row.action_item_id);
      return;
    }
    setValue("");
    setWell((open) => (open ? null : row.next_action === "name_owner" ? "owner" : "date"));
  };
  const save = async () => {
    const text = value.trim();
    if (!text) return;
    const ok = well === "owner"
      ? await ctrl.nameOwner(row.action_item_id, text)
      : await ctrl.setDate(row.action_item_id, text);
    if (ok) setWell(null);
  };

  return (
    <div className="recall-owed" data-recall-row data-next-action={row.next_action}>
      <SurfaceLedgerRow
        lead="Action"
        wrap
        primary={<span data-testid="recall-owed-title">{row.text}</span>}
        meta={
          <span className="recall-owed-meta">
            <span data-testid="recall-owner-token">{row.owner || "No owner"}</span>
            <span aria-hidden="true">·</span>
            <span data-tone={row.due_tone} data-testid="recall-due-token">
              {row.due_at ? row.due_token : "No date"}
            </span>
          </span>
        }
        trailing={
          <span className="recall-owed-verbs">
            {row.source ? (
              <Button dense variant="ghost" className="recall-owed-source"
                aria-label={`Open source: ${row.source.title || "Meeting"}`}
                data-testid="recall-owed-source"
                onClick={() => openSourceRef(row.source!.scope)}>
                From {row.source.title || "Meeting"}
              </Button>
            ) : null}
            <Button dense variant="ghost" disabled={busy}
              aria-label={`${verb}: ${row.text}`}
              aria-expanded={well ? true : undefined}
              data-testid="recall-owed-verb" onClick={act}>
              {busy ? "..." : verb}
            </Button>
          </span>
        }
        open={Boolean(well)}
        data-testid="recall-owed-row"
      >
        <div className="recall-owed-well" data-testid="recall-owed-well">
          <StringGadget
            label={well === "owner" ? "Owner" : "Due"}
            type={well === "owner" ? "text" : "date"}
            value={value}
            onChange={setValue}
            autoFocus
            onKeyDown={(event) => {
              if (event.key === "Enter") void save();
              if (event.key === "Escape") setWell(null);
            }}
          />
          <Button dense variant="secondary" disabled={!value.trim() || busy} onClick={() => void save()}
            aria-label={well === "owner" ? `Save owner: ${row.text}` : `Save date: ${row.text}`}
            data-testid="recall-owed-save">
            Save
          </Button>
        </div>
      </SurfaceLedgerRow>
    </div>
  );
}

/* ── memory hits (meetings, briefs, the rest) ── */

/** Kinds memory finds that have no window of their own: the row draws no
 * open (a verb that does nothing is a lie). */
const NO_WINDOW_KINDS = new Set(["brief", ...NO_WINDOW_REF_KINDS]);

function hitOpener(hit: MemoryHitRow): (() => void) | undefined {
  if (NO_WINDOW_KINDS.has(hit.kind)) return undefined;
  // The one open grammar: a settled action item (`action:<id>`) opens where
  // action items live, Follow-through.
  return () => openRef(hit.source_ref);
}

function HitRows({ rows, testid }: { rows: MemoryHitRow[]; testid: string }) {
  return (
    <SurfaceRows>
      {rows.map((hit) => (
        <SurfaceRow
          key={`${hit.kind}:${hit.source_ref}`}
          title={hit.title || hit.source_ref}
          detail={hit.snippet ? <MemorySnippet value={hit.snippet} /> : undefined}
          meta={
            <span className="project-memory-meta" data-testid={testid}>
              <span className="surface-token">{(hit.section || hit.kind).replaceAll("_", " ")}</span>
              {hit.retrieval_origin === "relationship" ? (
                <span className="surface-token">
                  Related · {String(hit.relationship || "linked source").replaceAll("_", " ")}
                </span>
              ) : null}
            </span>
          }
          onOpen={hitOpener(hit)}
        />
      ))}
    </SurfaceRows>
  );
}

/* ── the face ── */

export function RecallFace({ initialQuery = "" }: { initialQuery?: string } = {}) {
  const ctrl = useRecallController(initialQuery);
  const { result, status } = ctrl;
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const filtersRef = useRef<HTMLDivElement | null>(null);
  useRovingRows(resultsRef, { selector: "button, [role='button']", rowSelector: "[data-recall-row]" });

  // Search moves focus to the results region (design: focus return): only a
  // search he ran (searching -> ready). The quiet reads (the zero-query recent
  // read on open, a re-read after a desk change) never move focus: that focus
  // scrolled the window 180 px under him after it was drawn (the desk sweep's
  // still fence, under load).
  const lastStatus = useRef(status);
  useEffect(() => {
    const was = lastStatus.current;
    lastStatus.current = status;
    if (status === "ready" && was === "searching") resultsRef.current?.focus();
  }, [status]);

  const searched = status === "ready" || (status === "searching" && result.searched_at !== "");
  const dimmed = status === "searching" && result.searched_at !== "";
  // Astra, PR #877 P1: a write elsewhere re-reads the face; until that read
  // lands, a belief whose evidence names a changed source is not drawn.
  const held = useMemoryChanges(ctrl.reread);
  const cards = [...result.current];
  // Memory on the Desk (canvas section 2, option B): a belief is one more
  // kind of card, drawn in its state's section after the decisions.
  const drawn = result.beliefs.filter((b) => !held(b.evidence.map((e) => e.ref)));
  const beliefs = {
    current: drawn.filter((b) => b.state === "current"),
    disputed: drawn.filter((b) => b.state === "disputed"),
    superseded: drawn.filter((b) => b.state === "superseded"),
  };
  const sections = {
    current: result.current.length + beliefs.current.length,
    superseded: result.superseded.length + beliefs.superseded.length,
    disputed: result.disputed.length + beliefs.disputed.length,
    owed: result.owed.length,
    meetings: result.meetings.length,
    briefs: result.briefs.length,
    also: result.also.length,
  };
  // A held belief is not counted either: the head says what the face draws.
  const remembered = Math.max(0, result.remembered - (result.beliefs.length - drawn.length));
  const miss = searched && remembered === 0;

  const onFilterKeys = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    const tokens = Array.from(
      filtersRef.current?.querySelectorAll<HTMLButtonElement>(".surface-filter-token") ?? [],
    );
    const index = tokens.findIndex((t) => t === document.activeElement);
    if (index < 0) return;
    event.preventDefault();
    const next = event.key === "ArrowRight" ? Math.min(tokens.length - 1, index + 1) : Math.max(0, index - 1);
    tokens[next]?.focus();
  };

  return (
    <>
      <div className="room-body desk-memory-body recall-face" data-testid="desk-memory-body" data-status={status}>
        {/* The quiet recent read is out: busy until it lands (it adds the
            display line above the well). */}
        {ctrl.reading ? <span hidden aria-busy="true" data-testid="recall-reading" /> : null}
        <header className="recall-head">
          {searched ? (
            <div
              className="surface-display recall-display"
              data-accent={remembered > 0 || undefined}
              data-testid="recall-display"
            >
              {result.recent ? "Recent work" : displayLine(remembered)}
            </div>
          ) : null}
          <div className="recall-head-tokens">
            {status === "empty" ? (
              <span className="surface-token" data-testid="recall-empty-token">SEARCH THE DESK</span>
            ) : null}
            {searched ? (
              <>
                {result.query.trim() ? <>
                  <span className="surface-token" data-testid="recall-ref-token">REF · {result.query.toUpperCase()}</span>
                  <span className="surface-token recall-dot" aria-hidden="true">·</span>
                </> : null}
                <span className="surface-token" data-testid="recall-searched-token">{searchedToken(result.searched_at)}</span>
              </>
            ) : null}
            {status === "searching" ? (
              <span className="surface-token" data-testid="recall-searching-token">SEARCHING</span>
            ) : null}
            {status === "failed" ? (
              <>
                <span className="surface-token" data-tone="danger" data-testid="recall-failed-token">
                  CANT SEARCH · {ctrl.error.toUpperCase()}
                </span>
                <Button dense variant="ghost" onClick={() => void ctrl.search()} aria-label="Retry the search">
                  Retry
                </Button>
              </>
            ) : null}
          </div>
        </header>

        <div className="desk-chat-well recall-well">
          <div className="desk-chat-composer">
            <StringGadget
              label="Search the Desk"
              micLabel="Dictate into the search"
              type="search"
              value={ctrl.query}
              placeholder="Search"
              onChange={ctrl.setQuery}
              onKeyDown={(event) => {
                if (event.key === "Enter") void ctrl.search();
                if (event.key === "Escape") ctrl.clear();
              }}
            />
            <Button
              dense
              variant="secondary"
              loading={status === "searching"}
              disabled={!ctrl.query.trim()}
              aria-label="Search memory"
              data-testid="recall-search"
              onClick={() => void ctrl.search()}
            >
              Search
            </Button>
          </div>
        </div>

        <div ref={filtersRef} onKeyDown={onFilterKeys} className="recall-filters">
          <FilterTokens
            label="Filter the memory"
            options={RECALL_FILTERS.map((f) => ({ ...f, ariaLabel: `Filter: ${f.label}` }))}
            value={ctrl.filter}
            onChange={(next) => ctrl.setFilter(next as RecallFilter)}
          />
        </div>

        {searched ? (
          <div
            ref={resultsRef}
            role="region"
            aria-label={
              result.recent
                ? "Recent on this desk"
                : `Results for ${result.query}`
            }
            tabIndex={-1}
            className="recall-results"
            data-dimmed={dimmed || undefined}
            data-testid="recall-results"
          >
            {miss ? (
              <div className="recall-miss" data-testid="recall-miss">
                <span className="recall-miss-glyph" aria-hidden="true">▤</span>
                <span className="recall-miss-line">{missLine(result.projects_searched)}</span>
              </div>
            ) : null}
            {sections.current ? (
              <SurfaceSection label={countLabel("CURRENT", sections.current)} className="recall-section recall-current">
                {cards.map((card, index) => (
                  <DecisionCardView key={card.id} card={card} primary={index === 0} ctrl={ctrl} />
                ))}
                {beliefs.current.map((belief) => <BeliefCard key={belief.id} belief={belief} />)}
              </SurfaceSection>
            ) : null}
            {sections.disputed ? (
              <SurfaceSection label={countLabel("DISPUTED", sections.disputed)} className="recall-section">
                {result.disputed.map((card) => (
                  <DecisionCardView key={card.id} card={card} primary={false} ctrl={ctrl} />
                ))}
                {beliefs.disputed.map((belief) => <BeliefCard key={belief.id} belief={belief} />)}
              </SurfaceSection>
            ) : null}
            {sections.superseded ? (
              <SurfaceSection label={countLabel("SUPERSEDED", sections.superseded)} className="recall-section">
                {result.superseded.map((card) => (
                  <DecisionCardView key={card.id} card={card} primary={false} ctrl={ctrl} />
                ))}
                {beliefs.superseded.map((belief) => <BeliefCard key={belief.id} belief={belief} />)}
              </SurfaceSection>
            ) : null}
            {sections.owed ? (
              <SurfaceSection label={countLabel("OWED", sections.owed)} className="recall-section">
                <SurfaceLedger cols="recall">
                  {result.owed.map((row) => (
                    <OwedRowView key={row.ref} row={row} ctrl={ctrl} />
                  ))}
                </SurfaceLedger>
              </SurfaceSection>
            ) : null}
            {sections.meetings ? (
              <SurfaceSection label={countLabel("MEETINGS", sections.meetings)} className="recall-section">
                <HitRows rows={result.meetings} testid="recall-meeting-meta" />
              </SurfaceSection>
            ) : null}
            {sections.briefs ? (
              <SurfaceSection label={countLabel("BRIEFS", sections.briefs)} className="recall-section">
                <HitRows rows={result.briefs} testid="recall-brief-meta" />
              </SurfaceSection>
            ) : null}
            {sections.also ? (
              <SurfaceSection label={countLabel("ALSO", sections.also)} className="recall-section">
                <HitRows rows={result.also} testid="recall-also-meta" />
              </SurfaceSection>
            ) : null}
          </div>
        ) : null}
      </div>
    </>
  );
}
