// HS-170-03 — The Concierge: one screen for engine discovery + assignment.
// Its own surface window (not inside Settings). Every verb is the library Button.

import { useContext, useEffect } from "react";
import {
  SurfaceLedgerRow,
  SurfaceFooter,
  StateChip,
  EgressChip,
  ChoiceCardShell,
  StringGadget,
  countToken,
} from "../../desk/surface";
import { Button } from "../../components/signal/Signal";
import { TitleSlotContext } from "../../desk/surface/title";
import type { CoreProps } from "../../pages/cores/core-types";
import {
  useConciergeController,
  kindEmblem,
  humanSize,
  hardwareToken,
  latencyToken,
  engineHostLabel,
  engineHostScope,
  GROUP_GLYPHS,
  type ConciergeController,
  type FoundRow,
  type SetRow,
} from "./useConciergeController";
import type { Engine } from "./api";
import "./concierge.css";

/* ── Found engine row ── */

function FoundEngineRow({
  row,
  ctrl,
}: {
  row: FoundRow;
  ctrl: ConciergeController;
}) {
  const { engine } = row;
  const emblem = kindEmblem(engine.kind);
  const latency = latencyToken(engine.latencyMs);
  const size = humanSize(engine.sizeBytes);
  const hostLabel = engineHostLabel(engine);
  const hostScope = engineHostScope(engine);

  const isReady = engine.state === "READY";
  const isNotSet = engine.state === "NOT_SET";
  const isUnreachable = engine.state === "UNREACHABLE";
  const isWaiting = engine.state === "WAITING";
  const isCloud = engine.kind === "cloud";
  const isPreset = engine.kind === "preset" && !isReady;

  return (
    <SurfaceLedgerRow
      lead={<span className="concierge-lead">{emblem}</span>}
      primary={
        <span className="concierge-engine-name">{engine.name}</span>
      }
      cells={
        <span className="concierge-found-cells">
          {/* Line 1 tokens: latency, size, runtime, key */}
          {latency ? <span className="concierge-token">{latency}</span> : null}
          {size ? <span className="concierge-token">{size}</span> : null}
          {engine.runtimeToken ? <span className="concierge-token">{engine.runtimeToken}</span> : null}
          {isCloud && engine.keySet === true ? (
            <span className="concierge-key-chip" data-set data-testid="key-chip-set">KEY SET</span>
          ) : null}
          {isCloud && engine.keySet === false ? (
            <span className="concierge-key-chip" data-not-set data-testid="key-chip-not-set">KEY NOT SET</span>
          ) : null}
          {isCloud && engine.keySet ? (
            <span className="concierge-cloud-actions">
              <Button dense variant="ghost" onClick={(e: React.MouseEvent) => { e.stopPropagation(); ctrl.checkCloud(engine.id); }} data-testid={`concierge-check-${engine.id}`}>Check</Button>
              <span className="concierge-cost-chip">1 TOKEN · $</span>
            </span>
          ) : null}
          {isPreset && !row.downloading ? (
            <span className="concierge-cloud-actions">
              <Button dense variant="primary" onClick={(e: React.MouseEvent) => { e.stopPropagation(); if (engine.presetId) ctrl.downloadPreset(engine.presetId); }} data-testid={`concierge-download-${engine.id}`}>Download</Button>
            </span>
          ) : null}
          {row.downloading && row.progress ? (
            <span className="concierge-progress-token" data-testid={`concierge-progress-${engine.id}`}>
              {humanSize(row.progress.received)} / {humanSize(row.progress.total)}
            </span>
          ) : null}
          {/* State chip: right-aligned on line 1 */}
          <span className="concierge-found-state">
            {isReady ? <StateChip state="success" label="READY" icon="●" />
            : isNotSet ? <StateChip state="warning" label="KEY NOT SET" />
            : isUnreachable ? <StateChip state="failure" label="UNREACHABLE" />
            : isWaiting ? <StateChip state="idle" label="WAITING" icon="○" />
            : null}
          </span>
          {/* Line 2: host chip */}
          <span className="concierge-found-line2">
            <EgressChip label={hostLabel} scope={hostScope} />
          </span>
        </span>
      }
      expands={false}
      wrap
      data-testid={`concierge-found-${engine.id}`}
    />
  );
}

