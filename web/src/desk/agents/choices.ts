/** Betterment AG2: the choices an agent's question offers, read in words:
 *  "Answer 1 for config, 2 for env." in the question.
 *
 *  Betterment AG7: the agent's own numbered menu and the command an approval
 *  wants to run are read by the hub's screen rules (`member.screen`); the
 *  face's parse of the pane is parked in `desk/_parked/agents/paneParse.ts`.
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
