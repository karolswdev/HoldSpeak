// HS-101 round 5 — bespoke configuration components (the owner's
// bar: "these things are complicated enough that they can't just be
// dumbed down to a bunch of input boxes"). A complex idea gets a
// component shaped like the idea:
//  - RuntimeDestination: "where does voice typing run" — one choice
//    among bays, each revealing only ITS fields (13 boxes fold away).
//  - HotkeyCapture: a key is pressed, not typed — mapped to exactly
//    the key names the hub accepts (holdspeak/hotkey.py).
import { useEffect, useRef, useState } from "react";
import {
  Button,
  Select,
  TextInput,
} from "../../components/signal/Signal";
import { apiFetch, type JsonRecord } from "../../lib/api";
import { openSurfaceOr } from "../../desk/shell";
import {
  Disclosure,
} from "../../components/signal/Signal";
import {
  SurfaceGroup,
  SurfaceSettingRow,
  SurfaceToggle,
} from "../../desk/surface/Surface";

/* ── the hotkey: pressed, not typed ────────────────────────────── */

// The hub's accepted set (holdspeak/hotkey.py _key_name_map) — the
// capture can only ever write a name the listener understands.
const CODE_TO_NAME: Record<string, string> = {
  AltRight: "alt_r",
  AltLeft: "alt_l",
  ControlRight: "ctrl_r",
  ControlLeft: "ctrl_l",
  MetaRight: "cmd_r",
  MetaLeft: "cmd_l",
  ShiftRight: "shift_r",
  ShiftLeft: "shift_l",
  CapsLock: "caps_lock",
};
for (let n = 1; n <= 12; n += 1) CODE_TO_NAME[`F${n}`] = `f${n}`;

const NAME_TO_DISPLAY: Record<string, string> = {
  alt_r: "⌥R",
  alt_l: "⌥L",
  ctrl_r: "⌃R",
  ctrl_l: "⌃L",
  cmd_r: "⌘R",
  cmd_l: "⌘L",
  shift_r: "⇧R",
  shift_l: "⇧L",
  caps_lock: "⇪",
};
for (let n = 1; n <= 12; n += 1) NAME_TO_DISPLAY[`f${n}`] = `F${n}`;

