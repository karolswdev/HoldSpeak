import { useCallback, useEffect, useState } from "react";
import type { WriteAttempt } from "../hooks/useWriteReceipt";
import type { AutomationHistoryEntry, AutomationTestResult, WorkbenchAutomation } from "../detail-types";
import {
  createWorkbenchAutomation,
  fetchWorkbenchAutomationHistory,
  fetchWorkbenchAutomations,
  setWorkbenchAutomationEnabled,
  testWorkbenchAutomation,
} from "../api";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceState } from "../surface/Surface";
import { humanTime } from "../surface/format";
import { StringGadget } from "../surface/gadgets";

const PRESETS = [
  {
    id: "github-review-requested" as const,
    label: "GitHub · Review requested",
    detail: "Add a grounded review item when a review is requested.",
    available: true,
  },
  {
    id: "jira-assigned-to-me" as const,
    label: "Jira · Assigned to me",
    detail: "Requires the Jira adapter in Settings.",
    available: false,
  },
];

function providerLabel(provider: WorkbenchAutomation["provider"]): string {
  return provider === "github" ? "GITHUB" : provider === "jira" ? "JIRA" : "EVENT";
}

function statusTone(status: WorkbenchAutomation["status"]): "ok" | "warn" | "fail" {
  return status === "active" ? "ok" : status === "attention" || status === "unavailable" ? "fail" : "warn";
}

function historyTone(outcome: AutomationHistoryEntry["outcome"]): "ok" | "warn" | "fail" {
  return outcome === "added" ? "ok" : outcome === "skipped" ? "warn" : "fail";
}

function AutomationHistory({ workbenchId, automationId }: { workbenchId: string; automationId: string }) {
  const [history, setHistory] = useState<AutomationHistoryEntry[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let live = true;
    void fetchWorkbenchAutomationHistory(workbenchId, automationId)
      .then((items) => {
        if (!live) return;
        setHistory(items);
        setError("");
      })
      .catch(() => { if (live) setError("Automation history unavailable"); });
    return () => { live = false; };
  }, [workbenchId, automationId]);

  if (error) return <SurfaceState error={error} />;
  if (!history.length) return <SurfaceState empty emptyGlyph="○" emptyLabel="No receipts yet" />;
  return (
    <SurfaceLedger count={`${history.length} RECEIPTS`}>
      {history.map((entry) => (
        <SurfaceLedgerRow
          key={entry.id}
          time={humanTime(entry.occurred_at)}
          primary={`${entry.event_kind} · ${entry.subject}`}
          cells={<span className="desk-chip" data-tone={historyTone(entry.outcome)}>{entry.outcome.toUpperCase()}</span>}
        >
          <dl className="surface-facts wb-automation-history-detail">
            {entry.receipt_id ? <div><dt>receipt</dt><dd>{entry.receipt_id}</dd></div> : null}
            {entry.detail ? <div><dt>detail</dt><dd>{entry.detail}</dd></div> : null}
          </dl>
        </SurfaceLedgerRow>
      ))}
    </SurfaceLedger>
  );
}

