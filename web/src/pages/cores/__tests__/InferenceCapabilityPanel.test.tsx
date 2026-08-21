import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { InferenceCapabilityPanel } from "../InferenceCapabilityPanel";
import type { InferenceSetup } from "../inferenceSetup";

const hosted = (id: string, experience: "quick" | "balanced" | "deep") => ({
  kind: "hosted_profile_preset" as const,
  id,
  experience,
  label: `${experience} choice`,
  provider_adapter: "openai_compatible" as const,
  model_id: `provider/${id}`,
  boundary: "external_service" as const,
  secret_requirement: "profile_key" as const,
  context: { support: "bounded" as const, working_ceiling_tokens: 8192 },
  applicability: { state: "applicable" as const, reason: null },
  existing_profile: {
    target_id: `target-${id}`,
    name: `${experience} profile`,
    kind: "openAICompatible" as const,
    base_url: "https://example.test/v1",
    model: `provider/${id}`,
    context_limit: 8192,
    requires_key: true as const,
  },
});

function setup(overrides: Partial<InferenceSetup> = {}): InferenceSetup {
  return {
    schema_version: 1,
    observed_at: "2026-08-21T18:00:00Z",
    preset_catalog: {
      schema_version: 1, catalog_revision: 2,
      generated_at: "2026-08-21T00:00:00Z", expires_at: "2036-08-01T00:00:00Z",
      signing_key_id: "test", sha256: `sha256:${"c".repeat(64)}`,
    },
    hardware: {
      capability: {
        system: "Linux",
        architecture: "x86_64",
        apple_silicon: false,
        total_memory_bytes: 8_589_934_592,
        logical_cpu_count: 8,
        unified_memory: null,
        accelerators: [],
        sha256: "cap",
      },
      observation: {
        available_memory_bytes: null,
        storage_available_bytes: null,
        sha256: "obs",
      },
      detection: {
        state: "partial",
        reason: "Memory pressure could not be observed.",
      },
    },
    runtimes: [],
    current_routes: {
      authority: "config",
      thoughts: { target_id: null, inherits_this_device: true, revision: "route-1" },
      dictation: { target_id: null, backend: "llama_cpp" },
      meetings: { target_id: null, provider: "local" },
    },
    current_thought_deployment: {
      source: "global",
      configured_target_id: null,
      target: {
        id: "this_machine",
        name: "This device",
        kind: "this_device",
        boundary: "same_device",
        engine: "llama.cpp",
        model: "",
        context_limit: 8192,
      },
      readiness: {
        state: "unavailable",
        available: false,
        reason: "No executable model is configured.",
      },
      execution_support: {
        state: "unavailable",
        executable: false,
        reason: "No executable model is configured.",
      },
      execution_revision: {
        schema_version: 1,
        id: null,
        destination_id: "this_machine",
        kind: "this_device",
        engine: "llama.cpp",
        model: "",
        boundary: "same_device",
        has_local_artifact: false,
        requires_secret: false,
        artifact_id: null,
        runtime_id: null,
        context_ceiling: 8192,
      },
    },
    artifact_detection: {
      state: "unavailable",
      reason: "Model folders could not be inspected.",
    },
    detected_local_artifacts: [],
    installed_model_artifacts: [],
    acquisitions: [],
    presets: [
      hosted("deep-first", "deep"),
      hosted("balanced-second", "balanced"),
    ],
    limitations: [
      {
        code: "local_scan",
        title: "Local scan unavailable",
        detail: "The hub could not inspect local model folders.",
        repair: {
          action: "none",
          label: "Try again after the folders are available",
        },
      },
    ],
    ...overrides,
  };
}

const defaults = {
  loading: false,
  error: "",
  targets: [],
  targetsLoading: false,
  busyPresetId: null,
  status: "",
  onRetry: vi.fn(),
};

