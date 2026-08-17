/** The desk's typed data layer (HS-73-01) — the faithful port of the original
 * factory's loaders (`desk-app.js loadAll` + `fromWire*`): same endpoints,
 * same normalized shapes, same tolerance. The wire is snake_case; the in-app
 * shapes are the camelCase view shapes the world renders.
 *
 * HS-117-01: every entity that crosses the wire has a concrete TypeScript
 * interface. Mappers take `unknown`, return concrete types, use wireGuard. */
import { apiFetch } from "../lib/api";
import type {
  Artifact,
  Chain,
  Coder,
  Decision,
  Directory,
  Intelligence,
  KB,
  Meeting,
  Note,
  Persona,
  PeopleDesk,
  Primitive,
  PrimitiveKind,
  PrimitiveMap,
  Project,
  Repository,
  Roadmap,
  Story,
  Workbench,
  Workflow,
} from "../lib/primitives";
import { fetchRoadmaps, type RoadmapProject } from "./roadmap";
import { fetchRepositories } from "./repository";
import {
  wireString,
  wireNumber,
  wireBool,
  wireArray,
  wireStringOrNull,
  wireRaw,
  warnMissingId,
} from "./wireGuard";


/** Typed item buckets — one array per primitive kind (HS-117-01). */
export type TypedItems = { [K in PrimitiveKind]: PrimitiveMap[K][] };

/** @deprecated Compatibility alias during migration. */
export type Items = TypedItems;

export type Status = Partial<Record<PrimitiveKind | "profile", "live" | "unreachable">>;

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

/** One runnable model (HS-83-03): what a `model` override on /api/ask accepts.
 * HS-130-06: one row PER DESTINATION (never deduped by name); `id` is the
 * selector, so two destinations serving the same model name are both present
 * and addressable — the picker must key on `id`, not `name`. */
export interface HubModel {
  id: string;
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
  /** HS-134-02: surfaced so /api/profiles reads can retire. */
  endpoint?: string;
  node?: string;
}

export interface LoadResult {
  items: TypedItems;
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

export const EMPTY_ITEMS = {
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
  repository: [],
  workbench: [],
  intelligence: [
    { kind: "intelligence", id: "desk", name: "Intelligence" } satisfies Intelligence,
  ],
  people: [
    { kind: "people", id: "people", name: "People" } satisfies PeopleDesk,
  ],
  game: [],
  layout: [],
} satisfies TypedItems;

/** Unwrap {meta,value} change-set records, dropping tombstones. */
export function liveValues(records: unknown[]): unknown[] {
  return (records || [])
    .filter((rec) => {
      if (!rec || typeof rec !== "object") return true;
      const r = rec as Record<string, unknown>;
      const meta = r.meta as Record<string, unknown> | undefined;
      return !(meta && meta.deleted);
    })
    .map((rec) => {
      if (rec && typeof rec === "object" && "value" in (rec as Record<string, unknown>))
        return (rec as Record<string, unknown>).value;
      return rec;
    })
    .filter(Boolean);
}

export const fromWireNote = (n: unknown): Note | null => {
  const id = wireString(n, "id");
  if (!id) { warnMissingId("note", n, "id"); return null; }
  return {
    kind: "note",
    id,
    title: wireString(n, "title"),
    bodyMarkdown: wireString(n, "body_markdown"),
    tags: wireArray(n, "tags").filter((t): t is string => typeof t === "string"),
    createdAt: wireString(n, "created_at"),
    // HS-105-01: the freshness badge's named source (notes[].last_modified);
    // the adapter used to discard it — the badge-source map's finding 4.
    lastModified: wireStringOrNull(n, "last_modified") || wireStringOrNull(n, "updated_at"),
  };
};

export const fromWireDecision = (d: unknown): Decision | null => {
  const id = wireString(d, "id");
  if (!id) { warnMissingId("decision", d, "id"); return null; }
  return {
    kind: "decision",
    id,
    title: wireString(d, "title", "Untitled decision"),
    status: (wireString(d, "status", "proposed") as Decision["status"]) || "proposed",
    deciders: wireArray(d, "deciders").filter((x): x is string => typeof x === "string"),
    decidedAt: wireStringOrNull(d, "decided_at") ?? undefined,
    contextMarkdown: wireString(d, "context_markdown"),
    decisionMarkdown: wireString(d, "decision_markdown"),
    alternatives: wireArray(d, "alternatives") as Array<{ name: string; reason: string }>,
    consequencesMarkdown: wireString(d, "consequences_markdown"),
    supersededBy: wireStringOrNull(d, "superseded_by") ?? undefined,
    tags: wireArray(d, "tags").filter((t): t is string => typeof t === "string"),
    createdAt: wireString(d, "created_at"),
  };
};

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

export async function fetchDecisions(): Promise<Decision[]> {
  const data = await apiFetch<Record<string, unknown>>("/api/decisions");
  return wireArray(data, "decisions")
    .filter((d) => !wireBool(d, "deleted"))
    .map(fromWireDecision)
    .filter((d): d is Decision => d !== null);
}

export async function createDecision(input: DecisionInput): Promise<Decision | null> {
  const response = await apiFetch<Record<string, unknown>>("/api/decisions", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input),
  });
  return fromWireDecision(wireRaw(response, "decision"));
}

