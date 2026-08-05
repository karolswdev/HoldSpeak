// HS-117-09 — extracted from HistoryCore.tsx.
import type { StateToken } from "./helpers";

export function StateTokenSpan({ token }: { token: StateToken }) {
  return (
    <span className="surface-token" data-tone={token.tone}>
      {token.axis ? (
        <span className="surface-token-axis">{`${token.axis} `}</span>
      ) : null}
      {token.label}
    </span>
  );
}
