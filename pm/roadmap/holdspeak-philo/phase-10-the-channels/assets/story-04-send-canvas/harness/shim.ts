/* PHILO-10-04 canvas: the wire stories 01-03 will build, STATED here.
 *
 * Every other request goes to the REAL hub unchanged (the Room, the
 * updates, their Markdown, the manual Mark delivered route, the Connections
 * read, the Jira account route). This shim adds only what is unbuilt, and it
 * derives each face state from STORED rows by the design's rules
 * (design/send-lifecycle.md); it never poses a face state.
 *
 * 1. The records (design section 1), in sessionStorage key `p10.state`:
 *    `destinations` (channel_destinations), `sends` (channel_sends), and
 *    `keys` (key_ref -> true: the stand-in for the OS keychain; the value
 *    typed into the face is DROPPED here, never stored, never returned).
 *    They survive a reload of the tab ("a restart") and nothing else.
 * 2. Destinations: GET/POST /api/channels/destinations, POST .../{id}/park,
 *    POST .../{id}/check, POST /api/channels/keys. Validation at save as
 *    design section 5 (one Jira key; owner/repo; number >= 1; an absolute
 *    folder; at most 20 addresses; a name). Edit = the face POSTs a new row
 *    with `replaces`, and the old row is parked (a row never changes).
 * 3. Sends: POST /api/channels/preview renders the update for the channel,
 *    FREEZES the transport bytes (section 3: file/GitHub Markdown; Jira plain
 *    text; Confluence JSON {title, body XHTML}; email the SendGrid request
 *    JSON, text only) and returns the READABLE preview PARSED BACK FROM THOSE
 *    BYTES with their sha256. POST /api/channels/send takes the owner's
 *    inline form {document_ref, destination_id, preview_digest} or a
 *    prepared row {send_id}; one command_id = one send (a replay answers the
 *    stored row and never dispatches again). Before the boundary: parked /
 *    changed destination, GitHub login, Atlassian sign-in, email key ->
 *    REFUSED by name, nothing runs, a prepared row stays prepared. Then the
 *    boundary (`dispatching`), then the settle. The DISPATCH itself is the
 *    stand-in: by default each channel answers its SENT proof (file path +
 *    sha256; the comment URL; the Jira/Confluence id; SendGrid's message id).
 *    POST /api/channels/sends/{id}/discard: prepared -> discarded, one wins.
 * 4. Recovery (section 4a stand-in): at load, a row still `dispatching`
 *    settles `unknown` with reason `interrupted` -- never a second dispatch.
 * 5. The history (section 1): a send that settles `sent` or `unknown` is a
 *    delivery record; the face merges them with the REAL manual rows.
 * 6. The Connections read, overlaid (stated per board in the README):
 *    GitHub `connected` as `kwork` (an isolated HOME has no gh login);
 *    one Confluence account `owner_action_required` (no add route exists).
 *    The Jira account is REAL (added through POST /api/providers/jira/
 *    connections; `never_checked`).
 *
 * Fixture faults (each stated on its board):
 *    window.__p10Next = {kind: "failed"|"unknown"|"refused", code}  the next dispatch's answer
 *    window.__p10LoseNext = true   the next send SETTLES, then its answer is lost
 *    window.__p10CrashNext = true  the next send commits the boundary, then never answers (reload = restart)
 *    window.__p10Hold = true       hold the answer until window.__p10Release()
 *    window.__p10GhLogin = "..."   the effective gh login at dispatch
 *    window.__p10Prepare({...})    the steward's / an agent's channel.prepare (unbuilt)
 *    window.__p10Move(id, folder)  the folder now resolves elsewhere (changed destination)
 */

import { authenticatedHeaders } from "@w/lib/auth";
import { useDesk } from "@w/desk/store";

