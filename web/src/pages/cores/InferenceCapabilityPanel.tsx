import { useEffect, useId, useState } from "react";
import { Button } from "../../components/signal/Signal";
import type {
  HostedInferencePreset,
  InferenceAcquisition,
  InferencePreset,
  InferenceSetup,
  InferenceSetupArtifact,
  LocalInferencePreset,
} from "./inferenceSetup";

type ExistingTarget = { id: string; key_present: boolean };
type ChoiceMode = "device" | "hosted" | "experimental";

function bytes(value: number | null): string {
  if (value == null || !Number.isFinite(value) || value < 0) return "Unknown";
  if (value < 1024 ** 3) return `${Math.max(1, Math.round(value / 1024 ** 2))} MB`;
  return `${Math.round((value / 1024 ** 3) * 10) / 10} GB`;
}
function context(value: number): string {
  return value >= 1024 && value % 1024 === 0
    ? `${value / 1024}K`
    : `${value.toLocaleString()} tokens`;
}

function modelLabel(choice: InferencePreset | InferenceSetupArtifact): string {
  return choice.label
    .replace(/^OpenRouter · /, "")
    .replace(/^Quick local Qwen$/, "Quick Qwen")
    .replace(/^Tiny local Qwen$/, "Tiny Qwen");
}

function modelSummary(preset: InferencePreset): string {
  const summaries: Record<string, string> = {
    preset_local_qwen35_4b_gguf_q4km: "Fast everyday model.",
    preset_local_qwen35_08b_gguf_q4km: "Lightweight intent and routing.",
    preset_openrouter_qwen3_8b: "Fast everyday model.",
    preset_openrouter_qwen35_35b_a3b: "General reasoning.",
    preset_openrouter_qwen38_27b: "Harder reasoning and synthesis.",
    preset_openrouter_qwen37_flash: "Fast, economical everyday model.",
    preset_openrouter_gemma4_26b: "Writing and synthesis.",
    preset_openrouter_qwen3_coder_next: "Technical planning and code.",
  };
  return summaries[preset.id] || preset.summary;
}

function hardwareLine(setup: InferenceSetup): string {
  const { capability, detection } = setup.hardware;
  if (detection.state === "unavailable") return "Hardware details unavailable";
  const platform = capability.apple_silicon
    ? "Apple Silicon"
    : [capability.system, capability.architecture].filter(Boolean).join(" · ");
  const memory =
    capability.total_memory_bytes == null
      ? "memory unknown"
      : `${bytes(capability.total_memory_bytes)} ${capability.unified_memory ? "unified memory" : "memory"}`;
  return `${platform || "This device"} · ${memory}`;
}

function supportLabel(
  state: "current_v1" | "unsupported" | "candidate",
): string {
  switch (state) {
    case "current_v1":
      return "Used by Thoughts now";
    case "candidate":
      return "Detected · not configured";
    case "unsupported":
      return "Not available for Thoughts yet";
  }
}

function artifactActivation(artifact: InferenceSetupArtifact): InferenceSetupArtifact["activation"] {
  if (artifact.activation) return artifact.activation;
  if (artifact.configured_for_thoughts) {
    return { state: "current", action: "none", context_tokens: 8192, reason: "Thoughts already use this model." };
  }
  return {
    state: artifact.format === "gguf" ? "available" : "unsupported",
    action: artifact.format === "gguf" ? "use_existing" : "none",
    context_tokens: artifact.format === "gguf" ? 8192 : null,
    reason: artifact.thought_support.reason || "This model is not available for Thoughts yet.",
  };
}

