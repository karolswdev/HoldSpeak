/* PHILO-13-15 (C5) canvas: `Send to ▸` from any document window, drawn on the
 * REAL product as it is on main (the C1 frame and Chair, the C2 window menu).
 *
 * Loaded only in CANVAS_MODE=proposal with CANVAS_SHIMS containing c5. Every
 * seat (seats-c5.mjs) calls one `globalThis.__c5*` function defined here.
 * The build moves each piece into the named product file (story 15, Scope).
 *
 * WHAT IS REAL: every window, every body, the SEND well species and its
 * states, the meeting forms, the Room, the brief, the artifact, the real FILE
 * destination `Team updates` and every preview and send to it (a send writes a
 * real file into the run's scratch HOME, removed when the run ends), the reads
 * GET /api/meetings/{id} and GET /api/projects/{id}/updates.
 *
 * THE PROPOSED COMPOSITION (stated here; story 15 builds it):
 *   P1 ONE composition of `Send to ▸` from the window's own document: the
 *      window's right-button / long-press menu (first group) and the menu
 *      bar's Object menu (at 393 the Object group inside Go). Rows = the
 *      active saved destinations, `<name> · <CHANNEL>`; none = `Add
 *      destination`; withheld where the window's document cannot send.
 *   P2 the reads: a meeting's summary presence, a project's latest published
 *      update; unknown = `Send to · CHECKING`, failed = `Send to · CAN'T
 *      CHECK` (the pick still opens the well); a known absence withholds.
 *   P3 the push seam: a pick sets the well's destination in place (an open
 *      well reacts; no remount); Summary -> Digest keeps the destination.
 *   P4 the arrival: the picked row, its preview and Send come into view.
 *   P5 the artifact window: its SEND well on `artifact:<id>`; its three raw
 *      buttons are library Buttons.
 *   P7 the SENDING chip (StateChip `active`) draws its word on `--accent-text`: on main it reads 4.26:1
 *      (`--accent`), under the 4.5:1 floor C1 ratified (the build edits surface/patterns/state-chip.css).
 *   P6 offline (the hub does not answer): `Send to · OFFLINE`; the rows are
 *      the last read; a pick opens the well, which says what it cannot read.
 *
 * STAND-INS (named, so no board claims more than it shows):
 *   S1 `Slack #leads` and `PAY-118` (Jira) are stand-in destinations merged
 *      into the destinations read (their accounts need the owner's keychain
 *      and logins; a canvas never touches them). Their PREVIEW is the real
 *      hub's render of the same document through the real FILE destination;
 *      their SEND is answered HERE with the outcome the board names (SENDING,
 *      FAILED, UNKNOWN). NOTHING LEAVES THE MACHINE.
 *   S2 `none` answers the destinations read with no rows; `offline` makes
 *      every /api request fail as a dropped connection would.
 *   S3 the Meetings window's document is read from its open record's SEND
 *      well (the build reads HistoryCore's selection).
 */
import { useDesk } from "@w/desk/store";
import { frontWindowId } from "@w/desk/components/window/windowRegistry";
import { authenticatedHeaders } from "@w/lib/auth";
import { CHANNEL_WORD, requestDestinationsFocus } from "@w/features/channels/channels";
import type { WorkMenuEntry } from "@w/desk/components/DeskMenu";

type AnyRec = Record<string, any>;
const G = globalThis as any;

/* P7: the proposal's one CSS rule, injected last so it reads as the product's own. */
const p7 = document.createElement("style");
p7.id = "c5-proposal";
p7.textContent = '.desk-next .surface-state-chip[data-state="active"] { color: var(--accent-text); }';
const keepLast = () => { if (document.head.lastElementChild !== p7) document.head.appendChild(p7); };
keepLast();
new MutationObserver(keepLast).observe(document.head, { childList: true });

/* ── S1/S2: the fetch shim ─────────────────────────────────────────────── */

