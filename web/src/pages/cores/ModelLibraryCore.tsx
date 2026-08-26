import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { Button } from "../../components/signal/Signal";
import { readableError, newDeliveryId } from "../../lib/api";
import {
  EgressChip,
  FoldGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
import {
  SurfaceFacts,
  SurfaceSplit,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import {
  addDetectedModel,
  connectHostedModel,
  defineEndpoint,
  downloadModel,
  getModelLibrary,
  useModelFile,
  type ModelLibraryProjection,
  type ModelLibraryReceipt,
  type ModelLibraryRow,
} from "./modelLibrary";

const SUCCESS_COPY = "Added to the Model Library. Assignments are unchanged.";
const SOURCES = [
  ["all", "All"],
  ["device", "This device"],
  ["connected", "Connected"],
  ["available", "Available"],
] as const;
type Source = (typeof SOURCES)[number][0];
type AddFace = "inventory" | "choices" | "hosted" | "endpoint" | "file";

function sourceRows(rows: ModelLibraryRow[], source: Source): ModelLibraryRow[] {
  if (source === "all") return rows;
  const members: Record<Exclude<Source, "all">, string[]> = {
    device: ["detected", "installed", "acquiring"],
    connected: ["provider", "profile"],
    available: ["catalog", "detected", "legacy"],
  };
  return rows.filter((row) => members[source].includes(row.source));
}

function sourceCount(rows: ModelLibraryRow[], source: Source): number {
  return sourceRows(rows, source).length;
}

function statusWord(status: string): string {
  return status.replace(/[_-]+/g, " ");
}

function statusTone(status: string): "ok" | "warn" | "fail" | "quiet" {
  if (status === "ready") return "ok";
  if (["broken", "unavailable"].includes(status)) return "fail";
  if (["available", "detected", "configured", "acquiring"].includes(status)) return "warn";
  return "quiet";
}

function profileId(label: string, fallback: string): string {
  const normalized = label
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 75);
  return `library-${normalized || fallback}`;
}

function providerBoundary(face: AddFace, selected: ModelLibraryRow | null): boolean {
  return face === "hosted" || face === "endpoint" || selected?.source === "provider";
}

/** Host-agnostic availability glass. It consumes only ModelLibraryProjection@1. */
export function ModelLibraryCore() {
  const groupName = useId();
  const [projection, setProjection] = useState<ModelLibraryProjection | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [receipt, setReceipt] = useState("");
  const [source, setSource] = useState<Source>("all");
  const [selectedId, setSelectedId] = useState("");
  const [face, setFace] = useState<AddFace>("inventory");
  const [busy, setBusy] = useState(false);
  const [hosted, setHosted] = useState({ label: "", model: "", family: "openrouter" as "openrouter" | "anthropic" });
  const [endpoint, setEndpoint] = useState({
    label: "",
    model: "",
    url: "",
    family: "openai_compatible" as "openai_compatible" | "private_endpoint" | "future_backend",
  });
  const [file, setFile] = useState<File | null>(null);
  const secretRef = useRef<HTMLInputElement>(null);
  const addTriggerRef = useRef<HTMLButtonElement>(null);
  const addFaceRef = useRef<HTMLElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);
  const restoreAddFocus = useRef(false);
  const rowRefs = useRef<Record<string, HTMLInputElement | null>>({});

  const reload = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      setProjection(await getModelLibrary());
    } catch (error) {
      setLoadError(readableError(error));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const allRows = projection?.rows ?? [];
  const visibleRows = useMemo(() => sourceRows(allRows, source), [allRows, source]);
  const selected = visibleRows.find((row) => row.id === selectedId) ?? visibleRows[0] ?? null;
  // Header truth is closed and projected by the aggregate; this surface never
  // infers readiness from a local count (an empty library is an invitation).
  const summary = projection?.summary ?? null;

  useEffect(() => {
    if (selected?.id && selected.id !== selectedId) setSelectedId(selected.id);
  }, [selected, selectedId]);

  useEffect(() => {
    if (face !== "inventory" || !restoreAddFocus.current) return;
    restoreAddFocus.current = false;
    if (restoreFocusRef.current?.classList.contains("model-library-add-trigger")) {
      addTriggerRef.current?.focus();
    } else {
      restoreFocusRef.current?.focus();
    }
  }, [face]);

  useEffect(() => {
    // The trigger unmounts when the in-world flow opens. Move focus inside it
    // so Escape remains a real keyboard exit rather than falling onto body.
    if (face !== "inventory") addFaceRef.current?.focus();
  }, [face]);

  const showReceipt = (result: ModelLibraryReceipt) => {
    const message = result.receipt?.message;
    if (message !== SUCCESS_COPY) throw new Error("Model Library receipt was incomplete.");
    setReceipt(message);
    setActionError("");
  };

  const finish = async (operation: () => Promise<ModelLibraryReceipt>) => {
    setBusy(true);
    setActionError("");
    try {
      showReceipt(await operation());
      setFace("inventory");
      setFile(null);
      await reload();
    } catch (error) {
      setActionError(readableError(error));
    } finally {
      setBusy(false);
    }
  };

  const invokeSelected = useCallback(async () => {
    if (!projection || !selected || busy) return;
    const action = selected.selected_action;
    if (action === "Ready" || action === "Checking") return;
    if (action === "Download" && selected.id.startsWith("catalog:")) {
      await finish(() => downloadModel(selected.id.slice("catalog:".length), projection.catalog_revision));
      return;
    }
    if (action === "Add to library" && selected.id.startsWith("detected:")) {
      await finish(() => addDetectedModel(selected.id.slice("detected:".length)));
      return;
    }
    setFace(selected.source === "provider" ? "hosted" : "choices");
  // `finish` deliberately stays locally stable enough for a keyboard action;
  // it only closes over setters and `reload`.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projection, selected, busy]);

  const openChoices = (target: HTMLButtonElement) => {
    addTriggerRef.current = target;
    restoreFocusRef.current = target;
    setReceipt("");
    setActionError("");
    setFace("choices");
  };

  const leaveAdd = () => {
    restoreAddFocus.current = true;
    setFace("inventory");
  };

  const moveSelection = (event: KeyboardEvent<HTMLDivElement>) => {
    const keys: Record<string, number> = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 };
    if (!(event.key in keys) || !visibleRows.length) return;
    event.preventDefault();
    const current = Math.max(0, visibleRows.findIndex((row) => row.id === selected?.id));
    const index = (current + keys[event.key] + visibleRows.length) % visibleRows.length;
    const next = visibleRows[index];
    setSelectedId(next.id);
    requestAnimationFrame(() => rowRefs.current[next.id]?.focus());
  };

  const connectHosted = async () => {
    const key = secretRef.current?.value ?? "";
    if (!hosted.label.trim() || !hosted.model.trim() || !key.trim()) {
      setActionError("Name, model, and key are required.");
      return;
    }
    setBusy(true);
    setActionError("");
    try {
      const result = await connectHostedModel(
        {
          request_id: newDeliveryId(),
          profile_id: profileId(hosted.label, "hosted"),
          expected_profile_revision: 0,
          label: hosted.label.trim(),
          provider_family: hosted.family,
          model: hosted.model.trim(),
          requires_key: true,
        },
        key,
      );
      if (!result.provider?.secret.present) throw new Error("Provider key was not confirmed.");
      if (secretRef.current) secretRef.current.value = "";
      showReceipt(result);
      setFace("inventory");
      await reload();
    } catch (error) {
      setActionError(readableError(error));
    } finally {
      setBusy(false);
    }
  };

  const submitEndpoint = async () => {
    const key = secretRef.current?.value ?? "";
    if (!endpoint.label.trim() || !endpoint.model.trim() || !endpoint.url.trim()) {
      setActionError("Name, endpoint, and model are required.");
      return;
    }
    setBusy(true);
    setActionError("");
    try {
      const result = await defineEndpoint(
        {
          request_id: newDeliveryId(),
          profile_id: profileId(endpoint.label, "endpoint"),
          expected_profile_revision: 0,
          label: endpoint.label.trim(),
          provider_family: endpoint.family,
          model: endpoint.model.trim(),
          endpoint: endpoint.url.trim(),
          requires_key: Boolean(key.trim()),
        },
        key.trim() || null,
      );
      if (key.trim() && !result.provider?.secret.present) throw new Error("Provider key was not confirmed.");
      if (secretRef.current) secretRef.current.value = "";
      showReceipt(result);
      setFace("inventory");
      await reload();
    } catch (error) {
      setActionError(readableError(error));
    } finally {
      setBusy(false);
    }
  };

  const submitFile = async () => {
    if (!file) {
      setActionError("Choose a model file.");
      return;
    }
    await finish(() => useModelFile(file));
  };

  const activePrimary = () => {
    if (face === "hosted") return connectHosted;
    if (face === "endpoint") return submitEndpoint;
    if (face === "file") return submitFile;
    return invokeSelected;
  };

  const onSurfaceKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape" && face !== "inventory") {
      event.preventDefault();
      leaveAdd();
      return;
    }
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      void activePrimary()();
    }
  };

  const detail = selected ? (
    <aside className="model-library-detail" aria-live="polite">
      <div className="model-library-detail-head">
        <span className="model-library-status" data-tone={statusTone(selected.status)}>
          {statusWord(selected.status)}
        </span>
        <h3>{selected.label}</h3>
        {selected.repair && selected.repair.label !== selected.selected_action ? <p className="model-library-repair">{selected.repair.label}</p> : null}
      </div>
      {providerBoundary(face, selected) ? (
        <EgressChip label="Egress" scope="cloud" title="Provider request leaves this hub." />
      ) : null}
      <FoldGadget title="Providers" token={selected.source === "provider" ? "connected" : "library"}>
        <span className="model-library-provider-fact">{selected.source === "provider" ? "Connected provider" : "Provider custody"}</span>
      </FoldGadget>
      {projection ? (
        <FoldGadget title="Runs on" token={projection.artifact_detection.state}>
          <SurfaceFacts value={{ source: selected.source, artifact_detection: projection.artifact_detection.state }} />
        </FoldGadget>
      ) : null}
      <FoldGadget title="RAW" token="Details">
        <SurfaceFacts value={selected.detail} />
      </FoldGadget>
      <div className="model-library-action-seat" data-action={selected.selected_action}>
        {selected.selected_action === "Ready" || selected.selected_action === "Checking" ? (
          <span aria-live="polite">{selected.selected_action}</span>
        ) : (
          <Button
            variant="primary"
            loading={busy}
            disabled={busy}
            onClick={() => void invokeSelected()}
          >
            {selected.selected_action}
          </Button>
        )}
      </div>
    </aside>
  ) : null;

  const chooseCatalog = () => {
    setSource("available");
    setFace("inventory");
  };

  const addChoices = (
    <div className="model-library-add-choices">
      <button type="button" onClick={chooseCatalog}>Download from catalog</button>
      <button type="button" onClick={() => setFace("hosted")}>Connect hosted model</button>
      <button type="button" onClick={() => setFace("endpoint")}>Define endpoint</button>
      <button type="button" onClick={() => setFace("file")}>Use model file</button>
    </div>
  );

  const addFace = face === "choices" ? (
    <section ref={addFaceRef} tabIndex={-1} className="model-library-add" aria-label="Add model">
      <header>
        <h2>Add model</h2>
        <button type="button" className="model-library-back" onClick={leaveAdd}>Back</button>
      </header>
      {addChoices}
    </section>
  ) : face === "hosted" ? (
    <section ref={addFaceRef} tabIndex={-1} className="model-library-add" aria-label="Connect hosted model">
      <header><h2>Connect hosted model</h2><button type="button" className="model-library-back" onClick={leaveAdd}>Back</button></header>
      <div className="model-library-form">
        <EgressChip label="Egress" scope="cloud" title="Provider request leaves this hub." />
        <StringGadget label="Provider name" value={hosted.label} onChange={(label) => setHosted((current) => ({ ...current, label }))} placeholder="Provider model" />
        <StringGadget label="Model" value={hosted.model} onChange={(model) => setHosted((current) => ({ ...current, model }))} placeholder="Model" />
        <label className="model-library-select"><span>Provider</span><select aria-label="Hosted provider" value={hosted.family} onChange={(event) => setHosted((current) => ({ ...current, family: event.target.value as typeof hosted.family }))}><option value="openrouter">OpenRouter</option><option value="anthropic">Anthropic</option></select></label>
        <label className="model-library-secret"><span>Provider key</span><input ref={secretRef} type="password" autoComplete="new-password" aria-label="Provider key" /></label>
        <Button variant="primary" loading={busy} disabled={busy} onClick={() => void connectHosted()}>Connect</Button>
      </div>
    </section>
  ) : face === "endpoint" ? (
    <section ref={addFaceRef} tabIndex={-1} className="model-library-add" aria-label="Define endpoint">
      <header><h2>Define endpoint</h2><button type="button" className="model-library-back" onClick={leaveAdd}>Back</button></header>
      <div className="model-library-form">
        <EgressChip label="Egress" scope="cloud" title="Provider request leaves this hub." />
        <StringGadget label="Provider name" value={endpoint.label} onChange={(label) => setEndpoint((current) => ({ ...current, label }))} placeholder="Provider model" />
        <StringGadget label="Endpoint" value={endpoint.url} onChange={(url) => setEndpoint((current) => ({ ...current, url }))} placeholder="https://…/v1" />
        <StringGadget label="Model" value={endpoint.model} onChange={(model) => setEndpoint((current) => ({ ...current, model }))} placeholder="Model" />
        <label className="model-library-select"><span>Provider</span><select aria-label="Endpoint provider" value={endpoint.family} onChange={(event) => setEndpoint((current) => ({ ...current, family: event.target.value as typeof endpoint.family }))}><option value="openai_compatible">OpenAI-compatible</option><option value="private_endpoint">Private endpoint</option><option value="future_backend">Future backend</option></select></label>
        <label className="model-library-secret"><span>Provider key</span><input ref={secretRef} type="password" autoComplete="new-password" aria-label="Provider key" /></label>
        <Button variant="primary" loading={busy} disabled={busy} onClick={() => void submitEndpoint()}>Add model</Button>
      </div>
    </section>
  ) : face === "file" ? (
    <section ref={addFaceRef} tabIndex={-1} className="model-library-add" aria-label="Use model file">
      <header><h2>Use model file</h2><button type="button" className="model-library-back" onClick={leaveAdd}>Back</button></header>
      <div className="model-library-form">
        <label className="model-library-file"><span>Model file</span><input type="file" accept=".gguf,.mlx" aria-label="Model file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></label>
        <Button variant="primary" loading={busy} disabled={busy || !file} onClick={() => void submitFile()}>Add to library</Button>
      </div>
    </section>
  ) : null;

  return (
    <div className="model-library" onKeyDown={onSurfaceKeyDown}>
      <SurfaceVerbs status={summary ? <span className="model-library-summary" data-state={summary.state} role="status">{summary.label}</span> : null}>
        {face === "inventory" && allRows.length ? <button ref={addTriggerRef} type="button" className="model-library-add-trigger" onClick={(event) => openChoices(event.currentTarget)}>+ Add model</button> : null}
      </SurfaceVerbs>
      {receipt ? <div className="model-library-receipt" role="status">{receipt}</div> : null}
      {actionError ? <SurfaceState error={actionError} /> : null}
      {loading ? <SurfaceState loading /> : loadError ? <SurfaceState error={loadError} onRetry={() => void reload()} /> : addFace ? addFace : (
        <SurfaceSplit
          detailOpen={Boolean(selected)}
          main={
            <section className="model-library-inventory" aria-labelledby="model-library-title">
              <header className="model-library-title">
                <div><h2 id="model-library-title">Model Library</h2><span>{allRows.length} models</span></div>
                {summary ? <span className="model-library-status" data-state={summary.state}>{summary.label}</span> : null}
              </header>
              <div className="model-library-tabs" role="tablist" aria-label="Model source">
                {SOURCES.map(([value, label]) => <button key={value} type="button" role="tab" aria-selected={source === value} onClick={() => setSource(value)}>{label} <span>{sourceCount(allRows, value)}</span></button>)}
              </div>
              {visibleRows.length ? (
                <div className="model-library-rows" role="radiogroup" aria-label="Model Library" onKeyDown={moveSelection}>
                  {visibleRows.map((row) => {
                    const selectedRow = row.id === selected?.id;
                    return <label key={row.id} className="model-library-row" data-selected={selectedRow || undefined} data-tone={statusTone(row.status)}>
                      <input ref={(element) => { rowRefs.current[row.id] = element; }} type="radio" name={groupName} value={row.id} checked={selectedRow} onChange={() => setSelectedId(row.id)} />
                      <span className="model-library-row-copy"><strong>{row.label}</strong><small>{row.source} · {statusWord(row.status)}</small></span>
                      <span className="model-library-row-action">{row.selected_action}</span>
                    </label>;
                  })}
                </div>
              ) : (
                <SurfaceState
                  empty
                  emptyContent={
                    <section className="model-library-empty" aria-labelledby="model-library-empty-title">
                      <h3 id="model-library-empty-title">Add model</h3>
                      {addChoices}
                    </section>
                  }
                />
              )}
            </section>
          }
          detail={detail}
        />
      )}
    </div>
  );
}
