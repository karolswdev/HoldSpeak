/** Betterment AG7: "Why this state", behind Terminal in the agent's window
 *  (agents/DESIGN.md, "Seeing every agent"; herdr's `agent explain`).
 *
 *  Which source decided the state (the agent's hooks or a screen rule), the
 *  rule and its file, the lines it matched, and how old the read is. It reads
 *  `GET /api/agent/launches/{id}/explain` when he opens the fold. */
import { useCallback, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { FoldGadget } from "../surface/gadgets";

export interface ExplainWire {
  state: string | null;
  source: "hook" | "screen" | "none" | string;
  hook: { event: string | null; lifecycle: string | null; notification: string | null; age_seconds: number | null } | null;
  screen: {
    state: string | null;
    rule: string | null;
    fallback: string | null;
    evidence: string[];
    rules_file: string;
    rules_version: string;
    rules_source: string;
    age_seconds: number;
  } | null;
}

/** `4 s ago`, `3 min ago`, `2 h ago`. */
export function ageWords(seconds: number | null | undefined): string {
  if (seconds == null) return "";
  if (seconds < 60) return `${seconds} s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  return `${Math.floor(seconds / 3600)} h ago`;
}

const SOURCE_WORD: Record<string, string> = {
  hook: "The agent's hooks",
  screen: "The agent's screen",
  none: "Nothing for 10 min",
};

/** The rule file's name without its folder: `claude.toml`. */
function fileName(path: string): string {
  return path.split(/[\\/]/).pop() ?? path;
}

export function WhyThisStateBody({ explain }: { explain: ExplainWire }) {
  const screen = explain.screen;
  const hook = explain.hook;
  return (
    <div className="lw-why" data-testid="lane-why-body">
      <span className="lw-why-line" data-testid="lane-why-source">{`From: ${SOURCE_WORD[explain.source] ?? explain.source}`}</span>
      {hook?.event ? (
        <span className="lw-why-line" data-testid="lane-why-hook">
          {`Last hook: ${hook.event}${hook.notification ? ` (${hook.notification})` : ""}, ${ageWords(hook.age_seconds)}`}
        </span>
      ) : null}
      {screen ? (
        <>
          <span className="lw-why-line" data-testid="lane-why-rule">
            {screen.rule
              ? `Rule: ${screen.rule} · ${fileName(screen.rules_file)} ${screen.rules_version} (${screen.rules_source})`
              : `No rule matched · ${fileName(screen.rules_file)} ${screen.rules_version}`}
          </span>
          <span className="lw-why-line" data-testid="lane-why-age">{`Screen read ${ageWords(screen.age_seconds)}`}</span>
          {screen.evidence.length ? (
            <pre className="lw-raw-command lw-why-evidence" data-testid="lane-why-evidence">{screen.evidence.join("\n")}</pre>
          ) : null}
        </>
      ) : (
        <span className="lw-why-line">No screen read</span>
      )}
    </div>
  );
}

export function WhyThisState({ launchId }: { launchId: string }) {
  const [explain, setExplain] = useState<ExplainWire | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const read = useCallback(async () => {
    setBusy(true);
    try {
      setExplain(await apiFetch<ExplainWire>(`/api/agent/launches/${encodeURIComponent(launchId)}/explain`));
      setError(null);
    } catch (cause) {
      setError(`Not read · ${readableError(cause)}`);
    } finally {
      setBusy(false);
    }
  }, [launchId]);
  return (
    <FoldGadget
      title="Why this state"
      className="lw-why-fold"
      onToggle={(open) => {
        if (open) void read();
      }}
    >
      {explain ? <WhyThisStateBody explain={explain} /> : null}
      {error ? <span className="lw-why-line" role="alert">{error}</span> : null}
      <div className="lw-verbs">
        <Button dense variant="ghost" loading={busy} onClick={() => void read()} data-testid="lane-why-read">
          Read again
        </Button>
      </div>
    </FoldGadget>
  );
}
