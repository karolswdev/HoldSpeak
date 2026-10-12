import { wireClock } from "../../desk/surface/format";
import { PeopleHubCells } from "./settingsPeople";
import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-111-01 — the Prefs program's face (audit §3.1-§3.4): a drawer of
// pref modules, authored — never wire-derived. The module registry is a
// CODE CONSTANT: a new wire key never mints a pane again (unmapped keys
// land in System, the one place the generic walker survives).
// HS-170-04: the drawer face is now a hub of SurfaceLedgerRows showing
// state tokens from GET /api/settings/hub. The tile grid is retired.
import { useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { CONTROL_MODES, controlModeLabel } from "../../lib/productLanguage";
import {
  CycleGadget,
  EgressChip,
  GadgetGroup,
} from "../../desk/surface/gadgets";
import {
  SurfaceLedger,
  SurfaceLedgerRow,
  StateChip,
  countToken,
  Receipt,
} from "../../desk/surface";
import { ConfirmVerb } from "../../desk/surface/Surface";
import { useDesk } from "../../desk/store";
import "./settings.css";
import { useAtmospherePreference } from "../../desk/gl/atmospherePreference";
import { resolveAtmosphere } from "../../desk/gl/atmosphereRegistry";

/* ── the roster (owner-named destinations, including the Models/Assignments pair) ── */

export type PrefModule = {
  id: string;
  label: string;
  glyph: string;
  /** Bright pixel sprite filename under /desk/sprites/settings/. */
  sprite: string;
  /** Top-level /api/settings keys this module owns. */
  keys: string[];
};

export const PREF_MODULES: PrefModule[] = [
  // HS-139-05 established the compact owner-facing roster. Wallpaper is the
  // local personalization drawer; it does not claim an /api/settings key.
  // Voice merges Hotkey + Transcription + Voice Typing + Wake Word.
  { id: "voice", label: "Voice", glyph: "dictation", sprite: "voice", keys: ["hotkey", "model", "dictation", "wake_word"] },
  // Sounds & Presence merges Appearance (desk sounds only) + Presence.
  { id: "sounds", label: "Sounds & Presence", glyph: "presence", sprite: "sounds", keys: ["ui", "presence"] },
  { id: "wallpaper", label: "Wallpaper", glyph: "wallpaper", sprite: "wallpaper", keys: [] },
  // Meetings: capture pointer + calendar source + actuators + RAW well.
  { id: "meetings", label: "Meetings", glyph: "meeting", sprite: "meetings", keys: ["meeting", "calendar"] },
  // Rhythm: cadence user-facing + Telegram + RAW.
  { id: "rhythm", label: "Rhythm", glyph: "cadence", sprite: "rhythm", keys: ["cadence", "cadence_telegram"] },
  // PHILO-16 (C): ONE tile, Runs on. The Models and Assignments tiles only
  // redirected to the same window; both ids still open it (`assignments`
  // is an alias below).
  { id: "models", label: "Runs on", glyph: "models", sprite: "models", keys: ["rails_observer"] },
  // Connections: tool connections + credentials + RAW.
  { id: "integrations", label: "Connections", glyph: "secret", sprite: "integrations", keys: [] },
  // System: device name, desk reset, devices RAW.
  { id: "system", label: "System", glyph: "system", sprite: "system", keys: ["device", "mesh"] },
  // Conductor R7 (canvas K7a, ratified 2026-10-07): People MCP access.
  { id: "people", label: "People", glyph: "system", sprite: "system", keys: ["people"] },
];

/** Stable id aliases: deep links and scope params from retired modules
 *  still land on their successor tile (no broken palette links). */
export const MODULE_ALIASES: Record<string, string> = {
  appearance: "sounds",
  hotkey: "voice",
  transcription: "voice",
  "voice-typing": "voice",
  "wake-word": "voice",
  presence: "sounds",
  cadence: "rhythm",
  devices: "system",
  delivery: "models",
  assignments: "models",
  desk: "system",
};

/** Which module owns a top-level settings key (System catches the rest). */
export function moduleForKey(key: string): string {
  for (const module of PREF_MODULES)
    if (module.keys.includes(key)) return module.id;
  return "system";
}

/* ── enum option sets, derived from the hub's own config canon
      (holdspeak/config.py, holdspeak/languages.py) ── */

// HS-139-01: THEME_OPTIONS deleted (dead — the theme setting has no
// runtime consumer; the desk is dark by law).
export const WHISPER_MODEL_OPTIONS = [
  "tiny",
  "base",
  "small",
  "medium",
  "large",
].map((value) => ({ value }));
// HS-139-01: TRANSCRIBE_BACKEND_OPTIONS deleted (duplicate; the Models
// module's Hub Default Engine keeps the backend cycle).
export const EXPORT_FORMAT_OPTIONS = ["txt", "markdown", "json", "srt"].map(
  (value) => ({ value }),
);
export const INTEL_PROVIDER_OPTIONS = ["local", "cloud"].map((value) => ({
  value,
}));

/* ── HS-132-10: the ONE meetings placement dial ──────────────────────────
   Meetings placement had two independent faces (a Provider cycle here, a
   RUNS ON destination pointer in Models) and no precedence signal, so
   setting Provider = LOCAL under an adopted destination did nothing,
   silently. The hub already decides with one rule; these read the
   provenance it now ships (`_placement.meeting`) so the face states which
   dial decided and what it loaded. Copy is label grammar, never prose. */

export type MeetingPlacementWire = {
  /** "destination" | "provider" | "provider-selection-ignored" */
  placement_source?: string;
  /** Why a set destination pointer was dropped (empty when none was). */
  placement_reason?: string;
  provider_intent?: string;
  /** False exactly when an adopted destination decided instead. */
  provider_honored?: boolean;
  boundary?: string;
  target_id?: string;
  target_name?: string;
  engine?: string;
  model?: string;
  node?: string;
  runnable?: boolean;
  runnable_reason?: string;
};

/** The precedence rule, rendered where the placement is set. */
export const MEETING_PLACEMENT_RULE =
  "DESTINATION WINS · PROVIDER DECIDES WHEN NO DESTINATION";

export function meetingPlacement(
  settings: Record<string, unknown> | undefined,
): MeetingPlacementWire | null {
  const block = (settings?._placement as
    | { meeting?: MeetingPlacementWire }
    | undefined)?.meeting;
  return block && typeof block === "object" ? block : null;
}

/** WHERE meetings run right now, as one fact line. */
export function placementLine(placement: MeetingPlacementWire): string {
  const target = String(
    placement.target_name || placement.node || "HUB DEFAULT",
  ).toUpperCase();
  const parts = ["RUNS ON", target, String(placement.boundary ?? "").toUpperCase()];
  if (placement.model) parts.push(String(placement.model).toUpperCase());
  return parts.filter(Boolean).join(" · ");
}

/** WHY the Provider dial did not decide. Empty string when it did. */
export function providerIgnoredReason(placement: MeetingPlacementWire): string {
  if (placement.provider_honored !== false) return "";
  const target = String(
    placement.target_name || placement.node || placement.target_id || "DESTINATION",
  ).toUpperCase();
  return `PROVIDER SELECTION IGNORED · DESTINATION ${target} DECIDES`;
}
export const MIR_PROFILE_OPTIONS = [
  "balanced",
  "architect",
  "delivery",
  "product",
  "incident",
].map((value) => ({ value }));
export const WAKE_ACTION_OPTIONS = ["preview", "type"].map((value) => ({
  value,
}));
export const CADENCE_PRESSURE_OPTIONS = [
  "gentle",
  "normal",
  "aggressive",
].map((value) => ({ value }));

// The Whisper language registry (holdspeak/languages.py, vendored):
// "auto" is the per-utterance detection sentinel.
const WHISPER_LANGUAGES: Array<[string, string]> = [
  ["en", "English"], ["zh", "Chinese"], ["de", "German"], ["es", "Spanish"],
  ["ru", "Russian"], ["ko", "Korean"], ["fr", "French"], ["ja", "Japanese"],
  ["pt", "Portuguese"], ["tr", "Turkish"], ["pl", "Polish"], ["ca", "Catalan"],
  ["nl", "Dutch"], ["ar", "Arabic"], ["sv", "Swedish"], ["it", "Italian"],
  ["id", "Indonesian"], ["hi", "Hindi"], ["fi", "Finnish"], ["vi", "Vietnamese"],
  ["he", "Hebrew"], ["uk", "Ukrainian"], ["el", "Greek"], ["ms", "Malay"],
  ["cs", "Czech"], ["ro", "Romanian"], ["da", "Danish"], ["hu", "Hungarian"],
  ["ta", "Tamil"], ["no", "Norwegian"], ["th", "Thai"], ["ur", "Urdu"],
  ["hr", "Croatian"], ["bg", "Bulgarian"], ["lt", "Lithuanian"], ["la", "Latin"],
  ["mi", "Maori"], ["ml", "Malayalam"], ["cy", "Welsh"], ["sk", "Slovak"],
  ["te", "Telugu"], ["fa", "Persian"], ["lv", "Latvian"], ["bn", "Bengali"],
  ["sr", "Serbian"], ["az", "Azerbaijani"], ["sl", "Slovenian"], ["kn", "Kannada"],
  ["et", "Estonian"], ["mk", "Macedonian"], ["br", "Breton"], ["eu", "Basque"],
  ["is", "Icelandic"], ["hy", "Armenian"], ["ne", "Nepali"], ["mn", "Mongolian"],
  ["bs", "Bosnian"], ["kk", "Kazakh"], ["sq", "Albanian"], ["sw", "Swahili"],
  ["gl", "Galician"], ["mr", "Marathi"], ["pa", "Punjabi"], ["si", "Sinhala"],
  ["km", "Khmer"], ["sn", "Shona"], ["yo", "Yoruba"], ["so", "Somali"],
  ["af", "Afrikaans"], ["oc", "Occitan"], ["ka", "Georgian"], ["be", "Belarusian"],
  ["tg", "Tajik"], ["sd", "Sindhi"], ["gu", "Gujarati"], ["am", "Amharic"],
  ["yi", "Yiddish"], ["lo", "Lao"], ["uz", "Uzbek"], ["fo", "Faroese"],
  ["ht", "Haitian Creole"], ["ps", "Pashto"], ["tk", "Turkmen"],
  ["nn", "Nynorsk"], ["mt", "Maltese"], ["sa", "Sanskrit"],
  ["lb", "Luxembourgish"], ["my", "Myanmar"], ["bo", "Tibetan"],
  ["tl", "Tagalog"], ["mg", "Malagasy"], ["as", "Assamese"], ["tt", "Tatar"],
  ["haw", "Hawaiian"], ["ln", "Lingala"], ["ha", "Hausa"], ["ba", "Bashkir"],
  ["jw", "Javanese"], ["su", "Sundanese"], ["yue", "Cantonese"],
];
export const LANGUAGE_OPTIONS = [
  { value: "auto", label: "auto" },
  ...WHISPER_LANGUAGES.map(([code, name]) => ({
    value: code,
    label: `${name} (${code})`,
  })),
];

/* ── HS-139-07: the tile sprites (bright mold, 32x32 retina) ──
   The settings tile icons use the owner-ratified bright pixel mold in the
   owner-ratified bright mold (Phase 135 icon-palette.png: silver-white
   forward, ink outline, ember + blue-grey accents). They live under
   web/public/desk/sprites/settings/ and render at 32px displayed
   (64px physical on retina) with image-rendering: pixelated. */

const SETTINGS_SPRITE_BASE = `${import.meta.env.BASE_URL || "/_built/"}desk/sprites/settings/`;

export function SettingSprite({ name }: { name: string }) {
  return (
    <img
      src={`${SETTINGS_SPRITE_BASE}${name}.png`}
      alt=""
      aria-hidden="true"
      className="prefs-tile-sprite"
      width={32}
      height={32}
    />
  );
}

/* ── legacy SVG glyph (kept for non-tile uses: posture shield etc.) ── */

export function SettingGlyph({ name }: { name: string }) {
  const paths: Record<string, string> = {
    posture: "M8 1.8 13 3.8v3.4c0 3.2-2.1 5.6-5 6.9-2.9-1.3-5-3.7-5-6.9V3.8Z",
    secret: "M3.5 7.5h9v5.5h-9Z M5.5 7.5V5.4a2.5 2.5 0 0 1 5 0v2.1",
    ui: "M3 5h10M3 5v6h10V5M6 8h4",
    hotkey: "M2.5 4.5h11v7h-11Z M4.5 6.5h1M7.5 6.5h1M10.5 6.5h1M5 9.5h6",
    model: "M4 12V7m4 5V4m4 8V9",
    dictation:
      "M8 2.5a2 2 0 0 1 2 2v3a2 2 0 1 1-4 0v-3a2 2 0 0 1 2-2Z M4.5 7.5a3.5 3.5 0 0 0 7 0M8 11v2.5",
    wake_word: "M8 2l1.2 3.3L12.5 6.5 9.2 7.7 8 11 6.8 7.7 3.5 6.5 6.8 5.3Z",
    presence:
      "M2.5 8s2-3.5 5.5-3.5S13.5 8 13.5 8s-2 3.5-5.5 3.5S2.5 8 2.5 8Z M8 8m-1.5 0a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0-3 0",
    meeting:
      "M5.5 6.5a2 2 0 1 0 0-.01M10.5 6.5a2 2 0 1 0 0-.01M2.5 12c0-1.7 1.3-3 3-3s3 1.3 3 3M8.5 12c0-1.7 1.3-3 3-3s3 1.3 3 3",
    cadence: "M8 8V4.5M8 8l2.5 1.5M8 2.5A5.5 5.5 0 1 0 8 13.5 5.5 5.5 0 1 0 8 2.5Z",
    device: "M4.5 2.5h7v11h-7Z M7 11.5h2",
    delivery: "M2.5 5.5h11v8h-11Z M2.5 5.5 8 2.5l5.5 3M8 8.5v5",
    models: "M4.5 4.5h7v7h-7Z M8 1.5v3M8 11.5v3M1.5 8h3M11.5 8h3",
    desk: "M2.5 3.5h11v9h-11Z M2.5 8h11 M6.5 5.75h3 M6.5 10.25h3",
    system: "M3 4.5h10M3 8h10M3 11.5h10M6 3v3M10 6.5v3M5 10v3",
  };
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path
        d={
          paths[name] ??
          "M8 8m-2.6 0a2.6 2.6 0 1 0 5.2 0a2.6 2.6 0 1 0-5.2 0"
        }
      />
    </svg>
  );
}

