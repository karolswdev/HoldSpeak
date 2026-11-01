/* Programs: the planning draft (PROGRAM-LANGUAGE-2026-10-31 §5, §6.5
 * station 2, §9.3, §9.7; LANG7; canvas program-language-2026-10-31, the
 * planning draft panel).
 *
 * In Drafting, Plan it (the toolbar's verb, and Return in the Goal pad)
 * sends his goal to the planning engine (POST …/plan/draft). While the
 * engine reads, one line breathes "Planning · <engine>" and the window stays
 * usable. The answer is change rows: they open in the window's change well
 * (source "plan") with the counts as its head ("4 steps · 7 requirements")
 * and the engine's name and time; each added step's row has its size lamp
 * ("7k of 32k"); a step that does not fit says "Too big for qwen · 41k of
 * 32k" and has Split. Apply writes the steps and requirements through the
 * text; the rows are born on the board one after the other. Not this keeps
 * the Program as it was. A refusal (no engine, an answer it could not read)
 * is one line in place of the lamp, with its verbs. */
import { useCallback, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError } from "../../lib/api";
import { openSurfaceOr } from "../shell";
import { DotWord } from "../surface";
import { failureTitle } from "../surface/plainFailure";
import { applyPrograms, planDraft, readShapeEngine } from "./api";
import { openProgram } from "./open";
import { StationTrack } from "./StationTrack";
import { engineFact, useShapeEngine } from "./ShapeBar";
import type { TextProposal } from "./ProgramText";
import type { PlanAnswer, Program } from "./types";

type Refusal = { words: string; title: string; code: string };

function refusalOf(cause: unknown): Refusal {
  const payload = cause instanceof ApiError ? (cause.payload as { code?: string; detail?: string } | null) : null;
  const code = payload?.code ?? "";
  if (code === "no_engine") return { words: "No engine is set for planning", title: payload?.detail ?? "", code };
  if (payload?.detail) return { words: payload.detail, title: failureTitle(cause), code };
  return { words: "The goal did not reach the hub. The program is unchanged. Try again.", title: failureTitle(cause), code: "unreachable" };
}

/** The draft's rows as a proposal of the change well. */
export function planProposal(answer: PlanAnswer): TextProposal {
  return {
    source: "plan", text: answer.proposed_text, base: answer.base, answer,
    say: answer.words || answer.say, fact: engineFact(answer),
  };
}

/** Plan it: the hub call, its state and its one line. */
export function usePlanIt(programId: string, program: Program | null, onAnswer: (proposal: TextProposal) => void) {
  const engine = useShapeEngine(programId);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);

  const plan = useCallback(async (goal?: string) => {
    if (!program || busy) return;
    // The engine's read may not have landed yet: read it now, as the bar does
    // (a press before it sent the plan and drew the hub's 409 on the console).
    const known = engine === undefined ? await readShapeEngine(program.id).then((answer) => answer?.engine ?? null, () => undefined) : engine;
    if (known === null) {
      // The hub said no engine plans on this desk: nothing is sent or guessed.
      setRefusal({ words: "No engine is set for planning", title: "No engine is set for planning. The program is unchanged. Choose one in Engines.", code: "no_engine" });
      return;
    }
    setBusy(true);
    setRefusal(null);
    try {
      // The budget is the Program's (its text's `budget` line, else the
      // window of the engine pi runs on): the hub reads it.
      const body: { goal?: string } = {};
      if (goal != null && goal.trim() && goal !== program.goal) body.goal = goal;
      onAnswer(planProposal(await planDraft(program.id, body)));
    } catch (cause) {
      setRefusal(refusalOf(cause));
    } finally {
      setBusy(false);
    }
  }, [busy, engine, onAnswer, program]);

  /** Split one step of the draft in the well (its place in the draft). */
  const split = useCallback(async (proposal: TextProposal, place: number) => {
    if (!program) return;
    onAnswer(planProposal(await planDraft(program.id, { text: proposal.text, split: place })));
  }, [onAnswer, program]);

  return { plan, split, busy, refusal, engine, dismiss: () => setRefusal(null) };
}

/** The one line under the goal: the breathing lamp while the engine reads,
 *  or the refusal with its verbs. Nothing when there is nothing to say. */
export function PlanLine({ planner, onOpenText }: { planner: ReturnType<typeof usePlanIt>; onOpenText(): void }) {
  if (planner.busy) {
    return (
      <DotWord tone="info" live className="pg-plan-line" data-testid="program-plan-reading">
        {planner.engine ? `Planning · ${planner.engine}` : "Planning"}
      </DotWord>
    );
  }
  const refusal = planner.refusal;
  if (!refusal) return null;
  return (
    <div className="pg-plan-line pg-shape-refusal" role="status" title={refusal.title || undefined} data-testid="program-plan-refusal">
      <span>{refusal.words}</span>
      {refusal.code === "no_engine" ? (
        <>
          <Button dense variant="ghost" onClick={() => openSurfaceOr("configure-runs-on", "/settings", "models")}
            data-testid="program-plan-engines">Open Engines</Button>
          <Button dense variant="ghost" onClick={onOpenText} data-testid="program-plan-text">Open text</Button>
        </>
      ) : (
        <Button dense variant="ghost" onClick={() => void planner.plan()} data-testid="program-plan-retry">Try again</Button>
      )}
    </div>
  );
}

