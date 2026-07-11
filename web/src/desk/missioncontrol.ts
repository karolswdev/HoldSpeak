/** Mission control on the Desk (HS-82-03/04) — the typed data layer.
 *
 * The Desk consumes exactly the three documents the Delivery Workbench
 * contract allows a client: the state feed, the correlation document,
 * and the event log, all relayed byte-honest by the bridge
 * (/api/missioncontrol/*). Wire is snake_case; these are the camelCase
 * view shapes the belt renders. Statuses are typed and honest:
 * "compatibility" and "unreachable" render as themselves, never as an
 * empty belt pretending the rails are idle.
 * Design: docs/internal/MISSION_CONTROL_DESK.md §2–§3.
 */

import { create } from "zustand";
import { apiFetch } from "../lib/api";

export type McRepoStatus =
  "live" | "compatibility" | "unavailable" | "unreachable";

export interface McPhase {
  number: number;
  title: string;
  status: "open" | "closed";
  storiesDone: number;
  storiesTotal: number;
}

export interface McStory {
  storyId: string;
  title: string;
  status: string;
  phase: number;
  evidenceExists: boolean;
}

export interface McProject {
  slug: string;
  prefix: string;
  currentPhase: McPhase | null;
  nextStoryId: string | null;
  phases: McPhase[];
  stories: McStory[];
  warnings: number;
}

export interface McRepo {
  name: string;
  path: string;
  status: McRepoStatus;
  detail: string;
  projects: McProject[];
  /** GitHub receipts (HS-86-04): open PRs with a derived CI light. */
  receipts: "live" | "unavailable" | "unknown";
  prs: McPr[];
}

export interface McPr {
  number: number;
  title: string;
  url: string;
  branch: string;
  ci: CiLight;
}

export type CiLight = "pass" | "fail" | "pending" | "none";

export interface McStoryRef {
  storyId: string;
  project: string;
}

export interface McSession {
  key: string;
  agent: string;
  correlation: string;
  storyIds: string[];
  storyRefs: McStoryRef[];
  awaitingResponse: boolean;
  lastAssistantText: string;
  stale: boolean;
  tmuxSession: string | null;
}

export interface McEvent {
  ts: string;
  event: string;
  story: string | null;
  detail: Record<string, unknown>;
  repo: string;
}

const fromWirePhase = (p: any): McPhase => ({
  number: p.number,
  title: p.title || `phase ${p.number}`,
  status: p.status === "closed" ? "closed" : "open",
  storiesDone: p.stories_done ?? 0,
  storiesTotal: p.stories_total ?? 0,
});

const fromWireProject = (p: any): McProject => ({
  slug: p.slug || "",
  prefix: p.prefix || "",
  currentPhase: p.current_phase ? fromWirePhase(p.current_phase) : null,
  nextStoryId: p.next_story ? p.next_story.story_id || null : null,
  phases: (p.phases || []).map(fromWirePhase),
  stories: (p.stories || []).map((s: any): McStory => ({
    storyId: s.story_id || "",
    title: s.title || "",
    status: s.status || "",
    phase: s.phase ?? 0,
    evidenceExists: Boolean(s.evidence_exists),
  })),
  warnings: p.warnings ?? 0,
});

export const fromWireMcRepo = (entry: any): McRepo => ({
  name: entry.name || "",
  path: entry.path || "",
  status: (entry.status as McRepoStatus) || "unreachable",
  detail: entry.detail || "",
  projects:
    entry.status === "live" && entry.feed
      ? (entry.feed.projects || []).map(fromWireProject)
      : [],
  receipts: "unknown",
  prs: [],
});

/** Worst-conclusion CI light over a PR's check rollup — one honest
 * dot: any failure-shaped conclusion wins, then pending, then pass;
 * no checks at all is "none", never a fake green. */
export const ciLight = (rollup: any[]): CiLight => {
  if (!rollup || rollup.length === 0) return "none";
  let pending = false;
  for (const check of rollup) {
    const conclusion = String(check?.conclusion || "").toUpperCase();
    if (
      [
        "FAILURE",
        "TIMED_OUT",
        "CANCELLED",
        "ACTION_REQUIRED",
        "STARTUP_FAILURE",
      ].includes(conclusion)
    )
      return "fail";
    if (!conclusion || conclusion === "PENDING") pending = true;
  }
  return pending ? "pending" : "pass";
};

