import { sectionSprite } from "./native";
import { PrefStatus, stampDate, type PrefSaveState } from "./window";
// HS-111-01 — the Prefs program: authored sections, never wire-derived. The
// section roster is a CODE CONSTANT: a new wire key never mints a pane
// again. The language (2026-11-11): the rail says each section's health
// (`sectionHealth`), read from GET /api/settings/hub; the drawer face of
// HS-170-04 is gone.
import { useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  FoldGadget,
  GadgetGroup,
} from "../../../desk/surface/gadgets";
import { ConfirmVerb } from "../../../desk/surface/Surface";
import { DotWord } from "../../../desk/surface/kit";
import type { SpineTone } from "../../../desk/surface/patterns/Spine";
import { useDesk } from "../../../desk/store";

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
  // PHILO-17: Settings names the two hosted sections Engines and Accounts.
  { id: "models", label: "Engines", glyph: "models", sprite: "models", keys: ["rails_observer"] },
  { id: "integrations", label: "Accounts", glyph: "secret", sprite: "integrations", keys: [] },
  // System: device name, desk reset, devices RAW.
  { id: "system", label: "System", glyph: "system", sprite: "system", keys: ["device", "mesh"] },
  // Conductor R7 (canvas K7a, ratified 2026-10-07): People MCP access.
  { id: "people", label: "People", glyph: "system", sprite: "system", keys: ["people"] },
  // Betterment AG5 (DECISIONS #23): how many agents work at once.
  { id: "agents", label: "Agents", glyph: "system", sprite: "system", keys: ["agents"] },
];

/** The one-page Settings sections.  These ids are face anchors, rather than
 * another navigation layer: every old module scope resolves to one of these
 * sections and the page remains mounted while the owner moves around it. */
export const SETTINGS_SECTIONS = [
  { id: "you", label: "You", sprite: "system" },
  // The language (2026-11-11): Engines is a section of Settings, second,
  // because a working engine comes before every other choice.
  { id: "engines", label: "Engines", sprite: "models" },
  { id: "speak", label: "Speak", sprite: "voice" },
  { id: "meetings", label: "Meetings", sprite: "meetings" },
  // PG-DIRECTION DIR6 (ruled 2026-10-31): Notices becomes Reach; the id
  // stays for deep links.
  { id: "notices", label: "Reach", sprite: "rhythm" },
  { id: "accounts", label: "Accounts", sprite: "integrations" },
  { id: "calls", label: "Calls", sprite: "voice" },
  { id: "agents", label: "Agents", sprite: "system" },
  { id: "desk", label: "Desk", sprite: "wallpaper" },
  { id: "this-mac", label: "This Mac", sprite: "system" },
] as const;

export type SettingsSectionId = (typeof SETTINGS_SECTIONS)[number]["id"];

/** Palette rows are the same labels the page renders.  The registry uses
 * this list instead of inventing a second Settings search surface. */
export type SettingsPaletteRow = {
  id: string;
  label: string;
  section: SettingsSectionId;
  focus: string;
  terms?: string;
};

