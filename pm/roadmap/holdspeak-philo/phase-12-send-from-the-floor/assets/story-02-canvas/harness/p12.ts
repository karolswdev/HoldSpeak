/* PHILO-12-02 canvas: the unbuilt wire and the proposed composition, STATED here.
 *
 * Every request not named below goes to the REAL hub unchanged: the Floor's
 * items, the desk decision, the meetings and their stored intelligence, the
 * project, its updates and its Room, the brief (`latest`), the real folder
 * destination and every real preview and send to it (the Phase 10/11 renderers
 * on main; a send to the folder writes a real file into the run's temp folder).
 *
 * THE WIRE THIS SHIM STANDS IN FOR (design/floor-send.md):
 *  W1  `artifact:<id>` (story 01, section 4): rendered HERE from the stored body
 *      the Floor already holds (the same `body_markdown` story 01's renderer
 *      reads by id), the synthesis-owned source footer left out, labelled
 *      `ARTIFACT · <TYPE>`. Preview and Send for it answer here.
 *  W2  GET /api/brief/{id} (story 01, section 5): answered from /api/brief/latest
 *      when the id matches, else 404 `brief_not_found`.
 *  W3  The stand-in destinations Slack, GitHub, Jira, Confluence and email
 *      (each channel ships on main; their accounts would need the owner's
 *      keychain and logins, which a canvas never touches). They are merged
 *      into the destinations read. Their PREVIEW body is the real hub's render
 *      of the same document (asked through the real folder destination); their
 *      SEND is answered here as SENT. NOTHING LEAVES THE MACHINE.
 *  W4  The Fact<T> reads (story 03, section 2): a meeting's summary presence
 *      (GET /api/meetings/{id}) and a project's latest published update
 *      (GET /api/projects/{id}/updates), both REAL reads; the fixture
 *      `window.__p12Hold` holds one read `loading` or makes it `failed` (H7).
 *
 * THE PROPOSED COMPOSITION (stories 03 and 04), wired through the named seats
 * in vite.config.mjs: the binding resolver (section 2, as story 01 states it),
 * `Send to ▸` in the one shared object menu and the menu bar, the Floor layer
 * (destination icons at the right edge, the brief icon), the drop rule and its
 * tag, the open paths (decision, meeting, artifact windows; the Room link; the
 * brief's exact id), the pushed pick, the touch long-press on a list row.
 */
import { createElement as h, Fragment } from "react";
import { authenticatedHeaders } from "@w/lib/auth";
import { useDesk } from "@w/desk/store";
import { openIntelligence } from "@w/desk/intelligenceNavigation";
import { qualifiedRef } from "@w/desk/api";
import { objGlow } from "@w/desk/world";
import { verbById } from "@w/desk/verbRegistry";
import { spriteUrl } from "@w/desk/sprites";
import { CHANNEL_WORD, DEST_CHANGED, requestDestinationsFocus } from "@w/features/channels/channels";

type AnyRec = Record<string, any>;
const G = globalThis as any;

/* ── shim state (sessionStorage: survives a reload within one run) ───────── */

const KEY = "p12.state";
type State = { standins: string[]; parked: string[]; sends: AnyRec[]; hold: Record<string, "loading" | "failed"> };
const load = (): State => {
  try { return { standins: [], parked: [], sends: [], hold: {}, ...JSON.parse(sessionStorage.getItem(KEY) || "{}") }; }
  catch { return { standins: [], parked: [], sends: [], hold: {} }; }
};
const save = (s: State) => { try { sessionStorage.setItem(KEY, JSON.stringify(s)); } catch { /* canvas only */ } };

