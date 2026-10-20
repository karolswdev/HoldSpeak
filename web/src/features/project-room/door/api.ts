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
  found: FoundLinkResult[];
}

export interface FoundLinkResult {
  kind: "meeting" | "note";
  id: string;
  state: "linked" | "failed";
  error: string | null;
}

export type PreviewSourceState = "checked" | "cant_check" | "not_checked";

export interface PreviewSource {
  provider: string;
  scope: string;
  site?: string;
  label: string;
  state: PreviewSourceState;
  reason: string | null;
  connectionRef?: string;
  spaceId?: string;
}

export interface PreviewFoundItem {
  kind: "meeting" | "note";
  id: string;
  title: string;
  detail: string;
  attendees?: string[];
  selected: boolean;
  linkState: "pending" | "linked" | "failed";
  linkError: string | null;
}

export interface PreviewResponse {
  sources: PreviewSource[];
  found: PreviewFoundItem[];
  people: string[];
}

export interface DoorSourcePayload {
  provider: string;
  scope: string | { connection_ref: string; projects: string[] } | { connection_ref: string; space_key: string; space_id: string };
  watches: string[];
  adjust?: Record<string, unknown>;
  test_state?: "passed" | "not_checked";
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
  const found = Array.isArray(raw.found_links)
    ? raw.found_links.flatMap((rawItem) => {
        if (!rawItem || typeof rawItem !== "object") return [];
        const item = rawItem as Record<string, unknown>;
        const kind: FoundLinkResult["kind"] | null = item.kind === "note" || item.kind === "meeting" ? item.kind : null;
        const id = typeof item.id === "string" ? item.id : "";
        const state: FoundLinkResult["state"] | null = item.state === "linked" || item.state === "failed" ? item.state : null;
        if (!kind || !id || !state) return [];
        return [{
          kind,
          id,
          state,
          error: typeof item.error === "string" && item.error.trim() ? item.error : null,
        }];
      })
    : [];
  return {
    projectId: String(raw.project_id ?? raw.projectId ?? ""),
    found,
  };
}

/* ── API calls ── */

export async function doorCount(
  provider: string,
  scope: string | { connection_ref: string; projects: string[] } | { connection_ref: string; space_key: string; space_id: string },
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
  found?: { meeting_ids: string[]; note_ids: string[] },
): Promise<CreateResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/projects/door",
    { method: "POST", json: { outcome, sources, ...(found ? { found } : {}) } },
  );
  return decodeCreateResponse(raw);
}

function decodePreviewSource(raw: Record<string, unknown>): PreviewSource {
  const state = raw.state === "checked" || raw.state === "cant_check" ? raw.state : "not_checked";
  return {
    provider: String(raw.provider ?? ""),
    scope: String(raw.scope ?? ""),
    site: typeof raw.site === "string" ? raw.site : undefined,
    label: String(raw.label ?? raw.scope ?? ""),
    state,
    reason: typeof raw.reason === "string" ? raw.reason : null,
    connectionRef: typeof raw.connection_ref === "string" ? raw.connection_ref : undefined,
    spaceId: typeof raw.space_id === "string" ? raw.space_id : undefined,
  };
}

function decodePreviewFound(raw: Record<string, unknown>): PreviewFoundItem {
  return {
    kind: raw.kind === "note" ? "note" : "meeting",
    id: String(raw.id ?? ""),
    title: String(raw.title ?? ""),
    detail: String(raw.detail ?? ""),
    attendees: Array.isArray(raw.attendees) ? raw.attendees.map(String) : undefined,
    selected: raw.selected !== false,
    linkState: raw.link_state === "linked" || raw.linkState === "linked"
      ? "linked"
      : raw.link_state === "failed" || raw.linkState === "failed"
        ? "failed"
        : "pending",
    linkError: typeof (raw.link_error ?? raw.linkError) === "string"
      ? String(raw.link_error ?? raw.linkError)
      : null,
  };
}

function decodePreviewResponse(raw: Record<string, unknown>): PreviewResponse {
  return {
    sources: Array.isArray(raw.sources)
      ? (raw.sources as Record<string, unknown>[]).map(decodePreviewSource)
      : [],
    found: Array.isArray(raw.found)
      ? (raw.found as Record<string, unknown>[]).map(decodePreviewFound)
      : [],
    people: Array.isArray(raw.people) ? raw.people.map(String) : [],
  };
}

export async function doorPreview(outcome: string, pasted: string): Promise<PreviewResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/projects/door/preview",
    { method: "POST", json: { outcome, pasted } },
  );
  return decodePreviewResponse(raw);
}

/** PHILO-17 U10: the same source rows, added to a project that exists
 *  (the Room's Add source): the Door's route with project_id. */
export async function doorAddSources(
  projectId: string,
  sources: DoorSourcePayload[],
  found?: { meeting_ids: string[]; note_ids: string[] },
): Promise<CreateResponse> {
  const raw = await apiFetch<Record<string, unknown>>(
    "/api/projects/door",
    { method: "POST", json: { project_id: projectId, sources, ...(found ? { found } : {}) } },
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

/* ── HS-174-07: Confluence space discovery ── */

export interface ConfluenceSpaceItem {
  key: string;
  name: string;
  type: string;
}

export interface ConfluenceDiscoveryResponse {
  state: string;
  items: ConfluenceSpaceItem[];
  errorCode: string | null;
}

function decodeConfluenceSpaceItem(raw: Record<string, unknown>): ConfluenceSpaceItem {
  return {
    key: String(raw.key ?? ""),
    name: String(raw.name ?? ""),
    type: String(raw.type ?? ""),
  };
}

function decodeConfluenceDiscoveryResponse(
  raw: Record<string, unknown>,
): ConfluenceDiscoveryResponse {
  const items = Array.isArray(raw.items)
    ? raw.items.map((i: Record<string, unknown>) => decodeConfluenceSpaceItem(i))
    : [];
  return {
    state: String(raw.state ?? ""),
    items,
    errorCode: raw.error_code != null ? String(raw.error_code) : null,
  };
}

export async function discoverConfluence(
  connectionRef: string,
  query?: string,
): Promise<ConfluenceDiscoveryResponse> {
  const params = new URLSearchParams();
  params.set("connection_ref", connectionRef);
  params.set("kind", "spaces");
  if (query) params.set("query", query);
  const qs = params.toString();
  const raw = await apiFetch<Record<string, unknown>>(
    `${PROVIDERS}/confluence/discover${qs ? `?${qs}` : ""}`,
  );
  return decodeConfluenceDiscoveryResponse(raw);
}
