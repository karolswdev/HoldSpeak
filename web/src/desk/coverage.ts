// HS-200-07 (C4) — attention coverage: ONE reading of the aggregate's
// coverage projection for every consumer (arrival, shade, deck).
//
// The rule the faces obey: an empty result is an all-clear ONLY when
// coverage is complete. A partial result renders the coverage token and
// the repair rows instead — never the all-clear line.

import { wireDate } from "./surface/format";

export type CoverageState =
  | "available"
  | "stale"
  | "failed"
  | "forbidden"
  | "unavailable"
  /** PHILO-15 B60: not checked since HoldSpeak's own quiet hours held the
   *  sweep. Listed with its quiet end; never counted; not a gap. */
  | "quiet";

export interface CoverageRepair {
  token: string;
  verb: string;
  href: string;
}

export interface CoverageRecord {
  source_id: string;
  kind: string;
  state: CoverageState;
  observed_at: string | null;
  label?: string;
  project_id?: string;
  reason?: string | null;
  repair?: CoverageRepair | null;
  /** PHILO-15 B61: the Watches Retry re-checks for this source. */
  watch_ids?: string[];
  /** The host a re-check reaches (github.com, a Jira site); none = local. */
  host?: string | null;
}

export interface CoverageReading {
  /** True only when every expected source was observed. */
  complete: boolean;
  expected: number;
  available: number;
  /** `COVERAGE · 3 OF 4` — null when coverage is complete. */
  token: string | null;
  /** The sources that were not observed, worst first. */
  gaps: CoverageRecord[];
  /** PHILO-15 B60: sources held by quiet hours (listed, not counted, not gaps). */
  quiet: CoverageRecord[];
}

const COMPLETE: CoverageReading = {
  complete: true,
  expected: 0,
  available: 0,
  token: null,
  gaps: [],
  quiet: [],
};

/** The synthetic gap for a needs-you read the browser could not make. */
export const DESK_UNREAD: CoverageRecord = {
  source_id: "desk",
  kind: "project",
  state: "failed",
  observed_at: null,
  label: "Desk",
  reason: "could not read",
  repair: { token: "READ FAILED", verb: "Retry", href: "/" },
};

const GAP_ORDER: Record<string, number> = {
  failed: 0,
  forbidden: 1,
  unavailable: 2,
  stale: 3,
};

/**
 * Read a payload's coverage.
 *
 * `failed` marks a wire read that never landed: the reader observed
 * nothing, so the answer is incomplete no matter what the last payload
 * said.
 */
export function readCoverage(
  coverage: CoverageRecord[] | null | undefined,
  complete: boolean | undefined,
  failed = false,
): CoverageReading {
  if (failed) {
    return {
      complete: false,
      expected: 1,
      available: 0,
      token: "COVERAGE · 0 OF 1",
      gaps: [DESK_UNREAD],
      quiet: [],
    };
  }
  if (!coverage || coverage.length === 0) {
    // No coverage on the wire (an older payload): claim nothing new.
    return complete === false ? { ...COMPLETE, complete: false } : COMPLETE;
  }
  // PHILO-15 B60: a quiet source counts as observed (HoldSpeak chose to wait).
  const quiet = coverage.filter((row) => row.state === "quiet");
  const expected = coverage.length;
  const available = coverage.filter((row) => row.state === "available" || row.state === "quiet").length;
  const isComplete = complete ?? available === expected;
  if (isComplete && available === expected) return { ...COMPLETE, expected, available, quiet };
  const gaps = coverage
    .filter((row) => row.state !== "available" && row.state !== "quiet")
    .sort(
      (a, b) =>
        (GAP_ORDER[a.state] ?? 9) - (GAP_ORDER[b.state] ?? 9) ||
        (a.label ?? a.source_id).localeCompare(b.label ?? b.source_id),
    );
  return {
    complete: false,
    expected,
    available,
    token: `COVERAGE · ${available} OF ${expected}`,
    gaps,
    quiet,
  };
}

/** The row's visible name — never the raw source id (162's law). */
export function sourceLabel(record: CoverageRecord): string {
  return record.label || record.kind.toUpperCase();
}

/** `LAST SEEN 09-06 08:12` — the observation time, or the honest absence. */
export function observedToken(observedAt: string | null | undefined): string {
  if (!observedAt) return "NEVER OBSERVED";
  const parsed = wireDate(observedAt);
  if (!parsed) return "NEVER OBSERVED";
  const mm = String(parsed.getMonth() + 1).padStart(2, "0");
  const dd = String(parsed.getDate()).padStart(2, "0");
  const hh = String(parsed.getHours()).padStart(2, "0");
  const mi = String(parsed.getMinutes()).padStart(2, "0");
  return `LAST SEEN ${mm}-${dd} ${hh}:${mi}`;
}