export async function updateDecision(id: string, input: DecisionInput): Promise<Decision | null> {
  const response = await apiFetch<Record<string, unknown>>(`/api/decisions/${encodeURIComponent(id)}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input),
  });
  return fromWireDecision(wireRaw(response, "decision"));
}

export async function updateDecisionStatus(id: string, status: DecisionInput["status"]): Promise<Decision | null> {
  const response = await apiFetch<Record<string, unknown>>(`/api/decisions/${encodeURIComponent(id)}/status`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status }),
  });
  return fromWireDecision(wireRaw(response, "decision"));
}

export async function supersedeDecision(id: string): Promise<Decision | null> {
  const response = await apiFetch<Record<string, unknown>>(`/api/decisions/${encodeURIComponent(id)}/supersede`, { method: "POST" });
  return fromWireDecision(wireRaw(response, "decision"));
}

export const fromWireRecipe = (a: unknown): Persona | null => {
  const id = wireString(a, "id");
  if (!id) { warnMissingId("recipe", a, "id"); return null; }
  return {
    kind: "recipe",
    id,
    name: wireString(a, "name"),
    // HS-111-09 — no 🤖 default: an empty avatar renders as the automaton
    // sprite (AgentAvatar), the family that already owns the metaphor.
    avatar: wireString(a, "avatar"),
    role: wireString(a, "role"),
    systemPrompt: wireString(a, "system_prompt"),
    userTemplate: wireString(a, "user_template"),
    tools: wireArray(a, "tools").filter((t): t is string => typeof t === "string"),
    kbId: wireStringOrNull(a, "kb_id"),
    profileId: wireString(a, "profile_id"),
    capability: wireRaw(a, "capability") ?? null,
  };
};

export const fromWireKb = (k: unknown): KB | null => {
  const id = wireString(k, "id");
  if (!id) { warnMissingId("kb", k, "id"); return null; }
  return {
    kind: "kb",
    id,
    name: wireString(k, "name"),
    memberIds: wireArray(k, "member_ids").filter((m): m is string => typeof m === "string"),
    createdAt: wireString(k, "created_at"),
    // HS-105-01: freshness source (kbs[].last_modified), previously discarded.
    lastModified: wireStringOrNull(k, "last_modified"),
  };
};

export const fromWireWorkbench = (w: unknown): Workbench | null => {
  const id = wireString(w, "id");
  if (!id) { warnMissingId("workbench", w, "id"); return null; }
  return {
    kind: "workbench",
    id,
    name: wireString(w, "name"),
    recipeId: wireStringOrNull(w, "recipe_id"),
    profileId: wireStringOrNull(w, "profile_id"),
    resolverProfileId: wireStringOrNull(w, "resolver_profile_id"),
    schedule: wireRaw(w, "schedule") ?? null,
    scheduleEnabled: wireBool(w, "schedule_enabled"),
    itemCount: wireNumber(w, "item_count"),
    pendingCount: wireNumber(w, "pending_count"),
    lastRun: wireStringOrNull(w, "last_run"),
    createdAt: wireString(w, "created_at"),
    lastModified: wireStringOrNull(w, "last_modified"),
  };
};

export const fromWireDirectory = (d: unknown): Directory | null => {
  const id = wireString(d, "id");
  if (!id) { warnMissingId("directory", d, "id"); return null; }
  const memberIds = wireArray(d, "member_ids").filter((m): m is string => typeof m === "string");
  const fallbackMembers = typeof d === "object" && d !== null && "members" in d
    && typeof (d as Record<string, unknown>).members === "object"
    && (d as Record<string, unknown>).members !== null
    ? Object.keys((d as Record<string, unknown>).members as Record<string, unknown>)
    : [];
  return {
    kind: "directory",
    id,
    name: wireString(d, "name"),
    parentId: wireStringOrNull(d, "parent_id"),
    memberIds: memberIds.length > 0 ? memberIds : fallbackMembers,
    nameNormalized: wireString(d, "name_normalized") || "",
    createdAt: wireString(d, "created_at"),
  };
};

export const fromWireProject = (p: unknown): Project | null => {
  const id = wireString(p, "id");
  if (!id) { warnMissingId("project", p, "id"); return null; }
  return {
    kind: "project",
    id,
    name: wireString(p, "name"),
    description: wireString(p, "description"),
    keywords: wireArray(p, "keywords").filter((k): k is string => typeof k === "string"),
    teamMembers: wireArray(p, "team_members").filter((t): t is string => typeof t === "string"),
    meetingCount: wireNumber(p, "meeting_count"),
    createdAt: wireString(p, "created_at"),
    updatedAt: wireString(p, "updated_at"),
    lastModified: wireStringOrNull(p, "updated_at"),
  };
};

export const fromWireRoadmap = (r: unknown): Roadmap | null => {
  const slug = wireString(r, "slug");
  if (!slug) { warnMissingId("roadmap", r, "slug"); return null; }
  return {
    kind: "roadmap",
    id: `roadmap:${slug}`,
    title: wireString(r, "name"),
    slug,
    name: wireString(r, "name"),
    phaseCount: wireNumber(r, "phaseCount"),
    currentPhase: wireNumber(r, "currentPhase"),
    currentPhaseTitle: wireString(r, "currentPhaseTitle"),
    storiesDone: wireNumber(r, "storiesDone"),
    storiesTotal: wireNumber(r, "storiesTotal"),
    health: wireString(r, "health"),
    issues: wireArray(r, "issues").filter((i): i is string => typeof i === "string"),
    nextStoryId: wireStringOrNull(r, "nextStoryId"),
  };
};

export const fromWireRepository = (repository: unknown): Repository | null => {
  const id = wireString(repository, "id") || wireString(repository, "source_id");
  if (!id) { warnMissingId("repository", repository, "id"); return null; }
  return {
    kind: "repository",
    id,
    name: wireString(repository, "name", "Repository"),
    sourceId: wireString(repository, "source_id") || id,
    branch: wireString(repository, "branch"),
    createdAt: wireString(repository, "created_at"),
    lastModified: wireStringOrNull(repository, "created_at"),
  };
};

export const fromWireChain = (c: unknown): Chain | null => {
  const id = wireString(c, "id");
  if (!id) { warnMissingId("chain", c, "id"); return null; }
  return {
    kind: "chain",
    id,
    name: wireString(c, "name"),
    steps: wireArray(c, "steps").filter((s): s is string => typeof s === "string"),
    capability: wireRaw(c, "capability") ?? null,
  };
};

export const fromWireWorkflow = (w: unknown): Workflow | null => {
  const id = wireString(w, "id");
  if (!id) { warnMissingId("workflow", w, "id"); return null; }
  const graph = wireRaw(w, "graph_json");
  const hasGraph =
    graph != null && typeof graph === "object" && Object.keys(graph as Record<string, unknown>).length > 0;
  return {
    kind: "workflow",
    id,
    name: wireString(w, "name"),
    prompt: wireString(w, "prompt"),
    hasGraph: Boolean(hasGraph),
    graphJson: hasGraph ? (graph as Workflow["graphJson"]) : undefined,
    capability: wireRaw(w, "capability") ?? null,
  };
};

const fromWireMeeting = (m: unknown): Meeting | null => {
  const id = wireString(m, "id");
  if (!id) { warnMissingId("meeting", m, "id"); return null; }
  return {
    kind: "meeting",
    id,
    title: wireString(m, "title", "Untitled meeting"),
    startedAt: wireString(m, "started_at"),
    endedAt: wireStringOrNull(m, "ended_at"),
    segmentCount: wireNumber(m, "segment_count"),
    actionItemCount: wireNumber(m, "action_item_count"),
    durationSeconds: wireRaw(m, "duration_seconds") as number | null | undefined,
    tags: wireArray(m, "tags").filter((t): t is string => typeof t === "string"),
    intelStatus: wireStringOrNull(m, "intel_status"),
  };
};

const fromWireArtifact = (a: unknown): Artifact | null => {
  const id = wireString(a, "id");
  if (!id) { warnMissingId("artifact", a, "id"); return null; }
  return {
    kind: "artifact",
    id,
    meetingId: wireStringOrNull(a, "meeting_id"),
    artifactType: wireString(a, "artifact_type"),
    title: wireString(a, "title") || wireString(a, "artifact_type") || "Artifact",
    bodyMarkdown: wireString(a, "body_markdown"),
    status: wireString(a, "status"),
    confidence: wireRaw(a, "confidence") as number | null | undefined,
    sources: wireArray(a, "sources"),
  };
};

/** Resolve the session-items array from the real (nested) coders status. */
function coderSessionItems(data: unknown): unknown[] {
  if (!data || typeof data !== "object") return [];
  const d = data as Record<string, unknown>;
  const agent = d.agent as Record<string, unknown> | undefined;
  const nested = agent?.sessions;
  if (nested && typeof nested === "object" && !Array.isArray(nested) && Array.isArray((nested as Record<string, unknown>).items))
    return (nested as Record<string, unknown>).items as unknown[];
  if (Array.isArray(nested)) return nested;
  if (Array.isArray(d.sessions)) return d.sessions;
  return [];
}

export const fromCoderStatus = (data: unknown): Coder[] =>
  coderSessionItems(data).map((item: unknown, i: number) => {
    const rec = (item && typeof item === "object" ? item : {}) as Record<string, unknown>;
    const s = (rec.session && typeof rec.session === "object" ? rec.session : rec) as Record<string, unknown>;
    const identity = (rec.identity && typeof rec.identity === "object" ? rec.identity : {}) as Record<string, unknown>;
    const sessionId = String(s.session_id || `s${i}`);
    return {
      kind: "coder" as const,
      agent: (s.agent === "codex" ? "codex" : "claude") as Coder["agent"],
      id: sessionId,
      sessionId,
      title: String(s.project || s.cwd || s.project_name || ""),
      project: String(s.project || s.cwd || s.project_name || ""),
      model: String(s.model || ""),
      state: String(s.state || (s.awaiting_response ? "waiting" : "running")),
      question:
        (identity.question as string | null) ||
        (s.question as string | null) ||
        (s.last_question as string | null) ||
        (s.last_assistant_text as string | null) ||
        (s.awaiting_response ? (identity.prompt as string | null) || null : null),
      selected: Boolean(rec.selected),
      pinned: Boolean(rec.pinned ?? s.pinned),
      stale: Boolean(rec.stale),
    };
  });

/** The subset of PrimitiveKind that has a wire endpoint and a fromWire mapper. */
type WireKind = Exclude<
  PrimitiveKind,
  "game" | "layout" | "story" | "intelligence" | "people"
>;

/** Compile-time completeness guard: adding a new WireKind without a mapper
 * here is a type error. The registry is declarative — loadAll() still drives
 * the actual fetch orchestration (each kind has distinct endpoint shapes). */
const WIRE_MAPPERS = {
  meeting: fromWireMeeting,
  artifact: fromWireArtifact,
  note: fromWireNote,
  decision: fromWireDecision,
  directory: fromWireDirectory,
  kb: fromWireKb,
  project: fromWireProject,
  repository: fromWireRepository,
  recipe: fromWireRecipe,
  chain: fromWireChain,
  workflow: fromWireWorkflow,
  coder: fromCoderStatus, // returns Coder[] (batch mapper)
  roadmap: fromWireRoadmap,
  workbench: fromWireWorkbench,
} as const satisfies Record<WireKind, (...args: never[]) => unknown>;

// Ensure the registry is referenced so tree-shaking doesn't remove it.
void WIRE_MAPPERS;

/** Load every kind — the same allSettled sweep the original desk ran. */
export async function loadAll(): Promise<LoadResult> {
  const items: TypedItems = { ...EMPTY_ITEMS };
  const status: Status = {};
  let profiles: Array<Record<string, unknown>> = [];
  let projects: ProjectSummary[] = [];
  let inferenceTargets: InferenceTarget[] = [];
  let models: HubModel[] = [];
  let error = "";
  const fail = (kind: PrimitiveKind | "profile" | "project", label: string, e: unknown) => {
    status[kind] = "unreachable";
    if (!error) error = `${label}: ${e && typeof e === "object" && "message" in e ? (e as Error).message : String(e)}`;
  };

  await Promise.allSettled([
    apiFetch<Record<string, unknown>>("/api/meetings?limit=24")
      .then((d) => {
        items.meeting = wireArray(d, "meetings").map(fromWireMeeting).filter((x): x is Meeting => x !== null);
        status.meeting = "live";
      })
      .catch((e) => fail("meeting", "Meetings", e)),
    apiFetch<Record<string, unknown>>("/api/sync/pull?limit=50")
      .then((d) => {
        items.artifact = liveValues(wireArray(d, "artifacts"))
          .slice(0, 24)
          .map(fromWireArtifact).filter((x): x is Artifact => x !== null);
        status.artifact = "live";
      })
      .catch((e) => fail("artifact", "Artifacts", e)),
    apiFetch<Record<string, unknown>>("/api/notes")
      .then((d) => {
        items.note = wireArray(d, "notes")
          .filter((n) => !wireBool(n, "deleted"))
          .map(fromWireNote).filter((x): x is Note => x !== null);
        status.note = "live";
      })
      .catch((e) => fail("note", "Notes", e)),
    fetchDecisions()
      .then((decisions) => {
        items.decision = decisions;
        status.decision = "live";
      })
      .catch((e) => fail("decision", "Decisions", e)),
    apiFetch<Record<string, unknown>>("/api/recipes")
      .then((d) => {
        items.recipe = wireArray(d, "recipes")
          .filter((a) => !wireBool(a, "deleted"))
          .map(fromWireRecipe).filter((x): x is Persona => x !== null);
        status.recipe = "live";
      })
      .catch((e) => fail("recipe", "Agents", e)),
    apiFetch<Record<string, unknown>>("/api/kbs")
      .then((d) => {
        items.kb = wireArray(d, "kbs").filter((k) => !wireBool(k, "deleted")).map(fromWireKb).filter((x): x is KB => x !== null);
        status.kb = "live";
      })
      .catch((e) => fail("kb", "Knowledge", e)),
    apiFetch<Record<string, unknown>>("/api/directories")
      .then((d) => {
        const raw = wireArray(d, "directories");
        const source = raw.length > 0 ? raw : liveValues(Array.isArray(d) ? d : []);
        items.directory = source
          .filter((x) => !wireBool(x, "deleted"))
          .map(fromWireDirectory).filter((x): x is Directory => x !== null);
        status.directory = "live";
      })
      .catch((e) => fail("directory", "Zones", e)),
    apiFetch<Record<string, unknown>>("/api/chains")
      .then((d) => {
        items.chain = wireArray(d, "chains")
          .filter((c) => !wireBool(c, "deleted"))
          .map(fromWireChain).filter((x): x is Chain => x !== null);
        status.chain = "live";
      })
      .catch((e) => fail("chain", "Sequences", e)),
    apiFetch<Record<string, unknown>>("/api/workflows")
      .then((d) => {
        items.workflow = wireArray(d, "workflows")
          .filter((w) => !wireBool(w, "deleted"))
          .map(fromWireWorkflow).filter((x): x is Workflow => x !== null);
        status.workflow = "live";
      })
      .catch((e) => fail("workflow", "Workflows", e)),
    apiFetch<Record<string, unknown>>("/api/workbenches")
      .then((d) => {
        items.workbench = wireArray(d, "workbenches")
          .filter((w) => !wireBool(w, "deleted"))
          .map(fromWireWorkbench).filter((x): x is Workbench => x !== null);
        status.workbench = "live";
      })
      .catch((e) => fail("workbench", "Workbenches", e)),
    // HS-134-02: profiles derived from inference targets (read routes retired).
    apiFetch<Record<string, unknown>>("/api/projects")
      .then((d) => {
        const raw = wireArray(d, "projects").filter((p) => !wireBool(p, "is_archived"));
        items.project = raw.map(fromWireProject).filter((p): p is Project => p !== null);
        // Keep the ProjectSummary list for the store's separate projects field.
        projects = raw
          .filter((p) => typeof p === "object" && p !== null)
          .map((p) => p as ProjectSummary);
        status.project = "live";
      })
      .catch((e) => {
        projects = [];
        fail("project", "Projects", e);
      }),
    apiFetch<Record<string, unknown>>("/api/inference-targets")
      .then((d) => {
        inferenceTargets = Array.isArray((d as Record<string, unknown>).targets) ? (d as Record<string, unknown>).targets as InferenceTarget[] : [];
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
            endpoint: "",
            node: "",
          },
        ];
      }),
    // HS-83-03 — the runnable allow-list (what a `model` override accepts).
    apiFetch<Record<string, unknown>>("/api/models")
      .then((d) => {
        models = Array.isArray((d as Record<string, unknown>).models) ? (d as Record<string, unknown>).models as HubModel[] : [];
      })
      .catch(() => {
        models = []; /* older hub = honest empty door */
      }),
    fetchRoadmaps()
      .then((roadmaps) => {
        items.roadmap = roadmaps.map((r) => fromWireRoadmap(r)).filter((r): r is Roadmap => r !== null);
        status.roadmap = "live";
      })
      .catch((e) => fail("roadmap", "Roadmaps", e)),
    fetchRepositories()
      .then((repositories) => {
        items.repository = repositories.map((r) => fromWireRepository(r)).filter((x): x is Repository => x !== null);
        status.repository = "live";
      })
      .catch((e) => fail("repository", "Repositories", e)),
    apiFetch<unknown>("/api/coders/status")
      .then((d) => {
        items.coder = fromCoderStatus(d);
        status.coder = "live";
      })
      .catch(() => {
        items.coder = []; /* companion off = honest empty lane */
      }),
  ]);

  // HS-134-02: derive profiles from inference targets (read routes retired).
  // Consumers (RecipeEditor, Pullout, PersonaChat) need {id, name, kind, base_url, node}.
  const REVERSE_KIND: Record<string, string> = {
    private_endpoint: "openAICompatible",
    external_service: "openAICompatible",
    this_device: "onDevice",
    paired_device: "desktop",
    mesh_node: "meshNode",
  };
  profiles = inferenceTargets
    .filter((t) => t.profile_id != null)
    .map((t) => ({
      id: t.id,
      name: t.name,
      kind: REVERSE_KIND[t.kind] ?? t.kind,
      base_url: t.endpoint ?? "",
      node: t.node ?? "",
      model: t.model,
      context_limit: t.context_limit,
      requires_key: t.secret?.required ?? false,
    }));
  status.profile = inferenceTargets.length > 0 ? "live" : (status.profile || "unreachable");

  return { items, profiles, projects, inferenceTargets, models, status, error };
}

/* ── Workbench detail endpoints (HS-117-13) ──────────────────────────── */

import type {
  WorkbenchDetail,
  WorkbenchItem,
  WorkbenchRun,
  Skill,
  MemoryEntry,
  WorkbenchAutomation,
  AutomationHistoryEntry,
  AutomationTestResult,
  ResourcefulPolicy,
  ResourcefulDispatch,
} from "./detail-types";

export async function fetchWorkbenchDetail(id: string): Promise<WorkbenchDetail> {
  const data = await apiFetch<Record<string, unknown>>(`/api/workbenches/${encodeURIComponent(id)}`);
  return wireRaw(data, "workbench") as WorkbenchDetail;
}

export async function fetchWorkbenchRuns(id: string): Promise<WorkbenchRun[]> {
  const data = await apiFetch<Record<string, unknown>>(`/api/workbenches/${encodeURIComponent(id)}/runs`);
  return (wireArray(data, "runs") as WorkbenchRun[]) || [];
}

export async function fetchWorkbenchMemory(id: string): Promise<MemoryEntry[]> {
  const data = await apiFetch<Record<string, unknown>>(`/api/workbenches/${encodeURIComponent(id)}/memory`);
  return (wireArray(data, "entries") as MemoryEntry[]) || [];
}

export async function fetchSkills(): Promise<Skill[]> {
  const data = await apiFetch<Record<string, unknown>>("/api/skills");
  return (wireArray(data, "skills") as Skill[]) || [];
}

export async function updateWorkbenchField(
  id: string,
  fields: Record<string, unknown>,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(`/api/workbenches/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
}

export async function addWorkbenchItem(
  workbenchId: string,
  payload: Record<string, unknown>,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(`/api/workbenches/${encodeURIComponent(workbenchId)}/items`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function updateWorkbenchItem(
  workbenchId: string,
  itemId: string,
  fields: Record<string, unknown>,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/items/${encodeURIComponent(itemId)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(fields),
    },
  );
}

export async function deleteWorkbenchItem(
  workbenchId: string,
  itemId: string,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/items/${encodeURIComponent(itemId)}`,
    { method: "DELETE" },
  );
}

export async function triggerWorkbenchRun(workbenchId: string): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/run`,
    { method: "POST" },
  );
}

export async function updateSkill(
  skillId: string,
  fields: Record<string, unknown>,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(`/api/skills/${encodeURIComponent(skillId)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
}

export async function clearWorkbenchMemory(workbenchId: string): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/memory`,
    { method: "DELETE" },
  );
}

export async function promoteMemoryToSkill(
  workbenchId: string,
  index: number,
): Promise<void> {
  await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/memory/${index}/promote`,
    { method: "POST" },
  );
}

export async function retryMint(
  workbenchId: string,
  itemId: string,
): Promise<string | null> {
  const data = await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/items/${encodeURIComponent(itemId)}/retry-mint`,
    { method: "POST" },
  );
  return data?.artifact_id ? String(data.artifact_id) : null;
}

