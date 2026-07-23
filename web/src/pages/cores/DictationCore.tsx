// HS-95-05 — the Dictation surface's core, hosted anywhere.
// HS-98-02 — re-crafted native on the window material.
// HS-100-07 — Speak: the application opens ON the job (speak, see it
// land, judge it, teach it — trace B's loop is the entire front face);
// Journal and Blocks are the wings; Memory/Knowledge/Runtime/Hooks/
// Nudges and full readiness fold behind the one gear door
// (APPLICATION_LAYER_THESIS.md §1.1). Wire calls and verbs unchanged.
import { useEffect, useMemo, useRef, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
import { RuntimeDestination } from "./settingsBespoke";
import {
  Button,
  Disclosure,
  Field,
  InlineMessage,
  Select,
  StatusPill,
  TextArea,
  TextInput,
} from "../../components/signal/Signal";
import { RunsOnPicker } from "../../desk/components/RunsOnPicker";
import { MicButton } from "../../desk/components/MicButton";
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
  SurfaceColumns,
  SurfaceFacts,
  SurfaceGroup,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceSettingRow,
  SurfaceLibrary,
  SurfaceLibraryGhost,
  SurfaceLibraryTile,
  SurfaceState,
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
  SurfaceToggle,
} from "../../desk/surface/Surface";
import {
  humanTime,
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

/* HS-102-06 — the two raw dumps compose into honest sentences: what
   runs, where, at what budget, and why (with the remedy AT the point
   of the state, not a disconnected banner). Wire fields stay
   reachable behind a Disclosure for anyone who needs them. */
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
  const deliveryLine = target.label
    ? `Last typed into ${presentValue(target.label)}${
        target.source === "hints" ? " via the browser bridge" : ""
      }${confidencePct !== null ? ` · ${confidencePct}% confidence` : ""}`
    : "No delivery detected yet";
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
      <SurfaceGroup label="Pipeline">
        <SurfaceSettingRow
          label={
            enabled
              ? "Types automatically as you speak"
              : "Off — speaking here still works on paper"
          }
          description={`${presentValue(config.backend) || "automatic"} · budget ${presentValue(config.max_total_latency_ms) || "—"} ms`}
          control={
            <SurfaceToggle
              label="Dictation pipeline"
              checked={enabled}
              disabled={pending}
              onChange={(next) => void togglePipeline(next)}
            />
          }
        />
        {hasKbWarning ? (
          <SurfaceSettingRow
            label="Project KB file is missing"
            description="A starter file lets dictation ground on this project's facts"
            control={
              <Button dense loading={kbBusy} onClick={() => void createStarterKb()}>
                Create it
              </Button>
            }
          />
        ) : null}
        {otherWarnings.map((warning, index) => (
          <p className="surface-fact-line" key={String(warning.code ?? index)}>
            {presentValue(warning.message) || readableValue(warning)}
          </p>
        ))}
      </SurfaceGroup>
      <SurfaceGroup label="Delivery">
        <SurfaceSettingRow
          label={deliveryLine}
          description={runs > 0 ? `${runs} runs so far` : "No runs yet"}
          control={null}
        />
      </SurfaceGroup>
      <Disclosure title="Wire details">
        <SurfaceFacts value={config} />
        <SurfaceFacts value={target} />
        <SurfaceFacts value={depth} />
      </Disclosure>
    </SurfaceState>
  );
}

/* HS-100-07 — one readiness status LINE under the loop: quiet when the
   pipeline is live, a warning that opens the door when it is not. The
   diagnostics wall lives behind the gear. */
