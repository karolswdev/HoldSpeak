// PARKED (HS-170-02): retired by Phase 169; kept for reference, not built or scanned.
// HS-161-05 -- the GitHub provider wizard step: Discover -> Scope -> Test.
// HS-168-04: connection card REMOVED from the interview; the wizard asks
// SCOPE + POPULATION + TEST only. Heading = the Watch's ledger row.
// ProgressPlan `Repository . Population . Test`. Known-scope card offered
// at the top of the scope step. Verbs: Back (quiet) / Test this Watch
// (primary) -> Use this Watch (primary after passing test). EgressChip
// names the real host at the point of egress.

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChoiceCardShell,
  EgressChip,
  useRovingRows,
  StateChip,
  ProvenanceChip,
  Receipt,
  ProgressPlan,
  SurfaceFacts,
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
  type PlanStep,
} from "../../../desk/surface";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import { MicButton } from "../../../desk/surface/controls/MicButton";
import { Button } from "../../../components/signal/Signal";
import {
  cadenceLabel,
  conditionPlainWords,
  queryPlainWords,
  type KnownScopes,
  type DiscoveryItem,
  type DiscoveryResponse,
  type ValidateRepoResponse,
  type ClarifyScopeResponse,
  type SetupProposal,
  type ProviderConnectionStatus,
} from "./model";

/* ── Discovery list (searchable, bounded) ── */

export function DiscoveryList({
  items,
  cursor,
  query,
  onQueryChange,
  onLoadMore,
  onSelect,
  loading,
}: {
  items: DiscoveryItem[];
  cursor: string | null;
  query: string;
  onQueryChange: (q: string) => void;
  onLoadMore: () => void;
  onSelect: (ownerRepo: string) => void;
  loading: boolean;
}) {
  const listRef = useRef<HTMLDivElement>(null);
  useRovingRows(listRef, { selector: '[role="option"]' });

  const handleVoice = useCallback(
    (text: string) => {
      onQueryChange(query ? `${query} ${text}` : text);
    },
    [query, onQueryChange],
  );

  return (
    <div className="provider-discovery" data-testid="provider-discovery">
      <div className="provider-discovery-search">
        <input
          type="text"
          className="provider-discovery-input"
          placeholder="Search repositories"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          aria-label="Search repositories"
        />
        <MicButton onText={handleVoice} label="Speak repository name" />
      </div>

      {loading ? (
        <div className="provider-discovery-loading" aria-live="polite">
          Discovering repositories...
        </div>
      ) : null}

      {!loading && items.length === 0 ? (
        <div className="provider-discovery-empty" aria-live="polite">
          No repositories found.{" "}
          {query ? "Try a different search, or type a repository below." : "Type a repository path below."}
        </div>
      ) : null}

      {items.length > 0 ? (
        <div
          ref={listRef}
          className="provider-discovery-list"
          role="listbox"
          aria-label="Discovered repositories"
          data-testid="provider-discovery-list"
        >
          {items.map((item) => (
            <DiscoveryCard
              key={item.id}
              item={item}
              onSelect={onSelect}
            />
          ))}
        </div>
      ) : null}

      {cursor ? (
        <Button dense variant="ghost" onClick={onLoadMore} disabled={loading}>
          Load more
        </Button>
      ) : null}
    </div>
  );
}

/* ── Discovery card (ChoiceCardShell + ProvenanceChip) ── */

function DiscoveryCard({
  item,
  onSelect,
}: {
  item: DiscoveryItem;
  onSelect: (ownerRepo: string) => void;
}) {
  const ownerRepo = item.id;
  const ownerInitial = item.owner ? item.owner[0]?.toUpperCase() ?? "?" : "?";

  const handleClick = useCallback(() => {
    onSelect(ownerRepo);
  }, [ownerRepo, onSelect]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        onSelect(ownerRepo);
      }
    },
    [ownerRepo, onSelect],
  );

  return (
    <ChoiceCardShell
      label={ownerRepo}
      summary={item.visibility}
      emblem={ownerInitial}
      role="option"
      aria-selected={false}
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      data-testid={`discovery-card-${ownerRepo}`}
    >
      <ProvenanceChip source="gh" boundary="github.com" />
    </ChoiceCardShell>
  );
}

/* ── Typed-repo fallback input ── */

