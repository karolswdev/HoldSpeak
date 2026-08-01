// HS-101 round 5 / HS-111-01 — bespoke configuration components. A
// complex idea gets a component shaped like the idea, on the gadget kit:
//  - HotkeyCapture: a key is pressed, not typed — mapped to exactly the
//    key names the hub accepts (holdspeak/hotkey.py). Listening is
//    inverted video with a block cursor; a refusal lands in the Prefs
//    status bar (never row prose).
//  - RuntimeDestination: "where does voice typing run" — an mx radio
//    whose pick reveals only ITS gadgets (the GadTools pattern; the
//    pricing-card bays died in HS-111-01).
import { useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch, type JsonRecord } from "../../lib/api";
import { openSurfaceOr } from "../../desk/shell";
import {
  CheckGadget,
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  MxRadio,
  StepperGadget,
  StringGadget,
} from "../../desk/surface/gadgets";

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
  onRefuse,
}: {
  value: JsonRecord;
  onCommit: (next: { key: string; display: string }) => void;
  /** The refusal (names the accepted set) — lands in the status bar. */
  onRefuse?: (refusal: string) => void;
}) {
  const [listening, setListening] = useState(false);
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
        onRefuse?.(
          `${event.code} can't be a hold key: use a modifier (⌥ ⌃ ⌘ ⇧, left or right), ⇪, or F1–F12`,
        );
        return;
      }
      setListening(false);
      onCommit({ key: name, display: NAME_TO_DISPLAY[name] ?? name });
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [listening, onCommit, onRefuse]);
  const current = String(value.display || value.key || "unset");
  return (
    <GadgetGroup>
      <GadgetRow label="Push-to-talk key" fact="hold · release types">
        <button
          type="button"
          className={"gadget-keycap" + (listening ? " is-listening" : "")}
          aria-label={
            listening
              ? "Listening for the hold key. Esc cancels."
              : `Push-to-talk key: ${current}. Press to change.`
          }
          onClick={() => {
            onRefuse?.("");
            setListening((v) => !v);
          }}
        >
          {listening ? "" : current}
        </button>
      </GadgetRow>
    </GadgetGroup>
  );
}

/* ── the runtime: one destination, not thirteen boxes ──────────── */

type RuntimeMode = "auto" | "mlx" | "llama_cpp" | "openai_compatible" | "profile";

const MODE_LABEL: Record<RuntimeMode, string> = {
  auto: "Automatic",
  mlx: "This device · MLX",
  llama_cpp: "This device · llama.cpp",
  openai_compatible: "An endpoint",
  profile: "A saved destination",
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
        setProfiles((data.profiles ?? []).filter((row) => !row.deleted)),
      )
      .catch(() => setProfiles([]));
  }, []);
  const patch = (next: JsonRecord) => onCommit({ ...value, ...next });
  const choose = (next: string) => {
    if (next === "profile") {
      patch({ profile_id: String(profiles[0]?.id ?? "") || null });
    } else {
      patch({ backend: next, profile_id: null });
    }
  };
  const field = (label: string, key: string, placeholder?: string) => (
    <GadgetRow key={key} label={label}>
      <StringGadget
        label={label}
        value={String(value[key] ?? "")}
        placeholder={placeholder}
        onChange={(next) => patch({ [key]: next })}
      />
    </GadgetRow>
  );
  return (
    <div className="gadget-sheet">
      <GadgetGroup label="Runs on">
        <MxRadio
          label="Runs on"
          value={mode}
          onChange={choose}
          options={[
              { value: "auto", label: MODE_LABEL.auto },
              {
                value: "mlx",
                label: MODE_LABEL.mlx,
                children: field("MLX model", "mlx_model", "~/Models/mlx/…"),
              },
              {
                value: "llama_cpp",
                label: MODE_LABEL.llama_cpp,
                children: field(
                  "Model file",
                  "llama_cpp_model_path",
                  "~/Models/gguf/…",
                ),
              },
              {
                value: "openai_compatible",
                label: MODE_LABEL.openai_compatible,
                children: (
                  <>
                    {field(
                      "Endpoint URL",
                      "openai_compatible_base_url",
                      "http://…/v1",
                    )}
                    {field("Model", "openai_compatible_model")}
                    {field("API key env var", "openai_compatible_api_key_env")}
                  </>
                ),
              },
              {
                value: "profile",
                label: MODE_LABEL.profile,
                children: (
                  <GadgetRow label="Destination">
                    <CycleGadget
                      label="Saved destination"
                      value={String(value.profile_id ?? "")}
                      options={
                        profiles.length
                          ? profiles.map((row) => ({
                              value: String(row.id),
                              label: String(row.name ?? row.id),
                            }))
                          : [{ value: "", label: "No saved destinations" }]
                      }
                      onChange={(next) => patch({ profile_id: next || null })}
                    />
                    <Button
                      dense
                      variant="ghost"
                      onClick={() =>
                        openSurfaceOr("configure-runs-on", "/profiles")
                      }
                    >
                      Open Runs on
                    </Button>
                  </GadgetRow>
                ),
              },
          ]}
        />
      </GadgetGroup>
      <GadgetGroup label="Engine">
        <GadgetRow label="Context window" fact="tokens">
          <StepperGadget
            label="Context window"
            value={Number(value.n_ctx ?? 2048)}
            min={0}
            step={256}
            onChange={(next) => patch({ n_ctx: next })}
          />
        </GadgetRow>
        <GadgetRow label="Warm on start">
          <CheckGadget
            label="Warm on start"
            checked={Boolean(value.warm_on_start)}
            onChange={(checked) => patch({ warm_on_start: checked })}
          />
        </GadgetRow>
        <GadgetRow label="Idle eviction" fact="s">
          <StepperGadget
            label="Idle eviction seconds"
            value={Number(value.eviction_idle_seconds ?? 0)}
            min={0}
            step={30}
            onChange={(next) => patch({ eviction_idle_seconds: next })}
          />
        </GadgetRow>
      </GadgetGroup>
    </div>
  );
}
