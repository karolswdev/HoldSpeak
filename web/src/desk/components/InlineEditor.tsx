// The in-world editor (HS-73-03): the object IS the editor — the iPad's
// DioInlineNoteCard grammar. Anchored beside the object on the stage; the
// world dims AROUND it via a radial vignette (never a flat scrim, never a
// dialog takeover); saves are on-change (debounced PUT), so nothing is lost;
// Escape or a click outside settles the object back.
import { useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../store";
import type { WorldObject } from "../world";
import type { UnitPos } from "../store";
import { MicButton } from "./MicButton";

function useDebouncedSave(kind: string, id: string) {
  const { updatePrimitive } = useDesk.getState();
  const timer = useRef<number | null>(null);
  const pending = useRef<Record<string, unknown>>({});
  return (patch: Record<string, unknown>) => {
    pending.current = { ...pending.current, ...patch };
    if (timer.current) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      const body = pending.current;
      pending.current = {};
      void updatePrimitive(kind, id, body);
    }, 450);
  };
}

export function InlineEditor({ o, u }: { o: WorldObject; u: UnitPos }) {
  const { closeEditor } = useDesk.getState();
  const items = useDesk((s) => s.items);
  const profiles = useDesk((s) => s.profiles);
  const ref = useRef<HTMLDivElement | null>(null);
  const save = useDebouncedSave(o.kind === "kb" ? "kb" : o.kind, o.id);
  const [more, setMore] = useState(false);

  // Fresh field state seeded from the live item (the store's copy).
  const live = useMemo(
    () => (items[o.kind] || []).find((x) => x.id === o.id) || o.ref,
    [items, o.kind, o.id],
  );
  const [f, setF] = useState<Record<string, string>>(() => ({
    title: String((live as any).title || ""),
    body: String((live as any).bodyMarkdown || ""),
    tags: (((live as any).tags as string[]) || []).join(", "),
    name: String((live as any).name || ""),
    role: String((live as any).role || ""),
    systemPrompt: String((live as any).systemPrompt || ""),
    userTemplate: String((live as any).userTemplate || ""),
    tools: (((live as any).tools as string[]) || []).join(", "),
    kbId: String((live as any).kbId || ""),
    profileId: String((live as any).profileId || ""),
  }));

  const set = (key: string, wire: string, value: string, split = false) => {
    setF((prev) => ({ ...prev, [key]: value }));
    save({
      [wire]: split
        ? value.split(",").map((t) => t.trim()).filter(Boolean)
        : value,
    });
  };

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeEditor();
    };
    document.addEventListener("keydown", onKey);
    // Focus the first field on open.
    ref.current?.querySelector<HTMLInputElement>("input, textarea")?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  // Editor to the object's free side.
  const side = u.x > 0.55 ? "left" : "right";
  const style: React.CSSProperties = {
    top: `${Math.min(78, Math.max(8, u.y * 100 - 6)).toFixed(2)}%`,
    [side === "right" ? "left" : "right"]:
      `${(side === "right" ? u.x * 100 + 7 : (1 - u.x) * 100 + 7).toFixed(2)}%`,
  };

  return (
    <>
      <div
        className="desk-vignette"
        style={{ "--vx": `${u.x * 100}%`, "--vy": `${u.y * 100}%` } as React.CSSProperties}
        onPointerDown={closeEditor}
      />
      <div ref={ref} className="desk-editor" style={style} onPointerDown={(e) => e.stopPropagation()}>
        {o.kind === "note" && (
          <>
            <input
              value={f.title}
              placeholder="Title"
              onChange={(e) => set("title", "title", e.target.value)}
            />
            <textarea
              rows={7}
              value={f.body}
              placeholder="Write"
              onChange={(e) => set("body", "body_markdown", e.target.value)}
            />
            <input
              value={f.tags}
              placeholder="Tags"
              onChange={(e) => set("tags", "tags", e.target.value, true)}
            />
          </>
        )}
        {o.kind === "kb" && (
          <input
            value={f.name}
            placeholder="Name"
            onChange={(e) => set("name", "name", e.target.value)}
          />
        )}
        {o.kind === "agent" && (
          <>
            <input
              value={f.name}
              placeholder="Name"
              onChange={(e) => set("name", "name", e.target.value)}
            />
            <input
              value={f.role}
              placeholder="Role"
              onChange={(e) => set("role", "role", e.target.value)}
            />
            <textarea
              rows={4}
              value={f.systemPrompt}
              placeholder="System prompt"
              onChange={(e) => set("systemPrompt", "system_prompt", e.target.value)}
            />
            {more ? (
              <>
                <textarea
                  rows={3}
                  value={f.userTemplate}
                  placeholder="User template"
                  onChange={(e) => set("userTemplate", "user_template", e.target.value)}
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
                  <option value="">No KB</option>
                  {(items.kb || []).map((k) => (
                    <option key={String(k.id)} value={String(k.id)}>
                      {String(k.name || k.id)}
                    </option>
                  ))}
                </select>
                <select
                  value={f.profileId}
                  onChange={(e) => set("profileId", "profile_id", e.target.value)}
                >
                  <option value="">Hub default</option>
                  {profiles.map((p) => (
                    <option key={String(p.id)} value={String(p.id)}>
                      {String(p.name || p.id)}
                    </option>
                  ))}
                </select>
              </>
            ) : (
              <button type="button" className="desk-editor-more" onClick={() => setMore(true)}>
                More
              </button>
            )}
          </>
        )}
        <div className="desk-editor-foot">
          <MicButton
            onText={(t) => {
              // Fill the primary text field for the kind: a note's body,
              // otherwise the name/title.
              if (o.kind === "note") {
                set("body", "body_markdown", (f.body ? f.body + " " : "") + t);
              } else if (o.kind === "kb") {
                set("name", "name", (f.name ? f.name + " " : "") + t);
              } else {
                set("systemPrompt", "system_prompt", (f.systemPrompt ? f.systemPrompt + " " : "") + t);
              }
            }}
          />
          <span className="desk-editor-spacer" />
          <button type="button" className="desk-chip quiet" onClick={closeEditor}>
            Done
          </button>
        </div>
      </div>
    </>
  );
}
