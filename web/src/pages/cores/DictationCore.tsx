// HS-95-05 — the Dictation surface's core, hosted anywhere.
// HS-98-02 — re-crafted native on the window material.
// HS-100-07 — Speak: the application opens ON the job (speak, see it
// land, judge it, teach it — trace B's loop is the entire front face);
// Journal and Blocks are the wings; Memory/Knowledge/Runtime/Hooks/
// Nudges and full readiness fold behind the one gear door
// (APPLICATION_LAYER_THESIS.md §1.1). Wire calls and verbs unchanged.
import { useEffect, useMemo, useState } from "react";
import { openSurfaceOr } from "../../desk/shell";
import type { CoreProps } from "./ActivityCore";
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
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceStream,
  SurfaceStreamDay,
  SurfaceStreamEntry,
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

function Readiness() {
  const root = localStorage.getItem("holdspeak.projectRootOverride") ?? "";
  const resource = useResource<JsonRecord>(
    `/api/dictation/readiness${root ? `?project_root=${encodeURIComponent(root)}` : ""}`,
    {},
  );
  const warnings = Array.isArray(resource.data.warnings)
    ? resource.data.warnings
    : [];
  return (
    <SurfaceState
      loading={resource.loading}
      error={resource.error}
      onRetry={() => void resource.reload()}
    >
      <SurfaceColumns
        main={
          <SurfaceSection label="Pipeline readiness">
            <SurfaceFacts value={resource.data.config} />
            {warnings.map((warning, index) => (
              <InlineMessage tone="warning" key={index}>
                {readableValue(warning)}
              </InlineMessage>
            ))}
          </SurfaceSection>
        }
        side={
          <SurfaceSection label="Resolved delivery">
            <SurfaceFacts value={resource.data.target} />
            <SurfaceFacts value={resource.data.depth} />
          </SurfaceSection>
        }
      />
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
        <p className="speak-hint">
          Hold to talk, or type below. Runs the real pipeline on paper,
          without typing into another app.
        </p>
      </div>
      <Field label="Utterance">
        {({ id, describedBy }) => (
          <div className="desk-mic-row">
            <TextArea
              id={id}
              aria-describedby={describedBy}
              value={utterance}
              onChange={(event) => setUtterance(event.target.value)}
              placeholder="Explain the change I made…"
            />
          </div>
        )}
      </Field>
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
          <Field
            label="Project root"
            description="Optional grounding scope; saved only on this device."
          >
            {({ id, describedBy }) => (
              <TextInput
                id={id}
                aria-describedby={describedBy}
                value={projectRoot}
                onChange={(event) => setProjectRoot(event.target.value)}
                placeholder="/path/to/project"
              />
            )}
          </Field>
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
  const [form, setForm] = useState({
    id: "",
    name: "",
    examples: "",
    injection: "",
  });
  const [message, setMessage] = useState("");
  const create = async () => {
    setMessage("");
    try {
      await apiFetch(`/api/dictation/blocks?scope=${scope}`, {
        method: "POST",
        json: {
          block: {
            id: form.id.trim(),
            name: form.name.trim(),
            match: form.examples.split("\n").filter(Boolean),
            inject: form.injection,
          },
        },
      });
      setForm({ id: "", name: "", examples: "", injection: "" });
      await resource.reload();
    } catch (error) {
      setMessage(readableError(error));
    }
  };
  return (
    <SurfaceColumns
      main={
        <SurfaceSection
          label="Routing blocks"
          actions={
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
            empty={!rows.length}
            emptyLabel="No routing blocks"
            emptyGlyph="⧉"
            onRetry={() => void resource.reload()}
          >
            <SurfaceRows>
              {rows.map((row, index) => (
                <SurfaceRow
                  key={rowId(row, index)}
                  title={String(row.name ?? row.id ?? "Block")}
                  detail={
                    presentValue(row.description ?? row.inject) || undefined
                  }
                  meta={
                    <StatusPill>
                      {String(row.enabled === false ? "off" : "active")}
                    </StatusPill>
                  }
                />
              ))}
            </SurfaceRows>
          </SurfaceState>
        </SurfaceSection>
      }
      side={
        <SurfaceSection label="New block">
          <Field label="ID">
            {({ id }) => (
              <TextInput
                id={id}
                value={form.id}
                onChange={(event) =>
                  setForm({ ...form, id: event.target.value })
                }
              />
            )}
          </Field>
          <Field label="Name">
            {({ id }) => (
              <TextInput
                id={id}
                value={form.name}
                onChange={(event) =>
                  setForm({ ...form, name: event.target.value })
                }
              />
            )}
          </Field>
          <Field label="Example utterances">
            {({ id }) => (
              <TextArea
                id={id}
                value={form.examples}
                onChange={(event) =>
                  setForm({ ...form, examples: event.target.value })
                }
              />
            )}
          </Field>
          <Field label="Injection">
            {({ id }) => (
              <TextArea
                id={id}
                value={form.injection}
                onChange={(event) =>
                  setForm({ ...form, injection: event.target.value })
                }
              />
            )}
          </Field>
          <div className="surface-actions">
            <Button
              variant="primary"
              disabled={!form.id.trim()}
              onClick={create}
            >
              Create block
            </Button>
          </div>
          {message ? (
            <InlineMessage tone="error">{message}</InlineMessage>
          ) : null}
        </SurfaceSection>
      }
    />
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
            <SurfaceFacts value={digest.data} />
          </SurfaceState>
        </SurfaceSection>
      }
    />
  );
}

function Knowledge() {
  const [root, setRoot] = useState(
    () => localStorage.getItem("holdspeak.projectRootOverride") ?? "",
  );
  const query = root ? `?project_root=${encodeURIComponent(root)}` : "";
  const kb = useResource<JsonRecord>(`/api/dictation/project-kb${query}`, {});
  const hs = useResource<JsonRecord>(`/api/dictation/project-hs${query}`, {});
  const [kbText, setKbText] = useState("");
  const [hsText, setHsText] = useState("");
  const [message, setMessage] = useState("");
  const save = async (kind: "kb" | "hs") => {
    setMessage("");
    try {
      await apiFetch(`/api/dictation/project-${kind}${query}`, {
        method: "PUT",
        json: kind === "kb" ? { content: kbText } : { content: hsText },
      });
      setMessage("Project context saved.");
      kind === "kb" ? await kb.reload() : await hs.reload();
    } catch (error) {
      setMessage(readableError(error));
    }
  };
  return (
    <>
      <SurfaceSection label="Project scope">
        <div className="surface-actions">
          <Field label="Project root">
            {({ id }) => (
              <TextInput
                id={id}
                value={root}
                onChange={(event) => setRoot(event.target.value)}
              />
            )}
          </Field>
          <Button
            onClick={() => {
              localStorage.setItem("holdspeak.projectRootOverride", root);
              void kb.reload();
              void hs.reload();
            }}
          >
            Use project
          </Button>
        </div>
        {message ? (
          <InlineMessage tone={message.includes("saved") ? "success" : "error"}>
            {message}
          </InlineMessage>
        ) : null}
      </SurfaceSection>
      <SurfaceColumns
        main={
          <SurfaceSection label={String(kb.data.path ?? "Knowledge")}>
            <TextArea
              aria-label="Project knowledge"
              value={kbText || String(kb.data.content ?? "")}
              onChange={(event) => setKbText(event.target.value)}
            />
            <div className="surface-actions">
              <Button variant="primary" onClick={() => void save("kb")}>
                Save knowledge
              </Button>
            </div>
          </SurfaceSection>
        }
        side={
          <SurfaceSection label={String(hs.data.path ?? "Instructions")}>
            <TextArea
              aria-label="Project instructions"
              value={hsText || String(hs.data.content ?? "")}
              onChange={(event) => setHsText(event.target.value)}
            />
            <div className="surface-actions">
              <Button variant="primary" onClick={() => void save("hs")}>
                Save instructions
              </Button>
            </div>
          </SurfaceSection>
        }
      />
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

function Runtime() {
  const settings = useResource<JsonRecord>("/api/settings", {});
  const profiles = useResource<JsonRecord>("/api/profiles", {});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const runtime = ((settings.data.dictation as JsonRecord | undefined)
    ?.runtime ?? {}) as JsonRecord;
  const profileRows = asRows(profiles.data, ["profiles"]);
  const patch = (key: string, value: unknown) =>
    settings.setData({
      ...settings.data,
      dictation: {
        ...(settings.data.dictation as JsonRecord),
        runtime: { ...runtime, [key]: value },
      },
    });
  const save = async () => {
    setSaving(true);
    try {
      await apiFetch("/api/settings", {
        method: "PUT",
        json: { dictation: settings.data.dictation },
      });
      setMessage("Runtime saved.");
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setSaving(false);
    }
  };
  return (
    <SurfaceSection label="Dictation runtime">
      <Field label="Backend">
        {({ id }) => (
          <Select
            id={id}
            value={String(runtime.backend ?? "auto")}
            onChange={(event) => patch("backend", event.target.value)}
          >
            <option value="auto">Automatic</option>
            <option value="mlx">MLX</option>
            <option value="llama_cpp">llama.cpp</option>
            <option value="openai_compatible">OpenAI-compatible</option>
          </Select>
        )}
      </Field>
      <Field label="Runs on">
        {({ id }) => (
          <Select
            id={id}
            value={String(runtime.profile_id ?? "")}
            onChange={(event) =>
              patch("profile_id", event.target.value || null)
            }
          >
            <option value="">Hub default</option>
            {profileRows.map((profile, index) => (
              <option key={rowId(profile, index)} value={String(profile.id)}>
                {String(profile.name)}
              </option>
            ))}
          </Select>
        )}
      </Field>
      <Field label="Latency budget (ms)">
        {({ id }) => (
          <TextInput
            id={id}
            type="number"
            value={Number(
              (
                (settings.data.dictation as JsonRecord | undefined)
                  ?.pipeline as JsonRecord | undefined
              )?.max_total_latency_ms ?? 1200,
            )}
            readOnly
          />
        )}
      </Field>
      <div className="surface-actions">
        <Button variant="primary" loading={saving} onClick={save}>
          Save runtime
        </Button>
      </div>
      {message ? (
        <InlineMessage tone={message === "Runtime saved." ? "success" : "error"}>
          {message}
        </InlineMessage>
      ) : null}
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
