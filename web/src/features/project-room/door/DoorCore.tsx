// HS-169-02 — The streamlined Door: one screen to create a project.
// Composed from the surface library. Every verb is the library Button.

import { useRoomRead } from "../roomReads";
import { useContext, useEffect, type ComponentPropsWithoutRef } from "react";
import {
  EgressChip,
  CheckGadget,
  StringGadget,
} from "../../../desk/surface";
import { DotWord, StatusBar, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../../../desk/surface/kit";
import { useWindowInterior } from "../../../desk/surface/interior";
import { spriteUrl } from "../../../desk/sprites";
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
  { key: "open_prs", label: "Open PRs", templateId: "watch.github.review_queue", on: true },
  { key: "ci", label: "CI", templateId: "watch.github.branch_ci", on: true },
];

const JIRA_WATCH_DEFS: WatchDefault[] = [
  { key: "overdue", label: "Overdue", templateId: "watch.jira.due_risk", on: true },
  { key: "due_7_days", label: "Due in 7 days", templateId: "watch.jira.delivery_flow", on: true },
  { key: "blocked", label: "Blocked", templateId: "watch.jira.blockers", on: false },
];

/* HS-174-07: Confluence defaults -- Recent blogs (on) + Pages by ID (off).
   The CLI cannot list pages; honest and limited. */
const CONFLUENCE_WATCH_DEFS: WatchDefault[] = [
  { key: "recent_blogs", label: "Recent blogs", templateId: "watch.confluence.recent_blogs", on: true },
  { key: "pages_by_id", label: "Pages by ID", templateId: "watch.confluence.pages_by_id", on: false },
];

function watchDefs(provider: string): WatchDefault[] {
  if (provider === "github") return GITHUB_WATCH_DEFS;
  if (provider === "confluence") return CONFLUENCE_WATCH_DEFS;
  return JIRA_WATCH_DEFS;
}

/* ── Provider display helpers ── */

/* Window grammar (2026-10-24): each source row leads with its D glyph
   (Icons D, the 20 px world sprites): a repository, an issue, a page. */
const PROVIDER_SPRITE: Record<string, string> = {
  github: "repository",
  jira: "action",
  confluence: "artifact",
};

function ProviderGlyph({ provider }: { provider: string }) {
  return (
    <img
      className="door-row-glyph"
      src={spriteUrl(PROVIDER_SPRITE[provider] ?? "artifact", provider, "rest", null, 20)}
      alt=""
      width={20}
      height={20}
      draggable={false}
    />
  );
}

const PROVIDER_NAME: Record<string, string> = {
  github: "GitHub",
  jira: "Jira",
  confluence: "Confluence",
};

function providerName(provider: string): string {
  return PROVIDER_NAME[provider] ?? provider;
}

function providerPlaceholder(provider: string): string {
  if (provider === "github") return "Pick a repository";
  if (provider === "confluence") return "Pick a space";
  return "Pick a project";
}

function providerSearchPlaceholder(provider: string): string {
  if (provider === "github") return "Search repositories";
  if (provider === "confluence") return "Search spaces";
  return "Search projects";
}

/* ── Not-connected row ── */

/* Window grammar (2026-10-24): a source is one row of the form's
   label/control grid: the provider's glyph and name, then its control
   (the pick, the watches, the check state as a dot and a word, the
   counts as a quiet sans fact), then its one quiet verb at the right. The
   open well (the picker, Adjust, sign-in) spans the row under it. */
