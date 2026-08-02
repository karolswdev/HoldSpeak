// HS-111-01 — the Prefs program's face (audit §3.1-§3.4): a drawer of
// pref modules, authored — never wire-derived. The module registry is a
// CODE CONSTANT: a new wire key never mints a pane again (unmapped keys
// land in System, the one place the generic walker survives).
import { useMemo, useState, type ReactNode } from "react";
import { CONTROL_MODES, controlModeLabel } from "../../lib/productLanguage";
import {
  CycleGadget,
  EgressChip,
  GadgetGroup,
  StringGadget,
} from "../../desk/surface/gadgets";
import { ConfirmVerb } from "../../desk/surface/Surface";
import { useDesk } from "../../desk/store";

/* ── the roster (audit §3.2) ── */

export type PrefModule = {
  id: string;
  label: string;
  glyph: string;
  /** Top-level /api/settings keys this module owns. */
  keys: string[];
};

export const PREF_MODULES: PrefModule[] = [
  { id: "appearance", label: "Appearance", glyph: "ui", keys: ["ui"] },
  { id: "hotkey", label: "Hotkey", glyph: "hotkey", keys: ["hotkey"] },
  { id: "transcription", label: "Transcription", glyph: "model", keys: ["model"] },
  { id: "voice-typing", label: "Voice Typing", glyph: "dictation", keys: ["dictation"] },
  { id: "wake-word", label: "Wake Word", glyph: "wake_word", keys: ["wake_word"] },
  { id: "presence", label: "Presence", glyph: "presence", keys: ["presence"] },
  { id: "meetings", label: "Meetings", glyph: "meeting", keys: ["meeting"] },
  { id: "cadence", label: "Cadence", glyph: "cadence", keys: ["cadence", "cadence_telegram"] },
  { id: "devices", label: "Devices", glyph: "device", keys: ["device", "mesh"] },
  { id: "delivery", label: "Delivery", glyph: "delivery", keys: [] },
  { id: "models", label: "Models", glyph: "models", keys: [] },
  { id: "desk", label: "Desk", glyph: "desk", keys: [] },
  { id: "integrations", label: "Integrations", glyph: "secret", keys: [] },
  { id: "system", label: "System", glyph: "system", keys: [] },
];

/** Which module owns a top-level settings key (System catches the rest). */
export function moduleForKey(key: string): string {
  for (const module of PREF_MODULES)
    if (module.keys.includes(key)) return module.id;
  return "system";
}

/* ── enum option sets, derived from the hub's own config canon
      (holdspeak/config.py, holdspeak/languages.py) ── */

export const THEME_OPTIONS = ["dark", "light", "dracula", "monokai"].map(
  (value) => ({ value }),
);
export const WHISPER_MODEL_OPTIONS = [
  "tiny",
  "base",
  "small",
  "medium",
  "large",
].map((value) => ({ value }));
export const TRANSCRIBE_BACKEND_OPTIONS = [
  "auto",
  "mlx",
  "faster-whisper",
].map((value) => ({ value }));
export const EXPORT_FORMAT_OPTIONS = ["txt", "markdown", "json", "srt"].map(
  (value) => ({ value }),
);
export const INTEL_PROVIDER_OPTIONS = ["local", "cloud"].map((value) => ({
  value,
}));
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

/* ── the module glyphs (24px, the desk's stroke discipline) ── */

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
          RESETS · NOTES · KNOWLEDGE · AGENTS · WORKFLOWS · DRAWERS · LAYOUT
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
          confirmLabel="RESET DESK?"
          busy={busy}
          onConfirm={() => void fire()}
        />
        {refused ? (
          <span className="gadget-fact" data-tone="danger" role="alert">
            ⚠ RESET REFUSED
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

/* ── the drawer face ── */

export type DeepHit = { module: string; label: string; path: string[] };

export function PrefsFace({
  hits,
  onOpen,
  posture,
  postureBusy,
  onPosture,
  precedence,
}: {
  /** The deep setting index (module id + presented label + wire path). */
  hits: DeepHit[];
  onOpen(moduleId: string, highlight?: string): void;
  posture: string;
  postureBusy?: boolean;
  onPosture(mode: string): void;
  /** The precedence chain as data (etched fact line, never a paragraph). */
  precedence: string[];
}) {
  const [filter, setFilter] = useState("");
  const query = filter.trim().toLowerCase();
  const modules = useMemo(
    () =>
      query
        ? PREF_MODULES.filter((module) =>
            module.label.toLowerCase().includes(query),
          )
        : PREF_MODULES,
    [query],
  );
  const deep = useMemo(() => {
    if (!query) return [];
    return hits
      .filter((hit) => hit.label.toLowerCase().includes(query))
      .slice(0, 12);
  }, [hits, query]);
  const moduleLabel = (id: string) =>
    PREF_MODULES.find((module) => module.id === id)?.label ?? id;
  const openTop = () => {
    if (deep.length) onOpen(deep[0].module, deep[0].path.join("."));
    else if (modules.length) onOpen(modules[0].id);
  };
  return (
    <div className="prefs-face">
      <div className="prefs-filter">
        <StringGadget
          label="Filter settings"
          value={filter}
          placeholder="FILTER"
          onChange={setFilter}
          onKeyDown={(event) => {
            if (event.key === "Enter") openTop();
          }}
        />
      </div>
      {deep.length ? (
        <ul className="prefs-hits">
          {deep.map((hit) => (
            <li key={hit.path.join(".")}>
              <button
                type="button"
                onClick={() => onOpen(hit.module, hit.path.join("."))}
              >
                <span className="prefs-hit-module">
                  {moduleLabel(hit.module)}
                </span>
                <span aria-hidden="true"> » </span>
                {hit.label}
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      <div className="prefs-grid" role="list">
        {modules.map((module) => (
          <button
            key={module.id}
            type="button"
            role="listitem"
            className="prefs-tile"
            onClick={() => onOpen(module.id)}
          >
            <span className="prefs-tile-glyph">
              <SettingGlyph name={module.glyph} />
            </span>
            <span className="prefs-tile-label">{module.label}</span>
          </button>
        ))}
      </div>
      <div className="prefs-rule" aria-hidden="true" />
      <div className="prefs-posture">
        <span className="prefs-posture-label">POSTURE</span>
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
        <span className="gadget-fact">{controlModeLabel(posture)}</span>
      </div>
      <div className="prefs-precedence">
        {(precedence.length
          ? precedence
          : ["hard invariants", "grants", "mode", "feature default"]
        )
          .join(" → ")
          .toUpperCase()}
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
}: {
  /** Absent on the drawer face — the egress badge sits there instead. */
  onBack?: () => void;
  receipt: PrefReceipt;
}) {
  let center: ReactNode;
  if (receipt.refusal)
    center = (
      <span className="prefs-receipt" data-tone="danger" role="alert">
        ⚠ REFUSED · {receipt.refusal}
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
        USING · WRITTEN {receipt.writtenAt}
      </span>
    );
  else
    center = (
      <span className="prefs-receipt" role="status">
        USING
      </span>
    );
  return (
    <div className="surface-status prefs-status">
      {onBack ? (
        <button type="button" className="prefs-back" onClick={onBack}>
          « PREFS
        </button>
      ) : (
        <EgressChip />
      )}
      {center}
      <button
        type="button"
        className="prefs-defaults"
        disabled
        title="defaults source pending"
      >
        DEFAULTS
      </button>
    </div>
  );
}
