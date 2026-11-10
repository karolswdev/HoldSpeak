// Settings > Accounts: connections, calendar, destinations and credentials. Moved out of SettingsCore.tsx.
import { Button } from "../../../components/signal/Signal";
import { PreferencePane, ListPane, SegmentedTabs, PaneInspector, PaneActions, ListView, GadgetRow, StringGadget, ConfirmVerb } from "../../../desk/surface";
import { useEffect, useState } from "react";
import type { SecretState } from "../core-types";
import { apiFetch, readableError } from "../../../lib/api";
import { FoldGadget, GadgetGroup, SecretRow } from "../../../desk/surface/gadgets";
import { ConnectionsPane, type ConnectionsFoot } from "../connections";
import { Destinations } from "../connections/Destinations";
import { title, type SettingsBindings } from "./bindings";
import type { SettingsWriter } from "./writer";
import { CalendarSection, type CalendarSources } from "./Calendar";

const SECRET_LABELS: Record<string, string> = {
  web_token: "Web pairing token",
  device_psk: "Device audio key",
  telegram_bot_token: "Telegram bot token",
  telegram_pairing_code: "Telegram pairing code",
  failure_webhook_url: "Failure alert webhook",
  failure_webhook_credential: "Failure alert credential",
  companion_webhook_url: "Custom webhook",
};
const ROTATABLE_SECRETS = new Set(["web_token", "device_psk", "telegram_pairing_code"]);

/** A credential's Replace, Rotate and Delete. The face holds the busy id
 *  (the status bar says Saving while one is in flight). */
export function useSecretChanges(writer: SettingsWriter, onWritten: () => void) {
  const [secretBusy, setSecretBusy] = useState("");
  const changeSecret = async (secretId: string, action: "replace" | "rotate" | "delete", value?: string) => {
    setSecretBusy(secretId);
    writer.restoreRefusal();
    try {
      if (action === "replace") {
        await apiFetch(`/api/settings/secrets/${secretId}`, {
          method: "PUT",
          json: { value },
        });
      } else if (action === "rotate") {
        await apiFetch(`/api/settings/secrets/${secretId}/rotate`, {
          method: "POST",
        });
      } else {
        await apiFetch(`/api/settings/secrets/${secretId}`, {
          method: "DELETE",
        });
      }
      await writer.reconcileSettings();
      onWritten();
      return true;
    } catch (error) {
      writer.setRefusal(readableError(error));
      return false;
    } finally {
      setSecretBusy("");
    }
  };
  return { secretBusy, changeSecret };
}

export type SecretChanges = ReturnType<typeof useSecretChanges>;

/** Hub-wide keys belong to This Mac, separate from service accounts. */
export function CredentialsGroup({ b, secrets }: { b: SettingsBindings; secrets: SecretChanges }) {
  const rows = Object.entries((b.data._secrets ?? {}) as Record<string, SecretState>).filter(([id]) => !id.startsWith("telegram_"));
  const [picked, pick] = useState<string | null>(null);
  const [editing, edit] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const state = rows.find(([id]) => id === editing)?.[1];
  return <ListPane label="Credential inspector" list={(    <ListView
      label="Device credentials"
      rows={rows.map(([id, state]) => ({
        id,
        kind: "credential",
        name: SECRET_LABELS[id] ?? title(id),
        cells: { place: state.configured ? "Stored" : "Not set" },
      }))}
      columns={[
        { key: "name", word: "Credential", track: "minmax(0, 2fr)" },
        { key: "place", word: "State" },
      ]}
      selectedId={picked}
      onSelect={pick}
      verbs={[
        {
          id: "edit",
          label: "Edit…",
          key: "Enter",
          enabled: (row) => Boolean(row),
          run: (row) => { setDraft(""); edit(row!.id); },
        },
      ]}
      defaultVerb="edit"
    />)} >{state && editing ? (
    <PaneInspector label={SECRET_LABELS[editing] ?? title(editing)}>
      <GadgetGroup>
        <GadgetRow label="New value"><StringGadget label={`Replacement ${SECRET_LABELS[editing] ?? title(editing)}`} type="password" mic={false} value={draft} onChange={setDraft} inputProps={{autoComplete:"new-password"}} /></GadgetRow>
        {ROTATABLE_SECRETS.has(editing) || state.configured ? <GadgetRow label="Stored key"><PaneActions>
          {ROTATABLE_SECRETS.has(editing) ? <ConfirmVerb label="Rotate" confirmLabel="Rotate?" busy={secrets.secretBusy === editing} onConfirm={() => void secrets.changeSecret(editing, "rotate")} /> : null}
          {state.configured ? <ConfirmVerb label="Delete" confirmLabel="Delete?" busy={secrets.secretBusy === editing} onConfirm={() => void secrets.changeSecret(editing, "delete")} /> : null}
        </PaneActions></GadgetRow> : null}
      </GadgetGroup>
      <PaneActions><Button dense variant="ghost" disabled={Boolean(secrets.secretBusy)} onClick={() => {setDraft(""); edit(null);}}>Cancel</Button>
        <Button dense variant="primary" loading={secrets.secretBusy === editing} disabled={!draft.trim()} onClick={async () => {if (await secrets.changeSecret(editing, "replace", draft.trim())) {setDraft(""); edit(null);}}}>Save</Button></PaneActions>
    </PaneInspector>) : null}</ListPane>;
}