/* ── Set row (per capability group) ── */

function SetGroupRow({
  row,
  ctrl,
  engines,
}: {
  row: SetRow;
  ctrl: ConciergeController;
  engines: Engine[];
}) {
  const glyph = GROUP_GLYPHS[row.group] ?? "○";
  const engine = engines.find((e) => e.id === row.engineId);
  const engineName = row.engineId === "OFF" ? "—" : engine?.name ?? "—";
  const isOff = row.engineId === "OFF" || row.engineId === null;
  const latency = engine ? latencyToken(engine.latencyMs) : null;
  const hostLabel = engine ? engineHostLabel(engine) : row.host.toUpperCase() || "";

  return (
    <SurfaceLedgerRow
      lead={<span className="concierge-group-glyph">{glyph}</span>}
      primary={<span className="concierge-group-name">{row.label}</span>}
      cells={
        <span className="concierge-set-cells">
          <Button
            dense variant="ghost" className="concierge-picker-trigger"
            onClick={(e: React.MouseEvent) => { e.stopPropagation(); row.pickerOpen ? ctrl.closePicker(row.group) : ctrl.openPicker(row.group); }}
            data-testid={`concierge-picker-${row.group}`}
          >
            {engineName}
            <svg className="concierge-chevron" viewBox="0 0 12 12" aria-hidden="true">
              <path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </Button>
          {/* State chip: right-aligned on line 1 */}
          <span className="concierge-set-state">
            {row.state === "READY" ? <StateChip state="success" label="READY" icon="●" />
            : row.state === "CHECKING" ? <StateChip state="working" label="CHECKING" icon="○" />
            : row.state === "WAITING" ? <StateChip state="warning" label="WAITING" icon="○" />
            : row.state === "NOT_SET" ? <StateChip state="warning" label="KEY NOT SET" />
            : null}
          </span>
          {/* Line 2: latency + host */}
          <span className="concierge-set-line2">
            {!isOff && latency ? <span className="concierge-token">{latency}</span> : null}
            {!isOff && hostLabel ? <EgressChip label={hostLabel} scope={engine ? engineHostScope(engine) : "local"} /> : null}
          </span>
        </span>
      }
      open={row.pickerOpen}
      onToggle={() => { row.pickerOpen ? ctrl.closePicker(row.group) : ctrl.openPicker(row.group); }}
      wrap
      data-testid={`concierge-set-${row.group}`}
    >
      {row.pickerOpen ? <PickerWell row={row} ctrl={ctrl} engines={engines} /> : null}
    </SurfaceLedgerRow>
  );
}

/* ── Picker well: ChoiceCard items, in-world, no dialog ── */

