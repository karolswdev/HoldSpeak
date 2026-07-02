// HS-75-02: the dictation preview card's driver (the QueueHud idiom —
// markup in PreviewCard.astro, behavior here, frames from the ONE bus).
//
// A `dictation_preview` frame reveals the card with the armed text; Type it
// consumes the server-minted token through the real route (the runtime
// types only its own stored text); Discard burns it. One card at a time —
// a newer frame replaces the older (the hub already enforces one active
// preview). Keyboard-first: the primary button takes focus on arrival;
// Escape while the card holds focus discards.
import { subscribe } from "./runtime-bus.js";

export function mountPreviewCard() {
  const root = document.querySelector("[data-preview-card]");
  if (!root) return;
  const textEl = root.querySelector("[data-pc-text]");
  const errEl = root.querySelector("[data-pc-error]");
  const typeBtn = root.querySelector("[data-pc-type]");
  const discardBtn = root.querySelector("[data-pc-discard]");
  let token = null;
  let busy = false;

  function hide() {
    token = null;
    root.hidden = true;
    errEl.hidden = true;
    errEl.textContent = "";
  }

  function fail(message) {
    errEl.textContent = message;
    errEl.hidden = false;
  }

  async function act(path) {
    if (!token || busy) return;
    busy = true;
    try {
      const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.ok && body.success) {
        hide();
      } else if (res.status === 404) {
        // The token was consumed elsewhere (another surface won) — settle.
        hide();
      } else {
        fail(String(body.error || `HTTP ${res.status}`));
      }
    } catch (e) {
      fail(String(e && e.message ? e.message : e));
    } finally {
      busy = false;
    }
  }

  typeBtn.addEventListener("click", () => act("/api/dictation/preview/type"));
  discardBtn.addEventListener("click", () => act("/api/dictation/preview/discard"));
  root.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      e.stopPropagation();
      act("/api/dictation/preview/discard");
    }
  });

  subscribe("dictation_preview", (data) => {
    if (!data || !data.token) return;
    token = String(data.token);
    textEl.textContent = String(data.text || "");
    errEl.hidden = true;
    root.hidden = false;
    typeBtn.focus();
  });
}