function NotConnectedRow({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  const name = providerName(row.provider);
  const tool = ctrl.tools.find((t) => t.provider_id === row.provider);
  // PHILO-17 U29: the cause in plain words, from the producer's state.
  const signIn = notSignedIn(row.connectionState as ConnectionState);

  return (
    <li className="door-row" data-testid={`door-row-${row.provider}`} data-open={row.connectOpen ? "true" : undefined}>
      <span className="door-row-label">
        <ProviderGlyph provider={row.provider} />
        <span className="door-provider-name">{name}</span>
      </span>
      <span className="door-row-control">
        <DotWord tone={signIn ? "warn" : "idle"}>{signIn ? "Not signed in" : "Not set up"}</DotWord>
      </span>
      <span className="door-row-trailing">
        <Button
          dense
          variant="secondary"
          aria-expanded={row.connectOpen}
          onClick={() => ctrl.connect(row.provider)}
          data-testid={`door-connect-${row.provider}`}
        >
          Connect
        </Button>
      </span>
      {row.connectOpen && tool ? (
        <div className="door-row-well">
          <SignInWell
            tool={tool}
            busy={ctrl.busy === row.provider}
            onRecheck={() => ctrl.recheck(row.provider)}
            onAddAccount={(site, email) => ctrl.addAccount(row.provider, site, email)}
          />
        </div>
      ) : null}
    </li>
  );
}

/* ── Connected row ── */

function ConnectedRow({ row, ctrl }: { row: SourceRow; ctrl: DoorController }) {
  const defs = watchDefs(row.provider);
  const placeholder = providerPlaceholder(row.provider);

  const triggerText = row.scope ?? placeholder;
  const open = row.pickerOpen || row.adjustOpen;

  return (
    <li className="door-row" data-testid={`door-row-${row.provider}`} data-open={open ? "true" : undefined}
      data-picked={row.scope ? "true" : undefined}>
      <span className="door-row-label">
        <ProviderGlyph provider={row.provider} />
        <span className="door-provider-name">{providerName(row.provider)}</span>
      </span>
      <span className="door-row-control">
        <span className="door-row-line">
          <Button
            dense
            variant="ghost"
            className="door-scope-trigger"
            aria-expanded={row.pickerOpen}
            onClick={() => {
              if (row.pickerOpen) {
                ctrl.closePicker(row.provider);
              } else {
                ctrl.openPicker(row.provider);
              }
            }}
            data-testid={`door-trigger-${row.provider}`}
          >
            <span className="door-scope-text">{triggerText}</span>
            <svg className="door-chevron" viewBox="0 0 12 12" aria-hidden="true">
              <path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            </svg>
          </Button>
          {defs.map((d) => (
            <CheckGadget
              key={d.key}
              label={d.label}
              checked={row.toggles[d.key] ?? d.on}
              onChange={() => ctrl.toggleWatch(row.provider, d.key)}
              variant="token"
            />
          ))}
        </span>
        {row.state === "checking" || row.state === "cant_check" || (row.state === "live" && row.plain)
          || (row.provider === "confluence" && row.connectionEmail) ? (
          <span className="door-row-facts">
            {row.state === "checking" ? (
              <DotWord className="door-row-status" tone="info">Checking</DotWord>
            ) : row.state === "cant_check" ? (
              <>
                <DotWord className="door-row-status" tone="warn">Can&apos;t check</DotWord>
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
            {/* HS-174-07: Confluence says who it is signed in as. */}
            {row.provider === "confluence" && row.connectionEmail ? (
              <DotWord className="door-row-status" tone="ok">{`Signed in as ${row.connectionEmail}`}</DotWord>
            ) : null}
          </span>
        ) : null}
      </span>
      <span className="door-row-trailing">
        <Button
          dense
          variant="ghost"
          className="door-adjust-btn"
          aria-expanded={row.adjustOpen}
          onClick={() => {
            if (row.adjustOpen) ctrl.closeAdjust(row.provider);
            else ctrl.openAdjust(row.provider);
          }}
          data-testid={`door-adjust-${row.provider}`}
        >
          Adjust
        </Button>
      </span>
      {row.pickerOpen ? (
        <div className="door-row-well"><PickerWell row={row} ctrl={ctrl} /></div>
      ) : row.adjustOpen ? (
        <div className="door-row-well"><AdjustWell row={row} ctrl={ctrl} /></div>
      ) : null}
    </li>
  );
}

/** The egress of the picked sources: one chip per host that leaves the
 *  machine (A.9: egress where egress happens, at Create and Add). */
function SourceEgress({ ctrl }: { ctrl: DoorController }) {
  const hosts = [...new Set(ctrl.sources
    .filter((s) => s.connected && s.scope != null && s.host)
    .map((s) => String(s.host).toLowerCase()))];
  if (!hosts.length) return null;
  return (
    <span className="door-egress" data-testid="door-egress">
      {hosts.map((host) => <EgressChip key={host} label={host} scope="cloud" />)}
    </span>
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
            <ProviderGlyph provider={row.provider} />
            <span className="door-picker-card-label">{item.label}</span>
            <span className="door-picker-card-detail">{item.detail}</span>
            {item.knownBy ? (
              <span className="door-picker-card-known">
                Also watched by {item.knownBy}
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
          <span className="door-adjust-label">Space key</span>
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
          <span className="door-adjust-label">Base branch</span>
          <StringGadget
            label="Base branch"
            value={row.adjust.base ?? "main"}
            onChange={(v) => ctrl.updateAdjust(row.provider, { base: v })}
            placeholder="main"
          />
        </div>
        <div className="door-adjust-field">
          <span className="door-adjust-label">Labels</span>
          <StringGadget
            label="Labels"
            value={row.adjust.labels ?? ""}
            onChange={(v) => ctrl.updateAdjust(row.provider, { labels: v })}
            placeholder="any"
          />
        </div>
        <div className="door-adjust-field">
          <span className="door-adjust-label">Include</span>
          <span className="door-adjust-check-row">
            <CheckGadget
              label="Drafts"
              checked={row.adjust.drafts ?? false}
              onChange={(v) => ctrl.updateAdjust(row.provider, { drafts: v })}
            />
            <span className="door-adjust-check-label">Drafts</span>
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="door-adjust-well" data-testid={`door-adjust-well-${row.provider}`}>
      <div className="door-adjust-field">
        <span className="door-adjust-label">Issue types</span>
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
      <h3 className="door-section-label">Found</h3>
      {preview.sources.length ? (
        <ul className="door-preview-sources" data-testid="door-preview-sources">
          {preview.sources.map((source) => (
            <li key={`${source.provider}:${source.site ?? ""}:${source.scope}`} className="door-preview-source">
              <span>{source.label}</span>
              <DotWord tone={source.state === "checked" ? "ok" : source.state === "cant_check" ? "warn" : "idle"}>
                {source.state === "checked" ? "Checked" : source.state === "cant_check" ? "Can't check" : "Not checked"}
              </DotWord>
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
            <h3 className="door-section-label">Meetings and notes</h3>
            <Button dense variant="ghost" onClick={ctrl.selectAllFound} data-testid="door-found-add-all">
              Add all
            </Button>
          </div>
          <ul className="door-preview-found" data-testid="door-found">
            {preview.found.map((item) => (
              <li
                key={`${item.kind}:${item.id}`}
                className={item.linkState === "linked" || item.selected ? "door-found-row" : "door-found-row door-found-removed"}
              >
                <span>
                  <strong>{item.title}</strong>
                  {item.detail ? <small>{item.detail}</small> : null}
                </span>
                {item.linkState === "linked" ? (
                  <DotWord tone="ok">Added</DotWord>
                ) : item.linkState === "failed" ? (
                  <span className="door-found-failure">
                    <DotWord tone="fail">Can&apos;t add</DotWord>
                    {item.linkError ? <span data-testid={`door-found-error-${item.id}`}>{item.linkError}</span> : null}
                    <Button
                      dense
                      variant="ghost"
                      loading={ctrl.retryingFoundId === item.id}
                      disabled={ctrl.retryingFoundId !== null}
                      onClick={() => ctrl.retryFound(item.id)}
                      data-testid={`door-found-retry-${item.id}`}
                    >
                      Retry
                    </Button>
                  </span>
                ) : item.selected ? (
                  <Button dense variant="ghost" onClick={() => ctrl.removeFound(item.id)} data-testid={`door-found-remove-${item.id}`}>
                    Remove
                  </Button>
                ) : <span>Removed</span>}
              </li>
            ))}
          </ul>
          {preview.people.length ? (
            <span className="door-preview-people" data-testid="door-people">
              People · {preview.people.join(" · ")}
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
        <SourceEgress ctrl={ctrl} />
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

/* Window grammar (2026-10-24): New Project is a form window in the
   preference grammar. Title bar → Toolbar [Create project] [Cancel] → a
   label/control grid (Name; Links; one row per source with its glyph, its
   pick, its watches and its counts) → the links found → StatusBar
   (`2 sources · 4 watches`, the check state; the egress chip of each source
   that leaves the machine). The Door stays in its window (no modal). */
export function DoorCore({ scope }: CoreProps) {
  const ctrl = useDoorController();
  const setTitle = useContext(TitleSlotContext);
  useWindowInterior("editor");

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
  const checking = ctrl.sources.some((s) => s.connected && s.scope != null && s.state === "checking");
  const cantCheck = ctrl.sources.filter((s) => s.connected && s.scope != null && s.state === "cant_check").length;

  // Never a zero (A.8): no source is a blank project, said once.
  const receiptText = scopedCount > 0
    ? [countWords(scopedCount, "source"), countWords(watchCount, "watch", "watches")].filter(Boolean).join(" · ")
    : "Blank project";
  const items: Array<StatusBarItem | null> = [
    { key: "receipt", lamp: scopedCount ? "ok" : undefined, text: <span className="door-receipt" data-testid="door-receipt">{receiptText}</span> },
    checking ? { key: "checking", lamp: "info", text: "Checking" } : null,
    cantCheck ? { key: "cant", lamp: "warn", text: cantCheck === 1 ? "1 source can't be checked" : `${cantCheck} sources can't be checked` } : null,
  ];

  return (
    <div className="door-root" data-testid="door-root">
      <Toolbar label="New Project" data-testid="door-toolbar">
        <Button
          dense
          variant="primary"
          disabled={!ctrl.outcome.trim() || ctrl.creating}
          onClick={ctrl.create}
          loading={ctrl.creating}
          data-testid="door-create"
        >
          <ToolGlyph kind="project" />
          Create project
        </Button>
        <Button
          dense
          variant="ghost"
          onClick={ctrl.cancel}
          data-testid="door-cancel"
        >
          Cancel
        </Button>
      </Toolbar>

      <div className="door-form">
        <div className="door-grid">
          {/* Name */}
          <div className="door-field" data-testid="door-outcome">
            <span className="door-field-label" id="door-name-label">Name</span>
            <div className="door-field-control">
              <StringGadget
                label="Project name"
                placeholder="What are you delivering?"
                value={ctrl.outcome}
                onChange={ctrl.setOutcome}
                micLabel="Speak outcome"
                inputProps={{ maxLength: 600, "data-testid": "door-outcome-input" } as ComponentPropsWithoutRef<"input">}
              />
            </div>
          </div>

          {/* Links */}
          <div className="door-field door-source-paste" data-testid="door-source-paste">
            <span className="door-field-label">Links</span>
            <div className="door-field-control door-paste-control">
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
          </div>
        </div>

        {/* Sources */}
        <section className="door-sources-section" aria-labelledby="door-sources-label">
          <h3 className="door-section-label" id="door-sources-label" data-testid="door-sources-label">
            Sources{scopedCount > 0 ? <span className="door-section-count">{` ${scopedCount} picked`}</span> : null}
          </h3>
          <DoorSourceRows ctrl={ctrl} />
        </section>
        <DoorPreview ctrl={ctrl} />

        {ctrl.error ? (
          <div className="door-error" role="alert">
            {ctrl.error}
          </div>
        ) : null}
      </div>

      <StatusBar data-testid="door-status" items={items} egress={<SourceEgress ctrl={ctrl} />} />
    </div>
  );
}