const fromWirePr = (p: any): McPr => ({
  number: p.number ?? 0,
  title: p.title || "",
  url: p.url || "",
  branch: p.headRefName || "",
  ci: ciLight(p.statusCheckRollup || []),
});

/** Fold the receipts document into the repos by name (HS-86-04). */
export function mergeReceipts(repos: McRepo[], receipts: any): McRepo[] {
  const byName: Record<string, any> = {};
  for (const entry of receipts?.repos || []) byName[entry.name] = entry;
  return repos.map((repo) => {
    const entry = byName[repo.name];
    if (!entry) return repo;
    if (entry.status !== "live")
      return { ...repo, receipts: "unavailable" as const, prs: [] };
    return {
      ...repo,
      receipts: "live" as const,
      prs: (entry.prs || []).map(fromWirePr),
    };
  });
}

/** The gate station light: the newest gate event for a repo speaks
 * (events arrive newest-first). A refusal carries its rule verbatim. */
export function gateLightFor(
  events: McEvent[],
  repo: string,
): { state: "pass" | "refusal" | "none"; rule: string } {
  for (const e of events) {
    if (e.repo !== repo) continue;
    if (e.event === "gate_pass") return { state: "pass", rule: "" };
    if (e.event === "gate_refusal")
      return { state: "refusal", rule: String(e.detail?.rule ?? "") };
  }
  return { state: "none", rule: "" };
}

/** A `scope:"belt"` frame on the one bus (HS-86-03) — the conveyor
 * refreshes on sight instead of waiting for its tick. */
export function isBeltFrame(frame: any): boolean {
  return Boolean(
    frame &&
    frame.type === "intel_status" &&
    frame.data &&
    frame.data.scope === "belt",
  );
}

export const fromWireMcSession = (s: any): McSession => {
  const refs: McStoryRef[] = (s.stories || [])
    .map((st: any) => ({
      storyId: st.story_id || "",
      project: st.project || "",
    }))
    .filter((r: McStoryRef) => r.storyId);
  return {
    key: s.key || "",
    agent: s.agent || "",
    correlation: s.correlation || "",
    storyIds: refs.map((r) => r.storyId),
    storyRefs: refs,
    awaitingResponse: Boolean(s.awaiting_response),
    lastAssistantText: s.last_assistant_text || "",
    stale: Boolean(s.stale),
    tmuxSession: (s.tmux && s.tmux.session) || null,
  };
};

/** Resolve a story id to its {repo, project, story} flip target
 * (HS-87-05): find the repo whose live projects include the given
 * project slug. Null when nothing on the belt claims it. */
export function flipTargetForStory(
  repos: McRepo[],
  storyId: string,
  project: string,
): { repo: string; project: string; story: string } | null {
  if (!storyId || !project) return null;
  for (const repo of repos) {
    if (repo.status !== "live") continue;
    if (repo.projects.some((p) => p.slug === project)) {
      return { repo: repo.name, project, story: storyId };
    }
  }
  return null;
}

export const fromWireMcEvents = (repoEntry: any): McEvent[] =>
  repoEntry.status === "live"
    ? (repoEntry.events || []).map((e: any): McEvent => ({
        ts: e.ts || "",
        event: e.event || "",
        story: e.story || null,
        detail: e.detail || {},
        repo: repoEntry.name || "",
      }))
    : [];

/** Sessions keyed by the story they are on — the belt pins these. */
export function sessionsByStory(
  sessions: McSession[],
): Record<string, McSession[]> {
  const map: Record<string, McSession[]> = {};
  for (const s of sessions) {
    if (s.correlation !== "on_story") continue;
    for (const id of s.storyIds) (map[id] ||= []).push(s);
  }
  return map;
}

/** Sessions that cannot pin to a story, grouped in the correlation's
 * own honest buckets (ambiguous lists candidates; nothing guessed). */
export function offBeltSessions(sessions: McSession[]): McSession[] {
  return sessions.filter((s) => s.correlation !== "on_story");
}

/** One ticker line per event; gate refusals carry their rule id
 * verbatim — the rails' words, not ours. */
export function formatEvent(e: McEvent): string {
  const time = e.ts.includes("T") ? e.ts.split("T")[1].replace("Z", "") : e.ts;
  const detail = Object.entries(e.detail || {})
    .filter(([, v]) => v !== null && v !== undefined)
    .map(([k, v]) => `${k}=${v}`)
    .join(" ");
  return [time, e.event, e.story || "", detail].filter(Boolean).join("  ");
}

async function fetchJson(url: string, opts?: RequestInit): Promise<any> {
  return apiFetch<any>(url, opts);
}

