// HS-95-07 — the Runs-on core: runtime destinations, hosted anywhere.
// HS-98-07 — re-crafted native: the editor left its modal for an
// in-surface section; delete is an inline two-step. Wire calls
// unchanged.
import { useState } from "react";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  Checkbox,
  Field,
  InlineMessage,
  Select,
  StatusPill,
  TextInput,
} from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import {
  destinationClassLabel,
  type DestinationClass,
} from "../../lib/productLanguage";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceBay,
  SurfaceSection,
  SurfaceState,
  SurfaceSwitchboard,
  SurfaceVerbs,
} from "../../desk/surface/Surface";

type Profile = Record<string, unknown>;
type Envelope = {
  profiles?: Profile[];
  mesh_liveness?: Record<
    string,
    { live?: boolean; last_seen_seconds?: number }
  >;
};
const PRIVATE_HOST = /^(localhost|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;

function profileDestinationClass(profile: Profile): DestinationClass {
  const kind = String(profile.kind ?? "onDevice");
  if (kind === "desktop" || kind === "meshNode") return "paired_device";
  if (kind === "openAICompatible") {
    let host = "";
    try {
      host = new URL(String(profile.base_url || "")).hostname;
    } catch {
      host = "";
    }
    return PRIVATE_HOST.test(host) ? "private_endpoint" : "external_service";
  }
  return "this_device";
}

const blank = (): Profile => ({
  name: "",
  kind: "openAICompatible",
  model_file: "",
  base_url: "",
  model: "",
  node: "",
  context_limit: 16384,
  requires_key: true,
});

function lastSeenLabel(seconds: unknown): string {
  const n = Number(seconds);
  if (!Number.isFinite(n) || n < 0) return "offline";
  if (n < 90) return "offline — last seen just now";
  if (n < 5400) return `offline — last seen ${Math.round(n / 60)} m ago`;
  return `offline — last seen ${Math.round(n / 3600)} h ago`;
}

export function ProfilesCore({ hero }: CoreProps) {
  const resource = useResource<Envelope>("/api/profiles", {});
  const settings = useResource<Record<string, unknown>>("/api/settings", {});
  const [editing, setEditing] = useState<Profile | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const profiles = asRows(resource.data, ["profiles"]).filter(
    (row) => !row.deleted,
  );
  const dictation = (settings.data.dictation ?? {}) as Record<string, unknown>;
  const runtime = (dictation.runtime ?? {}) as Record<string, unknown>;
  const defaultId = String(runtime.profile_id ?? "");
  const makeDefault = async (profile: Profile) => {
    setBusy(true);
    setMessage("");
    try {
      await apiFetch("/api/settings", {
        method: "PUT",
        json: {
          dictation: { runtime: { profile_id: String(profile.id) } },
        },
      });
      await settings.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };

  const field = (key: string, value: unknown) =>
    setEditing((current) => (current ? { ...current, [key]: value } : current));
  const save = async () => {
    if (!editing || !String(editing.name ?? "").trim()) {
      setMessage("A Runs on destination needs a name.");
      return;
    }
    setBusy(true);
    setMessage("");
    try {
      const id = String(editing.id ?? "");
      await apiFetch(
        id ? `/api/profiles/${encodeURIComponent(id)}` : "/api/profiles",
        { method: id ? "PUT" : "POST", json: editing },
      );
      setEditing(null);
      await resource.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };
  const remove = async (profile: Profile) => {
    setBusy(true);
    try {
      await apiFetch(
        `/api/profiles/${encodeURIComponent(String(profile.id))}`,
        { method: "DELETE" },
      );
      await resource.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };

  const verbs = (
    <Button variant="primary" dense onClick={() => setEditing(blank())}>
      New destination
    </Button>
  );
  return (
    <>
      {hero ? hero(verbs) : <SurfaceVerbs>{verbs}</SurfaceVerbs>}
      {message ? <InlineMessage tone="error">{message}</InlineMessage> : null}
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceSection label="Destinations">
          {!profiles.length ? (
            <SurfaceState
              empty
              emptyLabel="No saved destinations"
              emptyGlyph="⇄"
            />
          ) : (
            <SurfaceSwitchboard>
              {[...profiles]
                .sort((a, b) =>
                  String(a.id) === defaultId
                    ? -1
                    : String(b.id) === defaultId
                      ? 1
                      : 0,
                )
                .map((profile, index) => {
                  const kind = String(profile.kind ?? "onDevice");
                  const node = String(profile.node ?? "");
                  const liveness = resource.data.mesh_liveness?.[node];
                  const isMesh = kind === "meshNode";
                  const live = isMesh ? Boolean(liveness?.live) : true;
                  const isDefault =
                    Boolean(defaultId) && String(profile.id) === defaultId;
                  const model =
                    String(profile.model ?? "") ||
                    String(profile.model_file ?? "").split("/").pop() ||
                    "";
                  const stateText = isMesh
                    ? live
                      ? "· live"
                      : `· ${lastSeenLabel(liveness?.last_seen_seconds)}`
                    : "· ready";
                  const ctx = Number(profile.context_limit ?? 0);
                  return (
                    <SurfaceBay
                      key={rowId(profile, index)}
                      route={isDefault}
                      lamp={
                        <span
                          className="lamp"
                          data-on={live ? "true" : "false"}
                          aria-hidden="true"
                        />
                      }
                      name={String(profile.name ?? "Untitled destination")}
                      state={stateText}
                      model={model || undefined}
                      where={
                        <>
                          {kind === "openAICompatible" ? (
                            <span>{String(profile.base_url ?? "")}</span>
                          ) : null}
                          {kind === "onDevice" ? <span>on device</span> : null}
                          {isMesh ? <span>mesh · {node}</span> : null}
                          {ctx > 0 ? (
                            <span>ctx {Math.round(ctx / 1024)}k</span>
                          ) : null}
                        </>
                      }
                      badge={
                        <StatusPill
                          tone={
                            isMesh && !live
                              ? "warning"
                              : profileDestinationClass(profile) ===
                                  "external_service"
                                ? "warning"
                                : "success"
                          }
                        >
                          {destinationClassLabel(
                            profileDestinationClass(profile),
                          )}
                        </StatusPill>
                      }
                      tag={isDefault ? "Default" : undefined}
                      verbs={
                        <>
                          {!isDefault ? (
                            <Button
                              dense
                              variant="ghost"
                              loading={busy}
                              onClick={() => void makeDefault(profile)}
                            >
                              Make default
                            </Button>
                          ) : null}
                          <Button
                            dense
                            onClick={() => setEditing({ ...profile })}
                          >
                            Edit
                          </Button>
                          <ConfirmVerb
                            label="Delete"
                            confirmLabel="Delete?"
                            busy={busy}
                            onConfirm={() => void remove(profile)}
                          />
                        </>
                      }
                    />
                  );
                })}
            </SurfaceSwitchboard>
          )}
        </SurfaceSection>
        {editing ? (
          <SurfaceSection
            label={
              editing.id ? "Edit Runs on destination" : "New Runs on destination"
            }
            actions={
              <Button dense variant="ghost" onClick={() => setEditing(null)}>
                Cancel
              </Button>
            }
          >
            <Field label="Name">
              {({ id }) => (
                <TextInput
                  id={id}
                  value={String(editing.name ?? "")}
                  onChange={(event) => field("name", event.target.value)}
                />
              )}
            </Field>
            <Field label="Kind">
              {({ id }) => (
                <Select
                  id={id}
                  value={String(editing.kind)}
                  onChange={(event) => field("kind", event.target.value)}
                >
                  <option value="openAICompatible">
                    OpenAI-compatible endpoint
                  </option>
                  <option value="onDevice">This device</option>
                  <option value="desktop">Paired device</option>
                  <option value="meshNode">Mesh node</option>
                </Select>
              )}
            </Field>
            {editing.kind === "openAICompatible" ? (
              <>
                <Field label="Base URL">
                  {({ id }) => (
                    <TextInput
                      id={id}
                      type="url"
                      value={String(editing.base_url ?? "")}
                      onChange={(event) => field("base_url", event.target.value)}
                    />
                  )}
                </Field>
                <Field label="Model">
                  {({ id }) => (
                    <TextInput
                      id={id}
                      value={String(editing.model ?? "")}
                      onChange={(event) => field("model", event.target.value)}
                    />
                  )}
                </Field>
                <Checkbox
                  label="Requires its own key on the hub"
                  checked={Boolean(editing.requires_key)}
                  onChange={(event) =>
                    field("requires_key", event.target.checked)
                  }
                />
              </>
            ) : null}
            {editing.kind === "onDevice" ? (
              <Field label="Model file">
                {({ id }) => (
                  <TextInput
                    id={id}
                    value={String(editing.model_file ?? "")}
                    onChange={(event) => field("model_file", event.target.value)}
                  />
                )}
              </Field>
            ) : null}
            {editing.kind === "meshNode" ? (
              <Field label="Node name">
                {({ id }) => (
                  <TextInput
                    id={id}
                    value={String(editing.node ?? "")}
                    onChange={(event) => field("node", event.target.value)}
                  />
                )}
              </Field>
            ) : null}
            <Field label="Context window">
              {({ id }) => (
                <TextInput
                  id={id}
                  type="number"
                  min={1024}
                  value={Number(editing.context_limit ?? 16384)}
                  onChange={(event) =>
                    field("context_limit", Number(event.target.value))
                  }
                />
              )}
            </Field>
            <div className="surface-actions">
              <Button variant="primary" dense loading={busy} onClick={save}>
                Save destination
              </Button>
            </div>
          </SurfaceSection>
        ) : null}
      </SurfaceState>
    </>
  );
}
