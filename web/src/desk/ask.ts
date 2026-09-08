/** The Ask AI atom's data layer (HSM-16-04, the web parity of HSM-16-09):
 * lasso context → pick a lens → speak/type the instruction → the hub runs it
 * → a card prints → keep it (a real synced Artifact with full lineage) or bin
 * it. The hub assembles the material from the canonical store and answers
 * with the run's HONEST egress — the badge states where THIS run went. */
import type { Primitive } from "../lib/primitives";
import { qualifiedRef, type Items } from "./api";
import { apiRequest } from "../lib/api";

/** One lasso'd card, as the ask reads it. */
export interface AskContext {
  id: string;
  kind: string;
  title: string;
  ref?: string;
}

/** The prompt presets — the iPad's `RouteLenses.all`, verbatim. */
export const ASK_LENSES: Array<{ name: string; instruction: string }> = [
  {
    name: "Summarize",
    instruction: "Summarize the following in 3–4 tight sentences. Be concrete.",
  },
  {
    name: "Action items",
    instruction:
      "Extract the concrete action items as a short list, each as 'task, owner, due' when known.",
  },
  {
    name: "Risks",
    instruction:
      "List the top risks, blockers, and open questions implied by the following. Be specific and brief.",
  },
  {
    name: "Decisions",
    instruction:
      "List the decisions that were made in the following. One line each.",
  },
  {
    name: "Draft email",
    instruction:
      "Write a short, friendly follow-up email summarizing the following and its next steps.",
  },
];

/** Resolve the selected ids to ask contexts (id + kind + live title). */
export function askContexts(items: Items, selectedIds: string[]): AskContext[] {
  const out: AskContext[] = [];
  for (const selected of selectedIds) {
    for (const kind of Object.keys(items) as Array<keyof Items>) {
      const hit = (items[kind] || []).find(
        (item: Primitive) =>
          selected === item.id || selected === qualifiedRef(kind, item.id),
      );
      if (hit) {
        out.push({
          id: hit.id,
          kind,
          ref: qualifiedRef(kind, hit.id),
          title: String(("title" in hit ? hit.title : "") || ("name" in hit ? hit.name : "") || hit.id),
        });
        break;
      }
    }
  }
  return out;
}

/** The printed card's lineage line — the iPad grammar ("3 items → Distill"). */
export function askLineageLine(context: AskContext[], lens: string): string {
  if (!context.length) return lens;
  const src =
    context.length === 1 ? context[0].title : `${context.length} items`;
  return `${src} → ${lens}`;
}

export function humanizeError(err: unknown): string {
  const status =
    err && typeof err === "object" ? (err as { status?: number }).status : undefined;
  if (status === 502 || status === 503)
    return "The model is temporarily unavailable. Try again in a moment.";
  if (status === 429)
    return "Rate limit reached. Wait a moment and try again.";
  if (status === 408)
    return "The request timed out. Try again.";
  if (
    err instanceof TypeError &&
    String(err.message).toLowerCase().includes("fetch")
  ) {
    return "Could not reach the server. Check your connection.";
  }
  return "Something went wrong. Try again.";
}

export interface AskRunResult {
  ok: boolean;
  output: string;
  /** HS-200-41: the identity this run was journaled under. The hub has always
   * returned it (the kernel's materializer stamps it onto the published
   * projection); the client simply never read it. It is the key back to a
   * durable `ask_results` row, so an answer that lands after the tab is gone
   * can be CLAIMED by a saved ask instead of paid for twice. */
  invocationId: string;
  /** HS-200-41: the hub's own BOUNDED refusal token on a failed run
   * (`code` in the /api/ask refusal body, minted by
   * `inference_targets.py:625` as `inference_target_<readiness_state>`).
   * It is the only thing a saved ask may send to `/ask-tasks/{id}/stopped`:
   * the server resolves it against its OWN live placement and quotes the
   * engine verbatim, so no sentence the browser wrote can land on a row
   * (ruling B5). Empty on a success and on a transport failure. */
  refusalCode: string;
  egress: { scope: "local" | "private_network" | "mesh" | "cloud"; host?: string } | null;
  model: string;
  profileId: string | null;
  inferenceTarget: Record<string, unknown> | null;
  actualPlacement: Record<string, unknown> | null;
  /** The lineage the hub actually read — grounding rows folded in (HS-83-01). */
  contextIds: string[];
  contextTitles: string[];
  /** HS-103-03: a quiet per-claim support signal against the cited material —
   * additive metadata only, never present when there was no source to check
   * against (a context-free ask). */
  groundingClaims: GroundingClaim[];
  /** The server's cited retrieval receipt (HS-109-04), never inferred. */
  groundingReceipt: {
    sourceRefs: string[];
    selection: string;
    matchedCount: number;
    overflowCount: number;
  } | null;
}