const T0 = "2026-09-30T08:00:00+00:00";
const STANDINS: Record<string, AnyRec> = {
  slack: { id: "chd_p12_slack", name: "Slack #leads", channel: "slack", account: { key_ref: "slack_canvas", key_present: true }, target: { channel_label: "#leads" } },
  github: { id: "chd_p12_github", name: "Ledger cutover issue", channel: "github", account: { host: "github.com", login: "owner" }, target: { repo: "acme/payments-ledger", kind: "issue", number: 42 }, connection: { state: "connected" } },
  jira: { id: "chd_p12_jira", name: "PAY-118", channel: "jira", account: { site: "acme.atlassian.net", email: "owner@acme.test" }, target: { key: "PAY-118" }, connection: { state: "connected" } },
  confluence: { id: "chd_p12_confluence", name: "Eng updates", channel: "confluence", account: { site: "acme.atlassian.net", email: "owner@acme.test" }, target: { space_id: "ENG" }, connection: { state: "connected" } },
  slack2: { id: "chd_p12_slack2", name: "Slack #eng", channel: "slack", account: { key_ref: "slack_canvas2", key_present: true }, target: { channel_label: "#eng" } },
  github2: { id: "chd_p12_github2", name: "Rollback PR", channel: "github", account: { host: "github.com", login: "owner" }, target: { repo: "acme/payments-ledger", kind: "pr", number: 57 }, connection: { state: "connected" } },
  jira2: { id: "chd_p12_jira2", name: "PAY-121", channel: "jira", account: { site: "acme.atlassian.net", email: "owner@acme.test" }, target: { key: "PAY-121" }, connection: { state: "connected" } },
  email2: { id: "chd_p12_email2", name: "Finance list", channel: "email", account: { provider: "sendgrid", from_email: "owner@acme.test", from_name: "Owner", key_ref: "email_canvas", key_present: true }, target: { to: ["finance@acme.test"] } },
  email: { id: "chd_p12_email", name: "Leads list", channel: "email", account: { provider: "sendgrid", from_email: "owner@acme.test", from_name: "Owner", key_ref: "email_canvas", key_present: true }, target: { to: ["leads@acme.test"] } },
};
const standin = (id: string) => Object.values(STANDINS).find((d) => d.id === id);
const standinRow = (d: AnyRec, st: State): AnyRec => ({
  synced: false, created_at: T0, ...d,
  state: st.parked.includes(d.id) ? "parked" : "active", parked_at: st.parked.includes(d.id) ? T0 : null,
});

