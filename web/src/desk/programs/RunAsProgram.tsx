/* JRN13 (PROGRAM-JOURNEYS, "Run as a program on a project action row"):
 * the library Button on an action's row in a Project's Room. The hub makes
 * a Drafting Program from the action (its words as the goal, the Project's
 * repository, the owner as its person when exactly one person has that
 * name; origin `action:<id>`, so its merge closes the action) and the
 * Program window opens. A refusal says the hub's words in place. */
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError, apiFetch } from "../../lib/api";
import { DotWord } from "../surface";
import { openProgram } from "./open";

export async function runActionAsProgram(actionId: string, projectId?: string | null): Promise<{ id: string }> {
  const made = await apiFetch<{ id?: string; program?: { id: string } }>("/api/programs/from-action", {
    method: "POST", json: { action_id: actionId, ...(projectId ? { project_id: projectId } : {}) },
  });
  return { id: String(made.id ?? made.program?.id ?? "") };
}

function refusal(cause: unknown): string {
  const payload = cause instanceof ApiError ? (cause.payload as { detail?: string } | null) : null;
  return payload?.detail || "The program was not made. The action is unchanged. Try again.";
}

export function RunAsProgramVerb({ actionId, projectId, title }: { actionId: string; projectId?: string | null; title: string }) {
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState("");
  const run = async () => {
    setBusy(true);
    setFailed("");
    try {
      const made = await runActionAsProgram(actionId, projectId);
      if (made.id) openProgram(made.id);
    } catch (cause) {
      setFailed(refusal(cause));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Button dense variant="ghost" loading={busy} disabled={busy} aria-label={`Run as a program: ${title}`}
        onClick={() => void run()} data-testid="run-as-program">Run as a program</Button>
      {failed ? <DotWord tone="warn" title={failed} data-testid="run-as-program-failed">{failed}</DotWord> : null}
    </>
  );
}
