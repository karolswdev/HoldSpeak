/* Run as a program: the ONE implementation (2026-11-08). One verb, one name,
 * every place it shows: an action's row in a Project's Room (JRN13), the
 * Needs you row menu, the decision reader and the Note's toolbar. It makes
 * a Drafting Program from its origin and the Program window opens.
 *
 * - An action goes through the hub's action path (origin `action:<id>`;
 *   the hub reads the action's words, its Project and its person, and its
 *   merge closes the action).
 * - A decision (its record, `decision_record:<id>`, the ref the hub reads
 *   its title by), a note or a Room item goes through POST /api/programs
 *   with `origin_ref` `<kind>:<id>`, its words as the goal, filed in its own
 *   Project, else the project the wizard picks (the window's scope's, else
 *   the only one; never a guess).
 *
 * A refusal says the hub's words in place. */
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { DotWord } from "../surface";
import { createProgram, defaultProjectId, readProjectChoices } from "./api";
import { openProgram } from "./open";

export type ProgramOrigin =
  | { kind: "action"; id: string; projectId?: string | null }
  | {
    kind: "decision_record" | "note" | "project_item";
    id: string;
    title: string;
    goal: string;
    projectId?: string | null;
    scopeProjectId?: string | null;
  };

const KIND_WORD: Record<ProgramOrigin["kind"], string> = {
  action: "action", decision_record: "decision", note: "note", project_item: "item",
};

function programTitleOf(title: string, body: string): string {
  const line = (title || body.split("\n").find((row) => row.trim()) || "").replace(/^#+\s*/, "").trim();
  return line.length > 80 ? `${line.slice(0, 79)}…` : line || "New program";
}

async function projectFor(projectId?: string | null, scopeProjectId?: string | null): Promise<string> {
  if (projectId) return projectId;
  try {
    return defaultProjectId(await readProjectChoices(), scopeProjectId);
  } catch {
    return "";
  }
}

/** Make the Program and open its window. Returns its id; throws the hub's refusal. */
export async function runAsProgram(origin: ProgramOrigin): Promise<{ id: string; projectId: string }> {
  if (origin.kind === "action") {
    const made = await apiFetch<{ id?: string; program?: { id: string } }>("/api/programs/from-action", {
      method: "POST", json: { action_id: origin.id, ...(origin.projectId ? { project_id: origin.projectId } : {}) },
    });
    const id = String(made.id ?? made.program?.id ?? "");
    if (id) openProgram(id);
    return { id, projectId: origin.projectId ?? "" };
  }
  const projectId = await projectFor(origin.projectId, origin.scopeProjectId);
  let made;
  try {
    made = await createProgram({
      title: programTitleOf(origin.title, origin.goal),
      goal: origin.goal,
      template: "fast-cycle",
      origin_ref: `${origin.kind}:${origin.id}`,
      ...(projectId ? { project_id: projectId } : {}),
    });
  } catch (cause) {
    throw Object.assign(cause instanceof Error ? cause : new Error(String(cause)), { projectId });
  }
  const id = String(made?.id ?? "");
  if (id) openProgram(id);
  return { id, projectId };
}

export function runAsProgramRefusal(cause: unknown, kind: ProgramOrigin["kind"]): string {
  const payload = cause instanceof ApiError ? (cause.payload as { detail?: string } | null) : null;
  return payload?.detail || `The program was not made. The ${KIND_WORD[kind]} is unchanged. Try again.`;
}

type VerbProps = {
  title: string;
  variant?: "ghost" | "secondary";
  testId?: string;
} & ({ origin: ProgramOrigin; actionId?: never; projectId?: never } | { origin?: never; actionId: string; projectId?: string | null });

export function RunAsProgramVerb(props: VerbProps) {
  const { title, variant = "ghost", testId = "run-as-program" } = props;
  const origin: ProgramOrigin = props.origin ?? { kind: "action", id: props.actionId, projectId: props.projectId };
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState("");
  const run = async () => {
    setBusy(true);
    setFailed("");
    try {
      await runAsProgram(origin);
    } catch (cause) {
      setFailed(runAsProgramRefusal(cause, origin.kind));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Button dense variant={variant} loading={busy} disabled={busy} aria-label={`Run as a program: ${title}`}
        onClick={() => void run()} data-testid={testId}>Run as a program</Button>
      {failed ? <DotWord tone="warn" title={failed} data-testid={`${testId}-failed`}>{failed}</DotWord> : null}
    </>
  );
}
