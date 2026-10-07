/** PHILO-14 B1 — AskWell: the agent's question at the top of its lane
 *  (board A-4).
 *
 *  `<AGENT> ASKS · <age>` as the caption, the question at the primary
 *  step, then the answer: a StringGadget (its mic: the voice law) and the
 *  Answer Button (primary; Enter in the field answers too). Under it, when
 *  the hub drafted one, the DRAFT line: the drafted words, **Use draft**,
 *  and the EgressChip that names where the draft was made.
 */
import { useRef } from "react";
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
  busy?: boolean;
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
  busy,
}: AskWellProps) {
  const caption = [`${agent.toUpperCase()} ASKS`, age?.toUpperCase()].filter(Boolean).join(" · ");
  const field = useRef<HTMLInputElement | null>(null);
  // An empty answer is never sent: the press takes you to the field.
  const send = () => {
    if (value.trim()) onAnswer(value.trim());
    else field.current?.focus();
  };
  return (
    <section className="ask-well" aria-label={`${agent} asks`}>
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
          inputRef={field}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              send();
            }
          }}
        />
        <Button variant="primary" onClick={send} loading={busy}>
          Answer
        </Button>
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
