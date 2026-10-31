// The briefing page's wire (PG-DIRECTION DIR2, DIRECTION-2026-10-31.md §11).
//
// The page is its own entry (web/briefing.html): it never imports the desk's
// auth client (src/lib/auth.ts) or src/lib/api.ts, which read the owner token.
// The token is the path segment only, never `?token=`; no cookie, no
// storage, no referrer. These three calls are its whole wire.

export type BriefingChoice = { id: string; label: string; consequence: string; primary: boolean };
export type BriefingPane = { pane: "pr" | "log" | "brief" | "text" | string; label: string; token: string };
export type BriefingOutcome = {
  words: string;
  choice?: string;
  label?: string;
  via?: string | null;
  at?: string | null;
  later_until?: string | null;
};
export type BriefingItem = {
  ref: string;
  kind: string;
  kind_words: string;
  head: string;
  question: string;
  level: string;
  since: string;
  program_title: string;
  step_ordinal: number | null;
  step_title: string;
  changed: { at: string; clock: string; line: string }[];
  choices: BriefingChoice[];
  evidence: BriefingPane[];
  state: "open" | "later" | "decided" | "gone";
  outcome?: BriefingOutcome;
};
export type LaterOption = { id: string; label: string; at: string };
export type BriefingPage = {
  package: { id: string; kind: string; head: string; expires_at: string; expires_words: string; hub: string };
  items: BriefingItem[];
  later: LaterOption[];
};
export type PaneBody =
  | { pane: string; kind: "rows"; rows: { label: string; value: string }[]; url?: string | null }
  | { pane: string; kind: "code"; text: string };

/** A refusal by name: `page_expired` (unknown, expired or revoked: no data),
 *  `answered_already`, `too_many_tries`. */
export class PageRefusal extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    readonly detail: string,
  ) {
    super(detail || code);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, credentials: "omit", cache: "no-store", referrerPolicy: "no-referrer" });
  } catch {
    throw new PageRefusal(0, "unreachable", "The hub does not answer. Try again on your tailnet.");
  }
  const body = (await response.json().catch(() => null)) as Record<string, unknown> | null;
  if (!response.ok) {
    throw new PageRefusal(response.status, String(body?.code ?? "page_failed"), String(body?.detail ?? ""));
  }
  return body as T;
}

export function readPage(token: string): Promise<BriefingPage> {
  return call<BriefingPage>(`/api/b/${token}`);
}

export function answerItem(
  token: string,
  body: { ref: string; choice: string; later?: string },
): Promise<{ item: BriefingItem }> {
  return call(`/api/b/${token}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function readPane(token: string, ref: string, pane: string): Promise<PaneBody> {
  return call<PaneBody>(`/api/b/${token}/evidence/${encodeURIComponent(ref)}/${encodeURIComponent(pane)}`);
}

/** `/b/<token>` → the token ("" when the path holds none). */
export function tokenFromPath(path: string): string {
  const found = /^\/b\/([A-Za-z0-9_-]{43})\/?$/.exec(path);
  return found ? found[1] : "";
}
