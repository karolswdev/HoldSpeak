/*
 * HoldSpeak Companion — background script.
 *
 * Listens for tab activation + URL changes, builds a minimal event,
 * posts it to the local HoldSpeak runtime over loopback. The
 * extension never reads page bodies, cookies, form data, or
 * credentials — those would be hard-rejected by the receiving
 * parser anyway (see holdspeak/activity_extension.py:FORBIDDEN_FIELDS).
 *
 * Configuration: the runtime URL is read from `browser.storage.local`
 * key `runtimeUrl`. Set it via the options page (defaults to
 * http://127.0.0.1:64524 — your runtime port may differ; check
 * the holdspeak runtime startup log).
 */

const DEFAULT_RUNTIME_URL = "http://127.0.0.1:64524";

async function getRuntimeUrl() {
  const stored = await browser.storage.local.get("runtimeUrl");
  return (stored && stored.runtimeUrl) || DEFAULT_RUNTIME_URL;
}

function isPostableUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

async function postEvents(events) {
  if (!events.length) return;
  const runtimeUrl = await getRuntimeUrl();
  try {
    const response = await fetch(`${runtimeUrl.replace(/\/$/, "")}/api/activity/extension/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events }),
    });
    if (!response.ok) {
      console.warn("[holdspeak-companion] runtime rejected batch", response.status);
    }
  } catch (error) {
    // Loopback runtime is local and may not be running; failure
    // is silent on purpose.
    console.debug("[holdspeak-companion] runtime not reachable", error);
  }
}

function buildEvent(tab) {
  if (!tab || !tab.url || !isPostableUrl(tab.url)) return null;
  if (tab.incognito) return null;
  return {
    url: tab.url,
    title: tab.title || "",
    visited_at: new Date().toISOString(),
    tab_id: tab.id,
    window_id: tab.windowId,
  };
}

browser.tabs.onActivated.addListener(async ({ tabId }) => {
  try {
    const tab = await browser.tabs.get(tabId);
    const event = buildEvent(tab);
    if (event) postEvents([event]);
  } catch {
    /* tab may have been closed before lookup */
  }
});

browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status !== "complete") return;
  const event = buildEvent(tab);
  if (event) postEvents([event]);
});
