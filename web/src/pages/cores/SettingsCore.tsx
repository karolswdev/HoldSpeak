// HS-95-07 / HS-111-01 — the Settings core, rethought as the OS's own
// Prefs program (the verified audit at .tmp/hs-111-01-audit.md §3):
// a drawer face of authored pref modules; a module swaps the WHOLE
// window body; the footer status bar carries the receipt and the
// refusals; every control is a gadget from the surface kit. The pane
// roster is a code constant — the wire never mints a pane again.
//
// This file is the composition: the window frame, the section list and the
// shared store wiring. Each section lives in `./settings/<Section>.tsx`; the
// one settings writer lives in `./settings/writer.ts`.
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import type { CoreProps, SettingsResponse, AuthorityPolicyResponse } from "./core-types";
import { Button } from "../../components/signal/Signal";
import { useResource } from "../pageSupport";
import { SurfaceState } from "../../desk/surface/Surface";
import { SurfaceWell } from "../../desk/surface";
import { openSurfaceOr } from "../../desk/shell";
import { OwnerNameGroup, ownerSaveState, useOwnerPreferences } from "./settingsPeople";
import { PrefSection, PrefWindow, clockWord } from "./settingsWindow";
import type { ConnectionsFoot } from "./connections";
import { CallsSettingsPane } from "../../desk/calls/CallsSettings";
import "./settingsSurfaceRepair.css";
import {
  SETTINGS_SECTIONS,
  type SettingsSectionId,
  PrefStatusBar,
  SettingsRailGlyph,
  type SettingsHubWire,
} from "./settingsPrefs";
import { SECTION_ALIASES, SETTINGS_FOCUS_PATHS, settingsPageScope } from "./settings/navigation";
import { useSettingsWriter, type SettingsChanges } from "./settings/writer";
import { settingsBindings } from "./settings/bindings";
import { GrantFootReceipt, type GrantAct } from "./settings/grants";
import { useCalendarSources } from "./settings/Calendar";
import { SpeakSection, useSpokenSymbolsDraft } from "./settings/Speak";
import { MeetingsSection } from "./settings/Meetings";
import { ReachSection } from "./settings/Reach";
import { AccountsSection, useSecretChanges } from "./settings/Accounts";
import { AgentsSection, useControlMode } from "./settings/Agents";
import { DeskSection } from "./settings/Desk";
import { ThisMacSection } from "./settings/ThisMac";

// Every name other modules and tests import from SettingsCore stays here.
export {
  mergeSettingsChanges,
  installSettingsChanges,
  projectPendingSettingsChanges,
} from "./settings/writer";
export {
  formatLocalClock,
  calendarSourceIdentity,
  snapshotEgressChip,
  calendarSourceEgressChips,
} from "./settings/Calendar";
export { settingsScope } from "./settings/navigation";
export {
  GRANT_WORDS,
  PROJECT_GRANT_WORDS,
  PROJECT_GRANT_PALETTES,
  DESK_GRANT_PALETTES,
  GRANT_REFUSAL_TOKEN,
  GrantReceiptWell,
  GrantFootReceipt,
  type GrantAct,
} from "./settings/grants";
export { RuntimeIdentityModule, hubPlaceWord, type RuntimeIdentityWire } from "./settings/ThisMac";
export { RemoteAccessModule } from "./settings/RemoteAccess";

export function SettingsCore(props: CoreProps) {
  return <SettingsFace {...props} />;
}