describe("InferenceCapabilityPanel", () => {
  it("selects the current preset or the first server row, never a browser recommendation", async () => {
    const onUseHosted = vi.fn(async () => true);
    const { rerender } = render(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup()}
        onUseHosted={onUseHosted}
      />,
    );
    await waitFor(() =>
      expect(screen.getByRole("radio", { name: /deep choice/i })).toBeChecked(),
    );
    expect(
      screen.getByRole("radio", { name: /balanced choice/i }),
    ).not.toBeChecked();

    rerender(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup({
          current_routes: {
            authority: "config",
            thoughts: {
              target_id: "target-balanced-second",
              inherits_this_device: false,
              revision: "route-2",
            },
            dictation: { target_id: null, backend: "llama_cpp" },
            meetings: { target_id: null, provider: "local" },
          },
        })}
        onUseHosted={onUseHosted}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByRole("radio", { name: /balanced choice/i }),
      ).toBeChecked(),
    );
    expect(document.body.textContent).not.toMatch(
      /recommended|ready to configure/i,
    );
  });

  it("distinguishes unknown inspection from a proven empty scan", () => {
    const onUseHosted = vi.fn(async () => true);
    const { rerender } = render(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup()}
        onUseHosted={onUseHosted}
      />,
    );
    expect(
      screen.getByText("Local AI inspection unavailable"),
    ).toBeInTheDocument();
    expect(screen.queryByText("No local AI detected")).toBeNull();

    rerender(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup({
          artifact_detection: { state: "complete", reason: null },
        })}
        onUseHosted={onUseHosted}
      />,
    );
    expect(screen.getByText("No local AI detected")).toBeInTheDocument();
  });

  it("uses executable support, never configured-path readiness, for Thought availability", () => {
    render(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup({
          current_thought_deployment: {
            ...setup().current_thought_deployment,
            readiness: { state: "ready", available: true, reason: null },
            execution_support: {
              state: "unsupported",
              executable: false,
              reason: "llama.cpp is not available.",
            },
          },
        })}
        onUseHosted={vi.fn(async () => true)}
      />,
    );
    expect(screen.getByText("llama.cpp is not available.")).toBeInTheDocument();
    expect(screen.queryByText("Available for Thoughts")).toBeNull();
  });

  it("renders a signed local preset with one explicit download action", async () => {
    const local = {
      kind: "local_artifact_preset" as const,
      id: "local-q",
      experience: "quick" as const,
      label: "Local Q",
      runtime_id: "llama.cpp",
      runtime_min_revision: "0.3.34",
      format: "gguf" as const,
      boundary: "same_device" as const,
      context: { recommended_tokens: 8192 as const, ceiling_tokens: 8192 },
      source: {
        repository: "org/repo",
        revision: "a".repeat(40),
        manifest_sha256: `sha256:${"b".repeat(64)}`,
        filename: "model.gguf",
        file_sha256: `sha256:${"d".repeat(64)}`,
        download_bytes: 42,
        installed_bytes: 42,
        peak_free_bytes: 84,
        license: "Apache-2.0",
      },
      platforms: ["linux-x86_64"],
      applicability: { state: "applicable" as const, reason: null },
    };
    const download = vi.fn(async () => undefined);
    render(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup({ presets: [local] })}
        onUseHosted={vi.fn(async () => true)}
        onDownloadLocal={download}
      />,
    );
    expect(screen.getAllByText("Local Q")).toHaveLength(2);
    expect(screen.getByText(/runs only on this device/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /download & use quick/i }));
    await waitFor(() => expect(download).toHaveBeenCalledWith(local));
  });

  it("clears a secret only after confirmed success and retains it on failure", async () => {
    const failed = vi.fn(async () => false);
    const { rerender } = render(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup()}
        onUseHosted={failed}
      />,
    );
    const key = screen.getByLabelText("OpenRouter key");
    fireEvent.change(key, { target: { value: "sentinel-secret" } });
    fireEvent.click(screen.getByRole("button", { name: "ADD & USE DEEP" }));
    await waitFor(() => expect(failed).toHaveBeenCalled());
    expect(key).toHaveValue("sentinel-secret");

    const succeeded = vi.fn(async () => true);
    rerender(
      <InferenceCapabilityPanel
        {...defaults}
        setup={setup()}
        onUseHosted={succeeded}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "ADD & USE DEEP" }));
    await waitFor(() => expect(key).toHaveValue(""));
  });
});
