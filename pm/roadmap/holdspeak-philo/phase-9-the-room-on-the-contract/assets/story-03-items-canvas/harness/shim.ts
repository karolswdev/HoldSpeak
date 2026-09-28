/* PHILO-9-03 canvas: the wire story 01 and story 02 will build, stated here.
 *
 * Every other request goes to the REAL hub unchanged. This shim adds only
 * what is unbuilt, and it DERIVES every effective state from stored rows by
 * a stated rule; it never poses a state.
 *
 * 1. Health and NEEDS YOU count a late milestone (story 01, F2).
 *    Rule: a milestone whose lifecycle is `planned` and whose `due_at` date is
 *    before today (local) is LATE by (today - due) days. Read from the REAL
 *    `GET /api/projects/{id}/items`. When any is late:
 *      health.assessment = "at_risk"; health.reason = "N MILESTONE(S) LATE"
 *        (only when the hub gave no reason: a stronger reason stays);
 *      needsYou.items gains one row per late milestone
 *        {source: "room", title, why: "MILESTONE · N DAYS LATE",
 *         severity: "high"}; needsYou.count += late.
 *    Nothing is late -> the hub's answer passes through unchanged.
 *
 * 2. Deliveries (story 01's table `project_update_deliveries`, story 02's
 *    route). The STORED rows live in sessionStorage (key
 *    `philo9.deliveries`), standing in for the table: they survive a reload
 *    (he leaves and returns) and nothing else.
 *    - `GET /api/projects/{id}/updates`: each update gains `deliveries`
 *      (its rows, oldest first).
 *    - `POST /api/updates/{id}/delivered` {delivered_to, command_id}:
 *        the update not published -> 409 {error_code: "update_not_published"};
 *        a known command_id with the same payload -> the ORIGINAL row (replay);
 *        a known command_id with a changed payload -> 409 idempotency_conflict;
 *        else one new row {id, update_id, project_id (from the stored update),
 *        delivered_at = now, delivered_to (trimmed, or null), operation_id}.
 *      `window.__philoHold = true` holds the answer until
 *      `window.__philoRelease()` (the pending face). Each call is logged in
 *      `window.__philoDeliveryCalls` for the facts.
 */

type Row = {
  id: string;
  update_id: string;
  project_id: string;
  delivered_at: string;
  delivered_to: string | null;
  operation_id: string;
  command_id: string;
};

declare global {
  interface Window {
    __philoHold?: boolean;
    __philoRelease?: () => void;
    __philoDeliveryCalls?: { command_id: string; delivered_to: string | null; status: number }[];
  }
}

const KEY = "philo9.deliveries";
const load = (): Row[] => {
  try { return JSON.parse(sessionStorage.getItem(KEY) || "[]"); } catch { return []; }
};
const save = (rows: Row[]) => {
  try { sessionStorage.setItem(KEY, JSON.stringify(rows)); } catch { /* canvas only */ }
};
const rid = (p: string) => `${p}_${Math.random().toString(16).slice(2, 14)}`;
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

const known = new Map<string, { project_id: string; lifecycle: string }>();
window.__philoDeliveryCalls = [];

function localDay(d: Date): number {
  return Math.round(new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime() / 86_400_000);
}
function dueDay(ymd: string): number {
  const [y, m, d] = ymd.slice(0, 10).split("-").map(Number);
  return localDay(new Date(y, m - 1, d));
}

const realFetch = window.fetch.bind(window);

window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
  const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
  const path = url.replace(/^https?:\/\/[^/]+/, "").split("?")[0];
  const method = (init?.method || (typeof input !== "string" && !(input instanceof URL) ? input.method : "GET")).toUpperCase();

  // 1. The Room read: health and NEEDS YOU count a late milestone.
  const room = path.match(/^\/api\/projects\/([^/]+)\/room$/);
  if (room && method === "GET") {
    const res = await realFetch(input, init);
    if (!res.ok) return res;
    const body = await res.json();
    const items = await realFetch(`/api/projects/${room[1]}/items?limit=200`, { headers: init?.headers })
      .then((r) => r.json()).then((r) => r.items ?? []).catch(() => []);
    const today = localDay(new Date());
    const late = (items as Record<string, string>[])
      .filter((i) => i.item_type === "milestone" && i.lifecycle === "planned" && i.due_at && dueDay(i.due_at) < today)
      .map((i) => ({ title: i.title, days: today - dueDay(i.due_at) }))
      .sort((a, b) => b.days - a.days);
    if (late.length > 0) {
      if (body.health?.state === "ok") {
        body.health.assessment = "at_risk";
        if (!body.health.reason) body.health.reason = `${late.length} MILESTONE${late.length === 1 ? "" : "S"} LATE`;
      }
      if (body.needsYou?.state === "ok") {
        const rows = late.map((l) => ({
          source: "room", title: l.title, why: `MILESTONE · ${l.days} DAY${l.days === 1 ? "" : "S"} LATE`,
          since: "", severity: "high", verb: null, url: null,
        }));
        body.needsYou.items = [...rows, ...(body.needsYou.items ?? [])];
        body.needsYou.count = Number(body.needsYou.count ?? 0) + rows.length;
      }
    }
    return json(body);
  }

  // 2a. The updates read carries its deliveries.
  const list = path.match(/^\/api\/projects\/([^/]+)\/updates$/);
  if (list && method === "GET") {
    const res = await realFetch(input, init);
    if (!res.ok) return res;
    const body = await res.json();
    const rows = load();
    for (const u of body.updates ?? []) {
      known.set(u.id, { project_id: u.project_id, lifecycle: u.lifecycle });
      u.deliveries = rows
        .filter((r) => r.update_id === u.id)
        .sort((a, b) => a.delivered_at.localeCompare(b.delivered_at))
        .map(({ command_id: _c, ...r }) => r);
    }
    return json(body);
  }

  // 2b. Mark delivered.
  const mark = path.match(/^\/api\/updates\/([^/]+)\/delivered$/);
  if (mark && method === "POST") {
    const args = JSON.parse(String(init?.body ?? "{}"));
    const to = typeof args.delivered_to === "string" && args.delivered_to.trim() ? args.delivered_to.trim() : null;
    const cmd = String(args.command_id ?? "") || rid("cmd");
    if (window.__philoHold) {
      await new Promise<void>((resolve) => { window.__philoRelease = () => { window.__philoHold = false; resolve(); }; });
    } else {
      await new Promise((r) => setTimeout(r, 250));
    }
    const upd = known.get(mark[1]);
    const log = (status: number) => window.__philoDeliveryCalls!.push({ command_id: cmd, delivered_to: to, status });
    if (!upd || upd.lifecycle !== "published") {
      log(409);
      return json({ success: false, error_code: "update_not_published" }, 409);
    }
    const rows = load();
    const prior = rows.find((r) => r.command_id === cmd);
    if (prior) {
      if (prior.delivered_to !== to || prior.update_id !== mark[1]) {
        log(409);
        return json({ success: false, error_code: "idempotency_conflict" }, 409);
      }
      log(200);
      const { command_id: _c, ...row } = prior;
      return json({ success: true, delivery: row, operation_id: row.operation_id, replayed: true });
    }
    const row: Row = {
      id: rid("pudel"), update_id: mark[1], project_id: upd.project_id,
      delivered_at: new Date().toISOString(), delivered_to: to, operation_id: rid("op"), command_id: cmd,
    };
    save([...rows, row]);
    log(200);
    const { command_id: _c, ...out } = row;
    return json({ success: true, delivery: out, operation_id: out.operation_id });
  }

  return realFetch(input, init);
};

export {};