function PickerWell({ row, ctrl, engines }: { row: SetRow; ctrl: ConciergeController; engines: Engine[] }) {
  const alts = row.alternatives;
  return (
    <div className="concierge-picker-well" data-testid={`concierge-picker-well-${row.group}`}>
      {alts.map((alt) => {
        const latency = latencyToken(alt.latencyMs);
        const size = humanSize(alt.sizeBytes);
        const isPreset = alt.kind === "preset";
        const isCloud = alt.kind === "cloud";
        return (
          <ChoiceCardShell key={alt.id} as="div" selected={row.engineId === alt.id}>
            <Button
              dense variant="ghost" className="concierge-picker-card"
              onClick={() => ctrl.pickEngine(row.group, alt.id)}
              data-testid={`concierge-pick-${row.group}-${alt.id}`}
            >
              <span className="concierge-picker-card-name">{alt.name}</span>
              <span className="concierge-picker-card-facts">
                {latency ? <span className="concierge-token">{latency}</span> : null}
                {size ? <span className="concierge-token">{size}</span> : null}
                {isPreset ? <span className="concierge-token">DOWNLOAD</span> : null}
                {isCloud && alt.keySet ? (
                  <>
                    <span className="concierge-key-chip" data-set>KEY SET</span>
                    <span className="concierge-cost-chip">$</span>
                  </>
                ) : null}
              </span>
              {!isPreset && !isCloud ? (
                <EgressChip label={engineHostLabel(alt)} scope={engineHostScope(alt)} />
              ) : null}
            </Button>
          </ChoiceCardShell>
        );
      })}
      <ChoiceCardShell as="div">
        <Button
          dense variant="ghost" className="concierge-picker-card"
          onClick={() => ctrl.pickEngine(row.group, "OFF")}
          data-testid={`concierge-pick-${row.group}-off`}
        >
          <span className="concierge-picker-card-name">OFF</span>
        </Button>
      </ChoiceCardShell>
    </div>
  );
}

/* ── Adjust well ── */

function AdjustWell({ ctrl }: { ctrl: ConciergeController }) {
  return (
    <div className="concierge-adjust-well" data-testid="concierge-adjust-well">
      {ctrl.adjustRows.map((r) => (
        <div key={r.capabilityId} className="concierge-adjust-row">
          <span className="concierge-adjust-cap">{r.capabilityId}</span>
          <span className="concierge-adjust-group">{r.group}</span>
          <span className="concierge-adjust-engine">
            {r.engineName}
            <svg className="concierge-chevron" viewBox="0 0 12 12" aria-hidden="true">
              <path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </span>
          <span className="concierge-adjust-host">
            <EgressChip label={r.host} scope="local" />
          </span>
        </div>
      ))}
    </div>
  );
}

/* ── ConciergeCore ── */