/** One decomposed claim from the answer, scored against the cited material. */
export interface GroundingClaim {
  text: string;
  score: number;
  label: "entailed" | "partial" | "unsupported";
  flagged: boolean;
}

/** Run the ask through the hub. Persists nothing — keep/bin is yours.
 * `grounding` (HS-83-01) ships REFERENCES — the hub hydrates from its own
 * store and refuses unknown ids by name (a 400 this returns verbatim). */
export async function runAsk(opts: {
  prompt: string;
  lens: string;
  context: AskContext[];
  grounding?: {
    meeting_ids: string[];
    artifact_ids: string[];
    refs?: string[];
    expand: "summary" | "full";
  } | null;
  /** HS-83-03: pin one of the hub's runnable models (the /api/models set);
   * an unknown name refuses 400 naming the allowed set. */
  model?: string;
  /** An in-world surface can abandon a still-pending transmission. */
  signal?: AbortSignal;
  /** HS-200-41: run under an identity a saved ask already pinned, so the
   * answer can be found again after a restart. Absent, the hub mints one. */
  invocationId?: string;
}): Promise<AskRunResult> {
  const fail = (output: string, refusalCode = ""): AskRunResult => ({
    ok: false,
    output,
    invocationId: "",
    refusalCode,
    egress: null,
    model: "",
    profileId: null,
    inferenceTarget: null,
    actualPlacement: null,
    contextIds: [],
    contextTitles: [],
    groundingClaims: [],
    groundingReceipt: null,
  });
  try {
    const res = await apiRequest("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: opts.signal,
      body: JSON.stringify({
        prompt: opts.prompt,
        lens: opts.lens,
        context: opts.context.map((c) => ({
          id: c.id,
          kind: c.kind,
          title: c.title,
          ref: c.ref || qualifiedRef(c.kind, c.id),
        })),
        ...(opts.grounding ? { grounding: opts.grounding } : {}),
        ...(opts.model ? { model: opts.model } : {}),
        ...(opts.invocationId ? { invocation_id: opts.invocationId } : {}),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      // The hub's deliberate refusals name the constraint it enforced. Keep
      // that receipt intact, including the ids it could not resolve; only
      // transport and unstructured failures need the friendly fallback.
      const error =
        data && typeof data === "object" && typeof data.error === "string"
          ? data.error
          : "";
      const unknownIds =
        data && typeof data === "object" && Array.isArray(data.unknown_ids)
          ? data.unknown_ids.map(String)
          : [];
      // The hub's bounded refusal token, kept apart from its sentence. The
      // sentence is for the owner's eye; the TOKEN is the only thing that may
      // travel back to the store (ruling B5).
      const code =
        data && typeof data === "object" && typeof data.code === "string"
          ? data.code
          : "";
      return fail(
        error
          ? unknownIds.length
            ? `${error} (${unknownIds.join(", ")})`
            : error
          : humanizeError(res),
        code,
      );
    }
    return parseAskResult(data);
  } catch (error) {
    return fail(humanizeError(error));
  }
}

/** One wire shape, parsed in ONE place. `/api/ask` and the resume route's
 *  claimed answer are the SAME payload — the kernel's published ask
 *  projection — so a resumed answer must not be parsed by a second,
 *  divergent reader (that divergence is what ruling B3 is guarding). */
export function parseAskResult(data: Record<string, any>): AskRunResult {
  return {
    ok: true,
    output: String(data.output || ""),
    invocationId: String(data.invocation_id || ""),
    refusalCode: "",
    egress: data.egress && data.egress.scope ? data.egress : null,
    model: String(data.model || ""),
    profileId: data.profile_id ? String(data.profile_id) : null,
    inferenceTarget:
      data.inference_target && typeof data.inference_target === "object"
        ? data.inference_target
        : null,
    actualPlacement:
      data.actual_placement && typeof data.actual_placement === "object"
        ? data.actual_placement
        : null,
    contextIds: Array.isArray(data.context_ids)
      ? data.context_ids.map(String)
      : [],
    contextTitles: Array.isArray(data.context_titles)
      ? data.context_titles.map(String)
      : [],
    groundingClaims: Array.isArray(data.grounding_claims)
      ? data.grounding_claims.map((c: Record<string, unknown>) => ({
          text: String(c.text || ""),
          score: Number(c.score) || 0,
          label:
            c.label === "entailed" || c.label === "partial"
              ? c.label
              : "unsupported",
          flagged: Boolean(c.flagged),
        }))
      : [],
    groundingReceipt:
      data.grounding && typeof data.grounding === "object"
        ? {
            sourceRefs: Array.isArray(data.grounding.source_refs)
              ? data.grounding.source_refs.map(String)
              : [],
            selection: String(data.grounding.selection || ""),
            matchedCount: Number(data.grounding.matched_count) || 0,
            overflowCount: Number(data.grounding.overflow_count) || 0,
          }
        : null,
};
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
    const res = await apiRequest("/api/ask/keep", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lens: opts.lens,
        prompt: opts.prompt,
        output: opts.output,
        context: opts.context.map((c) => ({
          id: c.id,
          kind: c.kind,
          ref: c.ref || qualifiedRef(c.kind, c.id),
          title: c.title,
        })),
      }),
    });
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    return data.artifact_id ? String(data.artifact_id) : null;
  } catch {
    return null;
  }
}