/* ── the Desk module (HS-112-03): reset-to-seed, the desk's FIRST
   destructive verb. Armed in-world in the kit's own grammar (the
   GadgetTable delete pattern — press, RESET DESK?, press again), never
   a modal, never a browser confirm. The face states in labels what
   resets and what survives; the receipt names the hub's counts. ── */

export function DeskModule() {
  const [busy, setBusy] = useState(false);
  const [receipt, setReceipt] = useState("");
  const [refused, setRefused] = useState(false);
  const fire = async () => {
    setBusy(true);
    setRefused(false);
    setReceipt("");
    const counts = await useDesk.getState().resetDesk();
    setBusy(false);
    if (!counts) {
      setRefused(true);
      return;
    }
    setReceipt(`CLEARED ${counts.tombstoned} · ADDED ${counts.seeded}`);
  };
  return (
    <GadgetGroup label="Desk">
      {/* PHILO-17 U35: plain words (was RESET TO SEED · TOMBSTONES
          EXISTING DESK OBJECTS); the consequence is one token each. */}
      <div className="prefs-egress-line">
        <span className="gadget-fact" data-testid="desk-reset-clears">
          CLEARS THE DESK · PUTS BACK THE DEFAULT ITEMS
        </span>
      </div>
      <div className="prefs-egress-line">
        <span className="gadget-fact" data-testid="desk-reset-keeps">
          KEEPS · MEETINGS · JOURNAL · SETTINGS · RUNS ON
        </span>
      </div>
      <div className="prefs-egress-line">
        <ConfirmVerb
          label="Reset desk to defaults"
          confirmLabel="Reset the desk?"
          busy={busy}
          onConfirm={() => void fire()}
        />
        {refused ? (
          <span className="gadget-fact" data-tone="danger" role="alert">
            <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" style={{ flexShrink: 0 }}><path d="M8 2 1.5 13.5h13Z" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /><line x1="8" y1="6.5" x2="8" y2="9.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" /><circle cx="8" cy="11.5" r="0.7" fill="currentColor" /></svg>{" "}
            RESET REFUSED
          </span>
        ) : receipt ? (
          <span className="gadget-fact" role="status">
            {receipt}
          </span>
        ) : null}
      </div>
    </GadgetGroup>
  );
}

