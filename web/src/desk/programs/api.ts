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
  Control, DecideBody, PersonProgramRow, PlanStep, Program, ProgramChangedFrame, ProgramList, ProgramRoomRow,
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
