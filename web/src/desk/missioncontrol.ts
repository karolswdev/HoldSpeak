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

export type McRepoStatus = "live" | "compatibility" | "unavailable" | "unreachable";

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
}

export interface McSession {
  key: string;
  agent: string;
  correlation: string;
  storyIds: string[];
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
});

export const fromWireMcSession = (s: any): McSession => ({
  key: s.key || "",
  agent: s.agent || "",
  correlation: s.correlation || "",
  storyIds: (s.stories || []).map((st: any) => st.story_id).filter(Boolean),
  awaitingResponse: Boolean(s.awaiting_response),
  lastAssistantText: s.last_assistant_text || "",
  stale: Boolean(s.stale),
  tmuxSession: (s.tmux && s.tmux.session) || null,
});

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

async function fetchJson(url: string): Promise<any> {
  const res = await fetch(url);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || body.detail || `HTTP ${res.status}`);
  return body;
}

export const POLL_MS = 15_000; // the design's cadence, single-flight

interface McState {
  repos: McRepo[];
  sessions: McSession[];
  sessionsStatus: string;
  sessionsDetail: string;
  events: McEvent[];
  updatedAt: number | null;
  inflight: boolean;
  open: boolean;
  toggle(): void;
  refresh(): Promise<void>;
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

  toggle() {
    set({ open: !get().open });
  },

  async refresh() {
    if (get().inflight) return; // single-flight: a slow poll skips ticks
    set({ inflight: true });
    try {
      const [state, sessions, events] = await Promise.all([
        fetchJson("/api/missioncontrol/state").catch(() => null),
        fetchJson("/api/missioncontrol/sessions").catch(() => null),
        fetchJson("/api/missioncontrol/events?tail=20").catch(() => null),
      ]);
      set({
        repos: state
          ? (state.repos || []).map(fromWireMcRepo)
          : get().repos.map((r) => ({ ...r, status: "unreachable" as const })),
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
