/** The desk's typed data layer (HS-73-01) — the faithful port of the original
 * factory's loaders (`desk-app.js loadAll` + `fromWire*`): same endpoints,
 * same normalized shapes, same tolerance. The wire is snake_case; the in-app
 * shapes are the camelCase view shapes the world renders. */
import { apiFetch } from "../lib/api";

export type Kind =
  | "meeting"
  | "artifact"
  | "note"
  | "recipe"
  | "kb"
  | "directory"
  | "chain"
  | "workflow"
  | "coder";

export interface DeskItem {
  kind: Kind;
  id: string;
  title?: string;
  name?: string;
  [key: string]: unknown;
}

export type Items = Record<Kind, DeskItem[]>;
export type Status = Partial<Record<Kind | "profile", "live" | "unreachable">>;

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
  recipe: [],
  kb: [],
  directory: [],
  chain: [],
  workflow: [],
  coder: [],
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
});

export const fromWireRecipe = (a: any): DeskItem => ({
  kind: "recipe",
  id: a.id,
  name: a.name,
  avatar: a.avatar || "🤖",
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
});

export const fromWireDirectory = (d: any): DeskItem => ({
  kind: "directory",
  id: d.id,
  name: d.name,
  parentId: d.parent_id || null,
  memberIds: d.member_ids || (d.members ? Object.keys(d.members) : []),
  createdAt: d.created_at,
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
  let inferenceTargets: InferenceTarget[] = [];
  let models: HubModel[] = [];
  let error = "";
  const fail = (kind: Kind | "profile", label: string, e: any) => {
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
    fetchJson("/api/recipes")
      .then((d) => {
        items.recipe = (d.recipes || [])
          .filter((a: any) => !a.deleted)
          .map(fromWireRecipe);
        status.recipe = "live";
      })
      .catch((e) => fail("recipe", "Personas", e)),
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
    fetchJson("/api/inference-targets")
      .then((d) => {
        inferenceTargets = Array.isArray(d.targets) ? d.targets : [];
      })
      .catch(() => {
        // Compatibility with an older hub: one explicitly local destination.
        inferenceTargets = [{
          version: 1,
          id: "this_machine",
          profile_id: null,
          name: "This device",
          kind: "this_device",
          boundary: "same_device",
          owner: "you",
          transport: "in_process",
          data_scope: { sent: ["instruction", "selected_context", "grounding"], returned: ["generated_output"] },
          engine: "local",
          model: "",
          context_limit: 16_384,
          readiness: { state: "ready", available: true, reason: "" },
          secret: { required: false, present: false },
        }];
      }),
    // HS-83-03 — the runnable allow-list (what a `model` override accepts).
    fetchJson("/api/models")
      .then((d) => {
        models = Array.isArray(d.models) ? d.models : [];
      })
      .catch(() => {
        models = []; /* older hub = honest empty door */
      }),
    fetchJson("/api/coders/status")
      .then((d) => {
        items.coder = fromCoderStatus(d);
        status.coder = "live";
      })
      .catch(() => {
        items.coder = []; /* companion off = honest empty lane */
      }),
  ]);

  return { items, profiles, inferenceTargets, models, status, error };
}
