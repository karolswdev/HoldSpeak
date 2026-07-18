// HS-95-07 — the Runs-on core: runtime destinations, hosted anywhere.
import { useState } from "react";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  Checkbox,
  Dialog,
  EmptyState,
  Field,
  InlineMessage,
  Panel,
  Select,
  StatusPill,
  TextInput,
} from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import {
  destinationClassLabel,
  type DestinationClass,
} from "../../lib/productLanguage";
import {
  ConfirmAction,
  ResourceState,
  asRows,
  rowId,
  useResource,
} from "../pageSupport";

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

export function ProfilesCore({ hero }: CoreProps) {
  const resource = useResource<Envelope>("/api/profiles", {});
  const [editing, setEditing] = useState<Profile | null>(null);
  const [deleting, setDeleting] = useState<Profile | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const profiles = asRows(resource.data, ["profiles"]).filter(
    (row) => !row.deleted,
  );

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
  const remove = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await apiFetch(
        `/api/profiles/${encodeURIComponent(String(deleting.id))}`,
        { method: "DELETE" },
      );
      setDeleting(null);
      await resource.reload();
    } catch (error) {
      setMessage(readableError(error));
    } finally {
      setBusy(false);
    }
  };

  const verbs = (
          <Button variant="primary" onClick={() => setEditing(blank())}>
            New destination
          </Button>
  );
  return (
    <>
      {hero ? hero(verbs) : <div className="desk-core-verbs">{verbs}</div>}
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <Panel title="Destinations" eyebrow="Stored definitions">
          {message ? (
            <InlineMessage tone="error">{message}</InlineMessage>
          ) : null}
          {!profiles.length ? (
            <EmptyState title="No saved destinations">
              Add a paired device, private endpoint, mesh node, or external
              service. The hub keeps required keys.
            </EmptyState>
          ) : (
            <ul className="data-list">
              {profiles.map((profile, index) => {
                const kind = String(profile.kind ?? "onDevice");
                const node = String(profile.node ?? "");
                const liveness = resource.data.mesh_liveness?.[node];
                return (
                  <li className="data-row" key={rowId(profile, index)}>
                    <div>
                      <strong>
                        {String(profile.name ?? "Untitled destination")}
                      </strong>
                      <small>
                        {kind === "openAICompatible"
                          ? String(profile.base_url ?? "Endpoint")
                          : kind === "meshNode"
                            ? `mesh · ${node}`
                            : String(profile.model_file ?? "This device")}
                      </small>
                    </div>
                    <div className="button-row">
                      <StatusPill
                        tone={
                          kind === "meshNode"
                            ? liveness?.live
                              ? "success"
                              : "warning"
                            : "neutral"
                        }
                      >
                        {kind === "meshNode"
                          ? liveness?.live
                            ? "live"
                            : "offline"
                          : destinationClassLabel(
                              profileDestinationClass(profile),
                            )}
                      </StatusPill>
                      <Button dense onClick={() => setEditing({ ...profile })}>
                        Edit
                      </Button>
                      <Button
                        dense
                        variant="ghost"
                        onClick={() => setDeleting(profile)}
                      >
                        Delete
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>
      </ResourceState>
      <Dialog
        open={Boolean(editing)}
        title={
          editing?.id ? "Edit Runs on destination" : "New Runs on destination"
        }
        onClose={() => setEditing(null)}
      >
        {editing ? (
          <div className="dialog-form">
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
                      onChange={(event) =>
                        field("base_url", event.target.value)
                      }
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
                    onChange={(event) =>
                      field("model_file", event.target.value)
                    }
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
            {message ? (
              <InlineMessage tone="error">{message}</InlineMessage>
            ) : null}
            <div className="button-row">
              <Button variant="primary" loading={busy} onClick={save}>
                Save destination
              </Button>
              <Button variant="ghost" onClick={() => setEditing(null)}>
                Cancel
              </Button>
            </div>
          </div>
        ) : null}
      </Dialog>
      <ConfirmAction
        open={Boolean(deleting)}
        title="Delete Runs on destination?"
        detail={`Delete ${String(deleting?.name ?? "this destination")}. Any hub configuration that refers to it will need another destination.`}
        busy={busy}
        onConfirm={remove}
        onClose={() => setDeleting(null)}
      />
    </>
  );
}
