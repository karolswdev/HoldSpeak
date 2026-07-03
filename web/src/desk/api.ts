/** The desk's typed data layer (HS-73-01) — the faithful port of the Alpine
 * factory's loaders (`desk-app.js loadAll` + `fromWire*`): same endpoints,
 * same normalized shapes, same tolerance. The wire is snake_case; the in-app
 * shapes are the camelCase view shapes the world renders. */

export type Kind =
  | "meeting" | "artifact" | "note" | "agent" | "kb"
  | "directory" | "chain" | "workflow" | "coder";

export interface DeskItem {
  kind: Kind;
  id: string;
  title?: string;
  name?: string;
  [key: string]: unknown;
}

export type Items = Record<Kind, DeskItem[]>;
export type Status = Partial<Record<Kind | "profile", "live" | "unreachable">>;

export interface LoadResult {
  items: Items;
  profiles: Array<Record<string, unknown>>;
  status: Status;
  error: string;
}

export const EMPTY_ITEMS: Items = {
  meeting: [], artifact: [], note: [], agent: [], kb: [],
  directory: [], chain: [], workflow: [], coder: [],
};

async function fetchJson(url: string, opts?: RequestInit): Promise<any> {
  const res = await fetch(url, opts);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || body.detail || `HTTP ${res.status}`);
  return body;
}

/** Unwrap {meta,value} change-set records, dropping tombstones. */
export function liveValues(records: any[]): any[] {
  return (records || [])
    .filter((rec) => !(rec && rec.meta && rec.meta.deleted))
    .map((rec) => (rec && rec.value ? rec.value : rec))
    .filter(Boolean);
}

export const fromWireNote = (n: any): DeskItem => ({
  kind: "note", id: n.id, title: n.title,
  bodyMarkdown: n.body_markdown, tags: n.tags || [], createdAt: n.created_at,
});

export const fromWireAgent = (a: any): DeskItem => ({
  kind: "agent", id: a.id, name: a.name, avatar: a.avatar || "🤖",
  role: a.role || "", systemPrompt: a.system_prompt || "",
  userTemplate: a.user_template || "", tools: a.tools || [],
  kbId: a.kb_id || null, profileId: a.profile_id || "",
});

export const fromWireKb = (k: any): DeskItem => ({
  kind: "kb", id: k.id, name: k.name,
  memberIds: k.member_ids || [], createdAt: k.created_at,
});

export const fromWireDirectory = (d: any): DeskItem => ({
  kind: "directory", id: d.id, name: d.name, parentId: d.parent_id || null,
  memberIds: d.member_ids || (d.members ? Object.keys(d.members) : []),
  createdAt: d.created_at,
});

export const fromWireChain = (c: any): DeskItem => ({
  kind: "chain", id: c.id, name: c.name, steps: c.steps || [],
});

export const fromWireWorkflow = (w: any): DeskItem => {
  const graph = w.graph_json;
  const hasGraph = graph && typeof graph === "object" && Object.keys(graph).length > 0;
  return {
    kind: "workflow", id: w.id, name: w.name, prompt: w.prompt || "",
    hasGraph: Boolean(hasGraph), graphJson: graph,
  };
};

const fromWireMeeting = (m: any): DeskItem => ({
  kind: "meeting", id: m.id, title: m.title || "Untitled meeting",
  startedAt: m.started_at, endedAt: m.ended_at, segmentCount: m.segment_count,
  actionItemCount: m.action_item_count, durationSeconds: m.duration_seconds,
  tags: m.tags || [], intelStatus: m.intel_status,
});

const fromWireArtifact = (a: any): DeskItem => ({
  kind: "artifact", id: a.id, meetingId: a.meeting_id,
  artifactType: a.artifact_type, title: a.title || a.artifact_type || "Artifact",
  bodyMarkdown: a.body_markdown || "", status: a.status,
  confidence: a.confidence, sources: a.sources || [],
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
        identity.question || s.question || s.last_question ||
        s.last_assistant_text ||
        (s.awaiting_response ? identity.prompt || null : null),
      selected: Boolean(item.selected),
      pinned: Boolean(item.pinned ?? s.pinned),
      stale: Boolean(item.stale),
    };
  });

/** Load every kind — the same allSettled sweep the Alpine desk ran. */
export async function loadAll(): Promise<LoadResult> {
  const items: Items = { ...EMPTY_ITEMS };
  const status: Status = {};
  let profiles: Array<Record<string, unknown>> = [];
  let error = "";
  const fail = (kind: Kind | "profile", label: string, e: any) => {
    status[kind] = "unreachable";
    if (!error) error = `${label}: ${e?.message || e}`;
  };

  await Promise.allSettled([
    fetchJson("/api/meetings?limit=24")
      .then((d) => { items.meeting = (d.meetings || []).map(fromWireMeeting); status.meeting = "live"; })
      .catch((e) => fail("meeting", "Meetings", e)),
    fetchJson("/api/sync/pull?limit=50")
      .then((d) => { items.artifact = liveValues(d.artifacts).slice(0, 24).map(fromWireArtifact); status.artifact = "live"; })
      .catch((e) => fail("artifact", "Artifacts", e)),
    fetchJson("/api/notes")
      .then((d) => { items.note = (d.notes || []).filter((n: any) => !n.deleted).map(fromWireNote); status.note = "live"; })
      .catch((e) => fail("note", "Notes", e)),
    fetchJson("/api/agents")
      .then((d) => { items.agent = (d.agents || []).filter((a: any) => !a.deleted).map(fromWireAgent); status.agent = "live"; })
      .catch((e) => fail("agent", "Agents", e)),
    fetchJson("/api/kbs")
      .then((d) => { items.kb = (d.kbs || []).filter((k: any) => !k.deleted).map(fromWireKb); status.kb = "live"; })
      .catch((e) => fail("kb", "KBs", e)),
    fetchJson("/api/directories")
      .then((d) => {
        const raw = d.directories || liveValues(d);
        items.directory = (raw || []).filter((x: any) => !x.deleted).map(fromWireDirectory);
        status.directory = "live";
      })
      .catch((e) => fail("directory", "Directories", e)),
    fetchJson("/api/chains")
      .then((d) => { items.chain = (d.chains || []).filter((c: any) => !c.deleted).map(fromWireChain); status.chain = "live"; })
      .catch((e) => fail("chain", "Chains", e)),
    fetchJson("/api/workflows")
      .then((d) => { items.workflow = (d.workflows || []).filter((w: any) => !w.deleted).map(fromWireWorkflow); status.workflow = "live"; })
      .catch((e) => fail("workflow", "Workflows", e)),
    fetchJson("/api/profiles")
      .then((d) => { profiles = (d.profiles || []).filter((p: any) => !p.deleted); status.profile = "live"; })
      .catch(() => { profiles = []; status.profile = "unreachable"; }),
    fetchJson("/api/coders/status")
      .then((d) => { items.coder = fromCoderStatus(d); status.coder = "live"; })
      .catch(() => { items.coder = []; /* companion off = honest empty lane */ }),
  ]);

  return { items, profiles, status, error };
}
