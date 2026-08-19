/** Recipe (Persona) inline editor content (HS-117-15). */
import { useMemo, useState } from "react";
import { useDesk } from "../../store";
import { MicButton } from "../../components/MicButton";
import { AgentAvatar } from "../../components/AgentAvatar";
import { CycleGadget, PadGadget, StringGadget } from "../../surface/gadgets";
import type { Persona } from "../../../lib/primitives";
import { useDebouncedSave } from "./useDebouncedSave";
import type { InlineEditorContentProps } from "./types";

export function RecipeEditor({ object: o, autoFocusName }: InlineEditorContentProps) {
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const save = useDebouncedSave("recipe", o.id);
  const [more, setMore] = useState(false);

  const live = useMemo(
    () => (items.recipe || []).find((x) => x.id === o.id) || o.ref as Persona,
    [items, o.id],
  );
  const [f, setF] = useState<Record<string, string>>(() => ({
    name: String(live.name || ""),
    avatar: String(live.avatar || ""),
    role: String(live.role || ""),
    systemPrompt: String(live.systemPrompt || ""),
    userTemplate: String(live.userTemplate || ""),
    tools: (live.tools || []).join(", "),
    kbId: String(live.kbId || ""),
    profileId: String(live.profileId || ""),
  }));

  const set = (key: string, wire: string, value: string, split = false) => {
    setF((prev) => ({ ...prev, [key]: value }));
    save({
      [wire]: split
        ? value.split(",").map((t) => t.trim()).filter(Boolean)
        : value,
    });
  };

  return (
    <>
      <div className="desk-inline-editor-row">
        <AgentAvatar
          avatar={f.avatar}
          id={o.id}
          size={32}
          className="desk-inline-editor-avatar"
        />
        <StringGadget
          label="Name"
          value={f.name}
          placeholder="Name"
          autoFocus={autoFocusName}
          onChange={(value) => set("name", "name", value)}
        />
      </div>
      <StringGadget
        label="Role"
        value={f.role}
        placeholder="Role"
        onChange={(value) => set("role", "role", value)}
      />
      <PadGadget
        label="System prompt"
        rows={4}
        value={f.systemPrompt}
        placeholder="System prompt"
        onChange={(value) => set("systemPrompt", "system_prompt", value)}
      />
      {more ? (
        <>
          <StringGadget
            label="Avatar"
            value={f.avatar}
            placeholder="Avatar"
            onChange={(value) => set("avatar", "avatar", value)}
          />
          <PadGadget
            label="User template"
            rows={3}
            value={f.userTemplate}
            placeholder="User template"
            onChange={(value) => set("userTemplate", "user_template", value)}
          />
          <StringGadget
            label="Tools"
            value={f.tools}
            placeholder="Tools"
            onChange={(value) => set("tools", "tools", value, true)}
          />
          <CycleGadget
            label="Context"
            value={f.kbId}
            options={[
              { value: "", label: "No context" },
              ...(items.kb || []).map((k) => ({
                value: String(k.id),
                label: String(k.name || k.id),
              })),
            ]}
            onChange={(value) => set("kbId", "kb_id", value)}
          />
          <CycleGadget
            label="Default runs on"
            value={f.profileId}
            options={[
              // HS-130-01: unset = INHERIT (falls through to the global
              // default), NOT "this device". One empty-value meaning, one
              // token: write null, the same token InfoWindow writes.
              { value: "", label: "Inherit default" },
              ...profiles.map((p) => ({
                value: String(p.id),
                label: String(p.name || p.id),
              })),
            ]}
            onChange={(value) => {
              setF((prev) => ({ ...prev, profileId: value }));
              save({ profile_id: value || null });
            }}
          />
        </>
      ) : (
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => setMore(true)}
        >
          More
        </button>
      )}
      <div className="desk-inline-editor-foot">
        <MicButton
          draftScope={`inline:${o.kind}:${o.id}`}
          onText={(t) => {
            set(
              "systemPrompt",
              "system_prompt",
              (f.systemPrompt ? f.systemPrompt + " " : "") + t,
            );
          }}
        />
      </div>
    </>
  );
}
