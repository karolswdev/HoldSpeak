/** The desk's typed data layer (HS-73-01) — the faithful port of the original
 * factory's loaders (`desk-app.js loadAll` + `fromWire*`): same endpoints,
 * same normalized shapes, same tolerance. The wire is snake_case; the in-app
 * shapes are the camelCase view shapes the world renders. */
import { apiFetch } from "../lib/api";
import { fetchRoadmaps, type RoadmapProject } from "./roadmap";

export type Kind =
  | "meeting"
  | "artifact"
  | "note"
  | "decision"
  | "recipe"
  | "kb"
  | "directory"
  | "project"
  | "chain"
  | "workflow"
  | "coder"
  | "roadmap"
  | "story";

export interface DeskItem {
  kind: Kind;
  id: string;
  title?: string;
  name?: string;
  [key: string]: unknown;
}

export type Items = Record<Exclude<Kind, "project" | "roadmap" | "story" | "decision">, DeskItem[]> & {
  /** Additive for older test fixtures and hubs; loadAll always initializes them. */
  project?: DeskItem[];
  roadmap?: DeskItem[];
  story?: DeskItem[];
  decision?: DeskItem[];
};
export type Status = Partial<Record<Kind | "profile", "live" | "unreachable">>;

export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  keywords: string[];
  team_members: string[];
  is_archived: boolean;
  meeting_count: number;
  created_at?: string;
  updated_at: string;
  context?: Record<string, unknown>;
}

/** One runnable model (HS-83-03): what a `model` override on /api/ask accepts. */
export interface HubModel {
  name: string;
  source: "hub" | "profile";
  profile_id: string | null;
}

/** HS-92-07 — destination identity, separate from engine/model selection. */
export interface InferenceTarget {
  version: number;
  id: string;
  profile_id: string | null;
  name: string;
  kind:
    | "this_device"
    | "paired_device"
    | "private_endpoint"
    | "mesh_node"
    | "external_service"
    | "unsupported";
  boundary: string;
  owner: string;
  transport: string;
  data_scope: { sent: string[]; returned: string[] };
  engine: string;
  model: string;
  context_limit: number;
  readiness: {
    state: string;
    available: boolean;
    reason: string;
    recovery?: { action: string; alternate_target_id: string };
  };
  secret: { required: boolean; present: boolean };
}

export interface LoadResult {
  items: Items;
  profiles: Array<Record<string, unknown>>;
  projects: ProjectSummary[];
  inferenceTargets: InferenceTarget[];
  models: HubModel[];
  status: Status;
  error: string;
}

/** Canonical identity shared with the hub and native Desk. */
export function qualifiedRef(kind: string, id: string): string {
  const canonical: Record<string, string> = {
    kb: "knowledge",
    directory: "zone",
    recipe: "persona",
    chain: "sequence",
  };
  return `${canonical[kind] || kind}:${id}`;
}

export const EMPTY_ITEMS: Items = {
  meeting: [],
  artifact: [],
  note: [],
  decision: [],
  recipe: [],
  kb: [],
  directory: [],
  project: [],
  chain: [],
  workflow: [],
  coder: [],
  roadmap: [],
  story: [],
};

async function fetchJson(url: string, opts?: RequestInit): Promise<any> {
  return apiFetch<any>(url, opts);
}

/** Unwrap {meta,value} change-set records, dropping tombstones. */
export function liveValues(records: any[]): any[] {
  return (records || [])
    .filter((rec) => !(rec && rec.meta && rec.meta.deleted))
    .map((rec) => (rec && rec.value ? rec.value : rec))
    .filter(Boolean);
}

export const fromWireNote = (n: any): DeskItem => ({
  kind: "note",
  id: n.id,
  title: n.title,
  bodyMarkdown: n.body_markdown,
  tags: n.tags || [],
  createdAt: n.created_at,
  // HS-105-01: the freshness badge's named source (notes[].last_modified);
  // the adapter used to discard it — the badge-source map's finding 4.
  lastModified: n.last_modified || n.updated_at || null,
});

