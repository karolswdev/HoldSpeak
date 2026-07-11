import { apiRequest } from "../lib/api";

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
  day: string; // "2026-07-01" or ""
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
  resources?: GroundingResource[];
}

export interface GroundingResource {
  ref: string;
  kind: string;
  id: string;
  title: string;
  chars: number;
}

export const emptyGrounding = (): GroundingSelection => ({ meetings: [], resources: [] });

export const groundingIsEmpty = (s: GroundingSelection): boolean =>
  s.meetings.length === 0 && (s.resources || []).length === 0;

/** The wire half: refs only. Null when nothing is selected. */
export function hubGrounding(
  s: GroundingSelection,
): {
  meeting_ids: string[];
  artifact_ids: string[];
  refs?: string[];
  expand: "summary" | "full";
} | null {
  if (groundingIsEmpty(s)) return null;
  return {
    meeting_ids: s.meetings.map((m) => m.id),
    artifact_ids: s.meetings.flatMap((m) =>
      m.artifacts.filter((a) => a.on).map((a) => a.id),
    ),
    ...((s.resources || []).length
      ? { refs: (s.resources || []).map((resource) => resource.ref) }
      : {}),
    expand: s.meetings.some((m) => m.includeTranscript) ? "full" : "summary",
  };
}

/** HS-88-02 — a picked rails object: a phase/story/evidence/roadmap
 * from the belt, priced by its real fetched file size. */
export interface RailsPick {
  repo: string;
  project: string;
  kind: string; // phase | story | evidence | roadmap
  id: string;
  title: string;
  chars: number; // real fetched length; 0 until hydrated
}

/** The rails wire refs (what the hub hydrator resolves). */
export function railsRefs(
  picks: RailsPick[],
): Array<{ repo: string; project: string; kind: string; id: string }> {
  return picks.map((p) => ({
    repo: p.repo,
    project: p.project,
    kind: p.kind,
    id: p.id,
  }));
}

/** The gauge's rails contribution — real file sizes + the provenance
 * header's own weight, in the same 4-chars/token estimate. */
export function railsTokens(picks: RailsPick[]): number {
  return tokens(picks.reduce((n, p) => n + p.chars + p.title.length + 32, 0));
}

/** One wire object for a run grounded on desk objects AND rails.
 * Null only when BOTH are empty. */
export function buildGrounding(
  sel: GroundingSelection,
  rails: RailsPick[],
): {
  meeting_ids: string[];
  artifact_ids: string[];
  refs?: string[];
  expand: "summary" | "full";
  rails?: Array<{ repo: string; project: string; kind: string; id: string }>;
} | null {
  const base = hubGrounding(sel);
  if (!base && rails.length === 0) return null;
  const wire = base || {
    meeting_ids: [],
    artifact_ids: [],
    expand: "summary" as const,
  };
  return rails.length ? { ...wire, rails: railsRefs(rails) } : wire;
}

/** Fetch the real hydrated size of picked rail refs (mirror of
 * fetchGroundingMeeting) so the gauge is honest, never guessed. The
 * hub reads the dw-named file; we keep only the size. */
export async function fetchRailsSizes(
  refs: Array<{ repo: string; project: string; kind: string; id: string }>,
): Promise<Record<string, number>> {
  if (refs.length === 0) return {};
  try {
    const res = await apiRequest("/api/missioncontrol/rails/size", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rails: refs }),
    });
    if (!res.ok) return {};
    const body = await res.json();
    const out: Record<string, number> = {};
    for (const row of body.sizes || [])
      out[`${row.kind}:${row.id}`] = row.chars || 0;
    return out;
  } catch {
    return {};
  }
}

/** ≈4 chars/token — the same deliberately simple estimator as OnDeviceBudget. */
const tokens = (chars: number): number =>
  chars <= 0 ? 0 : Math.max(1, Math.floor(chars / 4));

