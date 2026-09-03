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
import { ProviderWizardFlow } from "./ProviderWizardStep";
import { JiraWizardFlow } from "./JiraWizard";
import "./setup.css";

export function SetupCore({ scope }: CoreProps) {
  const ctrl = useSetupController();
  const setTitle = useContext(TitleSlotContext);
  const [clarifyingId, setClarifyingId] = useState<string | null>(null);
  const [providerWizardId, setProviderWizardId] = useState<string | null>(null);

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

  // The provider wizard proposal (HS-161-05)
  const wizardProposal =
    providerWizardId && (ctrl.state.kind === "proposals" || ctrl.state.kind === "review")
      ? ctrl.state.proposals.find((p) => p.id === providerWizardId) ?? null
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
                {/* HS-161-05 + HS-166-04: provider wizard takes priority when active */}
                {providerWizardId && wizardProposal && wizardProposal.providerId === "github" ? (
                  <ProviderWizardFlow
                    proposal={wizardProposal}
                    connection={ctrl.providerConnection}
                    discovery={ctrl.providerDiscovery}
                    checking={ctrl.providerChecking}
                    discovering={ctrl.providerDiscovering}
                    scopeState={ctrl.providerScopeState}
                    onCheckConnection={ctrl.checkConnection}
                    onRecheck={ctrl.recheckConnection}
                    onDiscover={ctrl.discoverRepos}
                    onValidateRepo={ctrl.validateRepo}
                    onClarifyScope={(repo) =>
                      ctrl.clarifyProposalScope(wizardProposal.id, repo)
                    }
                    onTest={() => {
                      void ctrl.testProp(wizardProposal.id);
                    }}
                    onDone={() => {
                      setProviderWizardId(null);
                      ctrl.resetProviderState();
                    }}
                  />
                ) : providerWizardId && wizardProposal && wizardProposal.providerId === "jira" ? (
                  <JiraWizardFlow
                    proposal={wizardProposal}
                    connections={ctrl.jiraConnections}
                    knownAccounts={ctrl.jiraKnownAccounts}
                    selectedRef={ctrl.selectedJiraRef}
                    projects={ctrl.jiraProjects}
                    issueTypes={ctrl.jiraIssueTypes}
                    statuses={ctrl.jiraStatuses}
                    scope={ctrl.jiraScope}
                    preview={ctrl.jiraPreview}
                    loading={ctrl.jiraLoading}
                    discovering={ctrl.jiraDiscovering}
                    previewing={ctrl.jiraPreviewing}
                    onLoadConnections={ctrl.loadJiraConnections}
                    onAddConnection={ctrl.addJiraConnection}
                    onRecheckConnection={ctrl.recheckJiraConnection}
                    onSelectConnection={ctrl.selectJiraConnection}
                    onSelectProject={(key) => {
                      const current = ctrl.jiraScope.projects;
                      const next = current.includes(key)
                        ? current.filter((k) => k !== key)
                        : [...current, key];
                      ctrl.updateJiraScope({ projects: next });
                      // Auto-discover types/statuses for the first selected project
                      if (!current.includes(key) && next.length === 1) {
                        void ctrl.discoverJiraTypes(key);
                        void ctrl.discoverJiraStatuses(key);
                      }
                    }}
                    onToggleType={(name) => {
                      const current = ctrl.jiraScope.issueTypes;
                      const next = current.includes(name)
                        ? current.filter((n) => n !== name)
                        : [...current, name];
                      ctrl.updateJiraScope({ issueTypes: next });
                    }}
                    onToggleStatus={(category) => {
                      const current = ctrl.jiraScope.statusCategories;
                      const next = current.includes(category)
                        ? current.filter((c) => c !== category)
                        : [...current, category];
                      ctrl.updateJiraScope({ statusCategories: next });
                    }}
                    onJqlChange={(jql) => ctrl.updateJiraScope({ jql })}
                    onPreview={() => {
                      // Preview with user JQL if provided, otherwise
                      // with a project-scoped query from the scope.
                      const jql = ctrl.jiraScope.jql.trim()
                        || (ctrl.jiraScope.projects.length > 0
                          ? `project in (${ctrl.jiraScope.projects.map((p) => `"${p}"`).join(", ")})`
                          : "");
                      if (jql) {
                        void ctrl.previewJiraPopulation(jql);
                      }
                    }}
                    onSearchProjects={(q) => void ctrl.discoverJiraProjects(q)}
                    onClarifyScope={() =>
                      ctrl.clarifyJiraProposalScope(wizardProposal.id)
                    }
                    onTest={() => {
                      void ctrl.testProp(wizardProposal.id);
                    }}
                    onDone={() => {
                      setProviderWizardId(null);
                      ctrl.resetJiraState();
                    }}
                    onUpdateScope={ctrl.updateJiraScope}
                  />
                ) : clarifyingProposal ? (
                  <ClarifyStep
                    proposal={clarifyingProposal}
                    onClarify={ctrl.clarifyProp}
                    onDone={() => setClarifyingId(null)}
                  />
                ) : (
                  <SuggestionCards
                    proposals={ctrl.state.proposals}
                    onSelect={(id) => {
                      // HS-161-05 + HS-166-04: provider proposals enter the wizard
                      const prop = ctrl.state.kind === "proposals"
                        ? ctrl.state.proposals.find((p) => p.id === id)
                        : undefined;
                      void ctrl.selectProp(id);
                      if (prop?.providerId === "github") {
                        setProviderWizardId(id);
                        void ctrl.checkConnection();
                      } else if (prop?.providerId === "jira") {
                        setProviderWizardId(id);
                        void ctrl.loadJiraConnections();
                      }
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

                {/* Proceed to review (hidden while provider wizard is active) */}
                {ctrl.state.proposals.length > 0 && !clarifyingProposal && !providerWizardId ? (
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
