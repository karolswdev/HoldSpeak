// Settings gadget bindings: one row per settings path, bound to the settings
// document and the writer's debounced `update`. They are plain functions,
// never components defined in render, which would remount and drop focus.
// Moved out of SettingsCore.tsx.
import type { SettingsResponse } from "../core-types";
import {
  CheckGadget,
  CycleGadget,
  GadgetRow,
  PropGadget,
  StepperGadget,
  StringGadget,
  type CycleOption,
} from "../../../desk/surface/gadgets";
import { SETTINGS_FOCUS_PATHS } from "./navigation";

/* HS-101 round 4 — the glass never wears wire keys: curated names
 * for the fields people actually meet, an acronym dictionary for the
 * rest. */
const FRIENDLY_FIELDS: Record<string, string> = {
  mlx_model: "MLX model",
  llama_cpp_model_path: "llama.cpp model file",
  profile_id: "Engine",
  max_total_latency_ms: "Latency budget",
  journal_retention: "Journal retention",
  n_ctx: "Context window",
};
const ACRONYMS: Record<string, string> = {
  Mlx: "MLX",
  Openai: "OpenAI",
  Api: "API",
  Url: "URL",
  Id: "ID",
  Ui: "UI",
  Llm: "LLM",
  Cpp: "C++",
  Ms: "ms",
  Env: "env",
  Ip: "IP",
  Db: "DB",
  Vad: "VAD",
  Mir: "MIR",
};

export function title(key: string) {
  const curated = FRIENDLY_FIELDS[key];
  if (curated) return curated;
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (value) => value.toUpperCase())
    .split(" ")
    .map((word) => ACRONYMS[word] ?? word)
    .join(" ");
}

export function settingsBindings(
  data: SettingsResponse,
  update: (path: string[], next: unknown) => void,
  highlight: string,
) {
  /* ── gadget bindings (plain function helpers — never components
        defined in render, which would remount and drop focus) ── */
  const val = (path: string[]): unknown =>
    path.reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object"
          ? (acc as Record<string, unknown>)[part]
          : undefined,
      data,
    );
  const hl = (path: string[]) => (SETTINGS_FOCUS_PATHS[highlight] ?? highlight) === path.join(".");
  const check = (path: string[], label: string, fact?: string) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
      controlWidth="short"
    >
      <CheckGadget
        variant="state"
        label={label}
        checked={Boolean(val(path))}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const str = (
    path: string[],
    label: string,
    opts?: { placeholder?: string; fact?: string },
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={opts?.fact}
      highlight={hl(path)}
      controlWidth="full"
    >
      <StringGadget
        label={label}
        value={val(path) == null ? "" : String(val(path))}
        placeholder={opts?.placeholder}
        onChange={(next) => update(path, next || null)}
      />
    </GadgetRow>
  );
  const num = (
    path: string[],
    label: string,
    opts?: { unit?: string; step?: number; min?: number; max?: number },
  ) => (
    <GadgetRow key={path.join(".")} label={label} highlight={hl(path)} controlWidth="short">
      <StepperGadget
        label={label}
        value={Number(val(path) ?? 0)}
        unit={opts?.unit}
        step={opts?.step}
        min={opts?.min}
        max={opts?.max}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const cyc = (
    path: string[],
    label: string,
    options: CycleOption[],
    fact?: string,
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
      controlWidth="standard"
    >
      <CycleGadget
        label={label}
        value={val(path) == null ? "" : String(val(path))}
        options={options}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const prop = (
    path: string[],
    label: string,
    opts?: { min?: number; max?: number; step?: number; fact?: string },
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={opts?.fact}
      highlight={hl(path)}
      controlWidth="full"
    >
      <PropGadget
        label={label}
        value={Number(val(path) ?? opts?.min ?? 0)}
        min={opts?.min}
        max={opts?.max}
        step={opts?.step}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const csv = (path: string[], label: string, fact = "comma-separated") => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
      controlWidth="full"
    >
      <StringGadget
        label={label}
        value={
          Array.isArray(val(path)) ? (val(path) as unknown[]).join(", ") : ""
        }
        onChange={(next) =>
          update(
            path,
            next
              .split(",")
              .map((part) => part.trim())
              .filter(Boolean),
          )
        }
      />
    </GadgetRow>
  );

  return { data, update, val, hl, check, str, num, cyc, prop, csv };
}

export type SettingsBindings = ReturnType<typeof settingsBindings>;