type Dest = {
  id: string; name: string; channel: string; account: Record<string, unknown>; target: Record<string, unknown>;
  synced: boolean; state: "active" | "parked"; created_at: string; parked_at: string | null; checked_at: string | null;
  digest: string; resolved?: string;
};
type SendRow = {
  id: string; update_id: string; destination_id: string; destination_name: string; channel: string;
  target: Record<string, unknown>; account: Record<string, unknown>; target_digest: string; draft_revision: number;
  payload: string; payload_digest: string; preview: unknown; file_name?: string;
  prepared_by_kind: string; prepared_by_identity: string; state: string; proof: Record<string, unknown> | null;
  reason: string | null; command_id: string | null; created_at: string; settled_at: string | null;
};
type State = { destinations: Dest[]; sends: SendRow[]; keys: Record<string, boolean> };

declare global {
  interface Window {
    __p10Next?: { kind: "failed" | "unknown" | "refused"; code: string };
    __p10LoseNext?: boolean;
    __p10CrashNext?: boolean;
    __p10Hold?: boolean;
    __p10Release?: () => void;
    __p10GhLogin?: string;
    __p10Calls?: { command_id: string; send_id?: string; destination_id?: string; update_id?: string; status: number; dispatched: boolean }[];
    __p10Prepare?: (a: { update_id: string; destination_name: string; by_kind: string; by_identity: string }) => Promise<string>;
    __p10Move?: (destinationName: string, folder: string) => void;
    __p10Dump?: () => State;
  }
}

const KEY = "p10.state";
const load = (): State => {
  try { return { destinations: [], sends: [], keys: {}, ...JSON.parse(sessionStorage.getItem(KEY) || "{}") }; }
  catch { return { destinations: [], sends: [], keys: {} }; }
};
const save = (s: State) => { try { sessionStorage.setItem(KEY, JSON.stringify(s)); } catch { /* canvas only */ } };
const rid = (p: string) => `${p}_${Math.random().toString(16).slice(2, 14)}`;
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
const now = () => new Date().toISOString();
async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}
const canon = (o: unknown): string =>
  JSON.stringify(o, (_k, v) => (v && typeof v === "object" && !Array.isArray(v) ? Object.fromEntries(Object.entries(v).sort()) : v));

window.__p10Calls = [];
const realFetch = window.fetch.bind(window);

// 4. Recovery at load: never a second dispatch.
{
  const s = load();
  let changed = false;
  for (const r of s.sends) if (r.state === "dispatching") { r.state = "unknown"; r.reason = "interrupted"; r.settled_at = now(); changed = true; }
  if (changed) save(s);
}

/* ── the channel serializers (stand-ins for stories 01-03) ─────────── */

const updateMeta = new Map<string, { project_id: string; lifecycle: string; draft_revision: number }>();
const projectNames = new Map<string, string>();

