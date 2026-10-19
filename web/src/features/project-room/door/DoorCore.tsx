// HS-169-02 — The streamlined Door: one screen to create a project.
// Composed from the surface library. Every verb is the library Button.

import { useRoomRead } from "../roomReads";
import { useContext, useEffect, type ComponentPropsWithoutRef } from "react";
import {
  SurfaceLedgerRow,
  SurfaceFooter,
  StateChip,
  EgressChip,
  CheckGadget,
  StringGadget,
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
import { SignInWell, notSignedIn } from "../../../pages/cores/connections/ConnectionsPane";
import type { ConnectionState } from "../../../pages/cores/connections/api";
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

/* HS-174-07: Confluence defaults -- RECENT BLOGS (on) + PAGES BY ID (off).
   The CLI cannot list pages; honest and limited. */
const CONFLUENCE_WATCH_DEFS: WatchDefault[] = [
  { key: "recent_blogs", label: "RECENT BLOGS", templateId: "watch.confluence.recent_blogs", on: true },
  { key: "pages_by_id", label: "PAGES BY ID", templateId: "watch.confluence.pages_by_id", on: false },
];

function watchDefs(provider: string): WatchDefault[] {
  if (provider === "github") return GITHUB_WATCH_DEFS;
  if (provider === "confluence") return CONFLUENCE_WATCH_DEFS;
  return JIRA_WATCH_DEFS;
}

/* ── Provider display helpers ── */

const PROVIDER_EMBLEM: Record<string, string> = {
  github: "GH",
  jira: "J",
  confluence: "C",
};

const PROVIDER_NAME: Record<string, string> = {
  github: "GitHub",
  jira: "Jira",
  confluence: "Confluence",
};

function providerEmblem(provider: string): string {
  return PROVIDER_EMBLEM[provider] ?? provider.slice(0, 2).toUpperCase();
}

function providerName(provider: string): string {
  return PROVIDER_NAME[provider] ?? provider;
}

function providerPlaceholder(provider: string): string {
  if (provider === "github") return "Choose a repository";
  if (provider === "confluence") return "Choose a space";
  return "Choose a project";
}

function providerSearchPlaceholder(provider: string): string {
  if (provider === "github") return "Search repositories";
  if (provider === "confluence") return "Search spaces";
  return "Search projects";
}

/* ── Not-connected row ── */

function NotConnectedRow({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  const emblem = providerEmblem(row.provider);
  const name = providerName(row.provider);
  const tool = ctrl.tools.find((t) => t.provider_id === row.provider);
  // PHILO-17 U29: the cause in plain words, from the producer's state.
  const signIn = notSignedIn(row.connectionState as ConnectionState);
  const chipState = signIn ? "warning" : "idle";
  const chipLabel = signIn ? "NOT SIGNED IN" : "NOT SET UP";

  return (
    <SurfaceLedgerRow
      lead={<span className="door-lead">{emblem}</span>}
      primary={<span className="door-provider-name">{name}</span>}
      cells={<StateChip state={chipState} label={chipLabel} />}
      trailing={
        <Button
          dense
          variant="secondary"
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            ctrl.connect(row.provider);
          }}
          data-testid={`door-connect-${row.provider}`}
        >
          Connect
        </Button>
      }
      open={row.connectOpen}
      onToggle={() => ctrl.connect(row.provider)}
      wrap
      data-testid={`door-row-${row.provider}`}
    >
      {row.connectOpen && tool ? (
        <SignInWell
          tool={tool}
          busy={ctrl.busy === row.provider}
          onRecheck={() => ctrl.recheck(row.provider)}
          onAddAccount={(site, email) => ctrl.addAccount(row.provider, site, email)}
        />
      ) : null}
    </SurfaceLedgerRow>
  );
}

/* ── Connected row ── */

