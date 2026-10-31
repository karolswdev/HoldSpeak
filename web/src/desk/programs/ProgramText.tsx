/* Programs: the Text view and the change well (PROGRAM-LANGUAGE-2026-10-31
 * §3, §9.1, §9.2, §14; LANG2; canvas program-language-2026-10-31, the Board
 * and Text panel, direction S-A "the bar and the well").
 *
 * The text is a view; the tables stay the truth (§3.6). The Text view reads
 * `program.text` (GET …/text), shows it in the kit's TextPane (each line's
 * lamp: the state of the step or the requirement it belongs to; the `#`
 * words at the line end, never text), and keeps the text he started from as
 * the base. Preview sends his text as a dry run; the rows open in the change
 * well above the view. Apply sends the allowed text (each refused hunk put
 * back) with `allow_lower` = only the rows he pressed one by one; a conflict
 * (the base moved) reads the text again and says so. The well takes rows
 * from any source (a typed text now; a shaped sentence in LANG3/4). */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ChangeWell, DiffRow, TextPane, countWords, lineMarks, type TextPaneLine } from "../surface";
import { plainFail } from "../surface/plainFailure";
import { applyProgramText, readProgramText } from "./api";
import { clock } from "./Ledger";
import { programTone, requirementTone, stepTone } from "./model";
import type { Program, TextApplyAnswer, TextChange } from "./types";

/** The words of the Program text (§3.2) drawn in ink. */
export const PROGRAM_KEYWORDS = [
  "program", "goal", "in", "control", "check", "check off", "agent", "reviewer", "planner", "budget", "when idle",
  "may call", "may hand off", "allow", "spend up to", "for", "from", "template", "delivery dw", "night", "within",
  "every step", "at the end", "round", "step", "owns", "after", "effort", "race", "review", "merge", "merged", "brief",
  "run", "expect", "shot", "walk", "bound",
] as const;

/** The lamp: two or more spaces, then `#` and the rest (holdspeak/services/program_text.py `_LAMP`). */
const LAMP = /\s{2,}#(?:\s(.*))?$/;

function requirementOf(program: Program, ordinal: number) {
  return [...(program.requirements ?? []), ...program.steps.flatMap((step) => step.requirements ?? [])]
    .find((row) => row.ordinal === ordinal);
}

/** The lines of a printed text: each line's lamp out of its text, the
 *  version line and the `?` questions read only, the tone of the thing the
 *  line belongs to (the program, a step, a requirement). */
export function textLines(text: string, program: Program | null): TextPaneLine[] {
  return text.split("\n").map((raw) => {
    const trimmed = raw.trimStart();
    if (trimmed.startsWith("#")) return { text: raw, readOnly: true };
    if (/^\?\s/.test(trimmed)) return { text: raw, readOnly: true };
    let body = raw;
    let lamp: string | undefined;
    if (!trimmed.startsWith(">")) {
      const found = LAMP.exec(raw);
      if (found) {
        body = raw.slice(0, found.index);
        lamp = (found[1] ?? "").trim() || undefined;
      }
    }
    const line: TextPaneLine = { text: body };
    if (lamp) line.lamp = lamp;
    if (program) {
      const step = /^step (\d+) /.exec(body);
      const req = /^\s*R(\d+) [a-z]+/.exec(body);
      if (body.startsWith("program ")) line.tone = programTone(program.state);
      else if (step) {
        const found = program.steps.find((row) => row.ordinal === Number(step[1]));
        if (found) line.tone = stepTone(found.state);
      } else if (req) {
        const found = requirementOf(program, Number(req[1]));
        if (found) line.tone = requirementTone(found);
      }
    }
    return line;
  });
}

/** His text, as the hub reads it (lamps are never sent: they are the run). */
export function textOf(lines: readonly TextPaneLine[]): string {
  return lines.map((line) => line.text).join("\n");
}

function bodyLines(text: string): string[] {
  return textLines(text, null).map((line) => line.text);
}

/** One proposal in the well: the rows and how Apply sends them. */
export type TextProposal = {
  /** Where the rows came from (the typed text; LANG3/4 add a sentence). */
  source: "text";
  /** The text that was previewed and the base it was read against. */
  text: string;
  base: string;
  answer: TextApplyAnswer;
  /** The base moved: the text was read again (the time). */
  readAgain?: string;
};

