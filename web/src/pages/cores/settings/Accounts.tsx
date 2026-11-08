// Settings > Accounts: connections, calendar, destinations and credentials. Moved out of SettingsCore.tsx.
import { useState } from "react";
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

/* ── Connections: tools + credentials + RAW ── */
export function AccountsSection({ b, secrets: secretChanges, cal, writer, connections }: {
  b: SettingsBindings;
  secrets: SecretChanges;
  cal: CalendarSources;
  writer: SettingsWriter;
  connections: {
    onFooterUpdate: (foot: ConnectionsFoot) => void;
    onOpenModule: (id: string) => void;
    focusProvider: string | null | undefined;
    onCalendarChanged: () => Promise<void>;
  };
}) {
  const { data } = b;
  const { secretBusy, changeSecret } = secretChanges;
  const secrets = (data._secrets ?? {}) as Record<string, SecretState>;
        const RAW_SECRETS = new Set([
          "failure_webhook_url",
          "failure_webhook_credential",
        ]);
        // PG-DIRECTION DIR5: the bot token lives in the keystore, set in
        // Settings ▸ Reach; the static pairing code is gone (one-time codes).
        const keepSecrets = Object.entries(secrets).filter(
          ([id]) => !RAW_SECRETS.has(id) && !id.startsWith("telegram_"),
        );
        const rawSecrets = Object.entries(secrets).filter(([id]) =>
          RAW_SECRETS.has(id),
        );
        const secretRow = ([secretId, state]: [string, SecretState]) => (
          <SecretRow
            key={secretId}
            label={SECRET_LABELS[secretId] ?? title(secretId)}
            configured={Boolean(state.configured)}
            destination={state.destination}
            busy={secretBusy === secretId}
            rotatable={ROTATABLE_SECRETS.has(secretId)}
            onReplace={(value) => void changeSecret(secretId, "replace", value)}
            onRotate={() => void changeSecret(secretId, "rotate")}
            onDelete={() => void changeSecret(secretId, "delete")}
          />
        );
        return (
          <div className="prefs-groups">
            <div className="prefs-column">
              {/* HS-168-03: the Connections face above credentials + mesh. */}
              <ConnectionsPane
                onFooterUpdate={connections.onFooterUpdate}
                onOpenModule={connections.onOpenModule}
                focusProvider={connections.focusProvider}
                onBeforeCalendarChange={writer.beforeCalendarChange}
                onCalendarChanged={connections.onCalendarChanged}
              />
              {/* Betterment setup ST1: Calendar's one home is Accounts. The
                  source rows, Add feed and Import image moved here from
                  Meetings, under the Calendar row's Choose calendar. */}
              <CalendarSection b={b} cal={cal} commitMany={writer.commitMany} onRefuse={writer.setRefusal} />
            </div>
            <div className="prefs-column">
              {/* PHILO-10-04 (B1): the Destinations group, under Tools. */}
              <Destinations />
              {/* PG-DIRECTION DIR6: Telegram's home is Settings ▸ Reach (its
                  token is in the keystore there; Cadence's switch folds there). */}
              {/* PHILO-17 REFIT: keys and tokens are technical; they fold. */}
              <FoldGadget title="Credentials">
                <GadgetGroup>
                  {keepSecrets.map(secretRow)}
                </GadgetGroup>
              </FoldGadget>
              {/* HS-139-04: operator-wiring secrets fold behind RAW. */}
              {rawSecrets.length ? (
                <FoldGadget title="More">
                  <GadgetGroup>{rawSecrets.map(secretRow)}</GadgetGroup>
                </FoldGadget>
              ) : null}
            </div>
          </div>
        );
}
