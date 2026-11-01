/* Programs (PROGRAMS-DESIGN-2026-10-28 §11): the faces' reads and writes.
 *
 * Every read and write goes through `apiFetch`. Live updates: the
 * `program_changed` frame (one per change; it names the Program) and a
 * `desk_changed` frame of kind `program`. A frame that names only windows
 * never re-reads (#1584). A hub without the Programs slice answers 404 on
 * the list: the faces draw the empty list, never a console error. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, apiFetch } from "../../lib/api";
import { useOptionalRuntimeBus } from "../../runtime/RuntimeBus";
import { frameChanges } from "../compositor/windowFrames";
import type {
  Control, DecideBody, PersonProgramRow, PlanStep, Program, ProgramChangedFrame, ProgramList, ProgramRoomRow, ProgramText,
  PlanAnswer, RoundAnswer, RoundAsked, RoundPressed, ShapeAnswer, ShapeEngine, TextApplyAnswer,
} from "./types";

const EMPTY_LIST: ProgramList = { programs: [], counts: {}, worst: null, worst_word: "" };

function notFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

const base = (id: string) => `/api/programs/${encodeURIComponent(id)}`;

export async function readPrograms(): Promise<ProgramList> {
  try {
    const body = await apiFetch<ProgramList>("/api/programs");
    return body && Array.isArray(body.programs) ? body : EMPTY_LIST;
  } catch (error) {
    if (notFound(error)) return EMPTY_LIST;
    throw error;
  }
}

export function readProgram(id: string): Promise<Program> {
  return apiFetch<Program>(base(id));
}

export interface CreateBody {
  title: string;
  goal?: string;
  repository?: string;
  project_id?: string;
  base_branch?: string;
  control?: Control;
  check_command?: string;
  template?: string;
  origin_ref?: string;
  for_person_id?: string;
}

/** The hub answers the new Program's wire (or `{program}`). */
export async function createProgram(body: CreateBody): Promise<Program> {
  const answer = await apiFetch<Program | { program: Program }>("/api/programs", { method: "POST", json: body });
  return "program" in (answer as object) ? (answer as { program: Program }).program : (answer as Program);
}

function unwrap(answer: Program | { program?: Program }): Program | null {
  if (answer && typeof answer === "object" && "steps" in answer) return answer as Program;
  return (answer as { program?: Program })?.program ?? null;
}

export async function planProgram(id: string, steps: PlanStep[], replace = true): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(`${base(id)}/plan`, { method: "POST", json: { steps, replace, size: null } }));
}

export type ProgramVerb = "start" | "park" | "resume";

export async function programVerb(id: string, verb: ProgramVerb): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(`${base(id)}/${verb}`, { method: "POST", json: {} }));
}

export async function decide(programId: string, stepId: string, body: DecideBody): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/steps/${encodeURIComponent(stepId)}/decide`, { method: "POST", json: body }));
}

/** Overturn one decision the engine made for him (§6 "Decided for you"). */
export async function overturn(programId: string, decisionId: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/decisions/${encodeURIComponent(decisionId)}/overturn`, { method: "POST", json: {} }));
}

/** PG20, Start from here: a new step whose worktree starts at the
 *  checkpoint's pinned ref (`refs/holdspeak/checkpoints/<step>/<n>`). */
export async function startFrom(programId: string, checkpointId: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/checkpoints/${encodeURIComponent(checkpointId)}/start-from`, { method: "POST", json: {} }));
}

/** Secure: he closes a Program whose steps are all finished. */
export async function closeProgram(programId: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(`${base(programId)}/close`, { method: "POST", json: {} }));
}

export async function race(programId: string, stepId: string, n: number): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/steps/${encodeURIComponent(stepId)}/race`, { method: "POST", json: { n } }));
}

