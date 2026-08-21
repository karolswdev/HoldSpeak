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
  onUseExisting,
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
  onUseExisting?(artifact: InferenceSetupArtifact): Promise<void>;
  onCancelAcquisition?(acquisition: InferenceAcquisition): Promise<void>;
}) {
  const groupName = useId();
  const [selectedId, setSelectedId] = useState("");
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
    setSelectedId(
      (prior) =>
        currentPreset?.id || currentArtifact?.id ||
        (choices.some((choice) => choice.id === prior)
          ? prior
          : choices[0].id),
    );
  }, [setup]);

  if (loading && !setup) {
    return (
      <section className="models-capability-opening" aria-busy="true">
        <span>Reading this hub…</span>
      </section>
    );
  }
  if (error || !setup) {
    return (
      <section className="models-capability-opening" role="alert">
        <strong>Could not read this hub’s AI setup.</strong>
        <p>{error || "The setup projection is unavailable."}</p>
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
  const acquisition = selectedLocal
    ? (setup.acquisitions ?? []).find((row) => row.preset_id === selectedLocal.id) || null
    : selectedArtifact
      ? (setup.acquisitions ?? []).find((row) => row.preset_id === selectedArtifact.id) || null
      : null;

  const selectChoice = (id: string) => {
    setSelectedId(id);
    setKey("");
  };

  return (
    <>
      <section
        className="models-capability-intro"
        aria-labelledby="models-capability-title"
      >
        <div>
          <p className="models-setup-kicker">AI setup</p>
          <h2 id="models-capability-title">Choose your AI</h2>
          <p>
            Choose a private local model or a configured connection. A local
            download starts only when you explicitly ask.
          </p>
        </div>
        <div
          className="models-current-route"
          data-available={deployment.execution_support.executable || undefined}
        >
          <span>Thoughts &amp; notes</span>
          <strong>
            {deployment.target.name}
            {routeModel ? ` · ${routeModel}` : ""}
          </strong>
          <small>
            {deployment.execution_support.executable
              ? "Available for Thoughts"
              : deployment.execution_support.reason ||
                "Not available for Thoughts"}
          </small>
        </div>
      </section>

      <section
        className="models-capability-device"
        aria-labelledby="models-device-title"
      >
        <header>
          <div>
            <p className="models-setup-kicker">This device</p>
            <h3 id="models-device-title">{hardwareLine(setup)}</h3>
          </div>
          {setup.hardware.detection.reason ? (
            <p>{setup.hardware.detection.reason}</p>
          ) : null}
        </header>
        {setup.detected_local_artifacts.length ? (
          <p className="models-device-summary">
            <strong>{setup.detected_local_artifacts.length} local model{setup.detected_local_artifacts.length === 1 ? "" : "s"} found.</strong>{" "}
            Choose one below to see what HoldSpeak can use now.
          </p>
        ) : setup.artifact_detection.state === "complete" ? (
          <div className="models-capability-empty">
            <strong>No local AI detected</strong>
            <p>
              You can keep using a configured connection or add an existing
              model in Advanced.
            </p>
          </div>
        ) : (
          <div className="models-capability-empty">
            <strong>
              Local AI inspection{" "}
              {setup.artifact_detection.state === "partial"
                ? "incomplete"
                : "unavailable"}
            </strong>
            <p>
              {setup.artifact_detection.reason ||
                "This hub could not verify whether local AI is present."}
            </p>
          </div>
        )}
      </section>

      <section
        className="models-capability-choices"
        aria-labelledby="models-choices-title"
      >
        <header>
          <p className="models-setup-kicker">Thoughts &amp; notes</p>
          <h3 id="models-choices-title">Choose an experience</h3>
          <p>
            These choices come from this hub’s verified catalog. Selecting one
            changes nothing.
          </p>
        </header>
        <div
          className="models-capability-radio"
          role="radiogroup"
          aria-label="AI choices"
        >
          {setup.detected_local_artifacts.length ? (
            <div className="models-choice-group" data-kind="detected">
              <h4>Already on this device</h4>
              {setup.detected_local_artifacts.map((artifact) => {
                const selectedCard = artifact.id === selectedId;
                return (
                  <label
                    key={artifact.id}
                    className="models-capability-card models-capability-card-compact"
                    data-selected={selectedCard || undefined}
                  >
                    <input
                      type="radio"
                      name={groupName}
                      value={artifact.id}
                      checked={selectedCard}
                      onChange={() => selectChoice(artifact.id)}
                    />
                    <span className="models-capability-experience">
                      {artifact.format === "gguf" ? "On device · GGUF" : "On device · MLX"}
                    </span>
                    <strong>{artifact.label}</strong>
                    <span>
                      <span>{supportLabel(artifact.thought_support.state)}</span>
                      {` · ${bytes(artifact.size_bytes)}`}
                    </span>
                  </label>
                );
              })}
            </div>
          ) : null}

          {downloadableLocalPresets.length ? (
            <div className="models-choice-group" data-kind="download">
              <h4>Suggested local models</h4>
              {downloadableLocalPresets.map((preset) => {
                const selectedCard = preset.id === selectedId;
                return (
                  <label
                    key={preset.id}
                    className="models-capability-card models-capability-card-compact"
                    data-selected={selectedCard || undefined}
                  >
                    <input
                      type="radio"
                      name={groupName}
                      value={preset.id}
                      checked={selectedCard}
                      onChange={() => selectChoice(preset.id)}
                    />
                    <span className="models-capability-experience">{preset.experience} · Download</span>
                    <strong>{preset.label}</strong>
                    <span>{preset.summary || `${preset.label} for private local work.`}</span>
                  </label>
                );
              })}
            </div>
          ) : null}

          {evaluationLocalPresets.length ? (
            <div className="models-choice-group" data-kind="evaluation">
              <h4>Experimental tool models</h4>
              {evaluationLocalPresets.map((preset) => {
                const selectedCard = preset.id === selectedId;
                return (
                  <label
                    key={preset.id}
                    className="models-capability-card models-capability-card-compact"
                    data-selected={selectedCard || undefined}
                  >
                    <input
                      type="radio"
                      name={groupName}
                      value={preset.id}
                      checked={selectedCard}
                      onChange={() => selectChoice(preset.id)}
                    />
                    <span className="models-capability-experience">Experimental · Tool calling</span>
                    <strong>{preset.label}</strong>
                    <span>{preset.summary}</span>
                  </label>
                );
              })}
            </div>
          ) : null}

          {hostedPresets.length ? (
            <div className="models-choice-group" data-kind="hosted">
              <h4>OpenRouter</h4>
              {hostedPresets.map((preset) => {
                const selectedCard = preset.id === selectedId;
                return (
                  <label
                    key={preset.id}
                    className="models-capability-card models-capability-card-compact"
                    data-selected={selectedCard || undefined}
                  >
                    <input
                      type="radio"
                      name={groupName}
                      value={preset.id}
                      checked={selectedCard}
                      onChange={() => selectChoice(preset.id)}
                    />
                    <span className="models-capability-experience">{preset.experience} · Cloud</span>
                    <strong>{preset.label}</strong>
                    <span>{preset.summary || `${preset.label} through OpenRouter.`}</span>
                  </label>
                );
              })}
            </div>
          ) : setup.detected_local_artifacts.length || localPresets.length ? null : (
            <div className="models-capability-empty">
              <strong>No model choices are available on this hub</strong>
              <p>Refresh Models after configuring a runtime or connection.</p>
            </div>
          )}
        </div>
        <div className="models-capability-action" aria-live="polite">
          {selected || selectedArtifact ? (
            <>
              <div>
                <strong>{selected?.label || selectedArtifact?.label}</strong>
                <span>
                  {acquisition
                    ? acquisition.state === "downloading"
                      ? `Downloading ${bytes(acquisition.transport_bytes)} of ${bytes(acquisition.bytes_total)}`
                      : acquisition.state === "verifying"
                        ? selectedArtifact
                          ? "Verifying this model’s complete contents…"
                          : "Verifying the published checksum…"
                        : acquisition.state === "installing"
                          ? selectedArtifact
                            ? "Making this the local AI for Thoughts…"
                            : "Installing verified model bytes…"
                          : acquisition.state === "ready" && acquisition.activation_state === "in_use"
                            ? "Ready · in use for Thoughts"
                            : acquisition.error?.message || acquisition.state
                    : selectedArtifact
                      ? artifactActivation(selectedArtifact).reason
                    : selectedLocal
                      ? selectedLocal.activation === "evaluation_only"
                        ? `${bytes(selectedLocal.source.download_bytes)} · ${selectedLocal.source.license} · evaluation candidate for HoldSpeak’s future tool-turn runtime`
                        : `${context(selectedLocal.context.recommended_tokens)} context · ${bytes(selectedLocal.source.download_bytes)} download · runs only on this device`
                    : current
                    ? "Currently used for Thoughts & notes"
                    : existing?.key_present
                      ? `Already configured · ${context(selectedHosted?.context.working_ceiling_tokens || 8192)} working context`
                      : `Requires an OpenRouter key · ${context(selectedHosted?.context.working_ceiling_tokens || 8192)} working context`}
                </span>
              </div>
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
                  <span className="models-capability-action-status">PREPARING VERIFICATION…</span>
                ) : acquisition && ["verifying", "installing"].includes(acquisition.state) ? (
                  <span className="models-capability-action-status">
                    {acquisition.state === "verifying" ? "VERIFYING…" : "MAKING IT AVAILABLE…"}
                  </span>
                ) : acquisition?.state === "ready" && acquisition.activation_state === "in_use" ? (
                  <span className="models-capability-action-status">IN USE FOR THOUGHTS</span>
                ) : artifactActivation(selectedArtifact).action === "use_existing" ? (
                  <Button
                    variant="primary"
                    disabled={Boolean(busyPresetId)}
                    loading={busyPresetId === selectedArtifact.id}
                    onClick={() => void onUseExisting?.(selectedArtifact)}
                  >
                    {acquisition?.state === "failed" ? "TRY AGAIN" : "USE THIS MODEL"}
                  </Button>
                ) : (
                  <span className="models-capability-action-status">
                    {selectedArtifact.configured_for_thoughts
                      ? "IN USE FOR THOUGHTS"
                      : artifactActivation(selectedArtifact).reason.toUpperCase()}
                  </span>
                )
              ) : selectedLocal ? (
                selectedLocal.activation === "evaluation_only" ? (
                  <span className="models-capability-action-status">
                    PRESENTED FOR EVALUATION · NOT ENABLED FOR TOOL EXECUTION
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
                ) : acquisition?.state === "ready" && acquisition.activation_state === "in_use" ? (
                  <span className="models-capability-action-status">IN USE FOR THOUGHTS</span>
                ) : (
                  <Button
                    variant="primary"
                    disabled={Boolean(busyPresetId)}
                    loading={busyPresetId === selectedLocal.id}
                    onClick={() => void onDownloadLocal?.(selectedLocal)}
                  >
                    {acquisition?.state === "failed" ? "TRY AGAIN" : `DOWNLOAD & USE ${selectedLocal.experience.toUpperCase()}`}
                  </Button>
                )
              ) : current ? (
                <span className="models-capability-action-status">
                  IN USE FOR THOUGHTS
                </span>
              ) : targetsLoading ? (
                <span className="models-capability-action-status">
                  READING SAVED CONNECTION…
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
                    ? `USE ${selectedHosted?.experience.toUpperCase()}`
                    : `ADD & USE ${selectedHosted?.experience.toUpperCase()}`}
                </Button>
              ) : (
                <span className="models-capability-action-status">
                  ENTER A KEY TO CONTINUE
                </span>
              )}
            </>
          ) : (
            <span className="models-capability-action-status">
              NO MODEL SELECTED
            </span>
          )}
        </div>
        {status ? (
          <p className="models-preset-status" role="status">
            {status}
          </p>
        ) : null}
      </section>

      {setup.limitations.length ? (
        <section
          className="models-capability-limits"
          aria-label="AI setup limitations"
        >
          {setup.limitations.map((limitation) => (
            <article key={limitation.code}>
              <strong>{limitation.title}</strong>
              <p>{limitation.detail}</p>
              <small>{limitation.repair.label}</small>
            </article>
          ))}
        </section>
      ) : null}
    </>
  );
}
