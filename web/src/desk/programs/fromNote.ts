/* Programs (design §9b, "Where it came from"): "Run as a program" on the
 * Note's toolbar. A new Program in Drafting, the note as its origin, the
 * note's words as its goal, filed in the note's Project (whose repository
 * it runs on); a note in no project goes to the project the wizard picks
 * (the window's scope's, else the only one). The hub plans its steps from
 * the goal. The Program window opens. */
import { plainFail, type PlainFail } from "../surface/plainFailure";
import { createProgram, defaultProjectId, readProjectChoices } from "./api";
import { openProgram } from "./open";

export function programTitleOf(title: string, body: string): string {
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

export async function runNoteAsProgram(note: { id: string; title: string; body: string; projectId?: string | null; scopeProjectId?: string | null }): Promise<PlainFail | null> {
  const projectId = await projectFor(note.projectId, note.scopeProjectId);
  try {
    const made = await createProgram({
      title: programTitleOf(note.title, note.body),
      goal: note.body,
      template: "fast-cycle",
      origin_ref: `note:${note.id}`,
      ...(projectId ? { project_id: projectId } : {}),
    });
    if (made?.id) openProgram(made.id);
    return null;
  } catch (cause) {
    return plainFail("The program was not made", cause, "The note is unchanged", projectId ? "Try again" : "File the note in a project first");
  }
}
