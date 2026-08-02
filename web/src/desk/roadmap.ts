import { apiFetch } from "../lib/api";

export interface RoadmapProject {
  slug: string;
  name: string;
  phaseCount: number;
  currentPhase: number;
  currentPhaseTitle: string;
  storiesDone: number;
  storiesTotal: number;
  health: "green" | "warn" | "red";
  issues: string[];
  nextStoryId: string | null;
}

export interface RoadmapStory {
  id: string;
  title: string;
  status: "backlog" | "ready" | "in-progress" | "blocked" | "done";
  hasEvidence: boolean;
  phase: number;
}

export interface RoadmapPhase {
  number: number;
  title: string;
  storiesDone: number;
  storiesTotal: number;
  status: "active" | "closed" | "not-started";
  stories: RoadmapStory[];
}

export interface RoadmapIssue {
  severity: "error" | "warn";
  path: string;
  issue: string;
}

export interface RoadmapDetail extends RoadmapProject {
  phases: RoadmapPhase[];
  healthIssues: RoadmapIssue[];
}

export async function fetchRoadmaps(): Promise<RoadmapProject[]> {
  const data = await apiFetch<{ roadmaps?: RoadmapProject[] }>("/api/roadmaps");
  return Array.isArray(data.roadmaps) ? data.roadmaps : [];
}

export async function fetchRoadmap(slug: string): Promise<RoadmapDetail> {
  return apiFetch<RoadmapDetail>(`/api/roadmaps/${encodeURIComponent(slug)}`);
}

export async function fetchRoadmapHealth(slug: string): Promise<{
  health: RoadmapProject["health"];
  issues: RoadmapIssue[];
}> {
  return apiFetch(`/api/roadmaps/${encodeURIComponent(slug)}/health`);
}

export async function fetchRoadmapNext(slug: string): Promise<unknown | null> {
  const data = await apiFetch<{ next: unknown | null }>(
    `/api/roadmaps/${encodeURIComponent(slug)}/next`,
  );
  return data.next ?? null;
}
