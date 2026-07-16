/** The Delivery Runtime read model on the Desk (HS-94-08).
 *
 * Phase 94's hub APIs (`/api/delivery/*`) are the ONE source of truth for
 * delivery work: sources, worktrees, projects, stories, work attempts,
 * coder sessions, evidence dossiers, receipts, and paired nodes. This store
 * is a projection over that read model and holds NO authority of its own:
 *
 *   - Story association, terminal target, policy, grant, and command status
 *     all come from the server snapshot/attempt/receipt records. The store
 *     never derives them from a UI field.
 *   - `localStorage` may hold view preferences (which board is open, which
 *     source is filtered) and NOTHING that binds work.
 *   - The snapshot is single-flight and cached hub-side; the Desk polls it
 *     economically with the revision as an ETag (a 304 keeps the last frame).
 *
 * Wire is snake_case; these are the camelCase view shapes the Desk renders.
 * Statuses are typed and honest: live, stale, offline, incompatible,
 * unauthorized, and unavailable each render as themselves — never an empty
 * board pretending the rails are idle.
 */

import { create } from "zustand";
import { apiRequest } from "../lib/api";

/** The one freshness enum, shared by sources and (mapped) nodes — §2.11. */
export type SourceStatus =
  | "live"
  | "stale"
  | "offline"
  | "incompatible"
  | "unauthorized"
  | "unavailable";

export const SOURCE_STATUSES: SourceStatus[] = [
  "live",
  "stale",
  "offline",
  "incompatible",
  "unauthorized",
  "unavailable",
];

export interface DeliveryPhase {
  number: number;
  title: string;
  status: string;
  storiesDone: number;
  storiesTotal: number;
}

export interface DeliveryStory {
  storyId: string;
  title: string;
  status: string;
  phase: number;
  evidenceExists: boolean;
  /** Provenance the store copies straight from the server — never invented. */
  sourceId: string;
  project: string;
}

export interface DeliveryProject {
  sourceId: string;
  slug: string;
  prefix: string;
  currentPhase: DeliveryPhase | null;
  nextStoryId: string | null;
  phases: DeliveryPhase[];
  stories: DeliveryStory[];
  warnings: number;
}

export interface DeliveryWorktree {
  worktreeId: string;
  branch: string;
  sourceId: string;
  nodeId: string | null;
}

export interface DeliverySource {
  sourceId: string;
  nodeId: string | null;
  label: string;
  status: SourceStatus;
  detail: string;
  observedAt: string;
  capabilities: Record<string, unknown> | null;
  worktrees: DeliveryWorktree[];
  projects: DeliveryProject[];
}

export interface AttemptStoryRef {
  sourceId: string;
  project: string;
  storyId: string;
}

export type AttemptAssociation =
  | "launch"
  | "rider_claim"
  | "manual"
  | "contract"
  | "heuristic";

export type AttemptState =
  | "starting"
  | "working"
  | "waiting"
  | "idle"
  | "ended"
  | "abandoned"
  | "unknown";

export interface WorkAttempt {
  attemptId: string;
  storyRef: AttemptStoryRef;
  nodeId: string | null;
  worktreeId: string;
  sessionId: string | null;
  targetId: string | null;
  association: AttemptAssociation;
  /** The correlator's own honesty bit — a heuristic row is never `exact`. */
  exact: boolean;
  claimedBy: string | null;
  state: AttemptState;
  startedAt: string;
  updatedAt: string;
  endedAt: string | null;
}

export type NodeStatus =
  | "live"
  | "stale"
  | "offline"
  | "unknown"
  | "legacy-direct";

export interface DeliveryNode {
  name: string;
  nodeId: string | null;
  kind: "node-link" | "legacy-direct";
  status: string;
  lastSeen: string;
  capabilities: string[];
  commandsEnabled: boolean;
  compat: string;
  clockSkewSeconds: number | null;
}

// ── wire → view normalizers (pure; the tested surface) ──────────────

const fromWirePhase = (p: any): DeliveryPhase => ({
  number: Number(p?.number ?? 0),
  title: String(p?.title || `phase ${p?.number ?? "?"}`),
  status: String(p?.status || "open"),
  storiesDone: Number(p?.stories_done ?? 0),
  storiesTotal: Number(p?.stories_total ?? 0),
});

const fromWireStory = (
  s: any,
  sourceId: string,
  project: string,
): DeliveryStory => ({
  storyId: String(s?.story_id || ""),
  title: String(s?.title || ""),
  status: String(s?.status || ""),
  phase: Number(s?.phase ?? 0),
  evidenceExists: Boolean(s?.evidence_exists),
  sourceId,
  project,
});