function ReadinessLine({ onOpenDoor }: { onOpenDoor: () => void }) {
  const root = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const resource = useResource<JsonRecord>(
    `/api/dictation/readiness${root ? `?project_root=${encodeURIComponent(root)}` : ""}`,
    {},
  );
  if (resource.loading || resource.error) return null;
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
        <span className="speak-status-dot is-live" aria-hidden="true" />
        Pipeline live
        {target.label ? ` · types into ${presentValue(target.label)}` : ""}
        {budget ? ` · ${presentValue(budget)} ms budget` : ""}
      </p>
    );
  }
  return (
    <p className="speak-status is-warn" role="status">
      <span className="speak-status-dot" aria-hidden="true" />
      {config.pipeline_enabled === true
        ? `${warnings.length} readiness ${warnings.length === 1 ? "warning" : "warnings"}`
        : "The pipeline is off — speaking here still works on paper"}
      <button type="button" className="speak-status-fix" onClick={onOpenDoor}>
        Review
      </button>
    </p>
  );
}

function SpeakFace({ onOpenDoor }: { onOpenDoor: () => void }) {
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
  const [recoveryMessage, setRecoveryMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [correctionKind, setCorrectionKind] = useState("target");
  const [correctionValue, setCorrectionValue] = useState("");
  const [taught, setTaught] = useState("");
  const [verdict, setVerdict] = useState<"" | "right" | "wrong">("");
  const [targets, setTargets] = useState<InferenceTarget[]>([]);
  const [targetId, setTargetId] = useState("this_machine");
  const run = async () => {
    setBusy(true);
    setError("");
    setFailure(null);
    setRecoveryMessage("");
    setVerdict("");
    setTaught("");
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
      localStorage.setItem("holdspeak.projectRootOverride", projectRoot);
    } catch (reason) {
      const category = dictationFailure(reason);
      setFailure(category);
      setError(DICTATION_FAILURES[category].message);
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
    setRecoveryMessage("");
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
      setRecoveryMessage(readableError(reason));
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
      setRecoveryMessage("Kept as a Note on your Desk.");
    } catch (reason) {
      setRecoveryMessage(
        `The Note was not kept. Your draft remains editable. ${readableError(reason)}`,
      );
    }
  };
  const teach = async () => {
    setBusy(true);
    setTaught("");
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
      setTaught("Correction learned for similar future dictations.");
      setCorrectionValue("");
    } catch (reason) {
      setTaught(readableError(reason));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="speak-face">
      <div className="speak-hero">
        <MicButton
          draftScope="dictation-dry-run-voice"
          label="Hold to talk"
          onText={(text) => setUtterance(text)}
        />
        <p className="speak-hint">Hold to talk, or type below — on paper</p>
      </div>
      <div className="desk-mic-row">
        <TextArea
          aria-label="Utterance"
          value={utterance}
          onChange={(event) => setUtterance(event.target.value)}
          placeholder="Explain the change I made…"
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
        <Disclosure title="Grounding scope">
          <TextInput
            aria-label="Project root — optional grounding scope, saved only on this device"
            placeholder="Project root (optional)"
            value={projectRoot}
            onChange={(event) => setProjectRoot(event.target.value)}
          />
        </Disclosure>
      </div>
      {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
      {utteranceRecovered && !error ? (
        <InlineMessage tone="info">
          Recovered your local dictation draft after relaunch.
        </InlineMessage>
      ) : null}
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
      {recoveryMessage ? (
        <InlineMessage
          tone={recoveryMessage.startsWith("Kept") ? "success" : "error"}
        >
          {recoveryMessage}
        </InlineMessage>
      ) : null}
      {result ? (
        <section className="speak-result" aria-label="Pipeline result">
          <InlineMessage tone="success">
            {String(
              result.final_text ??
                result.text ??
                result.output ??
                "Pipeline completed.",
            )}
          </InlineMessage>
          <div className="surface-actions" aria-label="Rate this result">
            <Button dense onClick={() => setVerdict("right")}>
              Right
            </Button>
            <Button dense variant="ghost" onClick={() => setVerdict("wrong")}>
              Wrong
            </Button>
          </div>
          {verdict === "right" ? (
            <InlineMessage tone="success">
              Marked right. Nothing was written to correction memory.
            </InlineMessage>
          ) : null}
          {verdict === "wrong" ? (
            <Disclosure title="Correct this result" open>
              <Field label="What should change?">
                {({ id }) => (
                  <Select
                    id={id}
                    value={correctionKind}
                    onChange={(event) => setCorrectionKind(event.target.value)}
                  >
                    <option value="target">Delivery target</option>
                    <option value="intent">Intent</option>
                  </Select>
                )}
              </Field>
              <Field label="Correct value">
                {({ id }) => (
                  <TextInput
                    id={id}
                    value={correctionValue}
                    onChange={(event) => setCorrectionValue(event.target.value)}
                  />
                )}
              </Field>
              <Button
                loading={busy}
                disabled={!correctionValue.trim()}
                onClick={teach}
              >
                Teach correction
              </Button>
              {taught ? (
                <InlineMessage
                  tone={taught.startsWith("Correction") ? "success" : "error"}
                >
                  {taught}
                </InlineMessage>
              ) : null}
            </Disclosure>
          ) : null}
          <Disclosure title="Raw trace">
            <SurfaceCode>{JSON.stringify(result, null, 2)}</SurfaceCode>
          </Disclosure>
        </section>
      ) : null}
      <ReadinessLine onOpenDoor={onOpenDoor} />
    </div>
  );
}

/** HS-101 B4 — Blocks reads like a library: the injection text IS
 * the tile's face, the name and spoken matches ride the spine,
 * create is a ghost tile in the shelf. Edits land on the material. */
function blockSlug(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function Blocks() {
  const [scope, setScope] = useState("global");
  const resource = useResource<JsonRecord>(
    `/api/dictation/blocks?scope=${scope}`,
    {},
  );
  const rows = asRows(
    (resource.data.document as JsonRecord | undefined)?.blocks,
    [],
  );
  const [message, setMessage] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [draft, setDraft] = useState({ name: "", examples: "", injection: "" });
  const save = async (row: Record<string, unknown>, patch: JsonRecord) => {
    setMessage("");
    try {
      await apiFetch(
        `/api/dictation/blocks/${encodeURIComponent(String(row.id))}?scope=${scope}`,
        { method: "PUT", json: { block: { ...row, ...patch } } },
      );
      await resource.reload();
    } catch (error) {
      setMessage(readableError(error));
    }
  };
  const remove = async (row: Record<string, unknown>) => {
    setMessage("");
    try {
      await apiFetch(
        `/api/dictation/blocks/${encodeURIComponent(String(row.id))}?scope=${scope}`,
        { method: "DELETE" },
      );
      await resource.reload();
    } catch (error) {
      setMessage(readableError(error));
    }
  };
  const create = async () => {
    const name = draft.name.trim();
    if (!name) return;
    setMessage("");
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
      setMessage(readableError(error));
    }
  };
  return (
    <SurfaceSection>
      <SurfaceLibrary
        count={rows.length}
        countLabel={rows.length === 1 ? "block" : "blocks"}
        controls={
          <Select
            aria-label="Block scope"
            value={scope}
            onChange={(event) => setScope(event.target.value)}
          >
            <option value="global">Global</option>
            <option value="project">Project</option>
          </Select>
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
                <TextArea
                  aria-label="Injection text"
                  placeholder="What this block injects"
                  rows={4}
                  value={draft.injection}
                  onChange={(event) =>
                    setDraft({ ...draft, injection: event.target.value })
                  }
                />
              </div>
              <div className="surface-tile-spine">
                <TextInput
                  aria-label="Block name"
                  placeholder="Name"
                  value={draft.name}
                  onChange={(event) =>
                    setDraft({ ...draft, name: event.target.value })
                  }
                />
                <TextInput
                  aria-label="Spoken matches, comma separated"
                  placeholder="Say: standup notes, stand up"
                  value={draft.examples}
                  onChange={(event) =>
                    setDraft({ ...draft, examples: event.target.value })
                  }
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
        {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      </SurfaceLibrary>
    </SurfaceSection>
  );
}

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
    <SurfaceColumns
      main={
        <SurfaceSection label="Correction memory">
          <SurfaceState
            loading={resource.loading}
            error={resource.error}
            empty={!rows.length}
            emptyLabel="Nothing learned yet"
            emptyGlyph="◈"
            onRetry={() => void resource.reload()}
          >
            <SurfaceRows>
              {rows.map((row, index) => (
                <SurfaceRow
                  key={rowId(row, index)}
                  title={String(row.gist ?? row.kind ?? "Correction")}
                  detail={
                    presentValue(row.value ?? row.replacement) || undefined
                  }
                  verbs={
                    <ConfirmVerb
                      label="Forget"
                      confirmLabel="Forget?"
                      onConfirm={() => void remove(row)}
                    />
                  }
                />
              ))}
            </SurfaceRows>
          </SurfaceState>
        </SurfaceSection>
      }
      side={
        <SurfaceSection label="Learning digest">
          <SurfaceState
            loading={digest.loading}
            error={digest.error}
            onRetry={() => void digest.reload()}
          >
            <LearningDigestFacts digest={digest.data} />
          </SurfaceState>
        </SurfaceSection>
      }
    />
  );
}

/* HS-102-06 — the digest's window/enabled/generated-at wrapper is
   metadata, not the fact; SurfaceFacts on the raw object was
   accidentally surfacing exactly that (the only top-level scalars)
   while the real counts sat hidden inside `totals`. Compose the
   totals into one honest sentence instead. */
function LearningDigestFacts({ digest }: { digest: JsonRecord }) {
  const totals = (digest.totals ?? {}) as JsonRecord;
  const made = Number(totals.corrections_made ?? 0);
  const corrected = Number(totals.dictations_corrected ?? 0);
  const nudged = Number(totals.similar_nudged ?? 0);
  const topBlocks = asRows(digest, ["by_block"]).slice(0, 3);
  if (!made && !corrected) {
    return <p className="surface-fact-line">Nothing learned this week yet</p>;
  }
  return (
    <>
      <p className="surface-fact-line">
        {made} correction{made === 1 ? "" : "s"} taught this week
        {corrected ? ` · ${corrected} dictation${corrected === 1 ? "" : "s"} corrected` : ""}
        {nudged ? ` · reached ${nudged} similar` : ""}
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
   keys) — a facts glossary, not free text; the old single textarea +
   orange save button was never wired to this shape (it PUT
   `{content}}`, which the route has always refused — a pre-existing
   defect this recompose fixes along with the surface). Each fact is
   its own row, edited in place; a small composer adds a new one.
   Instructions binds to the primary `.hs/instructions.md` file
   (`/api/dictation/project-hs`'s `{files: {<name>: <content>}}`
   shape) — the other named `.hs` files stay out of this face's
   scope. */
function Knowledge() {
  const [root, setRoot] = useState(
    () => localStorage.getItem("holdspeak.projectRootOverride") ?? "",
  );
  const query = root ? `?project_root=${encodeURIComponent(root)}` : "";
  const kb = useResource<JsonRecord>(`/api/dictation/project-kb${query}`, {});
  const hs = useResource<JsonRecord>(`/api/dictation/project-hs${query}`, {});
  const [saving, setSaving] = useState(false);
  const [savedTick, setSavedTick] = useState(false);
  const [message, setMessage] = useState("");
  const [draftKey, setDraftKey] = useState("");
  const [draftValue, setDraftValue] = useState("");
  const kbFacts = (kb.data.kb ?? {}) as Record<string, unknown>;
  const kbEntries = Object.entries(kbFacts);
  const instructionsFile = (
    ((hs.data.files ?? {}) as JsonRecord)["instructions.md"] ?? {}
  ) as JsonRecord;
  const putKb = async (next: Record<string, unknown>) => {
    setSaving(true);
    setMessage("");
    try {
      await apiFetch(`/api/dictation/project-kb${query}`, {
        method: "PUT",
        json: { kb: next },
      });
      setSavedTick(true);
      await kb.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setSaving(false);
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
      setMessage(
        "Fact names must look like BLUEBIRD or api_key — letters, numbers, underscore, starting with a letter or underscore.",
      );
      return;
    }
    void putKb({ ...kbFacts, [key]: draftValue.trim() });
    setDraftKey("");
    setDraftValue("");
  };
  const saveInstructions = async (content: string) => {
    setSaving(true);
    setMessage("");
    try {
      await apiFetch(`/api/dictation/project-hs${query}`, {
        method: "PUT",
        json: { files: { "instructions.md": content } },
      });
      setSavedTick(true);
      await hs.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setSaving(false);
    }
  };
  const whisper = (
    <span
      className={"settings-save-whisper" + (saving ? " is-saving" : "")}
      role="status"
    >
      {saving ? "Saving…" : savedTick ? "Saved" : ""}
    </span>
  );
  return (
    <>
      <SurfaceGroup label="Project scope">
        <SurfaceSettingRow
          label={
            <EditInPlace
              value={root || "This device's working directory"}
              label="Project root"
              onCommit={(next) =>
                setRoot(
                  next === "This device's working directory" ? "" : next,
                )
              }
            />
          }
          description="Where dictation looks for Knowledge and Instructions"
          control={
            <Button
              dense
              onClick={() => {
                localStorage.setItem("holdspeak.projectRootOverride", root);
                void kb.reload();
                void hs.reload();
              }}
            >
              Use project
            </Button>
          }
        />
      </SurfaceGroup>
      {whisper}
      <SurfaceColumns
        main={
          <SurfaceSection label="Knowledge">
            {kbEntries.length ? (
              <SurfaceRows>
                {kbEntries.map(([key, value]) => (
                  <SurfaceRow
                    key={key}
                    title={key}
                    detail={
                      <EditInPlace
                        value={String(value ?? "") || "(empty) click to add"}
                        label={`${key} value`}
                        onCommit={(next) => setFact(key, next)}
                      />
                    }
                    verbs={
                      <ConfirmVerb
                        label="Forget"
                        confirmLabel="Forget?"
                        onConfirm={() => forgetFact(key)}
                      />
                    }
                  />
                ))}
              </SurfaceRows>
            ) : (
              <p className="surface-fact-line">
                No facts yet — add one below.
              </p>
            )}
            <div className="surface-actions">
              <TextInput
                aria-label="Fact name"
                placeholder="BLUEBIRD"
                value={draftKey}
                onChange={(event) => setDraftKey(event.target.value)}
              />
              <TextInput
                aria-label="Fact value"
                placeholder="the codename for…"
                value={draftValue}
                onChange={(event) => setDraftValue(event.target.value)}
              />
              <Button dense disabled={!draftKey.trim()} onClick={addFact}>
                Add fact
              </Button>
            </div>
          </SurfaceSection>
        }
        side={
          <SurfaceSection label="Instructions">
            <EditInPlace
              value={
                String(instructionsFile.content ?? "") ||
                "No instructions yet — click to add."
              }
              label="Project instructions"
              multiline
              onCommit={(next) => void saveInstructions(next)}
            />
          </SurfaceSection>
        }
      />
      {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
    </>
  );
}

/** HS-101 B3 — the Journal reads like a journal: a dated stream. */
function Journal() {
  const resource = useResource<JsonRecord>(
    "/api/dictation/journal?limit=200",
    {},
  );
  const rows = asRows(resource.data, ["items"]);
  const [query, setQuery] = useState("");
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
      <SurfaceStream
        count={todayCount}
        countLabel={
          taughtCount
            ? `today · ${taughtCount} taught`
            : "today"
        }
        controls={
          <>
            <TextInput
              type="search"
              aria-label="Search the journal"
              placeholder="Search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <ConfirmVerb
              label="Clear…"
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
                const replayResult = replays[String(row.id)];
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
                  <SurfaceStreamEntry
                    key={rowId(row, index)}
                    when={streamTime(
                      streamDate(row.created_at ?? row.timestamp),
                    )}
                    meta={
                      <>
                        {destination ? <span>→ {destination}</span> : null}
                        {took > 0 ? <span>{Math.round(took)} ms</span> : null}
                        {row.corrected ? (
                          <span className="surface-learned">
                            ✓ taught
                            {learning?.matched && similar > 0
                              ? ` · from ${similar} similar`
                              : ""}
                          </span>
                        ) : null}
                      </>
                    }
                    verbs={
                      <>
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
                      </>
                    }
                    aside={
                      replayResult ? (
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
                      ) : null
                    }
                  >
                    <EditInPlace
                      value={String(row.transcript ?? "")}
                      label="transcript"
                      multiline
                      onCommit={(next) => void editTranscript(row, next)}
                    />
                  </SurfaceStreamEntry>
                );
              })}
            </SurfaceStreamDay>
          ))}
        </SurfaceState>
      </SurfaceStream>
    </SurfaceSection>
  );
}

