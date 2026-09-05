// HS-169-02 — The streamlined Door: one screen to create a project.
// Composed from the surface library. Every verb is the library Button.

import { useContext, useEffect } from "react";
import {
  SurfaceLedgerRow,
  SurfaceFooter,
  StateChip,
  EgressChip,
  CheckGadget,
  StringGadget,
  MicButton,
} from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import { TitleSlotContext } from "../../../desk/surface/title";
import type { CoreProps } from "../../../pages/cores/core-types";
import {
  useDoorController,
  type DoorController,
  type SourceRow,
  type WatchDefault,
} from "./useDoorController";
import "./door.css";

/* ── Default watch definitions (display only) ── */

const GITHUB_WATCH_DEFS: WatchDefault[] = [
  { key: "open_prs", label: "OPEN PRS", templateId: "watch.github.review_queue", on: true },
  { key: "ci", label: "CI", templateId: "watch.github.branch_ci", on: true },
];

const JIRA_WATCH_DEFS: WatchDefault[] = [
  { key: "overdue", label: "OVERDUE", templateId: "watch.jira.due_risk", on: true },
  { key: "due_7_days", label: "DUE 7 DAYS", templateId: "watch.jira.delivery_flow", on: true },
  { key: "blocked", label: "BLOCKED", templateId: "watch.jira.blockers", on: false },
];

function watchDefs(provider: string): WatchDefault[] {
  return provider === "github" ? GITHUB_WATCH_DEFS : JIRA_WATCH_DEFS;
}

/* ── Not-connected row ── */

function NotConnectedRow({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  const emblem = row.provider === "github" ? "GH" : "J";
  const name = row.provider === "github" ? "GitHub" : "Jira";
  const chipState = row.connectionState === "owner_action_required" ? "warning" : "idle";
  const chipLabel =
    row.connectionState === "owner_action_required"
      ? "SIGN IN"
      : "NOT SET UP";

  return (
    <SurfaceLedgerRow
      lead={<span className="door-lead">{emblem}</span>}
      primary={<span className="door-provider-name">{name}</span>}
      cells={<StateChip state={chipState} label={chipLabel} />}
      trailing={
        <Button
          dense
          variant="primary"
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            ctrl.connect(row.provider);
          }}
          data-testid={`door-connect-${row.provider}`}
        >
          Connect
        </Button>
      }
      expands={false}
      data-testid={`door-row-${row.provider}`}
    />
  );
}

/* ── Connected row ── */

function ConnectedRow({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  const emblem = row.provider === "github" ? "GH" : "J";
  const defs = watchDefs(row.provider);
  const placeholder =
    row.provider === "github" ? "Choose a repository" : "Choose a project";

  const triggerText = row.scope ?? placeholder;

  return (
    <SurfaceLedgerRow
      lead={<span className="door-lead">{emblem}</span>}
      primary={
        <Button
          dense
          variant="ghost"
          className="door-scope-trigger"
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            if (row.pickerOpen) {
              ctrl.closePicker(row.provider);
            } else {
              ctrl.openPicker(row.provider);
            }
          }}
          data-testid={`door-trigger-${row.provider}`}
        >
          {triggerText}
          <svg className="door-chevron" viewBox="0 0 12 12" aria-hidden="true">
            <path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
          </svg>
        </Button>
      }
      cells={
        <span className="door-row-cells">
          {defs.map((d) => (
            <CheckGadget
              key={d.key}
              label={d.label}
              checked={row.toggles[d.key] ?? d.on}
              onChange={() => ctrl.toggleWatch(row.provider, d.key)}
              variant="token"
            />
          ))}

          {row.state === "checking" ? (
            <StateChip state="working" label="CHECKING" icon="○" />
          ) : row.state === "cant_check" ? (
            <>
              <StateChip state="warning" label="CAN'T CHECK" />
              {row.reason ? (
                <span className="door-count-line door-count-reason">
                  {row.reason}
                </span>
              ) : null}
            </>
          ) : row.state === "live" && row.plain ? (
            <span className="door-count-line" data-testid={`door-counts-${row.provider}`}>
              {row.plain}
            </span>
          ) : null}
        </span>
      }
      trailing={
        <span className="door-row-trailing">
          <EgressChip label={row.host.toUpperCase() || "—"} scope="cloud" />
          <Button
            dense
            variant="ghost"
            className="door-adjust-btn"
            onClick={(e: React.MouseEvent) => {
              e.stopPropagation();
              if (row.adjustOpen) ctrl.closeAdjust(row.provider);
              else ctrl.openAdjust(row.provider);
            }}
            data-testid={`door-adjust-${row.provider}`}
          >
            Adjust
          </Button>
        </span>
      }
      open={row.pickerOpen || row.adjustOpen}
      onToggle={() => {
        if (row.pickerOpen) ctrl.closePicker(row.provider);
        else if (row.adjustOpen) ctrl.closeAdjust(row.provider);
        else ctrl.openPicker(row.provider);
      }}
      wrap
      data-testid={`door-row-${row.provider}`}
    >
      {row.pickerOpen ? (
        <PickerWell row={row} ctrl={ctrl} />
      ) : row.adjustOpen ? (
        <AdjustWell row={row} ctrl={ctrl} />
      ) : null}
    </SurfaceLedgerRow>
  );
}

