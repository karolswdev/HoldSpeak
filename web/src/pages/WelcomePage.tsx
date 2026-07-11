import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  Button,
  ChoiceCard,
  Field,
  InlineMessage,
  Panel,
  Select,
  StatusPill,
  Switch,
  TextInput,
} from "../components/signal/Signal";
import { apiFetch, readableError } from "../lib/api";
import { useRuntimeFrame } from "../runtime/RuntimeBus";
import { asRows, useResource } from "./pageSupport";

const STEPS = [
  "Welcome",
  "Permissions",
  "Model",
  "First dictation",
  "Presence",
  "Done",
];
type Setup = {
  overall?: string;
  first_run?: boolean;
  sections?: Array<Record<string, unknown>>;
};
type Options = {
  mlx?: Array<{ label: string; value: string }>;
  gguf?: Array<{ label: string; value: string }>;
  context_presets?: number[];
  platform?: { apple_silicon?: boolean };
};

export default function WelcomePage() {
  const [step, setStep] = useState(0);
  const [backend, setBackend] = useState("basic");
  const [modelPath, setModelPath] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [endpointModels, setEndpointModels] = useState<string[]>([]);
  const [model, setModel] = useState("");
  const [note, setNote] = useState<{
    tone: "success" | "error" | "info";
    text: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const setup = useResource<Setup>("/api/setup/status", {});
  const options = useResource<Options>("/api/setup/runtime-options", {});
  const settings = useResource<Record<string, unknown>>("/api/settings", {});
  const activity = useRuntimeFrame<Record<string, unknown>>("runtime_activity");
  const models =
    backend === "mlx" ? (options.data.mlx ?? []) : (options.data.gguf ?? []);
  const permissionRows = asRows(setup.data.sections, []).filter((row) =>
    String(row.id ?? row.label ?? "")
      .toLowerCase()
      .match(/mic|access|permission|hotkey/),
  );
  const liveSuccess =
    activity?.source === "dictation" && activity?.state === "complete";
  const hotkey = String(
    (settings.data.hotkey as Record<string, unknown> | undefined)?.key ??
      "your HoldSpeak hotkey",
  );
  const presenceOn = Boolean(
    (settings.data.presence as Record<string, unknown> | undefined)?.enabled,
  );

  useEffect(() => {
    heading.current?.focus();
  }, [step]);
  useEffect(() => {
    if (liveSuccess && step === 3)
      setNote({
        tone: "success",
        text: "Your first dictation reached its destination.",
      });
  }, [liveSuccess, step]);
  const progress = useMemo(
    () => Math.round(((step + 1) / STEPS.length) * 100),
    [step],
  );

  const discover = async () => {
    setBusy(true);
    setNote(null);
    try {
      const value = await apiFetch<{ models?: string[]; detail?: string }>(
        "/api/setup/discover-models",
        { method: "POST", json: { base_url: endpoint } },
      );
      setEndpointModels(value.models ?? []);
      setModel(value.models?.[0] ?? "");
      setNote({
        tone: "success",
        text: value.models?.length
          ? "Choose the model this profile should run."
          : (value.detail ?? "Connected, but no models were listed."),
      });
    } catch (error) {
      setNote({ tone: "error", text: readableError(error) });
    } finally {
      setBusy(false);
    }
  };

  const saveModel = async () => {
    setBusy(true);
    setNote(null);
    try {
      if (backend === "openai_compatible") {
        const name = new URL(endpoint).host;
        const created = await apiFetch<{
          profile?: Record<string, unknown>;
          id?: string;
        }>("/api/profiles", {
          method: "POST",
          json: {
            name,
            kind: "openAICompatible",
            base_url: endpoint,
            model,
            context_limit: 32768,
            requires_key: false,
          },
        });
        const id = String(created.profile?.id ?? created.id ?? "");
        await apiFetch("/api/settings", {
          method: "PUT",
          json: {
            dictation: {
              pipeline: { enabled: true },
              runtime: { backend, profile_id: id },
            },
          },
        });
      } else if (backend !== "basic") {
        await apiFetch("/api/settings", {
          method: "PUT",
          json: {
            dictation: {
              pipeline: { enabled: true },
              runtime: {
                backend,
                [backend === "mlx" ? "mlx_model" : "llama_cpp_model_path"]:
                  modelPath,
              },
            },
          },
        });
      }
      setNote({ tone: "success", text: "Runtime choice saved on the hub." });
    } catch (error) {
      setNote({ tone: "error", text: readableError(error) });
    } finally {
      setBusy(false);
    }
  };

  const testRuntime = async () => {
    setBusy(true);
    setNote(null);
    try {
      const result = await apiFetch<{ ok?: boolean; detail?: string }>(
        "/api/setup/runtime-test",
        { method: "POST" },
      );
      setNote({
        tone: result.ok ? "success" : "error",
        text:
          result.detail ??
          (result.ok ? "Runtime is ready." : "Runtime test failed."),
      });
    } catch (error) {
      setNote({ tone: "error", text: readableError(error) });
    } finally {
      setBusy(false);
    }
  };

  const setPresence = async (enabled: boolean) => {
    setBusy(true);
    setNote(null);
    try {
      const result = await apiFetch<{ settings?: Record<string, unknown> }>(
        "/api/settings",
        { method: "PUT", json: { presence: { enabled } } },
      );
      settings.setData(result.settings ?? settings.data);
      setNote({
        tone: "success",
        text: enabled ? "Desktop Presence is on." : "Desktop Presence is off.",
      });
    } catch (error) {
      setNote({ tone: "error", text: readableError(error) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="welcome-shell" id="main" tabIndex={-1}>
      <div className="welcome-mark">◍ HoldSpeak</div>
      <div
        className="welcome-progress"
        aria-label={`Step ${step + 1} of ${STEPS.length}`}
      >
        <span style={{ width: `${progress}%` }} />
      </div>
      <section className="welcome-card">
        <span className="signal-eyebrow">
          Step {step + 1} of {STEPS.length}
        </span>
        <h1 ref={heading} tabIndex={-1}>
          {STEPS[step]}
        </h1>
        {step === 0 ? (
          <>
            <p>
              One copilot, two modes: speak into any app, or turn a conversation
              into useful work.
            </p>
            <InlineMessage tone="info">
              Your hub remains the source of truth for privacy, models, and
              readiness.
            </InlineMessage>
          </>
        ) : null}
        {step === 1 ? (
          <div className="data-list">
            {permissionRows.length ? (
              permissionRows.map((row, index) => (
                <div className="data-row" key={String(row.id ?? index)}>
                  <div>
                    <strong>{String(row.label ?? row.id)}</strong>
                    <small>{String(row.detail ?? "")}</small>
                  </div>
                  <StatusPill
                    tone={row.status === "pass" ? "success" : "warning"}
                  >
                    {String(row.status ?? "unknown")}
                  </StatusPill>
                </div>
              ))
            ) : (
              <InlineMessage tone="info">
                Grant microphone and accessibility permission when HoldSpeak
                asks. You can continue and revisit Setup at any time.
              </InlineMessage>
            )}
          </div>
        ) : null}
        {step === 2 ? (
          <div className="welcome-stack">
            <div className="choice-grid">
              {[
                [
                  "basic",
                  "Basic voice typing",
                  "Whisper transcription without an LLM rewrite.",
                ],
                ["mlx", "Apple Silicon", "A local MLX model on this Mac."],
                ["llama_cpp", "Local GGUF", "A local llama.cpp model."],
                [
                  "openai_compatible",
                  "Model server",
                  "A local, LAN, or hosted OpenAI-compatible endpoint.",
                ],
              ].map(([id, label, description]) => (
                <ChoiceCard
                  key={id}
                  name="backend"
                  value={id}
                  checked={backend === id}
                  onChange={() => {
                    setBackend(id);
                    setNote(null);
                  }}
                  label={label}
                  description={description}
                />
              ))}
            </div>
            {backend === "mlx" || backend === "llama_cpp" ? (
              <Field
                label="Model"
                description="Choose a discovered model or enter its full path."
              >
                {({ id, describedBy }) => (
                  <>
                    <Select
                      id={id}
                      aria-describedby={describedBy}
                      value={modelPath}
                      onChange={(event) => setModelPath(event.target.value)}
                    >
                      <option value="">Choose a discovered model</option>
                      {models.map((item) => (
                        <option key={item.value} value={item.value}>
                          {item.label}
                        </option>
                      ))}
                    </Select>
                    <TextInput
                      aria-label="Custom model path"
                      value={modelPath}
                      onChange={(event) => setModelPath(event.target.value)}
                      placeholder="~/Models/…"
                    />
                  </>
                )}
              </Field>
            ) : null}
            {backend === "openai_compatible" ? (
              <>
                <Field
                  label="Server address"
                  description="Include /v1 when your server expects it."
                >
                  {({ id, describedBy }) => (
                    <TextInput
                      id={id}
                      aria-describedby={describedBy}
                      type="url"
                      value={endpoint}
                      onChange={(event) => setEndpoint(event.target.value)}
                      placeholder="http://localhost:11434/v1"
                    />
                  )}
                </Field>
                <Button loading={busy} onClick={discover}>
                  Connect and list models
                </Button>
                {endpointModels.length ? (
                  <Field label="Model">
                    {({ id }) => (
                      <Select
                        id={id}
                        value={model}
                        onChange={(event) => setModel(event.target.value)}
                      >
                        {endpointModels.map((item) => (
                          <option key={item}>{item}</option>
                        ))}
                      </Select>
                    )}
                  </Field>
                ) : null}
              </>
            ) : null}
            <div className="button-row">
              <Button
                variant="primary"
                loading={busy}
                disabled={
                  (backend === "openai_compatible" && !model) ||
                  ((backend === "mlx" || backend === "llama_cpp") && !modelPath)
                }
                onClick={saveModel}
              >
                Save model choice
              </Button>
              <Button loading={busy} onClick={testRuntime}>
                Test runtime
              </Button>
            </div>
          </div>
        ) : null}
        {step === 3 ? (
          <Panel title="Try it in any app" eyebrow="Moment of truth">
            <p>
              Hold <strong>{hotkey}</strong>, speak a sentence, then release.
              This page listens for the hub-reported completion frame.
            </p>
            <StatusPill
              tone={liveSuccess ? "success" : activity ? "live" : "neutral"}
            >
              {liveSuccess
                ? "It worked — dictation complete"
                : String(activity?.state ?? "Waiting")}
            </StatusPill>
          </Panel>
        ) : null}
        {step === 4 ? (
          <>
            <p>
              Desktop Presence can show a quiet HUD and Qlippy cards when the
              hub reports useful work.
            </p>
            <Switch
              label="Desktop Presence"
              description="Config-backed and reversible at any time."
              checked={presenceOn}
              disabled={busy}
              onChange={(event) => void setPresence(event.target.checked)}
            />
            <Link className="btn btn--secondary" to="/settings">
              Review Presence settings
            </Link>
          </>
        ) : null}
        {step === 5 ? (
          <>
            <p>
              The Desk is your front door. Dictation and Meetings remain one
              move away.
            </p>
            <Link className="btn btn--primary" to="/">
              Enter the Desk
            </Link>
          </>
        ) : null}
        {note ? (
          <InlineMessage tone={note.tone}>{note.text}</InlineMessage>
        ) : null}
        <footer className="welcome-actions">
          {step > 0 ? (
            <Button
              variant="ghost"
              onClick={() => setStep((value) => value - 1)}
            >
              Back
            </Button>
          ) : (
            <span />
          )}
          {step < STEPS.length - 1 ? (
            <Button
              variant="primary"
              onClick={() => setStep((value) => value + 1)}
            >
              {step === 0 ? "Begin" : "Continue"}
            </Button>
          ) : null}
        </footer>
      </section>
    </main>
  );
}
