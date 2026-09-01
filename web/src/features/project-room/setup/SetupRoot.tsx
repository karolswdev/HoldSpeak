// HS-159-05 -- the setup composition root: SurfaceColumns for
// question-plane + live-brief at >=560px container; brief follows
// in DOM order below (WEB-RSP-005).  This is a CoreProps-compatible
// component loaded by the SurfaceWindow system.

import { useContext, useEffect, useRef, useState } from "react";
import { SurfaceColumns } from "../../../desk/surface/Surface";
import { TitleSlotContext } from "../../../desk/surface/title";
import type { CoreProps } from "../../../pages/cores/core-types";
import { STAGE_META, STAGE_COUNT } from "./model";
import { useSetupController } from "./useSetupController";
import { SetupInterview } from "./SetupInterview";
import { SetupBrief } from "./SetupBrief";
import { SuggestionCards } from "./SuggestionCards";
import { ClarifyStep } from "./ClarifyStep";
import { ActivationReview } from "./ActivationReview";
import "./setup.css";

export function SetupCore({ scope }: CoreProps) {
  const ctrl = useSetupController();
  const setTitle = useContext(TitleSlotContext);
  const [clarifyingId, setClarifyingId] = useState<string | null>(null);

  // Set window title
  useEffect(() => {
    setTitle?.("New Project");
  }, [setTitle]);

  const rootRef = useRef<HTMLDivElement | null>(null);
  // Announce stage changes (WEB-A11Y-008) + keep the top of each stage in frame
  useEffect(() => {
    rootRef.current?.scrollIntoView({ block: "start" });
    const el = document.getElementById("setup-stage-announce");
    if (el) {
      const labels: Record<string, string> = {
        loading: "Loading setup",
        outcome: "Step 1: Define outcome",
        signals: "Step 2: Define signals",
        proposals: "Select Watch suggestions",
        review: "Review before activation",
        finalizing: "Creating project",
        done: "Project created",
        abandoned: "Setup abandoned",
        error: "Setup error",
      };
      el.textContent = labels[ctrl.state.kind] ?? "";
    }
  }, [ctrl.state.kind]);

  // The clarifying proposal
  const clarifyingProposal =
    clarifyingId && (ctrl.state.kind === "proposals" || ctrl.state.kind === "review")
      ? ctrl.state.proposals.find((p) => p.id === clarifyingId) ?? null
      : null;

  // Done state: surface has already opened the project room
  if (ctrl.state.kind === "done") {
    return (
      <div className="setup-root" data-testid="setup-done">
        <div className="setup-done" aria-live="polite">
          Project created. Opening Project Room...
        </div>
      </div>
    );
  }

  // Abandoned
  if (ctrl.state.kind === "abandoned") {
    return (
      <div className="setup-root" data-testid="setup-abandoned">
        <div className="setup-abandoned">Setup abandoned. No project was created.</div>
      </div>
    );
  }

  // Review stage -- NO brief panel: review IS the brief; every fact once (fix 2)
  if (ctrl.state.kind === "review") {
    return (
      <div className="setup-root" data-testid="setup-root" ref={rootRef}>
        <div className="sr-only" id="setup-stage-announce" aria-live="polite" role="status" />
        <ActivationReview
          outcomeAnswer={ctrl.state.outcomeAnswer}
          signalsAnswer={ctrl.state.signalsAnswer}
          proposals={ctrl.state.proposals}
          onFinalize={ctrl.finalize}
          onBack={ctrl.backToProposals}
          finalizing={false}
        />
      </div>
    );
  }

  // Finalizing
  if (ctrl.state.kind === "finalizing") {
    return (
      <div className="setup-root" data-testid="setup-root" ref={rootRef}>
        <div className="sr-only" id="setup-stage-announce" aria-live="polite" role="status" />
        <SurfaceColumns
          main={
            <SetupInterview
              state={ctrl.state}
              error={ctrl.error}
              onSubmitOutcome={ctrl.submitOutcome}
              onSubmitSignals={ctrl.submitSignals}
              onEditOutcome={ctrl.editOutcome}
              onEditSignals={ctrl.editSignals}
              onSetDraft={ctrl.setDraft}
            />
          }
          side={<SetupBrief state={ctrl.state} />}
        />
      </div>
    );
  }

  // Main flow: questions + proposals
  return (
    <div className="setup-root" data-testid="setup-root" ref={rootRef}>
      <div className="sr-only" id="setup-stage-announce" aria-live="polite" role="status" />
      <SurfaceColumns
        main={
          <>
            <SetupInterview
              state={ctrl.state}
              error={ctrl.error}
              onSubmitOutcome={ctrl.submitOutcome}
              onSubmitSignals={ctrl.submitSignals}
              onEditOutcome={ctrl.editOutcome}
              onEditSignals={ctrl.editSignals}
              onSetDraft={ctrl.setDraft}
            />

            {/* Suggestion cards (after both questions answered) */}
            {ctrl.state.kind === "proposals" ? (
              <>
                {/* Step indicator for proposals stage (defect 6) */}
                <div className="setup-step-token" aria-hidden="true" data-testid="setup-step-token">
                  Step {STAGE_META["proposals"].index} of {STAGE_COUNT}
                </div>
                {clarifyingProposal ? (
                  <ClarifyStep
                    proposal={clarifyingProposal}
                    onClarify={ctrl.clarifyProp}
                    onDone={() => setClarifyingId(null)}
                  />
                ) : (
                  <SuggestionCards
                    proposals={ctrl.state.proposals}
                    onSelect={(id) => {
                      void ctrl.selectProp(id);
                    }}
                    onDeselect={(id) => {
                      void ctrl.deselectProp(id);
                    }}
                    onTest={(id) => {
                      void ctrl.testProp(id);
                    }}
                    suggesting={ctrl.state.suggesting}
                  />
                )}

                {/* Proceed to review */}
                {ctrl.state.proposals.length > 0 && !clarifyingProposal ? (
                  <div className="setup-proceed">
                    <button
                      type="button"
                      className="setup-proceed-btn"
                      onClick={ctrl.advanceToReview}
                      data-testid="setup-proceed-review"
                    >
                      Review and activate
                    </button>
                    <button
                      type="button"
                      className="setup-proceed-blank"
                      onClick={ctrl.finalize}
                      data-testid="setup-proceed-blank"
                    >
                      Create blank Project
                    </button>
                  </div>
                ) : null}

                {/* Blank path explicit (INT-002) */}
                {ctrl.state.proposals.length === 0 && !ctrl.state.suggesting ? (
                  <div className="setup-proceed">
                    <button
                      type="button"
                      className="setup-proceed-btn"
                      onClick={ctrl.finalize}
                      data-testid="setup-proceed-blank"
                    >
                      Create blank Project
                    </button>
                  </div>
                ) : null}
              </>
            ) : null}
          </>
        }
        side={<SetupBrief state={ctrl.state} />}
      />

      {/* Abandon */}
      {ctrl.state.kind !== "loading" && ctrl.state.kind !== "error" ? (
        <div className="setup-abandon">
          <button
            type="button"
            className="setup-abandon-btn"
            onClick={ctrl.abandon}
          >
            Cancel setup
          </button>
        </div>
      ) : null}
    </div>
  );
}