/* ── Picker well ── */

function PickerWell({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  const placeholder =
    row.provider === "github" ? "Search repositories" : "Search projects";

  return (
    <div className="door-picker-well" data-testid={`door-picker-${row.provider}`}>
      <StringGadget
        label={placeholder}
        value={row.pickerQuery}
        onChange={(q) => ctrl.searchPicker(row.provider, q)}
        placeholder={placeholder}
        autoFocus
      />

      <div className="door-picker-items">
        {row.pickerItems.map((item) => (
          <Button
            key={item.value}
            dense
            variant="ghost"
            className="door-picker-card"
            onClick={() => {
              ctrl.pickScope(row.provider, item.value, item.label, item.value);
            }}
            data-testid={`door-pick-${item.value}`}
          >
            <span className="door-picker-card-emblem">
              {item.label.charAt(0).toUpperCase()}
            </span>
            <span className="door-picker-card-label">{item.label}</span>
            <span className="door-picker-card-detail">{item.detail}</span>
            {item.knownBy ? (
              <span className="door-picker-card-known">
                ALSO WATCHED BY {item.knownBy}
              </span>
            ) : null}
          </Button>
        ))}
      </div>

      {row.pickerCursor ? (
        <Button
          dense
          variant="ghost"
          className="door-picker-more"
          onClick={() => ctrl.loadMorePicker(row.provider)}
          disabled={row.pickerLoading}
        >
          Show more
        </Button>
      ) : null}
    </div>
  );
}

/* ── Adjust well ── */

function AdjustWell({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  if (row.provider === "github") {
    return (
      <div className="door-adjust-well" data-testid={`door-adjust-well-${row.provider}`}>
        <div className="door-adjust-field">
          <span className="door-adjust-label">BASE BRANCH</span>
          <StringGadget
            label="Base branch"
            value={row.adjust.base ?? "main"}
            onChange={(v) => ctrl.updateAdjust(row.provider, { base: v })}
            placeholder="main"
          />
        </div>
        <div className="door-adjust-field">
          <span className="door-adjust-label">LABELS</span>
          <StringGadget
            label="Labels"
            value={row.adjust.labels ?? ""}
            onChange={(v) => ctrl.updateAdjust(row.provider, { labels: v })}
            placeholder="any"
          />
        </div>
        <div className="door-adjust-field">
          <span className="door-adjust-label">INCLUDE</span>
          <span className="door-adjust-check-row">
            <CheckGadget
              label="Drafts"
              checked={row.adjust.drafts ?? false}
              onChange={(v) => ctrl.updateAdjust(row.provider, { drafts: v })}
            />
            <span className="door-adjust-check-label">DRAFTS</span>
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="door-adjust-well" data-testid={`door-adjust-well-${row.provider}`}>
      <div className="door-adjust-field">
        <span className="door-adjust-label">ISSUE TYPES</span>
        <StringGadget
          label="Issue types"
          value={(row.adjust.issueTypes ?? []).join(", ")}
          onChange={(v) =>
            ctrl.updateAdjust(row.provider, {
              issueTypes: v
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
            })
          }
          placeholder="all"
        />
      </div>
      <div className="door-adjust-field">
        <span className="door-adjust-label">JQL</span>
        <StringGadget
          label="JQL filter"
          value={row.adjust.jql ?? ""}
          onChange={(v) => ctrl.updateAdjust(row.provider, { jql: v })}
          placeholder="optional"
        />
      </div>
    </div>
  );
}

/* ── Source row dispatcher ── */

function SourceRowComponent({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  if (!row.connected) {
    return <NotConnectedRow row={row} ctrl={ctrl} />;
  }
  return <ConnectedRow row={row} ctrl={ctrl} />;
}

/* ── DoorCore ── */

export function DoorCore({ scope }: CoreProps) {
  const ctrl = useDoorController();
  const setTitle = useContext(TitleSlotContext);

  useEffect(() => {
    setTitle?.("New Project");
  }, [setTitle]);

  const scopedCount = ctrl.sources.filter(
    (s) => s.connected && s.scope != null,
  ).length;
  const watchCount = ctrl.sources.reduce(
    (n, s) =>
      n +
      (s.connected && s.scope
        ? Object.values(s.toggles).filter(Boolean).length
        : 0),
    0,
  );

  const receiptText =
    scopedCount > 0
      ? `${scopedCount} SOURCE${scopedCount > 1 ? "S" : ""} · ${watchCount} WATCH${watchCount !== 1 ? "ES" : ""}`
      : "NO SOURCES · BLANK PROJECT";

  return (
    <div className="door-root" data-testid="door-root">
      {/* 1. The outcome well */}
      <div className="door-outcome-well" data-testid="door-outcome">
        <div className="door-outcome-input-wrap">
          <input
            type="text"
            className="door-outcome-input"
            placeholder="What are you delivering?"
            value={ctrl.outcome}
            onChange={(e) => ctrl.setOutcome(e.target.value)}
            maxLength={600}
            data-testid="door-outcome-input"
          />
          <MicButton
            label="Speak outcome"
            onText={(text) => ctrl.setOutcome(text)}
          />
        </div>
        <span className="door-outcome-caption">
          THIS BECOMES THE PROJECT&apos;S NAME
        </span>
      </div>

      {/* 2. SOURCES section */}
      <div className="door-sources-section">
        <span className="door-section-label" data-testid="door-sources-label">
          SOURCES{scopedCount > 0 ? ` ${scopedCount}` : ""}
        </span>
        <ul className="door-sources-list">
          {ctrl.sources.map((row) => (
            <SourceRowComponent key={row.provider} row={row} ctrl={ctrl} />
          ))}
        </ul>
      </div>

      {/* 3. Footer */}
      <SurfaceFooter
        className="door-footer"
        receipt={
          <span className="door-receipt" data-testid="door-receipt">
            {receiptText}
          </span>
        }
        verbs={
          <>
            <Button
              dense
              variant="ghost"
              onClick={ctrl.cancel}
              data-testid="door-cancel"
            >
              Cancel
            </Button>
            <Button
              dense
              variant="primary"
              disabled={!ctrl.outcome.trim() || ctrl.creating}
              onClick={ctrl.create}
              loading={ctrl.creating}
              data-testid="door-create"
            >
              Create Project
            </Button>
          </>
        }
      />

      {ctrl.error ? (
        <div className="door-error" role="alert">
          {ctrl.error}
        </div>
      ) : null}
    </div>
  );
}
