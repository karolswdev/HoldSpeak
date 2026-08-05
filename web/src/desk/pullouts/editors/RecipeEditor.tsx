/** Recipe (Persona) inline editor content (HS-117-15). */
import { useMemo, useState } from "react";
import { useDesk } from "../../store";
import { MicButton } from "../../components/MicButton";
import type { Persona } from "../../../lib/primitives";
import { useDebouncedSave } from "./useDebouncedSave";
import type { InlineEditorContentProps } from "./types";

export function RecipeEditor({ object: o, onClose }: InlineEditorContentProps) {
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
        <input
          className="desk-inline-editor-avatar"
          value={f.avatar}
          placeholder="🤖"
          aria-label="Avatar"
          onChange={(e) => set("avatar", "avatar", e.target.value)}
        />
        <input
          value={f.name}
          placeholder="Name"
          onChange={(e) => set("name", "name", e.target.value)}
        />
      </div>
      <input
        value={f.role}
        placeholder="Role"
        onChange={(e) => set("role", "role", e.target.value)}
      />
      <textarea
        rows={4}
        value={f.systemPrompt}
        placeholder="System prompt"
        onChange={(e) =>
          set("systemPrompt", "system_prompt", e.target.value)
        }
      />
      {more ? (
        <>
          <textarea
            rows={3}
            value={f.userTemplate}
            placeholder="User template"
            onChange={(e) =>
              set("userTemplate", "user_template", e.target.value)
            }
          />
          <input
            value={f.tools}
            placeholder="Tools"
            onChange={(e) => set("tools", "tools", e.target.value, true)}
          />
          <select
            value={f.kbId}
            onChange={(e) => set("kbId", "kb_id", e.target.value)}
          >
            <option value="">No Knowledge</option>
            {(items.kb || []).map((k) => (
              <option key={String(k.id)} value={String(k.id)}>
                {String(k.name || k.id)}
              </option>
            ))}
          </select>
          <select
            value={f.profileId}
            onChange={(e) =>
              set("profileId", "profile_id", e.target.value)
            }
          >
            <option value="">Default Runs on</option>
            {profiles.map((p) => (
              <option key={String(p.id)} value={String(p.id)}>
                {String(p.name || p.id)}
              </option>
            ))}
          </select>
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
        <span className="desk-inline-editor-spacer" />
        <button
          type="button"
          className="desk-chip quiet"
          onClick={onClose}
        >
          Done
        </button>
      </div>
    </>
  );
}
