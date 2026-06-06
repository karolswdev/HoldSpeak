// HS-42-05: the trust/privacy view-model.
//
// Pure mapping from the `trust` (+ `presence`) block of GET /api/setup/status to
// the ambient shell chip posture and the full Trust & Privacy panel rows. Kept
// pure + exported so it's unit-testable (Node harness) independent of the DOM.

function _isLoopback(bind) {
  return !bind || bind === "127.0.0.1" || bind === "localhost" || bind === "::1";
}

// The single highest-priority posture for the ambient chip.
export function trustPosture(trust) {
  const t = trust || {};
  if (!_isLoopback(t.web_bind) && !t.auth_token_set) {
    return {
      id: "attention",
      label: "Needs attention",
      tone: "danger",
      detail: "The web runtime is reachable off-loopback without an auth token.",
    };
  }
  if (t.actuators_enabled) {
    return {
      id: "writes",
      label: "Writes need approval",
      tone: "warn",
      detail: "Actuators are on — external writes still require your per-action approval.",
    };
  }
  if (t.transcript_egress && t.transcript_egress !== "none") {
    return {
      id: "endpoint",
      label: "Configured endpoint",
      tone: "info",
      detail: "A transcript can be sent to a configured endpoint.",
    };
  }
  return {
    id: "local",
    label: "Local only",
    tone: "local",
    detail: "Everything stays on this machine.",
  };
}

// The full panel breakdown — plain-language rows answering "what can leave?".
export function trustRows(trust, presence) {
  const t = trust || {};
  const p = presence || {};
  const loopback = _isLoopback(t.web_bind);
  const endpoints = t.configured_endpoints || [];
  const egress = {
    none: "Local only — transcripts never leave this machine",
    configured: "A configured cloud endpoint can receive transcripts",
    possible: "Cloud-capable — may fall back to a cloud endpoint",
  }[t.transcript_egress] || "Local only";

  return [
    {
      label: "Web runtime",
      value: loopback ? `Loopback (${t.web_bind || "127.0.0.1"})` : `Bound to ${t.web_bind}`,
      tone: loopback ? "ok" : (t.auth_token_set ? "warn" : "danger"),
      meta: loopback
        ? "Only reachable from this machine"
        : (t.auth_token_set ? "Off-loopback, but auth-token protected" : "Off-loopback with no auth token"),
    },
    {
      label: "Transcript egress",
      value: egress,
      tone: t.transcript_egress === "none" ? "ok" : "warn",
      meta: endpoints.length ? endpoints[0] : "No endpoint configured",
    },
    {
      label: "Actuators (external writes)",
      value: t.actuators_enabled ? "Enabled — approval-gated" : "Disabled",
      tone: t.actuators_enabled ? "warn" : "ok",
      meta: t.actuators_enabled
        ? "Nothing runs without your explicit per-action approval"
        : "No external side effects",
    },
    {
      label: "Webhook hosts",
      value: (t.webhook_allowed_hosts && t.webhook_allowed_hosts.length)
        ? t.webhook_allowed_hosts.join(", ")
        : "None allow-listed",
      tone: (t.webhook_allowed_hosts && t.webhook_allowed_hosts.length) ? "warn" : "ok",
      meta: "Webhook connectors post only to allow-listed hosts",
    },
    {
      label: "Desktop presence",
      value: p.enabled ? `On · ${p.tier}` : (p.available ? `Available · ${p.tier} (off)` : "Not available"),
      tone: "neutral",
      meta: "An ambient status surface — never reads or sends your text",
    },
  ];
}
