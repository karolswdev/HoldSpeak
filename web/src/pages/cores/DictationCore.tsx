// HS-95-05 — the Dictation surface's core: the whole daily cockpit
// (readiness, dry run, blocks, memory, knowledge, journal, runtime,
// hooks, nudges) hosted anywhere (see ActivityCore for the pattern).
// HS-98-02 — re-crafted native: composed from the surface kit on the
// window material (DESIGN_SYSTEM.md, "The surface idiom"); wire calls
// and verbs unchanged.
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
  Tabs,
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
  SurfaceCode,
  SurfaceColumns,
  SurfaceFacts,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
} from "../../desk/surface/Surface";
import { humanTime, presentValue } from "../../desk/surface/format";

const TABS = [
  ["ready", "Readiness"],
  ["dry", "Try it"],
  ["blocks", "Blocks"],
  ["memory", "Memory"],
  ["knowledge", "Knowledge"],
  ["journal", "Journal"],
  ["runtime", "Runtime"],
  ["hooks", "Hooks"],
  ["nudges", "Nudges"],
].map(([id, label]) => ({ id, label }));

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

function DryRun() {
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
    <SurfaceColumns
      main={
        <SurfaceSection label="Speak on paper">
          <Field
            label="Utterance"
            description="Runs the real pipeline without typing into another app."
          >
            {({ id, describedBy }) => (
              <div className="desk-mic-row">
                <TextArea
                  id={id}
                  aria-describedby={describedBy}
                  value={utterance}
                  onChange={(event) => setUtterance(event.target.value)}
                  placeholder="Explain the change I made…"
                />
                <MicButton
                  draftScope="dictation-dry-run-voice"
                  onText={(text) => setUtterance(text)}
                />
              </div>
            )}
          </Field>
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
          <div className="surface-actions">
            <Button
              variant="primary"
              loading={busy}
              disabled={!utterance.trim()}
              onClick={run}
            >
              {error && actions.includes("retry")
                ? "Retry dry test"
                : "Run dry test"}
            </Button>
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
        </SurfaceSection>
      }
      side={
        <SurfaceSection label="Pipeline result">
          {result ? (
            <>
              <InlineMessage tone="success">
                {String(
                  result.final_text ??
                    result.text ??
                    result.output ??
                    "Pipeline completed.",
                )}
              </InlineMessage>
              <Disclosure title="Raw trace">
                <SurfaceCode>{JSON.stringify(result, null, 2)}</SurfaceCode>
              </Disclosure>
              <div className="surface-actions" aria-label="Rate this result">
                <Button dense onClick={() => setVerdict("right")}>
                  Right
                </Button>
                <Button
                  dense
                  variant="ghost"
                  onClick={() => setVerdict("wrong")}
                >
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
                        onChange={(event) =>
                          setCorrectionKind(event.target.value)
                        }
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
                        onChange={(event) =>
                          setCorrectionValue(event.target.value)
                        }
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
                      tone={
                        taught.startsWith("Correction") ? "success" : "error"
                      }
                    >
                      {taught}
                    </InlineMessage>
                  ) : null}
                </Disclosure>
              ) : null}
            </>
          ) : (
            <SurfaceState
              empty
              emptyLabel="No run yet"
              emptyGlyph="▹"
            />
          )}
        </SurfaceSection>
      }
    />
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
  return (
    <SurfaceSection
      label="Dictation journal"
      actions={
        <ConfirmVerb
          label="Clear journal"
          confirmLabel="Clear all?"
          disabled={!rows.length}
          onConfirm={() => void remove("all")}
        />
      }
    >
      <Field label="Search journal">
        {({ id }) => (
          <TextInput
            id={id}
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        )}
      </Field>
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        empty={!filtered.length}
        emptyLabel="No dictations on this device"
        emptyGlyph="✎"
        onRetry={() => void resource.reload()}
      >
        <SurfaceRows>
          {filtered.map((row, index) => {
            const replayResult = replays[String(row.id)];
            const replayAfter =
              replayResult?.after && typeof replayResult.after === "object"
                ? (replayResult.after as JsonRecord)
                : replayResult;
            const replayText = String(replayAfter?.final_text ?? "");
            return (
              <SurfaceRow
                key={rowId(row, index)}
                title={String(row.transcript ?? "Untitled dictation")}
                detail={
                  humanTime(row.created_at ?? row.timestamp) ||
                  presentValue(row.source) ||
                  undefined
                }
                verbs={
                  <>
                    <Button dense onClick={() => void replay(row)}>
                      Replay
                    </Button>
                    <ConfirmVerb
                      label="Delete"
                      confirmLabel="Delete?"
                      onConfirm={() => void remove(row)}
                    />
                  </>
                }
              >
                {replayResult ? (
                  <div className="surface-preview" role="status">
                    <span className="surface-preview-label">Preview only</span>
                    <p>{replayText || "The replay completed without text."}</p>
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
              </SurfaceRow>
            );
          })}
        </SurfaceRows>
      </SurfaceState>
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
  const [active, setActive] = useState("ready");
  const current = useMemo(
    () =>
      ({
        ready: <Readiness />,
        dry: <DryRun />,
        blocks: <Blocks />,
        memory: <Memory />,
        knowledge: <Knowledge />,
        journal: <Journal />,
        runtime: <Runtime />,
        hooks: <Hooks />,
        nudges: <Nudges />,
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
      <Tabs
        label="Dictation sections"
        tabs={TABS}
        active={active}
        onChange={setActive}
      />
      {current}
    </>
  );
}
