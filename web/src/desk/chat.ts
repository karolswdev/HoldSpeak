/** HS-83-02 — agent conversations on the web desk (the iPad's DioRecipeChat
 * posture): a persona opens to a persistent multi-turn thread; each turn runs
 * ONE hub call (`POST /api/recipes/{id}/chat`) that assembles the persona's
 * standing context + the HSM-15-12 grounding refs + the running conversation
 * server-side and persists NOTHING; harvest (`/keep`) is the human's judgment.
 *
 * Threads are DEVICE-LOCAL (`localStorage`) — the exact posture of the iPad's
 * AppStorage threads. Recipes sync; threads do not (the Phase-17 contract). */
import { groundingIsEmpty, hubGrounding, type GroundingSelection } from "./grounding";

export interface ChatTurn {
  id: string;
  role: "you" | "agent";
  text: string;
  error?: boolean;
  /** The turn's HONEST egress — the hub's answer, never inferred. */
  egress?: { scope: "local" | "cloud"; host?: string } | null;
  model?: string;
}

const THREADS_KEY = "hs.desk.chats";
const GROUNDING_KEY = "hs.desk.chatgrounding";

const readMap = <T,>(key: string): Record<string, T> => {
  try {
    return JSON.parse(localStorage.getItem(key) || "{}") || {};
  } catch {
    return {};
  }
};
const writeMap = (key: string, map: Record<string, unknown>) => {
  try {
    localStorage.setItem(key, JSON.stringify(map));
  } catch {
    /* storage full/blocked — the thread lives for the session */
  }
};

export function loadThread(personaId: string): ChatTurn[] {
  const t = readMap<ChatTurn[]>(THREADS_KEY)[personaId];
  return Array.isArray(t) ? t : [];
}

export function saveThread(personaId: string, turns: ChatTurn[]): void {
  const map = readMap<ChatTurn[]>(THREADS_KEY);
  map[personaId] = turns;
  writeMap(THREADS_KEY, map);
}

export function clearThread(personaId: string): void {
  const map = readMap<ChatTurn[]>(THREADS_KEY);
  delete map[personaId];
  writeMap(THREADS_KEY, map);
}

export function loadChatGrounding(personaId: string): GroundingSelection {
  const g = readMap<GroundingSelection>(GROUNDING_KEY)[personaId];
  return g && Array.isArray(g.meetings) ? g : { meetings: [] };
}

export function saveChatGrounding(personaId: string, sel: GroundingSelection): void {
  const map = readMap<GroundingSelection>(GROUNDING_KEY);
  if (groundingIsEmpty(sel)) delete map[personaId];
  else map[personaId] = sel;
  writeMap(GROUNDING_KEY, map);
}

export interface ChatTurnResult {
  ok: boolean;
  output: string;
  egress: { scope: "local" | "cloud"; host?: string } | null;
  model: string;
}

/** One conversational turn. The history windows server-side (12); we still
 * send only the tail to keep the request lean. */
export async function runChatTurn(
  recipeId: string,
  question: string,
  history: ChatTurn[],
  grounding: GroundingSelection,
): Promise<ChatTurnResult> {
  const fail = (output: string): ChatTurnResult => ({ ok: false, output, egress: null, model: "" });
  try {
    const res = await fetch(`/api/recipes/${encodeURIComponent(recipeId)}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        history: history.slice(-12).map((t) => ({ role: t.role, text: t.text })),
        ...(hubGrounding(grounding) ? { grounding: hubGrounding(grounding) } : {}),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const unknown = Array.isArray(data.unknown_ids) && data.unknown_ids.length
        ? ` (${data.unknown_ids.join(", ")})` : "";
      return fail(String(data.error || `HTTP ${res.status}`) + unknown);
    }
    return {
      ok: true,
      output: String(data.output || ""),
      egress: data.egress && data.egress.scope ? data.egress : null,
      model: String(data.model || ""),
    };
  } catch (e) {
    return fail(String(e));
  }
}

/** Harvest one reply onto the desk — the hub mints the run-born artifact. */
export async function keepReply(recipeId: string, question: string, output: string): Promise<string | null> {
  try {
    const res = await fetch(`/api/recipes/${encodeURIComponent(recipeId)}/keep`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, output }),
    });
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    return data.artifact_id ? String(data.artifact_id) : null;
  } catch {
    return null;
  }
}
