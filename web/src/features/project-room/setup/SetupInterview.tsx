// HS-159-05 -- the question plane: ONE question at a time (INT-003),
// the two SS4 questions verbatim (WEB-CR-002), prior answers collapse
// into editable rows (SS4.2).  Enter submits, Shift+Enter newline,
// Cmd/Ctrl+Enter accepts (WEB-CMD-005).  Voice fills, never submits
// (WEB-CMD-006).  Announcements per WEB-A11Y-008.

import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import { MicButton } from "../../../desk/surface/controls/MicButton";
import { QUESTION_TEXT, Q_OUTCOME, Q_SIGNALS, type SetupAnswer } from "./model";
import type { ControllerState } from "./useSetupController";

export function SetupInterview({
  state,
  error,
  onSubmitOutcome,
  onSubmitSignals,
  onEditOutcome,
  onEditSignals,
  onSetDraft,
}: {
  state: ControllerState;
  error: string;
  onSubmitOutcome: (text: string) => void;
  onSubmitSignals: (text: string) => void;
  onEditOutcome: (text: string) => void;
  onEditSignals: (text: string) => void;
  onSetDraft: (text: string) => void;
}) {
  return (
    <div className="setup-interview" role="form" aria-label="Project setup interview">
      {error ? (
        <div className="setup-interview-error" role="alert">{error}</div>
      ) : null}

      {state.kind === "loading" ? (
        <div className="setup-interview-loading" aria-live="polite">
          Starting setup...
        </div>
      ) : null}

      {state.kind === "outcome" ? (
        <QuestionStep
          questionId={Q_OUTCOME}
          questionText={QUESTION_TEXT[Q_OUTCOME]}
          draft={state.draft}
          onDraft={onSetDraft}
          onSubmit={onSubmitOutcome}
          stepLabel="Step 1 of 2"
        />
      ) : null}

      {state.kind === "signals" ? (
        <>
          <AnswerRow
            questionId={Q_OUTCOME}
            questionText={QUESTION_TEXT[Q_OUTCOME]}
            answer={state.outcomeAnswer}
            onEdit={onEditOutcome}
          />
          <QuestionStep
            questionId={Q_SIGNALS}
            questionText={QUESTION_TEXT[Q_SIGNALS]}
            draft={state.draft}
            onDraft={onSetDraft}
            onSubmit={onSubmitSignals}
            stepLabel="Step 2 of 2"
          />
        </>
      ) : null}

      {(state.kind === "proposals" || state.kind === "review") ? (
        <>
          <AnswerRow
            questionId={Q_OUTCOME}
            questionText={QUESTION_TEXT[Q_OUTCOME]}
            answer={state.outcomeAnswer}
            onEdit={onEditOutcome}
          />
          <AnswerRow
            questionId={Q_SIGNALS}
            questionText={QUESTION_TEXT[Q_SIGNALS]}
            answer={state.signalsAnswer}
            onEdit={onEditSignals}
          />
        </>
      ) : null}

      {state.kind === "finalizing" ? (
        <div className="setup-interview-loading" aria-live="polite">
          Creating project...
        </div>
      ) : null}

      {state.kind === "error" ? (
        <div className="setup-interview-error" role="alert">
          {state.message}
        </div>
      ) : null}
    </div>
  );
}

/* ── QuestionStep: one active question at a time ── */

