// HS-200-07 (C4) — attention coverage: ONE reading of the aggregate's
// coverage projection for every consumer (arrival, shade, deck).
//
// The rule the faces obey: an empty result is an all-clear ONLY when
// coverage is complete. A partial result renders the coverage token and
// the repair rows instead — never the all-clear line.

export type CoverageState =
  | "available"
  | "stale"
  | "failed"
  | "forbidden"
  | "unavailable";

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
}

const COMPLETE: CoverageReading = {
  complete: true,
  expected: 0,
  available: 0,
  token: null,
  gaps: [],
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
    };
  }
  if (!coverage || coverage.length === 0) {
    // No coverage on the wire (an older payload): claim nothing new.
    return complete === false ? { ...COMPLETE, complete: false } : COMPLETE;
  }
  const expected = coverage.length;
  const available = coverage.filter((row) => row.state === "available").length;
  const isComplete = complete ?? available === expected;
  if (isComplete && available === expected) return { ...COMPLETE, expected, available };
  const gaps = coverage
    .filter((row) => row.state !== "available")
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
  };
}

/** The row's visible name — never the raw source id (162's law). */
export function sourceLabel(record: CoverageRecord): string {
  return record.label || record.kind.toUpperCase();
}

/** `LAST SEEN 09-06 08:12` — the observation time, or the honest absence. */
export function observedToken(observedAt: string | null | undefined): string {
  if (!observedAt) return "NEVER OBSERVED";
  const parsed = new Date(observedAt);
  if (Number.isNaN(parsed.getTime())) return "NEVER OBSERVED";
  const mm = String(parsed.getMonth() + 1).padStart(2, "0");
  const dd = String(parsed.getDate()).padStart(2, "0");
  const hh = String(parsed.getHours()).padStart(2, "0");
  const mi = String(parsed.getMinutes()).padStart(2, "0");
  return `LAST SEEN ${mm}-${dd} ${hh}:${mi}`;
}