export const fromWireDecision = (d: any): DeskItem => ({
  kind: "decision",
  id: d.id,
  title: d.title || "Untitled decision",
  status: d.status || "proposed",
  deciders: d.deciders || [],
  decidedAt: d.decided_at || undefined,
  contextMarkdown: d.context_markdown || "",
  decisionMarkdown: d.decision_markdown || "",
  alternatives: Array.isArray(d.alternatives) ? d.alternatives : [],
  consequencesMarkdown: d.consequences_markdown || "",
  supersededBy: d.superseded_by || undefined,
  tags: d.tags || [],
  createdAt: d.created_at || "",
  lastModified: d.updated_at || null,
});

export interface DecisionInput {
  title?: string;
  status?: "proposed" | "accepted" | "superseded" | "deprecated";
  deciders?: string[];
  decided_at?: string | null;
  context_markdown?: string;
  decision_markdown?: string;
  alternatives?: Array<{ name: string; reason: string }>;
  consequences_markdown?: string;
  tags?: string[];
}

export async function fetchDecisions(): Promise<DeskItem[]> {
  const data = await fetchJson("/api/decisions");
  return (data.decisions || []).filter((d: any) => !d.deleted).map(fromWireDecision);
}

export async function createDecision(data: DecisionInput): Promise<DeskItem> {
  const response = await fetchJson("/api/decisions", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  return fromWireDecision(response.decision);
}

export async function updateDecision(id: string, data: DecisionInput): Promise<DeskItem> {
  const response = await fetchJson(`/api/decisions/${encodeURIComponent(id)}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  return fromWireDecision(response.decision);
}

export async function updateDecisionStatus(id: string, status: DecisionInput["status"]): Promise<DeskItem> {
  const response = await fetchJson(`/api/decisions/${encodeURIComponent(id)}/status`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }),
  });
  return fromWireDecision(response.decision);
}

export async function supersedeDecision(id: string): Promise<DeskItem> {
  const response = await fetchJson(`/api/decisions/${encodeURIComponent(id)}/supersede`, { method: "POST" });
  return fromWireDecision(response.decision);
}

export const fromWireRecipe = (a: any): DeskItem => ({
  kind: "recipe",
  id: a.id,
  name: a.name,
  // HS-111-09 — no 🤖 default: an empty avatar renders as the automaton
  // sprite (AgentAvatar), the family that already owns the metaphor.
  avatar: a.avatar || "",
  role: a.role || "",
  systemPrompt: a.system_prompt || "",
  userTemplate: a.user_template || "",
  tools: a.tools || [],
  kbId: a.kb_id || null,
  profileId: a.profile_id || "",
  capability: a.capability || null,
});

export const fromWireKb = (k: any): DeskItem => ({
  kind: "kb",
  id: k.id,
  name: k.name,
  memberIds: k.member_ids || [],
  createdAt: k.created_at,
  // HS-105-01: freshness source (kbs[].last_modified), previously discarded.
  lastModified: k.last_modified || null,
});

export const fromWireDirectory = (d: any): DeskItem => ({
  kind: "directory",
  id: d.id,
  name: d.name,
  parentId: d.parent_id || null,
  memberIds: d.member_ids || (d.members ? Object.keys(d.members) : []),
  createdAt: d.created_at,
});

export const fromWireProject = (project: ProjectSummary): DeskItem => ({
  kind: "project",
  id: project.id,
  name: project.name,
  description: project.description || "",
  keywords: project.keywords || [],
  teamMembers: project.team_members || [],
  meetingCount: project.meeting_count || 0,
  createdAt: project.created_at,
  updatedAt: project.updated_at,
  lastModified: project.updated_at,
});

export const fromWireRoadmap = (roadmap: RoadmapProject): DeskItem => ({
  kind: "roadmap",
  id: `roadmap:${roadmap.slug}`,
  title: roadmap.name,
  ...roadmap,
});

export const fromWireChain = (c: any): DeskItem => ({
  kind: "chain",
  id: c.id,
  name: c.name,
  steps: c.steps || [],
  capability: c.capability || null,
});

export const fromWireWorkflow = (w: any): DeskItem => {
  const graph = w.graph_json;
  const hasGraph =
    graph && typeof graph === "object" && Object.keys(graph).length > 0;
  return {
    kind: "workflow",
    id: w.id,
    name: w.name,
    prompt: w.prompt || "",
    hasGraph: Boolean(hasGraph),
    graphJson: graph,
    capability: w.capability || null,
  };
};

const fromWireMeeting = (m: any): DeskItem => ({
  kind: "meeting",
  id: m.id,
  title: m.title || "Untitled meeting",
  startedAt: m.started_at,
  endedAt: m.ended_at,
  segmentCount: m.segment_count,
  actionItemCount: m.action_item_count,
  durationSeconds: m.duration_seconds,
  tags: m.tags || [],
  intelStatus: m.intel_status,
});

const fromWireArtifact = (a: any): DeskItem => ({
  kind: "artifact",
  id: a.id,
  meetingId: a.meeting_id,
  artifactType: a.artifact_type,
  title: a.title || a.artifact_type || "Artifact",
  bodyMarkdown: a.body_markdown || "",
  status: a.status,
  confidence: a.confidence,
  sources: a.sources || [],
});

/** Resolve the session-items array from the real (nested) coders status. */
function coderSessionItems(data: any): any[] {
  const nested = data?.agent?.sessions;
  if (nested && Array.isArray(nested.items)) return nested.items;
  if (Array.isArray(nested)) return nested;
  if (Array.isArray(data?.sessions)) return data.sessions;
  return [];
}

export const fromCoderStatus = (data: any): DeskItem[] =>
  coderSessionItems(data).map((item: any, i: number) => {
    const s = item.session || item;
    const identity = item.identity || {};
    return {
      kind: "coder" as const,
      agent: s.agent === "codex" ? "codex" : "claude",
      id: s.session_id || `s${i}`,
      sessionId: s.session_id || `s${i}`,
      title: s.project || s.cwd || s.project_name || "",
      project: s.project || s.cwd || s.project_name || "",
      model: s.model || "",
      state: s.state || (s.awaiting_response ? "waiting" : "running"),
      question:
        identity.question ||
        s.question ||
        s.last_question ||
        s.last_assistant_text ||
        (s.awaiting_response ? identity.prompt || null : null),
      selected: Boolean(item.selected),
      pinned: Boolean(item.pinned ?? s.pinned),
      stale: Boolean(item.stale),
    };
  });

/** Load every kind — the same allSettled sweep the original desk ran. */
export async function loadAll(): Promise<LoadResult> {
  const items: Items = { ...EMPTY_ITEMS };
  const status: Status = {};
  let profiles: Array<Record<string, unknown>> = [];
  let projects: ProjectSummary[] = [];
  let inferenceTargets: InferenceTarget[] = [];
  let models: HubModel[] = [];
  let error = "";
  const fail = (kind: Kind | "profile" | "project", label: string, e: any) => {
    status[kind] = "unreachable";
    if (!error) error = `${label}: ${e?.message || e}`;
  };

  await Promise.allSettled([
    fetchJson("/api/meetings?limit=24")
      .then((d) => {
        items.meeting = (d.meetings || []).map(fromWireMeeting);
        status.meeting = "live";
      })
      .catch((e) => fail("meeting", "Meetings", e)),
    fetchJson("/api/sync/pull?limit=50")
      .then((d) => {
        items.artifact = liveValues(d.artifacts)
          .slice(0, 24)
          .map(fromWireArtifact);
        status.artifact = "live";
      })
      .catch((e) => fail("artifact", "Artifacts", e)),
    fetchJson("/api/notes")
      .then((d) => {
        items.note = (d.notes || [])
          .filter((n: any) => !n.deleted)
          .map(fromWireNote);
        status.note = "live";
      })
      .catch((e) => fail("note", "Notes", e)),
    fetchDecisions()
      .then((decisions) => {
        items.decision = decisions;
        status.decision = "live";
      })
      .catch((e) => fail("decision", "Decisions", e)),
    fetchJson("/api/recipes")
      .then((d) => {
        items.recipe = (d.recipes || [])
          .filter((a: any) => !a.deleted)
          .map(fromWireRecipe);
        status.recipe = "live";
      })
      .catch((e) => fail("recipe", "Agents", e)),
    fetchJson("/api/kbs")
      .then((d) => {
        items.kb = (d.kbs || []).filter((k: any) => !k.deleted).map(fromWireKb);
        status.kb = "live";
      })
      .catch((e) => fail("kb", "Knowledge", e)),
    fetchJson("/api/directories")
      .then((d) => {
        const raw = d.directories || liveValues(d);
        items.directory = (raw || [])
          .filter((x: any) => !x.deleted)
          .map(fromWireDirectory);
        status.directory = "live";
      })
      .catch((e) => fail("directory", "Zones", e)),
    fetchJson("/api/chains")
      .then((d) => {
        items.chain = (d.chains || [])
          .filter((c: any) => !c.deleted)
          .map(fromWireChain);
        status.chain = "live";
      })
      .catch((e) => fail("chain", "Sequences", e)),
    fetchJson("/api/workflows")
      .then((d) => {
        items.workflow = (d.workflows || [])
          .filter((w: any) => !w.deleted)
          .map(fromWireWorkflow);
        status.workflow = "live";
      })
      .catch((e) => fail("workflow", "Workflows", e)),
    fetchJson("/api/profiles")
      .then((d) => {
        profiles = (d.profiles || []).filter((p: any) => !p.deleted);
        status.profile = "live";
      })
      .catch(() => {
        profiles = [];
        status.profile = "unreachable";
      }),
    fetchJson("/api/projects")
      .then((d) => {
        projects = (d.projects || []).filter(
          (project: ProjectSummary) => !project.is_archived,
        );
        items.project = projects.map(fromWireProject);
        status.project = "live";
      })
      .catch((e) => {
        projects = [];
        fail("project", "Projects", e);
      }),
    fetchJson("/api/inference-targets")
      .then((d) => {
        inferenceTargets = Array.isArray(d.targets) ? d.targets : [];
      })
      .catch(() => {
        // Compatibility with an older hub: one explicitly local destination.
        inferenceTargets = [
          {
            version: 1,
            id: "this_machine",
            profile_id: null,
            name: "This device",
            kind: "this_device",
            boundary: "same_device",
            owner: "you",
            transport: "in_process",
            data_scope: {
              sent: ["instruction", "selected_context", "grounding"],
              returned: ["generated_output"],
            },
            engine: "local",
            model: "",
            context_limit: 16_384,
            readiness: { state: "ready", available: true, reason: "" },
            secret: { required: false, present: false },
          },
        ];
      }),
    // HS-83-03 — the runnable allow-list (what a `model` override accepts).
    fetchJson("/api/models")
      .then((d) => {
        models = Array.isArray(d.models) ? d.models : [];
      })
      .catch(() => {
        models = []; /* older hub = honest empty door */
      }),
    fetchRoadmaps()
      .then((roadmaps) => {
        items.roadmap = roadmaps.map(fromWireRoadmap);
        status.roadmap = "live";
      })
      .catch((e) => fail("roadmap", "Roadmaps", e)),
    fetchJson("/api/coders/status")
      .then((d) => {
        items.coder = fromCoderStatus(d);
        status.coder = "live";
      })
      .catch(() => {
        items.coder = []; /* companion off = honest empty lane */
      }),
  ]);

  return { items, profiles, projects, inferenceTargets, models, status, error };
}