const fromWireProject = (p: any, sourceId: string): DeliveryProject => {
  const slug = String(p?.slug || "");
  return {
    sourceId,
    slug,
    prefix: String(p?.prefix || ""),
    currentPhase: p?.current_phase ? fromWirePhase(p.current_phase) : null,
    nextStoryId: p?.next_story ? p.next_story.story_id || null : null,
    phases: (p?.phases || []).map(fromWirePhase),
    stories: (p?.stories || []).map((s: any) =>
      fromWireStory(s, sourceId, slug),
    ),
    warnings: Number(p?.warnings ?? 0),
  };
};

/** Unknown status values render `unavailable` rather than crashing (§14.3). */
function coerceSourceStatus(value: unknown): SourceStatus {
  const v = String(value || "");
  return (SOURCE_STATUSES as string[]).includes(v)
    ? (v as SourceStatus)
    : "unavailable";
}

export const fromWireSource = (s: any): DeliverySource => {
  const sourceId = String(s?.source_id || "");
  const nodeId = s?.node_id ? String(s.node_id) : null;
  return {
    sourceId,
    nodeId,
    label: String(s?.label || sourceId || "source"),
    status: coerceSourceStatus(s?.status),
    detail: String(s?.detail || ""),
    observedAt: String(s?.observed_at || ""),
    capabilities:
      s?.capabilities && typeof s.capabilities === "object"
        ? s.capabilities
        : null,
    // A non-live source keeps its last-known worktrees/projects (or honest
    // null) — the store never manufactures rows for an unreachable source.
    worktrees: (s?.worktrees || []).map((w: any): DeliveryWorktree => ({
      worktreeId: String(w?.worktree_id || ""),
      branch: String(w?.branch || ""),
      sourceId,
      nodeId,
    })),
    projects: (s?.projects || []).map((p: any) => fromWireProject(p, sourceId)),
  };
};

const ATTEMPT_ASSOCIATIONS: AttemptAssociation[] = [
  "launch",
  "rider_claim",
  "manual",
  "contract",
  "heuristic",
];

const ATTEMPT_STATES: AttemptState[] = [
  "starting",
  "working",
  "waiting",
  "idle",
  "ended",
  "abandoned",
  "unknown",
];

export const fromWireAttempt = (a: any): WorkAttempt => {
  const kindRaw = String(a?.association?.kind || "heuristic");
  const kind = (ATTEMPT_ASSOCIATIONS as string[]).includes(kindRaw)
    ? (kindRaw as AttemptAssociation)
    : "heuristic";
  const stateRaw = String(a?.state || "unknown");
  const state = (ATTEMPT_STATES as string[]).includes(stateRaw)
    ? (stateRaw as AttemptState)
    : "unknown";
  const ref = a?.story_ref || {};
  return {
    attemptId: String(a?.attempt_id || ""),
    storyRef: {
      sourceId: String(ref.source_id || ""),
      project: String(ref.project || ""),
      storyId: String(ref.story_id || ""),
    },
    nodeId: a?.node_id ? String(a.node_id) : null,
    worktreeId: String(a?.worktree_id || ""),
    sessionId: a?.session_id ? String(a.session_id) : null,
    targetId: a?.target_id ? String(a.target_id) : null,
    association: kind,
    // A heuristic association is ambiguity, always shown as inexact.
    exact: kind === "heuristic" ? false : Boolean(a?.exact),
    claimedBy: a?.association?.claimed_by
      ? String(a.association.claimed_by)
      : null,
    state,
    startedAt: String(a?.started_at || ""),
    updatedAt: String(a?.updated_at || ""),
    endedAt: a?.ended_at ? String(a.ended_at) : null,
  };
};

export const fromWireNode = (n: any): DeliveryNode => ({
  name: String(n?.name || ""),
  nodeId: n?.node_id ? String(n.node_id) : null,
  kind: n?.kind === "node-link" ? "node-link" : "legacy-direct",
  status: String(n?.status || "unknown"),
  lastSeen: String(n?.last_seen || ""),
  capabilities: Array.isArray(n?.capabilities)
    ? n.capabilities.map(String)
    : [],
  commandsEnabled: Boolean(n?.commands_enabled),
  compat: String(n?.compat || ""),
  clockSkewSeconds:
    typeof n?.clock_skew_seconds === "number" ? n.clock_skew_seconds : null,
});

// ── derived selectors over the read model (no authority) ────────────

/** Every project across every source, provenance intact. */
export function allProjects(sources: DeliverySource[]): DeliveryProject[] {
  return sources.flatMap((s) => s.projects);
}

/** Every story across every source — the list-view + search surface. */
export function allStories(sources: DeliverySource[]): DeliveryStory[] {
  return sources.flatMap((s) => s.projects.flatMap((p) => p.stories));
}

