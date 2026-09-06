import { useState } from "react";
import { Button, Select } from "../../components/signal/Signal";
import { countLabel, countToken } from "../surface";
import { interviewCommand, type InterviewState } from "../interview";
import { useDesk } from "../store";
import "./interview.css";

interface Props {
  state: InterviewState;
  disabled: boolean;
  reload: () => Promise<void>;
  onTry: (text: string) => void;
}

export function InterviewPanel({ state, disabled, reload, onTry }: Props) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const facts = Object.values(state.facts);
  const suggestions = Object.values(state.suggestions);
  const current = suggestions.filter(
    (s) => s.section === state.section && s.disposition === "proposed",
  );
  const ideaCount = countToken(suggestions.length, "idea", "ideas");
  const visible = showAll ? suggestions : current.slice(0, 3);

  async function change(event: Record<string, unknown>, next?: () => void) {
    setPending(true);
    setError("");
    try {
      await interviewCommand(state, event);
      await reload();
      next?.();
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "Interview update failed",
      );
      try {
        await reload();
      } catch {
        /* The original failure remains visible. */
      }
    } finally {
      setPending(false);
    }
  }

  return (
    <section
      className="interview-panel"
      aria-label="Interview"
      aria-busy={pending}
    >
      <div className="interview-controls">
        <label htmlFor={`interview-section-${state.thread_id}`}>Section</label>
        <Select
          id={`interview-section-${state.thread_id}`}
          value={state.section}
          disabled={disabled || pending}
          onChange={(event) =>
            void change({ kind: "section", section: event.target.value })
          }
        >
          {state.sections.map((section) => (
            <option key={section.id} value={section.id}>
              {section.name}
            </option>
          ))}
        </Select>
        <Button
          type="button"
          dense
          variant="ghost"
          aria-expanded={expanded}
          onClick={() => setExpanded(!expanded)}
        >
          Context{ideaCount ? ` · ${ideaCount}` : ""}
        </Button>
        {state.status === "drafting" && (
          <Button
            type="button"
            dense
            variant="ghost"
            disabled={disabled || pending}
            onClick={() => void change({ kind: "status", status: "exploring" })}
          >
            Explore
          </Button>
        )}
      </div>
      {error && <div role="alert">{error}</div>}
      {state.section === "people" && (
        <Button
          type="button"
          dense
          variant="ghost"
          onClick={() => useDesk.getState().openPullout("people:people")}
        >
          Open People
        </Button>
      )}
      {expanded && (
        <div className="interview-context">
          <details>
            <summary>{countLabel("Known context", facts.length)}</summary>
            {facts.length === 0 && <span>No saved facts</span>}
            {facts.map((fact) => (
              <div className="interview-fact" key={fact.id}>
                <p>
                  {fact.text}{" "}
                  <small>
                    {fact.basis === "inferred" ? "Inferred" : "Your answer"}
                  </small>
                </p>
                <details>
                  <summary>Source</summary>
                  <blockquote>{fact.quote}</blockquote>
                </details>
                <Button
                  type="button"
                  dense
                  variant="ghost"
                  disabled={disabled || pending}
                  aria-label={`Remove fact: ${fact.text}`}
                  onClick={() =>
                    void change({ kind: "remove_fact", fact_id: fact.id })
                  }
                >
                  Remove
                </Button>
              </div>
            ))}
          </details>
          <h3>Suggestions</h3>
          {visible.length === 0 && <span>No new suggestions</span>}
          {visible.map((suggestion) => (
            <article className="interview-suggestion" key={suggestion.id}>
              <h4>{suggestion.title}</h4>
              <p>{suggestion.benefit}</p>
              <p>{suggestion.behavior}</p>
              <details>
                <summary>Reason & prerequisites</summary>
                <p>{suggestion.basis}</p>
                <p>{suggestion.prerequisites}</p>
              </details>
              <small>
                {
                  {
                    manual: "Manual draft",
                    needs_input: "Needs input",
                    needs_connection: "Needs connection",
                    unsupported_idea: "Idea · unavailable",
                  }[suggestion.feasibility]
                }{" "}
                · {suggestion.disposition}
              </small>
              <div className="interview-actions">
                {suggestion.feasibility === "manual" &&
                  suggestion.disposition === "proposed" && (
                    <Button
                      type="button"
                      dense
                      variant="ghost"
                      disabled={disabled || pending}
                      onClick={() =>
                        void change(
                          {
                            kind: "disposition",
                            suggestion_id: suggestion.id,
                            disposition: "try",
                          },
                          () =>
                            onTry(
                              `Prepare a manual draft for this suggestion: ${suggestion.title}. ${suggestion.behavior} Use the available evidence and identify gaps. This request is for draft preparation; keep configuration as proposals.`,
                            ),
                        )
                      }
                    >
                      Try draft
                    </Button>
                  )}
                {suggestion.disposition === "proposed" && (
                  <>
                    <Button
                      type="button"
                      dense
                      variant="ghost"
                      disabled={disabled || pending}
                      onClick={() =>
                        void change({
                          kind: "disposition",
                          suggestion_id: suggestion.id,
                          disposition: "kept",
                        })
                      }
                    >
                      Keep idea
                    </Button>
                    <Button
                      type="button"
                      dense
                      variant="ghost"
                      disabled={disabled || pending}
                      onClick={() =>
                        void change({
                          kind: "disposition",
                          suggestion_id: suggestion.id,
                          disposition: "deferred",
                        })
                      }
                    >
                      Later
                    </Button>
                    <Button
                      type="button"
                      dense
                      variant="ghost"
                      disabled={disabled || pending}
                      onClick={() =>
                        void change({
                          kind: "disposition",
                          suggestion_id: suggestion.id,
                          disposition: "dismissed",
                        })
                      }
                    >
                      Dismiss
                    </Button>
                  </>
                )}
              </div>
            </article>
          ))}
          {suggestions.length > 0 && (
            <Button
              type="button"
              dense
              variant="ghost"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll
                ? "Current suggestions"
                : countLabel("All suggestions", suggestions.length)}
            </Button>
          )}
        </div>
      )}
    </section>
  );
}