/* HS-102-06 — the runtime knobs live in exactly ONE composed place:
   `RuntimeDestination` (settingsBespoke.tsx), the same component
   Settings uses for this exact same `dictation.runtime` value. This
   face embeds it rather than re-stating Backend/Runs on/Latency
   budget as a third label-over-Select stack. Saves on change,
   debounced, like every other configuring surface (HS-101 round 3). */
function Runtime() {
  const settings = useResource<JsonRecord>("/api/settings", {});
  const [saving, setSaving] = useState(false);
  const [savedTick, setSavedTick] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(saveTimer.current), []);
  const runtime = ((settings.data.dictation as JsonRecord | undefined)
    ?.runtime ?? {}) as JsonRecord;
  const save = async (dictation: JsonRecord) => {
    setSaving(true);
    try {
      await apiFetch("/api/settings", { method: "PUT", json: { dictation } });
      setSavedTick(true);
    } finally {
      setSaving(false);
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
    <SurfaceSection
      label="Dictation runtime"
      actions={
        <span
          className={"settings-save-whisper" + (saving ? " is-saving" : "")}
          role="status"
        >
          {saving ? "Saving…" : savedTick ? "Saved" : ""}
        </span>
      }
    >
      <RuntimeDestination value={runtime} onCommit={patch} />
    </SurfaceSection>
  );
}