/** PG19: hand a running step to another agent (owner only). */
export async function handoff(programId: string, stepId: string, to: { profile: string; engine: string | null }): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/steps/${encodeURIComponent(stepId)}/handoff`, { method: "POST", json: { to } }));
}

/* ── PG-REQ (PROGRAMS-REQUIREMENTS-2026-10-31 §11): requirements and adjust ── */

export interface RequireBody {
  text: string;
  /** Omitted: the hub guesses it by rule. */
  kind?: string;
  step_id?: string;
  each_step?: boolean;
  required?: boolean;
  spec?: { command?: string; case?: string; width?: number };
}

/** Add a requirement (his, at once). */
export async function addRequirement(programId: string, body: RequireBody): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(`${base(programId)}/requirements`, { method: "POST", json: body }));
}

/** Edit a requirement's sentence, kind or spec (a Met one goes to Not yet). */
export async function editRequirement(programId: string, requirementId: string,
  body: Partial<Pick<RequireBody, "text" | "kind" | "required" | "spec">>): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/requirements/${encodeURIComponent(requirementId)}`, { method: "PATCH", json: body }));
}

export type RequirementChoice = "met" | "unmet" | "waive" | "send_back" | "done" | "cant";

/** His press on a requirement: Met / Unmet (his word), Waive (with his
 *  line), Send back (one more round). */
export async function decideRequirement(programId: string, requirementId: string, choice: RequirementChoice,
  line?: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/requirements/${encodeURIComponent(requirementId)}/decide`,
    { method: "POST", json: line ? { choice, line } : { choice } }));
}

/** His answer to what an agent proposed (Add / Apply / Send, or Skip). */
export async function decideProposal(programId: string, proposalId: string | number, choice: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/proposals/${encodeURIComponent(String(proposalId))}/decide`, { method: "POST", json: { choice } }));
}

/** The §8 fields a step's state leaves open; `before` moves it (a step id,
 *  or `end`). A frozen field answers 409 `step_frozen` with its reason. */
export interface StepChangeBody {
  title?: string;
  brief?: string;
  owns?: string[];
  after?: number[];
  effort?: "low" | "medium" | "high";
  profile?: string | null;
  engine?: string | null;
  before?: string;
  /** PG-WINDOW: the step's gate, while it is Planned. */
  gate_check?: boolean;
  gate_review?: "none" | "agent" | "person";
  gate_merge?: "level" | "owner" | "none";
}

export async function changeStep(programId: string, stepId: string, body: StepChangeBody): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/steps/${encodeURIComponent(stepId)}`, { method: "PATCH", json: body }));
}

/** A line added to a started step's brief, typed at the next turn boundary. */
/** PG-IMPORT IMP6: he takes the step's lane over (the engine types nothing
 *  into it), or hands it back. No confirmation: each undoes the other. */
export async function takeLane(programId: string, stepId: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/steps/${encodeURIComponent(stepId)}/take`, { method: "POST", json: {} }));
}