/* ── HS-170-04: the hub wire shape (GET /api/settings/hub) ── */

export type SettingsHubWire = {
  models: { engines: number; groupsSet: number; defaultSet: boolean };
  connections: { connected: number };
  /** `engineSet`: the group resolves to an engine (its own or the default).
   *  A switch that is on with no engine is not a working path (A.10). */
  voice: { live: boolean; target: string; engineSet?: boolean };
  /** PHILO-15 B33: `engineSet` is the summary ROUTE the queue takes (exact,
   *  group, global default); `summariesOff` the owner's explicit OFF. */
  meetings: { intelligence: boolean; engineSet?: boolean; engine?: string | null; summariesOff?: boolean; auto?: string; host?: string; lastRunAt?: string | null; lastRunS?: number | null };
  /** PHILO-17 U35: the engine that answers an Ask; `engineSet` null = unknown. */
  answers?: { engineSet?: boolean | null; engine?: string | null };
  rhythm: {
    loops: number;
    sweepEveryMinutes?: number;
    nextSweepAt?: string | null;
    lastSweepAt?: string | null;
    quiet?: { start: number; end: number; held: boolean };
  };
  sounds: { on: boolean };
  system: { host: string; mesh: boolean; remote?: boolean };
  posture: string;
  writtenAt: number | null;
};

