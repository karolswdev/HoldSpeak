/** Betterment AG2: what an agent's question and its screen offer, read in
 *  words (until AG7's screen rules replace this parse).
 *
 *  - `questionChoices`: "Answer 1 for config, 2 for env." in the question.
 *  - `menuChoices`: the agent's own numbered menu at the bottom of its pane
 *    (`❯ 1. Yes`, `2. No`).
 *  - `wantsToRun`: the command above "Do you want to proceed?" in the pane.
 */

export interface AgentChoice {
  /** What one press sends: the number. */
  n: string;
  /** The words beside it (`config`, `Yes`). */
  label: string;
}

/** `Answer 1 for config, 2 for env.` -> `[1 · config, 2 · env]`; none: []. */
export function questionChoices(question: string | null | undefined): AgentChoice[] {
  const text = String(question ?? "");
  const at = text.search(/\b(?:answer|reply|say|type)\s+\d+\s+(?:for|to)\b/i);
  if (at < 0) return [];
  const tail = text.slice(at);
  const out: AgentChoice[] = [];
  const part = /(\d+)\s+(?:for|to)\s+([^,.;?!\n]+?)(?=\s*(?:,|\.|;|\?|!|\n|\bor\b|\band\b|$))/gi;
  for (const match of tail.matchAll(part)) {
    const label = match[2].trim().replace(/^(?:the|a|an)\s+/i, "");
    if (label && !out.some((c) => c.n === match[1])) out.push({ n: match[1], label });
  }
  return out.length >= 2 ? out : [];
}

const BOX = /[│┃║╭╮╰╯─━═┌┐└┘]/g;

function clean(line: string): string {
  return line.replace(BOX, " ").replace(/\s+$/, "").replace(/^\s+/, "");
}

/** The agent's numbered menu: the last run of `N. words` lines in the tail
 *  (the selected one may wear `❯`). Fewer than two: no menu. */
export function menuChoices(lines: readonly string[] | null | undefined): AgentChoice[] {
  const rows = (lines ?? []).map(clean);
  let end = rows.length - 1;
  while (end >= 0 && !/^(?:[❯>]\s*)?\d+\.\s+\S/.test(rows[end])) end--;
  if (end < 0) return [];
  let start = end;
  while (start - 1 >= 0 && /^(?:[❯>]\s*)?\d+\.\s+\S/.test(rows[start - 1])) start--;
  const out = rows.slice(start, end + 1).map((row) => {
    const match = /^(?:[❯>]\s*)?(\d+)\.\s+(.+)$/.exec(row)!;
    return { n: match[1], label: match[2].replace(/\s*\((?:esc|enter)\)\s*$/i, "").trim() };
  });
  return out.length >= 2 ? out : [];
}

/** The command an approval prompt asks to run: the lines between the tool's
 *  header (`● Bash command`, `Bash command`) and "Do you want to proceed?".
 *  Null when the tail shows no such prompt. */
export function wantsToRun(lines: readonly string[] | null | undefined): string | null {
  const rows = (lines ?? []).map(clean);
  let ask = rows.length - 1;
  while (ask >= 0 && !/do you want to (?:proceed|run|make this edit|allow)/i.test(rows[ask])) ask--;
  if (ask < 0) return null;
  const body: string[] = [];
  for (let i = ask - 1; i >= 0 && i >= ask - 12; i--) {
    const row = rows[i];
    if (/^(?:●\s*)?[A-Z][\w ]*?(?:command|tool use|edit|write)\s*$/i.test(row) || /^●/.test(row)) break;
    if (!row) {
      if (body.length) break;
      continue;
    }
    body.unshift(row);
  }
  // A real prompt names what the command is for under it; the command leads.
  const command = body.join("\n").trim();
  return command || null;
}