export function TypedRepoInput({
  onValidate,
  validating,
}: {
  onValidate: (ownerRepo: string) => void;
  validating: boolean;
}) {
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = draft.trim();
    if (trimmed && !validating) {
      onValidate(trimmed);
    }
  }, [draft, validating, onValidate]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        handleSubmit();
      }
    },
    [handleSubmit],
  );

  const handleVoice = useCallback(
    (text: string) => {
      setDraft((prev) => (prev ? `${prev} ${text}` : text));
    },
    [],
  );

  return (
    <div className="provider-typed-repo" data-testid="provider-typed-repo">
      <div className="provider-typed-repo-row">
        <input
          ref={inputRef}
          id="provider-repo-input"
          type="text"
          className="provider-typed-repo-input"
          placeholder="owner/repo"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={validating}
        />
        <MicButton onText={handleVoice} label="Speak repository name" />
        <Button
          dense
          variant="ghost"
          onClick={handleSubmit}
          disabled={!draft.trim() || validating}
        >
          {validating ? "Checking..." : "Check repo"}
        </Button>
      </div>
    </div>
  );
}

/* ── GitHub test result display (D3 recomposition) ── */

export function GitHubTestDisplay({
  repo,
  queryPlainWordsText,
  entityCount,
  representativeEntities,
  matchedConditions,
  observedAt,
  error,
  testState,
  baseBranch,
}: {
  repo: string;
  queryPlainWordsText: string;
  entityCount: number;
  representativeEntities: Record<string, unknown>[];
  matchedConditions: string;
  observedAt: string;
  error: { type: string; message: string } | null;
  testState: string;
  baseBranch?: string;
}) {
  const isPassed = testState === "passed";
  const isFailed = testState === "failed";

  return (
    <div
      className="provider-test-display"
      data-testid="provider-test-display"
      data-test-state={testState}
      role="status"
      aria-live="polite"
    >
      {/* D3 Population facts: SUBJECT / BASE / QUERY */}
      <SurfaceSection label="POPULATION">
        <SurfaceFacts value={{
          SUBJECT: "pull requests",
          ...(baseBranch ? { BASE: baseBranch } : {}),
          QUERY: queryPlainWordsText,
        }} />
      </SurfaceSection>

      {/* D3 Test ProgressPlan */}
      <SurfaceSection label="TEST">
        <ProgressPlan
          steps={[
            { id: "auth", label: "Auth", status: (isPassed || isFailed) ? (isPassed ? "done" : "failed") : "queued" as PlanStep["status"] },
            { id: "read", label: `Read ${repo}`, status: (isPassed || isFailed) ? (isPassed ? "done" : "failed") : "queued" as PlanStep["status"], rate: (isPassed || isFailed) ? undefined : undefined },
            { id: "fetch", label: `Fetch ${entityCount}`, status: (isPassed || isFailed) ? (isPassed ? "done" : "failed") : "queued" as PlanStep["status"] },
            { id: "baseline", label: "Baseline ready", status: (isPassed || isFailed) ? (isPassed ? "done" : "failed") : "queued" as PlanStep["status"] },
          ]}
          receipt={(isPassed || isFailed) ? (
            <Receipt status={isPassed ? "ok" : "danger"} label={isPassed ? "Passed" : "Failed"} timestamp={observedAt ? formatTestTime(observedAt) : undefined} />
          ) : undefined}
          ariaLabel="GitHub watch test"
        />
      </SurfaceSection>

      {/* Matches ledger */}
      {(isPassed || isFailed) ? (
        <SurfaceSection label={`MATCHES ${entityCount}`}>
          {entityCount === 0 ? (
            <StateChip
              state="success"
              label="0 matches"
            />
          ) : representativeEntities.length > 0 ? (
            <SurfaceLedger count={`${entityCount}`}>
              <ul className="surface-ledger-rows">
                {representativeEntities.slice(0, 5).map((entity, i) => {
                  const id = entity.id != null ? String(entity.id) : "";
                  const title = entity.title != null ? String(entity.title) : "";
                  const state = entity.state != null ? String(entity.state) : "";
                  const updatedAt = entity.updated_at != null ? String(entity.updated_at) : "";
                  return (
                    <SurfaceLedgerRow
                      key={i}
                      lead={id ? `#${id}` : ""}
                      primary={title}
                      cells={
                        <StateChip
                          state={state.toLowerCase() === "open" ? "success" : "idle"}
                          label={state.toUpperCase()}
                        />
                      }
                      time={updatedAt ? formatRelativeTime(updatedAt) : undefined}
                      expands={false}
                    />
                  );
                })}
              </ul>
            </SurfaceLedger>
          ) : null}
        </SurfaceSection>
      ) : null}

      {/* Error state */}
      {error ? (
        <div className="provider-test-error" data-testid="provider-test-error">
          <StateChip state="failure" label={error.type} />
          <div className="provider-test-error-message">{error.message}</div>
        </div>
      ) : null}
    </div>
  );
}