export type DeepHit = { module: string; label: string; path: string[] };

/* ── HS-172-02: auto-run label helpers ── */

const AUTO_LABELS: Record<string, string> = {
  room_linked: "AFTER ROOM MEETINGS",
  every: "AFTER EVERY MEETING",
  off: "OFF",
};

function autoLabel(auto: string | undefined): string {
  return AUTO_LABELS[auto ?? "off"] ?? "OFF";
}

export function autoDisplayFact(auto: string | undefined): string {
  const map: Record<string, string> = {
    room_linked: "After room meetings",
    every: "After every meeting",
    off: "Off",
  };
  return map[auto ?? "off"] ?? "Off";
}

export const INTELLIGENCE_AUTO_OPTIONS = [
  { value: "off", label: "OFF" },
  { value: "room_linked", label: "AFTER ROOM MEETINGS" },
  { value: "every", label: "AFTER EVERY MEETING" },
];

/* ── the drawer face ── */

/** The hub headline: the one fact that most needs him (UX-CANON C).
 *  PHILO-17 U35: a plain state of what he gets ("Summaries: <engine> ·
 *  Answers: <engine>"), never "No default model" (an operator's word). With
 *  no engine for any work: "No engine yet", and Choose opens Runs on. */
export function hubHeadline(hub: SettingsHubWire): { text: string; warning: boolean; choose: boolean } {
  const answersSet = hub.answers?.engineSet === true;
  // Astra r1 on #1090: the owner's OFF is a choice and an unknown Answers
  // route is no claim; neither makes "No engine yet". That state is only
  // for a desk where every KNOWN route is empty.
  if (!hub.meetings?.summariesOff && !hub.models.defaultSet && !workHasEngine(hub) && !answersSet) {
    return { text: "No engine yet", warning: true, choose: true };
  }
  const parts: string[] = [];
  let missing = false;
  const meetings = hub.meetings;
  if (meetings?.summariesOff) parts.push("Summaries: off");
  else if (meetings?.engineSet === false) { parts.push("Summaries: no engine"); missing = true; }
  else if (meetings?.engine) parts.push(`Summaries: ${meetings.engine}`);
  if (hub.answers?.engineSet === false) { parts.push("Answers: no engine"); missing = true; }
  else if (answersSet && hub.answers?.engine) parts.push(`Answers: ${hub.answers.engine}`);
  if (!parts.length) return { text: "All set", warning: false, choose: false };
  return { text: parts.join(" · "), warning: missing, choose: missing };
}

