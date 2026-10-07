/** PHILO-14 B1 — AskWell: the agent's question at the top of its lane
 *  (board A-4).
 *
 *  `<AGENT> ASKS · <age>` as the caption, the question at the primary
 *  step, then the answer: a StringGadget (its mic: the voice law) and the
 *  Answer Button (primary; Enter in the field answers too). Under it, when
 *  the hub drafted one, the DRAFT line: the drafted words, **Use draft**,
 *  and the EgressChip that names where the draft was made. `egress` names
 *  where the answer itself goes, beside Answer (egress where egress happens).
 */
import { useRef, type ReactNode, type Ref } from "react";
import { EgressChip, StringGadget } from "../gadgets";
import { Button } from "../../../components/signal/Signal";
import "./objects.css";

export interface AskWellProps {
  /** `Claude Code` → the caption `CLAUDE CODE ASKS`. */
  agent: string;
  /** `6 min`. */
  age?: string;
  question: string;
  value: string;
  onChange(next: string): void;
  onAnswer(answer: string): void;
  /** The drafted answer (the hub drafts one per wait). */
  draft?: string;
  onUseDraft?(draft: string): void;
  /** Where the draft was made (the egress chip's host and scope). */
  draftEgress?: { label: string; scope?: "local" | "mixed" | "cloud" | "remote" };
  /** Where the ANSWER goes when it is sent (the Answer action's egress),
   *  drawn beside Answer whether or not a draft exists. */
  egress?: { label: string; scope?: "local" | "mixed" | "cloud" | "remote" };
  busy?: boolean;
  /** The answer cannot be sent now (no session to send it to): Answer is
   *  disabled, without the busy spinner; the field stays open. */
  disabled?: boolean;
  /** Each new value starts the field's mic (a Speak answer press). */
  listenSignal?: number;
  /** The mic's draft scope: a recovered capture lands there. */
  draftScope?: string;
  /** The answer field, for a caller that focuses it. */
  inputRef?: Ref<HTMLInputElement>;
  /** The hand's gate beside Answer (Secure / Normal: `MODE · ARM FIRST`
   *  and the ARM key), drawn after the egress chip; wraps at 393. */
  arm?: ReactNode;
  /** Pass-through data-testid for the root `section`. */
  "data-testid"?: string;
}

export function AskWell({
  agent,
  age,
  question,
  value,
  onChange,
  onAnswer,
  draft,
  onUseDraft,
  draftEgress,
  egress,
  busy,
  disabled,
  listenSignal,
  draftScope,
  inputRef,
  arm,
  "data-testid": testId,
}: AskWellProps) {
  const caption = [`${agent.toUpperCase()} ASKS`, age?.toUpperCase()].filter(Boolean).join(" · ");
  const field = useRef<HTMLInputElement | null>(null);
  // An empty answer is never sent: the press takes you to the field.
  const send = () => {
    if (busy || disabled) return;
    if (value.trim()) onAnswer(value.trim());
    else field.current?.focus();
  };
  return (
    <section className="ask-well" aria-label={`${agent} asks`} data-testid={testId}>
      <p className="ask-well-caption">{caption}</p>
      <p className="ask-well-question">{question}</p>
      <div className="ask-well-answer">
        <StringGadget
          label="Answer"
          value={value}
          onChange={onChange}
          placeholder="Say or type the answer"
          micLabel="Speak the answer"
          disabled={busy}
          micStartSignal={listenSignal}
          micDraftScope={draftScope}
          inputRef={(el) => {
            field.current = el;
            if (typeof inputRef === "function") inputRef(el);
            else if (inputRef) (inputRef as { current: HTMLInputElement | null }).current = el;
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.nativeEvent.isComposing) {
              event.preventDefault();
              send();
            }
          }}
        />
        <Button variant="primary" onClick={send} loading={busy} disabled={disabled}>
          Answer
        </Button>
        {egress ? <EgressChip label={egress.label} scope={egress.scope} /> : null}
        {arm ?? null}
      </div>
      {draft ? (
        <div className="ask-well-draft">
          <span className="ask-well-draft-word">Draft</span>
          <span className="ask-well-draft-text">{draft}</span>
          {onUseDraft ? (
            <Button dense variant="ghost" onClick={() => onUseDraft(draft)}>
              Use draft
            </Button>
          ) : null}
          {draftEgress ? <EgressChip label={draftEgress.label} scope={draftEgress.scope} /> : null}
        </div>
      ) : null}
    </section>
  );
}
