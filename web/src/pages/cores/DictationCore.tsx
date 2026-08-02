// HS-95-05 — the Dictation surface's core, hosted anywhere.
// HS-98-02 — re-crafted native on the window material.
// HS-100-07 — Speak: the application opens ON the job (speak, see it
// land, judge it, teach it — trace B's loop is the entire front face);
// Journal and Blocks are the wings; Memory/Knowledge/Runtime/Hooks/
// Nudges and full readiness fold behind the one gear door
// (APPLICATION_LAYER_THESIS.md §1.1). Wire calls and verbs unchanged.
// HS-111-02 — the OS's dictation deck (audit §3): the cockpit is an
// instrument strip (TALK transport key, LED level meter, STATE
// register, etched readout cells); the Journal is a machine ledger
// (SurfaceLedger); the gear door is ONE gadget sheet; and every toast
// banner died into the footer receipt bar (the Prefs pattern).
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import { RuntimeDestination } from "./settingsBespoke";
import { Button } from "../../components/signal/Signal";
import { RunsOnPicker } from "../../desk/components/RunsOnPicker";
import { MicButton, type MicState } from "../../desk/components/MicButton";
import type { InferenceTarget } from "../../desk/api";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import {
  DICTATION_FAILURES,
  applicableActions,
  dictationFailure,
  type DictationFailure,
} from "../../lib/dictationRecovery";
import { useDurableDraft } from "../../lib/durableDraft";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  EditInPlace,
  SurfaceCode,
  SurfaceFacts,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceLibrary,
  SurfaceLibraryGhost,
  SurfaceLibraryTile,
  SurfaceSection,
  SurfaceState,
  SurfaceStreamDay,
} from "../../desk/surface/Surface";
import {
  CheckGadget,
  CycleGadget,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  LampGadget,
  LedMeter,
  PadGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
import {
  isSameStreamDay,
  presentValue,
  streamDate,
  streamDayLabel,
  streamTime,
} from "../../desk/surface/format";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";

const WINGS = [
  { id: "speak", label: "Speak" },
  { id: "journal", label: "Journal" },
  { id: "blocks", label: "Blocks" },
];

function readableValue(value: unknown): string {
  if (value && typeof value === "object") {
    const row = value as JsonRecord;
    for (const key of ["message", "detail", "warning", "error", "label"]) {
      if (typeof row[key] === "string" && row[key]) return row[key];
    }
    return JSON.stringify(value);
  }
  return String(value ?? "");
}

/* HS-111-02 — the ONE receipt channel: every outcome (save whisper,
   refusal, verdict, recovery note) lands as a token in the footer bar
   (the Prefs receipt/refusal pattern). The toast-banner species is
   dead in this program. */
type ReceiptTone = "ok" | "warn";
type Receipt = { text: string; tone: ReceiptTone };

const ReceiptContext = createContext<(text: string, tone?: ReceiptTone) => void>(
  () => undefined,
);

function useAnnounce() {
  return useContext(ReceiptContext);
}

function clockNow(): string {
  return new Date().toLocaleTimeString([], { hour12: false });
}

/* HS-111-02 — the gear door's Pipeline/Delivery sheet: axis-named
   check, fact tokens, the KB verb at the point of the fact. The
   readiness wire (config/target/depth/warnings) renders as equipment,
   never sentences. */
function Readiness() {
  const root = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const query = root ? `?project_root=${encodeURIComponent(root)}` : "";
  const resource = useResource<JsonRecord>(
    `/api/dictation/readiness${query}`,
    {},
  );
  const [pending, setPending] = useState(false);
  const [kbBusy, setKbBusy] = useState(false);
  const config = (resource.data.config ?? {}) as JsonRecord;
  const target = (resource.data.target ?? {}) as JsonRecord;
  const depth = (resource.data.depth ?? {}) as JsonRecord;
  const warnings = Array.isArray(resource.data.warnings)
    ? (resource.data.warnings as JsonRecord[])
    : [];
  const enabled = config.pipeline_enabled === true;
  const togglePipeline = async (next: boolean) => {
    setPending(true);
    try {
      await apiFetch("/api/settings", {
        method: "PUT",
        json: { dictation: { pipeline: { enabled: next } } },
      });
      await resource.reload();
    } finally {
      setPending(false);
    }
  };
  const createStarterKb = async () => {
    setKbBusy(true);
    try {
      await apiFetch(`/api/dictation/project-kb/starter${query}`, {
        method: "POST",
      });
      await resource.reload();
    } finally {
      setKbBusy(false);
    }
  };
  const confidencePct =
    typeof target.confidence === "number"
      ? Math.round((target.confidence as number) * 100)
      : null;
  const runs = Number(depth.runs ?? 0);
  const hasKbWarning = warnings.some((w) => w.code === "missing_project_kb");
  const otherWarnings = warnings.filter(
    (w) => w.code !== "pipeline_disabled" && w.code !== "missing_project_kb",
  );
  return (
    <SurfaceState
      loading={resource.loading}
      error={resource.error}
      onRetry={() => void resource.reload()}
    >
      <GadgetGroup label="Pipeline">
        <GadgetRow
          label="Dictation pipeline"
          fact={`${presentValue(config.backend) || "automatic"} · ${
            presentValue(config.max_total_latency_ms) || "—"
          } MS`}
        >
          <CheckGadget
            label="Dictation pipeline"
            checked={enabled}
            disabled={pending}
            onChange={(next) => void togglePipeline(next)}
          />
        </GadgetRow>
        {hasKbWarning ? (
          <GadgetRow label="Project KB" fact="MISSING">
            <Button dense loading={kbBusy} onClick={() => void createStarterKb()}>
              Create
            </Button>
          </GadgetRow>
        ) : null}
        {otherWarnings.map((warning, index) => (
          <p
            className="speak-token-line"
            data-tone="warn"
            key={String(warning.code ?? index)}
          >
            ⚠ {presentValue(warning.message) || readableValue(warning)}
          </p>
        ))}
      </GadgetGroup>
      <GadgetGroup label="Delivery">
        <GadgetRow label="Delivery target">
          <span className="speak-token-line">
            {target.label
              ? `${presentValue(target.label)}${
                  target.source === "hints" ? " · BROWSER BRIDGE" : ""
                }`
              : "—"}
          </span>
        </GadgetRow>
        {confidencePct !== null ? (
          <GadgetRow label="Confidence">
            <span className="speak-token-line">{confidencePct}%</span>
          </GadgetRow>
        ) : null}
        <GadgetRow label="Runs">
          <span className="speak-token-line">{runs}</span>
        </GadgetRow>
      </GadgetGroup>
      <FoldGadget title="Wire details">
        <SurfaceFacts value={config} />
        <SurfaceFacts value={target} />
        <SurfaceFacts value={depth} />
      </FoldGadget>
    </SurfaceState>
  );
}

/* HS-100-07/HS-111-02 — the footer bar: readiness tokens on the left
   (quiet when live, a warning that opens the door when not), the
   program's last receipt/refusal on the right. The one status line. */
function ReadinessLine({
  onOpenDoor,
  receipt,
}: {
  onOpenDoor: () => void;
  receipt: Receipt | null;
}) {
  const root = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const resource = useResource<JsonRecord>(
    `/api/dictation/readiness${root ? `?project_root=${encodeURIComponent(root)}` : ""}`,
    {},
  );
  const receiptSlot = receipt ? (
    <span
      className="speak-receipt"
      data-tone={receipt.tone === "warn" ? "warn" : undefined}
      role={receipt.tone === "warn" ? "alert" : "status"}
    >
      {receipt.text}
    </span>
  ) : null;
  if (resource.loading || resource.error) {
    return receiptSlot ? (
      <p className="speak-status">{receiptSlot}</p>
    ) : null;
  }
  const config = (resource.data.config ?? {}) as JsonRecord;
  const target = (resource.data.target ?? {}) as JsonRecord;
  const warnings = Array.isArray(resource.data.warnings)
    ? resource.data.warnings
    : [];
  const live = config.pipeline_enabled === true && warnings.length === 0;
  if (live) {
    const budget = config.max_total_latency_ms;
    return (
      <p className="speak-status" role="status">
        <span><span className="speak-status-dot is-live" aria-hidden="true" /> Pipeline live</span>
        {target.label ? <span>{"-> "}{presentValue(target.label)}</span> : null}
        {budget ? <span>{presentValue(budget)} ms</span> : null}
        {receiptSlot}
      </p>
    );
  }
  return (
    <p className="speak-status is-warn" role="status">
      <span><span className="speak-status-dot" aria-hidden="true" /> {config.pipeline_enabled === true
        ? `${warnings.length} ${warnings.length === 1 ? "warning" : "warnings"}`
        : "Pipeline off"}</span>
      <span>
        <button type="button" className="speak-status-fix" onClick={onOpenDoor}>
          Review
        </button>
      </span>
      {receiptSlot}
    </p>
  );
}

const STATE_TOKENS: { id: string; label: string }[] = [
  { id: "idle", label: "Idle" },
  { id: "listening", label: "Listening" },
  { id: "transcribing", label: "Transcribing" },
];

function SpeakFace() {
  const announce = useAnnounce();
  const {
    value: utterance,
    setDraft: setUtterance,
    recovered: utteranceRecovered,
    clearPersisted,
  } = useDurableDraft("dictation-dry-run");
  const [projectRoot, setProjectRoot] = useState(
    () => localStorage.getItem("holdspeak.projectRootOverride") ?? "",
  );
  const [result, setResult] = useState<JsonRecord | null>(null);
  const [error, setError] = useState("");
  const [failure, setFailure] = useState<DictationFailure | null>(null);
  const [busy, setBusy] = useState(false);
  const [correctionKind, setCorrectionKind] = useState("target");
  const [correctionValue, setCorrectionValue] = useState("");
  const [verdict, setVerdict] = useState<"" | "right" | "wrong">("");
  const [targets, setTargets] = useState<InferenceTarget[]>([]);
  const [targetId, setTargetId] = useState("this_machine");
  const [micState, setMicState] = useState<MicState>("idle");
  const [level, setLevel] = useState(0);
  // The strip's readout cells read the same wire the footer reads.
  const stripRoot = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const readiness = useResource<JsonRecord>(
    `/api/dictation/readiness${stripRoot ? `?project_root=${encodeURIComponent(stripRoot)}` : ""}`,
    {},
  );
  const readinessConfig = (readiness.data.config ?? {}) as JsonRecord;
  const readinessTarget = (readiness.data.target ?? {}) as JsonRecord;
  const pipelineOn = readinessConfig.pipeline_enabled === true;
  useEffect(() => {
    if (utteranceRecovered) announce("Draft restored");
  }, [utteranceRecovered, announce]);
  const run = async () => {
    setBusy(true);
    setError("");
    setFailure(null);
    setVerdict("");
    try {
      setResult(
        await apiFetch<JsonRecord>("/api/dictation/dry-run", {
          method: "POST",
          json: {
            utterance,
            ...(projectRoot ? { project_root: projectRoot } : {}),
          },
        }),
      );
      announce("");
      localStorage.setItem("holdspeak.projectRootOverride", projectRoot);
    } catch (reason) {
      const category = dictationFailure(reason);
      setFailure(category);
      const message = DICTATION_FAILURES[category].message;
      setError(message);
      announce(`⚠ ${message}`, "warn");
    } finally {
      setBusy(false);
    }
  };
  const actions = failure
    ? applicableActions(failure, { draftPresent: Boolean(utterance.trim()) })
    : [];
  useEffect(() => {
    if (!actions.includes("alternate_runs_on") || targets.length) return;
    let mounted = true;
    void apiFetch<{ targets?: InferenceTarget[] }>("/api/inference-targets")
      .then((result) => {
        if (mounted && Array.isArray(result.targets))
          setTargets(result.targets);
      })
      .catch(() => undefined);
    return () => {
      mounted = false;
    };
  }, [actions, targets.length]);
  const runElsewhere = async (id: string) => {
    setTargetId(id);
    try {
      await apiFetch("/api/settings", {
        method: "PUT",
        json: {
          dictation: {
            runtime: { profile_id: id === "this_machine" ? null : id },
          },
        },
      });
      await run();
    } catch (reason) {
      announce(`⚠ ${readableError(reason)}`, "warn");
    }
  };
  const keepDraft = async () => {
    if (!utterance.trim()) return;
    try {
      await apiFetch("/api/notes", {
        method: "POST",
        json: {
          title: "Retained dictation draft",
          body_markdown: utterance,
          tags: ["dictation"],
        },
      });
      clearPersisted();
      announce("Kept as a Note on your Desk.");
    } catch (reason) {
      announce(
        `⚠ The Note was not kept. Your draft remains editable. ${readableError(reason)}`,
        "warn",
      );
    }
  };
  const teach = async () => {
    setBusy(true);
    try {
      const journalId = result?.journal_id;
      await apiFetch(
        journalId !== undefined && journalId !== null
          ? `/api/dictation/journal/${encodeURIComponent(String(journalId))}/correct`
          : "/api/dictation/corrections",
        {
          method: "POST",
          json:
            journalId !== undefined && journalId !== null
              ? { kind: correctionKind, value: correctionValue }
              : {
                  kind: correctionKind,
                  text: utterance,
                  value: correctionValue,
                },
        },
      );
      announce("Taught · reaches similar dictations");
      setCorrectionValue("");
    } catch (reason) {
      announce(`⚠ Refused · ${readableError(reason)}`, "warn");
    } finally {
      setBusy(false);
    }
  };
  const activeState =
    micState === "busy"
      ? "transcribing"
      : micState === "listening"
        ? "listening"
        : "idle";
  return (
    <div className="speak-face">
      <div className="speak-strip" role="group" aria-label="Dictation deck">
        <MicButton
          variant="transport"
          draftScope="dictation-dry-run-voice"
          label="Hold to talk"
          onText={(text) => setUtterance(text)}
          onState={setMicState}
          onLevel={setLevel}
          onFailure={(category) =>
            announce(`⚠ ${DICTATION_FAILURES[category].message}`, "warn")
          }
        />
        <LedMeter label="Level" value={level} scanning={micState === "busy"} />
        <span className="speak-register" aria-label="Dictation state">
          <span className="speak-register-axis">State</span>
          {STATE_TOKENS.map((token) => (
            <span
              key={token.id}
              className="speak-register-token"
              data-active={activeState === token.id || undefined}
            >
              {token.label}
            </span>
          ))}
        </span>
        <span className="speak-cells">
          <span className="speak-cell">
            <span className="speak-cell-label">Pipeline</span>
            <span className="speak-cell-value">
              <LampGadget
                label={pipelineOn ? "Live" : "Off"}
                on={pipelineOn}
                tone={pipelineOn ? "ok" : "warn"}
              />
            </span>
          </span>
          <span className="speak-cell">
            <span className="speak-cell-label">{"-> Target"}</span>
            <span className="speak-cell-value">
              {presentValue(readinessTarget.label) || "—"}
            </span>
          </span>
          <span className="speak-cell">
            <span className="speak-cell-label">Budget</span>
            <span className="speak-cell-value">
              {presentValue(readinessConfig.max_total_latency_ms)
                ? `${presentValue(readinessConfig.max_total_latency_ms)} MS`
                : "—"}
            </span>
          </span>
        </span>
      </div>
      <div className="speak-well">
        <PadGadget
          label="Utterance"
          value={utterance}
          onChange={setUtterance}
          mic={false}
          placeholder="UTTERANCE"
        />
      </div>
      <div className="surface-actions speak-run-row">
        <Button
          variant="primary"
          loading={busy}
          disabled={!utterance.trim()}
          onClick={run}
        >
          {error && actions.includes("retry") ? "Retry dry test" : "Run dry test"}
        </Button>
        <span className="speak-grounding">
          <span className="speak-grounding-label">Grounding</span>
          <StringGadget
            label="Project root: optional grounding scope, saved only on this device"
            placeholder="project root"
            value={projectRoot}
            onChange={setProjectRoot}
          />
        </span>
      </div>
      {error ? (
        <div className="surface-actions">
          {actions.includes("copy") ? (
            <Button
              dense
              onClick={() => void navigator.clipboard.writeText(utterance)}
            >
              Copy
            </Button>
          ) : null}
          {actions.includes("keep_as_note") ? (
            <Button dense onClick={keepDraft}>
              Keep as Note
            </Button>
          ) : null}
          {actions.includes("setup") ? (
            <Button
              dense
              variant="secondary"
              onClick={() => openSurfaceOr("configure-setup", "/setup")}
            >
              Setup
            </Button>
          ) : null}
        </div>
      ) : null}
      {error && actions.includes("alternate_runs_on") && targets.length ? (
        <RunsOnPicker
          targets={targets}
          selectedId={targetId}
          onChange={(id) => void runElsewhere(id)}
          disabled={busy}
        />
      ) : null}
      {result ? (
        <section className="speak-result" aria-label="Pipeline result">
          <SurfaceCode>{`FINAL_TEXT: ${String(result.final_text ?? result.text ?? result.output ?? "")}`}</SurfaceCode>
          <div className="speak-result-facts">
            {result.intent ? <span>INTENT {String(result.intent)}</span> : null}
            {result.total_ms ? (
              <span>LATENCY {String(result.total_ms)} MS</span>
            ) : null}
            {result.target_profile ? (
              <span>TARGET {String(result.target_profile)}</span>
            ) : null}
          </div>
          <div
            className="surface-actions speak-result-verdict"
            aria-label="Rate this result"
          >
            <Button
              dense
              onClick={() => {
                setVerdict("right");
                announce("Marked OK · no correction written");
              }}
            >
              OK
            </Button>
            <Button dense variant="ghost" onClick={() => setVerdict("wrong")}>
              Wrong
            </Button>
          </div>
          {verdict === "wrong" ? (
            <div
              className="speak-correct"
              role="group"
              aria-label="Correct this result"
            >
              <GadgetRow label="Field">
                <CycleGadget
                  label="Correction field"
                  value={correctionKind}
                  options={[
                    { value: "target", label: "Delivery target" },
                    { value: "intent", label: "Intent" },
                  ]}
                  onChange={setCorrectionKind}
                />
              </GadgetRow>
              <GadgetRow label="Value">
                <StringGadget
                  label="Correct value"
                  value={correctionValue}
                  onChange={setCorrectionValue}
                />
              </GadgetRow>
              <div className="surface-actions">
                <Button
                  dense
                  loading={busy}
                  disabled={!correctionValue.trim()}
                  aria-label="Teach correction"
                  onClick={teach}
                >
                  Teach
                </Button>
              </div>
            </div>
          ) : null}
          <FoldGadget title="Raw trace">
            <SurfaceCode>{JSON.stringify(result, null, 2)}</SurfaceCode>
          </FoldGadget>
        </section>
      ) : null}
    </div>
  );
}

/** HS-101 B4 — Blocks reads like a library: the injection text IS
 * the tile's face, the name and spoken matches ride the spine,
 * create is a ghost tile in the shelf. Edits land on the material.
 * HS-111-02 — cosmetic refit: mono tile names, CycleGadget scope,
 * mics on every draft input, refusals in the footer bar. */
function blockSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function Blocks() {
  const announce = useAnnounce();
  const [scope, setScope] = useState("global");
  const resource = useResource<JsonRecord>(
    `/api/dictation/blocks?scope=${scope}`,
    {},
  );
  const rows = asRows(
    (resource.data.document as JsonRecord | undefined)?.blocks,
    [],
  );
  const [drafting, setDrafting] = useState(false);
  const [draft, setDraft] = useState({ name: "", examples: "", injection: "" });
  const save = async (row: Record<string, unknown>, patch: JsonRecord) => {
    try {
      await apiFetch(
        `/api/dictation/blocks/${encodeURIComponent(String(row.id))}?scope=${scope}`,
        { method: "PUT", json: { block: { ...row, ...patch } } },
      );
      await resource.reload();
    } catch (error) {
      announce(`⚠ ${readableError(error)}`, "warn");
    }
  };
  const remove = async (row: Record<string, unknown>) => {
    try {
      await apiFetch(
        `/api/dictation/blocks/${encodeURIComponent(String(row.id))}?scope=${scope}`,
        { method: "DELETE" },
      );
      await resource.reload();
    } catch (error) {
      announce(`⚠ ${readableError(error)}`, "warn");
    }
  };
  const create = async () => {
    const name = draft.name.trim();
    if (!name) return;
    try {
      await apiFetch(`/api/dictation/blocks?scope=${scope}`, {
        method: "POST",
        json: {
          block: {
            id: blockSlug(name),
            description: name,
            match: {
              examples: draft.examples
                .split(/[,\n]/)
                .map((part) => part.trim())
                .filter(Boolean),
            },
            inject: { mode: "replace", template: draft.injection },
          },
        },
      });
      setDraft({ name: "", examples: "", injection: "" });
      setDrafting(false);
      await resource.reload();
    } catch (error) {
      announce(`⚠ ${readableError(error)}`, "warn");
    }
  };
  return (
    <SurfaceSection className="speak-blocks">
      <SurfaceLibrary
        count={rows.length}
        countLabel={rows.length === 1 ? "block" : "blocks"}
        controls={
          <CycleGadget
            label="Block scope"
            value={scope}
            options={[
              { value: "global", label: "Global" },
              { value: "project", label: "Project" },
            ]}
            onChange={setScope}
          />
        }
      >
        <SurfaceState
          loading={resource.loading}
          error={resource.error}
          onRetry={() => void resource.reload()}
        >
          {rows.map((row, index) => {
            const match =
              row.match && typeof row.match === "object"
                ? (row.match as JsonRecord)
                : {};
            const examples = Array.isArray(match.examples)
              ? match.examples
              : [];
            const inject =
              row.inject && typeof row.inject === "object"
                ? (row.inject as JsonRecord)
                : {};
            const mode = String(inject.mode ?? "replace");
            return (
              <SurfaceLibraryTile
                key={rowId(row, index)}
                face={
                  <EditInPlace
                    value={String(inject.template ?? "")}
                    label={`${String(row.description ?? row.id)} template`}
                    multiline
                    onCommit={(next) =>
                      void save(row, { inject: { ...inject, template: next } })
                    }
                  />
                }
                name={
                  <EditInPlace
                    value={String(row.description ?? row.id ?? "Block")}
                    label={`${String(row.id)} name`}
                    onCommit={(next) => void save(row, { description: next })}
                  />
                }
                lamp={<span className="surface-mode">{mode}</span>}
                says={
                  examples.length
                    ? examples.slice(0, 3).map((say, sayIndex) => (
                        <span className="surface-say" key={sayIndex}>
                          {String(say)}
                        </span>
                      ))
                    : null
                }
                verbs={
                  <ConfirmVerb
                    label="Delete"
                    confirmLabel="Delete?"
                    onConfirm={() => void remove(row)}
                  />
                }
              />
            );
          })}
          {drafting ? (
            <li className="surface-tile surface-tile-drafting">
              <div className="surface-tile-face">
                <div className="desk-mic-row">
                  <PadGadget
                    label="Injection text"
                    placeholder="What this block injects"
                    rows={4}
                    value={draft.injection}
                    onChange={(next) =>
                      setDraft({ ...draft, injection: next })
                    }
                  />
                </div>
              </div>
              <div className="surface-tile-spine">
                <StringGadget
                  label="Block name"
                  placeholder="Name"
                  value={draft.name}
                  onChange={(name) => setDraft({ ...draft, name })}
                />
                <StringGadget
                  label="Spoken matches, comma separated"
                  placeholder="Say: standup notes, stand up"
                  value={draft.examples}
                  onChange={(examples) => setDraft({ ...draft, examples })}
                />
                <div className="surface-actions">
                  <Button
                    dense
                    variant="primary"
                    disabled={!draft.name.trim()}
                    onClick={() => void create()}
                  >
                    Create
                  </Button>
                  <Button dense variant="ghost" onClick={() => setDrafting(false)}>
                    Cancel
                  </Button>
                </div>
              </div>
            </li>
          ) : (
            <SurfaceLibraryGhost
              label="New block"
              hint={
                rows.length ? undefined : "No routing blocks on this scope yet"
              }
              onCreate={() => setDrafting(true)}
            />
          )}
        </SurfaceState>
      </SurfaceLibrary>
    </SurfaceSection>
  );
}

/* HS-111-02 — correction memory is a machine table: KIND | GIST |
   VALUE | REACH, the arming × per row. REACH is the wire's `similar`
   count — what makes the memory legible as equipment. */
function Memory() {
  const resource = useResource<JsonRecord>("/api/dictation/corrections", {});
  const digest = useResource<JsonRecord>("/api/dictation/learning-digest", {});
  const rows = asRows(resource.data, ["items", "corrections"]);
  const remove = async (row: Record<string, unknown>) => {
    await apiFetch(
      `/api/dictation/corrections/${encodeURIComponent(String(row.id))}`,
      { method: "DELETE" },
    );
    await resource.reload();
  };
  return (
    <>
      <GadgetGroup label="Correction memory">
        <SurfaceState
          loading={resource.loading}
          error={resource.error}
          empty={!rows.length}
          emptyLabel="Nothing learned yet"
          emptyGlyph="◈"
          onRetry={() => void resource.reload()}
        >
          <GadgetTable
            head={["Kind", "Gist", "Value", "Reach"]}
            rows={rows.map((row) => [
              String(row.kind ?? "—"),
              String(row.gist ?? "—"),
              presentValue(row.value ?? row.replacement) || "—",
              presentValue(row.similar) || "—",
            ])}
            verbs={(index) => (
              <ConfirmVerb
                label="×"
                confirmLabel="Forget?"
                onConfirm={() => void remove(rows[index])}
              />
            )}
          />
        </SurfaceState>
      </GadgetGroup>
      <GadgetGroup label="Learning digest">
        <SurfaceState
          loading={digest.loading}
          error={digest.error}
          onRetry={() => void digest.reload()}
        >
          <LearningDigestFacts digest={digest.data} />
        </SurfaceState>
      </GadgetGroup>
    </>
  );
}

/* HS-111-02 — the digest is a fact token row, never a sentence:
   WEEK · TAUGHT n · CORRECTED n · REACHED n (empty: WEEK · —). */
function LearningDigestFacts({ digest }: { digest: JsonRecord }) {
  const totals = (digest.totals ?? {}) as JsonRecord;
  const made = Number(totals.corrections_made ?? 0);
  const corrected = Number(totals.dictations_corrected ?? 0);
  const nudged = Number(totals.similar_nudged ?? 0);
  const topBlocks = asRows(digest, ["by_block"]).slice(0, 3);
  if (!made && !corrected) {
    // The empty week is an honest zero token, never a sentence.
    return <p className="speak-token-line">WEEK · TAUGHT 0</p>;
  }
  return (
    <>
      <p className="speak-token-line">
        {[
          "WEEK",
          `TAUGHT ${made}`,
          corrected ? `CORRECTED ${corrected}` : "",
          nudged ? `REACHED ${nudged}` : "",
        ]
          .filter(Boolean)
          .join(" · ")}
      </p>
      {topBlocks.length ? (
        <SurfaceFacts
          value={Object.fromEntries(
            topBlocks.map((row) => [
              String(row.block_id ?? "block"),
              row.count,
            ]),
          )}
        />
      ) : null}
    </>
  );
}

/* HS-102-06 — Knowledge is `{kb: {<KEY>: <string|null>, ...}}`
   (`/api/dictation/project-kb`, validated `[A-Za-z_][A-Za-z0-9_]*`
   keys) — a facts glossary, not free text. HS-111-02: the glossary is
   a GadgetTable (KEY | VALUE, EditInPlace values, ghost +ADD row of
   StringGadgets — mics included by the kit); the key refusal and the
   save whisper land in the footer bar. Instructions binds to the
   primary `.hs/instructions.md` file. */
function Knowledge() {
  const announce = useAnnounce();
  const [root, setRoot] = useState(
    () => localStorage.getItem("holdspeak.projectRootOverride") ?? "",
  );
  const query = root ? `?project_root=${encodeURIComponent(root)}` : "";
  const kb = useResource<JsonRecord>(`/api/dictation/project-kb${query}`, {});
  const hs = useResource<JsonRecord>(`/api/dictation/project-hs${query}`, {});
  const [drafting, setDrafting] = useState(false);
  const [draftKey, setDraftKey] = useState("");
  const [draftValue, setDraftValue] = useState("");
  const kbFacts = (kb.data.kb ?? {}) as Record<string, unknown>;
  const kbEntries = Object.entries(kbFacts);
  const instructionsFile = (
    ((hs.data.files ?? {}) as JsonRecord)["instructions.md"] ?? {}
  ) as JsonRecord;
  const putKb = async (next: Record<string, unknown>) => {
    announce("Saving…");
    try {
      await apiFetch(`/api/dictation/project-kb${query}`, {
        method: "PUT",
        json: { kb: next },
      });
      announce(`Written ${clockNow()}`);
      await kb.reload();
    } catch (error) {
      announce(`⚠ ${readableError(error)}`, "warn");
    }
  };
  const setFact = (key: string, value: string) =>
    void putKb({ ...kbFacts, [key]: value });
  const forgetFact = (key: string) => {
    const next = { ...kbFacts };
    delete next[key];
    void putKb(next);
  };
  const addFact = () => {
    const key = draftKey.trim();
    if (!key || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) {
      announce("⚠ Refused · key format A-Z _ 0-9, letter first", "warn");
      return;
    }
    void putKb({ ...kbFacts, [key]: draftValue.trim() });
    setDraftKey("");
    setDraftValue("");
    setDrafting(false);
  };
  const saveInstructions = async (content: string) => {
    announce("Saving…");
    try {
      await apiFetch(`/api/dictation/project-hs${query}`, {
        method: "PUT",
        json: { files: { "instructions.md": content } },
      });
      announce(`Written ${clockNow()}`);
      await hs.reload();
    } catch (error) {
      announce(`⚠ ${readableError(error)}`, "warn");
    }
  };
  return (
    <>
      <GadgetGroup label="Project scope">
        <GadgetRow label="Project root">
          <StringGadget
            label="Project root"
            placeholder="this device's working directory"
            value={root}
            onChange={setRoot}
          />
          <Button
            dense
            onClick={() => {
              localStorage.setItem("holdspeak.projectRootOverride", root);
              void kb.reload();
              void hs.reload();
            }}
          >
            Use
          </Button>
        </GadgetRow>
      </GadgetGroup>
      <GadgetGroup label="Knowledge">
        <GadgetTable
          head={["Key", "Value"]}
          rows={kbEntries.map(([key, value]) => [
            key,
            <EditInPlace
              key={key}
              value={String(value ?? "") || "(empty) click to add"}
              label={`${key} value`}
              onCommit={(next) => setFact(key, next)}
            />,
          ])}
          verbs={(index) => (
            <ConfirmVerb
              label="×"
              confirmLabel="Forget?"
              onConfirm={() => forgetFact(kbEntries[index][0])}
            />
          )}
          onAdd={drafting ? undefined : () => setDrafting(true)}
        />
        {drafting ? (
          <div className="surface-actions">
            <StringGadget
              label="Fact name"
              placeholder="BLUEBIRD"
              value={draftKey}
              onChange={setDraftKey}
            />
            <StringGadget
              label="Fact value"
              placeholder="the codename for…"
              value={draftValue}
              onChange={setDraftValue}
            />
            <Button
              dense
              variant="primary"
              disabled={!draftKey.trim()}
              onClick={addFact}
            >
              Add
            </Button>
            <Button
              dense
              variant="ghost"
              onClick={() => {
                setDrafting(false);
                setDraftKey("");
                setDraftValue("");
              }}
            >
              Cancel
            </Button>
          </div>
        ) : null}
      </GadgetGroup>
      <GadgetGroup label="Instructions">
        <EditInPlace
          value={
            String(instructionsFile.content ?? "") ||
            "No instructions yet. Click to add."
          }
          label="Project instructions"
          multiline
          onCommit={(next) => void saveInstructions(next)}
        />
      </GadgetGroup>
    </>
  );
}

/** HS-111-02 — the Journal is a machine ledger (audit §3.2): one mono
 * line per dictation, columns time/transcript/dest/ms/taught, click a
 * row to open it in place (the cursor line). Day bands stay. */
function Journal() {
  const resource = useResource<JsonRecord>(
    "/api/dictation/journal?limit=200",
    {},
  );
  const rows = asRows(resource.data, ["items"]);
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState("");
  const [replays, setReplays] = useState<Record<string, JsonRecord>>({});
  const filtered = rows.filter(
    (row) =>
      !query ||
      String(row.transcript ?? "")
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const today = new Date();
  const todayCount = rows.filter((row) => {
    const date = streamDate(row.created_at ?? row.timestamp);
    return date != null && isSameStreamDay(date, today);
  }).length;
  const taughtCount = rows.filter((row) => {
    if (!row.corrected) return false;
    const date = streamDate(row.created_at ?? row.timestamp);
    return date != null && isSameStreamDay(date, today);
  }).length;
  const days: { label: string; rows: typeof filtered }[] = [];
  for (const row of filtered) {
    const label = streamDayLabel(streamDate(row.created_at ?? row.timestamp));
    const bucket = days.at(-1);
    if (bucket && bucket.label === label) bucket.rows.push(row);
    else days.push({ label, rows: [row] });
  }
  const remove = async (target: Record<string, unknown> | "all") => {
    await apiFetch(
      target === "all"
        ? "/api/dictation/journal"
        : `/api/dictation/journal/${encodeURIComponent(String(target.id))}`,
      { method: "DELETE" },
    );
    await resource.reload();
  };
  const replay = async (row: Record<string, unknown>) => {
    const result = await apiFetch<JsonRecord>(
      `/api/dictation/journal/${encodeURIComponent(String(row.id))}/replay`,
      { method: "POST" },
    );
    setReplays((current) => ({ ...current, [String(row.id)]: result }));
  };
  const editTranscript = async (
    row: Record<string, unknown>,
    next: string,
  ) => {
    await apiFetch(
      `/api/dictation/journal/${encodeURIComponent(String(row.id))}`,
      { method: "PUT", json: { transcript: next } },
    );
    await resource.reload();
  };
  return (
    <SurfaceSection>
      <SurfaceLedger
        count={`Today ${todayCount} · Taught ${taughtCount}`}
        controls={
          <>
            <StringGadget
              label="Search the journal"
              placeholder="search"
              value={query}
              onChange={setQuery}
            />
            <ConfirmVerb
              label="Clear"
              confirmLabel="Clear all?"
              disabled={!rows.length}
              onConfirm={() => void remove("all")}
            />
          </>
        }
      >
        <SurfaceState
          loading={resource.loading}
          error={resource.error}
          empty={!filtered.length}
          emptyLabel="No dictations on this device"
          emptyGlyph="✎"
          onRetry={() => void resource.reload()}
        >
          {days.map((day) => (
            <SurfaceStreamDay key={day.label} label={day.label}>
              {day.rows.map((row, index) => {
                const id = String(row.id ?? rowId(row, index));
                const replayResult = replays[id];
                const replayAfter =
                  replayResult?.after && typeof replayResult.after === "object"
                    ? (replayResult.after as JsonRecord)
                    : replayResult;
                const replayText = String(replayAfter?.final_text ?? "");
                const learning =
                  row.learning && typeof row.learning === "object"
                    ? (row.learning as JsonRecord)
                    : null;
                const similar = Number(learning?.similar ?? 0);
                const destination =
                  presentValue(row.target_profile) || presentValue(row.intent);
                const took = Number(row.total_ms ?? 0);
                return (
                  <SurfaceLedgerRow
                    key={rowId(row, index)}
                    time={streamTime(
                      streamDate(row.created_at ?? row.timestamp),
                    )}
                    primary={String(row.transcript ?? "")}
                    open={openId === id}
                    onToggle={() => setOpenId(openId === id ? "" : id)}
                    cells={
                      <>
                        <span className="surface-ledger-cell surface-ledger-dest">
                          {destination ? `→ ${destination}` : ""}
                        </span>
                        <span className="surface-ledger-cell surface-ledger-ms">
                          {took > 0 ? `${Math.round(took)} ms` : ""}
                        </span>
                        <span className="surface-ledger-cell">
                          {row.corrected ? (
                            <span className="surface-learned">
                              ✓ taught
                              {learning?.matched && similar > 0
                                ? ` · from ${similar} similar`
                                : ""}
                            </span>
                          ) : null}
                        </span>
                      </>
                    }
                  >
                    <EditInPlace
                      value={String(row.transcript ?? "")}
                      label="transcript"
                      multiline
                      onCommit={(next) => void editTranscript(row, next)}
                    />
                    <div className="surface-row-verbs">
                      <Button dense onClick={() => void replay(row)}>
                        Replay
                      </Button>
                      <Button
                        dense
                        variant="ghost"
                        onClick={() =>
                          void navigator.clipboard.writeText(
                            String(row.transcript ?? ""),
                          )
                        }
                      >
                        Copy
                      </Button>
                      <ConfirmVerb
                        label="Delete"
                        confirmLabel="Delete?"
                        onConfirm={() => void remove(row)}
                      />
                    </div>
                    {replayResult ? (
                      <div className="surface-preview" role="status">
                        <span className="surface-preview-label">
                          Replay — preview only
                        </span>
                        <p>
                          {replayText ||
                            "The replay completed without text."}
                        </p>
                        <div className="surface-actions">
                          <Button
                            dense
                            variant="ghost"
                            disabled={!replayText}
                            onClick={() =>
                              void navigator.clipboard.writeText(replayText)
                            }
                          >
                            Copy result
                          </Button>
                        </div>
                      </div>
                    ) : null}
                  </SurfaceLedgerRow>
                );
              })}
            </SurfaceStreamDay>
          ))}
        </SurfaceState>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

/* HS-102-06 — the runtime knobs live in exactly ONE composed place:
   `RuntimeDestination` (settingsBespoke.tsx), the same component
   Settings uses for this exact same `dictation.runtime` value. This
   face embeds it rather than re-stating Backend/Runs on/Latency
   budget as a third label-over-Select stack. Saves on change,
   debounced; the receipt lands in the footer bar (HS-111-02). */
function Runtime() {
  const announce = useAnnounce();
  const settings = useResource<JsonRecord>("/api/settings", {});
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(saveTimer.current), []);
  const runtime = ((settings.data.dictation as JsonRecord | undefined)
    ?.runtime ?? {}) as JsonRecord;
  const save = async (dictation: JsonRecord) => {
    announce("Saving…");
    try {
      await apiFetch("/api/settings", { method: "PUT", json: { dictation } });
      announce(`Written ${clockNow()}`);
    } catch (error) {
      announce(`⚠ ${readableError(error)}`, "warn");
    }
  };
  const patch = (next: JsonRecord) => {
    const dictation = {
      ...(settings.data.dictation as JsonRecord),
      runtime: { ...runtime, ...next },
    };
    settings.setData({ ...settings.data, dictation });
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => void save(dictation), 700);
  };
  return (
    <GadgetGroup label="Dictation runtime">
      <RuntimeDestination value={runtime} onCommit={patch} />
    </GadgetGroup>
  );
}

/* HS-111-02 — Hooks is a designed face, not a JSON dump: the capture
   check, one fact row per agent destination with a SET/— chip (a
   recent captured session = SET), the raw wire behind Raw trace. */
function Hooks() {
  const [capture, setCapture] = useState(false);
  const resource = useResource<JsonRecord>(
    `/api/dictation/agent-hooks?capture_messages=${capture}`,
    {},
  );
  const destinations = (resource.data.destinations ?? {}) as JsonRecord;
  const agents = (resource.data.agents ?? {}) as JsonRecord;
  const chip = (agent: string) => {
    const info = agents[agent] as JsonRecord | undefined;
    const set = Boolean(info && info.latest_session);
    return (
      <span className="gadget-chip" data-set={set || undefined}>
        {set ? "SET" : "—"}
      </span>
    );
  };
  return (
    <GadgetGroup label="Automation hooks">
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <GadgetRow label="Capture messages" fact="hook template option">
          <CheckGadget
            label="Capture messages"
            checked={capture}
            onChange={setCapture}
          />
        </GadgetRow>
        <GadgetRow label="Claude" fact={presentValue(destinations.claude)}>
          {chip("claude")}
        </GadgetRow>
        <GadgetRow label="Codex" fact={presentValue(destinations.codex)}>
          {chip("codex")}
        </GadgetRow>
        <FoldGadget title="Raw trace">
          <SurfaceCode>{JSON.stringify(resource.data, null, 2)}</SurfaceCode>
        </FoldGadget>
      </SurfaceState>
    </GadgetGroup>
  );
}

/* HS-111-02 — nudges are ledger rows: HH:MM · domain · KIND with the
   USE / DISMISS verbs. The surveillance sentence died. */
function Nudges() {
  const resource = useResource<JsonRecord>("/api/activity/nudges?limit=8", {});
  const rows = asRows(resource.data, ["nudges", "items"]);
  const act = async (
    row: Record<string, unknown>,
    action: "select" | "dismiss",
  ) => {
    await apiFetch(
      action === "select"
        ? "/api/activity/nudges/select"
        : `/api/activity/nudges/${encodeURIComponent(String(row.id ?? row.key))}/dismiss`,
      {
        method: "POST",
        json: action === "select" ? { record_id: row.record_id ?? row.id } : {},
      },
    );
    await resource.reload();
  };
  const token = (row: Record<string, unknown>): string => {
    const citation = (
      Array.isArray(row.citations) ? row.citations[0] : null
    ) as JsonRecord | null;
    const time = streamTime(
      streamDate(citation?.last_seen_at ?? row.window_since),
    );
    const where =
      presentValue(citation?.domain) ||
      presentValue(row.title ?? row.text) ||
      "recent work";
    const kind = String(
      citation?.entity_type ?? row.kind ?? "activity",
    ).toUpperCase();
    return [time, where, kind].filter(Boolean).join(" · ");
  };
  return (
    <GadgetGroup label="Activity nudges">
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        empty={!rows.length}
        emptyLabel="No recent activity to cite"
        emptyGlyph="⌁"
        onRetry={() => void resource.reload()}
      >
        {rows.map((row, index) => (
          <div className="speak-nudge-row" key={rowId(row, index)}>
            <span className="speak-nudge-token">{token(row)}</span>
            <span className="surface-row-verbs">
              <Button dense onClick={() => void act(row, "select")}>
                Use
              </Button>
              <Button
                dense
                variant="ghost"
                onClick={() => void act(row, "dismiss")}
              >
                Dismiss
              </Button>
            </span>
          </div>
        ))}
      </SurfaceState>
    </GadgetGroup>
  );
}

export function DictationCore({ hero, scope, scopeLabel }: CoreProps) {
  const [view, setView] = useState("speak");
  const [doorOpen, setDoorOpen] = useState(false);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const announce = useCallback((text: string, tone: ReceiptTone = "ok") => {
    setReceipt(text ? { text, tone } : null);
  }, []);
  useWindowWings(
    <SurfaceWings
      wings={WINGS}
      active={doorOpen ? "" : view}
      onChange={(id) => {
        setDoorOpen(false);
        setView(id);
      }}
      door="Configure dictation"
      doorOpen={doorOpen}
      onDoor={() => setDoorOpen((v) => !v)}
    />,
    [view, doorOpen],
  );
  const active = doorOpen ? "configure" : view;
  const current = useMemo(
    () =>
      ({
        speak: <SpeakFace />,
        journal: <Journal />,
        blocks: <Blocks />,
        configure: <Configure />,
      })[active],
    [active],
  );
  return (
    <>
      {hero ? hero(null) : null}
      {scope ? (
        <p className="desk-scope-chip">
          <span aria-hidden="true">⌁</span> About {scopeLabel || scope}
        </p>
      ) : null}
      <ReceiptContext.Provider value={announce}>
        {current}
      </ReceiptContext.Provider>
      <ReadinessLine onOpenDoor={() => setDoorOpen(true)} receipt={receipt} />
    </>
  );
}

/* HS-100-07 — the one door: everything that is configuration
   (readiness diagnostics, memory, knowledge, runtime, hooks, nudges)
   stacked behind the gear. HS-111-02: the stack is ONE gadget sheet
   on the window material — full width, 26px rows, no settings mile. */
function Configure() {
  return (
    <div className="surface-door">
      <Readiness />
      <Memory />
      <Knowledge />
      <Runtime />
      <Hooks />
      <Nudges />
    </div>
  );
}