function AutomationRow({
  workbenchId,
  automation,
  write,
  onChanged,
}: {
  workbenchId: string;
  automation: WorkbenchAutomation;
  write: WriteAttempt;
  onChanged: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [testResult, setTestResult] = useState<AutomationTestResult | null>(null);
  const [baselineMessage, setBaselineMessage] = useState("");
  const adapterReady = automation.adapter_status === undefined || automation.adapter_status === "ready";
  const enableReason = adapterReady
    ? "Enable establishes a silent baseline; later matches add one item."
    : "Configure this adapter in Settings before enabling.";

  return (
    <div className="wb-automation">
      <button type="button" className="wb-automation-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="wb-automation-provider">{providerLabel(automation.provider)}</span>
        <span className="wb-automation-title">{automation.name}</span>
        <span className="desk-chip" data-tone={statusTone(automation.status)}>{automation.status.toUpperCase()}</span>
        <span aria-hidden="true">{open ? "▴" : "▾"}</span>
      </button>
      <p className="wb-automation-summary">WHEN {automation.event_kind} · ADD ITEM ONLY</p>
      {open ? (
        <div className="wb-automation-detail">
          <p className="wb-automation-safety">A test never adds work or advances the baseline. Enable creates a silent baseline; later matching events add one grounded item.</p>
          <div className="wb-automation-verbs">
            <button
              type="button"
              className="desk-chip"
              disabled={!adapterReady}
              title={adapterReady ? "Test matching without adding an item" : enableReason}
              onClick={() => void write("TEST AUTOMATION", async () => {
                const result = await testWorkbenchAutomation(workbenchId, automation.id);
                setTestResult(result);
                onChanged();
              })}
            >
              Test match
            </button>
            <button
              type="button"
              className="desk-chip"
              data-tone={automation.enabled ? "warn" : "ok"}
              disabled={!automation.enabled && !adapterReady}
              title={automation.enabled ? "Pause this trigger" : enableReason}
              onClick={() => void write(automation.enabled ? "PAUSE AUTOMATION" : "ENABLE AUTOMATION", async () => {
                await setWorkbenchAutomationEnabled(workbenchId, automation.id, !automation.enabled);
                setBaselineMessage(automation.enabled ? "" : "BASELINE ESTABLISHED · NO PAST ACTIVITY FIRED");
                onChanged();
              })}
            >
              {automation.enabled ? "Pause" : "Enable"}
            </button>
          </div>
          {testResult ? <p className="wb-automation-test" role="status">TEST ONLY · NO ITEMS ADDED · {testResult.would_add} MATCH{testResult.would_add === 1 ? "" : "ES"} FROM {testResult.entity_count} OBSERVED</p> : null}
          {baselineMessage ? <p className="wb-automation-test" role="status">{baselineMessage}</p> : null}
          {automation.last_error ? <SurfaceState error={automation.last_error} /> : null}
          {automation.last_good_at ? <p className="wb-automation-last">Last good {humanTime(automation.last_good_at)}</p> : null}
          {!adapterReady ? <p className="wb-automation-adapter">Adapter {automation.adapter_status?.replace("_", " ")}. Configure credentials and readiness in Settings.</p> : null}
          <AutomationHistory workbenchId={workbenchId} automationId={automation.id} />
        </div>
      ) : null}
    </div>
  );
}

/** The event branch of the Workbench's STARTS WHEN configuration. It
 * intentionally does not expose an auto-run mode in V1. */
export function WorkbenchAutomations({ workbenchId, write, onChanged }: { workbenchId: string; write: WriteAttempt; onChanged?: () => void }) {
  const [automations, setAutomations] = useState<WorkbenchAutomation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [repository, setRepository] = useState("");

  const refresh = useCallback(() => {
    setLoading(true);
    void fetchWorkbenchAutomations(workbenchId)
      .then((items) => { setAutomations(items); setError(""); })
      .catch(() => setError("Automations unavailable"))
      .finally(() => setLoading(false));
  }, [workbenchId]);

  const changed = () => {
    refresh();
    onChanged?.();
  };

  useEffect(refresh, [refresh]);

  return (
    <>
      <p className="wb-automation-intro">Observed events can place grounded work here. Enabled sources refresh every 35 minutes by default; they never run the whole Workbench or write to GitHub and Jira.</p>
      <div className="wb-automation-repository">
        <StringGadget
          label="GitHub repository"
          value={repository}
          onChange={setRepository}
          placeholder="OWNER/REPOSITORY"
          mic={false}
        />
      </div>
      <div className="wb-automation-presets" aria-label="Automation presets">
        {PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            className="desk-chip quiet"
            disabled={!preset.available || !repository.trim()}
            title={preset.detail}
            onClick={() => void write("ADD AUTOMATION", async () => {
              await createWorkbenchAutomation(workbenchId, preset.id, repository.trim());
              changed();
            })}
          >
            + {preset.label}{preset.available ? "" : " · SETTINGS REQUIRED"}
          </button>
        ))}
      </div>
      {!repository.trim() ? <p className="wb-automation-requirement">Repository required to add a GitHub trigger.</p> : null}
      {loading ? <SurfaceState loading /> : null}
      {error ? <SurfaceState error={error} onRetry={refresh} /> : null}
      {!loading && !error && !automations.length ? <SurfaceState empty emptyGlyph="◇" emptyLabel="No event triggers yet" /> : null}
      {!loading && !error ? <div className="wb-automations-list">{automations.map((automation) => <AutomationRow key={automation.id} workbenchId={workbenchId} automation={automation} write={write} onChanged={changed} />)}</div> : null}
    </>
  );
}
