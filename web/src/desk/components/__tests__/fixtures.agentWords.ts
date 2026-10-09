// The owner's shot (docs/internal/philo/phase-16/01-shots/08-lane-asks-1440.png):
// pi's turn end, word for word from evidence/hub-lane.json (events[7].text).
export const OWNER_TEXT = [
  "Steps 1–3 complete:",
  "",
  '1. **project.list** called once — project "pi rig: the third harness" (proj-e5abdabc568b).',
  "2. **cat /etc/hosts** was denied by the desk (outside the worktree). Per the item's rule, I did not retry; NOTES.md contains the line `hosts: not read`.",
  "3. **Committed** as `45e2b1a` on branch `hs/project_item-pitem_d25d3fc020be4d8cbc90269fc17da3f7`.",
  "",
  "Step 4 — my question to the owner:",
  "",
  "**May I open a pull request for branch `hs/project_item-pitem_d25d3fc020be4d8cbc90269fc17da3f7` (naming project_item:pitem_d25d3fc020be4d8cbc90269fc17da3f7 in the body)?**",
].join("\n");

/** The hub's 120-character head of the brief (`text_head`), cut inside a word. */
export const BRIEF_HEAD =
  'HoldSpeak hands you one item: project_item:pitem_d25d3fc020be4d8cbc90269fc17da3f7 "Write NOTES.md with the host line".\nP';

/** Markdown on a surface leaves no mark as text. */
export function noLiteralMarks(text: string): void {
  if (text.includes("**")) throw new Error(`literal ** in: ${text}`);
  if (/`[^`]*`/.test(text)) throw new Error(`literal backtick pair in: ${text}`);
  if (/(^|\s)1\. /.test(text)) throw new Error(`literal "1. " marker in: ${text}`);
}