/* ── HS-200-41: the saved ask ──────────────────────────────────────────
 *
 * A Room ask used to survive nothing: its words lived in `useState` and
 * died with the tab. These four calls are the browser half of the durable
 * record — `project_ask_tasks`, owned by `ProjectService` (ruling B2).
 *
 * The order is the law (ruling B3): SAVE mints the invocation identity
 * server-side and writes the row BEFORE anything is dispatched, then the
 * run goes out under that same identity. So an answer that lands while the
 * tab is gone can be CLAIMED out of `ask_results` on the way back instead
 * of being paid for twice. The client never invents an identity.
 */

/** One unfinished ask, as `_ask_task_dto` writes it. Absent facts are
 *  ABSENT on the wire (A.8) — an optional field here means the store has
 *  nothing to say, and the face must draw nothing rather than a zero. */
export interface AskTask {
  id: string;
  projectId: string;
  invocationId: string;
  purpose: string;
  lens: string;
  state: "saved" | "running" | "waiting" | "failed" | "incomplete" | "accepted" | "discarded";
  savedAt: string;
  updatedAt: string;
  resumeOrder: number;
  recipeKey?: string;
  grounding?: Record<string, unknown>;
  stoppedReason?: string;
  stoppedCode?: string;
  settledAt?: string;
  /** Ruling B7, corrected by F1: the VERDICT only — `here` → `SAVED HERE`,
   *  `elsewhere` → `SAVED ON ANOTHER DESK`. The hub's machine identity is an
   *  opaque token and never crosses the wire; a face must never print one
   *  (canon `raw-ids`). Never `THIS DEVICE` either — that word is egress. */
  custody?: "here" | "elsewhere";
}

function asAskTask(row: unknown): AskTask | null {
  if (!row || typeof row !== "object") return null;
  const data = row as Record<string, unknown>;
  if (!data.id || !data.invocationId) return null;
  return data as unknown as AskTask;
}

/** Persist an unfinished ask and take back the identity it was minted
 *  under. Returns null when the hub refused — the caller still runs the
 *  ask; durability is the bonus, never the gate on doing the work. */
export async function saveAskTask(
  projectId: string,
  input: {
    purpose: string;
    lens?: string;
    recipeKey?: string;
    grounding?: Record<string, unknown> | null;
    state?: "saved" | "failed" | "incomplete";
    stoppedReason?: string;
  },
): Promise<AskTask | null> {
  try {
    const res = await apiRequest(
      `/api/projects/${encodeURIComponent(projectId)}/ask-tasks`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          purpose: input.purpose,
          lens: input.lens || "Project",
          ...(input.recipeKey ? { recipe_key: input.recipeKey } : {}),
          ...(input.grounding ? { grounding: input.grounding } : {}),
          ...(input.state ? { state: input.state } : {}),
          ...(input.stoppedReason ? { stopped_reason: input.stoppedReason } : {}),
        }),
      },
    );
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    return asAskTask(data.task);
  } catch {
    return null;
  }
}

/** The Resume projection: unfinished only, bounded, keyset-paged.
 *  `discarded` and `accepted` never appear (ruling B6). */
