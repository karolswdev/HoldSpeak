// Settings navigation: the legacy scope contract, the section aliases and
// the row anchors a scope's focus names. Moved out of SettingsCore.tsx.
import {
  MODULE_ALIASES,
  PREF_MODULES,
  SETTINGS_SECTIONS,
  type SettingsSectionId,
} from "../settingsPrefs";

/* ── HS-172: egress helper (shared) ── */
// intelHostLabel / intelHostScope collapsed into egressFor (desk/surface/egress.ts).

export const SECTION_ALIASES: Record<string, SettingsSectionId> = {
  voice: "speak",
  hotkey: "speak",
  transcription: "speak",
  "voice-typing": "speak",
  "wake-word": "speak",
  meetings: "meetings",
  calendar: "accounts",
  rhythm: "notices",
  cadence: "notices",
  // PG-DIRECTION DIR6: the section reads Reach; its anchor id stays notices.
  reach: "notices",
  telegram: "notices",
  integrations: "accounts",
  accounts: "accounts",
  people: "you",
  owner: "you",
  agents: "agents",
  sounds: "desk",
  appearance: "desk",
  presence: "desk",
  wallpaper: "desk",
  desk: "desk",
  system: "this-mac",
  devices: "this-mac",
  models: "this-mac",
  assignments: "this-mac",
  delivery: "this-mac",
};
const LEGACY_FOCUS: Record<string, string> = {
  models: "engines",
  delivery: "engines",
  assignments: "engines",
  integrations: "connections",
  calendar: "calendar",
  wallpaper: "wallpaper",
  people: "owner-name",
  system: "device-name",
};
export const SETTINGS_FOCUS_PATHS: Record<string, string> = {
  "owner-name": "owner.name",
  "owner-aliases": "owner.aliases",
  "push-to-talk": "hotkey",
  language: "model.language",
  "preview-before-type": "dictation.preview_before_type",
  "voice-commands": "dictation.macros.enabled",
  "wake-word": "wake_word.enabled",
  "spoken-symbols": "dictation.spoken_symbols",
  "make-summary": "meeting.intelligence_auto",
  "record-by-itself": "meeting.auto_record",
  microphone: "meeting.mic_device",
  export: "meeting.auto_export",
  "quiet-hours": "heartbeat.quiet_hours",
  notify: "heartbeat.notify",
  "daily-brief": "cadence.brief_enabled",
  "max-nudges": "cadence.max_nudges_per_day",
  "desk-sounds": "ui.desk_sounds",
  motion: "motion",
  presence: "presence.enabled",
  "device-name": "mesh.device_name",
  "people-access": "people.access",
};

const SETTINGS_WINGS = [
  { id: "settings", label: "Settings" },
  { id: "models", label: "Engines" },
  { id: "integrations", label: "Accounts" },
];


/** Legacy scope contract retained for callers and old saved desks. The page
 * converts it to a section with `settingsPageScope` below. */
export function settingsScope(scope?: string): { module: string | null; focus?: string } {
  const [head, ...tail] = (scope ?? "").split("::");
  if (!head) return { module: null };
  if (head.startsWith("integration:")) {
    return { module: "integrations", focus: [head.slice("integration:".length), ...tail].filter(Boolean).join("::") };
  }
  // The retired Guide deep link lands in the one Setup window. It is not a
  // Settings wing, so new Settings navigation cannot create a second home.
  if (head === "guide" || head === "setup") return { module: "setup", focus: tail.length ? tail.join("::") : undefined };
  // `desk` is the one old alias whose successor changed section; keep its
  // face meaning ahead of the retired module table's system fallback.
  const module = MODULE_ALIASES[head] ?? (SETTINGS_WINGS.some((entry) => entry.id === head) || PREF_MODULES.some((entry) => entry.id === head) ? head : null);
  return { module, focus: tail.length ? tail.join("::") : undefined };
}

export function settingsPageScope(scope?: string): { module: string | null; focus?: string } {
  const [head, ...tail] = (scope ?? "").split("::");
  if (head.startsWith("integration:")) {
    return { module: "accounts", focus: [head.slice("integration:".length), ...tail].filter(Boolean).join("::") };
  }
  const legacy = head === "desk" ? head : MODULE_ALIASES[head] ?? head;
  if (head === "guide" || head === "setup") return { module: "setup", focus: tail.length ? tail.join("::") : undefined };
  const module = SECTION_ALIASES[legacy] ?? (SETTINGS_SECTIONS.some((entry) => entry.id === legacy) ? legacy : null);
  return { module, focus: tail.length ? tail.join("::") : LEGACY_FOCUS[head] };
}