function SettingsFace({ hero, scope }: CoreProps) {
  // A scope is a new entry intent. The page stays mounted and the scope only
  // chooses its section and row anchor.
  const [navigation, setNavigation] = useState(() => settingsPageScope(scope));
  // Window grammar: at a narrow content width the rail is the first view.
  // An entry with a scope (a palette row, a deep link) opens its pane.
  const [paneOpen, setPaneOpen] = useState(() => Boolean(settingsPageScope(scope).module));
  // The window's Back returns to where the owner came from. A pane opened by
  // a scope (a receipt, the palette, a deep link) lets the frame's Back close
  // the window; only a pane the owner opened from the rail returns to it.
  const [cameFromRail, setCameFromRail] = useState(false);
  useEffect(() => {
    setCameFromRail(false);
    const next = settingsPageScope(scope);
    if (next.module === "setup") {
      openSurfaceOr("configure-setup", "/");
      setNavigation({ module: null });
    } else {
      setNavigation(next);
      setHighlight(next.focus ?? "");
      if (next.module) setPaneOpen(true);
    }
  }, [scope]);
  // The You writer lives with the window: its state is the status bar's.
  const ownerPrefs = useOwnerPreferences();
  // Settings opens on the owner's identity category. A legacy "settings"
  // scope still lands on the same face; it never restores the old all-page
  // document.
  const moduleId = navigation.module === "settings" || !navigation.module ? "you" : navigation.module;
  const contentRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const body = contentRef.current?.closest<HTMLElement>(".desk-surface-body");
    if (!body) return;
    body.scrollTop = 0;
  }, [moduleId]);
  const integrationSubject =
    moduleId === "accounts"
      ? navigation.focus
      : null;
  const resource = useResource<SettingsResponse>("/api/settings", {});
  const authority = useResource<AuthorityPolicyResponse>(
    "/api/authority/policy",
    {},
  );
  // HS-170-04: the hub wire — one read for all seven module rows' state tokens.
  const hub = useResource<SettingsHubWire>("/api/settings/hub", {
    models: { engines: 0, groupsSet: 0, defaultSet: false },
    connections: { connected: 0 },
    voice: { live: false, target: "" },
    meetings: { intelligence: false, auto: "off", host: "" },
    rhythm: { loops: 0 },
    sounds: { on: false },
    system: { host: "THIS DEVICE", mesh: false, remote: false },
    posture: "neutral",
    writtenAt: null,
  });
  // null = the drawer face; a module id = that module owns the body.
  // PHILO-7-02: the last grant act's receipt (the footer's centre Button)
  // and whether its RECEIPT well is open under Remote access.
  const [grantAct, setGrantAct] = useState<GrantAct | null>(null);
  const [grantReceiptOpen, setGrantReceiptOpen] = useState(false);
  const [highlight, setHighlight] = useState("");
  const [writtenAt, setWrittenAt] = useState("");
  const stamp = () => setWrittenAt(new Date().toTimeString().slice(0, 8));
  // W6 (owner decision 2026-10-28): Saved counts per window. A You write is
  // a write made in this window, so every pane's bar says Saved after it.
  useEffect(() => {
    if (ownerPrefs.savedAt) setWrittenAt(ownerPrefs.savedAt.toTimeString().slice(0, 8));
  }, [ownerPrefs.savedAt]);
  /** Betterment setup ST1: a Notify or quiet-hours write draws the
   *  embedded sweep again (it reads the same heartbeat). */
  const [heartbeatRevision, setHeartbeatRevision] = useState(0);
  // HS-168-03: connections receipt for the integrations module footer.
  const [connectionsFoot, setConnectionsFoot] = useState<ConnectionsFoot | null>(null);
  const handleConnectionsFooter = useCallback((foot: ConnectionsFoot) => {
    setConnectionsFoot(foot);
  }, []);

  // HS-175-03: calendar sources facts for the CALENDAR section, and its well.
  const cal = useCalendarSources();
  // HS-130-07: Settings is the canonical full-document writer (writer.ts).
  const writer = useSettingsWriter(resource, (changes: SettingsChanges) => {
    stamp();
    void hub.reload();
    if (changes.some(([path]) => path[0] === "calendar" || path[0] === "meeting")) void cal.loadCalSources();
  });
  const { saving, refusal, failedChangesRef, retryFailedChanges } = writer;
  const symbolsDraft = useSpokenSymbolsDraft(resource.data, writer);
  const secretChanges = useSecretChanges(writer, () => {
    void hub.reload();
    stamp();
  });
  const control = useControlMode(authority, writer, stamp);
  const calendarChanged = async () => {
    await writer.reconcileSettings();
    void hub.reload();
    await cal.loadCalSources();
  };

  // The section words are the page index.  They scroll the existing face;
  // they never create a wing or replace the page body.
  const openSection = (id: string, focus = "") => {
    setNavigation({ module: id, focus });
    setHighlight(focus);
    setPaneOpen(true);
  };
  const openModule = (id: string) => {
    const section = SECTION_ALIASES[id] ?? id;
    openSection(section);
  };

  /* ── gadget bindings (plain function helpers — never components
        defined in render, which would remount and drop focus) ── */
  const b = settingsBindings(resource.data, writer.update, highlight);

  // You has its own owner writer and field receipts: while a You field is
  // Edited, Saving or Not saved, the bar says that word (ownerSaveState), and
  // a success of the general writer cannot acknowledge it. With no You state
  // to say, the bar says the window's last write (Saved counts per window).
  const receipt = { saving: saving || Boolean(secretChanges.secretBusy), writtenAt, refusal };
  const ownerSave = moduleId === "you" ? ownerSaveState(ownerPrefs) : undefined;
  const focusHighlight = SETTINGS_FOCUS_PATHS[navigation.focus ?? ""] ?? navigation.focus ?? "";
  const pageSection = (id: SettingsSectionId, label: string, children: ReactNode) => (
    <PrefSection id={id} label={label} hidden={moduleId !== id} quiet={id === "you" || id === "agents"}>{children}</PrefSection>
  );
  const railItems = SETTINGS_SECTIONS.map((section) => ({
    id: section.id,
    label: section.label,
    glyph: <SettingsRailGlyph section={section} />,
  }));
  const settingsPage = (
    <PrefWindow items={railItems} selected={moduleId} onSelect={(id) => { setCameFromRail(true); openSection(id); }} paneOpen={paneOpen} onBack={() => { setCameFromRail(false); setPaneOpen(false); }} frameBack holdFrameBack={cameFromRail} testId="settings-page">
        {refusal && moduleId !== "you" ? <div className="pref-pane-alert"><SurfaceWell><div className="prefs-read-failure" role="alert" data-testid="settings-save-failure"><span>{refusal}</span>{failedChangesRef.current.length ? <Button dense variant="ghost" disabled={saving} onClick={() => void retryFailedChanges()}>Retry</Button> : null}</div></SurfaceWell></div> : null}
        {pageSection("you", "You", <OwnerNameGroup prefs={ownerPrefs} highlight={focusHighlight} />)}
        {pageSection("speak", "Speak", <SpeakSection b={b} symbolsDraft={symbolsDraft} onRefuse={writer.setRefusal} />)}
        {pageSection("meetings", "Meetings", <MeetingsSection b={b} hub={hub} focusHighlight={focusHighlight} />)}
        {pageSection("notices", "Reach", <ReachSection b={b} focusHighlight={focusHighlight} onSaved={stamp} heartbeatRevision={heartbeatRevision} onHeartbeatWrite={() => setHeartbeatRevision((n) => n + 1)} />)}
        {pageSection("accounts", "Accounts", <AccountsSection
          b={b}
          secrets={secretChanges}
          cal={cal}
          writer={writer}
          connections={{
            onFooterUpdate: handleConnectionsFooter,
            onOpenModule: openModule,
            focusProvider: integrationSubject,
            onCalendarChanged: calendarChanged,
          }}
        />)}
        {pageSection("calls", "Calls", moduleId === "calls" ? <CallsSettingsPane highlight={focusHighlight} onSaved={stamp} /> : null)}
        {pageSection("agents", "Agents", <AgentsSection b={b} focusHighlight={focusHighlight} posture={hub.data.posture} authority={authority} control={control} />)}
        {pageSection("desk", "Desk", <DeskSection b={b} focusHighlight={focusHighlight} />)}
        {pageSection("this-mac", "This Mac", <ThisMacSection
          b={b}
          hubSystem={hub.data.system}
          grantAct={grantAct}
          receiptOpen={grantReceiptOpen}
          onGrantAct={(act) => { setGrantAct(act); setGrantReceiptOpen(false); }}
          focusHighlight={focusHighlight}
        />)}
    </PrefWindow>
  );
  return (
    <>
      {hero ? hero(null) : null}
      <div ref={contentRef} className="settings-content settings-page-content" data-settings-view={moduleId || "page"}>
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceState loading={hub.loading} error={hub.error} onRetry={() => void hub.reload()}>
          {settingsPage}
        </SurfaceState>
      </SurfaceState>
      </div>
      <PrefStatusBar
        receipt={receipt}
        save={ownerSave ?? undefined}
        failureTestId={moduleId === "you" ? undefined : null}
        onRetry={moduleId === "you"
          ? (ownerPrefs.state === "Not saved" ? () => void ownerPrefs.owner.flush() : undefined)
          : (failedChangesRef.current.length ? () => void retryFailedChanges() : undefined)}
        idleReceipt={moduleId === "accounts" && connectionsFoot?.checkedAt ? <span data-testid="settings-checked">Checked {clockWord(connectionsFoot.checkedAt)}</span> : undefined}
        grantReceipt={grantAct ? (
          <GrantFootReceipt
            act={grantAct}
            open={grantReceiptOpen}
            onToggle={() => setGrantReceiptOpen((open) => !open)}
          />
        ) : null}
        /* W6-A (atlas pass 3, defect 1): the bar says Saved only for a
           write made in this window. The settings file's own mtime
           (hub.writtenAt) is any writer's, so at open the bar was
           "Saved just now" for a save he never made. */
        hubWrittenAt={null}
      />
    </>
  );
}