function ConnectedRow({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  const emblem = providerEmblem(row.provider);
  const defs = watchDefs(row.provider);
  const placeholder = providerPlaceholder(row.provider);

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
            <StateChip className="door-row-status" state="working" label="CHECKING" icon="○" />
          ) : row.state === "cant_check" ? (
            <>
              <StateChip className="door-row-status" state="warning" label="CAN'T CHECK" />
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

          {/* HS-174-07: Confluence shows SIGNED IN AS <email> */}
          {row.provider === "confluence" && row.connectionEmail ? (
            <StateChip className="door-row-status" state="success" label={`SIGNED IN AS ${row.connectionEmail.toUpperCase()}`} />
          ) : null}
        </span>
      }
      trailing={
        <span className="door-row-trailing">
          {row.host ? <EgressChip label={row.host.toUpperCase()} scope="cloud" /> : null}
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
  const placeholder = providerSearchPlaceholder(row.provider);

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
  /* HS-174-07: Confluence adjust -- space key only (no page list). */
  if (row.provider === "confluence") {
    return (
      <div className="door-adjust-well" data-testid={`door-adjust-well-${row.provider}`}>
        <div className="door-adjust-field">
          <span className="door-adjust-label">SPACE KEY</span>
          <StringGadget
            label="Space key"
            value={row.adjust.spaceKey ?? ""}
            onChange={(v) => ctrl.updateAdjust(row.provider, { spaceKey: v })}
            placeholder="GOV"
          />
        </div>
      </div>
    );
  }

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

/** PHILO-17 U10: the Door's source rows, for the Room's Add source. */
export function DoorSourceRows({ ctrl }: { ctrl: DoorController }) {
  return (
    <ul className="door-sources-list">
      {ctrl.sources.map((row) => (
        <SourceRowComponent key={row.provider} row={row} ctrl={ctrl} />
      ))}
    </ul>
  );
}

function DoorPreview({ ctrl }: { ctrl: DoorController }) {
  const preview = ctrl.preview;
  if (!preview) return null;
  return (
    <div className="door-preview" data-testid="door-preview">
      <span className="door-section-label">FOUND</span>
      {preview.sources.length ? (
        <ul className="door-preview-sources" data-testid="door-preview-sources">
          {preview.sources.map((source) => (
            <li key={`${source.provider}:${source.site ?? ""}:${source.scope}`} className="door-preview-source">
              <span>{source.label}</span>
              <StateChip
                state={source.state === "checked" ? "success" : source.state === "cant_check" ? "warning" : "idle"}
                label={source.state === "checked" ? "CHECKED" : source.state === "cant_check" ? "CAN'T CHECK" : "NOT CHECKED"}
              />
              {source.reason ? <span className="door-preview-reason">{source.reason}</span> : null}
            </li>
          ))}
        </ul>
      ) : (
        <span className="door-preview-empty">No source links found</span>
      )}

      {preview.found.length ? (
        <>
          <div className="door-preview-heading">
            <span className="door-section-label">MEETINGS AND NOTES</span>
            <Button dense variant="ghost" onClick={ctrl.selectAllFound} data-testid="door-found-add-all">
              Add all
            </Button>
          </div>
          <ul className="door-preview-found" data-testid="door-found">
            {preview.found.map((item) => (
              <li key={`${item.kind}:${item.id}`} className={item.selected ? "door-found-row" : "door-found-row door-found-removed"}>
                <span>
                  <strong>{item.title}</strong>
                  {item.detail ? <small>{item.detail}</small> : null}
                </span>
                {item.selected ? (
                  <Button dense variant="ghost" onClick={() => ctrl.removeFound(item.id)} data-testid={`door-found-remove-${item.id}`}>
                    Remove
                  </Button>
                ) : <span>Removed</span>}
              </li>
            ))}
          </ul>
          {preview.people.length ? (
            <span className="door-preview-people" data-testid="door-people">
              PEOPLE · {preview.people.join(" · ")}
            </span>
          ) : null}
        </>
      ) : null}
    </div>
  );
}

/** PHILO-17 U10: Add source in the Room: the same rows as New Project,
 *  added to this project. */
export function AddSourcesWell({
  projectId,
  onAdded,
  onCancel,
}: {
  projectId: string;
  onAdded: () => void;
  onCancel: () => void;
}) {
  const ctrl = useDoorController({ projectId, onAdded, onCancel });
  useRoomRead("door", ctrl.loaded);
  const picked = ctrl.sources.filter((s) => s.connected && s.scope != null).length;
  return (
    <div className="door-add-well" data-testid="room-add-sources">
      <DoorSourceRows ctrl={ctrl} />
      {ctrl.error ? (
        <div className="door-error" role="alert">
          {ctrl.error}
        </div>
      ) : null}
      <div className="door-add-verbs">
        <Button dense variant="ghost" onClick={ctrl.cancel} data-testid="room-add-sources-cancel">
          Cancel
        </Button>
        <Button
          dense
          variant="primary"
          disabled={!picked || ctrl.creating}
          loading={ctrl.creating}
          onClick={ctrl.create}
          data-testid="room-add-sources-add"
        >
          Add
        </Button>
      </div>
    </div>
  );
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
          <StringGadget
            label="Project name"
            caption
            placeholder="What are you delivering?"
            value={ctrl.outcome}
            onChange={ctrl.setOutcome}
            micLabel="Speak outcome"
            inputProps={{ maxLength: 600, "data-testid": "door-outcome-input" } as ComponentPropsWithoutRef<"input">}
          />
        <span className="door-outcome-caption">
          THIS BECOMES THE PROJECT&apos;S NAME
        </span>
      </div>

      {/* 2. SOURCES section */}
      <div className="door-sources-section">
        <span className="door-section-label" data-testid="door-sources-label">
          SOURCES{scopedCount > 0 ? ` ${scopedCount}` : ""}
        </span>
        <DoorSourceRows ctrl={ctrl} />
        <div className="door-source-paste" data-testid="door-source-paste">
          <StringGadget
            label="Paste source links"
            placeholder="GitHub repository, Jira project or Confluence space"
            value={ctrl.sourcePaste}
            onChange={ctrl.setSourcePaste}
            micLabel="Speak source links"
            inputProps={{ "data-testid": "door-source-paste-input" } as ComponentPropsWithoutRef<"input">}
          />
          <Button
            dense
            variant="secondary"
            disabled={!ctrl.sourcePaste.trim() || ctrl.previewing}
            loading={ctrl.previewing}
            onClick={ctrl.previewSources}
            data-testid="door-source-check"
          >
            Check sources
          </Button>
        </div>
        <DoorPreview ctrl={ctrl} />
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
