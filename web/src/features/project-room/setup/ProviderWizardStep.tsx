// HS-161-05 -- the provider wizard step: Check connection -> Discover ->
// Test -> Activate. ONE next action per state. Recheck flow. Discovery list
// (searchable, bounded) + typed-repo fallback. SETFLOW-003: auth-recovery
// preserves setup state, names recovery, offers Recheck. GitHub NEVER
// appears active before a passing test. Egress badge (EgressChip) on every
// card and test action -- these reads leave the machine (local+cloud).

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChoiceCardShell,
  EgressChip,
  useRovingRows,
} from "../../../desk/surface";
import { MicButton } from "../../../desk/surface/controls/MicButton";
import {
  PROVIDER_STATE_COPY,
  PROVIDER_STATE_ACTION,
  type ProviderState,
  type ProviderConnectionStatus,
  type DiscoveryItem,
  type DiscoveryResponse,
} from "./model";

/* ── Connection status card ── */

export function ConnectionStatusCard({
  status,
  onRecheck,
  rechecking,
}: {
  status: ProviderConnectionStatus;
  onRecheck: () => void;
  rechecking: boolean;
}) {
  const copy = PROVIDER_STATE_COPY[status.state];
  const action = PROVIDER_STATE_ACTION[status.state];
  const isOk = status.state === "connected";
  const needsAuth = status.state === "owner_action_required";

  return (
    <div
      className="provider-status-card"
      data-testid="provider-status-card"
      data-state={status.state}
      role="status"
      aria-live="polite"
    >
      <div className="provider-status-headline">
        <span
          className="provider-status-icon"
          aria-hidden="true"
          data-ok={isOk || undefined}
          data-warn={needsAuth || undefined}
        >
          {isOk ? "✓" : needsAuth ? "!" : "…"}
        </span>
        <span className="provider-status-title">{copy.headline}</span>
        {status.display.account ? (
          <span className="provider-status-account">
            {status.display.account}
          </span>
        ) : null}
      </div>
      <div className="provider-status-detail">{copy.detail}</div>

      {/* SETFLOW-003: auth-recovery card names the recovery command */}
      {needsAuth && status.display.recoveryHint ? (
        <div
          className="provider-recovery"
          data-testid="provider-recovery"
          role="alert"
        >
          <div className="provider-recovery-label">
            To connect, run in your terminal:
          </div>
          <code className="provider-recovery-command">
            {status.display.recoveryHint}
          </code>
          <div className="provider-recovery-hint">
            Then press Recheck below.
          </div>
        </div>
      ) : null}

      {/* The ONE next action */}
      {action.kind === "recheck" || action.kind === "retry" ? (
        <button
          type="button"
          className="provider-action-btn"
          data-testid="provider-recheck-btn"
          onClick={onRecheck}
          disabled={rechecking}
        >
          {rechecking ? "Checking..." : action.label}
        </button>
      ) : null}

      {action.kind === "wait" ? (
        <div className="provider-action-wait">{action.label}</div>
      ) : null}

      {/* Egress badge: connection check reads leave the machine */}
      <EgressChip
        label="local + cloud"
        scope="mixed"
        title="This connection check contacts github.com from this device."
      />
    </div>
  );
}

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
          placeholder="Search repositories..."
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
        <button
          type="button"
          className="provider-discovery-more"
          onClick={onLoadMore}
          disabled={loading}
        >
          Load more
        </button>
      ) : null}
    </div>
  );
}

/* ── Discovery card (ChoiceCardShell + EgressChip) ── */

function DiscoveryCard({
  item,
  onSelect,
}: {
  item: DiscoveryItem;
  onSelect: (ownerRepo: string) => void;
}) {
  const ownerRepo = item.id;

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
      facts={[
        { label: "owner", value: item.owner },
      ]}
      role="option"
      aria-selected={false}
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      data-testid={`discovery-card-${ownerRepo}`}
    >
      {/* Egress badge: discovery reads leave the machine */}
      <EgressChip
        label="local + cloud"
        scope="mixed"
        title="Repository discovery contacts github.com."
      />
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
      <label
        className="provider-typed-repo-label"
        htmlFor="provider-repo-input"
      >
        Or type a repository path (owner/repo):
      </label>
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
        <button
          type="button"
          className="provider-typed-repo-btn"
          onClick={handleSubmit}
          disabled={!draft.trim() || validating}
        >
          {validating ? "Validating..." : "Use this repo"}
        </button>
      </div>
    </div>
  );
}