export async function listUnfinishedAsks(opts?: {
  projectId?: string;
  limit?: number;
  cursor?: string;
}): Promise<{ items: AskTask[]; nextCursor: string | null }> {
  const params = new URLSearchParams({ state: "unfinished" });
  if (opts?.projectId) params.set("project_id", opts.projectId);
  if (opts?.limit) params.set("limit", String(opts.limit));
  if (opts?.cursor) params.set("cursor", opts.cursor);
  try {
    const res = await apiRequest(`/api/ask-tasks?${params.toString()}`);
    if (!res.ok) return { items: [], nextCursor: null };
    const data = await res.json().catch(() => ({}));
    const items = Array.isArray(data.items)
      ? data.items.map(asAskTask).filter((t: AskTask | null): t is AskTask => t !== null)
      : [];
    return { items, nextCursor: data.next_cursor ? String(data.next_cursor) : null };
  } catch {
    return { items: [], nextCursor: null };
  }
}

/** The result of coming back to a saved ask. `claimed` means the answer
 *  was already on disk and NOTHING was dispatched — the whole point of
 *  ruling B3. `dispatched` means it genuinely had to run. */
export interface AskResumeOutcome {
  ok: boolean;
  task: AskTask | null;
  answer: AskRunResult | null;
  claimed: boolean;
  dispatched: boolean;
  /** The hub's own words when it refused; never composed here (B5). */
  error: string;
}

/** Return to one saved ask. This is also how a finished ask SETTLES: the
 *  route reads `ask_results` first, finds the answer the run just wrote,
 *  marks the task `accepted` and dispatches nothing. There is no separate
 *  accept route, and inventing a second identity to settle one would be
 *  exactly the double-spend ruling B3 forbids. */
export async function resumeAskTask(taskId: string): Promise<AskResumeOutcome> {
  const empty: AskResumeOutcome = {
    ok: false, task: null, answer: null, claimed: false, dispatched: false, error: "",
  };
  try {
    const res = await apiRequest(
      `/api/ask-tasks/${encodeURIComponent(taskId)}/resume`,
      { method: "POST", headers: { "Content-Type": "application/json" } },
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return {
        ...empty,
        error:
          data && typeof data.error === "string" && data.error
            ? data.error
            : humanizeError(res),
      };
    }
    return {
      ok: true,
      task: asAskTask(data.task),
      answer:
        data.answer && typeof data.answer === "object"
          ? parseAskResult(data.answer as Record<string, unknown>)
          : null,
      claimed: Boolean(data.claimed),
      dispatched: Boolean(data.dispatched),
      error: "",
    };
  } catch (error) {
    return { ...empty, error: humanizeError(error) };
  }
}

/** Record WHY a saved ask stopped — from the hub's own refusal CODE and
 *  nothing else.
 *
 *  `save_ask` writes the row BEFORE dispatch (ruling B3), so the ordinary
 *  failure — an engine that is not ready, seen by the browser — used to leave
 *  the row `saved` with nothing to say. This is the way back in.
 *
 *  **Send `code`, never a sentence.** The server ignores any reason a caller
 *  supplies, resolves the token against its OWN live placement, and quotes
 *  the destination verbatim only while it still observes the state the code
 *  names. That is ruling B5 enforced at the boundary rather than trusted:
 *  words in the store are the engine's, never the browser's.
 *
 *  A repeat on an already-failed row is a NO-OP, not an error — it comes back
 *  `changed: false`, and the face must not treat it as a failure. The row
 *  stays fully resumable either way: a failed ask is precisely the one the
 *  owner comes back to. */
export async function stopAskTask(
  taskId: string,
  code: string,
): Promise<{ ok: boolean; task: AskTask | null; changed: boolean }> {
  if (!code) return { ok: false, task: null, changed: false };
  try {
    const res = await apiRequest(
      `/api/ask-tasks/${encodeURIComponent(taskId)}/stopped`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code }),
      },
    );
    if (!res.ok) return { ok: false, task: null, changed: false };
    const data = await res.json().catch(() => ({}));
    return {
      ok: true,
      task: asAskTask(data.task),
      changed: Boolean(data.changed),
    };
  } catch {
    return { ok: false, task: null, changed: false };
  }
}

/** Discard is a STATE, never a delete (ruling B6). */
export async function discardAskTask(taskId: string): Promise<boolean> {
  try {
    const res = await apiRequest(
      `/api/ask-tasks/${encodeURIComponent(taskId)}/discard`,
      { method: "POST", headers: { "Content-Type": "application/json" } },
    );
    return res.ok;
  } catch {
    return false;
  }
}
