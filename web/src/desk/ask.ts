/** The Ask AI atom's data layer (HSM-16-04, the web parity of HSM-16-09):
 * lasso context → pick a lens → speak/type the instruction → the hub runs it
 * → a card prints → keep it (a real synced Artifact with full lineage) or bin
 * it. The hub assembles the material from the canonical store and answers
 * with the run's HONEST egress — the badge states where THIS run went. */
import type { DeskItem, Items } from "./api";

/** One lasso'd card, as the ask reads it. */
export interface AskContext {
  id: string;
  kind: string;
  title: string;
}

/** The prompt presets — the iPad's `RouteLenses.all`, verbatim. */
export const ASK_LENSES: Array<{ name: string; instruction: string }> = [
  { name: "Summarize", instruction: "Summarize the following in 3–4 tight sentences. Be concrete." },
  { name: "Action items", instruction: "Extract the concrete action items as a short list, each as 'task — owner — due' when known." },
  { name: "Risks", instruction: "List the top risks, blockers, and open questions implied by the following. Be specific and brief." },
  { name: "Decisions", instruction: "List the decisions that were made in the following. One line each." },
  { name: "Draft email", instruction: "Write a short, friendly follow-up email summarizing the following and its next steps." },
];

/** Resolve the selected ids to ask contexts (id + kind + live title). */
export function askContexts(items: Items, selectedIds: string[]): AskContext[] {
  const out: AskContext[] = [];
  for (const id of selectedIds) {
    for (const kind of Object.keys(items) as Array<keyof Items>) {
      const hit = (items[kind] || []).find((x: DeskItem) => x.id === id);
      if (hit) {
        out.push({ id, kind, title: String(hit.title || hit.name || id) });
        break;
      }
    }
  }
  return out;
}

/** The printed card's lineage line — the iPad grammar ("3 items → Distill"). */
export function askLineageLine(context: AskContext[], lens: string): string {
  if (!context.length) return lens;
  const src = context.length === 1 ? context[0].title : `${context.length} items`;
  return `${src} → ${lens}`;
}

export interface AskRunResult {
  ok: boolean;
  output: string;
  egress: { scope: "local" | "cloud"; host?: string } | null;
  model: string;
  profileId: string | null;
}

/** Run the ask through the hub. Persists nothing — keep/bin is yours. */
export async function runAsk(opts: {
  prompt: string;
  lens: string;
  context: AskContext[];
  profileId?: string;
}): Promise<AskRunResult> {
  try {
    const res = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt: opts.prompt,
        lens: opts.lens,
        context: opts.context.map((c) => ({ id: c.id, kind: c.kind, title: c.title })),
        ...(opts.profileId ? { profile_id: opts.profileId } : {}),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        ok: false,
        output: String(data.error || `HTTP ${res.status}`),
        egress: null, model: "", profileId: null,
      };
    }
    return {
      ok: true,
      output: String(data.output || ""),
      egress: data.egress && data.egress.scope ? data.egress : null,
      model: String(data.model || ""),
      profileId: data.profile_id ? String(data.profile_id) : null,
    };
  } catch (e) {
    return { ok: false, output: String(e), egress: null, model: "", profileId: null };
  }
}

/** Keep the printed card: the hub mints the same artifact the iPad's Keep
 * mints (via_kind "ask", every card read + the exact instruction). */
export async function keepAsk(opts: {
  lens: string;
  prompt: string;
  output: string;
  context: AskContext[];
}): Promise<string | null> {
  try {
    const res = await fetch("/api/ask/keep", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lens: opts.lens,
        prompt: opts.prompt,
        output: opts.output,
        context: opts.context.map((c) => ({ id: c.id, title: c.title })),
      }),
    });
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    return data.artifact_id ? String(data.artifact_id) : null;
  } catch {
    return null;
  }
}