/** Resolve a story's own source status so a stale/offline source is never
 *  dressed up as a live story. */
export function storySourceStatus(
  sources: DeliverySource[],
  story: DeliveryStory,
): SourceStatus {
  return (
    sources.find((s) => s.sourceId === story.sourceId)?.status || "unavailable"
  );
}

/** The typed recovery an off-live source offers — one distinct affordance per
 *  state (§13). Never a fabricated "try again"; the truth names itself. */
export interface Recovery {
  state: SourceStatus;
  label: string;
  hint: string;
}

export function sourceRecovery(source: DeliverySource): Recovery | null {
  const seen = source.observedAt ? ` · last seen ${source.observedAt}` : "";
  switch (source.status) {
    case "live":
      return null;
    case "stale":
      return { state: "stale", label: "Refresh source", hint: `stale${seen}` };
    case "offline":
      return {
        state: "offline",
        label: "Reconnect node",
        hint: `offline${seen}`,
      };
    case "incompatible":
      return {
        state: "incompatible",
        label: "Update source",
        hint: source.detail || "schema mismatch",
      };
    case "unauthorized":
      return {
        state: "unauthorized",
        label: "Reauthorize source",
        hint: source.detail || "not authorized",
      };
    case "unavailable":
    default:
      return {
        state: "unavailable",
        label: "Retry source",
        hint: source.detail || `unavailable${seen}`,
      };
  }
}

/** Attempts pinned to a story ref (exact key: source + project + story). */
export function attemptsForStory(
  attempts: WorkAttempt[],
  story: { sourceId: string; project: string; storyId: string },
): WorkAttempt[] {
  return attempts.filter(
    (a) =>
      a.storyRef.storyId === story.storyId &&
      a.storyRef.project === story.project &&
      (!story.sourceId || a.storyRef.sourceId === story.sourceId),
  );
}

const ACTIVE_STATES = new Set<AttemptState>(["starting", "working", "waiting"]);
export function activeAttempts(attempts: WorkAttempt[]): WorkAttempt[] {
  return attempts.filter((a) => ACTIVE_STATES.has(a.state));
}

/** A delivery object as a semantic list row (HS-93-08 List view inclusion).
 *  Bounded on purpose: the current phase's Stories per project plus every
 *  active Work attempt — never a dump of every historical Story. */
export interface DeliveryListRow {
  key: string;
  kind: "Story" | "Coder session";
  label: string;
  detail: string;
  freshness: SourceStatus;
  ref:
    | { type: "story"; project: string; storyId: string; sourceId: string }
    | { type: "attempt"; attemptId: string; targetId: string | null };
}

export function deliveryListRows(
  sources: DeliverySource[],
  attempts: WorkAttempt[],
): DeliveryListRow[] {
  const rows: DeliveryListRow[] = [];
  for (const source of sources) {
    for (const project of source.projects) {
      const phase = project.currentPhase?.number ?? null;
      for (const story of project.stories) {
        if (phase !== null && story.phase !== phase) continue;
        rows.push({
          key: `story:${source.sourceId}:${project.slug}:${story.storyId}`,
          kind: "Story",
          label: story.storyId,
          detail: `${story.title || story.status}`,
          freshness: source.status,
          ref: {
            type: "story",
            project: project.slug,
            storyId: story.storyId,
            sourceId: source.sourceId,
          },
        });
      }
    }
  }
  for (const attempt of activeAttempts(attempts)) {
    rows.push({
      key: `attempt:${attempt.attemptId}`,
      kind: "Coder session",
      label: attempt.storyRef.storyId || attempt.attemptId,
      detail: `${attempt.state}${attempt.nodeId ? ` · ${attempt.nodeId}` : ""}`,
      freshness: storySourceStatus(sources, {
        storyId: attempt.storyRef.storyId,
        project: attempt.storyRef.project,
        sourceId: attempt.storyRef.sourceId,
      } as DeliveryStory),
      ref: {
        type: "attempt",
        attemptId: attempt.attemptId,
        targetId: attempt.targetId,
      },
    });
  }
  return rows;
}

// ── compatibility selectors (§10/§14) ──────────────────────────────
// The belt (MissionControlConveyor) and its direct verbs keep working by
// reading the SAME delivery read model through these projections into the
// legacy McRepo/McStory shapes. The compatibility names stay internal; the
// belt renders exactly what it always did, now over one store.
import type {
  McPhase,
  McProject,
  McRepo,
  McRepoStatus,
  McStory,
} from "./missioncontrol";

