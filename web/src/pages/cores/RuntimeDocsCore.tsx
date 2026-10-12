// PHILO-17 REFIT — the Guide wing: what is ready and what is not.
//
// One row per readiness check the hub reports (`/api/setup/status`, the
// doctor's checks), in Today's grammar: the check's name, its fact in one
// muted line, a lamp pill, and the ONE verb that fixes it. The checks that
// need him lead; the ready ones fold. Install commands fold at the foot.
import { useState, type ReactNode } from "react";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps, SetupStatus } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { renderHeroSlot } from "./core-layout";
import { FoldGadget } from "../../desk/surface/gadgets";
import { SurfaceRow, SurfaceRows, SurfaceState } from "../../desk/surface/Surface";
import { apiFetch, readableError } from "../../lib/api";
import { asRows, useResource } from "../pageSupport";
import { SpeechSetup, useSpeechSetup } from "../../desk/firstrun/SpeechSetup";
import { CommandWell } from "./connections/ConnectionsPane";
import { sortChecks } from "./SetupCore";
import "./settings.css";

type Check = { id?: string; label?: string; status?: string; detail?: string; raw?: string; fix?: unknown };

/** The checks whose fix is choosing an engine (Runs on). */
const ENGINE_CHECKS = new Set([
  "dictation-ai-model",
  "dictation-ai-use",
  "meeting-intelligence-runtime",
  "where-ai-runs",
  "runtime-profiles",
  "cloud-ai-check",
  "endpoint-health",
  "transcription-backend",
]);

const PILL: Record<string, { tone: string; word: string }> = {
  pass: { tone: "ok", word: "Ready" },
  info: { tone: "idle", word: "Note" },
  warn: { tone: "warn", word: "Check" },
  fail: { tone: "danger", word: "Not working" },
  unknown: { tone: "idle", word: "Not known" },
};

/** A fix the hub states as a terminal command (shown only on demand). */
export function isCommand(fix: unknown): fix is string {
  return typeof fix === "string" && /^(uv|pip|brew|gh|acli|holdspeak|export|sudo|apt|xcode-select|ollama|npm)\b/.test(fix.trim());
}

/** The command in a fix: the fix itself, or the first `quoted` command in
 *  its words (`Install the hooks: \`holdspeak agent-hook install\``). */