/* ── Workbench automations (Reactions) ─────────────────────────────── */

export async function fetchWorkbenchAutomations(
  workbenchId: string,
): Promise<WorkbenchAutomation[]> {
  const data = await apiFetch<{ automations?: Record<string, unknown>[] }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations`,
  );
  return Array.isArray(data.automations) ? data.automations.map(automationFromWire) : [];
}

/** The service's rich Watch + Reaction document becomes the compact row the
 * Workbench needs. Keeping this mapper tolerant also lets a later facade send
 * that compact shape directly. */
function automationFromWire(value: Record<string, unknown>): WorkbenchAutomation {
  const reaction = value.reaction && typeof value.reaction === "object"
    ? value.reaction as Record<string, unknown>
    : value;
  const watch = value.watch && typeof value.watch === "object"
    ? value.watch as Record<string, unknown>
    : null;
  const connector = String(watch?.connector_id || value.provider || "custom");
  const provider = connector === "gh" || connector === "github"
    ? "github"
    : connector === "jira" ? "jira" : "custom";
  const enabled = Boolean(reaction.enabled);
  const lastError = watch?.last_error ? String(watch.last_error) : null;
  const adapterStatus = provider === "jira" ? "unavailable" : "ready";
  return {
    id: String(reaction.id || value.id || ""),
    name: String(reaction.name || value.name || "Automation"),
    provider,
    event_kind: String(reaction.event_pattern || value.event_kind || "event"),
    enabled,
    status: lastError ? "attention" : enabled ? "active" : "paused",
    adapter_status: adapterStatus,
    last_error: lastError,
    last_good_at: watch?.last_success_at ? String(watch.last_success_at) : value.last_good_at ? String(value.last_good_at) : null,
  };
}

export async function createWorkbenchAutomation(
  workbenchId: string,
  presetId: "github-review-requested" | "jira-assigned-to-me",
  repository: string,
): Promise<WorkbenchAutomation> {
  const data = await apiFetch<{ automation: Record<string, unknown> }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations`,
    { method: "POST", json: { preset_id: presetId, repository } },
  );
  return automationFromWire(data.automation);
}

