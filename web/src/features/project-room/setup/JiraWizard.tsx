// HS-166-04 round 2 -- the Jira face, composed from the surface library.
// HS-168-04: auth folds GONE from the interview; Account step = pick only
// (skipped when exactly one connection); known-scope card on Project step;
// heading = ledger row; ProgressPlan [Account .] Project . Population . Test;
// verbs Back / Test this Watch -> Use this Watch; Test enabled by a picked
// project (Preview = quiet verb, never a gate).

import { useCallback, useEffect, useState } from "react";
import {
  ChoiceCard,
  ChoiceCardGroup,
  ChoiceCardShell,
  StateChip,
  ProvenanceChip,
  Receipt,
  ProgressPlan,
  type PlanStep,
  SurfaceSection,
  SurfaceFacts,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
  GadgetGroup,
  GadgetRow,
  CheckGadget,
  StringGadget,
  EgressChip,
} from "../../../desk/surface";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import { Button } from "../../../components/signal/Signal";
import type {
  JiraConnection,
  JiraKnownAccount,
  JiraDiscoveryResponse,
  JiraSearchResult,
  JiraScope,
  SetupProposal,
  KnownScopes,
} from "./model";
import { cadenceLabel, conditionLabel, actionLabel, transitionLabel, plural, formatDueToken } from "./model";
import "./jira-wizard.css";

/* ── Helpers ── */

function siteInitial(site: string): string {
  return (site[0] ?? "?").toUpperCase();
}

function connChipState(state: string): "success" | "warning" | "failure" | "unreachable" {
  if (state === "connected") return "success";
  if (state === "owner_action_required") return "warning";
  if (state === "capability_missing") return "unreachable";
  return "failure";
}

function connChipLabel(state: string): string {
  if (state === "connected") return "Connected";
  if (state === "owner_action_required") return "Sign in";
  if (state === "capability_missing") return "acli missing";
  if (state === "unavailable") return "Unavailable";
  return "Disconnected";
}

function formatTime(iso: string): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

/* ═══════════════════════════════════════════════════════════════════
   D1 — Accounts step (pick only -- auth folds moved to Connections)
   ═══════════════════════════════════════════════════════════════════ */