async function realJson(path: string) {
  const r = await realFetch(path, { headers: authHeaders() });
  return r.ok ? r.json() : null;
}
function authHeaders(): HeadersInit {
  return authenticatedHeaders();   // the product's own credential (web/src/lib/auth.ts:36)
}
async function updateInfo(updateId: string) {
  let meta = updateMeta.get(updateId);
  const md: string = await realFetch(`/api/updates/${updateId}/markdown`, { headers: authHeaders() }).then((r) => r.text());
  if (!meta) meta = { project_id: "", lifecycle: "published", draft_revision: 1 };
  let project = projectNames.get(meta.project_id) ?? "";
  if (!project && meta.project_id) {
    const p = await realJson(`/api/projects/${meta.project_id}`);
    project = p?.project?.name ?? p?.name ?? "";
    projectNames.set(meta.project_id, project);
  }
  return { md, meta, project };
}
const slug = (s: string) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const ymd = (d = new Date()) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const MON = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
const plain = (md: string) => md
  .replace(/^#{1,6}\s*/gm, "").replace(/\*\*(.+?)\*\*/g, "$1").replace(/\*(.+?)\*/g, "$1")
  .replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1 ($2)").replace(/`([^`]+)`/g, "$1").replace(/\n{3,}/g, "\n\n").trim();
const esc = (s: string) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function xhtml(md: string): string {
  const out: string[] = []; let list = false;
  for (const line of md.split("\n")) {
    const li = line.match(/^\s*[-*]\s+(.*)$/);
    if (li) { if (!list) { out.push("<ul>"); list = true; } out.push(`<li>${esc(plain(li[1]))}</li>`); continue; }
    if (list) { out.push("</ul>"); list = false; }
    const h = line.match(/^#{1,6}\s+(.*)$/);
    if (h) out.push(`<h2>${esc(h[1])}</h2>`); else if (line.trim()) out.push(`<p>${esc(plain(line))}</p>`);
  }
  if (list) out.push("</ul>");
  return out.join("");
}
function xhtmlToText(x: string): string {
  return x.replace(/<li>/g, "• ").replace(/<\/(p|h2|li)>/g, "\n").replace(/<\/?ul>/g, "\n").replace(/<[^>]+>/g, "")
    .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&").replace(/\n{3,}/g, "\n\n").trim();
}

/** Freeze: the transport bytes. Returns the payload string (the bytes). */
function serialize(d: Dest, md: string, project: string, rev: number): string {
  const day = new Date();
  const title = `${project} · Update ${MON[day.getMonth()]} ${day.getDate()}`;
  switch (d.channel) {
    case "file":
    case "github": return md;
    case "jira": return plain(md);
    case "confluence": return JSON.stringify({ title, body: { storage: { value: xhtml(md), representation: "storage" } }, spaceId: String(d.target.space) });
    case "email": {
      const addr = (s: unknown) => String(s ?? "").split(",").map((x) => x.trim()).filter(Boolean).map((email) => ({ email }));
      const p: Record<string, unknown> = { to: addr(d.target.to) };
      const cc = addr(d.target.cc); if (cc.length) p.cc = cc;
      return JSON.stringify({
        personalizations: [p],
        from: { email: d.account.from_email, name: d.account.from_name },
        subject: title,
        content: [{ type: "text/plain", value: plain(md) }],
      });
    }
  }
  return md;
}

/** The READABLE preview, parsed back from the frozen bytes (never raw JSON or XHTML). */
function derivePreview(d: { channel: string; target: Record<string, unknown>; account: Record<string, unknown> }, payload: string, fileName: string) {
  const t = d.target, a = d.account;
  switch (d.channel) {
    case "file": return { fields: [{ label: "Folder", value: String(t.folder) }, { label: "File", value: fileName }], body_kind: "markdown", body: payload };
    case "github": return { fields: [
      { label: "Repository", value: String(t.repo) },
      { label: t.kind === "pr" ? "Pull request" : "Issue", value: `#${t.number}` },
      { label: "Account", value: `${a.login} · ${a.host}` }], body_kind: "markdown", body: payload };
    case "jira": return { fields: [
      { label: "Work item", value: String(t.key) },
      { label: "Account", value: `${a.email} · ${a.site}` }], body_kind: "text", body: payload };
    case "confluence": {
      const j = JSON.parse(payload);
      return { fields: [
        { label: "Space", value: String(j.spaceId) },
        { label: "Title", value: String(j.title) },
        { label: "Account", value: `${a.email} · ${a.site}` }], body_kind: "text", body: xhtmlToText(j.body.storage.value) };
    }
    case "email": {
      const j = JSON.parse(payload);
      const list = (x: { email: string }[] | undefined) => (x ?? []).map((e) => e.email).join(", ");
      const f = [
        { label: "From", value: `${j.from.name} <${j.from.email}>` },
        { label: "To", value: list(j.personalizations[0].to) },
      ];
      if (j.personalizations[0].cc) f.push({ label: "Cc", value: list(j.personalizations[0].cc) });
      f.push({ label: "Subject", value: String(j.subject) });
      return { fields: f, body_kind: "text", body: String(j.content[0].value) };
    }
  }
  return { fields: [], body_kind: "text", body: payload };
}

const destDigest = (d: Pick<Dest, "channel" | "account" | "target"> & { resolved?: string }) =>
  sha256(d.channel + canon(d.account) + canon(d.target) + (d.resolved ?? ""));

function connOverlay(body: { tools: Record<string, unknown>[] }) {
  for (const t of body.tools) {
    if (t.provider_id === "github" && !sessionStorage.getItem("p10.gh.real")) {
      Object.assign(t, { state: "connected", account: { login: window.__p10GhLogin ?? "kwork" }, last_checked_at: new Date(Date.now() - 5 * 60_000).toISOString() });
    }
    if (t.provider_id === "confluence" && !(t.connections as unknown[] | undefined)?.length) {
      t.connections = [{ connection_ref: "acme.atlassian.net|karol@acme.io", state: "owner_action_required",
        account: { site: "acme.atlassian.net", email: "karol@acme.io" }, recovery_hint: null, error_detail: null,
        last_checked_at: new Date(Date.now() - 3 * 3600_000).toISOString(), checked_age_seconds: null, egress_host: "acme.atlassian.net" }];
      t.state = "owner_action_required";
    }
  }
  return body;
}
let connCache: { tools: Record<string, unknown>[] } | null = null;
async function connections() {
  if (!connCache) {
    const r = await realFetch("/api/connections", { headers: authHeaders() });
    connCache = r.ok ? connOverlay(await r.json()) : { tools: [] };
  }
  return connCache;
}
async function accountState(channel: string, account: Record<string, unknown>): Promise<string> {
  const c = await connections();
  const tool = c.tools.find((t) => t.provider_id === channel);
  if (!tool) return "not_configured";
  if (channel === "github") return String(tool.state);
  const conn = (tool.connections as Record<string, unknown>[] | undefined ?? [])
    .find((x) => (x.account as Record<string, unknown>).site === account.site && (x.account as Record<string, unknown>).email === account.email);
  return conn ? String(conn.state) : "not_configured";
}

/* ── the send ─────────────────────────────────────────────────────── */

function proofOf(r: SendRow): Record<string, unknown> {
  const t = r.target, a = r.account;
  const n = String(Math.floor(1e9 + Math.random() * 8e9));
  switch (r.channel) {
    case "file": return { path: `${t.folder}/${r.file_name}`, sha256: r.payload_digest, size: new TextEncoder().encode(r.payload).length };
    case "github": return { url: `https://github.com/${t.repo}/${t.kind === "pr" ? "pull" : "issues"}/${t.number}#issuecomment-${n}` };
    case "jira": return { comment_id: n.slice(0, 6), url: `https://${a.site}/browse/${t.key}?focusedCommentId=${n.slice(0, 6)}` };
    case "confluence": return { id: n.slice(0, 8), url: `https://${a.site}/wiki/spaces/${t.space}/blog/${n.slice(0, 8)}` };
    case "email": return { message_id: `${Math.random().toString(36).slice(2, 12)}${Math.random().toString(36).slice(2, 12)}`.slice(0, 22) };
  }
  return {};
}
const pub = (r: SendRow) => { const { payload: _p, command_id: _c, target_digest: _d, file_name: _f, ...rest } = r; return rest; };
const pubDest = (d: Dest) => { const { digest: _d, resolved: _r, ...rest } = d; return rest; };

async function makeRow(d: Dest, updateId: string, byKind: string, byIdentity: string): Promise<SendRow> {
  const { md, meta, project } = await updateInfo(updateId);
  const id = rid("send");
  const fileName = `${ymd()}-${slug(project || "project")}-r${meta.draft_revision}-${id.slice(5, 13)}.md`;
  const payload = serialize(d, md, project || "Project", meta.draft_revision);
  return {
    id, update_id: updateId, destination_id: d.id, destination_name: d.name, channel: d.channel,
    target: d.target, account: d.account, target_digest: d.digest, draft_revision: meta.draft_revision,
    payload, payload_digest: await sha256(payload), preview: derivePreview(d, payload, fileName), file_name: fileName,
    prepared_by_kind: byKind, prepared_by_identity: byIdentity, state: "prepared", proof: null, reason: null,
    command_id: null, created_at: now(), settled_at: null,
  };
}

async function doSend(args: Record<string, string>): Promise<Response> {
  const cmd = String(args.command_id || "");
  const log = (status: number, dispatched: boolean, extra: Record<string, string> = {}) =>
    window.__p10Calls!.push({ command_id: cmd, send_id: args.send_id, destination_id: args.destination_id, status, dispatched, ...extra });
  let s = load();
  // One key = one send: a replay answers the stored row, never a dispatch.
  const prior = s.sends.find((r) => r.command_id === cmd);
  if (prior) { log(200, false, { replay: "true" }); return json({ send: pub(prior), replayed: true }); }
  const refuse = (code: string) => { log(409, false); return json({ success: false, outcome: "refused", error_code: code }, 409); };

  let row: SendRow;
  if (args.send_id) {
    const r = s.sends.find((x) => x.id === args.send_id);
    if (!r || r.state !== "prepared") return refuse("send_already_settled");
    row = r;
  } else {
    const d = s.destinations.find((x) => x.id === args.destination_id);
    if (!d || d.state !== "active") return refuse("destination_parked");
    row = await makeRow(d, String(args.document_ref).replace("project_update:", ""), "owner", "owner");
    if (row.payload_digest !== args.preview_digest) return refuse("preview_changed");
  }
  // Before the boundary: the destination, frozen twice (section 5).
  const dest = s.destinations.find((x) => x.id === row.destination_id);
  if (!dest || dest.state === "parked") return refuse("destination_parked");
  if ((await destDigest(dest)) !== row.target_digest || dest.digest !== row.target_digest) return refuse("destination_changed");
  // The concrete account, verified before dispatch.
  if (row.channel === "github") {
    const login = window.__p10GhLogin ?? "kwork";
    if (!login) return refuse("github_not_logged_in");
    if (login !== row.account.login) return refuse("github_identity_changed");
  }
  if (row.channel === "jira" || row.channel === "confluence") {
    if ((await accountState(row.channel, row.account)) === "owner_action_required") return refuse("atlassian_not_signed_in");
  }
  if (row.channel === "email" && !s.keys[String(row.account.key_ref)]) return refuse("email_key_missing");
  if (window.__p10Next?.kind === "refused") { const c = window.__p10Next.code; window.__p10Next = undefined; return refuse(c); }

  // The durable dispatch boundary: its own commit, before any effect.
  s = load();
  row.state = "dispatching"; row.command_id = cmd;
  const i = s.sends.findIndex((x) => x.id === row.id);
  if (i >= 0) s.sends[i] = row; else s.sends.push(row);
  save(s);
  log(0, true);
  if (window.__p10CrashNext) { window.__p10CrashNext = false; return new Promise<Response>(() => { /* the hub died */ }); }
  if (window.__p10Hold) {
    await new Promise<void>((res) => { window.__p10Release = () => { window.__p10Hold = false; res(); }; });
  } else {
    await new Promise((r) => setTimeout(r, 300));
  }
  // The settle.
  const next = window.__p10Next; window.__p10Next = undefined;
  if (next?.kind === "failed") { row.state = "failed"; row.reason = next.code; }
  else if (next?.kind === "unknown") { row.state = "unknown"; row.reason = next.code; }
  else { row.state = "sent"; row.proof = proofOf(row); }
  row.settled_at = now();
  s = load();
  s.sends = s.sends.map((x) => (x.id === row.id ? row : x));
  save(s);
  window.__p10Calls![window.__p10Calls!.length - 1].status = 200;
  if (window.__p10LoseNext) { window.__p10LoseNext = false; throw new TypeError("Failed to fetch"); }
  if (row.state === "failed") return json({ success: false, outcome: "failed", error_code: row.reason, send: pub(row) }, 409);
  return json({ send: pub(row) });
}

/* ── destinations ─────────────────────────────────────────────────── */

async function addDestination(body: Record<string, unknown>): Promise<Response> {
  const refuse = (code: string) => json({ success: false, outcome: "refused", error_code: code }, 409);
  const channel = String(body.channel);
  const t = (body.target ?? {}) as Record<string, unknown>;
  const name = String(body.name ?? "").trim();
  if (!name) return refuse("name_missing");
  let account = (body.account ?? {}) as Record<string, unknown>;
  const target: Record<string, unknown> = {};
  if (channel === "file") {
    const folder = String(t.folder ?? "").trim().replace(/\/+$/, "");
    if (!folder.startsWith("/")) return refuse("folder_not_absolute");
    target.folder = folder; account = {};
  } else if (channel === "github") {
    const repo = String(t.repo ?? "").trim();
    if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(repo)) return refuse("github_repo_invalid");
    const n = Number(t.number);
    if (!Number.isInteger(n) || n < 1) return refuse("number_invalid");
    Object.assign(target, { repo, kind: t.kind === "pr" ? "pr" : "issue", number: n });
    const login = window.__p10GhLogin ?? "kwork";          // the stand-in for `gh api user`
    if (!login) return refuse("github_not_logged_in");
    account = { host: "github.com", login };
  } else if (channel === "jira") {
    const key = String(t.key ?? "").trim();
    if (!/^[A-Z][A-Z0-9_]+-[1-9][0-9]*$/.test(key)) return refuse("jira_key_not_single");
    target.key = key;
    account = { site: account.site, email: account.email };
  } else if (channel === "confluence") {
    const space = String(t.space ?? "").trim();
    if (!/^[0-9]+$/.test(space)) return refuse("number_invalid");
    target.space = space;
    account = { site: account.site, email: account.email };
  } else if (channel === "email") {
    const list = (v: unknown) => String(v ?? "").split(",").map((x) => x.trim()).filter(Boolean);
    const to = list(t.to), cc = list(t.cc);
    const ok = (e: string) => /^[^\s@<>,]+@[^\s@<>,]+\.[^\s@<>,]+$/.test(e);
    if (!to.length || ![...to, ...cc].every(ok) || !ok(String(account.from_email ?? ""))) return refuse("address_invalid");
    if (to.length + cc.length > 20) return refuse("email_recipients_too_many");
    Object.assign(target, { to: to.join(", "), cc: cc.join(", ") });
    account = { provider: "sendgrid", from_email: account.from_email, from_name: account.from_name, key_ref: account.key_ref };
  } else return refuse("channel_unknown");
  const s = load();
  const d: Dest = {
    id: rid("dest"), name, channel, account, target, synced: channel === "file" && !!body.synced,
    state: "active", created_at: now(), parked_at: null, checked_at: null, digest: "",
  };
  d.resolved = channel === "file" ? String(target.folder) : undefined;
  d.digest = await destDigest(d);
  if (body.replaces) {
    const old = s.destinations.find((x) => x.id === body.replaces);
    if (old && old.state === "active") { old.state = "parked"; old.parked_at = now(); }
  }
  s.destinations.push(d);
  save(s);
  return json({ destination: pubDest(d) });
}

window.__p10Prepare = async ({ update_id, destination_name, by_kind, by_identity }) => {
  const s = load();
  const d = s.destinations.find((x) => x.name === destination_name && x.state === "active");
  if (!d) throw new Error(`no destination ${destination_name}`);
  const row = await makeRow(d, update_id, by_kind, by_identity);
  const s2 = load(); s2.sends.push(row); save(s2);
  return row.id;
};
window.__p10Move = (destinationName, folder) => {
  const s = load();
  const d = s.destinations.find((x) => x.name === destinationName && x.state === "active");
  if (d) { d.resolved = folder; save(s); }  // realpath now resolves elsewhere; the stored digest does not match
};
window.__p10Dump = load;
/* Harness navigation only (not a face verb): open Settings -> Connections the
 * way the Door does (web/src/features/project-room/door/useDoorController.ts:231). */
(window as unknown as { __p10OpenConnections: () => void }).__p10OpenConnections =
  () => useDesk.getState().openSurfaceWindow("configure-settings", "integrations");

/* ── the fetch hook ───────────────────────────────────────────────── */

window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  const path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0];
  const query = new URLSearchParams(url.split("?")[1] ?? "");
  const method = (init?.method || (typeof input !== "string" && !(input instanceof URL) ? input.method : "GET")).toUpperCase();
  const body = () => JSON.parse(String(init?.body ?? "{}"));

  // Learn update -> project + revision from the REAL updates read.
  const list = path.match(/^\/api\/projects\/([^/]+)\/updates$/);
  if (list && method === "GET") {
    const res = await realFetch(input, init);
    const clone = res.clone();
    try {
      const b = await clone.json();
      for (const u of b.updates ?? []) updateMeta.set(u.id, { project_id: u.project_id, lifecycle: u.lifecycle, draft_revision: Number(u.draft_revision ?? 1) });
    } catch { /* passthrough */ }
    return res;
  }
  if (path === "/api/connections" && method === "GET") {
    const res = await realFetch(input, init);
    if (!res.ok) return res;
    connCache = connOverlay(await res.json());
    return json(connCache);
  }

  if (path === "/api/channels/destinations" && method === "GET") {
    const all = query.get("include") === "parked";
    const s = load();
    const rows = s.destinations.filter((d) => all || d.state === "active").map((d) => ({
      ...pubDest(d), account: d.channel === "email" ? { ...d.account, key_present: !!s.keys[String(d.account.key_ref)] } : d.account,
    }));
    return json({ destinations: rows });
  }
  if (path === "/api/channels/destinations" && method === "POST") return addDestination(body());
  const park = path.match(/^\/api\/channels\/destinations\/([^/]+)\/park$/);
  if (park && method === "POST") {
    const s = load();
    const d = s.destinations.find((x) => x.id === park[1]);
    if (!d) return json({ error_code: "not_found" }, 404);
    if (d.state === "active") { d.state = "parked"; d.parked_at = now(); save(s); }
    return json({ destination: pubDest(d) });
  }
  const check = path.match(/^\/api\/channels\/destinations\/([^/]+)\/check$/);
  if (check && method === "POST") {
    await new Promise((r) => setTimeout(r, 250));
    const s = load();
    const d = s.destinations.find((x) => x.id === check[1]);
    if (!d) return json({ error_code: "not_found" }, 404);
    d.checked_at = now(); save(s);
    let state = "checked";
    if (d.channel === "github") state = (window.__p10GhLogin ?? "kwork") === d.account.login ? "checked" : "github_identity_changed";
    if (d.channel === "jira" || d.channel === "confluence") state = await accountState(d.channel, d.account);
    if (d.channel === "email") state = s.keys[String(d.account.key_ref)] ? "sender_verified" : "email_key_missing";
    return json({ destination: pubDest(d), state });
  }
  if (path === "/api/channels/keys" && method === "POST") {
    const b = body();
    const s = load();
    if (String(b.value ?? "").trim()) s.keys[String(b.key_ref)] = true;  // the value is dropped here
    save(s);
    return json({ key_present: !!s.keys[String(b.key_ref)] });
  }
  if (path === "/api/channels/sends" && method === "GET") {
    const ref = String(query.get("document_ref") ?? "").replace("project_update:", "");
    return json({ sends: load().sends.filter((r) => r.update_id === ref).map(pub) });
  }
  if (path === "/api/channels/preview" && method === "POST") {
    const b = body();
    const s = load();
    const d = s.destinations.find((x) => x.id === b.destination_id && x.state === "active");
    if (!d) return json({ outcome: "refused", error_code: "destination_parked" }, 409);
    const row = await makeRow(d, String(b.document_ref).replace("project_update:", ""), "owner", "owner");
    return json({ payload_digest: row.payload_digest, preview: row.preview, draft_revision: row.draft_revision });
  }
  if (path === "/api/channels/send" && method === "POST") return doSend(body());
  const discard = path.match(/^\/api\/channels\/sends\/([^/]+)\/discard$/);
  if (discard && method === "POST") {
    const s = load();
    const r = s.sends.find((x) => x.id === discard[1]);
    if (!r || r.state !== "prepared") return json({ outcome: "refused", error_code: "send_already_settled" }, 409);
    r.state = "discarded"; r.settled_at = now(); save(s);
    return json({ send: pub(r) });
  }
  return realFetch(input, init);
};

export {};