/** Map the one freshness enum onto the belt's four-value repo status. */
function beltRepoStatus(status: SourceStatus): McRepoStatus {
  switch (status) {
    case "live":
      return "live";
    case "incompatible":
      return "compatibility";
    case "unavailable":
    case "unauthorized":
      return "unavailable";
    default:
      return "unreachable";
  }
}

function beltProject(p: DeliveryProject): McProject {
  const phase = (ph: DeliveryPhase): McPhase => ({
    number: ph.number,
    title: ph.title,
    status: ph.status === "closed" ? "closed" : "open",
    storiesDone: ph.storiesDone,
    storiesTotal: ph.storiesTotal,
  });
  return {
    slug: p.slug,
    prefix: p.prefix,
    currentPhase: p.currentPhase ? phase(p.currentPhase) : null,
    nextStoryId: p.nextStoryId,
    phases: p.phases.map(phase),
    stories: p.stories.map(
      (s): McStory => ({
        storyId: s.storyId,
        title: s.title,
        status: s.status,
        phase: s.phase,
        evidenceExists: s.evidenceExists,
      }),
    ),
    warnings: p.warnings,
  };
}

/** The delivery read model projected into the belt's repo rows. */
export function deliveryBeltRepos(sources: DeliverySource[]): McRepo[] {
  return sources.map((s) => ({
    name: s.label,
    path: s.sourceId,
    status: beltRepoStatus(s.status),
    detail: s.detail,
    projects: s.status === "live" ? s.projects.map(beltProject) : [],
    receipts: "unknown" as const,
    prs: [],
  }));
}

const POLL_MS = 15_000; // the collector's single-flight cadence (§11)
export { POLL_MS };

interface DeliveryState {
  sources: DeliverySource[];
  nodes: DeliveryNode[];
  attempts: WorkAttempt[];
  revision: string;
  cursor: string;
  generatedAt: string;
  updatedAt: number | null;
  inflight: boolean;
  error: string;
  /** View preference only — which source is focused on the board. */
  focusSourceId: string | null;
  setFocusSource(sourceId: string | null): void;
  refresh(): Promise<void>;
}

const FOCUS_KEY = "hs.delivery.focus";

function loadFocus(): string | null {
  try {
    return localStorage.getItem(FOCUS_KEY);
  } catch {
    return null;
  }
}

async function readJson(url: string): Promise<any | null> {
  try {
    const res = await apiRequest(url);
    if (!res.ok) return null;
    return await res.json().catch(() => null);
  } catch {
    return null;
  }
}

export const useDelivery = create<DeliveryState>((set, get) => ({
  sources: [],
  nodes: [],
  attempts: [],
  revision: "",
  cursor: "",
  generatedAt: "",
  updatedAt: null,
  inflight: false,
  error: "",
  focusSourceId: loadFocus(),

  setFocusSource(sourceId) {
    set({ focusSourceId: sourceId });
    try {
      if (sourceId) localStorage.setItem(FOCUS_KEY, sourceId);
      else localStorage.removeItem(FOCUS_KEY);
    } catch {
      /* the focus just won't persist */
    }
  },

  async refresh() {
    if (get().inflight) return; // single-flight: a slow poll skips ticks
    set({ inflight: true });
    try {
      // The snapshot carries an ETag = its revision; If-None-Match answers
      // 304 without a body, so an unchanged board costs one stat, not a
      // fresh dw run (§11).
      let snapStatus = 0;
      let snap: any = null;
      try {
        const headers: Record<string, string> = {};
        const rev = get().revision;
        if (rev) headers["If-None-Match"] = rev;
        const res = await apiRequest("/api/delivery/snapshot", { headers });
        snapStatus = res.status;
        if (res.status === 200) snap = await res.json().catch(() => null);
      } catch {
        snap = null;
      }

      const [nodesBody, attemptsBody] = await Promise.all([
        readJson("/api/delivery/nodes"),
        readJson("/api/delivery/attempts?active_only=false"),
      ]);

      const patch: Partial<DeliveryState> = { updatedAt: Date.now() };
      if (snap && snapStatus === 200) {
        patch.sources = (snap.sources || []).map(fromWireSource);
        patch.revision = String(snap.revision || "");
        patch.cursor = String(snap.cursor || "");
        patch.generatedAt = String(snap.generated_at || "");
        patch.error = "";
      } else if (snapStatus !== 304 && get().updatedAt === null) {
        // First read failed outright — surface it, keep no invented rows.
        patch.error = "delivery snapshot unavailable";
      }
      if (nodesBody) patch.nodes = (nodesBody.nodes || []).map(fromWireNode);
      if (attemptsBody)
        patch.attempts = (attemptsBody.attempts || []).map(fromWireAttempt);
      set(patch);
    } finally {
      set({ inflight: false });
    }
  },
}));
