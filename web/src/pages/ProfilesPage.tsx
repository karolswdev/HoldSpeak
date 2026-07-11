import { useState } from "react";
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
} from "../components/signal/Signal";
import { apiFetch, readableError } from "../lib/api";
import {
  ConfirmAction,
  PageHero,
  ResourceState,
  asRows,
  rowId,
  useResource,
} from "./pageSupport";

type Profile = Record<string, unknown>;
type Envelope = {
  profiles?: Profile[];
  mesh_liveness?: Record<
    string,
    { live?: boolean; last_seen_seconds?: number }
  >;
};
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

export default function ProfilesPage() {
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
      setMessage("A profile needs a name.");
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

  return (
    <div className="page-wrap">
      <PageHero
        eyebrow="Runtime"
        title="Profiles"
        actions={
          <Button variant="primary" onClick={() => setEditing(blank())}>
            New profile
          </Button>
        }
      >
        Name where intelligence runs. Credentials remain on the hub and never
        enter this editor.
      </PageHero>
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <Panel title="Runtime destinations" eyebrow="Shape, never secrets">
          {message ? (
            <InlineMessage tone="error">{message}</InlineMessage>
          ) : null}
          {!profiles.length ? (
            <EmptyState title="No runtime profiles">
              Add a local model, model server, or mesh node. The hub keeps any
              required key.
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
                        {String(profile.name ?? "Untitled profile")}
                      </strong>
                      <small>
                        {kind === "openAICompatible"
                          ? String(profile.base_url ?? "Endpoint")
                          : kind === "meshNode"
                            ? `mesh · ${node}`
                            : String(profile.model_file ?? "On device")}
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
                          : kind === "openAICompatible"
                            ? "cloud-capable"
                            : "on device"}
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
        title={editing?.id ? "Edit runtime profile" : "New runtime profile"}
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
                  <option value="onDevice">On device</option>
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
                  label="Key is configured on the hub"
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
                Save profile
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
        title="Delete runtime profile?"
        detail={`Delete ${String(deleting?.name ?? "this profile")}. Any hub configuration that refers to it will need another destination.`}
        busy={busy}
        onConfirm={remove}
        onClose={() => setDeleting(null)}
      />
    </div>
  );
}
