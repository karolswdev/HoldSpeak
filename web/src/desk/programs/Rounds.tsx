/* Programs: the interview rounds (PROGRAM-LANGUAGE-2026-10-31 §6.2, §6.5
 * station 3, §9.4 direction R-A, §9.6, §9.7; LANG10; PROGRAM-JOURNEYS J1 and
 * "Reconciled"; canvas program-language-2026-10-31, the interview panel).
 *
 * The round strip over the board: Architecture · Product · Stack ·
 * Verification · Delivery as FilterTokens, each with its state lamp (open
 * hollow, asking breathing, done ok and "n changes", skipped struck
 * through), and the round's verbs at its right: Done with <round> (withheld
 * while a question waits), Skip round, Next question when none waits, Ask
 * more on a done or skipped round. Under it, ONE question in place (the kit's
 * QuestionRow): the question, why it matters, the offered answers as plated
 * Buttons, his own words with the mic, Skip question. The answered questions
 * of the round fold to one line each ("? … · = … → step 3 brief").
 *
 * His answer goes to the hub (one shaping call); its rows open in the
 * window's change well (source "round") and wait for Apply; the next
 * question rises in at once. Done with <round> and Skip round move on to
 * the next open round and ask its first question. Rounds never gate Start;
 * the strip stays while the Program runs (Ask more). */
