/* PHILO-11-03 canvas: the wire stories 01 and 02 will build, STATED here.
 *
 * Every other request goes to the REAL hub unchanged: the brief, the desk
 * decision, the decision records, the meetings and their aftercare digest and
 * follow-up draft, the Room, the updates and their Markdown, the Phase 10
 * destinations and every Phase 10 send of a project update.
 *
 * What this shim adds (design/document-sources.md sections 1-5), and nothing else:
 * 1. The document sources (section 1, 3): `document_ref` = `<kind>:<id>`.
 *    Each kind is RENDERED HERE from its stored record, read by id through
 *    the real hub, as story 01's renderer will: monday_brief (the brief the
 *    face shows, WITH its person sections; no Ack/Defer marks),
 *    desk_decision, decision_record, meeting_summary (summary + topics,
 *    never the transcript), meeting_digest and meeting_followup (the real
 *    aftercare reads). An unknown kind refuses `document_kind_unknown`; a
 *    meeting with no summary `no_summary`.
 * 2. The generic operations (section 4): POST /api/channels/preview and
 *    /api/channels/send take `document_ref`; GET /api/channels/sends filters
 *    by it. A project_update to a Phase 10 destination is FORWARDED to the
 *    real hub as `update_id` (the Phase 10 routes, unchanged); every other
 *    pair is answered here.
 * 3. Slack (section 5): destinations `channel: slack` {account {key_ref},
 *    target {channel_label}} kept in sessionStorage `p11.state` and merged
 *    into the real destinations read; PUT /api/channels/slack-keys/{ref}
 *    keeps only `true` (the URL typed on the face is DROPPED here, never
 *    stored, never returned); a URL that is not https://hooks.slack.com/
 *    services/... refuses `slack_webhook_invalid`. The payload is
 *    {"text": <slack text>}; the readable preview is parsed back from those
 *    bytes. Above 39,000 characters of Slack text: `payload_too_large:slack`
 *    at preview and at the inline Send, with `size` and `limit`.
 * 4. The press: the inline Send renders again and refuses `preview_changed`
 *    when the digest differs from the one he saw (Phase 10, unchanged). The
 *    DISPATCH is the stand-in: nothing leaves the machine; each channel
 *    answers its SENT proof (file path; comment URL; Jira key; post URL;
 *    message id; Slack: the time only, NO link).
 * 5. The steward's / an agent's channel.prepare: window.__p11Prepare(...).
 *
 * Fixture acts (each stated on its board):
 *    window.__p11Prepare({document_ref, destination_name, by_kind, by_identity})
 *    window.__p11Next = {kind: "failed"|"unknown", code}   the next dispatch's answer
 */

import { authenticatedHeaders } from "@w/lib/auth";

type Dest = {
  id: string; name: string; channel: string; account: Record<string, unknown>; target: Record<string, unknown>;
  synced: boolean; state: "active" | "parked"; created_at: string; parked_at: string | null;
};
type SendRow = {
  id: string; document_ref: string; destination_id: string; destination_name: string; channel: string;
  account: Record<string, unknown>; target: Record<string, unknown>; payload_digest: string; preview: Record<string, unknown>;
  prepared_by: { kind: string; identity: string }; prepare_operation_id: string | null; state: string;
  reason: string | null; proof: Record<string, unknown> | null; file_path: string | null; created_at: string;
  dispatch_started_at: string | null; settled_at: string | null; dispatch_seq: number | null; command_id: string | null;
};
type State = { slack: Dest[]; sends: SendRow[]; keys: Record<string, boolean>; seq: number };

declare global {
  interface Window {
    __p11Next?: { kind: "failed" | "unknown"; code: string };
    __p11Prepare?: (a: { document_ref: string; destination_name: string; by_kind: string; by_identity: string }) => Promise<string>;
    __p11Dump?: () => State;
  }
}

const KEY = "p11.state";
const SLACK_LIMIT = 39_000;
const load = (): State => {
  try { return { slack: [], sends: [], keys: {}, seq: 0, ...JSON.parse(sessionStorage.getItem(KEY) || "{}") }; }
  catch { return { slack: [], sends: [], keys: {}, seq: 0 }; }
};
const save = (s: State) => { try { sessionStorage.setItem(KEY, JSON.stringify(s)); } catch { /* canvas only */ } };
const rid = (p: string) => `${p}_${Math.random().toString(16).slice(2, 14)}`;
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
const refuse = (code: string, extra: Record<string, unknown> = {}, status = 409) =>
  json({ error_code: code, receipt: { state: "refused" }, ...extra }, status);
