/* Programs (design §9b, "Where it came from"): "Run as a program" on the
 * Note's toolbar, through the one implementation (RunAsProgram.tsx): a new
 * Program in Drafting, the note as its origin, the note's words as its
 * goal, filed in the note's Project, else the project the wizard picks.
 * The Note's toolbar says a refusal in its own plain-failure words. */
import { plainFail, type PlainFail } from "../surface/plainFailure";
import { runAsProgram } from "./RunAsProgram";

export async function runNoteAsProgram(note: { id: string; title: string; body: string; projectId?: string | null; scopeProjectId?: string | null }): Promise<PlainFail | null> {
  try {
    await runAsProgram({ kind: "note", id: note.id, title: note.title, goal: note.body,
      projectId: note.projectId, scopeProjectId: note.scopeProjectId });
    return null;
  } catch (cause) {
    const projectId = (cause as { projectId?: string } | null)?.projectId;
    return plainFail("The program was not made", cause, "The note is unchanged", projectId ? "Try again" : "File the note in a project first");
  }
}