import { useCallback, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { ApiError } from "../../lib/api";
import { DotWord, FilterTokens, QuestionFold, QuestionRow, type FilterTokenOption } from "../surface";
import { failureTitle } from "../surface/plainFailure";
import { answerRound, decideRound, nextQuestion, openRounds } from "./api";
import type { Program, ProgramRound, RoundAnswer, RoundState } from "./types";

type Failure = { words: string; title: string };

function failureOf(cause: unknown, words: string): Failure {
  const payload = cause instanceof ApiError ? (cause.payload as { code?: string; detail?: string } | null) : null;
  if (payload?.code === "no_engine") return { words: "No engine is set for planning", title: payload.detail ?? "" };
  return { words: payload?.detail ?? words, title: failureTitle(cause) };
}

const LAMP: Record<RoundState, FilterTokenOption["lamp"]> = { open: "idle", asking: "ask", done: "ok", skipped: undefined };

/** `4 changes` on a done round's token (the count stays for the session). */
function changesWords(n: number): string {
  return n === 1 ? "1 change" : `${n} changes`;
}

/** The round strip's tokens. */
export function roundTokens(rounds: readonly ProgramRound[]): FilterTokenOption[] {
  return rounds.map((round) => ({
    value: round.name,
    label: round.name,
    lamp: LAMP[round.state],
    live: round.state === "asking" && Boolean(round.waiting),
    struck: round.state === "skipped",
    aside: round.state === "done" && round.became ? `· ${changesWords(round.became)}` : undefined,
    ariaLabel: `${round.name} · ${round.state === "asking" ? "asking" : round.state}`,
  }));
}

/** The round the eye goes to: the one with a waiting question, else the one asking. */
function liveRound(rounds: readonly ProgramRound[]): string | null {
  return rounds.find((round) => round.waiting)?.name ?? rounds.find((round) => round.state === "asking")?.name ?? null;
}

/** The interview's state and its presses. `onAnswer` puts an answer's rows in
 *  the window's change well; `applyDraft` (Ask me first with the draft in the
 *  well) applies the draft first and says whether it landed. */
export function useRounds(program: Program | null, apply: (next: Program | null) => void, onAnswer: (answer: RoundAnswer) => void) {
  const [picked, setPicked] = useState<string | null>(null);
  const [busy, setBusy] = useState<"" | "ask" | "answer" | "press">("");
  const [failure, setFailure] = useState<Failure | null>(null);
  const [said, setSaid] = useState("");
  const rounds = program?.rounds ?? [];
  const current = (picked && rounds.some((round) => round.name === picked) ? picked : null) ?? liveRound(rounds);

  const ask = useCallback(async (name: string) => {
    if (!program) return;
    setPicked(name);
    setBusy("ask");
    setFailure(null);
    try {
      const answer = await nextQuestion(program.id, name);
      apply(answer.program);
    } catch (cause) {
      setFailure(failureOf(cause, "The question did not come. The program is unchanged. Try again."));
    } finally {
      setBusy("");
    }
  }, [apply, program]);

  /** The next round still open after `name` (in strip order), if any. */
  const nextOpen = (after: Program, name: string): string | null => {
    const list = after.rounds ?? [];
    const at = list.findIndex((round) => round.name === name);
    return [...list.slice(at + 1), ...list.slice(0, Math.max(at, 0))].find((round) => round.state === "open")?.name ?? null;
  };

  /** Ask me first: the rounds opened (the five defaults), the first question. */
  const askFirst = useCallback(async (applyDraft?: () => Promise<boolean>) => {
    if (!program) return;
    setBusy("ask");
    setFailure(null);
    try {
      if (applyDraft && !(await applyDraft())) return;
      const opened = (program.rounds ?? []).length ? null : await openRounds(program.id);
      if (opened) apply(opened.program);
      const list = (opened?.program ?? program).rounds ?? [];
      const first = liveRound(list) ?? list.find((round) => round.state === "open")?.name;
      if (first) await ask(first);
    } catch (cause) {
      setFailure(failureOf(cause, "The rounds did not open. The program is unchanged. Try again."));
    } finally {
      setBusy("");
    }
  }, [apply, ask, program]);

  const answer = useCallback(async (round: ProgramRound, words: string, choice?: string) => {
    if (!program || !round.waiting) return;
    setBusy("answer");
    setFailure(null);
    try {
      const out = await answerRound(program.id, round.name, {
        question_id: round.waiting, ...(choice ? { option: choice } : { answer: words }), apply: program.control === "yolo",
      });
      setSaid("");
      onAnswer(out);
      apply(out.program);
      // The next question rises in while the rows wait in the well.
      setBusy("");
      await ask(round.name);
    } catch (cause) {
      setFailure(failureOf(cause, "The answer did not reach the hub. Your words are kept. Try again."));
    } finally {
      setBusy("");
    }
  }, [apply, ask, onAnswer, program]);

  const press = useCallback(async (round: ProgramRound, verb: "skip_question" | "done" | "skip" | "reopen" | "not_this", questionId?: string) => {
    if (!program) return;
    setBusy("press");
    setFailure(null);
    try {
      const out = verb === "skip_question" || verb === "not_this"
        ? await answerRound(program.id, round.name, { question_id: questionId ?? round.waiting ?? "", ...(verb === "skip_question" ? { skip: true } : { not_this: true }) })
        : await decideRound(program.id, round.name, verb);
      apply(out.program);
      setBusy("");
      if (verb === "reopen") await ask(round.name);
      else if (verb === "done" || verb === "skip") {
        // The interview goes on with the next open round.
        const next = nextOpen(out.program, round.name);
        if (next) await ask(next);
        else setPicked(round.name);
      }
    } catch (cause) {
      setFailure(failureOf(cause, "The press did not land. The program is unchanged. Try again."));
    } finally {
      setBusy("");
    }
  }, [apply, ask, program]);

  return { rounds, current, pick: setPicked, ask, askFirst, answer, press, busy, failure, said, setSaid };
}

/** The strip over the board and the one question under it. Nothing when the
 *  Program has no rounds or is done. */
export function RoundPanel({ program, rounds: state, engine }: {
  program: Program;
  rounds: ReturnType<typeof useRounds>;
  engine?: string | null;
}) {
  const { rounds, current, busy, failure } = state;
  if (!rounds.length || program.state === "done") return null;
  const round = rounds.find((item) => item.name === current) ?? null;
  const waiting = round?.questions.find((question) => question.id === round.waiting) ?? null;
  const folded = round ? round.questions.filter((question) => question.id !== round.waiting) : [];
  const closed = round ? round.state === "done" || round.state === "skipped" : false;
  const pick = (name: string) => {
    const next = rounds.find((item) => item.name === name);
    state.pick(name);
    if (next && next.state === "open" && !next.waiting && !next.asked) void state.ask(name);
  };
  return (
    <section className="pg-rounds" aria-label="Rounds" data-testid="program-rounds">
      <div className="pg-round-strip" data-testid="program-round-strip">
        <span className="pg-round-label">Rounds</span>
        <FilterTokens label="Rounds" options={roundTokens(rounds)} value={current ?? ""} onChange={pick}
          disabled={Boolean(busy)} className="pg-round-tokens" />
        {round ? (
          <span className="pg-round-verbs">
            {closed ? (
              <Button dense variant="secondary" disabled={Boolean(busy)} onClick={() => void state.press(round, "reopen")}
                data-testid="program-round-ask-more">Ask more</Button>
            ) : (
              <>
                {!waiting ? (
                  <Button dense variant="secondary" loading={busy === "ask"} disabled={Boolean(busy)} onClick={() => void state.ask(round.name)}
                    data-testid="program-round-next">Next question</Button>
                ) : null}
                <Button dense variant="secondary" disabled={Boolean(busy) || Boolean(waiting)}
                  title={waiting ? "A question waits" : undefined}
                  onClick={() => void state.press(round, "done")} data-testid="program-round-done">{`Done with ${round.name}`}</Button>
                <Button dense variant="ghost" disabled={Boolean(busy)} onClick={() => void state.press(round, "skip")}
                  data-testid="program-round-skip">Skip round</Button>
              </>
            )}
          </span>
        ) : null}
      </div>
      {folded.map((question) => (
        <QuestionFold key={question.id} question={question.text} answer={question.answer} became={question.became}
          skipped={question.skipped && !question.answer} data-testid="program-round-fold" />
      ))}
      {round && waiting ? (
        <QuestionRow key={waiting.id} question={waiting.text} why={waiting.why} choices={waiting.choices}
          value={state.said} onChange={state.setSaid} busy={busy === "answer" || busy === "press"}
          onAnswer={(words, choice) => void state.answer(round, words, choice)}
          onSkip={() => void state.press(round, "skip_question", waiting.id)}
          reading={busy === "answer" ? (
            <DotWord tone="info" live className="pg-round-reading" data-testid="program-round-reading">
              {engine ? `Reading your answer · ${engine}` : "Reading your answer"}
            </DotWord>
          ) : null}
          data-testid="program-question" />
      ) : busy === "ask" ? (
        <DotWord tone="ask" live className="pg-round-reading" data-testid="program-round-asking">
          {engine ? `Asking · ${engine}` : "Asking"}
        </DotWord>
      ) : null}
      {failure ? (
        <p className="pg-failure" role="status" title={failure.title} data-testid="program-round-failure">{failure.words}</p>
      ) : null}
    </section>
  );
}
