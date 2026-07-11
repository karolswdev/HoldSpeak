const TOKEN_KEY = "hs.web.token";

let sessionToken = "";

function storage(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

/** Capture a tokenized arrival once, retain it for this tab, and scrub the URL. */
export function bootstrapAuth(location = window.location): string {
  const url = new URL(location.href);
  const queryToken = url.searchParams.get("token")?.trim() ?? "";
  if (queryToken) {
    sessionToken = queryToken;
    storage()?.setItem(TOKEN_KEY, queryToken);
    url.searchParams.delete("token");
    window.history.replaceState(
      window.history.state,
      "",
      `${url.pathname}${url.search}${url.hash}`,
    );
  } else {
    sessionToken = storage()?.getItem(TOKEN_KEY)?.trim() ?? "";
  }
  return sessionToken;
}

export function authToken(): string {
  return sessionToken || storage()?.getItem(TOKEN_KEY)?.trim() || "";
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
  const token = authToken();
  if (token) url.searchParams.set("token", token);
  return url.toString();
}
