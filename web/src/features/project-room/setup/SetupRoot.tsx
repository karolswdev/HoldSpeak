// HS-159-05 -- the setup composition root: SurfaceColumns for
// question-plane + live-brief at >=560px container; brief follows
// in DOM order below (WEB-RSP-005).  This is a CoreProps-compatible
// component loaded by the SurfaceWindow system.
// HS-168-04: TOOLS row from GET /api/connections above suggestions;
// wizard heading = ledger row; ProgressPlan scoped steps; verbs
// Back / Test this Watch -> Use this Watch; connect card opens
// Settings -> Connections in place; the re-read mechanism on
// windowsById subscription.

import { useContext, useEffect, useRef, useState } from "react";
import { SurfaceColumns } from "../../../desk/surface/Surface";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import { ProgressPlan, type PlanStep } from "../../../desk/surface/patterns/ProgressPlan";
import { TitleSlotContext } from "../../../desk/surface/title";
import { Button } from "../../../components/signal/Signal";
import type { CoreProps } from "../../../pages/cores/core-types";
import { STAGE_META, STAGE_COUNT } from "./model";
import { useSetupController } from "./useSetupController";
import { SetupInterview } from "./SetupInterview";
import { SetupBrief } from "./SetupBrief";
import { SuggestionCards } from "./SuggestionCards";
import { ToolsRow } from "./ToolsRow";
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
  // The TOOLS row the disconnected-card click scrolls to (never a global DOM query).
  const toolsRowRef = useRef<HTMLDivElement | null>(null);
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

  // HS-167-04: ProgressPlan steps computed from state
  const stateKind = ctrl.state.kind;
  const stepStatus = (step: string): PlanStep["status"] => {
    const order = ["outcome", "signals", "proposals", "review"];
    const stepIdx = order.indexOf(step);
    const kindIdx = order.indexOf(
      stateKind === "finalizing" || stateKind === "done" ? "done" : stateKind,
    );
    if (stateKind === "finalizing" || stateKind === "done") return "done";
    if (stepIdx < kindIdx) return "done";
    if (stepIdx === kindIdx) return "running";
    return "queued";
  };
  const setupSteps: PlanStep[] = [
    { id: "outcome", label: "Outcome", status: stepStatus("outcome") },
    { id: "notice", label: "Notice", status: stepStatus("signals") },
    { id: "sources", label: "Sources", status: stepStatus("proposals") },
    { id: "review", label: "Review", status: stepStatus("review") },
  ];

  const stepIndex =
    stateKind === "outcome" ? 1
    : stateKind === "signals" ? 2
    : stateKind === "proposals" ? 3
    : stateKind === "review" ? 4
    : stateKind === "finalizing" ? 4
    : 0;
  const stepLabel = stepIndex > 0 ? `${stepIndex} of ${STAGE_COUNT}` : "";

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
        <ProgressPlan steps={setupSteps} compact />
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
        <ProgressPlan steps={setupSteps} compact />
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
          side={<SetupBrief state={ctrl.state} connectionTools={ctrl.connectionTools} />}
        />
      </div>
    );
  }

  // Main flow: questions + proposals
  return (
    <div className="setup-root" data-testid="setup-root" ref={rootRef}>
      <div className="sr-only" id="setup-stage-announce" aria-live="polite" role="status" />
      <ProgressPlan steps={setupSteps} compact />
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
                {/* HS-161-05 + HS-166-04: provider wizard takes priority when active */}
                {providerWizardId && wizardProposal && wizardProposal.providerId === "github" ? (
                  <ProviderWizardFlow
                    proposal={wizardProposal}
                    connection={ctrl.providerConnection}
                    discovery={ctrl.providerDiscovery}
                    checking={ctrl.providerChecking}
                    discovering={ctrl.providerDiscovering}
                    scopeState={ctrl.providerScopeState}
                    knownScopes={ctrl.knownScopes}
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
                    onBack={() => {
                      setProviderWizardId(null);
                      ctrl.resetProviderState();
                      // HS-168-04: Back restores the pre-wizard selection state
                      if (wizardProposal.state === "selected") {
                        void ctrl.deselectProp(wizardProposal.id);
                      }
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
                    knownScopes={ctrl.knownScopes}
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
                    onBack={() => {
                      setProviderWizardId(null);
                      ctrl.resetJiraState();
                      // HS-168-04: Back restores the pre-wizard selection state
                      if (wizardProposal.state === "selected") {
                        void ctrl.deselectProp(wizardProposal.id);
                      }
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
                  <>
                    {/* HS-168-04: TOOLS row -- connector-pack providers from GET /api/connections */}
                    <ToolsRow
                    rootRef={toolsRowRef}
                      tools={ctrl.connectionTools}
                      onConnect={ctrl.openConnectionsInPlace}
                      onRecheck={() => void ctrl.readConnections()}
                    />
                    <SuggestionCards
                      proposals={ctrl.state.proposals}
                      onSelect={(id) => {
                        // HS-168-04: disconnected provider cards light the TOOLS connect card
                        const prop = ctrl.state.kind === "proposals"
                          ? ctrl.state.proposals.find((p) => p.id === id)
                          : undefined;
                        const conn = prop?.connection;
                        if (conn && conn.state !== "connected" && (prop?.providerId === "github" || prop?.providerId === "jira")) {
                          // Scroll to the TOOLS row connect card
                          toolsRowRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
                          return;
                        }
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
                  </>
                )}

                {/* Proceed/blank verbs moved to SurfaceFooter */}
              </>
            ) : null}
          </>
        }
        side={<SetupBrief state={ctrl.state} connectionTools={ctrl.connectionTools} />}
      />

      {/* Footer: receipt · Cancel · primary (hidden when wizard is active -- wizard has its own) */}
      {ctrl.state.kind !== "loading" && ctrl.state.kind !== "error" && !providerWizardId ? (
        <SurfaceFooter
          receipt={
            stepLabel ? (
              <span className="surface-footer-receipt-line" data-testid="setup-step-count">{stepLabel}</span>
            ) : undefined
          }
          verbs={
            <>
              <Button dense variant="ghost" className="setup-abandon-btn" onClick={ctrl.abandon}>
                Cancel setup
              </Button>
              {/* D2: Next always present during interview, disabled when empty */}
              {ctrl.state.kind === "outcome" ? (
                <Button
                  dense
                  variant="primary"
                  disabled={!("draft" in ctrl.state && (ctrl.state as { draft: string }).draft.trim())}
                  onClick={() => {
                    if ("draft" in ctrl.state) void ctrl.submitOutcome((ctrl.state as { draft: string }).draft);
                  }}
                  data-testid="setup-next"
                >
                  Next
                </Button>
              ) : null}
              {ctrl.state.kind === "signals" ? (
                <Button
                  dense
                  variant="primary"
                  disabled={!("draft" in ctrl.state && (ctrl.state as { draft: string }).draft.trim())}
                  onClick={() => {
                    if ("draft" in ctrl.state) void ctrl.submitSignals((ctrl.state as { draft: string }).draft);
                  }}
                  data-testid="setup-next"
                >
                  Next
                </Button>
              ) : null}
              {ctrl.state.kind === "proposals" && ctrl.state.proposals.length > 0 && !clarifyingProposal && !providerWizardId ? (
                <Button dense variant="primary" onClick={ctrl.advanceToReview} data-testid="setup-proceed-review">
                  Review and activate
                </Button>
              ) : null}
              {ctrl.state.kind === "proposals" && (ctrl.state.proposals.length === 0 && !ctrl.state.suggesting) ? (
                <Button dense variant="primary" onClick={ctrl.finalize} data-testid="setup-proceed-blank">
                  Create blank Project
                </Button>
              ) : null}
            </>
          }
        />
      ) : null}
    </div>
  );
}
