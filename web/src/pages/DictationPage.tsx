import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Button,
  Disclosure,
  EmptyState,
  Field,
  InlineMessage,
  Panel,
  Select,
  StatusPill,
  Tabs,
  TextArea,
  TextInput,
  Toolbar,
} from "../components/signal/Signal";
import { RunsOnPicker } from "../desk/components/RunsOnPicker";
import type { InferenceTarget } from "../desk/api";
import { apiFetch, readableError, type JsonRecord } from "../lib/api";
import {
  DICTATION_FAILURES,
  applicableActions,
  dictationFailure,
  type DictationFailure,
} from "../lib/dictationRecovery";
import { useDurableDraft } from "../lib/durableDraft";
import {
  ConfirmAction,
  PageHero,
  ResourceState,
  asRows,
  rowId,
  useResource,
  valueAt,
} from "./pageSupport";

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

function JsonFacts({ value }: { value: unknown }) {
  if (!value || typeof value !== "object")
    return <p>{String(value ?? "No data")}</p>;
  return (
    <dl className="signal-facts">
      {Object.entries(value as JsonRecord)
        .filter(
          ([, item]) =>
            ["string", "number", "boolean"].includes(typeof item) ||
            item === null,
        )
        .slice(0, 18)
        .map(([key, item]) => (
          <div key={key}>
            <dt>{key.replace(/_/g, " ")}</dt>
            <dd>{String(item ?? "—")}</dd>
          </div>
        ))}
    </dl>
  );
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
    <ResourceState
      loading={resource.loading}
      error={resource.error}
      onRetry={() => void resource.reload()}
    >
      <div className="page-grid">
        <Panel
          className="span-8"
          title="Pipeline readiness"
          eyebrow="Live hub report"
        >
          <JsonFacts value={resource.data.config} />
          {warnings.map((warning, index) => (
            <InlineMessage tone="warning" key={index}>
              {readableValue(warning)}
            </InlineMessage>
          ))}
        </Panel>
        <Panel
          className="span-4"
          title="Resolved delivery"
          eyebrow="Project context"
        >
          <JsonFacts value={resource.data.target} />
          <JsonFacts value={resource.data.depth} />
        </Panel>
      </div>
    </ResourceState>
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
    <div className="page-grid">
      <Panel className="span-4" title="Speak on paper" eyebrow="No typing">
        <Field
          label="Utterance"
          description="Runs the real pipeline without typing into another app."
        >
          {({ id, describedBy }) => (
            <TextArea
              id={id}
              aria-describedby={describedBy}
              value={utterance}
              onChange={(event) => setUtterance(event.target.value)}
              placeholder="Explain the change I made…"
            />
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
        <Button
          variant="primary"
          loading={busy}
          disabled={!utterance.trim()}
          onClick={run}
        >
          {error && actions.includes("retry") ? "Retry dry test" : "Run dry test"}
        </Button>
        {error ? <InlineMessage tone="error">{error}</InlineMessage> : null}
        {utteranceRecovered && !error ? (
          <InlineMessage tone="info">
            Recovered your local dictation draft after relaunch.
          </InlineMessage>
        ) : null}
        {error ? (
          <div className="button-row">
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
              <Link className="btn btn--secondary" to="/setup">
                Setup
              </Link>
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
      </Panel>
      <Panel className="span-8" title="Pipeline result" eyebrow="Trace">
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
            <pre className="code-block">{JSON.stringify(result, null, 2)}</pre>
            <div className="button-row" aria-label="Rate this result">
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
                    tone={taught.startsWith("Correction") ? "success" : "error"}
                  >
                    {taught}
                  </InlineMessage>
                ) : null}
              </Disclosure>
            ) : null}
          </>
        ) : (
          <EmptyState title="No run yet">
            Your routed result, target and stage trace will appear here.
          </EmptyState>
        )}
      </Panel>
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
    <div className="page-grid">
      <Panel
        className="span-8"
        title="Routing blocks"
        eyebrow={String(resource.data.path ?? scope)}
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
        <ResourceState
          loading={resource.loading}
          error={resource.error}
          empty={!rows.length}
          onRetry={() => void resource.reload()}
        >
          <ul className="data-list">
            {rows.map((row, index) => (
              <li className="data-row" key={rowId(row, index)}>
                <div>
                  <strong>{String(row.name ?? row.id ?? "Block")}</strong>
                  <small>{String(row.description ?? row.inject ?? "")}</small>
                </div>
                <StatusPill>
                  {String(row.enabled === false ? "off" : "active")}
                </StatusPill>
              </li>
            ))}
          </ul>
        </ResourceState>
      </Panel>
      <Panel className="span-4" title="New block" eyebrow="Intent routing">
        <Field label="ID">
          {({ id }) => (
            <TextInput
              id={id}
              value={form.id}
              onChange={(event) => setForm({ ...form, id: event.target.value })}
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
        <Button variant="primary" disabled={!form.id.trim()} onClick={create}>
          Create block
        </Button>
        {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      </Panel>
    </div>
  );
}

function Memory() {
  const resource = useResource<JsonRecord>("/api/dictation/corrections", {});
  const digest = useResource<JsonRecord>("/api/dictation/learning-digest", {});
  const rows = asRows(resource.data, ["items", "corrections"]);
  const [deleting, setDeleting] = useState<Record<string, unknown> | null>(
    null,
  );
  const remove = async () => {
    if (!deleting) return;
    await apiFetch(
      `/api/dictation/corrections/${encodeURIComponent(String(deleting.id))}`,
      { method: "DELETE" },
    );
    setDeleting(null);
    await resource.reload();
  };
  return (
    <div className="page-grid">
      <Panel
        className="span-8"
        title="Correction memory"
        eyebrow="Local learning"
      >
        <ResourceState
          loading={resource.loading}
          error={resource.error}
          empty={!rows.length}
          onRetry={() => void resource.reload()}
        >
          <ul className="data-list">
            {rows.map((row, index) => (
              <li className="data-row" key={rowId(row, index)}>
                <div>
                  <strong>
                    {String(row.gist ?? row.kind ?? "Correction")}
                  </strong>
                  <small>{String(row.value ?? row.replacement ?? "")}</small>
                </div>
                <Button dense variant="ghost" onClick={() => setDeleting(row)}>
                  Forget
                </Button>
              </li>
            ))}
          </ul>
        </ResourceState>
      </Panel>
      <Panel className="span-4" title="Learning digest" eyebrow="Honest reach">
        <ResourceState
          loading={digest.loading}
          error={digest.error}
          onRetry={() => void digest.reload()}
        >
          <JsonFacts value={digest.data} />
        </ResourceState>
      </Panel>
      <ConfirmAction
        open={Boolean(deleting)}
        title="Forget this correction?"
        detail="Future dictations will no longer receive this learned nudge."
        onConfirm={remove}
        onClose={() => setDeleting(null)}
      />
    </div>
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
    <div className="page-grid">
      <Panel
        className="span-12"
        title="Project grounding"
        eyebrow="Explicit scope"
      >
        <Toolbar label="Project scope">
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
        </Toolbar>
        {message ? (
          <InlineMessage tone={message.includes("saved") ? "success" : "error"}>
            {message}
          </InlineMessage>
        ) : null}
      </Panel>
      <Panel
        title="Knowledge"
        eyebrow={String(kb.data.path ?? "PROJECT_KB.md")}
      >
        <TextArea
          aria-label="Project knowledge"
          value={kbText || String(kb.data.content ?? "")}
          onChange={(event) => setKbText(event.target.value)}
        />
        <Button variant="primary" onClick={() => void save("kb")}>
          Save knowledge
        </Button>
      </Panel>
      <Panel
        title="Project instructions"
        eyebrow={String(hs.data.path ?? ".hs context")}
      >
        <TextArea
          aria-label="Project instructions"
          value={hsText || String(hs.data.content ?? "")}
          onChange={(event) => setHsText(event.target.value)}
        />
        <Button variant="primary" onClick={() => void save("hs")}>
          Save instructions
        </Button>
      </Panel>
    </div>
  );
}

function Journal() {
  const resource = useResource<JsonRecord>(
    "/api/dictation/journal?limit=200",
    {},
  );
  const rows = asRows(resource.data, ["items"]);
  const [query, setQuery] = useState("");
  const [deleting, setDeleting] = useState<
    Record<string, unknown> | "all" | null
  >(null);
  const [replays, setReplays] = useState<Record<string, JsonRecord>>({});
  const filtered = rows.filter(
    (row) =>
      !query ||
      String(row.transcript ?? "")
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  const remove = async () => {
    if (!deleting) return;
    await apiFetch(
      deleting === "all"
        ? "/api/dictation/journal"
        : `/api/dictation/journal/${encodeURIComponent(String(deleting.id))}`,
      { method: "DELETE" },
    );
    setDeleting(null);
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
    <Panel
      title="Dictation journal"
      eyebrow={`${rows.length} this-device entries`}
      actions={
        <Button
          dense
          variant="ghost"
          disabled={!rows.length}
          onClick={() => setDeleting("all")}
        >
          Clear journal
        </Button>
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
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        empty={!filtered.length}
        onRetry={() => void resource.reload()}
      >
        <ul className="data-list">
          {filtered.map((row, index) => {
            const replayResult = replays[String(row.id)];
            const replayAfter =
              replayResult?.after && typeof replayResult.after === "object"
                ? (replayResult.after as JsonRecord)
                : replayResult;
            const replayText = String(replayAfter?.final_text ?? "");
            return (
              <li className="data-row journal-row" key={rowId(row, index)}>
                <div className="journal-row-copy">
                  <strong>
                    {String(row.transcript ?? "Untitled dictation")}
                  </strong>
                  <small>
                    {String(
                      row.created_at ?? row.timestamp ?? row.source ?? "",
                    )}
                  </small>
                  {replayResult ? (
                    <div className="journal-replay" role="status">
                      <span className="signal-eyebrow">Preview only</span>
                      <p>
                        {replayText || "The replay completed without text."}
                      </p>
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
                  ) : null}
                </div>
                <div className="button-row">
                  <Button dense onClick={() => void replay(row)}>
                    Replay
                  </Button>
                  <Button
                    dense
                    variant="ghost"
                    onClick={() => setDeleting(row)}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      </ResourceState>
      <ConfirmAction
        open={Boolean(deleting)}
        title={
          deleting === "all"
            ? "Clear the journal?"
            : "Delete this journal entry?"
        }
        detail="This device's dictation history will be deleted and cannot be restored."
        onConfirm={remove}
        onClose={() => setDeleting(null)}
      />
    </Panel>
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
    <Panel title="Dictation runtime" eyebrow="One Runs on destination">
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
      <Button variant="primary" loading={saving} onClick={save}>
        Save runtime
      </Button>
      {message ? (
        <InlineMessage
          tone={message === "Runtime saved." ? "success" : "error"}
        >
          {message}
        </InlineMessage>
      ) : null}
    </Panel>
  );
}

function Hooks() {
  const resource = useResource<JsonRecord>(
    "/api/dictation/agent-hooks?capture_messages=false",
    {},
  );
  return (
    <Panel title="Automation hooks" eyebrow="Project-aware context">
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <pre className="code-block">
          {JSON.stringify(resource.data, null, 2)}
        </pre>
      </ResourceState>
    </Panel>
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
    <Panel title="Activity nudges" eyebrow="Source-cited context">
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        empty={!rows.length}
        onRetry={() => void resource.reload()}
      >
        <ul className="data-list">
          {rows.map((row, index) => (
            <li className="data-row" key={rowId(row, index)}>
              <div>
                <strong>
                  {String(row.title ?? row.text ?? "Recent work")}
                </strong>
                <small>
                  {String(
                    row.citation ?? row.source ?? row.url ?? "Local activity",
                  )}
                </small>
              </div>
              <div className="button-row">
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
              </div>
            </li>
          ))}
        </ul>
      </ResourceState>
    </Panel>
  );
}

export default function DictationPage() {
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
    <div className="page-wrap">
      <PageHero eyebrow="Daily cockpit" title="Dictation">
        Readiness first, active work second, expert depth when you ask for it.
      </PageHero>
      <Tabs
        label="Dictation sections"
        tabs={TABS}
        active={active}
        onChange={setActive}
      />
      {current}
    </div>
  );
}