const T0 = "2026-10-02T08:00:00+00:00";
const STANDINS: AnyRec[] = [
  { id: "chd_c5_slack", name: "Slack #leads", channel: "slack", account: { key_ref: "slack_canvas", key_present: true }, target: { channel_label: "#leads" } },
  { id: "chd_c5_jira", name: "PAY-118", channel: "jira", account: { site: "acme.atlassian.net", email: "owner@acme.test" }, target: { key: "PAY-118" }, connection: { state: "connected" } },
];
const standin = (id: string) => STANDINS.find((d) => d.id === id);
type Mode = { standins: boolean; none: boolean; offline: boolean; outcome: Record<string, "sending" | "failed" | "unknown">; hold: Record<string, "loading" | "failed"> };
const M: Mode = { standins: true, none: false, offline: false, outcome: {}, hold: {} };
const shimSends: AnyRec[] = [];

const realFetch = window.fetch.bind(window);
const auth = () => Object.fromEntries(new Headers(authenticatedHeaders() as HeadersInit).entries());
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
async function hubJson(path: string, init: RequestInit = {}): Promise<{ ok: boolean; status: number; body: AnyRec | null }> {
  const r = await realFetch(path, { ...init, headers: { ...auth(), "content-type": "application/json", ...((init.headers as AnyRec) || {}) } });
  let body: AnyRec | null = null;
  try { body = await r.json(); } catch { body = null; }
  return { ok: r.ok, status: r.status, body };
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
  if (M.offline && path.startsWith("/api/")) throw new TypeError("Failed to fetch");
  if (path === "/api/channels/destinations" && method === "GET") {
    if (M.none) return json({ destinations: [] });
    const r = await hubJson(path + url.search);
    if (!r.ok || !r.body) return json(r.body, r.status);
    const extra = M.standins ? STANDINS.map((d) => ({ synced: false, created_at: T0, state: "active", parked_at: null, ...d })) : [];
    return json({ ...r.body, destinations: [...(r.body.destinations ?? []), ...extra] });
  }
  if (path === "/api/channels/preview" && method === "POST") {
    const b = JSON.parse(String(init?.body || "{}"));
    const sd = standin(b.destination_id);
    if (sd) {
      const file = await realFile();
      const r = await hubJson(path, { method: "POST", body: JSON.stringify({ document_ref: b.document_ref, destination_id: file }) });
      if (!r.ok) return json(r.body, r.status);
      if (sd.channel === "slack" && r.body?.preview?.text)
        r.body.preview.text = String(r.body.preview.text).replace(/^#+\s*(.*)$/gm, "*$1*").replace(/\*\*(.+?)\*\*/g, "*$1*").replace(/^[-*] /gm, "• ");
      return json({ ...r.body, payload_digest: `${String(r.body?.payload_digest)}-${b.destination_id}` });
    }
  }
  if (path === "/api/channels/send" && method === "POST") {
    const b = JSON.parse(String(init?.body || "{}"));
    const sd = standin(b.destination_id);
    if (sd) {
      const at = new Date().toISOString();
      const o = M.outcome[sd.id] ?? "sending";
      const row: AnyRec = {
        id: `chs_c5_${Math.random().toString(16).slice(2, 10)}`, document_ref: b.document_ref, destination_id: sd.id,
        destination_name: sd.name, channel: sd.channel, account: sd.account, target: sd.target,
        payload_digest: b.preview_digest, preview: { text: "" }, prepared_by: { kind: "owner", identity: "owner" },
        prepare_operation_id: null, created_at: at, dispatch_started_at: at, dispatch_seq: 900 + shimSends.length,
        state: o === "sending" ? "dispatching" : o, settled_at: o === "sending" ? null : at,
        reason: o === "failed" ? "transport_error" : o === "unknown" ? "timeout" : null, proof: {},
      };
      shimSends.push(row);
      return json({ send: row, operation_id: row.id });
    }
  }
  if (path === "/api/channels/sends" && method === "GET") {
    const ref = url.searchParams.get("document_ref") || "";
    const r = await hubJson(path + url.search);
    const mine = shimSends.filter((s) => s.document_ref === ref);
    return json({ ...(r.body || {}), sends: [...((r.body?.sends ?? []) as AnyRec[]), ...mine] }, r.ok ? 200 : r.status);
  }
  return realFetch(input as RequestInfo, init);
}
window.fetch = shimFetch as typeof window.fetch;

/* ── the destinations, as the menu reads them (the wells read their own) ── */

let dests: AnyRec[] = [];
let destsAt: string | null = null;
let destsFailed = false;
async function readDests(tries = 0): Promise<void> {
  try {
    const res = await shimFetch("/api/channels/destinations", { headers: auth() });
    if (!res.ok) throw new Error(String(res.status));
    dests = ((await res.json()).destinations ?? []).filter((d: AnyRec) => d.state === "active");
    destsFailed = false;
    const d = new Date();
    destsAt = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  } catch {
    // before the app holds its token the read answers 401: read again; offline keeps the last read (P6)
    if (!M.offline && tries < 120) { window.setTimeout(() => void readDests(tries + 1), 500); return; }
    destsFailed = true;
  }
}

/* ── P2: the reads (Fact<T>, design floor-send.md §2) ──────────────────── */

type Fact<T> = { state: "unread" } | { state: "loading" } | { state: "failed" } | { state: "known"; value: T };
const facts = new Map<string, Fact<any>>();
const fact = (k: string): Fact<any> => facts.get(k) ?? { state: "unread" };
function read(kind: "meeting" | "project", id: string): Fact<any> {
  const k = `${kind}:${id}`;
  if (M.hold[k]) { facts.set(k, { state: M.hold[k] }); return fact(k); }
  const f = fact(k);
  if (f.state === "known" || f.state === "loading") return f;
  facts.set(k, { state: "loading" });
  const path = kind === "meeting" ? `/api/meetings/${encodeURIComponent(id)}` : `/api/projects/${encodeURIComponent(id)}/updates`;
  void hubJson(path).then((r) => {
    if (!r.ok || !r.body) { facts.set(k, { state: "failed" }); return; }
    if (kind === "meeting") {
      const b = r.body;
      facts.set(k, { state: "known", value: !!String(b.intel?.summary ?? b.summary ?? "").trim() });
    } else {
      // The tie rule (Muad'Dib 2026-09-30): the greatest published_at, then the later insert (the list's order).
      const list = ((r.body.updates ?? []) as AnyRec[]).map((u, i) => ({ u, i })).filter(({ u }) => (u.lifecycle ?? u.status) === "published")
        .sort((a, b) => String(b.u.published_at ?? "").localeCompare(String(a.u.published_at ?? "")) || b.i - a.i);
      facts.set(k, { state: "known", value: list[0]?.u.id ?? null });
    }
  }).catch(() => facts.set(k, { state: "failed" }));
  return fact(k);
}

/* ── the window's own document ─────────────────────────────────────────── */

type Doc =
  | { kind: "decision" | "artifact"; id: string }
  | { kind: "meeting"; id: string; summary: Fact<boolean> }
  | { kind: "project"; id: string; update: Fact<string | null> }
  | { kind: "brief"; id: string };

function briefIdOnGlass(winId: string): string | null {
  const el = document.getElementById(winId);
  const w = el?.querySelector<HTMLElement>("[data-testid=send-well][data-doc^='monday_brief:']");
  return w ? String(w.dataset.doc).slice("monday_brief:".length) : null;
}
function docOf(winId: string | null): Doc | null {
  if (!winId) return null;
  let m = /^pullout:(decision|artifact|meeting):(.+)$/.exec(winId);
  if (m) {
    if (m[1] === "meeting") return { kind: "meeting", id: m[2], summary: read("meeting", m[2]) };
    return { kind: m[1] as "decision" | "artifact", id: m[2] };
  }
  if (winId === "pullout:intelligence:desk" || winId === "chair:brief") {
    const id = briefIdOnGlass(winId);
    return id ? { kind: "brief", id } : null;
  }
  if (winId === "surface-project-memory") {
    const scope = String((useDesk.getState() as any).windowsById?.[winId]?.scope ?? "");
    m = /^project:(.+)$/.exec(scope);
    return m ? { kind: "project", id: m[1], update: read("project", m[1]) } : null;
  }
  if (winId === "surface-meetings") {
    // S3: the open record's well names its meeting; an open record with no well has no summary.
    const el = document.getElementById(winId);
    const well = el?.querySelector<HTMLElement>("[data-testid=send-well][data-doc^='meeting_']");
    if (well) { const id = String(well.dataset.doc).replace(/^meeting_\w+:/, ""); return { kind: "meeting", id, summary: read("meeting", id) }; }
    return null;
  }
  return null;   // notes, knowledge, personas, settings ...: nothing else sends
}
const factOf = (d: Doc): Fact<any> | null => (d.kind === "meeting" ? d.summary : d.kind === "project" ? d.update : null);

/* ── P1: ONE composition of `Send to ▸` ───────────────────────────────── */

function sendToLabel(d: Doc): string {
  if (M.offline || destsFailed) return "Send to · OFFLINE";
  const f = factOf(d);
  if (f?.state === "loading" || f?.state === "unread") return "Send to · CHECKING";
  if (f?.state === "failed") return "Send to · CAN'T CHECK";
  return "Send to";
}
function sendSub(winId: string | null): WorkMenuEntry | null {
  const d = docOf(winId);
  if (!d) return null;
  const f = factOf(d);
  if ((M.offline || destsFailed) && !dests.length) return null;   // nothing known to send to
  if (f && f.state === "known" && !f.value) return null;   // withheld: a known absence (UX-CANON A.11)
  const rows: WorkMenuEntry[] = dests.length
    ? dests.map((x) => ({
      type: "item" as const, id: `c5.send.${x.id}`,
      label: `${x.name} · ${CHANNEL_WORD[x.channel as keyof typeof CHANNEL_WORD] ?? String(x.channel).toUpperCase()}`,
      onSelect: () => pick(String(winId), x),
    }))
    : M.offline || destsFailed ? []
    : [{ type: "item" as const, id: "c5.send.add", label: "Add destination",
      onSelect: () => { requestDestinationsFocus(); useDesk.getState().openSurfaceWindow("configure-settings", "integrations"); } }];
  return { type: "sub", id: "c5.send-to", label: sendToLabel(d), entries: rows };
}

/** Seat: the window's right-button / long-press menu. `Send to ▸` leads, its own group. */
G.__c5HeadMenu = (winId: string, entries: WorkMenuEntry[]): WorkMenuEntry[] => {
  void readDests();
  const s = sendSub(winId);
  return s ? [s, { type: "sep", id: "c5-sep" }, ...entries] : entries;
};
/** Seat: the menu bar. The Object menu leads with it (the front window's document); at 393
 *  the Object group rides inside Go, and it leads that group. */
G.__c5BarSend = (menuId: string, compact: boolean, out: WorkMenuEntry[]) => {
  void readDests();
  const s = sendSub(frontWindowId());
  if (!s) return;
  if (menuId === "object" && !compact) { out.unshift(s, { type: "sep", id: "c5-bar-sep" }); return; }
  if (menuId === "go" && compact) {
    const at = out.findIndex((e) => e.type === "item" && e.id.startsWith("object."));
    if (at >= 0) out.splice(at, 0, s); else out.push(s);
  }
};

/* ── P3/P4: the pick, the push seam and the arrival ───────────────────── */

/** The well of `ref` inside the window `winId` (the same document can have a second seat, e.g. The week). */
const wellIn = (winId: string, ref: string) =>
  (document.getElementById(winId) ?? document).querySelector(`[data-testid=send-well][data-doc="${CSS.escape(ref)}"]`);
function push(ref: string, destId: string, winId: string, tries = 0) {
  if (G.__c5Pick && wellIn(winId, ref)) { G.__c5Pick(ref, destId); arrive(ref, winId); return; }
  if (tries < 100) window.setTimeout(() => push(ref, destId, winId, tries + 1), 100);
}
/** The arrival: once the preview has loaded, the picked row (or the meeting's form picker)
 *  scrolls to the top of its window's body, clear of any sticky strip. Nothing else moves. */
function arrive(ref: string, winId: string, tries = 0) {
  if (tries === 0) { window.setTimeout(() => arrive(ref, winId, 1), 150); return; }
  const well = wellIn(winId, ref);
  const open = well?.querySelector("[data-testid=send-open]");
  const ready = open?.querySelector("[data-testid=send-preview], [data-testid=preview-refused], [data-testid=preview-failed]");
  if (!well || !open || !ready) { if (tries < 150) window.setTimeout(() => arrive(ref, winId, tries + 1), 100); return; }
  window.setTimeout(() => {
    const target = (well.closest("[data-testid=meeting-send-well]")?.querySelector("[data-testid=doc-forms]") ?? open.closest("li.surface-ledger-row")) as HTMLElement | null;
    let sc: HTMLElement | null = target?.parentElement ?? null;
    while (sc && !(sc.scrollHeight > sc.clientHeight + 1 && /(auto|scroll)/.test(getComputedStyle(sc).overflowY))) sc = sc.parentElement;
    if (!target || !sc) { G.__c5Arrived = { ref, at: Date.now() }; return; }
    sc.scrollTop += target.getBoundingClientRect().top - sc.getBoundingClientRect().top - 8;
    for (let i = 0; i < 4; i++) {
      const r = target.getBoundingClientRect();
      const hit = document.elementFromPoint(r.left + Math.min(40, r.width / 2), r.top + 3);
      if (!hit || target.contains(hit)) break;
      let cover: Element | null = hit;
      while (cover && cover !== sc && !/(sticky|fixed)/.test(getComputedStyle(cover).position)) cover = cover.parentElement;
      sc.scrollTop -= (cover && cover !== sc ? cover : hit).getBoundingClientRect().bottom - r.top + 8;
    }
    G.__c5Arrived = { ref, at: Date.now() };
  }, 250);
}
function roomLink(projectId: string, updateId: string, destinationId: string) {
  const token = `${Date.now()}-${Math.random()}`;
  let n = 0;
  const fire = () => {
    if (G.__c5RoomLinkTaken === token || n++ > 60) return;
    window.dispatchEvent(new CustomEvent("c5:room-link", { detail: { projectId, updateId, destinationId, token } }));
    window.setTimeout(fire, 250);
  };
  fire();
}
function pick(winId: string, dest: AnyRec, waited = 0) {
  const d = docOf(winId);
  if (!d) return;
  const f = factOf(d);
  if (f && (f.state === "loading" || f.state === "unread") && waited < 600) { window.setTimeout(() => pick(winId, dest, waited + 1), 100); return; }
  useDesk.getState().focusPanel(winId);
  switch (d.kind) {
    case "decision": push(`desk_decision:${d.id}`, dest.id, winId); break;
    case "artifact": push(`artifact:${d.id}`, dest.id, winId); break;
    case "brief": push(`monday_brief:${d.id}`, dest.id, winId); break;
    case "meeting": {
      // The window's current form (Summary unless he chose another); a failed read still opens the well.
      const well = document.getElementById(winId)?.querySelector<HTMLElement>("[data-testid=send-well][data-doc^='meeting_']");
      push(well ? String(well.dataset.doc) : `meeting_summary:${d.id}`, dest.id, winId);
      break;
    }
    case "project":
      if (d.update.state === "known" && d.update.value) roomLink(d.id, d.update.value, dest.id);
      break;   // CAN'T CHECK: the Room is open; its own Update well tells the truth
  }
}

/* G8: Summary -> Digest -> Follow-up keeps the picked destination. */
G.__c5FormMove = (meetingId: string, from: string, to: string) => {
  const was = G.__c5Picked?.(`${from}:${meetingId}`);
  const win = document.activeElement?.closest?.(".desk-window-shell")?.id ?? `pullout:meeting:${meetingId}`;
  if (was) push(`${to}:${meetingId}`, was, win);
};

/* ── the rig's hands (the canvas's own state; never a product write) ── */
G.__c5Arrive = arrive;
G.__c5 = {
  mode: (v: Partial<Mode>) => { Object.assign(M, v); facts.clear(); void readDests(); },
  outcome: (destId: string, o: "sending" | "failed" | "unknown") => { M.outcome[destId] = o; },
  hold: (key: string, how: "loading" | "failed" | null) => { if (how) M.hold[key] = how; else delete M.hold[key]; facts.delete(key); },
  readDests,
  facts: () => Object.fromEntries(facts),
  sends: () => shimSends,
  docOf: (winId: string) => docOf(winId),
};
void readDests();
