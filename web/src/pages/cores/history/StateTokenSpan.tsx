// HS-117-09 — extracted from HistoryCore.tsx.
import type { StateToken } from "./helpers";
import { Token } from "../../../desk/surface/Token";

export function StateTokenSpan({ token }: { token: StateToken }) {
  return (
    <Token className="surface-token" data-tone={token.tone}>
      {token.axis ? (
        <span className="surface-token-axis">{`${token.axis} `}</span>
      ) : null}
      {token.label}
    </Token>
  );
}