function QuestionStep({
  questionId,
  questionText,
  draft,
  onDraft,
  onSubmit,
  stepLabel,
}: {
  questionId: string;
  questionText: string;
  draft: string;
  onDraft: (text: string) => void;
  onSubmit: (text: string) => void;
  stepLabel: string;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [submitting, setSubmitting] = useState(false);

  // Focus the textarea on mount for keyboard-first flow
  useEffect(() => {
    textareaRef.current?.focus();
  }, [questionId]);

  // Announce the step (WEB-A11Y-008)
  useEffect(() => {
    const el = document.getElementById(`setup-step-announce-${questionId}`);
    if (el) el.textContent = `${stepLabel}: ${questionText}`;
  }, [questionId, stepLabel, questionText]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // Enter submits one-line answer; Shift+Enter = newline (WEB-CMD-005)
      if (e.key === "Enter" && !e.shiftKey && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        if (draft.trim() && !submitting) {
          setSubmitting(true);
          onSubmit(draft);
        }
      }
      // Cmd/Ctrl+Enter = accept (same as Enter for questions)
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        if (draft.trim() && !submitting) {
          setSubmitting(true);
          onSubmit(draft);
        }
      }
    },
    [draft, onSubmit, submitting],
  );

  // Voice fills, never submits (WEB-CMD-006)
  const handleVoice = useCallback(
    (text: string) => {
      onDraft(draft ? `${draft} ${text}` : text);
    },
    [draft, onDraft],
  );

  return (
    <div className="setup-question" data-testid={`setup-question-${questionId}`}>
      <div
        className="setup-question-step"
        aria-hidden="true"
      >
        {stepLabel}
      </div>
      <label
        className="setup-question-label"
        htmlFor={`setup-input-${questionId}`}
      >
        {questionText}
      </label>
      <div className="setup-question-input-row">
        <textarea
          ref={textareaRef}
          id={`setup-input-${questionId}`}
          className="setup-question-textarea"
          value={draft}
          onChange={(e) => onDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type or speak your answer..."
          rows={2}
          disabled={submitting}
          aria-describedby={`setup-step-announce-${questionId}`}
        />
        <MicButton
          onText={handleVoice}
          label="Speak your answer"
        />
      </div>
      <div
        id={`setup-step-announce-${questionId}`}
        className="sr-only"
        aria-live="polite"
        role="status"
      />
    </div>
  );
}

/* ── AnswerRow: collapsed previous answer, editable (SS4.2) ── */

function AnswerRow({
  questionId,
  questionText,
  answer,
  onEdit,
}: {
  questionId: string;
  questionText: string;
  answer: SetupAnswer;
  onEdit: (text: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editDraft, setEditDraft] = useState(answer.answer.normalized);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  const handleSave = useCallback(() => {
    if (editDraft.trim()) {
      onEdit(editDraft.trim());
      setEditing(false);
    }
  }, [editDraft, onEdit]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSave();
      }
      if (e.key === "Escape") {
        setEditDraft(answer.answer.normalized);
        setEditing(false);
      }
    },
    [handleSave, answer.answer.normalized],
  );

  // Voice fills (WEB-CMD-006)
  const handleVoice = useCallback(
    (text: string) => {
      setEditDraft((prev) => (prev ? `${prev} ${text}` : text));
    },
    [],
  );

  if (editing) {
    return (
      <div className="setup-answer-row setup-answer-row-editing" data-testid={`setup-answer-${questionId}`}>
        <div className="setup-answer-question">{questionText}</div>
        <div className="setup-question-input-row">
          <textarea
            ref={inputRef}
            className="setup-question-textarea"
            value={editDraft}
            onChange={(e) => setEditDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
          />
          <MicButton onText={handleVoice} label="Speak" />
        </div>
        <div className="setup-answer-actions">
          <button
            type="button"
            className="setup-answer-save"
            onClick={handleSave}
          >
            Save
          </button>
          <button
            type="button"
            className="setup-answer-cancel"
            onClick={() => {
              setEditDraft(answer.answer.normalized);
              setEditing(false);
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="setup-answer-row" data-testid={`setup-answer-${questionId}`}>
      <div className="setup-answer-question">{questionText}</div>
      <div className="setup-answer-text">{answer.answer.normalized}</div>
      <button
        type="button"
        className="setup-answer-edit"
        onClick={() => setEditing(true)}
        aria-label={`Edit answer for: ${questionText}`}
      >
        Edit
      </button>
    </div>
  );
}
