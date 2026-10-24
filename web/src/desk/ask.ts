/** Ask's data layer. The hub assembles qualified source material from its
 * canonical store and returns the run's actual egress. The window keeps each
 * answer in a thread; Save as note writes editable Markdown provenance. */
import type { Primitive } from "../lib/primitives";
import { qualifiedRef, type Items } from "./api";
import { apiRequest } from "../lib/api";
import { parseUse, type AgentUse } from "./used";
import { refOpener } from "./openObject";
import type { ProjectReturn } from "./store/types";

/** One lasso'd card, as the ask reads it. */
export interface AskContext {
  id: string;
  kind: string;
  title: string;
  ref?: string;
}

/** The exact still-owned Note version admitted before model dispatch. */
export interface AskSourceSnapshot {
  ref: string;
  thought_id: string;
  working_revision: number;
  body_sha256: string;
}

export interface AskSelectionHandoff {
  noteRef: string;
  text: string;
  /** The writer's saved body at handoff, used only to validate return. */
  body: string;
  /** CodeMirror's UTF-16 origin, independent of the optional prompt quote. */
  range: { from: number; to: number; text: string } | null;
  /** The actual window that handed this Note to Ask. */
  windowId: string | null;
  /** The source editor's scroll position at handoff. */
  scrollTop: number | null;
  /** The Note window has just saved this source. Floor selection is separate. */
  source?: AskContext;
  sourceSnapshot?: AskSourceSnapshot;
  /** The exact new-Ask request this Note handoff opened. */
  requestNonce?: number;
  /** The explicit Project row to return to; never sent as source material. */
  projectReturn?: ProjectReturn | null;
}

const ASK_SELECTION_EVENT = "holdspeak:ask-selection";
let pendingAskSelection: AskSelectionHandoff | null = null;

/** A transient Note → Ask handoff. The Note remains the canonical context. */
export function latchAskSelection(selection: AskSelectionHandoff | null): void {
  pendingAskSelection = selection && (selection.text.trim() || selection.source)
    ? { ...selection, range: selection.range ? { ...selection.range } : null, ...(selection.source ? { source: { ...selection.source } } : {}), ...(selection.sourceSnapshot ? { sourceSnapshot: { ...selection.sourceSnapshot } } : {}), ...(selection.projectReturn ? { projectReturn: { ...selection.projectReturn } } : {}) }
    : null;
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent<AskSelectionHandoff | null>(ASK_SELECTION_EVENT, { detail: pendingAskSelection }));
  }
}

export function takeAskSelection(): AskSelectionHandoff | null {
  const selection = pendingAskSelection;
  pendingAskSelection = null;
  return selection;
}

export function selectionPrompt(question: string, selection: AskSelectionHandoff | null): string {
  if (!selection?.text.trim()) return question.trim();
  const quote = selection.text.split("\n").map((line) => `> ${line}`).join("\n");
  return [question.trim(), `Selected text:\n${quote}`].filter(Boolean).join("\n\n");
}

export const ASK_SELECTION_EVENT_NAME = ASK_SELECTION_EVENT;

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
  /** Closed route reason for a failed run; empty on success. */
  reason?: string;
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
  /** Where the bytes went: the receipt's lamp word and the host. */
  egress: { scope: "local" | "private_network" | "mesh" | "cloud"; host?: string } | null;
  /** The route execution receipt id (the footer prints its last four). */
  receiptId?: string;
  /** The hub's receipt route (inference_locality.served_route): where the
   * bytes went, on a success AND on a refusal that sent them. */
  route?: unknown;
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
  /** Betterment Q4: the thread this Ask was kept in (empty on a plain ask). */
  threadId: string;
  /** Betterment Q4: what the answer read, by his names for it. */
  lookedAt: LookedAt[];
  /** Betterment Q7: what the answer's tools read, wrote and prepared (null
   *  for an engine without the desk's tools). */
  used: AgentUse | null;
  /** Betterment Q7: the answer could use the desk's tools. */
  deskTools: boolean;
  /** Betterment Q7: the answer's message id in its thread. */
  answerId?: string;
}

/** Betterment Q4: one record an answer read, as a link. */
export interface LookedAt {
  ref: string;
  title: string;
}

/** One decomposed claim from the answer, scored against the cited material. */
export interface GroundingClaim {
  text: string;
  score: number;
  label: "entailed" | "partial" | "unsupported";
  flagged: boolean;
}

/** Run Ask through the hub; thread mode keeps the answered exchange.
 * `grounding` (HS-83-01) ships REFERENCES — the hub hydrates from its own
 * store and refuses unknown ids by name (a 400 this returns verbatim). */