export function InferenceCapabilityPanel({
  setup,
  loading,
  error,
  targets,
  targetsLoading,
  busyPresetId,
  status,
  onRetry,
  onUseHosted,
  onDownloadLocal,
  onAddExisting,
  onCancelAcquisition,
}: {
  setup: InferenceSetup | null;
  loading: boolean;
  error: string;
  targets: ExistingTarget[];
  targetsLoading: boolean;
  busyPresetId: string | null;
  status: string;
  onRetry(): void;
  onUseHosted(preset: HostedInferencePreset, key: string): Promise<boolean>;
  onDownloadLocal?(preset: LocalInferencePreset): Promise<void>;
  onAddExisting?(artifact: InferenceSetupArtifact): Promise<void>;
  onCancelAcquisition?(acquisition: InferenceAcquisition): Promise<void>;
}) {
  const groupName = useId();
  const [selectedId, setSelectedId] = useState("");
  const [choiceMode, setChoiceMode] = useState<ChoiceMode>("device");
  const [key, setKey] = useState("");

  useEffect(() => {
    if (!setup) {
      setSelectedId("");
      return;
    }
    const choices = [...setup.detected_local_artifacts, ...setup.presets];
    if (!choices.length) {
      setSelectedId("");
      return;
    }
    const current = setup.current_routes.thoughts.target_id;
    const currentPreset = setup.presets.find(
      (preset) =>
        preset.kind === "hosted_profile_preset" &&
        preset.existing_profile.target_id === current,
    );
    const currentArtifact = setup.detected_local_artifacts.find(
      (artifact) => artifact.configured_for_thoughts,
    );
    setSelectedId((prior) => {
      const next =
        currentPreset?.id || currentArtifact?.id ||
        (choices.some((choice) => choice.id === prior) ? prior : choices[0].id);
      const preset = setup.presets.find((choice) => choice.id === next);
      setChoiceMode(
        preset?.kind === "hosted_profile_preset"
          ? "hosted"
          : preset?.kind === "local_artifact_preset" && preset.activation === "evaluation_only"
            ? "experimental"
            : "device",
      );
      return next;
    });
  }, [setup]);

  if (loading && !setup) {
    return (
      <section className="models-capability-opening" aria-busy="true">
        <span>Loading models…</span>
      </section>
    );
  }
  if (error || !setup) {
    return (
      <section className="models-capability-opening" role="alert">
        <strong>Models couldn’t load.</strong>
        <p>{error || "Try again."}</p>
        <Button variant="primary" onClick={onRetry}>
          TRY AGAIN
        </Button>
      </section>
    );
  }

  const deployment = setup.current_thought_deployment;
  const routeModel =
    deployment.execution_revision?.schema_version === 2
      ? deployment.execution_revision.model
      : deployment.target.model;
  const routePreset = setup.presets.find(
    (preset) =>
      preset.kind === "hosted_profile_preset" &&
      preset.existing_profile.target_id === setup.current_routes.thoughts.target_id,
  );
  const routeArtifact = setup.detected_local_artifacts.find(
    (artifact) => artifact.configured_for_thoughts,
  );
  const selected: InferencePreset | null =
    setup.presets.find((preset) => preset.id === selectedId) || null;
  const selectedArtifact =
    setup.detected_local_artifacts.find((artifact) => artifact.id === selectedId) || null;
  const selectedHosted = selected?.kind === "hosted_profile_preset" ? selected : null;
  const selectedLocal = selected?.kind === "local_artifact_preset" ? selected : null;
  const existing = selected
    && selected.kind === "hosted_profile_preset"
    ? targets.find(
        (target) => target.id === selected.existing_profile.target_id,
      )
    : null;
  const current =
    selectedHosted?.existing_profile.target_id ===
    setup.current_routes.thoughts.target_id;
  const canUse = Boolean(selectedHosted && (existing?.key_present || key.trim()));
  const localPresets = setup.presets.filter(
    (preset): preset is LocalInferencePreset => preset.kind === "local_artifact_preset",
  );
  const downloadableLocalPresets = localPresets.filter(
    (preset) => preset.activation === "download",
  );
  const evaluationLocalPresets = localPresets.filter(
    (preset) => preset.activation === "evaluation_only",
  );
  const hostedPresets = setup.presets.filter(
    (preset): preset is HostedInferencePreset => preset.kind === "hosted_profile_preset",
  );
  const deviceChoices: Array<InferenceSetupArtifact | LocalInferencePreset> = [
    ...setup.detected_local_artifacts,
    ...downloadableLocalPresets,
  ];
  const visibleChoices: Array<InferenceSetupArtifact | InferencePreset> =
    choiceMode === "hosted"
      ? hostedPresets
      : choiceMode === "experimental"
        ? evaluationLocalPresets
        : deviceChoices;
  const acquisition = selectedLocal
    ? (setup.acquisitions ?? []).find((row) => row.preset_id === selectedLocal.id) || null
    : selectedArtifact
      ? (setup.acquisitions ?? []).find((row) => row.preset_id === selectedArtifact.id) || null
      : null;
  const selectedArtifactActivation = selectedArtifact
    ? artifactActivation(selectedArtifact)
    : null;
  // Acquisition makes a model available in the library.  It does not choose
  // the model for Thoughts (that is a later capability-assignment decision).
  const acquisitionAdded =
    acquisition?.state === "ready" &&
    acquisition.activation_state === "not_requested";

  const selectChoice = (id: string) => {
    setSelectedId(id);
    setKey("");
  };

  const chooseMode = (mode: ChoiceMode) => {
    const choices =
      mode === "hosted"
        ? hostedPresets
        : mode === "experimental"
          ? evaluationLocalPresets
          : deviceChoices;
    setChoiceMode(mode);
    selectChoice(
      choices.length
        ? choices.some((choice) => choice.id === selectedId)
          ? selectedId
          : choices[0].id
        : "",
    );
  };

  return (
    <>
      <section
        className="models-model-picker"
        aria-labelledby="models-capability-title"
      >
        <header className="models-picker-header">
          <h2 id="models-capability-title">Choose a model</h2>
          <div
            className="models-current-route"
            data-available={deployment.execution_support.executable || undefined}
            title={deployment.execution_support.reason || undefined}
          >
            <span>Thoughts</span>
            <strong>
              {deployment.execution_support.executable
                ? routePreset
                  ? modelLabel(routePreset)
                  : routeArtifact
                    ? modelLabel(routeArtifact)
                    : routeModel || deployment.target.name
                : "Not configured"}
            </strong>
          </div>
        </header>

        <div className="models-model-picker-body">
          <div className="models-model-picker-main">
            <div className="models-source-choices" role="tablist" aria-label="Model source">
              <button type="button" role="tab" aria-selected={choiceMode === "device"} onClick={() => chooseMode("device")}>
                <strong>This device</strong><span>{deviceChoices.length}</span>
              </button>
              <button type="button" role="tab" aria-selected={choiceMode === "hosted"} disabled={!hostedPresets.length} onClick={() => chooseMode("hosted")}>
                <strong>OpenRouter</strong><span>{hostedPresets.length}</span>
              </button>
              <button type="button" role="tab" aria-selected={choiceMode === "experimental"} disabled={!evaluationLocalPresets.length} onClick={() => chooseMode("experimental")}>
                <strong>Experimental</strong><span>{evaluationLocalPresets.length}</span>
              </button>
            </div>

            {choiceMode === "device" ? (
              <p className="models-picker-facts">
                {hardwareLine(setup)} · {setup.detected_local_artifacts.length} detected · {downloadableLocalPresets.length} to download
                {setup.artifact_detection.state === "complete"
                  ? ""
                  : ` · Scan ${setup.artifact_detection.state}`}
              </p>
            ) : null}

            {visibleChoices.length ? (
              <div className="models-capability-radio" role="radiogroup" aria-label="AI choices">
                {visibleChoices.map((choice) => {
                  const artifact = "thought_support" in choice ? (choice as InferenceSetupArtifact) : null;
                  const preset = artifact ? null : (choice as InferencePreset);
                  const selectedCard = choice.id === selectedId;
                  const meta = artifact
                    ? `${artifact.format.toUpperCase()} · ${bytes(artifact.size_bytes)}`
                    : preset?.kind === "hosted_profile_preset"
                      ? `${preset.experience} · ${context(preset.context.working_ceiling_tokens)}`
                      : preset?.activation === "evaluation_only"
                        ? `${bytes(preset.source.download_bytes)} · ${context(preset.context.recommended_tokens)}`
                        : `${preset?.experience} · ${bytes(preset?.source.download_bytes ?? 0)} · ${context(preset?.context.recommended_tokens ?? 8192)}`;
                  const descriptor = artifact
                    ? supportLabel(artifact.thought_support.state)
                    : preset?.kind === "local_artifact_preset" && preset.activation === "evaluation_only"
                      ? "Tool calling"
                    : preset ? modelSummary(preset) : "Configured connection";
                  return (
                    <label key={choice.id} className="models-capability-card models-capability-card-compact" data-selected={selectedCard || undefined}>
                      <input type="radio" name={groupName} value={choice.id} checked={selectedCard} onChange={() => selectChoice(choice.id)} />
                      <strong>{modelLabel(choice)}</strong>
                      <span>{descriptor}</span>
                      <small>{meta}</small>
                    </label>
                  );
                })}
              </div>
            ) : (
              <div className="models-capability-empty"><strong>No models here</strong></div>
            )}
          </div>

          <aside className="models-model-detail" aria-live="polite">
            <div className="models-capability-action">
              {selected || selectedArtifact ? (
                <>
                  <div>
                    <strong>{selected ? modelLabel(selected) : selectedArtifact ? modelLabel(selectedArtifact) : ""}</strong>
                  </div>
                  <span className="models-selected-summary">
                  {acquisition
                    ? acquisition.state === "downloading"
                      ? `Downloading ${bytes(acquisition.transport_bytes)} of ${bytes(acquisition.bytes_total)}`
                      : acquisition.state === "verifying"
                        ? selectedArtifact
                          ? "Verifying…"
                          : "Verifying the published checksum…"
                        : acquisition.state === "installing"
                          ? selectedArtifact
                            ? "Installing…"
                            : "Installing…"
                          : acquisitionAdded
                            ? "Available in Models"
                            : acquisition.state === "ready" && acquisition.activation_state === "in_use"
                            ? "In use"
                            : acquisition.error?.message || acquisition.state
                    : selectedArtifact
                      ? selectedArtifactActivation?.state === "current"
                        ? "In use"
                        : selectedArtifactActivation?.action === "use_existing"
                          ? "Verify before adding."
                          : selectedArtifactActivation?.reason
                    : selectedLocal
                      ? selectedLocal.activation === "evaluation_only"
                        ? `${bytes(selectedLocal.source.download_bytes)} · ${context(selectedLocal.context.recommended_tokens)} · ${selectedLocal.source.license}`
                        : `Local · ${context(selectedLocal.context.recommended_tokens)} · ${bytes(selectedLocal.source.download_bytes)} download`
                    : current
                    ? "In use"
                    : existing?.key_present
                      ? `OpenRouter · ${context(selectedHosted?.context.working_ceiling_tokens || 8192)}`
                      : `OpenRouter key required · ${context(selectedHosted?.context.working_ceiling_tokens || 8192)}`}
                </span>
              {selectedHosted && !current && !targetsLoading && !existing?.key_present ? (
                <label>
                  <span>OpenRouter key</span>
                  <input
                    type="password"
                    autoComplete="new-password"
                    value={key}
                    placeholder="sk-or-v1-…"
                    onChange={(event) => setKey(event.target.value)}
                  />
                </label>
              ) : null}
              {selectedArtifact ? (
                acquisition && ["requested", "resolving_source"].includes(acquisition.state) ? (
                  <span className="models-capability-action-status">PREPARING…</span>
                ) : acquisition && ["verifying", "installing"].includes(acquisition.state) ? (
                  <span className="models-capability-action-status">
                    {acquisition.state === "verifying" ? "VERIFYING…" : "INSTALLING…"}
                  </span>
                ) : acquisitionAdded ? (
                  <span className="models-capability-action-status">ADDED</span>
                ) : acquisition?.state === "ready" && acquisition.activation_state === "in_use" ? (
                  <span className="models-capability-action-status">IN USE</span>
                ) : selectedArtifactActivation?.action === "use_existing" ? (
                  <Button
                    variant="primary"
                    disabled={Boolean(busyPresetId)}
                    loading={busyPresetId === selectedArtifact.id}
                    onClick={() => void onAddExisting?.(selectedArtifact)}
                  >
                    {acquisition?.state === "failed" ? "TRY AGAIN" : "ADD MODEL"}
                  </Button>
                ) : (
                  <span className="models-capability-action-status">
                    {selectedArtifact.configured_for_thoughts
                      ? "IN USE"
                      : selectedArtifactActivation?.reason.toUpperCase()}
                  </span>
                )
              ) : selectedLocal ? (
                selectedLocal.activation === "evaluation_only" ? (
                  <span className="models-capability-action-status">
                    Evaluation only · tool execution isn’t available yet.
                  </span>
                ) : acquisition && ["requested", "resolving_source", "downloading"].includes(acquisition.state) ? (
                  <>
                    <progress
                      max={acquisition.bytes_total}
                      value={acquisition.transport_bytes}
                      aria-label={`Downloading ${selectedLocal.label}`}
                    />
                    {acquisition.can_cancel ? (
                      <Button onClick={() => void onCancelAcquisition?.(acquisition)}>
                        CANCEL DOWNLOAD
                      </Button>
                    ) : null}
                  </>
                ) : acquisition && ["verifying", "installing"].includes(acquisition.state) ? (
                  <span className="models-capability-action-status">
                    {acquisition.state === "verifying" ? "VERIFYING…" : "INSTALLING…"}
                  </span>
                ) : acquisitionAdded ? (
                  <span className="models-capability-action-status">ADDED</span>
                ) : acquisition?.state === "ready" && acquisition.activation_state === "in_use" ? (
                  <span className="models-capability-action-status">IN USE</span>
                ) : (
                  <Button
                    variant="primary"
                    disabled={Boolean(busyPresetId)}
                    loading={busyPresetId === selectedLocal.id}
                    onClick={() => void onDownloadLocal?.(selectedLocal)}
                  >
                    {acquisition?.state === "failed" ? "TRY AGAIN" : "DOWNLOAD"}
                  </Button>
                )
              ) : current ? (
                <span className="models-capability-action-status">
                  IN USE
                </span>
              ) : targetsLoading ? (
                <span className="models-capability-action-status">
                  LOADING CONNECTION…
                </span>
              ) : canUse ? (
                <Button
                  variant="primary"
                  loading={busyPresetId === selectedHosted?.id}
                  disabled={Boolean(busyPresetId)}
                  onClick={async () => {
                    if (selectedHosted && await onUseHosted(selectedHosted, key.trim())) setKey("");
                  }}
                >
                  {existing?.key_present
                    ? "USE MODEL"
                    : "CONNECT & USE"}
                </Button>
              ) : (
                <span className="models-capability-action-status">
                  ENTER AN OPENROUTER KEY
                </span>
              )}
            </>
          ) : (
            <span className="models-capability-action-status">
              NO MODEL SELECTED
            </span>
          )}
            </div>
          </aside>
        </div>
        {status ? (
          <p className="models-preset-status" role="status">
            {status}
          </p>
        ) : null}
      </section>

      {setup.limitations.length ? (
        <details className="models-capability-limits">
          <summary>{setup.limitations.length} setup {setup.limitations.length === 1 ? "issue" : "issues"}</summary>
          <div>
            {setup.limitations.map((limitation) => (
              <article key={limitation.code}>
                <strong>{limitation.title}</strong>
                <p>{limitation.detail}</p>
                <small>{limitation.repair.label}</small>
              </article>
            ))}
          </div>
        </details>
      ) : null}
    </>
  );
}