export async function handLaneBack(programId: string, stepId: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/steps/${encodeURIComponent(stepId)}/hand-back`, { method: "POST", json: {} }));
}

export async function amendStep(programId: string, stepId: string, line: string): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(
    `${base(programId)}/steps/${encodeURIComponent(stepId)}/amend`, { method: "POST", json: { line } }));
}

/** Insert before: a new Planned step at the place of `beforeId`; with
 *  `waits` that step now also comes after the new one. */
export async function insertStep(programId: string, beforeId: string, step: PlanStep, waits = true): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(`${base(programId)}/plan`, {
    method: "POST", json: { steps: [step], before: beforeId, waits },
  }));
}

/** The address of a requirement's evidence file (its log text or its shot
 *  image): the hub serves it only to this desk. */
export function evidenceUrl(programId: string, requirementId: string): string {
  return `${base(programId)}/requirements/${encodeURIComponent(requirementId)}/evidence`;
}

/** The Room's Programs fold and the person's room line (§9b). */
export async function readProjectPrograms(projectId: string): Promise<ProgramRoomRow[]> {
  try {
    const body = await apiFetch<{ programs?: ProgramRoomRow[] }>(`/api/programs?project_id=${encodeURIComponent(projectId)}`);
    return Array.isArray(body?.programs) ? body.programs : [];
  } catch (error) {
    if (notFound(error)) return [];
    throw error;
  }
}

export async function readPersonPrograms(personId: string): Promise<PersonProgramRow[]> {
  try {
    const body = await apiFetch<{ programs?: PersonProgramRow[] }>(`/api/programs?person_id=${encodeURIComponent(personId)}`);
    return Array.isArray(body?.programs) ? body.programs : [];
  } catch (error) {
    if (notFound(error)) return [];
    throw error;
  }
}

/** The templates (design §10; `holdspeak/program_templates.py`), with the
 *  one line the Templates fold draws. */
export const TEMPLATES = [
  { id: "fast-cycle", name: "Fast cycle", line: "A step for each brief you paste. Your check, your merge.", agent: "claude" },
  { id: "build-and-review", name: "Build and review", line: "A step for each brief; Codex reviews each one.", agent: "codex" },
  { id: "race", name: "Race", line: "One brief, two agents; the first green one wins.", agent: "claude" },
  { id: "overnight", name: "Overnight on the home box", line: "qwen builds when the engine is idle; Claude Code reviews; it merges on green.", agent: "pi" },
  { id: "from-the-desk", name: "From the desk", line: "A step for each open action of a project.", agent: "" },
  // #1697: the night program (23:30–07:00, YOLO, pi on the home engine, 64k a step).
  { id: "dreaming", name: "Dreaming", line: "Runs at night on the idle home engine; fills itself from tasks marked Tonight", agent: "pi" },
] as const;

/** One frame names a Program (`program_changed`, or `desk_changed` kind
 *  `program`): the id, else "" for a frame that is not about Programs. */
export function programOfFrame(type: string, data: unknown): string | null {
  if (type === "program_changed") {
    const frame = data as ProgramChangedFrame | null;
    return frame?.program_id ? String(frame.program_id) : "";
  }
  const changes = frameChanges(data);
  const mine = (changes ?? []).find((change) => change.kind === "program");
  return mine ? mine.id : null;
}

/** Re-read on a Program frame. `onFrame(id)` gets the Program id named. */
export function useProgramFrames(onFrame: (programId: string) => void): void {
  const subscribe = useOptionalRuntimeBus()?.subscribe;
  const handler = useRef(onFrame);
  handler.current = onFrame;
  useEffect(() => {
    if (!subscribe) return;
    const offProgram = subscribe("program_changed", (frame) => {
      const id = programOfFrame("program_changed", frame.data);
      if (id !== null) handler.current(id);
    });
    const offDesk = subscribe("desk_changed", (frame) => {
      const id = programOfFrame("desk_changed", frame.data);
      if (id !== null) handler.current(id);
    });
    return () => { offProgram(); offDesk(); };
  }, [subscribe]);
}

export function usePrograms() {
  const [state, setState] = useState<{ loading: boolean; error: unknown; list: ProgramList }>({
    loading: true, error: null, list: EMPTY_LIST,
  });
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  const load = useCallback(async () => {
    try {
      const list = await readPrograms();
      if (alive.current) setState({ loading: false, error: null, list });
    } catch (error) {
      if (alive.current) setState((now) => ({ ...now, loading: false, error }));
    }
  }, []);
  useEffect(() => { void load(); }, [load]);
  useProgramFrames(() => void load());
  return { ...state, reload: load };
}

export function useProgram(id: string) {
  const [state, setState] = useState<{ loading: boolean; error: unknown; program: Program | null }>({
    loading: true, error: null, program: null,
  });
  const alive = useRef(true);
  useEffect(() => () => { alive.current = false; }, []);
  const load = useCallback(async () => {
    try {
      const program = await readProgram(id);
      if (alive.current) setState({ loading: false, error: null, program });
    } catch (error) {
      if (alive.current) setState((now) => ({ ...now, loading: false, error }));
    }
  }, [id]);
  useEffect(() => { void load(); }, [load]);
  useProgramFrames((named) => { if (!named || named === id) void load(); });
  const apply = useCallback((program: Program | null) => {
    if (program && alive.current) setState({ loading: false, error: null, program });
  }, []);
  return { ...state, reload: load, apply };
}

/** The Program's own fields (title, goal, control, the default Runs on,
 *  when idle, project). */
export interface UpdateBody {
  title?: string;
  goal?: string;
  control?: Control;
  default_profile?: string;
  default_engine?: string | null;
  prefer_idle?: boolean;
  project_id?: string | null;
  /** PG19: the ordered agents, who may read the repository, hand off on its own. */
  runs_on?: { profile: string; engine: string | null }[];
  allowed_profiles?: string[];
  may_handoff?: boolean;
}

export async function updateProgram(id: string, body: UpdateBody): Promise<Program | null> {
  return unwrap(await apiFetch<Program | { program?: Program }>(base(id), { method: "PATCH", json: body }));
}

/* ── PG-LANG (PROGRAM-LANGUAGE-2026-10-31 §3.6): the Program text ── */

export function readProgramText(id: string): Promise<ProgramText> {
  return apiFetch<ProgramText>(`${base(id)}/text`);
}

export interface TextApplyBody {
  text: string;
  /** The text he started from: a field that moved since is a conflict. */
  base: string;
  /** True (the default): a preview, nothing written. */
  dry_run: boolean;
  /** The rows that lower the bar he pressed one by one. */
  allow_lower?: string[];
}

export function applyProgramText(id: string, body: TextApplyBody): Promise<TextApplyAnswer> {
  return apiFetch<TextApplyAnswer>(`${base(id)}/text`, { method: "POST", json: body });
}

/** PG-LANG LANG3: the engine that shapes this Program (the bar names it). */
export function readShapeEngine(id: string): Promise<ShapeEngine> {
  return apiFetch<ShapeEngine>(`${base(id)}/shape`);
}

/** PG-LANG LANG3: one sentence → the change rows; `apply` lands the allowed
 *  rows at once at YOLO only (the hub decides by the level). */
export function shapeProgram(id: string, body: { sentence: string; apply: boolean; pending?: string }): Promise<ShapeAnswer> {
  return apiFetch<ShapeAnswer>(`${base(id)}/shape`, { method: "POST", json: body });
}

/** PG-LANG LANG5: Not this on the rows a call left in the change well. */
export function dropHeldShape(id: string): Promise<Program> {
  return apiFetch<Program>(`${base(id)}/shape/held`, { method: "DELETE" });
}

/** PG-LANG LANG9: the interview rounds (the five defaults, each open). */
export function openRounds(id: string, names?: string[]): Promise<RoundPressed> {
  return apiFetch<RoundPressed>(`${base(id)}/rounds`, { method: "POST", json: names ? { names } : {} });
}

/** PG-LANG LANG9: the ONE next question of a round (one engine call). */
export function nextQuestion(id: string, round: string): Promise<RoundAsked> {
  return apiFetch<RoundAsked>(`${base(id)}/rounds/${encodeURIComponent(round)}/next`, { method: "POST", json: {} });
}

/** PG-LANG LANG9: his answer (his words or an offered one), Skip question,
 *  or Not this on the answer's rows. */
export function answerRound(id: string, round: string, body: {
  question_id: string; answer?: string; option?: string; skip?: boolean; not_this?: boolean; apply?: boolean;
}): Promise<RoundAnswer & RoundPressed> {
  return apiFetch<RoundAnswer & RoundPressed>(`${base(id)}/rounds/${encodeURIComponent(round)}/answer`, { method: "POST", json: body });
}

/** PG-LANG LANG9: Done with <round>, Skip round, Ask more. */
export function decideRound(id: string, round: string, choice: "done" | "skip" | "reopen"): Promise<RoundPressed> {
  return apiFetch<RoundPressed>(`${base(id)}/rounds/${encodeURIComponent(round)}/decide`, { method: "POST", json: { choice } });
}

/** PG-LANG LANG6: the goal drafted into change rows (nothing is written; Apply
 *  is `applyProgramText`). Split on a too-big row sends the draft and the
 *  step's place. */
export function planDraft(id: string, body: { goal?: string; budget?: string; text?: string; split?: number }): Promise<PlanAnswer> {
  return apiFetch<PlanAnswer>(`${base(id)}/plan/draft`, { method: "POST", json: body });
}


/* ── JRN2 (PG-LANG LANG12, #1687): Add to tonight ── */

export interface TonightAnswer {
  added: boolean;
  program_id: string;
  step_id: string;
  ordinal: number;
  /** "Added to tonight: step 3 · …" or "It is in tonight already: step 3". */
  say: string;
  program?: Program | null;
}

/** A Door task (`action`), a note line (`note` with `line`) or a program
 *  step becomes a Planned step of the night Program. */
export async function addToTonight(body: { kind: "action" | "note" | "program_step"; item_id: string; line?: string }): Promise<TonightAnswer> {
  return apiFetch<TonightAnswer>("/api/programs/tonight", { method: "POST", json: body });
}