/** JRN1 (PROGRAM-JOURNEYS J1, PROGRAM-LANGUAGE §13b JRN1): the draft
 *  proposes several Programs when the goal is several goals. One row per
 *  proposed Program: its title, its goal's first line, its steps (a mini
 *  track, one hollow dot each) and what it hands the next; Apply this one
 *  on each row, Apply all and Not this on the well. The first is this
 *  Program; each other is a new Program in Drafting that waits on the one
 *  before it. The made Programs are named, with Open, in place. */
function stepsWords(steps: readonly string[]): string {
  const n = steps.length;
  return n === 1 ? "1 step" : `${n} steps`;
}

export function ProgramsSplitWell({ program, answer, onApplied, onDismiss }: {
  program: Program;
  answer: PlanAnswer;
  onApplied(next: Program | null): void;
  onDismiss(): void;
}) {
  const programs = answer.programs ?? [];
  const [busy, setBusy] = useState<string>("");
  const [failed, setFailed] = useState<Refusal | null>(null);
  const [made, setMade] = useState<{ id: string; title: string }[] | null>(null);
  const [done, setDone] = useState<Set<number>>(new Set());
  const apply = async (which: "all" | number) => {
    setBusy(String(which));
    setFailed(null);
    try {
      const out = await applyPrograms(program.id, programs.map(({ title, goal, text }) => ({ title, goal, text })), which);
      onApplied(out.program);
      setMade((now) => [...(now ?? []), ...out.made]);
      setDone((now) => new Set([...now, ...(which === "all" ? programs.map((_row, index) => index) : [which])]));
    } catch (cause) {
      setFailed(refusalOf(cause));
    } finally {
      setBusy("");
    }
  };
  const count = programs.length;
  const all = done.size >= count;
  return (
    <section className="pg-split" aria-label="The draft proposes several programs" data-testid="programs-split-well">
      <div className="pg-split-head">
        <b>{`Split into ${programs.length > 1 ? programs.length : 2} programs`}</b>
        <span className="pg-split-fact">{engineFact(answer)}</span>
        <span className="pg-split-verbs">
          {all ? (
            <Button dense variant="secondary" onClick={onDismiss} data-testid="programs-split-close">Done</Button>
          ) : (
            <>
              <Button dense variant="primary" loading={busy === "all"} disabled={Boolean(busy) || done.size > 0}
                onClick={() => void apply("all")} data-testid="programs-split-apply-all">Apply all</Button>
              <Button dense variant="ghost" disabled={Boolean(busy)} onClick={onDismiss} data-testid="programs-split-not-this">Not this</Button>
            </>
          )}
        </span>
      </div>
      <ol className="pg-split-rows">
        {programs.map((row, index) => (
          <li key={`${index}-${row.title}`} className="pg-split-row" data-testid="programs-split-row" data-done={done.has(index) ? "" : undefined}>
            <span className="pg-split-n" aria-hidden="true">{index + 1}</span>
            <span className="pg-split-words">
              <b className="pg-split-title">{row.title}</b>
              <span className="pg-split-goal">{row.goal.split("\n")[0]}</span>
              {row.hands ? <span className="pg-split-hands">{`Hands the next: ${row.hands}`}</span> : null}
            </span>
            <span className="pg-split-steps">
              <StationTrack stations={row.steps.map((title, place) => ({ key: String(place), word: title, state: "ahead" as const, tone: "idle" }))}
                label={stepsWords(row.steps)} />
              <span className="pg-split-count" data-testid="programs-split-steps">{stepsWords(row.steps)}</span>
            </span>
            <span className="pg-split-verb">
              {done.has(index) ? <DotWord tone="ok">{index === 0 ? "This program" : "Made"}</DotWord> : (
                <Button dense variant="ghost" loading={busy === String(index)} disabled={Boolean(busy)}
                  onClick={() => void apply(index)} data-testid="programs-split-apply-one">Apply this one</Button>
              )}
            </span>
          </li>
        ))}
      </ol>
      {made?.length ? (
        <p className="pg-split-made" data-testid="programs-split-made">
          {made.map((row) => (
            <Button key={row.id} dense variant="ghost" onClick={() => openProgram(row.id)}>{`Open ${row.title}`}</Button>
          ))}
        </p>
      ) : null}
      {failed ? <p className="pg-failure" role="status" title={failed.title} data-testid="programs-split-failure">{failed.words}</p> : null}
    </section>
  );
}