export function HotkeyCapture({
  value,
  onCommit,
}: {
  value: JsonRecord;
  onCommit: (next: { key: string; display: string }) => void;
}) {
  const [listening, setListening] = useState(false);
  const [refused, setRefused] = useState("");
  useEffect(() => {
    if (!listening) return;
    const onKey = (event: KeyboardEvent) => {
      event.preventDefault();
      event.stopPropagation();
      if (event.key === "Escape") {
        setListening(false);
        return;
      }
      const name = CODE_TO_NAME[event.code];
      if (!name) {
        setRefused(
          `${event.code} can't be a hold key — use a modifier (⌥ ⌃ ⌘ ⇧, left or right), ⇪, or F1–F12`,
        );
        return;
      }
      setRefused("");
      setListening(false);
      onCommit({ key: name, display: NAME_TO_DISPLAY[name] ?? name });
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [listening, onCommit]);
  const current = String(value.display || value.key || "unset");
  return (
    <SurfaceGroup>
      <SurfaceSettingRow
        label="Push-to-talk key"
        description={
          listening
            ? refused || "Press the key to hold — Esc cancels"
            : "Hold it to talk, release to type"
        }
        control={
          <button
            type="button"
            className={
              "settings-keycap" + (listening ? " is-listening" : "")
            }
            onClick={() => {
              setRefused("");
              setListening((v) => !v);
            }}
          >
            {listening ? "…" : current}
          </button>
        }
      />
    </SurfaceGroup>
  );
}

/* ── the runtime: one destination, not thirteen boxes ──────────── */

type RuntimeMode = "auto" | "mlx" | "llama_cpp" | "openai_compatible" | "profile";

const MODE_LABEL: Record<RuntimeMode, [string, string]> = {
  auto: ["Automatic", "picks the best local engine on this device"],
  mlx: ["This device · MLX", "an Apple-silicon model file"],
  llama_cpp: ["This device · llama.cpp", "a GGUF model file"],
  openai_compatible: ["An endpoint", "any OpenAI-compatible server"],
  profile: ["A saved destination", "one of your Runs on destinations"],
};

function runtimeMode(rt: JsonRecord): RuntimeMode {
  if (rt.profile_id) return "profile";
  const backend = String(rt.backend ?? "auto");
  return (["mlx", "llama_cpp", "openai_compatible"] as const).includes(
    backend as never,
  )
    ? (backend as RuntimeMode)
    : "auto";
}

export function RuntimeDestination({
  value,
  onCommit,
}: {
  value: JsonRecord;
  onCommit: (next: JsonRecord) => void;
}) {
  const mode = runtimeMode(value);
  const [profiles, setProfiles] = useState<JsonRecord[]>([]);
  const fetched = useRef(false);
  useEffect(() => {
    if (fetched.current) return;
    fetched.current = true;
    void apiFetch<{ profiles?: JsonRecord[] }>("/api/profiles")
      .then((data) =>
        setProfiles(
          (data.profiles ?? []).filter((row) => !row.deleted),
        ),
      )
      .catch(() => setProfiles([]));
  }, []);
  const patch = (next: JsonRecord) => onCommit({ ...value, ...next });
  const choose = (next: RuntimeMode) => {
    if (next === "profile") {
      patch({ profile_id: String(profiles[0]?.id ?? "") || null });
    } else {
      patch({ backend: next, profile_id: null });
    }
  };
  const field = (
    label: string,
    key: string,
    placeholder?: string,
  ) => (
    <SurfaceSettingRow
      label={label}
      control={
        <TextInput
          aria-label={label}
          value={String(value[key] ?? "")}
          placeholder={placeholder}
          onChange={(event) => patch({ [key]: event.target.value })}
        />
      }
    />
  );
  return (
    <div className="settings-destination">
      <div className="settings-bays" role="radiogroup" aria-label="Runs on">
        {(Object.keys(MODE_LABEL) as RuntimeMode[]).map((option) => {
          const [name, caption] = MODE_LABEL[option];
          const selected = option === mode;
          return (
            <button
              key={option}
              type="button"
              role="radio"
              aria-checked={selected}
              className={
                "settings-bay" + (selected ? " is-selected" : "")
              }
              onClick={() => choose(option)}
            >
              <span className="settings-bay-dot" aria-hidden="true" />
              <span className="settings-bay-text">
                <strong>{name}</strong>
                <small>{caption}</small>
              </span>
            </button>
          );
        })}
      </div>
      <SurfaceGroup>
        {mode === "mlx"
          ? field("MLX model", "mlx_model", "~/Models/mlx/…")
          : null}
        {mode === "llama_cpp"
          ? field("Model file", "llama_cpp_model_path", "~/Models/gguf/…")
          : null}
        {mode === "openai_compatible" ? (
          <>
            {field("Endpoint URL", "openai_compatible_base_url", "http://…/v1")}
            {field("Model", "openai_compatible_model")}
            {field("API key env var", "openai_compatible_api_key_env")}
          </>
        ) : null}
        {mode === "profile" ? (
          <SurfaceSettingRow
            label="Destination"
            control={
              <span className="surface-actions">
                <Select
                  aria-label="Saved destination"
                  value={String(value.profile_id ?? "")}
                  onChange={(event) =>
                    patch({ profile_id: event.target.value || null })
                  }
                >
                  {profiles.length ? null : (
                    <option value="">No saved destinations</option>
                  )}
                  {profiles.map((row) => (
                    <option key={String(row.id)} value={String(row.id)}>
                      {String(row.name ?? row.id)}
                    </option>
                  ))}
                </Select>
                <Button
                  dense
                  variant="ghost"
                  onClick={() => openSurfaceOr("configure-runs-on", "/profiles")}
                >
                  Open Runs on
                </Button>
              </span>
            }
          />
        ) : null}
      </SurfaceGroup>
      <Disclosure title="Engine details">
        <SurfaceGroup>
          <SurfaceSettingRow
            label="Context window"
            control={
              <TextInput
                aria-label="Context window"
                type="number"
                value={Number(value.n_ctx ?? 2048)}
                onChange={(event) =>
                  patch({ n_ctx: Number(event.target.value) })
                }
              />
            }
          />
          <SurfaceSettingRow
            label="Warm on start"
            control={
              <SurfaceToggle
                label="Warm on start"
                checked={Boolean(value.warm_on_start)}
                onChange={(checked) => patch({ warm_on_start: checked })}
              />
            }
          />
          <SurfaceSettingRow
            label="Idle eviction (s)"
            control={
              <TextInput
                aria-label="Idle eviction seconds"
                type="number"
                value={Number(value.eviction_idle_seconds ?? 0)}
                onChange={(event) =>
                  patch({ eviction_idle_seconds: Number(event.target.value) })
                }
              />
            }
          />
        </SurfaceGroup>
      </Disclosure>
    </div>
  );
}
