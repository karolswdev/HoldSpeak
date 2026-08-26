import { ApiError, apiFetch, apiRequest, newDeliveryId } from "../../lib/api";

export type ModelLibraryAction =
  | "Download"
  | "Add to library"
  | "Connect"
  | "Add model"
  | "Ready"
  | "Checking"
  | "Try again";

export type ModelLibraryRow = {
  id: string;
  source: string;
  label: string;
  status: string;
  detail: Record<string, unknown>;
  repair: { code: string; label: string } | null;
  /** The service may name one typed repair in addition to the closed base enum. */
  selected_action: ModelLibraryAction | string;
};

export type ModelLibraryProjection = {
  schema: "ModelLibraryProjection@1";
  catalog_revision: number;
  artifact_detection: { state: string };
  rows: ModelLibraryRow[];
};

export type ModelLibraryReceipt = {
  receipt: {
    kind: string;
    message: string;
    assignments_unchanged: true;
  };
  provider?: {
    profile_id: string;
    profile_revision: number;
    binding_id: string;
    binding_revision: number;
    provider_family: string;
    secret: { required: boolean; present: boolean };
  };
};

export type HostedModelDraft = {
  request_id: string;
  profile_id: string;
  expected_profile_revision: number;
  label: string;
  provider_family: "openrouter" | "anthropic";
  model: string;
  requires_key: boolean;
};

export type EndpointDraft = {
  request_id: string;
  profile_id: string;
  expected_profile_revision: number;
  label: string;
  provider_family: "openai_compatible" | "private_endpoint" | "future_backend";
  model: string;
  endpoint: string;
  requires_key: boolean;
};

export function getModelLibrary(signal?: AbortSignal): Promise<ModelLibraryProjection> {
  return apiFetch<ModelLibraryProjection>("/api/inference/model-library", { signal });
}

export function downloadModel(
  catalogId: string,
  catalogRevision: number,
  requestId = newDeliveryId(),
): Promise<ModelLibraryReceipt> {
  return apiFetch<ModelLibraryReceipt>("/api/inference/model-library/download", {
    method: "POST",
    json: { request_id: requestId, catalog_id: catalogId, catalog_revision: catalogRevision },
  });
}

export function addDetectedModel(
  detectedArtifactId: string,
  requestId = newDeliveryId(),
): Promise<ModelLibraryReceipt> {
  return apiFetch<ModelLibraryReceipt>("/api/inference/model-library/add-to-library", {
    method: "POST",
    json: { request_id: requestId, detected_artifact_id: detectedArtifactId },
  });
}

export function connectHostedModel(
  draft: HostedModelDraft,
  secret: string | null,
): Promise<ModelLibraryReceipt> {
  return apiFetch<ModelLibraryReceipt>("/api/inference/model-library/connect-hosted-model", {
    method: "POST",
    json: { draft, secret: secret ? { value: secret } : null },
  });
}

export function defineEndpoint(
  draft: EndpointDraft,
  secret: string | null,
): Promise<ModelLibraryReceipt> {
  return apiFetch<ModelLibraryReceipt>("/api/inference/model-library/define-endpoint", {
    method: "POST",
    json: { draft, secret: secret ? { value: secret } : null },
  });
}

export async function useModelFile(
  file: File,
  requestId = newDeliveryId(),
): Promise<ModelLibraryReceipt> {
  const body = new FormData();
  body.set("request_id", requestId);
  body.set("file", file);
  const response = await apiRequest("/api/inference/model-library/use-model-file", {
    method: "POST",
    headers: { Accept: "application/json" },
    body,
  });
  const payload: unknown = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload && typeof payload === "object" && typeof (payload as { message?: unknown }).message === "string"
      ? (payload as { message: string }).message
      : `HoldSpeak could not complete that request (HTTP ${response.status}).`;
    throw new ApiError(response.status, message, payload);
  }
  return payload as ModelLibraryReceipt;
}
