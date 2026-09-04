// HS-167-04 — the question plane recomposed on the surface library.
// SurfaceSection label = the question word (OUTCOME / NOTICE); helper = placeholder.
// AnswerRow = SurfaceLedgerRow (lead ✓, primary = answer, wrap, trailing Edit).

import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import {
  SurfaceSection,
  SurfaceLedgerRow,
} from "../../../desk/surface/Surface";
import { MicButton } from "../../../desk/surface/controls/MicButton";
import { Button } from "../../../components/signal/Signal";
import { QUESTION_TEXT, Q_OUTCOME, Q_SIGNALS, type SetupAnswer } from "./model";
import type { ControllerState } from "./useSetupController";

const QUESTION_LABEL: Record<string, string> = {
  [Q_OUTCOME]: "OUTCOME",
  [Q_SIGNALS]: "NOTICE",
};

const QUESTION_PLACEHOLDER: Record<string, string> = {
  [Q_OUTCOME]: QUESTION_TEXT[Q_OUTCOME],
  [Q_SIGNALS]: QUESTION_TEXT[Q_SIGNALS],
};

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

/* ── QuestionStep: SurfaceSection label + well with mic ── */

function QuestionStep({
  questionId,
  questionText,
  draft,
  onDraft,
  onSubmit,
}: {
  questionId: string;
  questionText: string;
  draft: string;
  onDraft: (text: string) => void;
  onSubmit: (text: string) => void;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    textareaRef.current?.focus();
  }, [questionId]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        if (draft.trim() && !submitting) {
          setSubmitting(true);
          onSubmit(draft);
        }
      }
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

  const handleVoice = useCallback(
    (text: string) => {
      onDraft(draft ? `${draft} ${text}` : text);
    },
    [draft, onDraft],
  );

  return (
    <div data-testid={`setup-question-${questionId}`}>
      <SurfaceSection label={QUESTION_LABEL[questionId] ?? questionId.toUpperCase()}>
        <div className="setup-well-container">
          <textarea
            ref={textareaRef}
            id={`setup-input-${questionId}`}
            className="setup-well-textarea"
            value={draft}
            onChange={(e) => onDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={QUESTION_PLACEHOLDER[questionId] ?? questionText}
            rows={3}
            disabled={submitting}
            aria-label={questionText}
          />
          <div className="setup-well-mic">
            <MicButton
              onText={handleVoice}
              label="Speak your answer"
            />
          </div>
        </div>
      </SurfaceSection>
    </div>
  );
}

/* ── AnswerRow: SurfaceLedgerRow (lead ✓, primary = answer, wrap, trailing Edit) ── */

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

  const handleVoice = useCallback(
    (text: string) => {
      setEditDraft((prev) => (prev ? `${prev} ${text}` : text));
    },
    [],
  );

  if (editing) {
    return (
      <div data-testid={`setup-answer-${questionId}`}>
        <div className="setup-well-container">
          <textarea
            ref={inputRef}
            className="setup-well-textarea"
            value={editDraft}
            onChange={(e) => setEditDraft(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
          />
          <div className="setup-well-mic">
            <MicButton onText={handleVoice} label="Speak" />
          </div>
        </div>
        <div className="setup-answer-verb-row">
          <Button dense variant="primary" onClick={handleSave}>Save</Button>
          <Button dense variant="ghost" onClick={() => { setEditDraft(answer.answer.normalized); setEditing(false); }}>Cancel</Button>
        </div>
      </div>
    );
  }

  return (
    <div data-testid={`setup-answer-${questionId}`}>
      <ul className="surface-ledger-rows">
        <SurfaceLedgerRow
          lead={"✓"}
          primary={<span className="setup-answer-text">{answer.answer.normalized}</span>}
          wrap
          trailing={
            <Button dense variant="ghost" onClick={() => setEditing(true)} aria-label={`Edit answer for: ${questionText}`}>
              Edit
            </Button>
          }
          expands={false}
        />
      </ul>
    </div>
  );
}