/* ── Helpers ── */

function formatTestTime(iso: string): string {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

function formatRelativeTime(iso: string): string {
  if (!iso) return "";
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "now";
    if (mins < 60) return `${mins} min`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} hr`;
    const days = Math.floor(hours / 24);
    return `${days} d`;
  } catch {
    return "";
  }
}

/* ── Known-scope card (D0 vocabulary) ── */

function KnownScopeCard({
  label,
  summary,
  onUse,
}: {
  label: string;
  summary: string;
  onUse: () => void;
}) {
  return (
    <ChoiceCardShell
      label={label}
      summary={summary}
      tier="balanced"
      data-testid="known-scope-card"
    >
      <Button dense variant="ghost" onClick={onUse} data-testid="known-scope-use">
        Use this repo
      </Button>
    </ChoiceCardShell>
  );
}

/* ── ProviderWizardFlow: scope + population + test (no auth) ── */

export function ProviderWizardFlow({
  proposal,
  connection,
  discovery,
  checking,
  discovering,
  scopeState,
  knownScopes,
  onCheckConnection,
  onRecheck,
  onDiscover,
  onValidateRepo,
  onClarifyScope,
  onTest,
  onBack,
  onDone,
}: {
  proposal: SetupProposal;
  connection: ProviderConnectionStatus | null;
  discovery: DiscoveryResponse | null;
  checking: boolean;
  discovering: boolean;
  scopeState: "unscoped" | "scoped" | null;
  knownScopes: KnownScopes;
  onCheckConnection: () => void;
  onRecheck: () => void;
  onDiscover: (query?: string, cursor?: string) => void;
  onValidateRepo: (ownerRepo: string) => Promise<ValidateRepoResponse | null>;
  onClarifyScope: (repo?: string) => Promise<ClarifyScopeResponse | null>;
  onTest: () => void;
  onBack: () => void;
  onDone: () => void;
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [validating, setValidating] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Auto-check connection on mount if not already checked
  useEffect(() => {
    if (!connection && !checking) {
      onCheckConnection();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-discover when connection becomes connected and no discovery yet
  useEffect(() => {
    if (connection?.state === "connected" && !discovery && !discovering && scopeState !== "scoped") {
      onDiscover();
    }
  }, [connection?.state]); // eslint-disable-line react-hooks/exhaustive-deps

  const isConnected = connection?.state === "connected";
  const isScoped = scopeState === "scoped";
  const hasPassed = proposal.testState === "passed";

  // HS-168-04: ProgressPlan wizard steps
  const wizardSteps: PlanStep[] = [
    { id: "repository", label: "Repository", status: isScoped ? "done" : isConnected ? "running" : "queued" },
    { id: "population", label: "Population", status: hasPassed ? "done" : isScoped ? "running" : "queued" },
    { id: "test", label: "Test", status: hasPassed ? "done" : "queued" },
  ];

  // Known-scope card for this provider
  const knownGitHub = knownScopes.github.find((ks) => ks.forProposalId !== proposal.id && ks.repository);

  // Handle discovery card selection -> clarify scope
  const handleRepoSelect = useCallback(async (ownerRepo: string) => {
    setValidationError(null);
    await onClarifyScope(ownerRepo);
  }, [onClarifyScope]);

  // Handle typed repo validation -> clarify scope
  const handleTypedRepo = useCallback(async (ownerRepo: string) => {
    setValidating(true);
    setValidationError(null);
    const result = await onValidateRepo(ownerRepo);
    if (result && result.valid) {
      await onClarifyScope(ownerRepo);
    } else if (result && !result.valid) {
      setValidationError(result.message ?? "Invalid repository path. Use owner/repo format.");
    }
    setValidating(false);
  }, [onValidateRepo, onClarifyScope]);

  // Handle search query changes
  const handleSearchChange = useCallback((q: string) => {
    setSearchQuery(q);
    onDiscover(q || undefined);
  }, [onDiscover]);

  // The repo from scope (for the test display)
  const scopedRepo = String(proposal.spec.subject.scope?.repository ?? "");
  const baseBranch = String((proposal.spec.subject.scope?.query as Record<string, unknown> | undefined)?.base ?? "");

  return (
    <div
      className="provider-wizard-flow"
      data-testid="provider-wizard-flow"
      role="region"
      aria-label={`Configure ${proposal.spec.name}`}
    >
      {/* HS-168-04: heading = the Watch's ledger row as a flex composition */}
      <div className="setup-wizard-heading" data-testid="wizard-heading">
        <span className="setup-wizard-heading-name" data-testid="wizard-heading-name">
          {proposal.spec.name}
        </span>
        <span className="surface-token" data-chip>{cadenceLabel(proposal.spec.trigger)}</span>
        <span className="surface-token" data-chip>{proposal.spec.action.kind === "project.observe" ? "observe" : proposal.spec.action.kind}</span>
        <ProvenanceChip source="gh" boundary="github.com" />
      </div>

      {/* Wizard ProgressPlan */}
      <ProgressPlan steps={wizardSteps} compact />

      {/* Repository step: known-scope card + discovery + typed repo */}
      {isConnected && !isScoped ? (
        <SurfaceSection label="REPOSITORY">
          {/* Known-scope card (offered, never applied) */}
          {knownGitHub ? (
            <KnownScopeCard
              label={knownGitHub.repository!}
              summary={`chosen for ${knownGitHub.watchName ?? "another Watch"}`}
              onUse={() => void onClarifyScope(knownGitHub.repository!)}
            />
          ) : null}
          <DiscoveryList
            items={discovery?.items ?? []}
            cursor={discovery?.cursor ?? null}
            query={searchQuery}
            onQueryChange={handleSearchChange}
            onLoadMore={() => onDiscover(searchQuery || undefined, discovery?.cursor ?? undefined)}
            onSelect={handleRepoSelect}
            loading={discovering}
          />
          <TypedRepoInput
            onValidate={handleTypedRepo}
            validating={validating}
          />
          {validationError ? (
            <div className="provider-wizard-error" role="alert">
              <StateChip state="failure" label="Error" />
              <span>{validationError}</span>
            </div>
          ) : null}
        </SurfaceSection>
      ) : null}

      {/* Scoped: population facts + test */}
      {isConnected && isScoped ? (
        <>
          {proposal.testResult ? (
            <GitHubTestDisplay
              repo={scopedRepo}
              queryPlainWordsText={queryPlainWords(proposal.spec)}
              entityCount={proposal.testResult.entityCount}
              representativeEntities={proposal.testResult.representativeEntities}
              matchedConditions={conditionPlainWords(proposal.spec)}
              observedAt={proposal.testResult.observedAt}
              error={proposal.testResult.error}
              testState={proposal.testState ?? ""}
              baseBranch={baseBranch || undefined}
            />
          ) : (
            <SurfaceSection label="POPULATION">
              <SurfaceFacts value={{
                SUBJECT: "pull requests",
                ...(baseBranch ? { BASE: baseBranch } : {}),
                QUERY: queryPlainWords(proposal.spec),
              }} />
            </SurfaceSection>
          )}
        </>
      ) : null}

      {/* Checking state */}
      {!isConnected && checking ? (
        <div className="provider-wizard-loading" aria-live="polite">
          Checking GitHub connection...
        </div>
      ) : null}

      {/* Footer: EgressChip + Back + Test this Watch / Use this Watch */}
      <SurfaceFooter
        egress={<EgressChip label="github.com" scope="mixed" title="GitHub reads leave the machine." />}
        receipt={hasPassed ? (
          <Receipt status="ok" label="Passed" timestamp={proposal.testResult?.observedAt ? formatTestTime(proposal.testResult.observedAt) : undefined} />
        ) : undefined}
        verbs={
          <>
            <Button dense variant="ghost" onClick={onBack} data-testid="provider-wizard-back">
              Back
            </Button>
            {hasPassed ? (
              <Button dense variant="primary" onClick={onDone} data-testid="provider-wizard-done">
                Use this Watch
              </Button>
            ) : (
              <Button
                dense
                variant="primary"
                disabled={!isScoped}
                onClick={onTest}
                data-testid="provider-test-btn"
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
