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
    schema_version: 1;
    id: string | null;
    destination_id: string;
    kind: string;
    engine: string;
    model: string;
    boundary: string;
    has_local_artifact: boolean;
    requires_secret: boolean;
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
  format: "gguf" | "mlx_safetensors";
  boundary: "same_device";
  source: {
    repository: string;
    revision: string;
    manifest_sha256: string;
    download_bytes: number;
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
  preset_catalog: { schema_version: 1; sha256: string };
  hardware: InferenceSetupHardware;
  runtimes: InferenceSetupRuntime[];
  current_routes: {
    authority: "config";
    thoughts: { target_id: string | null; inherits_this_device: boolean };
    dictation: { target_id: string | null; backend: string };
    meetings: { target_id: string | null; provider: string };
  };
  current_thought_deployment: InferenceSetupDeployment;
  artifact_detection: {
    state: "complete" | "partial" | "unavailable";
    reason: string | null;
  };
  detected_local_artifacts: InferenceSetupArtifact[];
  presets: InferencePreset[];
  limitations: InferenceSetupLimitation[];
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