/** Enabling is the owner gesture that establishes an initial silent baseline. */
export async function setWorkbenchAutomationEnabled(
  workbenchId: string,
  automationId: string,
  enabled: boolean,
): Promise<WorkbenchAutomation> {
  const data = await apiFetch<{ automation: Record<string, unknown> }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations/${encodeURIComponent(automationId)}`,
    { method: "PATCH", json: { enabled } },
  );
  return automationFromWire(data.automation);
}

/** A test exercises matching without adding an item or advancing the baseline. */
export async function testWorkbenchAutomation(
  workbenchId: string,
  automationId: string,
): Promise<AutomationTestResult> {
  const data = await apiFetch<Record<string, unknown>>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations/${encodeURIComponent(automationId)}/test`,
    { method: "POST" },
  );
  const changes = Array.isArray(data.changes) ? data.changes.length : Number(data.changes || 0);
  return {
    entity_count: Number(data.entity_count || 0),
    changes,
    would_add: Number(data.would_project || data.would_add || 0),
  };
}

export async function fetchWorkbenchAutomationHistory(
  workbenchId: string,
  automationId: string,
): Promise<AutomationHistoryEntry[]> {
  const data = await apiFetch<{ history?: Record<string, unknown>[] }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/automations/${encodeURIComponent(automationId)}/history`,
  );
  return Array.isArray(data.history) ? data.history.map((entry) => ({
    id: String(entry.id || entry.event_id || ""),
    occurred_at: String(entry.occurred_at || entry.projected_at || entry.event_created_at || ""),
    outcome: entry.item_id ? "added" : "skipped",
    event_kind: String(entry.event_kind || entry.event_type || "event"),
    subject: String(entry.subject || entry.subject_ref || ""),
    receipt_id: entry.receipt_id ? String(entry.receipt_id) : null,
    detail: entry.detail ? String(entry.detail) : null,
  })) : [];
}

export async function fetchResourcefulPolicy(
  workbenchId: string,
): Promise<ResourcefulPolicy> {
  const data = await apiFetch<{ policy: ResourcefulPolicy }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/resourceful`,
  );
  return data.policy;
}

