const TOKEN_KEY = "hs.web.token";

let sessionToken = "";

/** PHILO-17 wayin: the token lives per hub origin in localStorage, so a new
 * tab, a bookmark, or a browser restart stays signed in to the same hub. */
function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function read(): string {
  try {
    return storage()?.getItem(TOKEN_KEY)?.trim() ?? "";
  } catch {
    return "";
  }
}

function write(token: string): void {
  try {
    storage()?.setItem(TOKEN_KEY, token);
  } catch {
    /* private mode: the token stays in memory for this page */
  }
}

/** The older tab-scoped copy (before PHILO-17): move it once, then drop it. */
function migrateSessionToken(): string {
  try {
    const old = window.sessionStorage.getItem(TOKEN_KEY)?.trim() ?? "";
    if (old) window.sessionStorage.removeItem(TOKEN_KEY);
    return old;
  } catch {
    return "";
  }
}

/** Capture a tokenized arrival once, keep it for this hub, and scrub the URL. */
export function bootstrapAuth(location = window.location): string {
  const url = new URL(location.href);
  const queryToken = url.searchParams.get("token")?.trim() ?? "";
  if (queryToken) {
    sessionToken = queryToken;
    write(queryToken);
    migrateSessionToken();
    url.searchParams.delete("token");
    window.history.replaceState(
      window.history.state,
      "",
      `${url.pathname}${url.search}${url.hash}`,
    );
  } else {
    sessionToken = read();
    if (!sessionToken) {
      sessionToken = migrateSessionToken();
      if (sessionToken) write(sessionToken);
    }
  }
  return sessionToken;
}

/** The stored token wins over this page's copy: another tab may have stored
 * a newer one. The copy serves only when storage is closed (private mode). */
export function authToken(): string {
  return read() || sessionToken;
}

/** The hub refused this token (wrong or rotated): forget it, so the page asks
 * for the token URL again. This page's copy and the stored token are each
 * cleared only when they ARE the refused one: an old tab never erases a newer
 * token that another tab stored. */
export function forgetAuthToken(refused: string): void {
  if (!refused) return;
  if (sessionToken === refused) sessionToken = "";
  if (read() !== refused) return;
  try {
    storage()?.removeItem(TOKEN_KEY);
  } catch {
    /* nothing stored */
  }
}

export function authenticatedHeaders(initial?: HeadersInit): Headers {
  const headers = new Headers(initial);
  const token = authToken();
  if (token && !headers.has("X-HoldSpeak-Token")) {
    headers.set("X-HoldSpeak-Token", token);
  }
  return headers;
}

export function websocketUrl(path = "/ws"): string {
  const url = new URL(path, window.location.href);
  url.protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return url.toString();
}

/** Browser WebSockets cannot set Authorization headers. Offer the credential
 * as a subprotocol header so it never enters the URL, history, or access logs. */
export function websocketProtocols(): string[] {
  const token = authToken();
  if (!token) return ["holdspeak.v1"];
  const bytes = new TextEncoder().encode(token);
  let binary = "";
  bytes.forEach((byte) => { binary += String.fromCharCode(byte); });
  const encoded = window.btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replace(/=+$/, "");
  return ["holdspeak.v1", `holdspeak.auth.v1.${encoded}`];
}