export const POLL_MS = 15_000; // the design's cadence, single-flight

export interface McProposal {
  id: string;
  status: string;
  preview: string;
  error: string | null;
}

export const fromWireProposal = (p: any): McProposal => ({
  id: p.id || "",
  status: p.status || "",
  preview: p.preview || "",
  error: p.error || null,
});

export interface McEvidence {
  storyId: string;
  path: string;
  text: string;
}

interface McState {
  repos: McRepo[];
  sessions: McSession[];
  sessionsStatus: string;
  sessionsDetail: string;
  events: McEvent[];
  updatedAt: number | null;
  inflight: boolean;
  open: boolean;
  proposal: McProposal | null;
  proposalError: string;
  evidence: McEvidence | null;
  evidenceDetail: string;
  toggle(): void;
  refresh(): Promise<void>;
  proposeFlip(
    repo: string,
    project: string,
    story: string,
    status: string,
  ): Promise<void>;
  decide(decision: "approved" | "rejected"): Promise<void>;
  dismissProposal(): void;
  openEvidence(repo: string, project: string, story: string): Promise<void>;
  closeEvidence(): void;
}

export const useMissionControl = create<McState>((set, get) => ({
  repos: [],
  sessions: [],
  sessionsStatus: "unreachable",
  sessionsDetail: "",
  events: [],
  updatedAt: null,
  inflight: false,
  open: true,
  proposal: null,
  proposalError: "",
  evidence: null,
  evidenceDetail: "",

  toggle() {
    set({ open: !get().open });
  },

  async proposeFlip(repo, project, story, status) {
    set({ proposalError: "" });
    try {
      const body = await fetchJson("/api/missioncontrol/story/propose", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo, verb: "status", project, story, status }),
      });
      set({ proposal: fromWireProposal(body.proposal) });
    } catch (e: any) {
      set({ proposalError: e.message || "propose failed", proposal: null });
    }
  },

  async decide(decision) {
    const proposal = get().proposal;
    if (!proposal) return;
    try {
      const body = await fetchJson(
        `/api/missioncontrol/proposals/${proposal.id}/decision`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ decision, actor: "desk-owner" }),
        },
      );
      set({ proposal: fromWireProposal(body.proposal) });
      if (body.proposal && body.proposal.status === "executed") {
        await get().refresh(); // the belt moves
      }
    } catch (e: any) {
      set({ proposalError: e.message || "decision failed" });
    }
  },

  dismissProposal() {
    set({ proposal: null, proposalError: "" });
  },

  async openEvidence(repo, project, story) {
    set({ evidence: null, evidenceDetail: "" });
    try {
      const body = await fetchJson(
        `/api/missioncontrol/evidence?repo=${encodeURIComponent(repo)}` +
          `&project=${encodeURIComponent(project)}&story=${encodeURIComponent(story)}`,
      );
      if (body.status === "live") {
        set({ evidence: { storyId: story, path: body.path, text: body.text } });
      } else {
        set({ evidenceDetail: `${body.status}: ${body.detail || story}` });
      }
    } catch (e: any) {
      set({ evidenceDetail: e.message || "evidence read failed" });
    }
  },

  closeEvidence() {
    set({ evidence: null, evidenceDetail: "" });
  },

  async refresh() {
    if (get().inflight) return; // single-flight: a slow poll skips ticks
    set({ inflight: true });
    try {
      const [state, sessions, events, receipts] = await Promise.all([
        fetchJson("/api/missioncontrol/state").catch(() => null),
        fetchJson("/api/missioncontrol/sessions").catch(() => null),
        fetchJson("/api/missioncontrol/events?tail=20").catch(() => null),
        fetchJson("/api/missioncontrol/receipts").catch(() => null),
      ]);
      set({
        repos: mergeReceipts(
          state
            ? (state.repos || []).map(fromWireMcRepo)
            : get().repos.map((r) => ({
                ...r,
                status: "unreachable" as const,
              })),
          receipts,
        ),
        sessions:
          sessions && sessions.status === "live"
            ? (sessions.sessions.sessions || []).map(fromWireMcSession)
            : [],
        sessionsStatus: sessions ? sessions.status : "unreachable",
        sessionsDetail: sessions ? sessions.detail || "" : "",
        events: events
          ? (events.repos || []).flatMap(fromWireMcEvents).reverse()
          : [],
        updatedAt: Date.now(),
      });
    } finally {
      set({ inflight: false });
    }
  },
}));
