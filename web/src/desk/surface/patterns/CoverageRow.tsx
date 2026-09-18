/** CoverageLedger / CoverageRow (HS-200-15, species S1 of the daily-workflow
 *  design) — ONE grammar for "a source that was not observed", on every face
 *  that reads sources (arrival, brief, meeting, repair).
 *
 *  A row draws, in order: the emblem (what KIND of source), the source's
 *  name at the primary step, the source's own reason in the row's ink,
 *  the state chip (the repair TOKEN — `CANT CHECK`, `STALE`, `READ FAILED`
 *  …), `OBSERVED hh:mm` (or `NEVER OBSERVED`), and the OWNING repair verb
 *  as the library Button, drawn raised.
 *
 *  Three rules the species enforces so no face has to remember them:
 *
 *  - **The reason is the source's own words, uppercased, never composed**
 *    (`JIRA REJECTED THE QUERY`); a row with no reason draws no reason
 *    token (UX-CANON A.8).
 *  - **`stale` is a warning; every other gap is a failure** — the same
 *    ink `web/src/desk/coverage.ts` orders gaps by.
 *  - **One failure class, one verb** (design D1): the species draws the
 *    verb the coverage record names (`Retry` · `Reconnect` · `Open source`)
 *    and hands the whole record to `onRepair`; the face decides where the
 *    verb leads. The species never invents a verb.
 *
 *  Promoted from `ChairHome.tsx`'s `CoverageSection` / `CoverageVerb`
 *  (HS-200-07), where the token was a raw span while `ConciergeCore` drew
 *  the same fact as a `StateChip` — converged here on `StateChip`.
 */
import { Button } from "../../../components/signal/Signal";
import { observedAtToken } from "../../attention";
import { sourceLabel, type CoverageRecord } from "../../coverage";
import { SurfaceLedger, SurfaceLedgerRow } from "../Surface";
import { StateChip } from "./StateChip";
import "./coverage-row.css";

/** Plain words only (162's no-raw-ids law): an error code such as
 *  `needsYou_read_failed` or a stack line is NOT a reason the face may
 *  draw — the token (`READ FAILED`) already names the class. */
const PLAIN_WORDS = /^[A-Za-z][A-Za-z0-9 ,'’.-]{0,59}$/;
export function plainReason(reason: string | null | undefined): string {
  const text = (reason || "").trim();
  if (!text || !PLAIN_WORDS.test(text) || text.includes("_") || /\w\.\w/.test(text)) return "";
  return text.toUpperCase();
}

/** The emblem for a coverage row: what KIND of source went unobserved. */
export function coverageEmblem(kind: string): string {
  if (kind === "watch") return "SRC";
  if (kind === "meeting") return "MTG";
  if (kind === "commitment") return "CMT";
  return "RM";
}

export interface CoverageRowProps {
  gap: CoverageRecord;
  /** The owning verb was pressed; the face maps it to its action. */
  onRepair: (gap: CoverageRecord) => void;
  /** The clock the `OBSERVED` token is read against (tests pin it). */
  now?: Date;
  "data-testid"?: string;
}

export function CoverageRow({
  gap,
  onRepair,
  now,
  "data-testid": dataTestId = "coverage-row",
}: CoverageRowProps) {
  const repair = gap.repair;
  const reason = plainReason(gap.reason);
  const tone = gap.state === "stale" ? "warning" : "failure";
  const name = sourceLabel(gap);
  return (
    <SurfaceLedgerRow
      lead={
        <span className="arrival-source-emblem surface-coverage-emblem" data-testid="arrival-source-emblem">
          {coverageEmblem(gap.kind)}
        </span>
      }
      primary={name}
      cells={
        <span className="surface-coverage-meta">
          {reason ? (
            <span
              className="surface-coverage-reason"
              data-tone={tone}
              data-testid="arrival-coverage-reason"
            >
              {reason}
            </span>
          ) : null}
          <StateChip
            state={tone}
            icon="●"
            label={repair?.token ?? gap.state.toUpperCase()}
            className="surface-coverage-token"
            data-testid="arrival-coverage-token"
          />
          <span className="surface-coverage-observed" data-testid="arrival-coverage-observed">
            {observedAtToken(gap.observed_at, now)}
          </span>
        </span>
      }
      trailing={
        repair ? (
          <Button
            variant="secondary"
            dense
            onClick={() => onRepair(gap)}
            aria-label={`${repair.verb}: ${name}`}
            data-testid="arrival-coverage-verb"
          >
            {repair.verb}
          </Button>
        ) : null
      }
      wrap
      expands={false}
      data-testid={dataTestId}
    />
  );
}

export interface CoverageLedgerProps {
  gaps: CoverageRecord[];
  onRepair: (gap: CoverageRecord) => void;
  now?: Date;
  rowTestId?: string;
}

/** The ledger of every unobserved source, worst first (the caller sorts via
 *  `readCoverage`). Renders nothing over no gaps (A.8). */
export function CoverageLedger({ gaps, onRepair, now, rowTestId }: CoverageLedgerProps) {
  if (gaps.length === 0) return null;
  return (
    <SurfaceLedger count={null} cols="room">
      {gaps.map((gap) => (
        <CoverageRow
          key={gap.source_id}
          gap={gap}
          onRepair={onRepair}
          now={now}
          data-testid={rowTestId}
        />
      ))}
    </SurfaceLedger>
  );
}