export function JiraAccountsStep({
  connections,
  selectedRef,
  onSelect,
  onNext,
}: {
  connections: JiraConnection[];
  selectedRef: string | null;
  onSelect: (ref: string) => void;
  onNext: () => void;
}) {
  const connectedCount = connections.filter((c) => c.state === "connected").length;

  return (
    <div data-testid="jira-accounts-step">
      <SurfaceSection label="ACCOUNT">
        <ChoiceCardGroup
          name="jira-account"
          value={selectedRef}
          onChange={onSelect}
          ariaLabel="Jira accounts"
          layout="row"
        >
          {connections.map((conn) => {
            const site = conn.account.site;
            return (
              <ChoiceCard
                key={conn.connection_ref}
                value={conn.connection_ref}
                name="jira-account"
                selectedValue={selectedRef}
                onChange={onSelect}
                label={site}
                summary={conn.account.email}
                emblem={siteInitial(site)}
              >
                <div className="jira-inline-chips">
                  <StateChip state={connChipState(conn.state)} label={connChipLabel(conn.state)} />
                  <ProvenanceChip source="acli" boundary={site} />
                </div>
              </ChoiceCard>
            );
          })}
        </ChoiceCardGroup>
      </SurfaceSection>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   D2 — Scope step (project cards + population gadget sheet)
   ═══════════════════════════════════════════════════════════════════ */

export function JiraScopeStep({
  projects,
  issueTypes,
  statuses,
  scope,
  preview,
  site,
  knownScopes,
  proposalId,
  onSelectProject,
  onToggleType,
  onToggleStatus,
  onJqlChange,
  onPreview,
  onSearchProjects,
  discovering,
  previewing,
  onApplyKnownScope,
}: {
  projects: JiraDiscoveryResponse | null;
  issueTypes: JiraDiscoveryResponse | null;
  statuses: JiraDiscoveryResponse | null;
  scope: JiraScope;
  preview: JiraSearchResult | null;
  site: string;
  knownScopes: KnownScopes;
  proposalId: string;
  onSelectProject: (key: string) => void;
  onToggleType: (name: string) => void;
  onToggleStatus: (category: string) => void;
  onJqlChange: (jql: string) => void;
  onPreview: () => void;
  onSearchProjects: (query?: string) => void;
  discovering: boolean;
  previewing: boolean;
  onApplyKnownScope: (projectKey: string) => void;
}) {
  const selectedProject = scope.projects[0] ?? null;

  const statusItems = statuses?.items ?? [];
  const distinctCategories = new Set(statusItems.map((s) => s.category).filter(Boolean));
  const totalStatusCategories = statuses?.categories?.length ?? 3;

  // Known-scope card for Jira
  const knownJira = knownScopes.jira.find((ks) => ks.forProposalId !== proposalId && ks.projectKey);

  return (
    <div data-testid="jira-scope-step">
      <SurfaceSection label="PROJECT">
        {/* Known-scope card (offered, never applied) */}
        {knownJira ? (
          <ChoiceCardShell
            label={`${knownJira.projectKey}`}
            summary={`chosen for ${knownJira.watchName ?? "another Watch"}`}
            tier="balanced"
            data-testid="known-scope-card"
          >
            <Button dense variant="ghost" onClick={() => onApplyKnownScope(knownJira.projectKey!)} data-testid="known-scope-use">
              Use this project
            </Button>
          </ChoiceCardShell>
        ) : null}

        {/* Project cards */}
        <ChoiceCardGroup
          name="jira-project"
          value={selectedProject}
          onChange={onSelectProject}
          ariaLabel="Projects"
          layout="row"
        >
          {(projects?.items ?? []).map((proj) => (
            <ChoiceCard
              key={proj.id}
              value={proj.key ?? proj.id}
              name="jira-project"
              selectedValue={selectedProject}
              onChange={onSelectProject}
              label={proj.name}
              emblem={proj.key ?? proj.id}
              tier={scope.projects.includes(proj.key ?? proj.id) ? "ok" : undefined}
              facts={[
                ...(proj.type ? [{ label: "type", value: proj.type }] : []),
                ...(proj.style ? [{ label: "style", value: proj.style }] : []),
              ]}
            >
              <ProvenanceChip source="acli" boundary={site} />
            </ChoiceCard>
          ))}
        </ChoiceCardGroup>
      </SurfaceSection>

      {/* Population sheet */}
      {selectedProject ? (
        <div className="jira-population-gap">
        <GadgetGroup label="Population">
          {/* Types (enumerated) */}
          {issueTypes && issueTypes.items.length > 0 ? (
            <GadgetRow label="Types" fact="enumerated" wide>
              <div className="jira-toggle-row">
                {issueTypes.items.map((it) => (
                  <label key={it.id} className="jira-toggle-label">
                    <CheckGadget
                      label={it.name}
                      checked={scope.issueTypes.includes(it.name)}
                      onChange={() => onToggleType(it.name)}
                    />
                    <span className="jira-toggle-text">{it.name}</span>
                  </label>
                ))}
              </div>
            </GadgetRow>
          ) : null}

          {/* Status (observed) */}
          {statusItems.length > 0 ? (
            <GadgetRow label="Status" fact="observed" wide>
              <div className="jira-toggle-row">
                {statusItems.map((st) => (
                  <label key={st.id} className="jira-toggle-label">
                    <CheckGadget
                      label={st.name}
                      checked={scope.statusCategories.includes(st.category ?? "")}
                      onChange={() => onToggleStatus(st.category ?? "")}
                    />
                    <span className="jira-toggle-text">{st.name}</span>
                  </label>
                ))}
                <StateChip state="idle" label={`${distinctCategories.size} of ${totalStatusCategories} categories seen`} />
              </div>
            </GadgetRow>
          ) : null}

          {/* Due */}
          <GadgetRow label="Due" wide highlight>
            <div className="jira-toggle-row">
              <label className="jira-toggle-label">
                <CheckGadget label="Within 7 days" checked={false} onChange={() => {}} />
                <span className="jira-toggle-text">Within 7 days</span>
              </label>
              <label className="jira-toggle-label">
                <CheckGadget label="Overdue" checked={false} onChange={() => {}} />
                <span className="jira-toggle-text">Overdue</span>
              </label>
            </div>
          </GadgetRow>

          {/* JQL (optional) */}
          <GadgetRow label={<>JQL<br /><small className="jira-fact-sub">optional</small></>} wide>
            <StringGadget
              label="JQL"
              value={scope.jql}
              onChange={onJqlChange}
              placeholder="assignee = currentUser()"
            />
          </GadgetRow>
        </GadgetGroup>
        </div>
      ) : null}

      {/* Preview (quiet verb -- not a gate) */}
      {selectedProject ? (
        <Button
          dense
          variant="ghost"
          onClick={onPreview}
          disabled={previewing}
          data-testid="jira-preview-btn"
        >
          {previewing ? "Previewing..." : "Preview"}
        </Button>
      ) : null}

      {/* Preview result */}
      {preview && !preview.errorCode ? (
        <div data-testid="jira-preview">
          <SurfaceLedger count={plural(preview.items.length, "issue")}>
            <ul className="surface-ledger-rows">
              {preview.items.slice(0, 5).map((item) => (
                <SurfaceLedgerRow
                  key={item.key}
                  lead={item.key}
                  primary={item.summary}
                  cells={
                    <>
                      <StateChip
                        state={item.statusCategory === "done" ? "success" : item.statusCategory === "indeterminate" ? "working" : "idle"}
                        label={item.status}
                      />
                      {item.dueDate ? <span className="jira-wizard-token">{formatDueToken(item.dueDate)}</span> : null}
                    </>
                  }
                  expands={false}
                  data-testid={`jira-preview-${item.key}`}
                />
              ))}
            </ul>
          </SurfaceLedger>
        </div>
      ) : null}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   D3 — Test step
   ═══════════════════════════════════════════════════════════════════ */

export function JiraTestStep({
  proposal,
  site,
  email,
}: {
  proposal: SetupProposal;
  site: string;
  email: string;
}) {
  const tr = proposal.testResult;
  const isPassed = proposal.testState === "passed";
  const isFailed = proposal.testState === "failed";
  const testDone = isPassed || isFailed;
  const stepStatus: PlanStep["status"] = isPassed ? "done" : isFailed ? "failed" : "queued";

  const projects = tr?.projects ?? [];
  const entityCount = tr?.entityCount ?? 0;
  const calls = tr?.calls ?? 0;
  const durationMs = tr?.durationMs ?? 0;
  const representativeEntities = tr?.representativeEntities ?? [];

  const enrichCount = Math.max(0, calls - 1);

  const steps: PlanStep[] = [
    { id: "switch", label: `Switch to ${site}`, status: testDone ? stepStatus : "queued" },
    { id: "readback", label: `Read back account`, status: testDone ? stepStatus : "queued" },
    { id: "search", label: `Search ${projects[0] ?? "project"}`, status: testDone ? stepStatus : "queued", rate: testDone ? `${entityCount} found` : undefined },
    { id: "enrich", label: "Enrich", status: testDone ? stepStatus : "queued", rate: testDone ? `${enrichCount} of ${entityCount}` : undefined },
    { id: "baseline", label: "Baseline ready", status: testDone ? stepStatus : "queued", rate: testDone ? `${(durationMs / 1000).toFixed(1)}s` : undefined },
  ];

  return (
    <div data-testid="jira-test-step">
      <SurfaceSection label="TEST">
        <ProgressPlan
          steps={steps}
          receipt={
            testDone ? (
              <Receipt
                status={isPassed ? "ok" : "danger"}
                label={isPassed ? "Passed" : "Failed"}
                timestamp={tr?.observedAt ? formatTime(tr.observedAt) : undefined}
              />
            ) : undefined
          }
          egress={<ProvenanceChip source="acli" boundary={site} />}
          ariaLabel="Jira watch test"
        />
      </SurfaceSection>

      {/* Matches */}
      {testDone ? (
        <SurfaceSection label={`MATCHES ${entityCount}`}>
          {entityCount === 0 ? (
            <StateChip
              state="success"
              label="0 matches"
            />
          ) : representativeEntities.length > 0 ? (
            <SurfaceLedger count={`${representativeEntities.length} shown`}>
              <ul className="surface-ledger-rows">
                {representativeEntities.slice(0, 5).map((entity: Record<string, unknown>, i: number) => {
                  const key = String(entity.key ?? entity.id ?? "");
                  const summary = String(entity.summary ?? entity.title ?? "");
                  const status = String(entity.status ?? "");
                  const due = entity.due_at ?? entity.duedate ?? null;

                  return (
                    <SurfaceLedgerRow
                      key={i}
                      lead={key}
                      primary={summary}
                      cells={
                        <>
                          <StateChip
                            state={status.toLowerCase().includes("done") ? "success" : status.toLowerCase().includes("progress") ? "working" : "idle"}
                            label={status}
                          />
                          {due ? <span className="jira-wizard-token">{formatDueToken(String(due))}</span> : null}
                        </>
                      }
                      expands={false}
                      data-testid={`jira-match-${key}`}
                    />
                  );
                })}
              </ul>
            </SurfaceLedger>
          ) : null}
        </SurfaceSection>
      ) : null}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   JiraWizardFlow — sequences [accounts ->] scope -> test
   ═══════════════════════════════════════════════════════════════════ */

type WizardStep = "accounts" | "scope" | "test";

export function JiraWizardFlow({
  proposal,
  connections,
  knownAccounts,
  selectedRef,
  projects,
  issueTypes,
  statuses,
  scope,
  preview,
  loading,
  discovering,
  previewing,
  knownScopes,
  onLoadConnections,
  onAddConnection,
  onRecheckConnection,
  onSelectConnection,
  onSelectProject,
  onToggleType,
  onToggleStatus,
  onJqlChange,
  onPreview,
  onSearchProjects,
  onClarifyScope,
  onTest,
  onBack,
  onDone,
  onUpdateScope,
}: {
  proposal: SetupProposal;
  connections: JiraConnection[];
  knownAccounts: JiraKnownAccount[];
  selectedRef: string | null;
  projects: JiraDiscoveryResponse | null;
  issueTypes: JiraDiscoveryResponse | null;
  statuses: JiraDiscoveryResponse | null;
  scope: JiraScope;
  preview: JiraSearchResult | null;
  loading: boolean;
  discovering: boolean;
  previewing: boolean;
  knownScopes: KnownScopes;
  onLoadConnections: () => void;
  onAddConnection: (site: string, email: string) => void;
  onRecheckConnection: (ref: string) => void;
  onSelectConnection: (ref: string) => void;
  onSelectProject: (key: string) => void;
  onToggleType: (name: string) => void;
  onToggleStatus: (category: string) => void;
  onJqlChange: (jql: string) => void;
  onPreview: () => void;
  onSearchProjects: (query?: string) => void;
  onClarifyScope: () => void | Promise<unknown>;
  onTest: () => void;
  onBack: () => void;
  onDone: () => void;
  onUpdateScope: (partial: Partial<JiraScope>) => void;
}) {
  // HS-168-04: auto-skip accounts when exactly one connection exists (D2/D4)
  const skipAccounts = connections.length === 1;
  const [step, setStep] = useState<WizardStep>(skipAccounts ? "scope" : "accounts");

  useEffect(() => {
    if (connections.length === 0 && !loading) {
      onLoadConnections();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-skip + auto-select when exactly one connection.
  // selectConnection already discovers projects (the controller does it).
  useEffect(() => {
    if (connections.length === 1 && !selectedRef) {
      onSelectConnection(connections[0].connection_ref);
      if (step === "accounts") {
        setStep("scope");
      }
    }
  }, [connections.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedConn = connections.find((c) => c.connection_ref === selectedRef);
  const site = selectedConn?.account.site ?? "";
  const email = selectedConn?.account.email ?? "";

  const hasPassed = proposal.testState === "passed";
  const hasScope = scope.projects.length > 0;

  // HS-168-04: ProgressPlan wizard steps
  const showAccountStep = !skipAccounts;
  const wizardSteps: PlanStep[] = [
    ...(showAccountStep ? [{ id: "account", label: "Account", status: (step === "scope" || step === "test" ? "done" : "running") as PlanStep["status"] }] : []),
    { id: "project", label: "Project", status: step === "test" ? "done" : step === "scope" ? "running" : "queued" },
    { id: "population", label: "Population", status: step === "test" && hasPassed ? "done" : step === "test" ? "running" : "queued" },
    { id: "test", label: "Test", status: hasPassed ? "done" : step === "test" ? "running" : "queued" },
  ];

  const goToScope = useCallback(() => {
    if (selectedRef) {
      onSearchProjects();
      setStep("scope");
    }
  }, [selectedRef, onSearchProjects]);

  const goToTest = useCallback(async () => {
    setStep("test");
    await onClarifyScope();
    onTest();
  }, [onClarifyScope, onTest]);

  // HS-168-04: apply known scope for Jira
  const handleApplyKnownScope = useCallback((projectKey: string) => {
    onSelectProject(projectKey);
  }, [onSelectProject]);

  // The Jira egress host
  const egressHost = site || "Jira";

  return (
    <div className="jira-wizard-flow" data-testid="jira-wizard-flow" role="region" aria-label={`Configure: ${proposal.spec.name}`}>
      {/* HS-168-04: heading = the Watch's ledger row as a flex composition */}
      <div className="setup-wizard-heading" data-testid="wizard-heading">
        <span className="setup-wizard-heading-name" data-testid="wizard-heading-name">
          {proposal.spec.name}
        </span>
        <span className="surface-token" data-chip>{cadenceLabel(proposal.spec.trigger)}</span>
        <span className="surface-token" data-chip>{proposal.spec.action.kind === "project.observe" ? "observe" : proposal.spec.action.kind}</span>
        <ProvenanceChip source="acli" boundary={site || egressHost} />
      </div>

      {/* Wizard ProgressPlan */}
      <ProgressPlan steps={wizardSteps} compact />

      {step === "accounts" ? (
        <JiraAccountsStep
          connections={connections}
          selectedRef={selectedRef}
          onSelect={onSelectConnection}
          onNext={goToScope}
        />
      ) : null}

      {step === "scope" ? (
        <JiraScopeStep
          projects={projects}
          issueTypes={issueTypes}
          statuses={statuses}
          scope={scope}
          preview={preview}
          site={site}
          knownScopes={knownScopes}
          proposalId={proposal.id}
          onSelectProject={(key) => {
            onSelectProject(key);
            const current = scope.projects;
            if (!current.includes(key)) {
              if (current.length === 0) {
                setTimeout(() => {
                  onToggleType("");
                }, 100);
              }
            }
          }}
          onToggleType={onToggleType}
          onToggleStatus={onToggleStatus}
          onJqlChange={onJqlChange}
          onPreview={onPreview}
          onSearchProjects={onSearchProjects}
          discovering={discovering}
          previewing={previewing}
          onApplyKnownScope={handleApplyKnownScope}
        />
      ) : null}

      {step === "test" ? (
        <JiraTestStep
          proposal={proposal}
          site={site}
          email={email}
        />
      ) : null}

      {/* Footer: EgressChip + Back + Test this Watch / Use this Watch */}
      <SurfaceFooter
        egress={<EgressChip label={egressHost} scope="mixed" title={`This Watch reads from ${egressHost}.`} />}
        receipt={hasPassed ? (
          <Receipt status="ok" label="Passed" timestamp={proposal.testResult?.observedAt ? formatTime(proposal.testResult.observedAt) : undefined} />
        ) : hasScope ? (
          <Receipt status="ok" label="Scoped" />
        ) : undefined}
        verbs={
          <>
            <Button dense variant="ghost" onClick={step === "accounts" ? onBack : step === "scope" && showAccountStep ? () => setStep("accounts") : onBack} data-testid="jira-wizard-back">
              Back
            </Button>
            {step === "accounts" ? (
              <Button dense variant="primary" disabled={!selectedRef} onClick={goToScope} data-testid="jira-choose-project">
                Choose project
              </Button>
            ) : hasPassed ? (
              <Button dense variant="primary" onClick={onDone} data-testid="jira-wizard-done">
                Use this Watch
              </Button>
            ) : (
              <Button
                dense
                variant="primary"
                disabled={!hasScope}
                onClick={goToTest}
                data-testid="jira-test-btn"
              >
                Test this Watch
              </Button>
            )}
          </>
        }
      />
    </div>
  );
}
