/** HS-83-01 — the context envelope's web mouth (the HSM-15-12 parity).
 *
 * The web lives ON the hub, so a grounded ask ships REFERENCES ONLY —
 * `grounding: {meeting_ids, artifact_ids, expand}` — and the hub hydrates
 * from its own store (unknown ids refuse by name; a cut transcript is marked
 * in-block). There is no client-side hydration branch, by design.
 *
 * The gauge is honest or absent: pricing uses REAL fetched lengths (the
 * ≈4-chars/token estimator the iPad's OnDeviceBudget uses), fetched when a
 * meeting is picked — never guessed from metadata. */

export interface GroundingArtifactRow {
  id: string;
  title: string;
  chars: number;
  on: boolean;
}

export interface GroundingMeeting {
  id: string;
  title: string;
  day: string;                 // "2026-07-01" or ""
  hasIntel: boolean;
  includeIntel: boolean;
  transcriptLines: number;
  includeTranscript: boolean;
  intelChars: number;
  transcriptChars: number;
  artifacts: GroundingArtifactRow[];
}

export interface GroundingSelection {
  meetings: GroundingMeeting[];
}

export const emptyGrounding = (): GroundingSelection => ({ meetings: [] });

export const groundingIsEmpty = (s: GroundingSelection): boolean => s.meetings.length === 0;

/** The wire half: refs only. Null when nothing is selected. */
export function hubGrounding(
  s: GroundingSelection,
): { meeting_ids: string[]; artifact_ids: string[]; expand: "summary" | "full" } | null {
  if (groundingIsEmpty(s)) return null;
  return {
    meeting_ids: s.meetings.map((m) => m.id),
    artifact_ids: s.meetings.flatMap((m) => m.artifacts.filter((a) => a.on).map((a) => a.id)),
    expand: s.meetings.some((m) => m.includeTranscript) ? "full" : "summary",
  };
}

/** ≈4 chars/token — the same deliberately simple estimator as OnDeviceBudget. */
const tokens = (chars: number): number => (chars <= 0 ? 0 : Math.max(1, Math.floor(chars / 4)));

/** The gauge's number: the selected blocks' real fetched lengths. */
export function groundingTokens(s: GroundingSelection): number {
  let chars = 0;
  for (const m of s.meetings) {
    chars += m.title.length + 24; // the provenance header's own weight
    if (m.includeIntel) chars += m.intelChars;
    if (m.includeTranscript) chars += m.transcriptChars;
    for (const a of m.artifacts) if (a.on) chars += a.chars + a.title.length + 24;
  }
  return tokens(chars);
}

/** The chip's label: "2 meetings · 3 artifacts". */
export function groundingLabel(s: GroundingSelection): string {
  if (groundingIsEmpty(s)) return "";
  const m = s.meetings.length;
  const a = s.meetings.reduce((n, x) => n + x.artifacts.filter((r) => r.on).length, 0);
  const parts = [`${m} meeting${m === 1 ? "" : "s"}`];
  if (a > 0) parts.push(`${a} artifact${a === 1 ? "" : "s"}`);
  return parts.join(" · ");
}

/** The provenance rows a grounded keep carries (receipts by name). */
export function groundingReceiptRows(s: GroundingSelection): Array<{ id: string; title: string }> {
  const rows: Array<{ id: string; title: string }> = s.meetings.map((m) => ({ id: m.id, title: m.title }));
  for (const m of s.meetings) for (const a of m.artifacts) if (a.on) rows.push({ id: a.id, title: a.title });
  return rows;
}

/** Pick a meeting: fetch its REAL expansion (segments, intel, bound artifacts)
 * so every toggle the picker offers is priced from what the hub actually
 * holds. Digest defaults on when intel exists (the iPad default). */
export async function fetchGroundingMeeting(id: string, title: string, startedAt?: string): Promise<GroundingMeeting> {
  const [detail, arts] = await Promise.all([
    fetch(`/api/meetings/${encodeURIComponent(id)}`).then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
    fetch(`/api/meetings/${encodeURIComponent(id)}/artifacts`).then((r) => (r.ok ? r.json() : {})).catch(() => ({})),
  ]);
  const segments: Array<{ speaker?: string; text?: string }> = Array.isArray(detail.segments) ? detail.segments : [];
  const transcriptChars = segments.reduce(
    (n, sgm) => n + String(sgm.speaker || "Speaker").length + 2 + String(sgm.text || "").length + 1, 0);
  const intel = detail.intel || {};
  const actionTasks: string[] = Array.isArray(intel.action_items)
    ? intel.action_items.map((i: any) => String(i?.task || "")).filter(Boolean)
    : [];
  const intelChars = String(intel.summary || "").length + actionTasks.reduce((n, t) => n + t.length + 3, 0);
  const rows: any[] = Array.isArray(arts.artifacts) ? arts.artifacts : [];
  return {
    id,
    title: String(detail.title || title || id),
    day: String(startedAt || detail.started_at || "").slice(0, 10),
    hasIntel: intelChars > 0,
    includeIntel: intelChars > 0,
    transcriptLines: segments.length,
    includeTranscript: false,
    intelChars,
    transcriptChars,
    artifacts: rows.map((a) => ({
      id: String(a.id),
      title: String(a.title || a.artifact_type || "Artifact"),
      chars: String(a.body_markdown || "").length,
      on: false,
    })),
  };
}