/** The Text view's state: the base, his lines, the reads. */
export function useProgramText(programId: string, program: Program | null, active: boolean) {
  const [base, setBase] = useState<string | null>(null);
  const [lines, setLines] = useState<TextPaneLine[]>([]);
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const [busy, setBusy] = useState("");
  const programRef = useRef(program);
  programRef.current = program;
  const edited = base != null && textOf(lines) !== bodyLines(base).join("\n");
  const editedRef = useRef(edited);
  editedRef.current = edited;

  /** Read the text; with `keep`, his lines stay (only the base and the lamps move). */
  const read = useCallback(async (keep = false) => {
    try {
      const answer = await readProgramText(programId);
      setBase(answer.text);
      if (!keep) setLines(textLines(answer.text, programRef.current));
      setFailed(null);
      return answer.text;
    } catch (cause) {
      setFailed(plainFail("The program text did not load", cause, "The board is unchanged", "Try again"));
      return null;
    }
  }, [programId]);

  // The first read when the view opens; then a frame re-reads the lamps
  // while he has not changed the text.
  const revision = program?.revision;
  useEffect(() => {
    if (!active) return;
    if (base == null || !editedRef.current) void read();
  }, [active, revision]); // eslint-disable-line react-hooks/exhaustive-deps

  const reset = useCallback((text: string) => {
    setBase(text);
    setLines(textLines(text, programRef.current));
  }, []);
  const revert = useCallback(() => { if (base != null) setLines(textLines(base, programRef.current)); }, [base]);

  const preview = useCallback(async (): Promise<TextProposal | null> => {
    if (base == null) return null;
    const text = textOf(lines);
    setBusy("preview");
    setFailed(null);
    try {
      const answer = await applyProgramText(programId, { text, base, dry_run: true });
      const conflict = answer.changes.some((row) => row.verdict === "conflict");
      if (conflict) await read(true);
      return { source: "text", text, base, answer, readAgain: conflict ? clock(new Date().toISOString()) : undefined };
    } catch (cause) {
      setFailed(plainFail("The preview did not come back", cause, "Your text is kept", "Try again"));
      return null;
    } finally {
      setBusy("");
    }
  }, [base, lines, programId, read]);

  // The marks: his lines against the base; a refused row's line is marked.
  const marks = base == null ? [] : lineMarks(bodyLines(base), lines.map((line) => line.text));
  return { base, lines, setLines, edited, marks, read, reset, revert, preview, busy, failed };
}

/** The well's head: how many changes, how many refused (never a zero). */
function headWords(rows: readonly TextChange[]): { head: string; fact: string } {
  const refused = rows.filter((row) => row.verdict === "refused" || row.verdict === "conflict").length;
  const lowers = rows.filter((row) => row.verdict === "lowers").length;
  return {
    head: rows.length === 1 ? rows[0].say : "Changes from the text",
    fact: [countWords(rows.length, "change"), refused ? `${refused} refused` : "", lowers ? `${lowers} ${lowers === 1 ? "lowers" : "lower"} the bar` : ""]
      .filter(Boolean).join(" · "),
  };
}

/** The field words of a row (`merge`, `agent`), when the row is one field. */
function fieldWords(row: TextChange): string | undefined {
  if (row.op === "add" || row.op === "move" || row.field === "step" || row.field === "position") return undefined;
  if (row.field === "amend") return "brief";
  return row.field.replace(/_/g, " ");
}

/** The change well of a Program window (direction S-A): the rows, Apply
 *  (`Apply 5` when a row is refused: it applies the allowed text), Not
 *  this, and Apply this on each row that lowers the bar. */
