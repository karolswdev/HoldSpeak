import { useEffect, useId, useState } from "react";
import { Button } from "../../components/signal/Signal";
import type {
  HostedInferencePreset,
  InferenceAcquisition,
  InferencePreset,
  InferenceSetup,
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
    if (!setup.presets.length) {
      setSelectedId("");
      return;
    }
    const current = setup.current_routes.thoughts.target_id;
    const currentPreset = setup.presets.find(
      (preset) =>
        preset.kind === "hosted_profile_preset" &&
        preset.existing_profile.target_id === current,
    );
    setSelectedId(
      (prior) =>
        currentPreset?.id ||
        (setup.presets.some((preset) => preset.id === prior)
          ? prior
          : setup.presets[0].id),
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
  const acquisition = selectedLocal
    ? (setup.acquisitions ?? []).find((row) => row.preset_id === selectedLocal.id) || null
    : null;

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
          <div className="models-artifact-list" aria-label="Detected local AI">
            {setup.detected_local_artifacts.map((artifact) => (
              <article key={artifact.id}>
                <span>{artifact.format === "gguf" ? "GGUF" : "MLX"}</span>
                <strong>{artifact.label}</strong>
                <small>{supportLabel(artifact.thought_support.state)}</small>
                {artifact.thought_support.reason ? (
                  <p>{artifact.thought_support.reason}</p>
                ) : null}
              </article>
            ))}
          </div>
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
          {setup.presets.length ? (
            setup.presets.map((preset) => {
              const selectedCard = preset.id === selectedId;
              return (
                <label
                  key={preset.id}
                  className="models-capability-card"
                  data-selected={selectedCard || undefined}
                >
                  <input
                    type="radio"
                    name={groupName}
                    value={preset.id}
                    checked={selectedCard}
                    onChange={() => {
                      setSelectedId(preset.id);
                      setKey("");
                    }}
                  />
                  <span className="models-capability-experience">
                    {preset.experience}
                  </span>
                  <strong>{preset.label}</strong>
                  {preset.kind === "hosted_profile_preset" ? (
                    <>
                      <span>
                        Hosted · {context(preset.context.working_ceiling_tokens)}{" "}
                        working ceiling
                      </span>
                      <small>Saved Note material may leave this hub.</small>
                    </>
                  ) : (
                    <>
                      <span>
                        GGUF · {context(preset.context.recommended_tokens)} context
                      </span>
                      <small>Runs only on this device. Note text stays here.</small>
                      <small>
                        {bytes(preset.source.download_bytes)} download · {bytes(preset.source.installed_bytes)} installed · {bytes(preset.source.peak_free_bytes)} free required
                      </small>
                      <small>
                        From Hugging Face · {preset.source.repository} · {preset.source.license}
                      </small>
                    </>
                  )}
                </label>
              );
            })
          ) : (
            <div className="models-capability-empty">
              <strong>No curated hosted choices for this hub</strong>
              <p>Existing connections remain available below.</p>
            </div>
          )}
        </div>
        <div className="models-capability-action" aria-live="polite">
          {selected ? (
            <>
              <div>
                <strong>{selected.label}</strong>
                <span>
                  {selectedLocal && acquisition
                    ? acquisition.state === "downloading"
                      ? `Downloading ${bytes(acquisition.transport_bytes)} of ${bytes(acquisition.bytes_total)}`
                      : acquisition.state === "verifying"
                        ? "Verifying the published checksum…"
                        : acquisition.state === "installing"
                          ? "Installing verified model bytes…"
                          : acquisition.state === "ready" && acquisition.activation_state === "in_use"
                            ? "Ready · in use for Thoughts"
                            : acquisition.error?.message || acquisition.state
                    : selectedLocal
                      ? "Private local model · downloads only on your command"
                    : current
                    ? "Currently used for Thoughts & notes"
                    : existing?.key_present
                      ? "Already configured on this hub"
                      : "Requires an OpenRouter key"}
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
              {selectedLocal ? (
                acquisition && ["requested", "resolving_source", "downloading"].includes(acquisition.state) ? (
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
                  loading={busyPresetId === selected.id}
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
              NO CATALOG ACTION AVAILABLE
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