/** Accounts are three list panes; secrets keep their separate inspector. */
export function AccountsSection({
  b,
  secrets: secretChanges,
  cal,
  writer,
  connections,
  onStatus,
}: {
  onStatus?: (fact: string) => void;
  b: SettingsBindings;
  secrets: SecretChanges;
  cal: CalendarSources;
  writer: SettingsWriter;
  connections: {
    onFooterUpdate: (foot: ConnectionsFoot) => void;
    onOpenModule: (id: string) => void;
    focusProvider: string | null | undefined;
    onAttention?: (reason: string | null) => void;
    onCalendarChanged: () => Promise<void>;
  };
}) {
  const tabFor = (focus: string | null | undefined) => focus === "calendar" ? "calendars" : focus === "destinations" ? "destinations" : "services";
  const [tab, setTab] = useState(tabFor(connections.focusProvider));
  const [serviceFocus, focusService] = useState(connections.focusProvider);
  useEffect(() => {
    if (!connections.focusProvider) return;
    setTab(tabFor(connections.focusProvider));
    focusService(connections.focusProvider);
  }, [connections.focusProvider]);
  const [services, setServices] = useState(0);
  const [destinations, setDestinations] = useState(0);
  const calendars = ((b.data.calendar as { sources?: unknown[] })?.sources ?? []).length;
  const count = tab === "services" ? services : tab === "calendars" ? calendars : destinations;
  const noun = tab === "services" ? "account" : tab === "calendars" ? "calendar" : "destination";
  useEffect(() => {
    onStatus?.(count ? `${count} ${noun}${count === 1 ? "" : "s"}` : "");
  }, [count, noun, onStatus]);
  return (
    <PreferencePane label="Accounts" testId="settings-accounts">
      <SegmentedTabs
        label="Accounts"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "services", label: "Services" },
          { id: "calendars", label: "Calendars" },
          { id: "destinations", label: "Send to" },
        ]}
      >
        <div className="surface-tab-panel" hidden={tab !== "services"}>
          <ConnectionsPane {...connections} key={serviceFocus} focusProvider={serviceFocus} onCount={setServices} />
        </div>
        <div className="surface-tab-panel" hidden={tab !== "calendars"}>
          <CalendarSection b={b} cal={cal} commitMany={writer.commitMany} onRefuse={writer.setRefusal} beforeChange={writer.beforeCalendarChange} onChanged={connections.onCalendarChanged} />
        </div>
        <div className="surface-tab-panel" hidden={tab !== "destinations"}>
          <Destinations onCount={setDestinations} onSetUpAccount={(channel) => { focusService(channel); setTab("services"); }} />
        </div>
      </SegmentedTabs>
    </PreferencePane>
  );
}