export const SETTINGS_PALETTE_ROWS: readonly SettingsPaletteRow[] = [
  { id: "owner-name", label: "Your name", section: "you", focus: "owner-name", terms: "owner you identity" },
  { id: "owner-aliases", label: "Also called", section: "you", focus: "owner-aliases", terms: "aliases names" },
  { id: "push-to-talk", label: "Push-to-talk key", section: "speak", focus: "push-to-talk", terms: "hotkey mic speak" },
  { id: "language", label: "Language", section: "speak", focus: "language", terms: "speech transcription" },
  { id: "preview-before-type", label: "Preview before type", section: "speak", focus: "preview-before-type", terms: "dictation typing" },
  { id: "voice-commands", label: "Voice commands", section: "speak", focus: "voice-commands", terms: "macros" },
  { id: "wake-word", label: "Wake word", section: "speak", focus: "wake-word", terms: "wake" },
  { id: "spoken-symbols", label: "Spoken symbols", section: "speak", focus: "spoken-symbols", terms: "symbols" },
  { id: "make-summary", label: "Make summary", section: "meetings", focus: "make-summary", terms: "summary meeting" },
  { id: "record-by-itself", label: "Auto-record", section: "meetings", focus: "record-by-itself", terms: "record recording" },
  { id: "microphone", label: "Microphone", section: "meetings", focus: "microphone", terms: "mic audio" },
  { id: "export", label: "Export", section: "meetings", focus: "export", terms: "meeting export" },
  { id: "notify", label: "Notify", section: "notices", focus: "notify", terms: "notification rhythm" },
  { id: "quiet-hours", label: "Quiet hours", section: "notices", focus: "quiet-hours", terms: "quiet rhythm cadence" },
  { id: "daily-brief", label: "Daily brief", section: "notices", focus: "daily-brief", terms: "brief morning rhythm" },
  { id: "max-nudges", label: "Max nudges", section: "notices", focus: "max-nudges", terms: "nudges rhythm" },
  { id: "reach-telegram", label: "Telegram", section: "notices", focus: "reach.telegram", terms: "telegram bot pair reach notices" },
  { id: "reach-ladder", label: "When to reach you", section: "notices", focus: "reach.ladder", terms: "reach ladder phone call message" },
  { id: "reach-later", label: "Later means", section: "notices", focus: "reach.later", terms: "later defer reach" },
  { id: "reach-digest", label: "Digest", section: "notices", focus: "reach.digest", terms: "digest morning reach telegram" },
  { id: "connections", label: "Connections", section: "accounts", focus: "connections", terms: "account provider" },
  { id: "calendar", label: "Calendar", section: "accounts", focus: "calendar", terms: "calendar" },
  { id: "destinations", label: "Destinations", section: "accounts", focus: "destinations", terms: "send" },
  { id: "secrets", label: "Secrets", section: "accounts", focus: "secrets", terms: "credentials tokens" },
  { id: "calls", label: "Calls", section: "calls", focus: "calls", terms: "phone call ai-phone telnyx sip passphrase" },
  { id: "agents", label: "Agents", section: "agents", focus: "agents", terms: "agent readiness" },
  { id: "agents-act", label: "Agents act", section: "agents", focus: "agents-act", terms: "secure normal yolo posture" },
  { id: "people-access", label: "People access", section: "agents", focus: "people-access", terms: "people read write" },
  { id: "wallpaper", label: "Wallpaper", section: "desk", focus: "wallpaper", terms: "change places atmosphere" },
  { id: "desk-sounds", label: "Desk sounds", section: "desk", focus: "desk-sounds", terms: "sounds" },
  { id: "motion", label: "Motion", section: "desk", focus: "motion", terms: "animation" },
  { id: "presence", label: "Presence", section: "desk", focus: "presence", terms: "mascot" },
  { id: "engines", label: "Engines", section: "this-mac", focus: "engines", terms: "models runs on" },
  { id: "setup", label: "Setup", section: "this-mac", focus: "setup", terms: "found readiness" },
  { id: "other-devices", label: "Other devices", section: "this-mac", focus: "other-devices", terms: "remote mesh" },
  { id: "device-name", label: "Name of this Mac", section: "this-mac", focus: "device-name", terms: "device computer" },
  { id: "reset-desk", label: "Reset the desk", section: "this-mac", focus: "reset-desk", terms: "reset defaults" },
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

/* ── enum option sets, derived from the hub's own config canon
      (holdspeak/config.py, holdspeak/languages.py) ── */

// HS-139-01: THEME_OPTIONS deleted (dead — the theme setting has no
// runtime consumer; the desk is dark by law).
/** Window Program W4 (the words): a select shows a sentence-case word; the
 *  stored value stays the wire token underneath (`normal` reads `Normal`). */
const worded = (value: string) => ({ value, label: value.charAt(0).toUpperCase() + value.slice(1) });
// HS-139-01: TRANSCRIBE_BACKEND_OPTIONS deleted (duplicate; the Models
// module's Hub Default Engine keeps the backend cycle).
export const EXPORT_FORMAT_OPTIONS = ["txt", "markdown", "json", "srt"].map(
  (value) => ({ value }),
);
export const MIR_PROFILE_OPTIONS = [
  "balanced",
  "architect",
  "delivery",
  "product",
  "incident",
].map(worded);
export const WAKE_ACTION_OPTIONS = ["preview", "type"].map(worded);
export const CADENCE_PRESSURE_OPTIONS = [
  "gentle",
  "normal",
  "aggressive",
].map(worded);

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
  { value: "auto", label: "Automatic" },
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

export function SettingSprite({ name, src }: { name: string; src?: string }) {
  return (
    <img
      src={src ?? `${SETTINGS_SPRITE_BASE}${name}.png`}
      alt=""
      aria-hidden="true"
      className="prefs-tile-sprite"
      width={32}
      height={32}
    />
  );
}

/* The rail's illustrated glyphs: the section's sprite (`sectionSprite`,
   one place for the rail and the mast). */
export function SettingsRailGlyph({ section }: { section: (typeof SETTINGS_SECTIONS)[number] }) {
  return <SettingSprite name={section.sprite} src={sectionSprite(section.id, section.sprite)} />;
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
    setReceipt(`Cleared ${counts.tombstoned} · Added ${counts.seeded}`);
  };
  return (
    <GadgetGroup label="Desk" material="inset" actions={<>
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
          <span role="status">
            <DotWord tone="ok">{receipt}</DotWord>
          </span>
        ) : null}
      </>}>
      {/* PHILO-17 U35: plain words (was RESET TO SEED · TOMBSTONES
          EXISTING DESK OBJECTS); the consequence is one token each. */}
      <FoldGadget title="Reset details">
        <div className="prefs-reset-details">
          <span className="gadget-fact" data-testid="desk-reset-clears">
            CLEARS THE DESK · PUTS BACK THE DEFAULT ITEMS
          </span>
          <span className="gadget-fact" data-testid="desk-reset-keeps">
            KEEPS · MEETINGS · JOURNAL · SETTINGS · ENGINES
          </span>
        </div>
      </FoldGadget>
    </GadgetGroup>
  );
}