export async function updateResourcefulPolicy(
  workbenchId: string,
  policy: Pick<ResourcefulPolicy,
    "enabled" | "idle_after_minutes" | "cooldown_hours" | "nightly_target" |
    "night_only" | "night_start_hour" | "night_end_hour" | "routines"
  >,
): Promise<ResourcefulPolicy> {
  const data = await apiFetch<{ policy: ResourcefulPolicy }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/resourceful`,
    { method: "PUT", json: policy },
  );
  return data.policy;
}

export async function fetchResourcefulHistory(
  workbenchId: string,
): Promise<ResourcefulDispatch[]> {
  const data = await apiFetch<{ history?: ResourcefulDispatch[] }>(
    `/api/workbenches/${encodeURIComponent(workbenchId)}/resourceful/history`,
  );
  return Array.isArray(data.history) ? data.history : [];
}

/** HS-118-05: resolve voice references via the workbench's resolver profile. */
export async function resolveVoiceReferences(
  workbenchId: string,
  transcript: string,
  requestId: string,
): Promise<{
  refs: Array<{ name: string; id: string; ref: string; kind: string }>;
  egress: { boundary: string; model: string };
  request_id: string;
  error?: string;
  attempts?: number;
}> {
  return apiFetch(`/api/workbenches/${encodeURIComponent(workbenchId)}/voice/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ transcript, request_id: requestId }),
  });
}
