// HS-169-02 — typed client for the streamlined Door routes.
// Mirrors holdspeak/services/door_service.py (count + create).

import { apiFetch } from "../../../lib/api";

/* ── Wire types ── */

export interface CountToken {
  key: string;
  label: string;
  count: number;
}

export interface CountResponse {
  tokens: CountToken[];
  plain: string;
  checkedAt: string;
  host: string;
  state: "live" | "cant_check";
  reason: string | null;
}

export interface CreateResponse {
  projectId: string;
}

export interface DoorSourcePayload {
  provider: string;
  scope: string | { connection_ref: string; projects: string[] };
  watches: string[];
  adjust?: Record<string, unknown>;
}

/* ── Decoders ── */

function decodeCountToken(raw: Record<string, unknown>): CountToken {
  return {
    key: String(raw.key ?? ""),
    label: String(raw.label ?? ""),
    count: typeof raw.count === "number" ? raw.count : 0,
  };
}

function decodeCountResponse(raw: Record<string, unknown>): CountResponse {
  const tokens = Array.isArray(raw.tokens)
    ? (raw.tokens as Record<string, unknown>[]).map(decodeCountToken)
    : [];
  return {
    tokens,
    plain: String(raw.plain ?? ""),
    checkedAt: String(raw.checked_at ?? raw.checkedAt ?? ""),
    host: String(raw.host ?? ""),
    state: raw.state === "cant_check" ? "cant_check" : "live",
    reason: typeof raw.reason === "string" ? raw.reason : null,
  };
}

function decodeCreateResponse(raw: Record<string, unknown>): CreateResponse {
  return {
    projectId: String(raw.project_id ?? raw.projectId ?? ""),
  };
}

/* ── API calls ── */

export async function doorCount(
  provider: string,
  scope: string | { connection_ref: string; projects: string[] },
  watches: string[],
  adjust?: Record<string, unknown>,
): Promise<CountResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/projects/door/count",
    { method: "POST", json: { provider, scope, watches, adjust } },
  );
  return decodeCountResponse(raw);
}

export async function doorCreate(
  outcome: string,
  sources: DoorSourcePayload[],
): Promise<CreateResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/projects/door",
    { method: "POST", json: { outcome, sources } },
  );
  return decodeCreateResponse(raw);
}

/* ── Provider discovery (moved from setup/api to avoid importing a parked folder) ── */

const PROVIDERS = "/api/providers";

export interface DiscoveryItem {
  id: string;
  name: string;
  owner: string;
  visibility: string;
}

export interface DiscoveryResponse {
  state: string;
  items: DiscoveryItem[];
  cursor: string | null;
  errorCode: string | null;
}

function decodeDiscoveryItem(raw: Record<string, unknown>): DiscoveryItem {
  const id = String(raw.id ?? "");
  const derivedOwner = id.includes("/") ? id.split("/")[0] : "";
  return {
    id,
    name: String(raw.name ?? ""),
    owner: derivedOwner,
    visibility: String(raw.visibility ?? ""),
  };
}

function decodeDiscoveryResponse(raw: Record<string, unknown>): DiscoveryResponse {
  const items = Array.isArray(raw.items)
    ? raw.items.map((i: Record<string, unknown>) => decodeDiscoveryItem(i))
    : [];
  return {
    state: String(raw.state ?? ""),
    items,
    cursor: raw.cursor != null ? String(raw.cursor) : null,
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
  };
}

export async function discoverGitHub(
  query?: string,
  cursor?: string,
): Promise<DiscoveryResponse> {
  const params = new URLSearchParams();
  if (query) params.set("query", query);
  if (cursor) params.set("cursor", cursor);
  const qs = params.toString();
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/github/discover${qs ? `?${qs}` : ""}`,
  );
  return decodeDiscoveryResponse(raw);
}

export interface JiraDiscoveryItem {
  id: string;
  key?: string;
  name: string;
  project_id?: string;
  type?: string;
  style?: string;
  private?: boolean;
  lead?: string | null;
  subtask?: boolean;
  hierarchy_level?: number;
  category?: string;
  category_name?: string;
}

export interface JiraDiscoveryResponse {
  state: string;
  items: JiraDiscoveryItem[];
  cursor: number | null;
  errorCode: string | null;
  errorDetail: string | null;
  connectionRef: string;
  source?: string;
  categories?: Array<{ key: string; name: string; source: string }>;
}

function decodeJiraDiscoveryItem(raw: Record<string, unknown>): JiraDiscoveryItem {
  const item: JiraDiscoveryItem = {
    id: String(raw.id ?? ""),
    name: String(raw.name ?? ""),
  };
  if (raw.key != null) item.key = String(raw.key);
  if (raw.project_id != null) item.project_id = String(raw.project_id);
  if (raw.type != null) item.type = String(raw.type);
  if (raw.style != null) item.style = String(raw.style);
  if (raw.private != null) item.private = Boolean(raw.private);
  if (raw.lead != null) item.lead = String(raw.lead);
  if (raw.subtask != null) item.subtask = Boolean(raw.subtask);
  if (raw.hierarchy_level != null) item.hierarchy_level = Number(raw.hierarchy_level);
  if (raw.category != null) item.category = String(raw.category);
  if (raw.category_name != null) item.category_name = String(raw.category_name);
  return item;
}

function decodeJiraDiscoveryResponse(raw: Record<string, unknown>): JiraDiscoveryResponse {
  const items = Array.isArray(raw.items)
    ? raw.items.map((i: Record<string, unknown>) => decodeJiraDiscoveryItem(i))
    : [];
  const categories = Array.isArray(raw.categories)
    ? raw.categories.map((c: Record<string, unknown>) => ({
        key: String(c.key ?? ""),
        name: String(c.name ?? ""),
        source: String(c.source ?? ""),
      }))
    : undefined;
  return {
    state: String(raw.state ?? ""),
    items,
    cursor: raw.cursor != null ? Number(raw.cursor) : null,
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
    errorDetail: raw.error_detail != null ? String(raw.error_detail) : null,
    connectionRef: String(raw.connection_ref ?? ""),
    source: raw.source != null ? String(raw.source) : undefined,
    categories,
  };
}

export async function discoverJira(
  connectionRef: string,
  kind: "projects" | "issue_types" | "statuses",
  opts?: { query?: string; projectKey?: string; cursor?: number; limit?: number },
): Promise<JiraDiscoveryResponse> {
  const params = new URLSearchParams();
  params.set("connection_ref", connectionRef);
  params.set("kind", kind);
  if (opts?.query) params.set("query", opts.query);
  if (opts?.projectKey) params.set("project_key", opts.projectKey);
  if (opts?.cursor != null) params.set("cursor", String(opts.cursor));
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/jira/discover?${params.toString()}`,
  );
  return decodeJiraDiscoveryResponse(raw);
}
