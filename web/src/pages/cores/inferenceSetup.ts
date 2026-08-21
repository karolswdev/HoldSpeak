import { apiFetch } from "../../lib/api";

export type InferenceFactState = "available" | "partial" | "unavailable";

export interface InferenceSetupHardware {
  capability: {
    system: string;
    architecture: string;
    apple_silicon: boolean;
    total_memory_bytes: number | null;
    logical_cpu_count: number | null;
    unified_memory: boolean | null;
    accelerators: string[];
    sha256: string;
  };
  observation: {
    available_memory_bytes: number | null;
    storage_available_bytes: number | null;
    sha256: string;
  };
  detection: {
    state: InferenceFactState;
    reason: string | null;
  };
}

export interface InferenceSetupRuntime {
  id: string;
  revision: string;
  formats: string[];
  availability: { state: "available" | "unavailable"; reason: string | null };
  thought_support: {
    state: "supported" | "unsupported" | "unavailable";
    reason: string | null;
  };
}

export interface InferenceSetupTarget {
  id: string;
  name: string;
  kind: string;
  boundary: string;
  engine: string;
  model: string;
  context_limit: number;
}

export interface InferenceSetupDeployment {
  source: "config" | "global";
  configured_target_id: string | null;
  target: InferenceSetupTarget;
  readiness: {
    state:
      | "ready"
      | "unavailable"
      | "needs_key"
      | "unsupported"
      | "offline"
      | "stale_manifest";
    available: boolean;
    reason: string | null;
  };
  execution_support: {
    state: "executable" | "unavailable" | "unsupported";
    executable: boolean;
    reason: string | null;
  };
  execution_revision: {
    schema_version: 1 | 2;
    id: string | null;
    destination_id: string;
    kind: string;
    engine: string;
    model: string;
    boundary: string;
    has_local_artifact: boolean;
    requires_secret: boolean;
    artifact_id: string | null;
    runtime_id: string | null;
    context_ceiling: number;
  } | null;
}

export interface InferenceSetupArtifact {
  id: string;
  label: string;
  format: "gguf" | "mlx_safetensors";
  configured_for_thoughts: boolean;
  thought_support: {
    state: "current_v1" | "unsupported" | "candidate";
    reason: string | null;
  };
}

export interface HostedInferencePreset {
  kind: "hosted_profile_preset";
  id: string;
  experience: "quick" | "balanced" | "deep";
  label: string;
  provider_adapter: "openai_compatible";
  model_id: string;
  boundary: "external_service";
  secret_requirement: "profile_key";
  context: { support: "bounded"; working_ceiling_tokens: number };
  applicability: { state: "applicable"; reason: null };
  existing_profile: {
    target_id: string;
    name: string;
    kind: "openAICompatible";
    base_url: string;
    model: string;
    context_limit: number;
    requires_key: true;
  };
}

export interface LocalInferencePreset {
  kind: "local_artifact_preset";
  id: string;
  experience: "quick" | "balanced" | "deep";
  label: string;
  runtime_id: string;
  runtime_min_revision: string;
  format: "gguf" | "mlx_safetensors";
  boundary: "same_device";
  context: { recommended_tokens: 8192 | 16384 | 32768; ceiling_tokens: number };
  source: {
    repository: string;
    revision: string;
    manifest_sha256: string;
    filename: string;
    file_sha256: string;
    download_bytes: number;
    installed_bytes: number;
    peak_free_bytes: number;
    license: string;
  };
  platforms: string[];
  applicability: {
    state: "applicable" | "unavailable";
    reason: string | null;
  };
}

export type InferencePreset = HostedInferencePreset | LocalInferencePreset;

export interface InferenceSetupLimitation {
  code: string;
  title: string;
  detail: string;
  repair: { action: "open_models" | "none"; label: string };
}

export interface InferenceSetup {
  schema_version: 1;
  observed_at: string;
  preset_catalog: {
    schema_version: 1;
    catalog_revision: number;
    generated_at: string;
    expires_at: string;
    signing_key_id: string;
    sha256: string;
  };
  hardware: InferenceSetupHardware;
  runtimes: InferenceSetupRuntime[];
  current_routes: {
    authority: "config";
    thoughts: {
      target_id: string | null;
      inherits_this_device: boolean;
      revision: string;
    };
    dictation: { target_id: string | null; backend: string };
    meetings: { target_id: string | null; provider: string };
  };
  current_thought_deployment: InferenceSetupDeployment;
  artifact_detection: {
    state: "complete" | "partial" | "unavailable";
    reason: string | null;
  };
  detected_local_artifacts: InferenceSetupArtifact[];
  installed_model_artifacts: Array<{
    id: string;
    format: "gguf" | "mlx_safetensors";
    source_repository: string;
    source_revision: string;
    installed_bytes: number;
    state: "verified";
    verified_at: string;
  }>;
  acquisitions: InferenceAcquisition[];
  presets: InferencePreset[];
  limitations: InferenceSetupLimitation[];
}

export interface InferenceAcquisition {
  id: string;
  preset_id: string;
  state:
    | "requested"
    | "resolving_source"
    | "downloading"
    | "verifying"
    | "installing"
    | "ready"
    | "cancelled"
    | "failed"
    | "indeterminate";
  verified_bytes: number;
  transport_bytes: number;
  bytes_total: number;
  artifact_id: string | null;
  activation_state: "pending" | "in_use" | "failed" | "not_requested";
  error: { code: string; message: string } | null;
  resumable: boolean;
  can_cancel: boolean;
  revision: number;
  created_at: string;
  updated_at: string;
}

export async function downloadAndUseLocalPreset(
  setup: InferenceSetup,
  preset: LocalInferencePreset,
  requestId: string,
): Promise<InferenceAcquisition> {
  const result = await apiFetch<{
    acquisition: InferenceAcquisition;
    setup: InferenceSetup;
  }>("/api/inference/acquisitions/download-and-use", {
    method: "POST",
    json: {
      request_id: requestId,
      preset_id: preset.id,
      catalog_revision: setup.preset_catalog.catalog_revision,
      context_choice: preset.context.recommended_tokens,
      expected_route_revision: setup.current_routes.thoughts.revision,
    },
  });
  return result.acquisition;
}

export async function getInferenceAcquisition(
  id: string,
): Promise<InferenceAcquisition> {
  const result = await apiFetch<{ acquisition: InferenceAcquisition }>(
    `/api/inference/acquisitions/${encodeURIComponent(id)}`,
  );
  return result.acquisition;
}

export async function cancelInferenceAcquisition(
  acquisition: InferenceAcquisition,
  requestId: string,
): Promise<InferenceAcquisition> {
  const result = await apiFetch<{ acquisition: InferenceAcquisition }>(
    `/api/inference/acquisitions/${encodeURIComponent(acquisition.id)}/cancel`,
    {
      method: "POST",
      json: {
        request_id: requestId,
        expected_revision: acquisition.revision,
      },
    },
  );
  return result.acquisition;
}

export async function getInferenceSetup(
  signal?: AbortSignal,
): Promise<InferenceSetup> {
  const response = await apiFetch<{ setup: InferenceSetup }>(
    "/api/inference/setup",
    { signal },
  );
  return response.setup;
}
