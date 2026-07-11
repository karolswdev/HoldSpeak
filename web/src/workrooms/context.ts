export const WORKROOM_CONTEXT_VERSION = 1 as const;
export const WORKROOM_QUERY_KEY = "room";

const MAX_ENCODED_CONTEXT = 1400;
const QUALIFIED_REF = /^[a-z][a-z0-9_-]{0,31}:[^\s/?#]{1,240}$/i;
const ACTION = /^[a-z][a-z0-9._-]{0,63}$/;
const CONTENT_KEYS = new Set([
  "body",
  "content",
  "draft",
  "input",
  "prompt",
  "text",
  "transcript",
  "utterance",
]);

export interface WorkroomContext {
  version: number;
  origin: "desk";
  subject_ref?: string;
  action: string;
  draft_ref?: string;
  run_ref?: string;
  return_to: "desk";
  return_ref?: string;
}

export interface WorkroomContextInput {
  action: string;
  subjectRef?: string;
  draftRef?: string;
  runRef?: string;
  returnRef?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function validRef(value: unknown): value is string {
  return typeof value === "string" && QUALIFIED_REF.test(value);
}

/**
 * Decode only identity and orientation. Unknown metadata is ignored for
 * forward compatibility; content-bearing fields are refused explicitly.
 */
export function normalizeWorkroomContext(
  value: unknown,
): WorkroomContext | null {
  if (!isRecord(value)) return null;
  if (Object.keys(value).some((key) => CONTENT_KEYS.has(key.toLowerCase())))
    return null;

  const version = Number(value.version ?? WORKROOM_CONTEXT_VERSION);
  if (!Number.isInteger(version) || version < 1 || version > 999) return null;
  if (value.origin !== "desk" || value.return_to !== "desk") return null;
  if (typeof value.action !== "string" || !ACTION.test(value.action))
    return null;

  for (const key of ["subject_ref", "draft_ref", "run_ref", "return_ref"]) {
    const ref = value[key];
    if (ref !== undefined && !validRef(ref)) return null;
  }

  return {
    version,
    origin: "desk",
    ...(value.subject_ref ? { subject_ref: String(value.subject_ref) } : {}),
    action: value.action,
    ...(value.draft_ref ? { draft_ref: String(value.draft_ref) } : {}),
    ...(value.run_ref ? { run_ref: String(value.run_ref) } : {}),
    return_to: "desk",
    ...(value.return_ref ? { return_ref: String(value.return_ref) } : {}),
  };
}

export function makeWorkroomContext(
  input: WorkroomContextInput,
): WorkroomContext {
  const context = normalizeWorkroomContext({
    version: WORKROOM_CONTEXT_VERSION,
    origin: "desk",
    subject_ref: input.subjectRef,
    action: input.action,
    draft_ref: input.draftRef,
    run_ref: input.runRef,
    return_to: "desk",
    return_ref: input.returnRef ?? input.subjectRef,
  });
  if (!context) throw new Error("Invalid workroom identity context");
  return context;
}

function encodeBase64Url(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary)
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

function decodeBase64Url(value: string): string {
  const base64 = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = base64.padEnd(Math.ceil(base64.length / 4) * 4, "=");
  const binary = atob(padded);
  return new TextDecoder().decode(
    Uint8Array.from(binary, (character) => character.charCodeAt(0)),
  );
}

export function encodeWorkroomContext(context: WorkroomContext): string {
  const normalized = normalizeWorkroomContext(context);
  if (!normalized) throw new Error("Invalid workroom identity context");
  const encoded = encodeBase64Url(JSON.stringify(normalized));
  if (encoded.length > MAX_ENCODED_CONTEXT)
    throw new Error("Workroom identity context is too large");
  return encoded;
}

export function decodeWorkroomContext(search: string): WorkroomContext | null {
  const params = new URLSearchParams(search);
  if ([...params.keys()].some((key) => CONTENT_KEYS.has(key.toLowerCase())))
    return null;
  const encoded = params.get(WORKROOM_QUERY_KEY);
  if (!encoded || encoded.length > MAX_ENCODED_CONTEXT) return null;
  if (!/^[A-Za-z0-9_-]+$/.test(encoded)) return null;
  try {
    return normalizeWorkroomContext(JSON.parse(decodeBase64Url(encoded)));
  } catch {
    return null;
  }
}

export function workroomHref(
  path: string,
  input: WorkroomContextInput | WorkroomContext,
): string {
  if (!path.startsWith("/") || path.startsWith("//"))
    throw new Error("Workrooms require an internal route");
  const url = new URL(path, "https://holdspeak.invalid");
  if (url.origin !== "https://holdspeak.invalid")
    throw new Error("Workrooms require an internal route");
  if (
    [...url.searchParams.keys()].some((key) =>
      CONTENT_KEYS.has(key.toLowerCase()),
    )
  )
    throw new Error("Workroom URLs cannot carry authored content");
  const context = "origin" in input ? input : makeWorkroomContext(input);
  url.searchParams.set(WORKROOM_QUERY_KEY, encodeWorkroomContext(context));
  return `${url.pathname}${url.search}${url.hash}`;
}

export function workroomReturnHref(context: WorkroomContext | null): string {
  const ref = context?.return_ref ?? context?.subject_ref;
  return ref ? `/?open=${encodeURIComponent(ref)}` : "/";
}

export function workroomSubjectId(
  context: WorkroomContext | null,
  kind?: string,
): string | null {
  const ref = context?.subject_ref;
  if (!ref) return null;
  const split = ref.indexOf(":");
  if (split < 1) return null;
  if (kind && ref.slice(0, split) !== kind) return null;
  return ref.slice(split + 1);
}

export function workroomActionLabel(action: string): string {
  return action
    .replace(/[._-]+/g, " ")
    .replace(/^\w/, (letter) => letter.toUpperCase());
}
