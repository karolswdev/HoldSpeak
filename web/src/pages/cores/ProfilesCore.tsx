// HS-95-07 — the Runs-on core: runtime destinations, hosted anywhere.
// HS-98-07 — re-crafted native: the editor left its modal for an
// in-surface section; delete is an inline two-step. Wire calls
// unchanged.
// HS-102-01 — the refit: creating/editing a destination is a choice
// among BAYS (endpoint / this device / paired device / mesh node,
// only the chosen path's fields render) that opens IN PLACE on the
// switchboard — the same idea `RuntimeDestination`
// (`settingsBespoke.tsx`) already proved for Settings, applied here
// instead of re-derived. No modal, no form section below the list.
import { useState } from "react";
import type { CoreProps } from "./ActivityCore";
import { Button } from "../../components/signal/Signal";
import {
  LampGadget,
  StepperGadget,
  StringGadget,
} from "../../desk/surface/gadgets";
import { apiFetch, readableError } from "../../lib/api";
import {
  destinationClassLabel,
  type DestinationClass,
} from "../../lib/productLanguage";
import { asRows, rowId, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceBay,
  SurfaceGroup,
  SurfaceSection,
  SurfaceSettingRow,
  SurfaceState,
  SurfaceSwitchboard,
  SurfaceToggle,
} from "../../desk/surface/Surface";

const KIND_BAYS: Array<{ value: string; name: string; caption: string }> = [
  {
    value: "openAICompatible",
    name: "Endpoint",
    caption: "An OpenAI-compatible API, anywhere",
  },
  {
    value: "onDevice",
    name: "This device",
    caption: "A model file already on this machine",
  },
  {
    value: "desktop",
    name: "Paired device",
    caption: "Another HoldSpeak-paired Mac",
  },
  {
    value: "meshNode",
    name: "Mesh node",
    caption: "A configured mesh worker",
  },
];

function validUrl(value: string): boolean {
  if (!value.trim()) return true;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

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
  if (n < 90) return "offline, last seen just now";
  if (n < 5400) return `offline, last seen ${Math.round(n / 60)} m ago`;
  return `offline, last seen ${Math.round(n / 3600)} h ago`;
}

export function ProfilesCore(_props: CoreProps) {
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
    if (
      editing.kind === "openAICompatible" &&
      !validUrl(String(editing.base_url ?? ""))
    ) {
      setMessage("The Base URL isn't a valid http(s) address.");
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

  const editorFor = (target: Profile) => {
    const urlInvalid =
      target.kind === "openAICompatible" &&
      !validUrl(String(target.base_url ?? ""));
    return (
      <>
        <div
          className="settings-bays"
          role="radiogroup"
          aria-label="Destination kind"
        >
          {KIND_BAYS.map((bay) => (
            <button
              key={bay.value}
              type="button"
              role="radio"
              aria-checked={target.kind === bay.value}
              className={
                "settings-bay" +
                (target.kind === bay.value ? " is-selected" : "")
              }
              onClick={() => field("kind", bay.value)}
            >
              <span className="settings-bay-dot" aria-hidden="true" />
              <span className="settings-bay-text">
                <strong>{bay.name}</strong>
                <small>{bay.caption}</small>
              </span>
            </button>
          ))}
        </div>
        <SurfaceGroup>
          <SurfaceSettingRow
            label="Name"
            control={
              <StringGadget
                label="Name"
                value={String(target.name ?? "")}
                onChange={(next) => field("name", next)}
              />
            }
          />
          {target.kind === "openAICompatible" ? (
            <>
              <SurfaceSettingRow
                label="Base URL"
                description={urlInvalid ? "Not a valid http(s) address" : undefined}
                control={
                  <StringGadget
                    label="Base URL"
                    type="url"
                    value={String(target.base_url ?? "")}
                    onChange={(next) => field("base_url", next)}
                  />
                }
              />
              <SurfaceSettingRow
                label="Model"
                control={
                  <StringGadget
                    label="Model"
                    value={String(target.model ?? "")}
                    onChange={(next) => field("model", next)}
                  />
                }
              />
              <SurfaceSettingRow
                label="Requires its own key on the hub"
                control={
                  <SurfaceToggle
                    label="Requires its own key on the hub"
                    checked={Boolean(target.requires_key)}
                    onChange={(checked) => field("requires_key", checked)}
                  />
                }
              />
            </>
          ) : null}
          {target.kind === "onDevice" ? (
            <SurfaceSettingRow
              label="Model file"
              control={
                <StringGadget
                  label="Model file"
                  value={String(target.model_file ?? "")}
                  onChange={(next) => field("model_file", next)}
                />
              }
            />
          ) : null}
          {target.kind === "meshNode" ? (
            <SurfaceSettingRow
              label="Node name"
              control={
                <StringGadget
                  label="Node name"
                  value={String(target.node ?? "")}
                  onChange={(next) => field("node", next)}
                />
              }
            />
          ) : null}
          <SurfaceSettingRow
            label="Context window"
            control={
              <StepperGadget
                label="Context window"
                min={1024}
                step={1024}
                unit="tok"
                value={Number(target.context_limit ?? 16384)}
                onChange={(next) => field("context_limit", next)}
              />
            }
          />
        </SurfaceGroup>
        <div className="surface-actions">
          <Button dense variant="ghost" onClick={() => setEditing(null)}>
            Cancel
          </Button>
          <Button variant="primary" dense loading={busy} onClick={save}>
            {target.id ? "Save" : "Add destination"}
          </Button>
        </div>
      </>
    );
  };

  return (
    <>
      {message ? <SurfaceState error={message} /> : null}
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceSection label="Destinations">
          {!profiles.length ? (
            <p className="surface-empty-caption">
              Nothing runs anywhere but this device yet — add a
              destination below.
            </p>
          ) : null}
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
                  const isEditingThis =
                    Boolean(editing?.id) &&
                    String(editing?.id) === String(profile.id);
                  if (isEditingThis && editing) {
                    return (
                      <SurfaceBay
                        key={rowId(profile, index)}
                        expanded
                        editor={editorFor(editing)}
                      />
                    );
                  }
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
                        <LampGadget
                          on
                          tone={
                            (isMesh && !live) ||
                            profileDestinationClass(profile) ===
                              "external_service"
                              ? "warn"
                              : "ok"
                          }
                          label={destinationClassLabel(
                            profileDestinationClass(profile),
                          )}
                        />
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
              {editing && !editing.id ? (
                <SurfaceBay expanded editor={editorFor(editing)} />
              ) : (
                <SurfaceBay
                  ghost
                  name="+ New destination"
                  onClick={() => setEditing(blank())}
                />
              )}
          </SurfaceSwitchboard>
        </SurfaceSection>
      </SurfaceState>
    </>
  );
}
