/** StepHeading: the heading of one numbered step in a setup pane.
 *
 *  A setup that has an order (make a bot, paste its token, connect a chat)
 *  shows each step with its number in a circle. The step that is his to do
 *  now is `current` (the circle is cobalt and filled); a step that is done
 *  shows a check; a step that waits for an earlier one is `later` (dimmed),
 *  and `after` says what it waits for ("After step 2"), as a short pill.
 *  The words are the heading of the group under it: give the same words to
 *  no second heading. One `h3`; its accessible name is "Step 2, done: Paste
 *  its token", so a screen reader hears the number and the state. */
import "./step-heading.css";

export type StepState = "current" | "done" | "later";

const STATE_WORD: Record<StepState, string> = { current: "", done: ", done", later: ", later" };

export function StepHeading({
  number,
  title,
  state = "current",
  after,
  testId,
}: {
  number: number;
  title: string;
  state?: StepState;
  /** What a later step waits for, in two or three words. */
  after?: string;
  testId?: string;
}) {
  return (
    <h3
      className="surface-step-heading"
      data-state={state}
      data-testid={testId}
      aria-label={`Step ${number}${STATE_WORD[state]}: ${title}`}
    >
      <span className="surface-step-heading-number" aria-hidden="true">
        {state === "done" ? "✓" : number}
      </span>
      <span className="surface-step-heading-title" aria-hidden="true">
        {title}
      </span>
      {state === "later" && after ? (
        <span className="surface-step-heading-after" aria-hidden="true">
          {after}
        </span>
      ) : null}
    </h3>
  );
}
