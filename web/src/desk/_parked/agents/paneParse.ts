/** Parked (Betterment AG7, 2026-10-18): the Agents row's own read of an
 *  agent's pane and its parse (Betterment AG2). The hub's screen rules
 *  (holdspeak/agent_context/screen_rules.py: prompt_reading) now read the
 *  command and the numbered menu, and the row shows `member.screen`.
 *  Nothing imports this file. */
import { useEffect, useState } from "react";
import { apiFetch } from "../../../lib/api";
import type { AgentChoice } from "../../agents/choices";

/** The bottom of the agent's screen (read only; watching is free). An
 *  unread screen is no menu and no command: the row still answers. */
export function usePaneTail(sessionKey: string | null | undefined, when: unknown): string[] {
  const [lines, setLines] = useState<string[]>([]);
  useEffect(() => {
    let live = true;
    if (!sessionKey) return;
    void apiFetch<{ peek?: { status?: string; lines?: string[] } }>(
      `/api/coders/${encodeURIComponent(sessionKey)}/peek?lines=40`,
    )
      .then((answer) => {
        if (live && answer?.peek?.status === "live" && Array.isArray(answer.peek.lines)) setLines(answer.peek.lines);
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [sessionKey, when]);
  return lines;
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