/* ── HS-170-04: the hub wire shape (GET /api/settings/hub) ── */

export type SettingsHubWire = {
  models: { engines: number; groupsSet: number; defaultSet: boolean };
  connections: { connected: number };
  /** `engineSet`: the group resolves to an engine (its own or the default).
   *  A switch that is on with no engine is not a working path (A.10). */
  voice: { live: boolean; target: string; engineSet?: boolean; speechReady?: boolean | null };
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
  /** Betterment AG5: the working-at-once limit (absent on an older hub). */
  agents?: { workingAtOnce: number };
  system: { host: string; mesh: boolean; remote?: boolean };
  posture: string;
  writtenAt: number | null;
};

export const INTELLIGENCE_AUTO_OPTIONS = [
  { value: "off", label: "Manual" },
  { value: "room_linked", label: "After room meetings" },
  { value: "every", label: "After every meeting" },
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

/* ── the rail's health (the language, 2026-11-11): one tone and one word
   per section, from the one hub read. Moss is set up, brass needs him,
   coral is failing, idle is not set. No zero counts: an empty section
   says "Not set". ── */

export type SectionHealth = { tone: SpineTone; word: string };

export function sectionHealth(hub: SettingsHubWire, ownerName = ""): Partial<Record<SettingsSectionId, SectionHealth>> {
  const idle = (word = "Not set"): SectionHealth => ({ tone: "idle", word });
  const head = hubHeadline(hub);
  const engines = hub.models.engines;
  const meetings = hub.meetings;
  return {
    you: ownerName.trim() ? { tone: "moss", word: ownerName.trim() } : { tone: "brass", word: "Add your name" },
    engines: head.text === "No engine yet" && engines === 0
      ? { tone: "brass", word: "No engine yet" }
      : head.warning
        ? { tone: "brass", word: "Choose an engine" }
        : { tone: "moss", word: engines > 0 ? (engines === 1 ? "1 engine" : `${engines} engines`) : "Engine assigned" },
    speak: !hub.voice.live ? idle("Off")
      : hub.voice.speechReady === false ? { tone: "brass", word: "Speech not set up" }
        : { tone: "moss", word: "On" },
    meetings: !meetings.intelligence || meetings.summariesOff ? idle("Summaries off")
      : meetings.engineSet === false ? { tone: "brass", word: "No summary engine" }
        : { tone: "moss", word: meetings.engine ? `Summaries · ${meetings.engine}` : "Summaries on" },
    notices: hub.rhythm.sweepEveryMinutes != null
      ? { tone: "moss", word: hub.rhythm.sweepEveryMinutes >= 60 ? `Every ${Math.round(hub.rhythm.sweepEveryMinutes / 60)} hr` : `Every ${hub.rhythm.sweepEveryMinutes} min` }
      : hub.rhythm.loops > 0 ? { tone: "moss", word: hub.rhythm.loops === 1 ? "1 loop" : `${hub.rhythm.loops} loops` } : idle(),
    accounts: hub.connections.connected > 0 ? { tone: "moss", word: `${hub.connections.connected} connected` } : idle(),
    agents: hub.agents ? { tone: "moss", word: `Up to ${hub.agents.workingAtOnce} at once` } : idle(),
    desk: { tone: hub.sounds.on ? "moss" : "idle", word: hub.sounds.on ? "Sounds on" : "Sounds off" },
    "this-mac": hub.system.remote ? { tone: "moss", word: "Other devices on" } : idle("This Mac only"),
  };
}

/* ── the status bar (window grammar 2026-10-24): save state · facts ── */

export type PrefReceipt = {
  saving: boolean;
  writtenAt: string;
  refusal: string;
};

/** The general preferences writer's state, as the status bar says it. */
export function prefSaveState(receipt: PrefReceipt, hubWrittenAt?: string | null): PrefSaveState | null {
  // The plain reason is in the pane's alert; the bar stays short.
  if (receipt.refusal) return { tone: "danger", text: "Not saved" };
  if (receipt.saving) return { tone: "busy", text: "Saving…" };
  const at = stampDate(receipt.writtenAt) ?? stampDate(hubWrittenAt);
  if (at) return { tone: "ok", text: "Saved", at };
  return null;
}

export function PrefStatusBar({
  onBack,
  receipt,
  grantReceipt,
  hubWrittenAt,
  idleReceipt,
  onRetry,
  save,
  facts,
  failureTestId,
}: {
  /** Absent on the Settings window; a hosted module may name its way back. */
  onBack?: () => void;
  receipt: PrefReceipt;
  /** PHILO-7-02: the last grant act's receipt Button, after the facts. */
  grantReceipt?: ReactNode;
  /** HS-170-04: writtenAt from the hub wire (HH:MM), said as Saved <clock>. */
  hubWrittenAt?: string | null;
  /** A fact said when nothing is being saved (Checked 16:22). */
  idleReceipt?: ReactNode;
  onRetry?: () => void;
  /** A writer with its own receipts (Settings You) says its own state. */
  save?: PrefSaveState | null;
  facts?: ReactNode[];
  failureTestId?: string | null;
}) {
  const state = save !== undefined ? save : prefSaveState(receipt, onBack ? null : hubWrittenAt);
  return (
    <PrefStatus
      save={state}
      facts={[...(facts ?? []), idleReceipt ?? null]}
      extra={grantReceipt}
      onRetry={onRetry}
      retryDisabled={receipt.saving}
      failureTestId={failureTestId}
      verbs={onBack ? (
        <Button variant="secondary" dense onClick={onBack}>
          <span aria-hidden="true">«</span> Settings
        </Button>
      ) : null}
    />
  );
}
