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
  // Models stays the availability-only Model Library.
  { id: "models", label: "Models", glyph: "models", sprite: "models", keys: ["rails_observer"] },
  // Assignments is Models' peer: which compatible chain each job uses.
  { id: "assignments", label: "Assignments", glyph: "models", sprite: "models", keys: [] },
  // Connections: tool connections + credentials + RAW.
  { id: "integrations", label: "Connections", glyph: "secret", sprite: "integrations", keys: [] },
  // System: device name, desk reset, devices RAW.
  { id: "system", label: "System", glyph: "system", sprite: "system", keys: ["device", "mesh"] },
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
    setReceipt(`TOMBSTONED ${counts.tombstoned} · SEEDED ${counts.seeded}`);
  };
  return (
    <GadgetGroup label="Reset to seed">
      <div className="prefs-egress-line">
        <span className="gadget-fact">
          TOMBSTONES EXISTING DESK OBJECTS · RESTORES FURNISHED DEFAULTS
        </span>
      </div>
      <div className="prefs-egress-line">
        <span className="gadget-fact">
          KEEPS · MEETINGS · JOURNAL · SETTINGS · RUNS-ON TARGETS
        </span>
      </div>
      <div className="prefs-egress-line">
        <ConfirmVerb
          label="RESET TO SEED"
          confirmLabel="TOMBSTONE DESK & RESTORE DEFAULTS?"
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
  voice: { live: boolean; target: string };
  meetings: { intelligence: boolean; auto?: string; host?: string; lastRunAt?: string | null; lastRunS?: number | null };
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

/** The hub headline: the one fact that most needs him (UX-CANON C). */
function hubHeadline(hub: SettingsHubWire): { text: string; warning: boolean } {
  if (!hub.models.defaultSet) return { text: "No default model", warning: true };
  return { text: "All set", warning: false };
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
  const writtenAt = formatWrittenAt(hub.writtenAt);

  // Module rows — each opens the module face (the hub is the truth table).
  const openVerb = (moduleId: string) => (
    <Button variant="ghost" dense onClick={() => onOpen(moduleId)}>Open</Button>
  );

  return (
    <div className="prefs-face prefs-hub">
      <span
        className="surface-display prefs-hub-headline"
        data-warning={headline.warning || undefined}
      >
        {headline.text}
      </span>
      <SurfaceLedger count="" cols="hub">
        {/* Models: NO DEFAULT warning or N GROUPS SET + N ENGINES */}
        <SurfaceLedgerRow
          primary="Models"
          expands={false}
          onToggle={() => onOpen("models")}
          trailing={openVerb("models")}
          cells={<>
            {!hub.models.defaultSet
              ? <StateChip state="warning" label="NO DEFAULT" />
              : null}
            {hub.models.defaultSet && hub.models.groupsSet > 0
              ? <span className="surface-token" data-chip>{countToken(hub.models.groupsSet, "GROUP SET", "GROUPS SET")}</span>
              : null}
            {hub.models.engines > 0
              ? <span className="surface-token" data-chip>{countToken(hub.models.engines, "ENGINE", "ENGINES")}</span>
              : null}
          </>}
        />
        {/* Connections: N CONNECTED */}
        <SurfaceLedgerRow
          primary="Connections"
          expands={false}
          onToggle={() => onOpen("integrations")}
          trailing={openVerb("integrations")}
          cells={<>
            {hub.connections.connected > 0
              ? <span className="surface-token" data-chip>{countToken(hub.connections.connected, "CONNECTED", "CONNECTED")}</span>
              : null}
          </>}
        />
        {/* Voice: LIVE green + target, or nothing */}
        <SurfaceLedgerRow
          primary="Voice"
          expands={false}
          onToggle={() => onOpen("voice")}
          trailing={openVerb("voice")}
          cells={<>
            {hub.voice.live
              ? <StateChip state="success" label="LIVE" />
              : null}
            {hub.voice.live && hub.voice.target
              ? <span className="surface-token" data-chip>{hub.voice.target.toUpperCase()}</span>
              : null}
          </>}
        />
        {/* Meetings: INTELLIGENCE ON · AFTER ROOM MEETINGS / OFF */}
        <SurfaceLedgerRow
          primary="Meetings"
          expands={false}
          onToggle={() => onOpen("meetings")}
          trailing={openVerb("meetings")}
          cells={<>
            {hub.meetings.intelligence
              ? <StateChip state="success" label={`INTELLIGENCE ON${hub.meetings.auto && hub.meetings.auto !== "off" ? ` · ${autoLabel(hub.meetings.auto)}` : ""}`} />
              : <StateChip state="warning" label="INTELLIGENCE OFF" />}
          </>}
        />
        {/* Rhythm: EVERY N MIN · NEXT HH:MM when sweep runs; NO LOOPS only at zero + no sweep */}
        <SurfaceLedgerRow
          primary="Rhythm"
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
                  NEXT {hub.rhythm.nextSweepAt.slice(11, 16)}
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
          primary="Sounds & Presence"
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
          primary="Wallpaper"
          expands={false}
          onToggle={() => onOpen("wallpaper")}
          trailing={openVerb("wallpaper")}
          cells={<span className="surface-token" data-chip>{resolveAtmosphere(atmosphereId).name}</span>}
        />
        {/* System: THIS DEVICE + MESH OFF|ON + REMOTE OFF|ON */}
        <SurfaceLedgerRow
          primary="System"
          expands={false}
          onToggle={() => onOpen("system")}
          trailing={openVerb("system")}
          cells={<>
            <span className="surface-token" data-chip>{hub.system.host}</span>
            <span className="surface-token" data-chip>{hub.system.mesh ? "MESH ON" : "MESH OFF"}</span>
            {hub.system.remote
              ? <StateChip state="success" label="REMOTE ON" />
              : <span className="surface-token" data-chip>REMOTE OFF</span>}
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
    </div>
  );
}

/* ── the footer status bar: « PREFS | receipt | DEFAULTS (§3.6) ── */

export type PrefReceipt = {
  saving: boolean;
  writtenAt: string;
  refusal: string;
};

export function PrefStatusBar({
  onBack,
  receipt,
  hubWrittenAt,
}: {
  /** Absent on the drawer face — the egress badge sits there instead. */
  onBack?: () => void;
  receipt: PrefReceipt;
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
    <SurfaceFooter verbs={<>
      {onBack ? (
        <Button variant="ghost" dense className="prefs-back" onClick={onBack}>
          « PREFS
        </Button>
      ) : (
        <EgressChip />
      )}
      {center}
    </>} />
  );
}