/** PHILO-15 B33: some work runs on an engine now (the summary route, or the
 *  voice rewrite's effective assignment). With no default, the headline and
 *  the Assignments row said "no model" while summaries ran on the LAN box. */
export function workHasEngine(hub: SettingsHubWire): boolean {
  return hub.meetings?.engineSet === true || hub.voice?.engineSet === true;
}

/** PHILO-17 REFIT: one pill per job on the Runs on plate: the job's word
 *  and a lamp (green set, amber no engine, grey off). The engine names stay
 *  in the headline; a job the hub does not report is left out. */
export function jobPills(hub: SettingsHubWire): Array<{ key: string; word: string; tone: "ok" | "warn" | "idle"; title?: string }> {
  const pills: Array<{ key: string; word: string; tone: "ok" | "warn" | "idle"; title?: string }> = [];
  if (hub.voice?.engineSet === false) pills.push({ key: "voice", word: "Speech", tone: "warn", title: "No engine" });
  else if (hub.voice?.engineSet === true) pills.push({ key: "voice", word: "Speech", tone: "ok" });
  const meetings = hub.meetings;
  if (meetings?.summariesOff) pills.push({ key: "summaries", word: "Summaries", tone: "idle", title: "Off" });
  else if (meetings?.engineSet === false) pills.push({ key: "summaries", word: "Summaries", tone: "warn", title: "No engine" });
  else if (meetings?.engineSet === true) pills.push({ key: "summaries", word: "Summaries", tone: "ok", title: meetings.engine ?? undefined });
  if (hub.answers?.engineSet === false) pills.push({ key: "answers", word: "Answers", tone: "warn", title: "No engine" });
  else if (hub.answers?.engineSet === true) pills.push({ key: "answers", word: "Answers", tone: "ok", title: hub.answers.engine ?? undefined });
  // The default (Everything else): a quiet fact while some work has an
  // engine of its own (PHILO-15 B33), amber when nothing has one.
  if (hub.models.defaultSet) pills.push({ key: "default", word: "Everything else", tone: "ok" });
  else pills.push({ key: "default", word: "Everything else", tone: workHasEngine(hub) ? "idle" : "warn", title: "No default" });
  return pills;
}