/* ── GitHub test result display (SS 8.1) ── */

export function GitHubTestDisplay({
  repo,
  queryPlainWords,
  entityCount,
  representativeEntities,
  matchedConditions,
  observedAt,
  error,
  testState,
}: {
  repo: string;
  queryPlainWords: string;
  entityCount: number;
  representativeEntities: Record<string, unknown>[];
  matchedConditions: string;
  observedAt: string;
  error: { type: string; message: string } | null;
  testState: string;
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
      {/* Status + count */}
      <div className="provider-test-header">
        <span className="provider-test-icon" aria-hidden="true">
          {isPassed ? "✓" : isFailed ? "✗" : "…"}
        </span>
        <span className="provider-test-status">
          {isPassed ? "Test passed" : isFailed ? "Test failed" : "Testing"}
        </span>
        <span className="provider-test-count">
          {entityCount} current {entityCount === 1 ? "match" : "matches"}
        </span>
      </div>

      {/* ACT-002: zero-match "0 current matches = PASS" */}
      {isPassed && entityCount === 0 ? (
        <div className="provider-test-zero-match" data-testid="provider-test-zero-match">
          0 current matches is a valid result. The Watch is correctly configured
          and will activate when matching PRs appear.
        </div>
      ) : null}

      {/* Repository */}
      <div className="provider-test-field">
        <span className="provider-test-field-label">Repository</span>
        <span className="provider-test-field-value">{repo}</span>
      </div>

      {/* Query in plain words */}
      <div className="provider-test-field">
        <span className="provider-test-field-label">Query</span>
        <span className="provider-test-field-value">{queryPlainWords}</span>
      </div>

      {/* Entity count */}
      <div className="provider-test-field">
        <span className="provider-test-field-label">Entities</span>
        <span className="provider-test-field-value">{entityCount}</span>
      </div>

      {/* Representative PRs (up to 5) */}
      {representativeEntities.length > 0 ? (
        <div className="provider-test-entities">
          <span className="provider-test-field-label">
            Representative PRs ({Math.min(representativeEntities.length, 5)} shown)
          </span>
          {representativeEntities.slice(0, 5).map((entity, i) => (
            <div key={i} className="provider-test-entity">
              {prEntityLabel(entity)}
            </div>
          ))}
        </div>
      ) : null}

      {/* Matched conditions */}
      {matchedConditions ? (
        <div className="provider-test-field">
          <span className="provider-test-field-label">Conditions</span>
          <span className="provider-test-field-value">{matchedConditions}</span>
        </div>
      ) : null}

      {/* Observed time */}
      <div className="provider-test-field">
        <span className="provider-test-field-label">Observed</span>
        <span className="provider-test-field-value">
          {formatTestTime(observedAt)}
        </span>
      </div>

      {/* PROV-009 error codes rendered honestly */}
      {error ? (
        <div className="provider-test-error" data-testid="provider-test-error">
          <span className="provider-test-error-type">{error.type}</span>
          <span className="provider-test-error-message">{error.message}</span>
        </div>
      ) : null}

      {/* Egress badge on test results */}
      <EgressChip
        label="local + cloud"
        scope="mixed"
        title="This test contacted github.com to query pull requests."
      />
    </div>
  );
}

/* ── Helpers ── */

function prEntityLabel(entity: Record<string, unknown>): string {
  const num = entity.number != null ? `#${entity.number}` : "";
  const title = entity.title ?? entity.name ?? entity.id;
  const state = entity.state ?? "";
  return `${num} ${String(title ?? "Unknown")}${state ? ` (${state})` : ""}`.trim();
}

function formatTestTime(iso: string): string {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}