function Hooks() {
  const resource = useResource<JsonRecord>(
    "/api/dictation/agent-hooks?capture_messages=false",
    {},
  );
  return (
    <SurfaceSection label="Automation hooks">
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceCode>{JSON.stringify(resource.data, null, 2)}</SurfaceCode>
      </SurfaceState>
    </SurfaceSection>
  );
}

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
  return (
    <SurfaceSection label="Activity nudges">
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        empty={!rows.length}
        emptyLabel="No recent activity to cite"
        emptyGlyph="⌁"
        onRetry={() => void resource.reload()}
      >
        <SurfaceRows>
          {rows.map((row, index) => (
            <SurfaceRow
              key={rowId(row, index)}
              title={String(row.title ?? row.text ?? "Recent work")}
              detail={
                presentValue(row.citation ?? row.source ?? row.url) ||
                "Local activity"
              }
              verbs={
                <>
                  <Button dense onClick={() => void act(row, "select")}>
                    Use as context
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => void act(row, "dismiss")}
                  >
                    Dismiss
                  </Button>
                </>
              }
            />
          ))}
        </SurfaceRows>
      </SurfaceState>
    </SurfaceSection>
  );
}

export function DictationCore({ hero, scope, scopeLabel }: CoreProps) {
  const [view, setView] = useState("speak");
  const [doorOpen, setDoorOpen] = useState(false);
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
        speak: <SpeakFace onOpenDoor={() => setDoorOpen(true)} />,
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
      {current}
    </>
  );
}

/* HS-100-07 — the one door: everything that is configuration
   (readiness diagnostics, memory, knowledge, runtime, hooks, nudges)
   stacked behind the gear. No tab wall. */
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