export async function runAsk(opts: {
  prompt: string;
  lens: string;
  context: AskContext[];
  sourceSnapshot?: AskSourceSnapshot;
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
  /** Betterment Q4: keep this Ask as a thread. A thread id continues that
   * thread (a follow-up); `true` starts a new one. */
  thread?: string | true;
}): Promise<AskRunResult> {
  const fail = (output: string, refusalCode = "", route: unknown = null, reason = ""): AskRunResult => {
    const result: AskRunResult = {
      ok: false,
      output,
      route,
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
      threadId: "",
      lookedAt: [],
      used: null,
      deskTools: false,
    };
    if (reason) result.reason = reason;
    return result;
  };
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
        ...(opts.sourceSnapshot ? { source_snapshot: opts.sourceSnapshot } : {}),
        ...(opts.model ? { model: opts.model } : {}),
        ...(opts.invocationId ? { invocation_id: opts.invocationId } : {}),
        ...(opts.thread === true ? { thread: true } : opts.thread ? { thread_id: opts.thread } : {}),
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
      const reason =
        data && typeof data === "object" && typeof data.reason === "string"
          ? data.reason
          : "did_not_answer";
      return fail(
        error
          ? unknownIds.length
            ? `${error} (${unknownIds.join(", ")})`
            : error
          : humanizeError(res),
        code,
        data && typeof data === "object" ? data.route ?? null : null,
        reason,
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
    receiptId: String(data.route_execution_receipt?.execution_id || ""),
    route: data.route ?? null,
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
    threadId: String(data.thread_id || ""),
    lookedAt: Array.isArray(data.looked_at)
      ? data.looked_at
          .filter((row: Record<string, unknown>) => row && typeof row.ref === "string" && row.ref.includes(":"))
          .map((row: Record<string, unknown>) => ({ ref: String(row.ref), title: sourceName(String(row.ref), String(row.title || "")) }))
      : [],
    used: parseUse(data.used),
    deskTools: data.tools === "desk",
    answerId: String(data.message_ids?.answer || ""),
};
}

/* ── Betterment Q4: one Ask window over a thread ───────────────────── */

const KIND_WORDS: Record<string, string> = {
  meeting: "A meeting", note: "A note", artifact: "A document", thread: "A conversation",
  project: "A project", person: "A person", people: "A person", decision: "A decision",
  desk_decision: "A decision", kb: "A collection", directory: "A drawer", zone: "A drawer",
};

/** His name for a source; a word for its kind when the only name is an id
 * (no raw ids on the face). */
export function sourceName(ref: string, title: string): string {
  const [kind, rest = ""] = ref.split(/:(.*)/s);
  const id = rest.split("#")[0];
  const name = title.replace(/\s+/g, " ").trim();
  if (!name || name === ref || name === rest || name === id || /^(th|tm|tr|tp)_[0-9a-f]+$/i.test(name)) {
    return KIND_WORDS[kind] || "A source";
  }
  return name;
}

/** One question and its answer in the Ask window. */
export interface AskTurn {
  /** The answer's message id (or a local key before the hub names it). */
  key: string;
  question: string;
  answer: string;
  lookedAt: LookedAt[];
  /** Betterment Q7: what its tools wrote and prepared (Looked at is above). */
  used?: AgentUse | null;
}

/** Betterment Q7: Looked at with what the tools read after it, once each. */
export function withToolReads(lookedAt: LookedAt[], used: AgentUse | null | undefined): LookedAt[] {
  const rows = [...lookedAt];
  for (const row of used?.looked_at ?? []) {
    if (!rows.some((known) => known.ref === row.ref)) rows.push({ ref: row.ref, title: sourceName(row.ref, row.label) });
  }
  return rows;
}

/** Betterment Q7: can the Answers engine use the desk's tools? */
export async function readAskEngineTools(): Promise<boolean> {
  try {
    const res = await apiRequest("/api/ask/engine");
    if (!res.ok) return false;
    const data = await res.json().catch(() => ({}));
    return data?.tools === "desk";
  } catch {
    return false;
  }
}

/** Betterment Q7: Make it a task. The same write the agent makes
 *  (`door.add_item`, through the thread's `/todo`): the task text is the
 *  answer's first line. Returns the task's ref, or null. */