export function ConciergeCore({ scope }: CoreProps) {
  const ctrl = useConciergeController();
  const setTitle = useContext(TitleSlotContext);

  useEffect(() => {
    setTitle?.("Models");
  }, [setTitle]);

  if (ctrl.loading) {
    return (
      <div className="concierge-root" data-testid="concierge-root">
        <span className="concierge-token">LOADING</span>
      </div>
    );
  }

  // Headline: "3 engines found" (accent) or "No engine yet" (muted)
  const foundCountToken = countToken(ctrl.foundCount, "engine", "engines");
  const headlineText = foundCountToken ? `${foundCountToken} found` : "No engine yet";
  const isCold = ctrl.foundCount === 0;

  const hwToken = hardwareToken(ctrl.hardware);
  const checkedTime = ctrl.checkedAt
    ? new Date(ctrl.checkedAt).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
    : "";

  // Section label (UX-CANON A8: no counters of zero)
  const foundLabel = ctrl.foundCount > 0 ? `FOUND ${ctrl.foundCount}` : "FOUND";

  // Receipt: `7 GROUPS · 3 ENGINES · 1 WAITING` or `NO ENGINE · SET UP NOTHING`
  // After apply: `3 GROUPS SET · 1 FAILED · <plainReason>`
  const receiptParts: string[] = [];
  if (ctrl.applyFailures.length > 0) {
    const setCount = ctrl.setRows.length - ctrl.applyFailures.length;
    const setToken = countToken(setCount, "GROUP SET", "GROUPS SET");
    const failToken = countToken(ctrl.applyFailures.length, "FAILED");
    if (setToken) receiptParts.push(setToken);
    if (failToken) receiptParts.push(failToken);
    if (ctrl.applyFailures[0]?.plainReason) {
      receiptParts.push(ctrl.applyFailures[0].plainReason);
    }
  } else {
    const groupsToken = countToken(ctrl.receipt.groups, "GROUP");
    const enginesToken = countToken(ctrl.receipt.engines, "ENGINE");
    const waitingToken = countToken(ctrl.receipt.waiting, "WAITING");
    if (groupsToken) receiptParts.push(groupsToken);
    if (enginesToken) receiptParts.push(enginesToken);
    if (waitingToken) receiptParts.push(waitingToken);
  }
  const receiptText = receiptParts.length > 0 ? receiptParts.join(" · ") : "NO ENGINE · SET UP NOTHING";

  return (
    <div className="concierge-root" data-testid="concierge-root">
      {/* 1. Headline — display step (26px/650) */}
      <div>
        <h1
          className={`surface-display concierge-headline${isCold ? " concierge-headline--cold" : ""}`}
          data-testid="concierge-headline"
        >
          {headlineText}
        </h1>
        <div className="concierge-hardware-row">
          <span className="concierge-hardware-token">{hwToken}</span>
          {checkedTime ? <span className="concierge-checked-at">CHECKED {checkedTime}</span> : null}
        </div>
      </div>

      {/* 2. FOUND section */}
      <div className="concierge-section">
        <div className="concierge-section-header">
          <span className="concierge-section-label" data-testid="concierge-found-label">{foundLabel}</span>
        </div>
        <ul className="concierge-found-list" data-testid="concierge-found-list">
          {ctrl.foundRows.map((row) => (
            <FoundEngineRow key={row.engine.id} row={row} ctrl={ctrl} />
          ))}
        </ul>
        {ctrl.addEngineOpen ? (
          <div className="concierge-add-engine-row" data-testid="concierge-add-engine-row">
            <StringGadget
              label="Base URL"
              value={ctrl.addEngineUrl}
              onChange={ctrl.setAddEngineUrl}
              placeholder="http://192.168.1.43:8080/v1"
              autoFocus
            />
            <Button dense variant="ghost" onClick={ctrl.checkNewEngine} disabled={ctrl.addEngineChecking || !ctrl.addEngineUrl.trim()} data-testid="concierge-add-check">Check</Button>
            <Button dense variant="primary" onClick={ctrl.checkNewEngine} disabled={ctrl.addEngineChecking || !ctrl.addEngineUrl.trim()} loading={ctrl.addEngineChecking} data-testid="concierge-add-submit">Add</Button>
          </div>
        ) : (
          <span className="concierge-add-engine" data-testid="concierge-add-engine" role="button" tabIndex={0} onClick={ctrl.addEngine} onKeyDown={(e) => { if (e.key === "Enter") ctrl.addEngine(); }}>
            Add an engine...
          </span>
        )}
      </div>

      {/* 3. THE SET section */}
      <div className="concierge-section">
        <div className="concierge-section-header">
          <span className="concierge-section-label" data-testid="concierge-set-label">THE SET</span>
          <Button dense variant={ctrl.adjustOpen ? "secondary" : "ghost"} className="concierge-adjust-trigger" onClick={ctrl.toggleAdjust} data-testid="concierge-adjust-trigger">Adjust</Button>
        </div>
        <ul className="concierge-set-list" data-testid="concierge-set-list">
          {ctrl.setRows.map((row) => (
            <SetGroupRow key={row.group} row={row} ctrl={ctrl} engines={ctrl.engines} />
          ))}
        </ul>
        {ctrl.adjustOpen ? <AdjustWell ctrl={ctrl} /> : null}
      </div>

      {/* 4. Footer — portaled into the frame's foot slot */}
      <SurfaceFooter
        className="concierge-footer"
        receipt={<span className="concierge-receipt" data-testid="concierge-receipt">{receiptText}</span>}
        verbs={
          <>
            <Button dense variant="ghost" onClick={ctrl.cancel} data-testid="concierge-cancel">Cancel</Button>
            <Button dense variant="primary" disabled={!ctrl.canApply || ctrl.applying} onClick={ctrl.apply} loading={ctrl.applying} data-testid="concierge-apply">Use these</Button>
          </>
        }
      />

      {ctrl.error ? <div className="concierge-error" role="alert">{ctrl.error}</div> : null}
    </div>
  );
}