export function commandOf(fix: unknown): string | null {
  if (isCommand(fix)) return fix.trim();
  if (typeof fix !== "string") return null;
  for (const match of fix.matchAll(/`([^`]+)`/g)) if (isCommand(match[1])) return match[1].trim();
  return null;
}

function GuideRow({ check, lead, speech, onReady }: {
  check: Check;
  lead: boolean;
  speech: ReturnType<typeof useSpeechSetup>;
  onReady: () => void;
}) {
  const [open, setOpen] = useState(false);
  // The technical fact (`raw`) unfolds under the row's name.
  const [more, setMore] = useState(false);
  const status = String(check.status ?? "unknown");
  const pill = PILL[status] ?? PILL.unknown;
  const needs = status === "fail" || status === "warn";
  const id = String(check.id ?? "");
  const fix = check.fix;
  const command = commandOf(fix);
  let verb: ReactNode = null;
  if (needs && id === "speech-model") {
    verb = <SpeechSetup setup={speech} bare primary={lead} onReady={onReady} testId="guide-speech-setup" />;
  } else if (needs && ENGINE_CHECKS.has(id)) {
    verb = (
      <Button dense variant={lead ? "primary" : "secondary"} onClick={() => openSurfaceOr("open-concierge", "/models")}>
        Choose engines
      </Button>
    );
  } else if (needs && command) {
    verb = (
      <Button dense variant={lead ? "primary" : "secondary"} aria-expanded={open} onClick={() => setOpen((value) => !value)}>
        {open ? "Hide the fix" : "Show the fix"}
      </Button>
    );
  }
  // The meta line is the check's fact; the hub's fix sentence is its title.
  const fixWords = typeof fix === "string" && fix ? fix : undefined;
  return (
    <li className="guide-row" data-status={status} data-testid={`guide-check-${id}`}>
      <div className="guide-row-text">
        {check.raw && check.raw !== check.detail ? (
          <Button variant="chrome" className="guide-row-name guide-row-title" aria-expanded={more} onClick={() => setMore((value) => !value)} data-testid={`guide-raw-toggle-${id}`}>
            {check.label ?? id}
          </Button>
        ) : (
          <span className="guide-row-name">{check.label ?? id}</span>
        )}
        {check.detail ? (
          <span className="guide-row-meta" title={fixWords ?? check.detail}>{check.detail}</span>
        ) : null}
      </div>
      <span className="kit-pill" data-dot="" data-tone={pill.tone === "idle" ? undefined : pill.tone}>{pill.word}</span>
      {verb ? <span className="guide-row-verb">{verb}</span> : null}
      {more && check.raw ? <code className="guide-row-raw" data-testid={`guide-raw-${id}`}>{check.raw}</code> : null}
      {open && command ? <div className="guide-row-fix"><CommandWell hint={command} /></div> : null}
    </li>
  );
}

/** `1 thing needs you`, `3 things need you` (drawn only when one does). */
function needWords(n: number): string {
  return n === 1 ? "1 thing needs you" : `${n} things need you`;
}

export function RuntimeDocsCore({ hero }: CoreProps) {
  const resource = useResource<SetupStatus>("/api/setup/status", {});
  const speech = useSpeechSetup();
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null);
  const checks = sortChecks(asRows(resource.data.sections, []) as Check[]);
  const needs = checks.filter((c) => c.status === "fail" || c.status === "warn");
  const fine = checks.filter((c) => !(c.status === "fail" || c.status === "warn"));
  const fixable = (c: Check) => c.id === "speech-model" || ENGINE_CHECKS.has(String(c.id ?? "")) || Boolean(commandOf(c.fix));
  const leadCheck = needs.find(fixable);
  const loaded = !resource.loading || checks.length > 0;

  const testRuntime = async () => {
    setTesting(true);
    try {
      const value = await apiFetch<{ ok?: boolean; detail?: string }>("/api/setup/runtime-test", { method: "POST" });
      setResult({ ok: Boolean(value.ok), text: value.ok ? "Test passed" : value.detail ?? "Test failed" });
    } catch (error) {
      setResult({ ok: false, text: readableError(error) });
    } finally {
      setTesting(false);
    }
  };

  const headline = !loaded
    ? "Checking"
    : needs.length
      ? needWords(needs.length)
      : "Everything is ready";
  // ONE filled primary: the first row that needs him, else Test runtime.
  return (
    <>
      {renderHeroSlot(hero, null)}
      <div className="settings-home guide" data-testid="guide">
        <div className="settings-head">
          <h2 className="settings-title" data-warning={needs.length ? "" : undefined} data-testid="guide-headline">{headline}</h2>
          <span className="guide-head-sp" />
          <Button dense variant={leadCheck ? "secondary" : "primary"} loading={testing} onClick={() => void testRuntime()} data-testid="guide-test">
            Test runtime
          </Button>
        </div>
        {resource.error ? <SurfaceState error={resource.error} onRetry={() => void resource.reload()} /> : null}
        {needs.length ? (
          <ul className="guide-list" aria-label="Needs you">
            {needs.map((check, index) => (
              <GuideRow key={String(check.id ?? index)} check={check} lead={check === leadCheck} speech={speech} onReady={() => void resource.reload()} />
            ))}
          </ul>
        ) : null}
        {fine.length ? (
          <FoldGadget title="Ready" token={String(fine.length)}>
            <ul className="guide-list">
              {fine.map((check, index) => (
                <GuideRow key={String(check.id ?? index)} check={check} lead={false} speech={speech} onReady={() => void resource.reload()} />
              ))}
            </ul>
          </FoldGadget>
        ) : null}
        <FoldGadget title="Install commands">
          <SurfaceRows>
            <SurfaceRow title="Voice typing" detail="uv pip install -e '.[whisper]'" />
            <SurfaceRow title="Apple Silicon (MLX)" detail="uv pip install -e '.[dictation-mlx]'" />
            <SurfaceRow title="Local GGUF (llama.cpp)" detail="uv pip install -e '.[dictation-llama]'" />
            <SurfaceRow title="OpenAI-compatible server" detail="uv pip install -e '.[dictation-openai]'" />
          </SurfaceRows>
        </FoldGadget>
      </div>
      <SurfaceFooter
        receipt={result ? (
          <span className="surface-footer-receipt-line" role="status" data-tone={result.ok ? "ok" : "danger"}>{result.text}</span>
        ) : undefined}
      />
    </>
  );
}