/** Format writtenAt (epoch seconds) as HH:MM for the receipt. */
function formatWrittenAt(epoch: number | null): string | null {
  if (epoch == null) return null;
  const d = new Date(epoch * 1000);
  return d.toTimeString().slice(0, 5);
}

export function PrefsFace({
  onOpen,
  hub,
  posture,
  postureBusy,
  onPosture,
  precedence,
}: {
  onOpen(moduleId: string): void;
  hub: SettingsHubWire;
  posture: string;
  postureBusy?: boolean;
  onPosture(mode: string): void;
  /** The precedence chain as data (etched fact line, never a paragraph). */
  precedence: string[];
}) {
  // HS-170-04: the hub is rows that tell the truth before you open them.
  // HS-139-07: precedence chain folded into the POSTURE title attribute.
  const precedenceText = (precedence.length
    ? precedence
    : ["hard invariants", "grants", "mode", "feature default"]
  )
    .join(" → ")
    .toUpperCase();

  const [atmosphereId] = useAtmospherePreference();
  const headline = hubHeadline(hub);
  const [more, setMore] = useState(false);
  const writtenAt = formatWrittenAt(hub.writtenAt);

  // Module rows — each opens the module face (the hub is the truth table).
  const openVerb = (moduleId: string) => (
    <Button variant="ghost" dense onClick={() => onOpen(moduleId)}>Open</Button>
  );

  // PHILO-17 REFIT: the two things he does here lead the window, each on a
  // raised plate: pick which engine does which job, and connect an account.
  // Everything else folds under More settings. ONE filled primary: Choose
  // engines while a job has no engine, else Connect an account while none is
  // connected, else Choose engines.
  const connected = hub.connections.connected;
  const lead: "engines" | "accounts" = !headline.choose && connected === 0 ? "accounts" : "engines";
  const jobs = jobPills(hub);
  return (
    <div className="prefs-face prefs-hub settings-home">
      <div className="settings-head">
        <h2
          className="surface-display prefs-hub-headline settings-title"
          data-warning={headline.warning || undefined}
        >
          {headline.text}
        </h2>
        <span className="settings-strip">
          <span>{hub.system.host}</span>
          {hub.models.engines > 0 ? <span><b>{hub.models.engines}</b> {hub.models.engines === 1 ? "engine" : "engines"}</span> : null}
          {connected > 0 ? <span><b>{connected}</b> connected</span> : null}
        </span>
      </div>
      <div className="settings-leads">
        <section className="settings-plate" data-focus={lead === "engines" || undefined} data-testid="settings-lead-engines" aria-label="Runs on">
          <header className="settings-plate-bar">
            <span className="settings-plate-label">RUNS ON</span>
          </header>
          <div className="settings-plate-body">
            <span className="settings-plate-sprite" aria-hidden="true"><SettingSprite name="models" /></span>
            <div className="settings-plate-text">
              <span className="settings-plate-title">Which engine does each job</span>
              <span className="settings-pills" data-testid="settings-job-pills">
                {jobs.map((job) => (
                  <span key={job.key} className="settings-pill" data-tone={job.tone} title={job.title} data-testid={`settings-job-${job.key}`}>{job.word}</span>
                ))}
              </span>
            </div>
          </div>
          <div className="settings-plate-verbs">
            <Button dense variant={lead === "engines" ? "primary" : "secondary"} onClick={() => onOpen("models")} data-testid="settings-hub-choose">
              Choose engines
            </Button>
          </div>
        </section>
        <section className="settings-plate" data-focus={lead === "accounts" || undefined} data-testid="settings-lead-accounts" aria-label="Accounts">
          <header className="settings-plate-bar">
            <span className="settings-plate-label">ACCOUNTS</span>
          </header>
          <div className="settings-plate-body">
            <span className="settings-plate-sprite" aria-hidden="true"><SettingSprite name="integrations" /></span>
            <div className="settings-plate-text">
              <span className="settings-plate-title">GitHub, Jira, Confluence, calendar</span>
              <span className="settings-pills">
                {connected > 0
                  ? <span className="settings-pill" data-tone="ok">{connected} connected</span>
                  : <span className="settings-pill" data-tone="idle">None connected</span>}
              </span>
            </div>
          </div>
          <div className="settings-plate-verbs">
            <Button dense variant={lead === "accounts" ? "primary" : "secondary"} onClick={() => onOpen("integrations")} data-testid="settings-hub-accounts">
              {connected > 0 ? "Open accounts" : "Connect an account"}
            </Button>
          </div>
        </section>
      </div>
      <Button
        variant="ghost"
        dense
        className="settings-more"
        aria-expanded={more}
        onClick={() => setMore((open) => !open)}
        data-testid="settings-more"
      >
        <span className="settings-more-caret" aria-hidden="true">{more ? "▾" : "▸"}</span> More settings
      </Button>
      {more ? (<>
      <SurfaceLedger count="" cols="hub">
        {/* Voice: LIVE green + target, or nothing */}
        <SurfaceLedgerRow
          primary={<span className="settings-row-name"><SettingSprite name="voice" />Voice</span>}
          expands={false}
          onToggle={() => onOpen("voice")}
          trailing={openVerb("voice")}
          cells={<>
            {/* Inventory 2026-10-03: this row said LIVE with no speech engine
                while Speak said NOT SET. LIVE needs the switch and an engine. */}
            {hub.voice.live && hub.voice.engineSet === false
              ? <StateChip state="warning" label="NO ENGINE" />
              : hub.voice.live
                ? <StateChip state="success" label="LIVE" />
                : null}
            {hub.voice.live && hub.voice.engineSet !== false && hub.voice.target
              ? <span className="surface-token" data-chip>{hub.voice.target.toUpperCase()}</span>
              : null}
          </>}
        />
        {/* Meetings: SUMMARY ON · AFTER ROOM MEETINGS / OFF.
            HS-202-04 (F06): the registry rules that every face says
            Summary for a meeting's result (`docs/product-language.json:23`);
            the hub row said the wire's word while the Meetings face two
            windows over said Summary on the same setting. */}
        <SurfaceLedgerRow
          primary={<span className="settings-row-name"><SettingSprite name="meetings" />Meetings</span>}
          expands={false}
          onToggle={() => onOpen("meetings")}
          trailing={openVerb("meetings")}
          cells={<>
            {/* PHILO-13-04 (A3): this row reads the CONFIGURED switch, so it
                says SET; whether an engine can run now is the Chair's fact
                ("No engine for summaries"), and a stored summary is the
                record's. No green: a setting is not a result (A.10). */}
            {/* Inventory 2026-10-03: with the switch on and no engine the row
                said SET ON beside the headline "No default model". The row
                names the missing engine, as the Chair does. */}
            {hub.meetings.intelligence && hub.meetings.summariesOff
              ? <StateChip state="idle" label="SUMMARIES OFF" />
              : hub.meetings.intelligence && hub.meetings.engineSet === false
              ? <StateChip state="warning" label="SUMMARY · NO ENGINE" />
              : hub.meetings.intelligence
              ? (
                // PHILO-17: the idle lamp's empty ring read as an empty
                // checkbox beside "AFTER EVERY MEETING". A summary that runs
                // by itself shows a check; by hand only, the ring stays.
                <StateChip
                  state="idle"
                  icon={hub.meetings.auto && hub.meetings.auto !== "off" ? "✓" : undefined}
                  label={`SUMMARY SET ON${hub.meetings.auto && hub.meetings.auto !== "off" ? ` · ${autoLabel(hub.meetings.auto)}` : ""}`}
                  data-testid="settings-hub-summary-chip"
                />
              )
              : <StateChip state="warning" label="SUMMARY SET OFF" />}
          </>}
        />
        {/* Rhythm: EVERY N MIN · NEXT HH:MM when sweep runs; NO LOOPS only at zero + no sweep */}
        <SurfaceLedgerRow
          primary={<span className="settings-row-name"><SettingSprite name="rhythm" />Rhythm</span>}
          expands={false}
          onToggle={() => onOpen("rhythm")}
          trailing={openVerb("rhythm")}
          cells={<>
            {hub.rhythm.sweepEveryMinutes != null
              ? <span className="surface-token" data-chip>
                  {hub.rhythm.sweepEveryMinutes >= 60
                    ? `EVERY ${Math.round(hub.rhythm.sweepEveryMinutes / 60)} HR`
                    : `EVERY ${hub.rhythm.sweepEveryMinutes} MIN`}
                </span>
              : null}
            {hub.rhythm.nextSweepAt
              ? <span className="surface-token" data-chip data-muted>
                  NEXT {wireClock(hub.rhythm.nextSweepAt)}
                </span>
              : null}
            {hub.rhythm.sweepEveryMinutes == null && hub.rhythm.loops > 0
              ? <span className="surface-token" data-chip>{countToken(hub.rhythm.loops, "LOOP", "LOOPS")}</span>
              : null}
            {hub.rhythm.sweepEveryMinutes == null && hub.rhythm.loops === 0
              ? <span className="surface-token" data-chip data-muted>NO LOOPS</span>
              : null}
          </>}
        />
        {/* Sounds & Presence: ON green or OFF */}
        <SurfaceLedgerRow
          primary={<span className="settings-row-name"><SettingSprite name="sounds" />Sounds & Presence</span>}
          expands={false}
          onToggle={() => onOpen("sounds")}
          trailing={openVerb("sounds")}
          cells={<>
            {hub.sounds.on
              ? <StateChip state="success" label="ON" />
              : <span className="surface-token" data-chip data-muted>OFF</span>}
          </>}
        />
        <SurfaceLedgerRow
          primary={<span className="settings-row-name"><SettingSprite name="wallpaper" />Wallpaper</span>}
          expands={false}
          onToggle={() => onOpen("wallpaper")}
          trailing={openVerb("wallpaper")}
          cells={<span className="surface-token" data-chip>{resolveAtmosphere(atmosphereId).name}</span>}
        />
        {/* People: Agents can read People | Agents: off (Conductor R7, K7a; PHILO-17 U35). */}
        <SurfaceLedgerRow
          primary={<span className="settings-row-name"><SettingSprite name="system" />People</span>}
          expands={false}
          onToggle={() => onOpen("people")}
          trailing={openVerb("people")}
          cells={<PeopleHubCells />}
        />
        {/* System: THIS DEVICE + Other devices: off|on (PHILO-17 U35: was
            MESH OFF · REMOTE OFF; the mesh name is a RAW fact now). */}
        <SurfaceLedgerRow
          primary={<span className="settings-row-name"><SettingSprite name="system" />System</span>}
          expands={false}
          onToggle={() => onOpen("system")}
          trailing={openVerb("system")}
          cells={<>
            <span className="surface-token" data-chip>{hub.system.host}</span>
            <OtherDevicesChip on={Boolean(hub.system.remote)} />
          </>}
        />
      </SurfaceLedger>
      <div className="prefs-rule" aria-hidden="true" />
      <div className="prefs-posture" title={precedenceText}>
        <span className="prefs-posture-label">Posture</span>
        <CycleGadget
          label="Control posture"
          value={posture}
          disabled={postureBusy}
          options={CONTROL_MODES.map((mode) => ({
            value: mode,
            label: controlModeLabel(mode),
          }))}
          onChange={onPosture}
        />
      </div>
      </>) : null}
    </div>
  );
}