const now = () => new Date().toISOString();
async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

const realFetch = window.fetch.bind(window);
const auth = () => { const h = new Headers(authenticatedHeaders() as HeadersInit); return Object.fromEntries(h.entries()); };
async function hub<T = Record<string, unknown>>(path: string): Promise<T | null> {
  const r = await realFetch(path, { headers: auth() });
  if (!r.ok) return null;
  return (await r.json()) as T;
}

/* ── 1. the document sources (story 01's renderers, stated) ─────────── */

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
const day = (iso?: unknown) => { const d = new Date(String(iso ?? "")); return Number.isNaN(d.getTime()) ? "" : `${MONTHS[d.getMonth()]} ${d.getDate()}`; };
const isoDay = (iso?: unknown) => String(iso ?? "").slice(0, 10);

type Doc = { title: string; body: string; slug: string; label: string };
type Refused = { refused: string };

const BRIEF_SECTIONS: [string, string][] = [
  ["this_week", "This week"], ["changed", "Changed"], ["broke", "Broke"], ["waiting", "Waiting"], ["decisions", "Decisions"],
];

async function render(ref: string): Promise<Doc | Refused> {
  const i = ref.indexOf(":");
  const kind = ref.slice(0, i), id = ref.slice(i + 1);
  switch (kind) {
    case "monday_brief": {
      // The brief the face shows, with the real person overlay the route composes.
      const b = await hub<Record<string, any>>("/api/brief/latest");
      if (!b || b.id !== id) return { refused: "document_not_found" };
      const out = [`# Brief · ${b.period_label ?? ""}`, "", `${b.generated_label ?? ""}`, "", b.headline ?? ""];
      for (const [key, head] of BRIEF_SECTIONS) {
        const items = (b.sections?.[key] ?? []) as Record<string, unknown>[];
        if (!items.length) continue;
        out.push("", `## ${head}`, ...items.map((it) => `- ${it.text}${it.detail ? ` (${it.detail})` : ""}`));
      }
      const people = (b.person_sections ?? []) as Record<string, any>[];
      if (people.length) {
        out.push("", "## People");
        for (const p of people) {
          const sig: string[] = [];
          if (p.they_owe_count > 0) sig.push(`they owe ${p.they_owe_count}${p.stalest_age_days != null ? ` (${p.stalest_age_days}d)` : ""}`);
          if (p.you_owe_count > 0) sig.push(`you owe ${p.you_owe_count}`);
          if (p.agenda_backlog > 0) sig.push(`${p.agenda_backlog} agenda`);
          if (p.next_one_on_one) sig.push(`next: ${p.next_one_on_one.title || "1:1"}`);
          out.push(`- ${p.display_name}: ${sig.join(" · ")}`);
        }
      }
      return { title: `Brief ${b.period_label ?? ""}`, body: out.join("\n").trim(), slug: "brief", label: `BRIEF ${day(b.generated_at)}` };
    }
    case "desk_decision": {
      const r = await hub<{ decision: Record<string, any> }>(`/api/decisions/${encodeURIComponent(id)}`);
      const d = r?.decision;
      if (!d) return { refused: "document_not_found" };
      const out = [`# ${d.title}`, "", `Status: ${d.status}${d.deciders?.length ? ` · Deciders: ${d.deciders.join(", ")}` : ""}`];
      if (String(d.context_markdown || "").trim()) out.push("", "## Context", "", d.context_markdown);
      if (String(d.decision_markdown || "").trim()) out.push("", "## Decision", "", d.decision_markdown);
      if (String(d.consequences_markdown || "").trim()) out.push("", "## Consequences", "", d.consequences_markdown);
      if (d.alternatives?.length) out.push("", "## Alternatives", ...d.alternatives.map((a: any) => `- ${a.name}${a.reason ? `: ${a.reason}` : ""}`));
      return { title: d.title, body: out.join("\n"), slug: "decision", label: `DECISION ${id.replace(/^decision_/, "").slice(0, 6).toUpperCase()}` };
    }
    case "decision_record": {
      const r = await hub<Record<string, any>>(`/api/decision-records/${encodeURIComponent(id)}`);
      if (!r?.id) return { refused: "document_not_found" };
      const out = [`# ${r.decision_text}`, ""];
      if (r.rationale) out.push(`**Why:** ${r.rationale}`, "");
      if (r.alternatives) out.push(`**Alternatives:** ${r.alternatives}`, "");
      if (r.owner) out.push(`**Owner:** ${r.owner}`, "");
      if (r.review_date) out.push(`**Review:** ${r.review_date}`, "");
      const srcs = ((r.sources ?? []) as Record<string, any>[]).filter((s) => s.source_type === "meeting");
      if (srcs.length) out.push(`**From:** ${srcs.map((s) => s.title || s.source_ref).join(", ")}`, "");
      out.push(`**State:** ${r.lifecycle}${r.successor_id ? ` · superseded by ${r.successor_id}` : ""}`);
      return { title: r.decision_text, body: out.join("\n").trim(), slug: "decision", label: `D-${id.replace(/^record-/, "").slice(0, 6).toUpperCase()}` };
    }
    case "meeting_summary": {
      const m = await hub<Record<string, any>>(`/api/meetings/${encodeURIComponent(id)}`);
      if (!m) return { refused: "document_not_found" };
      const summary = String(m.intel?.summary ?? "").trim();
      if (!summary) return { refused: "no_summary" };
      const topics = (m.intel?.topics ?? []) as string[];
      // Never the transcript (m.segments is not read).
      const body = [`# ${m.title}`, "", isoDay(m.started_at), "", summary, ...(topics.length ? ["", `Topics: ${topics.join(", ")}`] : [])].join("\n");
      return { title: m.title, body, slug: "meeting-summary", label: `SUMMARY ${day(m.started_at)}` };
    }
    case "meeting_digest": {
      const a = await hub<Record<string, any>>(`/api/meetings/${encodeURIComponent(id)}/aftercare`);
      if (!a) return { refused: "document_not_found" };
      const out = [`# ${a.meeting_title}`, "", isoDay(a.meeting_date)];
      const dec = ((a.decisions ?? []) as Record<string, any>[]).filter((d) => d.decision);
      if (dec.length) out.push("", "## What we decided", ...dec.map((d) => `- ${d.decision}${d.rationale ? `. Why: ${d.rationale}` : ""}`));
      const open = ((a.open_items?.by_owner ?? []) as Record<string, any>[]).flatMap((g) =>
        ((g.items ?? []) as Record<string, any>[]).map((it) => `- ${g.owner || "Unassigned"}: ${it.task}${it.due ? ` (due ${it.due})` : ""}`));
      if (open.length) out.push("", "## Still open", ...open);
      if (!dec.length && !open.length) return { refused: "no_summary" };
      return { title: `${a.meeting_title}: digest`, body: out.join("\n"), slug: "meeting-digest", label: `DIGEST ${day(a.meeting_date)}` };
    }
    case "meeting_followup": {
      const f = await hub<Record<string, any>>(`/api/meetings/${encodeURIComponent(id)}/followup-draft`);
      const m = await hub<Record<string, any>>(`/api/meetings/${encodeURIComponent(id)}`);
      if (!f?.markdown) return { refused: "no_summary" };
      return { title: `${m?.title ?? ""}: follow-up`, body: String(f.markdown), slug: "meeting-followup", label: `FOLLOW-UP ${day(m?.started_at)}` };
    }
    case "project_update": {
      const r = await realFetch(`/api/updates/${encodeURIComponent(id)}/markdown`, { headers: auth() });
      if (!r.ok) return { refused: "not_published" };
      const text = await r.text();
      let md = text;
      try { const j = JSON.parse(text); md = String(j.markdown ?? j.body ?? text); } catch { /* plain text */ }
      return { title: md.split("\n")[0].replace(/^#\s*/, ""), body: md, slug: "update", label: "REV" };
    }
    case "meeting_decision":
      // A source kind with no face seat (design 6a): reachable over MCP and a thread only.
      return { refused: "document_not_found" };
    default:
      return { refused: "document_kind_unknown" };
  }
}

/* ── the channel serializers (story 01 file/GitHub/Jira/Confluence/email as
 *    Phase 10 froze them; story 02 Slack) ─────────────────────────────── */

/** Markdown -> Slack text (design section 5: headings and bold to *bold*,
 *  links to <url|text>, lists kept). */
function toSlack(md: string): string {
  return md.split("\n").map((l) => {
    const h = l.match(/^#{1,6}\s+(.*)$/);
    if (h) return `*${h[1]}*`;
    return l.replace(/\*\*(.+?)\*\*/g, "*$1*").replace(/\[([^\]]+)\]\(([^)]+)\)/g, "<$2|$1>").replace(/^- /, "• ");
  }).join("\n");
}
const plain = (md: string) => md.split("\n").map((l) => l.replace(/^#{1,6}\s+/, "").replace(/\*\*(.+?)\*\*/g, "$1")).join("\n");

function serialize(d: Dest, doc: Doc): { payload: string; preview: Record<string, unknown>; size: number } {
  switch (d.channel) {
    case "slack": {
      const text = toSlack(doc.body);
      const payload = JSON.stringify({ text });
      return { payload, preview: { text: JSON.parse(payload).text }, size: text.length };
    }
    case "jira": case "confluence": {
      const text = plain(doc.body);
      return { payload: JSON.stringify({ title: doc.title, text }), preview: { text, title: doc.title }, size: text.length };
    }
    case "email": {
      const a = d.account, t = d.target;
      const text = plain(doc.body);
      const req = { from: `${a.from_name ?? ""} <${a.from_email ?? ""}>`, to: t.to, cc: t.cc, subject: doc.title, text };
      return { payload: JSON.stringify(req), preview: req, size: text.length };
    }
    default:
      return { payload: doc.body, preview: { text: doc.body }, size: doc.body.length };
  }
}

async function destinations(): Promise<Dest[]> {
  const r = await hub<{ destinations: Dest[] }>("/api/channels/destinations");
  const s = load();
  return [...(r?.destinations ?? []), ...s.slack.filter((d) => d.state === "active")
    .map((d) => ({ ...d, account: { ...d.account, key_present: !!s.keys[String(d.account.key_ref)] } }))];
}
const isShimDest = (id: string) => load().slack.some((d) => d.id === id);

async function previewFor(ref: string, destId: string) {
  const d = (await destinations()).find((x) => x.id === destId);
  if (!d) return { refused: "destination_not_saved" } as Refused;
  const doc = await render(ref);
  if ("refused" in doc) return doc;
  const ser = serialize(d, doc);
  const digest = await sha256(ser.payload);
  return { d, doc, ...ser, digest };
}

/* ── the dispatch (the stand-in: nothing leaves this machine) ────────── */

function proofFor(r: SendRow, doc: { slug: string; label: string }): { proof: Record<string, unknown>; file_path: string | null } {
  const t = r.target, a = r.account;
  const short = r.id.replace(/^send_/, "").slice(0, 8);
  switch (r.channel) {
    case "file": {
      const path = `${t.folder}/${isoDay(now())}-${doc.slug}-${doc.label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}-${short}.md`;
      return { proof: { path }, file_path: path };
    }
    case "github": return { proof: { url: `https://${a.host ?? "github.com"}/${t.repo}/issues/${t.number}#issuecomment-${parseInt(short, 16)}` }, file_path: null };
    case "jira": return { proof: { key: t.key }, file_path: null };
    case "confluence": return { proof: { url: `/spaces/${t.space_id}/blog/${parseInt(short, 16)}` }, file_path: null };
    case "email": return { proof: { message_id: `p11.${short}`, provider: a.provider ?? "sendgrid" }, file_path: null };
    case "slack": return { proof: { posted_at: now() }, file_path: null };   // `ok`: no link
    default: return { proof: {}, file_path: null };
  }
}

function settle(row: SendRow, doc: { slug: string; label: string }) {
  const s = load();
  const r = s.sends.find((x) => x.id === row.id)!;
  s.seq += 1;
  r.state = "dispatching"; r.dispatch_started_at = now(); r.dispatch_seq = s.seq;
  const next = window.__p11Next; window.__p11Next = undefined;
  if (!s.keys[String(r.account.key_ref)] && r.channel === "slack") {
    r.state = "prepared"; r.dispatch_started_at = null; r.dispatch_seq = null; save(s);
    return { refused: "slack_webhook_missing" } as Refused;
  }
  if (next) { r.state = next.kind; r.reason = next.code; }
  else { const p = proofFor(r, doc); r.state = "sent"; r.proof = p.proof; r.file_path = p.file_path; }
  r.settled_at = now();
  save(s);
  return r;
}

/* ── the fetch hook ─────────────────────────────────────────────────── */

window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  const u = new URL(url, location.origin);
  const method = (init?.method ?? "GET").toUpperCase();
  const p = u.pathname;
  const body = (): Record<string, any> => { try { return JSON.parse(String(init?.body ?? "{}")); } catch { return {}; } };

  if (!p.startsWith("/api/channels/")) return realFetch(input, init);

  if (p === "/api/channels/destinations" && method === "GET") {
    const r = await realFetch(input, init);
    if (!r.ok) return r;
    const j = await r.json();
    const s = load();
    const all = u.searchParams.get("include_parked") === "true";
    const mine = s.slack.filter((d) => all || d.state === "active")
      .map((d) => ({ ...d, account: { ...d.account, key_present: !!s.keys[String(d.account.key_ref)] } }));
    return json({ ...j, destinations: [...j.destinations, ...mine] });
  }
  if (p === "/api/channels/destinations" && method === "POST" && body().channel === "slack") {
    const b = body();
    const s = load();
    if (!String(b.name ?? "").trim()) return refuse("destination_name_invalid", {}, 422);
    if (!s.keys[String(b.key_ref)]) return refuse("slack_webhook_missing", {}, 422);
    if (b.replaces) { const old = s.slack.find((d) => d.id === b.replaces); if (old) { old.state = "parked"; old.parked_at = now(); } }
    const d: Dest = { id: rid("dest"), name: String(b.name).trim(), channel: "slack", account: { key_ref: b.key_ref },
      target: { channel_label: String(b.channel_label ?? "").trim() }, synced: false, state: "active", created_at: now(), parked_at: null };
    s.slack.push(d); save(s);
    return json({ destination: d });
  }
  const destM = p.match(/^\/api\/channels\/destinations\/([^/]+)(\/check)?$/);
  if (destM && isShimDest(decodeURIComponent(destM[1]))) {
    const s = load();
    const d = s.slack.find((x) => x.id === decodeURIComponent(destM[1]))!;
    if (destM[2]) {
      const key = !!s.keys[String(d.account.key_ref)];
      return json({ destination: d, check: { state: key ? "webhook_ready" : "slack_webhook_missing", answered_at: null } });
    }
    if (method === "DELETE") { d.state = "parked"; d.parked_at = now(); save(s); return json({ destination: d }); }
  }
  const keyM = p.match(/^\/api\/channels\/slack-keys\/([^/]+)$/);
  if (keyM && method === "PUT") {
    const url2 = String(body().webhook_url ?? "");
    // The host rule at save (design section 5). The URL itself is dropped here.
    if (!/^https:\/\/hooks\.slack\.com\/services\/\S+$/.test(url2)) return refuse("slack_webhook_invalid", {}, 422);
    const s = load(); s.keys[decodeURIComponent(keyM[1])] = true; save(s);
    return json({ key_ref: decodeURIComponent(keyM[1]), saved: true });
  }

  if (p === "/api/channels/sends" && method === "GET") {
    const ref = u.searchParams.get("document_ref") ?? `project_update:${u.searchParams.get("update_id")}`;
    let real: SendRow[] = [];
    if (ref.startsWith("project_update:")) {
      const r = await realFetch(`/api/channels/sends?update_id=${encodeURIComponent(ref.slice(15))}`, { headers: auth() });
      if (!r.ok) return r;
      real = (await r.json()).sends ?? [];
    }
    return json({ sends: [...real, ...load().sends.filter((x) => x.document_ref === ref)] });
  }

  if (p === "/api/channels/preview" && method === "POST") {
    const b = body();
    const ref = String(b.document_ref ?? `project_update:${b.update_id}`);
    if (ref.startsWith("project_update:") && !isShimDest(b.destination_id)) {
      return realFetch("/api/channels/preview", { ...init, body: JSON.stringify({ update_id: ref.slice(15), destination_id: b.destination_id }) });
    }
    const pv = await previewFor(ref, b.destination_id);
    if ("refused" in pv) return refuse(pv.refused, {}, 422);
    if (pv.d.channel === "slack" && pv.size > SLACK_LIMIT) return refuse("payload_too_large:slack", { size: pv.size, limit: SLACK_LIMIT }, 422);
    return json({ payload_digest: pv.digest, preview: pv.preview, size: pv.size });
  }

  if (p === "/api/channels/send" && method === "POST") {
    const b = body();
    const s0 = load();
    if (b.send_id && !s0.sends.some((x) => x.id === b.send_id)) return realFetch(input, init);
    if (b.send_id) {
      const row = s0.sends.find((x) => x.id === b.send_id)!;
      if (row.state !== "prepared") return json({ send: row });
      const doc = await render(row.document_ref);
      const out = settle(row, "refused" in doc ? { slug: "doc", label: "DOC" } : doc);
      return "refused" in out ? refuse(out.refused) : json({ send: out });
    }
    const ref = String(b.document_ref ?? `project_update:${b.update_id}`);
    if (ref.startsWith("project_update:") && !isShimDest(b.destination_id)) {
      const { document_ref: _drop, ...rest } = b;
      return realFetch("/api/channels/send", { ...init, body: JSON.stringify({ ...rest, update_id: ref.slice(15) }) });
    }
    // One command id = one send: a replay answers the stored row.
    const replay = s0.sends.find((x) => x.command_id && x.command_id === b.command_id);
    if (replay) return json({ send: replay });
    const pv = await previewFor(ref, b.destination_id);
    if ("refused" in pv) return refuse(pv.refused);
    if (pv.d.channel === "slack" && pv.size > SLACK_LIMIT) return refuse("payload_too_large:slack", { size: pv.size, limit: SLACK_LIMIT });
    if (pv.digest !== b.preview_digest) return refuse("preview_changed");
    const row: SendRow = {
      id: rid("send"), document_ref: ref, destination_id: pv.d.id, destination_name: pv.d.name, channel: pv.d.channel,
      account: pv.d.account, target: pv.d.target, payload_digest: pv.digest, preview: pv.preview,
      prepared_by: { kind: "owner", identity: "owner" }, prepare_operation_id: null, state: "prepared", reason: null, proof: null,
      file_path: null, created_at: now(), dispatch_started_at: null, settled_at: null, dispatch_seq: null, command_id: String(b.command_id ?? ""),
    };
    const s = load(); s.sends.push(row); save(s);
    const out = settle(row, pv.doc);
    return "refused" in out ? refuse(out.refused) : json({ send: out });
  }

  const discM = p.match(/^\/api\/channels\/sends\/([^/]+)\/discard$/);
  if (discM && load().sends.some((x) => x.id === decodeURIComponent(discM[1]))) {
    const s = load();
    const r = s.sends.find((x) => x.id === decodeURIComponent(discM[1]))!;
    if (r.state === "prepared") { r.state = "discarded"; r.settled_at = now(); save(s); }
    return json({ send: r });
  }
  return realFetch(input, init);
};

/* ── 5. channel.prepare by the steward or an agent (stated) ─────────── */

window.__p11Prepare = async ({ document_ref, destination_name, by_kind, by_identity }) => {
  const d = (await destinations()).find((x) => x.name === destination_name);
  if (!d) throw new Error(`no destination ${destination_name}`);
  const pv = await previewFor(document_ref, d.id);
  if ("refused" in pv) throw new Error(pv.refused);
  const row: SendRow = {
    id: rid("send"), document_ref, destination_id: d.id, destination_name: d.name, channel: d.channel,
    account: d.account, target: d.target, payload_digest: pv.digest, preview: pv.preview,
    prepared_by: { kind: by_kind, identity: by_identity }, prepare_operation_id: rid("op"), state: "prepared", reason: null,
    proof: null, file_path: null, created_at: now(), dispatch_started_at: null, settled_at: null, dispatch_seq: null, command_id: null,
  };
  const s = load(); s.sends.push(row); save(s);
  return row.id;
};
window.__p11Dump = load;

