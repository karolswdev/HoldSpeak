import { authenticatedHeaders, forgetAuthToken } from "./auth";

export type JsonRecord = Record<string, unknown>;

/** One stable client claim per committed delivery. */
export function newDeliveryId(): string {
  const entropy =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2);
  return `speak:${Date.now()}-${entropy}`;
}

export class ApiError extends Error {
  readonly status: number;
  readonly payload: unknown;

  constructor(status: number, message: string, payload: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

/** Authenticated low-level request for modules that must inspect headers/status. */
export async function apiRequest(
  input: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = authenticatedHeaders(init.headers);
  const response = await fetch(input, { ...init, headers });
  // PHILO-17 wayin: a 401 means the hub knows no owner for this token (none,
  // wrong, or rotated). Forget it so the next page load does not reuse it.
  if (response.status === 401) forgetAuthToken(headers.get("X-HoldSpeak-Token") ?? "");
  return response;
}

/** The one sentence a browser without the hub token sees (PHILO-17 wayin). */
export const SIGN_IN_SENTENCE =
  'To open the desk, use the address that "holdspeak web" prints on your Mac.';

function messageFor(payload: unknown, status: number): string {
  if (status === 401) return SIGN_IN_SENTENCE;
  if (payload && typeof payload === "object") {
    const row = payload as JsonRecord;
    for (const key of ["error", "detail", "message"]) {
      if (typeof row[key] === "string" && row[key]) return row[key];
    }
  }
  return `HoldSpeak could not complete that request (HTTP ${status}).`;
}

export async function apiFetch<T = JsonRecord>(
  input: string,
  init: RequestInit & { json?: unknown } = {},
): Promise<T> {
  const { json, ...request } = init;
  const headers = authenticatedHeaders(request.headers);
  headers.set("Accept", "application/json");
  if (json !== undefined) headers.set("Content-Type", "application/json");
  const response = await apiRequest(input, {
    ...request,
    headers,
    body: json === undefined ? request.body : JSON.stringify(json),
  });
  const contentType =
    response.headers?.get?.("content-type") ?? "application/json";
  const payload: unknown = contentType.includes("json")
    ? await response.json().catch(() => ({}))
    : await response.text().catch(() => "");
  if (!response.ok)
    throw new ApiError(
      response.status,
      messageFor(payload, response.status),
      payload,
    );
  return payload as T;
}

export async function apiBlob(input: string): Promise<Blob> {
  const response = await apiRequest(input, { headers: { Accept: "*/*" } });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      messageFor(payload, response.status),
      payload,
    );
  }
  return response.blob();
}

export function readableError(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Request failed. Retry the action.";
}