/** PHILO-17 U35: remote access in plain words, on the hub row and the
 *  System face alike. */
export function OtherDevicesChip({ on }: { on: boolean }) {
  return on
    ? <StateChip state="success" label="Other devices: on" />
    : <span className="surface-token" data-chip>Other devices: off</span>;
}

/* ── the footer status bar: « Settings | receipt | DEFAULTS (§3.6) ── */

export type PrefReceipt = {
  saving: boolean;
  writtenAt: string;
  refusal: string;
};

export function PrefStatusBar({
  onBack,
  receipt,
  grantReceipt,
  hubWrittenAt,
}: {
  /** Absent on the drawer face — the egress badge sits there instead. */
  onBack?: () => void;
  receipt: PrefReceipt;
  /** PHILO-7-02: the last grant act's receipt Button, in the footer's CENTRE
   *  slot (away from the resize grip). */
  grantReceipt?: ReactNode;
  /** HS-170-04: writtenAt from the hub wire (epoch seconds), shown on
   *  the drawer face as WRITTEN HH:MM; module-level receipt overrides. */
  hubWrittenAt?: string | null;
}) {
  let center: ReactNode;
  if (receipt.refusal)
    center = (
      <span className="prefs-receipt" data-tone="danger" role="alert">
        <svg width="12" height="12" viewBox="0 0 16 16" aria-hidden="true" style={{ flexShrink: 0 }}><path d="M8 2 1.5 13.5h13Z" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" /><line x1="8" y1="6.5" x2="8" y2="9.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" /><circle cx="8" cy="11.5" r="0.7" fill="currentColor" /></svg>{" "}
        REFUSED · {receipt.refusal}
      </span>
    );
  else if (receipt.saving)
    center = (
      <span className="prefs-receipt" role="status">
        SAVING…
      </span>
    );
  else if (receipt.writtenAt)
    center = (
      <span className="prefs-receipt" role="status">
        WRITTEN {receipt.writtenAt}
      </span>
    );
  else if (!onBack && hubWrittenAt)
    center = (
      <span className="prefs-receipt" role="status">
        WRITTEN {hubWrittenAt}
      </span>
    );
  else center = null; /* HS-139-07: no dangling "USING" when idle */
  return (
    <SurfaceFooter receipt={grantReceipt ?? undefined} verbs={<>
      {onBack ? (
        <Button variant="ghost" dense className="prefs-back" onClick={onBack}>
          <span aria-hidden="true">«</span> Settings
        </Button>
      ) : (
        <EgressChip />
      )}
      {center}
    </>} />
  );
}
