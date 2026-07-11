const TARGET_LABELS = {
  cli_python: "HoldSpeak Python CLI",
  web_react: "React Web Desk",
  ios_flagship_swift: "Flagship Swift app",
  ios_companion_swift: "Companion Swift app",
  ios_classic_swift: "Classic/demo Swift app",
  ios_unclassified_swift: "Unclassified Swift build (diagnostic only)",
  legacy_unqualified: "Legacy unqualified evidence (invalid)",
};

const FORM_FACTOR_LABELS = {
  local_shell: "local terminal",
  desktop: "desktop browser",
  desktop_browser: "desktop browser",
  ipad_browser: "physical iPad browser (web, not native)",
  iphone_browser: "physical iPhone browser (web, not native)",
  tablet_browser: "tablet browser (web, not native)",
  tablet_viewport: "desktop tablet viewport (web simulation, not native)",
  phone_viewport: "phone viewport in a browser",
  ipad: "iPad",
  iphone: "iPhone",
};

export function targetLabel(target) {
  return TARGET_LABELS[target] || String(target || "unknown implementation").replaceAll("_", " ");
}

export function formFactorLabel(formFactor) {
  return FORM_FACTOR_LABELS[formFactor] || String(formFactor || "unknown form factor").replaceAll("_", " ");
}

export function isWebSlot(slot) {
  return slot?.target === "web_react" && slot?.native !== true;
}

export function slotLabel(slot) {
  const supplied = slot?.label || formFactorLabel(slot?.form_factor);
  if (isWebSlot(slot)) return `WEB · React · ${supplied}`;
  if (slot?.native) return `NATIVE · ${supplied}`;
  return `LOCAL · ${supplied}`;
}

export function matchingDeviceSession(slot, sessions = []) {
  if (!slot?.native) return null;
  return sessions.find((session) =>
    (session.target || session.execution_target) === slot.target
      && session.form_factor === slot.form_factor
      && (session.pairing_verified === true || session.pairing_verified === 1)
  ) || null;
}
