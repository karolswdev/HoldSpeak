/* QuestionRow (PG-LANG §9.4, §11; direction R-A): one question that
 * changes a plan, in place.
 *
 * The question in 15/600 ink, why it matters in muted words under it, up to
 * three offered answers as plated library Buttons, a StringGadget with its
 * mic for his own words, Answer (Return sends) and Skip question. While the
 * engine reads his answer, a breathing line says so (the host passes it).
 * It is not a form: one question at a time; the host folds an answered one
 * to a `QuestionFold` line. At the phone width the row stacks: the offered
 * answers in a column, the field under them, 44 px targets. */
import { type KeyboardEvent, type ReactNode } from "react";
import "./question-row.css";
import { Button } from "../../components/signal/Signal";
import { StringGadget } from "./gadgets";

export function QuestionRow({
  question,
  why,
  choices = [],
  value,
  onChange,
  onAnswer,
  onSkip,
  busy,
  reading,
  failure,
  "data-testid": testId,
}: {
  question: string;
  why?: string | null;
  /** Up to three short answers he can press. */
  choices?: readonly string[];
  value: string;
  onChange(next: string): void;
  /** His answer: his own words, or the offered answer he pressed. */
  onAnswer(words: string, choice?: string): void;
  onSkip(): void;
  busy?: boolean;
  /** The breathing line while the engine reads the answer. */
  reading?: ReactNode;
  failure?: ReactNode;
  "data-testid"?: string;
}) {
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey && value.trim()) {
      event.preventDefault();
      onAnswer(value.trim());
    }
  };
  return (
    <section className="kit-question" aria-label="Question" data-busy={busy ? "" : undefined} data-testid={testId}>
      <p className="kit-question-text">{question}</p>
      {why ? <p className="kit-question-why">{why}</p> : null}
      {choices.length ? (
        <div className="kit-question-choices" role="group" aria-label="Offered answers">
          {choices.slice(0, 3).map((choice) => (
            <Button key={choice} dense variant="secondary" className="kit-question-choice" disabled={busy}
              onClick={() => onAnswer(choice, choice)} data-testid="kit-question-choice">{choice}</Button>
          ))}
        </div>
      ) : null}
      <div className="kit-question-answer">
        <StringGadget label="Your answer" placeholder="Your answer" value={value} onChange={onChange} onKeyDown={onKeyDown}
          disabled={busy} micLabel="Speak your answer" />
        <Button dense variant="secondary" disabled={busy || !value.trim()} loading={busy}
          onClick={() => onAnswer(value.trim())} data-testid="kit-question-answer">Answer</Button>
        <Button dense variant="ghost" disabled={busy} onClick={onSkip} data-testid="kit-question-skip">Skip question</Button>
      </div>
      {reading ?? null}
      {failure ?? null}
    </section>
  );
}

/** An answered question, folded to one line: `? Where does it run · = In the hub  → step 1 owns`. */
export function QuestionFold({ question, answer, became, skipped, "data-testid": testId }: {
  question: string;
  answer?: string | null;
  became?: readonly string[];
  skipped?: boolean;
  "data-testid"?: string;
}) {
  return (
    <div className="kit-question-fold" data-skipped={skipped ? "" : undefined} data-testid={testId}>
      <span className="kit-question-fold-q" aria-hidden="true">?</span>
      <span className="kit-question-fold-text">{question}</span>
      <span className="kit-question-fold-answer">{skipped ? "Skipped" : `= ${answer ?? ""}`}</span>
      {became?.length ? <span className="kit-question-fold-became">{`→ ${became.join(", ")}`}</span> : null}
    </div>
  );
}