/** The gauge's number: the selected blocks' real fetched lengths. */
export function groundingTokens(s: GroundingSelection): number {
  let chars = 0;
  for (const m of s.meetings) {
    chars += m.title.length + 24; // the provenance header's own weight
    if (m.includeIntel) chars += m.intelChars;
    if (m.includeTranscript) chars += m.transcriptChars;
    for (const a of m.artifacts)
      if (a.on) chars += a.chars + a.title.length + 24;
  }
  for (const resource of s.resources || [])
    chars += resource.chars + resource.title.length + 24;
  return tokens(chars);
}

/** The chip's label: "2 meetings · 3 artifacts". */
export function groundingLabel(s: GroundingSelection): string {
  if (groundingIsEmpty(s)) return "";
  const m = s.meetings.length;
  const a = s.meetings.reduce(
    (n, x) => n + x.artifacts.filter((r) => r.on).length,
    0,
  );
  const parts = [`${m} meeting${m === 1 ? "" : "s"}`];
  if (a > 0) parts.push(`${a} artifact${a === 1 ? "" : "s"}`);
  const r = (s.resources || []).length;
  if (r > 0) parts.push(`${r} object${r === 1 ? "" : "s"}`);
  return parts.join(" · ");
}

/** The provenance rows a grounded keep carries (receipts by name). */
export function groundingReceiptRows(
  s: GroundingSelection,
): Array<{ id: string; kind: string; ref: string; title: string }> {
  const rows: Array<{ id: string; kind: string; ref: string; title: string }> = s.meetings.map((m) => ({
    id: m.id,
    kind: "meeting",
    ref: `meeting:${m.id}`,
    title: m.title,
  }));
  for (const m of s.meetings)
    for (const a of m.artifacts)
      if (a.on) rows.push({ id: a.id, kind: "artifact", ref: `artifact:${a.id}`, title: a.title });
  rows.push(...(s.resources || []).map((resource) => ({
    id: resource.id, kind: resource.kind, ref: resource.ref, title: resource.title,
  })));
  return rows;
}

/** Resolve and price exactly what the hub would ground; stale refs refuse. */
export async function fetchGroundingResource(
  ref: string, kind: string, id: string, title: string,
): Promise<GroundingResource | null> {
  try {
    const response = await apiRequest("/api/grounding/resolve", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refs: [ref] }),
    });
    if (!response.ok) return null;
    const body = await response.json();
    return { ref, kind, id, title: body.titles?.[0] || title, chars: Number(body.chars || 0) };
  } catch {
    return null;
  }
}

/** Pick a meeting: fetch its REAL expansion (segments, intel, bound artifacts)
 * so every toggle the picker offers is priced from what the hub actually
 * holds. Digest defaults on when intel exists (the iPad default). */
export async function fetchGroundingMeeting(
  id: string,
  title: string,
  startedAt?: string,
): Promise<GroundingMeeting> {
  const [detail, arts]: [Record<string, any>, Record<string, any>] =
    await Promise.all([
      apiRequest(`/api/meetings/${encodeURIComponent(id)}`)
        .then((r) => (r.ok ? r.json() : {}))
        .catch(() => ({})) as Promise<Record<string, any>>,
      apiRequest(`/api/meetings/${encodeURIComponent(id)}/artifacts`)
        .then((r) => (r.ok ? r.json() : {}))
        .catch(() => ({})) as Promise<Record<string, any>>,
    ]);
  const segments: Array<{ speaker?: string; text?: string }> = Array.isArray(
    detail.segments,
  )
    ? detail.segments
    : [];
  const transcriptChars = segments.reduce(
    (n, sgm) =>
      n +
      String(sgm.speaker || "Speaker").length +
      2 +
      String(sgm.text || "").length +
      1,
    0,
  );
  const intel = detail.intel || {};
  const actionTasks: string[] = Array.isArray(intel.action_items)
    ? intel.action_items.map((i: any) => String(i?.task || "")).filter(Boolean)
    : [];
  const intelChars =
    String(intel.summary || "").length +
    actionTasks.reduce((n, t) => n + t.length + 3, 0);
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