const realFetch = window.fetch.bind(window);
const auth = () => Object.fromEntries(new Headers(authenticatedHeaders() as HeadersInit).entries());
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
async function hubJson(path: string, init: RequestInit = {}): Promise<{ ok: boolean; status: number; body: AnyRec | null }> {
  const r = await realFetch(path, { ...init, headers: { ...auth(), "content-type": "application/json", ...(init.headers as AnyRec || {}) } });
  let body: AnyRec | null = null;
  try { body = await r.json(); } catch { body = null; }
  return { ok: r.ok, status: r.status, body };
}
async function sha256(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/* ── W1: the artifact source ─────────────────────────────────────────────── */

const FOOTER = /^- Source (windows|plugin runs): .*$/;
function artifactDoc(id: string): { text: string; title: string } | { refused: string } {
  const a = (useDesk.getState().items.artifact || []).find((x: AnyRec) => String(x.id) === id) as AnyRec | undefined;
  if (!a) return { refused: "document_not_found" };
  if (typeof a.bodyMarkdown !== "string") return { refused: "artifact_not_text" };
  // Only the synthesis-owned footer (its two source lines) is left out; authored text stays.
  const body = a.bodyMarkdown.split("\n").filter((l: string) => !FOOTER.test(l)).join("\n").trim();
  if (!body) return { refused: "artifact_body_missing" };
  return { title: String(a.title || "Artifact"), text: body };
}

const realFile = async (): Promise<string | null> => {
  const r = await hubJson("/api/channels/destinations");
  const d = ((r.body?.destinations ?? []) as AnyRec[]).find((x) => x.channel === "file" && x.state === "active");
  return d ? String(d.id) : null;
};

async function shimFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const url = new URL(typeof input === "string" ? input : input instanceof URL ? input.href : input.url, location.origin);
  const method = (init?.method || (input instanceof Request ? input.method : "GET")).toUpperCase();
  const path = url.pathname;
  const st = load();
  if (path === "/api/channels/destinations" && method === "GET") {
    const r = await hubJson(path + url.search);
    if (!r.ok || !r.body) return json(r.body, r.status);
    const parked = url.searchParams.get("include_parked") === "true";
    const extra = st.standins.map((id) => standinRow(standin(id)!, st)).filter((d) => parked || d.state === "active");
    return json({ ...r.body, destinations: [...(r.body.destinations ?? []), ...extra] });
  }
  if (path === "/api/channels/preview" && method === "POST") {
    const b = JSON.parse(String(init?.body || "{}"));
    const ref = String(b.document_ref || "");
    if (ref.startsWith("artifact:")) {
      const doc = artifactDoc(ref.slice("artifact:".length));
      if ("refused" in doc) return json({ success: false, code: doc.refused, error_code: doc.refused }, 400);
      // The stored body as it is; a title heading only when the body does not open with one.
      const text = /^#{1,6}\s/.test(doc.text) ? doc.text : `# ${doc.title}\n\n${doc.text}`;
      return json({ payload_digest: await sha256(text + b.destination_id), preview: { text, title: doc.title } });
    }
    if (standin(b.destination_id)) {
      const file = await realFile();
      if (!file) return json({ success: false, code: "document_not_found" }, 400);
      const r = await hubJson(path, { method: "POST", body: JSON.stringify({ document_ref: ref, destination_id: file }) });
      if (!r.ok) return json(r.body, r.status);
      // Slack's text, minimally (Phase 11 design section 5): headings and bold as *bold*, lists as bullets.
      if (standin(b.destination_id)?.channel === "slack" && r.body?.preview?.text)
        r.body.preview.text = String(r.body.preview.text).replace(/^#+\s*(.*)$/gm, "*$1*").replace(/\*\*(.+?)\*\*/g, "*$1*").replace(/^[-*] /gm, "• ");
      return json({ ...r.body, payload_digest: await sha256(String(r.body?.payload_digest) + b.destination_id) });
    }
  }
  if (path === "/api/channels/send" && method === "POST") {
    const b = JSON.parse(String(init?.body || "{}"));
    const ref = String(b.document_ref || "");
    const sd = standin(b.destination_id);
    if (sd || ref.startsWith("artifact:")) {
      const dest = sd ?? ((await hubJson("/api/channels/destinations")).body?.destinations ?? []).find((d: AnyRec) => d.id === b.destination_id);
      const at = new Date().toISOString();
      const row = {
        id: `chs_p12_${Math.random().toString(16).slice(2, 10)}`, document_ref: ref, destination_id: b.destination_id,
        destination_name: dest?.name ?? null, channel: dest?.channel ?? "file", account: dest?.account ?? {}, target: dest?.target ?? {},
        payload_digest: b.preview_digest, preview: { text: "" }, prepared_by: { kind: "owner", identity: "owner" },
        prepare_operation_id: null, state: "sent", reason: null,
        proof: dest?.channel === "file" ? { file_path: `${dest?.target?.folder ?? ""}/artifact.md` } : {},
        file_path: dest?.channel === "file" ? `${dest?.target?.folder ?? ""}/artifact.md` : null,
        created_at: at, dispatch_started_at: at, settled_at: at, dispatch_seq: st.sends.length + 1,
      };
      st.sends.push(row); save(st);
      return json({ send: row, operation_id: row.id, receipt: { state: "succeeded" } });
    }
  }
  if (path === "/api/channels/sends" && method === "GET") {
    const ref = url.searchParams.get("document_ref") || "";
    const mine = st.sends.filter((s) => !ref || s.document_ref === ref);
    if (ref.startsWith("artifact:")) return json({ sends: mine });
    const r = await hubJson(path + url.search);
    return json({ ...(r.body || {}), sends: [...((r.body?.sends ?? []) as AnyRec[]), ...mine] }, r.ok ? 200 : r.status);
  }
  const m = /^\/api\/brief\/([^/]+)$/.exec(path);
  if (m && method === "GET" && !["latest", "shelf", "generate"].includes(m[1])) {
    const r = await hubJson("/api/brief/latest");
    if (r.body && r.body.id === decodeURIComponent(m[1])) return json(r.body);
    return json({ success: false, code: "brief_not_found", error_code: "brief_not_found" }, 404);
  }
  return realFetch(input as RequestInfo, init);
}
window.fetch = shimFetch as typeof window.fetch;

/* ── caches: destinations, the brief, the facts (W4) ─────────────────────── */

let tick = 0;
const subs = new Set<() => void>();
const bump = () => { tick++; subs.forEach((f) => f()); };
const nudgeFloor = () => {
  const s = useDesk.getState();
  useDesk.setState({ items: { ...s.items } });   // the list memo and the GL scene rebuild
};

let dests: AnyRec[] = [];
async function readDests(tries = 0): Promise<void> {
  try {
    const res = await shimFetch("/api/channels/destinations", { headers: auth() });
    if (!res.ok) throw new Error(String(res.status));   // before the app has taken its token: read again
    const r = await res.json();
    dests = (r.destinations ?? []).filter((d: AnyRec) => d.state === "active");
  } catch {
    if (tries < 120) { window.setTimeout(() => void readDests(tries + 1), 500); return; }
    dests = [];
  }
  bump(); nudgeFloor();
}
window.addEventListener(DEST_CHANGED, () => void readDests());

const MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
let brief: { id: string; label: string } | null = null;
async function readBrief(tries = 0): Promise<void> {
  try {
    const r = await hubJson("/api/brief/latest");
    if (r.status === 401 && tries < 120) { window.setTimeout(() => void readBrief(tries + 1), 500); return; }
    const b = r.ok ? r.body : null;
    if (b && b.id) {
      const d = new Date(String(b.generated_at ?? b.period_end ?? ""));
      brief = { id: String(b.id), label: Number.isNaN(d.getTime()) ? "BRIEF" : `BRIEF ${MONTHS[d.getMonth()]} ${d.getDate()}` };
    } else brief = null;
  } catch { brief = null; }
  bump(); nudgeFloor();
}

type Fact<T> = { state: "unread" } | { state: "loading" } | { state: "failed" } | { state: "known"; value: T };
const facts = new Map<string, Fact<unknown>>();
const fact = (k: string): Fact<any> => facts.get(k) ?? { state: "unread" };
function read(kind: "meeting" | "project", id: string) {
  const k = `${kind}:${id}`;
  const held = load().hold[k];
  if (held) { facts.set(k, { state: held }); bump(); return; }
  const f = fact(k);
  if (f.state === "known" || f.state === "loading") return;
  facts.set(k, { state: "loading" }); bump();
  const path = kind === "meeting" ? `/api/meetings/${encodeURIComponent(id)}` : `/api/projects/${encodeURIComponent(id)}/updates`;
  void hubJson(path).then((r) => {
    if (!r.ok || !r.body) { facts.set(k, { state: "failed" }); bump(); return; }
    if (kind === "meeting") {
      const b = r.body;
      facts.set(k, { state: "known", value: !!String(b.intel?.summary ?? b.meeting?.intel?.summary ?? b.summary ?? "").trim() });
    } else {
      const pub = ((r.body.updates ?? []) as AnyRec[]).filter((u) => (u.lifecycle ?? u.status) === "published")
        .sort((a, b) => String(b.published_at ?? b.updated_at ?? "").localeCompare(String(a.published_at ?? a.updated_at ?? "")));
      facts.set(k, { state: "known", value: pub[0]?.id ?? null });
    }
    bump();
  }).catch(() => { facts.set(k, { state: "failed" }); bump(); });
}

/* ── the binding (design section 2; story 01's pure resolver, stated) ─────── */

type Input =
  | { kind: "decision" | "artifact"; id: string }
  | { kind: "meeting"; id: string; summary: Fact<boolean> }
  | { kind: "project"; id: string; latestPublishedUpdateId: Fact<string | null> }
  | { kind: "brief"; briefId: string };
type Resolved = { ref: string } | { refusal: string } | { pending: "unread" | "loading" | "failed" };
function resolve(input: Input, destination: { id: string; state: string }): Resolved {
  if (destination.state === "parked") return { refusal: "destination_parked" };
  switch (input.kind) {
    case "decision": return { ref: `desk_decision:${input.id}` };
    case "artifact": return { ref: `artifact:${input.id}` };
    case "brief": return { ref: `monday_brief:${input.briefId}` };
    case "meeting": return input.summary.state !== "known" ? { pending: input.summary.state }
      : input.summary.value ? { ref: `meeting_summary:${input.id}` } : { refusal: "no_summary" };
    case "project": return input.latestPublishedUpdateId.state !== "known" ? { pending: input.latestPublishedUpdateId.state }
      : input.latestPublishedUpdateId.value ? { ref: `project_update:${input.latestPublishedUpdateId.value}` } : { refusal: "not_published" };
  }
}

/** The Floor ref (`decision:<id>`, `intelligence:brief`, ...) as the resolver's input; null = not sendable. */
function inputOf(ref: string): Input | null {
  if (ref.includes("intelligence:brief")) return brief ? { kind: "brief", briefId: brief.id } : null;
  const i = ref.indexOf(":");
  const kind = ref.slice(0, i), id = ref.slice(i + 1);
  if (kind === "decision" || kind === "artifact") return { kind, id };
  if (kind === "meeting") { read("meeting", id); return { kind, id, summary: fact(`meeting:${id}`) }; }
  if (kind === "project") { read("project", id); return { kind, id, latestPublishedUpdateId: fact(`project:${id}`) }; }
  return null;   // notes, knowledge, personas, zones ...: nothing else on the Floor sends
}
const REFUSAL_WORD: Record<string, string> = { no_summary: "NO SUMMARY", not_published: "NO PUBLISHED UPDATE", destination_parked: "PARKED" };

/* ── the open paths (story 03) and the pushed pick ───────────────────────── */

function push(ref: string, destId: string, tries = 0) {
  if (G.__p12Pick) { G.__p12Pick(ref, destId); arrive(ref); return; }
  if (tries < 100) window.setTimeout(() => push(ref, destId, tries + 1), 100);
}

/** THE ARRIVAL (Astra canvas r1 finding 1; story 03): a pushed pick brings ITSELF into view once
 *  its preview has loaded -- the meeting's form picker if the well has one, else the picked row --
 *  clear of the host's own sticky strip (the Room's Back strip, a window head). The document's
 *  name (the window title), the picked destination, its preview and Send are then on screen with
 *  no other scroll. Nothing else moves. */
function arrive(ref: string, tries = 0) {
  // The first look waits one render: the old pick's row may still be open in the same tick.
  if (tries === 0) { window.setTimeout(() => arrive(ref, 1), 150); return; }
  const well = document.querySelector(`[data-testid=send-well][data-doc="${CSS.escape(ref)}"]`);
  const open = well?.querySelector("[data-testid=send-open]");
  const ready = open?.querySelector("[data-testid=send-preview], [data-testid=preview-refused], [data-testid=preview-failed]");
  if (!well || !open || !ready) {
    if (tries < 150) window.setTimeout(() => arrive(ref, tries + 1), 100);
    return;
  }
  window.setTimeout(() => {
    const target = (well.querySelector("[data-testid=doc-forms]") ?? open.closest("li.surface-ledger-row")) as HTMLElement | null;
    let sc: HTMLElement | null = target?.parentElement ?? null;
    while (sc && !(sc.scrollHeight > sc.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
    if (!target || !sc) { G.__p12Arrived = { ref, at: Date.now(), scrolled: false }; return; }   // nothing to scroll: already in view
    const top0 = target.getBoundingClientRect().top - sc.getBoundingClientRect().top;
    sc.scrollTop += top0;
    // Clear the host's own sticky strip: whatever covers the target's head is moved past.
    for (let i = 0; i < 4; i++) {
      const r = target.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + Math.min(40, r.width / 2), r.top + 3);
      if (!hit || target.contains(hit)) break;
      let cover: Element | null = hit;
      while (cover && cover !== sc && !/(sticky|fixed)/.test(getComputedStyle(cover).position)) cover = cover.parentElement;
      const bottom = (cover && cover !== sc ? cover : hit).getBoundingClientRect().bottom;
      sc.scrollTop -= bottom - r.top + 8;
    }
    G.__p12Arrived = { ref, at: Date.now() };
  }, 250);
}
G.__p12Arrive = arrive;
function roomLink(projectId: string, updateId: string, destinationId: string) {
  const token = `${Date.now()}-${Math.random()}`;
  const ds = useDesk.getState();
  const open = !!document.querySelector("[data-testid=room-body], [data-testid=update-list], [data-seat=update]");
  if (!open) ds.openPullout(qualifiedRef("project", projectId));
  let n = 0;
  const fire = () => {
    if (G.__p12RoomLinkTaken === token || n++ > 60) return;
    window.dispatchEvent(new CustomEvent("p12:room-link", { detail: { projectId, updateId, destinationId, token } }));
    window.setTimeout(fire, 250);
  };
  fire();
}
function openDoc(input: Input, ref: string | null, destId: string, origin?: { x: number; y: number }) {
  const ds = useDesk.getState();
  switch (input.kind) {
    case "decision": ds.openPullout(qualifiedRef("decision", input.id), origin); push(`desk_decision:${input.id}`, destId); break;
    case "artifact": ds.openPullout(qualifiedRef("artifact", input.id), origin); push(`artifact:${input.id}`, destId); break;
    // A failed read still opens the window with the pick on its Summary: a summary shows its preview; none, no well.
    case "meeting": ds.openPullout(qualifiedRef("meeting", input.id), origin); push(ref ?? `meeting_summary:${input.id}`, destId); break;
    case "brief": G.__p12BriefId = input.briefId; openIntelligence({ view: "brief" }); push(`monday_brief:${input.briefId}`, destId); break;
    case "project":
      if (ref) roomLink(input.id, ref.slice("project_update:".length), destId);
      else ds.openPullout(qualifiedRef("project", input.id), origin);   // CAN'T CHECK: the Room tells the truth
      break;
  }
}
/** A pick or a release: waits for a pending read; known absence opens nothing; failed opens the window. */
function pick(floorRef: string, dest: AnyRec, origin?: { x: number; y: number }, waited = 0) {
  const input = inputOf(floorRef);
  if (!input) return;
  const r = resolve(input, { id: dest.id, state: load().parked.includes(dest.id) ? "parked" : "active" });
  if ("ref" in r) return openDoc(input, r.ref, dest.id, origin);
  if ("refusal" in r) return;
  if (r.pending === "failed") return openDoc(input, null, dest.id, origin);
  if (waited < 600) window.setTimeout(() => pick(floorRef, dest, origin, waited + 1), 100);
}

/* ── `Send to ▸`: one shared composition (spatial, list, menu bar, Go) ───── */

/** The `Send to` row's words: the label is a string (it also names the submenu for a screen
 *  reader); a read not yet known adds its state word (H7). */
function sendToLabel(input: Input): string {
  const f = input.kind === "meeting" ? input.summary : input.kind === "project" ? input.latestPublishedUpdateId : null;
  if (f?.state === "loading" || f?.state === "unread") return "Send to · CHECKING";
  if (f?.state === "failed") return "Send to · CAN'T CHECK";
  return "Send to";
}
function sendSub(floorRef: string): AnyRec | null {
  const input = inputOf(floorRef);
  if (!input) return null;
  const f = input.kind === "meeting" ? input.summary : input.kind === "project" ? input.latestPublishedUpdateId : null;
  if (f && f.state === "known" && !f.value) return null;   // withheld where it cannot run (UX-CANON A.11)
  const rows = dests.length
    ? dests.map((d) => ({
      type: "item", id: `p12.send.${d.id}`,
      label: h(Fragment, null, d.name, h("small", { className: "quiet" }, ` · ${CHANNEL_WORD[d.channel as keyof typeof CHANNEL_WORD] ?? d.channel}`)),
      onSelect: () => pick(floorRef, d),
    }))
    : [{
      type: "item", id: "p12.send.add", label: "Add destination",
      onSelect: () => { requestDestinationsFocus(); useDesk.getState().openSurfaceWindow("configure-settings", "integrations"); },
    }];
  return { type: "sub", id: "p12.send-to", label: sendToLabel(input), entries: rows };
}
const openItem = (onSelect: () => void) => {
  const v = verbById("object.open");
  return { type: "item", id: "p12.open", label: "Open", glyph: v?.glyph, onSelect };
};
G.__p12ObjectMenu = (target: AnyRec) => {
  if (target.kind === "destination") return [openItem(() => openDestination(String(target.id)))];
  if (target.kind === "brief") { const s = sendSub("intelligence:brief"); return [openItem(() => openBrief()), ...(s ? [s] : [])]; }
  return undefined;
};
G.__p12Insert = (ref: string, e: AnyRec) => {
  if (e.type !== "item" || e.id !== "object.open") return undefined;
  const s = sendSub(ref);
  return s ? [e, s] : [e];
};
G.__p12BarSend = (selectedRef: string | null, out: AnyRec[]) => {
  if (!selectedRef) return;
  const s = sendSub(selectedRef);
  if (!s) return;
  // The same place as in the object menu: right after Open (one composition, every entry point).
  const at = out.findIndex((e) => e.type === "item" && e.id === "object.open");
  if (at >= 0) out.splice(at + 1, 0, s); else out.push(s);
};

/* ── the Floor layer (story 04): destinations at the right edge, the brief ── */

function openDestination(iconId: string) {
  const id = iconId.replace(/^destination:/, "");
  const d = dests.find((x) => x.id === id);
  G.__p12DestRow = { id, name: d?.name ?? "" };
  useDesk.getState().openSurfaceWindow("configure-settings", "integrations");
  window.setTimeout(() => window.dispatchEvent(new CustomEvent("p12:dest-row", { detail: { id, name: d?.name ?? "" } })), 400);
}
function openBrief() {
  if (!brief) return;
  G.__p12BriefId = brief.id;
  openIntelligence({ view: "brief" });
}
G.__p12OpenIcon = (o: AnyRec) => {
  if (o.kind === "destination") { openDestination(String(o.id)); return true; }
  if (o.kind === "brief") { openBrief(); return true; }
  return false;
};

const ROW = 128;   // one cell (OBJ_H 116) and its gap, in px
G.__p12FloorIcons = (input: AnyRec, placed: AnyRec[] = [], zones: AnyRec[] = []) => {
  if (input.divedZone || input.compact) return [];
  const w = Math.max(320, input.worldWidth || innerWidth);
  const hgt = (document.querySelector(".desk-world") as HTMLElement | null)?.clientHeight || innerHeight;
  // Cells taken already: every drawer (top-anchored) and every object (centred), 104 x 116 px.
  type Box = { l: number; t: number; r: number; b: number };
  const taken: Box[] = [
    ...zones.map((z) => ({ l: z.u.x * w - 52, t: z.u.y * hgt, r: z.u.x * w + 52, b: z.u.y * hgt + 116 })),
    ...placed.map((o) => ({ l: o.u.x * w - 52, t: o.u.y * hgt - 58, r: o.u.x * w + 52, b: o.u.y * hgt + 58 })),
  ];
  const free = (b: Box) => !taken.some((t) => b.l < t.r && b.r > t.l && b.t < t.b && b.b > t.t);
  // One column at the right edge (the strip right of the zone band). It TIGHTENS (128 px down to
  // 106 px a cell: a label's foot then meets the next sprite's head, never overlaps it) before it
  // wraps. Past that it wraps into the next column to the LEFT (Workbench's disk icons), and a
  // wrapped cell that would overlap a drawer or an object is skipped (icons never stack; Astra
  // canvas r1 finding 3). The first sprite clears the menu bar; the last label clears the Dock.
  const n = (brief ? 1 : 0) + dests.length;
  const top = 90, bottom = hgt - 110;   // the world runs under the Dock: the last label ends above it
  const step = n > 1 ? Math.max(106, Math.min(ROW, (bottom - top) / (n - 1))) : ROW;
  const cells: { x: number; y: number }[] = [];
  for (let c = 0; cells.length < n && c < 8; c++) {
    const cx = w - 60 - c * 112;
    for (let y = top; y <= bottom && cells.length < n; y += step) {
      const box = { l: cx - 52, t: y - 58, r: cx + 52, b: y + 58 };
      if (c > 0 && !free(box)) continue;
      cells.push({ x: cx / w, y: y / hgt });
      taken.push(box);
    }
  }
  const icons: AnyRec[] = [];
  const add = (kind: string, id: string, title: string, slot: number) => {
    const saved = input.positions[id];
    const sel = input.selectedIds.includes(id);
    icons.push({
      key: id, kind, id, selectionRef: id, title,
      u: saved && typeof saved.x === "number" ? saved : cells[slot] ?? cells[cells.length - 1],
      phase: 0, tilt: 0, scale: 1, glow: objGlow(kind === "brief" ? "note" : "chain"),
      sprite: spriteUrl(kind, id, sel ? "sel" : "rest"), small: false, selected: sel,
      dragging: input.draggingId === id, isNew: false, editing: false, attention: 0, count: null,
      fresh: false, stale: false, spriteState: null, spriteVariant: "",
    });
  };
  let slot = 0;
  if (brief) add("brief", "intelligence:brief", brief.label, slot++);
  for (const d of dests) add("destination", `destination:${d.id}`, d.name, slot++);
  return icons;
};
G.__p12ListRows = () => (brief ? [{ kind: "brief", id: "intelligence:brief", title: brief.label, ref: { kind: "brief", id: "intelligence:brief" } }] : []);

G.__p12Sprite = (kind: string, id: string) => {
  if (kind === "decision") return "p12/decision";
  if (kind === "brief") return "p12/brief";
  if (kind === "destination") {
    const d = dests.find((x) => `destination:${x.id}` === id) ?? standin(id.replace(/^destination:/, ""));
    return `p12/ch-${d?.channel ?? "file"}`;
  }
  return null;
};

/* ── the drop (story 04) ─────────────────────────────────────────────────── */

G.__p12DropRule = (target: AnyRec, dragged: AnyRec) => {
  if (target.kind !== "destination") return undefined;
  const id = String(target.id).replace(/^destination:/, "");
  const d = dests.find((x) => x.id === id);
  const input = inputOf(String(dragged.selectionRef));
  if (!d || !input) return null;   // an inert pair: no tag
  const r = resolve(input, { id, state: load().parked.includes(id) ? "parked" : "active" });
  if ("refusal" in r) return { accepts: new Set(), verb: REFUSAL_WORD[r.refusal] ?? r.refusal.toUpperCase(), action: "p12-refused" };
  return { accepts: new Set(), verb: `Preview for ${d.name}`, action: "p12-send" };
};
G.__p12Drop = (obj: AnyRec, target: AnyRec, origin: { x: number; y: number }) => {
  const d = dests.find((x) => `destination:${x.id}` === target.id);
  if (d) pick(String(obj.selectionRef), d, origin);
};

/* ── G8: the destination kept across meeting forms ───────────────────────── */

G.__p12FormMove = (meetingId: string, from: string, to: string) => {
  const was = G.__p12Picked?.(`${from}:${meetingId}`);
  if (was) { G.__p12Pick?.(`${to}:${meetingId}`, was); arrive(`${to}:${meetingId}`); }
};

/* ── the touch long-press on a list row (story 03; the GL engine has its own) ─ */

let press: { t: number; x: number; y: number; row: Element } | null = null;
let swallowClick = false;
document.addEventListener("pointerdown", (e) => {
  if (e.pointerType !== "touch") return;
  swallowClick = false;
  const row = (e.target as Element)?.closest?.(".desk-sortable-table-row");
  if (!row) return;
  const { clientX: x, clientY: y } = e;
  press = {
    x, y, row, t: window.setTimeout(() => {
      press = null; swallowClick = true;
      window.setTimeout(() => { swallowClick = false; }, 700);   // only the click the lifting finger makes
      row.dispatchEvent(new MouseEvent("contextmenu", { bubbles: true, cancelable: true, clientX: x, clientY: y }));
    }, 500),
  };
}, true);
document.addEventListener("pointermove", (e) => {
  if (press && Math.abs(e.clientX - press.x) + Math.abs(e.clientY - press.y) > 8) { clearTimeout(press.t); press = null; }
}, true);
document.addEventListener("pointerup", () => { if (press) { clearTimeout(press.t); press = null; } }, true);
document.addEventListener("click", (e) => { if (swallowClick) { swallowClick = false; e.stopPropagation(); e.preventDefault(); } }, true);

/* ── fixtures for the rig (each stated on its board) ─────────────────────── */

G.__p12Fixture = {
  standins: (names: string[]) => { const s = load(); s.standins = names.map((n) => STANDINS[n].id); save(s); return readDests(); },
  parkQuietly: (name: string) => { const s = load(); s.parked.push(STANDINS[name].id); save(s); },   // parked since the Floor's last read
  hold: (key: string, mode: "loading" | "failed" | null) => {
    const s = load(); if (mode) s.hold[key] = mode; else delete s.hold[key]; save(s);
    facts.delete(key); bump();
  },
  refresh: () => Promise.all([readDests(), readBrief()]),
  facts: () => Object.fromEntries(facts),
  sends: () => load().sends,
};

/* rig reads (no behaviour) */
G.__p12Store = () => useDesk.getState();
G.__p12Brief = () => brief?.label ?? null;
G.__p12SpriteOf = (ref: string) => { const i = ref.indexOf(":"); return spriteUrl(ref.slice(0, i), ref.slice(i + 1)); };
/** He opened this update in the Room (the Room's own Updates list, called directly). */
G.__p12OpenRoomUpdate = (projectId: string, updateId: string) => {
  const token = `open-${Date.now()}`;
  let n = 0;
  const fire = () => {
    if (G.__p12RoomLinkTaken === token || n++ > 60) return;
    window.dispatchEvent(new CustomEvent("p12:room-link", { detail: { projectId, updateId, destinationId: null, token } }));
    window.setTimeout(fire, 250);
  };
  fire();
};

void readDests();
void readBrief();
