import { useCallback, useEffect, useMemo, useState } from "react";
import "./surface-footer.css";

export interface LedgerFilterToken {
  field: string;
  value: string;
}

export interface UseLedgerFilterOpts<T> {
  /** The localStorage key suffix for this ledger's query. */
  key: string;
  match: (item: T, query: string) => boolean;
}

export function useLedgerFilter<T>(items: T[], opts: UseLedgerFilterOpts<T>) {
  const storageKey = `hs.filter.${opts.key}`;
  const [query, setQuery] = useState(() => {
    try {
      return localStorage.getItem(storageKey) || "";
    } catch {
      return "";
    }
  });
  const [tokens, setTokens] = useState<LedgerFilterToken[]>([]);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, query);
    } catch {
      // Persistence is an enhancement; unavailable storage must not block filtering.
    }
  }, [storageKey, query]);

  const filtered = useMemo(() => {
    if (!query.trim()) return items;
    return items.filter((item) => opts.match(item, query.trim()));
  }, [items, query, opts.match]);

  const clear = useCallback(() => {
    setQuery("");
    setTokens([]);
    try {
      localStorage.removeItem(storageKey);
    } catch {
      // Persistence is an enhancement; unavailable storage must not block filtering.
    }
  }, [storageKey]);

  const addToken = useCallback((field: string, value: string) => {
    setTokens((previous) =>
      previous.some((token) => token.field === field && token.value === value)
        ? previous
        : [...previous, { field, value }],
    );
  }, []);

  const removeToken = useCallback((field: string, value: string) => {
    setTokens((previous) =>
      previous.filter((token) => !(token.field === field && token.value === value)),
    );
  }, []);

  const isActive = query.trim().length > 0 || tokens.length > 0;

  return {
    query,
    setQuery,
    tokens,
    addToken,
    removeToken,
    clear,
    filtered,
    isActive,
    total: items.length,
  };
}

export function LedgerFilterBar({
  query,
  onQueryChange,
  tokens,
  onRemoveToken,
  onClear,
  total,
  matchCount,
  isActive,
}: {
  query: string;
  onQueryChange: (query: string) => void;
  tokens: LedgerFilterToken[];
  onRemoveToken: (field: string, value: string) => void;
  onClear: () => void;
  total: number;
  matchCount: number;
  isActive: boolean;
}) {
  return (
    <div className="ledger-filter">
      <div className="ledger-filter-rail">
        <span className={`ledger-filter-label ${isActive ? "is-active" : ""}`}>
          {isActive ? "Filtered" : "Filter"}
        </span>
        <div className="ledger-filter-well">
          <input
            type="text"
            className="ledger-filter-query"
            placeholder="Filter..."
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
          />
        </div>
        <span className="ledger-filter-count">
          {isActive ? `${matchCount}/${total}` : String(total)}
        </span>
        {isActive ? (
          <button
            type="button"
            className="ledger-filter-clear"
            onClick={onClear}
            aria-label="Clear filters"
          >
            Clear
          </button>
        ) : null}
      </div>
      {tokens.length > 0 ? (
        <div className="ledger-filter-tokens">
          {tokens.map((token) => (
            <span
              key={`${token.field}-${token.value}`}
              className="ledger-filter-token"
            >
              <span className="ledger-filter-token-body">
                <span className="ledger-filter-token-marker" />
                <span className="ledger-filter-token-field">{token.field}</span>
                <span className="ledger-filter-token-sep">&middot;</span>
                <span className="ledger-filter-token-value">{token.value}</span>
              </span>
              <button
                type="button"
                className="ledger-filter-token-remove"
                onClick={() => onRemoveToken(token.field, token.value)}
                aria-label={`Remove ${token.field} filter: ${token.value}`}
              >
                &times;
              </button>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
