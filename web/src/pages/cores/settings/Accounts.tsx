// Settings > Accounts: connections, calendar, destinations and credentials. Moved out of SettingsCore.tsx.
import { Button } from "../../../components/signal/Signal";
import { PreferencePane, SegmentedTabs, PaneInspector, PaneActions } from "../../../desk/surface";
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
const ROTATABLE_SECRETS = new Set([
  "web_token",
  "device_psk",
  "telegram_pairing_code",
]);

/** A credential's Replace, Rotate and Delete. The face holds the busy id
 *  (the status bar says Saving while one is in flight). */
export function useSecretChanges(writer: SettingsWriter, onWritten: () => void) {
  const [secretBusy, setSecretBusy] = useState("");
  const changeSecret = async (
    secretId: string,
    action: "replace" | "rotate" | "delete",
    value?: string,
  ) => {
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
    } catch (error) {
      writer.setRefusal(readableError(error));
    } finally {
      setSecretBusy("");
    }
  };
  return { secretBusy, changeSecret };
}

export type SecretChanges = ReturnType<typeof useSecretChanges>;

/** Accounts are three list panes; secrets keep their separate inspector. */
export function AccountsSection({ b, secrets: secretChanges, cal, writer, connections }: {
  b: SettingsBindings; secrets: SecretChanges; cal: CalendarSources; writer: SettingsWriter;
  connections: { onFooterUpdate: (foot: ConnectionsFoot) => void; onOpenModule: (id: string) => void; focusProvider: string | null | undefined; onAttention?: (reason: string | null) => void; onCalendarChanged: () => Promise<void> };
}) {
  const tabFor = (focus: string | null | undefined) => focus === "calendar" ? "calendars" : focus === "destinations" ? "destinations" : "services";
  const [tab, setTab] = useState(tabFor(connections.focusProvider));
  const [serviceFocus, focusService] = useState(connections.focusProvider);
  const [credentials, showCredentials] = useState(false);
  useEffect(() => {
    if (!connections.focusProvider) return;
    setTab(tabFor(connections.focusProvider));
    focusService(connections.focusProvider);
    showCredentials(false);
  }, [connections.focusProvider]);
  const secretRows = Object.entries((b.data._secrets ?? {}) as Record<string, SecretState>).filter(([id]) => !id.startsWith("telegram_"));
  return <PreferencePane label="Accounts" testId="settings-accounts">
    <SegmentedTabs label="Accounts" value={tab} onChange={(id) => { setTab(id); showCredentials(false); }} tabs={[
      { id: "services", label: "Services" }, { id: "calendars", label: "Calendars" }, { id: "destinations", label: "Send to" },
    ]}>
      <div className="surface-tab-panel" hidden={tab !== "services"}>
        {credentials ? <PaneInspector label="Credentials" onClose={() => showCredentials(false)}><GadgetGroup>{secretRows.map(([id, state]) => <SecretRow key={id}
          label={SECRET_LABELS[id] ?? title(id)} configured={Boolean(state.configured)} destination={state.destination}
          busy={secretChanges.secretBusy === id} rotatable={ROTATABLE_SECRETS.has(id)}
          onReplace={(value) => void secretChanges.changeSecret(id, "replace", value)} onRotate={() => void secretChanges.changeSecret(id, "rotate")} onDelete={() => void secretChanges.changeSecret(id, "delete")} />)}</GadgetGroup></PaneInspector>
        : <><ConnectionsPane {...connections} key={serviceFocus} focusProvider={serviceFocus} extraVerbs={[{ id: "credentials", label: "Credentials…", run: () => showCredentials(true) }]} /></>}
      </div>
      <div className="surface-tab-panel" hidden={tab !== "calendars"}><CalendarSection b={b} cal={cal} commitMany={writer.commitMany} onRefuse={writer.setRefusal} beforeChange={writer.beforeCalendarChange} onChanged={connections.onCalendarChanged} /></div>
      <div className="surface-tab-panel" hidden={tab !== "destinations"}><Destinations onSetUpAccount={(channel) => { focusService(channel); setTab("services"); }} /></div>
    </SegmentedTabs>
  </PreferencePane>;
}