export async function makeTaskFromAnswer(threadId: string, answer: string): Promise<{ ref: string; label: string } | null> {
  const line = answer
    .split("\n")
    .map((text) => text.replace(/^[\s>#*\-•]+/, "").replace(/[*_`]/g, "").trim())
    .find(Boolean) || "";
  const text = line.length > 140 ? `${line.slice(0, 139).trimEnd()}…` : line;
  if (!threadId || !text) return null;
  try {
    const res = await apiRequest(`/api/threads/${encodeURIComponent(threadId)}/todo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    const id = String(data?.result?.id || "");
    return id && data?.status === "ok" ? { ref: `action_item:${id}`, label: text } : null;
  } catch {
    return null;
  }
}

/** Betterment Q7: his press on a call the desk's tool loop holds. */
export async function decideHeldCall(threadId: string, callId: string, decision: "approve" | "deny"): Promise<boolean> {
  try {
    const res = await apiRequest(`/api/threads/${encodeURIComponent(threadId)}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ call_id: callId, decision }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

function frozenTitle(raw: unknown): string {
  if (raw && typeof raw === "object") return String((raw as Record<string, unknown>).title || "");
  if (typeof raw === "string" && raw.trim().startsWith("{")) {
    try { return String((JSON.parse(raw) as Record<string, unknown>).title || ""); } catch { return ""; }
  }
  return "";
}

/** A kept thread as the Ask window draws it: question and answer pairs, the
 * answer's Looked at, and the About its questions named. Only text parts are
 * drawn; a question with no answer yet is left out. */
export function askTurnsFromThread(detail: {
  messages: Array<{ id: string; role: string; parts: Array<{ kind: string; text: string }> }>;
  refs: Array<{ messageId: string; refKind: string; refId: string; frozenJson: unknown; origin?: string }>;
  used?: Record<string, AgentUse>;
}): { turns: AskTurn[]; about: LookedAt[] } {
  const textOf = (message: { parts: Array<{ kind: string; text: string }> }) =>
    message.parts.filter((part) => part.kind === "text" && part.text).map((part) => part.text).join("\n").trim();
  // Betterment Q7: an answer made with the desk's tools keeps each pass's
  // words in its own part; the answer is the last one.
  const answerOf = (message: { parts: Array<{ kind: string; text: string }> }) =>
    message.parts.filter((part) => part.kind === "text" && part.text?.trim()).map((part) => part.text.trim()).at(-1) ?? "";
  const refsFor = (messageId: string, origin: string) => {
    const seen = new Set<string>();
    const out: LookedAt[] = [];
    for (const row of detail.refs) {
      if (row.messageId !== messageId || (row.origin && row.origin !== origin)) continue;
      const ref = `${row.refKind}:${row.refId}`;
      if (!row.refKind || !row.refId || seen.has(ref)) continue;
      seen.add(ref);
      out.push({ ref, title: sourceName(ref, frozenTitle(row.frozenJson)) });
    }
    return out;
  };
  const turns: AskTurn[] = [];
  const about: LookedAt[] = [];
  let question: { id: string; text: string } | null = null;
  for (const message of detail.messages) {
    const text = message.role === "assistant" ? answerOf(message) : textOf(message);
    if (message.role === "user") {
      question = text ? { id: message.id, text } : null;
      for (const row of refsFor(message.id, "reference")) {
        if (!about.some((known) => known.ref === row.ref)) about.push(row);
      }
    } else if (message.role === "assistant" && question && text) {
      const used = detail.used?.[message.id] ?? null;
      turns.push({
        key: message.id, question: question.text, answer: text,
        lookedAt: withToolReads(refsFor(message.id, "relevance"), used), used,
      });
      question = null;
    }
  }
  return { turns, about };
}

function markdownLabel(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/([\[\]])/g, "\\$1").replace(/[\r\n]+/g, " ");
}

function markdownDestination(value: string): string {
  // ReadingDocument passes the URL node straight to refOpener; angle-bracket
  // Markdown URLs include the brackets in that node and become inert there.
  return encodeURI(value).replace(/[()<>\\]/g, (character) => encodeURIComponent(character));
}

/** Editable provenance: openable refs link through the Desk's reader; other
 * qualified refs stay visible as text. This is not immutable lineage. */
export function answerNoteBody(turn: AskTurn, threadId?: string | null): string {
  const sources = turn.lookedAt
    .map((row) => /^[a-z][a-z_]*:\S+$/i.test(row.ref) && refOpener(row.ref)
      ? `[${markdownLabel(row.title)}](${markdownDestination(row.ref)})`
      : `${markdownLabel(row.title)} (${markdownLabel(row.ref)})`);
  const looked = sources.length ? `\n\nLooked at: ${sources.join(", ")}` : "";
  const origin = threadId ? `\n\nFrom: [Ask thread](${markdownDestination(`thread:${threadId}`)})` : "";
  return `${turn.answer}${looked}${origin}`;
}

/** Save an editable Note with the answer's actual qualified source refs. */
export async function saveAnswerAsNote(turn: AskTurn, threadId?: string | null): Promise<string | null> {
  try {
    const res = await apiRequest("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: turn.question.slice(0, 120), body_markdown: answerNoteBody(turn, threadId), tags: ["ask"] }),
    });
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    const id = String(data?.note?.id || "");
    return id ? `note:${id}` : null;
  } catch {
    return null;
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
  /** The hub's reason token for a refused Resume (Betterment Q1); the face
   *  prints `reasonWords(reason)`, never `error`. Empty when the hub sent none. */
  reason: string;
}

/** Return to one saved ask. This is also how a finished ask SETTLES: the
 *  route reads `ask_results` first, finds the answer the run just wrote,
 *  marks the task `accepted` and dispatches nothing. There is no separate
 *  accept route, and inventing a second identity to settle one would be
 *  exactly the double-spend ruling B3 forbids. */
export async function resumeAskTask(taskId: string): Promise<AskResumeOutcome> {
  const empty: AskResumeOutcome = {
    ok: false, task: null, answer: null, claimed: false, dispatched: false, error: "", reason: "",
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
        reason: data && typeof data.reason === "string" ? data.reason : "",
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
      reason: "",
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