export function ProgramChangeWell({ programId, proposal, settling, onApplied, onAnswer, onDismiss }: {
  programId: string;
  proposal: TextProposal;
  settling?: boolean;
  /** The hub applied it: the answer carries the Program and its new text. */
  onApplied(answer: TextApplyAnswer): void;
  /** The hub answered with rows again (a conflict at apply time). */
  onAnswer(proposal: TextProposal): void;
  onDismiss(): void;
}) {
  const [pressed, setPressed] = useState<Record<string, true>>({});
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<{ words: string; title: string } | null>(null);
  const rows = proposal.answer.changes;
  const blocked = rows.filter((row) => row.verdict === "refused" || row.verdict === "conflict");
  const applicable = rows.length - blocked.length;
  const waiting = rows.filter((row) => row.verdict === "lowers" && !pressed[row.id]);
  const { head, fact } = headWords(rows);
  const apply = async () => {
    setBusy(true);
    setFailed(null);
    try {
      const answer = await applyProgramText(programId, {
        text: blocked.length ? proposal.answer.allowed_text : proposal.text,
        base: proposal.base,
        dry_run: false,
        allow_lower: rows.filter((row) => row.verdict === "lowers" && pressed[row.id]).map((row) => row.id),
      });
      if (answer.applied) onApplied(answer);
      else onAnswer({ ...proposal, answer });
    } catch (cause) {
      setFailed(plainFail("The change was not applied", cause, "The program is unchanged", "Try again"));
    } finally {
      setBusy(false);
    }
  };
  return (
    <ChangeWell head={proposal.readAgain ? "Changed since you read it" : head}
      fact={proposal.readAgain ? `Read again at ${proposal.readAgain}` : fact} settling={settling} failure={failed}
      data-testid="programs-change-well"
      verbs={(
        <>
          {applicable ? (
            <Button dense variant="primary" loading={busy} disabled={busy || waiting.length > 0}
              title={waiting.length ? "Press Apply this on each row that lowers the bar" : undefined}
              onClick={() => void apply()} data-testid="programs-well-apply">
              {blocked.length ? `Apply ${applicable}` : "Apply"}
            </Button>
          ) : null}
          <Button dense variant="secondary" disabled={busy} onClick={onDismiss} data-testid="programs-well-not-this">Not this</Button>
        </>
      )}>
      {rows.map((row, index) => (
        <DiffRow key={row.id} index={index} op={row.op} where={row.where} field={fieldWords(row)}
          before={row.before || undefined} after={row.after || undefined} verdict={row.verdict} reason={row.reason} line={row.line}
          pressed={Boolean(pressed[row.id])} disabled={busy}
          onPress={row.verdict === "lowers" ? (next) => setPressed((now) => {
            const copy = { ...now };
            if (next) copy[row.id] = true; else delete copy[row.id];
            return copy;
          }) : undefined}
          data-testid="programs-diff-row" data-row={row.id} />
      ))}
    </ChangeWell>
  );
}

/** The ids of the steps the applied rows touched: new ones are born, the
 *  rest changed (each `step N` named in the base). */
export function landedSteps(before: Program, after: Program, rows: readonly TextChange[]): Record<string, "born" | "changed"> {
  const known = new Set(before.steps.map((step) => step.id));
  const out: Record<string, "born" | "changed"> = {};
  for (const step of after.steps) if (!known.has(step.id)) out[step.id] = "born";
  for (const row of rows) {
    if (row.verdict === "refused" || row.verdict === "conflict" || row.op === "add") continue;
    const ordinal = /^step (\d+)$/.exec(row.where)?.[1];
    const step = ordinal ? before.steps.find((candidate) => candidate.ordinal === Number(ordinal)) : undefined;
    if (step && !out[step.id] && after.steps.some((candidate) => candidate.id === step.id)) out[step.id] = "changed";
  }
  return out;
}

/** The Text view: the pane with its marks, a refused row's line marked. */
export function ProgramTextPane({ text, proposal, scrollTo, onLines }: {
  text: ReturnType<typeof useProgramText>;
  proposal: TextProposal | null;
  scrollTo?: number | null;
  onLines(next: TextPaneLine[]): void;
}) {
  if (text.base == null) {
    return text.failed ? (
      <p className="pg-failure" role="status" title={text.failed.title} data-testid="programs-text-failure">
        {text.failed.words}
        <Button dense variant="secondary" onClick={() => void text.read()} data-testid="programs-text-retry">Try again</Button>
      </p>
    ) : <p className="pg-text-reading" data-testid="programs-text-reading">Reading the program</p>;
  }
  const refused = new Map<number, string>();
  for (const row of proposal?.answer.changes ?? []) {
    if ((row.verdict === "refused" || row.verdict === "conflict") && row.line) refused.set(row.line - 1, row.reason ?? "Refused");
  }
  const lines = text.lines.map((line, index) => {
    const reason = refused.get(index);
    if (reason) return { ...line, mark: "!" as const, title: reason };
    const mark = text.marks[index];
    return mark ? { ...line, mark } : line;
  });
  return (
    <>
      {text.failed ? <p className="pg-failure" role="status" title={text.failed.title} data-testid="programs-text-failure">{text.failed.words}</p> : null}
      <TextPane label="Program text" lines={lines} keywords={PROGRAM_KEYWORDS} scrollTo={scrollTo}
        onChange={(next) => onLines(next.map(({ mark: _mark, title: _title, ...line }) => line))}
        className="pg-text" data-testid="programs-text" />
    </>
  );
}
