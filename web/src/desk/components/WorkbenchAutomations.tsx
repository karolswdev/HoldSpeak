import { useCallback, useEffect, useState } from "react";
import { Button } from "../../components/signal/Signal";
import type { WriteAttempt } from "../hooks/useWriteReceipt";
import type { AutomationHistoryEntry, AutomationTestResult, WorkbenchAutomation } from "../detail-types";
import {
  createWorkbenchAutomation,
  fetchWorkbenchAutomationHistory,
  fetchWorkbenchAutomations,
  setWorkbenchAutomationEnabled,
  testWorkbenchAutomation,
} from "../api";
import { countLabel } from "../surface";
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
    <SurfaceLedger count={countLabel("RECEIPTS", history.length)}>
      {history.map((entry) => {
        const eventKind = entry.event_kind;
        const receiptId = entry.receipt_id;
        return (
        <SurfaceLedgerRow
          key={entry.id}
          time={humanTime(entry.occurred_at)}
          primary={`${eventKind} · ${entry.subject}`}
          cells={<span className="desk-chip" data-tone={historyTone(entry.outcome)}>{entry.outcome.toUpperCase()}</span>}
        >
          <dl className="surface-facts wb-automation-history-detail">
            {receiptId ? <div><dt>receipt</dt><dd>{receiptId}</dd></div> : null}
            {entry.detail ? <div><dt>detail</dt><dd>{entry.detail}</dd></div> : null}
          </dl>
        </SurfaceLedgerRow>
        );
      })}
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
  const wouldAdd = testResult?.would_add;
  const entityCt = testResult?.entity_count;
  const [baselineMessage, setBaselineMessage] = useState("");
  const eventKind = automation.event_kind;
  const adapterStatus = automation.adapter_status;
  const lastGoodAt = automation.last_good_at;
  const adapterReady = adapterStatus === undefined || adapterStatus === "ready";
  const enableReason = adapterReady
    ? "Enable establishes a silent baseline; later matches add one item."
    : "Configure this adapter in Settings before enabling.";

  return (
    <div className="wb-automation">
      <Button variant="ghost" className="wb-automation-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="egress-badge is-cloud" title={providerLabel(automation.provider)}>{providerLabel(automation.provider)}</span>
        <span className="wb-automation-title">{automation.name}</span>
        <span className="desk-chip" data-tone={statusTone(automation.status)}>{automation.status.toUpperCase()}</span>
        <span aria-hidden="true">{open ? "▴" : "▾"}</span>
      </Button>
      <span className="wb-automation-summary surface-token">{`WHEN ${eventKind} · ADD ITEM ONLY`}</span>
      {open ? (
        <div className="wb-automation-detail">
          <span className="wb-automation-safety surface-token">SILENT BASELINE · MATCH ADDS ONE ITEM</span>
          <div className="wb-automation-verbs">
            <Button
              dense
              variant="ghost"
              disabled={!adapterReady}
              title={adapterReady ? "Test matching without adding an item" : enableReason}
              onClick={() => void write("TEST AUTOMATION", async () => {
                const result = await testWorkbenchAutomation(workbenchId, automation.id);
                setTestResult(result);
                onChanged();
              })}
            >
              Test match
            </Button>
            <Button
              dense
              disabled={!automation.enabled && !adapterReady}
              title={automation.enabled ? "Pause this trigger" : enableReason}
              onClick={() => void write(automation.enabled ? "PAUSE AUTOMATION" : "ENABLE AUTOMATION", async () => {
                await setWorkbenchAutomationEnabled(workbenchId, automation.id, !automation.enabled);
                setBaselineMessage(automation.enabled ? "" : "BASELINE ESTABLISHED");
                onChanged();
              })}
            >
              {automation.enabled ? "Pause" : "Enable"}
            </Button>
          </div>
          {testResult ? <span className="wb-automation-test surface-token" role="status">{`TEST · ${wouldAdd} MATCH${wouldAdd === 1 ? "" : "ES"} / ${entityCt} OBSERVED`}</span> : null}
          {baselineMessage ? <p className="wb-automation-test" role="status">{baselineMessage}</p> : null}
          {automation.last_error ? <SurfaceState error={automation.last_error} /> : null}
          {lastGoodAt ? <span className="wb-automation-last surface-token">{`LAST GOOD ${humanTime(lastGoodAt)}`}</span> : null}
          {!adapterReady ? <span className="wb-automation-adapter surface-token" data-tone="warn">{`ADAPTER ${(adapterStatus || "").replace("_", " ").toUpperCase()}`}</span> : null}
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
      <span className="wb-automation-safety surface-token">EVENT TRIGGER · READ-ONLY · 35 MIN REFRESH</span>
      <div className="wb-automation-repository">
        <StringGadget
          label="GitHub repository"
          value={repository}
          onChange={setRepository}
          placeholder="OWNER/REPOSITORY"
          mic={true}
        />
      </div>
      <div className="wb-automation-presets" aria-label="Automation presets">
        {PRESETS.map((preset) => (
          <Button
            key={preset.id}
            dense
            variant="ghost"
            disabled={!preset.available || !repository.trim()}
            title={preset.detail}
            onClick={() => void write("ADD AUTOMATION", async () => {
              await createWorkbenchAutomation(workbenchId, preset.id, repository.trim());
              changed();
            })}
          >
            + {preset.label}{preset.available ? "" : " · SETTINGS REQUIRED"}
          </Button>
        ))}
      </div>
      {!repository.trim() ? <span className="wb-automation-requirement surface-token">REPOSITORY REQUIRED</span> : null}
      {loading ? <SurfaceState loading /> : null}
      {error ? <SurfaceState error={error} onRetry={refresh} /> : null}
      {!loading && !error && !automations.length ? <SurfaceState empty emptyGlyph="◇" emptyLabel="No event triggers yet" /> : null}
      {!loading && !error ? <div className="wb-automations-list">{automations.map((automation) => <AutomationRow key={automation.id} workbenchId={workbenchId} automation={automation} write={write} onChanged={changed} />)}</div> : null}
    </>
  );
}
