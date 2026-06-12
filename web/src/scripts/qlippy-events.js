// HS-56-03: the actuator cards — Qlippy's marquee moment (absorbs backlog G).
//
// Consumes the broadcasts presence-app.js re-dispatches as `hs-broadcast`
// DOM events and presents them through the HS-56-02 card shell. The Approve
// and Decline buttons send the IDENTICAL request the dashboard's proposal
// panels send (POST {decision} to the existing decision route): approving
// records the decision and an audit entry — it performs NO side effect;
// execution stays the guarded executor's separate job. Proposed cards are
// sticky (they never auto-expire and never auto-decide); dismissing is
// always safe — the proposal still lives in the dashboard.
//
// The G panel: every actionable card answers, in plain language, what data
// is used (the human preview — the machine payload is never on the wire),
// whether anything leaves this machine (the named target), and what control
// the user has (the buttons + dismiss).

function presentCard(card) {
  if (window.qlippyCard) window.qlippyCard.present(card);
}

async function decideProposal(data, decision) {
  const response = await fetch(
    `/api/meetings/${data.meeting_id}/proposals/${data.id}/decision`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    }
  );
  const body = await response.json().catch(() => ({}));
  if (!response.ok || body.success === false) {
    throw new Error(body.error || `HTTP ${response.status}`);
  }
  return body;
}

// HS-62-01: cards state their egress with the compact badge (the `egress`
// field on presentCard), never a privacy paragraph. Cloud-scoped cards keep
// the target name on the badge.
function onActuatorProposed(data) {
  if (!data || !data.id || !data.meeting_id) return;
  presentCard({
    key: `proposal:${data.id}`,
    sprite: "alert",
    glyph: "bang",
    headline: "A decision needs you",
    detail:
      `${data.target || "?"} · ${data.action || "?"}` +
      (data.reversible ? " · reversible" : ""),
    preview: data.preview || "",
    egress: { scope: "cloud", label: data.target || undefined },
    sticky: true,
    actions: [
      {
        label: "Approve",
        kind: "primary",
        onClick: () => {
          decideProposal(data, "approved").catch((error) =>
            presentCard({
              sprite: "error",
              glyph: "x",
              headline: "Couldn't record the decision",
              detail: String(error.message || error),
            })
          );
        },
      },
      {
        label: "Decline",
        kind: "danger",
        onClick: () => {
          decideProposal(data, "rejected").catch((error) =>
            presentCard({
              sprite: "error",
              glyph: "x",
              headline: "Couldn't record the decision",
              detail: String(error.message || error),
            })
          );
        },
      },
    ],
  });
}

function onActuatorResult(data) {
  if (!data || !data.status) return;
  const action = data.action || "the action";
  if (data.status === "executed") {
    presentCard({
      sprite: "approve",
      glyph: "check",
      headline: `Done — ${action}`,
      detail: `${data.target || ""} · ${data.preview || ""}`.trim(),
      egress: { scope: "cloud", label: data.target || undefined },
    });
  } else if (data.status === "failed") {
    presentCard({
      sprite: "error",
      glyph: "x",
      headline: "Didn't run",
      detail: String(data.error || "The connector reported a failure."),
      egress: { scope: "local", label: "Nothing sent" },
    });
  } else if (data.status === "rejected") {
    presentCard({
      sprite: "decline",
      glyph: "x",
      headline: "Declined",
      detail: `${action} will not run.`,
    });
  }
}

// HS-56-04: the learning loop, reflected honestly. The backend only emits
// this when a correction was actually taught AND has real Jaccard reach
// (similar > 0) — Qlippy never claims learning that did not happen.
function onLearningEvent(data) {
  if (!data || !data.similar) return;
  const n = Number(data.similar) || 0;
  presentCard({
    sprite: "learned",
    glyph: "lightbulb",
    headline: "Learned from you",
    detail:
      `Applied "${data.gist || ""}" → ${data.value || ""} — matches ${n} past ` +
      `dictation${n === 1 ? "" : "s"}` +
      (data.enabled ? "." : " (turn on corrections to use it while routing)."),
    egress: { scope: "local" },
    actions: [
      {
        label: "View digest",
        kind: "ghost",
        onClick: () => window.open("/dictation", "_blank"),
      },
    ],
  });
}

// HS-56-04: a wrapped meeting that left open work. The backend stays quiet
// for an empty digest.
function onAftercareReady(data) {
  if (!data || !data.meeting_id) return;
  const open = Number(data.open_total) || 0;
  const top = (data.top_items || [])
    .map((item) => `${item.task}${item.owner ? ` (${item.owner})` : ""}`)
    .join(" · ");
  presentCard({
    sprite: "present-note",
    headline: `Your meeting left ${open} open item${open === 1 ? "" : "s"}`,
    detail: `${data.title || "The meeting"}${top ? ` — ${top}` : ""}`,
    egress: { scope: "local" },
    autoDismissMs: 14000,
    actions: [
      {
        label: "Open aftercare",
        kind: "ghost",
        onClick: () => window.open("/history", "_blank"),
      },
    ],
  });
}

// HS-60: the wake preview — the safety fork made visible. The wake word
// armed, your sentence ran the normal pipeline, and NOTHING was typed:
// this card is the one decisive glance. Type it sends the one-shot token;
// the server types only its own stored preview and burns the token.
function onWakePreview(data) {
  if (!data || !data.token) return;
  presentCard({
    key: `wake:${data.token}`,
    sprite: "alert",
    glyph: "check",
    headline: "Heard you — review before it types",
    detail: data.transcript || "",
    preview: data.text || "",
    egress: { scope: "local", label: "Local · not typed yet" },
    sticky: true,
    actions: [
      {
        label: "Type it",
        kind: "primary",
        onClick: () => {
          fetch("/api/dictation/wake/type", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ token: data.token }),
          })
            .then((r) => r.json())
            .then((body) => {
              if (!body.success) throw new Error(body.error || "failed");
            })
            .catch((error) =>
              presentCard({
                sprite: "error",
                glyph: "x",
                headline: "Couldn't type the preview",
                detail: String(error.message || error),
              })
            );
        },
      },
    ],
  });
}

document.addEventListener("hs-broadcast", (event) => {
  const msg = event.detail;
  if (!msg || !msg.type) return;
  if (msg.type === "actuator_proposed") onActuatorProposed(msg.data);
  if (msg.type === "actuator_result") onActuatorResult(msg.data);
  if (msg.type === "learning_event") onLearningEvent(msg.data);
  if (msg.type === "aftercare_ready") onAftercareReady(msg.data);
  if (msg.type === "wake_preview") onWakePreview(msg.data);
});
