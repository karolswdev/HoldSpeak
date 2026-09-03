// HS-166-04 round 2 — the Jira face, composed from the surface library.
// D1 accounts = ChoiceCardGroup, D2 scope = project cards + gadget sheet,
// D3 test = ProgressPlan. Zero feature CSS restyling — layout only.

import { useCallback, useEffect, useState } from "react";
import {
  ChoiceCard,
  ChoiceCardGroup,
  ChoiceCardShell,
  StateChip,
  ProvenanceChip,
  Receipt,
  ActionNotice,
  ProgressPlan,
  type PlanStep,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceWell,
  GadgetGroup,
  GadgetRow,
  CheckGadget,
  StringGadget,
  LampGadget,
  TransportKey,
} from "../../../desk/surface";
import type {
  JiraConnection,
  JiraKnownAccount,
  JiraDiscoveryResponse,
  JiraSearchResult,
  JiraScope,
  SetupProposal,
  ProviderState,
} from "./model";
import { providerStateCopy, conditionLabel, actionLabel, transitionLabel, plural, cadenceLabel, formatDueToken } from "./model";
import "./jira-wizard.css";

/* ── Helpers ── */

function siteInitial(site: string): string {
  return (site[0] ?? "?").toUpperCase();
}

function connTier(state: string): string | undefined {
  if (state === "connected") return "ok";
  if (state === "owner_action_required") return "warn";
  return undefined;
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

const INLINE_CHIPS: React.CSSProperties = { display: "flex", flexWrap: "wrap", gap: "6px", alignItems: "center", width: "100%" };
const TOGGLE_LABEL: React.CSSProperties = { display: "inline-flex", alignItems: "center", gap: "6px", cursor: "pointer" };
const TOGGLE_TEXT: React.CSSProperties = { fontSize: "var(--text-xs)", fontFamily: "var(--font-mono, monospace)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.06em" };
const FACT_SUB: React.CSSProperties = { fontSize: "10px", color: "var(--text-tertiary)", textTransform: "uppercase", letterSpacing: "0.04em" };

/* ═══════════════════════════════════════════════════════════════════
   D1 — Accounts step
   ═══════════════════════════════════════════════════════════════════ */

export function JiraAccountsStep({
  connections,
  knownAccounts,
  selectedRef,
  onSelect,
  onRecheck,
  onAdd,
  onBack,
  onNext,
}: {
  connections: JiraConnection[];
  knownAccounts: JiraKnownAccount[];
  selectedRef: string | null;
  onSelect: (ref: string) => void;
  onRecheck: (ref: string) => void;
  onAdd: (site: string, email: string) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const [addSite, setAddSite] = useState("");
  const [addEmail, setAddEmail] = useState("");

  const handleAdd = useCallback(() => {
    const s = addSite.trim();
    const e = addEmail.trim();
    if (s && e) {
      onAdd(s, e);
      setAddSite("");
      setAddEmail("");
    }
  }, [addSite, addEmail, onAdd]);

  const addedRefs = new Set(connections.map((c) => c.connection_ref));
  const unaddedKnown = knownAccounts.filter((ka) => !addedRefs.has(ka.ref));
  const connectedCount = connections.filter((c) => c.state === "connected").length;

  return (
    <div data-testid="jira-accounts-step">
      <ChoiceCardGroup
        name="jira-account"
        value={selectedRef}
        onChange={onSelect}
        ariaLabel="Jira accounts"
        layout="row"
      >
        {connections.map((conn) => {
          const site = conn.account.site;
          const loginCmd = conn.recovery?.command ?? `acli jira auth login --site ${site} --email ${conn.account.email} --token`;
          const needsAuth = conn.state === "owner_action_required";

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
              tier={connTier(conn.state)}
              fold={needsAuth ? (
                <>
                  <SurfaceWell>
                    <code style={{ overflowWrap: "anywhere", font: "inherit" }}>{loginCmd}</code>
                    <TransportKey label="Copy" glyph="C" compact onClick={() => {
                      try { void navigator.clipboard.writeText(loginCmd); } catch { /* noop */ }
                    }} />
                  </SurfaceWell>
                  <button type="button" className="provider-action-btn" data-primary="" onClick={() => onRecheck(conn.connection_ref)}>
                    Recheck
                  </button>
                </>
              ) : undefined}
              foldLabel={needsAuth ? "Login command" : undefined}
            >
              {/* Inline chips row: state + provenance + verb */}
              <div style={INLINE_CHIPS}>
                <StateChip state={connChipState(conn.state)} label={connChipLabel(conn.state)} />
                <ProvenanceChip source="acli" boundary={site} />
                {!needsAuth ? (
                  <button type="button" className="provider-action-btn" onClick={() => onRecheck(conn.connection_ref)}>
                    Recheck
                  </button>
                ) : null}
              </div>
            </ChoiceCard>
          );
        })}

        {/* Known-to-acli cards */}
        {unaddedKnown.map((ka) => (
          <ChoiceCardShell
            key={ka.ref}
            label={ka.site}
            summary={ka.email}
            emblem={siteInitial(ka.site)}
            tier="cool"
            data-testid={`jira-known-${ka.ref}`}
          >
            <div style={INLINE_CHIPS}>
              <StateChip state="active" label="Known to acli" />
              <button type="button" className="provider-action-btn" onClick={() => onAdd(ka.site, ka.email)}>
                Use this account
              </button>
            </div>
          </ChoiceCardShell>
        ))}

        {/* Ghost add card */}
        <ChoiceCardShell
          label="Add account"
          emblem="+"
          data-testid="jira-add-card"
          className="jira-ghost-card"
        >
          <StringGadget label="Site" value={addSite} onChange={setAddSite} placeholder="site.atlassian.net" />
          <StringGadget label="Email" value={addEmail} onChange={setAddEmail} placeholder="email" />
          <button type="button" className="provider-action-btn" disabled={!addSite.trim() || !addEmail.trim()} onClick={handleAdd}>
            Add
          </button>
        </ChoiceCardShell>
      </ChoiceCardGroup>

      {/* Footer */}
      <div className="jira-wizard-footer">
        <LampGadget
          label={`${connectedCount} of ${connections.length} connected`}
          on={connectedCount > 0}
          tone={connectedCount > 0 ? "ok" : "warn"}
        />
        <span className="jira-wizard-spacer" />
        <button type="button" className="provider-action-btn" onClick={onBack}>Back</button>
        <button type="button" className="provider-action-btn" data-primary="" disabled={!selectedRef} onClick={onNext}>
          Choose project
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   D2 — Scope step
   ═══════════════════════════════════════════════════════════════════ */

export function JiraScopeStep({
  projects,
  issueTypes,
  statuses,
  scope,
  preview,
  site,
  onSelectProject,
  onToggleType,
  onToggleStatus,
  onJqlChange,
  onPreview,
  onSearchProjects,
  discovering,
  previewing,
  onBack,
  onTest,
}: {
  projects: JiraDiscoveryResponse | null;
  issueTypes: JiraDiscoveryResponse | null;
  statuses: JiraDiscoveryResponse | null;
  scope: JiraScope;
  preview: JiraSearchResult | null;
  site: string;
  onSelectProject: (key: string) => void;
  onToggleType: (name: string) => void;
  onToggleStatus: (category: string) => void;
  onJqlChange: (jql: string) => void;
  onPreview: () => void;
  onSearchProjects: (query?: string) => void;
  discovering: boolean;
  previewing: boolean;
  onBack: () => void;
  onTest: () => void;
}) {
  const selectedProject = scope.projects[0] ?? null;

  const statusItems = statuses?.items ?? [];
  const distinctCategories = new Set(statusItems.map((s) => s.category).filter(Boolean));
  // Jira has 3 fixed status categories (new, indeterminate, done).
  // The discover response carries a static `categories` list.
  const totalStatusCategories = statuses?.categories?.length ?? 3;

  return (
    <div data-testid="jira-scope-step">
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

      {/* Population sheet — 12px gap from the project cards */}
      {selectedProject ? (
        <div style={{ marginTop: "12px" }}>
        <GadgetGroup label="Population">
          {/* Types (enumerated) — wide row: inline label token + toggles */}
          {issueTypes && issueTypes.items.length > 0 ? (
            <GadgetRow label="Types" fact="enumerated" wide>
              <div className="jira-toggle-row">
                {issueTypes.items.map((it) => (
                  <label key={it.id} style={TOGGLE_LABEL}>
                    <CheckGadget
                      label={it.name}
                      checked={scope.issueTypes.includes(it.name)}
                      onChange={() => onToggleType(it.name)}
                    />
                    <span style={TOGGLE_TEXT}>{it.name}</span>
                  </label>
                ))}
              </div>
            </GadgetRow>
          ) : null}

          {/* Status (observed) — wide row */}
          {statusItems.length > 0 ? (
            <GadgetRow label="Status" fact="observed" wide>
              <div className="jira-toggle-row">
                {statusItems.map((st) => (
                  <label key={st.id} style={TOGGLE_LABEL}>
                    <CheckGadget
                      label={st.name}
                      checked={scope.statusCategories.includes(st.category ?? "")}
                      onChange={() => onToggleStatus(st.category ?? "")}
                    />
                    <span style={TOGGLE_TEXT}>{st.name}</span>
                  </label>
                ))}
                <StateChip state="idle" label={`${distinctCategories.size} of ${totalStatusCategories} categories seen`} />
              </div>
            </GadgetRow>
          ) : null}

          {/* Due — wide row, highlighted */}
          <GadgetRow label="Due" wide highlight>
            <div className="jira-toggle-row">
              <label style={TOGGLE_LABEL}>
                <CheckGadget label="Within 7 days" checked={false} onChange={() => {}} />
                <span style={TOGGLE_TEXT}>Within 7 days</span>
              </label>
              <label style={TOGGLE_LABEL}>
                <CheckGadget label="Overdue" checked={false} onChange={() => {}} />
                <span style={TOGGLE_TEXT}>Overdue</span>
              </label>
            </div>
          </GadgetRow>

          {/* JQL (optional) */}
          <GadgetRow label={<>JQL<br /><small style={FACT_SUB}>optional</small></>} wide>
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

      {/* Preview button — visible whenever a project is selected */}
      {selectedProject ? (
        <button
          type="button"
          className="provider-action-btn"
          onClick={onPreview}
          disabled={previewing}
          data-testid="jira-preview-btn"
        >
          {previewing ? "Previewing..." : "Preview"}
        </button>
      ) : null}

      {/* Preview result */}
      {preview && !preview.errorCode ? (
        <div data-testid="jira-preview">
          <div className="jira-wizard-big">
            {preview.items.length}
            <small> {preview.items.length === 1 ? "issue" : "issues"} · {plural(preview.calls, "call")}</small>
          </div>
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
          <div style={INLINE_CHIPS}>
            <ProvenanceChip source="acli" boundary={site} />
          </div>
        </div>
      ) : null}

      {/* query_invalid */}
      {preview?.errorCode === "query_invalid" && preview.queryInvalid ? (
        <ActionNotice tone="warn" icon="⚠" role="alert">
          {preview.queryInvalid}
        </ActionNotice>
      ) : null}

      {/* Footer */}
      <div className="jira-wizard-footer">
        <LampGadget label="Scoped" on={scope.projects.length > 0} />
        <span className="jira-wizard-spacer" />
        <button type="button" className="provider-action-btn" onClick={onBack}>Back</button>
        <button type="button" className="provider-action-btn" data-primary="" disabled={scope.projects.length === 0} onClick={onTest}>
          Test this Watch
        </button>
      </div>
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
  onTestAgain,
  onReview,
  onBack,
}: {
  proposal: SetupProposal;
  site: string;
  email: string;
  onTestAgain: () => void;
  onReview: () => void;
  onBack: () => void;
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
  const normalizedJql = tr?.normalizedJql ?? "";
  const matchedConditions = tr?.matchedConditions ?? "";
  const supportedTransitions = tr?.supportedTransitions ?? [];
  const representativeEntities = tr?.representativeEntities ?? [];

  const enrichCount = Math.max(0, calls - 1);

  const steps: PlanStep[] = [
    { id: "switch", label: `Switch to ${site}`, status: testDone ? stepStatus : "queued", rate: testDone ? "" : undefined, progress: testDone ? 1 : 0 },
    { id: "readback", label: `Read back account · ${email}`, status: testDone ? stepStatus : "queued", progress: testDone ? 1 : 0 },
    { id: "search", label: `Search ${projects[0] ?? "project"}`, status: testDone ? stepStatus : "queued", rate: testDone ? `${entityCount} found` : undefined, progress: testDone ? 1 : 0 },
    { id: "enrich", label: "Enrich due dates, resolution, activity", status: testDone ? stepStatus : "queued", rate: testDone ? `${enrichCount} of ${entityCount}` : undefined, progress: testDone ? 1 : 0 },
    { id: "baseline", label: "Baseline ready", status: testDone ? stepStatus : "queued", rate: testDone ? `${(durationMs / 1000).toFixed(1)}s` : undefined, progress: testDone ? 1 : 0 },
  ];

  // Conditions: prefer matched_conditions from test result, fall back to spec rules
  const spec = proposal.spec;
  // Condition chips: human labels from spec rules (conditionLabel map)
  let conditionChips: string[] = [];
  if (spec.rules) {
    for (const rule of spec.rules) {
      const clauses = rule?.condition?.clauses ?? [];
      for (const clause of clauses) {
        conditionChips.push(conditionLabel(clause));
      }
    }
  }

  const cadenceChip = cadenceLabel(spec.trigger ?? { kind: "manual" });
  const actionChip = actionLabel(spec.action?.kind ?? "");

  return (
    <div data-testid="jira-test-step">
      {/* Progress plan */}
      <ProgressPlan
        steps={steps}
        receipt={
          testDone ? (
            <Receipt
              status={isPassed ? "ok" : "danger"}
              label={isPassed ? "Test passed" : "Test failed"}
              timestamp={tr?.observedAt ? formatTime(tr.observedAt) : undefined}
            />
          ) : undefined
        }
        egress={<ProvenanceChip source="acli" boundary={site} />}
        ariaLabel="Jira watch test"
      />

      {/* Matches — always show when test is done, even with 0 entities */}
      {testDone ? (
        <>
          <div className="jira-wizard-big" data-testid="jira-test-match-count">
            {entityCount}
            <small> {entityCount === 1 ? "issue" : "issues"} · {plural(calls, "call")}</small>
          </div>
          {representativeEntities.length > 0 ? (
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
        </>
      ) : null}

      {/* Will notice: conditions (accent) + transitions (quiet) + cadence + action */}
      {testDone ? (
        <div data-testid="jira-will-notice">
          <div style={INLINE_CHIPS}>
            {conditionChips.map((c) => (
              <StateChip key={c} state="active" label={c} />
            ))}
            {supportedTransitions.map((t) => (
              <StateChip key={t} state="idle" label={transitionLabel(t)} />
            ))}
          </div>
          <div style={{ ...INLINE_CHIPS, marginTop: "6px" }}>
            <StateChip state="idle" label={cadenceChip} />
            {actionChip ? <StateChip state="idle" label={actionChip} /> : null}
          </div>
        </div>
      ) : null}

      {/* Footer */}
      <div className="jira-wizard-footer">
        <LampGadget label={testDone ? "Tested" : "Testing"} on={isPassed} tone={isPassed ? "ok" : "warn"} />
        <span className="jira-wizard-spacer" />
        {testDone ? (
          <button type="button" className="provider-action-btn" onClick={onTestAgain}>Test again</button>
        ) : null}
        <button type="button" className="provider-action-btn" data-primary="" disabled={!isPassed} onClick={onReview}>
          Review and activate
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════
   JiraWizardFlow — sequences accounts → scope → test
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
  onDone: () => void;
  onUpdateScope: (partial: Partial<JiraScope>) => void;
}) {
  const [step, setStep] = useState<WizardStep>("accounts");

  useEffect(() => {
    if (connections.length === 0 && !loading) {
      onLoadConnections();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const selectedConn = connections.find((c) => c.connection_ref === selectedRef);
  const site = selectedConn?.account.site ?? "";
  const email = selectedConn?.account.email ?? "";

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

  return (
    <div className="jira-wizard-flow" data-testid="jira-wizard-flow" role="region" aria-label={`Configure: ${proposal.spec.name}`}>
      {step === "accounts" ? (
        <JiraAccountsStep
          connections={connections}
          knownAccounts={knownAccounts}
          selectedRef={selectedRef}
          onSelect={onSelectConnection}
          onRecheck={onRecheckConnection}
          onAdd={onAddConnection}
          onBack={onDone}
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
          onBack={() => setStep("accounts")}
          onTest={goToTest}
        />
      ) : null}

      {step === "test" ? (
        <JiraTestStep
          proposal={proposal}
          site={site}
          email={email}
          onTestAgain={onTest}
          onReview={onDone}
          onBack={() => setStep("scope")}
        />
      ) : null}
    </div>
  );
}
